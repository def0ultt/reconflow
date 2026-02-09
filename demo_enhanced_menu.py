"""
Demo script to showcase ReconFlow's enhanced menu system
Run this to see all the beautiful visual components in action
"""

import time
from rich.console import Console
from cli.menu.components import (
    print_header, create_info_panel, create_success_panel,
    create_warning_panel, create_error_panel, create_menu_header,
    show_success, show_info, show_warning, show_error,
    show_loading, typewriter_effect, create_beautiful_table
)
from cli.menu.styles import get_theme_colors

console = Console()

def demo_header():
    """Demo the beautiful header"""
    print_header()
    time.sleep(2)

def demo_panels():
    """Demo various panel types"""
    console.clear()
    console.print("\n[bold cyan]═══ PANEL DEMONSTRATIONS ═══[/]\n")
    
    # Info panel
    info = create_info_panel(
        "This is an informational message with helpful context",
        "📌 Information"
    )
    console.print(info)
    time.sleep(1.5)
    
    # Success panel
    success = create_success_panel(
        "Operation completed successfully!",
        "✓ Success"
    )
    console.print(success)
    time.sleep(1.5)
    
    # Warning panel
    warning = create_warning_panel(
        "Please review before continuing",
        "⚠ Warning"
    )
    console.print(warning)
    time.sleep(1.5)
    
    # Error panel
    error = create_error_panel(
        "Critical error occurred during processing",
        "✗ Error"
    )
    console.print(error)
    time.sleep(1.5)
    
    # Menu header
    menu = create_menu_header(
        "🎯 MAIN MENU",
        "Select an option to continue"
    )
    console.print(menu)
    time.sleep(2)

def demo_animations():
    """Demo loading and message animations"""
    console.clear()
    console.print("\n[bold cyan]═══ ANIMATION DEMONSTRATIONS ═══[/]\n")
    
    # Loading animation
    show_loading("Initializing system", 1.5)
    
    # Success message
    show_success("Connection established")
    
    # Info message
    show_info("Scanning for vulnerabilities")
    
    # Warning message
    show_warning("Rate limit approaching")
    
    # Error message
    show_error("Connection timeout")
    
    # Typewriter effect
    console.print("\n[bold magenta]Typewriter Effect:[/]\n")
    typewriter_effect("Initializing ReconFlow reconnaissance suite...", delay=0.05, style="cyan")
    time.sleep(1)

def demo_tables():
    """Demo beautiful tables"""
    console.clear()
    console.print("\n[bold cyan]═══ TABLE DEMONSTRATIONS ═══[/]\n")
    
    # Project stats table
    headers = ["Metric", "Value", "Status"]
    rows = [
        ["Total Projects", "12", "✓ Active"],
        ["Modules Loaded", "45", "✓ Ready"],
        ["API Keys", "8/15", "⚠ Partial"],
        ["Last Scan", "2 hours ago", "✓ Success"]
    ]
    
    table = create_beautiful_table(
        "📊 ReconFlow Statistics",
        headers,
        rows,
        show_lines=True
    )
    console.print(table)
    time.sleep(3)

def demo_color_themes():
    """Demo different color themes"""
    console.clear()
    console.print("\n[bold cyan]═══ COLOR THEME SHOWCASE ═══[/]\n")
    
    themes = ['cyberpunk', 'matrix', 'professional']
    
    for theme_name in themes:
        colors = get_theme_colors(theme_name)
        
        console.print(f"\n[bold {colors['primary']}]◆ {theme_name.upper()} THEME[/]")
        console.print(f"[{colors['accent']}]━━━━━━━━━━━━━━━━━━━━━━━━[/]")
        console.print(f"  [{colors['primary']}]Primary:[/] {colors['primary']}")
        console.print(f"  [{colors['secondary']}]Secondary:[/] {colors['secondary']}")
        console.print(f"  [{colors['accent']}]Accent:[/] {colors['accent']}")
        console.print(f"  [{colors['success']}]Success:[/] {colors['success']}")
        console.print(f"  [{colors['warning']}]Warning:[/] {colors['warning']}")
        console.print(f"  [{colors['error']}]Error:[/] {colors['error']}")
        time.sleep(2)

def main():
    """Run all demos"""
    try:
        # 1. Header demo
        demo_header()
        
        # 2. Panels demo
        demo_panels()
        
        # 3. Animations demo
        demo_animations()
        
        # 4. Tables demo
        demo_tables()
        
        # 5. Color themes demo
        demo_color_themes()
        
        # Final message
        console.clear()
        print_header()
        
        console.print("\n[bold green]✓ Demo Complete![/]\n")
        console.print("[cyan]All visual components are working beautifully![/]")
        console.print("[dim]The enhanced menu system is ready to use.[/]\n")
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Demo interrupted by user[/]\n")

if __name__ == "__main__":
    main()
