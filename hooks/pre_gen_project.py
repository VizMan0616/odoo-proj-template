import sys

odoo_version = "{{ cookiecutter.odoo_version }}"
ubuntu_release = "{{ cookiecutter.ubuntu_release }}"

if odoo_version == "16.0" and ubuntu_release in ["bionic", "focal"]:
    print("Error: Odoo 16.0 should be used with Ubuntu 22.04 (Jammy Jellyfish)")
    sys.exit(1)