"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { 
  ArrowRight, 
  BookOpen, 
  CircleCheck,
  ChevronRight
} from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { apiRequest } from "@/lib/api";
import type { StudentProfile } from "@/lib/types";

const FIELD_OPTIONS = [
  "Data Science",
  "Artificial Intelligence",
  "Analytics",
  "Computer Science",
  "Machine Learning"
];

const COUNTRY_OPTIONS = [
  { value: "CA", label: "Canada", flags: "🇨🇦" },
  { value: "US", label: "USA", flags: "🇺🇸" },
  { value: "PK", label: "Pakistan", flags: "🇵🇰" },
];

export function OnboardingFlow() {
  const router = useRouter();
  const { accessToken, currentUser } = useAuth();
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [profile, setProfile] = useState<StudentProfile>({
    citizenship_country_code: "PK",
    gpa_value: 3.5,
    gpa_scale: 4,
    target_field: "Data Science",
    target_degree_level: "MS",
    target_country_code: "CA",
    language_test_type: "IELTS",
    language_test_score: 7.0,
  });

  const nextStep = () => setStep(s => s + 1);

  const handleComplete = async () => {
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      await apiRequest("/profile", {
        method: "PUT",
        token: accessToken,
        body: JSON.stringify(profile),
      });
      nextStep(); // Move to success step
    } catch (error) {
      console.error("Failed to save profile:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const stepVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 100 : -100,
      opacity: 0,
      scale: 0.95
    }),
    center: {
      x: 0,
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.6,
        ease: [0.16, 1, 0.3, 1] as const
      }
    },
    exit: (direction: number) => ({
      x: direction < 0 ? 100 : -100,
      opacity: 0,
      scale: 1.05,
      transition: {
        duration: 0.4,
        ease: [0.16, 1, 0.3, 1] as const
      }
    })
  };

  return (
    <div className="relative min-h-[400px]">
      <AnimatePresence mode="wait" custom={step}>
        {step === 1 && (
          <motion.div
            key="step1"
            custom={1}
            variants={stepVariants}
            initial="enter"
            animate="center"
            exit="exit"
            className="space-y-8"
          >
            <div className="space-y-2">
              <span className="text-[10px] font-black uppercase tracking-widest text-cobalt-500">Phase 01 · Greeting</span>
              <h2 className="text-3xl font-medium text-white">Welcome, {currentUser?.full_name?.split(' ')[0]}.</h2>
              <p className="text-neutral-500 text-lg font-light">Let&apos;s refine your scholarship trajectory in three minutes.</p>
            </div>
            
            <button 
              onClick={nextStep}
              className="group flex items-center gap-3 px-8 py-4 bg-white text-black rounded-full font-black uppercase tracking-widest text-[10px] hover:scale-105 transition-all shadow-xl"
            >
              Begin Initialization <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div
            key="step2"
            custom={1}
            variants={stepVariants}
            initial="enter"
            animate="center"
            exit="exit"
            className="space-y-8"
          >
            <div className="space-y-2">
              <span className="text-[10px] font-black uppercase tracking-widest text-cobalt-500">Phase 02 · Intent</span>
              <h2 className="text-3xl font-medium text-white">Academic Focus.</h2>
              <p className="text-neutral-500 text-lg font-light">Select your primary field of research.</p>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {FIELD_OPTIONS.map(field => (
                <button
                  key={field}
                  onClick={() => {
                    setProfile(p => ({ ...p, target_field: field }));
                    nextStep();
                  }}
                  className={`flex items-center justify-between p-5 rounded-2xl border transition-all text-left group ${
                    profile.target_field === field 
                    ? 'bg-cobalt-600/10 border-cobalt-600/30 ring-1 ring-cobalt-600/20' 
                    : 'bg-white/[0.02] border-white/5 hover:bg-white/5 hover:border-white/10'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${profile.target_field === field ? 'bg-cobalt-600 text-white' : 'bg-white/5 text-neutral-400'}`}>
                      <BookOpen size={18} />
                    </div>
                    <span className={`text-sm font-medium ${profile.target_field === field ? 'text-white' : 'text-neutral-400'}`}>{field}</span>
                  </div>
                  <ChevronRight size={16} className={`text-neutral-600 group-hover:translate-x-1 transition-transform ${profile.target_field === field ? 'opacity-100' : 'opacity-0'}`} />
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div
            key="step3"
            custom={1}
            variants={stepVariants}
            initial="enter"
            animate="center"
            exit="exit"
            className="space-y-8"
          >
             <div className="space-y-2">
              <span className="text-[10px] font-black uppercase tracking-widest text-cobalt-500">Phase 03 · Destination</span>
              <h2 className="text-3xl font-medium text-white">Global Target.</h2>
              <p className="text-neutral-500 text-lg font-light">Where would you like to conduct your studies?</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
               {COUNTRY_OPTIONS.map(country => (
                 <button
                   key={country.value}
                   onClick={() => setProfile(p => ({ ...p, target_country_code: country.value }))}
                   className={`p-6 rounded-3xl border transition-all text-center flex flex-col items-center gap-4 ${
                     profile.target_country_code === country.value
                     ? 'bg-cobalt-600/10 border-cobalt-600/30'
                     : 'bg-white/[0.02] border-white/5 hover:bg-white/5 hover:border-white/10'
                   }`}
                 >
                   <span className="text-4xl">{country.flags}</span>
                   <span className={`text-xs font-black uppercase tracking-widest ${profile.target_country_code === country.value ? 'text-white' : 'text-neutral-500'}`}>
                     {country.label}
                   </span>
                 </button>
               ))}
            </div>

            <button 
              onClick={nextStep}
              disabled={!profile.target_country_code}
              className="w-full flex items-center justify-center gap-2 px-8 py-5 bg-white text-black rounded-full font-black uppercase tracking-widest text-[10px] hover:scale-[1.02] transition-all"
            >
              Continue Calibration
            </button>
          </motion.div>
        )}

        {step === 4 && (
          <motion.div
            key="step4"
            custom={1}
            variants={stepVariants}
            initial="enter"
            animate="center"
            exit="exit"
            className="space-y-8"
          >
             <div className="space-y-2">
              <span className="text-[10px] font-black uppercase tracking-widest text-cobalt-500">Phase 04 · Merit</span>
              <h2 className="text-3xl font-medium text-white">Academic Merit.</h2>
              <p className="text-neutral-500 text-lg font-light">Precision data for scholarship matching.</p>
            </div>

            <div className="space-y-6">
               <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase tracking-widest text-neutral-600 ml-1">Current GPA (0.00)</label>
                  <input 
                    type="number"
                    step="0.01"
                    value={profile.gpa_value ?? ''}
                    onChange={(e) => setProfile(p => ({ ...p, gpa_value: Number(e.target.value) }))}
                    className="w-full bg-white/[0.03] border border-white/10 rounded-2xl p-6 text-2xl font-light text-white outline-none focus:ring-2 focus:ring-cobalt-600/30 focus:border-cobalt-600/50 transition-all placeholder:text-neutral-800"
                    placeholder="3.80"
                  />
               </div>

               <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <label className="text-[10px] font-black uppercase tracking-widest text-neutral-600 ml-1">Scale</label>
                    <select 
                      value={profile.gpa_scale}
                      onChange={(e) => setProfile(p => ({ ...p, gpa_scale: Number(e.target.value) }))}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-xl p-4 text-sm text-neutral-300 outline-none"
                    >
                      <option value={4}>4.0 Scale</option>
                      <option value={5}>5.0 Scale</option>
                      <option value={10}>10.0 Scale</option>
                    </select>
                  </div>
                  <div className="space-y-3">
                    <label className="text-[10px] font-black uppercase tracking-widest text-neutral-600 ml-1">Degrees</label>
                    <div className="w-full bg-white/5 border border-white/5 rounded-xl p-4 text-xs font-bold text-cobalt-500 text-center uppercase tracking-widest">
                       Master&apos;s (MS)
                    </div>
                  </div>
               </div>
            </div>

            <button 
              onClick={handleComplete}
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 px-8 py-5 bg-cobalt-600 text-white rounded-full font-black uppercase tracking-widest text-[10px] hover:scale-[1.02] transition-all shadow-[0_0_30px_rgba(37,99,235,0.3)]"
            >
              {isSubmitting ? 'Synchronizing...' : 'Finalize Profile'}
            </button>
          </motion.div>
        )}

        {step === 5 && (
          <motion.div
            key="step5"
            custom={1}
            variants={stepVariants}
            initial="enter"
            animate="center"
            exit="exit"
            className="flex flex-col items-center justify-center text-center py-10 space-y-8"
          >
             <motion.div
               initial={{ scale: 0 }}
               animate={{ scale: 1 }}
               transition={{ type: "spring", damping: 12, stiffness: 200, delay: 0.2 }}
               className="w-24 h-24 bg-emerald-500 rounded-full flex items-center justify-center shadow-[0_0_50px_rgba(16,185,129,0.3)]"
             >
                <CircleCheck size={48} className="text-white" />
             </motion.div>

             <div className="space-y-2">
                <h2 className="text-3xl font-medium text-white">Synthesis Complete.</h2>
                <p className="text-neutral-500 text-lg font-light max-w-sm">Your profile is now live. We&apos;ve identified matching scholarships based on your data.</p>
             </div>

             <button 
              onClick={() => router.push('/dashboard')}
              className="flex items-center gap-3 px-10 py-5 bg-white text-black rounded-full font-black uppercase tracking-widest text-[10px] hover:scale-105 transition-all shadow-xl"
            >
              Enter Dashboard <ArrowRight size={14} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Progress Indicator */}
      {step < 5 && (
        <div className="mt-20 flex gap-2 justify-center">
           {[1,2,3,4].map(i => (
             <div 
               key={i} 
               className={`h-1 rounded-full transition-all duration-500 ${step === i ? 'w-8 bg-cobalt-500' : 'w-2 bg-white/10'}`} 
             />
           ))}
        </div>
      )}
    </div>
  );
}
