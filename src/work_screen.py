import traceback as traceback
import tkinter as tk
import paramiko as paramiko
import os as os
import datetime as datetime
import configparser as configparser
import remote_connection as remote_connection
import json_reader as json_reader
import find_user as find_user
from tkinter import filedialog
from tkinter import ttk
from ui import theme, settings
from ui.widgets import HostTile, confirm
from ui.main_window import MainWindow
from pathlib import Path
from base_dir import BASE_DIR


current_date = datetime.date.today()
current_time = datetime.datetime.now().strftime("%H_%M")
print("staring date:", current_date, " starting time:", current_time)

logs_dest = Path(f"~/Lab_master/logs/{current_date}/{current_time}").expanduser()
os.makedirs(str(logs_dest), exist_ok=True)


# Check for the presence of the file in the the path ~/Lab_master/config.ini
# If NOT exists we put the default config, if we file is present we take that
# file instead of the default config

config_file_path = Path("~/Lab_master/config.ini").expanduser()

if not config_file_path.exists():
    with open(config_file_path,"w") as des_file:
        with open(BASE_DIR / "config.ini") as src_file:
            content = src_file.read()
            des_file.write(content)    
    
config = configparser.ConfigParser()
config.read(config_file_path)


# this is imported here as we need the file and folder need to be created
import get_password 


common_user = ""
common_pass = ""

isReconnect = False
isSUDO = None
isSTFM = 0
isSTOP = 0

missing_ips_list = set()
connected_ips_list = set()

client_list_to_term_btn_dict = {}

array_of_term_btns = []
list_of_ips = []
list_of_clients = []
list_of_lists = []
list_of_elements = []

term_screen=None
ctrl_screen=None
canvas_screen=None

status_bar = None
ui = None

isSUDO_check_box=None

dashboard_btn = None
cmd_btn     = None
copy_btn    = None
msg_btn     = None
lock_btn    = None
shut_down_btn=None

short_form_btn =None
help_btn       =None
exit_btn       =None

src_file_label=None
des_file_label=None

src_browse_btn=None
des_browse_btn=None

username_entry =None
password_entry =None
cmd_entry      =None

# The Tk root is created by stable.py (start -> scan -> review -> dashboard flow)
# or by the standalone block at the bottom of this file.
main_frame = None

# Host status keys (see ui/theme.py STATUS). The old *_ICON names are kept
# so the logic below reads the same as before.
IDLE_ICON      = "idle"            # connected, nothing running
GREEN_ICON     = "success"
GREY_ICON      = "not_connected"
RED_ICON       = "failed"
YELLOW_ICON    = "running"
RED_CROSS_ICON = "offline"

src_file_path = None #tk.StringVar(value="")
des_file_path = None #tk.StringVar(value="")


class term_btn(HostTile):

    # components related to the remote machine
    client      = None
    active_users= None
    conn_status = "not_conn"

    def __init__(self, parent, ip_address):
        super().__init__(parent, ip_address, on_open=open_single_host)

    def set_user_list(self, list_of_users):
        self.active_users = list_of_users
        self.set_details(self.hostname, list_of_users)


def open_single_host(t_btn):
    get_password.options_for_single_host(main_frame, t_btn, username_entry.get(), password_entry.get())


def get_term_btn():

    global array_of_term_btns

    print(list_of_ips)

    for ip in list_of_ips:
        temp_term_btn = term_btn(ui.grid.inner, ip)
        array_of_term_btns.append(temp_term_btn)
        ui.grid.add(temp_term_btn)

    ui.grid.reflow()

def change_term_btn_icon(ip_address, icon_status):

    global array_of_term_btns

    print("CHANGING THE STATUS OF:", ip_address, "->", icon_status)
    for t_btn in array_of_term_btns:
        if(t_btn.ip_address == ip_address):
            t_btn.set_status(icon_status)

            if (icon_status in (GREY_ICON, RED_CROSS_ICON)):
                t_btn.conn_status = "not_conn"
            else:
                t_btn.conn_status = "alive"

            break

    ui.refresh_counts()
    main_frame.update()

def set_term_btn_client(ip_address, client):

    global array_of_term_btns

    for t_btn in array_of_term_btns:
        if(t_btn.ip_address == ip_address):
            t_btn.client = client
            break

    print("=== mapped ",ip_address, " to correct term box ===")

def set_term_btn_users(ip_address, list_of_users):

    global array_of_term_btns
    for t_btn in array_of_term_btns:
        if(t_btn.ip_address == ip_address):
            t_btn.set_user_list(list_of_users)
            break

    print("=== mapped ",ip_address, "with the correct users_list ===")

def set_term_btn_hostname(ip_address, hostname):
    global array_of_term_btns
    for t_btn in array_of_term_btns:
        if(t_btn.ip_address == ip_address):
            t_btn.hostname = hostname.strip()
            break

    print("=== mapped ",hostname, "with the correct machine name ===")

def reset_color_all_term_btns(icon_status):
    for t_btn in array_of_term_btns:
        if(t_btn.conn_status == "alive"):
            t_btn.set_status(icon_status)

    ui.refresh_counts()
    main_frame.update()

def short_long_form(array_of_term_btns):
    ui.compact.set(not ui.compact.get())
    ui.grid.set_compact(ui.compact.get())


def get_initial_data(client):

    list_of_users = []

    hostname = "hostname"
    init_cmd = "w -h"
    
    stdin, stdout, stderr = remote_connection.run_cmd(client, init_cmd)
    #ip_address = client.get_transport().getpeername()[0]
    out_content = stdout.read().decode()

    t_stdin, t_stdout, t_stderr = remote_connection.run_cmd(client, "hostname")
    hostname = t_stdout.read().decode()

    exit_code   = stdout.channel.recv_exit_status()
    t_exit_code = t_stdout.channel.recv_exit_status()
        
    if(exit_code == 0 and t_exit_code == 0):
        ## success
        init_data_list = find_user.parse_w_to_dict(out_content)
        print(init_data_list)
        for one_user in init_data_list:
            if ("ssh" in one_user['cmd']):
                conn_type = "ssh"
            else:
                conn_type = "local"
            list_of_users.append([one_user['user'], conn_type])

    else:
        print("-------- obtained initial data failed ----------")
        return [-1], -1
        
    return list_of_users, hostname
    
def connect_all(list_of_ips, common_username, common_password):

    global list_of_clients, connected_ips_list, missing_ips_list, isSTOP, isReconnect
    print("Number of IPs : ", len(list_of_ips))

    need_to_connect_count = len(list_of_ips)
    connection_done_count = 0
    success_count         = 0
    failure_count         = 0
    
    if(isReconnect == True):
        need_to_connect_count = len(missing_ips_list)

    status_bar.progress_update(connection_done_count, need_to_connect_count, failure_count)
    main_frame.update()
    
    for ip in list_of_ips:
        
        if(isSTOP == 1):
            isSTOP = 0
            print("\n\nstoped the connected process\n\n")
            break;

        if(ip in connected_ips_list):
            continue
        
        
        temp_client = paramiko.SSHClient()
        temp_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            print("Trying to connect:", ip)
            temp_client.connect(hostname = ip, username = common_username, password = common_password, port = 22, timeout=5)
            list_of_clients.append(temp_client)
            print("connected: ", ip)

            set_term_btn_client(ip, temp_client)

            list_of_users, hostname = get_initial_data(temp_client)
            print("{ list users }")
            print(list_of_users)

            set_term_btn_hostname(ip, hostname)
            set_term_btn_users(ip, list_of_users)
            
            connected_ips_list.add(ip) ; success_count += 1
            missing_ips_list.discard(ip)

            change_term_btn_icon( ip, IDLE_ICON)
            
        except Exception as e:
            print("Connection failed :", ip) 
            change_term_btn_icon(ip, RED_CROSS_ICON)
            print("Exception:", repr(e))

            traceback.print_exc()

            missing_ips_list.add(ip) ; failure_count += 1
            connected_ips_list.discard(ip)
            
            # this part if the number of user is comparetelivy more 
            # print("writting to the missing_ips.list file")
            # with open("missing_ips.list", "a") as f:
            #     f.write(ip)


        connection_done_count += 1
        status_bar.progress_update(connection_done_count, need_to_connect_count, failure_count)
        main_frame.update()



    status_bar.done(success_count, failure_count)
    main_frame.update()
        
    isReconnect = True
    if success_count:
        ui.set_connected()
    return list_of_clients


def connect_missing_ips():

    print(" ; adding missing client ; ")
    missing_ips_list_copy = missing_ips_list.copy()

    connect_all(missing_ips_list_copy, common_username, common_password)

    print("Missing list")
    
def close_all(list_of_clients):
    if(len(list_of_clients) == 0):
        print("No active client now")   
        return -1
    else:
        for client in list_of_clients:
            client.close()

    
         
def run_cmd_all(list_of_clients, cmd, username, password, isSUDO, inputs=False):
    global isSTOP
    print("no of client:",len(list_of_clients))

    for client in list_of_clients:
        ip_address = client.get_transport().getpeername()[0]
        change_term_btn_icon(ip_address, YELLOW_ICON)

    global list_of_lists
    
    list_of_lists = []
    total_count   = len(list_of_clients)
    finished_count= 0
    success_count = 0
    failure_count = 0

    status_bar.progress_update(finished_count, total_count, failure_count)
    main_frame.update()
    
    for client in list_of_clients:

        if(isSTOP == 1):
            isSTOP = 0
            print("\n\nstoped the RUN CMD process\n\n")
            break;
    
        stdin = stdout = stderr = None
        ip_address = client.get_transport().getpeername()[0]
        if (isSUDO == False and type(inputs) == type(False) ):
            stdin, stdout, stderr = remote_connection.run_cmd(client, cmd)
        elif (isSUDO == True and type(inputs) == type(False) ):
            stdin, stdout, stderr = remote_connection.run_sudo_cmd(client, cmd, username, password)
        elif (isSUDO == False and type(inputs) == type([])):
            stdin, stdout, stderr = remote_connection.run_cmd_inputs(client, cmd,inputs )
        elif (isSUDO == True and type(inputs) == type([])):
            stdin, stdout, stderr = remote_connection.run_sudo_cmd_inputs(client, cmd, username, password, inputs )
        
        content = ""
        errors  = ""
        print("client:", client.get_transport().getpeername()[0])
        print(" ===== content =====")
        for line in stdout:
            print(line, end="")
            content += line

        print(" ===== errors =====")
        for line in stderr:
            print(line, end="")
            errors += line

        exit_code = stdout.channel.recv_exit_status()
    
        if(exit_code == 0):
            print("success!!!") ; success_count += 1
            change_term_btn_icon(ip_address, GREEN_ICON)
        else:
            print("{ FAILED }") ; failure_count += 1
            change_term_btn_icon(ip_address, RED_ICON)

        print("EXIT CODE: ", exit_code)

        list_of_lists.append([ip_address, stdin, stdout, stderr, exit_code])

        logs_src = Path(f"~/Lab_master/logs/{current_date}/{current_time}/{ip_address}").expanduser()
        with open(logs_src, "a") as f:
            cmd_str = "CMD_EXECUTED = " + cmd + "\n"
            f.write(cmd_str)
            f.write(content)
            f.write(errors)
            exit_str = "EXIT_CODE: " + str(exit_code) + "\n"
            f.write(exit_str)


        status_bar.progress_update(success_count + failure_count, total_count, failure_count)
        main_frame.update()
            

    status_bar.done(success_count, failure_count)
    main_frame.update()
   
    return list_of_lists



def refresh_data():
    global array_of_term_btns

    reset_color_all_term_btns(YELLOW_ICON)
    
    for t_btn in array_of_term_btns:

        if (t_btn.conn_status != "alive"):
            continue

        list_of_users, hostname = get_initial_data(t_btn.client)

        if (hostname == -1 or list_of_users[0] == -1):
            print("print getting intial data for ", t_btn.ip_address, "failed")
            return "NOT found or connection failed"

        print("{ list users }")
        print(list_of_users)

        set_term_btn_hostname(t_btn.ip_address , hostname)
        set_term_btn_users(t_btn.ip_address, list_of_users)
        
        connected_ips_list.add(t_btn.ip_address)
        missing_ips_list.discard(t_btn.ip_address)

        change_term_btn_icon(t_btn.ip_address, IDLE_ICON)

    status_bar.message("Host info refreshed.")
    return 0
        

def connect_default(cmd):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname = "10.198.122.106", username = "machine", password = "machine@123", port = 22)

    print("client connected")

    stdin, stdout, stderr, exit_code = remote_connection.run_sudo_cmd(client, cmd, "machine", "machine@123")

    print("output: ", stdout.read().decode())
    print("Exit code: ", stdout.channel.recv_exit_status())
    client.close()

def send_msg_all():
    global list_of_clients

#     str_msg_cmd = window_functions.pop_up_question_for_send_msg(main_frame)
#   
#     print("Sending messages with command ->", window_functions._str_msg_cmd)
# 
#     run_cmd_all(list_of_clients, window_functions._str_msg_cmd, common_user, common_pass, isSUDO = False)

    str_msg_cmd = get_password.get_msg_details(main_frame)
    if(str_msg_cmd == ""):
        print("EMPTY STRING")
        return -1

    print("P ",str_msg_cmd," P")    
    # final_msg = f'''GUI_USER=$(loginctl list-sessions --no-legend | awk '$4=="seat0" {{print $3; exit}}'); \
    # [ -n "$GUI_USER" ] && sudo -u "$GUI_USER" DISPLAY=:0 XAUTHORITY=/home/$GUI_USER/.Xauthority zenity --info --text="{str_msg_cmd} & disown" || echo "No active GUI session"'''

    final_msg = f'''GUI_USER=$(loginctl list-sessions --no-legend | awk '$4=="seat0" {{print $3; exit}}');
    GUI_UID=$(id -u "$GUI_USER");
    [ -n "$GUI_USER" ] && sudo -u "$GUI_USER" DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/$GUI_UID notify-send "{str_msg_cmd}"
    '''
    
    print("final : ", final_msg)

   # connect_default(final_msg)
    try:
        run_cmd_all(list_of_clients, final_msg, username_entry.get(), password_entry.get(), isSUDO = True )
    except Exception as e:
        traceback.print_exc()

def copy_all():
    global list_of_clients, src_file_path, des_file_path

    total_count   = len(list_of_clients)
    success_count = 0
    failure_count = 0

    if(src_file_path.get() == "" or des_file_path.get() == ""):
        print("File not specified")
        status_bar.message("Choose a source path and a destination path first.", error=True)
        return -1

    reset_color_all_term_btns(YELLOW_ICON)
    
    for client in list_of_clients:
        ip_address = client.get_transport().getpeername()[0]
        print("------- COPY OPERATION ------")
        print("{", ip_address ," }")
        copy_result = remote_connection.copy_file(client, src_file_path.get(), des_file_path.get())
        if ( copy_result == 0 ):
            print("SUCCESS") ; success_count += 1
            change_term_btn_icon(ip_address,  GREEN_ICON)

        elif ( copy_result == -1):
            print("FAILURE") ; failure_count += 1
            change_term_btn_icon(ip_address, RED_ICON)


        status_bar.progress_update(success_count + failure_count, total_count, failure_count)
        main_frame.update()


    status_bar.done(success_count, failure_count)
    main_frame.update()
        
    return 0

def copy_move_all():
    global list_of_clients, src_file_path, des_file_path

    total_count   = len(list_of_clients)
    success_count = 0
    failure_count = 0

    if(src_file_path.get() == "" or des_file_path.get() == ""):
        print("File not specified")
        status_bar.message("Choose a source path and a destination path first.", error=True)
        return -1

    reset_color_all_term_btns(YELLOW_ICON)
    
    for client in list_of_clients:
        ip_address = client.get_transport().getpeername()[0]
        print("------- COPY MOVE OPERATION ------")
        print("{", ip_address ," }")
        copy_result = remote_connection.copy_file(client, src_file_path.get(),  "/var/tmp/temp_file")
        if ( copy_result == 0 ):
            print("SUCCESS") ; success_count += 1
            change_term_btn_icon(ip_address,  GREEN_ICON)

        elif ( copy_result == -1):
            print("FAILURE") ; failure_count += 1
            change_term_btn_icon(ip_address, RED_ICON)

            continue

        net_cmd = "sudo mv /var/tmp/temp_file " + des_file_path.get()

        run_cmd_all([client], net_cmd, username_entry.get(), password_entry.get(), isSUDO=True)


        status_bar.progress_update(success_count + failure_count, total_count, failure_count)
        main_frame.update()


    status_bar.done(success_count, failure_count)
    main_frame.update()
        
    return 0


def download_all():
    global list_of_clients, src_file_path, des_file_path

    if(src_file_path.get() == "" or des_file_path.get() == ""):
        print("File not specified")
        status_bar.message("Choose a source path and a destination path first.", error=True)
        return -1

    total_count   = len(list_of_clients)
    success_count = 0 
    failure_count = 0

    src_file_name = os.path.basename(src_file_path.get())
    
    reset_color_all_term_btns(YELLOW_ICON)
    
    for client in list_of_clients:

        ip_address = client.get_transport().getpeername()[0]
        download_result = remote_connection.download_file(client, src_file_path.get(), f"~/Lab_master/pulls/{current_date}/{current_time}/{ip_address}/{src_file_name}")

        if ( download_result == -1 ):
            change_term_btn_icon(ip_address,  RED_ICON) ; failure_count += 1

        elif ( download_result == 0):
            change_term_btn_icon(ip_address, GREEN_ICON) ; success_count += 1


        status_bar.progress_update(success_count + failure_count, total_count, failure_count)
        main_frame.update()


    status_bar.done(success_count, failure_count)
    main_frame.update()
    return 0



def download_folder_all():
    global list_of_clients, src_file_path, des_file_path

    if(src_file_path.get() == ""):
        print("File not specified")
        status_bar.message("Choose a source folder path first.", error=True)
        return -1

    total_count   = len(list_of_clients)
    success_count = 0 
    failure_count = 0

    src_file_name = os.path.basename(src_file_path.get())
    
    reset_color_all_term_btns(YELLOW_ICON)
    
    for client in list_of_clients:

        ip_address = client.get_transport().getpeername()[0]
        download_result = remote_connection.download_folder(client, src_file_path.get(), f"~/Lab_master/pulls/{current_date}/{current_time}/{ip_address}/{src_file_name}")

        if ( download_result == -1 ):
            change_term_btn_icon(ip_address,  RED_ICON) ; failure_count += 1

        elif ( download_result == 0):
            change_term_btn_icon(ip_address, GREEN_ICON) ; success_count += 1


        status_bar.progress_update(success_count + failure_count, total_count, failure_count)
        main_frame.update()


    status_bar.done(success_count, failure_count)
    main_frame.update()
    return 0



def lock_user():
    global list_of_clients
    username = get_password.get_username(main_frame, "Lock user", "Lock user")

    if(username == ""):
        print("FIELD EMPTY")
        return -1

    lock_user_cmd = config.get("system_cmd", "LOCK_USER") + " " + username
    print("the LOCK user  cmd = ", lock_user_cmd)

    run_cmd_all(list_of_clients, lock_user_cmd, username_entry.get(), password_entry.get(), isSUDO=True)

def unlock_user():
    global list_of_clients
    username = get_password.get_username(main_frame, "Unlock user", "Unlock user")

    if(username == ""):
        print("FIELD EMPTY")
        return -1

    unlock_user_cmd = config.get("system_cmd", "UNLOCK_USER") + " " + username
    print("the UNLOCK user cmd = ", unlock_user_cmd)

    run_cmd_all(list_of_clients, unlock_user_cmd, username_entry.get(), password_entry.get(), isSUDO=True)


def lock_sessions_all():
    global list_of_clients

    lock_cmd = config.get("system_cmd", "LOCK_SCREEN")
    print("the LOCK cmd = ", lock_cmd)

    run_cmd_all(list_of_clients, lock_cmd, username_entry.get(), password_entry.get(), isSUDO=True)

def shut_down_all():
    global list_of_clients

    if not ui.confirm_shutdown():
        return -1

    shutdown_cmd = config.get("system_cmd", "SHUT_DOWN_NOW")
    print("the LOCK cmd = ", shutdown_cmd)

    run_cmd_all(list_of_clients, shutdown_cmd, username_entry.get(), password_entry.get(), isSUDO=True)

def change_passwd_all():
        # This function change the passwd for the list of users
        # For to change the passwd the ssh connect user must be
        # a root or high level user(sudo) than the list users

    global list_of_clients, main_frame

    list_of_new_users =  get_password.get_new_passwd(main_frame)
    print(list_of_new_users)

    if not list_of_new_users:
        return -1

    change_passwd_cmd = config.get("system_cmd", "CHANGE_PASSWD")
        
    for new_user in list_of_new_users:
        print("Changing password for the user:", new_user[0])
        run_cmd_all(list_of_clients, change_passwd_cmd +" " + new_user[0], username_entry.get(), password_entry.get(), isSUDO=True, inputs=[new_user[1]+"\n", new_user[1]+"\n" ])
        

def user_add_all():
    pass

    
def user_del_all():

    global list_of_clients, main_frame    

    list_old_users = get_password.get_old_users(main_frame)
    print("got the list of users ",list_old_users)

    if not list_old_users:
        return -1

    if not confirm(main_frame, "Delete these users?",
                   "This permanently deletes the accounts and their home folders on "
                   "every connected host:\n\n  " + "\n  ".join(list_old_users),
                   f"Delete {len(list_old_users)} user(s)"):
        return -1
    
    user_del_cmd = config.get("system_cmd", "USER_DEL")

    
    for old_user in list_old_users:

        print("deleting the user:", old_user)
        net_cmd = user_del_cmd + " " +old_user
        run_cmd_all(list_of_clients, net_cmd, username_entry.get(), password_entry.get(), isSUDO=True)
    
def get_credentials():

    global username_entry, password_entry
    
    print("user: ",username_entry.get())
    print("password: ",password_entry.get())

def get_src_file_path():

    global src_file_path
    
    selected_file = filedialog.askopenfilename()

    print("SOURCE SELECTED: ", selected_file)
    
    src_file_path.set( selected_file )

def get_des_file_path():

    global des_file_path
    
    selected_file = filedialog.askopenfilename()

    print("DESTINATION SELECTED: ", selected_file)
    
    des_file_path.set( selected_file )

def load_host_list():
    global list_of_ips

    selected_ips = json_reader.read_any_file(main_frame)

    if not selected_ips:
        status_bar.message("No host list selected.", error=True)
        return

    list_of_ips = selected_ips

    status_bar.message(f"Loaded {len(list_of_ips)} hosts.")


def stop_all():

# Set the varibale to 1

    global isSTOP 

    isSTOP = 1

    return isSTOP


def exit_main():
    global list_of_clients, main_frame
    
    close_all(list_of_clients)

    main_frame.destroy()


def initialize(parent, ips=None):
    """Build the dashboard inside `parent`. `ips` is the host list (may be empty)."""
    global main_frame, screen
    global src_file_path, des_file_path
    global array_of_term_btns, list_of_ips
    global username_entry, password_entry, cmd_entry, isSUDO
    global status_bar, ui

    # Reuse the root created by stable.py.
    main_frame = parent

    # Create a separate frame for the Work Screen.
    screen = ttk.Frame(main_frame, style="App.TFrame")

    # Create Tkinter variables only after the root exists.
    src_file_path = tk.StringVar(master=main_frame, value="")
    des_file_path = tk.StringVar(master=main_frame, value="")

    array_of_term_btns = []
    list_of_ips = list(ips or [])

    actions = {
        "connect":          lambda: connect_all(list_of_ips, username_entry.get(), password_entry.get()),
        "run":              lambda: run_cmd_all(list_of_clients, cmd_entry.get().strip(),
                                                username_entry.get(), password_entry.get(), isSUDO.get()),
        "stop":             stop_all,
        "message":          send_msg_all,
        "lock_screens":     lock_sessions_all,
        "shutdown":         shut_down_all,
        "refresh":          refresh_data,
        "lock_user":        lock_user,
        "unlock_user":      unlock_user,
        "change_password":  change_passwd_all,
        "add_user":         None,            # user_add_all is not implemented yet
        "delete_user":      user_del_all,
        "browse_src":       get_src_file_path,
        "browse_des":       get_des_file_path,
        "upload":           copy_all,
        "upload_sudo_move": copy_move_all,
        "download":         download_all,
        "download_folder":  download_folder_all,
        "exit":             exit_main,
    }

    ui = MainWindow(
        main_frame,
        actions,
        src_file_path,
        des_file_path,
        source_name=json_reader.last_file_name,
        host_count=len(list_of_ips),
        content_frame=screen
    )

    status_bar     = ui.status_bar
    username_entry = ui.username_entry
    password_entry = ui.password_entry
    cmd_entry      = ui.cmd_entry
    isSUDO         = ui.is_sudo

    username_entry.insert(0, common_user)

    get_term_btn()
    ui.refresh_counts()
    if not list_of_ips:
        status_bar.message("No hosts loaded. Restart and choose a .json or .txt IP list.", error=True)
    username_entry.focus_set()

    screen.place(relwidth=1, relheight=1)


if __name__ == "__main__":
    # Standalone: choose a host list file, then open the dashboard directly.
    theme.enable_hidpi()                     # before tk.Tk(), or text is blurry at 125 %/150 %
    root = tk.Tk()
    theme.apply(root, settings.get("theme"))
    initialize(root, json_reader.read_any_file(root))
    root.mainloop()
