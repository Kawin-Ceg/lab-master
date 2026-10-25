"""
Reusable widgets: tooltips, icon buttons, password entry with show/hide,
modal dialog base, confirmation dialog, scrollable frame, host tile,
host grid and status bar.

Widgets that draw colours themselves (canvases, tiles, tooltips, icons)
repaint through theme.on_change(), so the light/dark switch is live.
"""
import ipaddress
import sys
import tkinter as tk
from tkinter import ttk

from . import theme as t


# ---------------------------------------------------------------- tooltip --
class Tooltip:
    """
    Small help bubble for any widget.

        Tooltip(widget, "What this does")
        Tooltip(widget, "What this does", shortcut="Ctrl+M")
        tip.text = "new text"          # can be changed at any time

    Shows after a short delay on mouse hover, or when the widget is reached
    with Tab (not when focus is set by a click or by code). Hides on leave,
    click, typing, scrolling or Escape. Stays inside the screen: flips above
    the widget near the bottom edge and shifts left near the right edge.
    """

    DELAY_MS     = 500
    keyboard_nav = False      # True after Tab, False after a mouse click
    _current     = None       # only one tooltip is visible at a time
    _hooked      = False

    def __init__(self, widget, text="", shortcut=""):
        if not Tooltip._hooked:
            root = widget.winfo_toplevel()
            root.bind_all("<KeyPress-Tab>",       lambda e: setattr(Tooltip, "keyboard_nav", True), add="+")
            root.bind_all("<ISO_Left_Tab>",       lambda e: setattr(Tooltip, "keyboard_nav", True), add="+")
            root.bind_all("<ButtonPress>",        lambda e: setattr(Tooltip, "keyboard_nav", False), add="+")
            root.bind_all("<KeyPress-Escape>",    lambda e: Tooltip.hide_current(), add="+")
            root.bind_all("<MouseWheel>",         lambda e: Tooltip.hide_current(), add="+")
            Tooltip._hooked = True
        self.widget   = widget
        self.text     = text
        self.shortcut = shortcut
        self.tip      = None
        self.job      = None
        self._pointer = None
        widget.bind("<Enter>",       self._on_enter, add="+")
        widget.bind("<Leave>",       self._hide,     add="+")
        widget.bind("<FocusIn>",     self._on_focus, add="+")
        widget.bind("<FocusOut>",    self._hide,     add="+")
        widget.bind("<ButtonPress>", self._hide,     add="+")
        widget.bind("<KeyPress>",    self._on_key,   add="+")
        widget.bind("<Destroy>",     self._hide,     add="+")

    @classmethod
    def hide_current(cls):
        if cls._current:
            cls._current._hide()

    # -- triggers
    def _on_enter(self, event):
        self._pointer = event.x_root
        self._schedule()

    def _on_focus(self, _event=None):
        if Tooltip.keyboard_nav:
            self._pointer = None
            self._schedule()

    def _on_key(self, event):
        if event.keysym not in ("Tab", "ISO_Left_Tab", "Shift_L", "Shift_R"):
            self._hide()

    def _schedule(self):
        self._cancel()
        self.job = self.widget.after(self.DELAY_MS, self._show)

    def _cancel(self):
        if self.job:
            try:
                self.widget.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None

    # -- drawing
    def _show(self):
        self.job = None
        if self.tip or not self.text:
            return
        try:
            if not self.widget.winfo_viewable():
                return
        except tk.TclError:
            return
        Tooltip.hide_current()
        Tooltip._current = self

        tip = self.tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        try:
            tip.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        box = tk.Frame(tip, bg=t.TOOLTIP_BG, padx=t.S, pady=t.XS)
        box.pack()
        tk.Label(box, text=self.text, justify="left", wraplength=t.px(320),
                 bg=t.TOOLTIP_BG, fg=t.TOOLTIP_FG, font=t.FONTS["caption"]).pack(anchor="w")
        if self.shortcut:
            tk.Label(box, text=f"Shortcut: {self.shortcut}", justify="left",
                     bg=t.TOOLTIP_BG, fg=t.TOOLTIP_MUTED, font=t.FONTS["caption"]).pack(anchor="w")

        tip.update_idletasks()
        w, h = tip.winfo_reqwidth(), tip.winfo_reqheight()
        sw, sh = tip.winfo_screenwidth(), tip.winfo_screenheight()
        wx, wy = self.widget.winfo_rootx(), self.widget.winfo_rooty()
        x = (self._pointer if self._pointer is not None else wx) + t.S
        y = wy + self.widget.winfo_height() + t.XS
        if y + h > sh - t.S:                         # no room below: show above
            y = wy - h - t.XS
        x = max(t.XS, min(x, sw - w - t.XS))         # keep inside the screen
        tip.wm_geometry(f"+{x}+{max(t.XS, y)}")

    def _hide(self, _event=None):
        self._cancel()
        if self.tip:
            try:
                self.tip.destroy()
            except tk.TclError:
                pass
            self.tip = None
        if Tooltip._current is self:
            Tooltip._current = None


# ------------------------------------------------------------------ icons --
# Line icons from images/ui (generated by ui/make_icons.py), one colour per
# button style and theme, because Tk cannot recolour an image at runtime.
_ICONS = {}
_ICON_BUTTONS = []        # (button, icon name, style) for repainting on theme change


def _variant(style):
    if style.startswith("Primary"):
        return "dark"
    if style.startswith("Danger"):
        return "white"
    return "light" if t.MODE == "dark" else "dark"


def icon(name, variant="light"):
    key = (name, variant)
    if key not in _ICONS:
        from base_dir import BASE_DIR
        _ICONS[key] = tk.PhotoImage(file=str(BASE_DIR / "images" / "ui" / f"{name}_{variant}.png"))
    return _ICONS[key]


def icon_for(name, style="TButton"):
    """Image spec for ttk: normal image plus a muted one for the disabled state."""
    return (icon(name, _variant(style)), "disabled", icon(name, "disabled"))


def set_button_icon(btn, name, style):
    btn.configure(image=icon_for(name, style), compound="left")
    _ICON_BUTTONS[:] = [entry for entry in _ICON_BUTTONS if entry[0] is not btn]
    _ICON_BUTTONS.append((btn, name, style))


def _repaint_icons():
    alive = []
    for btn, name, style in _ICON_BUTTONS:
        try:
            btn.configure(image=icon_for(name, style))
            alive.append((btn, name, style))
        except tk.TclError:
            pass                                    # button was destroyed
    _ICON_BUTTONS[:] = alive


t.on_change(_repaint_icons)


def button(parent, text, command, tooltip="", shortcut="", style="TButton", icon_name=None, **kw):
    """ttk.Button with an optional left icon and a tooltip that names its shortcut."""
    if icon_name:
        text = f" {text}"
    btn = ttk.Button(parent, text=text, command=command, style=style, **kw)
    if icon_name:
        set_button_icon(btn, icon_name, style)
    if tooltip or shortcut:
        btn.tooltip = Tooltip(btn, tooltip, shortcut)
    return btn


def card(parent, title):
    return ttk.LabelFrame(parent, text=title, style="Card.TLabelframe")


# --------------------------------------------------------- password entry --
class PasswordEntry(ttk.Frame):
    """Entry that hides its text, with a Show/Hide toggle button."""

    def __init__(self, parent, textvariable=None, width=20, **kw):
        super().__init__(parent, **kw)
        self.entry = ttk.Entry(self, show="•", textvariable=textvariable, width=width)
        self.toggle = ttk.Button(self, text="Show", width=5, style="Ghost.TButton",
                                 command=self._toggle, takefocus=True)
        Tooltip(self.toggle, "Show or hide the password")
        self.entry.pack(side="left", fill="x", expand=True)
        self.toggle.pack(side="left", padx=(t.XS, 0))

    def _toggle(self):
        hidden = self.entry.cget("show") != ""
        self.entry.config(show="" if hidden else "•")
        self.toggle.config(text="Hide" if hidden else "Show")

    def get(self):
        return self.entry.get()

    def bind_entry(self, sequence, func):
        self.entry.bind(sequence, func)

    def focus_set(self):
        self.entry.focus_set()


# ---------------------------------------------------------- modal dialogs --
class Dialog(tk.Toplevel):
    """
    Base modal dialog: title, body frame, button row.
    Enter = primary action, Escape = cancel. Blocks until closed.
    """

    def __init__(self, parent, title, subtitle=""):
        super().__init__(parent)
        self.withdraw()
        self.title(title)
        self.configure(bg=t.SURFACE)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.result = None

        outer = ttk.Frame(self, padding=t.L)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=title, font=t.FONTS["heading"]).pack(anchor="w")
        if subtitle:
            ttk.Label(outer, text=subtitle, style="Muted.TLabel",
                      wraplength=t.px(380), justify="left").pack(anchor="w", pady=(t.XS, 0))

        self.body = ttk.Frame(outer)
        self.body.pack(fill="both", expand=True, pady=(t.M, t.M))
        self.buttons = ttk.Frame(outer)
        self.buttons.pack(fill="x")

        self.bind("<Escape>", lambda e: self.cancel())
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def add_buttons(self, ok_text, on_ok, ok_style="Primary.TButton"):
        ttk.Button(self.buttons, text=ok_text, style=ok_style, command=on_ok).pack(side="right")
        ttk.Button(self.buttons, text="Cancel", command=self.cancel).pack(side="right", padx=(0, t.S))
        self.bind("<Return>", lambda e: on_ok())

    def cancel(self):
        self.result = None
        self.destroy()

    def run(self, focus=None):
        """Centre over the parent, grab input, wait until closed and return self.result."""
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_reqwidth())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.deiconify()
        self.grab_set()
        (focus or self).focus_set()
        self.wait_window(self)
        return self.result


def confirm(parent, title, message, action_text, danger=True):
    """
    Confirmation for destructive actions. Cancel has focus, so an accidental
    Enter does nothing; the action button names the exact action.
    """
    dlg = Dialog(parent, title)
    ttk.Label(dlg.body, text=message, wraplength=t.px(380), justify="left").pack(anchor="w")

    def ok():
        dlg.result = True
        dlg.destroy()

    ttk.Button(dlg.buttons, text=action_text, command=ok,
               style="Danger.TButton" if danger else "Primary.TButton").pack(side="right")
    cancel_btn = ttk.Button(dlg.buttons, text="Cancel", command=dlg.cancel)
    cancel_btn.pack(side="right", padx=(0, t.S))
    cancel_btn.bind("<Return>", lambda e: dlg.cancel())
    return bool(dlg.run(focus=cancel_btn))


def info(parent, title, message):
    dlg = Dialog(parent, title)
    ttk.Label(dlg.body, text=message, justify="left", font=t.FONTS["mono"]).pack(anchor="w")
    ok = ttk.Button(dlg.buttons, text="Close", style="Primary.TButton", command=dlg.cancel)
    ok.pack(side="right")
    dlg.bind("<Return>", lambda e: dlg.cancel())
    dlg.run(focus=ok)


# ----------------------------------------------------------- scroll frame --
class ScrollFrame(ttk.Frame):
    """
    Vertical scrolling container. Put children in `.inner`. The scrollbar only
    appears when the content is taller than the space, and the frame keeps
    the natural width of its content.
    """

    def __init__(self, parent, inner_style="App.TFrame", **kw):
        super().__init__(parent, style=inner_style, **kw)
        self.canvas = tk.Canvas(self, bg=t.BG, highlightthickness=0, bd=0)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                    style="App.Vertical.TScrollbar")
        self.inner  = ttk.Frame(self.canvas, style=inner_style)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self._bar_shown = False

        self.inner.bind("<Configure>",  self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_wheel))
        self.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        t.on_change(lambda: self.canvas.configure(bg=t.BG))

    def _on_inner(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"),
                              width=self.inner.winfo_reqwidth())
        self._update_bar()

    def _on_canvas(self, event):
        self.canvas.itemconfig(self.window, width=event.width)
        self._update_bar()

    def _update_bar(self):
        need = self.inner.winfo_reqheight() > self.canvas.winfo_height() + 1
        if need and not self._bar_shown:
            self.scroll.pack(side="right", fill="y", padx=(t.XS, 0))
        elif not need and self._bar_shown:
            self.scroll.pack_forget()
            self.canvas.yview_moveto(0)
        self._bar_shown = need

    def _on_wheel(self, event):
        if self._bar_shown:
            self.canvas.yview_scroll(int(-event.delta / 120) or (-1 if event.delta > 0 else 1), "units")

    def follow_focus(self):
        """Scroll so that keyboard focus inside the frame stays visible."""
        def walk(widget):
            widget.bind("<FocusIn>", lambda e, w=widget: self.see(w), add="+")
            for child in widget.winfo_children():
                walk(child)
        walk(self.inner)

    def see(self, widget):
        if not self._bar_shown:
            return
        total = max(self.inner.winfo_height(), 1)
        top   = widget.winfo_rooty() - self.inner.winfo_rooty()
        bottom = top + widget.winfo_height()
        view_top = self.canvas.yview()[0] * total
        view_h   = self.canvas.winfo_height()
        if top < view_top:
            self.canvas.yview_moveto(max(top - t.S, 0) / total)
        elif bottom > view_top + view_h:
            self.canvas.yview_moveto((bottom - view_h + t.S) / total)


# -------------------------------------------------------------- host tile --
def tile_width():
    return t.px(188)


class HostTile:
    """
    One machine in the host grid.

    Status is shown three ways: coloured edge strip, glyph and word.
    The whole tile is focusable:
      click / Enter / Space        open the host actions
      right-click / Shift+F10      context menu
      arrow keys, Home, End        move between tiles (handled by HostGrid)
    """

    def __init__(self, parent, ip_address, on_open):
        self.ip_address = ip_address
        self.hostname   = ""
        self.users      = []
        self.status     = "not_connected"
        self.compact    = False
        self._on_open   = on_open
        self._grid      = None
        self._spin      = 0

        self.cover = ttk.Frame(parent, style="Tile.TFrame", takefocus=True, cursor="hand2")
        self.strip = tk.Frame(self.cover, width=max(4, t.px(4)), bg=t.STATUS["not_connected"][2])
        self.strip.pack(side="left", fill="y")

        inner = ttk.Frame(self.cover, style="Tile.TFrame", padding=(t.S, t.S, t.S, t.S))
        inner.pack(side="left", fill="both", expand=True)

        self.status_label = ttk.Label(inner, style="Status_not_connected.TLabel")
        self.name_label   = ttk.Label(inner, text=ip_address, style="TileName.TLabel")
        self.ip_label     = ttk.Label(inner, text="", style="TileMuted.TLabel")
        self.users_label  = ttk.Label(inner, text="", style="TileMuted.TLabel", justify="left")

        self.status_label.pack(anchor="w")
        self.name_label.pack(anchor="w", pady=(t.XS, 0))
        self.ip_label.pack(anchor="w")
        self.users_label.pack(anchor="w")
        self._detail_widgets = (self.ip_label, self.users_label)

        self.tooltip = Tooltip(self.cover, "")
        parts = (self.cover, inner, self.strip, self.status_label, self.name_label, self.ip_label, self.users_label)
        for widget in parts:
            widget.bind("<Button-1>", lambda e: self.open())
            widget.bind("<Button-3>", self.show_menu)
            if sys.platform == "darwin":
                widget.bind("<Button-2>", self.show_menu)
        self.cover.bind("<Return>",    lambda e: self.open())
        self.cover.bind("<space>",     lambda e: self.open())
        self.cover.bind("<Shift-F10>", self.show_menu)
        if sys.platform == "win32":
            self.cover.bind("<App>",   self.show_menu)
        else:
            self.cover.bind("<Menu>",  self.show_menu)
        self.cover.bind("<FocusIn>",  self._on_focus_in, add="+")
        self.cover.bind("<FocusOut>", lambda e: self.cover.configure(style="Tile.TFrame"), add="+")

        self.set_status("not_connected")

    # -- actions
    def open(self):
        self.tooltip._hide()
        self.cover.focus_set()
        self._on_open(self)

    def show_menu(self, event=None):
        self.tooltip._hide()
        self.cover.focus_set()
        menu = tk.Menu(self.cover, tearoff=0, bg=t.SURFACE, fg=t.TEXT,
                       activebackground=t.SURFACE_3, activeforeground=t.TEXT,
                       disabledforeground=t.TEXT_DISABLED, bd=1, relief="solid",
                       font=t.FONTS["body"])
        menu.add_command(label="Host actions…", accelerator="Enter", command=self.open)
        menu.add_separator()
        menu.add_command(label="Copy IP address", command=lambda: self._copy(self.ip_address))
        menu.add_command(label="Copy hostname", command=lambda: self._copy(self.hostname),
                         state="normal" if self.hostname else "disabled")
        if event is not None and event.type == tk.EventType.ButtonPress:
            x, y = event.x_root, event.y_root
        else:
            x = self.cover.winfo_rootx() + t.M
            y = self.cover.winfo_rooty() + self.cover.winfo_height() // 2
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()
        return "break"

    def _copy(self, text):
        self.cover.clipboard_clear()
        self.cover.clipboard_append(text)

    def _on_focus_in(self, _event=None):
        self.cover.configure(style="TileFocus.TFrame")
        if self._grid:
            self._grid.see(self)

    # -- state
    def set_status(self, key):
        self.status = key
        self._spin  = 0
        glyph, label, colour = t.STATUS[key]
        self.status_label.configure(text=f"{glyph}  {label}", style=f"Status_{key}.TLabel")
        self.strip.configure(bg=colour)
        self._update_tooltip()

    def advance_spinner(self):
        """Next frame of the running animation (called by HostGrid)."""
        self._spin = (self._spin + 1) % len(t.SPINNER)
        self.status_label.configure(text=f"{t.SPINNER[self._spin]}  {t.STATUS['running'][1]}")

    def set_details(self, hostname, users):
        """users: list of [username, 'ssh' | 'local'] as produced by find_user."""
        self.hostname = hostname.strip()
        self.users    = users or []
        self.name_label.configure(text=self.hostname or self.ip_address)
        self.ip_label.configure(text=self.ip_address if self.hostname else "")
        lines = [("Remote: " if kind == "ssh" else "Local: ") + name for name, kind in self.users[:3]]
        if len(self.users) > 3:
            lines.append(f"+{len(self.users) - 3} more")
        self.users_label.configure(text="\n".join(lines) if lines else "No users logged in")
        self._update_tooltip()

    def set_compact(self, compact):
        self.compact = compact
        for widget in self._detail_widgets:
            if compact:
                widget.pack_forget()
            else:
                widget.pack(anchor="w")

    def matches(self, query):
        query = query.strip().lower()
        if not query:
            return True
        haystack = " ".join([self.ip_address, self.hostname, t.STATUS[self.status][1]]
                            + [u[0] for u in self.users]).lower()
        return query in haystack

    def _update_tooltip(self):
        users = ", ".join(u[0] for u in self.users) or "none"
        self.tooltip.text = (f"{self.hostname or '(hostname unknown)'}\n{self.ip_address}\n"
                             f"Status: {t.STATUS[self.status][1]}\nLogged in: {users}\n"
                             "Click or Enter: host actions · Right-click: more")


# -------------------------------------------------------------- host grid --
def _ip_key(ip):
    try:
        return (0, ipaddress.ip_address(ip))
    except ValueError:
        return (1, ip)


SORTS = {
    "ip":     ("IP address", lambda tile: _ip_key(tile.ip_address)),
    "name":   ("Hostname",   lambda tile: ((tile.hostname or "~").lower(), _ip_key(tile.ip_address))),
    "status": ("Status",     lambda tile: (list(t.STATUS_TEXT).index(tile.status), _ip_key(tile.ip_address))),
}


class HostGrid(ttk.Frame):
    """
    Scrollable, responsive grid of HostTile objects with text filter,
    status filter, sorting, keyboard navigation and the running animation.
    """

    SPIN_MS = 180

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.tiles   = []
        self.visible = []
        self.query   = ""
        self.status_filter = None        # None = all, else a STATUS key
        self.sort_key = "ip"
        self._cols   = 0

        self.canvas = tk.Canvas(self, bg=t.SURFACE, highlightthickness=0, bd=0)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner  = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.empty_label = ttk.Label(self.inner, style="Muted.TLabel")

        self.scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.bind("<Configure>", self._on_resize)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"), add="+")
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"), add="+")

        t.on_change(self._retheme)
        self.after(self.SPIN_MS, self._tick)

    def add(self, tile):
        tile._grid = self
        for key, dx, dy in (("<Left>", -1, 0), ("<Right>", 1, 0), ("<Up>", 0, -1), ("<Down>", 0, 1)):
            tile.cover.bind(key, lambda e, tl=tile, a=dx, b=dy: self.move_focus(tl, a, b))
        tile.cover.bind("<Home>", lambda e: self._focus_index(0))
        tile.cover.bind("<End>",  lambda e: self._focus_index(len(self.visible) - 1))
        self.tiles.append(tile)

    # -- layout
    def _on_wheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120) or (-1 if event.delta > 0 else 1), "units")

    def _on_resize(self, event):
        self.canvas.itemconfig(self.window, width=event.width)
        cols = max(1, event.width // (tile_width() + t.S))
        if cols != self._cols:
            self._cols = cols
            self.reflow()

    def set_filter(self, query):
        self.query = query
        self.reflow()

    def set_status_filter(self, key):
        self.status_filter = key or None
        self.reflow()

    def set_sort(self, key):
        self.sort_key = key
        self.reflow()

    def set_compact(self, compact):
        for tile in self.tiles:
            tile.set_compact(compact)
        self.reflow()

    def _shown(self, tile):
        if self.status_filter and tile.status != self.status_filter:
            return False
        return tile.matches(self.query)

    def reflow(self):
        cols = max(1, self._cols)
        self.visible = sorted((tile for tile in self.tiles if self._shown(tile)),
                              key=SORTS[self.sort_key][1])
        for tile in self.tiles:
            tile.cover.grid_forget()
        self.empty_label.grid_forget()
        for c in range(cols):
            self.inner.columnconfigure(c, minsize=tile_width(), uniform="tiles")

        for index, tile in enumerate(self.visible):
            tile.cover.grid(row=index // cols, column=index % cols,
                            padx=(0, t.S), pady=(0, t.S), sticky="nsew")
        self.canvas.yview_moveto(0)
        if not self.visible:
            if not self.tiles:
                text = "No hosts loaded. Restart and choose an IP list file."
            elif self.status_filter:
                text = f"No hosts are {t.STATUS[self.status_filter][1].lower()}."
            else:
                text = "No hosts match the filter."
            self.empty_label.configure(text=text)
            self.empty_label.grid(row=0, column=0, columnspan=cols, sticky="w", pady=t.M)

    # -- keyboard
    def move_focus(self, tile, dx, dy):
        if tile not in self.visible:
            return "break"
        cols = max(1, self._cols)
        index = self.visible.index(tile) + dx + dy * cols
        if 0 <= index < len(self.visible):
            self._focus_index(index)
        return "break"

    def _focus_index(self, index):
        if self.visible:
            self.visible[max(0, min(index, len(self.visible) - 1))].cover.focus_set()
        return "break"

    def focus_first(self):
        self._focus_index(0)

    def see(self, tile):
        """Scroll the grid so `tile` is fully visible."""
        self.update_idletasks()
        total = max(self.inner.winfo_height(), 1)
        top = tile.cover.winfo_y()
        bottom = top + tile.cover.winfo_height()
        view_top = self.canvas.yview()[0] * total
        view_h = self.canvas.winfo_height()
        if top < view_top or bottom - top > view_h:
            self.canvas.yview_moveto(top / total)
        elif bottom > view_top + view_h:
            self.canvas.yview_moveto((bottom - view_h + t.S) / total)

    # -- animation and theming
    def _tick(self):
        for tile in self.tiles:
            if tile.status == "running":
                tile.advance_spinner()
        self.after(self.SPIN_MS, self._tick)

    def _retheme(self):
        self.canvas.configure(bg=t.SURFACE)
        for tile in self.tiles:
            tile.set_status(tile.status)          # status colours differ per theme

    def counts(self):
        result = {key: 0 for key in t.STATUS}
        for tile in self.tiles:
            result[tile.status] += 1
        return result


# ------------------------------------------------------------- flow frame --
class FlowFrame(ttk.Frame):
    """Lays its children out left to right and wraps to a new row when full."""

    def __init__(self, parent, gap=None, **kw):
        super().__init__(parent, **kw)
        self.gap = t.XS if gap is None else gap
        self.items = []
        self.bind("<Configure>", lambda e: self.relayout())

    def add(self, widget):
        self.items.append(widget)

    def relayout(self):
        width = self.winfo_width()
        if width <= 1:
            width = self.master.winfo_width()
        x = y = row_h = 0
        for widget in self.items:
            if not getattr(widget, "flow_visible", True):
                widget.place_forget()
                continue
            w, h = widget.winfo_reqwidth(), widget.winfo_reqheight()
            if x and x + w > width:
                x, y = 0, y + row_h + self.gap
                row_h = 0
            widget.place(x=x, y=y)
            x += w + self.gap
            row_h = max(row_h, h)
        height = y + row_h
        if height and int(self.cget("height") or 0) != height:
            self.configure(height=height)


# ------------------------------------------------------------- status bar --
class StatusBar(ttk.Frame):
    """Bottom bar: current activity, progress bar and running counts."""

    def __init__(self, parent, **kw):
        super().__init__(parent, style="Status.TFrame", padding=(t.M, t.S), **kw)
        self.message_label = ttk.Label(self, text="Ready. Enter credentials and press Connect.",
                                       style="Status.TLabel")
        self.progress = ttk.Progressbar(self, mode="determinate", length=t.px(200))
        self.hosts_label = ttk.Label(self, text="", style="StatusMuted.TLabel")
        self._tone = "normal"

        self.message_label.pack(side="left")
        self.hosts_label.pack(side="right")
        self.progress.pack(side="right", padx=(t.M, t.M))
        t.on_change(lambda: self._set_tone(self._tone))

    def _set_tone(self, tone):
        self._tone = tone
        colour = {"normal": t.TEXT, "error": t.DANGER_TEXT, "success": t.STATUS["success"][2]}[tone]
        self.message_label.configure(foreground=colour)

    def progress_update(self, done, total, failed=0):
        self.progress.configure(maximum=max(total, 1), value=done)
        text = f"Working… finished {done}/{total}"
        if failed:
            text += f", {failed} failed"
        self.message_label.configure(text=text)
        self._set_tone("normal")

    def done(self, success, failure):
        total = success + failure
        self.progress.configure(maximum=max(total, 1), value=total)
        if failure:
            self.message_label.configure(text=f"✖ Done: {success} succeeded, {failure} failed")
            self._set_tone("error")
        else:
            self.message_label.configure(text=f"✔ Done: {success} succeeded")
            self._set_tone("success")

    def message(self, text, error=False):
        self.message_label.configure(text=text)
        self._set_tone("error" if error else "normal")

    def set_host_counts(self, counts):
        parts = [f"{t.STATUS[k][0]} {counts[k]} {t.STATUS[k][1].lower()}" for k in t.STATUS if counts[k]]
        self.hosts_label.configure(text="   ".join(parts))
