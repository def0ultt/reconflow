import { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

interface DataTableProps {
    columns: string[];
    rows: Record<string, any>[];
    searchQuery: string;
    isRegex: boolean;
    pageSize?: number;
}

const DataTable = ({ columns, rows, searchQuery, isRegex, pageSize = 50 }: DataTableProps) => {
    const [sortCol, setSortCol] = useState<string | null>(null);
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
    const [page, setPage] = useState(0);

    // Filter rows
    const filteredRows = useMemo(() => {
        if (!searchQuery.trim()) return rows;

        try {
            const pattern = isRegex
                ? new RegExp(searchQuery, 'i')
                : new RegExp(searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');

            return rows.filter(row =>
                columns.some(col => {
                    const val = String(row[col] ?? '');
                    return pattern.test(val);
                })
            );
        } catch {
            return rows;
        }
    }, [rows, columns, searchQuery, isRegex]);

    // Sort rows
    const sortedRows = useMemo(() => {
        if (!sortCol) return filteredRows;
        return [...filteredRows].sort((a, b) => {
            const va = a[sortCol] ?? '';
            const vb = b[sortCol] ?? '';
            const cmp = String(va).localeCompare(String(vb), undefined, { numeric: true });
            return sortDir === 'asc' ? cmp : -cmp;
        });
    }, [filteredRows, sortCol, sortDir]);

    // Paginate
    const totalPages = Math.ceil(sortedRows.length / pageSize);
    const pageRows = sortedRows.slice(page * pageSize, (page + 1) * pageSize);

    // Reset page when filter changes
    useMemo(() => setPage(0), [searchQuery]);

    const handleSort = (col: string) => {
        if (sortCol === col) {
            setSortDir(d => d === 'asc' ? 'desc' : 'asc');
        } else {
            setSortCol(col);
            setSortDir('asc');
        }
    };

    // Highlight matching text
    const highlightMatch = (text: string) => {
        if (!searchQuery.trim()) return text;
        try {
            const pattern = isRegex
                ? new RegExp(`(${searchQuery})`, 'gi')
                : new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            const parts = text.split(pattern);
            return parts.map((part, i) =>
                pattern.test(part)
                    ? <span key={i} className="bg-primary/30 text-primary px-0.5 rounded">{part}</span>
                    : part
            );
        } catch {
            return text;
        }
    };

    if (columns.length === 0) {
        return <div className="p-8 text-center text-gray-500 text-sm">No data to display</div>;
    }

    return (
        <div className="flex flex-col h-full">
            {/* Table */}
            <div className="flex-1 overflow-auto">
                <table className="w-full text-sm">
                    <thead className="sticky top-0 z-10">
                        <tr className="bg-surface border-b border-border">
                            <th className="text-left px-4 py-2.5 text-[10px] text-gray-600 uppercase tracking-wider font-medium w-12">#</th>
                            {columns.map(col => (
                                <th
                                    key={col}
                                    onClick={() => handleSort(col)}
                                    className="text-left px-4 py-2.5 text-[10px] text-gray-500 uppercase tracking-wider font-medium cursor-pointer hover:text-gray-300 transition-colors select-none"
                                >
                                    <div className="flex items-center space-x-1">
                                        <span>{col}</span>
                                        {sortCol === col && (
                                            sortDir === 'asc'
                                                ? <ChevronUp size={12} className="text-primary" />
                                                : <ChevronDown size={12} className="text-primary" />
                                        )}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {pageRows.map((row, idx) => (
                            <tr
                                key={idx}
                                className="border-b border-border/30 hover:bg-white/[0.02] transition-colors"
                            >
                                <td className="px-4 py-2 text-gray-600 text-xs font-mono">
                                    {page * pageSize + idx + 1}
                                </td>
                                {columns.map(col => (
                                    <td key={col} className="px-4 py-2 text-gray-300 font-mono text-xs max-w-[300px] truncate">
                                        {highlightMatch(String(row[col] ?? ''))}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Footer / Pagination */}
            <div className="flex items-center justify-between px-4 py-2.5 border-t border-border bg-surface/50 flex-shrink-0">
                <span className="text-xs text-gray-500">
                    Total: <span className="text-gray-300 font-medium">{sortedRows.length.toLocaleString()}</span>
                    {searchQuery && ` (filtered from ${rows.length.toLocaleString()})`}
                </span>

                {totalPages > 1 && (
                    <div className="flex items-center space-x-1">
                        <button
                            onClick={() => setPage(p => Math.max(0, p - 1))}
                            disabled={page === 0}
                            className="p-1 rounded text-gray-500 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        >
                            <ChevronLeft size={14} />
                        </button>

                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                            let pageNum: number;
                            if (totalPages <= 5) {
                                pageNum = i;
                            } else if (page < 3) {
                                pageNum = i;
                            } else if (page > totalPages - 4) {
                                pageNum = totalPages - 5 + i;
                            } else {
                                pageNum = page - 2 + i;
                            }
                            return (
                                <button
                                    key={pageNum}
                                    onClick={() => setPage(pageNum)}
                                    className={clsx(
                                        "w-7 h-7 rounded text-xs font-medium transition-colors",
                                        page === pageNum
                                            ? "bg-primary/20 text-primary"
                                            : "text-gray-500 hover:text-white hover:bg-white/5"
                                    )}
                                >
                                    {pageNum + 1}
                                </button>
                            );
                        })}

                        <button
                            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                            disabled={page >= totalPages - 1}
                            className="p-1 rounded text-gray-500 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        >
                            <ChevronRight size={14} />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DataTable;
