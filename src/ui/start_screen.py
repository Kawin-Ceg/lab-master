from tkinter import ttk
from tkinter import font as tkfont

from . import theme as t

screen = None
button_panel = None
start_btn = None

# (number, title, what happens in this step)
WORKFLOW = [
    ("01", "Scan",
     "Find the lab machines: sweep a network for SSH, or test a list of IPs."),
    ("02", "Review hosts",
     "See which machines answered and pick the ones to manage."),
    ("03", "Dashboard",
     "Connect once and work on every selected machine together."),
]

# (title, what you can do with it)
FEATURES = [
    ("Discover machines",
     "Fast scan sweeps a network; Reliable scan tests a list of IPs with your login."),
    ("Run commands everywhere",
     "Run one command on every machine at once and see which succeeded or failed."),
    ("Manage sessions and users",
     "Message, lock or shut down machines; lock, unlock or delete users and reset passwords."),
    ("Move files",
     "Upload a file to every machine, or collect files and folders from each one."),
]


def _styles():
    style = ttk.Style()
    style.configure("StartTitle.TLabel", background=t.SURFACE, foreground=t.TEXT, font=_title_font)
    style.configure("StartSection.TLabel", background=t.SURFACE, foreground=t.TEXT, font=t.FONTS["heading"])
    style.configure("StartNumber.TLabel", background=t.SURFACE, foreground=t.FOCUS, font=t.FONTS["heading"])
    style.configure("StartItem.TLabel", background=t.SURFACE, foreground=t.TEXT, font=t.FONTS["strong"])


def _row(parent, marker, title, text, marker_style):
    """One list row: marker on the left, title and description stacked on the right."""
    row = ttk.Frame(parent)
    row.pack(fill="x", pady=(0, t.XS))
    row.columnconfigure(1, weight=1)
    ttk.Label(row, text=marker, style=marker_style, width=3, anchor="w").grid(
        row=0, column=0, rowspan=2, sticky="nw", padx=(0, t.S))
    ttk.Label(row, text=title, style="StartItem.TLabel").grid(row=0, column=1, sticky="w")
    ttk.Label(row, text=text, style="Muted.TLabel", wraplength=t.px(600), justify="left").grid(
        row=1, column=1, sticky="w")
    return row


def initialize(add_to_parent_frame):
    global screen, button_panel, start_btn, _title_font

    _title_font = tkfont.Font(family=t.FONTS["title"].actual("family"), size=26, weight="bold")
    _styles()
    t.on_change(_styles)

    screen = ttk.Frame(
        add_to_parent_frame,
        style="App.TFrame"
    )

    button_panel = ttk.Frame(
        screen,
        padding=(t.XL, t.M)
    )

    # 1. Title, centred
    ttk.Label(
        button_panel,
        text="Lab Master",
        style="StartTitle.TLabel"
    ).pack(anchor="center")

    # 2. One-line description, centred
    ttk.Label(
        button_panel,
        text="Manage every Linux machine in your lab from one place.",
        style="Muted.TLabel"
    ).pack(anchor="center", pady=(t.XS, t.M))

    # 3. Workflow, top to bottom
    ttk.Label(button_panel, text="Your workflow", style="StartSection.TLabel").pack(anchor="w", pady=(0, t.S))
    workflow = ttk.Frame(button_panel)
    workflow.pack(fill="x")
    for number, title, text in WORKFLOW:
        _row(workflow, number, title, text, "StartNumber.TLabel")

    ttk.Separator(button_panel).pack(fill="x", pady=(t.S, t.S))

    # 4. What you can do, top to bottom
    ttk.Label(button_panel, text="What you can do", style="StartSection.TLabel").pack(anchor="w", pady=(0, t.S))
    features = ttk.Frame(button_panel)
    features.pack(fill="x")
    for title, text in FEATURES:
        _row(features, "✔", title, text, "StartNumber.TLabel")

    # 5. Primary action, centred
    start_btn = ttk.Button(
        button_panel,
        text="Get Started  →",
        style="Primary.TButton",
        width=24
    )
    start_btn.pack(anchor="center", pady=(t.M, 0), ipady=t.XS)

    # Centre the content
    button_panel.place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )

    screen.place(
        relwidth=1,
        relheight=1
    )
