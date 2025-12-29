import { useState, useEffect } from "react";
import { ShieldCheck, ShieldAlert, Monitor, Smartphone, Globe, AlertTriangle } from "lucide-react";
import { DataTable, StatusBadge } from "./DataTable";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface Device {
    id: string;
    contractor_email: string;
    browser: string;
    os: string;
    device_type: string;
    trust_score: number;
    is_trusted: boolean;
    is_blocked: boolean;
    last_seen: string;
}

export function DevicesPanel() {
    const [devices, setDevices] = useState<Device[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchDevices = async () => {
        try {
            const token = localStorage.getItem("auth_token");
            const res = await fetch(`${API_URL}/api/devices`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setDevices(data.devices || []);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDevices();
    }, []);

    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-emerald-400 bg-emerald-500/10 ring-emerald-500/20";
        if (score >= 50) return "text-amber-400 bg-amber-500/10 ring-amber-500/20";
        return "text-rose-400 bg-rose-500/10 ring-rose-500/20";
    };

    const getDeviceIcon = (type: string) => {
        switch (type) {
            case "desktop": return <Monitor className="h-4 w-4" />;
            case "mobile": return <Smartphone className="h-4 w-4" />;
            default: return <Globe className="h-4 w-4" />;
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-white">Device Trust</h2>
                    <p className="text-slate-400">Monitor and manage trusted devices for Zero Trust access</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-slate-400 text-sm">Trusted Devices</p>
                            <h3 className="text-2xl font-bold text-white mt-1">{devices.filter(d => d.is_trusted).length}</h3>
                        </div>
                        <ShieldCheck className="h-5 w-5 text-emerald-500" />
                    </div>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-slate-400 text-sm">Average Trust Score</p>
                            <h3 className="text-2xl font-bold text-white mt-1">
                                {devices.length > 0 ? Math.round(devices.reduce((acc, d) => acc + d.trust_score, 0) / devices.length) : 0}
                            </h3>
                        </div>
                        <AlertTriangle className="h-5 w-5 text-amber-500" />
                    </div>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-slate-400 text-sm">Blocked</p>
                            <h3 className="text-2xl font-bold text-white mt-1">{devices.filter(d => d.is_blocked).length}</h3>
                        </div>
                        <ShieldAlert className="h-5 w-5 text-rose-500" />
                    </div>
                </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center text-slate-400">Loading devices...</div>
                ) : (
                    <DataTable
                        columns={["Device / OS", "Contractor", "Trust Score", "Status", "Last Seen", "Actions"]}
                        data={devices}
                        renderRow={(device) => (
                            <tr key={device.id} className="hover:bg-slate-700/30 transition-colors border-b border-slate-700/50 last:border-0">
                                <td className="p-4">
                                    <div className="flex items-center gap-3">
                                        <div className="h-8 w-8 rounded bg-slate-800 flex items-center justify-center border border-slate-700 text-slate-400">
                                            {getDeviceIcon(device.device_type)}
                                        </div>
                                        <div>
                                            <div className="font-medium text-white">{device.browser || "Unknown"}</div>
                                            <div className="text-xs text-slate-500">{device.os || "Unknown OS"}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="p-4 text-slate-300">{device.contractor_email}</td>
                                <td className="p-4">
                                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ring-1 ring-inset ${getScoreColor(device.trust_score)}`}>
                                        {device.trust_score}/100
                                    </span>
                                </td>
                                <td className="p-4">
                                    <StatusBadge status={device.is_blocked ? "revoked" : (device.is_trusted ? "active" : "pending")} />
                                </td>
                                <td className="p-4 text-slate-400 text-sm">
                                    {new Date(device.last_seen).toLocaleDateString()}
                                </td>
                                <td className="p-4">
                                    <div className="flex items-center gap-2">
                                        {!device.is_trusted && !device.is_blocked && (
                                            <button className="text-xs bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 px-2 py-1 rounded transition-colors border border-emerald-500/20">
                                                Trust
                                            </button>
                                        )}
                                        {!device.is_blocked ? (
                                            <button className="text-xs bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 px-2 py-1 rounded transition-colors border border-rose-500/20">
                                                Block
                                            </button>
                                        ) : (
                                            <button className="text-xs bg-slate-700 text-slate-300 hover:bg-slate-600 px-2 py-1 rounded transition-colors">
                                                Unblock
                                            </button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        )}
                    />
                )}
            </div>
        </div>
    );
}
