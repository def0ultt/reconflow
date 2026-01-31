"""
Built-in parsers for common reconnaissance tools
Each parser takes stdout string and returns List[Dict]
"""
import re
import json
from typing import List, Dict


def parse_subfinder(stdout: str) -> List[Dict]:
    """
    Parse subfinder output - one subdomain per line
    
    Example input:
        www.example.com
        api.example.com
    
    Returns:
        [{'subdomain': 'www.example.com'}, ...]
    """
    results = []
    for line in stdout.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            results.append({'subdomain': line})
    return results


def parse_httpx(stdout: str) -> List[Dict]:
    """
    Parse httpx JSON output (one JSON per line)
    
    Example input:
        {"url":"https://example.com","status_code":200}
        {"url":"https://api.example.com","status_code":404}
    
    Returns:
        [{'url': 'https://example.com', 'status_code': 200}, ...]
    """
    results = []
    for line in stdout.splitlines():
        line = line.strip()
        if line:
            try:
                data = json.loads(line)
                results.append(data)
            except json.JSONDecodeError:
                # Fallback: treat as URL
                results.append({'url': line})
    return results


def parse_nmap(stdout: str) -> List[Dict]:
    """
    Parse nmap output (simple text format)
    
    Example input:
        22/tcp   open  ssh     OpenSSH 8.2p1
        80/tcp   open  http    nginx 1.18.0
    
    Returns:
        [{'port': '22', 'protocol': 'tcp', 'state': 'open', 'service': 'ssh'}, ...]
    """
    results = []
    
    # Pattern: PORT/PROTOCOL  STATE  SERVICE  [VERSION]
    pattern = r'(\d+)/(tcp|udp)\s+(open|closed|filtered)\s+(\S+)(?:\s+(.+))?'
    
    for line in stdout.splitlines():
        line = line.strip()
        match = re.match(pattern, line)
        if match:
            result = {
                'port': match.group(1),
                'protocol': match.group(2),
                'state': match.group(3),
                'service': match.group(4)
            }
            if match.group(5):
                result['version'] = match.group(5).strip()
            results.append(result)
    
    return results


def parse_nuclei(stdout: str) -> List[Dict]:
    """
    Parse nuclei JSON output (one JSON per line)
    
    Example input:
        {"template-id":"cve-2021-1234","matched-at":"https://example.com"}
    
    Returns:
        [{'template-id': 'cve-2021-1234', 'matched-at': 'https://example.com'}, ...]
    """
    # Nuclei outputs JSON lines, same as httpx
    return parse_httpx(stdout)


def parse_naabu(stdout: str) -> List[Dict]:
    """
    Parse naabu output - host:port format
    
    Example input:
        192.168.1.1:22
        192.168.1.1:80
    
    Returns:
        [{'host': '192.168.1.1', 'port': '22'}, ...]
    """
    results = []
    for line in stdout.splitlines():
        line = line.strip()
        if ':' in line:
            parts = line.rsplit(':', 1)
            if len(parts) == 2:
                results.append({
                    'host': parts[0],
                    'port': parts[1]
                })
    return results


# Registry of all built-in parsers
BUILTIN_PARSERS = {
    'subfinder': parse_subfinder,
    'httpx': parse_httpx,
    'nmap': parse_nmap,
    'nuclei': parse_nuclei,
    'naabu': parse_naabu,
}
