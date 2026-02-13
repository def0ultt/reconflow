import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Loader2, CheckCircle2, XCircle, Cpu } from 'lucide-react';
import { ProcessorNodeData } from '../../../types';
import { PORT_COLORS } from './portColors';

const statusConfig = {
    idle: { icon: Cpu, color: '#71717a', label: 'Idle' },
    running: { icon: Loader2, color: '#eab308', label: 'Running' },
    completed: { icon: CheckCircle2, color: '#22c55e', label: 'Done' },
    failed: { icon: XCircle, color: '#ef4444', label: 'Failed' },
};

const ProcessorNode = memo(({ data, selected }: NodeProps<ProcessorNodeData>) => {
    const status = statusConfig[data.status];
    const StatusIcon = status.icon;

    return (
        <div
            className="processor-node"
            style={{
                borderColor: selected ? '#a855f7' : 'rgba(255,255,255,0.08)',
                boxShadow: selected ? '0 0 20px rgba(168, 85, 247, 0.2)' : 'none',
            }}
        >
            {/* Input Handles */}
            {data.inputs.map((port, i) => (
                <Handle
                    key={port.id}
                    type="target"
                    position={Position.Left}
                    id={port.id}
                    className="workflow-handle"
                    style={{
                        backgroundColor: PORT_COLORS[port.type],
                        top: `${44 + i * 28}px`,
                    }}
                />
            ))}

            {/* Header */}
            <div className="processor-node__header">
                <div className="processor-node__title">
                    <Cpu size={14} className="text-primary" />
                    <span>{data.label}</span>
                </div>
                <div
                    className="processor-node__status"
                    style={{ color: status.color }}
                    title={status.label}
                >
                    <StatusIcon
                        size={14}
                        className={data.status === 'running' ? 'animate-spin' : ''}
                    />
                </div>
            </div>

            {/* Ports */}
            <div className="processor-node__ports">
                {/* Input ports */}
                <div className="processor-node__port-list">
                    {data.inputs.map((port) => (
                        <div key={port.id} className="processor-node__port processor-node__port--input">
                            <span
                                className="processor-node__port-dot"
                                style={{ backgroundColor: PORT_COLORS[port.type] }}
                            />
                            <span className="processor-node__port-name">
                                {port.name}{port.required ? '*' : ''}
                            </span>
                        </div>
                    ))}
                </div>

                {/* Output ports */}
                <div className="processor-node__port-list processor-node__port-list--right">
                    {data.outputs.map((port) => (
                        <div key={port.id} className="processor-node__port processor-node__port--output">
                            <span className="processor-node__port-name">{port.name}</span>
                            <span
                                className="processor-node__port-dot"
                                style={{ backgroundColor: PORT_COLORS[port.type] }}
                            />
                        </div>
                    ))}
                </div>
            </div>

            {/* Output Handles */}
            {data.outputs.map((port, i) => (
                <Handle
                    key={port.id}
                    type="source"
                    position={Position.Right}
                    id={port.id}
                    className="workflow-handle"
                    style={{
                        backgroundColor: PORT_COLORS[port.type],
                        top: `${44 + i * 28}px`,
                    }}
                />
            ))}
        </div>
    );
});

ProcessorNode.displayName = 'ProcessorNode';
export default ProcessorNode;
