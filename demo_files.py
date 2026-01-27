from db.session import init_db, get_session
from db.repositories.project_repo import ProjectRepository
from core.file_manager import FileManager
import os
from pathlib import Path

def demo():
    print("--- 1. Initialize System ---")
    init_db()
    session = get_session()
    project_repo = ProjectRepository(session)
    file_manager = FileManager(project_repo)

    # Setup a demo project
    project_name = "demo_project"
    project_path = "/tmp/reconflow_demo"
    
    # Clean up previous run
    if os.path.exists(project_path):
        import shutil
        shutil.rmtree(project_path)
    
    print(f"Creating project '{project_name}' at '{project_path}'...")
    # Get or create
    project = project_repo.get_by_name(project_name)
    if not project:
        project = project_repo.create_project(project_name, project_path, "A demo project")

    print("\n--- 2. Simulate Nmap Scan (JSON output) ---")
    # Simulate Nmap outputting JSON
    nmap_json = '{"nmaprun": {"host": {"address": "192.168.1.1"}}}'
    print("Saving 'nmap_scan.json'...")
    file_manager.save_tool_output(project, "nmap", nmap_json, "nmap_scan.json")
    
    print("\n[NOTE] You should see that 'nmap_scan.txt' was also created automatically.")

    print("\n--- 3. Simulate Subfinder (Text output) ---")
    subfinder_txt = "sub1.example.com\nsub2.example.com"
    print("Saving 'subs.txt'...")
    file_manager.save_tool_output(project, "subfinder", subfinder_txt, "subs.txt")

    print("\n--- 4. List Files (Database Query) ---")
    # This simulates 'show files' command
    files = project_repo.get_files(project.id)
    print(f"{'TOOL':<12} | {'FILENAME':<20} | {'SIZE (Bytes)':<10}")
    print("-" * 50)
    for f in files:
        filename = os.path.basename(f.file_path)
        print(f"{f.tool_name:<12} | {filename:<20} | {f.file_size_bytes:<10}")

    print("\n--- 5. Read File Content (Simulates 'show [filename]') ---")
    target_file = "nmap_scan.txt"
    print(f"Reading content of '{target_file}':")
    content = file_manager.get_file_content(project.id, target_file)
    print("-" * 20)
    print(content)
    print("-" * 20)

if __name__ == "__main__":
    demo()
