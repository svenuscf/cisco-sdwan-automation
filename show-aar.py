from vmanage_api import VManage
from creds_loader import load_vmanage_creds
import sys
import json
import tabulate
from datetime import datetime

def ms_to_date(ms_val):
    try:
        if isinstance(ms_val, (int, float)) and ms_val > 1000000000:
            return datetime.fromtimestamp(ms_val / 1000).strftime("%Y-%m-%d %H:%M:%S")
        else:
            return ms_val
    except Exception:
        return ms_val

def list_aar_policies(vm):
    """Fetch all application-priority profiles."""
    resp = vm.get("/v1/feature-profile/sdwan/application-priority?referenceCount=true")
    if isinstance(resp, dict) and "data" in resp:
        policies = resp["data"]
    elif isinstance(resp, list):
        policies = resp
    else:
        raise ValueError(f"Unexpected format: {json.dumps(resp, indent=2)}")
    return policies

def pick_aar_policy(policies):
    headers = ["#", "Profile Name", "Description", "Parcel Count", "Last Updated By", "Last Updated", "Ref Count"]
    table = []

    for idx, p in enumerate(policies, start=1):
        table.append([
            idx,
            p.get("profileName", ""),
            p.get("description", ""),
            p.get("profileParcelCount", ""),
            p.get("lastUpdatedBy", ""),
            ms_to_date(p.get("lastUpdatedOn", "")),
            p.get("referenceCount", "")
        ])

    print(tabulate.tabulate(table, headers, tablefmt="fancy_grid"))

    while True:
        choice = input("Select a policy number to expand (or 'q' to quit): ").strip()
        if choice.lower() == "q":
            sys.exit(0)
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(policies):
                return policies[choice - 1]  # return full policy object
        print("Invalid selection, try again.")

def expand_aar_policy(vm, policy):
    """Fetch and display parcels/subparcels in table format."""
    profile_id = policy.get("profileId", "")
    if not profile_id:
        print("No profileId found for selected policy.")
        return

    endpoint = f"/v1/feature-profile/sdwan/application-priority/{profile_id}"
    resp = vm.get(endpoint)

    # get associated parcels
    parcels = resp.get("associatedProfileParcels", [])
    if not parcels:
        print("\nNo associated parcels found for this policy.")
        return

    # build table for main parcels
    headers = ["#", "Parcel Name", "Parcel Type", "Created By", "Last Updated By", "Last Updated"]
    table = []
    row_num = 1

    for parcel in parcels:
        table.append([
            row_num,
            parcel.get("payload", {}).get("name", ""),
            parcel.get("parcelType", ""),
            parcel.get("createdBy", ""),
            parcel.get("lastUpdatedBy", ""),
            ms_to_date(parcel.get("lastUpdatedOn", ""))
        ])

        row_num += 1

        # add subparcels if any
        subparcels = parcel.get("subparcels", [])
        if subparcels:
            for sp in subparcels:
                table.append([
                    "",  # no row number for subparcel
                    f"  ↳ {sp.get('payload', {}).get('name', '')}",
                    sp.get("parcelType", ""),
                    sp.get("createdBy", ""),
                    sp.get("lastUpdatedBy", ""),
                    ms_to_date(sp.get("lastUpdatedOn", ""))
                ])

    print("\n=== Associated Parcels for Policy ===")
    print(tabulate.tabulate(table, headers=headers, tablefmt="fancy_grid"))

def main():
    if len(sys.argv) >= 4:
        host, user, pwd = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        host, user, pwd = load_vmanage_creds()

    vm = VManage(host, user, pwd)

    try:
        policies = list_aar_policies(vm)
    except Exception as e:
        print(f"Error fetching AAR policies: {e}")
        sys.exit(1)

    selected_policy = pick_aar_policy(policies)
    expand_aar_policy(vm, selected_policy)

if __name__ == "__main__":
    main()
