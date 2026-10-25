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

def initialize(parent):
    global screen
    global ip_entry, username_entry, password_entry
    global output_area
    global scan_btn, stop_btn
    global back_btn, home_btn, review_btn
    global status_label, progress_bar, progress_label
    global success_label, failure_label

    screen = ttk.Frame(
        parent,
        style="App.TFrame",
        padding=t.M
    )

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    header = ttk.Frame(screen)

    title_area = ttk.Frame(header)

    ttk.Label(
        title_area,
        text="Reliable Scan",
        font=t.FONTS["title"]
    ).pack(anchor="w")

    ttk.Label(
        title_area,
        text="Test SSH connectivity to your lab machines.",
        style="Muted.TLabel"
    ).pack(anchor="w", pady=(t.XS, 0))

    title_area.pack(
        side="left",
        fill="x",
        expand=True
    )

    header.pack(
        fill="x",
        pady=(0, t.M)
    )

    # -----------------------------------------------------
    # Bottom navigation
    # Pack this before the expanding results section.
    # -----------------------------------------------------

    nav = ttk.Frame(screen)

    nav.pack(
        side="bottom",
        fill="x",
        pady=(t.M, 0)
    )

    back_btn = ttk.Button(
        nav,
        text="← Back"
    )
    back_btn.pack(side="left")

    home_btn = ttk.Button(
        nav,
        text="⌂ Home"
    )
    home_btn.pack(
        side="left",
        padx=(t.S, 0)
    )

    review_btn = ttk.Button(
        nav,
        text="Review Hosts →",
        style="Primary.TButton",
        state="disabled"
    )
    review_btn.pack(side="right")

    # -----------------------------------------------------
    # Workflow indicator
    # -----------------------------------------------------

    workflow = ttk.Frame(screen)

    workflow.pack(
        fill="x",
        pady=(0, t.M)
    )

    steps = [
        ("01", "Scan"),
        ("02", "Review Hosts"),
        ("03", "Dashboard")
    ]

    for index, (number, title) in enumerate(steps):
        step = ttk.Frame(workflow)

        step.pack(
            side="left",
            fill="x",
            expand=True
        )

        ttk.Label(
            step,
            text=number,
            font=t.FONTS["heading"],
            style="TLabel" if index == 0 else "Muted.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            step,
            text=title,
            font=t.FONTS["caption"],
            style="TLabel" if index == 0 else "Muted.TLabel"
        ).pack(
            anchor="w",
            pady=(t.XS, 0)
        )

        if index < len(steps) - 1:
            ttk.Label(
                workflow,
                text="→",
                style="Muted.TLabel"
            ).pack(
                side="left",
                padx=t.XS
            )

    # -----------------------------------------------------
    # Connection configuration
    # -----------------------------------------------------

    config = ttk.LabelFrame(
        screen,
        text="Connection Configuration",
        padding=t.M
    )

    config.pack(
        fill="x",
        pady=(0, t.M)
    )

    ttk.Label(
        config,
        text="Target IP addresses (comma-separated)"
    ).pack(anchor="w")

    ip_entry = ttk.Entry(config)
    ip_entry.insert(0, "127.0.0.1")

    ip_entry.pack(
        fill="x",
        pady=(t.XS, t.M)
    )

    credentials = ttk.Frame(config)
    credentials.pack(fill="x")

    user_frame = ttk.Frame(credentials)

    user_frame.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, t.S)
    )

    ttk.Label(
        user_frame,
        text="SSH Username"
    ).pack(anchor="w")

    username_entry = ttk.Entry(user_frame)

    username_entry.pack(
        fill="x",
        pady=(t.XS, 0)
    )

    password_frame = ttk.Frame(credentials)

    password_frame.pack(
        side="left",
        fill="x",
        expand=True
    )

    ttk.Label(
        password_frame,
        text="SSH Password"
    ).pack(anchor="w")

    password_entry = ttk.Entry(
        password_frame,
        show="*"
    )

    password_entry.pack(
        fill="x",
        pady=(t.XS, 0)
    )

    ttk.Label(
        config,
        text="Only test machines you are authorized to access.",
        style="Muted.TLabel"
    ).pack(
        anchor="w",
        pady=(t.S, 0)
    )

    # -----------------------------------------------------
    # Scan controls
    # -----------------------------------------------------

    controls = ttk.Frame(screen)

    controls.pack(
        fill="x",
        pady=(0, t.M)
    )

    scan_btn = ttk.Button(
        controls,
        text="▶ Test Connections",
        style="Primary.TButton"
    )

    scan_btn.pack(
        side="left",
        padx=(0, t.S)
    )

    stop_btn = ttk.Button(
        controls,
        text="■ Stop Scan",
        state="disabled"
    )

    stop_btn.pack(side="left")

    # -----------------------------------------------------
    # Connection progress
    # -----------------------------------------------------

    progress_section = ttk.LabelFrame(
        screen,
        text="Connection Progress",
        padding=t.M
    )

    progress_section.pack(
        fill="x",
        pady=(0, t.M)
    )

    status_row = ttk.Frame(progress_section)
    status_row.pack(fill="x")

    ttk.Label(
        status_row,
        text="Status:",
        font=t.FONTS["body"]
    ).pack(side="left")

    status_label = ttk.Label(
        status_row,
        text="Ready",
        style="Muted.TLabel"
    )

    status_label.pack(
        side="left",
        padx=(t.XS, 0)
    )

    progress_label = ttk.Label(
        progress_section,
        text="Hosts tested: 0 / 0",
        style="Muted.TLabel"
    )

    progress_label.pack(
        anchor="w",
        pady=(t.XS, 0)
    )

    progress_bar = ttk.Progressbar(
        progress_section,
        mode="determinate",
        maximum=100
    )

    progress_bar.pack(
        fill="x",
        pady=(t.S, 0)
    )

    counts = ttk.Frame(progress_section)

    counts.pack(
        fill="x",
        pady=(t.S, 0)
    )

    success_label = ttk.Label(
        counts,
        text="Connected: 0",
        style="Muted.TLabel"
    )

    success_label.pack(side="left")

    failure_label = ttk.Label(
        counts,
        text="Failed: 0",
        style="Muted.TLabel"
    )

    failure_label.pack(
        side="left",
        padx=(t.L, 0)
    )

    # -----------------------------------------------------
    # Connection results
    # -----------------------------------------------------

    results_section = ttk.LabelFrame(
        screen,
        text="Connection Results",
        padding=t.S
    )

    results_section.pack(
        fill="both",
        expand=True,
        pady=(0, t.M)
    )

    output_frame = ttk.Frame(results_section)
    output_frame.pack(
        fill="both",
        expand=True
    )

    scrollbar = ttk.Scrollbar(
        output_frame,
        orient="vertical"
    )

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
        yscrollcommand=scrollbar.set
    )

    scrollbar.config(command=output_area.yview)

    output_area.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    # Fill the parent frame.
    screen.place(
        relwidth=1,
        relheight=1
    )


# =========================================================
# Output helpers
# =========================================================

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

    hr.set_hosts(results)

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

    # Read IP addresses.
    ips = [
        ip.strip()
        for ip in ip_entry.get().split(",")
        if ip.strip()
    ]

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

    scan_btn.config(state="disabled")
    stop_btn.config(state="normal")
    back_btn.config(state="disabled")
    home_btn.config(state="disabled")
    review_btn.config(state="disabled")

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

    append_output(message)

    status_label.config(text=status)

    scan_btn.config(state="normal")
    stop_btn.config(state="disabled")
    back_btn.config(state="normal")
    home_btn.config(state="normal")

    review_btn.config(
        state="normal" if tested > 0 else "disabled"
    )


# =========================================================
# Stop scan
# =========================================================

def stop_reliable_scan():
    """Request the background scan to stop."""

    if scan_thread is None or not scan_thread.is_alive():
        return

    stop_event.set()

    stop_btn.config(state="disabled")
    status_label.config(text="Stopping...")

    append_output(
        "Stopping scan after the current connection attempt..."
    )