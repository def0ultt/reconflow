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
