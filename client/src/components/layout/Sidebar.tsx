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
        <div
            className={clsx(
                'h-screen bg-surface border-r border-border flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out overflow-hidden',
                collapsed ? 'w-[70px]' : 'w-64'
            )}
            aria-expanded={!collapsed}
        >
            {/* Header */}
            <div
                className={clsx(
                    'border-b border-border flex items-center transition-all duration-300',
                    collapsed ? 'flex-col gap-2 py-4 px-2' : 'justify-between p-6'
                )}
            >
                {/* Logo: full text when expanded, icon-only when collapsed */}
                {collapsed ? (
                    <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                        <span className="text-white font-bold text-sm">RF</span>
                    </div>
                ) : (
                    <div className="min-w-0">
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent whitespace-nowrap">
                            ReconFlow
                        </h1>
                        <p className="text-xs text-gray-400 mt-1">v2.0 (Localhost)</p>
                    </div>
                )}

                <button
                    onClick={onToggle}
                    className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                    aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                    title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                >
                    {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
            </div>

            {/* Navigation */}
            <nav className={clsx('flex-1 space-y-1 overflow-hidden', collapsed ? 'px-2 py-4' : 'p-4')}>
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            clsx(
                                'group relative flex items-center rounded-lg transition-all duration-200',
                                collapsed
                                    ? 'justify-center p-3'
                                    : 'space-x-3 px-4 py-3',
                                isActive
                                    ? 'bg-primary/20 text-primary border border-primary/30'
                                    : 'text-gray-400 hover:bg-white/5 hover:text-white'
                            )
                        }
                    >
                        <item.icon size={20} className="min-w-[20px] flex-shrink-0" />

                        {/* Label — hidden when collapsed */}
                        {!collapsed && (
                            <span className="font-medium whitespace-nowrap">{item.name}</span>
                        )}

                        {/* Tooltip — shown on hover when collapsed */}
                        {collapsed && (
                            <span className="pointer-events-none absolute left-full ml-3 px-2.5 py-1.5 rounded-md bg-zinc-800 text-white text-xs font-medium shadow-xl border border-white/10 whitespace-nowrap opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 z-50">
                                {item.name}
                            </span>
                        )}
                    </NavLink>
                ))}
            </nav>

            {/* User Info */}
            <div className={clsx('border-t border-border', collapsed ? 'px-2 py-4' : 'p-4')}>
                <div
                    className={clsx(
                        'group relative flex items-center rounded-lg',
                        collapsed ? 'justify-center p-2' : 'space-x-3 px-4 py-3'
                    )}
                >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-purple-600 flex-shrink-0" />

                    {!collapsed && (
                        <div className="min-w-0">
                            <p className="text-sm font-medium text-white whitespace-nowrap">Local User</p>
                            <p className="text-xs text-green-400 whitespace-nowrap">● Online</p>
                        </div>
                    )}

                    {/* Tooltip for user info when collapsed */}
                    {collapsed && (
                        <span className="pointer-events-none absolute left-full ml-3 px-2.5 py-1.5 rounded-md bg-zinc-800 text-white text-xs font-medium shadow-xl border border-white/10 whitespace-nowrap opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 z-50">
                            Local User — Online
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
