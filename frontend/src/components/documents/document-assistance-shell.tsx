"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiRequest } from "@/lib/api";
import type {
  ApiError,
  DocumentDetail,
  DocumentInputMethod,
  DocumentListResponse,
  DocumentSubmissionResponse,
  DocumentType,
} from "@/lib/types";
import { PrepLabShell } from "@/components/layout/prep-lab-shell";
import { Plus, RefreshCw, Terminal, Sparkles, AlertTriangle } from "lucide-react";

type DocumentState = {
  isLoading: boolean;
  isSubmitting: boolean;
  isRefreshing: boolean;
  error: string | null;
  items: DocumentDetail[];
  selectedId: string | null;
};

export function DocumentAssistanceShell() {
  const { accessToken } = useAuth();
  const [inputMethod, setInputMethod] = useState<DocumentInputMethod>("text");
  const [documentType, setDocumentType] = useState<DocumentType>("sop");
  const [title, setTitle] = useState("");
  const [contentText, setContentText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [state, setState] = useState<DocumentState>({
    isLoading: true,
    isSubmitting: false,
    isRefreshing: false,
    error: null,
    items: [],
    selectedId: null,
  });

  useEffect(() => {
    if (!accessToken) return;

    let isActive = true;

    const loadDocuments = async () => {
      setState((current) => ({ ...current, isLoading: true, error: null }));
      try {
        const response = await apiRequest<DocumentListResponse>("/documents", {
          token: accessToken,
        });
        if (!isActive) return;

        if (response.items.length === 0) {
          setState((current) => ({
            ...current,
            isLoading: false,
            items: [],
            selectedId: null,
          }));
          return;
        }

        const detailResponses = await Promise.all(
          response.items.slice(0, 10).map((item) =>
            apiRequest<DocumentDetail>(`/documents/${item.id}`, {
              token: accessToken,
            }),
          ),
        );

        if (!isActive) return;

        setState((current) => ({
          ...current,
          isLoading: false,
          items: detailResponses,
          selectedId: current.selectedId ?? detailResponses[0]?.id ?? null,
        }));
      } catch (error) {
        if (!isActive) return;
        setState((current) => ({
          ...current,
          isLoading: false,
          error: resolveErrorMessage(error),
        }));
      }
    };

    void loadDocuments();

    return () => {
      isActive = false;
    };
  }, [accessToken]);


  const selectedDocument = useMemo(
    () => state.items.find((item) => item.id === state.selectedId) ?? null,
    [state.items, state.selectedId],
  );

  const handleSubmit = async () => {
    if (!accessToken) return;

    const clientError = validateClientSubmission(inputMethod, contentText, file);
    if (clientError) {
      setFormError(clientError);
      return;
    }

    setFormError(null);
    setState((current) => ({ ...current, isSubmitting: true, error: null }));

    const formData = new FormData();
    formData.append("document_type", documentType);
    if (title.trim()) formData.append("title", title.trim());
    if (inputMethod === "text") formData.append("content_text", contentText.trim());
    if (inputMethod === "file" && file) formData.append("file", file);

    try {
      const response = await apiRequest<DocumentSubmissionResponse>("/documents", {
        method: "POST",
        body: formData,
        token: accessToken,
      });

      setState((current) => {
        const nextItems = [
          response.document,
          ...current.items.filter((item) => item.id !== response.document.id),
        ];
        return {
          ...current,
          isSubmitting: false,
          items: nextItems,
          selectedId: response.document.id,
        };
      });
      setTitle("");
      setContentText("");
      setFile(null);
      setInputMethod("text");
      setDocumentType("sop");
    } catch (error) {
      setState((current) => ({
        ...current,
        isSubmitting: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  const handleRefreshFeedback = async () => {
    if (!accessToken || !selectedDocument) return;

    setState((current) => ({ ...current, isRefreshing: true, error: null }));
    try {
      const response = await apiRequest<DocumentSubmissionResponse>(
        `/documents/${selectedDocument.id}/feedback`,
        {
          method: "POST",
          token: accessToken,
        },
      );
      setState((current) => ({
        ...current,
        isRefreshing: false,
        items: current.items.map((item) =>
          item.id === response.document.id ? response.document : item,
        ),
        selectedId: response.document.id,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isRefreshing: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  return (
    <PrepLabShell 
      eyebrow="Redaction Phase"
      title="Writing Room."
    >
      <div className="flex h-[calc(100vh-320px)] gap-8">
        
        {/* Left: Document Ledger & New Form */}
        <aside className={`${isSidebarOpen ? 'w-80' : 'w-0'} flex-shrink-0 transition-all duration-500 overflow-hidden`}>
           <div className="glass-surface h-full flex flex-col border-white/5 bg-white/[0.02]">
              <div className="p-6 border-b border-white/5 flex items-center justify-between">
                 <h2 className="text-sm font-bold uppercase tracking-widest text-neutral-500">Ledger</h2>
                 <button 
                  onClick={() => setIsSidebarOpen(false)}
                  className="p-1 hover:bg-white/5 rounded-md transition-colors"
                 >
                    <Plus size={16} className="rotate-45" />
                 </button>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-2">
                 {state.isLoading ? (
                    <div className="space-y-4">
                      {[1,2,3].map(i => <div key={i} className="h-20 bg-white/5 animate-pulse rounded-2xl" />)}
                    </div>
                 ) : state.items.map(item => (
                    <button
                      key={item.id}
                      onClick={() => setState(c => ({ ...c, selectedId: item.id }))}
                      className={`w-full text-left p-4 rounded-2xl border transition-all ${
                        item.id === state.selectedId 
                        ? 'bg-cobalt-600/10 border-cobalt-600/30' 
                        : 'border-transparent hover:bg-white/5 hover:border-white/10'
                      }`}
                    >
                       <div className="flex items-center justify-between mb-2">
                          <span className={`${item.processing_status === 'completed' ? 'text-emerald-500' : 'text-cobalt-500'} text-[10px] font-black uppercase tracking-tighter`}>
                             {formatStatus(item.processing_status)}
                          </span>
                          <span className="text-[10px] text-neutral-600">
                             {new Date(item.updated_at).toLocaleDateString()}
                          </span>
                       </div>
                       <h3 className="text-sm font-medium truncate">{item.title}</h3>
                       <p className="text-[10px] text-neutral-600 mt-1 uppercase tracking-widest">{item.document_type}</p>
                    </button>
                 ))}
              </div>

              <div className="p-4 border-t border-white/5">
                 <button 
                  onClick={() => {
                    setState(c => ({ ...c, selectedId: null }));
                    setTitle("");
                    setContentText("");
                  }}
                  className="w-full py-4 flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl text-xs font-bold uppercase tracking-widest transition-all"
                 >
                    <Plus size={14} /> New Draft
                 </button>
              </div>
           </div>
        </aside>

        {/* Center: Immersive Editor */}
        <main className="flex-1 flex flex-col gap-6">
           {!isSidebarOpen && (
             <button 
               onClick={() => setIsSidebarOpen(true)}
               className="self-start glass-surface px-4 py-2 rounded-full border-white/5 text-[10px] font-black uppercase tracking-widest text-neutral-500 hover:text-white transition-all mb-2"
             >
               Open Ledger
             </button>
           )}

           <div className="flex-1 glass-surface rounded-[2.5rem] border-white/10 bg-white/[0.03] shadow-inner relative overflow-hidden group">
              {state.selectedId ? (
                 <div className="absolute inset-0 p-12 overflow-y-auto selection:bg-cobalt-500/30">
                    <header className="mb-12 flex items-center justify-between">
                       <div>
                          <span className="text-[10px] font-black uppercase tracking-widest text-cobalt-500 mb-2 block">
                            Document Scope · {selectedDocument?.document_type.toUpperCase()}
                          </span>
                          <h2 className="text-3xl font-medium">{selectedDocument?.title}</h2>
                       </div>
                       <div className="flex items-center gap-4">
                          <StatusBadge 
                             label={formatStatus(selectedDocument?.processing_status || '')} 
                             variant={selectedDocument?.processing_status === 'completed' ? 'validated' : 'planned'} 
                          />
                       </div>
                    </header>
                    <div className="prose prose-invert max-w-none">
                       <p className="text-xl leading-[1.8] text-white/70 font-light whitespace-pre-wrap">
                          {selectedDocument?.content_text}
                       </p>
                    </div>
                 </div>
              ) : (
                 <div className="absolute inset-0 p-12 overflow-y-auto">
                    <header className="mb-12">
                       <h2 className="text-3xl font-medium">Draft Neutralization.</h2>
                       <p className="text-neutral-500 mt-2">Submit a new baseline draft for neural analysis.</p>
                    </header>

                    <form 
                      onSubmit={(e) => { e.preventDefault(); void handleSubmit(); }}
                      className="space-y-8 max-w-2xl"
                    >
                       <div className="grid grid-cols-2 gap-6">
                          <div className="space-y-2">
                             <label className="text-[10px] font-bold uppercase tracking-widest text-neutral-500">Document Blueprint</label>
                             <select 
                                value={documentType}
                                onChange={(e) => setDocumentType(e.target.value as DocumentType)}
                                className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm outline-none focus:ring-2 focus:ring-cobalt-600/20"
                             >
                                <option value="sop">Statement of Purpose</option>
                                <option value="essay">Thematic Essay</option>
                             </select>
                          </div>
                          <div className="space-y-2">
                             <label className="text-[10px] font-bold uppercase tracking-widest text-neutral-500">Working Title</label>
                             <input 
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="Refined Draft v1"
                                className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm outline-none focus:ring-2 focus:ring-cobalt-600/20"
                             />
                          </div>
                       </div>

                       <div className="space-y-2">
                          <label className="text-[10px] font-bold uppercase tracking-widest text-neutral-500">Content Manifest</label>
                          <textarea 
                             value={contentText}
                             onChange={(e) => setContentText(e.target.value)}
                             placeholder="Inject draft content here..."
                             rows={12}
                             className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-lg font-light outline-none focus:ring-2 focus:ring-cobalt-600/20 resize-none"
                          />
                       </div>

                       {formError && (
                          <div className="p-4 bg-coral-600/10 border border-coral-600/20 rounded-xl text-coral-500 text-sm flex items-center gap-3">
                             <AlertTriangle size={16} /> {formError}
                          </div>
                       )}

                       <button 
                          disabled={state.isSubmitting}
                          className="px-10 py-5 bg-white text-black font-black uppercase tracking-widest text-[10px] rounded-full hover:scale-105 transition-all shadow-xl"
                       >
                          {state.isSubmitting ? 'Neutralizing...' : 'Submit to Core'}
                       </button>
                    </form>
                 </div>
              )}
           </div>
        </main>

        {/* Right: Neutral Feedback Panel */}
        <aside className="w-96 flex-shrink-0">
           <div className="glass-surface h-full flex flex-col border-white/5 bg-white/[0.02]">
              <div className="p-6 border-b border-white/5 flex items-center justify-between">
                 <h2 className="text-sm font-bold uppercase tracking-widest text-neutral-500">Neural Observations</h2>
                 <RefreshCw 
                    size={16} 
                    className={`text-neutral-600 cursor-pointer hover:text-white transition-all ${state.isRefreshing ? 'animate-spin' : ''}`}
                    onClick={() => void handleRefreshFeedback()}
                 />
              </div>

              <div className="flex-1 overflow-y-auto p-8">
                 {selectedDocument?.latest_feedback ? (
                    <div className="space-y-12">
                       <section>
                          <div className="flex items-center gap-2 mb-4 text-emerald-500">
                             <Sparkles size={14} />
                             <h4 className="text-[10px] font-black uppercase tracking-widest">Synthesis</h4>
                          </div>
                          <p className="text-sm leading-relaxed text-neutral-300">
                             {selectedDocument.latest_feedback.summary}
                          </p>
                       </section>

                       <section>
                          <h4 className="text-[10px] font-black uppercase tracking-widest text-emerald-500 mb-6 flex items-center gap-2">
                             <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                             Structural Strengths
                          </h4>
                          <ul className="space-y-4">
                             {selectedDocument.latest_feedback.strengths.slice(0, 3).map((s, i) => (
                                <li key={i} className="text-xs text-neutral-400 bg-white/5 p-4 rounded-xl border border-white/5">
                                   {s}
                                </li>
                             ))}
                          </ul>
                       </section>

                       <section>
                          <h4 className="text-[10px] font-black uppercase tracking-widest text-cobalt-500 mb-6 flex items-center gap-2">
                             <div className="w-1.5 h-1.5 rounded-full bg-cobalt-500" />
                             Revision Vectors
                          </h4>
                          <ul className="space-y-4">
                             {selectedDocument.latest_feedback.revision_priorities.slice(0, 3).map((s, i) => (
                                <li key={i} className="text-xs text-neutral-400 bg-white/5 p-4 rounded-xl border border-white/5">
                                   {s}
                                </li>
                             ))}
                          </ul>
                       </section>

                       <section className="pt-8 border-t border-white/5">
                          <h4 className="text-[10px] font-black uppercase tracking-widest text-neutral-600 mb-4">Neural Context</h4>
                          <div className="flex flex-wrap gap-2">
                             {selectedDocument.latest_feedback.grounded_context.slice(0, 2).map((c, i) => (
                                <span key={i} className="px-2 py-1 bg-white/5 rounded-md text-[9px] text-neutral-500 uppercase font-bold border border-white/5">
                                   {c}
                                </span>
                             ))}
                          </div>
                       </section>
                    </div>
                 ) : (
                    <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
                       <Terminal size={40} className="mb-6" />
                       <h3 className="text-sm font-medium">Awaiting Data.</h3>
                       <p className="text-xs text-neutral-600 mt-2">Select a document to retrieve neural logs.</p>
                    </div>
                 )}
              </div>
           </div>
        </aside>

      </div>
    </PrepLabShell>
  );
}

function validateClientSubmission(
  inputMethod: DocumentInputMethod,
  contentText: string,
  file: File | null,
) {
  if (inputMethod === "text") {
    if (contentText.trim().length < 50) {
      return "Injection requires at least 50 characters of baseline text.";
    }
    return null;
  }

  if (!file) {
    return "Neutralize requires a valid .txt or .md archive.";
  }

  return null;
}

function formatStatus(status: string) {
  if (status === "completed") return "Ready";
  if (status === "processing") return "Analyzing";
  if (status === "failed") return "Halt";
  return "Queued";
}

function resolveErrorMessage(error: unknown) {
  if (typeof error === "object" && error !== null && "message" in error) {
    return (error as ApiError).message;
  }
  return "Unexpected Neural Environment failure";
}
