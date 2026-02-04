
import sys
import os
import json
from unittest.mock import MagicMock

sys.path.append(os.path.abspath('reconflow'))

from cli.commands import cmd_bcat
from core.context import Context

def setup_test_files():
    os.makedirs('results/projects/test/color-test', exist_ok=True)
    
    # Create test data with diverse value types
    data = [
        {
            "url": "https://example.com/admin",
            "status_code": 200,
            "content_type": "text/html; charset=UTF-8",
            "tech": "nginx:1.18.0",
            "title": "Admin Panel",
            "content_length": 1256
        },
        {
            "url": "http://api.example.com/v1/users",
            "status_code": 404,
            "content_type": "application/json",
            "tech": "FrontPage:6.0",
            "title": "Not Found",
            "content_length": 48
        }
    ]
    
    with open('results/projects/test/color-test/data.json', 'w') as f:
        json.dump(data, f)

def test_colorized_output():
    ctx = MagicMock(spec=Context)
    ctx.current_project = MagicMock()
    ctx.current_project.path = os.path.abspath('results/projects/test')

    print("\n" + "="*60)
    print("COLORIZED OUTPUT TEST")
    print("="*60)
    print("\nExpected colors:")
    print("  Keys: Blue (bold)")
    print("  URLs: Cyan")
    print("  Numbers (status_code, content_length): Yellow")
    print("  Content types: Magenta")
    print("  Tech versions: Green")
    print("  Default (title): White")
    print("\n" + "="*60 + "\n")
    
    # Display all records with colorization
    cmd_bcat(ctx, "color-test/data.json")
    
    print("\n" + "="*60)
    print("Test with field filtering:")
    print("="*60 + "\n")
    
    # Display with field filtering
    cmd_bcat(ctx, "color-test/data.json --include=url,status_code,tech")

if __name__ == "__main__":
    setup_test_files()
    test_colorized_output()
