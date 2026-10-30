"""
Design tokens and ttk style setup for Lab Master.

Every colour, font size and spacing value used by the UI lives here, so the
look of the whole app can be changed from one file. There are two palettes
(dark and light) that can be switched while the app runs; widgets that draw
colours themselves register with on_change() to repaint.
Contrast ratios (WCAG 2.1) are noted next to each foreground colour.
"""
import sys
from tkinter import ttk, font as tkfont


# --------------------------------------------------------------- palettes --
PALETTES = {
    "dark": {                         # matched to the project website (docs/index.html)
        "BG":            "#0e1117",   # window background
        "SURFACE":       "#161b25",   # cards
        "SURFACE_2":     "#1e2535",   # inputs, tiles, secondary buttons
        "SURFACE_3":     "#2a3446",   # hover
        "BORDER":        "#2f3a4f",   # card / input borders (decorative)
        "TEXT":          "#e6edf3",   # 14.6:1 on SURFACE, 16.0:1 on BG       (AAA)
        "TEXT_MUTED":    "#9aa8bc",   #  7.2:1 on SURFACE, 6.4:1 on SURFACE_2  (AA)
        "TEXT_DISABLED": "#7d8ba0",   #  4.4:1 on SURFACE_2 (disabled text is exempt)
        "ACCENT":        "#1db954",   # primary action background
        "ACCENT_HOVER":  "#22c55e",
        "ACCENT_PRESSED":"#16a34a",
        "ON_ACCENT":     "#0e1117",   #  7.3:1 on ACCENT                      (AAA)
        "DANGER":        "#b91c1c",   # destructive button background
        "DANGER_HOVER":  "#dc2626",
        "DANGER_PRESSED":"#991b1b",
        "ON_DANGER":     "#ffffff",   #  6.5:1 on DANGER                      (AA)
        "DANGER_TEXT":   "#f87171",   #  6.2:1 on SURFACE (error messages)    (AA)
        "FOCUS":         "#60a5fa",   #  6.8:1 on SURFACE (focus ring, >= 3:1 needed)
        "TOOLTIP_BG":    "#e6edf3",
        "TOOLTIP_FG":    "#0e1117",   # 16.0:1
        "TOOLTIP_MUTED": "#4b5563",   #  6.9:1 on TOOLTIP_BG
        "STATUS": {                   # contrast on SURFACE_2
            "not_connected": "#9aa8bc",   # 6.4:1
            "idle":          "#60a5fa",   # 6.0:1
            "running":       "#facc15",   # 10.0:1
            "success":       "#4ade80",   # 8.8:1
            "failed":        "#f87171",   # 5.5:1
            "offline":       "#fb923c",   # 6.9:1
        },
    },
    "light": {
        "BG":            "#f3f5f8",
        "SURFACE":       "#ffffff",
        "SURFACE_2":     "#eef1f5",
        "SURFACE_3":     "#e2e7ee",
        "BORDER":        "#c9d1dc",
        "TEXT":          "#111827",   # 17.7:1 on SURFACE, 15.7:1 on SURFACE_2 (AAA)
        "TEXT_MUTED":    "#4b5563",   #  7.6:1 on SURFACE, 6.7:1 on SURFACE_2  (AA)
        "TEXT_DISABLED": "#6b7280",   #  4.3:1 on SURFACE_2 (disabled text is exempt)
        "ACCENT":        "#1db954",
        "ACCENT_HOVER":  "#22c55e",
        "ACCENT_PRESSED":"#16a34a",
        "ON_ACCENT":     "#0e1117",   #  7.3:1                                (AAA)
        "DANGER":        "#b91c1c",
        "DANGER_HOVER":  "#dc2626",
        "DANGER_PRESSED":"#991b1b",
        "ON_DANGER":     "#ffffff",   #  6.5:1                                (AA)
        "DANGER_TEXT":   "#b91c1c",   #  6.5:1 on SURFACE                     (AA)
        "FOCUS":         "#2563eb",   #  5.2:1 on SURFACE, 4.6:1 on SURFACE_2
        "TOOLTIP_BG":    "#111827",
        "TOOLTIP_FG":    "#f3f5f8",   # 16.2:1
        "TOOLTIP_MUTED": "#9aa8bc",   #  7.4:1 on TOOLTIP_BG
        "STATUS": {                   # contrast on SURFACE_2
            "not_connected": "#4b5563",   # 6.7:1
            "idle":          "#1d4ed8",   # 5.9:1
            "running":       "#92400e",   # 6.3:1
            "success":       "#166534",   # 6.3:1
            "failed":        "#b91c1c",   # 5.7:1
            "offline":       "#9a3412",   # 6.5:1
        },
    },
}

# Host status: colour + glyph + word, so status never relies on colour alone.
# Order = the order used for "sort by status" (problems first) and the filter chips.
STATUS_TEXT = {
    "failed":        ("✖", "Failed"),
    "offline":       ("⊘", "Offline"),
    "running":       ("◐", "Running"),
    "success":       ("✔", "Success"),
    "idle":          ("●", "Online"),
    "not_connected": ("○", "Not connected"),
}
SPINNER = "◐◓◑◒"          # frames of the "running" glyph

MODE   = "dark"
STATUS = {}               # key -> (glyph, label, colour) for the current palette

# Colour names of the active palette (filled in by _use_palette, declared for linters/editors)
BG = SURFACE = SURFACE_2 = SURFACE_3 = BORDER = ""
TEXT = TEXT_MUTED = TEXT_DISABLED = FOCUS = ""
ACCENT = ACCENT_HOVER = ACCENT_PRESSED = ON_ACCENT = ""
DANGER = DANGER_HOVER = DANGER_PRESSED = ON_DANGER = DANGER_TEXT = ""
TOOLTIP_BG = TOOLTIP_FG = TOOLTIP_MUTED = ""


def _use_palette(mode):
    global MODE, STATUS
    MODE = mode
    palette = PALETTES[mode]
    for name, value in palette.items():
        if name != "STATUS":
            globals()[name] = value
    STATUS = {k: (g, label, palette["STATUS"][k]) for k, (g, label) in STATUS_TEXT.items()}


_use_palette("dark")      # module-level names (BG, TEXT, ...) exist from import time


# ----------------------------------------------------------------- spacing --
# 8 px grid at 100 % scaling. XS is the only half step. apply() multiplies
# these by the display scale so padding grows with the text on HiDPI screens.
BASE_SPACING = {"XS": 4, "S": 8, "M": 16, "L": 24, "XL": 32}
XS, S, M, L, XL = 4, 8, 16, 24, 32
SCALE = 1.0


def px(value):
    """Scale a 100 %-layout pixel value to the current display."""
    return int(round(value * SCALE))


def enable_hidpi():
    """
    Ask Windows for sharp (unscaled) rendering. Must run BEFORE tk.Tk().
    Without it Windows bitmap-stretches the whole window at 125 %/150 %,
    which makes every letter blurry. No effect on Linux/macOS.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)      # per-system DPI aware
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


# -------------------------------------------------------------------- type --
UI_FAMILIES   = ("Inter", "Segoe UI", "Ubuntu", "Cantarell", "DejaVu Sans", "Helvetica")
MONO_FAMILIES = ("JetBrains Mono", "Cascadia Mono", "Ubuntu Mono", "DejaVu Sans Mono", "Consolas", "Courier")

# Type scale in points (Tk positive sizes are points, so they follow the DPI).
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


def _set_scale(root):
    global SCALE, XS, S, M, L, XL
    dpi = root.winfo_fpixels("1i")
    SCALE = max(1.0, dpi / 96.0)
    XS, S, M, L, XL = (px(BASE_SPACING[k]) for k in ("XS", "S", "M", "L", "XL"))


# ---------------------------------------------------------- theme switching --
_root      = None
_listeners = []


def on_change(callback):
    """callback() runs after every palette switch, to repaint non-ttk colours."""
    _listeners.append(callback)


def apply(root, mode="dark"):
    """Build fonts, compute scaling and configure every ttk style. Call once, right after tk.Tk()."""
    global _root
    _root = root
    _set_scale(root)
    _build_fonts(root)
    _use_palette(mode)
    return _configure(root)


def set_mode(mode):
    """Switch between "dark" and "light" while the app is running."""
    if mode == MODE or _root is None:
        return
    _use_palette(mode)
    _configure(_root)
    for callback in list(_listeners):
        try:
            callback()
        except Exception:          # a destroyed widget must not stop the others
            pass


def _configure(root):
    root.configure(bg=BG)
    root.option_add("*TCombobox*Listbox.background", SURFACE_2)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", FOCUS)
    root.option_add("*TCombobox*Listbox.selectForeground", SURFACE)

    style = ttk.Style(root)
    style.theme_use("clam")       # clam is the only built-in theme that honours colours everywhere

    style.configure(".",
                    background=SURFACE, foreground=TEXT, font=FONTS["body"],
                    bordercolor=BORDER, darkcolor=SURFACE, lightcolor=SURFACE,
                    troughcolor=SURFACE_2, focuscolor=FOCUS,
                    selectbackground=FOCUS, selectforeground=SURFACE,
                    insertcolor=TEXT)

    # ---- containers
    style.configure("App.TFrame",  background=BG)
    style.configure("TFrame",      background=SURFACE)
    style.configure("Card.TLabelframe", background=SURFACE, bordercolor=BORDER,
                    relief="solid", borderwidth=1, padding=(M, XS, M, M))
    style.configure("Card.TLabelframe.Label", background=SURFACE, foreground=TEXT,
                    font=FONTS["heading"])
    style.configure("Banner.TFrame", background=SURFACE_2)
    style.configure("Banner.TLabel", background=SURFACE_2, foreground=TEXT)
    style.configure("BannerMuted.TLabel", background=SURFACE_2, foreground=TEXT_MUTED, font=FONTS["caption"])
    style.configure("BannerStep.TLabel", background=SURFACE_2, foreground=FOCUS, font=FONTS["strong"])

    # ---- step indicator (01 Scan › 02 Review hosts › 03 Dashboard)
    style.configure("Step.TLabel",        background=SURFACE, foreground=TEXT_MUTED, font=FONTS["caption"])
    style.configure("StepNum.TLabel",     background=SURFACE, foreground=TEXT_MUTED, font=FONTS["strong"])
    style.configure("StepActive.TLabel",  background=SURFACE, foreground=TEXT, font=FONTS["strong"])
    style.configure("StepNumActive.TLabel", background=SURFACE, foreground=FOCUS, font=FONTS["strong"])

    # ---- option cards (choose scan method)
    style.configure("Option.TFrame", background=SURFACE, bordercolor=BORDER, relief="solid", borderwidth=1)
    style.configure("OptionHover.TFrame", background=SURFACE, bordercolor=FOCUS, relief="solid", borderwidth=1)
    style.configure("OptionTitle.TLabel", background=SURFACE, foreground=TEXT, font=FONTS["heading"])
    style.configure("Big.TLabel", background=SURFACE, foreground=TEXT, font=FONTS["title"])

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
    button("Primary.TButton", ACCENT,    ON_ACCENT, ACCENT_HOVER, ACCENT_PRESSED, FONTS["strong"])
    button("Danger.TButton",  DANGER,    ON_DANGER, DANGER_HOVER, DANGER_PRESSED)
    button("Ghost.TButton",   SURFACE,   TEXT_MUTED, SURFACE_2,   SURFACE_3)
    style.configure("Ghost.TButton", padding=(S, XS))
    style.configure("Tight.TButton", padding=(S, XS), width=0)
    button("Header.TButton",  BG,        TEXT,      SURFACE_2,    SURFACE_3)
    style.configure("Header.TButton", padding=(S, XS), width=0, bordercolor=BG)

    # ---- filter chips (radio buttons drawn as toggle pills)
    style.configure("Chip.Toolbutton", background=SURFACE, foreground=TEXT_MUTED,
                    bordercolor=BORDER, lightcolor=SURFACE, darkcolor=SURFACE,
                    focuscolor=FOCUS, padding=(S, XS // 2 or 1), font=FONTS["caption"],
                    relief="solid", borderwidth=1)
    style.map("Chip.Toolbutton",
              background=[("selected", SURFACE_2), ("active", SURFACE_2)],
              foreground=[("selected", TEXT), ("active", TEXT)],
              bordercolor=[("focus", FOCUS), ("selected", FOCUS)],
              lightcolor=[("selected", SURFACE_2)], darkcolor=[("selected", SURFACE_2)])

    # ---- inputs
    style.configure("TEntry", fieldbackground=SURFACE_2, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=SURFACE_2, darkcolor=SURFACE_2,
                    padding=(S, XS))
    style.map("TEntry",
              bordercolor=[("focus", FOCUS)],
              lightcolor=[("focus", FOCUS)],
              fieldbackground=[("disabled", SURFACE)])
    style.configure("Mono.TEntry", font=FONTS["mono"])

    style.configure("TCombobox", fieldbackground=SURFACE_2, background=SURFACE_2, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=SURFACE_2, darkcolor=SURFACE_2,
                    arrowcolor=TEXT_MUTED, padding=(S, XS))
    style.map("TCombobox",
              fieldbackground=[("readonly", SURFACE_2)],
              foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", SURFACE_2)],
              selectforeground=[("readonly", TEXT)],
              bordercolor=[("focus", FOCUS)],
              background=[("active", SURFACE_3)])

    style.configure("TMenubutton", background=SURFACE_2, foreground=TEXT, arrowcolor=TEXT_MUTED,
                    bordercolor=BORDER, lightcolor=SURFACE_2, darkcolor=SURFACE_2,
                    padding=(S, XS), relief="flat")
    style.map("TMenubutton",
              background=[("active", SURFACE_3), ("pressed", SURFACE_3)],
              bordercolor=[("focus", FOCUS)])

    style.configure("TSpinbox", fieldbackground=SURFACE_2, background=SURFACE_2, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=SURFACE_2, darkcolor=SURFACE_2,
                    arrowcolor=TEXT_MUTED, padding=(S, XS))
    style.map("TSpinbox", bordercolor=[("focus", FOCUS)], background=[("active", SURFACE_3)])

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
                    bordercolor=SURFACE_2, lightcolor=ACCENT, darkcolor=ACCENT, thickness=px(8))
    style.configure("Vertical.TScrollbar", background=SURFACE_2, troughcolor=SURFACE,
                    bordercolor=SURFACE, arrowcolor=TEXT_MUTED, lightcolor=SURFACE_2, darkcolor=SURFACE_2)
    style.map("Vertical.TScrollbar", background=[("active", SURFACE_3)])
    style.configure("App.Vertical.TScrollbar", background=SURFACE_2, troughcolor=BG,
                    bordercolor=BG, arrowcolor=TEXT_MUTED, lightcolor=SURFACE_2, darkcolor=SURFACE_2)
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
