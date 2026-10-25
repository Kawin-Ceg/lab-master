"""
Main dashboard layout.

    ┌ header ───────────────────────────────────────────────┐
    │ sidebar: Connection    │ Command                      │
    │          Session/power │ File transfer                │
    │          Users         │ Hosts (filter, grid)         │
    ├ status bar ───────────────────────────────────────────┤

The window knows nothing about SSH. work_screen.py passes in an `actions`
dict of callbacks and reads the inputs through the attributes below.
"""
import tkinter as tk
from tkinter import ttk

from . import theme as t
from .widgets import (button, card, confirm, info, PasswordEntry, Tooltip,
                      HostGrid, StatusBar)


SHORTCUTS = [
    ("Enter (in password)", "Connect"),
    ("Ctrl+Enter / F5",     "Run command on all connected hosts"),
    ("Ctrl+.",              "Stop after the current host"),
    ("Ctrl+M",              "Send message"),
    ("Ctrl+L",              "Lock all screens"),
    ("Ctrl+R",              "Refresh host info"),
    ("Ctrl+U",              "Upload source file"),
    ("Ctrl+D",              "Download source file"),
    ("Ctrl+F",              "Filter hosts"),
    ("Ctrl+T",              "Toggle compact host tiles"),
    ("F1",                  "Show this help"),
    ("Ctrl+Q",              "Exit"),
    ("",                    ""),
    ("Shut down, Delete user", "No shortcut on purpose. Always asks to confirm."),
]


class MainWindow:

    SIDEBAR_WIDTH = 320

    def __init__(self, root, actions, src_var, des_var,
             source_name="", host_count=0, content_frame=None):

        self.root = root
        self.actions = actions
        self.busy = False
        self._action_buttons = []

        # Use a separate frame for dashboard content.
        self.content_frame = content_frame if content_frame is not None else root
        content = self.content_frame

        self.is_sudo = tk.BooleanVar(master=root, value=False)
        self.is_display = tk.BooleanVar(master=root, value=False)
        self.compact = tk.BooleanVar(master=root, value=False)
        self.filter_var = tk.StringVar(master=root)
        self.src_var = src_var
        self.des_var = des_var

        content.configure(bg=t.BG)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        # Build dashboard widgets inside the content frame.
        self._build_header(source_name, host_count)
        body = ttk.Frame(content, style="App.TFrame", padding=(t.M, 0, t.M, t.M))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(body, style="App.TFrame", width=self.SIDEBAR_WIDTH)
        sidebar.grid(row=0, column=0, sticky="nsw", padx=(0, t.M))
        main = ttk.Frame(body, style="App.TFrame")
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        self._build_connection(sidebar)
        self._build_session(sidebar)
        self._build_users(sidebar)
        self._build_command(main)
        self._build_files(main)
        self._build_hosts(main)

        self.status_bar = StatusBar(content)
        self.status_bar.grid(row=2, column=0, sticky="ew")

        self._bind_shortcuts()
        self.set_busy(False)
        root.protocol("WM_DELETE_WINDOW", self._wrap(actions["exit"]))
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
        self.status_bar.set_host_counts(self.grid.counts())

    def set_connected(self):
        """After the first connect, Run becomes the only primary action."""
        self.dashboard_btn.configure(style="TButton", text="Reconnect missing")
        Tooltip(self.dashboard_btn, "Retries hosts that are not connected yet.\nShortcut: Enter in the password field")

    # ------------------------------------------------------------- header --
    def _build_header(self, source_name, host_count):
        header = ttk.Frame(self.content_frame, style="App.TFrame",
                   padding=(t.M, t.S, t.M, t.S))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Lab Master", style="Title.TLabel").pack(side="left")
        detail = f"{host_count} hosts loaded" + (f" from {source_name}" if source_name else "")
        ttk.Label(header, text=detail, style="AppMuted.TLabel").pack(side="left", padx=(t.M, 0), pady=(t.XS, 0))
        button(header, "Exit", self._wrap(self.actions["exit"]), "Close all connections and quit",
               "Ctrl+Q", style="Tight.TButton", icon_name="exit").pack(side="right")
        button(header, "Help", self.show_help, "Keyboard shortcuts", "F1",
               style="Tight.TButton", icon_name="help").pack(side="right", padx=(0, t.S))

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

        self.dashboard_btn = self._btn(box, "Connect", "connect",
                                     "Connect to every host in the list over SSH",
                                     "Enter in the password field", style="Primary.TButton", icon="connect")
        self.dashboard_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(t.S, 0))

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

        self.cmd_entry = ttk.Entry(box, style="Mono.TEntry", font=t.FONTS["mono"])
        self.cmd_entry.grid(row=0, column=0, sticky="ew")
        Tooltip(self.cmd_entry, "Shell command to run on every connected host")
        self.cmd_entry.bind("<Return>", self._wrap(self.actions["run"]))

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
        self.run_btn = self._btn(box, "Run on all", "run", "Runs the command on every connected host",
                                 "Ctrl+Enter or F5", style="Primary.TButton", icon="play")
        self.run_btn.grid(row=0, column=1, sticky="ew", padx=(t.S, 0))

    def _build_files(self, parent):
        box = card(parent, "File transfer")
        box.grid(row=1, column=0, sticky="ew", pady=(0, t.M))
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="Source path").grid(row=0, column=0, sticky="w", pady=t.XS)
        src = ttk.Entry(box, textvariable=self.src_var)
        src.grid(row=0, column=1, sticky="ew", padx=t.S, pady=t.XS)
        Tooltip(src, "Upload: a file on this computer.\nDownload: a file or folder on the hosts.")
        self._btn(box, "Browse…", "browse_src", "Pick a file on this computer", style="Tight.TButton", icon="folder").grid(row=0, column=2, pady=t.XS)

        ttk.Label(box, text="Destination path").grid(row=1, column=0, sticky="w", pady=t.XS)
        des = ttk.Entry(box, textvariable=self.des_var)
        des.grid(row=1, column=1, sticky="ew", padx=t.S, pady=t.XS)
        Tooltip(des, "Upload: full path on the hosts, e.g. /home/student/notes.pdf\n"
                     "Downloads are saved to ~/Lab_master/pulls/<date>/<time>/<ip>/")
        self._btn(box, "Browse…", "browse_des", "Pick a local path (type remote paths by hand)", style="Tight.TButton", icon="folder").grid(row=1, column=2, pady=t.XS)

        row = ttk.Frame(box)
        row.grid(row=2, column=0, columnspan=3, sticky="w", pady=(t.S, 0))
        for text, key, tip, sc, ic in [
            ("Upload",          "upload",           "Copy the source file to the destination on every host", "Ctrl+U", "upload"),
            ("Upload as root",  "upload_sudo_move", "Upload, then move into place with sudo (for protected folders)", "", "upload_root"),
            ("Download",        "download",         "Fetch the source file from every host", "Ctrl+D", "download"),
            ("Download folder", "download_folder",  "Fetch the source folder from every host", "", "folder_download"),
        ]:
            self._btn(row, text, key, tip, sc, style="Tight.TButton", icon=ic).pack(side="left", padx=(0, t.XS))

    def _build_hosts(self, parent):
        box = card(parent, "Hosts")
        box.grid(row=2, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(1, weight=1)

        bar = ttk.Frame(box)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, t.S))
        ttk.Label(bar, text="Filter").pack(side="left")
        self.filter_entry = ttk.Entry(bar, textvariable=self.filter_var, width=20)
        self.filter_entry.pack(side="left", padx=(t.S, t.M))
        Tooltip(self.filter_entry, "Filter by IP, hostname, user or status.\n"
                                    "Only changes what is shown; commands still run on all connected hosts.\n"
                                    "Shortcut: Ctrl+F")
        self.filter_var.trace_add("write", lambda *_: self.grid.set_filter(self.filter_var.get()))

        self._btn(bar, "Refresh", "refresh", "Re-read hostname and logged-in users", "Ctrl+R", style="Tight.TButton", icon="refresh").pack(side="right")
        compact = ttk.Checkbutton(bar, text="Compact tiles", variable=self.compact,
                                  command=lambda: self.grid.set_compact(self.compact.get()))
        compact.pack(side="right", padx=(0, t.M))
        Tooltip(compact, "Hide IP and user details on each tile.\nShortcut: Ctrl+T")

        self.grid = HostGrid(box)
        self.grid.grid(row=1, column=0, sticky="nsew")

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
        for seq, fn in [
            ("<Control-Return>", a("run")), ("<F5>", a("run")),
            ("<Control-period>", lambda e: self.busy and self._confirm_stop()),
            ("<Control-m>", a("message")), ("<Control-l>", a("lock_screens")),
            ("<Control-r>", a("refresh")), ("<Control-u>", a("upload")),
            ("<Control-d>", a("download")),
            ("<Control-f>", lambda e: (self.filter_entry.focus_set(), "break")[1]),
            ("<Control-t>", lambda e: (self.compact.set(not self.compact.get()),
                                       self.grid.set_compact(self.compact.get()))),
            ("<F1>", lambda e: self.show_help()),
            ("<Control-q>", a("exit")),
        ]:
            r.bind(seq, fn)
