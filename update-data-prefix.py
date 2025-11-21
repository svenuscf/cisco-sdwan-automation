from vmanage_api import VManage
from creds_loader import load_vmanage_creds
import sys
import tabulate
import json

def list_policy_object_profiles(vm):
    resp = vm.get("/v1/feature-profile/sdwan/policy-object")
    if isinstance(resp, dict) and "data" in resp:
        return resp["data"]
    elif isinstance(resp, list):
        return resp
    else:
        raise ValueError(f"Unexpected format: {json.dumps(resp, indent=2)}")

def build_prefix_menu(vm, profiles):
    menu_items = []
    counter = 1
    for p in profiles:
        profile_id = p.get("profileId", "")
        url = f"/v1/feature-profile/sdwan/policy-object/{profile_id}/security-data-ip-prefix"
        resp = vm.get(url)
        prefixes = resp["data"] if isinstance(resp, dict) and "data" in resp else resp

        for prefix in prefixes:
            payload = prefix.get("payload", {})
            prefix_name = payload.get("name", "")
            menu_items.append({
                "number": counter,
                "prefix_name": prefix_name,
                "profile_id": profile_id,
                "parcel_id": prefix.get("parcelId", ""),
                "parcel_type": prefix.get("parcelType", ""),
                "created_by": prefix.get("createdBy", ""),
                "full_entry": prefix
            })
            counter += 1
    return menu_items

def pick_prefix(menu_items):
    headers = ["#", "Prefix Object Name", "Parcel ID", "Created By"]
    table = [[i["number"], i["prefix_name"], i["parcel_id"], i["created_by"]] for i in menu_items]
    print(tabulate.tabulate(table, headers, tablefmt="fancy_grid"))

    while True:
        choice = input("Select a number to view prefix details (or 'q' to quit): ").strip()
        if choice.lower() == "q":
            sys.exit(0)
        if choice.isdigit():
            choice_num = int(choice)
            selected = next((i for i in menu_items if i["number"] == choice_num), None)
            if selected:
                return selected
        print("Invalid selection, try again.")

def show_prefix_details_table(prefix_object):
    payload = prefix_object.get("payload", {})
    prefix_name = payload.get("name", "")
    entries = payload.get("data", {}).get("entries", [])

    headers = ["#", "Prefix Object Name", "IP Prefix", "Option Type"]
    rows = []
    for idx, entry in enumerate(entries, start=1):
        ip_info = entry.get("ipPrefix", {})
        rows.append([idx, prefix_name, ip_info.get("value", "-"), ip_info.get("optionType", "-")])

    print("\n=== Prefix Entries ===")
    if rows:
        print(tabulate.tabulate(rows, headers=headers, tablefmt="fancy_grid"))
    else:
        print("No entries found for this prefix object.")

def push_update(vm, profile_id, parcel_id, prefix_name, entries):
    updated_payload = {
        "name": prefix_name,
        "data": {
            "entries": entries
        }
    }
    resp = vm.put(f"/v1/feature-profile/sdwan/policy-object/{profile_id}/security-data-ip-prefix/{parcel_id}", updated_payload)
    return resp

def add_multiple_prefixes(vm, selected):
    payload = selected.get("full_entry", {}).get("payload", {})
    prefix_name = payload.get("name", "")
    entries = payload.get("data", {}).get("entries", [])
    profile_id = selected["profile_id"]
    parcel_id = selected["parcel_id"]

    new_prefixes = []
    print("\nEnter new prefixes (blank to finish):")
    while True:
        prefix_value = input(f"New IP prefix for '{prefix_name}': ").strip()
        if not prefix_value:
            break
        option_type = input("Option type (default 'global'): ").strip() or "global"
        new_prefixes.append({"ipPrefix": {"optionType": option_type, "value": prefix_value}})

    if not new_prefixes:
        print("No new prefixes entered. Aborting.")
        return

    entries.extend(new_prefixes)
    print("\nUpdated entries will be:")
    print(tabulate.tabulate([(e["ipPrefix"]["value"], e["ipPrefix"]["optionType"]) for e in entries],
                            headers=["IP Prefix", "Option Type"], tablefmt="fancy_grid"))

    if input("Confirm push to vManage? (y/n): ").strip().lower() != "y":
        print("Aborted.")
        return

    resp = push_update(vm, profile_id, parcel_id, prefix_name, entries)
    print("\nPush result:")
    print(json.dumps(resp, indent=2))
    updated_obj = vm.get(f"/v1/feature-profile/sdwan/policy-object/{profile_id}/security-data-ip-prefix/{parcel_id}")
    show_prefix_details_table(updated_obj)

def delete_prefixes(vm, selected):
    payload = selected.get("full_entry", {}).get("payload", {})
    prefix_name = payload.get("name", "")
    entries = payload.get("data", {}).get("entries", [])
    profile_id = selected["profile_id"]
    parcel_id = selected["parcel_id"]

    show_prefix_details_table(selected["full_entry"])

    del_indexes = input("\nEnter prefix numbers to delete (comma-separated): ").strip()
    if not del_indexes:
        print("No prefixes selected for deletion. Aborting.")
        return

    try:
        indexes_to_delete = sorted(set(int(i.strip()) for i in del_indexes.split(",")), reverse=True)
    except ValueError:
        print("Invalid input. Aborting.")
        return

    for idx in indexes_to_delete:
        if 1 <= idx <= len(entries):
            del entries[idx - 1]

    print("\nUpdated entries will be:")
    print(tabulate.tabulate([(e["ipPrefix"]["value"], e["ipPrefix"]["optionType"]) for e in entries],
                            headers=["IP Prefix", "Option Type"], tablefmt="fancy_grid"))

    if input("Confirm deletion push to vManage? (y/n): ").strip().lower() != "y":
        print("Aborted.")
        return

    resp = push_update(vm, profile_id, parcel_id, prefix_name, entries)
    print("\nPush result:")
    print(json.dumps(resp, indent=2))
    updated_obj = vm.get(f"/v1/feature-profile/sdwan/policy-object/{profile_id}/security-data-ip-prefix/{parcel_id}")
    show_prefix_details_table(updated_obj)

def main():
    if len(sys.argv) >= 4:
        host, user, pwd = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        host, user, pwd = load_vmanage_creds()

    vm = VManage(host, user, pwd)
    profiles = list_policy_object_profiles(vm)
    menu_items = build_prefix_menu(vm, profiles)
    selected_prefix = pick_prefix(menu_items)
    show_prefix_details_table(selected_prefix["full_entry"])

    while True:
        action = input("\nOptions: [a] Add prefixes, [d] Delete prefixes, [q] Quit: ").strip().lower()
        if action == "q":
            sys.exit(0)
        elif action == "a":
            add_multiple_prefixes(vm, selected_prefix)
        elif action == "d":
            delete_prefixes(vm, selected_prefix)
        else:
            print("Invalid option, try again.")

if __name__ == "__main__":
    main()
