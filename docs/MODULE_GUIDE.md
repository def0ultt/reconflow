# ReconFlow Module Creation Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Module Structure](#module-structure)
4. [Variables & Strict Scoping](#variables--strict-scoping)
5. [Steps & Execution](#steps--execution)
6. [Advanced Features](#advanced-features)
7. [Complete Examples](#complete-examples)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Introduction

A **Module** is the core execution unit in ReconFlow. Modules can:
- Execute CLI tools
- Call other modules recursively
- Run steps in parallel or sequentially
- Manage complex execution workflows

> **Note**: Modules have replaced workflows. All execution logic uses the unified module architecture.

---

## Quick Start

### Minimal Module Example

```yaml
type: module

info:
  id: hello-world
  name: Hello World
  description: Simple echo module
  author: your-name

vars:
  message:
    default: "Hello, ReconFlow!"

steps:
  - name: greet
    tool: echo
    args: "{{message}}"
```

### How to Use

1. Save as `modules/custom/hello.yml`
2. In ReconFlow CLI:
   ```
   use modules/custom/hello.yml
   run
   ```

---

## Module Structure

Every module has 4 required sections:

### 1. Type Declaration (Required)

```yaml
type: module
```

**Must be the first line** of every module file.

### 2. Info Block (Required)

```yaml
info:
  id: unique-module-id        # Unique identifier (kebab-case)
  name: Human Readable Name   # Display name
  description: What this module does
  author: your-name           # Creator
```

| Field | Required | Format | Example |
|-------|----------|--------|---------|
| `id` | ✅ | kebab-case | `subdomain-enum` |
| `name` | ✅ | Any string | `Subdomain Enumeration` |
| `description` | ✅ | Any string | `Discovers subdomains using multiple tools` |
| `author` | ✅ | Any string | `alice` |

### 3. Variables (Optional)

```yaml
vars:
  target:
    required: true
  
  threads:
    default: 10
  
  wordlist:
    default: "/usr/share/wordlists/common.txt"
```

### 4. Steps (Required)

```yaml
steps:
  - name: step1
    tool: echo
    args: "{{target}}"
```

---

## Variables & Strict Scoping

### Variable Rules (IMPORTANT)

⚠️ **Strict Scoping Enforced**:
- **ONLY** variables defined in `vars` can be used
- **NO** automatic global variables (no `{{target}}`, `{{proxy}}`, etc. unless you define them)
- Using undefined variables causes **hard errors**

### Variable Configuration

```yaml
vars:
  # Required variable (must be provided)
  target:
    required: true
  
  # Optional with default
  timeout:
    default: "30s"
  
  # Optional without default (can be null)
  custom_flag:
    required: false
```

### Variable Types

| Option | Description | Example |
|--------|-------------|---------|
| `required: true` | Must be provided before execution | User must set value |
| `default: value` | Fallback if not provided | Uses default if unset |
| `required: false` | Optional, can be null | May or may not be set |

### Using Variables

```yaml
vars:
  domain:
    required: true
  output_dir:
    default: "/tmp/results"

steps:
  - name: scan
    tool: nmap
    args: "-p- {{domain}} -oN {{output_dir}}/scan.txt"
```

### ❌ Common Mistakes

```yaml
# WRONG - using undefined variable
steps:
  - name: fail
    tool: echo
    args: "{{undefined_var}}"  # ERROR: undefined_var not in vars

# CORRECT - define first
vars:
  my_var:
    default: "value"

steps:
  - name: success
    tool: echo
    args: "{{my_var}}"  # OK: my_var is defined
```

---

## Steps & Execution

### Step Anatomy

```yaml
steps:
  - name: step_name          # Required: Unique identifier
    tool: command            # Either tool OR module (not both)
    args: "flags here"       # Arguments/parameters
    depends_on: []           # Dependencies (optional)
    parallel: true           # Allow parallel execution (default: true)
    path: "/custom/path"     # Custom tool path (optional)
    capture: true            # Save output (optional)
    stdin: true              # Use dependency output (optional)
    timeout: "5m"            # Execution timeout (optional)
    condition: "expr"        # Conditional execution (optional)
```

### Step Types

#### 1. Tool Execution

```yaml
- name: port_scan
  tool: nmap
  args: "-p 80,443 {{target}}"
```

#### 2. Module Execution

```yaml
- name: subdomain_scan
  module: modules/recon/subdomains.yml
  args: ""  # Can pass variables to submodule
```

### Execution Order

#### Parallel Execution (Default)

```yaml
steps:
  - name: step1
    tool: sleep
    args: "2"
  
  - name: step2
    tool: sleep
    args: "2"
  
  # Both run simultaneously (~2s total, not 4s)
```

#### Sequential Execution (Dependencies)

```yaml
steps:
  - name: discover
    tool: subfinder
    args: "-d {{domain}}"
    capture: true
  
  - name: scan
    tool: nmap
    args: "-iL {{discover.output}}"
    depends_on: [discover]  # Waits for discover to complete
```

#### Mixed Execution

```yaml
steps:
  # These 3 run in parallel
  - name: dns_enum
    tool: dnsenum
    args: "{{domain}}"
  
  - name: subdomain_enum
    tool: subfinder
    args: "-d {{domain}}"
    capture: true
  
  - name: screenshot
    tool: gowitness
    args: "{{domain}}"
  
  # This waits for subdomain_enum only
  - name: port_scan
    tool: nmap
    args: "-iL {{subdomain_enum.output}}"
    depends_on: [subdomain_enum]
```

### Accessing Step Output

```yaml
steps:
  - name: find_hosts
    tool: subfinder
    args: "-d {{domain}} -silent"
    capture: true
  
  - name: scan_hosts
    tool: nmap
    args: "-iL -"
    stdin: true
    depends_on: [find_hosts]
    # stdin receives output from find_hosts
```

**Access patterns**:
- `{{step_name.output}}` - Output file path
- `{{step_name.stdout}}` - Standard output
- `{{step_name.stderr}}` - Standard error

---

## Advanced Features

### 1. Custom Tool Paths

Override the system PATH for specific tools:

```yaml
vars:
  custom_tool_path:
    default: "/opt/custom-tools/scanner"

steps:
  - name: custom_scan
    tool: scanner
    path: "{{custom_tool_path}}"  # Uses this exact path
    args: "{{target}}"
```

**Use cases**:
- Custom compiled tools
- Specific tool versions
- Non-standard installation locations

### 2. Conditional Execution

```yaml
vars:
  enable_vuln_scan:
    default: "true"

steps:
  - name: vuln_scan
    tool: nuclei
    args: "-u {{target}}"
    condition: "{{enable_vuln_scan}} == 'true'"
```

### 3. Timeouts

```yaml
steps:
  - name: slow_scan
    tool: nmap
    args: "-p- {{target}}"
    timeout: "30m"  # Formats: 30s, 5m, 2h
```

### 4. Output Capture

```yaml
steps:
  - name: discover
    tool: subfinder
    args: "-d {{domain}}"
    capture: true
    output:
      filename: "subdomains.txt"  # Saves to project directory
```

### 5. Recursive Modules

```yaml
# main-recon.yml
steps:
  - name: passive_recon
    module: modules/recon/passive.yml
  
  - name: active_recon
    module: modules/recon/active.yml
    depends_on: [passive_recon]

# passive.yml can also call other modules
```

---

## New Features (v2.0)

### 1. Conditional Argument Syntax
Support for conditional flags based on variable presence.
Syntax: `{-l {{targets}} || -h {{target}} }`

- Checks if variables in the first option exist/truthy. If yes, uses it.
- Else checks second option.
- Strict validation: Fails if no option is valid.

```yaml
args: "{-l {{targets}} || -h {{target}} } -p 80"
```

### 2. Simplified Condition Syntax
Cleaner syntax for step conditions (no more verbose Jinja2).

- **Existence**: `condition: "{var}"` (Run if var exists)
- **Absence**: `condition: "{!var}"` (Run if var missing/empty)
- **Equality**: `condition: "{mode == 'fast'}"`
- **Inequality**: `condition: "{env != 'prod'}"`

### 3. Generic Parsers & Visualization
Built-in tools to visualize JSON/XML files as rich tables.

- `tool: json_parser` args: `-i file.json`
- `tool: xml_parser` args: `-i file.xml`

### 4. Multi-Dependency Piping
Pipe output from multiple dependencies into one tool (concatenated).

```yaml
  - name: consolidate
    tool: anew
    stdin: true
    depends_on: [tool1, tool2, tool3]
    # Input will be: tool1_out + \n + tool2_out + \n + tool3_out
```

---

## Complete Examples

### Example 1: Simple Port Scanner

```yaml
type: module

info:
  id: simple-port-scan
  name: Simple Port Scanner
  description: Scans common ports on a target
  author: alice

vars:
  target:
    required: true
  ports:
    default: "80,443,8080,8443"

steps:
  - name: scan
    tool: nmap
    args: "-p {{ports}} {{target}}"
```

### Example 2: Subdomain Discovery Pipeline

```yaml
type: module

info:
  id: subdomain-pipeline
  name: Subdomain Discovery Pipeline
  description: Multi-tool subdomain enumeration
  author: bob

vars:
  domain:
    required: true
  output_dir:
    default: "./results"

steps:
  # Run multiple tools in parallel
  - name: subfinder
    tool: subfinder
    args: "-d {{domain}} -silent"
    capture: true
    output:
      filename: "subfinder.txt"
  
  - name: assetfinder
    tool: assetfinder
    args: "{{domain}}"
    capture: true
    output:
      filename: "assetfinder.txt"
  
  # Combine results after both complete
  - name: combine
    tool: sort
    args: "-u {{output_dir}}/subfinder.txt {{output_dir}}/assetfinder.txt"
    depends_on: [subfinder, assetfinder]
    output:
      filename: "all_subdomains.txt"
```

### Example 3: Full Recon Workflow

```yaml
type: module

info:
  id: full-recon
  name: Full Reconnaissance
  description: Complete recon pipeline with parallel execution
  author: charlie

vars:
  target:
    required: true
  wordlist:
    default: "/usr/share/wordlists/common.txt"
  threads:
    default: 50

steps:
  # Phase 1: Parallel discovery
  - name: subdomain_enum
    tool: subfinder
    args: "-d {{target}} -t {{threads}}"
    capture: true
  
  - name: dns_enum
    tool: dnsenum
    args: "{{target}}"
  
  - name: whois_lookup
    tool: whois
    args: "{{target}}"
  
  # Phase 2: Port scanning (depends on subdomains)
  - name: port_scan
    tool: nmap
    args: "-iL {{subdomain_enum.output}} -p- -T4"
    depends_on: [subdomain_enum]
    timeout: "1h"
    capture: true
  
  # Phase 3: Directory brute force (parallel with port scan)
  - name: dir_brute
    tool: ffuf
    args: "-u https://{{target}}/FUZZ -w {{wordlist}}"
    depends_on: []  # Independent
  
  # Phase 4: Vulnerability scanning (after port scan)
  - name: vuln_scan
    tool: nuclei
    args: "-l {{port_scan.output}}"
    depends_on: [port_scan]
```

### Example 4: Using Custom Tool Path

```yaml
type: module

info:
  id: custom-scanner
  name: Custom Scanner
  description: Uses custom compiled tool
  author: dave

vars:
  target:
    required: true

steps:
  - name: custom_scan
    tool: my-scanner
    path: "/home/user/tools/my-scanner"
    args: "--target {{target}} --fast"
```

---

## Best Practices

### 1. Variable Naming

✅ **Good**:
```yaml
vars:
  target_domain:
    required: true
  scan_timeout:
    default: "30m"
```

❌ **Bad**:
```yaml
vars:
  t:  # Too short
    required: true
  ScanTimeout:  # Use snake_case
    default: "30m"
```

### 2. Step Naming

✅ **Good**:
```yaml
steps:
  - name: discover_subdomains
  - name: scan_ports
  - name: enumerate_services
```

❌ **Bad**:
```yaml
steps:
  - name: step1  # Not descriptive
  - name: DoScan  # Use snake_case
```

### 3. Dependency Management

✅ **Good** (Explicit dependencies):
```yaml
steps:
  - name: discover
    tool: subfinder
    args: "-d {{domain}}"
    capture: true
  
  - name: scan
    tool: nmap
    args: "-iL {{discover.output}}"
    depends_on: [discover]  # Clear dependency
```

❌ **Bad** (Implicit assumptions):
```yaml
steps:
  - name: scan
    tool: nmap
    args: "-iL {{discover.output}}"
    # Missing depends_on - may fail if discover hasn't run
```

### 4. Error Handling

✅ **Good** (Set timeouts):
```yaml
steps:
  - name: slow_operation
    tool: nmap
    args: "-p- {{target}}"
    timeout: "30m"  # Prevent hanging
```

### 5. Output Organization

✅ **Good**:
```yaml
vars:
  output_dir:
    default: "./results"

steps:
  - name: scan
    tool: nmap
    args: "{{target}}"
    output:
      filename: "nmap_scan.txt"
```

---

## Troubleshooting

### Error: "Variable 'X' is undefined"

**Cause**: Using a variable not defined in `vars`

**Solution**:
```yaml
# Add to vars section
vars:
  X:
    default: "value"
```

### Error: "Tool path not found"

**Cause**: Custom path doesn't exist

**Solution**:
```yaml
# Verify path exists or remove path field
steps:
  - name: scan
    tool: nmap
    path: "/usr/bin/nmap"  # Must exist
```

### Steps Not Running in Parallel

**Cause**: Implicit dependencies or `parallel: false`

**Solution**:
```yaml
# Ensure no depends_on and parallel: true (default)
steps:
  - name: step1
    tool: command1
    parallel: true  # Explicit
  
  - name: step2
    tool: command2
    parallel: true
```

### Module Not Loading

**Cause**: Missing `type: module` or invalid YAML

**Solution**:
```yaml
# First line must be:
type: module

# Validate YAML syntax
```

### Timeout Errors

**Cause**: Operation takes longer than timeout

**Solution**:
```yaml
steps:
  - name: long_scan
    tool: nmap
    args: "-p- {{target}}"
    timeout: "2h"  # Increase timeout
```

---

## Quick Reference

### Minimal Module Template

```yaml
type: module

info:
  id: my-module
  name: My Module
  description: Description here
  author: your-name

vars:
  target:
    required: true

steps:
  - name: main_step
    tool: echo
    args: "{{target}}"
```

### Common Patterns

**Sequential Pipeline**:
```yaml
steps:
  - name: step1
    tool: tool1
    capture: true
  
  - name: step2
    tool: tool2
    args: "{{step1.output}}"
    depends_on: [step1]
```

**Parallel + Merge**:
```yaml
steps:
  - name: task1
    tool: tool1
  
  - name: task2
    tool: tool2
  
  - name: merge
    tool: combine
    depends_on: [task1, task2]
```

**Conditional Execution**:
```yaml
steps:
  - name: optional_step
    tool: tool
    condition: "{{enable}} == 'true'"
```

---

## Summary

1. **Always** start with `type: module`
2. **Define all variables** in `vars` (strict scoping)
3. **Use dependencies** for execution order
4. **Leverage parallelism** for independent tasks
5. **Set timeouts** for long operations
6. **Capture output** for reuse in later steps
7. **Test incrementally** - start simple, add complexity

For more examples, see `examples/` directory or run `show modules` in ReconFlow CLI.
