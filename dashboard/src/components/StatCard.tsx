import { LucideIcon } from "lucide-react";

interface StatCardProps {
    label: string;
    value: number | string;
    icon: LucideIcon;
    color?: "blue" | "green" | "red" | "yellow" | "purple";
    trend?: string;
}

export function StatCard({ label, value, icon: Icon, color = "blue", trend }: StatCardProps) {
    const colors = {
        blue: "from-blue-500/20 to-blue-600/5 text-blue-400 border-blue-500/20",
        green: "from-emerald-500/20 to-emerald-600/5 text-emerald-400 border-emerald-500/20",
        red: "from-rose-500/20 to-rose-600/5 text-rose-400 border-rose-500/20",
        yellow: "from-amber-500/20 to-amber-600/5 text-amber-400 border-amber-500/20",
        purple: "from-violet-500/20 to-violet-600/5 text-violet-400 border-violet-500/20",
    };

    const iconColors = {
        blue: "bg-blue-500/20 text-blue-400",
        green: "bg-emerald-500/20 text-emerald-400",
        red: "bg-rose-500/20 text-rose-400",
        yellow: "bg-amber-500/20 text-amber-400",
        purple: "bg-violet-500/20 text-violet-400",
    };

    return (
        <div className={`relative overflow-hidden rounded-xl border p-5 bg-gradient-to-br backdrop-blur-sm transition-transform hover:scale-[1.02] ${colors[color]}`}>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm font-medium text-slate-400">{label}</p>
                    <h3 className="mt-2 text-2xl font-bold text-white tracking-tight">{value}</h3>
                    {trend && <p className="mt-1 text-xs text-slate-500">{trend}</p>}
                </div>
                <div className={`rounded-lg p-2 ${iconColors[color]}`}>
                    <Icon className="h-5 w-5" />
                </div>
            </div>
        </div>
    );
}
