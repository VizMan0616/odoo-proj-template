import sys
import subprocess

from typing import Union


def check_if_dependencies_are_met(command: Union[str | list]) -> bool:
    try:
        subprocess.call(command)
        return True, None
    except FileNotFoundError:
        if isinstance(command, str):
            return False, command
        return False, command[0]


if __name__ == "__main__":
    exists, err = check_if_dependencies_are_met(["git", "--version"])
    if not exists:
        print(f"ERROR: {err} is missing! Please install it to continue")
        sys.exit(1)
