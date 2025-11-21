from vmanage_api import VManage
from creds_loader import load_vmanage_creds
import sys
import tabulate
from datetime import datetime, timezone

def format_uptime_ms(ms_value):
    """
    vManage returns uptime as epoch ms for many fields.
    Convert to 'Xd Yh Zm' based on now.
    """
    try:
        ms = int(ms_value)
    except (TypeError, ValueError):
        return "n/a"

    # Treat as "boot time" in epoch ms, compute how long since then
    boot_time = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - boot_time

    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)

def main():
    if len(sys.argv) >= 4:
        host, user, pwd = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        host, user, pwd = load_vmanage_creds()
    vm = VManage(host, user, pwd)

    devices = vm.get("device")
    print("\n=== Device Health Summary ===")
    print(f"{'HOSTNAME':30} {'SYSTEM-IP':15} {'STATE':10} {'UPTIME'}")

    for d in devices["data"]:
        hostname = d.get("host-name", "unknown")
        systemip = d.get("system-ip", "unknown")
        status   = d.get("status", "unknown")

        raw_uptime = (
            d.get("uptime") or
            d.get("uptime-date") or
            d.get("uptime-string") or
            d.get("lastupdated")
        )

        uptime_str = format_uptime_ms(raw_uptime) if raw_uptime else "n/a"

        print(f"{hostname:30} {systemip:15} {status:10} {uptime_str}")

if __name__ == "__main__":
    main()

