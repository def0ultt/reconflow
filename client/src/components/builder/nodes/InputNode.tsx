import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Type, FileText, ToggleRight, FolderOpen } from 'lucide-react';
import { InputNodeData, InputNodeKind } from '../../../types';
import { PORT_COLORS } from './portColors';

const kindConfig: Record<InputNodeKind, { icon: any; color: string; bg: string }> = {
    string: { icon: Type, color: '#a855f7', bg: 'rgba(168, 85, 247, 0.12)' },
    file: { icon: FileText, color: '#f97316', bg: 'rgba(249, 115, 22, 0.12)' },
    boolean: { icon: ToggleRight, color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.12)' },
    folder: { icon: FolderOpen, color: '#22c55e', bg: 'rgba(34, 197, 94, 0.12)' },
};

const InputNode = memo(({ data, selected }: NodeProps<InputNodeData>) => {
    const config = kindConfig[data.kind];
    const Icon = config.icon;

    return (
        <div
            className="input-node"
            style={{
                borderColor: selected ? config.color : 'rgba(255,255,255,0.08)',
                boxShadow: selected ? `0 0 20px ${config.color}33` : 'none',
            }}
        >
            {/* Header */}
            <div className="input-node__header" style={{ background: config.bg }}>
                <div className="input-node__icon" style={{ color: config.color }}>
                    <Icon size={14} />
                </div>
                <span className="input-node__kind" style={{ color: config.color }}>
                    {data.kind.toUpperCase()}
                </span>
            </div>

            {/* Body */}
            <div className="input-node__body">
                <span className="input-node__label">{data.label}</span>
                {data.kind === 'boolean' ? (
                    <span className="input-node__value" style={{ color: data.value ? '#22c55e' : '#ef4444' }}>
                        {data.value ? 'true' : 'false'}
                    </span>
                ) : data.kind === 'string' || data.kind === 'file' ? (
                    <span className="input-node__value">
                        {data.value
                            ? String(data.value).split('\n').length + ' line(s)'
                            : 'Empty'}
                    </span>
                ) : null}
            </div>

            {/* Output Handle */}
            <Handle
                type="source"
                position={Position.Right}
                id={data.output.id}
                className="workflow-handle"
                style={{ backgroundColor: PORT_COLORS[data.output.type] }}
            />
        </div>
    );
});

InputNode.displayName = 'InputNode';
export default InputNode;
