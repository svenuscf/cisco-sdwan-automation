from vmanage_api import VManage
from creds_loader import load_vmanage_creds
import sys
import tabulate
import json
from datetime import datetime
import csv

def ms_to_date(ms_val):
    try:
        if isinstance(ms_val, (int, float)) and ms_val > 1000000000:
            return datetime.fromtimestamp(ms_val / 1000).strftime("%Y-%m-%d %H:%M:%S")
        else:
            return ms_val
    except Exception:
        return ms_val

def list_policies(vm):
    resp = vm.get("/v1/feature-profile/sdwan/embedded-security")
    if isinstance(resp, dict) and "data" in resp:
        profiles = resp["data"]
    elif isinstance(resp, list):
        profiles = resp
    else:
        raise ValueError(f"Unexpected format: {json.dumps(resp, indent=2)}")
    return profiles

def pick_policy(profiles):
    headers = ["#", "Policy ID", "Name", "Description", "Last Updated By", "Last Updated"]
    table = []
    for idx, p in enumerate(profiles, start=1):
        table.append([
            idx,
            p.get("profileId", ""),
            p.get("profileName", ""),
            p.get("description", ""),
            p.get("lastUpdatedBy", ""),
            ms_to_date(p.get("lastUpdatedOn", ""))
        ])
    print(tabulate.tabulate(table, headers, tablefmt="fancy_grid"))

    while True:
        choice = input("Select a policy number to view NGFW details (or 'q' to quit): ").strip()
        if choice.lower() == "q":
            sys.exit(0)
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(profiles):
                return profiles[choice - 1].get("profileId", "")
        print("Invalid selection, try again.")

def get_friendly_name(vm, ref_id):
    """Try to resolve a UUID to a friendly name via policy-object API."""
    try:
        resp = vm.get(f"/v1/feature-profile/sdwan/policy-object/{ref_id}")
        if isinstance(resp, dict):
            return resp.get("name", ref_id)
    except Exception:
        pass
    return ref_id  # fallback to UUID if lookup fails

def parse_ngfw(vm, parcel_list):
    """Convert NGFW parcels to readable structured table."""
    headers = [
        "Parcel Name", "Rule Name", "Base Action", "Enabled?",
        "Source IP", "Destination IP", "Prefix List Name", "Port List Name", "FQDN List Name",
        "Extra Actions"
    ]
    table = []

    for parcel in parcel_list:
        payload = parcel.get("payload", {})
        parcel_name = payload.get("name", "")
        sequences = payload.get("data", {}).get("sequences", [])

        for seq in sequences:
            rule_name = seq.get("sequenceName", {}).get("value", "")
            base_action = seq.get("baseAction", {}).get("value", "")
            enabled = not seq.get("disableSequence", {}).get("value", False)

            src_ip = dst_ip = prefix_list = port_list = fqdn_list = ""

            match_entries = seq.get("match", {}).get("entries", [])
            for entry in match_entries:
                if "sourceIp" in entry:
                    vals = entry["sourceIp"]["ipv4Value"]["value"]
                    src_ip = ", ".join(vals)
                if "destinationIp" in entry:
                    vals = entry["destinationIp"]["ipv4Value"]["value"]
                    dst_ip = ", ".join(vals)
                if "destinationDataPrefixList" in entry:
                    ref_id = entry["destinationDataPrefixList"]["refId"]["value"][0]
                    prefix_list = get_friendly_name(vm, ref_id)
                if "destinationPortList" in entry:
                    ref_id = entry["destinationPortList"]["refId"]["value"][0]
                    port_list = get_friendly_name(vm, ref_id)
                if "destinationFqdnList" in entry:
                    ref_id = entry["destinationFqdnList"]["refId"]["value"][0]
                    fqdn_list = get_friendly_name(vm, ref_id)

            extra_actions = []
            for act in seq.get("actions", []):
                act_type = act.get("type", {}).get("value", "")
                act_param = act.get("parameter", {}).get("value", "")
                if act_type:
                    extra_actions.append(f"{act_type}={act_param}")
            extra_str = "; ".join(extra_actions) if extra_actions else "-"

            table.append([
                parcel_name, rule_name, base_action, "Yes" if enabled else "No",
                src_ip or "-", dst_ip or "-", prefix_list or "-", port_list or "-", fqdn_list or "-",
                extra_str
            ])
    return headers, table

def show_ngfw_details(vm, policy_id):
    endpoint = f"/v1/feature-profile/sdwan/embedded-security/{policy_id}/unified/ngfirewall"
    resp = vm.get(endpoint)

    if isinstance(resp, dict) and "data" in resp:
        parcels = resp["data"]
    elif isinstance(resp, list):
        parcels = resp
    else:
        print("Unexpected NGFW detail format:")
        print(json.dumps(resp, indent=2))
        return

    headers, rows = parse_ngfw(vm, parcels)
    print("\n=== NGFW Policy Table ===")
    print(tabulate.tabulate(rows, headers=headers, tablefmt="fancy_grid"))

    # Optional CSV export
    save_csv = input("Export to CSV? (y/n): ").strip().lower()
    if save_csv == "y":
        filename = f"{policy_id}_ngfw.csv"
        with open(filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"Saved table to {filename}")

def main():
    if len(sys.argv) >= 4:
        host, user, pwd = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        host, user, pwd = load_vmanage_creds()

    vm = VManage(host, user, pwd)

    try:
        profiles = list_policies(vm)
    except Exception as e:
        print(f"Error fetching profiles: {e}")
        sys.exit(1)

    policy_id = pick_policy(profiles)
    show_ngfw_details(vm, policy_id)

if __name__ == "__main__":
    main()
