"""
Visual components for ReconFlow menu system
Beautiful panels, headers, animations, and UI elements
"""

import time
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich import box
from .styles import get_theme_colors

console = Console()

# Current theme (can be changed later)
CURRENT_THEME = 'cyberpunk'

def get_colors():
    """Get current theme colors"""
    return get_theme_colors(CURRENT_THEME)

# ═══════════════════════════════════════════════════════════════
# HEADERS & LOGOS
# ═══════════════════════════════════════════════════════════════

def print_header(clear=True):
    """Display beautiful ReconFlow header with gradient effect"""
    if clear:
        console.clear()
    
    colors = get_colors()
    
    # ASCII art logo for RECONFLOW
    logo = """
    ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗███████╗██╗      ██████╗ ██╗    ██╗
    ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║██╔════╝██║     ██╔═══██╗██║    ██║
    ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║█████╗  ██║     ██║   ██║██║ █╗ ██║
    ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║██╔══╝  ██║     ██║   ██║██║███╗██║
    ██║  ██║███████╗╚██████╗╚██████╔╝██║ ║████║██║     ███████╗╚██████╔╝╚███╔███╔╝
    ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ 
    """
    
    # Create styled text
    header_text = Text(logo)
    
    # Apply gradient-like effect by coloring different parts
    lines = logo.split('\n')
    styled_logo = Text()
    
    for i, line in enumerate(lines):
        if i == 0 or i == len(lines) - 1:
            continue  # Skip empty lines
        # Alternate colors for depth effect
        if i % 2 == 0:
            styled_logo.append(line + '\n', style=f"bold {colors['primary']}")
        else:
            styled_logo.append(line + '\n', style=f"bold {colors['secondary']}")
    
    subtitle = Text("Reconnaissance Automation Framework v2.0", style=f"italic {colors['accent']}")
    tagline = Text("\"Automate. Discover. Dominate.\"", style=f"dim {colors['highlight']}")
    
    console.print(Align.center(styled_logo))
    console.print(Align.center(subtitle))
    console.print(Align.center(tagline))
    console.print(Align.center("─" * 80, style=f"dim {colors['primary']}"))
    console.print()

# ═══════════════════════════════════════════════════════════════
# PANELS & CONTAINERS
# ═══════════════════════════════════════════════════════════════

def create_info_panel(message, title="ℹ Info"):
    """Create a beautiful info panel"""
    colors = get_colors()
    return Panel(
        f"[{colors['text']}]{message}[/]",
        title=f"[bold {colors['primary']}]{title}[/]",
        border_style=colors['primary'],
        box=box.ROUNDED,
        padding=(1, 2)
    )

def create_success_panel(message, title="✓ Success"):
    """Create a success panel"""
    colors = get_colors()
    return Panel(
        f"[{colors['success']}]{message}[/]",
        title=f"[bold {colors['success']}]{title}[/]",
        border_style=colors['success'],
        box=box.ROUNDED,
        padding=(1, 2)
    )

def create_warning_panel(message, title="⚠ Warning"):
    """Create a warning panel"""
    colors = get_colors()
    return Panel(
        f"[{colors['warning']}]{message}[/]",
        title=f"[bold {colors['warning']}]{title}[/]",
        border_style=colors['warning'],
        box=box.ROUNDED,
        padding=(1, 2)
    )

def create_error_panel(message, title="✗ Error"):
    """Create an error panel"""
    colors = get_colors()
    return Panel(
        f"[{colors['error']}]{message}[/]",
        title=f"[bold {colors['error']}]{title}[/]",
        border_style=colors['error'],
        box=box.DOUBLE,
        padding=(1, 2)
    )

def create_menu_header(title, subtitle=None):
    """Create a beautiful menu header panel"""
    colors = get_colors()
    
    content = f"[bold {colors['text']}]{title}[/]"
    if subtitle:
        content += f"\n[dim {colors['dim']}]{subtitle}[/]"
    
    return Panel(
        content,
        border_style=colors['accent'],
        box=box.DOUBLE,
        padding=(0, 2)
    )

# ═══════════════════════════════════════════════════════════════
# ANIMATIONS & EFFECTS
# ═══════════════════════════════════════════════════════════════

def typewriter_effect(text, delay=0.03, style=""):
    """Print text with typewriter effect"""
    for char in text:
        if style:
            console.print(f"[{style}]{char}[/]", end="")
        else:
            console.print(char, end="")
        sys.stdout.flush()
        time.sleep(delay)
    console.print()

def show_loading(message="Processing", duration=1.2):
    """Show loading animation"""
    colors = get_colors()
    with console.status(f"[bold {colors['primary']}]{message}...[/]", spinner="dots"):
        time.sleep(duration)

def show_success(message, delay=0.8):
    """Display success message with icon"""
    colors = get_colors()
    console.print(f"\n[{colors['success']}]✓[/] [bold {colors['success']}]{message}[/]\n")
    time.sleep(delay)

def show_info(message, delay=0.5):
    """Display info message with icon"""
    colors = get_colors()
    console.print(f"\n[{colors['primary']}]ℹ[/] [{colors['text']}]{message}[/]\n")
    time.sleep(delay)

def show_warning(message, delay=0.8):
    """Display warning message with icon"""
    colors = get_colors()
    console.print(f"\n[{colors['warning']}]⚠[/] [bold {colors['warning']}]{message}[/]\n")
    time.sleep(delay)

def show_error(message, delay=1.0):
    """Display error message with icon"""
    colors = get_colors()
    console.print(f"\n[{colors['error']}]✗[/] [bold {colors['error']}]{message}[/]\n")
    time.sleep(delay)

# ═══════════════════════════════════════════════════════════════
# EXIT ANIMATION
# ═══════════════════════════════════════════════════════════════

def exit_animation():
    """Beautiful exit animation"""
    console.clear()
    colors = get_colors()
    
    # Goodbye message
    goodbye_text = Text()
    goodbye_text.append("Thank you for using ", style="dim")
    goodbye_text.append("RECONFLOW", style=f"bold {colors['primary']}")
    goodbye_text.append("!", style="dim")
    
    exit_panel = Panel(
        Align.center(goodbye_text),
        title=f"[bold {colors['accent']}]👋 Goodbye[/]",
        border_style=colors['accent'],
        box=box.DOUBLE,
        padding=(1, 2)
    )
    
    console.print("\n")
    console.print(exit_panel)
    console.print(f"\n[dim italic {colors['dim']}]Happy Hacking...[/]\n")
    
    time.sleep(1.5)
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════
# TABLE UTILITIES
# ═══════════════════════════════════════════════════════════════

def create_beautiful_table(title, headers, rows, show_lines=True):
    """Create a beautifully styled table"""
    colors = get_colors()
    
    table = Table(
        title=title,
        show_header=True,
        header_style=f"bold {colors['primary']}",
        border_style=colors['accent'],
        box=box.ROUNDED,
        show_lines=show_lines
    )
    
    # Add columns
    for header in headers:
        table.add_column(header, style=f"{colors['text']}")
    
    # Add rows
    for row in rows:
        table.add_row(*row)
    
    return table
