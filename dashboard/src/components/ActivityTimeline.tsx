import { ExternalLink, Clock, FolderGit2 } from "lucide-react";

interface SessionActivity {
    id: string;
    url: string;
    title: string | null;
    transition_type: string | null;
    timestamp: string;
    duration_ms: number | null;
}

export function ActivityTimeline({
    activities,
    selectedTokenId,
    onSelectToken
}: {
    activities: SessionActivity[];
    selectedTokenId: string | null;
    onSelectToken?: () => void;
}) {
    if (!selectedTokenId) return null;

    return (
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden shadow-sm h-full flex flex-col">
            <div className="p-4 bg-slate-900/50 border-b border-slate-700/50 flex items-center justify-between">
                <div>
                    <h4 className="font-semibold text-white">Session Activity</h4>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">Token: {selectedTokenId.slice(0, 12)}...</p>
                </div>
                <div className="text-xs bg-blue-500/10 text-blue-400 px-2 py-1 rounded-full border border-blue-500/20">
                    {activities.length} Events
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar relative">
                {activities.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-48 text-slate-500">
                        <FolderGit2 className="h-10 w-10 mb-2 opacity-50" />
                        <p>No activity recorded yet</p>
                    </div>
                ) : (
                    <div className="relative">
                        {/* Vertical line */}
                        <div className="absolute left-3 top-2 bottom-2 w-px bg-slate-700/50"></div>

                        {activities.map((activity, i) => (
                            <div key={activity.id} className="relative pl-10 group mb-6 last:mb-0">
                                {/* Dot */}
                                <div className="absolute left-0 top-1.5 w-6 h-6 rounded-full border-4 border-slate-900 bg-slate-700 group-hover:bg-blue-500 group-hover:border-blue-900/50 transition-colors z-10 flex items-center justify-center">
                                    <div className="w-1.5 h-1.5 rounded-full bg-slate-400 group-hover:bg-white"></div>
                                </div>

                                <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 hover:border-slate-600 transition-colors">
                                    <div className="flex justify-between items-start gap-4">
                                        <h5 className="font-medium text-slate-200 line-clamp-1" title={activity.title || "Untitled"}>
                                            {activity.title || "Untitled"}
                                        </h5>
                                        <span className="text-xs text-slate-500 whitespace-nowrap">
                                            {new Date(activity.timestamp).toLocaleTimeString()}
                                        </span>
                                    </div>

                                    <a
                                        href={activity.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-1.5 text-xs text-blue-400 mt-1 hover:underline truncate"
                                    >
                                        <ExternalLink className="h-3 w-3 flex-shrink-0" />
                                        <span className="truncate">{activity.url}</span>
                                    </a>

                                    <div className="flex items-center gap-4 mt-2 text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                                        {activity.duration_ms && (
                                            <span className="flex items-center gap-1">
                                                <Clock className="h-3 w-3" />
                                                {Math.round(activity.duration_ms / 1000)}s
                                            </span>
                                        )}
                                        {activity.transition_type && (
                                            <span className="bg-slate-700/50 px-1.5 py-0.5 rounded">
                                                {activity.transition_type}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
