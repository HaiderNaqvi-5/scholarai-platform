"use client";

import { useState, useRef } from "react";
import { StatusBadge } from "@/components/ui/status-badge";

export function AudioRecorder({
  onRecordingComplete,
}: {
  onRecordingComplete: (base64Audio: string) => void;
}) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);

        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          const base64String = reader.result as string;
          // Strip the data:audio/webm;base64, prefix
          const base64 = base64String.split(",")[1];
          onRecordingComplete(base64);
        };
      };

      mediaRecorder.start();
      setIsRecording(true);
      setAudioUrl(null);
    } catch (err) {
      console.error("Error accessing microphone:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream
        .getTracks()
        .forEach((track) => track.stop());
      setIsRecording(false);
    }
  };

  return (
    <div className="audio-recorder p-4 surface-quiet rounded-xl border border-border-soft flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-ink-500">
          Voice Feedback (Optional)
        </span>
        {isRecording && <StatusBadge label="Recording..." variant="warning" />}
      </div>

      <div className="flex items-center gap-3">
        {!isRecording ? (
          <button
            type="button"
            className="auth-link auth-link--primary whitespace-nowrap"
            onClick={startRecording}
          >
            Start Mic
          </button>
        ) : (
          <button
            type="button"
            className="auth-link border-red-200 bg-red-50 text-red-600 whitespace-nowrap"
            onClick={stopRecording}
          >
            Stop Recording
          </button>
        )}

        {audioUrl && !isRecording && (
          <audio src={audioUrl} controls className="h-10 flex-1 max-w-[200px]" />
        )}
      </div>

      <p className="text-[10px] opacity-60 leading-tight">
        Capture your verbal response for AI speech-to-text evaluation. This
        augments your text submission.
      </p>
    </div>
  );
}
