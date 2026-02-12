import { useState, useEffect } from 'react';
import { Plus, Trash2, FolderOpen, HardDrive, Clock, FileText, Zap, Monitor } from 'lucide-react';
import axios from 'axios';
import { Project, ProjectCreate } from '../types';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import ConfirmationModal from '../components/ui/ConfirmationModal';

const API_URL = 'http://localhost:8000/api';

const Projects = () => {
    const navigate = useNavigate();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreateOpen, setCreateOpen] = useState(false);
    const [newProject, setNewProject] = useState<ProjectCreate>({ name: '', path: '' });
    const [error, setError] = useState<string | null>(null);

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

    const [deleteId, setDeleteId] = useState<number | null>(null);

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

    return (
        <div className="p-8 h-full overflow-y-auto">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
                        Projects
                    </h1>
                    <p className="text-gray-400 mt-1">Manage and organize your reconnaissance workflows</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleCreateTemp}
                        className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-surface border border-accent/30 text-accent hover:bg-accent/10 transition-all"
                    >
                        <Zap size={18} />
                        <span>Temp Project</span>
                    </button>
                    <button
                        onClick={() => setCreateOpen(true)}
                        className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary/80 text-white transition-all shadow-lg shadow-primary/20"
                    >
                        <Plus size={20} />
                        <span>New Project</span>
                    </button>
                </div>
            </div>

            {error && (
                <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg">
                    {error}
                </div>
            )}

            {loading ? (
                <div className="flex justify-center items-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {projects.map((proj) => (
                        <div
                            key={proj.id}
                            onClick={() => navigate(`/projects/${proj.id}`)}
                            className="group p-6 rounded-xl bg-surface border border-border hover:border-primary/50 transition-all cursor-pointer relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                    onClick={(e) => handleDeleteClick(proj.id, e)}
                                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-400/10 rounded-full transition-colors"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>

                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 rounded-lg bg-primary/10 text-primary">
                                    <FolderOpen size={24} />
                                </div>
                                {proj.description === "Temporary Project" && (
                                    <span className="px-2 py-1 text-xs bg-accent/10 text-accent border border-accent/20 rounded-full">
                                        Temp
                                    </span>
                                )}
                            </div>

                            <h2 className="text-xl font-semibold mb-2 group-hover:text-primary transition-colors truncate">
                                {proj.name}
                            </h2>
                            <p className="text-gray-500 text-xs mb-4 font-mono truncate">
                                {proj.path}
                            </p>

                            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
                                <div className="flex items-center space-x-2 text-gray-400 text-xs">
                                    <FileText size={14} />
                                    <span>{proj.stats?.file_count || 0} Files</span>
                                </div>
                                <div className="flex items-center space-x-2 text-gray-400 text-xs">
                                    <HardDrive size={14} />
                                    <span>{formatBytes(proj.stats?.total_size_bytes || 0)}</span>
                                </div>
                                <div className="flex items-center space-x-2 text-gray-400 text-xs col-span-2">
                                    <Clock size={14} />
                                    <span>{proj.created_at ? new Date(proj.created_at).toLocaleDateString() : 'N/A'}</span>
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Empty State */}
                    {projects.length === 0 && (
                        <div className="col-span-full py-20 text-center border-2 border-dashed border-gray-700 rounded-xl">
                            <div className="mx-auto w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mb-4">
                                <Monitor size={32} className="text-gray-500" />
                            </div>
                            <h3 className="text-xl font-medium text-gray-300">No Projects Found</h3>
                            <p className="text-gray-500 mt-2">Create a new project to get started</p>
                        </div>
                    )}
                </div>
            )}

            {/* Create Project Modal */}
            {isCreateOpen && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-surface border border-white/10 p-8 rounded-2xl w-full max-w-md shadow-2xl">
                        <h2 className="text-2xl font-bold mb-6">Create New Project</h2>
                        <form onSubmit={handleCreate}>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-1">Project Name</label>
                                    <input
                                        type="text"
                                        required
                                        value={newProject.name}
                                        onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                                        className="w-full bg-background border border-gray-700 rounded-lg p-3 text-white focus:border-primary outline-none transition-colors"
                                        placeholder="e.g. BugBounty-Target"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-1">Custom Path (Optional)</label>
                                    <input
                                        type="text"
                                        value={newProject.path}
                                        onChange={(e) => setNewProject({ ...newProject, path: e.target.value })}
                                        className="w-full bg-background border border-gray-700 rounded-lg p-3 text-white focus:border-primary outline-none transition-colors"

                                    />
                                </div>
                            </div>
                            <div className="flex justify-end space-x-3 mt-8">
                                <button
                                    type="button"
                                    onClick={() => setCreateOpen(false)}
                                    className="px-5 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-5 py-2 rounded-lg bg-primary hover:bg-primary/90 text-white font-medium transition-colors"
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
                message="Are you sure you want to delete this project? This action cannot be undone and will permanently remove all associated files and data."
                confirmText="Delete Project"
            />
        </div>
    );
};

export default Projects;
