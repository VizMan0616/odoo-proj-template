import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from configparser import RawConfigParser
from pathlib import Path
from typing import Dict, List, Tuple


class FileReplace:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.backup_path = self.file_path.with_suffix(f"{self.file_path.suffix}.bak")
        self.original_content = ""

    def _create_backup(self):
        self.original_content = self.file_path.read_text()
        self.backup_path.write_text(self.original_content)

    def _restore_backup(self):
        if self.backup_path.exists():
            self.backup_path.replace(self.file_path)

    def _clean_backup(self):
        if self.backup_path.exists():
            self.backup_path.unlink()

    def apply_replacements(self, replacements: Dict[str, str]) -> str:
        content = self.original_content

        for pattern, replacement in replacements.items():
            if not re.search(pattern, content, re.DOTALL):
                raise ValueError(f"Pattern not found: {pattern[:50]}")
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        return content

    def execute(self, replacements: Dict[str, str], dry_run: bool = False):
        if not self.file_path.exists():
            print(f"Error: File not found at {self.file_path}", file=sys.stderr)
            sys.exit(1)

        try:
            self._create_backup()
            modified_content = self.apply_replacements(replacements)

            if dry_run:
                print(f"Original {self.file_path}\n{self.original_content}\n\nModified {self.file_path}\n{modified_content}")
                self._clean_backup()
                return

            self.file_path.write_text(modified_content)
            print(f"Successfully updated {self.file_path}")
            self._clean_backup()
        except Exception as ex:
            self._restore_backup()
            print("Restored original file from backup", file=sys.stderr)
            print(f"Error: {ex}", file=sys.stderr)
            sys.exit(1)


def generate_run_block(addons_list: List[str], base_command: str = "RUN chown odoo /etc/odoo/odoo.conf", mkdir_cmd: str = "mkdir -p", chown_cmd: str = "chown -R odoo") -> str:
    lines = [base_command]
    for path in addons_list:
        lines.append(f"    && {mkdir_cmd} {path}")
        lines.append(f"    && {chown_cmd} {path}")

    return " \\\n".join(lines)


def generate_volume_block(addons_list: List[str], always_include: List[str] = None) -> str:
    if always_include is None:
        always_include = []

    all_volumes = always_include + addons_list
    return f"VOLUME [{', '.join(f'"{v}"' for v in all_volumes)}]"


def execute_git(cmds: List[str], verbose: bool = False) -> (bool, str):
    try:
        if verbose:
            PIPE = subprocess.PIPE
            process = subprocess.Popen(["git"] + cmds, stdout=PIPE, text=True, bufsize=1)
            for line in iter(process.stdout.readline, ""):
                print(line.strip())

            process.stdout.close()
            return False, ""
        else:
            output = subprocess.run(["git"] + cmds, capture_output=True, check=True)
            return False, output.stdout.decode("utf-8")
    except Exception as ex:
        return True, ex.stderr.decode("utf-8")


class DockerfileReplacer(FileReplace):
    def get_replacements(self, addons_list: List[str]) -> dict:
        run_pattern = r"RUN\s+chown\s+odoo\s+/etc/odoo/odoo\.conf\s+.*?(?=\n\S|\Z)"
        volume_pattern = r"VOLUME\s+\[[^\]]*\]"

        return {
            run_pattern: generate_run_block(addons_list),
            volume_pattern: generate_volume_block(addons_list, always_include=["/var/lib/odoo"])
        }


class ComposeReplacer(FileReplace):
    def get_replacements(self, addons_list: List[Tuple[str, str]]) -> dict:
        volume_lines = []

        volume_lines.append("      - odoo:/var/lib/odoo")
        volume_lines.append("      - ./config:/etc/odoo")

        for path in addons_list:
            volume_lines.append(f"      - ./{path[0]}:{path[1]}")

        def replace_volume_section(content: str):
            lines = content.split("\n")
            in_odoo_service = False
            in_volume_section = False
            result_lines = []

            for line in lines:
                if re.match(r"^  [a-zA-Z0-9_-]+:", line):
                    in_odoo_service = ("odoo:" in line)
                    in_volume_section = False

                if in_odoo_service and re.match(r"^    volumes:", line):
                    in_volume_section = True
                    result_lines.append("    volumes:")
                    for volume_line in volume_lines:
                        result_lines.append(volume_line)
                    continue

                if in_volume_section:
                    if re.match("^      -", line):
                        continue
                    elif line and not line.startswith("      "):
                        in_volume_section = False
                        result_lines.append(line)
                else:
                    result_lines.append(line)
            return "\n".join(result_lines)

        return {"__custom__": replace_volume_section}

    def apply_replacements(self, replacements: dict) -> str:
        content = self.original_content

        for pattern, replacement in replacements.items():
            if pattern == "__custom__":
                content = replacement(content)
            else:
                if not re.search(pattern, content, re.DOTALL):
                    raise ValueError(f"Pattern not found: {pattern[:50]}...")
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        return content

CWD = Path.cwd()
MODULE_INDEX = "__manifest__.py"
config = RawConfigParser()
compose = None
rcfile = os.path.join(CWD, "config", "odoo.conf")
composefile = os.path.join(CWD, "docker-compose.yml")
dockerfile = os.path.join(CWD, "Dockerfile")
repository = "git@{{ cookiecutter.git_server }}:{{ cookiecutter.github_user }}/{{ cookiecutter.github_repo }}.git"
GIT_COMMANDS_QUEUE = [
    (["init"], False),
    (["remote", "add", "origin", repository], False),
    (["fetch", "origin"], True),
    (["remote", "set-head", "origin", "--auto"], False)
]

if "{{ cookiecutter.odoo_version }}" != "19.0":
    if os.path.exists(os.path.join(CWD, "postgres.Dockerfile")):
        print("Removing 'postgres.Dockerfile' file...")
        os.remove(os.path.join(CWD, "postgres.Dockerfile"))
    if os.path.exists(os.path.join(CWD, "config", "init-pgvector.sql")):
        print("Removing 'init-pgvector.sql' file...")
        os.remove(os.path.join(CWD, "config", "init-pgvector.sql"))

if "{{ cookiecutter.github_user }}" != "ExampleUser" and "{{ cookiecutter.github_repo }}" != "example-repo":
    if os.path.exists(os.path.join(CWD, ".gitignore")):
        print("Template '.gitignore' will be deleted because it may block checkout.")
        os.remove(os.path.join(CWD, ".gitignore"))

    for commands, verbose in GIT_COMMANDS_QUEUE:
        err, output = execute_git(commands, verbose=verbose)
        if err:
            print(output)
            sys.exit(1)
        if output:
            print(output)

    _, branch = execute_git(["symbolic-ref", "refs/remotes/origin/HEAD", "--short"])
    branch = branch.strip("\n").split("/")[1]

    execute_git(["checkout", branch], verbose=True)

    if os.path.exists(os.path.join(CWD, ".gitmodules")):
        execute_git(["submodule", "update", "--init", "--recursive", "--progress"], verbose=True)

modules_container = []
modules = []
for root_folder, dummy, file_names in os.walk(CWD):
    if MODULE_INDEX in file_names:
        tmp_file_path = Path(os.path.join(root_folder, MODULE_INDEX)).relative_to(CWD)
        level = len(tmp_file_path.parents) - 1

        if level == 1:
            folder = str(tmp_file_path.parent)
            if folder in modules:
                continue
            modules.append(str(folder))
        else:
            folder = str(tmp_file_path.parent.parent)
            if folder in modules_container:
                continue
            modules_container.append(folder)

config.read([rcfile])
config["options"]["admin_passwd"] = hashlib.sha1(str(time.time()).encode()).hexdigest()

if modules_container:
    shutil.rmtree(os.path.join(CWD, "addons"))

    volume_modules = []
    for container in modules_container:
        tmp_container = container.split("/")
        volume_modules.append(f"/mnt/{tmp_container[-1]}")

    config["options"]["addons_path"] = ",".join(volume_modules)

    dockerfile_replacer = DockerfileReplacer(dockerfile)
    compose_replacer = ComposeReplacer(composefile)

    dockerfile_replacements = dockerfile_replacer.get_replacements(volume_modules)
    dockerfile_replacer.execute(dockerfile_replacements)

    compose_replacements = compose_replacer.get_replacements(zip(modules_container, volume_modules))
    compose_replacer.execute(compose_replacements)
else:
    extra_files = [(os.path.join(CWD, ".git"), ".git"), (os.path.join(CWD, "README.md"), "README.md")]
    modules_to_move = [(os.path.join(CWD, f), f) for f in modules] + extra_files
    dir_to_move = os.path.join(CWD, "addons")
    os.remove(os.path.join(dir_to_move, ".gitkeep"))

    for module_to_move in modules_to_move:
        if os.path.exists(module_to_move[0]):
            print(f"Moving {module_to_move[1]}...")
            shutil.move(module_to_move[0], dir_to_move)

entrypoints = ["entrypoint.sh", "wait-for-psql.py"]
subprocess.call([
    "chmod",
    "+x",
    *[os.path.join(CWD, f) for f in entrypoints]
])

config.write(open(rcfile, "w"))
