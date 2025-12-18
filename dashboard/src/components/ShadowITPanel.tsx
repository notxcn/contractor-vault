import { useState } from "react";
import { Plus, ShieldAlert, CheckCircle, ExternalLink } from "lucide-react";
import { DataTable, StatusBadge } from "./DataTable";

interface DetectedSignup {
    id: string;
    contractor_email: string;
    service_name: string;
    service_domain: string | null;
    email_subject: string;
    email_from: string | null;
    email_date: string;
    detected_at: string;
    status: string;
}

export function ShadowITPanel({
    detections,
    summary,
    onDismiss,
    onAddManual
}: {
    detections: DetectedSignup[];
    summary: any;
    onDismiss: (id: string) => void;
    onAddManual: (email: string, service: string) => Promise<void>;
}) {
    const [newEmail, setNewEmail] = useState("");
    const [newService, setNewService] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async () => {
        if (!newEmail || !newService) return;
        setIsSubmitting(true);
        await onAddManual(newEmail, newService);
        setNewEmail("");
        setNewService("");
        setIsSubmitting(false);
    };

    return (
        <div className="space-y-6">
            {/* Summary Cards */}
            {summary && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-rose-900/20 to-rose-950/10 border border-rose-500/20 rounded-xl p-5">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-rose-400 text-sm font-medium">Active Risks</p>
                                <h3 className="text-3xl font-bold text-white mt-2">{summary.total_active_detections}</h3>
                            </div>
                            <ShieldAlert className="h-6 w-6 text-rose-500" />
                        </div>
                        <div className="mt-4 pt-4 border-t border-rose-500/10">
                            <p className="text-xs text-rose-300">Requires attention</p>
                        </div>
                    </div>

                    <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
                        <h4 className="text-sm font-medium text-slate-400 mb-3">Top Offenders</h4>
                        <div className="space-y-2">
                            {summary.top_contractors?.slice(0, 3).map((c: any, i: number) => (
                                <div key={i} className="flex justify-between items-center text-sm">
                                    <span className="text-slate-200 truncate">{c.email}</span>
                                    <span className="text-rose-400 font-mono bg-rose-500/10 px-1.5 py-0.5 rounded">{c.count}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
                        <h4 className="text-sm font-medium text-slate-400 mb-3">Top Services</h4>
                        <div className="space-y-2">
                            {summary.popular_services?.slice(0, 3).map((s: any, i: number) => (
                                <div key={i} className="flex justify-between items-center text-sm">
                                    <span className="text-slate-200">{s.service}</span>
                                    <span className="text-amber-400 font-mono bg-amber-500/10 px-1.5 py-0.5 rounded">{s.count}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Manual Entry */}
            <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-4 flex gap-3 items-center flex-wrap backdrop-blur-sm">
                <h4 className="font-semibold text-sm text-slate-300 mr-2">Manual Entry:</h4>
                <input
                    type="email"
                    placeholder="Contractor Email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    className="bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors flex-1 min-w-[200px]"
                />
                <input
                    type="text"
                    placeholder="Service (e.g. Canva)"
                    value={newService}
                    onChange={(e) => setNewService(e.target.value)}
                    className="bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors flex-1 min-w-[150px]"
                />
                <button
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
                >
                    <Plus className="h-4 w-4" />
                    Add
                </button>
            </div>

            {/* Table */}
            <DataTable
                columns={["Service", "Contractor", "Status", "Detected", "Actions"]}
                data={detections}
                renderRow={(detection) => (
                    <tr key={detection.id} className="hover:bg-slate-700/30 transition-colors">
                        <td className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="h-8 w-8 rounded bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center font-bold text-slate-400 border border-slate-600/50">
                                    {detection.service_name[0]}
                                </div>
                                <div>
                                    <div className="font-medium text-white">{detection.service_name}</div>
                                    <div className="text-xs text-slate-500 truncate max-w-[150px]">{detection.email_subject}</div>
                                </div>
                            </div>
                        </td>
                        <td className="p-4 text-slate-300">{detection.contractor_email}</td>
                        <td className="p-4">
                            <StatusBadge status={detection.status} />
                        </td>
                        <td className="p-4 text-slate-400 text-sm">{new Date(detection.detected_at).toLocaleDateString()}</td>
                        <td className="p-4">
                            {detection.status === "active" && (
                                <button
                                    onClick={() => onDismiss(detection.id)}
                                    className="bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1.5 rounded text-xs font-medium transition-colors border border-slate-600"
                                >
                                    Dismiss
                                </button>
                            )}
                        </td>
                    </tr>
                )}
            />
        </div>
    );
}
