import { Save } from 'lucide-react';

const Settings = () => {
    return (
        <div className="p-8 max-w-2xl">
            <h1 className="text-3xl font-bold mb-6">Settings</h1>

            <div className="space-y-6">
                <div className="p-6 bg-surface rounded-xl border border-border">
                    <h3 className="text-lg font-semibold mb-4 text-purple-400">API Configuration</h3>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-1 text-gray-300">Backend URL</label>
                            <input type="text" defaultValue="http://localhost:8000" className="w-full bg-background border border-border rounded p-2 focus:border-primary outline-none" />
                        </div>
                    </div>
                </div>

                <div className="p-6 bg-surface rounded-xl border border-border">
                    <h3 className="text-lg font-semibold mb-4 text-purple-400">Environment</h3>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-1 text-gray-300">Default Project Path</label>
                            <input type="text" defaultValue="/home/defaut/reconflow/projects" className="w-full bg-background border border-border rounded p-2 focus:border-primary outline-none" />
                        </div>
                    </div>
                </div>

                <button className="flex items-center space-x-2 px-6 py-2 bg-success text-white rounded hover:bg-green-600 transition-colors">
                    <Save size={18} />
                    <span>Save Changes</span>
                </button>
            </div>
        </div>
    );
};

export default Settings;
