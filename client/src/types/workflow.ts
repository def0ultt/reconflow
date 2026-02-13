// ─── Port Types ───────────────────────────────────────────────
export type PortType = 'string' | 'file' | 'boolean' | 'folder';

export interface WorkflowPort {
    id: string;
    name: string;
    type: PortType;
    required?: boolean;
    description?: string;
}

// ─── Input Node ───────────────────────────────────────────────
export type InputNodeKind = 'string' | 'file' | 'boolean' | 'folder';

export interface InputNodeData {
    kind: InputNodeKind;
    label: string;
    value: string | boolean | null;
    output: WorkflowPort;
}

// ─── Processor Node ───────────────────────────────────────────
export interface ProcessorNodeData {
    label: string;
    toolId: number;
    toolName: string;
    toolDescription: string | null;
    toolIcon: string | null;
    toolCategory: string | null;
    inputs: WorkflowPort[];
    outputs: WorkflowPort[];
    status: 'idle' | 'running' | 'completed' | 'failed';
}

// ─── Logs ─────────────────────────────────────────────────────
export type LogChannel = 'stdout' | 'stderr' | 'system';

export interface LogEntry {
    timestamp: number;
    channel: LogChannel;
    nodeId?: string;
    nodeName?: string;
    message: string;
}

// ─── Execution result per-node ────────────────────────────────
export interface NodeResult {
    nodeId: string;
    output: string;
}
