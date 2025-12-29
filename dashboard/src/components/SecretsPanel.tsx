import { useState, useEffect } from "react";
import { Plus, Trash2, Edit2, Share2, Key, Database, Terminal, FileCode, CheckCircle, Copy, Loader2, AlertCircle } from "lucide-react";
import { DataTable, StatusBadge } from "./DataTable";
import { Modal } from "./Modal";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface Secret {
    id: string;
    name: string;
    secret_type: string;
    description: string;
    is_active: boolean;
    created_at: string;
    access_count: number;
}

export function SecretsPanel() {
    const [secrets, setSecrets] = useState<Secret[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // Create Modal State
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [newName, setNewName] = useState("");
    const [newType, setNewType] = useState("api_key");
    const [newValue, setNewValue] = useState("");
    const [newDescription, setNewDescription] = useState("");
    const [creating, setCreating] = useState(false);

    // Share Modal State
    const [sharedUrl, setSharedUrl] = useState("");
    const [isShareModalOpen, setIsShareModalOpen] = useState(false);

    const fetchSecrets = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("auth_token");
            const res = await fetch(`${API_URL}/api/secrets`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSecrets(data.secrets || []);
            } else {
                setError("Failed to fetch secrets");
            }
        } catch (err) {
            setError("Network error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSecrets();
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true);
        setError("");

        try {
            const token = localStorage.getItem("auth_token");
            const res = await fetch(`${API_URL}/api/secrets`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: newName,
                    secret_type: newType,
                    value: newValue,
                    description: newDescription,
                    metadata: {}
                })
            });

            if (res.ok) {
                setIsCreateModalOpen(false);
                setNewName("");
                setNewValue("");
                setNewDescription("");
                fetchSecrets();
            } else {
                const data = await res.json();
                setError(data.detail || "Failed to create secret");
            }
        } catch (err) {
            setError("Network error");
        } finally {
            setCreating(false);
        }
    };

    const handleShare = async (secretId: string) => {
        try {
            const token = localStorage.getItem("auth_token");
            const res = await fetch(`${API_URL}/api/secrets/${secretId}/share`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                // Construct share URL (using frontend URL usually, but here simulating backend link or direct access)
                // The backend returns { share_link: "...", token: "..." }
                // Let's assume we show the share_link directly
                setSharedUrl(data.share_link);
                setIsShareModalOpen(true);
            }
        } catch (err) {
            alert("Failed to share secret");
        }
    };

    const getIconForType = (type: string) => {
        switch (type) {
            case "api_key": return <Key className="h-4 w-4 text-emerald-500" />;
            case "database": return <Database className="h-4 w-4 text-blue-500" />;
            case "ssh_key": return <Terminal className="h-4 w-4 text-slate-500" />;
            default: return <FileCode className="h-4 w-4 text-purple-500" />;
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-white">Secrets Management</h2>
                    <p className="text-slate-400">Securely store and share API keys, credentials, and tokens</p>
                </div>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
                >
                    <Plus className="h-4 w-4" />
                    New Secret
                </button>
            </div>

            {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg flex items-center gap-2">
                    <AlertCircle className="h-5 w-5" />
                    {error}
                </div>
            )}

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden">
                {loading ? (
                    <div className="p-8 flex justify-center text-slate-400">Loading secrets...</div>
                ) : (
                    <DataTable
                        columns={["Name", "Type", "Status", "Access Count", "Created", "Actions"]}
                        data={secrets}
                        renderRow={(secret) => (
                            <tr key={secret.id} className="hover:bg-slate-700/30 transition-colors border-b border-slate-700/50 last:border-0">
                                <td className="p-4">
                                    <div className="flex items-center gap-3">
                                        <div className="h-8 w-8 rounded bg-slate-800 flex items-center justify-center border border-slate-700">
                                            {getIconForType(secret.secret_type)}
                                        </div>
                                        <div>
                                            <div className="font-medium text-white">{secret.name}</div>
                                            <div className="text-xs text-slate-500">{secret.description}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="p-4">
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-300">
                                        {secret.secret_type.replace('_', ' ').toUpperCase()}
                                    </span>
                                </td>
                                <td className="p-4">
                                    <StatusBadge status={secret.is_active ? "active" : "inactive"} />
                                </td>
                                <td className="p-4 text-slate-300 font-mono">
                                    {secret.access_count}
                                </td>
                                <td className="p-4 text-slate-400 text-sm">
                                    {new Date(secret.created_at).toLocaleDateString()}
                                </td>
                                <td className="p-4">
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => handleShare(secret.id)}
                                            className="p-1.5 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition-colors"
                                            title="Share"
                                        >
                                            <Share2 className="h-4 w-4" />
                                        </button>
                                        <button className="p-1.5 hover:bg-red-500/10 rounded text-slate-400 hover:text-red-400 transition-colors" title="Delete">
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        )}
                    />
                )}
            </div>

            {/* Create Secret Modal */}
            <Modal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                title="Create New Secret"
                icon={<Key className="h-6 w-6 text-white" />}
            >
                <form onSubmit={handleCreate} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Name</label>
                        <input
                            type="text"
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                            placeholder="e.g. Stripe Prod Key"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Type</label>
                        <select
                            value={newType}
                            onChange={(e) => setNewType(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                        >
                            <option value="api_key">API Key</option>
                            <option value="database">Database</option>
                            <option value="ssh_key">SSH Key</option>
                            <option value="env_var">Environment Variable</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Secret Value</label>
                        <textarea
                            value={newValue}
                            onChange={(e) => setNewValue(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
                            rows={3}
                            placeholder="Enter the secret value..."
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Description</label>
                        <input
                            type="text"
                            value={newDescription}
                            onChange={(e) => setNewDescription(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                            placeholder="Optional description"
                        />
                    </div>
                    <div className="flex gap-3 mt-6">
                        <button
                            type="button"
                            onClick={() => setIsCreateModalOpen(false)}
                            className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={creating}
                            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                        >
                            {creating && <Loader2 className="h-4 w-4 animate-spin" />}
                            Create Secret
                        </button>
                    </div>
                </form>
            </Modal>

            {/* Share Modal */}
            <Modal
                isOpen={isShareModalOpen}
                onClose={() => setIsShareModalOpen(false)}
                title="Secret Shared"
                icon={<CheckCircle className="h-6 w-6 text-white" />}
            >
                <div>
                    <p className="text-slate-400 mb-4">Send this link to the contractor. It will expire in 1 hour.</p>
                    <div className="bg-slate-900 p-3 rounded-lg border border-slate-700 break-all text-sm font-mono text-cyan-400 mb-4">
                        {sharedUrl}
                    </div>
                    <button
                        onClick={() => setIsShareModalOpen(false)}
                        className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
                    >
                        Done
                    </button>
                </div>
            </Modal>
        </div>
    );
}
