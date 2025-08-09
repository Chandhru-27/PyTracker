import subprocess
import socket
import time
from typing import Iterable, Set

try:
    # Use existing admin check
    from utils.utilities import Utility
except Exception:
    Utility = None


RULE_PREFIX = "PyTrackerBlock"


def resolve_domain_ips(domain: str) -> Set[str]:
    """Resolve a domain to a set of IPv4 addresses."""
    ips: Set[str] = set()
    try:
        for family, _, _, _, sockaddr in socket.getaddrinfo(domain, None):
            if family == socket.AF_INET:  # IPv4 only for firewall simplicity
                ip = sockaddr[0]
                ips.add(ip)
    except Exception:
        pass
    return ips


def _run(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def rule_name_for(domain: str) -> str:
    return f"{RULE_PREFIX} {domain}"


def delete_rule(domain: str) -> None:
    name = rule_name_for(domain)
    _run(f'netsh advfirewall firewall delete rule name="{name}"')


def add_block_rule_for_ips(domain: str, ips: Iterable[str]) -> bool:
    """Create/replace an outbound firewall rule that blocks the given IPs for the domain."""
    ip_list = ",".join(sorted(ips))
    if not ip_list:
        return False
    name = rule_name_for(domain)
    # Remove any existing rule first (idempotent behavior)
    delete_rule(domain)
    cmd = (
        f'netsh advfirewall firewall add rule name="{name}" '
        f'dir=out action=block remoteip={ip_list} enable=yes protocol=any'
    )
    result = _run(cmd)
    return result.returncode == 0


def add_block_rule_fqdn(domain: str) -> bool:
    """Attempt to block by FQDN using PowerShell New-NetFirewallRule if supported (Win10+)."""
    name = rule_name_for(domain)
    # Delete any existing rule with this name (regardless of type)
    delete_rule(domain)
    # Use PowerShell cmdlet which supports FQDN in -RemoteAddress on modern Windows
    ps_cmd = (
        f'powershell -Command "New-NetFirewallRule -DisplayName \"{name}\" '
        f'-Direction Outbound -Action Block -RemoteAddress {domain} -Enabled True"'
    )
    result = _run(ps_cmd)
    # Heuristic: returncode 0 and no obvious error in stderr
    return result.returncode == 0 and not result.stderr.strip()


def update_domain_block(domain: str) -> bool:
    """Resolve current IPs and (re)apply the firewall rule."""
    ips = resolve_domain_ips(domain)
    return add_block_rule_for_ips(domain, ips)


def block_domains(domains: Iterable[str]) -> None:
    for d in domains:
        ok = update_domain_block(d)
        print(f"[{d}] block {'OK' if ok else 'FAILED'}")


def unblock_domains(domains: Iterable[str]) -> None:
    for d in domains:
        delete_rule(d)
        print(f"[{d}] unblocked (rule deleted)")


def show_rule(domain: str) -> None:
    name = rule_name_for(domain)
    out = _run(f'netsh advfirewall firewall show rule name="{name}"')
    print(out.stdout or out.stderr)


def quick_demo():
    """Run a safe demo: block example.com briefly, show rule, then remove."""
    test_domain = "facebook.com"

    if Utility and not Utility.is_admin():
        print("[!] Please run this script as Administrator to modify firewall rules.")
        return

    print(f"Resolving {test_domain}...")
    ips = resolve_domain_ips(test_domain)
    print(f"IPs: {', '.join(sorted(ips)) or 'None'}")
    if not ips:
        print("No IPs resolved; skipping demo.")
        return

    print(f"Adding firewall block for {test_domain} (trying FQDN)...")
    ok = add_block_rule_fqdn(test_domain)
    if not ok:
        print("FQDN not supported or failed; falling back to IP list...")
        ok = add_block_rule_for_ips(test_domain, ips)
    print("Add rule:", "OK" if ok else "FAILED")

    print("Showing rule:")
    show_rule(test_domain)

    print("Waiting 10s...")
    time.sleep(10)

    print("Removing rule...")
    delete_rule(test_domain)
    print("Done.")


if __name__ == "__main__":
    # Change domains here for a manual test, e.g., ["facebook.com", "instagram.com"]
    quick_demo()


