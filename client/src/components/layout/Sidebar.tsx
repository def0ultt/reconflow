import { NavLink } from 'react-router-dom';
import { LayoutGrid, Workflow, Settings, ScanSearch, ChevronLeft, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

interface SidebarProps {
    collapsed: boolean;
    onToggle: () => void;
}

const Sidebar = ({ collapsed, onToggle }: SidebarProps) => {
    const navItems = [
        { name: 'Projects', path: '/projects', icon: LayoutGrid },
        { name: 'Modules', path: '/modules', icon: Workflow },
        { name: 'Scans', path: '/scans', icon: ScanSearch },
        { name: 'Settings', path: '/settings', icon: Settings },
    ];

    return (
        <div className="relative flex-shrink-0">
            {/* Sidebar Panel */}
            <div
                className={clsx(
                    "h-screen bg-surface border-r border-border flex flex-col transition-all duration-300 ease-in-out overflow-hidden whitespace-nowrap",
                    collapsed ? "w-0 border-none" : "w-64"
                )}
            >
                {/* Header with Logo */}
                <div className="p-6 border-b border-border flex items-center justify-between min-w-[256px]">
                    <div>
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                            ReconFlow
                        </h1>
                        <p className="text-xs text-gray-400 mt-1">v2.0 (Localhost)</p>
                    </div>
                    <button
                        onClick={onToggle}
                        className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                        title="Collapse Sidebar"
                    >
                        <ChevronLeft size={18} />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4 space-y-2 min-w-[256px]">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) =>
                                clsx(
                                    "flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200",
                                    isActive
                                        ? "bg-primary/20 text-primary border border-primary/30"
                                        : "text-gray-400 hover:bg-white/5 hover:text-white"
                                )
                            }
                        >
                            <item.icon size={20} className="min-w-[20px]" />
                            <span className="font-medium">{item.name}</span>
                        </NavLink>
                    ))}
                </nav>

                {/* User Info */}
                <div className="p-4 border-t border-border min-w-[256px]">
                    <div className="flex items-center space-x-3 px-4 py-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-purple-600 min-w-[32px]"></div>
                        <div>
                            <p className="text-sm font-medium text-white">Local User</p>
                            <p className="text-xs text-green-400">● Online</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Expand Button - visible only when collapsed, sits outside the sidebar */}
            {collapsed && (
                <button
                    onClick={onToggle}
                    className="absolute top-4 -right-10 z-50 p-1.5 rounded-md bg-surface border border-white/10 text-gray-400 hover:text-white hover:bg-white/5 transition-colors shadow-lg"
                    title="Expand Sidebar"
                >
                    <ChevronRight size={16} />
                </button>
            )}
        </div>
    );
};

export default Sidebar;
