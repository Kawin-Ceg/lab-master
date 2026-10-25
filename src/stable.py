import tkinter as tk
from ui import theme
from ui import start_screen as start
from ui import scan_screen as scan
from ui import fast_scan as fs
from ui import reliable_scan as rs
from ui import host_review as hr
import work_screen as ws
import shell_process as sh_process
import get_password as password_window
from tkinter import ttk
import threading
import subprocess


# function to switch pages
password=""

def switch_to_start_page():
    start.screen.tkraise()


def switch_to_scan_page():
    scan.screen.tkraise()


def switch_to_fastscan_page():
    fs.screen.tkraise()

def switch_to_reliable_scan_page():
    rs.screen.tkraise()

def switch_to_host_review_page():
    hr.screen.tkraise()

def switch_to_work_screen():
    ws.screen.tkraise()


def go_back_to_scan_methods():
    scan.screen.tkraise()


def go_home():
    start.screen.tkraise()

def fast_scan_btn_click():
    cmd = fs.text_box.get().strip()

    if not cmd:
        fs.text_area.insert(tk.END, "Please enter a scan command.\n")
        return

    if fs.scan_thread and fs.scan_thread.is_alive():
        return

    fs.stop_event.clear()

    fs.scan_btn.config(state="disabled")
    fs.stop_btn.config(state="normal")
    fs.back_btn.config(state="disabled")
    fs.home_btn.config(state="disabled")

    fs.text_area.delete("1.0", tk.END)
    fs.text_area.insert(tk.END, "Starting scan...\n")

    def run_scan():
        import shlex
        import time

        process = None
        stopped = False

        try:
            args = shlex.split(cmd)

            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            

            fs.scan_process = process

            # Poll for output without blocking on readline().
            while process.poll() is None:
                if fs.stop_event.is_set():
                    stopped = True
                    process.terminate()
                    break

                # Read available output without waiting indefinitely.
                import os
                import select

                ready, _, _ = select.select(
                    [process.stdout],
                    [],
                    [],
                    0.1
                )

                if ready:
                    line = process.stdout.readline()
                    if line:
                        main_frame.after(
                            0,
                            lambda output=line: append_scan_output(output)
                        )

            if process.poll() is None:
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

            # Drain any remaining output.
            if process.stdout:
                remaining = process.stdout.read()
                if remaining:
                    main_frame.after(
                        0,
                        lambda output=remaining: append_scan_output(output)
                    )

            main_frame.after(0, lambda: finish_scan(stopped))

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

    fs.stop_btn.config(state="disabled")

    fs.text_area.insert(tk.END, "\nStopping scan...\n")
    fs.text_area.see(tk.END)

    process = fs.scan_process

    if process is not None and process.poll() is None:
        try:
            process.terminate()
        except OSError:
            pass



def finish_scan(stopped=False):
    if stopped:
        message = "\nScan stopped by user.\n"
    else:
        message = "\nScan process finished.\n"

    fs.text_area.insert(tk.END, message)
    fs.text_area.see(tk.END)

    fs.scan_btn.config(state="normal")
    fs.stop_btn.config(state="disabled")
    fs.back_btn.config(state="normal")
    fs.home_btn.config(state="normal")
    fs.review_btn.config(state="normal")
    


def fail_scan(message):
    fs.text_area.insert(tk.END, f"\nError: {message}\n")
    fs.text_area.see(tk.END)

    fs.scan_btn.config(state="normal")
    fs.stop_btn.config(state="disabled")
    fs.back_btn.config(state="normal")
    fs.home_btn.config(state="normal")


def append_scan_output(line):
    fs.text_area.insert(tk.END, line)
    fs.text_area.see(tk.END)


        
# fixing the properties of the main frame 
main_frame = tk.Tk()
main_frame.title("Lab master")
main_frame.geometry("800x600")
theme.apply(main_frame)
main_frame.resizable(True, True)




start.initialize(main_frame)
scan.initialize(main_frame)
fs.initialize(main_frame)
rs.initialize(main_frame)
hr.initialize(main_frame)

ws.initialize(main_frame)

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

rs.back_btn.config(
    command=go_back_to_scan_methods
)

rs.home_btn.config(
    command=go_home
)


hr.dashboard_btn.config(
    command=switch_to_work_screen
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
start.screen.tkraise()
password = password_window.get_password(main_frame)


#print("l" , password, "o", password)
# start the listening of the events and view of screen
main_frame.mainloop()
