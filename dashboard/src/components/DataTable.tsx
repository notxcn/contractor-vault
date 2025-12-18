export function StatusBadge({ status }: { status: string }) {
    const styles: Record<string, string> = {
        active: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        expired: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        revoked: "bg-rose-500/10 text-rose-400 border-rose-500/20",
        dismissed: "bg-slate-500/10 text-slate-400 border-slate-500/20",
        manual: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    };

    return (
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status] || "bg-slate-700 text-slate-300 border-slate-600"}`}>
            {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
    );
}

export function DataTable<T>({
    columns,
    data,
    renderRow,
}: {
    columns: string[];
    data: T[];
    renderRow: (item: T) => React.ReactNode;
}) {
    return (
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden shadow-sm">
            <table className="w-full">
                <thead className="bg-slate-900/50 border-b border-slate-700/50">
                    <tr>
                        {columns.map((col) => (
                            <th key={col} className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                {col}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                    {data.map((item) => renderRow(item))}
                    {data.length === 0 && (
                        <tr>
                            <td colSpan={columns.length} className="py-12 text-center text-slate-500">
                                No data found
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}
