from typing import List, Dict
from sqlalchemy.orm import Session
from .base_repo import BaseRepository
from ..models.workflow import Workflow, WorkflowModule, WorkflowModuleTool
from ..models.tool import Tool

class WorkflowRepository(BaseRepository[Workflow]):
    def __init__(self, session: Session):
        super().__init__(Workflow, session)

    def get_by_name(self, name: str) -> Workflow | None:
        return self.session.query(Workflow).filter(Workflow.name == name).first()

    def create_full_workflow(self, name: str, description: str, modules_data: List[Dict]):
        """
        Create a workflow with its modules and tools in one go.
        modules_data structure:
        [
            {
                "name": "Recon",
                "order": 1,
                "tools": [
                    {"name": "subfinder", "arguments": "-d {target}", "order": 1},
                    {"name": "amass", "arguments": "-d {target}", "order": 2}
                ]
            }
        ]
        """
        workflow = Workflow(name=name, description=description)
        self.session.add(workflow)
        self.session.flush() # Get ID

        for mod_data in modules_data:
            module = WorkflowModule(
                workflow_id=workflow.id,
                name=mod_data["name"],
                order=mod_data.get("order", 0)
            )
            self.session.add(module)
            self.session.flush()

            for tool_data in mod_data.get("tools", []):
                # Find tool by name
                tool = self.session.query(Tool).filter(Tool.name == tool_data["name"]).first()
                if tool:
                    wmt = WorkflowModuleTool(
                        module_id=module.id,
                        tool_id=tool.id,
                        order=tool_data.get("order", 0),
                        arguments=tool_data.get("arguments", "")
                    )
                    self.session.add(wmt)
        
        self.session.commit()
        self.session.refresh(workflow)
        return workflow
