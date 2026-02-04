from db.session import init_db, create_new_session, get_session
from db.models import SessionModel, Project
from core.context import Context
from cli.session_cmd import cmd_sessions
from rich.console import Console
from io import StringIO
import datetime

# Setup Mocks
init_db()

# Create dummy project
db = get_session()
p = db.query(Project).filter_by(name="session_test").first()
if not p:
    p = Project(name="session_test", path="/tmp/session_test")
    db.add(p)
    db.commit()

# Create STUCK sessions (simulate crash)
s1 = SessionModel(
    project_id=p.id, module="stuck_module_1", target="127.0.0.1", 
    status="running", start_time=datetime.datetime.utcnow()
)
db.add(s1)
db.commit()
stuck_id = s1.id

# Create Context
class MockSessionManager:
    def __init__(self):
        self.active_sessions = {}
    
    # We rely on the REAL stop_session method logic, but for testing we import it or duplicate relevant part?
    # Better to import the real one if possible, but it has dependencies. 
    # Let's import the REAL SessionManager since we patched it.
    
from core.session_manager import SessionManager
real_mgr = SessionManager()

ctx = Context()
ctx.current_project = p
ctx.session_manager = real_mgr

# Capture Output
capture = StringIO()
import cli.session_cmd
cli.session_cmd.console = Console(file=capture)

print(f"--- Listing Sessions (Expect 'running' for ID {stuck_id}) ---")
cmd_sessions(ctx, "") # List
output = capture.getvalue()
print(output)
if f"{stuck_id}" in output and "stuck_module_1" in output and "127.0.0.1" in output:
    print("[SUCCESS] List format looks correct.")
else:
    print("[FAILURE] List format incorrect.")

# Test Cleanup
capture.truncate(0)
capture.seek(0)
print(f"\n--- Stopping Stuck Session {stuck_id} ---")
# Manually invoke logic
cmd_sessions(ctx, f"--stop {stuck_id}")

# Verify DB status
db.refresh(s1)
print(f"Session {stuck_id} Status: {s1.status}")

if s1.status == "stopped":
    print("[SUCCESS] Stuck session stopped via DB update.")
else:
    print("[FAILURE] Stuck session NOT stopped.")
