#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess
from collections import defaultdict
import shutil

def check_nmap():
    if not shutil.which("nmap"):
        print("Error: nmap is not installed or not in PATH.")
        sys.exit(1)

def parse_naabu_output(filepath):
    """
    Parses a file containing 'host:port' lines.
    Returns a dict: {host: [port1, port2, ...]}
    """
    targets = defaultdict(list)
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if ':' in line:
                    host, port = line.rsplit(':', 1)
                    targets[host].append(port)
                else:
                    # Just host, assume default scan or skip? 
                    # Naabu usually outputs host:port
                    pass
    except FileNotFoundError:
        print(f"Error: Input file '{filepath}' not found.")
        sys.exit(1)
    return targets

def run_nmap(host, ports, verify=False):
    """
    Runs nmap against the host for the specified ports.
    """
    ports_str = ",".join(ports)
    print(f"[*] Scanning {host} on ports: {ports_str}")
    
    # Base command
    # -sV: Version detection
    # -sC: Default scripts
    # -Pn: Treat as online
    cmd = ["nmap", "-sV", "-sC", "-Pn", "-p", ports_str, host]
    
    # Check for root if we want OS detection or SYN scan (not enabled here by default but user might want it)
    # The user specifically mentioned sudo issues. 
    # If we are not root, and we need root features, nmap fails or degrades.
    
    # Let's check effective UID
    euid = os.geteuid()
    if euid != 0:
        print(f"[!] Warning: Running without root privileges. Nmap functionality may be limited.")
        # Attempt to use sudo if available and passwordless?
        # Or just let nmap run and fail if it needs root.
        # Often it's better to just run the script with sudo: sudo python naabutonmap.py
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error scanning {host}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Convert Naabu output to Nmap scan")
    parser.add_argument("-i", "--input", required=True, help="Input file from Naabu (host:port)")
    parser.add_argument("--sudo", action="store_true", help="Attempt to prepend sudo to nmap command")
    args = parser.parse_args()

    check_nmap()
    targets = parse_naabu_output(args.input)

    if not targets:
        print("[-] No targets found in input file.")
        return

    print(f"[+] Found {len(targets)} hosts to scan.")
    
    for host, ports in targets.items():
        # Clean up ports (remove duplicates, sort)
        ports = sorted(list(set(ports)), key=lambda x: int(x) if x.isdigit() else 0)
        
        nmap_cmd = ["nmap", "-sV", "-sC", "-Pn", "-p", ",".join(ports), host]
        
        if args.sudo:
            if os.geteuid() != 0:
                nmap_cmd.insert(0, "sudo")
        
        print(f"[*] Executing: {' '.join(nmap_cmd)}")
        try:
             subprocess.run(nmap_cmd, check=True)
        except subprocess.CalledProcessError:
             print(f"[!] Failed to scan {host}")
        except KeyboardInterrupt:
            print("\n[!] Scan interrupted.")
            sys.exit(0)

if __name__ == "__main__":
    main()
