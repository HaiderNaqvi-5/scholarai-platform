"use client";

import { motion } from "framer-motion";
import { StatusBadge } from "@/components/ui/status-badge";
import { Activity, Star, Target } from "lucide-react";

type PulseHeaderProps = {
  name?: string;
  savedCount: number;
  profileReady: boolean;
};

export function PulseHeader({ name, savedCount, profileReady }: PulseHeaderProps) {
  return (
    <header className="mb-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <motion.div 
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3 mb-2"
          >
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-bold uppercase tracking-widest text-neutral-400">
              ScholarAI Pulse — Live
            </span>
          </motion.div>
          
          <h1 className="text-5xl font-semibold tracking-tight text-neutral-900 leading-tight">
            {name ? `Hello, ${name.split(' ')[0]}.` : "Your Workspace."}
          </h1>
        </div>

        <div className="flex gap-4">
          <MetricBadge 
            icon={<Star size={14} />} 
            label="Shortlist" 
            value={savedCount.toString()} 
            delay={0.1}
          />
          <MetricBadge 
            icon={<Target size={14} />} 
            label="Profile" 
            value={profileReady ? "Ready" : "Syncing"} 
            delay={0.2}
            color={profileReady ? "emerald" : "cobalt"}
          />
        </div>
      </div>
      
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mt-8 flex flex-wrap items-center gap-3 text-sm text-neutral-500"
      >
        <Activity size={16} className="text-cobalt-600" />
        <span>Optimization active:</span>
        <StatusBadge label="Grounded RAG" variant="validated" />
        <StatusBadge label="XGBoost Reranking" variant="generated" />
      </motion.div>
    </header>
  );
}

function MetricBadge({ icon, label, value, delay, color = "neutral" }: { 
  icon: React.ReactNode; 
  label: string; 
  value: string; 
  delay: number;
  color?: "neutral" | "emerald" | "cobalt";
}) {
  const colorClasses = {
    neutral: "text-neutral-400",
    emerald: "text-emerald-500",
    cobalt: "text-cobalt-600"
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.5 }}
      className="glass-surface px-6 py-4 rounded-2xl flex flex-col gap-1 min-w-[140px]"
    >
      <div className={`flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider ${colorClasses[color]}`}>
        {icon}
        {label}
      </div>
      <div className="text-2xl font-semibold text-neutral-800">
        {value}
      </div>
    </motion.div>
  );
}
