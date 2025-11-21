from vmanage_api import VManage
from creds_loader import load_vmanage_creds
import sys
import tabulate
from datetime import datetime

def ms_to_date(ms_val):
    """Convert ms since epoch to human-readable date/time."""
    try:
        if isinstance(ms_val, (int, float)) and ms_val > 1000000000:
            return datetime.fromtimestamp(ms_val / 1000).strftime("%Y-%m-%d %H:%M:%S")
        else:
            return ms_val
    except Exception:
        return ms_val

def main():
    # --- Load Credentials ---
    if len(sys.argv) >= 4:
        host, user, pwd = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        host, user, pwd = load_vmanage_creds()

    vm = VManage(host, user, pwd)

    # --- Fetch Policy Groups ---
    try:
        resp = vm.get("/v1/policy-group")
    except Exception as e:
        print(f"Error fetching policy groups: {e}")
        sys.exit(1)

    # Normalize to list
    if isinstance(resp, dict) and "data" in resp:
        policy_groups = resp["data"]
    elif isinstance(resp, list):
        policy_groups = resp
    else:
        print("Unexpected /policy-group response format:")
        print(resp)
        sys.exit(1)

    # Table headers
    headers = [
        "Policy Group ID",
        "Name",
        "Description",
        "Solution",
        "Last Updated By",
        "Last Updated",
        "Associated Devices"
    ]
    table = []

    # --- Loop through each Policy Group ---
    for pg in policy_groups:
        policy_group_id = pg.get("id", "")
        name            = pg.get("name", "")
        description     = pg.get("description", "")
        solution        = pg.get("solution", "")
        last_updated_by = pg.get("lastUpdatedBy", "")
        last_updated    = ms_to_date(pg.get("lastUpdatedOn", ""))

        # --- Fetch Associated Devices for this Policy Group ---
        associated_devices_list = []
        if policy_group_id:
            try:
                assoc_resp = vm.get(f"/v1/policy-group/{policy_group_id}/device/associate")
                if isinstance(assoc_resp, dict) and "data" in assoc_resp:
                    devices_assoc = assoc_resp["data"]
                elif isinstance(assoc_resp, list):
                    devices_assoc = assoc_resp
                else:
                    devices_assoc = []

                for dev in devices_assoc:
                    hostname = dev.get("host-name") or dev.get("system-ip") or "Unknown"
                    associated_devices_list.append(hostname)

            except Exception as e:
                associated_devices_list = [f"Error: {e}"]

        associated_devices = ", ".join(associated_devices_list) if associated_devices_list else "-"

        # --- Append table row ---
        table.append([
            policy_group_id,
            name,
            description,
            solution,
            last_updated_by,
            last_updated,
            associated_devices
        ])

    # --- Print ---
    print(tabulate.tabulate(table, headers, tablefmt="fancy_grid"))

if __name__ == "__main__":
    main()
