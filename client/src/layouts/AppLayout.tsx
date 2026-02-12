import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';

const AppLayout = () => {
    const [sidebarOpen, setSidebarOpen] = useState(true);

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">
            <Sidebar
                collapsed={!sidebarOpen}
                onToggle={() => setSidebarOpen(!sidebarOpen)}
            />
            <main className="flex-1 overflow-auto relative">
                <Outlet context={{ sidebarOpen, setSidebarOpen }} />
            </main>
        </div>
    );
};

export default AppLayout;
