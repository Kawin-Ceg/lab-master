import tkinter as tk
from tkinter import ttk
import threading
import subprocess

from . import theme as t

screen = None
label = None
text_box = None
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

default_command = "sudo -S masscan 192.168.136.0/24 -p22 -oL - -oJ ips.json"

output_count = 0


def initialize(add_to_frame):
    global screen, label, text_box, scan_btn, stop_btn, text_area
    global back_btn, home_btn, review_btn
    global status_label, progress_bar, target_label, output_count_label
    global output_count

    output_count = 0

    screen = ttk.Frame(
        add_to_frame,
        style="App.TFrame",
        padding=t.M
    )

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------
    header = ttk.Frame(screen)
    header.pack(fill="x", pady=(0, t.S))

    label = ttk.Label(
        header,
        text="Fast Scan",
        font=t.FONTS["title"]
    )
    label.pack(anchor="w")

    ttk.Label(
        header,
        text="Rapidly discover machines with SSH access.",
        style="Muted.TLabel"
    ).pack(anchor="w", pady=(t.XS, 0))

    # ---------------------------------------------------------
    # Three-step workflow
    # ---------------------------------------------------------
    workflow = ttk.Frame(screen)
    workflow.pack(fill="x", pady=(0, t.S))

    steps = [
        ("01", "Scan"),
        ("02", "Review Hosts"),
        ("03", "Dashboard")
    ]

    for index, (number, title) in enumerate(steps):
        step = ttk.Frame(workflow)
        step.pack(side="left", fill="x", expand=True)

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
        ).pack(anchor="w", pady=(t.XS, 0))

        if index < len(steps) - 1:
            ttk.Label(
                workflow,
                text="→",
                style="Muted.TLabel"
            ).pack(side="left", padx=t.XS)

    # ---------------------------------------------------------
    # Scan configuration
    # ---------------------------------------------------------
    command_section = ttk.LabelFrame(
        screen,
        text="Scan Configuration",
        padding=t.S
    )
    command_section.pack(fill="x", pady=(0, t.S))

    ttk.Label(
        command_section,
        text="Command",
        font=t.FONTS["body"]
    ).pack(anchor="w", pady=(0, t.XS))

    command_row = ttk.Frame(command_section)
    command_row.pack(fill="x")

    text_box = ttk.Entry(
        command_row,
        style="Mono.TEntry",
        font=t.FONTS["mono"]
    )
    text_box.insert(0, default_command)
    text_box.pack(side="left", fill="x", expand=True)

    scan_btn = ttk.Button(
        command_row,
        text="▶ Scan",
        style="Primary.TButton",
        state="normal"
    )
    scan_btn.pack(side="left", padx=(t.S, 0))

    stop_btn = ttk.Button(
        command_row,
        text="■ Stop",
        state="disabled"
    )
    stop_btn.pack(side="left", padx=(t.XS, 0))

    ttk.Label(
        command_section,
        text="Only scan networks you are authorized to access.",
        style="Muted.TLabel"
    ).pack(anchor="w", pady=(t.XS, 0))

    # ---------------------------------------------------------
    # Scan progress
    # ---------------------------------------------------------
    progress_section = ttk.LabelFrame(
        screen,
        text="Scan Progress",
        padding=t.S
    )
    progress_section.pack(fill="x", pady=(0, t.S))

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
    status_label.pack(side="left", padx=(t.XS, 0))

    target_label = ttk.Label(
        progress_section,
        text="Target: Not started",
        style="Muted.TLabel"
    )
    target_label.pack(anchor="w", pady=(t.XS, 0))

    progress_bar = ttk.Progressbar(
        progress_section,
        mode="indeterminate"
    )
    progress_bar.pack(fill="x", pady=(t.XS, 0))

    output_count_label = ttk.Label(
        progress_section,
        text="Output lines: 0",
        style="Muted.TLabel"
    )
    output_count_label.pack(anchor="w", pady=(t.XS, 0))

        # ---------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------
    nav = ttk.Frame(screen)
    nav.pack(side="bottom", fill="x", pady=(t.S, 0))

    back_btn = ttk.Button(
        nav,
        text="← Back"
    )
    back_btn.pack(side="left")

    home_btn = ttk.Button(
        nav,
        text="⌂ Home"
    )
    home_btn.pack(side="left", padx=(t.S, 0))

    review_btn = ttk.Button(
        nav,
        text="Review Hosts →",
        style="Primary.TButton",
        state="disabled"
    )
    review_btn.pack(side="right")

    # ---------------------------------------------------------
    # Scan output
    # The output area expands into the space left over.
    # ---------------------------------------------------------
    output_section = ttk.LabelFrame(
        screen,
        text="Scan Output",
        padding=t.XS
    )
    output_section.pack(
        side="top",
        fill="both",
        expand=True,
        pady=(0, t.XS)
    )

    output_frame = ttk.Frame(output_section)
    output_frame.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(
        output_frame,
        orient="vertical"
    )

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
        yscrollcommand=scrollbar.set
    )

    scrollbar.config(command=text_area.yview)

    text_area.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Fill the parent window.
    screen.place(
        relwidth=1,
        relheight=1
    )


# -------------------------------------------------------------
# Progress helpers
# These can be called from stable.py on the Tkinter main thread.
# -------------------------------------------------------------
def set_status(status, running=False, target=None):
    if status_label is not None:
        status_label.config(text=status)

    if running:
        progress_bar.start(10)
    else:
        progress_bar.stop()

    if target is not None:
        target_label.config(text=f"Target: {target}")


def reset_output_count():
    global output_count

    output_count = 0

    if output_count_label is not None:
        output_count_label.config(text="Output lines: 0")


def increment_output_count():
    global output_count

    output_count += 1

    if output_count_label is not None:
        output_count_label.config(
            text=f"Output lines: {output_count}"
        )
