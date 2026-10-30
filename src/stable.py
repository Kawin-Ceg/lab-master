import tkinter as tk
from ui import theme, settings
from ui import start_screen as start
from ui import scan_screen as scan
from ui import fast_scan as fs
from ui import reliable_scan as rs
from ui import host_review as hr
from ui import dialogs
import json_reader
import work_screen as ws
import threading
import subprocess


# function to switch pages
def show(screen):
    """Raise a screen and move keyboard focus into it, so hidden screens get no key presses."""
    screen.tkraise()
    screen.focus_set()


def switch_to_start_page():
    show(start.screen)


def switch_to_scan_page():
    show(scan.screen)


def switch_to_fastscan_page():
    show(fs.screen)

def switch_to_reliable_scan_page():
    show(rs.screen)

def switch_to_host_review_page():
    show(hr.screen)

def switch_to_work_screen():
    show(ws.screen)
    ws.username_entry.focus_set()      # dashboard shortcuts work once focus is inside it


def go_back_to_scan_methods():
    show(scan.screen)


def go_home():
    show(start.screen)


# -------------------------------------------------------------
# Review -> Dashboard
# -------------------------------------------------------------
def open_dashboard():
    """Load the hosts chosen on the Review screen into the dashboard and show it."""
    ips = hr.hosts_for_dashboard()
    if not ips:
        return

    # A Reliable scan already asked for SSH credentials: reuse them so the
    # admin does not type them a second time on the dashboard.
    username = password = ""
    if hr.source_name == "Reliable scan":
        username = rs.username_entry.get().strip()
        password = rs.password_entry.get()

    ws.load_hosts(ips, source=hr.source_name, username=username, password=password)
    show(ws.screen)
    if username and password:
        ws.ui.connect_btn.focus_set()
    else:
        ws.username_entry.focus_set()


# -------------------------------------------------------------
# Open a saved IP list (skips scanning)
# -------------------------------------------------------------
def open_saved_list():
    ips = json_reader.read_any_file(main_frame)
    if not ips:
        return
    hr.set_hosts(ips, source=json_reader.last_file_name or "saved list")
    show(hr.screen)


# -------------------------------------------------------------
# Fast scan
# -------------------------------------------------------------
def fast_scan_btn_click():
    import shlex

    cmd = fs.text_box.get().strip()

    if not cmd:
        append_scan_output("Please enter a scan command.\n")
        return

    if fs.scan_thread and fs.scan_thread.is_alive():
        return

    try:
        args = shlex.split(cmd)
    except ValueError as exc:
        append_scan_output(f"Could not read the command: {exc}\n")
        return

    # masscan needs root: ask for the sudo password only when the command uses
    # "sudo -S" (read the password from stdin), and explain what it is for.
    sudo_password = None
    if args and args[0] == "sudo" and "-S" in args:
        sudo_password = dialogs.ask_password(
            main_frame,
            title="Password for sudo",
            subtitle="The scan runs masscan with sudo on this computer. "
                     "Enter your password for this computer (not the lab machines).",
            ok_text="Start scan")
        if not sudo_password:
            append_scan_output("Scan cancelled: no sudo password entered.\n")
            return

    hr.SCAN_DIR.mkdir(parents=True, exist_ok=True)
    try:
        hr.RESULTS_FILE.unlink()             # never show results from an older scan
    except FileNotFoundError:
        pass

    fs.stop_event.clear()

    fs.stop_btn.state(["!disabled"])
    fs.back_btn.state(["disabled"])
    fs.home_btn.state(["disabled"])
    fs.set_review_count(0)

    fs.text_area.delete("1.0", tk.END)
    fs.reset_output_count()
    fs.set_status("Scanning…", running=True, target=cmd)
    append_scan_output("Starting scan...\n")

    def run_scan():
        process = None
        stopped = False

        try:
            # Run inside SCAN_DIR so "-oJ ips.json" is written where the
            # Review screen reads it.
            process = subprocess.Popen(
                args,
                cwd=str(hr.SCAN_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            fs.scan_process = process

            if process.stdin:
                if sudo_password:
                    process.stdin.write(sudo_password + "\n")
                    process.stdin.flush()
                process.stdin.close()

            # readline() returns "" when the process ends or is terminated by
            # Stop; this works on Linux and Windows (select() on pipes does not).
            for line in iter(process.stdout.readline, ""):
                main_frame.after(0, lambda output=line: append_scan_output(output))
                if fs.stop_event.is_set():
                    stopped = True
                    process.terminate()
                    break

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            stopped = stopped or fs.stop_event.is_set()
            code = process.returncode
            main_frame.after(0, lambda: finish_scan(stopped, code))

        except Exception as exc:
            error_message = str(exc)
            main_frame.after(
                0,
                lambda msg=error_message: fail_scan(msg)
            )

        finally:
            fs.scan_process = None

    fs.scan_thread = threading.Thread(
        target=run_scan,
        daemon=True
    )
    fs.scan_thread.start()


def stop_fast_scan():
    fs.stop_event.set()

    fs.stop_btn.state(["disabled"])
    fs.set_status("Stopping…", running=True)
    append_scan_output("\nStopping scan...\n")

    process = fs.scan_process

    if process is not None and process.poll() is None:
        try:
            process.terminate()
        except OSError:
            pass


def finish_scan(stopped=False, code=0):
    if stopped:
        message = "\nScan stopped by user.\n"
        fs.set_status("Stopped", running=False)
    elif code:
        message = f"\nScan ended with an error (exit code {code}).\n"
        fs.set_status("Failed", running=False)
    else:
        message = "\nScan process finished.\n"
        fs.set_status("Finished", running=False)

    append_scan_output(message)

    fs.stop_btn.state(["disabled"])
    fs.back_btn.state(["!disabled"])
    fs.home_btn.state(["!disabled"])

    # Load whatever the scan saved straight into the Review screen.
    hr.load_hosts()
    found = len(hr.hosts)
    if found:
        append_scan_output(f"{found} host(s) with SSH found. Press “Review hosts” to continue.\n")
    elif not stopped:
        append_scan_output("No hosts with SSH (port 22) were found.\n")
    fs.set_review_count(found)


def fail_scan(message):
    append_scan_output(f"\nError: {message}\n")
    fs.set_status("Failed", running=False)

    fs.stop_btn.state(["disabled"])
    fs.back_btn.state(["!disabled"])
    fs.home_btn.state(["!disabled"])


def append_scan_output(line):
    fs.text_area.insert(tk.END, line)
    fs.text_area.see(tk.END)
    fs.increment_output_count(line)



# fixing the properties of the main frame
theme.enable_hidpi()
main_frame = tk.Tk()
main_frame.title("Lab master")
main_frame.geometry("800x600")
theme.apply(main_frame, settings.get("theme"))
main_frame.resizable(True, True)




start.initialize(main_frame)
scan.initialize(main_frame)
fs.initialize(main_frame)
rs.initialize(main_frame)
hr.initialize(main_frame)

# The dashboard starts empty; the Review screen fills it via open_dashboard().
ws.initialize(main_frame, on_new_scan=go_back_to_scan_methods)

fs.scan_btn.config(command=fast_scan_btn_click)
fs.stop_btn.config(command=stop_fast_scan)

# Reliable Scan controls
rs.scan_btn.config(
    command=lambda: rs.start_scan(main_frame)
)

rs.stop_btn.config(
    command=rs.stop_reliable_scan,
    state="disabled"
)


hr.dashboard_btn.config(
    command=open_dashboard
)

hr.back_btn.config(command=go_back_to_scan_methods)
hr.home_btn.config(command=go_home)

# Start screen -> Choose scan method
start.start_btn.config(
    command=switch_to_scan_page
)

# Choose scan method -> Fast scan
scan.fast_scan_btn.config(
    command=switch_to_fastscan_page
)

# Choose scan method -> Open a saved list
scan.open_list_btn.config(
    command=open_saved_list
)

# Choose scan method -> Reliable scan
scan.reliable_scan_btn.config(
    command=switch_to_reliable_scan_page
)

# Back/Home navigation
scan.back_btn.config(
    command=switch_to_start_page
)

scan.home_btn.config(
    command=switch_to_start_page
)

fs.back_btn.config(
    command=go_back_to_scan_methods
)

fs.home_btn.config(
    command=go_home
)

rs.back_btn.config(
    command=go_back_to_scan_methods
)

rs.home_btn.config(
    command=go_home
)

fs.review_btn.config(
    command=switch_to_host_review_page
)

rs.review_btn.config(
    command=switch_to_host_review_page
)




# intialily setting the page to be at teh start page
# (no password prompt here any more: each step asks for what it needs, once)
show(start.screen)


# start the listening of the events and view of screen
main_frame.mainloop()
