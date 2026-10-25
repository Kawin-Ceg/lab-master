"""
Main dashboard layout.

    ┌ header: title · hosts loaded          [Hide panel][Light mode][Help][Exit] ┐
    │ sidebar (scrolls):  │ Command                                              │
    │   Connection        │ File transfer                                        │
    │   Session & power   │ Hosts: filter · sort · compact · refresh             │
    │   User management   │        status chips · first-run guide · grid         │
    ├ status bar ────────────────────────────────────────────────────────────────┤

The window knows nothing about SSH. work_screen.py passes in an `actions`
dict of callbacks and reads the inputs through the attributes below.
"""
import tkinter as tk
from tkinter import ttk

from . import theme as t
from . import settings
from .widgets import (button, card, confirm, info, set_button_icon, PasswordEntry, Tooltip,
                      ScrollFrame, FlowFrame, HostGrid, StatusBar, SORTS)


SHORTCUTS = [
    ("Enter (in password)", "Connect"),
    ("Ctrl+Enter / F5",     "Run command on all connected hosts"),
    ("Ctrl+.",              "Stop after the current host"),
    ("Ctrl+M",              "Send message"),
    ("Ctrl+L",              "Lock all screens"),
    ("Ctrl+R",              "Refresh host info"),
    ("Ctrl+U",              "Upload source file"),
    ("Ctrl+D",              "Download source file"),
    ("",                    ""),
    ("Ctrl+F",              "Filter hosts (Esc clears the filter)"),
    ("Ctrl+G",              "Jump to the host grid"),
    ("Arrow keys, Home/End","Move between hosts"),
    ("Enter / Space",       "Open actions for the focused host"),
    ("Shift+F10 / Menu key","Host context menu (or right-click)"),
    ("Ctrl+T",              "Toggle compact host tiles"),
    ("Ctrl+B",              "Hide or show the side panel"),
    ("",                    ""),
    ("F1",                  "Show this help"),
    ("Ctrl+Q",              "Exit"),
    ("",                    ""),
    ("Shut down, Delete user", "No shortcut on purpose. Always asks to confirm."),
]


class MainWindow:

    def __init__(self, root, actions, src_var, des_var, source_name="", host_count=0):
        self.root    = root
        self.actions = actions
        self.busy    = False
        self.host_count = host_count
        self._action_buttons = []

        root.title("Lab Master")
        self._size_window()
        root.configure(bg=t.BG)

        self.is_sudo    = tk.BooleanVar(value=False)
        self.is_display = tk.BooleanVar(value=False)
        self.compact    = tk.BooleanVar(value=bool(settings.get("compact")))
        self.filter_var = tk.StringVar()
        self.status_var = tk.StringVar(value="")
        self.sort_var   = tk.StringVar(value=settings.get("sort") if settings.get("sort") in SORTS else "ip")
        self.src_var    = src_var
        self.des_var    = des_var

        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        self._build_header(source_name, host_count)
        body = ttk.Frame(root, style="App.TFrame", padding=(t.M, 0, t.M, t.M))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self.sidebar = ScrollFrame(body)
        self.sidebar.grid(row=0, column=0, sticky="nsw", padx=(0, t.M))
        main = ttk.Frame(body, style="App.TFrame")
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        self._build_connection(self.sidebar.inner)
        self._build_session(self.sidebar.inner)
        self._build_users(self.sidebar.inner)
        self._build_files(self.sidebar.inner)
        self.sidebar.follow_focus()
        self._build_command(main)
        self._build_hosts(main)

        self.status_bar = StatusBar(root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

        self._bind_shortcuts()
        self.set_busy(False)
        if not settings.get("sidebar_visible"):
            self.toggle_sidebar()
        root.protocol("WM_DELETE_WINDOW", self._wrap(actions["exit"]))

    def _size_window(self):
        """1280×720 at 100 %, scaled for HiDPI but never larger than the screen."""
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w = min(t.px(1280), sw - t.px(40))
        h = min(t.px(720),  sh - t.px(80))
        self.root.geometry(f"{w}x{h}+{max((sw - w) // 2, 0)}+{max((sh - h) // 3, 0)}")
        self.root.minsize(min(t.px(960), w), min(t.px(600), h))

    # ------------------------------------------------------------ helpers --
    def _wrap(self, fn):
        """Run an action with every other action disabled, so runs cannot overlap."""
        def run(*_):
            if self.busy or fn is None:
                return "break"
            self.set_busy(True)
            try:
                fn()
            finally:
                self.set_busy(False)
                self.refresh_counts()
                if self.grid.sort_key == "status" or self.grid.status_filter:
                    self.grid.reflow()             # statuses changed: re-sort / re-filter once
            return "break"
        return run

    def _btn(self, parent, text, key, tooltip, shortcut="", style="TButton", icon=None):
        b = button(parent, text, self._wrap(self.actions.get(key)), tooltip, shortcut, style, icon_name=icon)
        if self.actions.get(key) is None:
            b.state(["disabled"])
        self._action_buttons.append(b)
        return b

    def set_busy(self, busy):
        self.busy = busy
        for b in self._action_buttons:
            if self.actions_enabled(b):
                b.state(["disabled"] if busy else ["!disabled"])
        self.stop_btn.state(["!disabled"] if busy else ["disabled"])
        self.root.configure(cursor="watch" if busy else "")

    def actions_enabled(self, b):
        return not getattr(b, "_never_enabled", False)

    def _connected_count(self):
        c = self.grid.counts()
        return c["idle"] + c["running"] + c["success"] + c["failed"]

    def refresh_counts(self):
        counts = self.grid.counts()
        self.status_bar.set_host_counts(counts)
        self.chips[""].configure(text=f"All {len(self.grid.tiles)}")
        for key, chip in self.chips.items():
            if key:
                glyph, label, _ = t.STATUS[key]
                chip.configure(text=f"{glyph} {label} {counts[key]}")
                # hide statuses no host has, unless that chip is the active filter
                chip.flow_visible = counts[key] > 0 or self.status_var.get() == key
        self.chip_row.relayout()

    def set_connected(self):
        """After the first connect, Run becomes the only primary action."""
        self.connect_btn.configure(style="TButton", text=" Reconnect missing")
        set_button_icon(self.connect_btn, "connect", "TButton")
        self.connect_btn.tooltip.text = "Retries hosts that are not connected yet"
        self.banner.grid_remove()

    # ------------------------------------------------------------- header --
    def _build_header(self, source_name, host_count):
        header = ttk.Frame(self.root, style="App.TFrame", padding=(t.M, t.S, t.M, t.S))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Lab Master", style="Title.TLabel").pack(side="left")
        detail = f"{host_count} hosts loaded" + (f" from {source_name}" if source_name else "")
        ttk.Label(header, text=detail, style="AppMuted.TLabel").pack(side="left", padx=(t.M, 0), pady=(t.XS, 0))

        tools = ttk.Frame(header, style="App.TFrame")
        tools.pack(side="right")
        self.sidebar_btn = button(tools, "Hide panel", self.toggle_sidebar,
                                  "Hide the side panel to give the host grid more room", "Ctrl+B",
                                  style="Tight.TButton")
        self.theme_btn = button(tools, "Light mode" if t.MODE == "dark" else "Dark mode", self.toggle_theme,
                                "Switch between dark and light colours", style="Tight.TButton")
        help_btn = button(tools, "Help", self.show_help, "Keyboard shortcuts", "F1",
                          style="Tight.TButton", icon_name="help")
        exit_btn = button(tools, "Exit", self._wrap(self.actions["exit"]), "Close all connections and quit",
                          "Ctrl+Q", style="Tight.TButton", icon_name="exit")
        for b in (self.sidebar_btn, self.theme_btn, help_btn, exit_btn):
            b.pack(side="left", padx=(t.XS, 0))

    def toggle_sidebar(self):
        if self.sidebar.grid_info():
            self.sidebar.grid_remove()
            self.sidebar_btn.configure(text="Show panel")
            settings.set("sidebar_visible", False)
        else:
            self.sidebar.grid()
            self.sidebar_btn.configure(text="Hide panel")
            settings.set("sidebar_visible", True)

    def toggle_theme(self):
        mode = "light" if t.MODE == "dark" else "dark"
        t.set_mode(mode)
        settings.set("theme", mode)
        self.theme_btn.configure(text="Light mode" if mode == "dark" else "Dark mode")
        self.refresh_counts()

    # ------------------------------------------------------------ sidebar --
    def _build_connection(self, parent):
        box = card(parent, "Connection")
        box.pack(fill="x", pady=(0, t.M))
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="Username").grid(row=0, column=0, sticky="w", pady=t.XS)
        self.username_entry = ttk.Entry(box, width=16)
        self.username_entry.grid(row=0, column=1, sticky="ew", padx=(t.S, 0), pady=t.XS)
        Tooltip(self.username_entry, "SSH user that exists on every lab machine")

        ttk.Label(box, text="Password").grid(row=1, column=0, sticky="w", pady=t.XS)
        self.password_entry = PasswordEntry(box, width=10)
        self.password_entry.grid(row=1, column=1, sticky="ew", padx=(t.S, 0), pady=t.XS)

        self.connect_btn = self._btn(box, "Connect", "connect",
                                     "Connect to every host in the list over SSH",
                                     "Enter in the password field", style="Primary.TButton", icon="connect")
        self.connect_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(t.S, 0))

        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())
        self.password_entry.bind_entry("<Return>", self._wrap(self.actions["connect"]))

    def _build_session(self, parent):
        box = card(parent, "Session & power")
        box.pack(fill="x", pady=(0, t.M))
        box.columnconfigure((0, 1), weight=1, uniform="session")

        self._btn(box, "Send message…", "message", "Desktop notification on all connected hosts",
                  "Ctrl+M", style="Tight.TButton", icon="message").grid(row=0, column=0, sticky="ew", padx=(0, t.XS))
        self._btn(box, "Lock screens", "lock_screens", "Locks every session on all connected hosts",
                  "Ctrl+L", style="Tight.TButton", icon="lock").grid(row=0, column=1, sticky="ew", padx=(t.XS, 0))

        ttk.Separator(box).grid(row=1, column=0, columnspan=2, sticky="ew", pady=t.S)
        self._btn(box, "Shut down all…", "shutdown", "Powers off all connected hosts. Asks to confirm.",
                  style="Danger.TButton", icon="power").grid(row=2, column=0, columnspan=2, sticky="ew")

    def _build_users(self, parent):
        box = card(parent, "User management")
        box.pack(fill="x", pady=(0, t.M))
        box.columnconfigure((0, 1), weight=1, uniform="users")

        cells = [
            ("Lock user…",   "lock_user",       "Disables a user's password login on all hosts", "user_lock"),
            ("Unlock user…", "unlock_user",     "Re-enables a locked user on all hosts",         "user_unlock"),
            ("Password…",    "change_password", "Change the password of one or more users",      "key"),
            ("Add user…",    "add_user",        "Not implemented yet",                           "user_add"),
        ]
        for i, (text, key, tip, ic) in enumerate(cells):
            b = self._btn(box, text, key, tip, style="Tight.TButton", icon=ic)
            if self.actions.get(key) is None:
                b._never_enabled = True
            b.grid(row=i // 2, column=i % 2, sticky="ew",
                   padx=(0, t.XS) if i % 2 == 0 else (t.XS, 0), pady=(0, t.S))

        ttk.Separator(box).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, t.S))
        self._btn(box, "Delete user…", "delete_user",
                  "Deletes accounts and home folders on all hosts. Asks to confirm.",
                  style="Danger.TButton", icon="user_del").grid(row=3, column=0, columnspan=2, sticky="ew")

    # --------------------------------------------------------- main column --
    def _build_command(self, parent):
        box = card(parent, "Command")
        box.grid(row=0, column=0, sticky="ew", pady=(0, t.M))
        box.columnconfigure(0, weight=1)

        # created in reading order so Tab goes: command → Run → options → Stop
        self.cmd_entry = ttk.Entry(box, style="Mono.TEntry", font=t.FONTS["mono"])
        self.cmd_entry.grid(row=0, column=0, sticky="ew")
        Tooltip(self.cmd_entry, "Shell command to run on every connected host. Enter runs it.")
        self.cmd_entry.bind("<Return>", self._wrap(self.actions["run"]))

        self.run_btn = self._btn(box, "Run on all", "run", "Runs the command on every connected host",
                                 "Ctrl+Enter or F5", style="Primary.TButton", icon="play")
        self.run_btn.grid(row=0, column=1, sticky="ew", padx=(t.S, 0))

        opts = ttk.Frame(box)
        opts.grid(row=1, column=0, sticky="w", pady=(t.S, 0))
        sudo = ttk.Checkbutton(opts, text="Run as sudo", variable=self.is_sudo)
        sudo.pack(side="left", padx=(0, t.M))
        Tooltip(sudo, "Runs the command with sudo, using the connection password")
        disp = ttk.Checkbutton(opts, text="Use display (DISPLAY=:0)", variable=self.is_display)
        disp.pack(side="left")
        Tooltip(disp, "For commands that open a window on the host screen.\n"
                      "Note: not wired to the command runner yet.")

        self.stop_btn = button(box, "Stop", self._confirm_stop,
                               "Stops after the host currently being processed", "Ctrl+.", icon_name="stop")
        self.stop_btn.grid(row=1, column=1, sticky="ew", padx=(t.S, 0), pady=(t.S, 0))

    def _build_files(self, parent):
        box = card(parent, "File transfer")
        box.pack(fill="x")
        box.columnconfigure(0, weight=1)

        # label above each field: the sidebar is narrow
        ttk.Label(box, text="Source path").grid(row=0, column=0, columnspan=2, sticky="w")
        src = ttk.Entry(box, textvariable=self.src_var, width=16)
        src.grid(row=1, column=0, sticky="ew", pady=(t.XS, t.S))
        Tooltip(src, "Upload: a file on this computer.\nDownload: a file or folder on the hosts.")
        self._btn(box, "Browse…", "browse_src", "Pick a file on this computer",
                  style="Tight.TButton", icon="folder").grid(row=1, column=1, sticky="ew", padx=(t.S, 0), pady=(t.XS, t.S))

        ttk.Label(box, text="Destination path").grid(row=2, column=0, columnspan=2, sticky="w")
        des = ttk.Entry(box, textvariable=self.des_var, width=16)
        des.grid(row=3, column=0, sticky="ew", pady=(t.XS, t.S))
        Tooltip(des, "Upload: full path on the hosts, e.g. /home/student/notes.pdf\n"
                     "Downloads are saved to ~/Lab_master/pulls/<date>/<time>/<ip>/")
        self._btn(box, "Browse…", "browse_des", "Pick a local path (type remote paths by hand)",
                  style="Tight.TButton", icon="folder").grid(row=3, column=1, sticky="ew", padx=(t.S, 0), pady=(t.XS, t.S))

        self.file_row = ttk.Frame(box)
        self.file_row.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.file_btns = [
            self._btn(self.file_row, text, key, tip, sc, style="Tight.TButton", icon=ic)
            for text, key, tip, sc, ic in [
                ("Upload",          "upload",           "Copy the source file to the destination on every host", "Ctrl+U", "upload"),
                ("Upload as root",  "upload_sudo_move", "Upload, then move into place with sudo (for protected folders)", "", "upload_root"),
                ("Download",        "download",         "Fetch the source file from every host", "Ctrl+D", "download"),
                ("Download folder", "download_folder",  "Fetch the source folder from every host", "", "folder_download"),
            ]
        ]
        self._file_cols = 0
        box.bind("<Configure>", self._layout_file_buttons, add="+")
        self._layout_file_buttons()

    def _layout_file_buttons(self, _event=None):
        """One row of four buttons when there is room, otherwise a 2×2 grid."""
        self.file_row.update_idletasks()
        need = sum(b.winfo_reqwidth() for b in self.file_btns) + t.XS * 4
        avail = self.file_row.master.winfo_width() - 2 * t.M
        cols = 4 if avail <= 1 or avail >= need else 2
        if cols == self._file_cols:
            return
        self._file_cols = cols
        for c in range(4):
            self.file_row.columnconfigure(c, weight=1 if c < cols else 0, uniform="files" if c < cols else "")
        for i, b in enumerate(self.file_btns):
            b.grid(row=i // cols, column=i % cols, sticky="ew",
                   padx=(0, t.XS) if i % cols != cols - 1 else 0, pady=(0, t.XS if cols == 2 else 0))

    def _build_hosts(self, parent):
        box = card(parent, "Hosts")
        box.grid(row=1, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(3, weight=1)

        # -- toolbar: filter · show · sort · compact · refresh (wraps on narrow windows)
        bar = FlowFrame(box, gap=t.M)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, t.S))

        def group():
            g = ttk.Frame(bar)
            bar.add(g)
            return g

        g = group()
        ttk.Label(g, text="Filter").pack(side="left")
        self.filter_entry = ttk.Entry(g, textvariable=self.filter_var, width=14)
        self.filter_entry.pack(side="left", padx=(t.S, 0))
        Tooltip(self.filter_entry, "Filter by IP, hostname, user or status. Esc clears it.\n"
                                    "Only changes what is shown; commands still run on all connected hosts.",
                shortcut="Ctrl+F")
        self.filter_var.trace_add("write", lambda *_: self.grid.set_filter(self.filter_var.get()))
        self.filter_entry.bind("<Escape>", lambda e: (self.filter_var.set(""), "break")[1])

        g = group()
        ttk.Label(g, text="Show").pack(side="left")
        self.show_btn = ttk.Menubutton(g, text="All hosts", width=0)
        self.show_btn.pack(side="left", padx=(t.S, 0))
        Tooltip(self.show_btn, "Show only hosts with one status. Same as the chips below.")
        self._build_show_menu()
        t.on_change(self._build_show_menu)

        g = group()
        ttk.Label(g, text="Sort").pack(side="left")
        self.sort_btn = ttk.Menubutton(g, text=SORTS[self.sort_var.get()][0], width=0)
        self.sort_btn.pack(side="left", padx=(t.S, 0))
        Tooltip(self.sort_btn, "Order of the host tiles. Status puts failed and offline hosts first.")
        self._build_sort_menu()
        t.on_change(self._build_sort_menu)

        g = group()
        compact = ttk.Checkbutton(g, text="Compact", variable=self.compact, command=self._apply_compact)
        compact.pack(side="left", padx=(0, t.M))
        Tooltip(compact, "Compact tiles: hide IP and user details on each tile", shortcut="Ctrl+T")
        self._btn(g, "Refresh", "refresh", "Re-read hostname and logged-in users", "Ctrl+R",
                  style="Tight.TButton", icon="refresh").pack(side="left")

        # -- status chips
        self.chip_row = FlowFrame(box)
        self.chip_row.grid(row=1, column=0, sticky="ew", pady=(0, t.S))
        self.chips = {}
        for key in [""] + list(t.STATUS):
            chip = ttk.Radiobutton(self.chip_row, variable=self.status_var, value=key, style="Chip.Toolbutton",
                                   command=self._apply_status_filter)
            self.chip_row.add(chip)
            Tooltip(chip, "Show all hosts" if not key else f"Show only hosts that are {t.STATUS[key][1].lower()}")
            self.chips[key] = chip

        # -- first-run guide (hidden after the first successful connect)
        self.banner = ttk.Frame(box, style="Banner.TFrame", padding=(t.M, t.S))
        self.banner.grid(row=2, column=0, sticky="ew", pady=(0, t.S))
        steps = FlowFrame(self.banner, gap=t.M, style="Banner.TFrame")
        steps.pack(fill="x")
        for num, text in [("1", "Enter username and password"), ("2", "Press Connect"),
                          ("3", "Type a command and press Run on all")]:
            step = ttk.Frame(steps, style="Banner.TFrame")
            ttk.Label(step, text=num, style="BannerStep.TLabel").pack(side="left", padx=(0, t.S))
            ttk.Label(step, text=text, style="Banner.TLabel").pack(side="left")
            steps.add(step)
        ttk.Label(self.banner, text="Tip: right-click a host for more options · F1 lists all shortcuts",
                  style="BannerMuted.TLabel").pack(anchor="w", pady=(t.XS, 0))
        if not self.host_count:
            self.banner.grid_remove()

        # -- grid
        self.grid = HostGrid(box)
        self.grid.grid(row=3, column=0, sticky="nsew")
        self.grid.sort_key = self.sort_var.get()
        if self.compact.get():
            self.root.after_idle(self._apply_compact)

    def _build_sort_menu(self):
        menu = tk.Menu(self.sort_btn, tearoff=0, bg=t.SURFACE, fg=t.TEXT,
                       activebackground=t.SURFACE_3, activeforeground=t.TEXT,
                       selectcolor=t.FOCUS, bd=1, relief="solid", font=t.FONTS["body"])
        for key, (label, _fn) in SORTS.items():
            menu.add_radiobutton(label=label, value=key, variable=self.sort_var,
                                 command=self._apply_sort)
        self.sort_btn.configure(menu=menu)

    def _build_show_menu(self):
        menu = tk.Menu(self.show_btn, tearoff=0, bg=t.SURFACE, fg=t.TEXT,
                       activebackground=t.SURFACE_3, activeforeground=t.TEXT,
                       selectcolor=t.FOCUS, bd=1, relief="solid", font=t.FONTS["body"],
                       postcommand=lambda: self._fill_show_menu(menu))
        self.show_btn.configure(menu=menu)

    def _fill_show_menu(self, menu):
        """Rebuilt each time it opens, so the counts are current."""
        counts = self.grid.counts()
        menu.delete(0, "end")
        menu.add_radiobutton(label=f"All hosts ({len(self.grid.tiles)})", value="",
                             variable=self.status_var, command=self._apply_status_filter)
        menu.add_separator()
        for key, (glyph, label, _colour) in t.STATUS.items():
            menu.add_radiobutton(label=f"{glyph}  {label} ({counts[key]})", value=key,
                                 variable=self.status_var, command=self._apply_status_filter)

    def _apply_status_filter(self):
        """Shared by the Show dropdown and the chips: both use status_var."""
        key = self.status_var.get()
        self.grid.set_status_filter(key)
        self.show_btn.configure(text="All hosts" if not key else f"{t.STATUS[key][0]}  {t.STATUS[key][1]}")
        self.refresh_counts()

    def _apply_sort(self):
        key = self.sort_var.get()
        self.sort_btn.configure(text=SORTS[key][0])
        self.grid.set_sort(key)
        settings.set("sort", key)

    def _apply_compact(self):
        self.grid.set_compact(self.compact.get())
        settings.set("compact", self.compact.get())

    # ---------------------------------------------------------- behaviour --
    def _confirm_stop(self):
        if confirm(self.root, "Stop the current operation?",
                   "Hosts that were already processed keep their changes. "
                   "The host in progress finishes first.", "Stop", danger=False):
            self.actions["stop"]()

    def confirm_shutdown(self):
        n = self._connected_count()
        return confirm(self.root, "Shut down all hosts?",
                       f"{n} connected host(s) will power off immediately. "
                       "Anyone using them will lose unsaved work.", f"Shut down {n} host(s)")

    def show_help(self):
        width = max(len(k) for k, _ in SHORTCUTS)
        info(self.root, "Keyboard shortcuts",
             "\n".join(f"{k.ljust(width)}   {v}" for k, v in SHORTCUTS))

    def _bind_shortcuts(self):
        r = self.root
        def a(key):
            return self._wrap(self.actions.get(key))
        def toggle_compact(_e=None):
            self.compact.set(not self.compact.get())
            self._apply_compact()
        for seq, fn in [
            ("<Control-Return>", a("run")), ("<F5>", a("run")),
            ("<Control-period>", lambda e: self.busy and self._confirm_stop()),
            ("<Control-m>", a("message")), ("<Control-l>", a("lock_screens")),
            ("<Control-r>", a("refresh")), ("<Control-u>", a("upload")),
            ("<Control-d>", a("download")),
            ("<Control-f>", lambda e: (self.filter_entry.focus_set(), self.filter_entry.select_range(0, "end"), "break")[2]),
            ("<Control-g>", lambda e: (self.grid.focus_first(), "break")[1]),
            ("<Control-t>", toggle_compact),
            ("<Control-b>", lambda e: (self.toggle_sidebar(), "break")[1]),
            ("<F1>", lambda e: self.show_help()),
            ("<Control-q>", a("exit")),
        ]:
            r.bind(seq, fn)
