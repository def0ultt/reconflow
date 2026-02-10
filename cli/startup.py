import questionary
import uuid
from rich.align import Align
import shutil
import atexit
from pathlib import Path
from core.context import Context
from rich.console import Console
from rich.table import Table
from cli.menu.components import (
    print_header, create_info_panel, create_menu_header,
    show_success, show_info, show_warning, show_error,
    show_loading, exit_animation, create_beautiful_table
)
from cli.menu.styles import CYBERPUNK_STYLE

console = Console()

def run_startup_flow(ctx: Context):
    """
    Interactive startup flow with beautiful visuals:
    - Load Existing Project
    - Create New Project
    - Temporary Project
    """
    # Display beautiful header
    print_header()
    
    # Show welcome panel
    info_panel = create_info_panel(
        "[dim]Navigate using arrow keys • Press Enter to select[/]\n"
        "[dim]Your all-in-one reconnaissance automation suite[/]",
        title="🔷 Welcome to ReconFlow"
    )
    console.print(info_panel)
    console.print()
    
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "📁 Projects",
                "🔧 Modules",
                "⚙️  Settings",
                "🚪 Exit"
            ],
            style=CYBERPUNK_STYLE,
            instruction="(Use arrow keys)"
        ).ask()
        
        if choice == "📁 Projects":
            # If project is loaded/created, return to continue to CLI
            if run_projects_menu(ctx):
                return  # Exit to CLI shell
            print_header()
            console.print(info_panel)
            console.print()
            
        elif choice == "🔧 Modules":
            run_modules_menu(ctx)
            print_header()
            console.print(info_panel)
            console.print()
            
        elif choice == "⚙️  Settings":
            run_settings_flow(ctx)
            print_header()
            console.print(info_panel)
            console.print()
            
        elif choice == "🚪 Exit":
            exit_animation()

def run_projects_menu(ctx: Context):
    """Enhanced projects menu - returns True if project is ready to use"""
    console.clear()
    
    # Projects menu header
    header = create_menu_header(
        "📁 PROJECT MANAGEMENT",
        "Create, load, and manage your reconnaissance projects"
    )
    console.print(header)
    console.print()
    
    while True:
        action = questionary.select(
            "Project Actions:",
            choices=[
                "📂 Load Project",
                "🆕 Create Project",
                "⚡ Create Temp Project",
                "📁 Change Project Path",
                "🗑️  Delete Project",
                "⬅️  Back to Main Menu"
            ],
            style=CYBERPUNK_STYLE,
            instruction="(Select an action)"
        ).ask()
        
        if action == "📂 Load Project":
            projects = ctx.project_repo.get_all()
            if not projects:
                show_warning("No projects found. Please create a new one.")
                continue
            
            project_names = [p.name for p in projects]
            p_name = questionary.select(
                "Select a project:",
                choices=project_names + ["⬅️ Cancel"],
                style=CYBERPUNK_STYLE
            ).ask()
            
            if p_name and p_name != "⬅️ Cancel":
                show_loading("Loading project")
                proj = ctx.project_repo.get_by_name(p_name)
                ctx.current_project = proj
                show_success(f"Loaded project: {proj.name}")
                return True  # Project loaded, return to CLI
            
        elif action == "🆕 Create Project":
            if _create_new_project(ctx):
                return True  # Project created, return to CLI
            
        elif action == "⚡ Create Temp Project":
            _create_temp_project(ctx)
            return True  # Temp project created, return to CLI
            
        elif action == "📁 Change Project Path":
            show_info("Change project path feature - Coming soon!")
            
        elif action == "🗑️  Delete Project":
            projects = ctx.project_repo.get_all()
            if not projects:
                show_warning("No projects available to delete.")
                continue
            
            project_names = [p.name for p in projects]
            p_name = questionary.select(
                "Select project to delete:",
                choices=project_names + ["⬅️  Cancel"],
                style=CYBERPUNK_STYLE
            ).ask()
            
            if p_name and p_name != "⬅️  Cancel":
                confirm = questionary.confirm(
                    f"Are you sure you want to delete '{p_name}'?",
                    default=False
                ).ask()
                
                if confirm:
                    show_loading("Deleting project")
                    try:
                        proj = ctx.project_repo.get_by_name(p_name)
                        ctx.project_repo.delete(proj.id)
                        show_success(f"Deleted project: {p_name}")
                    except Exception as e:
                        show_error(f"Failed to delete project: {str(e)}")
            
        elif action == "⬅️  Back to Main Menu":
            return False  # No project selected, back to menu

def run_modules_menu(ctx: Context):
    """Enhanced modules menu"""
    console.clear()
    
    # Modules menu header
    header = create_menu_header(
        "🔧 MODULE MANAGEMENT",
        "Import and manage reconnaissance modules"
    )
    console.print(header)
    console.print()
    
    while True:
        action = questionary.select(
            "Module Actions:",
            choices=[
                "📥 Import Module",
                "⬅️  Back to Main Menu"
            ],
            style=CYBERPUNK_STYLE,
            instruction="(Select an action)"
        ).ask()
        
        if action == "📥 Import Module":
            show_info("Module import feature - Coming soon!")
            
        elif action == "⬅️  Back to Main Menu":
            break

def run_settings_flow(ctx: Context):
    """Enhanced settings menu with beautiful visuals"""
    console.clear()
    
    # Settings header
    header = create_menu_header(
        "⚙️  CONFIGURATION",
        "Manage API keys and global variables"
    )
    console.print(header)
    console.print()
    
    while True:
        action = questionary.select(
            "Settings:",
            choices=[
                "🔑 API Keys",
                "🌐 Global Variables",
                "⬅️  Back to Main Menu"
            ],
            style=CYBERPUNK_STYLE,
            instruction="(Navigate and select)"
        ).ask()
        
        if action == "⬅️  Back to Main Menu":
            break
        elif action == "🔑 API Keys":
            _run_api_keys_flow(ctx)
        elif action == "🌐 Global Variables":
            _run_global_vars_flow(ctx)

def _run_api_keys_flow(ctx: Context):
    """Enhanced API keys configuration with beautiful interface"""
    # List of services
    services = [
        "360PassiveDNS", "ARIN", "AbuseIPDB", "Ahrefs", "AlienVault", "Alterations", "AnubisDB",
        "ArchiveIt", "Arquivo", "Ask", "AskDNS", "BGPTools", "BGPView", "Baidu", "BinaryEdge",
        "Bing", "Brute Forcing", "BufferOver", "BuiltWith", "C99", "CIRCL", "Censys", "CertSpotter",
        "Chaos", "Cloudflare", "CommonCrawl", "Crtsh", "DNSDB", "DNSDumpster", "DNSRepo", "DNSlytics",
        "Detectify", "Digitorus", "DuckDuckGo", "FOFA", "FacebookCT", "FullHunt", "Gists", "GitHub",
        "GitLab", "GoogleCT", "Greynoise", "HAW", "HackerOne", "HackerTarget", "Hunter", "HyperStat",
        "IPdata", "IPinfo", "IPv4Info", "IntelX", "LeakIX", "Maltiverse", "Mnemonic", "N45HT",
        "NetworksDB", "ONYPHE", "PKey", "PassiveTotal", "PentestTools", "Quake", "RADb", "RapidDNS",
        "Riddler", "Robtex", "Searchcode", "Searx", "SecurityTrails", "ShadowServer", "Shodan",
        "SiteDossier", "SonarSearch", "Spamhaus", "SpyOnWeb", "Spyse", "Sublist3rAPI", "TeamCymru",
        "ThreatBook", "ThreatCrowd", "ThreatMiner", "Twitter", "UKWebArchive", "URLScan", "Umbrella",
        "VirusTotal", "Wayback", "WhoisXMLAPI", "Yahoo", "ZETAlytics", "ZoomEye"
    ]
    
    # Get all configured keys
    configured_keys = {k.tool_name for k in ctx.settings_manager.list_api_keys()}
    
    choices = []
    for s in services:
        if s in configured_keys:
            choices.append(questionary.Choice(title=f"✓ {s}", value=s))
        else:
            choices.append(questionary.Choice(title=f"  {s}", value=s))
    
    choices.append(questionary.Choice(title="⬅️  Back", value="Back"))

    selected = questionary.select(
        "Select Service to Configure:",
        choices=choices,
        style=CYBERPUNK_STYLE,
        instruction="(✓ = configured)"
    ).ask()
    
    if selected == "Back" or not selected:
        return
        
    current_key = ctx.settings_manager.get_api_key(selected)
    
    if current_key:
        show_info(f"Current Key: {'*' * (len(current_key) - 4)}{current_key[-4:]}")
    else:
        show_info(f"No API key set for {selected}")
    
    new_key = questionary.password(
        f"Enter API Key for {selected} (Leave empty to keep current):",
        style=CYBERPUNK_STYLE
    ).ask()
    
    if new_key:
        show_loading("Saving API key")
        ctx.settings_manager.set_api_key(selected, new_key)
        show_success(f"API Key for {selected} saved securely!")

def _run_global_vars_flow(ctx: Context):
    # Get ALL variables
    vars_list = ctx.settings_manager.list_variables(include_all=True)
    
    # Pre-fetch project names for ID resolution
    projects = {p.id: p.name for p in ctx.project_repo.get_all()}
    
    global_vars = []
    local_vars = []
    
    for v in vars_list:
        if v.project_id:
            local_vars.append(v)
        else:
            global_vars.append(v)
            
    # Sort
    global_vars.sort(key=lambda x: x.key)
    local_vars.sort(key=lambda x: (projects.get(x.project_id, ""), x.key))

    console.print()
    
    # Global Table
    if global_vars:
        g_table = Table(title="Global Variables", show_header=True,show_lines=True)
        g_table.add_column("Variable", style="bold cyan")
        g_table.add_column("Value", style="bold red")
        
        for v in global_vars:
            g_table.add_row(v.key, v.value)
        centered_table = Align.center(g_table)
        console.print(centered_table)
    else:
        console.print("[dim]No Global Variables set.[/dim]")

    console.print()

    # Local Table
    if local_vars:
        l_table = Table(title="Local Variables", show_header=True,show_lines=True)
        l_table.add_column("Variable", style="bold cyan")
        l_table.add_column("Value", style="bold red")
        l_table.add_column("Project Scope", style="bold white")
        
        for v in local_vars:
            p_name = projects.get(v.project_id, f"ID:{v.project_id}")
            l_table.add_row(v.key, v.value, p_name)
        centered_table = Align.center(l_table)
        console.print(centered_table)
    else:
        console.print("[dim]No Local Variables set.[/dim]")
        
    console.print()
    
    action = questionary.select("Action:", choices=["Add/Edit Variable", "Delete Variable", "Back"]).ask()
    
    if action == "Add/Edit Variable":
        key = questionary.text("Variable Name (must start with $):").ask()
        if not key.startswith('$'):
            console.print("[red]Variable name must start with $[/red]")
            return
            
        value = questionary.text("Value:").ask()
        
        # Scope selection
        # "current_projet|(default_false|means work all projet"
        is_global = questionary.confirm("Apply globally (for all projects)?").ask()
        
        project_id = None
        if not is_global:
            # Select project
            projects = ctx.project_repo.get_all()
            if not projects:
                console.print("[red]No projects available to scope to.[/red]")
                return
            p_names = [p.name for p in projects]
            p_name = questionary.select("Select Project scope:", choices=p_names).ask()
            if p_name:
                p = ctx.project_repo.get_by_name(p_name)
                project_id = p.id
        
        ctx.settings_manager.set_variable(key, value, project_id)
        scope_str = "Globally" if not project_id else f"for Project {project_id}"
        console.print(f"[green]Variable {key} set {scope_str}.[/green]")

    elif action == "Delete Variable":
        # Prepare list for deletion
        # Format: "key (Global)" or "key (Project: Name)"
        choices = []
        
        for v in global_vars:
            choices.append(questionary.Choice(f"{v.key} (Global)", value=(v.key, None)))
            
        for v in local_vars:
            p_name = projects.get(v.project_id, f"ID:{v.project_id}")
            choices.append(questionary.Choice(f"{v.key} (Project: {p_name})", value=(v.key, v.project_id)))
            
        if not choices:
            console.print("[yellow]No variables to delete.[/yellow]")
            return

        choices.append(questionary.Choice("Cancel", value=None))

        selected = questionary.select("Select Variable to Delete:", choices=choices).ask()
        
        if selected:
            key, project_id = selected
            confirm = questionary.confirm(f"Are you sure you want to delete {key}?").ask()
            if confirm:
                if ctx.settings_manager.delete_variable(key, project_id):
                    console.print(f"[green]Variable {key} deleted.[/green]")
                else:
                    console.print(f"[red]Error deleting variable {key}.[/red]")

def _create_new_project(ctx: Context):
    """Enhanced project creation with beautiful interface - returns True on success"""
    name = questionary.text(
        "Enter project name:",
        style=CYBERPUNK_STYLE
    ).ask()
    
    if not name:
        show_error("Project name is required!")
        return False
        
    path = questionary.path(
        "Project Path (Leave empty for default):",
        default="",
        style=CYBERPUNK_STYLE
    ).ask()
    
    if not path:
        path = None
        
    try:
        show_loading("Creating project")
        proj = ctx.project_manager.create_project(name, path=path)
        ctx.current_project = proj
        show_success(f"Project '{proj.name}' created successfully!")
        return True
    except Exception as e:
        show_error(f"Failed to create project: {str(e)}")
        return False

def _create_temp_project(ctx: Context):
    """Enhanced temporary project creation with cleanup"""
    from datetime import datetime
    
    # Create timestamp-based temp project name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    temp_id = f"temp{timestamp}"
    
    show_info(f"Creating temporary project: {temp_id}")
    
    try:
        # Use /results directory
        temp_path = Path("results") / temp_id
        
        show_loading("Setting up temporary workspace")
        proj = ctx.project_repo.create({
            "name": temp_id,
            "path": str(temp_path.absolute()),
            "description": "Temporary Project"
        })
        temp_path.mkdir(parents=True, exist_ok=True)
        ctx.current_project = proj
        
        def cleanup():
            console.print(f"\n[yellow]🧹 Cleaning up temporary project {temp_id}...[/yellow]")
            try:
                if temp_path.exists():
                    shutil.rmtree(temp_path)
                from db.session import get_session
                session = get_session()
                session.query(type(proj)).filter_by(id=proj.id).delete()
                session.commit()
                console.print("[green]✓ Cleanup complete![/green]")
            except Exception as e:
                console.print(f"[red]✗ Cleanup failed: {e}[/red]")

        atexit.register(cleanup)
        ctx.is_temporary_project = True
        
        show_success(f"Temporary project created! Will auto-clean on exit.")
        
    except Exception as e:
        show_error(f"Failed to create temp project: {str(e)}")
        exit(1)
