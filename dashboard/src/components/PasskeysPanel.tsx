import { useState } from "react";
import { Fingerprint, Plus, Smartphone, Laptop } from "lucide-react";
import { DataTable, StatusBadge } from "./DataTable";

export function PasskeysPanel() {
    const [passkeys, setPasskeys] = useState([
        {
            id: "1",
            device_name: "MacBook Pro - Touch ID",
            created_at: new Date().toISOString(),
            last_used_at: new Date().toISOString(),
            credential_type: "platform"
        }
    ]);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-white">Passkeys</h2>
                    <p className="text-slate-400">Passwordless authentication using Face ID, Touch ID, or security keys</p>
                </div>
                <button className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors">
                    <Plus className="h-4 w-4" />
                    Register New Passkey
                </button>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden">
                <DataTable
                    columns={["Passkey Name", "Type", "Status", "Created", "Last Used", "Actions"]}
                    data={passkeys}
                    renderRow={(passkey) => (
                        <tr key={passkey.id} className="hover:bg-slate-700/30 transition-colors border-b border-slate-700/50 last:border-0">
                            <td className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="h-8 w-8 rounded bg-slate-800 flex items-center justify-center border border-slate-700 text-blue-400">
                                        <Fingerprint className="h-5 w-5" />
                                    </div>
                                    <div className="font-medium text-white">{passkey.device_name}</div>
                                </div>
                            </td>
                            <td className="p-4">
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-300">
                                    {passkey.credential_type === "platform" ? <Laptop className="h-3 w-3" /> : <Smartphone className="h-3 w-3" />}
                                    {passkey.credential_type}
                                </span>
                            </td>
                            <td className="p-4">
                                <StatusBadge status="active" />
                            </td>
                            <td className="p-4 text-slate-400 text-sm">
                                {new Date(passkey.created_at).toLocaleDateString()}
                            </td>
                            <td className="p-4 text-slate-400 text-sm">
                                {new Date(passkey.last_used_at).toLocaleString()}
                            </td>
                            <td className="p-4">
                                <button className="text-xs bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 px-2 py-1 rounded transition-colors border border-rose-500/20">
                                    Revoke
                                </button>
                            </td>
                        </tr>
                    )}
                />
            </div>
        </div>
    );
}
