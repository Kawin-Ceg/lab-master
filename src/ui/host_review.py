import json
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

total_hosts_label = None
reachable_hosts_label = None
unreachable_hosts_label = None
status_label = None

back_btn = None
home_btn = None
refresh_btn = None
dashboard_btn = None

hosts = []
selected_host = None

# Path is relative to the project root, not the current directory.
RESULTS_FILE = Path(__file__).resolve().parents[1] / "ips.json"

STATIC_HOSTS = [
    {
        "ip": "10.11.96.103",
        "port": 22,
        "status": "Not tested"
    },
    {
        "ip": "10.11.96.128",
        "port": 22,
        "status": "Not tested"
    },
    {
        "ip": "127.0.0.1",
        "port": 22,
        "status": "Not tested"
    },
    {
        "ip": "127.0.0.2",
        "port": 22,
        "status": "Not tested"
    }
]

# -------------------------------------------------------------
# Initialize screen
# -------------------------------------------------------------
def initialize(parent):
    global screen, host_tree, search_entry
    global total_hosts_label, reachable_hosts_label
    global unreachable_hosts_label, status_label
    global back_btn, home_btn, refresh_btn, dashboard_btn

    style = ttk.Style(screen)

    style.configure(
        "HostReview.Treeview",
        background=t.SURFACE_2,
        fieldbackground=t.SURFACE_2,
        foreground=t.TEXT,
        bordercolor=t.BORDER,
        rowheight=32,
        font=t.FONTS["body"]
    )

    style.configure(
        "HostReview.Treeview.Heading",
        background=t.SURFACE,
        foreground=t.TEXT,
        font=t.FONTS["strong"],
        bordercolor=t.BORDER
    )

    style.map(
        "HostReview.Treeview",
        background=[("selected", t.FOCUS)],
        foreground=[("selected", t.BG)]
    )

    style.map(
        "HostReview.Treeview.Heading",
        background=[("active", t.SURFACE_3)]
    )

    screen = ttk.Frame(
        parent,
        style="App.TFrame",
        padding=t.M
    )

    # Header
    header = ttk.Frame(screen)
    header.pack(fill="x", pady=(0, t.S))

    ttk.Label(
        header,
        text="Review Hosts",
        font=t.FONTS["title"]
    ).pack(anchor="w")

    ttk.Label(
        header,
        text="Step 2 of 3 · Review discovered machines before connecting.",
        style="Muted.TLabel"
    ).pack(anchor="w", pady=(t.XS, 0))

    # Workflow
    workflow = ttk.Frame(screen)
    workflow.pack(fill="x", pady=(0, t.M))

    steps = [
        ("01", "Scan", False),
        ("02", "Review Hosts", True),
        ("03", "Dashboard", False)
    ]

    for index, (number, title, active) in enumerate(steps):
        step = ttk.Frame(workflow)
        step.pack(side="left", fill="x", expand=True)

        ttk.Label(
            step,
            text=number,
            font=t.FONTS["heading"],
            style="TLabel" if active else "Muted.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            step,
            text=title,
            font=t.FONTS["caption"],
            style="TLabel" if active else "Muted.TLabel"
        ).pack(anchor="w", pady=(t.XS, 0))

        if index < len(steps) - 1:
            ttk.Label(
                workflow,
                text="→",
                style="Muted.TLabel"
            ).pack(side="left", padx=t.XS)

    # Summary cards
    summary = ttk.Frame(screen)
    summary.pack(fill="x", pady=(0, t.M))

    total_hosts_label = _create_summary_card(
        summary, "Hosts Discovered", "0"
    )

    reachable_hosts_label = _create_summary_card(
        summary, "SSH Reachable", "0"
    )

    unreachable_hosts_label = _create_summary_card(
        summary, "SSH Unreachable", "0"
    )

    # Toolbar
    toolbar = ttk.Frame(screen)
    toolbar.pack(fill="x", pady=(0, t.S))

    ttk.Label(
        toolbar,
        text="Discovered Machines",
        font=t.FONTS["heading"]
    ).pack(side="left")

    refresh_btn = w.button(
        toolbar,
        text="Refresh",
        command=load_hosts,
        tooltip="Reload the latest saved scan results",
        style="TButton"
    )
    refresh_btn.pack(side="right")

    # Search
    search_row = ttk.Frame(screen)
    search_row.pack(fill="x", pady=(0, t.S))

    ttk.Label(
        search_row,
        text="Search IP:",
        style="Muted.TLabel"
    ).pack(side="left", padx=(0, t.S))

    search_entry = ttk.Entry(search_row)
    search_entry.pack(side="left", fill="x", expand=True)
    search_entry.bind("<KeyRelease>", filter_hosts)

    # Host table
    table_frame = ttk.Frame(screen)
    table_frame.pack(fill="both", expand=True)

    columns = ("ip", "port", "status")

    host_tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        style="HostReview.Treeview",
        selectmode="none"
    )

    host_tree.heading("ip", text="IP Address")
    host_tree.heading("port", text="SSH Port")
    host_tree.heading("status", text="SSH Status")

    host_tree.column("ip", width=240, anchor="w")
    host_tree.column("port", width=100, anchor="center")
    host_tree.column("status", width=180, anchor="center")

    scrollbar = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=host_tree.yview
    )

    host_tree.configure(yscrollcommand=scrollbar.set)

    host_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    #host_tree.bind("<<TreeviewSelect>>", on_host_selected)

    # Status
    status_label = ttk.Label(
        screen,
        text="Loading scan results...",
        style="Muted.TLabel"
    )
    status_label.pack(anchor="w", pady=(t.S, 0))

    # Navigation and actions
    nav = ttk.Frame(screen)
    nav.pack(fill="x", pady=(t.M, 0))

    back_btn = w.button(
        nav,
        text="Back",
        command=lambda: None,
        tooltip="Return to the scan-method selection screen"
    )
    back_btn.pack(side="left")

    home_btn = w.button(
        nav,
        text="Home",
        command=lambda: None,
        tooltip="Return to the start screen"
    )
    home_btn.pack(side="left", padx=(t.S, 0))

    dashboard_btn = w.button(
        nav,
        text="Go to Dashboard →",
        command=lambda: None,
        tooltip="Open the existing Lab Master dashboard",
        style="Primary.TButton"
    )
    dashboard_btn.pack(side="right")

    # Fill parent
    screen.place(relwidth=1, relheight=1)

    set_hosts(STATIC_HOSTS)

    status_label.config(
        text="Showing the four configured hosts. Connection status has not been tested."
    )


# -------------------------------------------------------------
# Summary card
# -------------------------------------------------------------
def _create_summary_card(parent, title, initial_value):
    card = w.card(parent, title)

    card.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, t.S)
    )

    value_label = ttk.Label(
        card,
        text=initial_value,
        font=t.FONTS["heading"]
    )
    value_label.pack(anchor="w", padx=t.XS, pady=t.XS)

    return value_label


# -------------------------------------------------------------
# IP validation
# -------------------------------------------------------------
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
            text=f"No scan results found at {RESULTS_FILE.name}. Run a scan first."
        )
        return

    try:
        with RESULTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

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

        set_hosts(list(unique.values()))

        status_label.config(
            text=f"Loaded {len(hosts)} host(s) from {RESULTS_FILE.name}."
        )

    except (OSError, json.JSONDecodeError, ValueError) as exc:
        set_hosts([])

        status_label.config(
            text=f"Unable to read scan results: {exc}"
        )


# -------------------------------------------------------------
# Set results from another module
# -------------------------------------------------------------
def set_hosts(host_list):
    global hosts, selected_host

    normalized = []

    for item in host_list:
        if isinstance(item, str):
            ip = item.strip()

            if _valid_ip(ip):
                normalized.append({
                    "ip": ip,
                    "port": 22,
                    "status": "Not tested"
                })

            continue

        if not isinstance(item, dict):
            continue

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

        normalized.append({
            "ip": str(ip),
            "port": 22,
            "status": _normalize_status(
                item.get(
                    "status",
                    item.get("reachable", item.get("success"))
                )
            )
        })

    unique = {}

    for host in normalized:
        ip = host["ip"]

        if (
            ip not in unique
            or (
                unique[ip]["status"] == "Not tested"
                and host["status"] != "Not tested"
            )
        ):
            unique[ip] = host

    hosts = sorted(
        unique.values(),
        key=lambda host: ipaddress.ip_address(host["ip"])
    )

    selected_host = None

    populate_table()
    update_summary()


# -------------------------------------------------------------
# Populate table
# -------------------------------------------------------------
def populate_table(filtered_hosts=None):
    if host_tree is None:
        return

    for item in host_tree.get_children():
        host_tree.delete(item)

    displayed = hosts if filtered_hosts is None else filtered_hosts

    for host in displayed:
        host_tree.insert(
            "",
            "end",
            values=(
                host["ip"],
                host["port"],
                host["status"]
            )
        )


# -------------------------------------------------------------
# Search
# -------------------------------------------------------------
def filter_hosts(_event=None):
    query = search_entry.get().strip().lower()

    filtered = [
        host for host in hosts
        if query in host["ip"].lower()
    ]

    populate_table(filtered)

    status_label.config(
        text=f"Showing {len(filtered)} of {len(hosts)} host(s)."
    )


# -------------------------------------------------------------
# Host selection
# -------------------------------------------------------------
def on_host_selected(_event=None):
    global selected_host

    selection = host_tree.selection()

    if not selection:
        selected_host = None
        dashboard_btn.config(state="disabled")
        return

    values = host_tree.item(selection[0], "values")

    if not values:
        selected_host = None
        dashboard_btn.config(state="disabled")
        return

    selected_host = {
        "ip": values[0],
        "port": int(values[1]),
        "status": values[2]
    }

    # Only hosts verified by the SSH connection check can connect.
    dashboard_btn.config(
        state=(
            "normal"
            if selected_host["status"] == "Reachable"
            else "disabled"
        )
    )

    status_label.config(
        text=f"Selected {selected_host['ip']} · {selected_host['status']}"
    )


# -------------------------------------------------------------
# Update summary cards
# -------------------------------------------------------------
def update_summary():
    total = len(hosts)

    reachable = sum(
        host["status"] == "Reachable"
        for host in hosts
    )

    unreachable = sum(
        host["status"] == "Unreachable"
        for host in hosts
    )

    total_hosts_label.config(text=str(total))
    reachable_hosts_label.config(text=str(reachable))
    unreachable_hosts_label.config(text=str(unreachable))


# -------------------------------------------------------------
# Retrieve selected host for stable.py
# -------------------------------------------------------------
def get_selected_host():
    return selected_host


# -------------------------------------------------------------
# Connect action
# -------------------------------------------------------------
def connect_selected_host():
    host = get_selected_host()

    if not host:
        return

    if host["status"] != "Reachable":
        status_label.config(
            text="Verify SSH connectivity before connecting."
        )
        return

    # stable.py should replace this with the existing dashboard
    # navigation and SSH connection logic.
    status_label.config(
        text=f"Selected {host['ip']}. Dashboard connection is not wired yet."
    )