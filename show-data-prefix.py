from vmanage_api import VManage
from creds_loader import load_vmanage_creds
import sys
import tabulate
import json

def list_policy_object_profiles(vm):
    """Fetch all SD-WAN policy-object feature profiles."""
    resp = vm.get("/v1/feature-profile/sdwan/policy-object")
    if isinstance(resp, dict) and "data" in resp:
        profiles = resp["data"]
    elif isinstance(resp, list):
        profiles = resp
    else:
        raise ValueError(f"Unexpected format: {json.dumps(resp, indent=2)}")
    return profiles

def build_prefix_menu(vm, profiles):
    """Loop through all profiles and retrieve their security-data-ip-prefix entries."""
    menu_items = []
    counter = 1

    for p in profiles:
        profile_id = p.get("profileId", "")
        url = f"/v1/feature-profile/sdwan/policy-object/{profile_id}/security-data-ip-prefix"
        resp = vm.get(url)

        # Data can be dict with "data" or a list
        if isinstance(resp, dict) and "data" in resp:
            prefixes = resp["data"]
        elif isinstance(resp, list):
            prefixes = resp
        else:
            prefixes = []

        for prefix in prefixes:
            payload = prefix.get("payload", {})
            prefix_name = payload.get("name", "")
            menu_items.append({
                "number": counter,
                "prefix_name": prefix_name,
                "parcel_id": prefix.get("parcelId", ""),
                "parcel_type": prefix.get("parcelType", ""),
                "created_by": prefix.get("createdBy", ""),
                "full_entry": prefix
            })
            counter += 1

    return menu_items

def pick_prefix(menu_items):
    """Show the prefixes as a numbered table and let user select one."""
    headers = ["#", "Prefix Object Name", "Parcel ID", "Parcel Type", "Created By"]
    table = [
        [item["number"], item["prefix_name"], item["parcel_id"], item["parcel_type"], item["created_by"]]
        for item in menu_items
    ]

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

def show_prefix_details(selected):
    """Display the list of prefixes from the payload in a clean table."""
    payload = selected.get("full_entry", {}).get("payload", {})
    prefix_name = payload.get("name", "")
    entries = payload.get("data", {}).get("entries", [])

    headers = ["Prefix Object Name", "IP Prefix", "Option Type"]
    rows = []
    for entry in entries:
        ip_info = entry.get("ipPrefix", {})
        rows.append([prefix_name, ip_info.get("value", "-"), ip_info.get("optionType", "-")])

    if rows:
        print("\n=== Prefix Entries ===")
        print(tabulate.tabulate(rows, headers=headers, tablefmt="fancy_grid"))
    else:
        print("\nNo entries found for this prefix object.")

def main():
    if len(sys.argv) >= 4:
        host, user, pwd = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        host, user, pwd = load_vmanage_creds()

    vm = VManage(host, user, pwd)

    try:
        profiles = list_policy_object_profiles(vm)
    except Exception as e:
        print(f"Error fetching profiles: {e}")
        sys.exit(1)

    menu_items = build_prefix_menu(vm, profiles)
    if not menu_items:
        print("No security-data-ip-prefix entries found.")
        sys.exit(0)

    selected_prefix = pick_prefix(menu_items)
    show_prefix_details(selected_prefix)

if __name__ == "__main__":
    main()
