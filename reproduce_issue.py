from rich.console import Console
from rich.syntax import Syntax

yaml_content = """steps:
  - name: katana_enum
    tool: katana
    args: "-u {{target}} -d {{depth}} -aff -xhr -fx -sb -H '{{header}}' -cos '.*\\\\/logout.*' -silent"
  - name: inject_payloads
    tool: /bin/bash
    args: "-c 'cat {{payloads}} | while read payload; do cat {{katana_enum.output}} | zap \\"$payload\\"; done'"
    depends_on: [katana_enum]
    timeout: "1h"
  - name: httpx_test
    tool: httpx
    args: " -fr -mr 'google.com' -location -H '{{header}}' -random-agent -threads {{threads}}"
    stdin: true
    depends_on: [inject_payloads]"""

console = Console(width=100) # Simulate a wide terminal
print("--- With code_width=76 ---")
syntax = Syntax(
    yaml_content, 
    "yaml", 
    theme="dracula",
    line_numbers=True,
    word_wrap=False,
    background_color="default",
    code_width=76
)
console.print(syntax)

print("\n--- Without code_width (Default) ---")
syntax_fixed = Syntax(
    yaml_content, 
    "yaml", 
    theme="dracula",
    line_numbers=True,
    word_wrap=False,
    background_color="default",
    # code_width=76  <-- Removed
)
console.print(syntax_fixed)
