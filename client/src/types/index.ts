export interface ProjectStats {
    file_count: number;
    total_size_bytes: number;
    last_modified: string | null;
}

export interface Project {
    id: number;
    name: string;
    description: string | null;
    path: string;
    created_at: string;
    stats: ProjectStats | null;
}

export interface ProjectCreate {
    name: string;
    description?: string;
    path?: string;
    is_temp?: boolean;
}

export interface Module {
    id: string;
    name: string;
    description: string | null;
    author: string | null;
    version: string | null;
    tag: string | null;
    category: string | null;
    inputs: any[];
}

export interface Artifact {
    name: string;
    path: string;
    size: number;
    modified: number;
    type: string;
}

export interface WorkflowNode {
    id: string;
    type: string;
    data: {
        label: string;
        module: Module;
        status?: 'pending' | 'running' | 'completed' | 'failed';
    };
    position: { x: number; y: number };
}

export interface ToolIO {
    name: string;
    type: string;       // "string" | "file" | "list"
    required?: boolean;
    description?: string;
}

export interface ToolTemplate {
    id: number;
    name: string;
    description: string | null;
    binary_path: string | null;
    command_template: string | null;
    default_args: string[];
    category: string | null;
    tags: string[];
    inputs: ToolIO[];
    outputs: ToolIO[];
    icon: string | null;
    author: string | null;
    is_active: boolean;
}

export * from './workflow';
