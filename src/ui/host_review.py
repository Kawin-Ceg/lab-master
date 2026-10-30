import json
import re
import ipaddress
import tkinter as tk
from tkinter import ttk
from pathlib import Path

from . import theme as t
from . import widgets as w


# -------------------------------------------------------------
# State
# -------------------------------------------------------------
screen = None
host_tree = None
search_entry = None

summary_labels = {}          # status name (or "Total") -> number label
status_label = None
source_label = None
show_btn = None

back_btn = None
home_btn = None
refresh_btn = None
dashboard_btn = None

hosts = []
selected_host = None
source_name = ""             # "Fast scan" / "Reliable scan" / file name, shown on the dashboard

search_var = None
show_var = None              # "" = all statuses
_selected = set()            # selected IPs, kept while filtering hides rows
_repopulating = False
_sort = ("ip", False)        # (column, descending)

# Fast scan runs masscan inside SCAN_DIR, so its "-oJ ips.json" lands here.
SCAN_DIR = Path("~/Lab_master/scans").expanduser()
RESULTS_FILE = SCAN_DIR / "ips.json"

# Review status -> (glyph, theme status key for the colour, meaning)
STATUS_META = {
    "Reachable":    ("✔", "success",       "SSH login worked"),
    "Not tested":   ("○", "not_connected", "SSH port is open; login not tried yet"),
    "Login failed": ("⚠", "failed",        "Machine answered, but the username or password was rejected"),
    "Unreachable":  ("⊘", "offline",       "No answer on SSH (port 22)"),
}
STATUS_ORDER = list(STATUS_META)


# -------------------------------------------------------------
# Table colours (called again after a light/dark switch)
# -------------------------------------------------------------
def _style_table():
    style = ttk.Style()
    style.configure("HostReview.Treeview", background=t.SURFACE_2, fieldbackground=t.SURFACE_2,
                    foreground=t.TEXT, bordercolor=t.BORDER, rowheight=t.px(30), font=t.FONTS["body"])
    style.configure("HostReview.Treeview.Heading", background=t.SURFACE, foreground=t.TEXT,
                    font=t.FONTS["strong"], bordercolor=t.BORDER)
    style.map("HostReview.Treeview", background=[("selected", t.FOCUS)], foreground=[("selected", t.SURFACE)])
    style.map("HostReview.Treeview.Heading", background=[("active", t.SURFACE_3)])
    style.configure("Summary.TFrame", background=t.SURFACE, bordercolor=t.BORDER, relief="solid", borderwidth=1)
    for name, (_g, key, _m) in STATUS_META.items():
        style.configure(f"Sum{key}.TLabel", background=t.SURFACE, foreground=t.STATUS[key][2], font=t.FONTS["title"])
    style.configure("SumTotal.TLabel", background=t.SURFACE, foreground=t.TEXT, font=t.FONTS["title"])
    if host_tree is not None:
        for name, (_g, key, _m) in STATUS_META.items():
            host_tree.tag_configure(name, foreground=t.STATUS[key][2])


# -------------------------------------------------------------
# Initialize screen
# -------------------------------------------------------------
def initialize(parent):
    global screen, host_tree, search_entry, status_label, source_label, show_btn
    global back_btn, home_btn, refresh_btn, dashboard_btn
    global search_var, show_var

    _style_table()
    t.on_change(_style_table)
    search_var = tk.StringVar(master=parent)
    show_var = tk.StringVar(master=parent, value="")

    screen = ttk.Frame(parent, style="App.TFrame", padding=t.M)

    # -- header: title, subtitle, where am I
    header = ttk.Frame(screen, padding=(t.S, t.S))
    header.pack(fill="x", pady=(0, t.S))
    ttk.Label(header, text="Review hosts", style="Big.TLabel").pack(side="left")
    ttk.Label(header, text="Check what the scan found, then choose which machines to manage.",
              style="Muted.TLabel").pack(side="left", padx=(t.M, 0), pady=(t.XS, 0))
    w.step_indicator(header, current=2).pack(side="right")

    # -- navigation first, so the table can never push it off the screen
    nav = ttk.Frame(screen)
    nav.pack(side="bottom", fill="x", pady=(t.S, 0))
    back_btn = w.button(nav, "←  Back", None, "Choose a different way to find machines")
    back_btn.pack(side="left")
    home_btn = w.button(nav, "⌂  Home", None, "Return to the start screen")
    home_btn.pack(side="left", padx=(t.S, 0))
    dashboard_btn = w.button(nav, "Open dashboard  →", None,
                             "Open the dashboard with the selected hosts.\n"
                             "With nothing selected: every host that is not unreachable.",
                             "Enter", style="Primary.TButton")
    dashboard_btn.state(["disabled"])
    dashboard_btn.pack(side="right")

    status_label = ttk.Label(screen, style="Muted.TLabel")
    status_label.pack(side="bottom", anchor="w", pady=(t.S, 0))

    # -- summary cards
    summary = ttk.Frame(screen, style="App.TFrame")
    summary.pack(fill="x", pady=(0, t.S))
    cards = [("Total", "SumTotal.TLabel", "Every host the scan returned")] + [
        (name, f"Sum{key}.TLabel", meaning) for name, (_g, key, meaning) in STATUS_META.items()]
    for i, (name, style, meaning) in enumerate(cards):
        summary.columnconfigure(i, weight=1, uniform="sum")
        card = ttk.Frame(summary, style="Summary.TFrame", padding=(t.M, t.S))
        card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else t.S, 0))
        number = ttk.Label(card, text="0", style=style)
        number.pack(anchor="w")
        glyph = STATUS_META[name][0] + "  " if name in STATUS_META else ""
        ttk.Label(card, text=glyph + name, style="Muted.TLabel").pack(anchor="w")
        w.Tooltip(card, meaning)
        if name in STATUS_META:              # click a card = show only that status
            for widget in (card,) + tuple(card.winfo_children()):
                widget.bind("<Button-1>", lambda e, n=name: _set_show(n))
                widget.configure(cursor="hand2")
        summary_labels[name] = number

    # -- toolbar: search · show · selection helpers · refresh
    box = w.card(screen, "Discovered machines")
    box.pack(fill="both", expand=True)

    bar = w.FlowFrame(box, gap=t.M)
    bar.pack(fill="x", pady=(0, t.S))

    def group():
        g = ttk.Frame(bar)
        bar.add(g)
        return g

    g = group()
    ttk.Label(g, text="Search").pack(side="left")
    search_entry = ttk.Entry(g, textvariable=search_var, width=18)
    search_entry.pack(side="left", padx=(t.S, 0))
    w.Tooltip(search_entry, "Show only IPs containing this text. Esc clears it.", shortcut="Ctrl+F")
    search_var.trace_add("write", lambda *_: filter_hosts())
    search_entry.bind("<Escape>", lambda e: (search_var.set(""), "break")[1])

    g = group()
    ttk.Label(g, text="Show").pack(side="left")
    show_btn = ttk.Menubutton(g, text="All statuses", width=0)
    show_btn.pack(side="left", padx=(t.S, 0))
    w.Tooltip(show_btn, "Show only hosts with one status (or click a summary card above)")
    _build_show_menu()
    t.on_change(_build_show_menu)

    g = group()
    for text, cmd, tip in [
        ("Select all", _select_all_shown, "Select every host in the table (Ctrl+A)"),
        ("Select reachable", _select_reachable, "Select only hosts where the SSH login worked"),
        ("Clear", _clear_selection, "Clear the selection: the dashboard then gets every host that is not unreachable"),
    ]:
        w.button(g, text, cmd, tip, style="Tight.TButton").pack(side="left", padx=(0, t.XS))

    g = group()
    refresh_btn = w.button(g, "Reload last fast scan", load_hosts,
                           "Load the results of the most recent Fast scan again", style="Tight.TButton",
                           icon_name="refresh")
    refresh_btn.pack(side="left")

    source_label = ttk.Label(box, style="Muted.TLabel")
    source_label.pack(anchor="w", pady=(0, t.XS))

    # -- table
    table_frame = ttk.Frame(box)
    table_frame.pack(fill="both", expand=True)

    host_tree = ttk.Treeview(table_frame, columns=("ip", "port", "status"), show="headings",
                             style="HostReview.Treeview", selectmode="extended", height=6)
    for col, title, width, anchor in [("ip", "IP address", 240, "w"), ("port", "SSH port", 100, "center"),
                                      ("status", "SSH status", 220, "w")]:
        host_tree.heading(col, text=title, command=lambda c=col: _sort_by(c))
        host_tree.column(col, width=t.px(width), anchor=anchor)
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=host_tree.yview)
    host_tree.configure(yscrollcommand=scrollbar.set)
    host_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    w.Tooltip(host_tree, "Click to select · Ctrl/Shift+click for several · double-click opens just that host\n"
                         "Click a column title to sort")

    host_tree.bind("<<TreeviewSelect>>", on_host_selected)
    host_tree.bind("<Double-1>", _open_one)
    host_tree.bind("<Return>", lambda e: dashboard_btn.invoke() if dashboard_btn.instate(["!disabled"]) else None)
    host_tree.bind("<Control-a>", lambda e: (_select_all_shown(), "break")[1])
    screen.bind_all("<Control-f>", lambda e: _focus_search(), add="+")

    _style_table()
    screen.place(relwidth=1, relheight=1)
    set_hosts([])


def _focus_search():
    # only when the review screen is the one in front
    focus = screen.focus_get()
    if focus is not None and str(focus).startswith(str(screen)):
        search_entry.focus_set()
        return "break"


# -------------------------------------------------------------
# Show (status filter)
# -------------------------------------------------------------
def _build_show_menu():
    menu = tk.Menu(show_btn, tearoff=0, bg=t.SURFACE, fg=t.TEXT, activebackground=t.SURFACE_3,
                   activeforeground=t.TEXT, selectcolor=t.FOCUS, bd=1, relief="solid", font=t.FONTS["body"],
                   postcommand=lambda: _fill_show_menu(menu))
    show_btn.configure(menu=menu)


def _fill_show_menu(menu):
    counts = _counts()
    menu.delete(0, "end")
    menu.add_radiobutton(label=f"All statuses ({len(hosts)})", value="", variable=show_var,
                         command=lambda: _set_show(""))
    menu.add_separator()
    for name, (glyph, _k, _m) in STATUS_META.items():
        menu.add_radiobutton(label=f"{glyph}  {name} ({counts[name]})", value=name, variable=show_var,
                             command=lambda n=name: _set_show(n))


def _set_show(name):
    show_var.set(name)
    show_btn.configure(text="All statuses" if not name else f"{STATUS_META[name][0]}  {name}")
    filter_hosts()


def _counts():
    counts = {name: 0 for name in STATUS_META}
    for host in hosts:
        counts[host["status"]] = counts.get(host["status"], 0) + 1
    return counts


def _valid_ip(value):
    try:
        ipaddress.ip_address(str(value))
        return True
    except ValueError:
        return False


# -------------------------------------------------------------
# Status normalization
# -------------------------------------------------------------
def _normalize_status(value):
    if value is True:
        return "Reachable"

    if value is False:
        return "Unreachable"

    if value is None:
        return "Not tested"

    value = str(value).strip().lower()

    if value in {
        "reachable", "connected", "success", "successful"
    }:
        return "Reachable"

    if value in {
        "unreachable", "failed", "failure", "timeout"
    }:
        return "Unreachable"

    if value in {"authentication failed", "auth failed", "login failed"}:
        return "Login failed"

    # An open TCP port does not prove SSH authentication works.
    return "Not tested"


# -------------------------------------------------------------
# Parse Masscan JSON records
# -------------------------------------------------------------
def _parse_masscan_record(record):
    ip = record.get("ip") or record.get("ip_address")

    if not ip or not _valid_ip(ip):
        return None

    ports = record.get("ports", [])

    # Masscan commonly stores ports as a list of dictionaries.
    # Only include hosts with port 22 reported open.
    ssh_open = any(
        str(port.get("port")) == "22"
        and str(port.get("status", "")).lower() == "open"
        for port in ports
        if isinstance(port, dict)
    )

    if not ssh_open:
        return None

    return {
        "ip": str(ip),
        "port": 22,
        "status": "Not tested"
    }


# -------------------------------------------------------------
# Load hosts from saved JSON results
# -------------------------------------------------------------
def load_hosts():
    if not RESULTS_FILE.exists():
        set_hosts([])

        status_label.config(
            text="No fast-scan results yet. Run a scan first."
        )
        return

    try:
        text = RESULTS_FILE.read_text(encoding="utf-8")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # some masscan versions leave a trailing comma before the closing ]
            data = json.loads(re.sub(r",\s*\]\s*$", "]", text.strip()))

        if isinstance(data, dict):
            data = data.get("hosts", data.get("results", [data]))

        if not isinstance(data, list):
            raise ValueError("Expected a list of host records.")

        parsed = []

        for item in data:
            # A plain IP string can be used as an unverified host.
            if isinstance(item, str):
                ip = item.strip()

                if _valid_ip(ip):
                    parsed.append({
                        "ip": ip,
                        "port": 22,
                        "status": "Not tested"
                    })

                continue

            if not isinstance(item, dict):
                continue

            # Masscan JSON record.
            if "ports" in item:
                host = _parse_masscan_record(item)

                if host:
                    parsed.append(host)

                continue

            # Generic host record, including Reliable Scan results.
            ip = (
                item.get("ip")
                or item.get("ip_address")
                or item.get("address")
                or item.get("host")
            )

            if not ip or not _valid_ip(ip):
                continue

            port = item.get("port", 22)

            if str(port) != "22":
                continue

            parsed.append({
                "ip": str(ip),
                "port": 22,
                "status": _normalize_status(
                    item.get(
                        "status",
                        item.get("reachable", item.get("success"))
                    )
                )
            })

        # Merge duplicates, preferring a verified status over "Not tested".
        unique = {}

        for host in parsed:
            ip = host["ip"]

            if (
                ip not in unique
                or (
                    unique[ip]["status"] == "Not tested"
                    and host["status"] != "Not tested"
                )
            ):
                unique[ip] = host

        set_hosts(list(unique.values()), source="Fast scan")

    except (OSError, json.JSONDecodeError, ValueError) as exc:
        set_hosts([])

        status_label.config(
            text=f"Unable to read scan results: {exc}"
        )


# -------------------------------------------------------------
# Set results from another module
# -------------------------------------------------------------
def set_hosts(host_list, source=""):
    """Replace the table with new results (IP strings or {ip, port, status} records)."""
    global hosts, selected_host, source_name

    source_name = source
    normalized = []

    for item in host_list:
        if isinstance(item, str):
            ip = item.strip()
            if _valid_ip(ip):
                normalized.append({"ip": ip, "port": 22, "status": "Not tested"})
            continue

        if not isinstance(item, dict):
            continue

        ip = item.get("ip") or item.get("ip_address") or item.get("address") or item.get("host")
        if not ip or not _valid_ip(ip):
            continue
        if str(item.get("port", 22)) != "22":
            continue

        normalized.append({
            "ip": str(ip),
            "port": 22,
            "status": _normalize_status(item.get("status", item.get("reachable", item.get("success")))),
        })

    # merge duplicates, preferring a tested status over "Not tested"
    unique = {}
    for host in normalized:
        old = unique.get(host["ip"])
        if old is None or (old["status"] == "Not tested" and host["status"] != "Not tested"):
            unique[host["ip"]] = host

    hosts = sorted(unique.values(), key=lambda h: ipaddress.ip_address(h["ip"]))
    selected_host = None
    _selected.clear()
    if show_var is not None:
        _set_show("") if show_var.get() else filter_hosts()
    update_summary()

    if source_label is not None:
        source_label.configure(
            text=f"From: {source}  ·  {len(hosts)} host{'s' if len(hosts) != 1 else ''}" if hosts else "")


# -------------------------------------------------------------
# Table, filters and sorting
# -------------------------------------------------------------
def _shown_hosts():
    query = search_var.get().strip().lower() if search_var is not None else ""
    status = show_var.get() if show_var is not None else ""
    shown = [h for h in hosts if query in h["ip"].lower() and (not status or h["status"] == status)]

    col, desc = _sort
    if col == "status":
        key = lambda h: (STATUS_ORDER.index(h["status"]) if h["status"] in STATUS_ORDER else 99,
                         ipaddress.ip_address(h["ip"]))
    else:
        key = lambda h: ipaddress.ip_address(h["ip"])
    return sorted(shown, key=key, reverse=desc)


def populate_table(filtered_hosts=None):
    global _repopulating
    if host_tree is None:
        return
    _repopulating = True
    host_tree.delete(*host_tree.get_children())
    for host in (filtered_hosts if filtered_hosts is not None else _shown_hosts()):
        glyph = STATUS_META.get(host["status"], ("?",))[0]
        item = host_tree.insert("", "end", iid=host["ip"],
                                values=(host["ip"], host["port"], f"{glyph}  {host['status']}"),
                                tags=(host["status"],))
        if host["ip"] in _selected:
            host_tree.selection_add(item)
    _repopulating = False
    on_host_selected()


def filter_hosts(_event=None):
    shown = _shown_hosts()
    populate_table(shown)
    if status_label is None:
        return
    if not hosts:
        status_label.config(text="No hosts yet. Go back and run a Fast scan or Reliable scan, or open a saved IP list.")
    elif len(shown) < len(hosts):
        status_label.config(text=f"Showing {len(shown)} of {len(hosts)} hosts (filtered). "
                                 "Selected hosts stay selected while hidden.")
    else:
        status_label.config(text="Select rows to open only those, or continue with every host that is not "
                                 "unreachable. Double-click a row to open just that host.")


def _sort_by(col):
    global _sort
    _sort = (col, not _sort[1] if _sort[0] == col else False)
    arrow = " ▼" if _sort[1] else " ▲"
    for c, title in (("ip", "IP address"), ("port", "SSH port"), ("status", "SSH status")):
        host_tree.heading(c, text=title + (arrow if c == col else ""))
    populate_table()


# -------------------------------------------------------------
# Selection
# -------------------------------------------------------------
def _select_all_shown():
    host_tree.selection_set(host_tree.get_children())


def _select_reachable():
    reachable = [h["ip"] for h in hosts if h["status"] == "Reachable"]
    _selected.clear()
    _selected.update(reachable)
    populate_table()


def _clear_selection():
    _selected.clear()
    host_tree.selection_remove(host_tree.selection())
    on_host_selected()


def _open_one(event):
    item = host_tree.identify_row(event.y)
    if not item:
        return
    _selected.clear()
    _selected.add(item)
    host_tree.selection_set(item)
    if dashboard_btn.instate(["!disabled"]):
        dashboard_btn.invoke()


def on_host_selected(_event=None):
    """Keep the selected-IP set in step with the table and update the dashboard button."""
    global selected_host

    if dashboard_btn is None or host_tree is None:
        return

    if not _repopulating and _event is not None:
        shown = set(host_tree.get_children())
        _selected.difference_update(shown)                # hidden rows keep their state
        _selected.update(host_tree.selection())

    selected_host = None
    if len(_selected) == 1:
        ip = next(iter(_selected))
        host = next((h for h in hosts if h["ip"] == ip), None)
        if host:
            selected_host = dict(host)

    count = len(hosts_for_dashboard())
    if _selected:
        text = f"Open dashboard with {count} selected  →"
    else:
        text = f"Open dashboard with {count} host{'s' if count != 1 else ''}  →"
    dashboard_btn.configure(text=text)
    dashboard_btn.state(["!disabled"] if count else ["disabled"])


def hosts_for_dashboard():
    """
    IPs to open on the dashboard: the selected rows (also those hidden by a
    filter), or with nothing selected, every host except the unreachable ones.
    """
    if _selected:
        return [h["ip"] for h in sorted(hosts, key=lambda h: ipaddress.ip_address(h["ip"])) if h["ip"] in _selected]
    return [h["ip"] for h in sorted(hosts, key=lambda h: ipaddress.ip_address(h["ip"]))
            if h["status"] != "Unreachable"]


# -------------------------------------------------------------
# Summary cards
# -------------------------------------------------------------
def update_summary():
    if not summary_labels:
        return
    counts = _counts()
    summary_labels["Total"].config(text=str(len(hosts)))
    for name in STATUS_META:
        summary_labels[name].config(text=str(counts[name]))


def get_selected_host():
    return selected_host
