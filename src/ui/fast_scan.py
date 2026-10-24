import tkinter as tk
from tkinter import ttk

from . import theme as t


screen   = None
label    = None
text_box = None
text_area= None
scan_btn = None
stop_btn = None


default_command =  "sudo -S masscan 192.168.136.0/24 -p22 -oL - -oJ ips.json"

def initialize(add_to_frame):
    global screen, label, text_box, scan_btn, stop_btn, text_area

    screen = ttk.Frame(add_to_frame, padding=t.M)

    label = ttk.Label(screen, text="Fast scan", font=t.FONTS["title"])

    row = ttk.Frame(screen)
    text_box = ttk.Entry(row, style="Mono.TEntry", font=t.FONTS["mono"])
    text_box.insert(0, default_command)
    scan_btn = ttk.Button(row, text="▶ Scan", style="Primary.TButton")

    text_area = tk.Text(screen, bg=t.SURFACE_2, fg=t.TEXT, insertbackground=t.TEXT,
                        font=t.FONTS["mono"], relief="flat", padx=t.S, pady=t.S,
                        highlightthickness=1, highlightbackground=t.BORDER, highlightcolor=t.FOCUS)

    label.pack(side="top", anchor="w", pady=(0, t.S))
    text_box.pack(side="left", fill="x", expand=True)
    scan_btn.pack(side="left", padx=(t.S, 0))
    row.pack(side="top", fill="x")
    text_area.pack(side="top", fill="both", expand=True, pady=(t.M, 0))

    screen.place(relwidth=1, relheight=1)
