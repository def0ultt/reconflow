#!/usr/bin/env python3

import requests
import argparse
import sys
import json
import time
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# Try importing rich for beautiful output
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.table import Table
    from rich import print as rprint
except ImportError:
    print("[-] Please install 'rich' library for beautiful output: pip install rich")
    sys.exit(1)

# --- Configuration ---
# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
}

def banner():
    text = """
    [bold cyan]╔21:00╗[/bold cyan] [bold white]BACKUP ARTIFACT HUNTER[/bold white]
    [bold cyan]╚═════╝[/bold cyan] [dim]Advanced Enumeration Tool[/dim]
    """
    rprint(text)

def get_domain_parts(url):
    """Parses URL and returns domain parts for wordlist generation."""
    if not url.startswith('http'):
        url = f"http://{url}"
    
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Split domain into parts (e.g., test.dev.example.com -> [test, dev, example, com])
    parts = domain.split('.')
    return url, domain, parts

def generate_wordlist(subdomains, mode):
    """
    Generates the list of filenames (stems) to test based on the Mode.
    """
    local_map = {} # Key: Subdomain, Value: List of stems to try on that subdomain
    global_words = set()

    # Pre-process to gather words
    for sub in subdomains:
        _, domain, parts = get_domain_parts(sub)
        
        # Always add the full domain (e.g., sub.example.com)
        stems = set()
        stems.add(domain) 
        
        # Add the first part (hostname)
        if parts:
            stems.add(parts[0])
            global_words.add(parts[0])

        # Add composite (sub.example)
        if len(parts) > 2:
            composite = f"{parts[0]}.{parts[1]}"
            stems.add(composite)
            global_words.add(composite)

        # Mode 2 Aggressive: Add all individual parts
        if mode >= 2:
            for p in parts:
                stems.add(p)
                global_words.add(p)

        local_map[sub] = list(stems)

    # Mode 3: Apply ALL words found to ALL domains
    if mode == 3:
        final_map = {}
        global_list = list(global_words)
        for sub in subdomains:
            final_map[sub] = global_list
        return final_map
    
    return local_map

def check_target(target_data):
    """
    Worker function.
    target_data = (url, proxy_config)
    """
    url, proxies = target_data
    result = {
        "url": url,
        "status": 0,
        "length": 0,
        "found": False
    }

    try:
        # HEAD request first for speed
        resp = requests.head(url, headers=HEADERS, proxies=proxies, verify=False, timeout=5, allow_redirects=True)
        
        # 405 Method Not Allowed? Try GET
        if resp.status_code == 405:
             resp = requests.get(url, headers=HEADERS, proxies=proxies, verify=False, stream=True, timeout=5)
             resp.close()

        result["status"] = resp.status_code
        result["length"] = int(resp.headers.get('content-length', 0))

        if resp.status_code in [200, 401, 403]:
            # Simple filter: Ignore 200 OK if content-length is 0
            if resp.status_code == 200 and result["length"] == 0:
                pass
            else:
                result["found"] = True

    except Exception:
        pass

    return result

def main():
    parser = argparse.ArgumentParser(description="Backup File Hunter")
    parser.add_argument("-f", "--file", required=True, help="List of subdomains")
    parser.add_argument("-x", "--extensions", required=True, help="List of extensions")
    parser.add_argument("-m", "--mode", type=int, choices=[1, 2, 3], default=1, help="1=Normal, 2=Aggressive, 3=All Combinations")
    parser.add_argument("-p", "--proxy", help="Proxy URL (http://127.0.0.1:8080)")
    parser.add_argument("-t", "--threads", type=int, default=20, help="Threads")
    parser.add_argument("--json", help="Output file for JSONL format (e.g., output.jsonl)")
    
    args = parser.parse_args()
    
    banner()

    # 1. Load Data
    try:
        with open(args.file, 'r') as f:
            subs = [line.strip() for line in f if line.strip()]
        with open(args.extensions, 'r') as f:
            exts = [line.strip() if line.strip().startswith('.') else f".{line.strip()}" for line in f if line.strip()]
    except FileNotFoundError:
        console.print("[bold red][!] File not found.[/bold red]")
        sys.exit(1)

    # 2. Prepare Proxy
    proxies = {"http": args.proxy, "https": args.proxy} if args.proxy else None
    if proxies:
        console.print(f"[yellow][*] Proxy Enabled:[/yellow] {args.proxy}")

    # 3. Generate Tasks based on Mode
    console.print(f"[blue][*] analyzing {len(subs)} domains in Mode {args.mode}...[/blue]")
    
    wordlist_map = generate_wordlist(subs, args.mode)
    tasks = []

    for sub in subs:
        base_url = f"http://{sub}" if not sub.startswith('http') else sub
        base_url = base_url.rstrip('/')
        
        # Get the specific list of words for this domain based on the map
        stems = wordlist_map.get(sub, [])
        
        for stem in stems:
            for ext in exts:
                full_url = f"{base_url}/{stem}{ext}"
                tasks.append((full_url, proxies))

    console.print(f"[bold green][+] Generated {len(tasks)} URLs to check.[/bold green]")
    console.print("-" * 50)

    # 4. Execute with Progress Bar
    found_count = 0
    json_file = None
    
    if args.json:
        json_file = open(args.json, 'a')

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task_id = progress.add_task("[cyan]Scanning...", total=len(tasks))
            
            with ThreadPoolExecutor(max_workers=args.threads) as executor:
                # Submit all tasks
                futures = {executor.submit(check_target, t): t for t in tasks}
                
                for future in as_completed(futures):
                    result = future.result()
                    progress.advance(task_id)
                    
                    if result["found"]:
                        found_count += 1
                        
                        # Color coding based on status
                        color = "green"
                        if result["status"] == 401: color = "yellow"
                        if result["status"] == 403: color = "magenta"
                        
                        # Print finding to console
                        console.print(f"[{color}][{result['status']}] found: {result['url']} (Size: {result['length']})[/{color}]")
                        
                        # Save to JSON if requested
                        if json_file:
                            json.dump(result, json_file)
                            json_file.write('\n')
                            json_file.flush()

    except KeyboardInterrupt:
        console.print("\n[bold red][!] Scan interrupted by user.[/bold red]")
    finally:
        if json_file:
            json_file.close()

    console.print("-" * 50)
    console.print(f"[bold white]Scan Finished. Found {found_count} files.[/bold white]")
    if args.json:
        console.print(f"[dim]JSONL results saved to: {args.json}[/dim]")

if __name__ == "__main__":
    main()