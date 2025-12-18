import { useState } from "react";
import { Link, Mail, Check, Copy } from "lucide-react";
import { DataTable } from "./DataTable";

interface Contractor {
    id: string;
    email: string;
    display_name: string | null;
    is_active: boolean;
    created_at: string;
    last_login: string | null;
    linked_clients: { id: string; client_name: string; linked_at: string }[];
    token_count?: number; // Added from topContractors join in parent
    total_uses?: number;
}

export function ContractorsPanel({
    contractors,
    onSendMagicLink,
    onLinkClient
}: {
    contractors: Contractor[];
    onSendMagicLink: (email: string) => Promise<void>;
    onLinkClient: (email: string, clientName: string) => Promise<void>;
}) {
    const [email, setEmail] = useState("");
    const [sending, setSending] = useState(false);

    const handleSend = async () => {
        if (!email) return;
        setSending(true);
        await onSendMagicLink(email);
        setEmail("");
        setSending(false);
    };

    return (
        <div className="space-y-6">
            {/* Send Magic Link */}
            <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-500/20 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-2">Agency Bridge Invite</h3>
                <p className="text-slate-400 text-sm mb-4">
                    Send a magic link to a contractor. They can use this single identity to access multiple client vaults.
                </p>
                <div className="flex gap-2 max-w-xl">
                    <div className="relative flex-1">
                        <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                        <input
                            type="email"
                            placeholder="Contractor Email Address"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>
                    <button
                        onClick={handleSend}
                        disabled={sending}
                        className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors disabled:opacity-50 shadow-lg shadow-purple-900/20"
                    >
                        {sending ? "Sending..." : "Send Invite"}
                        <Link className="h-4 w-4" />
                    </button>
                </div>
            </div>

            {/* Contractors Table */}
            <DataTable
                columns={["Contractor", "Tokens", "Usage", "Last Login", "Actions"]}
                data={contractors}
                renderRow={(contractor) => (
                    <tr key={contractor.email} className="hover:bg-slate-700/30 transition-colors">
                        <td className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="h-8 w-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-semibold text-slate-300">
                                    {contractor.email.slice(0, 2).toUpperCase()}
                                </div>
                                <div>
                                    <div className="font-medium text-white">{contractor.email}</div>
                                    <div className="text-xs text-slate-500">Joined {new Date(contractor.created_at || Date.now()).toLocaleDateString()}</div>
                                </div>
                            </div>
                        </td>
                        <td className="p-4">
                            <span className="bg-slate-700/50 px-2 py-1 rounded text-xs text-slate-300">
                                {contractor.token_count || 0} active
                            </span>
                        </td>
                        <td className="p-4 text-slate-400 text-sm">{contractor.total_uses || 0}</td>
                        <td className="p-4 text-slate-500 text-sm">
                            {contractor.last_login ? new Date(contractor.last_login).toLocaleDateString() : "Never"}
                        </td>
                        <td className="p-4">
                            <button
                                onClick={() => onLinkClient(contractor.email, "New Client")}
                                className="text-blue-400 hover:text-blue-300 text-sm font-medium hover:underline"
                            >
                                Manage Clients
                            </button>
                        </td>
                    </tr>
                )}
            />
        </div>
    );
}
