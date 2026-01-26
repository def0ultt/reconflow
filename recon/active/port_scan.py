import time

def scan_ports(target: str):
    """
    Perform port scanning on the target.
    """
    print(f"🔌 Scanning ports on {target}...")
    # Simulated work
    time.sleep(1)
    results = [80, 443, 22, 8080]
    print(f"✅ Found open ports: {', '.join(map(str, results))}")
    return results
