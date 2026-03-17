"use client";

import { motion } from "framer-motion";
import { ChevronLeft } from "lucide-react";
import Link from "next/link";

type PrepLabShellProps = {
  children: React.ReactNode;
  title: string;
  eyebrow: string;
  backHref?: string;
};

export function PrepLabShell({ children, title, eyebrow, backHref = "/dashboard" }: PrepLabShellProps) {
  return (
    <main className="min-h-screen bg-[#050505] text-white relative overflow-hidden selection:bg-cobalt-500/30">
      {/* Immersive Background Layers */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-cobalt-600/10 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-600/5 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay pointer-events-none" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-12">
        <nav className="mb-12 flex items-center justify-between">
          <Link 
            href={backHref}
            className="group flex items-center gap-2 text-sm font-medium text-neutral-400 hover:text-white transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center group-hover:bg-white/10 transition-all">
              <ChevronLeft size={16} />
            </div>
            Back to Hub
          </Link>

          <div className="flex items-center gap-4">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-neutral-500">
              Lab Environment Active
            </span>
          </div>
        </nav>

        <header className="mb-16">
          <motion.p 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-xs font-bold uppercase tracking-[0.2em] text-cobalt-500 mb-4"
          >
            {eyebrow}
          </motion.p>
          <motion.h1 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-6xl font-semibold tracking-tight leading-tight"
          >
            {title}
          </motion.h1>
        </header>

        <motion.div
          initial={{ opacity: 0, scale: 0.99 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          {children}
        </motion.div>
      </div>
    </main>
  );
}
