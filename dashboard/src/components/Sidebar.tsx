import {
    PieChart,
    MonitorPlay,
    Key,
    Activity,
    ShieldAlert,
    Users,
    FileText
} from "lucide-react";

interface SidebarProps {
    activeTab: string;
    onChange: (tab: any) => void;
    userEmail?: string | null;
}

export function Sidebar({ activeTab, onChange, userEmail }: SidebarProps) {
    const menuItems = [
        { id: "analytics", label: "Analytics", icon: PieChart },
        { id: "sessions", label: "Sessions", icon: MonitorPlay },
        { id: "tokens", label: "Tokens", icon: Key },
        { id: "activity", label: "Activity Logs", icon: Activity },
        { id: "shadowit", label: "Shadow IT", icon: ShieldAlert },
        { id: "contractors", label: "Contractors", icon: Users },
        { id: "logs", label: "Audit Trail", icon: FileText },
    ];

    // Get initials from email
    const getInitials = (email: string | null | undefined) => {
        if (!email) return "US";
        const parts = email.split("@")[0];
        return parts.slice(0, 2).toUpperCase();
    };

    return (
        <div className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 p-4 flex flex-col h-screen fixed left-0 top-0 overflow-y-auto transition-colors duration-200">
            <div className="flex items-center gap-3 px-2 mb-8 mt-2">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center">
                    <Key className="h-5 w-5 text-white" />
                </div>
                <div>
                    <h1 className="font-bold text-lg text-slate-900 dark:text-white leading-tight">Contractor<br /><span className="text-blue-600 dark:text-blue-400">Vault</span></h1>
                </div>
            </div>

            <nav className="space-y-1 flex-1">
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => onChange(item.id)}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${isActive
                                ? "bg-blue-600/10 text-blue-600 dark:text-blue-400 border border-blue-600/20 shadow-sm"
                                : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/50"
                                }`}
                        >
                            <Icon className={`h-4 w-4 ${isActive ? "text-blue-600 dark:text-blue-400" : "text-slate-400 dark:text-slate-500"}`} />
                            {item.label}
                        </button>
                    );
                })}
            </nav>

            <div className="mt-8 pt-4 border-t border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-3 px-2">
                    <div className="h-8 w-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-xs font-bold text-white">
                        {getInitials(userEmail)}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">Logged In</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{userEmail || "Not logged in"}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

