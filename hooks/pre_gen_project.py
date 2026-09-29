import subprocess
import sys

ODOO_VERSION = "{{ cookiecutter.odoo_version }}"
POSTGRESQL_VERSION = int("{{ cookiecutter.postgresql_version }}")
MIN_POSTGRESQL = {
    "20.0": 16,
}

minimum_postgresql = MIN_POSTGRESQL.get(ODOO_VERSION)
if minimum_postgresql is not None and POSTGRESQL_VERSION < minimum_postgresql:
    print(
        f"ERROR: Odoo {ODOO_VERSION} requires PostgreSQL {minimum_postgresql} or newer. "
        f"Selected version: {POSTGRESQL_VERSION}."
    )
    sys.exit(1)


def execute_git(*args) -> str:
    try:
        output = subprocess.run(["git", *args], capture_output=True, check=True)
        return False, output.stdout.decode("utf-8")
    except Exception as ex:
        return True, ex.stderr.decode("utf-8")


repository = "git@{{ cookiecutter.git_server }}:{{ cookiecutter.github_user }}/{{ cookiecutter.github_repo }}.git"

if (
    "{{ cookiecutter.github_user }}" != "ExampleUser"
    and "{{ cookiecutter.github_repo }}" != "example-repo"
):
    err, output = execute_git("ls-remote", repository)
    if err:
        print(output)
        sys.exit(1)
