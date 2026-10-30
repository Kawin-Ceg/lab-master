from tkinter import ttk

from . import theme as t
from . import widgets as w

screen = None
button_panel = None

reliable_scan_btn = None
fast_scan_btn = None
open_list_btn = None
back_btn = None
home_btn = None          # same as back_btn here (kept for stable.py)

# (title, best when, details, button text, tooltip)
OPTIONS = {
    "fast": (
        "Search a network",
        "Best when you don't know the IP addresses.",
        "Finds every machine with SSH (port 22) in a range such as 192.168.1.0/24.\n"
        "Needs masscan and sudo on this computer.",
        "Fast scan  →",
        "Sweep a network range for machines that accept SSH",
    ),
    "reliable": (
        "Test a list of IP addresses",
        "Best when you know which machines to manage.",
        "Logs in to each machine with your SSH username and password,\n"
        "so you see which logins work before you connect.",
        "Reliable scan  →",
        "Try to log in to each IP you type, and report which ones work",
    ),
    "open": (
        "Open a saved IP list",
        "Best when you already have the list as a file.",
        "Load a .json or .txt file (one IP per line) and go straight to Review.",
        "Open list…",
        "Skip scanning: load IP addresses from a .json or .txt file",
    ),
}


def _option(parent, key, primary=False):
    """A clickable card: title, when to use it, details and a button."""
    title, best, details, btn_text, tip = OPTIONS[key]

    card = ttk.Frame(parent, style="Option.TFrame", padding=(t.M, t.S + t.XS), cursor="hand2")
    card.pack(fill="x", pady=(0, t.S))
    card.columnconfigure(0, weight=1)

    ttk.Label(card, text=title, style="OptionTitle.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(card, text=best, style="TLabel").grid(row=1, column=0, sticky="w", pady=(t.XS, 0))
    ttk.Label(card, text=details, style="Muted.TLabel", justify="left").grid(
        row=2, column=0, sticky="w", pady=(t.XS, 0))

    btn = w.button(card, btn_text, None, tip, style="Primary.TButton" if primary else "TButton")
    btn.grid(row=0, column=1, rowspan=3, sticky="e", padx=(t.M, 0))

    # Click anywhere on the card = press its button; highlight on hover.
    def press(_e=None):
        if btn.instate(["!disabled"]):
            btn.invoke()
    for widget in [card] + card.winfo_children():
        if widget is not btn:
            widget.bind("<Button-1>", press)
    card.bind("<Enter>", lambda e: card.configure(style="OptionHover.TFrame"))
    card.bind("<Leave>", lambda e: card.configure(style="Option.TFrame"))
    return btn


def initialize(add_to_frame):
    global screen, button_panel
    global reliable_scan_btn, fast_scan_btn, open_list_btn
    global back_btn, home_btn

    screen = ttk.Frame(
        add_to_frame,
        style="App.TFrame"
    )

    button_panel = ttk.Frame(
        screen,
        padding=(t.XL, t.L)
    )

    # Where am I in the flow
    w.step_indicator(button_panel, current=1).pack(anchor="center", pady=(0, t.L))

    # Heading
    ttk.Label(
        button_panel,
        text="Find your lab machines",
        style="Big.TLabel"
    ).pack(anchor="center")

    ttk.Label(
        button_panel,
        text="Choose how Lab Master should find the machines you want to manage.",
        style="Muted.TLabel"
    ).pack(anchor="center", pady=(t.XS, t.L))

    # Methods, most common first
    methods = ttk.Frame(button_panel)
    methods.pack(fill="x")
    fast_scan_btn = _option(methods, "fast", primary=True)
    reliable_scan_btn = _option(methods, "reliable")
    open_list_btn = _option(methods, "open")

    # Guidance
    ttk.Label(
        button_panel,
        text="Only scan networks you are authorized to access.",
        style="Muted.TLabel"
    ).pack(anchor="center", pady=(t.S, t.M))

    # Navigation (Back and Home both lead to the start screen here)
    nav = ttk.Frame(button_panel)
    nav.pack(fill="x")
    back_btn = w.button(nav, "←  Back", None, "Return to the start screen")
    back_btn.pack(side="left")
    home_btn = back_btn

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
