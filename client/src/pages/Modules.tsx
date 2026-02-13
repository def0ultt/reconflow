import React, { useState, useCallback, useRef } from 'react';
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
import { ToolTemplate } from '../types';
import { Play, Save } from 'lucide-react';
import clsx from 'clsx';
import { useSearchParams } from 'react-router-dom';
import ToolLibrary from '../components/builder/ToolLibrary';

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

let id = 0;
const getId = () => `dndnode_${id++}`;

const ModulesContent = ({ projectIdProp }: { projectIdProp?: string }) => {
    const reactFlowWrapper = useRef<HTMLDivElement>(null);
    const [nodes, setNodes] = useState<Node[]>(initialNodes);
    const [edges, setEdges] = useState<Edge[]>(initialEdges);
    const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

    // Execution State
    const [logs, setLogs] = useState<string[]>([]);
    const [executionId, setExecutionId] = useState<string | null>(null);
    const [isExecuting, setIsExecuting] = useState(false);
    const logsEndRef = useRef<HTMLDivElement>(null);

    // Project Context
    const [searchParams] = useSearchParams();
    const projectId = projectIdProp || searchParams.get('project');

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
            const toolDataStr = event.dataTransfer.getData('application/reactflow');

            if (!toolDataStr || !reactFlowInstance || !reactFlowBounds) return;

            const toolData = JSON.parse(toolDataStr) as ToolTemplate;

            const position = reactFlowInstance.project({
                x: event.clientX - reactFlowBounds.left,
                y: event.clientY - reactFlowBounds.top,
            });

            const newNode: Node = {
                id: getId(),
                type: 'default',
                position,
                data: { label: toolData.name, tool: toolData },
                style: {
                    background: '#18181b',
                    color: '#fff',
                    border: '1px solid #7c3aed',
                    borderRadius: '8px',
                    padding: '10px',
                    width: 180,
                },
            };

            setNodes((nds) => nds.concat(newNode));
        },
        [reactFlowInstance]
    );

    const onDragStart = (event: React.DragEvent, tool: ToolTemplate) => {
        event.dataTransfer.setData('application/reactflow', JSON.stringify(tool));
        event.dataTransfer.effectAllowed = 'move';
    };

    const handleRun = async () => {
        if (nodes.length === 0) {
            alert('Canvas is empty. Add tools first.');
            return;
        }
        // TODO: Implement execution pipeline
        alert('Execution pipeline coming soon!');
    };

    return (
        <div className="h-full w-full flex overflow-hidden">
            {/* Tool Library Sidebar */}
            <ToolLibrary onDragStart={onDragStart} />

            {/* Main Canvas Area */}
            <div className="flex-1 flex flex-col h-full relative">
                {/* Toolbar */}
                <div className="h-14 border-b border-white/10 bg-surface/50 backdrop-blur-md flex items-center justify-between px-6 z-10">
                    <div className="flex items-center space-x-2">
                        <div className="px-3 py-1 bg-primary/20 text-primary rounded-full text-xs font-medium border border-primary/20">
                            {projectId ? `Project #${projectId}` : 'No Project'}
                        </div>
                        <span className="text-[11px] text-gray-500">
                            {nodes.length} node{nodes.length !== 1 ? 's' : ''} · {edges.length} edge{edges.length !== 1 ? 's' : ''}
                        </span>
                    </div>

                    <div className="flex space-x-2">
                        <button className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-surface border border-white/10 hover:bg-white/5 text-gray-300 text-xs transition-colors">
                            <Save size={14} />
                            <span>Save</span>
                        </button>
                        <button
                            onClick={handleRun}
                            disabled={isExecuting}
                            className={clsx(
                                "flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-white text-xs font-medium transition-all shadow-lg",
                                isExecuting ? "bg-gray-600 cursor-not-allowed" : "bg-primary hover:bg-primary/90 shadow-primary/25"
                            )}
                        >
                            <Play size={14} fill="currentColor" />
                            <span>{isExecuting ? 'Running...' : 'Run'}</span>
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

                {/* Logs Panel */}
                <div className={clsx(
                    "absolute bottom-0 left-0 right-0 bg-[#0c0c0e] border-t border-white/10 transition-all duration-300 flex flex-col shadow-2xl z-20",
                    logs.length > 0 || isExecuting ? "h-56" : "h-0 border-none"
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
