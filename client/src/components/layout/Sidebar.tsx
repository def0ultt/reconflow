import { NavLink } from 'react-router-dom';
import { LayoutGrid, Workflow, Settings, ScanSearch } from 'lucide-react';
import clsx from 'clsx';

interface SidebarProps {
    collapsed: boolean;
}

const Sidebar = ({ collapsed }: SidebarProps) => {
    const navItems = [
        { name: 'Projects', path: '/projects', icon: LayoutGrid },
        { name: 'Modules', path: '/modules', icon: Workflow },
        { name: 'Scans', path: '/scans', icon: ScanSearch },
        { name: 'Settings', path: '/settings', icon: Settings },
    ];

    return (
        <div
            className={clsx(
                "h-screen bg-surface border-r border-border flex flex-col transition-all duration-300 ease-in-out overflow-hidden whitespace-nowrap",
                collapsed ? "w-[0px] border-none" : "w-64"
            )}
        >
            <div className="p-6 border-b border-border">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent opacity-100 transition-opacity duration-300">
                    {collapsed ? '' : 'ReconFlow'}
                </h1>
                <p className={clsx("text-xs text-gray-400 mt-1 transition-opacity", collapsed && "opacity-0")}>
                    v2.0 (Localhost)
                </p>
            </div>

            <nav className="flex-1 p-4 space-y-2">
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
                        <span className={clsx("font-medium transition-opacity duration-200", collapsed && "opacity-0 w-0")}>{item.name}</span>
                    </NavLink>
                ))}
            </nav>

            <div className="p-4 border-t border-border">
                <div className="flex items-center space-x-3 px-4 py-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-purple-600 min-w-[32px]"></div>
                    <div className={clsx("transition-opacity duration-200", collapsed && "opacity-0 hidden")}>
                        <p className="text-sm font-medium text-white">Local User</p>
                        <p className="text-xs text-green-400">● Online</p>
                    </div>
                </div>
            </div>
        </div>
    );
};


export default Sidebar;
