import json
import os
import glob
import yaml
from utils.paths import get_project_root

class WorkflowManager:
    """
    Manage workflow definitions (creation, listing, execution).
    """
    def __init__(self, workflow_file="workflows.json"):
        self.workflow_file = get_project_root() / workflow_file
        self.workflows = {}
        self.load_workflows()
        self.load_yaml_workflows()

    def load_yaml_workflows(self, root_dir="workflows"):
        """Scans for .yml files in workflows/ directory."""
        path = get_project_root() / root_dir
        if not path.exists():
            return
            
        for filepath in glob.glob(str(path / "*.yml")) + glob.glob(str(path / "*.yaml")):
             try:
                 with open(filepath, 'r') as f:
                     data = yaml.safe_load(f)
                     if not data: continue
                     
                     # Use ID or Filename as key
                     # User example has 'id' in metadata
                     wf_id = data.get('metadata', {}).get('id')
                     if not wf_id:
                         wf_id = os.path.splitext(os.path.basename(filepath))[0]
                     
                     self.workflows[wf_id] = data
                     print(f"[+] Loaded YAML Workflow: {wf_id}")
             except Exception as e:
                 print(f"Error loading workflow {filepath}: {e}")

    def create_workflow(self, name: str, steps: list):
        self.workflows[name] = steps
        self.save_workflows()

    def get_workflow(self, name: str):
        return self.workflows.get(name)

    def list_workflows(self):
        return self.workflows

    def delete_workflow(self, name: str):
        if name in self.workflows:
            del self.workflows[name]
            self.save_workflows()
            return True
        return False

    def save_workflows(self):
        try:
            with open(self.workflow_file, 'w') as f:
                json.dump(self.workflows, f, indent=2)
        except Exception as e:
            print(f"Error saving workflows: {e}")

    def load_workflows(self):
        if os.path.exists(self.workflow_file):
            try:
                with open(self.workflow_file, 'r') as f:
                    self.workflows = json.load(f)
            except Exception as e:
                print(f"Error loading workflows: {e}")
                self.workflows = {}
