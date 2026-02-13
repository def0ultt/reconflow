import { useState, useEffect } from 'react';
import axios from 'axios';
import { ToolTemplate } from '../../types';
import {
    Search, GripVertical, Plus, ChevronDown, ChevronRight,
    Globe, Zap, Radar, ShieldAlert, Link, SearchIcon,
    Archive, Server, Rocket, Terminal
} from 'lucide-react';
import clsx from 'clsx';
import ImportToolModal from './ImportToolModal';

const API_URL = 'http://localhost:8000/api';

// Map icon string names to Lucide components
const ICON_MAP: Record<string, any> = {
    globe: Globe,
    zap: Zap,
    radar: Radar,
    'shield-alert': ShieldAlert,
    link: Link,
    search: SearchIcon,
    archive: Archive,
    server: Server,
    rocket: Rocket,
    terminal: Terminal,
};

// Category display config
const CATEGORY_CONFIG: Record<string, { label: string; color: string }> = {
    recon: { label: 'RECON', color: 'text-blue-400' },
    scanning: { label: 'SCANNING', color: 'text-orange-400' },
    vulnerability: { label: 'VULNERABILITY', color: 'text-red-400' },
    bruteforce: { label: 'BRUTEFORCE', color: 'text-yellow-400' },
    dns: { label: 'DNS', color: 'text-cyan-400' },
    other: { label: 'OTHER', color: 'text-gray-400' },
};

interface ToolLibraryProps {
    onDragStart: (event: React.DragEvent, tool: ToolTemplate) => void;
}

const ToolLibrary = ({ onDragStart }: ToolLibraryProps) => {
    const [tools, setTools] = useState<ToolTemplate[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(new Set());
    const [importOpen, setImportOpen] = useState(false);

    const fetchTools = async () => {
        try {
            const res = await axios.get(`${API_URL}/tools`);
            setTools(res.data);
        } catch (err) {
            console.error('Failed to fetch tools', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTools();
    }, []);

    const toggleCategory = (cat: string) => {
        setCollapsedCategories(prev => {
            const next = new Set(prev);
            if (next.has(cat)) {
                next.delete(cat);
            } else {
                next.add(cat);
            }
            return next;
        });
    };

    // Filter tools
    const filtered = tools.filter(t => {
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return (
            t.name.toLowerCase().includes(q) ||
            (t.description || '').toLowerCase().includes(q) ||
            t.tags.some(tag => tag.toLowerCase().includes(q))
        );
    });

    // Group by category
    const grouped: Record<string, ToolTemplate[]> = {};
    for (const t of filtered) {
        const cat = t.category || 'other';
        if (!grouped[cat]) grouped[cat] = [];
        grouped[cat].push(t);
    }

    // Sort categories
    const categoryOrder = ['recon', 'scanning', 'dns', 'vulnerability', 'bruteforce', 'other'];
    const sortedCategories = Object.keys(grouped).sort((a, b) => {
        const ai = categoryOrder.indexOf(a);
        const bi = categoryOrder.indexOf(b);
        return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
    });

    const getIcon = (iconName: string | null) => {
        return ICON_MAP[iconName || ''] || Rocket;
    };

    return (
        <>
            <div className="w-full bg-surface border-r border-white/10 flex flex-col h-full z-20 shadow-xl">
                {/* Header */}
                <div className="p-4 border-b border-white/10">
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-sm font-bold flex items-center text-gray-200">
                            <Terminal className="mr-2 text-primary" size={16} />
                            Tool Library
                        </h2>
                        <button
                            onClick={() => setImportOpen(true)}
                            className="flex items-center space-x-1 px-2 py-1 rounded-md bg-primary/15 text-primary text-[11px] font-medium hover:bg-primary/25 transition-colors border border-primary/20"
                        >
                            <Plus size={12} />
                            <span>Import</span>
                        </button>
                    </div>
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" size={14} />
                        <input
                            type="text"
                            placeholder="Search tools..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-black/20 border border-white/10 rounded-lg py-1.5 pl-8 pr-3 text-xs focus:border-primary outline-none transition-colors"
                        />
                    </div>
                </div>

                {/* Tool List */}
                <div className="flex-1 overflow-y-auto">
                    {loading ? (
                        <div className="p-4 space-y-3">
                            {[1, 2, 3, 4].map(i => <div key={i} className="skeleton h-10 rounded-lg" />)}
                        </div>
                    ) : sortedCategories.length === 0 ? (
                        <div className="text-center py-8 text-gray-500 text-xs">
                            {searchQuery ? 'No tools match your search' : 'No tools available'}
                        </div>
                    ) : (
                        sortedCategories.map(cat => {
                            const config = CATEGORY_CONFIG[cat] || { label: cat.toUpperCase(), color: 'text-gray-400' };
                            const isCollapsed = collapsedCategories.has(cat);
                            const catTools = grouped[cat];

                            return (
                                <div key={cat}>
                                    {/* Category Header */}
                                    <button
                                        onClick={() => toggleCategory(cat)}
                                        className="w-full flex items-center justify-between px-4 py-2 bg-background/30 hover:bg-background/50 transition-colors border-b border-white/5"
                                    >
                                        <div className="flex items-center space-x-2">
                                            {isCollapsed
                                                ? <ChevronRight size={12} className="text-gray-500" />
                                                : <ChevronDown size={12} className="text-gray-500" />
                                            }
                                            <span className={clsx("text-[10px] font-bold uppercase tracking-wider", config.color)}>
                                                {config.label}
                                            </span>
                                        </div>
                                        <span className="text-[10px] text-gray-600 font-mono">{catTools.length}</span>
                                    </button>

                                    {/* Tools in category */}
                                    {!isCollapsed && (
                                        <div className="py-1">
                                            {catTools.map(tool => {
                                                const Icon = getIcon(tool.icon);
                                                return (
                                                    <div
                                                        key={tool.id}
                                                        onDragStart={(e) => onDragStart(e, tool)}
                                                        draggable
                                                        className="group flex items-center space-x-2.5 px-4 py-2 mx-1 rounded-md cursor-grab active:cursor-grabbing hover:bg-white/5 transition-all"
                                                    >
                                                        <div className="p-1.5 bg-primary/10 rounded text-primary group-hover:bg-primary group-hover:text-white transition-colors flex-shrink-0">
                                                            <Icon size={12} />
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <div className="text-xs font-medium text-gray-200 group-hover:text-white truncate">
                                                                {tool.name}
                                                            </div>
                                                            <div className="text-[10px] text-gray-500 line-clamp-2 leading-relaxed">
                                                                {tool.description || 'No description'}
                                                            </div>
                                                        </div>
                                                        <GripVertical className="text-gray-600 opacity-0 group-hover:opacity-100 flex-shrink-0" size={14} />
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            );
                        })
                    )}
                </div>

                {/* Footer */}
                <div className="px-4 py-2 border-t border-white/5 text-[10px] text-gray-600 text-center">
                    {tools.length} tools available
                </div>
            </div>

            {/* Import Tool Modal */}
            {importOpen && (
                <ImportToolModal
                    onClose={() => setImportOpen(false)}
                    onCreated={() => {
                        setImportOpen(false);
                        fetchTools();
                    }}
                />
            )}
        </>
    );
};

export default ToolLibrary;
