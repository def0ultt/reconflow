import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

const AppLayout = () => {
    const [sidebarOpen, setSidebarOpen] = useState(true);

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">
            <Sidebar collapsed={!sidebarOpen} />

            <main className="flex-1 overflow-auto relative flex flex-col">
                {/* Toggle Button - Floating or Integrated? 
                    User asked for "top navigation bar". 
                    Since standard pages might not have one, we can either:
                    1. Put it here absolute.
                    2. Or inject it logic.
                    
                    Let's try absolute positioning in top-left, 
                    ensuring it sits on top of any page headers.
                */}
                <div className="absolute top-3 left-4 z-50">
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="p-1.5 rounded-md bg-surface border border-white/10 text-gray-400 hover:text-white hover:bg-white/5 transition-colors shadow-lg"
                        title={sidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
                    >
                        {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
                    </button>
                </div>

                <div className="flex-1 h-full w-full">
                    <Outlet context={{ sidebarOpen, setSidebarOpen }} />
                </div>
            </main>
        </div>
    );
};

export default AppLayout;
