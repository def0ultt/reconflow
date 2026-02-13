import { useState } from 'react';
import axios from 'axios';
import { X, Plus, Minus, CheckCircle, AlertCircle } from 'lucide-react';
import clsx from 'clsx';

const API_URL = 'http://localhost:8000/api';

interface ImportToolModalProps {
    onClose: () => void;
    onCreated: () => void;
}

interface IOField {
    name: string;
    type: string;
    required: boolean;
    description: string;
}

const CATEGORY_OPTIONS = [
    'recon',
    'scanning',
    'dns',
    'vulnerability',
    'bruteforce',
    'other',
];

const ImportToolModal = ({ onClose, onCreated }: ImportToolModalProps) => {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [binaryPath, setBinaryPath] = useState('');
    const [category, setCategory] = useState('recon');
    const [defaultArgs, setDefaultArgs] = useState('');
    const [tags, setTags] = useState('');
    const [inputs, setInputs] = useState<IOField[]>([
        { name: '', type: 'string', required: true, description: '' }
    ]);
    const [outputs, setOutputs] = useState<IOField[]>([
        { name: '', type: 'file', required: false, description: '' }
    ]);

    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [validating, setValidating] = useState(false);
    const [validationResult, setValidationResult] = useState<{ valid: boolean; message: string } | null>(null);

    const addIO = (kind: 'input' | 'output') => {
        const newField: IOField = { name: '', type: kind === 'input' ? 'string' : 'file', required: false, description: '' };
        if (kind === 'input') setInputs([...inputs, newField]);
        else setOutputs([...outputs, newField]);
    };

    const removeIO = (kind: 'input' | 'output', idx: number) => {
        if (kind === 'input') setInputs(inputs.filter((_, i) => i !== idx));
        else setOutputs(outputs.filter((_, i) => i !== idx));
    };

    const updateIO = (kind: 'input' | 'output', idx: number, field: string, value: any) => {
        const setter = kind === 'input' ? setInputs : setOutputs;
        const arr = kind === 'input' ? [...inputs] : [...outputs];
        (arr[idx] as any)[field] = value;
        setter(arr);
    };

    const handleValidate = async () => {
        if (!binaryPath.trim()) return;
        setValidating(true);
        setValidationResult(null);

        // Create tool just for validation — but we can validate the path directly
        try {
            const res = await axios.post(`${API_URL}/tools`, {
                name: `__validate_${Date.now()}`,
                binary_path: binaryPath.trim(),
            });
            // Delete the temp tool
            const toolId = res.data.id;
            const valRes = await axios.post(`${API_URL}/tools/${toolId}/validate`);
            await axios.delete(`${API_URL}/tools/${toolId}`);
            setValidationResult(valRes.data);
        } catch {
            setValidationResult({ valid: false, message: 'Validation failed' });
        } finally {
            setValidating(false);
        }
    };

    const handleSubmit = async () => {
        if (!name.trim()) {
            setError('Tool name is required');
            return;
        }

        setSaving(true);
        setError(null);

        const payload = {
            name: name.trim(),
            description: description.trim() || null,
            binary_path: binaryPath.trim() || null,
            category,
            default_args: defaultArgs.trim() ? defaultArgs.split(/\s+/) : [],
            tags: tags.trim() ? tags.split(',').map(t => t.trim()).filter(Boolean) : [],
            inputs: inputs.filter(i => i.name.trim()),
            outputs: outputs.filter(o => o.name.trim()),
        };

        try {
            await axios.post(`${API_URL}/tools`, payload);
            onCreated();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to create tool');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-surface border border-border rounded-xl w-[560px] max-h-[85vh] overflow-y-auto shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-3 border-b border-border sticky top-0 bg-surface z-10">
                    <h3 className="text-sm font-bold text-gray-200">Import Tool</h3>
                    <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                        <X size={16} />
                    </button>
                </div>

                <div className="p-5 space-y-4">
                    {/* Error */}
                    {error && (
                        <div className="flex items-center space-x-2 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs">
                            <AlertCircle size={14} />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Name + Category Row */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Name *</label>
                            <input
                                type="text"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                placeholder="subfinder"
                                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary transition-colors font-mono"
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Category</label>
                            <select
                                value={category}
                                onChange={e => setCategory(e.target.value)}
                                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary transition-colors"
                            >
                                {CATEGORY_OPTIONS.map(c => (
                                    <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Description */}
                    <div>
                        <label className="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Description</label>
                        <input
                            type="text"
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            placeholder="Fast passive subdomain enumeration tool"
                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary transition-colors"
                        />
                    </div>

                    {/* Binary Path */}
                    <div>
                        <label className="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Binary Path</label>
                        <div className="flex space-x-2">
                            <input
                                type="text"
                                value={binaryPath}
                                onChange={e => { setBinaryPath(e.target.value); setValidationResult(null); }}
                                placeholder="/usr/bin/subfinder or subfinder"
                                className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary transition-colors font-mono"
                            />
                            <button
                                onClick={handleValidate}
                                disabled={validating || !binaryPath.trim()}
                                className="px-3 py-2 rounded-lg bg-primary/15 text-primary text-xs font-medium hover:bg-primary/25 transition-colors border border-primary/20 disabled:opacity-50"
                            >
                                {validating ? '...' : 'Validate'}
                            </button>
                        </div>
                        {validationResult && (
                            <div className={clsx("flex items-center space-x-1.5 mt-1.5 text-[11px]",
                                validationResult.valid ? "text-green-400" : "text-red-400"
                            )}>
                                {validationResult.valid ? <CheckCircle size={12} /> : <AlertCircle size={12} />}
                                <span>{validationResult.message}</span>
                            </div>
                        )}
                    </div>

                    {/* Default Arguments */}
                    <div>
                        <label className="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Default Arguments</label>
                        <input
                            type="text"
                            value={defaultArgs}
                            onChange={e => setDefaultArgs(e.target.value)}
                            placeholder="-silent -o {{output}}"
                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary transition-colors font-mono"
                        />
                        <p className="text-[10px] text-gray-600 mt-1">Space-separated. Use {'{{output}}'} for dynamic output path.</p>
                    </div>

                    {/* Tags */}
                    <div>
                        <label className="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Tags</label>
                        <input
                            type="text"
                            value={tags}
                            onChange={e => setTags(e.target.value)}
                            placeholder="subdomain, passive, enumeration"
                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary transition-colors"
                        />
                        <p className="text-[10px] text-gray-600 mt-1">Comma-separated tags for filtering.</p>
                    </div>

                    {/* Inputs */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="text-[10px] font-medium text-gray-500 uppercase tracking-wider">Inputs</label>
                            <button onClick={() => addIO('input')} className="text-primary text-[10px] hover:underline flex items-center space-x-1">
                                <Plus size={10} /><span>Add Input</span>
                            </button>
                        </div>
                        <div className="space-y-2">
                            {inputs.map((inp, idx) => (
                                <div key={idx} className="flex items-center space-x-2 bg-background/50 rounded-lg p-2 border border-border/50">
                                    <input
                                        type="text"
                                        value={inp.name}
                                        onChange={e => updateIO('input', idx, 'name', e.target.value)}
                                        placeholder="name"
                                        className="flex-1 bg-transparent text-xs outline-none font-mono px-1"
                                    />
                                    <select
                                        value={inp.type}
                                        onChange={e => updateIO('input', idx, 'type', e.target.value)}
                                        className="bg-background border border-border rounded px-1.5 py-0.5 text-[10px] outline-none"
                                    >
                                        <option value="string">string</option>
                                        <option value="file">file</option>
                                        <option value="list">list</option>
                                    </select>
                                    <label className="flex items-center space-x-1 text-[10px] text-gray-500">
                                        <input
                                            type="checkbox"
                                            checked={inp.required}
                                            onChange={e => updateIO('input', idx, 'required', e.target.checked)}
                                            className="accent-primary w-3 h-3"
                                        />
                                        <span>req</span>
                                    </label>
                                    <button onClick={() => removeIO('input', idx)} className="text-gray-600 hover:text-red-400">
                                        <Minus size={12} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Outputs */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="text-[10px] font-medium text-gray-500 uppercase tracking-wider">Outputs</label>
                            <button onClick={() => addIO('output')} className="text-primary text-[10px] hover:underline flex items-center space-x-1">
                                <Plus size={10} /><span>Add Output</span>
                            </button>
                        </div>
                        <div className="space-y-2">
                            {outputs.map((out, idx) => (
                                <div key={idx} className="flex items-center space-x-2 bg-background/50 rounded-lg p-2 border border-border/50">
                                    <input
                                        type="text"
                                        value={out.name}
                                        onChange={e => updateIO('output', idx, 'name', e.target.value)}
                                        placeholder="name"
                                        className="flex-1 bg-transparent text-xs outline-none font-mono px-1"
                                    />
                                    <select
                                        value={out.type}
                                        onChange={e => updateIO('output', idx, 'type', e.target.value)}
                                        className="bg-background border border-border rounded px-1.5 py-0.5 text-[10px] outline-none"
                                    >
                                        <option value="file">file</option>
                                        <option value="string">string</option>
                                        <option value="list">list</option>
                                    </select>
                                    <button onClick={() => removeIO('output', idx)} className="text-gray-600 hover:text-red-400">
                                        <Minus size={12} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end px-5 py-3 border-t border-border space-x-3 sticky bottom-0 bg-surface">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg text-xs text-gray-400 hover:text-white transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={saving || !name.trim()}
                        className={clsx(
                            "px-4 py-2 rounded-lg text-xs font-medium transition-all",
                            saving || !name.trim()
                                ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                                : "bg-primary text-white hover:bg-primary/90 shadow-lg shadow-primary/25"
                        )}
                    >
                        {saving ? 'Creating...' : 'Import Tool'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ImportToolModal;
