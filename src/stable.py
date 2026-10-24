# importing the library
import tkinter as tk
from ui import theme
from ui import start_screen as start
from ui import scan_screen as scan
from ui import fast_scan as fs
import shell_process as sh_process
import get_password as password_window
from tkinter import ttk


# function to switch pages
password=""

def switch_to_scan_page():
    scan.screen.tkraise()
    print("switched to scan page")

def switch_to_fastscan_page():
    fs.screen.tkraise()
    print("switched to mass scan or fast scan page")

def fast_scan_btn_click():
    cmd = fs.text_box.get()
   
    
    process_stdout = sh_process.run_cmd(cmd, password)

    for line in process_stdout:
        #print(line, end="") 
        
        print("found \\r @ (", line.find('\r'),") and \\n @ (",line.find('\n'),")")
        fs.text_area.insert(tk.END, line)     
        fs.text_area.see(tk.END)

        main_frame.update()
        
# fixing the properties of the main frame 
main_frame = tk.Tk()
main_frame.title("Lab master")
main_frame.geometry("800x600")
theme.apply(main_frame)
main_frame.resizable(True, True)




start.initialize(main_frame)
scan.initialize(main_frame)
fs.initialize(main_frame)
fs.scan_btn.config(command=fast_scan_btn_click)

start.over_the_network_btn.config(command=switch_to_scan_page)
scan.fast_scan_btn.config(command=switch_to_fastscan_page)



# intialily setting the page to be at teh start page
start.screen.tkraise()
_password =  password_window.get_password(main_frame)


print("l" , _password, "o", password)
# start the listening of the events and view of screen
main_frame.mainloop()
