import sys
import os
import subprocess
import time
import hashlib

from configparser import ConfigParser

repository = "git@github.com:{{ cookiecutter.github_user }}/{{ cookiecutter.github_repo }}.git"
config = ConfigParser()
rcfile = os.path.abspath(f"{os.curdir}/odoo.conf")

GIT_COMMANDS_QUEUE = [
    ["init"],
    ["remote", "add", "origin", repository],
    ["fetch", "origin"],
    ["remote", "set-head", "origin", "--auto"]
]


def execute_git(*args) -> str:
    try:
        output = subprocess.run(["git", *args], capture_output=True, check=True)
        return False, output.stdout.decode("utf-8")
    except Exception as ex:
        return True, ex.stderr.decode("utf-8")

config.read([rcfile])
config["options"]["admin_passw"] = hashlib.sha1(str(time.time()).encode()).hexdigest()
config.write(open(rcfile, "w"))

for commands in GIT_COMMANDS_QUEUE:
    err, output = execute_git(*commands)
    if err:
        print(output)
        sys.exit(1)
    if output:
        print(output)

_, branch = execute_git("symbolic-ref", "refs/remotes/origin/HEAD", "--short")
execute_git("checkout", branch.strip("\n").split("/")[1])

entrypoints = ["entrypoint.sh", "wait-for-psql.py"]
subprocess.call([
    "chmod",
    "+x",
    *[os.path.abspath(f"{os.curdir}/{f}") for f in entrypoints]
])