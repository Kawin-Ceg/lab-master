from tkinter import ttk

from . import theme as t

screen=None
button_panel=None
over_the_network_btn=None
row_col_btn=None


def initialize(add_to_parent_frame):

    global screen,  button_panel, over_the_network_btn, row_col_btn
    screen = ttk.Frame(add_to_parent_frame, style="App.TFrame")

    button_panel = ttk.Frame(screen, padding=t.XL)

    ttk.Label(button_panel, text="Lab Master", font=t.FONTS["title"]).pack(anchor="w")
    ttk.Label(button_panel, text="How do you want to find the lab machines?",
              style="Muted.TLabel").pack(anchor="w", pady=(t.XS, t.L))

    over_the_network_btn = ttk.Button(button_panel, text="Scan the network", style="Primary.TButton")
    row_col_btn          = ttk.Button(button_panel, text="Row / column layout")

    over_the_network_btn.pack(fill="x", pady=(0, t.S))
    row_col_btn.pack(fill="x")

    button_panel.place(relx=0.5, rely=0.5, anchor="center")
    screen.place(relwidth=1, relheight=1)
