import React, { useState, useCallback, useRef, useMemo } from 'react';
import ReactFlow, {
    Controls,
    Background,
    applyEdgeChanges,
    applyNodeChanges,
    addEdge,
    Connection,
    Edge,
    Node,
    ReactFlowProvider,
    ConnectionLineType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ToolTemplate, InputNodeKind, InputNodeData, ProcessorNodeData, WorkflowPort } from '../types';
import { Play, Save } from 'lucide-react';
import clsx from 'clsx';
import { useSearchParams } from 'react-router-dom';

import InputNode from '../components/builder/nodes/InputNode';
import ProcessorNode from '../components/builder/nodes/ProcessorNode';
import InputsSidebar from '../components/builder/InputsSidebar';
import NodeInspector from '../components/builder/NodeInspector';
import LogsPanel from '../components/builder/LogsPanel';
import { useWorkflowEngine } from '../hooks/useWorkflowEngine';

// ─── Custom node type registry ────────────────────────────────
const nodeTypes = {
    inputNode: InputNode,
    processorNode: ProcessorNode,
};

let idCounter = 0;
const getId = () => `node_${Date.now()}_${idCounter++}`;

// ─── Main Component ──────────────────────────────────────────
const WorkflowBuilderContent = ({ projectIdProp }: { projectIdProp?: string }) => {
    const reactFlowWrapper = useRef<HTMLDivElement>(null);
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);
    const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

    const [searchParams] = useSearchParams();
    const projectId = projectIdProp || searchParams.get('project');

    const { logs, isRunning, execute, clearLogs } = useWorkflowEngine();

    // ─── ReactFlow handlers ───────────────────────────────────
    const onNodesChange = useCallback(
        (changes: any) => setNodes((nds) => applyNodeChanges(changes, nds)),
        []
    );
    const onEdgesChange = useCallback(
        (changes: any) => setEdges((eds) => applyEdgeChanges(changes, eds)),
        []
    );

    // Validate connection: only connect compatible port types
    const isValidConnection = useCallback((connection: Connection) => {
        if (!connection.sourceHandle || !connection.targetHandle) return false;
        // Extract type from handle id (format: "portname_type" or just allow all for now)
        // For simplicity, allow all connections — the mock engine handles data passing
        return true;
    }, []);

    const onConnect = useCallback(
        (params: Connection) => {
            const edge: Edge = {
                ...params,
                id: `edge_${params.source}_${params.target}_${Date.now()}`,
                animated: true,
                style: { stroke: '#a855f7', strokeWidth: 2 },
                type: 'smoothstep',
            } as Edge;
            setEdges((eds) => addEdge(edge, eds));
        },
        []
    );

    const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
        setSelectedNodeId(node.id);
    }, []);

    const onPaneClick = useCallback(() => {
        setSelectedNodeId(null);
    }, []);

    // ─── Drag & Drop ──────────────────────────────────────────
    const onDragOver = useCallback((event: React.DragEvent) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    const onDrop = useCallback(
        (event: React.DragEvent) => {
            event.preventDefault();
            const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
            if (!reactFlowInstance || !reactFlowBounds) return;

            const position = reactFlowInstance.project({
                x: event.clientX - reactFlowBounds.left,
                y: event.clientY - reactFlowBounds.top,
            });

            // Check if it's an input node drag
            const inputKind = event.dataTransfer.getData('application/input-kind') as InputNodeKind;
            if (inputKind) {
                const nodeId = getId();
                const portType = inputKind === 'boolean' ? 'boolean' as const
                    : inputKind === 'folder' ? 'folder' as const
                        : inputKind === 'file' ? 'file' as const
                            : 'string' as const;

                const newNode: Node<InputNodeData> = {
                    id: nodeId,
                    type: 'inputNode',
                    position,
                    data: {
                        kind: inputKind,
                        label: `${inputKind.charAt(0).toUpperCase() + inputKind.slice(1)} Input`,
                        value: inputKind === 'boolean' ? false : null,
                        output: {
                            id: `${nodeId}_output`,
                            name: 'value',
                            type: portType,
                        },
                    },
                };
                setNodes((nds) => nds.concat(newNode));
                return;
            }

            // Check if it's a tool drag
            const toolDataStr = event.dataTransfer.getData('application/reactflow');
            if (toolDataStr) {
                const tool = JSON.parse(toolDataStr) as ToolTemplate;
                const nodeId = getId();

                const inputs: WorkflowPort[] = (tool.inputs || []).map((inp, i) => ({
                    id: `${nodeId}_in_${i}`,
                    name: inp.name,
                    type: (inp.type as WorkflowPort['type']) || 'string',
                    required: inp.required,
                    description: inp.description,
                }));

                const outputs: WorkflowPort[] = (tool.outputs || []).map((out, i) => ({
                    id: `${nodeId}_out_${i}`,
                    name: out.name,
                    type: (out.type as WorkflowPort['type']) || 'file',
                    description: out.description,
                }));

                const newNode: Node<ProcessorNodeData> = {
                    id: nodeId,
                    type: 'processorNode',
                    position,
                    data: {
                        label: tool.name,
                        toolId: tool.id,
                        toolName: tool.name,
                        toolDescription: tool.description,
                        toolIcon: tool.icon,
                        toolCategory: tool.category,
                        inputs,
                        outputs,
                        status: 'idle',
                    },
                };
                setNodes((nds) => nds.concat(newNode));
            }
        },
        [reactFlowInstance]
    );

    // ─── Input sidebar drag handlers ──────────────────────────
    const onDragInputStart = useCallback((event: React.DragEvent, kind: InputNodeKind) => {
        event.dataTransfer.setData('application/input-kind', kind);
        event.dataTransfer.effectAllowed = 'move';
    }, []);

    const onDragToolStart = useCallback((event: React.DragEvent, tool: ToolTemplate) => {
        event.dataTransfer.setData('application/reactflow', JSON.stringify(tool));
        event.dataTransfer.effectAllowed = 'move';
    }, []);

    // ─── Node update (from inspector) ─────────────────────────
    const onUpdateNode = useCallback((id: string, partialData: Partial<InputNodeData | ProcessorNodeData>) => {
        setNodes((nds) =>
            nds.map((n) =>
                n.id === id ? { ...n, data: { ...n.data, ...partialData } } : n
            )
        );
    }, []);

    // ─── Execute ──────────────────────────────────────────────
    const handleExecute = useCallback(async () => {
        if (nodes.length === 0) return;
        // Reset all processor statuses
        setNodes((nds) =>
            nds.map((n) =>
                n.type === 'processorNode' ? { ...n, data: { ...n.data, status: 'idle' } } : n
            )
        );
        await execute(nodes, edges, setNodes);
    }, [nodes, edges, execute]);

    // ─── Selected node ────────────────────────────────────────
    const selectedNode = useMemo(
        () => nodes.find((n) => n.id === selectedNodeId) || null,
        [nodes, selectedNodeId]
    );

    return (
        <div className="workflow-builder">
            {/* Left: Inputs / Library sidebar */}
            <InputsSidebar
                onDragInputStart={onDragInputStart}
                onDragToolStart={onDragToolStart}
            />

            {/* Center: Canvas + toolbar + logs */}
            <div className="workflow-builder__center">
                {/* Toolbar */}
                <div className="workflow-builder__toolbar">
                    <div className="flex items-center space-x-2">
                        <div className="px-3 py-1 bg-primary/20 text-primary rounded-full text-xs font-medium border border-primary/20">
                            {projectId ? `Project #${projectId}` : 'Workflow Builder'}
                        </div>
                        <span className="text-[11px] text-gray-500">
                            {nodes.length} node{nodes.length !== 1 ? 's' : ''} · {edges.length} edge{edges.length !== 1 ? 's' : ''}
                        </span>
                    </div>

                    <div className="flex space-x-2">
                        <button className="workflow-builder__btn workflow-builder__btn--secondary">
                            <Save size={14} />
                            <span>Save</span>
                        </button>
                        <button
                            onClick={handleExecute}
                            disabled={isRunning || nodes.length === 0}
                            className={clsx(
                                'workflow-builder__btn',
                                isRunning || nodes.length === 0
                                    ? 'workflow-builder__btn--disabled'
                                    : 'workflow-builder__btn--primary'
                            )}
                        >
                            <Play size={14} fill="currentColor" />
                            <span>{isRunning ? 'Running...' : 'Execute'}</span>
                        </button>
                    </div>
                </div>

                {/* ReactFlow Canvas */}
                <div className="workflow-builder__canvas" ref={reactFlowWrapper}>
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        isValidConnection={isValidConnection}
                        onInit={setReactFlowInstance}
                        onDrop={onDrop}
                        onDragOver={onDragOver}
                        onNodeClick={onNodeClick}
                        onPaneClick={onPaneClick}
                        nodeTypes={nodeTypes}
                        connectionLineType={ConnectionLineType.SmoothStep}
                        connectionLineStyle={{ stroke: '#a855f7', strokeWidth: 2 }}
                        fitView
                        className="bg-[#09090b]"
                        defaultEdgeOptions={{
                            animated: true,
                            type: 'smoothstep',
                            style: { stroke: '#a855f7', strokeWidth: 2 },
                        }}
                    >
                        <Background color="#27272a" gap={20} size={1} />
                        <Controls className="bg-surface border-white/10 fill-white" />
                    </ReactFlow>
                </div>

                {/* Logs Panel */}
                <LogsPanel logs={logs} onClear={clearLogs} />
            </div>

            {/* Right: Node Inspector */}
            <NodeInspector
                selectedNode={selectedNode}
                onUpdateNode={onUpdateNode}
                onClose={() => setSelectedNodeId(null)}
            />
        </div>
    );
};

// ─── Wrapped with ReactFlowProvider ───────────────────────────
const Modules = (props: { projectIdProp?: string }) => (
    <ReactFlowProvider>
        <WorkflowBuilderContent {...props} />
    </ReactFlowProvider>
);

export default Modules;
