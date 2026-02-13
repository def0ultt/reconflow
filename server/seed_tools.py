"""
Seed script to populate the database with common recon tool templates.
Run: python -m server.seed_tools
"""
import json
from db.session import get_session
from db.repositories.tool_repo import ToolRepository

SEED_TOOLS = [
    {
        "name": "subfinder",
        "description": "Fast passive subdomain enumeration tool",
        "binary_path": "subfinder",
        "category": "recon",
        "tags": json.dumps(["subdomain", "passive", "enumeration"]),
        "default_args": json.dumps(["-silent"]),
        "inputs": json.dumps([
            {"name": "domain", "type": "string", "required": True, "description": "Target domain"}
        ]),
        "outputs": json.dumps([
            {"name": "subdomains", "type": "file", "description": "Discovered subdomains"}
        ]),
        "icon": "globe",
        "author": "builtin",
    },
    {
        "name": "httpx",
        "description": "Fast HTTP toolkit for probing and technology detection",
        "binary_path": "httpx",
        "category": "recon",
        "tags": json.dumps(["http", "probe", "technology"]),
        "default_args": json.dumps(["-silent", "-status-code", "-title"]),
        "inputs": json.dumps([
            {"name": "urls", "type": "file", "required": True, "description": "List of URLs/hosts to probe"}
        ]),
        "outputs": json.dumps([
            {"name": "results", "type": "file", "description": "HTTP probe results"}
        ]),
        "icon": "zap",
        "author": "builtin",
    },
    {
        "name": "nmap",
        "description": "Network exploration and security auditing tool",
        "binary_path": "nmap",
        "category": "scanning",
        "tags": json.dumps(["port", "scan", "network", "service"]),
        "default_args": json.dumps(["-sV", "-T4"]),
        "inputs": json.dumps([
            {"name": "target", "type": "string", "required": True, "description": "Target IP/range/hostname"}
        ]),
        "outputs": json.dumps([
            {"name": "scan_results", "type": "file", "description": "Scan output"}
        ]),
        "icon": "radar",
        "author": "builtin",
    },
    {
        "name": "nuclei",
        "description": "Fast vulnerability scanner based on templates",
        "binary_path": "nuclei",
        "category": "vulnerability",
        "tags": json.dumps(["vuln", "scanner", "template"]),
        "default_args": json.dumps(["-silent", "-severity", "medium,high,critical"]),
        "inputs": json.dumps([
            {"name": "targets", "type": "file", "required": True, "description": "List of target URLs"}
        ]),
        "outputs": json.dumps([
            {"name": "findings", "type": "file", "description": "Vulnerability findings"}
        ]),
        "icon": "shield-alert",
        "author": "builtin",
    },
    {
        "name": "katana",
        "description": "Next-generation crawling and spidering framework",
        "binary_path": "katana",
        "category": "recon",
        "tags": json.dumps(["crawler", "spider", "url"]),
        "default_args": json.dumps(["-silent", "-jc"]),
        "inputs": json.dumps([
            {"name": "target", "type": "string", "required": True, "description": "Target URL to crawl"}
        ]),
        "outputs": json.dumps([
            {"name": "urls", "type": "file", "description": "Discovered URLs"}
        ]),
        "icon": "link",
        "author": "builtin",
    },
    {
        "name": "ffuf",
        "description": "Fast web fuzzer for directory and content discovery",
        "binary_path": "ffuf",
        "category": "bruteforce",
        "tags": json.dumps(["fuzzer", "directory", "bruteforce"]),
        "default_args": json.dumps(["-mc", "200,301,302,403"]),
        "inputs": json.dumps([
            {"name": "url", "type": "string", "required": True, "description": "Target URL with FUZZ keyword"},
            {"name": "wordlist", "type": "file", "required": True, "description": "Wordlist file"}
        ]),
        "outputs": json.dumps([
            {"name": "results", "type": "file", "description": "Fuzzing results"}
        ]),
        "icon": "search",
        "author": "builtin",
    },
    {
        "name": "amass",
        "description": "In-depth attack surface mapping and asset discovery",
        "binary_path": "amass",
        "category": "recon",
        "tags": json.dumps(["subdomain", "osint", "enumeration"]),
        "default_args": json.dumps(["enum", "-passive"]),
        "inputs": json.dumps([
            {"name": "domain", "type": "string", "required": True, "description": "Target domain"}
        ]),
        "outputs": json.dumps([
            {"name": "subdomains", "type": "file", "description": "Discovered subdomains"}
        ]),
        "icon": "globe",
        "author": "builtin",
    },
    {
        "name": "dnsx",
        "description": "Fast multi-purpose DNS toolkit for running DNS queries",
        "binary_path": "dnsx",
        "category": "dns",
        "tags": json.dumps(["dns", "resolve", "records"]),
        "default_args": json.dumps(["-silent", "-a", "-resp"]),
        "inputs": json.dumps([
            {"name": "domains", "type": "file", "required": True, "description": "List of domains to resolve"}
        ]),
        "outputs": json.dumps([
            {"name": "records", "type": "file", "description": "DNS resolution results"}
        ]),
        "icon": "server",
        "author": "builtin",
    },
    {
        "name": "gau",
        "description": "Fetch known URLs from various sources (AlienVault, Wayback, etc.)",
        "binary_path": "gau",
        "category": "recon",
        "tags": json.dumps(["url", "wayback", "osint"]),
        "default_args": json.dumps(["--threads", "5"]),
        "inputs": json.dumps([
            {"name": "domain", "type": "string", "required": True, "description": "Target domain"}
        ]),
        "outputs": json.dumps([
            {"name": "urls", "type": "file", "description": "Known URLs"}
        ]),
        "icon": "archive",
        "author": "builtin",
    },
    {
        "name": "naabu",
        "description": "Fast port scanner written in Go",
        "binary_path": "naabu",
        "category": "scanning",
        "tags": json.dumps(["port", "scan", "fast"]),
        "default_args": json.dumps(["-silent", "-top-ports", "1000"]),
        "inputs": json.dumps([
            {"name": "hosts", "type": "file", "required": True, "description": "List of hosts to scan"}
        ]),
        "outputs": json.dumps([
            {"name": "ports", "type": "file", "description": "Open ports"}
        ]),
        "icon": "radar",
        "author": "builtin",
    },
]


def seed():
    session = get_session()
    repo = ToolRepository(session)

    added = 0
    skipped = 0

    for tool_data in SEED_TOOLS:
        existing = repo.get_by_name(tool_data["name"])
        if existing:
            skipped += 1
            continue
        tool_data["is_active"] = True
        repo.create(tool_data)
        added += 1

    print(f"Seed complete: {added} tools added, {skipped} already existed.")


if __name__ == "__main__":
    seed()
