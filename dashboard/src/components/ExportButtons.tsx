"use client";

import { Download, FileSpreadsheet } from "lucide-react";

interface ExportButtonsProps {
    data: any[];
    filename: string;
    columns: { key: string; label: string }[];
}

export function ExportButtons({ data, filename, columns }: ExportButtonsProps) {
    const exportToCSV = () => {
        if (data.length === 0) {
            alert("No data to export");
            return;
        }

        // Create header row
        const headers = columns.map(col => col.label).join(",");

        // Create data rows
        const rows = data.map(item =>
            columns.map(col => {
                const value = item[col.key];
                // Escape quotes and wrap in quotes if contains comma
                if (value === null || value === undefined) return "";
                const strValue = String(value);
                if (strValue.includes(",") || strValue.includes('"') || strValue.includes("\n")) {
                    return `"${strValue.replace(/"/g, '""')}"`;
                }
                return strValue;
            }).join(",")
        );

        const csv = [headers, ...rows].join("\n");

        // Create download
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `${filename}_${new Date().toISOString().split("T")[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const exportToJSON = () => {
        if (data.length === 0) {
            alert("No data to export");
            return;
        }

        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `${filename}_${new Date().toISOString().split("T")[0]}.json`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="flex gap-2">
            <button
                onClick={exportToCSV}
                className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg text-sm transition border border-emerald-500/30"
                title="Export as CSV"
            >
                <FileSpreadsheet className="h-4 w-4" />
                CSV
            </button>
            <button
                onClick={exportToJSON}
                className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg text-sm transition border border-blue-500/30"
                title="Export as JSON"
            >
                <Download className="h-4 w-4" />
                JSON
            </button>
        </div>
    );
}
