"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Mail, Lock, Loader2, Shield, ArrowRight, CheckCircle2, Key, Globe, Fingerprint } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function FeatureCard({ icon: Icon, title, description }: { icon: any, title: string, description: string }) {
    return (
        <div className="bg-slate-800/30 border border-slate-700/50 p-6 rounded-xl hover:bg-slate-800/50 transition duration-300">
            <div className="h-10 w-10 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-lg flex items-center justify-center mb-4">
                <Icon className="h-6 w-6 text-cyan-400" />
            </div>
            <h3 className="text-white font-semibold text-lg mb-2">{title}</h3>
            <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
        </div>
    );
}

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/auth/password-login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Store token and redirect
                localStorage.setItem("auth_token", data.token);
                localStorage.setItem("user_email", data.user.email);
                router.push("/");
            } else {
                setError(data.detail || "Invalid email or password");
            }
        } catch (err) {
            setError("Network error. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col">

            {/* Hero Section with Login */}
            <div className="flex-1 flex flex-col lg:flex-row">

                {/* Left: Marketing Copy */}
                <div className="lg:w-1/2 p-8 lg:p-20 flex flex-col justify-center relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-blue-900/20 via-slate-950 to-slate-950 z-0"></div>

                    <div className="relative z-10 max-w-xl mx-auto lg:mx-0">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="h-10 w-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-600/20">
                                <Shield className="h-6 w-6 text-white" />
                            </div>
                            <div className="text-2xl font-bold text-white tracking-tight">ShadowKey</div>
                        </div>
                        <h1 className="text-5xl font-bold text-white mb-6 leading-tight">
                            Secure Access for Your <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300">Extended Workforce</span>
                        </h1>

                        <p className="text-lg text-slate-400 mb-8 leading-relaxed">
                            ShadowKey provides Zero Trust access management for external teams and agencies.
                            Share credentials securely, monitor active sessions, and revoke access instantly.
                        </p>

                        <div className="flex flex-col gap-4">
                            <div className="flex items-center gap-3 text-slate-300">
                                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                                <span>SOC2 Ready Audit Logs</span>
                            </div>
                            <div className="flex items-center gap-3 text-slate-300">
                                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                                <span>Time-limited Access Tokens</span>
                            </div>
                            <div className="flex items-center gap-3 text-slate-300">
                                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                                <span>Extension-based Session Injection</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right: Login Form */}
                <div className="lg:w-1/2 bg-slate-900 border-l border-slate-800 flex items-center justify-center p-8">
                    <div className="w-full max-w-md">
                        <div className="text-center mb-8">
                            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 mb-4 shadow-lg shadow-cyan-500/20">
                                <Shield className="w-6 h-6 text-white" />
                            </div>
                            <h2 className="text-2xl font-bold text-white">Admin Portal</h2>
                        </div>

                        <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-8 shadow-xl">
                            <form onSubmit={handleLogin} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Email address</label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                                        <input
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            placeholder="admin@company.com"
                                            required
                                            className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Password</label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                                        <input
                                            type="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            placeholder="••••••••"
                                            required
                                            className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition"
                                        />
                                    </div>
                                </div>

                                {error && (
                                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                                        {error}
                                    </div>
                                )}

                                <button
                                    type="submit"
                                    disabled={loading || !email || !password}
                                    className="w-full py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium rounded-lg transition shadow-lg shadow-cyan-900/20 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Sign In"}
                                </button>
                            </form>
                        </div>
                        <p className="text-center text-slate-500 text-xs mt-6">
                            Protected by Cloudflare Turnstile • <a href="#" className="hover:text-cyan-400 transition">Privacy Policy</a>
                        </p>
                    </div>
                </div>
            </div>

            {/* Features Grid */}
            <div className="bg-slate-900 border-t border-slate-800 py-20 px-8">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-bold text-white mb-4">Enterprise-Grade Security</h2>
                        <p className="text-slate-400 max-w-2xl mx-auto">
                            Built for modern engineering teams and agencies. Compliance ready out of the box.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <FeatureCard
                            icon={Key}
                            title="Secrets Management"
                            description="Securely store and share API keys, SSH credentials, and database passwords with zero leakage risk."
                        />
                        <FeatureCard
                            icon={Fingerprint}
                            title="Device Trust"
                            description="Enforce Zero Trust policies. Verify device health, OS version, and browser before granting access."
                        />
                        <FeatureCard
                            icon={Globe}
                            title="SaaS Discovery"
                            description="Detect Shadow IT automatically. Identify unsafe tools your contractors are using without approval."
                        />
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="bg-slate-950 py-12 px-8 border-t border-slate-800 text-center">
                <p className="text-slate-500 text-sm">© 2024 ShadowKey Inc. All rights reserved.</p>
            </div>
        </div>
    );
}
