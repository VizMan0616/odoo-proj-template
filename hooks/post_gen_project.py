import sys
import os
import subprocess
import time
import hashlib

from configparser import RawConfigParser


def execute_git(*args) -> str:
    try:
        output = subprocess.run(["git", *args], capture_output=True, check=True)
        return False, output.stdout.decode("utf-8")
    except Exception as ex:
        return True, ex.stderr.decode("utf-8")

config = RawConfigParser()
rcfile = os.path.abspath(f"{os.curdir}/config/odoo.conf")
repository = "git@{{ cookiecutter.git_server }}:{{ cookiecutter.github_user }}/{{ cookiecutter.github_repo }}.git"
GIT_COMMANDS_QUEUE = [
    ["init"],
    ["remote", "add", "origin", repository],
    ["fetch", "origin"],
    ["remote", "set-head", "origin", "--auto"]
]

if "{{ cookiecutter.github_user }}" != "ExampleUser" and "{{ cookiecutter.github_repo }}" != "example-repo":
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

config.read([rcfile])
config["options"]["admin_passwd"] = hashlib.sha1(str(time.time()).encode()).hexdigest()
config.write(open(rcfile, "w"))