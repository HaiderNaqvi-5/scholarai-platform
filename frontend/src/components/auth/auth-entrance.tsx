"use client";

import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

type AuthEntranceProps = {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
};

export function AuthEntrance({ children, title, subtitle }: AuthEntranceProps) {
  return (
    <div className="auth-entrance relative overflow-hidden bg-black selection:bg-cobalt-500/30">
      {/* Background Layer */}
      <div className="auth-background pointer-events-none">
        <motion.div 
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
          className="blur-circle blur-circle--1" 
        />
        <motion.div 
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear", delay: -5 }}
          className="blur-circle blur-circle--2" 
        />
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key="auth-card"
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 1.05 }}
          transition={{
            duration: 0.8,
            ease: [0.16, 1, 0.3, 1], // Apple ease
          }}
          className="glass-surface auth-card relative z-10 border-white/5 bg-white/[0.03] shadow-2xl backdrop-blur-3xl ring-1 ring-white/10"
        >
          {/* Subtle Grain Overlay */}
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none mix-blend-overlay bg-[url('https://grainy-gradients.vercel.app/noise.svg')]" />

          <Link 
            href="/" 
            className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-neutral-500 hover:text-white transition-all mb-10 group"
          >
            <ChevronLeft size={14} className="group-hover:-translate-x-1 transition-transform" />
            Back to home
          </Link>

          <header className="mb-10">
            <motion.h1 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="text-5xl font-medium tracking-tight text-white mb-3"
            >
              {title}
            </motion.h1>
            {subtitle && (
              <motion.p 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                className="text-neutral-400 text-lg font-light leading-relaxed"
              >
                {subtitle}
              </motion.p>
            )}
          </header>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            {children}
          </motion.div>

          <footer className="mt-16 pt-8 border-t border-white/5 text-center">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-neutral-600">
                  &copy; {new Date().getFullYear()} ScholarAI · Premium Integrity
              </p>
          </footer>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
