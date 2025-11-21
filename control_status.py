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

    # Inventory – this is known to work in your environment
    resp = vm.get("/device")

    # Normalise into a list
    if isinstance(resp, dict) and "data" in resp:
        devices = resp["data"]
    elif isinstance(resp, list):
        devices = resp
    else:
        print("Unexpected /device response format:")
        print(resp)
        sys.exit(1)

    headers = [
        "Host-Name",
        "System IP",
        "Reachability",
        "Ctrl Conn",
        "OMP Peers",
        "Device Type",
        "Version",
        "Model",
    ]
    table = []

    for d in devices:
        hostname    = d.get("host-name", "")
        system_ip   = d.get("system-ip", "")
        # different versions use 'reachability' or 'status'
        reach       = d.get("reachability", d.get("status", ""))
        ctrl_conn   = d.get("controlConnections", d.get("controlConnectionsUp", ""))
        omp_peers   = d.get("ompPeers", d.get("ompPeersUp", ""))
        device_type = d.get("device-type", "")
        version     = d.get("version", "")
        model       = d.get("device-model", "")

        row = [
            hostname,
            system_ip,
            reach,
            ctrl_conn,
            omp_peers,
            device_type,
            version,
            model,
        ]
        table.append(row)

    print(tabulate.tabulate(table, headers, tablefmt="fancy_grid"))


if __name__ == "__main__":
    main()

