"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { SkeletonLine } from "@/components/ui/skeleton";
import { AudioRecorder } from "@/components/interview/audio-recorder";
import { apiRequest } from "@/lib/api";
import type {
  ApiError,
  InterviewCurrentQuestion,
  InterviewSessionSummary,
} from "@/lib/types";
import { PrepLabShell } from "@/components/layout/prep-lab-shell";
import { motion, AnimatePresence } from "framer-motion";
import { Send, History, Award, CheckCircle2, AlertCircle } from "lucide-react";

const LATEST_SESSION_KEY = "scholarai.latest_interview_session";

type InterviewState = {
  isLoading: boolean;
  isStarting: boolean;
  isSubmitting: boolean;
  error: string | null;
  session: InterviewSessionSummary | null;
};

export function InterviewPracticeShell() {
  const { accessToken } = useAuth();
  const [answerText, setAnswerText] = useState("");
  const [audioB64, setAudioB64] = useState<string | null>(null);
  const [state, setState] = useState<InterviewState>({
    isLoading: true,
    isStarting: false,
    isSubmitting: false,
    error: null,
    session: null,
  });

  useEffect(() => {
    if (!accessToken) return;

    const sessionId = localStorage.getItem(LATEST_SESSION_KEY);
    if (!sessionId) {
      setState((current) => ({ ...current, isLoading: false }));
      return;
    }

    let isActive = true;

    const loadSession = async () => {
      try {
        const session = await apiRequest<InterviewSessionSummary>(
          `/interviews/${sessionId}`,
          { token: accessToken },
        );
        if (!isActive) return;
        setState({
          isLoading: false,
          isStarting: false,
          isSubmitting: false,
          error: null,
          session,
        });
      } catch (error) {
        if (!isActive) return;
        localStorage.removeItem(LATEST_SESSION_KEY);
        setState((current) => ({
          ...current,
          isLoading: false,
          error: resolveErrorMessage(error),
          session: null,
        }));
      }
    };

    void loadSession();

    return () => {
      isActive = false;
    };
  }, [accessToken]);

  const currentQuestion = useMemo<InterviewCurrentQuestion | null>(
    () => state.session?.current_question ?? null,
    [state.session],
  );

  const startSession = async () => {
    if (!accessToken) return;

    setState((current) => ({ ...current, isStarting: true, error: null }));
    try {
      const session = await apiRequest<InterviewSessionSummary>("/interviews", {
        method: "POST",
        body: JSON.stringify({ practice_mode: "general" }),
        token: accessToken,
      });
      localStorage.setItem(LATEST_SESSION_KEY, session.session_id);
      setAnswerText("");
      setAudioB64(null);
      setState({
        isLoading: false,
        isStarting: false,
        isSubmitting: false,
        error: null,
        session,
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        isStarting: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  const submitAnswer = async () => {
    if (!accessToken || !state.session) return;

    const hasText = answerText.trim().length >= 50;
    const hasAudio = Boolean(audioB64);

    if (!hasText && !hasAudio) {
      setState((current) => ({
        ...current,
        error: "Voice response or 50+ chars of text required.",
      }));
      return;
    }

    setState((current) => ({ ...current, isSubmitting: true, error: null }));
    try {
      const session = await apiRequest<InterviewSessionSummary>(
        `/interviews/${state.session.session_id}/responses`,
        {
          method: "POST",
          body: JSON.stringify({
            answer_text: hasText ? answerText.trim() : null,
            audio_b64: audioB64,
          }),
          token: accessToken,
        },
      );
      localStorage.setItem(LATEST_SESSION_KEY, session.session_id);
      setAnswerText("");
      setAudioB64(null);
      setState((current) => ({
        ...current,
        isSubmitting: false,
        session,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isSubmitting: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  return (
    <PrepLabShell 
      eyebrow="Simulation Phase"
      title="Interview Hub."
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
        
        {/* Left: Controls & Status */}
        <div className="lg:col-span-4 space-y-6">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass-surface p-8 rounded-[2rem] border-white/5 shadow-2xl"
          >
            <div className="flex items-center justify-between mb-8">
               <h2 className="text-xl font-medium">Session Status</h2>
               {state.session && (
                 <div className="px-3 py-1 bg-cobalt-600/20 text-cobalt-500 rounded-full text-[10px] font-bold uppercase tracking-wider">
                   Active
                 </div>
               )}
            </div>

            {state.isLoading ? (
               <SkeletonLine count={3} />
            ) : state.session ? (
               <div className="space-y-6">
                 <div className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/5">
                    <span className="text-neutral-400 text-sm">Progress</span>
                    <span className="text-lg font-mono font-bold">
                       {state.session.current_question_index} <span className="text-neutral-600">/</span> {state.session.total_questions}
                    </span>
                 </div>
                 <button
                    onClick={() => void startSession()}
                    disabled={state.isStarting}
                    className="w-full py-4 text-sm font-bold text-neutral-400 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl transition-all"
                 >
                   {state.isStarting ? "Re-initializing..." : "Reset Simulation"}
                 </button>
               </div>
            ) : (
               <button
                  onClick={() => void startSession()}
                  className="w-full py-6 bg-cobalt-600 text-white font-bold rounded-2xl shadow-lg shadow-cobalt-600/20 hover:scale-[1.02] transition-all"
               >
                 Start Simulation
               </button>
            )}

            {state.error && (
              <div className="mt-8 flex items-center gap-3 p-4 bg-coral-600/10 border border-coral-600/20 rounded-2xl text-coral-500 text-sm">
                 <AlertCircle size={18} />
                 {state.error}
              </div>
            )}
          </motion.div>

          {/* Feedback Metrics Summary */}
          {state.session?.latest_feedback && (
            <motion.div 
               initial={{ opacity: 0, x: -20 }}
               animate={{ opacity: 1, x: 0 }}
               transition={{ delay: 0.1 }}
               className="glass-surface p-8 rounded-[2rem] border-white/5"
            >
               <h3 className="text-sm font-bold text-neutral-500 uppercase tracking-widest mb-6">Latest Performance</h3>
               <div className="space-y-4">
                  {state.session.latest_feedback.dimensions.map(d => (
                    <div key={d.dimension} className="flex items-center justify-between">
                       <span className="text-sm text-neutral-400 capitalize">{d.dimension}</span>
                       <div className="flex items-center gap-2">
                          <div className="w-24 h-1.5 bg-white/5 rounded-full overflow-hidden">
                             <div 
                                className="h-full bg-cobalt-500 rounded-full" 
                                style={{ width: `${(d.score / 4) * 100}%` }} 
                             />
                          </div>
                          <span className="text-xs font-mono font-bold">{d.score}</span>
                       </div>
                    </div>
                  ))}
               </div>
            </motion.div>
          )}
        </div>

        {/* Right: Immersive Interaction Panel */}
        <div className="lg:col-span-8">
           <AnimatePresence mode="wait">
             {currentQuestion?.question_text ? (
               <motion.div 
                  key="question"
                  initial={{ opacity: 0, scale: 0.98, y: 20 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.98, y: -20 }}
                  className="glass-surface p-12 rounded-[2.5rem] border-white/10 shadow-[0_40px_100px_-20px_rgba(0,0,0,0.5)] bg-white/5"
               >
                  <div className="mb-12">
                     <span className="inline-block px-4 py-1.5 bg-cobalt-600 text-white text-[10px] font-black uppercase tracking-[0.2em] rounded-full mb-6 italic">
                       Phase 0{currentQuestion.question_index}
                     </span>
                     <h2 className="text-4xl font-medium leading-tight text-white/90">
                       {currentQuestion.question_text}
                     </h2>
                  </div>

                  {state.session?.status !== "completed" && (
                    <div className="space-y-8">
                       <AudioRecorder onRecordingComplete={(b64) => setAudioB64(b64)} />
                       
                       <div className="relative group">
                          <textarea
                            value={answerText}
                            onChange={(e) => setAnswerText(e.target.value)}
                            placeholder="Draft your response here (Voice preferred)..."
                            className="w-full bg-white/[0.03] border border-white/5 rounded-[1.5rem] p-6 text-lg text-white/80 placeholder:text-neutral-600 focus:ring-2 focus:ring-cobalt-600/20 focus:bg-white/[0.05] transition-all outline-none resize-none min-h-[200px]"
                          />
                          <div className="absolute bottom-6 right-6 flex items-center gap-4">
                             <span className="text-[10px] font-bold text-neutral-600 uppercase">
                               {answerText.length} Characters
                             </span>
                          </div>
                       </div>

                       <div className="pt-8 border-t border-white/5 flex items-center justify-between">
                          <div className="flex items-center gap-2 text-neutral-500 text-xs">
                             <CheckCircle2 size={14} />
                             Responses are analyzed by GPT neural models
                          </div>
                          <button 
                            disabled={state.isSubmitting}
                            onClick={() => void submitAnswer()}
                            className="group flex items-center gap-3 px-8 py-4 bg-white text-black font-black uppercase tracking-widest text-xs rounded-full hover:scale-105 transition-all disabled:opacity-50"
                          >
                            {state.isSubmitting ? "Processing..." : "Submit Answer"}
                            <Send size={16} className="group-hover:translate-x-1 transition-transform" />
                          </button>
                       </div>
                    </div>
                  )}
               </motion.div>
             ) : (
               <motion.div 
                 key="empty"
                 initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                 className="h-[600px] flex flex-col items-center justify-center text-center p-12 border-2 border-dashed border-white/5 rounded-[3rem]"
               >
                 <div className="w-20 h-20 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-8 text-neutral-300">
                    <Award size={40} />
                 </div>
                 <h2 className="text-3xl font-medium mb-4">Simulation Readiness</h2>
                 <p className="text-neutral-500 max-w-sm mb-12">
                   {state.session?.status === "completed" 
                    ? "Simulation complete. Comprehensive feedback generated below."
                    : "Initializing neural environment. Prepare for behavioral assessment."}
                 </p>
                 {state.session?.status === "completed" && (
                   <button 
                      onClick={() => void startSession()}
                      className="px-10 py-4 bg-white text-black font-bold rounded-full hover:bg-neutral-200 transition-all uppercase tracking-widest text-xs"
                   >
                     New Practice Run
                   </button>
                 )}
               </motion.div>
             )}
           </AnimatePresence>
        </div>
      </div>

      {/* Results Workspace */}
      <AnimatePresence>
         {state.session?.responses.length ? (
           <motion.section 
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-24 pt-24 border-t border-white/5"
           >
              <div className="flex items-center gap-4 mb-12">
                 <History size={24} className="text-cobalt-600" />
                 <h2 className="text-3xl font-medium">Session Transcript</h2>
              </div>

              <div className="space-y-8">
                 {state.session.responses.map((res, i) => (
                    <motion.div 
                       key={i}
                       className="glass-surface p-8 rounded-[2rem] border-white/5 hover:border-white/10 transition-all"
                    >
                       <div className="flex justify-between items-start mb-6">
                          <div>
                             <span className="text-[10px] font-black uppercase tracking-widest text-cobalt-500">Response Analysis {i + 1}</span>
                             <h4 className="text-lg font-medium text-white/90 mt-2">{res.question_text}</h4>
                          </div>
                          <div className="px-4 py-1.5 bg-emerald-500/10 text-emerald-500 rounded-full text-xs font-bold uppercase tracking-widest">
                             {res.overall_band} · {res.overall_score}/4
                          </div>
                       </div>
                       <p className="text-neutral-500 leading-relaxed italic border-l-2 border-white/10 pl-6 mb-8">
                         &quot;{res.answer_text}&quot;
                       </p>
                       <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-white/5">
                          <div>
                             <h5 className="text-[10px] font-black uppercase tracking-widest text-emerald-500 mb-4">Neural Strengths</h5>
                             <ul className="space-y-2">
                                {res.strengths.slice(0, 3).map(s => (
                                  <li key={s} className="text-sm text-neutral-400 flex items-start gap-2">
                                     <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5" />
                                     {s}
                                  </li>
                                ))}
                             </ul>
                          </div>
                          <div>
                             <h5 className="text-[10px] font-black uppercase tracking-widest text-coral-500 mb-4">Growth Vectors</h5>
                             <ul className="space-y-2">
                                {res.improvement_prompts.slice(0, 3).map(s => (
                                  <li key={s} className="text-sm text-neutral-400 flex items-start gap-2">
                                     <div className="w-1.5 h-1.5 rounded-full bg-coral-500 mt-1.5" />
                                     {s}
                                  </li>
                                ))}
                             </ul>
                          </div>
                       </div>
                    </motion.div>
                 ))}
              </div>
           </motion.section>
         ) : null}
      </AnimatePresence>
    </PrepLabShell>
  );
}

function resolveErrorMessage(error: unknown) {
  if (typeof error === "object" && error !== null && "message" in error) {
    return (error as ApiError).message;
  }
  return "Unexpected interview practice failure";
}
