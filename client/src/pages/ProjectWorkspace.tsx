import { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Project, Artifact } from '../types';
import {
    LayoutDashboard, Hammer, Settings as SettingsIcon,
    ChevronRight, FileText, HardDrive, FolderOpen,
    Clock, Activity, RefreshCw
} from 'lucide-react';
import clsx from 'clsx';
import Modules from './Modules';
import ArtifactViewer from '../components/dashboard/ArtifactViewer';
import GlobalSearch from '../components/dashboard/GlobalSearch';

const API_URL = 'http://localhost:8000/api';

const ProjectWorkspace = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();

    const currentTab = searchParams.get('tab') || 'dashboard';

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
            } finally {
                setLoading(false);
            }
        };
        if (id) fetchProject();
    }, [id]);

    if (loading) {
        return (
            <div className="flex flex-col justify-center items-center h-full space-y-3">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
                <span className="text-gray-500 text-sm">Loading project...</span>
            </div>
        );
    }

    if (!project) {
        return (
            <div className="flex flex-col justify-center items-center h-full space-y-3">
                <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center">
                    <FolderOpen size={28} className="text-red-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-300">Project Not Found</h3>
                <button
                    onClick={() => navigate('/projects')}
                    className="text-sm text-primary hover:underline"
                >
                    ← Back to Projects
                </button>
            </div>
        );
    }

    const tabs = [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'builder', label: 'Builder', icon: Hammer },
        { id: 'settings', label: 'Settings', icon: SettingsIcon },
    ];

    return (
        <div className="flex flex-col h-full bg-background text-white overflow-hidden">
            {/* Top Navigation Bar */}
            <div className="h-12 border-b border-border flex items-center px-5 bg-surface/50 backdrop-blur-sm flex-shrink-0">
                {/* Breadcrumbs */}
                <div className="flex items-center space-x-2 text-xs font-medium text-gray-500 mr-6">
                    <span
                        className="hover:text-white cursor-pointer transition-colors"
                        onClick={() => navigate('/projects')}
                    >
                        Projects
                    </span>
                    <ChevronRight size={12} />
                    <span className="text-gray-200 font-semibold">{project.name}</span>
                </div>

                {/* Divider */}
                <div className="h-5 w-px bg-border mr-4" />

                {/* Tabs */}
                <div className="flex space-x-1 h-full items-center">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => handleTabChange(tab.id)}
                            className={clsx(
                                "flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all",
                                currentTab === tab.id
                                    ? "bg-primary/15 text-primary border border-primary/20"
                                    : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
                            )}
                        >
                            <tab.icon size={14} />
                            <span>{tab.label}</span>
                        </button>
                    ))}
                </div>

                {/* Right Side Info */}
                <div className="ml-auto flex items-center space-x-3 text-xs text-gray-600">
                    <span className="font-mono">{project.path}</span>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden">
                {currentTab === 'dashboard' && <DashboardView projectId={String(project.id)} />}
                {currentTab === 'builder' && <Modules projectIdProp={String(project.id)} />}
                {currentTab === 'settings' && <ProjectSettingsView project={project} />}
            </div>
        </div>
    );
};

/* ---- Dashboard Tab ---- */
const DashboardView = ({ projectId }: { projectId: string }) => {
    const [artifacts, setArtifacts] = useState<Artifact[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);

    const fetchArtifacts = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API_URL}/projects/${projectId}/artifacts`);
            setArtifacts(res.data);
        } catch (err) {
            console.error("Failed to fetch artifacts", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchArtifacts();
    }, [projectId]);

    // If a file is selected, show the ArtifactViewer
    if (selectedArtifact) {
        return (
            <ArtifactViewer
                projectId={projectId}
                filePath={selectedArtifact.path}
                fileName={selectedArtifact.name}
                onBack={() => setSelectedArtifact(null)}
            />
        );
    }

    const formatBytes = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    const formatDate = (ts: number) => new Date(ts * 1000).toLocaleString();

    const totalSize = artifacts.reduce((sum, a) => sum + a.size, 0);
    const fileTypes = [...new Set(artifacts.map(a => a.type))];

    return (
        <div className="h-full overflow-y-auto p-6 space-y-6">
            {/* Stats Row */}
            <div className="grid grid-cols-4 gap-4">
                <StatCard icon={FileText} label="Total Files" value={String(artifacts.length)} />
                <StatCard icon={HardDrive} label="Total Size" value={formatBytes(totalSize)} />
                <StatCard icon={Activity} label="File Types" value={fileTypes.join(', ') || 'None'} />
                <StatCard icon={Clock} label="Last Updated" value={artifacts.length > 0 ? formatDate(Math.max(...artifacts.map(a => a.modified))) : '—'} />
            </div>

            {/* Global Search */}
            <GlobalSearch
                projectId={projectId}
                artifacts={artifacts}
                onOpenFile={(a) => setSelectedArtifact(a)}
            />

            {/* Artifacts Table */}
            <div className="bg-surface border border-border rounded-xl overflow-hidden">
                <div className="flex items-center justify-between px-5 py-3 border-b border-border">
                    <h3 className="text-sm font-semibold text-gray-300">Project Files</h3>
                    <button
                        onClick={fetchArtifacts}
                        className="flex items-center space-x-1.5 text-xs text-gray-500 hover:text-primary transition-colors"
                    >
                        <RefreshCw size={12} />
                        <span>Refresh</span>
                    </button>
                </div>

                {loading ? (
                    <div className="p-6 space-y-3">
                        {[1, 2, 3].map(i => <div key={i} className="skeleton h-10 rounded-lg" />)}
                    </div>
                ) : artifacts.length === 0 ? (
                    <div className="py-12 text-center">
                        <FolderOpen size={32} className="text-gray-700 mx-auto mb-3" />
                        <p className="text-gray-500 text-sm">No files yet</p>
                        <p className="text-gray-600 text-xs mt-1">Run a module to generate output files</p>
                    </div>
                ) : (
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-border">
                                <th className="text-left px-5 py-2.5 font-medium">Name</th>
                                <th className="text-left px-5 py-2.5 font-medium">Type</th>
                                <th className="text-right px-5 py-2.5 font-medium">Size</th>
                                <th className="text-right px-5 py-2.5 font-medium">Modified</th>
                            </tr>
                        </thead>
                        <tbody>
                            {artifacts.map((artifact, idx) => (
                                <tr
                                    key={idx}
                                    onClick={() => setSelectedArtifact(artifact)}
                                    className="border-b border-border/50 hover:bg-white/[0.02] transition-colors cursor-pointer group"
                                >
                                    <td className="px-5 py-3 font-mono text-gray-200 group-hover:text-primary transition-colors">{artifact.name}</td>
                                    <td className="px-5 py-3">
                                        <span className="px-2 py-0.5 text-[10px] font-medium bg-primary/10 text-primary rounded-full uppercase">
                                            {artifact.type}
                                        </span>
                                    </td>
                                    <td className="px-5 py-3 text-right text-gray-400">{formatBytes(artifact.size)}</td>
                                    <td className="px-5 py-3 text-right text-gray-500 text-xs">{formatDate(artifact.modified)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

/* ---- Stat Card ---- */
const StatCard = ({ icon: Icon, label, value }: { icon: any, label: string, value: string }) => (
    <div className="p-4 bg-surface border border-border rounded-xl">
        <div className="flex items-center space-x-2 text-gray-500 mb-2">
            <Icon size={14} />
            <span className="text-[11px] uppercase tracking-wider font-medium">{label}</span>
        </div>
        <p className="text-lg font-bold text-gray-200 truncate">{value}</p>
    </div>
);

/* ---- Project Settings Tab ---- */
const ProjectSettingsView = ({ project }: { project: Project }) => (
    <div className="h-full overflow-y-auto p-6 max-w-2xl space-y-6">
        <h2 className="text-xl font-bold">Project Settings</h2>
        <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
            <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wider">Project Name</label>
                <p className="text-sm text-gray-200 font-medium">{project.name}</p>
            </div>
            <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wider">Path</label>
                <p className="text-sm text-gray-300 font-mono">{project.path}</p>
            </div>
            <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wider">Created At</label>
                <p className="text-sm text-gray-300">{project.created_at ? new Date(project.created_at).toLocaleString() : 'N/A'}</p>
            </div>
            {project.description && (
                <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wider">Description</label>
                    <p className="text-sm text-gray-300">{project.description}</p>
                </div>
            )}
        </div>
    </div>
);

export default ProjectWorkspace;
