"""
All pop-up windows of Lab Master. Each function blocks until the dialog
closes and returns what the user entered ("" / [] / None when cancelled).
Business logic stays in get_password.py and work_screen.py.
"""
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from datetime import date
import re

from . import theme as t
from .widgets import Dialog, PasswordEntry, Tooltip, confirm, icon_for


# --------------------------------------------------------------- IP file --
IP_FILE_TYPES = [("IP list (JSON or text)", "*.json *.txt"), ("JSON", "*.json"), ("Text", "*.txt")]


def ask_ip_file(main_frame):
    """Ask for the .json / .txt file listing the lab machines. Returns a path or ""."""
    dlg = Dialog(main_frame, "Open host list",
                 "Choose the file that lists the lab machines: a .json file like "
                 "src/ips.json, or a .txt file with one IP address per line.")
    path = tk.StringVar()
    error = ttk.Label(dlg.body, text="", style="Error.TLabel")

    row = ttk.Frame(dlg.body)
    ttk.Label(row, text="Host list file").pack(anchor="w")
    entry = ttk.Entry(row, textvariable=path, width=42)
    entry.pack(side="left", fill="x", expand=True, pady=(t.XS, 0))

    def browse():
        chosen = filedialog.askopenfilename(parent=dlg, title="Choose host list", filetypes=IP_FILE_TYPES)
        if chosen:
            path.set(chosen)
            error.configure(text="")

    ttk.Button(row, text="Browse…", command=browse).pack(side="left", padx=(t.S, 0), pady=(t.XS, 0))
    row.pack(fill="x")
    error.pack(anchor="w", pady=(t.S, 0))

    def ok():
        from pathlib import Path
        p = Path(path.get().strip()).expanduser()
        if not path.get().strip() or not p.is_file():
            error.configure(text="File not found. Choose an existing file.")
            return
        if p.suffix.lower() not in (".json", ".txt"):
            error.configure(text="Only .json or .txt files are supported.")
            return
        dlg.result = str(p)
        dlg.destroy()

    dlg.add_buttons("Open", ok)
    return dlg.run(focus=entry) or ""


# -------------------------------------------------------------- password --
def ask_password(main_frame):
    dlg = Dialog(main_frame, "Enter password")
    entry = PasswordEntry(dlg.body, width=28)
    entry.pack(fill="x")

    def ok():
        dlg.result = entry.get()
        dlg.destroy()

    dlg.add_buttons("OK", ok)
    return dlg.run(focus=entry.entry) or ""


# --------------------------------------------------------------- message --
def ask_message(main_frame, target="all connected hosts"):
    dlg = Dialog(main_frame, "Send message",
                 f"Shows a desktop notification to the person logged in on {target}.")
    text = tk.Text(dlg.body, width=44, height=6, wrap="word",
                   bg=t.SURFACE_2, fg=t.TEXT, insertbackground=t.TEXT,
                   relief="flat", highlightthickness=1,
                   highlightbackground=t.BORDER, highlightcolor=t.FOCUS,
                   padx=t.S, pady=t.S)
    text.pack(fill="both", expand=True)
    hint = ttk.Label(dlg.body, text="Ctrl+Enter to send", style="Muted.TLabel")
    hint.pack(anchor="w", pady=(t.XS, 0))
    error = ttk.Label(dlg.body, text="", style="Error.TLabel")
    error.pack(anchor="w")

    def ok():
        msg = text.get("1.0", "end").strip()
        if not msg:
            error.configure(text="Type a message first.")
            return
        dlg.result = msg
        dlg.destroy()

    ttk.Button(dlg.buttons, text="Send", style="Primary.TButton", command=ok).pack(side="right")
    ttk.Button(dlg.buttons, text="Cancel", command=dlg.cancel).pack(side="right", padx=(0, t.S))
    text.bind("<Control-Return>", lambda e: (ok(), "break")[1])
    return dlg.run(focus=text) or ""


# -------------------------------------------------------------- username --
def ask_username(main_frame, title, action_text, subtitle=""):
    dlg = Dialog(main_frame, title, subtitle)
    ttk.Label(dlg.body, text="Username").pack(anchor="w")
    entry = ttk.Entry(dlg.body, width=32)
    entry.pack(fill="x", pady=(t.XS, 0))
    error = ttk.Label(dlg.body, text="", style="Error.TLabel")
    error.pack(anchor="w", pady=(t.XS, 0))

    def ok():
        name = entry.get().strip()
        if not name:
            error.configure(text="Enter a username.")
            return
        dlg.result = name
        dlg.destroy()

    dlg.add_buttons(action_text, ok)
    return dlg.run(focus=entry) or ""


# ---------------------------------------------------- multi-user dialogs --
class _RowList:
    """A vertical list of repeated input rows with an 'Add another' button."""

    def __init__(self, dlg, build_row, add_text):
        self.rows = []
        self.build_row = build_row
        self.frame = ttk.Frame(dlg.body)
        self.frame.pack(fill="both", expand=True)
        ttk.Button(dlg.body, text=add_text, style="Ghost.TButton", command=self.add).pack(anchor="w", pady=(t.S, 0))
        self.add()

    def add(self):
        if self.rows:
            ttk.Separator(self.frame).pack(fill="x", pady=t.S)
        row = self.build_row(self.frame)
        self.rows.append(row)
        row["first"].focus_set()


def ask_new_passwords(main_frame):
    """Returns [[username, new_password], ...] or [] when cancelled."""
    dlg = Dialog(main_frame, "Change password",
                 "Sets a new password for these users on every connected host.")

    def build(parent):
        f = ttk.Frame(parent)
        f.pack(fill="x")
        ttk.Label(f, text="Username").grid(row=0, column=0, sticky="w", pady=t.XS)
        user = ttk.Entry(f, width=24)
        user.grid(row=0, column=1, sticky="ew", padx=(t.S, 0), pady=t.XS)
        ttk.Label(f, text="New password").grid(row=1, column=0, sticky="w", pady=t.XS)
        p1 = PasswordEntry(f, width=18)
        p1.grid(row=1, column=1, sticky="ew", padx=(t.S, 0), pady=t.XS)
        ttk.Label(f, text="Confirm password").grid(row=2, column=0, sticky="w", pady=t.XS)
        p2 = PasswordEntry(f, width=18)
        p2.grid(row=2, column=1, sticky="ew", padx=(t.S, 0), pady=t.XS)
        err = ttk.Label(f, text="", style="Error.TLabel")
        err.grid(row=3, column=0, columnspan=2, sticky="w")
        return {"first": user, "user": user, "p1": p1, "p2": p2, "error": err}

    rows = _RowList(dlg, build, "+ Add another user")

    def ok():
        valid = True
        for r in rows.rows:
            msg = ""
            if not r["user"].get().strip():
                msg = "Enter a username."
            elif not r["p1"].get():
                msg = "Enter a new password."
            elif r["p1"].get() != r["p2"].get():
                msg = "Passwords do not match."
            r["error"].configure(text=msg)
            valid = valid and not msg
        if valid:
            dlg.result = [[r["user"].get().strip(), r["p1"].get()] for r in rows.rows]
            dlg.destroy()

    dlg.add_buttons("Change password", ok)
    return dlg.run(focus=rows.rows[0]["first"]) or []


def ask_users_to_delete(main_frame):
    """Returns [username, ...] or [] when cancelled. Caller must confirm."""
    dlg = Dialog(main_frame, "Delete users",
                 "Deletes these accounts and their home folders on every connected host.")

    def build(parent):
        f = ttk.Frame(parent)
        f.pack(fill="x")
        ttk.Label(f, text="Username").pack(side="left")
        user = ttk.Entry(f, width=28)
        user.pack(side="left", fill="x", expand=True, padx=(t.S, 0))
        return {"first": user, "user": user}

    rows = _RowList(dlg, build, "+ Add another user")
    error = ttk.Label(dlg.body, text="", style="Error.TLabel")
    error.pack(anchor="w")

    def ok():
        names = [r["user"].get().strip() for r in rows.rows if r["user"].get().strip()]
        if not names:
            error.configure(text="Enter at least one username.")
            return
        dlg.result = names
        dlg.destroy()

    dlg.add_buttons("Continue…", ok, ok_style="Danger.TButton")
    return dlg.run(focus=rows.rows[0]["first"]) or []


# ------------------------------------------------------ single host menu --
def host_actions(main_frame, tile, on_message, on_lock, on_shutdown, on_terminal):
    """Action sheet for one host. Each callback receives no arguments."""
    title = tile.hostname or tile.ip_address
    connected = tile.status not in ("not_connected", "offline")
    subtitle = f"{tile.ip_address} · {t.STATUS[tile.status][1]}"
    if not connected:
        subtitle += "\nConnect first to send a message, lock or shut down this host."
    dlg = Dialog(main_frame, title, subtitle)

    def run(callback, close=True):
        if close:
            dlg.destroy()
        callback()

    def shutdown():
        if confirm(dlg, "Shut down this host?",
                   f"{title} ({tile.ip_address}) will power off immediately. "
                   "Anyone using it will lose unsaved work.", "Shut down"):
            run(on_shutdown)

    state = "!disabled" if connected else "disabled"
    items = [
        ("Open terminal",  "Opens an SSH session to this host in a new terminal window (Linux only).",
         lambda: run(on_terminal), "terminal", "!disabled"),
        ("Send message…",  "Shows a desktop notification on this host.", lambda: run(on_message), "message", state),
        ("Lock screen",    "Locks every session on this host.",          lambda: run(on_lock),    "lock",    state),
    ]
    for text, tip, cmd, ic, st in items:
        b = ttk.Button(dlg.body, text=f" {text}", command=cmd, image=icon_for(ic), compound="left")
        b.state([st])
        b.pack(fill="x", pady=(0, t.S))
        Tooltip(b, tip)

    ttk.Separator(dlg.body).pack(fill="x", pady=(t.S, t.M))
    sd = ttk.Button(dlg.body, text=" Shut down…", style="Danger.TButton", command=shutdown,
                    image=icon_for("power", "Danger.TButton"), compound="left")
    sd.state([state])
    sd.pack(fill="x")

    ttk.Button(dlg.buttons, text="Close", command=dlg.cancel).pack(side="right")
    dlg.run(focus=dlg.body.winfo_children()[0])

# ------------------------------------------------------------ output viewer --
def show_output(main_frame, ip):
    """Display command history and output for a host."""

    log_root = Path("~/Lab_master/logs").expanduser()

    # Find all log files belonging to this IP.
    log_files = sorted(
        (
            path
            for path in log_root.glob("*/*/*")
            if path.is_file() and path.name == ip
        ),
        key=lambda path: (path.parent.parent.name, path.parent.name),
    )

    dlg = Dialog(
        main_frame,
        "Command History",
        f"Command output and execution history for {ip}",
    )

    # Scrollable output area.
    container = ttk.Frame(dlg.body)
    container.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(container, orient="vertical")
    scrollbar.pack(side="right", fill="y")

    output = tk.Text(
        container,
        wrap="word",
        font=("TkFixedFont", 10),
        height=22,
        width=82,
        bg="#15191f",
        fg="#e6edf3",
        insertbackground="#e6edf3",
        relief="flat",
        padx=14,
        pady=12,
        yscrollcommand=scrollbar.set,
        state="disabled",
    )
    output.pack(side="left", fill="both", expand=True)
    scrollbar.configure(command=output.yview)

    # Colour the command status indicators.
    output.tag_configure("success", foreground="#4ade80")
    output.tag_configure("failure", foreground="#f87171")
    output.tag_configure("command", foreground="#7dd3fc")
    output.tag_configure("muted", foreground="#9ca3af")
    output.tag_configure("body", foreground="#e6edf3")

    def append(text, tag=None):
        output.insert("end", text, tag)

    if not log_files:
        append("No command history found for this host.\n", "muted")
        append(
            "\nLogs will appear here after commands have been executed "
            "through Lab Master.",
            "body",
        )
    else:
        for log_file in log_files:
            try:
                raw = log_file.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                append(f"Could not read {log_file}:\n{exc}\n\n", "failure")
                continue

            # Each record begins with CMD_EXECUTED and ends with EXIT_CODE.
            records = re.split(r"(?=^CMD_EXECUTED = )", raw, flags=re.MULTILINE)

            for record in records:
                record = record.strip("\n")
                if not record.strip():
                    continue

                lines = record.splitlines()
                command_line = lines[0]

                if not command_line.startswith("CMD_EXECUTED = "):
                    append(record + "\n\n", "body")
                    continue

                command = command_line[len("CMD_EXECUTED = "):]
                exit_index = next(
                    (
                        i for i, line in enumerate(lines)
                        if line.startswith("EXIT_CODE: ")
                    ),
                    None,
                )

                if exit_index is None:
                    result_lines = lines[1:]
                    exit_code = None
                else:
                    result_lines = lines[1:exit_index]
                    try:
                        exit_code = int(
                            lines[exit_index].split(":", 1)[1].strip()
                        )
                    except ValueError:
                        exit_code = None

                if exit_code == 0:
                    append("✔  ", "success")
                elif exit_code is not None:
                    append("✖  ", "failure")
                else:
                    append("◐  ", "muted")

                append(command + "\n", "command")

                if exit_code is None:
                    append("   Exit code: unavailable\n", "muted")
                else:
                    tag = "success" if exit_code == 0 else "failure"
                    append(f"   Exit code: {exit_code}\n", tag)

                append("   " + "─" * 48 + "\n", "muted")

                if result_lines:
                    append("\n".join(result_lines) + "\n", "body")
                else:
                    append("(No output)\n", "muted")

                append("\n\n")

    output.configure(state="disabled")
    output.yview_moveto(0)

    ttk.Button(
        dlg.buttons,
        text="Close",
        command=dlg.cancel,
    ).pack(side="right")

    dlg.run()