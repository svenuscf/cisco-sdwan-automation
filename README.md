This directory contains helper scripts for interacting with Cisco vManage
(e.g., device.py, control_status.py) and a reusable credential loader module
(creds_loader.py).

The scripts do not hardcode your vManage credentials.
Instead, they load the URL, username, and password securely from an encrypted file
using Ansible Vault.

1. Files in This Folder
```
File			Purpose
creds_loader.py		Module that decrypts the credential file using ansible-vault view
vmanage_creds.yml	Your encrypted credential file (contains URL/username/password)
control_status.py	Example script that loads credentials automatically
device.py		Inventory script also using the same loader
```

2. Location of Credential File

The credential file is:

```
~/scripts/vmanage_creds.yml
```

This file contains:
```
vmanage_url: "https://dotwa-vmanage.sdwan.cisco.com"
username: <username>
password: <password>
```
…but this file is encrypted, so you cannot read it directly.

The decryption is handled by:

```
creds_loader.py
```

3. How Scripts Load the Credentials

Any script can simply do:

```
from creds_loader import load_vmanage_creds
host, user, pwd = load_vmanage_creds()
```

No manual typing of URL/user/pass is required.

4. Changing the vManage URL or Credentials

If you need to update the URL, username, or password (e.g., a new environment):

Step 1 — Decrypt the file
```
ansible-vault decrypt ~/scripts/vmanage_creds.yml
```

Enter the vault password when prompted.

Step 2 — Edit the file

Change any of the fields:
```
vmanage_url: "https://new-vmanage.company.com"
username: "newuser"
password: "NewPass123!"
```
Done — all scripts will automatically use the updated values.

5. Optional: Using a Vault Password File

If you want scripts to run without interactive vault password prompts, create:
```
~/.ansible_vault_pass.txt
```

Add your vault password:

```
echo 'YourVaultPasswordHere' > ~/.ansible_vault_pass.txt
chmod 600 ~/.ansible_vault_pass.txt
```

creds_loader.py will automatically detect and use this file.

6. Troubleshooting
If scripts fail with "permission denied"

Check file permissions.

If you forget the vault password

Ansible Vault encryption cannot be recovered.
You must delete and recreate vmanage_creds.yml.
