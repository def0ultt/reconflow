import { useState, useCallback, useEffect } from 'react';
import { Type, FileText, ToggleRight, FolderOpen, Layers, Library } from 'lucide-react';
import clsx from 'clsx';
import { InputNodeKind, ToolTemplate } from '../../types';
import ToolLibrary from './ToolLibrary';

interface InputsSidebarProps {
    onDragInputStart: (event: React.DragEvent, kind: InputNodeKind) => void;
    onDragToolStart: (event: React.DragEvent, tool: ToolTemplate) => void;
}

const inputTypes: { kind: InputNodeKind; icon: any; color: string; description: string }[] = [
    { kind: 'string', icon: Type, color: '#a855f7', description: 'Text value' },
    { kind: 'file', icon: FileText, color: '#f97316', description: 'File contents' },
    { kind: 'boolean', icon: ToggleRight, color: '#3b82f6', description: 'True / False' },
    { kind: 'folder', icon: FolderOpen, color: '#22c55e', description: 'Directory path' },
];

const MIN_WIDTH = 240;
const MAX_WIDTH = 600;

const InputsSidebar = ({ onDragInputStart, onDragToolStart }: InputsSidebarProps) => {
    const [activeTab, setActiveTab] = useState<'inputs' | 'library'>('inputs');
    const [width, setWidth] = useState(290);
    const [isResizing, setIsResizing] = useState(false);

    const startResizing = useCallback(() => {
        setIsResizing(true);
    }, []);

    const stopResizing = useCallback(() => {
        setIsResizing(false);
    }, []);

    const resize = useCallback(
        (mouseMoveEvent: MouseEvent) => {
            if (isResizing) {
                const newWidth = mouseMoveEvent.clientX; // Assuming sidebar is on the left
                if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
                    setWidth(newWidth);
                }
            }
        },
        [isResizing]
    );

    useEffect(() => {
        window.addEventListener('mousemove', resize);
        window.addEventListener('mouseup', stopResizing);
        return () => {
            window.removeEventListener('mousemove', resize);
            window.removeEventListener('mouseup', stopResizing);
        };
    }, [resize, stopResizing]);

    return (
        <div
            className="inputs-sidebar relative group/sidebar"
            style={{ width: width }}
        >
            {/* Tabs */}
            <div className="inputs-sidebar__tabs">
                <button
                    onClick={() => setActiveTab('inputs')}
                    className={clsx(
                        'inputs-sidebar__tab',
                        activeTab === 'inputs' && 'inputs-sidebar__tab--active'
                    )}
                >
                    <Layers size={14} />
                    <span>Inputs</span>
                </button>
                <button
                    onClick={() => setActiveTab('library')}
                    className={clsx(
                        'inputs-sidebar__tab',
                        activeTab === 'library' && 'inputs-sidebar__tab--active'
                    )}
                >
                    <Library size={14} />
                    <span>Library</span>
                </button>
            </div>

            {/* Content */}
            <div className="inputs-sidebar__content">
                {activeTab === 'inputs' ? (
                    <div className="p-3 space-y-2">
                        <p className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold px-1 mb-2">
                            Drag to canvas
                        </p>
                        {inputTypes.map(({ kind, icon: Icon, color, description }) => (
                            <div
                                key={kind}
                                draggable
                                onDragStart={(e) => onDragInputStart(e, kind)}
                                className="inputs-sidebar__item"
                                style={{ '--accent-color': color } as React.CSSProperties}
                            >
                                <div
                                    className="inputs-sidebar__item-icon"
                                    style={{ backgroundColor: `${color}18`, color }}
                                >
                                    <Icon size={16} />
                                </div>
                                <div className="min-w-0">
                                    <p className="text-sm font-medium text-gray-200 capitalize">{kind}</p>
                                    <p className="text-[11px] text-gray-500">{description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <ToolLibrary onDragStart={onDragToolStart} />
                )}
            </div>

            {/* Resize Handle */}
            <div
                className={clsx(
                    "absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-primary/50 transition-colors z-50",
                    isResizing && "bg-primary/50"
                )}
                onMouseDown={startResizing}
            />
        </div>
    );
};

export default InputsSidebar;
