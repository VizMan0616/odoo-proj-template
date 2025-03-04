import sys
import subprocess
import configparser


def execute_git(*args) -> str:
    try:
        output = subprocess.run(["git", *args], capture_output=True, check=True)
        return False, output.stdout.decode("utf-8")
    except Exception as ex:
        return True, ex.stderr.decode("utf-8")

odoo_version = "{{ cookiecutter.odoo_version }}"
ubuntu_release = "{{ cookiecutter.ubuntu_release }}"
repository = "git@{{ cookiecutter.git_server }}:{{ cookiecutter.github_user }}/{{ cookiecutter.github_repo }}.git"

if odoo_version in ["16.0", "17.0"] and ubuntu_release in ["bionic", "focal"]:
    print("Error: Odoo 16.0 should be used with Ubuntu 22.04 (Jammy Jellyfish)")
    sys.exit(1)

err, output = execute_git("ls-remote", repository)
if err:
    print(output)
    sys.exit(1)