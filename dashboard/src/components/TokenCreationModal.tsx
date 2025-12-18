"use client";

import { useState } from "react";
import { Plus, X, Loader2, Key, Mail, Clock, Globe, Shield } from "lucide-react";

interface TokenCreationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (data: TokenCreationData) => Promise<void>;
}

interface TokenCreationData {
    contractor_email: string;
    credential_name: string;
    target_url: string;
    duration_hours: number;
    allowed_ip?: string;
}

export function TokenCreationModal({ isOpen, onClose, onSubmit }: TokenCreationModalProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [formData, setFormData] = useState<TokenCreationData>({
        contractor_email: "",
        credential_name: "",
        target_url: "",
        duration_hours: 24,
    });

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            await onSubmit(formData);
            setFormData({ contractor_email: "", credential_name: "", target_url: "", duration_hours: 24 });
            onClose();
        } catch (err: any) {
            setError(err.message || "Failed to create token");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-700">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                            <Key className="h-5 w-5 text-white" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Create Access Token</h3>
                            <p className="text-sm text-slate-400">Grant temporary access to a contractor</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-700 rounded-lg transition">
                        <X className="h-5 w-5 text-slate-400" />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            <Mail className="inline h-4 w-4 mr-2" />
                            Contractor Email
                        </label>
                        <input
                            type="email"
                            value={formData.contractor_email}
                            onChange={(e) => setFormData({ ...formData, contractor_email: e.target.value })}
                            placeholder="contractor@example.com"
                            required
                            className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            <Key className="inline h-4 w-4 mr-2" />
                            Credential Name
                        </label>
                        <input
                            type="text"
                            value={formData.credential_name}
                            onChange={(e) => setFormData({ ...formData, credential_name: e.target.value })}
                            placeholder="e.g., Shopify Admin Access"
                            required
                            className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            <Globe className="inline h-4 w-4 mr-2" />
                            Target URL
                        </label>
                        <input
                            type="url"
                            value={formData.target_url}
                            onChange={(e) => setFormData({ ...formData, target_url: e.target.value })}
                            placeholder="https://admin.shopify.com"
                            required
                            className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            <Clock className="inline h-4 w-4 mr-2" />
                            Access Duration
                        </label>
                        <select
                            value={formData.duration_hours}
                            onChange={(e) => setFormData({ ...formData, duration_hours: parseInt(e.target.value) })}
                            className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        >
                            <option value={1}>1 hour</option>
                            <option value={2}>2 hours</option>
                            <option value={4}>4 hours</option>
                            <option value={8}>8 hours</option>
                            <option value={24}>24 hours</option>
                            <option value={48}>48 hours</option>
                            <option value={72}>72 hours</option>
                            <option value={168}>1 week</option>
                            <option value={168}>1 week</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            <Shield className="inline h-4 w-4 mr-2" />
                            IP Whitelist (Optional)
                        </label>
                        <input
                            type="text"
                            value={formData.allowed_ip || ""}
                            onChange={(e) => setFormData({ ...formData, allowed_ip: e.target.value })}
                            placeholder="e.g. 203.0.113.1"
                            className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        />
                    </div>

                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <div className="flex gap-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-4 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium rounded-lg hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 transition flex items-center justify-center gap-2"
                        >
                            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                            Create Token
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
