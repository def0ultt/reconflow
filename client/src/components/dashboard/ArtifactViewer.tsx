import { useState, useEffect } from 'react';
import { ArrowLeft, RefreshCw, Search, Regex, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';
import clsx from 'clsx';
import DataTable from './DataTable';

const API_URL = 'http://localhost:8000/api';

interface ArtifactViewerProps {
    projectId: string;
    filePath: string;
    fileName: string;
    onBack: () => void;
}

const ArtifactViewer = ({ projectId, filePath, fileName, onBack }: ArtifactViewerProps) => {
    const [allColumns, setAllColumns] = useState<string[]>([]);
    const [visibleColumns, setVisibleColumns] = useState<Set<string>>(new Set());
    const [rows, setRows] = useState<Record<string, any>[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [totalCount, setTotalCount] = useState(0);

    // Search
    const [searchQuery, setSearchQuery] = useState('');
    const [isRegex, setIsRegex] = useState(false);

    // Column panel
    const [columnPanelOpen, setColumnPanelOpen] = useState(false);

    const fetchContent = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await axios.get(`${API_URL}/projects/${projectId}/artifacts/${filePath}`);
            const data = res.data;

            if (data.type === 'binary') {
                setError(data.message || 'Binary file cannot be displayed');
                setAllColumns([]);
                setRows([]);
                return;
            }

            const cols = data.columns || [];
            setAllColumns(cols);
            setVisibleColumns(new Set(cols));
            setRows(data.rows || []);
            setTotalCount(data.total_count || 0);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load file');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchContent();
    }, [projectId, filePath]);

    const toggleColumn = (col: string) => {
        setVisibleColumns(prev => {
            const next = new Set(prev);
            if (next.has(col)) {
                next.delete(col);
            } else {
                next.add(col);
            }
            return next;
        });
    };

    const displayColumns = allColumns.filter(c => visibleColumns.has(c));

    return (
        <div className="flex flex-col h-full">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-surface/50 flex-shrink-0">
                <div className="flex items-center space-x-3">
                    <button
                        onClick={onBack}
                        className="flex items-center space-x-1.5 text-xs text-gray-400 hover:text-white transition-colors"
                    >
                        <ArrowLeft size={14} />
                        <span>Back</span>
                    </button>
                    <div className="h-4 w-px bg-border" />
                    <span className="text-sm font-mono text-gray-200">{fileName}</span>
                    <span className="text-[10px] text-gray-500 px-2 py-0.5 bg-primary/10 text-primary rounded-full uppercase font-medium">
                        {totalCount.toLocaleString()} rows
                    </span>
                </div>

                <div className="flex items-center space-x-2">
                    <button
                        onClick={() => setColumnPanelOpen(!columnPanelOpen)}
                        className={clsx(
                            "flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs transition-colors",
                            columnPanelOpen
                                ? "bg-primary/15 text-primary"
                                : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
                        )}
                    >
                        {columnPanelOpen ? <EyeOff size={12} /> : <Eye size={12} />}
                        <span>Columns</span>
                    </button>
                    <button
                        onClick={fetchContent}
                        className="flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs text-gray-500 hover:text-primary transition-colors hover:bg-white/5"
                    >
                        <RefreshCw size={12} />
                        <span>Refresh</span>
                    </button>
                </div>
            </div>

            {/* Search Bar */}
            <div className="flex items-center px-4 py-2 border-b border-border bg-surface/30 flex-shrink-0 space-x-2">
                <Search size={14} className="text-gray-600 flex-shrink-0" />
                <input
                    type="text"
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder="Filter your data..."
                    className="flex-1 bg-transparent text-sm outline-none placeholder:text-gray-600"
                />
                <button
                    onClick={() => setIsRegex(!isRegex)}
                    title={isRegex ? "Regex mode ON" : "Regex mode OFF"}
                    className={clsx(
                        "p-1 rounded transition-colors text-xs",
                        isRegex
                            ? "bg-primary/15 text-primary"
                            : "text-gray-600 hover:text-gray-400"
                    )}
                >
                    <Regex size={14} />
                </button>
            </div>

            {/* Main Content */}
            <div className="flex flex-1 overflow-hidden">
                {/* Column Panel */}
                {columnPanelOpen && (
                    <div className="w-48 border-r border-border bg-surface/30 overflow-y-auto flex-shrink-0 p-3 space-y-1">
                        <p className="text-[10px] uppercase tracking-wider text-gray-500 font-medium mb-2">Columns</p>
                        {allColumns.map(col => (
                            <label
                                key={col}
                                className="flex items-center space-x-2 px-2 py-1.5 rounded hover:bg-white/5 cursor-pointer transition-colors"
                            >
                                <input
                                    type="checkbox"
                                    checked={visibleColumns.has(col)}
                                    onChange={() => toggleColumn(col)}
                                    className="accent-primary w-3 h-3"
                                />
                                <span className="text-xs text-gray-300 font-mono truncate">{col}</span>
                            </label>
                        ))}
                    </div>
                )}

                {/* Table */}
                <div className="flex-1 overflow-hidden">
                    {loading ? (
                        <div className="flex items-center justify-center h-full">
                            <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent" />
                        </div>
                    ) : error ? (
                        <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                            {error}
                        </div>
                    ) : (
                        <DataTable
                            columns={displayColumns}
                            rows={rows}
                            searchQuery={searchQuery}
                            isRegex={isRegex}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default ArtifactViewer;
