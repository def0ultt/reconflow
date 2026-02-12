import { Save, Server, FolderOpen, Key, Globe } from 'lucide-react';

const Settings = () => {
    return (
        <div className="p-8 h-full overflow-y-auto">
            <div className="max-w-2xl">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
                        Settings
                    </h1>
                    <p className="text-gray-500 text-sm mt-1">Global configuration for ReconFlow</p>
                </div>

                <div className="space-y-5">
                    {/* API Config */}
                    <SettingsSection
                        icon={Server}
                        title="API Configuration"
                    >
                        <SettingsField
                            label="Backend URL"
                            defaultValue="http://localhost:8000"
                            placeholder="http://localhost:8000"
                        />
                    </SettingsSection>

                    {/* Environment */}
                    <SettingsSection
                        icon={FolderOpen}
                        title="Environment"
                    >
                        <SettingsField
                            label="Default Project Path"
                            defaultValue="/home/defaut/reconflow/projects"
                            placeholder="/path/to/projects"
                            mono
                        />
                    </SettingsSection>

                    {/* API Keys */}
                    <SettingsSection
                        icon={Key}
                        title="API Keys"
                    >
                        <SettingsField
                            label="Shodan API Key"
                            defaultValue=""
                            placeholder="Enter your Shodan API key"
                            type="password"
                        />
                        <SettingsField
                            label="SecurityTrails API Key"
                            defaultValue=""
                            placeholder="Enter your SecurityTrails API key"
                            type="password"
                        />
                    </SettingsSection>

                    {/* Tool Paths */}
                    <SettingsSection
                        icon={Globe}
                        title="Tool Paths"
                    >
                        <SettingsField
                            label="Nuclei Binary"
                            defaultValue="/usr/local/bin/nuclei"
                            placeholder="/path/to/nuclei"
                            mono
                        />
                        <SettingsField
                            label="Subfinder Binary"
                            defaultValue="/usr/local/bin/subfinder"
                            placeholder="/path/to/subfinder"
                            mono
                        />
                    </SettingsSection>

                    {/* Save Button */}
                    <button className="flex items-center space-x-2 px-6 py-2.5 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors text-sm font-medium shadow-lg shadow-primary/20">
                        <Save size={16} />
                        <span>Save Changes</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

/* ---- Reusable Section ---- */
const SettingsSection = ({ icon: Icon, title, children }: { icon: any, title: string, children: React.ReactNode }) => (
    <div className="p-5 bg-surface rounded-xl border border-border">
        <div className="flex items-center space-x-2 mb-4">
            <Icon size={16} className="text-primary" />
            <h3 className="text-sm font-semibold text-gray-200">{title}</h3>
        </div>
        <div className="space-y-4">
            {children}
        </div>
    </div>
);

/* ---- Reusable Field ---- */
const SettingsField = ({ label, defaultValue, placeholder, type = 'text', mono = false }: {
    label: string, defaultValue: string, placeholder: string, type?: string, mono?: boolean
}) => (
    <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wider">{label}</label>
        <input
            type={type}
            defaultValue={defaultValue}
            placeholder={placeholder}
            className={`w-full bg-background border border-border rounded-lg p-2.5 text-sm focus:border-primary outline-none transition-colors ${mono ? 'font-mono' : ''}`}
        />
    </div>
);

export default Settings;
