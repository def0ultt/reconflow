import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Project } from '../types';
import { LayoutDashboard, Hammer, Settings as SettingsIcon, ChevronRight } from 'lucide-react';
import clsx from 'clsx';
import Modules from './Modules'; // We will use this as the Builder tab

const API_URL = 'http://localhost:8000/api';

const ProjectWorkspace = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();

    // Tab State
    const currentTab = searchParams.get('tab') || 'dashboard';

    // Data State
    const [project, setProject] = useState<Project | null>(null);
    const [loading, setLoading] = useState(true);

    const handleTabChange = (tab: string) => {
        setSearchParams({ tab });
    };

    useEffect(() => {
        const fetchProject = async () => {
            try {
                const res = await axios.get(`${API_URL}/projects/${id}`);
                setProject(res.data);
            } catch (err) {
                console.error("Failed to fetch project", err);
                // navigate('/projects');
            } finally {
                setLoading(false);
            }
        };
        if (id) fetchProject();
    }, [id]);

    if (loading) {
        return <div className="flex justify-center items-center h-full">Loading Project...</div>;
    }

    if (!project) {
        return <div className="text-center p-10 text-red-500">Project Not Found</div>;
    }

    return (
        <div className="flex flex-col h-full bg-[#09090b] text-white overflow-hidden">
            {/* Top Navigation Bar */}
            <div className="h-14 border-b border-white/10 flex items-center px-6 bg-[#0c0c0e]">
                {/* Breadcrumbs / Title */}
                <div className="flex items-center space-x-2 text-sm font-medium text-gray-400 mr-8">
                    <span
                        className="hover:text-white cursor-pointer transition-colors"
                        onClick={() => navigate('/projects')}
                    >
                        Projects
                    </span>
                    <ChevronRight size={14} />
                    <span className="text-white font-bold tracking-wide">{project.name}</span>
                </div>

                {/* Navigation Tabs */}
                <div className="flex space-x-1 h-full items-center">
                    <TabButton
                        active={currentTab === 'dashboard'}
                        onClick={() => handleTabChange('dashboard')}
                        icon={<LayoutDashboard size={16} />}
                        label="Dashboard"
                    />
                    <TabButton
                        active={currentTab === 'builder'}
                        onClick={() => handleTabChange('builder')}
                        icon={<Hammer size={16} />}
                        label="Builder"
                    />
                    <TabButton
                        active={currentTab === 'settings'}
                        onClick={() => handleTabChange('settings')}
                        icon={<SettingsIcon size={16} />}
                        label="Settings"
                    />
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 overflow-hidden relative">
                {currentTab === 'dashboard' && <DashboardView projectId={project.id} />}
                {currentTab === 'builder' && <BuilderWrapper projectId={project.id} />}
                {currentTab === 'settings' && <div className="p-10"><h1>Project Settings</h1><p>Path: {project.path}</p></div>}
            </div>
        </div>
    );
};

const TabButton = ({ active, onClick, icon, label }: any) => (
    <button
        onClick={onClick}
        className={clsx(
            "flex items-center space-x-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all",
            active
                ? "bg-primary/20 text-primary border border-primary/20 shadow-[0_0_10px_rgba(139,92,246,0.2)]"
                : "text-gray-400 hover:text-white hover:bg-white/5"
        )}
    >
        {icon}
        <span>{label}</span>
    </button>
);

// Placeholder for Dashboard
const DashboardView = ({ projectId }: { projectId: string }) => {
    return (
        <div className="p-6 h-full overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Results Dashboard</h2>
            <p className="text-gray-500">Select a module output to view results (Implementation in progress)</p>
        </div>
    );
};

// Wrapper for existing Modules component
const BuilderWrapper = ({ projectId }: { projectId: string }) => {
    // The existing Modules component expects a URL param 'project' or we can just render it.
    // But Modules component parses URL search params 'project' right now.
    // We should probably modify Modules.tsx to accept props or just rely on the fact that we passed ?project={id}
    // Wait, if we use /projects/:id, the Modules component logic of reading `?project=` from URL might fail if 
    // we don't pass it in URL or if Modules.tsx reads query params.

    // Actually, Modules.tsx reads `searchParams.get('project')`.
    // In our new route `/projects/X?tab=builder`, the `project` param is missing.
    // We need to update Modules.tsx or trick it.
    // Better update Modules.tsx to accept prop `projectId`.
    return <Modules projectIdProp={projectId} />;
};

export default ProjectWorkspace;
