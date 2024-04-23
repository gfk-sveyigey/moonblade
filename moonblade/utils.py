from psutil import process_iter
from base64 import b64encode

def find_LCU_process():
    for process in process_iter():
        if process.name() in ["LeagueClientUx.exe", "LeagueClientUx"]:
            return process
    return None

def parse_LCU_cmdline(cmdline_args):
    cmdline_args_parsed = {}
    for cmdline_arg in cmdline_args:
        if len(cmdline_arg) > 0 and "=" in cmdline_arg:
            key, value = cmdline_arg[2:].split("=", 1)
            cmdline_args_parsed[key] = value
    return cmdline_args_parsed

def build_auth_header(username:str, password):
    userpass = b":".join((username.encode("utf-8"), password.encode("utf-8")))
    token = b64encode(userpass).decode()
    return f"Basic {token}"