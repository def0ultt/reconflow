#!/usr/bin/env python3

"""
CSP Analyzer - Enhanced Content Security Policy Analysis Tool
Analyzes CSP headers with deep security insights and multiple output formats
Author: Enhanced by Claude (Original by @gwendallecoguic)
"""

import sys
import json
import requests
import urllib.parse
from typing import Dict, List, Tuple
import tldextract

# Optional rich library for beautiful tables
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: 'rich' library not available. Install with: pip install rich")
    print("Falling back to basic output...\n")


class CSPAnalyzer:
    """Content Security Policy Analyzer with security assessment"""

    # CSP Directive Definitions
    DIRECTIVES = {
        # Fetch Directives
        "child-src": {
            "desc": "Defines valid sources for web workers and nested browsing contexts (frames/iframes)",
            "category": "fetch",
            "risk_level": "medium",
        },
        "connect-src": {
            "desc": "Restricts URLs for script interfaces (AJAX, WebSocket, EventSource, etc.)",
            "category": "fetch",
            "risk_level": "high",
        },
        "default-src": {
            "desc": "Fallback for other fetch directives - sets default policy",
            "category": "fetch",
            "risk_level": "critical",
        },
        "font-src": {
            "desc": "Valid sources for fonts loaded via @font-face",
            "category": "fetch",
            "risk_level": "low",
        },
        "frame-src": {
            "desc": "Valid sources for nested browsing contexts (frames/iframes)",
            "category": "fetch",
            "risk_level": "high",
        },
        "img-src": {
            "desc": "Valid sources for images and favicons",
            "category": "fetch",
            "risk_level": "medium",
        },
        "manifest-src": {
            "desc": "Valid sources for application manifest files",
            "category": "fetch",
            "risk_level": "low",
        },
        "media-src": {
            "desc": "Valid sources for audio, video, and track elements",
            "category": "fetch",
            "risk_level": "medium",
        },
        "object-src": {
            "desc": "Valid sources for object, embed, and applet elements",
            "category": "fetch",
            "risk_level": "high",
        },
        "prefetch-src": {
            "desc": "Valid sources to be prefetched or prerendered",
            "category": "fetch",
            "risk_level": "low",
        },
        "script-src": {
            "desc": "Valid sources for JavaScript and WebAssembly",
            "category": "fetch",
            "risk_level": "critical",
        },
        "script-src-elem": {
            "desc": "Valid sources for JavaScript script elements",
            "category": "fetch",
            "risk_level": "critical",
        },
        "script-src-attr": {
            "desc": "Valid sources for JavaScript inline event handlers",
            "category": "fetch",
            "risk_level": "critical",
        },
        "style-src": {
            "desc": "Valid sources for stylesheets",
            "category": "fetch",
            "risk_level": "medium",
        },
        "style-src-elem": {
            "desc": "Valid sources for stylesheet link elements",
            "category": "fetch",
            "risk_level": "medium",
        },
        "style-src-attr": {
            "desc": "Valid sources for inline styles",
            "category": "fetch",
            "risk_level": "medium",
        },
        "worker-src": {
            "desc": "Valid sources for Worker, SharedWorker, ServiceWorker scripts",
            "category": "fetch",
            "risk_level": "high",
        },
        # Document Directives
        "base-uri": {
            "desc": "Restricts URLs usable in document's base element",
            "category": "document",
            "risk_level": "medium",
        },
        "sandbox": {
            "desc": "Enables sandbox for requested resource (like iframe sandbox)",
            "category": "document",
            "risk_level": "high",
        },
        # Navigation Directives
        "form-action": {
            "desc": "Restricts URLs for form submissions",
            "category": "navigation",
            "risk_level": "high",
        },
        "frame-ancestors": {
            "desc": "Valid parents that may embed this page (anti-clickjacking)",
            "category": "navigation",
            "risk_level": "high",
        },
        "navigate-to": {
            "desc": "Restricts URLs for document navigation",
            "category": "navigation",
            "risk_level": "medium",
        },
        # Reporting Directives
        "report-uri": {
            "desc": "URI to send CSP violation reports (deprecated, use report-to)",
            "category": "reporting",
            "risk_level": "low",
        },
        "report-to": {
            "desc": "Group name for reporting API endpoints",
            "category": "reporting",
            "risk_level": "low",
        },
        # Other Directives
        "require-trusted-types-for": {
            "desc": "Requires Trusted Types for DOM XSS injection sinks",
            "category": "other",
            "risk_level": "high",
        },
        "trusted-types": {
            "desc": "Controls Trusted Types policy creation",
            "category": "other",
            "risk_level": "high",
        },
        "upgrade-insecure-requests": {
            "desc": "Instructs browsers to upgrade HTTP to HTTPS",
            "category": "other",
            "risk_level": "low",
        },
        "block-all-mixed-content": {
            "desc": "Prevents loading HTTP assets on HTTPS pages",
            "category": "other",
            "risk_level": "low",
        },
    }

    # Source Value Definitions
    SOURCE_VALUES = {
        "*": {
            "desc": "Wildcard - allows any URL except data:, blob:, filesystem:",
            "risk_level": "critical",
            "severity": 5,
        },
        "'none'": {
            "desc": "Prevents loading resources from any source",
            "risk_level": "safe",
            "severity": 0,
        },
        "'self'": {
            "desc": "Allows resources from same origin (scheme, host, port)",
            "risk_level": "safe",
            "severity": 1,
        },
        "data:": {
            "desc": "Allows data: scheme (Base64 encoded resources)",
            "risk_level": "warning",
            "severity": 3,
        },
        "blob:": {
            "desc": "Allows blob: scheme resources",
            "risk_level": "warning",
            "severity": 3,
        },
        "'unsafe-inline'": {
            "desc": "DANGEROUS: Allows inline scripts/styles/event handlers",
            "risk_level": "critical",
            "severity": 5,
        },
        "'unsafe-eval'": {
            "desc": "DANGEROUS: Allows eval() and similar dynamic code execution",
            "risk_level": "critical",
            "severity": 5,
        },
        "'unsafe-hashes'": {
            "desc": "WARNING: Allows inline event handlers matching hashes",
            "risk_level": "high",
            "severity": 4,
        },
        "'strict-dynamic'": {
            "desc": "Allows scripts loaded by trusted scripts (CSP3)",
            "risk_level": "low",
            "severity": 2,
        },
        "'report-sample'": {
            "desc": "Includes sample of violating code in reports",
            "risk_level": "safe",
            "severity": 0,
        },
        "https:": {
            "desc": "Allows any HTTPS resource",
            "risk_level": "warning",
            "severity": 3,
        },
        "http:": {
            "desc": "WARNING: Allows any HTTP resource (insecure)",
            "risk_level": "high",
            "severity": 4,
        },
    }

    def __init__(self, url: str, cookies: Dict[str, str] = None):
        self.url = url
        self.cookies = cookies or {}
        self.csp_header = None
        self.parsed_csp = {}
        self.security_score = 100
        self.findings = []
        self.console = Console() if RICH_AVAILABLE else None

    def fetch_csp(self) -> bool:
        """Fetch CSP header from URL"""
        try:
            if not self.url.startswith("http"):
                self.url = "https://" + self.url

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:105.0) Gecko/20100101 Firefox/105.0"
            }

            response = requests.get(
                self.url,
                cookies=self.cookies,
                allow_redirects=False,
                headers=headers,
                timeout=10,
            )

            if "Content-Security-Policy" in response.headers:
                self.csp_header = response.headers["Content-Security-Policy"]
                return True
            elif "Content-Security-Policy-Report-Only" in response.headers:
                self.csp_header = response.headers[
                    "Content-Security-Policy-Report-Only"
                ]
                self.findings.append(
                    {
                        "type": "info",
                        "message": "CSP is in Report-Only mode (not enforced)",
                    }
                )
                return True
            else:
                return False

        except Exception as e:
            print(f"Error fetching URL: {e}")
            return False

    def parse_csp(self):
        """Parse CSP header into directives"""
        if not self.csp_header:
            return

        directives = self.csp_header.split(";")

        for directive in directives:
            directive = directive.strip()
            if not directive:
                continue

            parts = directive.split()
            if not parts:
                continue

            directive_name = parts[0]
            sources = parts[1:] if len(parts) > 1 else []

            self.parsed_csp[directive_name] = sources

    def analyze_security(self):
        """Perform deep security analysis"""
        url_parts = urllib.parse.urlparse(self.url)
        tld_info = tldextract.extract(url_parts.netloc)

        # Check for missing critical directives
        self._check_missing_directives()

        # Analyze each directive
        for directive, sources in self.parsed_csp.items():
            if directive in self.DIRECTIVES:
                self._analyze_directive(directive, sources, tld_info)

        # Check for common misconfigurations
        self._check_common_issues()

    def _check_missing_directives(self):
        """Check for missing important directives"""
        critical_directives = [
            "default-src",
            "script-src",
            "object-src",
            "base-uri",
            "frame-ancestors",
        ]

        for directive in critical_directives:
            if directive not in self.parsed_csp:
                severity = (
                    "high" if directive in ["script-src", "object-src"] else "medium"
                )
                self.findings.append(
                    {
                        "type": "missing",
                        "severity": severity,
                        "directive": directive,
                        "message": f"Missing '{directive}' directive - {self.DIRECTIVES.get(directive, {}).get('desc', '')}",
                        "impact": self._get_missing_impact(directive),
                    }
                )

                if severity == "high":
                    self.security_score -= 15
                else:
                    self.security_score -= 5

    def _get_missing_impact(self, directive: str) -> str:
        """Get security impact of missing directive"""
        impacts = {
            "script-src": "Without script-src, attackers may inject malicious scripts (XSS)",
            "object-src": "Without object-src, attackers may embed malicious plugins",
            "base-uri": "Without base-uri, attackers may hijack relative URLs",
            "frame-ancestors": "Without frame-ancestors, site is vulnerable to clickjacking",
            "default-src": "Without default-src, no fallback policy exists",
        }
        return impacts.get(directive, "Reduced security posture")

    def _analyze_directive(self, directive: str, sources: List[str], tld_info):
        """Analyze individual directive and its sources"""
        if not sources:
            self.findings.append(
                {
                    "type": "warning",
                    "severity": "medium",
                    "directive": directive,
                    "message": f"Directive '{directive}' has no sources defined",
                }
            )
            return

        for source in sources:
            risk_info = self._assess_source_risk(source, directive, tld_info)
            if risk_info:
                self.findings.append(risk_info)
                self.security_score -= risk_info.get("score_impact", 0)

    def _assess_source_risk(self, source: str, directive: str, tld_info) -> Dict:
        """Assess risk level of a source value"""

        # Check known dangerous values
        if source in self.SOURCE_VALUES:
            source_info = self.SOURCE_VALUES[source]
            severity_level = source_info["severity"]

            if severity_level >= 4:
                return {
                    "type": "vulnerability",
                    "severity": "critical" if severity_level == 5 else "high",
                    "directive": directive,
                    "source": source,
                    "message": source_info["desc"],
                    "score_impact": severity_level * 3,
                    "remediation": self._get_remediation(source, directive),
                }
            elif severity_level == 3:
                return {
                    "type": "warning",
                    "severity": "medium",
                    "directive": directive,
                    "source": source,
                    "message": source_info["desc"],
                    "score_impact": 5,
                }

        # Check nonce/hash
        if source.startswith("'nonce-") or source.startswith("'sha"):
            return {
                "type": "good_practice",
                "severity": "info",
                "directive": directive,
                "source": source[:12] + "...",
                "message": "Using cryptographic nonce/hash - excellent security practice",
            }

        # Check domain-based sources
        if source.startswith("http") or ("." in source and not source.startswith("'")):
            return self._assess_domain_source(source, directive, tld_info)

        return None

    def _assess_domain_source(self, source: str, directive: str, tld_info) -> Dict:
        """Assess risk of domain-based source"""
        if not source.startswith("http"):
            source = "https://" + source

        try:
            parsed = urllib.parse.urlparse(source)
            source_tld = tldextract.extract(parsed.netloc)

            # Wildcard detection
            if "*" in parsed.netloc:
                return {
                    "type": "warning",
                    "severity": "medium",
                    "directive": directive,
                    "source": source,
                    "message": f"Wildcard domain - allows any subdomain under {source_tld.domain}.{source_tld.suffix}",
                    "score_impact": 8,
                }

            # Third-party domain
            if (
                source_tld.domain != tld_info.domain
                or source_tld.suffix != tld_info.suffix
            ):
                return {
                    "type": "info",
                    "severity": "info",
                    "directive": directive,
                    "source": source,
                    "message": f"Third-party domain: {parsed.netloc}",
                    "score_impact": 2,
                }

        except Exception:
            pass

        return None

    def _check_common_issues(self):
        """Check for common CSP misconfigurations"""

        # Check for unsafe-inline with script-src
        if "script-src" in self.parsed_csp:
            if "'unsafe-inline'" in self.parsed_csp["script-src"]:
                if not any(
                    s.startswith("'nonce-") or s.startswith("'sha")
                    for s in self.parsed_csp["script-src"]
                ):
                    self.findings.append(
                        {
                            "type": "vulnerability",
                            "severity": "critical",
                            "directive": "script-src",
                            "message": "CRITICAL: 'unsafe-inline' in script-src defeats XSS protection",
                            "impact": "Allows inline JavaScript execution - primary XSS vector",
                            "remediation": "Use nonces or hashes instead of 'unsafe-inline'",
                            "score_impact": 20,
                        }
                    )

        # Check for object-src wildcard
        if "object-src" in self.parsed_csp:
            if (
                "*" in self.parsed_csp["object-src"]
                or "data:" in self.parsed_csp["object-src"]
            ):
                self.findings.append(
                    {
                        "type": "vulnerability",
                        "severity": "high",
                        "directive": "object-src",
                        "message": "Dangerous object-src policy allows plugin-based attacks",
                        "remediation": "Set object-src to 'none' unless plugins are required",
                    }
                )

    def _get_remediation(self, source: str, directive: str) -> str:
        """Get remediation advice for risky sources"""
        remediations = {
            "'unsafe-inline'": f"For {directive}: Use CSP nonces or hashes instead of unsafe-inline. Generate unique nonce per request.",
            "'unsafe-eval'": f"For {directive}: Refactor code to avoid eval(), Function(), setTimeout(string), setInterval(string).",
            "*": f"For {directive}: Replace wildcard with specific trusted domains. Use 'self' when possible.",
            "data:": f"For {directive}: Avoid data: URIs. Host resources on same/trusted domains instead.",
        }
        return remediations.get(
            source, "Review and restrict source to minimum required domains"
        )

    def get_security_grade(self) -> str:
        """Calculate security grade based on score"""
        if self.security_score >= 90:
            return "A"
        elif self.security_score >= 80:
            return "B"
        elif self.security_score >= 70:
            return "C"
        elif self.security_score >= 60:
            return "D"
        else:
            return "F"

    def output_json(self) -> str:
        """Output analysis in JSON Lines format"""
        result = {
            "url": self.url,
            "csp_header": self.csp_header,
            "security_score": max(0, self.security_score),
            "security_grade": self.get_security_grade(),
            "directives": {},
            "findings": self.findings,
            "summary": {
                "total_directives": len(self.parsed_csp),
                "critical_issues": len(
                    [f for f in self.findings if f.get("severity") == "critical"]
                ),
                "high_issues": len(
                    [f for f in self.findings if f.get("severity") == "high"]
                ),
                "medium_issues": len(
                    [f for f in self.findings if f.get("severity") == "medium"]
                ),
                "info": len([f for f in self.findings if f.get("severity") == "info"]),
            },
        }

        # Add directive details
        for directive, sources in self.parsed_csp.items():
            result["directives"][directive] = {
                "sources": sources,
                "description": self.DIRECTIVES.get(directive, {}).get(
                    "desc", "Unknown directive"
                ),
                "category": self.DIRECTIVES.get(directive, {}).get(
                    "category", "unknown"
                ),
                "risk_level": self.DIRECTIVES.get(directive, {}).get(
                    "risk_level", "unknown"
                ),
            }

        return json.dumps(result, indent=2)

    def output_table(self):
        """Output analysis in rich table format"""
        if not RICH_AVAILABLE:
            self._output_basic()
            return

        # Header
        self.console.print()
        self.console.print(
            Panel.fit(
                f"[bold cyan]CSP Security Analysis[/bold cyan]\n"
                f"[white]URL:[/white] {self.url}\n"
                f"[white]Security Score:[/white] [bold]{max(0, self.security_score)}/100[/bold] "
                f"[bold]Grade: {self.get_security_grade()}[/bold]",
                border_style="cyan",
            )
        )

        # Directives Table
        if self.parsed_csp:
            self.console.print("\n[bold cyan]═══ CSP Directives ═══[/bold cyan]\n")

            table = Table(
                box=box.SIMPLE_HEAD,
                show_header=True,
                header_style="bold cyan",
                show_lines=False,
                padding=(0, 1),
            )
            table.add_column("Directive", style="cyan bold", width=22)
            table.add_column("Description", style="white", width=40, no_wrap=False)
            table.add_column("Sources", style="yellow", width=45, no_wrap=False)

            for directive, sources in self.parsed_csp.items():
                desc = self.DIRECTIVES.get(directive, {}).get(
                    "desc", "Unknown directive"
                )
                sources_text = ", ".join(sources) if sources else "[dim]none[/dim]"
                table.add_row(directive, desc, sources_text)

            self.console.print(table)

        # Findings Table
        if self.findings:
            self.console.print("\n[bold cyan]═══ Security Findings ═══[/bold cyan]\n")

            # Group by severity
            severity_order = [
                "critical",
                "high",
                "medium",
                "warning",
                "info",
                "missing",
                "good_practice",
            ]
            severity_colors = {
                "critical": "bold red",
                "high": "red",
                "medium": "yellow",
                "warning": "yellow",
                "info": "blue",
                "missing": "magenta",
                "good_practice": "green",
            }

            findings_table = Table(
                show_header=True,
                header_style="bold cyan",
                padding=(0, 1),
                show_lines=True,
            )
            findings_table.add_column("Severity", width=10, style="bold")
            findings_table.add_column("Directive", width=18)
            findings_table.add_column("Finding", width=45, no_wrap=False)
            findings_table.add_column("Impact", width=35, no_wrap=False)

            sorted_findings = sorted(
                self.findings,
                key=lambda x: severity_order.index(
                    x.get("severity", x.get("type", "info"))
                ),
            )

            for finding in sorted_findings:
                severity = finding.get("severity", finding.get("type", "info"))
                color = severity_colors.get(severity, "white")
                directive = finding.get("directive", "N/A")

                message = finding.get("message", "")
                impact = finding.get("impact", "-")

                # Add remediation to impact if exists
                if "remediation" in finding:
                    impact += (
                        f"\n[dim italic]Fix: {finding['remediation']}[/dim italic]"
                    )

                findings_table.add_row(
                    f"[{color}]{severity.upper()}[/{color}]",
                    f"[cyan]{directive}[/cyan]",
                    message,
                    f"[dim]{impact}[/dim]",
                )

            self.console.print(findings_table)

        # Summary
        self.console.print(f"\n[bold cyan]═══ Summary ═══[/bold cyan]\n")

        summary_table = Table(box=None, show_header=False, padding=(0, 2))
        summary_table.add_column("Label", style="white")
        summary_table.add_column("Value", style="bold")

        summary_table.add_row(
            "Total Directives:", f"[cyan]{len(self.parsed_csp)}[/cyan]"
        )
        summary_table.add_row(
            "Critical Issues:",
            f"[bold red]{len([f for f in self.findings if f.get('severity') == 'critical'])}[/bold red]",
        )
        summary_table.add_row(
            "High Issues:",
            f"[red]{len([f for f in self.findings if f.get('severity') == 'high'])}[/red]",
        )
        summary_table.add_row(
            "Medium Issues:",
            f"[yellow]{len([f for f in self.findings if f.get('severity') == 'medium'])}[/yellow]",
        )
        summary_table.add_row(
            "Info/Warnings:",
            f"[blue]{len([f for f in self.findings if f.get('severity') in ['info', 'warning']])}[/blue]",
        )

        self.console.print(summary_table)
        self.console.print()

    def _output_basic(self):
        """Basic output when rich is not available"""
        print("\n" + "=" * 80)
        print(f"CSP SECURITY ANALYSIS")
        print("=" * 80)
        print(f"URL: {self.url}")
        print(
            f"Security Score: {max(0, self.security_score)}/100 (Grade: {self.get_security_grade()})"
        )
        print("=" * 80)

        print("\n--- CSP DIRECTIVES ---\n")
        for directive, sources in self.parsed_csp.items():
            desc = self.DIRECTIVES.get(directive, {}).get("desc", "Unknown")
            print(f"{directive}")
            print(f"  Description: {desc}")
            print(f"  Sources: {', '.join(sources) if sources else 'none'}")
            print()

        if self.findings:
            print("\n--- SECURITY FINDINGS ---\n")
            for finding in self.findings:
                severity = finding.get("severity", finding.get("type", "info")).upper()
                print(f"[{severity}] {finding.get('directive', 'N/A')}")
                print(f"  {finding.get('message', '')}")
                if "remediation" in finding:
                    print(f"  Fix: {finding['remediation']}")
                print()


def print_banner():
    """Print tool banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   CSP Analyzer Pro - Content Security Policy Analysis Tool       ║
║   Deep Security Assessment & Vulnerability Detection             ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    print_banner()

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python3 csp_analyzer.py <url> [cookies] [-j|--json]")
        print("\nOptions:")
        print("  -j, --json    Output in JSON format")
        print("\nExamples:")
        print("  python3 csp_analyzer.py https://example.com")
        print("  python3 csp_analyzer.py example.com 'session=abc123'")
        print("  python3 csp_analyzer.py example.com -j")
        sys.exit(1)

    url = sys.argv[1]
    cookies = {}
    json_output = False

    # Parse additional arguments
    for arg in sys.argv[2:]:
        if arg in ["-j", "--json"]:
            json_output = True
        elif "=" in arg:
            # Parse cookies
            for cookie in arg.split(";"):
                cookie = cookie.strip()
                if "=" in cookie:
                    k, v = cookie.split("=", 1)
                    cookies[k.strip()] = v.strip()

    # Create analyzer
    analyzer = CSPAnalyzer(url, cookies)

    # Fetch and analyze
    print(f"Analyzing: {analyzer.url}")

    if not analyzer.fetch_csp():
        print(f"\n❌ Error: No Content-Security-Policy header found at {url}")
        print("   The site either doesn't use CSP or the request failed.")
        sys.exit(1)

    print("✓ CSP header found")
    print("✓ Parsing directives...")

    analyzer.parse_csp()

    print("✓ Analyzing security...\n")
    analyzer.analyze_security()

    # Output results
    if json_output:
        print(analyzer.output_json())
    else:
        analyzer.output_table()


if __name__ == "__main__":
    main()
