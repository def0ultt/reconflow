# How to Import Modules and Workflows

Here is a step-by-step example using the sample files provided in this directory.

## 1. Import a Module (Tool)
This takes an external YAML tool definition and copies it into your `modules/custom/` library.

**Command:**
```bash
reconflow> import module examples/demo_tool.yml
```

**Verify:**
```bash
reconflow> list
...
Modules:
...
custom/demo_tool
```

## 2. Import a Workflow
This takes an external YAML workflow and copies it into your `workflows/custom/` library. 

**Command:**
```bash
reconflow> import workflow examples/demo_workflow.yml
```

**Verify:**
```bash
reconflow> show workflow
...
workflow/custom/demo_flow
```

## 3. Use the Imported Items
Now you can use them just like standard tools.

**Use the Workflow:**
```bash
reconflow> use workflow/custom/demo_flow
reconflow> set target 8.8.8.8
reconflow> run
```

**Use the Module directly:**
```bash
reconflow> use custom/demo_tool
reconflow> run
```
