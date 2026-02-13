import { Node } from 'reactflow';
import { InputNodeData, ProcessorNodeData } from '../../types';
import { PORT_COLORS } from './nodes/portColors';
import { X, Cpu } from 'lucide-react';

// Re-export PORT_LABELS from types if needed
const portLabel = (type: string) => {
    const labels: Record<string, string> = { string: 'String', file: 'File', boolean: 'Boolean', folder: 'Folder' };
    return labels[type] || type;
};

interface NodeInspectorProps {
    selectedNode: Node | null;
    onUpdateNode: (id: string, data: Partial<InputNodeData | ProcessorNodeData>) => void;
    onClose: () => void;
}

const NodeInspector = ({ selectedNode, onUpdateNode, onClose }: NodeInspectorProps) => {
    if (!selectedNode) {
        return (
            <div className="node-inspector node-inspector--empty">
                <div className="node-inspector__placeholder">
                    <Cpu size={40} className="text-gray-600 mb-3" />
                    <p className="text-sm text-gray-500">Select a node to configure</p>
                </div>
            </div>
        );
    }

    const isInput = selectedNode.type === 'inputNode';
    const data = selectedNode.data as InputNodeData | ProcessorNodeData;

    return (
        <div className="node-inspector">
            {/* Header */}
            <div className="node-inspector__header">
                <h3 className="text-sm font-semibold text-white truncate">
                    {isInput ? (data as InputNodeData).kind.toUpperCase() + ' Input' : (data as ProcessorNodeData).label}
                </h3>
                <button
                    onClick={onClose}
                    className="p-1 rounded hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                >
                    <X size={16} />
                </button>
            </div>

            <div className="node-inspector__body">
                {isInput ? (
                    <InputEditor
                        node={selectedNode}
                        data={data as InputNodeData}
                        onUpdate={onUpdateNode}
                    />
                ) : (
                    <ProcessorInfo data={data as ProcessorNodeData} />
                )}
            </div>
        </div>
    );
};

// ─── Input Editor ─────────────────────────────────────────────
function InputEditor({
    node,
    data,
    onUpdate,
}: {
    node: Node;
    data: InputNodeData;
    onUpdate: (id: string, data: Partial<InputNodeData>) => void;
}) {
    const handleLabelChange = (label: string) => onUpdate(node.id, { label });
    const handleValueChange = (value: string | boolean | null) => onUpdate(node.id, { value });

    return (
        <div className="space-y-4">
            {/* Label */}
            <div>
                <label className="node-inspector__label">Label</label>
                <input
                    type="text"
                    value={data.label}
                    onChange={(e) => handleLabelChange(e.target.value)}
                    className="node-inspector__input"
                    placeholder="Node label"
                />
            </div>

            {/* Value editor based on kind */}
            <div>
                <label className="node-inspector__label">
                    Value
                    <span className="node-inspector__type-badge" style={{ color: PORT_COLORS[data.kind] }}>
                        {portLabel(data.kind)}
                    </span>
                </label>

                {data.kind === 'string' && (
                    <textarea
                        value={typeof data.value === 'string' ? data.value : ''}
                        onChange={(e) => handleValueChange(e.target.value)}
                        className="node-inspector__textarea"
                        placeholder="Enter text value..."
                        rows={6}
                    />
                )}

                {data.kind === 'file' && (
                    <textarea
                        value={typeof data.value === 'string' ? data.value : ''}
                        onChange={(e) => handleValueChange(e.target.value)}
                        className="node-inspector__textarea"
                        placeholder="Paste file contents (one item per line)..."
                        rows={8}
                    />
                )}

                {data.kind === 'boolean' && (
                    <button
                        onClick={() => handleValueChange(!data.value)}
                        className={`node-inspector__toggle ${data.value ? 'node-inspector__toggle--on' : ''}`}
                    >
                        <span className="node-inspector__toggle-knob" />
                        <span className="ml-3 text-sm text-gray-300">
                            {data.value ? 'true' : 'false'}
                        </span>
                    </button>
                )}

                {data.kind === 'folder' && (
                    <input
                        type="text"
                        value={typeof data.value === 'string' ? data.value : ''}
                        onChange={(e) => handleValueChange(e.target.value)}
                        className="node-inspector__input"
                        placeholder="/path/to/folder"
                    />
                )}
            </div>
        </div>
    );
}

// ─── Processor Info (read-only) ───────────────────────────────
function ProcessorInfo({ data }: { data: ProcessorNodeData }) {
    return (
        <div className="space-y-4">
            {/* Description */}
            {data.toolDescription && (
                <div>
                    <label className="node-inspector__label">Description</label>
                    <p className="text-xs text-gray-400 leading-relaxed">{data.toolDescription}</p>
                </div>
            )}

            {/* Category */}
            {data.toolCategory && (
                <div>
                    <label className="node-inspector__label">Category</label>
                    <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-primary/20 text-primary">
                        {data.toolCategory}
                    </span>
                </div>
            )}

            {/* Inputs */}
            <div>
                <label className="node-inspector__label">Inputs</label>
                <div className="space-y-1.5">
                    {data.inputs.map((port) => (
                        <div key={port.id} className="flex items-center gap-2 text-xs">
                            <span
                                className="w-2 h-2 rounded-full flex-shrink-0"
                                style={{ backgroundColor: PORT_COLORS[port.type] }}
                            />
                            <span className="text-gray-300">{port.name}</span>
                            <span className="text-gray-600">({portLabel(port.type)})</span>
                            {port.required && <span className="text-red-400">*</span>}
                        </div>
                    ))}
                </div>
            </div>

            {/* Outputs */}
            <div>
                <label className="node-inspector__label">Outputs</label>
                <div className="space-y-1.5">
                    {data.outputs.map((port) => (
                        <div key={port.id} className="flex items-center gap-2 text-xs">
                            <span
                                className="w-2 h-2 rounded-full flex-shrink-0"
                                style={{ backgroundColor: PORT_COLORS[port.type] }}
                            />
                            <span className="text-gray-300">{port.name}</span>
                            <span className="text-gray-600">({portLabel(port.type)})</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default NodeInspector;
