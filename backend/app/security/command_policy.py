import shlex
from typing import List
from fastapi import HTTPException


FORBIDDEN_TOKENS = {
    "rm", "del", "format", "shutil", "sudo", "curl", "wget",
    "bash", "powershell", "cmd.exe", "/bin/sh", "chmod", "eval",
    "exec", "import os; os.system"
}


def validate_command_policy(command: List[str]) -> None:
    """
    Ensures only allowlisted test commands (pytest) can be executed.
    Blocks arbitrary shell commands, subshells, and prohibited tokens.
    """
    if not command:
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    cmd_str = " ".join(command).lower()

    for token in FORBIDDEN_TOKENS:
        if token in cmd_str:
            raise HTTPException(status_code=400, detail=f"Command policy violation: prohibited token '{token}'")

    first_arg = command[0].lower()
    if not ("pytest" in first_arg or "python" in first_arg):
        raise HTTPException(status_code=400, detail=f"Command policy violation: unallowlisted executable '{command[0]}'")

