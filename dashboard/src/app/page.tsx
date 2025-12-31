"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shield, Fingerprint, Globe, Key, CheckCircle2, ArrowRight } from "lucide-react";
import Link from "next/link";
// Using the new SVG icon we created
import Icon from "./icon.svg";

export default function LandingPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // If logged in, redirect to dashboard
    const token = localStorage.getItem("auth_token");
    if (token) {
      router.push("/dashboard");
    }
  }, [router]);

  if (!mounted) return null; // Avoid hydration mismatch

  return (
    <div className="min-h-screen bg-slate-950 font-sans text-slate-200 selection:bg-cyan-500/30">
      {/* Navbar */}
      <nav className="border-b border-slate-800 bg-slate-950/80 backdrop-blur fixed w-full z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl text-white tracking-tight">ShadowKey</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium">
            <Link href="#features" className="hover:text-cyan-400 transition-colors">Features</Link>
            <Link href="/docs" className="hover:text-cyan-400 transition-colors">Documentation</Link>
            <Link href="#pricing" className="hover:text-cyan-400 transition-colors">Pricing</Link>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm font-medium hover:text-white transition-colors">Log In</Link>
            <Link href="/register" className="px-4 py-2 bg-white text-slate-950 rounded-full text-sm font-bold hover:bg-cyan-50 transition-colors">
              Get Access
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/20 via-slate-950 to-slate-950 z-0"></div>
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold mb-6">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
            Now in Beta
          </div>
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight tracking-tight">
            Secure Access for <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Zero-Trust Teams</span>
          </h1>
          <p className="text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            Share access to any dashboard without sharing passwords.
            Grant granular, time-limited sessions to contractors and agencies with one click.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/register" className="px-8 py-3.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded-lg shadow-lg shadow-cyan-900/20 transition-all flex items-center gap-2">
              Start Free Trial <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/docs" className="px-8 py-3.5 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-lg border border-slate-700 transition-all">
              Read the Docs
            </Link>
          </div>
        </div>
      </section>

      {/* Features Feature Grid */}
      <section id="features" className="py-24 bg-slate-900/50 border-y border-slate-800">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard
              icon={Fingerprint}
              title="Device Fingerprinting"
              description="Lock sessions to specific devices and OS versions. If a contractor switches laptops, access is revoked instantly."
            />
            <FeatureCard
              icon={Key}
              title="Session Injection"
              description="Our browser extension injects authenticated sessions directly. No passwords are ever copied, pasted, or seen."
            />
            <FeatureCard
              icon={Globe}
              title="Shadow IT Discovery"
              description="Automatically detect when contractors sign up for unauthorized SaaS tools using their company email."
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-slate-800 bg-slate-950 text-center">
        <p className="text-slate-500 text-sm">© 2024 ShadowKey Inc. All rights reserved.</p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, description }: { icon: any, title: string, description: string }) {
  return (
    <div className="p-8 rounded-2xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors">
      <div className="w-12 h-12 rounded-lg bg-slate-900 flex items-center justify-center mb-6">
        <Icon className="w-6 h-6 text-cyan-500" />
      </div>
      <h3 className="text-xl font-bold text-white mb-3">{title}</h3>
      <p className="text-slate-400 leading-relaxed">{description}</p>
    </div>
  );
}
