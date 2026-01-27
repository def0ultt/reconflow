import questionary
import uuid
from rich.align import Align
import shutil
import atexit
from pathlib import Path
from core.context import Context
from rich.console import Console
from rich.table import Table

console = Console()

def run_startup_flow(ctx: Context):
    """
    Interactive startup flow:
    - Load Existing Project
    - Create New Project
    - Temporary Project
    """
    console.print("[bold cyan]Welcome to ReconFlow[/bold cyan]")
    
    choice = questionary.select(
        "What would you like to do?",
        choices=[
            "Load Existing Project",
            "Create New Project",
            "Create Temporary Project",
            "Settings",
            "Exit"
        ]
    ).ask()

    if choice == "Load Existing Project":
        projects = ctx.project_repo.get_all()
        if not projects:
            console.print("[yellow]No projects found. Creating a new one.[/yellow]")
            return _create_new_project(ctx)
        
        project_names = [p.name for p in projects]
        p_name = questionary.select(
            "Select a project:",
            choices=project_names
        ).ask()
        
        if p_name:
            proj = ctx.project_repo.get_by_name(p_name)
            ctx.current_project = proj
            console.print(f"[green]Loaded project: {proj.name}[/green]")
        else:
            exit(0)

    elif choice == "Create New Project":
        return _create_new_project(ctx)

    elif choice == "Create Temporary Project":
        return _create_temp_project(ctx)
    
    elif choice == "Settings":
        run_settings_flow(ctx)
        run_startup_flow(ctx) # Loop back to main menu

    elif choice == "Exit":
        exit(0)

def run_settings_flow(ctx: Context):
    while True:
        action = questionary.select(
            "Settings:",
            choices=["API Keys", "Global Variables", "Back"]
        ).ask()
        
        if action == "Back":
            break
        elif action == "API Keys":
            _run_api_keys_flow(ctx)
        elif action == "Global Variables":
            _run_global_vars_flow(ctx)

def _run_api_keys_flow(ctx: Context):
    # List of services from user request
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
    
    # Get all configured keys to mark them
    configured_keys = {k.tool_name for k in ctx.settings_manager.list_api_keys()}
    
    choices = []
    for s in services:
        if s in configured_keys:
            choices.append(questionary.Choice(title=f"[+] {s}", value=s))
        else:
            choices.append(questionary.Choice(title=f"    {s}", value=s))
    
    choices.append(questionary.Choice(title="    Back", value="Back"))

    selected = questionary.select("Select Service to Configure:", choices=choices).ask()
    if selected == "Back" or not selected:
        return
        
    current_key = ctx.settings_manager.get_api_key(selected)
    print(f"Current Key: {current_key or 'Not Set'}")
    
    new_key = questionary.text(f"Enter API Key for {selected} (Leave empty to keep current):").ask()
    if new_key:
        ctx.settings_manager.set_api_key(selected, new_key)
        console.print(f"[green]API Key for {selected} saved.[/green]")

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
    name = questionary.text("Enter project name:").ask()
    if not name:
        console.print("[red]Project name required.[/red]")
        exit(1)
        
    try:
        proj = ctx.project_manager.create_project(name)
        ctx.current_project = proj
        console.print(f"[green]Created project: {proj.name}[/green]")
    except Exception as e:
        console.print(f"[red]Error creating project: {e}[/red]")
        exit(1)

def _create_temp_project(ctx: Context):
    temp_id = f"temp_{uuid.uuid4().hex[:8]}"
    console.print(f"[yellow]Creating temporary project: {temp_id}[/yellow]")
    
    try:
        temp_path = Path("/tmp/reconflow_temps") / temp_id
        proj = ctx.project_repo.create({"name": temp_id, "path": str(temp_path), "description": "Temporary Project"})
        temp_path.mkdir(parents=True, exist_ok=True)
        ctx.current_project = proj
        
        def cleanup():
            console.print(f"\n[yellow]Cleaning up temporary project {temp_id}...[/yellow]")
            try:
                if temp_path.exists():
                    shutil.rmtree(temp_path)
                from db.session import get_session
                session = get_session()
                session.query(type(proj)).filter_by(id=proj.id).delete()
                session.commit()
                console.print("[green]Cleanup complete.[/green]")
            except Exception as e:
                console.print(f"[red]Cleanup failed: {e}[/red]")

        atexit.register(cleanup)
        ctx.is_temporary_project = True 
        
    except Exception as e:
        console.print(f"[red]Error creating temp project: {e}[/red]")
        exit(1)
