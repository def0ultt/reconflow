from db.session import get_session, init_db
from db.models import Project
from sqlalchemy.orm.exc import DetachedInstanceError

# Initialize DB
init_db()

# 1. Main Context simulates startup
main_session = get_session()
p = Project(name="test_project", path="/tmp/test_project")
main_session.add(p)
main_session.commit()
print(f"Project created: {p.name} (Attached to session: {p in main_session})")

# 2. Simulate SessionManager.create_session (running on same thread)
# It gets a session (which will be main_session due to scoped_session)
task_session = get_session()
print(f"Task session is Main session: {task_session is main_session}")

# Task session does some work
task_session.commit()
task_session.close() # <--- THE PROBLEM

print("\nSession closed.")

# 3. Simulate Shell accessing project
try:
    print(f"Accessing project name: {p.name}")
except DetachedInstanceError:
    print("\n[SUCCESS] Caught expected DetachedInstanceError!")
except Exception as e:
    print(f"\n[FAILURE] Caught unexpected exception: {e}")
else:
    print("\n[FAILURE] Did not catch DetachedInstanceError (maybe eager loading?)")
