#!/usr/bin/env python3

"""
Web Reconnaissance Tool
Combines WhatWeb, wafw00f, and Aquatone for comprehensive web fingerprinting
"""

import subprocess
import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# Check if rich is installed
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.layout import Layout
    from rich.syntax import Syntax
    from rich.layout import Layout
    from rich.syntax import Syntax
    from rich import box
    from rich.live import Live
    from rich.console import Group
except ImportError:
    print("❌ Error: 'rich' library not found!")
    print("📦 Install it with: pip install rich")
    sys.exit(1)

console = Console()


class WebRecon:
    def __init__(
        self,
        targets,
        aggression_level=1,
        screenshot=False,
        waf_detect=True,
        json_output=False,
    ):
        self.targets = targets
        self.aggression_level = aggression_level
        self.screenshot = screenshot
        self.waf_detect = waf_detect
        self.json_output = json_output
        self.results = []
        self.live_table = None

        # Create output directory
        self.output_dir = Path("recon_results") / datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def check_tools(self):
        """Check if required tools are installed"""
        tools = {"whatweb": "WhatWeb", "wafw00f": "wafw00f"}

        if self.screenshot:
            tools["aquatone"] = "Aquatone"

        missing_tools = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Checking required tools...", total=len(tools)
            )

            for cmd, name in tools.items():
                if subprocess.run(["which", cmd], capture_output=True).returncode != 0:
                    missing_tools.append(name)
                progress.advance(task)

        if missing_tools:
            console.print(f"[red]❌ Missing tools: {', '.join(missing_tools)}[/red]")
            console.print("\n[yellow]📦 Installation instructions:[/yellow]")
            if "WhatWeb" in missing_tools:
                console.print(
                    "   • WhatWeb: [cyan]sudo apt install whatweb[/cyan] or [cyan]gem install whatweb[/cyan]"
                )
            if "wafw00f" in missing_tools:
                console.print("   • wafw00f: [cyan]pip install wafw00f[/cyan]")
            if "Aquatone" in missing_tools:
                console.print(
                    "   • Aquatone: Download from [cyan]https://github.com/michenriksen/aquatone/releases[/cyan]"
                )
            return False

        console.print("[green]✅ All required tools are installed![/green]\n")
        return True

    def run_whatweb(self, target):
        """Run WhatWeb scan on target"""
        cmd = [
            "whatweb",
            target,
            "-a",
            str(self.aggression_level),
            "--color=never",
            "--log-json=/dev/stdout",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.stdout:
                # Parse JSON output
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            return data
                        except json.JSONDecodeError:
                            pass
            return None
        except subprocess.TimeoutExpired:
            return {"error": "Timeout"}
        except Exception as e:
            return {"error": str(e)}

    def run_wafw00f(self, target):
        """Run wafw00f WAF detection"""
        cmd = ["wafw00f", target, "-o", "/dev/stdout"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = result.stdout

            # Parse wafw00f output
            waf_detected = "No WAF detected"
            if "is behind" in output:
                for line in output.split("\n"):
                    if "is behind" in line:
                        waf_detected = line.split("is behind")[1].strip()
                        break

            return waf_detected
        except subprocess.TimeoutExpired:
            return "Timeout"
        except Exception as e:
            return f"Error: {str(e)}"

    def run_aquatone(self):
        """Run Aquatone for screenshots"""
        if not self.screenshot:
            return

        console.print("\n[cyan]📸 Taking screenshots with Aquatone...[/cyan]")

        # Prepare targets for aquatone
        targets_content = "\n".join(self.targets)

        try:
            # Create aquatone directory
            aquatone_dir = self.output_dir / "aquatone"
            aquatone_dir.mkdir(exist_ok=True)

            # Run aquatone
            process = subprocess.Popen(
                ["aquatone", "-out", str(aquatone_dir)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stdout, stderr = process.communicate(input=targets_content, timeout=300)

            console.print(f"[green]✅ Screenshots saved to: {aquatone_dir}[/green]")
            console.print(
                f"[green]   Open: {aquatone_dir / 'aquatone_report.html'}[/green]"
            )

        except subprocess.TimeoutExpired:
            console.print("[red]❌ Aquatone timeout[/red]")
        except FileNotFoundError:
            console.print("[red]❌ Aquatone not found in PATH[/red]")
        except Exception as e:
            console.print(f"[red]❌ Aquatone error: {e}[/red]")

    def display_banner(self):
        """Display tool banner"""
        banner = r"""
 ██╗    ██╗███████╗██████╗     ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██║    ██║██╔════╝██╔══██╗    ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ██║ █╗ ██║█████╗  ██████╔╝    ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██║███╗██║██╔══╝  ██╔══██╗    ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ╚███╔███╔╝███████╗██████╔╝    ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
  ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝

                [ WEB RECON MODULE ]
                     reconflow
"""
        console.print(
            Panel(
                f"[bold cyan]{banner}[/bold cyan]\n"
                f"[yellow]WhatWeb + WAF Detection + Screenshot Tool[/yellow]\n"
                f"[dim]Comprehensive Web Reconnaissance[/dim]",
                border_style="cyan",
                box=box.DOUBLE,
            )
        )

    def create_table(self):
        """Create the main results table"""
        table = Table(
            title="🌐 Web Reconnaissance Results",
            title_style="bold cyan",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan",
            box=box.ROUNDED,
            expand=True,
            show_lines=True
        )
        table.add_column("Target", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold", justify="center", width=12)
        table.add_column("Technologies", style="white")
        table.add_column("WAF", style="red")
        table.add_column("Screenshot", style="blue")
        return table

    def update_table(self, current_target=None, current_status=""):
        """Update the table with current results"""
        table = self.create_table()

        for res in self.results:
            target = res["target"]
            
            # Format WhatWeb Output
            whatweb = res.get("whatweb", {})
            tech_str = ""
            if whatweb and "plugins" in whatweb:
                plugins = whatweb.get("plugins", {})
                techs_list = []
                # Sort plugins by name for consistent output
                for name in sorted(plugins.keys()):
                    data = plugins[name]
                    values = []
                    
                    # Extract values from dict
                    if isinstance(data, dict):
                        # Priority keys to display
                        for key in ["string", "version", "account", "module", "os"]:
                            if key in data:
                                val = data[key]
                                if isinstance(val, list):
                                    values.extend([str(v) for v in val])
                                else:
                                    values.append(str(val))
                    # Extract values from list
                    elif isinstance(data, list):
                        for item in data:
                             if isinstance(item, dict):
                                  for key in ["string", "version", "account", "module", "os"]:
                                       if key in item:
                                            values.append(str(item[key]))
                             else:
                                  values.append(str(item))

                    if values:
                        # Format: Name[Value1,Value2]
                        # Join values with comma
                        v_str = ",".join(values)
                        techs_list.append(f"{name}[{v_str}]")
                    else:
                        techs_list.append(f"{name}")

                tech_str = ", ".join(techs_list)
            elif whatweb is None:
                 tech_str = "[red]Failed[/red]"
            else:
                 tech_str = "[dim]Scanning...[/dim]"

            # WAF
            waf = res.get("waf", "[dim]...[/dim]")
            if waf == "No WAF detected" or waf == "No WAF":
                 waf = "[green]None[/green]"
            
            # Screenshot (Placeholder for now as logic was separated)
            ss = "[dim]-[/dim]"
            if self.screenshot:
                 ss = "[yellow]Pending[/yellow]"
            
            table.add_row(
                target,
                "[green]Done[/green]",
                tech_str,
                str(waf),
                ss
            )

        # Add current target being scanned
        if current_target and current_target not in [r["target"] for r in self.results]:
             table.add_row(
                  current_target,
                  current_status,
                  "[dim]Scanning...[/dim]",
                  "[dim]...[/dim]",
                  "[dim]...[/dim]"
             )
        
        # Add pending targets
        scanned_targets = [r["target"] for r in self.results]
        if current_target:
             scanned_targets.append(current_target)
        
        for t in self.targets:
             if t not in scanned_targets:
                  table.add_row(
                       t,
                       "[dim]Pending[/dim]",
                       "",
                       "",
                       ""
                  )

        return table

    def scan(self):
        """Main scanning function"""

        # If JSON output mode, skip banner and just scan
        if self.json_output:
            self.json_scan()
            return

        self.display_banner()

        # Check tools
        if not self.check_tools():
            return
            
        # Initial Table
        with Live(self.update_table(), refresh_per_second=4, console=console) as live:
             
            for idx, target in enumerate(self.targets, 1):
                # Update status to scanning
                live.update(self.update_table(current_target=target, current_status="[bold yellow]⚡ Scanning[/bold yellow]"))

                # Run WhatWeb
                whatweb_data = self.run_whatweb(target)

                # Run wafw00f
                waf_info = "Skipped"
                if self.waf_detect:
                    waf_info = self.run_wafw00f(target)

                # Store results
                self.results.append(
                    {
                        "target": target,
                        "whatweb": whatweb_data,
                        "waf": waf_info,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                
                # Update table with result
                live.update(self.update_table(current_target=None))
            
            # Run Aquatone if enabled
            if self.screenshot:
                console.print("\n[cyan]📸 Taking screenshots with Aquatone...[/cyan]")
                self.run_aquatone()
            
            # Final Update
            live.update(self.update_table())

        # Save results to JSON
        self.save_results()

        # Display summary
        self.display_summary()

    def json_scan(self):
        """Scan in JSON output mode (JSONL format)"""
        # Check tools silently
        tools = {"whatweb": "WhatWeb"}
        if self.waf_detect:
            tools["wafw00f"] = "wafw00f"
        if self.screenshot:
            tools["aquatone"] = "Aquatone"

        missing_tools = []
        for cmd in tools.keys():
            if subprocess.run(["which", cmd], capture_output=True).returncode != 0:
                missing_tools.append(tools[cmd])

        if missing_tools:
            error_output = {
                "error": "Missing tools",
                "missing": missing_tools,
                "timestamp": datetime.now().isoformat(),
            }
            print(json.dumps(error_output))
            sys.exit(1)

        # Scan each target and output JSONL
        for target in self.targets:
            # Run WhatWeb
            whatweb_data = self.run_whatweb(target)

            # Run wafw00f
            waf_info = "Skipped"
            if self.waf_detect:
                waf_info = self.run_wafw00f(target)

            # Create result object
            result = {
                "target": target,
                "whatweb": whatweb_data,
                "waf": waf_info,
                "timestamp": datetime.now().isoformat(),
            }

            # Output as JSONL (one JSON object per line)
            print(json.dumps(result))
            sys.stdout.flush()  # Ensure immediate output

        # Run Aquatone if enabled
        if self.screenshot:
            self.run_aquatone()

    def save_results(self):
        """Save results to JSON file"""
        output_file = self.output_dir / "results.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        console.print(f"\n[green]💾 Results saved to: {output_file}[/green]")

    def display_summary(self):
        """Display scan summary"""
        console.print("\n")
        summary_panel = Panel(
            f"[bold green]✅ Scan Complete![/bold green]\n\n"
            f"[cyan]📊 Total Targets Scanned:[/cyan] {len(self.targets)}\n"
            f"[cyan]📁 Results Directory:[/cyan] {self.output_dir}\n"
            f"[cyan]⏰ Completed:[/cyan] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            title="[bold]Summary[/bold]",
            border_style="green",
            box=box.DOUBLE,
        )
        console.print(summary_panel)


def main():
    parser = argparse.ArgumentParser(
        description="Web Reconnaissance Tool - WhatWeb + WAF Detection + Screenshots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -t example.com -a 3                    # Single target, aggression level 3
  %(prog)s -l targets.txt -a 1 -ss                # Multiple targets with screenshots
  %(prog)s -t example.com -a 4 -ss --no-waf       # Disable WAF detection
        """,
    )

    # Target options
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("-t", "--target", help="Single target URL")
    target_group.add_argument(
        "-l", "--list", help="File containing list of targets (one per line)"
    )

    # Scan options
    parser.add_argument(
        "-a",
        "--aggression",
        type=int,
        choices=[1, 3, 4],
        default=1,
        help="WhatWeb aggression level (1=stealthy, 3=aggressive, 4=heavy) [default: 1]",
    )
    parser.add_argument(
        "-ss",
        "--screenshot",
        action="store_true",
        help="Take screenshots with Aquatone",
    )
    parser.add_argument("--no-waf", action="store_true", help="Disable WAF detection")
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Output results in JSONL format (one JSON object per line, no colors)",
    )

    args = parser.parse_args()

    # Prepare targets
    targets = []
    if args.target:
        # Single target
        target = args.target
        if not target.startswith("http"):
            target = "http://" + target
        targets = [target]
    else:
        # Multiple targets from file
        try:
            with open(args.list, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if not line.startswith("http"):
                            line = "http://" + line
                        targets.append(line)
        except FileNotFoundError:
            console.print(f"[red]❌ Error: File '{args.list}' not found![/red]")
            sys.exit(1)

    if not targets:
        console.print("[red]❌ No targets found![/red]")
        sys.exit(1)

    # Create and run scanner
    scanner = WebRecon(
        targets=targets,
        aggression_level=args.aggression,
        screenshot=args.screenshot,
        waf_detect=not args.no_waf,
        json_output=args.json,
    )

    scanner.scan()


if __name__ == "__main__":
    main()
