"use client";

import { Moon, Sun } from "lucide-react";
import { useState, useEffect } from "react";

export function ThemeToggle() {
    const [isDark, setIsDark] = useState(true);

    useEffect(() => {
        // Check for saved preference
        const saved = localStorage.getItem("theme");
        if (saved) {
            setIsDark(saved === "dark");
        }
    }, []);

    const toggleTheme = () => {
        const newTheme = !isDark;
        setIsDark(newTheme);
        localStorage.setItem("theme", newTheme ? "dark" : "light");
        // For now, just toggle the state. Full theme implementation would require CSS variables
        document.documentElement.classList.toggle("light-mode", !newTheme);
    };

    return (
        <button
            onClick={toggleTheme}
            className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 hover:bg-slate-700 rounded-lg border border-slate-700 transition"
            title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
            {isDark ? (
                <>
                    <Sun className="h-4 w-4 text-amber-400" />
                    <span className="text-sm text-slate-300">Light</span>
                </>
            ) : (
                <>
                    <Moon className="h-4 w-4 text-blue-400" />
                    <span className="text-sm text-slate-300">Dark</span>
                </>
            )}
        </button>
    );
}
