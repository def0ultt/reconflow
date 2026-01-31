from db.session import get_session, init_db, create_new_session
from db.models import Project
from sqlalchemy.orm.exc import DetachedInstanceError, UnmappedClassError
import sys

# Initialize DB
init_db()

# 1. Main Context simulates startup
main_session = get_session()
try:
    p = Project(name="test_project_fix", path="/tmp/test_project_fix")
    main_session.add(p)
    main_session.commit()
    print(f"Project created: {p.name} (Attached to session: {p in main_session})")
except Exception as e:
    print(f"Setup error (ignoring if just model issue): {e}")
    # continue if possible for the logic test, but likely fatal for this script
    
# 2. Simulate SessionManager.create_session (running on same thread, but using logic compliant with fix)
# NOW using create_new_session() simulating the fix
print("\n--- Simulating SessionManager with create_new_session() ---")
task_session = create_new_session()
print(f"Task session is Main session: {task_session is main_session}")

# Task session does some work
task_session.commit()
task_session.close() # <--- This should NOT affect main_session

print("Session closed.")

# 3. Simulate Shell accessing project
print("\n--- Verifying Main Session ---")
try:
    if main_session.is_active:
        print("Main session is still active.")
    else:
        print("Main session is INACTIVE (Failed).")

    # If logic is correct, p should still be attached or at least reloadable
    print(f"Accessing project name: {p.name}")
    print("[SUCCESS] Accessed project name without DetachedInstanceError!")
except DetachedInstanceError:
    print("\n[FAILURE] Caught DetachedInstanceError! The fix did not work.")
except Exception as e:
    print(f"\n[FAILURE] Caught unexpected exception: {e}")
