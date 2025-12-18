"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Key, Shield, AlertTriangle, Monitor, RotateCw, LogOut, User } from "lucide-react";
import { Sidebar } from "../components/Sidebar";
import { StatCard } from "../components/StatCard";
import { DataTable, StatusBadge } from "../components/DataTable";
import { ActivityTimeline } from "../components/ActivityTimeline";
import { ShadowITPanel } from "../components/ShadowITPanel";
import { ContractorsPanel } from "../components/ContractorsPanel";

const API_URL = "https://contractor-vault-production.up.railway.app";

// ===== INTERFACES =====
// (Keeping interfaces here or move totypes.ts - keeping here for simplicity as per previous code)

interface Session {
  id: string;
  name: string;
  target_url: string;
  cookie_count: number;
  created_by: string;
  created_at: string;
}

interface Token {
  id: string;
  token: string;
  credential_id: string;
  credential_name: string | null;
  target_url: string | null;
  contractor_email: string;
  expires_at: string;
  is_revoked: boolean;
  revoked_at: string | null;
  revoked_by: string | null;
  created_at: string;
  created_by: string;
  use_count: number;
  status: "active" | "expired" | "revoked";
}

interface AuditLog {
  id: string;
  actor: string;
  action: string;
  target_resource: string;
  ip_address: string;
  timestamp: string;
  description: string;
}

interface AnalyticsSummary {
  tokens: { total: number; active: number; revoked: number; expired: number };
  credentials: { total: number };
  activity_24h: { grants: number; injections: number; revokes: number };
}

interface TopContractor {
  email: string;
  token_count: number;
  total_uses: number;
}

interface SessionActivity {
  id: string;
  url: string;
  title: string | null;
  transition_type: string | null;
  timestamp: string;
  duration_ms: number | null;
}

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

interface Contractor {
  id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  linked_clients: { id: string; client_name: string; linked_at: string }[];
}

export default function Dashboard() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("analytics");
  const [loading, setLoading] = useState(true);
  const [authChecked, setAuthChecked] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  // Data States
  const [sessions, setSessions] = useState<Session[]>([]);
  const [tokens, setTokens] = useState<Token[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [topContractors, setTopContractors] = useState<TopContractor[]>([]);

  // Feature Specific States
  const [sessionActivities, setSessionActivities] = useState<SessionActivity[]>([]);
  const [selectedTokenForActivity, setSelectedTokenForActivity] = useState<string | null>(null);

  const [detectedSignups, setDetectedSignups] = useState<DetectedSignup[]>([]);
  const [shadowItSummary, setShadowItSummary] = useState<any>(null);

  const [contractors, setContractors] = useState<Contractor[]>([]); // Note: logic mapped from topContractors in this demo

  // Action States
  const [revoking, setRevoking] = useState<string | null>(null);
  const adminEmail = userEmail || "admin@company.com";

  // Auth check on mount
  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    const email = localStorage.getItem("user_email");

    if (!token) {
      router.push("/login");
      return;
    }

    setUserEmail(email);
    setAuthChecked(true);
    fetchData(token);
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_email");
    router.push("/login");
  };

  async function fetchData(authToken?: string) {
    const token = authToken || localStorage.getItem("auth_token");
    if (!token) return;

    const headers = { "Authorization": `Bearer ${token}` };
    setLoading(true);
    try {
      const results = await Promise.allSettled([
        fetch(`${API_URL}/api/sessions/`),
        fetch(`${API_URL}/api/access/tokens`),
        fetch(`${API_URL}/api/audit-log/`),
        fetch(`${API_URL}/api/analytics/summary`),
        fetch(`${API_URL}/api/analytics/top-contractors`),
      ]);

      const [sessionsRes, tokensRes, logsRes, analyticsRes, topRes] = results;

      if (sessionsRes.status === "fulfilled" && sessionsRes.value.ok) setSessions(await sessionsRes.value.json());
      if (tokensRes.status === "fulfilled" && tokensRes.value.ok) setTokens(await tokensRes.value.json());
      if (logsRes.status === "fulfilled" && logsRes.value.ok) setAuditLogs(await logsRes.value.json());
      if (analyticsRes.status === "fulfilled" && analyticsRes.value.ok) setAnalytics(await analyticsRes.value.json());

      const topData = (topRes.status === "fulfilled" && topRes.value.ok) ? await topRes.value.json() : [];
      setTopContractors(topData);

      // Map top contractors to compatible type for ContractorPanel if needed
      setContractors(topData.map((c: any) => ({
        id: c.email,
        email: c.email,
        is_active: true,
        created_at: new Date().toISOString(),
        last_login: null,
        linked_clients: [],
        token_count: c.token_count,
        total_uses: c.total_uses
      })));

      // Fetch Shadow IT safely
      try {
        const shadowRes = await fetch(`${API_URL}/api/email/detections`);
        if (shadowRes.ok) setDetectedSignups(await shadowRes.json());

        const summaryRes = await fetch(`${API_URL}/api/email/dashboard-summary`);
        if (summaryRes.ok) setShadowItSummary(await summaryRes.json());
      } catch (err) {
        console.warn("Shadow IT fetch failed", err);
      }

    } catch (e) {
      console.error("Critical failure fetching data:", e);
    }
    setLoading(false);
  }

  async function fetchActivityForToken(tokenId: string) {
    try {
      const res = await fetch(`${API_URL}/api/activity/${tokenId}`);
      if (res.ok) {
        setSessionActivities(await res.json());
        setSelectedTokenForActivity(tokenId);
      }
    } catch (e) {
      console.error("Failed to fetch activity:", e);
    }
  }

  async function revokeToken(tokenId: string) {
    setRevoking(tokenId);
    try {
      await fetch(`${API_URL}/api/access/revoke/${tokenId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admin_email: adminEmail, reason: "Revoked from dashboard" }),
      });
      await fetchData();
    } catch (e) {
      console.error("Revoke failed:", e);
    }
    setRevoking(null);
  }

  // --- Handlers passed to children ---

  const handleDismissDetection = async (id: string) => {
    try {
      await fetch(`${API_URL}/api/email/detections/dismiss/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admin_email: adminEmail }),
      });
      await fetchData();
    } catch (e) { console.error(e); }
  };

  const handleAddManualDetection = async (email: string, service: string) => {
    try {
      await fetch(`${API_URL}/api/email/detections/manual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contractor_email: email, service_name: service }),
      });
      await fetchData();
    } catch (e) { console.error(e); }
  };

  const handleSendMagicLink = async (email: string) => {
    try {
      const res = await fetch(`${API_URL}/api/contractor/auth/request-magic-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (res.ok) {
        const result = await res.json();
        alert(`Magic link created!\nDemo token: ${result.demo_token}`);
      }
    } catch (e) { console.error(e); }
  };

  // Show loading while checking auth
  if (!authChecked) {
    return (
      <div className="flex min-h-screen bg-slate-950 items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-blue-500/30">
      <Sidebar activeTab={activeTab} onChange={setActiveTab} />

      <main className="flex-1 ml-64 p-8 overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold text-white capitalize">{activeTab}</h2>
            <p className="text-slate-400 text-sm mt-1">
              Management & Overview
            </p>
          </div>
          <div className="flex items-center gap-4">
            {/* User Info */}
            <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 rounded-lg border border-slate-700">
              <User className="w-4 h-4 text-cyan-400" />
              <span className="text-sm text-slate-300">{userEmail}</span>
            </div>

            {/* Refresh */}
            <button
              onClick={() => fetchData()}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-all border border-slate-700 shadow-sm"
            >
              <RotateCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh Data
            </button>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg text-sm transition-all border border-red-500/30"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="space-y-6 animate-in fade-in duration-500">

          {/* Analytics */}
          {activeTab === "analytics" && analytics && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard label="Total Tokens" value={analytics.tokens.total} icon={Key} color="blue" />
                <StatCard label="Active Sessions" value={analytics.tokens.active} icon={Monitor} color="green" />
                <StatCard label="Revoked" value={analytics.tokens.revoked} icon={Shield} color="red" />
                <StatCard label="Expired" value={analytics.tokens.expired} icon={AlertTriangle} color="yellow" />
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
                  <h3 className="font-semibold text-white mb-4">24h System Activity</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-800/50">
                      <span className="text-slate-400 text-sm">Access Granted</span>
                      <span className="text-green-400 font-mono font-bold">{analytics.activity_24h.grants}</span>
                    </div>
                    <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-800/50">
                      <span className="text-slate-400 text-sm">Cookies Injected</span>
                      <span className="text-blue-400 font-mono font-bold">{analytics.activity_24h.injections}</span>
                    </div>
                    <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-800/50">
                      <span className="text-slate-400 text-sm">Access Revoked</span>
                      <span className="text-rose-400 font-mono font-bold">{analytics.activity_24h.revokes}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Sessions */}
          {activeTab === "sessions" && (
            <DataTable
              columns={["Name", "Type", "Cookies", "Created By", "Date"]}
              data={sessions}
              renderRow={(session) => (
                <tr key={session.id} className="hover:bg-slate-800/50 transition-colors">
                  <td className="p-4 font-medium text-white">{session.name}</td>
                  <td className="p-4 text-blue-400 text-sm truncate max-w-[200px]">{session.target_url}</td>
                  <td className="p-4 text-slate-400 font-mono text-xs">{session.cookie_count} cookies</td>
                  <td className="p-4 text-slate-400 text-sm">{session.created_by}</td>
                  <td className="p-4 text-slate-500 text-xs">{new Date(session.created_at).toLocaleString()}</td>
                </tr>
              )}
            />
          )}

          {/* Tokens */}
          {activeTab === "tokens" && (
            <DataTable
              columns={["Contractor", "Credential", "Status", "Expires", "Actions"]}
              data={tokens}
              renderRow={(token) => (
                <tr key={token.id} className="hover:bg-slate-800/50 transition-colors group">
                  <td className="p-4">
                    <div className="text-sm font-medium text-white">{token.contractor_email}</div>
                    <div className="text-xs text-slate-500 font-mono">...{token.token.slice(-6)}</div>
                  </td>
                  <td className="p-4 text-slate-300 text-sm">{token.credential_name || "—"}</td>
                  <td className="p-4"><StatusBadge status={token.status} /></td>
                  <td className="p-4 text-slate-500 text-xs">{new Date(token.expires_at).toLocaleString()}</td>
                  <td className="p-4 flex gap-2">
                    <button
                      onClick={() => {
                        fetchActivityForToken(token.id);
                        setActiveTab("activity");
                      }}
                      className="p-1.5 rounded bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors"
                      title="View Activity"
                    >
                      <Monitor className="h-4 w-4" />
                    </button>
                    {token.status === "active" && (
                      <button
                        onClick={() => revokeToken(token.id)}
                        disabled={revoking === token.id}
                        className="p-1.5 rounded bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-colors disabled:opacity-50"
                        title="Revoke Access"
                      >
                        <Shield className="h-4 w-4" />
                      </button>
                    )}
                  </td>
                </tr>
              )}
            />
          )}

          {/* Activity Logs (Session Recorder) */}
          {activeTab === "activity" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-12rem)]">
              {/* Token Selector Sidebar */}
              <div className="lg:col-span-1 bg-slate-800/30 border border-slate-700/50 rounded-xl overflow-y-auto p-4 custom-scrollbar">
                <h3 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">Select Session</h3>
                <div className="space-y-2">
                  {tokens.map(token => (
                    <button
                      key={token.id}
                      onClick={() => fetchActivityForToken(token.id)}
                      className={`w-full text-left p-3 rounded-lg border transition-all ${selectedTokenForActivity === token.id
                        ? "bg-blue-600/10 border-blue-500/50 text-blue-400"
                        : "bg-slate-800/50 border-slate-700/50 text-slate-400 hover:bg-slate-700/50"
                        }`}
                    >
                      <div className="font-medium text-sm truncate">{token.contractor_email}</div>
                      <div className="flex justify-between mt-1 text-xs opacity-70">
                        <span>...{token.token.slice(-4)}</span>
                        <span>{new Date(token.created_at).toLocaleDateString()}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Timeline View */}
              <div className="lg:col-span-2 h-full">
                <ActivityTimeline
                  activities={sessionActivities}
                  selectedTokenId={selectedTokenForActivity}
                />
              </div>
            </div>
          )}

          {/* Shadow IT */}
          {activeTab === "shadowit" && (
            <ShadowITPanel
              detections={detectedSignups}
              summary={shadowItSummary}
              onDismiss={handleDismissDetection}
              onAddManual={handleAddManualDetection}
            />
          )}

          {/* Contractors */}
          {activeTab === "contractors" && (
            <ContractorsPanel
              contractors={contractors}
              onSendMagicLink={handleSendMagicLink}
              onLinkClient={async () => { /* Placeholder for linking logic */ }}
            />
          )}

          {/* Audit Logs */}
          {activeTab === "logs" && (
            <DataTable
              columns={["Actor", "Action", "Resource", "IP Address", "Timestamp"]}
              data={auditLogs}
              renderRow={(log) => (
                <tr key={log.id} className="hover:bg-slate-800/50">
                  <td className="p-4 font-medium text-slate-200">{log.actor}</td>
                  <td className="p-4">
                    <span className={`text-xs px-2 py-0.5 rounded font-mono ${log.action.includes("REVOKE") ? "bg-rose-500/10 text-rose-400" :
                      log.action.includes("GRANT") ? "bg-emerald-500/10 text-emerald-400" :
                        "bg-blue-500/10 text-blue-400"
                      }`}>{log.action}</span>
                  </td>
                  <td className="p-4 text-slate-400 text-sm truncate max-w-[200px]">{log.target_resource}</td>
                  <td className="p-4 text-slate-500 text-xs font-mono">{log.ip_address}</td>
                  <td className="p-4 text-slate-500 text-xs">{new Date(log.timestamp).toLocaleString()}</td>
                </tr>
              )}
            />
          )}

        </div>
      </main>
    </div>
  );
}
