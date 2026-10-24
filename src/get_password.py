import traceback
import remote_connection
import shell_process
import configparser as configparser
from pathlib import Path

from ui import dialogs


config_file_path = Path("~/Lab_master/config.ini").expanduser()

config = configparser.ConfigParser()
config.read(config_file_path)


print(config.get("system_cmd","LOCK_SCREEN"))

# The windows themselves live in ui/dialogs.py. These names are kept so
# existing callers (work_screen.py, stable.py) do not have to change.

def get_password(main_frame):
    return dialogs.ask_password(main_frame)

def get_msg_details(main_frame):
    return dialogs.ask_message(main_frame)

def get_username(main_frame, title="Choose user", action_text="OK"):
    return dialogs.ask_username(main_frame, title, action_text)

def get_new_passwd(main_frame):
    # [ [name, passwd], [name,passwd], [...] ]
    return dialogs.ask_new_passwords(main_frame)

def get_old_users(main_frame):
    # [username1, username2, ... ]
    return dialogs.ask_users_to_delete(main_frame)

# ------------------------------------------------------

def notify_cmd(message):
    return f'''GUI_USER=$(loginctl list-sessions --no-legend | awk '$4=="seat0" {{print $3; exit}}');
    GUI_UID=$(id -u "$GUI_USER");
    [ -n "$GUI_USER" ] && sudo -u "$GUI_USER" DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/$GUI_UID notify-send "{message}"
    '''

def send_msg_single(main_frame, term_btn, username, password):

    small_msg = dialogs.ask_message(main_frame, term_btn.hostname or term_btn.ip_address)
    if small_msg == "":
        return -1

    print("got message", small_msg)
    try:
        remote_connection.run_sudo_cmd(term_btn.client, notify_cmd(small_msg), username, password)
    except Exception as e:
        traceback.print_exc()

def lock_screen_single(main_frame, term_btn, username, password):

    final_msg = config.get("system_cmd", "LOCK_SCREEN")
    try:
        remote_connection.run_sudo_cmd(term_btn.client, final_msg, username, password)
    except Exception as e:
        traceback.print_exc()

def shut_down_single(main_frame, term_btn, username, password):

    final_msg = config.get("system_cmd", "SHUT_DOWN_NOW")

    try:
        remote_connection.run_sudo_cmd(term_btn.client, final_msg, username, password)
    except Exception as e:
        traceback.print_exc()

def options_for_single_host(main_frame, term_btn, username, password):

    dialogs.host_actions(
        main_frame, term_btn,
        on_message = lambda: send_msg_single(main_frame, term_btn, username, password),
        on_lock    = lambda: lock_screen_single(main_frame, term_btn, username, password),
        on_shutdown= lambda: shut_down_single(main_frame, term_btn, username, password),
        on_terminal= lambda: shell_process.spawn_terminal_session_with_ssh(username, term_btn.ip_address),
    )
