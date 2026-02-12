import { useState } from 'react';
import { Search, Regex, X, FileText, Filter } from 'lucide-react';
import axios from 'axios';
import clsx from 'clsx';
import { Artifact } from '../../types';

const API_URL = 'http://localhost:8000/api';

interface SearchMatch {
    line_number: number;
    content: string;
}

interface SearchResult {
    file: string;
    match_count: number;
    matches: SearchMatch[];
}

interface GlobalSearchProps {
    projectId: string;
    artifacts: Artifact[];
    onOpenFile: (artifact: Artifact) => void;
    onSearchActive?: (active: boolean) => void;
}

const GlobalSearch = ({ projectId, artifacts, onOpenFile, onSearchActive }: GlobalSearchProps) => {
    const [query, setQuery] = useState('');
    const [isRegex, setIsRegex] = useState(false);
    const [searching, setSearching] = useState(false);
    const [results, setResults] = useState<SearchResult[] | null>(null);
    const [totalMatches, setTotalMatches] = useState(0);
    const [showFilters, setShowFilters] = useState(false);

    // Include/Exclude
    const [includePattern, setIncludePattern] = useState('');
    const [excludePattern, setExcludePattern] = useState('');

    // Expanded results
    const [expandedFile, setExpandedFile] = useState<string | null>(null);

    const handleSearch = async () => {
        if (!query.trim()) return;

        setSearching(true);
        try {
            const params: any = { q: query, regex: isRegex };
            if (includePattern.trim()) params.include = includePattern.trim();
            if (excludePattern.trim()) params.exclude = excludePattern.trim();

            const res = await axios.get(`${API_URL}/projects/${projectId}/search`, { params });
            setResults(res.data.results);
            setTotalMatches(res.data.total_matches);
            onSearchActive?.(res.data.results.length > 0);
        } catch (err: any) {
            console.error("Search failed:", err);
            setResults([]);
            setTotalMatches(0);
        } finally {
            setSearching(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleSearch();
    };

    const clearSearch = () => {
        setQuery('');
        setResults(null);
        setTotalMatches(0);
        onSearchActive?.(false);
    };

    // Highlight query in text
    const highlight = (text: string) => {
        if (!query.trim()) return text;
        try {
            const pattern = isRegex
                ? new RegExp(`(${query})`, 'gi')
                : new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            const parts = text.split(pattern);
            return parts.map((part, i) =>
                pattern.test(part)
                    ? <span key={i} className="bg-primary/30 text-primary">{part}</span>
                    : part
            );
        } catch {
            return text;
        }
    };

    return (
        <div className="space-y-3">
            {/* Search Bar */}
            <div className="bg-surface border border-border rounded-xl overflow-hidden">
                <div className="flex items-center px-4 py-2.5 space-x-2">
                    <Search size={16} className="text-gray-600 flex-shrink-0" />
                    <input
                        type="text"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Search across all files... (Enter to search)"
                        className="flex-1 bg-transparent text-sm outline-none placeholder:text-gray-600"
                    />
                    {query && (
                        <button onClick={clearSearch} className="text-gray-500 hover:text-gray-300 transition-colors">
                            <X size={14} />
                        </button>
                    )}
                    <button
                        onClick={() => setIsRegex(!isRegex)}
                        title={isRegex ? "Regex ON" : "Regex OFF"}
                        className={clsx(
                            "p-1 rounded transition-colors",
                            isRegex ? "bg-primary/15 text-primary" : "text-gray-600 hover:text-gray-400"
                        )}
                    >
                        <Regex size={14} />
                    </button>
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        title="Include/Exclude Filters"
                        className={clsx(
                            "p-1 rounded transition-colors",
                            showFilters ? "bg-primary/15 text-primary" : "text-gray-600 hover:text-gray-400"
                        )}
                    >
                        <Filter size={14} />
                    </button>
                    <button
                        onClick={handleSearch}
                        disabled={searching || !query.trim()}
                        className="px-3 py-1 bg-primary/20 text-primary text-xs font-medium rounded hover:bg-primary/30 transition-colors disabled:opacity-40"
                    >
                        {searching ? 'Searching...' : 'Search'}
                    </button>
                </div>

                {/* Include / Exclude Filters */}
                {showFilters && (
                    <div className="px-4 py-2.5 border-t border-border/50 flex items-center space-x-4">
                        <div className="flex items-center space-x-2 flex-1">
                            <span className="text-[10px] uppercase tracking-wider text-green-400 font-medium w-14 flex-shrink-0">Include</span>
                            <input
                                type="text"
                                value={includePattern}
                                onChange={e => setIncludePattern(e.target.value)}
                                className="flex-1 bg-background border border-border rounded px-2 py-1 text-xs outline-none focus:border-primary transition-colors font-mono"
                            />
                        </div>
                        <div className="flex items-center space-x-2 flex-1">
                            <span className="text-[10px] uppercase tracking-wider text-red-400 font-medium w-14 flex-shrink-0">Exclude</span>
                            <input
                                type="text"
                                value={excludePattern}
                                onChange={e => setExcludePattern(e.target.value)}
                                className="flex-1 bg-background border border-border rounded px-2 py-1 text-xs outline-none focus:border-primary transition-colors font-mono"
                            />
                        </div>
                    </div>
                )}
            </div>

            {/* Results */}
            {results !== null && (
                <div className="bg-surface border border-border rounded-xl overflow-hidden">
                    <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
                        <span className="text-xs text-gray-400">
                            <span className="text-primary font-medium">{totalMatches.toLocaleString()}</span> matches across{' '}
                            <span className="text-gray-300 font-medium">{results.length}</span> files
                        </span>
                    </div>

                    {results.length === 0 ? (
                        <div className="py-8 text-center text-gray-500 text-sm">No matches found</div>
                    ) : (
                        <div className="max-h-[600px] overflow-y-auto">
                            {results.map((result, idx) => {
                                const isExpanded = expandedFile === result.file;
                                const artifact = artifacts.find(a => a.path === result.file);

                                return (
                                    <div key={idx} className="border-b border-border/30 last:border-b-0">
                                        {/* File Header */}
                                        <div
                                            onClick={() => setExpandedFile(isExpanded ? null : result.file)}
                                            className="flex items-center justify-between px-4 py-2 hover:bg-white/[0.02] cursor-pointer transition-colors"
                                        >
                                            <div className="flex items-center space-x-2">
                                                <FileText size={14} className="text-gray-500" />
                                                <span className="text-sm font-mono text-gray-200">{result.file}</span>
                                            </div>
                                            <div className="flex items-center space-x-3">
                                                <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                                                    {result.match_count} matches
                                                </span>
                                                {artifact && (
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); onOpenFile(artifact); }}
                                                        className="text-[10px] text-gray-500 hover:text-primary transition-colors"
                                                    >
                                                        Open →
                                                    </button>
                                                )}
                                            </div>
                                        </div>

                                        {/* Matches Preview */}
                                        {isExpanded && (
                                            <div className="px-4 pb-2">
                                                {result.matches.slice(0, 20).map((match, mIdx) => (
                                                    <div
                                                        key={mIdx}
                                                        className="flex items-start space-x-3 py-1 text-xs font-mono"
                                                    >
                                                        <span className="text-gray-600 w-8 text-right flex-shrink-0">{match.line_number}</span>
                                                        <span className="text-gray-400 break-all">{highlight(match.content)}</span>
                                                    </div>
                                                ))}
                                                {result.matches.length > 20 && (
                                                    <p className="text-[10px] text-gray-600 mt-1 pl-11">
                                                        ...and {result.matches.length - 20} more matches
                                                    </p>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default GlobalSearch;
