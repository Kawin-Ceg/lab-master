import json as json
import re as re
from pathlib import Path

from ui import dialogs

list_of_hosts = []
last_file_name = ""
list_of_ips   = []

def read_json_file(file_name):

    global list_of_ips, list_of_hosts

    file = open(file_name)

    if(file == None):
        print("File does not exit!!!")
        return -1
    print("File Opened Successfully")

    
    list_of_hosts = json.load(file)
    

    for element in list_of_hosts:
        print(str(element.get("ip")))

        list_of_ips.append( str( element.get("ip")))

    return list_of_ips

def read_txt_file(file_name):

    global list_of_ips, list_of_hosts

    ip_pattern = r"^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$"
    
    with open(file_name, "r") as file:

        for line in file:
            line = line.strip()
            if re.match(ip_pattern, line):
                print(line)
                list_of_ips.append(line)
            else:
                print("This is NOT a valid ip address:", line)
                continue

    return list_of_ips




def read_any_file(main_frame):
    global last_file_name
    # The file picker window lives in ui/dialogs.py.
    # Always returns a list, so callers can loop over it safely.

    file_name = dialogs.ask_ip_file(main_frame)
    if file_name == "":
        print("No host list selected")
        return []

    file = Path(file_name)
    last_file_name = file.name
    print(f"Reading from {str(file)}")

    try:
        if (file.suffix.lower() == ".json"):
            return read_json_file(file)
        elif (file.suffix.lower() == ".txt"):
            return read_txt_file(file)
    except (ValueError, OSError) as e:
        print("Could not read host list:", repr(e))

    return []
