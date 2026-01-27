try:
    from cli import startup
    print("Successfully imported cli.startup")
except ImportError as e:
    print(f"ImportError: {e}")
    exit(1)
except SyntaxError as e:
    print(f"SyntaxError: {e}")
    exit(1)

print("Startup module syntax check passed.")
