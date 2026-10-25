from tkinter import ttk

from . import theme as t

screen = None
button_panel = None

reliable_scan_btn = None
fast_scan_btn = None
back_btn = None
home_btn = None


def initialize(add_to_frame):
    global screen, button_panel
    global reliable_scan_btn, fast_scan_btn
    global back_btn, home_btn

    screen = ttk.Frame(
        add_to_frame,
        style="App.TFrame"
    )

    button_panel = ttk.Frame(
        screen,
        padding=t.XL
    )

    # Workflow indicator
    workflow = ttk.Frame(button_panel)
    workflow.pack(fill="x", pady=(0, t.L))

    steps = [
        ("01", "Scan"),
        ("02", "Review Hosts"),
        ("03", "Dashboard")
    ]

    for index, (number, title) in enumerate(steps):
        step = ttk.Frame(workflow)
        step.pack(side="left", fill="x", expand=True)

        current = index == 0

        ttk.Label(
            step,
            text=number,
            font=t.FONTS["heading"],
            style="TLabel" if current else "Muted.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            step,
            text=title,
            font=t.FONTS["body"] if current else t.FONTS["caption"],
            style="TLabel" if current else "Muted.TLabel"
        ).pack(anchor="w", pady=(t.XS, 0))

        if index < len(steps) - 1:
            ttk.Label(
                workflow,
                text="→",
                style="Muted.TLabel"
            ).pack(side="left", padx=t.XS)

    # Heading
    ttk.Label(
        button_panel,
        text="Discover Lab Machines",
        font=t.FONTS["title"]
    ).pack(anchor="w")

    ttk.Label(
        button_panel,
        text="Step 1 of 3 · Choose how to discover your machines.",
        style="Muted.TLabel",
        wraplength=540
    ).pack(anchor="w", pady=(t.XS, t.L))

    # Scanning methods
    methods = ttk.Frame(button_panel)
    methods.pack(fill="x", pady=(0, t.M))

    # Reliable Scan card
    reliable_card = ttk.LabelFrame(
        methods,
        text="Reliable Scan",
        padding=t.M
    )
    reliable_card.pack(fill="x", pady=(0, t.M))

    ttk.Label(
        reliable_card,
        text="Controlled discovery",
        font=t.FONTS["heading"]
    ).pack(anchor="w")

    ttk.Label(
        reliable_card,
        text=(
            "Use Lab Master's reliable discovery method "
            "to check machines through the existing workflow."
        ),
        style="Muted.TLabel",
        wraplength=520,
        justify="left"
    ).pack(anchor="w", pady=(t.XS, t.M))

    reliable_scan_btn = ttk.Button(
        reliable_card,
        text="Choose Reliable Scan  →"
    )
    reliable_scan_btn.pack(anchor="e")

    # Fast Scan card
    fast_card = ttk.LabelFrame(
        methods,
        text="Fast Scan",
        padding=t.M
    )
    fast_card.pack(fill="x")

    ttk.Label(
        fast_card,
        text="Rapid network discovery",
        font=t.FONTS["heading"]
    ).pack(anchor="w")

    ttk.Label(
        fast_card,
        text=(
            "Use Masscan to rapidly discover hosts with "
            "SSH on port 22 across the configured network."
        ),
        style="Muted.TLabel",
        wraplength=520,
        justify="left"
    ).pack(anchor="w", pady=(t.XS, t.M))

    fast_scan_btn = ttk.Button(
        fast_card,
        text="Choose Fast Scan  →",
        style="Primary.TButton"
    )
    fast_scan_btn.pack(anchor="e")

    # Guidance
    ttk.Label(
        button_panel,
        text="Only scan networks you are authorized to access.",
        style="Muted.TLabel",
        wraplength=540
    ).pack(anchor="w", pady=(t.M, t.L))

    # Navigation
    nav = ttk.Frame(button_panel)

    back_btn = ttk.Button(
        nav,
        text="← Back"
    )

    home_btn = ttk.Button(
        nav,
        text="⌂ Home"
    )

    back_btn.pack(side="left")
    home_btn.pack(side="right")

    nav.pack(fill="x")

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