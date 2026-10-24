from tkinter import ttk

from . import theme as t

screen=None
button_panel=None
reliable_scan_btn=None
fast_scan_btn=None


def initialize(add_to_frame):

    global screen, button_panel, reliable_scan_btn, fast_scan_btn

    screen = ttk.Frame(add_to_frame, style="App.TFrame")

    button_panel = ttk.Frame(screen, padding=t.XL)

    ttk.Label(button_panel, text="Scan the network", font=t.FONTS["title"]).pack(anchor="w")
    ttk.Label(button_panel, text="Fast scan uses masscan to find hosts with SSH (port 22) open.",
              style="Muted.TLabel").pack(anchor="w", pady=(t.XS, t.L))

    reliable_scan_btn = ttk.Button(button_panel, text="Reliable scan")
    fast_scan_btn     = ttk.Button(button_panel, text="Fast scan", style="Primary.TButton")

    reliable_scan_btn.pack(fill="x", pady=(0, t.S))
    fast_scan_btn.pack(fill="x")

    button_panel.place(relx=0.5, rely=0.5, anchor="center")
    screen.place(relwidth=1, relheight=1)
