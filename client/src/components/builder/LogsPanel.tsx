import { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';
import { Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { LogEntry, LogChannel } from '../../types';

interface LogsPanelProps {
    logs: LogEntry[];
    onClear: () => void;
}

const TABS: { key: LogChannel | 'all'; label: string }[] = [
    { key: 'all', label: 'Output' },
    { key: 'stdout', label: 'stdout' },
    { key: 'stderr', label: 'stderr' },
    { key: 'system', label: 'system' },
];

const channelColors: Record<LogChannel, string> = {
    stdout: 'text-green-400',
    stderr: 'text-red-400',
    system: 'text-blue-400',
};

const LogsPanel = ({ logs, onClear }: LogsPanelProps) => {
    const [activeTab, setActiveTab] = useState<LogChannel | 'all'>('all');
    const [collapsed, setCollapsed] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    const filtered = activeTab === 'all' ? logs : logs.filter((l) => l.channel === activeTab);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [filtered.length]);

    return (
        <div className={clsx('logs-panel', collapsed && 'logs-panel--collapsed')}>
            {/* Header */}
            <div className="logs-panel__header">
                <div className="logs-panel__tabs">
                    {TABS.map((tab) => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={clsx(
                                'logs-panel__tab',
                                activeTab === tab.key && 'logs-panel__tab--active'
                            )}
                        >
                            {tab.label}
                            {tab.key !== 'all' && (
                                <span className="logs-panel__tab-count">
                                    {logs.filter((l) => l.channel === tab.key).length}
                                </span>
                            )}
                        </button>
                    ))}
                </div>
                <div className="flex items-center gap-1">
                    <button
                        onClick={onClear}
                        className="p-1.5 rounded hover:bg-white/10 text-gray-500 hover:text-white transition-colors"
                        title="Clear logs"
                    >
                        <Trash2 size={13} />
                    </button>
                    <button
                        onClick={() => setCollapsed(!collapsed)}
                        className="p-1.5 rounded hover:bg-white/10 text-gray-500 hover:text-white transition-colors"
                        title={collapsed ? 'Expand' : 'Collapse'}
                    >
                        {collapsed ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                    </button>
                </div>
            </div>

            {/* Log lines */}
            {!collapsed && (
                <div className="logs-panel__body" ref={scrollRef}>
                    {filtered.length === 0 ? (
                        <p className="text-xs text-gray-600 p-4 text-center">No logs yet. Execute a workflow to see output.</p>
                    ) : (
                        filtered.map((entry, i) => (
                            <div key={i} className="logs-panel__line">
                                <span className="logs-panel__ts">
                                    {new Date(entry.timestamp).toLocaleTimeString()}
                                </span>
                                {entry.nodeName && (
                                    <span className="logs-panel__node-badge">{entry.nodeName}</span>
                                )}
                                <span className={clsx('logs-panel__msg', channelColors[entry.channel])}>
                                    {entry.message}
                                </span>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
};

export default LogsPanel;
