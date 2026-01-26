import time

def check_vulnerabilities(target: str):
    """
    Check for vulnerabilities on the target.
    """
    print(f"🛡️  Checking vulnerabilities on {target}...")
    # Simulated work
    time.sleep(1.5)
    print("⚠️  Found potential issue: X-Powered-By header revealed")
    return ["X-Powered-By revealed"]
