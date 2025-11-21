# creds_loader.py
import os
import subprocess
import yaml

VAULT_FILE = os.path.expanduser("~/scripts/cisco-sdwan/vmanage_creds.yml")
VAULT_PASS_FILE = os.path.expanduser("~/.ansible_vault_pass.txt")


def load_vmanage_creds():
    """
    Decrypt vmanage_creds.yml using ansible-vault and return (url, username, password).
    """
    cmd = ["ansible-vault", "view", VAULT_FILE]

    # If a vault password file exists, use it automatically
    if os.path.isfile(VAULT_PASS_FILE):
        cmd.extend(["--vault-password-file", VAULT_PASS_FILE])

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    )

    data = yaml.safe_load(result.stdout)

    return (
        data["vmanage_url"],
        data["username"],
        data["password"],
    )

