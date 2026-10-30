import tkinter as tk
from tkinter import ttk
import threading
import paramiko
from paramiko.ssh_exception import NoValidConnectionsError

from . import theme as t


# =========================================================
# Global references
# =========================================================

screen = None

ip_entry = None
username_entry = None
password_entry = None
output_area = None

scan_btn = None
stop_btn = None
back_btn = None
home_btn = None
review_btn = None

status_label = None
progress_bar = None
progress_label = None
success_label = None
failure_label = None

stop_event = threading.Event()
scan_thread = None


# =========================================================
# Initialize screen
# =========================================================

MAX_TARGETS = 1024           # a typo like /16 must not start 65 000 SSH logins

ip_var = None
input_hint = None


def expand_targets(text):
    """
    Turn "10.0.0.5, 10.0.0.8 10.0.0.20-10.0.0.25 10.0.1.0/30" into a list of IPs.
    Returns (ips, error_message).
    """
    import ipaddress
    import re

    ips = []
    for part in [p for p in re.split(r"[,\s;]+", text.strip()) if p]:
        try:
            if "-" in part:
                first, last = (ipaddress.ip_address(x) for x in part.split("-", 1))
                if int(last) < int(first):
                    return [], f"“{part}”: the end address is before the start."
                if int(last) - int(first) + 1 > MAX_TARGETS:
                    return [], f"“{part}” has more than {MAX_TARGETS} addresses."
                ips += [str(ipaddress.ip_address(n)) for n in range(int(first), int(last) + 1)]
            elif "/" in part:
                net = ipaddress.ip_network(part, strict=False)
                if net.num_addresses > MAX_TARGETS:
                    return [], f"“{part}” has more than {MAX_TARGETS} addresses."
                hosts = list(net.hosts()) or [net.network_address]
                ips += [str(h) for h in hosts]
            else:
                ips.append(str(ipaddress.ip_address(part)))
        except ValueError:
            return [], f"“{part}” is not a valid IP address, range or network."
    ips = list(dict.fromkeys(ips))           # remove duplicates, keep order
    if len(ips) > MAX_TARGETS:
        return [], f"That is {len(ips)} addresses; test at most {MAX_TARGETS} at a time."
    return ips, ""


def validate_inputs(_event=None):
    """Live check of the form: inline messages and the Test button state."""
    if input_hint is None:
        return False
    ips, error = expand_targets(ip_var.get())
    user_ok = bool(username_entry.get().strip())
    pass_ok = bool(password_entry.get())
    running = scan_thread is not None and scan_thread.is_alive()

    if not ip_var.get().strip():
        input_hint.configure(text="Type IP addresses, or use “Load from file…”.", style="Muted.TLabel")
    elif error:
        input_hint.configure(text=error, style="Error.TLabel")
    else:
        missing = [n for n, ok in (("username", user_ok), ("password", pass_ok)) if not ok]
        extra = f"  ·  Enter the SSH {' and '.join(missing)} to start." if missing else ""
        input_hint.configure(text=f"{len(ips)} machine{'s' if len(ips) != 1 else ''} will be tested.{extra}",
                             style="Muted.TLabel")

    ok = bool(ips) and not error and user_ok and pass_ok and not running
    if scan_btn is not None:
        scan_btn.state(["!disabled"] if ok else ["disabled"])
    return ok


def load_ip_file():
    """Fill the IP field from a .json / .txt list (the same files the dashboard accepts)."""
    from . import dialogs
    from pathlib import Path
    import json
    import re

    path = dialogs.ask_ip_file(screen)
    if not path:
        return
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    found = []
    try:
        data = json.loads(text)
        items = data if isinstance(data, list) else data.get("hosts", data.get("results", []))
        for item in items:
            ip = item if isinstance(item, str) else (item.get("ip") or item.get("ip_address") or "")
            if ip:
                found.append(str(ip).strip())
    except (ValueError, AttributeError):
        found = re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", text)
    if found:
        ip_var.set(", ".join(dict.fromkeys(found)))
        append_output(f"Loaded {len(found)} address(es) from {Path(path).name}.")
    else:
        append_output(f"No IP addresses found in {Path(path).name}.")


def set_review_count(count):
    if count:
        review_btn.configure(text=f"Review {count} host{'s' if count != 1 else ''}  →")
        review_btn.state(["!disabled"])
    else:
        review_btn.configure(text="Review hosts  →")
        review_btn.state(["disabled"])


def initialize(parent):
    global screen
    global ip_entry, username_entry, password_entry
    global output_area
    global scan_btn, stop_btn
    global back_btn, home_btn, review_btn
    global status_label, progress_bar, progress_label
    global success_label, failure_label
    global ip_var, input_hint

    from . import widgets as w

    ip_var = tk.StringVar(master=parent)

    screen = ttk.Frame(parent, style="App.TFrame", padding=t.M)

    # -- header: title, subtitle, where am I
    header = ttk.Frame(screen, padding=(t.S, t.S))
    header.pack(fill="x", pady=(0, t.S))
    ttk.Label(header, text="Reliable scan", style="Big.TLabel").pack(side="left")
    ttk.Label(header, text="Log in to each machine to check which ones you can manage.",
              style="Muted.TLabel").pack(side="left", padx=(t.M, 0), pady=(t.XS, 0))
    w.step_indicator(header, current=1).pack(side="right")

    # -- navigation (packed before the expanding results)
    nav = ttk.Frame(screen)
    nav.pack(side="bottom", fill="x", pady=(t.S, 0))
    back_btn = w.button(nav, "←  Back", None, "Choose a different way to find machines")
    back_btn.pack(side="left")
    home_btn = w.button(nav, "⌂  Home", None, "Return to the start screen")
    home_btn.pack(side="left", padx=(t.S, 0))
    review_btn = w.button(nav, "Review hosts  →", None,
                          "See which logins worked, then open the dashboard. Your username and\n"
                          "password are filled in on the dashboard automatically.", style="Primary.TButton")
    review_btn.state(["disabled"])
    review_btn.pack(side="right")

    # -- what to test
    config = w.card(screen, "Machines and login")
    config.pack(fill="x", pady=(0, t.S))
    config.columnconfigure(1, weight=1)
    config.columnconfigure(3, weight=1)

    ttk.Label(config, text="IP addresses").grid(row=0, column=0, sticky="w", pady=t.XS)
    ip_entry = ttk.Entry(config, textvariable=ip_var, style="Mono.TEntry", font=t.FONTS["mono"])
    ip_entry.grid(row=0, column=1, columnspan=3, sticky="ew", padx=(t.S, t.S), pady=t.XS)
    w.Tooltip(ip_entry, "Separate with commas or spaces. Ranges and networks work too:\n"
                        "10.0.0.5, 10.0.0.8   ·   10.0.0.20-10.0.0.40   ·   10.0.1.0/28\n"
                        f"At most {MAX_TARGETS} machines at a time.")
    load_btn = w.button(config, "Load from file…", load_ip_file,
                        "Fill the list from a .json or .txt file (one IP per line)",
                        style="Tight.TButton", icon_name="folder")
    load_btn.grid(row=0, column=4, sticky="e", pady=t.XS)

    input_hint = ttk.Label(config, style="Muted.TLabel")
    input_hint.grid(row=1, column=1, columnspan=4, sticky="w", padx=(t.S, 0))

    ttk.Label(config, text="SSH username").grid(row=2, column=0, sticky="w", pady=(t.S, t.XS))
    username_entry = ttk.Entry(config, width=18)
    username_entry.grid(row=2, column=1, sticky="ew", padx=(t.S, t.M), pady=(t.S, t.XS))
    w.Tooltip(username_entry, "An account that exists on every lab machine")
    ttk.Label(config, text="SSH password").grid(row=2, column=2, sticky="w", pady=(t.S, t.XS))
    password_entry = w.PasswordEntry(config, width=14)
    password_entry.grid(row=2, column=3, columnspan=2, sticky="ew", padx=(t.S, 0), pady=(t.S, t.XS))

    controls = ttk.Frame(config)
    controls.grid(row=3, column=0, columnspan=5, sticky="ew", pady=(t.S, 0))
    scan_btn = w.button(controls, "▶  Test connections", None,
                        "Try to log in to each machine over SSH (5 s timeout per machine)",
                        "Enter", style="Primary.TButton")
    scan_btn.pack(side="left", padx=(0, t.S))
    stop_btn = w.button(controls, "■  Stop", None, "Stop after the machine being tested now")
    stop_btn.state(["disabled"])
    stop_btn.pack(side="left")
    ttk.Label(controls, text="Only test machines you are authorized to access.",
              style="Muted.TLabel").pack(side="right")

    for widget in (ip_entry, username_entry, password_entry.entry):
        widget.bind("<KeyRelease>", validate_inputs, add="+")
        widget.bind("<Return>", lambda e: scan_btn.invoke() if scan_btn.instate(["!disabled"]) else None)
    ip_var.trace_add("write", lambda *_: validate_inputs())

    # -- progress and results in one card, so the log keeps room on short windows
    progress_section = w.card(screen, "Progress and results")
    progress_section.pack(fill="both", expand=True)

    status_row = ttk.Frame(progress_section)
    status_row.pack(fill="x")
    ttk.Label(status_row, text="Status:").pack(side="left")
    status_label = ttk.Label(status_row, text="Ready", style="Muted.TLabel")
    status_label.pack(side="left", padx=(t.XS, 0))
    progress_label = ttk.Label(status_row, text="Hosts tested: 0 / 0", style="Muted.TLabel")
    progress_label.pack(side="left", padx=(t.L, 0))
    success_label = ttk.Label(status_row, text="Connected: 0", style="Muted.TLabel")
    success_label.pack(side="left", padx=(t.L, 0))
    failure_label = ttk.Label(status_row, text="Failed: 0", style="Muted.TLabel")
    failure_label.pack(side="left", padx=(t.L, 0))
    w.Tooltip(failure_label, "Unreachable machines and rejected logins")

    progress_bar = ttk.Progressbar(progress_section, mode="determinate", maximum=100)
    progress_bar.pack(fill="x", pady=(t.S, 0))

    output_frame = ttk.Frame(progress_section)
    output_frame.pack(fill="both", expand=True, pady=(t.S, 0))
    scrollbar = ttk.Scrollbar(output_frame, orient="vertical")
    output_area = tk.Text(
        output_frame,
        bg=t.SURFACE_2,
        fg=t.TEXT,
        insertbackground=t.TEXT,
        font=t.FONTS["mono"],
        relief="flat",
        padx=t.S,
        pady=t.S,
        highlightthickness=1,
        highlightbackground=t.BORDER,
        highlightcolor=t.FOCUS,
        wrap="word",
        state="disabled",
        height=4,
        yscrollcommand=scrollbar.set
    )
    t.on_change(lambda: _recolour_text(output_area))
    scrollbar.config(command=output_area.yview)
    output_area.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    validate_inputs()

    # Fill the parent frame.
    screen.place(relwidth=1, relheight=1)


# =========================================================
# Output helpers
# =========================================================

def _recolour_text(widget):
    """tk.Text is not a ttk widget: repaint it after a light/dark switch."""
    widget.configure(bg=t.SURFACE_2, fg=t.TEXT, insertbackground=t.TEXT,
                     highlightbackground=t.BORDER, highlightcolor=t.FOCUS)


def append_output(message):
    """Append a message to the results area."""

    if output_area is None:
        return

    output_area.configure(state="normal")
    output_area.insert(tk.END, str(message) + "\n")
    output_area.see(tk.END)
    output_area.configure(state="disabled")


def clear_output():
    """Clear the results area."""

    if output_area is None:
        return

    output_area.configure(state="normal")
    output_area.delete("1.0", tk.END)
    output_area.configure(state="disabled")


# =========================================================
# Host review integration
# =========================================================

def update_review_hosts(results):
    """
    Send reliable scan results to the Host Review screen.

    Each record contains:
        ip
        port
        status
    """

    from . import host_review as hr

    hr.set_hosts(results, source="Reliable scan")

    # Enable the button belonging to this screen.
    if review_btn is not None:
        review_btn.config(
            state="normal" if results else "disabled"
        )


# =========================================================
# Start reliable scan
# =========================================================

def start_scan(root):
    global scan_thread

    # Prevent simultaneous scans.
    if scan_thread is not None and scan_thread.is_alive():
        return

    # Read IP addresses (commas, spaces, ranges and networks).
    ips, ip_error = expand_targets(ip_entry.get())
    if ip_error:
        append_output(ip_error)
        return

    username = username_entry.get().strip()
    password = password_entry.get()

    # Validate inputs.
    if not ips:
        append_output("Please enter at least one IP address.")
        return

    if not username or not password:
        append_output("Please enter your SSH username and password.")
        return

    # Reset scan state.
    stop_event.clear()

    scan_btn.state(["disabled"])
    stop_btn.state(["!disabled"])
    back_btn.state(["disabled"])
    home_btn.state(["disabled"])
    set_review_count(0)

    status_label.config(text="Connecting...")

    progress_label.config(
        text=f"Hosts tested: 0 / {len(ips)}"
    )

    progress_bar.config(value=0)
    success_label.config(text="Connected: 0")
    failure_label.config(text="Failed: 0")

    clear_output()
    append_output("Starting Reliable Scan...")

    # -----------------------------------------------------
    # Background worker
    # -----------------------------------------------------

    def worker():
        successes = 0
        failures = 0
        tested = 0

        # Important: initialize results before using it.
        results = []

        try:
            for index, ip in enumerate(ips, start=1):

                # Stop before starting another host.
                if stop_event.is_set():
                    break

                root.after(
                    0,
                    lambda i=index, host=ip:
                    append_output(
                        f"[{i}/{len(ips)}] Testing {host}..."
                    )
                )

                client = paramiko.SSHClient()

                # Preserve the original behavior. See security note below.
                client.set_missing_host_key_policy(
                    paramiko.AutoAddPolicy()
                )

                # Set a default outcome in case an exception occurs.
                host_status = "Unreachable"

                try:
                    client.connect(
                        hostname=ip,
                        username=username,
                        password=password,
                        port=22,
                        timeout=5,
                        banner_timeout=5,
                        auth_timeout=5
                    )

                    successes += 1
                    host_status = "Reachable"

                    message = (
                        f"[{index}/{len(ips)}] "
                        f"{ip} — SSH Connected"
                    )

                except paramiko.AuthenticationException:
                    failures += 1

                    # SSH responded, but the supplied credentials failed.
                    host_status = "Authentication Failed"

                    message = (
                        f"[{index}/{len(ips)}] "
                        f"{ip} — Authentication Failed"
                    )

                except NoValidConnectionsError:
                    failures += 1
                    host_status = "Unreachable"

                    message = (
                        f"[{index}/{len(ips)}] "
                        f"{ip} — Connection Refused"
                    )

                except (TimeoutError, paramiko.SSHException) as exc:
                    failures += 1
                    host_status = "Unreachable"

                    message = (
                        f"[{index}/{len(ips)}] "
                        f"{ip} — {type(exc).__name__}: {exc}"
                    )

                except OSError as exc:
                    failures += 1
                    host_status = "Unreachable"

                    message = (
                        f"[{index}/{len(ips)}] "
                        f"{ip} — Network Error: {exc}"
                    )

                except Exception as exc:
                    failures += 1
                    host_status = "Unreachable"

                    message = (
                        f"[{index}/{len(ips)}] "
                        f"{ip} — {type(exc).__name__}: {exc}"
                    )

                finally:
                    client.close()

                # Store one record per tested host.
                results.append({
                    "ip": ip,
                    "port": 22,
                    "status": host_status
                })

                tested += 1

                # Update UI only from Tkinter's main thread.
                root.after(
                    0,
                    lambda msg=message:
                    append_output(msg)
                )

                root.after(
                    0,
                    lambda done=tested,
                           total=len(ips),
                           ok=successes,
                           failed=failures:
                    update_progress(
                        done,
                        total,
                        ok,
                        failed
                    )
                )

        finally:
            stopped = stop_event.is_set()

            if stopped:
                final_message = "\nScan stopped by user."
                final_status = "Stopped"
            else:
                final_message = (
                    f"\nScan complete. Connected: {successes} "
                    f"| Failed: {failures}"
                )
                final_status = "Completed"

            # Capture worker values before scheduling UI callbacks.
            final_results = results.copy()
            final_tested = tested

            root.after(
                0,
                lambda data=final_results:
                update_review_hosts(data)
            )

            root.after(
                0,
                lambda msg=final_message,
                       stat=final_status,
                       count=final_tested:
                finish_scan(msg, stat, count)
            )

    scan_thread = threading.Thread(
        target=worker,
        daemon=True
    )

    scan_thread.start()


# =========================================================
# Progress updates
# =========================================================

def update_progress(tested, total, successes, failures):
    """Update the scan progress indicators."""

    if progress_label is not None:
        progress_label.config(
            text=f"Hosts tested: {tested} / {total}"
        )

    percentage = (
        tested / total * 100
        if total
        else 0
    )

    if progress_bar is not None:
        progress_bar.config(value=percentage)

    if success_label is not None:
        success_label.config(
            text=f"Connected: {successes}"
        )

    if failure_label is not None:
        failure_label.config(
            text=f"Failed: {failures}"
        )


# =========================================================
# Finish scan
# =========================================================

def finish_scan(message, status, tested):
    """Restore controls when the scan finishes."""
    global scan_thread
    scan_thread = None          # the worker is finishing; allow a new test

    append_output(message)

    status_label.config(text=status)

    stop_btn.state(["disabled"])
    back_btn.state(["!disabled"])
    home_btn.state(["!disabled"])

    set_review_count(tested)
    validate_inputs()


# =========================================================
# Stop scan
# =========================================================

def stop_reliable_scan():
    """Request the background scan to stop."""

    if scan_thread is None or not scan_thread.is_alive():
        return

    stop_event.set()

    stop_btn.state(["disabled"])
    status_label.config(text="Stopping...")

    append_output(
        "Stopping scan after the current connection attempt..."
    )