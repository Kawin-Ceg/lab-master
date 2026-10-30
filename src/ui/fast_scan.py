import tkinter as tk
from tkinter import ttk
import ipaddress
import re
import threading

from . import theme as t
from . import widgets as w

screen = None
label = None
text_box = None          # the masscan command actually run (stable.py reads it)
text_area = None
scan_btn = None
stop_btn = None
scan_process = None
scan_thread = None
stop_event = threading.Event()

back_btn = None
home_btn = None
review_btn = None

status_label = None
progress_bar = None
target_label = None
output_count_label = None
found_label = None

range_var = None
rate_var = None
advanced_var = None
range_hint = None
command_row = None

DEFAULT_RANGE = "192.168.136.0/24"
DEFAULT_RATE = "1000"
default_command = "sudo -S masscan 192.168.136.0/24 -p22 --rate 1000 -oL - -oJ ips.json"

output_count = 0
found_hosts = set()
_running = False
_command_edited = False          # user typed in the advanced command box

FOUND_RE = re.compile(r"open port 22/tcp on (\S+)", re.I)


# -------------------------------------------------------------
# Network range validation
# -------------------------------------------------------------
def parse_range(text):
    """
    Accepts CIDR blocks, single IPs and a-b ranges, separated by commas or spaces.
    Returns (number_of_addresses, error_message).
    """
    parts = [p for p in re.split(r"[,\s]+", text.strip()) if p]
    if not parts:
        return 0, "Enter a network range, for example 192.168.1.0/24."
    total = 0
    for part in parts:
        try:
            if "-" in part:
                first, last = (ipaddress.ip_address(x) for x in part.split("-", 1))
                if int(last) < int(first):
                    return 0, f"“{part}”: the end address is before the start."
                total += int(last) - int(first) + 1
            else:
                total += ipaddress.ip_network(part, strict=False).num_addresses
        except ValueError:
            return 0, f"“{part}” is not a valid IP, range or network (e.g. 192.168.1.0/24)."
    return total, ""


def build_command():
    rng = " ".join(p for p in re.split(r"[,\s]+", range_var.get().strip()) if p)
    rate = rate_var.get().strip() or DEFAULT_RATE
    return f"sudo -S masscan {rng} -p22 --rate {rate} -oL - -oJ ips.json"


def _on_settings_change(*_):
    """Validate the range, update the hint and (unless edited by hand) the command."""
    count, error = parse_range(range_var.get())
    rate_ok = rate_var.get().strip().isdigit() and int(rate_var.get()) > 0
    if error:
        range_hint.configure(text=error, style="Error.TLabel")
    elif not rate_ok:
        range_hint.configure(text="Speed must be a whole number of packets per second.", style="Error.TLabel")
    else:
        range_hint.configure(text=f"{count:,} address{'es' if count != 1 else ''} will be checked for SSH (port 22).",
                             style="Muted.TLabel")
    if not _command_edited:
        text_box.delete(0, "end")
        text_box.insert(0, build_command())
    refresh_scan_button()


def settings_valid():
    if advanced_var.get() and _command_edited:
        return bool(text_box.get().strip())
    count, error = parse_range(range_var.get())
    rate_ok = rate_var.get().strip().isdigit() and int(rate_var.get()) > 0
    return not error and rate_ok


def refresh_scan_button():
    """Start is only enabled when the settings are valid and nothing is running."""
    if scan_btn is not None:
        scan_btn.state(["!disabled"] if settings_valid() and not _running else ["disabled"])


def _toggle_advanced():
    global _command_edited
    if advanced_var.get():
        command_row.grid()
    else:
        command_row.grid_remove()
        _command_edited = False          # back to the simple form: rebuild the command
        _on_settings_change()


def _on_command_typed(_e=None):
    global _command_edited
    _command_edited = text_box.get().strip() != build_command()
    refresh_scan_button()


def initialize(add_to_frame):
    global screen, label, text_box, scan_btn, stop_btn, text_area
    global back_btn, home_btn, review_btn
    global status_label, progress_bar, target_label, output_count_label, found_label
    global range_var, rate_var, advanced_var, range_hint, command_row
    global output_count

    output_count = 0
    range_var = tk.StringVar(master=add_to_frame, value=DEFAULT_RANGE)
    rate_var = tk.StringVar(master=add_to_frame, value=DEFAULT_RATE)
    advanced_var = tk.BooleanVar(master=add_to_frame, value=False)

    screen = ttk.Frame(
        add_to_frame,
        style="App.TFrame",
        padding=t.M
    )

    # ---------------------------------------------------------
    # Header + where am I
    # ---------------------------------------------------------
    header = ttk.Frame(screen, padding=(t.S, t.S))
    header.pack(fill="x", pady=(0, t.S))

    label = ttk.Label(header, text="Fast scan", style="Big.TLabel")
    label.pack(side="left")
    ttk.Label(header, text="Search a network for machines that accept SSH.",
              style="Muted.TLabel").pack(side="left", padx=(t.M, 0), pady=(t.XS, 0))
    w.step_indicator(header, current=1).pack(side="right")

    # ---------------------------------------------------------
    # Navigation (packed before the expanding output)
    # ---------------------------------------------------------
    nav = ttk.Frame(screen)
    nav.pack(side="bottom", fill="x", pady=(t.S, 0))

    back_btn = w.button(nav, "←  Back", None, "Choose a different way to find machines")
    back_btn.pack(side="left")
    home_btn = w.button(nav, "⌂  Home", None, "Return to the start screen")
    home_btn.pack(side="left", padx=(t.S, 0))
    review_btn = w.button(nav, "Review hosts  →", None,
                          "Check the machines this scan found, then open the dashboard",
                          style="Primary.TButton")
    review_btn.state(["disabled"])
    review_btn.pack(side="right")

    # ---------------------------------------------------------
    # Scan settings
    # ---------------------------------------------------------
    settings_card = w.card(screen, "Scan settings")
    settings_card.pack(fill="x", pady=(0, t.S))
    settings_card.columnconfigure(1, weight=1)

    ttk.Label(settings_card, text="Network range").grid(row=0, column=0, sticky="w", pady=t.XS)
    range_entry = ttk.Entry(settings_card, textvariable=range_var, style="Mono.TEntry", font=t.FONTS["mono"])
    range_entry.grid(row=0, column=1, sticky="ew", padx=(t.S, t.M), pady=t.XS)
    w.Tooltip(range_entry, "Which addresses to scan. Examples:\n"
                           "192.168.1.0/24  (192.168.1.0 – 192.168.1.255)\n"
                           "10.0.0.5-10.0.0.60  ·  several, separated by commas", shortcut="Enter starts the scan")

    ttk.Label(settings_card, text="Speed").grid(row=0, column=2, sticky="w", pady=t.XS)
    rate_box = ttk.Spinbox(settings_card, from_=100, to=100000, increment=500, width=8, textvariable=rate_var)
    rate_box.grid(row=0, column=3, sticky="w", padx=(t.S, t.XS), pady=t.XS)
    ttk.Label(settings_card, text="packets/s", style="Muted.TLabel").grid(row=0, column=4, sticky="w")
    w.Tooltip(rate_box, "How fast masscan sends probes. Lower is gentler on the lab network;\n"
                        "1000 is a safe default.")

    range_hint = ttk.Label(settings_card, style="Muted.TLabel")
    range_hint.grid(row=1, column=1, columnspan=4, sticky="w", padx=(t.S, 0))

    buttons = ttk.Frame(settings_card)
    buttons.grid(row=2, column=0, columnspan=5, sticky="ew", pady=(t.S, 0))
    scan_btn = w.button(buttons, "▶  Start scan", None,
                        "Run masscan. You will be asked for this computer's sudo password.",
                        style="Primary.TButton")
    scan_btn.pack(side="left")
    stop_btn = w.button(buttons, "■  Stop", None, "Stop the running scan")
    stop_btn.state(["disabled"])
    stop_btn.pack(side="left", padx=(t.S, 0))
    adv = ttk.Checkbutton(buttons, text="Show command (advanced)", variable=advanced_var, command=_toggle_advanced)
    adv.pack(side="left", padx=(t.L, 0))
    w.Tooltip(adv, "See or edit the exact masscan command that will run")
    ttk.Label(buttons, text="Only scan networks you are authorized to access.",
              style="Muted.TLabel").pack(side="right")

    command_row = ttk.Frame(settings_card)
    command_row.grid(row=3, column=0, columnspan=5, sticky="ew", pady=(t.S, 0))
    ttk.Label(command_row, text="Command").pack(side="left")
    text_box = ttk.Entry(command_row, style="Mono.TEntry", font=t.FONTS["mono"])
    text_box.pack(side="left", fill="x", expand=True, padx=(t.S, 0))
    text_box.bind("<KeyRelease>", _on_command_typed)
    w.Tooltip(text_box, "Runs inside ~/Lab_master/scans; keep “-oJ ips.json” so the\n"
                        "Review screen can read the results.")
    command_row.grid_remove()

    range_var.trace_add("write", _on_settings_change)
    rate_var.trace_add("write", _on_settings_change)
    range_entry.bind("<Return>", lambda e: scan_btn.invoke() if scan_btn.instate(["!disabled"]) else None)

    # ---------------------------------------------------------
    # Progress
    # ---------------------------------------------------------
    progress_card = w.card(screen, "Progress")
    progress_card.pack(fill="x", pady=(0, t.S))

    status_row = ttk.Frame(progress_card)
    status_row.pack(fill="x")
    ttk.Label(status_row, text="Status:").pack(side="left")
    status_label = ttk.Label(status_row, text="Ready", style="Muted.TLabel")
    status_label.pack(side="left", padx=(t.XS, 0))
    found_label = ttk.Label(status_row, text="Hosts found: 0", style="TLabel")
    found_label.pack(side="left", padx=(t.L, 0))
    output_count_label = ttk.Label(status_row, text="Output lines: 0", style="Muted.TLabel")
    output_count_label.pack(side="left", padx=(t.L, 0))

    target_label = ttk.Label(progress_card, text="Target: not started", style="Muted.TLabel")
    target_label.pack(anchor="w", pady=(t.XS, 0))

    progress_bar = ttk.Progressbar(progress_card, mode="determinate", value=0)
    progress_bar.pack(fill="x", pady=(t.XS, 0))

    # ---------------------------------------------------------
    # Output (expands into the space that is left)
    # ---------------------------------------------------------
    output_section = w.card(screen, "Scan output")
    output_section.pack(side="top", fill="both", expand=True)

    output_frame = ttk.Frame(output_section)
    output_frame.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(output_frame, orient="vertical")
    text_area = tk.Text(
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
        wrap="none",
        height=4,
        yscrollcommand=scrollbar.set
    )
    t.on_change(lambda: _recolour_text(text_area))
    scrollbar.config(command=text_area.yview)
    text_area.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    _on_settings_change()

    # Fill the parent window.
    screen.place(relwidth=1, relheight=1)


def _recolour_text(widget):
    """tk.Text is not a ttk widget: repaint it after a light/dark switch."""
    widget.configure(bg=t.SURFACE_2, fg=t.TEXT, insertbackground=t.TEXT,
                     highlightbackground=t.BORDER, highlightcolor=t.FOCUS)


# -------------------------------------------------------------
# Progress helpers
# These can be called from stable.py on the Tkinter main thread.
# -------------------------------------------------------------
def set_status(status, running=False, target=None):
    global _running
    _running = running
    if status_label is not None:
        status_label.config(text=status)

    if running:
        progress_bar.configure(mode="indeterminate")
        progress_bar.start(10)
    else:
        progress_bar.stop()
        progress_bar.configure(mode="determinate", value=0)

    if target is not None:
        target_label.config(text=f"Target: {target}")
    refresh_scan_button()


def reset_output_count():
    global output_count
    output_count = 0
    found_hosts.clear()
    if output_count_label is not None:
        output_count_label.config(text="Output lines: 0")
        found_label.config(text="Hosts found: 0")


def increment_output_count(line=""):
    """Count output lines, and hosts reported with SSH open."""
    global output_count
    output_count += 1
    if output_count_label is not None:
        output_count_label.config(text=f"Output lines: {output_count}")
    match = FOUND_RE.search(line or "")
    if match:
        found_hosts.add(match.group(1))
        found_label.config(text=f"Hosts found: {len(found_hosts)}")


def set_review_count(found):
    """Enable the Review button and say how many hosts it will show."""
    if found:
        review_btn.configure(text=f"Review {found} host{'s' if found != 1 else ''}  →")
        review_btn.state(["!disabled"])
    else:
        review_btn.configure(text="Review hosts  →")
        review_btn.state(["disabled"])
