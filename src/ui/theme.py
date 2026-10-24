"""
Design tokens and ttk style setup for Lab Master.

Every colour, font size and spacing value used by the UI lives here, so the
look of the whole app can be changed from one file.
Contrast ratios (WCAG 2.1) are noted next to each foreground colour.
"""
import tkinter as tk
from tkinter import ttk, font as tkfont


# ---------------------------------------------------------------- colours --
# One dark theme, matched to the project website (docs/index.html).
BG          = "#0e1117"   # window background
SURFACE     = "#161b25"   # cards
SURFACE_2   = "#1e2535"   # inputs, tiles, secondary buttons
SURFACE_3   = "#2a3446"   # hover
BORDER      = "#2f3a4f"   # card / input borders (decorative)

TEXT        = "#e6edf3"   # 14.6:1 on SURFACE, 16.0:1 on BG       (AAA)
TEXT_MUTED  = "#9aa8bc"   #  7.2:1 on SURFACE, 6.4:1 on SURFACE_2  (AA)
TEXT_DISABLED = "#7d8ba0" #  4.4:1 on SURFACE_2 (disabled text is exempt)

ACCENT      = "#1db954"   # primary action background
ACCENT_HOVER= "#22c55e"
ON_ACCENT   = "#0e1117"   #  7.3:1 on ACCENT                      (AAA)

DANGER      = "#b91c1c"   # destructive button background
DANGER_HOVER= "#dc2626"
ON_DANGER   = "#ffffff"   #  6.5:1 on DANGER                      (AA)
DANGER_TEXT = "#f87171"   #  6.2:1 on SURFACE (error messages)    (AA)

FOCUS       = "#60a5fa"   #  6.8:1 on SURFACE (focus ring, >= 3:1 needed)

# Host status: colour + glyph + word, so status never relies on colour alone.
STATUS = {
    #  key              glyph  label            colour     (contrast on SURFACE_2)
    "not_connected": ("○", "Not connected", "#9aa8bc"),   # 6.4:1
    "idle":          ("●", "Online",        "#60a5fa"),   # 6.0:1
    "running":       ("◐", "Running",       "#facc15"),   # 10.0:1
    "success":       ("✔", "Success",       "#4ade80"),   # 8.8:1
    "failed":        ("✖", "Failed",        "#f87171"),   # 5.5:1
    "offline":       ("⊘", "Offline",       "#fb923c"),   # 6.9:1
}

# ----------------------------------------------------------------- spacing --
# 8 px grid. XS is the only half step.
XS, S, M, L, XL = 4, 8, 16, 24, 32

# -------------------------------------------------------------------- type --
UI_FAMILIES   = ("Inter", "Segoe UI", "Ubuntu", "Cantarell", "DejaVu Sans", "Helvetica")
MONO_FAMILIES = ("JetBrains Mono", "Cascadia Mono", "Ubuntu Mono", "DejaVu Sans Mono", "Consolas", "Courier")

# Type scale in points (Tk positive sizes are points).
SIZE_CAPTION = 10
SIZE_BODY    = 11
SIZE_HEADING = 12
SIZE_TITLE   = 16

FONTS = {}


def _pick(families, root):
    available = set(tkfont.families(root))
    for family in families:
        if family in available:
            return family
    return "TkDefaultFont"


def _build_fonts(root):
    ui   = _pick(UI_FAMILIES, root)
    mono = _pick(MONO_FAMILIES, root)
    FONTS["caption"] = tkfont.Font(root, family=ui,   size=SIZE_CAPTION)
    FONTS["body"]    = tkfont.Font(root, family=ui,   size=SIZE_BODY)
    FONTS["strong"]  = tkfont.Font(root, family=ui,   size=SIZE_BODY,    weight="bold")
    FONTS["heading"] = tkfont.Font(root, family=ui,   size=SIZE_HEADING, weight="bold")
    FONTS["title"]   = tkfont.Font(root, family=ui,   size=SIZE_TITLE,   weight="bold")
    FONTS["mono"]    = tkfont.Font(root, family=mono, size=SIZE_BODY)

    # plain tk widgets (Text, Listbox, menus, messageboxes) follow the body font
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
        tkfont.nametofont(name).configure(family=ui, size=SIZE_BODY)


def apply(root):
    """Build fonts and configure every ttk style. Call once, right after tk.Tk()."""
    _build_fonts(root)
    root.configure(bg=BG)
    root.option_add("*TCombobox*Listbox.background", SURFACE_2)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)

    style = ttk.Style(root)
    style.theme_use("clam")       # clam is the only built-in theme that honours colours everywhere

    style.configure(".",
                    background=SURFACE, foreground=TEXT, font=FONTS["body"],
                    bordercolor=BORDER, darkcolor=SURFACE, lightcolor=SURFACE,
                    troughcolor=SURFACE_2, focuscolor=FOCUS,
                    selectbackground=FOCUS, selectforeground=BG,
                    insertcolor=TEXT)

    # ---- containers
    style.configure("App.TFrame",  background=BG)
    style.configure("TFrame",      background=SURFACE)
    style.configure("Card.TLabelframe", background=SURFACE, bordercolor=BORDER,
                    relief="solid", borderwidth=1, padding=(M, XS, M, M))
    style.configure("Card.TLabelframe.Label", background=SURFACE, foreground=TEXT,
                    font=FONTS["heading"])

    # ---- text
    style.configure("TLabel",          background=SURFACE, foreground=TEXT)
    style.configure("Muted.TLabel",    background=SURFACE, foreground=TEXT_MUTED, font=FONTS["caption"])
    style.configure("Error.TLabel",    background=SURFACE, foreground=DANGER_TEXT)
    style.configure("Title.TLabel",    background=BG,      foreground=TEXT, font=FONTS["title"])
    style.configure("AppMuted.TLabel", background=BG,      foreground=TEXT_MUTED, font=FONTS["caption"])

    # ---- buttons: secondary (default), primary, danger, ghost
    def button(name, bg, fg, hover, pressed, font=FONTS["body"]):
        style.configure(name, background=bg, foreground=fg, font=font,
                        bordercolor=BORDER, darkcolor=bg, lightcolor=bg,
                        focusthickness=2, focuscolor=FOCUS,
                        padding=(M, XS), relief="flat", anchor="center")
        style.map(name,
                  background=[("disabled", SURFACE_2), ("pressed", pressed), ("active", hover)],
                  foreground=[("disabled", TEXT_DISABLED)],
                  bordercolor=[("focus", FOCUS)],
                  darkcolor=[("pressed", pressed), ("active", hover)],
                  lightcolor=[("pressed", pressed), ("active", hover)])

    button("TButton",         SURFACE_2, TEXT,      SURFACE_3,    BORDER)
    button("Primary.TButton", ACCENT,    ON_ACCENT, ACCENT_HOVER, "#16a34a", FONTS["strong"])
    button("Danger.TButton",  DANGER,    ON_DANGER, DANGER_HOVER, "#991b1b")
    button("Ghost.TButton",   SURFACE,   TEXT_MUTED, SURFACE_2,   SURFACE_3)
    style.configure("Ghost.TButton", padding=(S, XS))
    style.configure("Tight.TButton", padding=(S, XS), width=0)

    # ---- inputs
    style.configure("TEntry", fieldbackground=SURFACE_2, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=SURFACE_2, darkcolor=SURFACE_2,
                    padding=(S, XS))
    style.map("TEntry",
              bordercolor=[("focus", FOCUS)],
              lightcolor=[("focus", FOCUS)],
              fieldbackground=[("disabled", SURFACE)])
    style.configure("Mono.TEntry", font=FONTS["mono"])

    style.configure("TCheckbutton", background=SURFACE, foreground=TEXT,
                    indicatorbackground=SURFACE_2, indicatorforeground=TEXT,
                    focuscolor=FOCUS, padding=(0, XS))
    style.map("TCheckbutton",
              background=[("active", SURFACE)],
              indicatorbackground=[("selected", ACCENT), ("active", SURFACE_3)],
              indicatorforeground=[("selected", ON_ACCENT)])

    # ---- status bar, progress, scrollbar, separators
    style.configure("Status.TFrame", background=SURFACE_2)
    style.configure("Status.TLabel", background=SURFACE_2, foreground=TEXT)
    style.configure("StatusMuted.TLabel", background=SURFACE_2, foreground=TEXT_MUTED, font=FONTS["caption"])
    style.configure("Horizontal.TProgressbar", troughcolor=SURFACE, background=ACCENT,
                    bordercolor=SURFACE_2, lightcolor=ACCENT, darkcolor=ACCENT, thickness=8)
    style.configure("Vertical.TScrollbar", background=SURFACE_2, troughcolor=SURFACE,
                    bordercolor=SURFACE, arrowcolor=TEXT_MUTED, lightcolor=SURFACE_2, darkcolor=SURFACE_2)
    style.map("Vertical.TScrollbar", background=[("active", SURFACE_3)])
    style.configure("TSeparator", background=BORDER)

    # ---- host tiles
    style.configure("Tile.TFrame", background=SURFACE_2, bordercolor=BORDER, relief="solid", borderwidth=1)
    style.configure("TileFocus.TFrame", background=SURFACE_2, bordercolor=FOCUS, relief="solid", borderwidth=2)
    style.configure("Tile.TLabel", background=SURFACE_2, foreground=TEXT)
    style.configure("TileMuted.TLabel", background=SURFACE_2, foreground=TEXT_MUTED, font=FONTS["caption"])
    style.configure("TileName.TLabel", background=SURFACE_2, foreground=TEXT, font=FONTS["strong"])
    for key, (_glyph, _label, colour) in STATUS.items():
        style.configure(f"Status_{key}.TLabel", background=SURFACE_2, foreground=colour, font=FONTS["strong"])

    return style
