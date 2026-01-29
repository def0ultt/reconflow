# ReconFlow YAML Attribute Specification

This document outlines the standard format for defining **Modules** and **Workflows** in ReconFlow.

## 1. Global Requirement: The Type Declaration

Every YAML file **must** begin with the `type` key on the first line. This instructs the engine which parser to use.

```yaml
type: module    # Options: 'module' or 'workflow'
```

---

## 2. The `info` Block (Metadata)

Common to both Modules and Workflows, this section provides context and categorization.

| Key | Description | Example |
| :--- | :--- | :--- |
| **`id`** | Unique identifier/slug for the template. | `passive-recon-01` |
| **`name`** | Human-readable display name. | `Subdomain Enumeration` |
| **`author`** | The creator's handle/name. | `amir` |
| **`description`** | Detailed explanation of what the logic does. | `Runs subfinder and amass.` |

**Example:**
```yaml
info:
  id: sub-enumerator
  name: Subdomain Enumerator
  author: network_admin
  description: Passive subdomain enumeration module
```

---

## 3. Variable Management (`vars`)

Variables allow for dynamic input. You can use placeholders like `{{target}}` throughout the YAML file.

### Configuration
The `vars` block is a dictionary where each key is a variable name.

*   **`default`**: The value used if the user provides no input.
*   **`required`**: (Boolean) If `true`, the framework will error if this variable is missing/undefined.

**Example:**
```yaml
vars:
  target:
    default: "google.com"
    required: true
  threads:
    default: "10"
```

### CLI Overrides
Users can change these default values at runtime using the `set` command:
```bash
reconflow> set target facebook.com
reconflow> set threads 5
reconflow> run
```

---

## 4. Module Specification (`type: module`)

A **Module** defines the execution of specific CLI tools.

### The `steps` Array
Each step represents an atomic execution unit.

*   **`name`**: Logical ID for the step (used for referencing outputs later).
*   **`tool`**: The binary name (must be in system PATH) or absolute path (e.g., `/home/user/script.sh`).
*   **`args`**: Flags and parameters. Supports `{{variable}}` substitution.
*   **`capture`**: (Boolean) If `true`, saves `stdout` to memory for use in subsequent steps.
*   **`stdin`**: (Boolean) If `true`, pipes the output of the *previous* step into this one.
*   **`timeout`**: Time limit (e.g., `5m`, `1h`).
*   **`condition`**: usage logic check (e.g., `"{{threads}} > 5"`).

### Output Handling (`output`)
*   **`path`**: Location to save results (e.g., `{{output_dir}}/raw.txt`).
    *   *Note*: If a specific path is provided, the engine saves it there **AND** automatically creates a copy in the project's result folder to ensure data consistency.

**Example Module:**
```yaml
type: module
info:
  id: sub-enumerator

vars:
  target:
    required: true

steps:
  - name: run_tool
    tool: subfinder
    args: "-d {{target}} -silent"
    output:
      path: "{{output_dir}}/subdomains.txt"
```

---

## 5. Workflow Specification (`type: workflow`)

A **Workflow** orchestrates multiple modules into a single pipeline.

### The `workflow` Array
Defines the list of modules to execute.

*   **`name`**: Local identifier for this stage of the workflow.
*   **`module`**: The path or ID of the module to run.
*   **`depends_on`**: A list of stage names that must finish before this one starts.
*   **`inputs`**: Overrides the default variables for the referenced module.

**Example Workflow:**
```yaml
type: workflow
info:
  id: global-target-scanner

vars:
  target: 
    required: true
  output_base: "./results/{{target}}"

workflow:
  - name: recon_phase
    module: modules/recon/passive.yaml

  - name: port_scan
    module: modules/scan/nmap.yaml
    depends_on: [ "recon_phase" ]
    inputs:
      # Pass output from previous phase into this module
      scan_target: "{{recon_phase.found_ips}}"
```

---

## 6. Built-in Placeholders (Global Variables)

The engine automatically populates these variables at runtime. They are globally available.

1.  **`{{target}}`**: The main user-supplied global target (set via header/CLI once).
2.  **`{{output_name}}`**: The default output name (usually derived from the module name).save under projet folder
3.  **`{{date}}`**: The current date in `YYYY-MM-DD` format.
4. **`{{proxy}}`**: If the user wants to route traffic through Burp Suite or a SOCKS5 proxy, this variable can be passed to all tool flags. this work if user specifique proxy flag in tool and use {{proxy}} now user can set proxy 127.0.0.1:8080 and it will be applied to all tools that use {{proxy}}
5. **`{{threads}}`**: Global concurrency (e.g., 50). Used for tools like subfinder -t {{threads}}.this work when user specifique threads flag in tool and use {{threads}}
example args: -t {{threads}} now user can use set threads 50 and it will be applied to all tools that use {{threads}}
6. **Integration Keys (The "Secrets" Bus)**: 
{{github_token}}: For github-subdomains or trufflehog.
{{discord_webhook}} / {{slack_webhook}}: For final reporting modules.
{{shodan_key}}: For passive IP discovery.

tool load this token from settings under API KEY this maen you can set it in settings and tool will use it 
---

## 7. Logic & Operators

Standard operators available within `args` or `condition` fields:

*  **stdin**: Use `stdin` to tell the tool to listen for piped data instead of reading a file.
* **depends_on**: Use `depends_on` to specify the order of execution. This is useful when you have a module that depends on the output of another module.
---

## Comparison: Module vs. Workflow

| Feature | Module | Workflow |
| :--- | :--- | :--- |
| **Primary Goal** | Executing CLI tools | Chaining modules together |
| **Logic Unit** | `steps` | `workflow` (list of modules) |
| **Data Flow** | Piped `stdin/stdout` | Variable & Output Referencing |
| **Execution** | Atomic | Orchestrated (DAG) |
