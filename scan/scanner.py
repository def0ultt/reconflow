from recon.active.port_scan import scan_ports
from recon.passive.subdomain_enum import enumerate_subdomains
from .vuln_scan import check_vulnerabilities

def perform_scan(target: str):
    """
    Perform a combined scan (recon + vuln) on the target.
    """
    print(f"🚀 Starting full scan on {target}...")
    
    # Simple logic: if domain, do subdomain enum
    if not target.replace('.','').isdigit(): 
        enumerate_subdomains(target)
    
    scan_ports(target)
    check_vulnerabilities(target)
    
    print("✅ Full scan completed.")
