# ReconFlow Unified Module Specification

A **Module** is the core execution unit in ReconFlow. 

> **Important**: Modules replace workflows. All workflow logic is now implemented using modules only.

A module can:
*   Execute CLI tools
*   Call other modules
*   Orchestrate complex execution chains
*   Combine tools and sub-modules in one pipeline

Modules can call other modules recursively.

---

## 1. Global Requirement
Every module file must begin with:

```yaml
type: module
```
This allows the engine to identify module files.

---

## 2. Metadata (`info`)
The `info` block describes the module.

| Field | Description | Example |
| :--- | :--- | :--- |
| `id` | Unique module identifier | `full-recon-suite` |
| `name` | Human-readable module name | `Full Passive Recon` |
| `author` | Creator or maintainer | `amir` |
| `description` | Module purpose | `Chains subfinder and port scanning` |

**Example:**
```yaml
info:
  id: full-recon-suite
  name: Full Passive Recon
  author: amir
  description: Chains subfinder with port scanning.
```

---

## 3. Variable Management (`vars`)
Variables define runtime inputs. Users can override them from CLI:
`set target example.com`

**Rules:**
*   `required: true` → engine stops if missing
*   `default:` → fallback value

**Example:**
```yaml
vars:
  target:
    required: true

  wordlist:
    default: "/usr/share/wordlists/dirb/common.txt"
```

---

## 4. Execution Engine (`steps`)
The `steps` array defines execution logic. A step can run a CLI tool **OR** call another module.

### Step Attributes
| Attribute | Required | Description |
| :--- | :--- | :--- |
| `name` | ✅ | Unique step name |
| `tool` | Optional | CLI binary to run |
| `module` | Optional | Module path or ID to execute |
| `depends_on` | Optional | List of step names required before execution |
| `args` | Optional | Tool flags or module parameters |
| `capture` | Optional | Save stdout for later reuse |
| `stdin` | Optional | Pipe output from dependency step |
| `parallel` | Optional | Explicitly allow parallel execution |

### Execution Rules
1.  **Parallel by Default**: Steps run in parallel unless `depends_on` is set.
2.  **Dependencies**: If `depends_on` is set, the step waits. A step cannot start until all dependencies finish.
3.  **Data Flow**: Tools that depend on previous output must use dependencies. "If Step B needs Step A output, they cannot run in parallel."

---

## 5. Example: Tool + Submodule Execution

```yaml
type: module

info:
  id: web-audit-plus
  name: Web Audit Plus

vars:
  target:
    required: true

steps:
  # Step 1 — Subdomain discovery
  - name: find_subs
    tool: subfinder
    args: "-d {{target}} -silent"
    capture: true

  # Step 2 — Port scanning using another module
  - name: port_scan
    module: modules/scanner/nmap.yaml
    depends_on: ["find_subs"]
    args:
      target_list: "{{find_subs.output}}"

  # Step 3 — Visual recon in parallel (runs with Step 1)
  - name: screenshot_target
    tool: gowitness
    args: "single {{target}}"
```

---

## 6. Global Placeholders
The engine injects these automatically:

| Placeholder | Description |
| :--- | :--- |
| `{{target}}` | Current target |
| `{{threads}}` | Global concurrency limit |
| `{{proxy}}` | Global proxy configuration |
| `{{step.output}}` | Captured output from a step |

**Example:**
`args: "-t {{threads}} --proxy {{proxy}}"`

---

## 7. Design Principles
*   **Modules replace workflows entirely.**
*   Modules may call other modules.
*   Dependency controls execution order.
*   Independent steps may run concurrently.
*   Output can be reused between steps.
