"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Mail, Lock, ArrowRight, AlertCircle } from "lucide-react";

import { isApiError, useAuth } from "@/components/auth/auth-provider";
import { AuthEntrance } from "@/components/auth/auth-entrance";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const nextPath = searchParams.get("next") ?? "/dashboard";

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace(nextPath);
    }
  }, [isAuthenticated, isLoading, nextPath, router]);

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.6,
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 15 },
    show: { 
      opacity: 1, 
      y: 0,
      transition: { ease: [0.16, 1, 0.3, 1] as const, duration: 0.6 }
    }
  };

  return (
    <AuthEntrance
      title="Sign in."
      subtitle="Continue your scholarship journey."
    >
      <motion.form
        variants={container}
        initial="hidden"
        animate="show"
        className="space-y-6"
        data-testid="login-form"
        onSubmit={async (event) => {
          event.preventDefault();
          setError(null);
          setIsSubmitting(true);
          try {
            await login({ email, password });
            router.push(nextPath);
          } catch (caughtError) {
            setError(
              isApiError(caughtError)
                ? caughtError.message
                : "Credential authentication failed.",
            );
          } finally {
            setIsSubmitting(false);
          }
        }}
      >
        <motion.div variants={item} className="space-y-2">
          <label className="text-[10px] font-black uppercase tracking-widest text-neutral-600 ml-1">Identity</label>
          <div className="relative group">
            <Mail className="absolute left-5 top-1/2 -translate-y-1/2 text-neutral-600 group-focus-within:text-cobalt-500 transition-colors" size={18} />
            <input
              className="w-full bg-white/[0.03] border border-white/5 rounded-2xl py-5 pl-14 pr-6 text-sm text-white outline-none focus:ring-2 focus:ring-cobalt-600/20 focus:border-cobalt-600/40 transition-all placeholder:text-neutral-700"
              name="email"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="student@example.ac.ae"
              type="email"
              value={email}
              required
            />
          </div>
        </motion.div>

        <motion.div variants={item} className="space-y-2">
          <div className="flex items-center justify-between ml-1">
             <label className="text-[10px] font-black uppercase tracking-widest text-neutral-600">Access Key</label>
             <Link href="#" className="text-[10px] font-black uppercase tracking-widest text-neutral-500 hover:text-white transition-colors">Forgot?</Link>
          </div>
          <div className="relative group">
            <Lock className="absolute left-5 top-1/2 -translate-y-1/2 text-neutral-600 group-focus-within:text-cobalt-500 transition-colors" size={18} />
            <input
              className="w-full bg-white/[0.03] border border-white/5 rounded-2xl py-5 pl-14 pr-6 text-sm text-white outline-none focus:ring-2 focus:ring-cobalt-600/20 focus:border-cobalt-600/40 transition-all placeholder:text-neutral-700"
              name="password"
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
              type="password"
              value={password}
              required
            />
          </div>
        </motion.div>

        {error && (
          <motion.div 
            variants={item} 
            className="flex items-center gap-3 p-4 bg-coral-600/10 border border-coral-600/20 rounded-xl text-coral-500 text-xs font-medium"
          >
            <AlertCircle size={14} />
            {error}
          </motion.div>
        )}

        <motion.div variants={item} className="pt-4">
          <button 
            className="w-full flex items-center justify-center gap-3 py-5 bg-white text-black rounded-full font-black uppercase tracking-widest text-[10px] hover:scale-[1.02] transition-all shadow-xl group disabled:opacity-50 disabled:scale-100" 
            disabled={isSubmitting} 
            type="submit"
          >
             {isSubmitting ? "Authenticating..." : "Establish Session"}
             <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
          </button>
        </motion.div>

        <motion.p variants={item} className="text-center mt-10 text-[10px] font-black uppercase tracking-widest text-neutral-500">
          New to ScholarAI?{" "}
          <Link href="/signup" className="text-cobalt-500 hover:text-white transition-colors">
            Create account
          </Link>
        </motion.p>
      </motion.form>
    </AuthEntrance>
  );
}
