import { useState, useCallback } from 'react';
import { Node, Edge } from 'reactflow';
import { LogEntry, InputNodeData, ProcessorNodeData } from '../types';

// ─── Mock tool outputs ────────────────────────────────────────
const MOCK_OUTPUTS: Record<string, (input: string) => string> = {
    subfinder: (input: string) => {
        const domains = input.trim().split('\n').filter(Boolean);
        return domains
            .flatMap((d) => [
                `api.${d}`,
                `blog.${d}`,
                `app.${d}`,
                `mail.${d}`,
                `dev.${d}`,
            ])
            .join('\n');
    },
    httpx: (input: string) => {
        const lines = input.trim().split('\n').filter(Boolean);
        return lines
            .map((l) => `https://${l} [200] [${l.split('.')[0].toUpperCase()}]`)
            .join('\n');
    },
    nmap: (input: string) => {
        return `Starting Nmap scan on ${input.trim()}\nPORT     STATE SERVICE\n22/tcp   open  ssh\n80/tcp   open  http\n443/tcp  open  https\nNmap done: 1 IP address (1 host up)`;
    },
    nuclei: (input: string) => {
        const lines = input.trim().split('\n').filter(Boolean);
        return lines.slice(0, 3).map((l) =>
            `[CVE-2024-1234] [medium] ${l} [info-disclosure]`
        ).join('\n');
    },
    katana: (input: string) => {
        return input.trim().split('\n').filter(Boolean).flatMap((d) => [
            `https://${d}/login`,
            `https://${d}/api/v1`,
            `https://${d}/docs`,
        ]).join('\n');
    },
};

const defaultMock = (toolName: string, input: string) =>
    `[mock] ${toolName} processed ${input.trim().split('\n').length} line(s)`;

// ─── Topological sort ─────────────────────────────────────────
function topoSort(nodes: Node[], edges: Edge[]): Node[] {
    const inDegree = new Map<string, number>();
    const adj = new Map<string, string[]>();

    nodes.forEach((n) => {
        inDegree.set(n.id, 0);
        adj.set(n.id, []);
    });

    edges.forEach((e) => {
        adj.get(e.source)?.push(e.target);
        inDegree.set(e.target, (inDegree.get(e.target) || 0) + 1);
    });

    const queue: string[] = [];
    inDegree.forEach((deg, id) => { if (deg === 0) queue.push(id); });

    const sorted: string[] = [];
    while (queue.length > 0) {
        const id = queue.shift()!;
        sorted.push(id);
        for (const next of adj.get(id) || []) {
            const deg = (inDegree.get(next) || 1) - 1;
            inDegree.set(next, deg);
            if (deg === 0) queue.push(next);
        }
    }

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    return sorted.map((id) => nodeMap.get(id)!).filter(Boolean);
}

// ─── Hook ─────────────────────────────────────────────────────
export function useWorkflowEngine() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isRunning, setIsRunning] = useState(false);

    const addLog = useCallback((channel: LogEntry['channel'], message: string, nodeId?: string, nodeName?: string) => {
        setLogs((prev) => [...prev, { timestamp: Date.now(), channel, message, nodeId, nodeName }]);
    }, []);

    const clearLogs = useCallback(() => setLogs([]), []);

    const execute = useCallback(async (
        nodes: Node[],
        edges: Edge[],
        setNodes: React.Dispatch<React.SetStateAction<Node[]>>,
    ) => {
        setIsRunning(true);
        setLogs([]);

        const outputs = new Map<string, string>(); // nodeId → output text
        const sorted = topoSort(nodes, edges);

        addLog('system', `Starting workflow execution (${sorted.length} nodes)...`);

        // Helper to update a single node's status
        const updateStatus = (id: string, status: ProcessorNodeData['status']) => {
            setNodes((nds) =>
                nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, status } } : n))
            );
        };

        for (const node of sorted) {
            await new Promise((r) => setTimeout(r, 400)); // simulate delay

            if (node.type === 'inputNode') {
                const data = node.data as InputNodeData;
                const val = typeof data.value === 'boolean' ? String(data.value) : (data.value || '');
                outputs.set(node.id, val);
                addLog('system', `Input "${data.label}" ready`, node.id, data.label);
            } else if (node.type === 'processorNode') {
                const data = node.data as ProcessorNodeData;
                updateStatus(node.id, 'running');
                addLog('system', `Executing "${data.label}"...`, node.id, data.label);

                await new Promise((r) => setTimeout(r, 800)); // simulate work

                // Gather inputs from connected edges
                const incomingEdges = edges.filter((e) => e.target === node.id);
                const inputParts: string[] = [];
                for (const edge of incomingEdges) {
                    const srcOutput = outputs.get(edge.source);
                    if (srcOutput) inputParts.push(srcOutput);
                }
                const combinedInput = inputParts.join('\n');

                // Mock execute
                const toolName = data.toolName.toLowerCase();
                const mockFn = MOCK_OUTPUTS[toolName];
                const result = mockFn ? mockFn(combinedInput) : defaultMock(toolName, combinedInput);

                outputs.set(node.id, result);
                addLog('stdout', result, node.id, data.label);
                updateStatus(node.id, 'completed');
                addLog('system', `"${data.label}" completed`, node.id, data.label);
            }
        }

        await new Promise((r) => setTimeout(r, 300));
        addLog('system', 'Workflow execution finished.');
        setIsRunning(false);
    }, [addLog]);

    return { logs, isRunning, execute, clearLogs };
}
