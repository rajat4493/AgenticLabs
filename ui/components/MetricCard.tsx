"use client";

import { ReactNode } from "react";

type MetricCardProps = {
  label: string;
  value: string;
  sublabel?: string;
  valueClassName?: string;
  children?: ReactNode;
};

export function MetricCard({
  label,
  value,
  sublabel,
  valueClassName,
  children,
}: MetricCardProps) {
  return (
    <div className="flex flex-col gap-1 rounded-2xl border border-slate-800 bg-slate-900/60 px-4 py-3">
      <div className="text-xs font-medium uppercase tracking-[0.16em] text-slate-400">
        {label}
      </div>
      <div className="flex items-baseline justify-between">
        <div
          className={`tabular-nums text-slate-50 ${
            valueClassName ?? "text-lg font-semibold"
          }`}
        >
          {value}
        </div>
      </div>
      {sublabel && (
        <div className="text-xs text-slate-400">{sublabel}</div>
      )}
      {children}
    </div>
  );
}
