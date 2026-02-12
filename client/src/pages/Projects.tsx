import { useState, useEffect } from 'react';
import { Plus, Trash2, FolderOpen, HardDrive, Clock, FileText, Zap, Monitor, Search } from 'lucide-react';
import axios from 'axios';
import { Project, ProjectCreate } from '../types';
import { useNavigate } from 'react-router-dom';
import ConfirmationModal from '../components/ui/ConfirmationModal';

const API_URL = 'http://localhost:8000/api';

const Projects = () => {
    const navigate = useNavigate();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreateOpen, setCreateOpen] = useState(false);
    const [newProject, setNewProject] = useState<ProjectCreate>({ name: '', path: '' });
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [deleteId, setDeleteId] = useState<number | null>(null);

    const fetchProjects = async () => {
        try {
            const res = await axios.get(`${API_URL}/projects/`);
            setProjects(res.data);
            setError(null);
        } catch (err) {
            console.error(err);
            setError("Failed to fetch projects. Is the backend running?");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProjects();
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await axios.post(`${API_URL}/projects/`, newProject);
            setCreateOpen(false);
            setNewProject({ name: '', path: '' });
            fetchProjects();
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to create project");
        }
    };

    const handleCreateTemp = async () => {
        try {
            await axios.post(`${API_URL}/projects/`, { name: 'temp', is_temp: true });
            fetchProjects();
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to create temp project");
        }
    };

    const handleDeleteClick = (id: number, e: React.MouseEvent) => {
        e.stopPropagation();
        setDeleteId(id);
    };

    const confirmDelete = async () => {
        if (deleteId === null) return;
        try {
            await axios.delete(`${API_URL}/projects/${deleteId}`);
            fetchProjects();
        } catch (err: any) {
            alert(err.response?.data?.detail || "Failed to delete project");
        }
    };

    const formatBytes = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const filtered = projects.filter(p =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="p-8 h-full overflow-y-auto">
            {/* Header */}
            <div className="flex justify-between items-start mb-8">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
                        Projects
                    </h1>
                    <p className="text-gray-500 text-sm mt-1">Manage your reconnaissance scopes</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleCreateTemp}
                        className="flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-surface border border-accent/30 text-accent hover:bg-accent/10 transition-all text-sm font-medium"
                    >
                        <Zap size={16} />
                        <span>Temp Project</span>
                    </button>
                    <button
                        onClick={() => setCreateOpen(true)}
                        className="flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-primary hover:bg-primary/80 text-white transition-all shadow-lg shadow-primary/20 text-sm font-medium"
                    >
                        <Plus size={16} />
                        <span>New Project</span>
                    </button>
                </div>
            </div>

            {/* Search & Stats Bar */}
            <div className="flex items-center justify-between mb-6">
                <div className="relative w-72">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                    <input
                        type="text"
                        placeholder="Search projects..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-surface border border-border rounded-lg py-2 pl-9 pr-4 text-sm focus:border-primary outline-none transition-colors"
                    />
                </div>
                <span className="text-xs text-gray-500">{projects.length} project{projects.length !== 1 ? 's' : ''}</span>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg text-sm flex items-center justify-between">
                    <span>{error}</span>
                    <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300 ml-4 text-xs">Dismiss</button>
                </div>
            )}

            {/* Content */}
            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="skeleton h-48 rounded-xl" />
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {filtered.map((proj) => (
                        <div
                            key={proj.id}
                            onClick={() => navigate(`/projects/${proj.id}`)}
                            className="group p-5 rounded-xl bg-surface border border-border hover:border-primary/40 transition-all cursor-pointer relative overflow-hidden"
                        >
                            {/* Hover Glow */}
                            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

                            {/* Delete */}
                            <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                                <button
                                    onClick={(e) => handleDeleteClick(proj.id, e)}
                                    className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                                >
                                    <Trash2 size={14} />
                                </button>
                            </div>

                            {/* Header Row */}
                            <div className="flex items-center justify-between mb-3 relative">
                                <div className="flex items-center space-x-3">
                                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                                        <FolderOpen size={18} />
                                    </div>
                                    <div>
                                        <h2 className="text-base font-semibold group-hover:text-primary transition-colors truncate max-w-[180px]">
                                            {proj.name}
                                        </h2>
                                        <p className="text-gray-600 text-[10px] font-mono truncate max-w-[180px]">
                                            {proj.path}
                                        </p>
                                    </div>
                                </div>
                                {proj.description === "Temporary Project" && (
                                    <span className="px-2 py-0.5 text-[10px] bg-accent/10 text-accent border border-accent/20 rounded-full font-medium">
                                        Temp
                                    </span>
                                )}
                            </div>

                            {/* Stats */}
                            <div className="flex items-center gap-4 pt-3 border-t border-white/5 text-gray-500 text-xs">
                                <div className="flex items-center space-x-1.5">
                                    <FileText size={12} />
                                    <span>{proj.stats?.file_count || 0} files</span>
                                </div>
                                <div className="flex items-center space-x-1.5">
                                    <HardDrive size={12} />
                                    <span>{formatBytes(proj.stats?.total_size_bytes || 0)}</span>
                                </div>
                                <div className="flex items-center space-x-1.5 ml-auto">
                                    <Clock size={12} />
                                    <span>{proj.created_at ? new Date(proj.created_at).toLocaleDateString() : 'N/A'}</span>
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Empty State */}
                    {filtered.length === 0 && (
                        <div className="col-span-full py-16 text-center border border-dashed border-border rounded-xl">
                            <div className="mx-auto w-14 h-14 bg-surface rounded-full flex items-center justify-center mb-4 border border-border">
                                <Monitor size={24} className="text-gray-600" />
                            </div>
                            <h3 className="text-lg font-medium text-gray-400">
                                {searchQuery ? 'No matching projects' : 'No projects yet'}
                            </h3>
                            <p className="text-gray-600 text-sm mt-1">
                                {searchQuery ? 'Try a different search term' : 'Create a new project to get started'}
                            </p>
                        </div>
                    )}
                </div>
            )}

            {/* Create Modal */}
            {isCreateOpen && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-surface border border-white/10 p-8 rounded-2xl w-full max-w-md shadow-2xl">
                        <h2 className="text-xl font-bold mb-6">Create New Project</h2>
                        <form onSubmit={handleCreate}>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Project Name</label>
                                    <input
                                        type="text"
                                        required
                                        value={newProject.name}
                                        onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                                        className="w-full bg-background border border-border rounded-lg p-3 text-white focus:border-primary outline-none transition-colors text-sm"
                                        placeholder="e.g. BugBounty-Target"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Custom Path (Optional)</label>
                                    <input
                                        type="text"
                                        value={newProject.path}
                                        onChange={(e) => setNewProject({ ...newProject, path: e.target.value })}
                                        className="w-full bg-background border border-border rounded-lg p-3 text-white focus:border-primary outline-none transition-colors text-sm font-mono"
                                        placeholder="/home/user/projects/my-target"
                                    />
                                </div>
                            </div>
                            <div className="flex justify-end space-x-3 mt-8">
                                <button
                                    type="button"
                                    onClick={() => setCreateOpen(false)}
                                    className="px-5 py-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors text-sm"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-5 py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-white font-medium transition-colors text-sm"
                                >
                                    Create Project
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <ConfirmationModal
                isOpen={deleteId !== null}
                onClose={() => setDeleteId(null)}
                onConfirm={confirmDelete}
                title="Delete Project?"
                message="This action will permanently remove all project data."
                confirmText="Delete"
            />
        </div>
    );
};

export default Projects;
