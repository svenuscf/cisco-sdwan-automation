from vmanage_api import VManage
from creds_loader import load_vmanage_creds
import json
import sys
import tabulate
import ipaddress

def list_policy_object_profiles(vm):
    """Return all policy-object profiles."""
    resp = vm.get("/v1/feature-profile/sdwan/policy-object")
    if isinstance(resp, dict) and "data" in resp:
        return resp["data"]
    elif isinstance(resp, list):
        return resp
    else:
        raise ValueError("Unexpected format from vManage")

def build_prefix_menu(vm, profiles):
    """Build menu from all prefixes in all profiles."""
    menu_items = []
    counter = 1
    for p in profiles:
        profile_id = p.get("profileId", "")
        url = f"/v1/feature-profile/sdwan/policy-object/{profile_id}/security-data-ip-prefix"
        resp = vm.get(url)
        prefixes = resp["data"] if isinstance(resp, dict) and "data" in resp else resp
        for prefix in prefixes:
            payload = prefix.get("payload", {})
            name = payload.get("name", "")
            menu_items.append({
                "number": counter,
                "prefix_name": name,
                "profile_id": profile_id,
                "parcel_id": prefix.get("parcelId", ""),
                "full_entry": prefix
            })
            counter += 1
    return menu_items

def expand_only_16_subnets(ip_list):
    """Expand only /16 subnets into .1.10/32 and .1.11/32."""
    generated_entries = []
    for ip_str in ip_list:
        net = ipaddress.ip_network(ip_str, strict=False)
        if net.prefixlen == 16:
            octets = ip_str.split(".")
            host1 = f"{octets[0]}.{octets[1]}.1.10/32"
            host2 = f"{octets[0]}.{octets[1]}.1.11/32"
            generated_entries.append({"ipPrefix": {"optionType": "global", "value": host1}})
            generated_entries.append({"ipPrefix": {"optionType": "global", "value": host2}})
    return generated_entries

def merge_entries_unique(existing_entries, new_entries):
    """Merge entries avoiding duplicates."""
    existing_values = {e["ipPrefix"]["value"] for e in existing_entries}
    merged = existing_entries.copy()
    for entry in new_entries:
        if entry["ipPrefix"]["value"] not in existing_values:
            merged.append(entry)
            existing_values.add(entry["ipPrefix"]["value"])
    return merged

def push_update(vm, profile_id, parcel_id, prefix_name, entries):
    updated_payload = {
        "name": prefix_name,
        "data": {
            "entries": entries
        }
    }
    resp = vm.put(f"/v1/feature-profile/sdwan/policy-object/{profile_id}/security-data-ip-prefix/{parcel_id}", updated_payload)
    return resp

def main():
    # Login
    host, user, pwd = load_vmanage_creds()
    vm = VManage(host, user, pwd)

    # Find grp_Data_Server_for_PCI_Access
    profiles = list_policy_object_profiles(vm)
    menu_items = build_prefix_menu(vm, profiles)
    target = next((item for item in menu_items if item["prefix_name"] == "grp_Data_Server_for_PCI_Access"), None)
    if not target:
        print("Error: grp_Data_Server_for_PCI_Access not found!")
        sys.exit(1)

    payload = target["full_entry"].get("payload", {})
    existing_entries = payload.get("data", {}).get("entries", [])

    # Your tweaked list (only /16 entries will be expanded)
    given_list = [
        "10.32.0.0/16", "10.23.0.0/16", "10.26.0.0/16", "10.14.0.0/16",
        "10.38.0.0/16", "10.13.0.0/16", "10.40.0.0/16", "10.15.0.0/16",
        "10.33.0.0/16", "10.34.0.0/16", "10.16.0.0/16", "10.37.0.0/16",
        "10.6.0.0/16", "10.4.0.0/16", "10.11.0.0/16", "10.18.0.0/16",
        "10.29.0.0/16", "10.7.0.0/16", "10.41.0.0/16", "10.19.0.0/16",
        "10.46.0.0/16", "10.5.0.0/16", "10.20.0.0/16", "10.22.0.0/16",
        "10.42.0.0/16", "10.9.0.0/16", "10.3.0.0/16", "10.10.0.0/16",
        "10.21.0.0/16", "10.45.0.0/16"
    ]

    # Generate expansions (only /16s)
    new_entries = expand_only_16_subnets(given_list)

    # Merge with duplicate check
    updated_entries = merge_entries_unique(existing_entries, new_entries)

    # Preview before push
    headers = ["IP Prefix", "Option Type"]
    rows = [(e["ipPrefix"]["value"], e["ipPrefix"]["optionType"]) for e in updated_entries]
    print("\n=== Updated entries preview ===")
    print(tabulate.tabulate(rows, headers=headers, tablefmt="fancy_grid"))

    confirm = input("Confirm push to vManage? (y/n): ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    # Push update
    resp = push_update(vm, target["profile_id"], target["parcel_id"], "grp_Data_Server_for_PCI_Access", updated_entries)
    print("\nPush result:")
    print(json.dumps(resp, indent=2))

    # Verify
    updated_obj = vm.get(f"/v1/feature-profile/sdwan/policy-object/{target['profile_id']}/security-data-ip-prefix/{target['parcel_id']}")
    print("\n=== Updated Prefix Object ===")
    payload = updated_obj.get("payload", {})
    entries = payload.get("data", {}).get("entries", [])
    confirm_rows = [(e["ipPrefix"]["value"], e["ipPrefix"]["optionType"]) for e in entries]
    print(tabulate.tabulate(confirm_rows, headers=headers, tablefmt="fancy_grid"))

if __name__ == "__main__":
    main()
