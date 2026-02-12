import React, { useState, useEffect, useCallback, useRef } from 'react';
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
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import { Module } from '../types';
import { Play, Save, Search, GripVertical, Terminal, Rocket } from 'lucide-react';
import clsx from 'clsx';
import { useSearchParams } from 'react-router-dom';

const API_URL = 'http://localhost:8000/api';

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

let id = 0;
const getId = () => `dndnode_${id++}`;

const ModulesContent = ({ projectIdProp }: { projectIdProp?: string }) => {
    const reactFlowWrapper = useRef<HTMLDivElement>(null);
    const [nodes, setNodes] = useState<Node[]>(initialNodes);
    const [edges, setEdges] = useState<Edge[]>(initialEdges);
    const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

    // Modules State
    const [modules, setModules] = useState<Module[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loadingModules, setLoadingModules] = useState(true);

    // Execution State
    const [logs, setLogs] = useState<string[]>([]);
    const [executionId, setExecutionId] = useState<string | null>(null);
    const [isExecuting, setIsExecuting] = useState(false);
    const logsEndRef = useRef<HTMLDivElement>(null);

    // Project Context
    const [searchParams] = useSearchParams();
    const projectId = projectIdProp || searchParams.get('project');

    // Fetch Modules
    useEffect(() => {
        const fetchModules = async () => {
            try {
                const res = await axios.get(`${API_URL}/modules/`);
                setModules(res.data);
            } catch (err) {
                console.error("Failed to fetch modules", err);
            } finally {
                setLoadingModules(false);
            }
        };
        fetchModules();
    }, []);

    // WebSocket for Logs
    useEffect(() => {
        if (!executionId) return;

        const ws = new WebSocket(`ws://localhost:8000/api/ws/logs/${executionId}`);

        ws.onopen = () => {
            setLogs(prev => [...prev, `[System] Connected to log stream for ${executionId}`]);
        };

        ws.onmessage = (event) => {
            setLogs(prev => [...prev, event.data]);
        };

        ws.onclose = () => {
            setIsExecuting(false);
            setLogs(prev => [...prev, `[System] Connection closed.`]);
        };

        return () => {
            ws.close();
        };
    }, [executionId]);

    // Auto-scroll logs
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    const onNodesChange = useCallback(
        (changes: any) => setNodes((nds) => applyNodeChanges(changes, nds)),
        []
    );
    const onEdgesChange = useCallback(
        (changes: any) => setEdges((eds) => applyEdgeChanges(changes, eds)),
        []
    );
    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge(params, eds)),
        []
    );

    const onDragOver = useCallback((event: React.DragEvent) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    const onDrop = useCallback(
        (event: React.DragEvent) => {
            event.preventDefault();

            const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
            const moduleDataStr = event.dataTransfer.getData('application/reactflow');

            if (!moduleDataStr || !reactFlowInstance || !reactFlowBounds) return;

            const moduleData = JSON.parse(moduleDataStr) as Module;

            const position = reactFlowInstance.project({
                x: event.clientX - reactFlowBounds.left,
                y: event.clientY - reactFlowBounds.top,
            });

            const newNode: Node = {
                id: getId(),
                type: 'default', // Using default node for MVP, custom later
                position,
                data: { label: moduleData.name, module: moduleData },
                style: {
                    background: '#18181b',
                    color: '#fff',
                    border: '1px solid #7c3aed',
                    borderRadius: '8px',
                    padding: '10px',
                    width: 180
                }
            };

            setNodes((nds) => nds.concat(newNode));
        },
        [reactFlowInstance]
    );

    const onDragStart = (event: React.DragEvent, module: Module) => {
        event.dataTransfer.setData('application/reactflow', JSON.stringify(module));
        event.dataTransfer.effectAllowed = 'move';
    };

    const handleRun = async () => {
        if (nodes.length === 0) {
            alert("Canvas is empty. Add modules first.");
            return;
        }

        setIsExecuting(true);
        setLogs([]);

        // Convert Graph to Linear Workflow (Naive Top-Sort or just Sequence based on edges)
        // For MVP, if we have 1 node, run it. If multiple connected, run in sequence.
        // We need to construct the ModuleSchema expected by backend.

        // Simulating a linear sequence from connected nodes for now.
        // Find distinct nodes.

        // NOTE: The backend expects a YAML-like structure with 'steps'.
        // We'll map each node to a step.

        const steps = nodes.map(node => ({
            name: node.data.label,
            tool: node.data.module.id, // Or 'module' depending on definition
            // args: ... 
        }));

        const workflowPayload = {
            name: "Visual Workflow",
            description: "Generated from Visual Editor",
            steps: steps
        };

        try {
            const res = await axios.post(`${API_URL}/run`, {
                workflow: workflowPayload,
                variables: {
                    target: "example.com" // TODO: Ask user for variables
                }
            });
            setExecutionId(res.data.execution_id);
        } catch (err: any) {
            console.error(err);
            alert("Failed to start workflow: " + (err.response?.data?.detail || err.message));
            setIsExecuting(false);
        }
    };

    const filteredModules = modules.filter(m =>
        m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (m.description && m.description.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
        <div className="h-full w-full flex overflow-hidden">
            {/* Sidebar Tools */}
            <div className="w-80 bg-surface border-r border-white/10 flex flex-col h-full z-20 shadow-xl">
                <div className="p-4 border-b border-white/10">
                    <h2 className="text-lg font-bold flex items-center mb-4">
                        <Terminal className="mr-2 text-primary" size={20} />
                        Modules Library
                    </h2>
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <input
                            type="text"
                            placeholder="Search tools..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-black/20 border border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm focus:border-primary outline-none transition-colors"
                        />
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-3 space-y-2">
                    {loadingModules ? (
                        <div className="text-center py-8 text-gray-500 text-sm">Loading modules...</div>
                    ) : filteredModules.length > 0 ? (
                        filteredModules.map((mod) => (
                            <div
                                key={mod.id}
                                onDragStart={(event) => onDragStart(event, mod)}
                                draggable
                                className="group bg-background/50 hover:bg-white/5 border border-transparent hover:border-primary/50 p-3 rounded-lg cursor-grab active:cursor-grabbing transition-all flex items-start space-x-3"
                            >
                                <div className="mt-1 p-1.5 bg-primary/10 rounded text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                                    <Rocket size={14} />
                                </div>
                                <div>
                                    <div className="font-medium text-sm text-gray-200 group-hover:text-white">{mod.name}</div>
                                    <div className="text-xs text-gray-500 line-clamp-2 mt-0.5">{mod.description || 'No description'}</div>
                                </div>
                                <GripVertical className="ml-auto text-gray-600 opacity-0 group-hover:opacity-100" size={16} />
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-8 text-gray-500 text-sm">No modules found</div>
                    )}
                </div>
            </div>

            {/* Main Canvas Area */}
            <div className="flex-1 flex flex-col h-full relative">
                {/* Toolbar */}
                <div className="h-16 border-b border-white/10 bg-surface/50 backdrop-blur-md flex items-center justify-between px-6 z-10">
                    <div className="flex items-center space-x-2">
                        <div className="px-3 py-1 bg-primary/20 text-primary rounded-full text-xs font-medium border border-primary/20">
                            {projectId ? `Project ID: ${projectId}` : 'No Project Selected'}
                        </div>
                    </div>

                    <div className="flex space-x-3">
                        <button className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-surface border border-white/10 hover:bg-white/5 text-gray-300 transition-colors">
                            <Save size={18} />
                            <span>Save</span>
                        </button>
                        <button
                            onClick={handleRun}
                            disabled={isExecuting}
                            className={clsx(
                                "flex items-center space-x-2 px-4 py-2 rounded-lg text-white font-medium transition-all shadow-lg",
                                isExecuting ? "bg-gray-600 cursor-not-allowed" : "bg-primary hover:bg-primary/90 shadow-primary/25"
                            )}
                        >
                            <Play size={18} fill="currentColor" />
                            <span>{isExecuting ? 'Running...' : 'Run Workflow'}</span>
                        </button>
                    </div>
                </div>

                {/* Flow Canvas */}
                <div className="flex-1 h-full w-full bg-[#09090b]" ref={reactFlowWrapper}>
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        onInit={setReactFlowInstance}
                        onDrop={onDrop}
                        onDragOver={onDragOver}
                        fitView
                        className="bg-[#09090b]"
                    >
                        <Background color="#27272a" gap={20} size={1} />
                        <Controls className="bg-surface border-white/10 fill-white" />
                    </ReactFlow>
                </div>

                {/* Logs Panel (Bottom Sheet) */}
                <div className={clsx(
                    "absolute bottom-0 left-0 right-0 bg-[#0c0c0e] border-t border-white/10 transition-all duration-300 flex flex-col shadow-2xl z-20",
                    logs.length > 0 || isExecuting ? "h-64" : "h-0 border-none"
                )}>
                    <div className="flex items-center justify-between px-4 py-2 bg-surface border-b border-white/5">
                        <span className="text-xs font-mono text-gray-400 uppercase tracking-wider">Execution Logs</span>
                        <div className="flex space-x-2">
                            <button onClick={() => setLogs([])} className="text-xs text-gray-500 hover:text-white">Clear</button>
                            <button onClick={() => setExecutionId(null)} className="text-xs text-gray-500 hover:text-white">Close</button>
                        </div>
                    </div>
                    <div className="flex-1 overflow-auto p-4 font-mono text-sm space-y-1">
                        {logs.map((log, i) => (
                            <div key={i} className="text-gray-300 break-all border-l-2 border-primary/30 pl-2">
                                {log}
                            </div>
                        ))}
                        <div ref={logsEndRef} />
                    </div>
                </div>
            </div>
        </div>
    );
};

const Modules = (props: { projectIdProp?: string }) => (
    <ReactFlowProvider>
        <ModulesContent {...props} />
    </ReactFlowProvider>
);

export default Modules;
