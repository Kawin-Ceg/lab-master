from tkinter import ttk

from . import theme as t

screen = None
button_panel = None
start_btn = None


def initialize(add_to_parent_frame):
    global screen, button_panel, start_btn

    screen = ttk.Frame(
        add_to_parent_frame,
        style="App.TFrame"
    )

    button_panel = ttk.Frame(
        screen,
        padding=t.XL
    )

    # Application title
    ttk.Label(
        button_panel,
        text="Lab Master",
        font=t.FONTS["title"]
    ).pack(anchor="w")

    ttk.Label(
        button_panel,
        text="Linux Lab Management & Discovery",
        style="Muted.TLabel"
    ).pack(anchor="w", pady=(t.XS, t.M))

    ttk.Label(
        button_panel,
        text="Discover and manage your lab machines from one place.",
        wraplength=540
    ).pack(anchor="w", pady=(0, t.L))

    # Three-step workflow
    workflow = ttk.LabelFrame(
        button_panel,
        text="Your workflow",
        padding=t.M
    )
    workflow.pack(fill="x", pady=(0, t.L))

    steps = ttk.Frame(workflow)
    steps.pack(fill="x")

    step_data = [
        ("01", "Scan", "Discover machines"),
        ("02", "Review Hosts", "Check discovered hosts"),
        ("03", "Dashboard", "Manage your machines")
    ]

    for index, (number, title, description) in enumerate(step_data):
        step = ttk.Frame(steps)
        step.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0 if index == 0 else t.XS, 0)
        )

        ttk.Label(
            step,
            text=number,
            font=t.FONTS["heading"],
            style="Muted.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            step,
            text=title,
            font=t.FONTS["heading"]
        ).pack(anchor="w", pady=(t.XS, 0))

        ttk.Label(
            step,
            text=description,
            style="Muted.TLabel",
            wraplength=150
        ).pack(anchor="w", pady=(t.XS, 0))

        # Connector between steps
        if index < len(step_data) - 1:
            ttk.Label(
                steps,
                text="→",
                style="Muted.TLabel"
            ).pack(side="left", padx=t.XS)

    # Feature section
    ttk.Label(
        button_panel,
        text="What you can do",
        font=t.FONTS["heading"]
    ).pack(anchor="w", pady=(0, t.S))

    features = ttk.Frame(button_panel)
    features.pack(fill="x", pady=(0, t.L))

    feature_data = [
        (
            "Machine Discovery",
            "Find machines on your authorized network."
        ),
        (
            "SSH Connectivity",
            "Test remote access to discovered machines."
        ),
        (
            "Centralized Dashboard",
            "View machine status and access host actions."
        )
    ]

    for index, (title, description) in enumerate(feature_data):
        feature = ttk.Frame(
            features,
            padding=(t.S, t.S)
        )
        feature.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0 if index == 0 else t.XS, 0)
        )

        ttk.Label(
            feature,
            text=title,
            font=t.FONTS["body"]
        ).pack(anchor="w")

        ttk.Label(
            feature,
            text=description,
            style="Muted.TLabel",
            wraplength=155,
            justify="left"
        ).pack(anchor="w", pady=(t.XS, 0))

    # Primary action
    start_btn = ttk.Button(
        button_panel,
        text="Get Started  →",
        style="Primary.TButton"
    )
    start_btn.pack(fill="x", pady=(0, t.M))

    # Readiness indicator
    ttk.Label(
        button_panel,
        text="● Ready to discover machines",
        style="Muted.TLabel"
    ).pack(anchor="w")

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
