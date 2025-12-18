"use client";

import { Moon, Sun } from "lucide-react";
import { useState, useEffect } from "react";

export function ThemeToggle() {
    const [isDark, setIsDark] = useState(true);

    useEffect(() => {
        // Check for saved preference or system preference
        const saved = localStorage.getItem("theme");
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

        if (saved === "dark" || (!saved && prefersDark)) {
            setIsDark(true);
            document.documentElement.classList.add("dark");
        } else {
            setIsDark(false);
            document.documentElement.classList.remove("dark");
        }
    }, []);

    const toggleTheme = () => {
        const newTheme = !isDark;
        setIsDark(newTheme);
        localStorage.setItem("theme", newTheme ? "dark" : "light");

        if (newTheme) {
            document.documentElement.classList.add("dark");
        } else {
            document.documentElement.classList.remove("dark");
        }
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
