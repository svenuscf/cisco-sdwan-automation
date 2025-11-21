from vmanage_api import VManage
from creds_loader import load_vmanage_creds
import sys
import tabulate


def main():
    if len(sys.argv) >= 4:
        host, user, pwd = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        host, user, pwd = load_vmanage_creds()
    vm = VManage(host, user, pwd)

    # vm.get() already returns JSON (dict or list)
    resp = vm.get("/device")

    # Normalise response into a list of items
    if isinstance(resp, dict) and "data" in resp:
        items = resp["data"]
    elif isinstance(resp, list):
        items = resp
    else:
        print("Unexpected /device response format:")
        print(resp)
        sys.exit(1)

    headers = ["Host-Name", "Device Type", "Device ID",
               "System IP", "Site ID", "Version", "Device Model"]
    table = []

    for item in items:
        # use .get() so we don’t crash if a field is missing
        row = [
            item.get("host-name", ""),
            item.get("device-type", ""),
            item.get("uuid", ""),
            item.get("system-ip", ""),
            item.get("site-id", ""),
            item.get("version", ""),
            item.get("device-model", ""),
        ]
        table.append(row)

    try:
        print(tabulate.tabulate(table, headers, tablefmt="fancy_grid"))
    except UnicodeEncodeError:
        print(tabulate.tabulate(table, headers, tablefmt="grid"))


if __name__ == "__main__":
    main()

