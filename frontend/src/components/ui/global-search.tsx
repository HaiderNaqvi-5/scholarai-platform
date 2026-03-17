"use client";

import { useEffect, useState } from "react";
import { Search, Command, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";

export function GlobalSearch() {
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setIsOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm text-neutral-500 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-all group"
      >
        <Search size={14} className="group-hover:text-cobalt-600 transition-colors" />
        <span>Search scholarships...</span>
        <kbd className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium text-neutral-400 bg-white/5 border border-white/10 rounded">
          <Command size={10} />K
        </kbd>
      </button>

      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            />
            
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
              className="relative w-full max-w-xl glass-surface overflow-hidden rounded-2xl shadow-2xl"
            >
              <div className="flex items-center gap-3 p-4 border-b border-white/10">
                <Search size={20} className="text-neutral-400" />
                <input
                  autoFocus
                  placeholder="Type to search scholarships, profile, or prep tools..."
                  className="flex-1 bg-transparent border-none outline-none text-neutral-900 placeholder:text-neutral-500 text-lg"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                        router.push(`/scholarships?q=${e.currentTarget.value}`);
                        setIsOpen(false);
                    }
                  }}
                />
                <button 
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-white/10 rounded-md transition-colors"
                >
                  <X size={18} className="text-neutral-500" />
                </button>
              </div>
              
              <div className="p-4 max-h-[60vh] overflow-y-auto">
                <div className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-4 px-2">
                  Quick Actions
                </div>
                <div className="grid gap-1">
                  <SearchItem 
                    label="View Recommendations" 
                    shortcut="R" 
                    onClick={() => { router.push("/recommendations"); setIsOpen(false); }}
                  />
                  <SearchItem 
                    label="Continue Interview Prep" 
                    shortcut="I" 
                    onClick={() => { router.push("/interview"); setIsOpen(false); }}
                  />
                  <SearchItem 
                    label="Update My Profile" 
                    shortcut="P" 
                    onClick={() => { router.push("/profile"); setIsOpen(false); }}
                  />
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}

function SearchItem({ label, shortcut, onClick }: { label: string; shortcut: string; onClick: () => void }) {
  return (
    <button 
      onClick={onClick}
      className="flex items-center justify-between w-full p-2.5 rounded-xl hover:bg-cobalt-600/10 group transition-all text-left"
    >
      <span className="font-medium text-neutral-700 group-hover:text-cobalt-600 transition-colors">
        {label}
      </span>
      <span className="text-[10px] font-bold text-neutral-300 px-1.5 py-0.5 rounded border border-neutral-200 uppercase">
        {shortcut}
      </span>
    </button>
  );
}
