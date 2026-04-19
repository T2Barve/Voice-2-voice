import { useState, useEffect, useRef, useCallback } from "react";
import Editor from "@monaco-editor/react";
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Play,
  ChevronRight,
  Code2,
  Brain,
  Trophy,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  Terminal,
  Zap,
  BarChart3,
  ArrowRight,
  RefreshCw,
  User,
  Briefcase,
  Star,
} from "lucide-react";

// ─── Constants ────────────────────────────────────────────────────────────────

const BOILERPLATE = {
  python: `def solution():\n    # Write your solution here\n    pass\n`,
  javascript: `function solution() {\n  // Write your solution here\n}\n`,
  java: `class Solution {\n    public void solution() {\n        // Write your solution here\n    }\n}\n`,
  cpp: `#include <bits/stdc++.h>\nusing namespace std;\n\nvoid solution() {\n    // Write your solution here\n}\n`,
};

const LANGUAGES = ["python", "javascript", "java", "cpp"];

const EXPERIENCE_OPTIONS = [
  { value: "0-2", label: "0 – 2 years", sub: "Junior" },
  { value: "3-5", label: "3 – 5 years", sub: "Mid-level" },
  { value: "5+", label: "5+ years", sub: "Senior" },
];

const ROLES = [
  "Software Engineer",
  "Frontend Engineer",
  "Backend Engineer",
  "Full Stack Engineer",
  "Data Engineer",
  "ML Engineer",
];

// ─── Tiny helpers ─────────────────────────────────────────────────────────────

function fmtTime(ms) {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  if (h > 0) return `${h}h ${m % 60}m`;
  if (m > 0) return `${m}m ${s % 60}s`;
  return `${s}s`;
}

function scoreColor(n) {
  if (n >= 8) return "text-emerald-400";
  if (n >= 5) return "text-amber-400";
  return "text-red-400";
}

function scoreBar(n) {
  if (n >= 8) return "bg-emerald-500";
  if (n >= 5) return "bg-amber-500";
  return "bg-red-500";
}

// ─── useTTS hook ──────────────────────────────────────────────────────────────

function useTTS() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const utterRef = useRef(null);

  const speak = useCallback((text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.95;
    u.pitch = 1;
    u.onstart = () => setIsSpeaking(true);
    u.onend = () => setIsSpeaking(false);
    u.onerror = () => setIsSpeaking(false);
    utterRef.current = u;
    window.speechSynthesis.speak(u);
  }, []);

  const stop = useCallback(() => {
    window.speechSynthesis?.cancel();
    setIsSpeaking(false);
  }, []);

  return { isSpeaking, speak, stop };
}

// ─── useSTT hook ──────────────────────────────────────────────────────────────

function useSTT(onResult) {
  const [isListening, setIsListening] = useState(false);
  const [interim, setInterim] = useState("");
  const recogRef = useRef(null);

  const start = useCallback(() => {
    const SpeechRec =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      alert("Speech recognition not supported in this browser.");
      return;
    }
    const r = new SpeechRec();
    r.continuous = true;
    r.interimResults = true;
    r.lang = "en-US";
    r.onresult = (e) => {
      let fin = "",
        int = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) fin += e.results[i][0].transcript;
        else int += e.results[i][0].transcript;
      }
      setInterim(int);
      if (fin) {
        onResult(fin);
        setInterim("");
      }
    };
    r.onend = () => setIsListening(false);
    r.onerror = () => setIsListening(false);
    recogRef.current = r;
    r.start();
    setIsListening(true);
  }, [onResult]);

  const stop = useCallback(() => {
    recogRef.current?.stop();
    setIsListening(false);
    setInterim("");
  }, []);

  return { isListening, interim, start, stop };
}

// ─── useTimer hook ────────────────────────────────────────────────────────────

function useTimer(running) {
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef(null);

  useEffect(() => {
    if (!running) return;
    startRef.current = Date.now() - elapsed;
    const id = setInterval(
      () => setElapsed(Date.now() - startRef.current),
      1000,
    );
    return () => clearInterval(id);
  }, [running]); // eslint-disable-line

  const reset = () => {
    setElapsed(0);
    startRef.current = null;
  };
  return { elapsed, reset };
}

// ─── Welcome Screen ───────────────────────────────────────────────────────────

function WelcomeScreen({ onStart }) {
  const [name, setName] = useState("");
  const [role, setRole] = useState(ROLES[0]);
  const [experience, setExperience] = useState("3-5");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleStart() {
    if (!name.trim()) {
      setError("Please enter your name.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const threadId = crypto.randomUUID();
      const res = await fetch("/api/dsa/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role, experience, thread_id: threadId }),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      onStart({
        name,
        role,
        experience,
        threadId,
        firstQuestion: data.question,
      });
    } catch (e) {
      setError(e.message || "Failed to start. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background glow orbs */}
      <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-violet-900/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-indigo-900/20 blur-[120px] pointer-events-none" />

      <div className="relative w-full max-w-md">
        {/* Badge */}
        <div className="flex justify-center mb-8">
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-violet-500/30 bg-violet-500/10 text-violet-300 text-sm font-mono tracking-wider">
            <Zap size={12} className="text-violet-400" />
            DSA INTERVIEW ROUND
          </span>
        </div>

        {/* Heading */}
        <h1
          className="text-center text-4xl font-bold text-white mb-2 tracking-tight"
          style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}
        >
          Ready to crack it?
        </h1>
        <p className="text-center text-slate-400 text-sm mb-10 font-mono">
          Solve real DSA problems. Get instant AI feedback.
        </p>

        {/* Card */}
        <div className="bg-[#13131a] border border-white/[0.06] rounded-2xl p-8 shadow-2xl space-y-6">
          {/* Name */}
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-2 tracking-widest uppercase">
              Your Name
            </label>
            <div className="relative">
              <User
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
              />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleStart()}
                placeholder="Mayur Patil"
                className="w-full pl-9 pr-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-slate-600 text-sm focus:outline-none focus:border-violet-500/60 focus:bg-white/[0.06] transition-all"
              />
            </div>
          </div>

          {/* Role */}
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-2 tracking-widest uppercase">
              Role
            </label>
            <div className="relative">
              <Briefcase
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
              />
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full pl-9 pr-4 py-3 rounded-xl bg-[#0a0a0f] border border-white/[0.08] text-white text-sm focus:outline-none focus:border-violet-500/60 transition-all appearance-none cursor-pointer"
              >
                {ROLES.map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Experience */}
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-2 tracking-widest uppercase">
              Experience
            </label>
            <div className="grid grid-cols-3 gap-2">
              {EXPERIENCE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setExperience(opt.value)}
                  className={`py-3 rounded-xl border text-center transition-all ${
                    experience === opt.value
                      ? "border-violet-500 bg-violet-500/15 text-white"
                      : "border-white/[0.08] bg-white/[0.03] text-slate-400 hover:border-white/20"
                  }`}
                >
                  <div className="text-sm font-semibold">{opt.value}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    {opt.sub}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
              <AlertCircle size={14} /> {error}
            </div>
          )}

          {/* CTA */}
          <button
            onClick={handleStart}
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold text-sm tracking-wide flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-violet-900/30 active:scale-[0.98]"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" /> Initialising...
              </>
            ) : (
              <>
                <Play size={16} /> Start DSA Interview
              </>
            )}
          </button>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6 font-mono">
          3 questions · AI-evaluated · Real-time feedback
        </p>
      </div>
    </div>
  );
}

// ─── Question Panel ───────────────────────────────────────────────────────────

function QuestionPanel({ raw, isSpeaking, onSpeak, onStop, qIndex }) {
  // Naive parse: split on lines, detect Examples / Constraints sections
  const lines = raw.split("\n");
  const title = lines.find((l) => l.trim()) || `Problem ${qIndex + 1}`;
  const body = lines.slice(1).join("\n");

  return (
    <div className="h-full flex flex-col bg-[#0e0e16] border-r border-white/[0.06] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-slate-500 bg-white/[0.04] px-2 py-0.5 rounded-md border border-white/[0.06]">
            Q{qIndex + 1}
          </span>
          <h2 className="text-white font-semibold text-sm truncate max-w-[180px]">
            {title}
          </h2>
        </div>
        <button
          onClick={isSpeaking ? onStop : () => onSpeak(raw)}
          className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-all ${
            isSpeaking
              ? "border-violet-500/50 bg-violet-500/15 text-violet-300"
              : "border-white/[0.08] text-slate-400 hover:border-violet-500/30 hover:text-violet-300"
          }`}
        >
          {isSpeaking ? (
            <>
              <VolumeX size={13} /> Stop
            </>
          ) : (
            <>
              <Volume2 size={13} /> Listen
            </>
          )}
        </button>
      </div>

      {/* Speaking indicator */}
      {isSpeaking && (
        <div className="flex items-center gap-2 px-5 py-2 bg-violet-500/10 border-b border-violet-500/20">
          <span className="flex gap-0.5">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="w-1 h-3 bg-violet-400 rounded-full animate-pulse"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </span>
          <span className="text-violet-300 text-xs font-mono">
            AI is speaking…
          </span>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4 text-sm scrollbar-thin scrollbar-thumb-white/10">
        <div className="prose prose-invert prose-sm max-w-none">
          {body.split(/\n\n+/).map((block, i) => {
            const isExample = /^(example|input|output)/i.test(block.trim());
            const isConstraint = /^(constraint|note|limit)/i.test(block.trim());
            if (isExample) {
              return (
                <div
                  key={i}
                  className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 font-mono text-xs text-slate-300 whitespace-pre-wrap"
                >
                  {block}
                </div>
              );
            }
            if (isConstraint) {
              return (
                <div
                  key={i}
                  className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 text-amber-200/70 text-xs"
                >
                  {block}
                </div>
              );
            }
            return (
              <p key={i} className="text-slate-300 leading-relaxed">
                {block}
              </p>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── Voice Notes Panel ────────────────────────────────────────────────────────

function VoicePanel({
  isListening,
  interim,
  transcript,
  onStart,
  onStop,
  onClear,
}) {
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript, interim]);

  return (
    <div className="bg-[#0e0e16] border border-white/[0.06] rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-slate-400 tracking-widest uppercase">
          Voice Notes
        </span>
        <div className="flex items-center gap-2">
          {transcript && (
            <button
              onClick={onClear}
              className="text-[10px] text-slate-500 hover:text-slate-300 font-mono transition-colors"
            >
              clear
            </button>
          )}
          <button
            onClick={isListening ? onStop : onStart}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
              isListening
                ? "bg-red-500/15 border-red-500/40 text-red-300 animate-pulse"
                : "bg-white/[0.04] border-white/[0.08] text-slate-300 hover:border-violet-500/40 hover:text-violet-300"
            }`}
          >
            {isListening ? (
              <>
                <MicOff size={12} /> Stop
              </>
            ) : (
              <>
                <Mic size={12} /> Record
              </>
            )}
          </button>
        </div>
      </div>

      <div className="min-h-[60px] max-h-[120px] overflow-y-auto bg-black/20 rounded-lg p-3 text-sm font-mono text-slate-300 leading-relaxed">
        {transcript || ""}
        {interim && <span className="text-slate-500 italic">{interim}</span>}
        {!transcript && !interim && (
          <span className="text-slate-600 text-xs">
            Your spoken notes will appear here…
          </span>
        )}
        <div ref={endRef} />
      </div>

      {isListening && (
        <div className="flex items-center gap-2">
          <span className="flex gap-0.5">
            {[0, 1, 2, 3].map((i) => (
              <span
                key={i}
                className="w-1 rounded-full bg-red-400 animate-pulse"
                style={{
                  height: `${8 + Math.random() * 10}px`,
                  animationDelay: `${i * 0.1}s`,
                }}
              />
            ))}
          </span>
          <span className="text-red-300 text-xs font-mono">Listening…</span>
        </div>
      )}
    </div>
  );
}

// ─── Coding Screen ────────────────────────────────────────────────────────────

function CodingScreen({ session, onEnd }) {
  const [question, setQuestion] = useState(session.firstQuestion);
  const [qIndex, setQIndex] = useState(0);
  const [code, setCode] = useState(BOILERPLATE.python);
  const [language, setLanguage] = useState("python");
  const [transcript, setTranscript] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null); // { score, feedback, passed, total }
  const [error, setError] = useState("");
  const [results, setResults] = useState([]);
  const { elapsed } = useTimer(true);
  const { isSpeaking, speak, stop } = useTTS();

  const handleSTTResult = useCallback((text) => {
    setTranscript((prev) => prev + " " + text);
  }, []);

  const {
    isListening,
    interim,
    start: startSTT,
    stop: stopSTT,
  } = useSTT(handleSTTResult);

  // Auto-speak first question on mount
  useEffect(() => {
    if (question) speak(question);
  }, []); // eslint-disable-line

  function handleLangChange(lang) {
    setLanguage(lang);
    setCode(BOILERPLATE[lang]);
  }

  async function handleSubmit() {
    if (submitting) return;
    setSubmitting(true);
    setFeedback(null);
    setError("");
    try {
      const res = await fetch("/api/dsa/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: session.threadId,
          user_answer: code,
        }),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();

      const entry = {
        qIndex,
        question: question.split("\n")[0] || `Q${qIndex + 1}`,
        score: data.score,
        feedback: data.feedback,
        passed: data.test_cases_passed,
        total: data.total_test_cases,
        elapsed,
      };
      const newResults = [...results, entry];
      setResults(newResults);

      setFeedback(entry);
      speak(data.feedback);

      if (data.status === "ended") {
        setTimeout(() => onEnd(newResults, elapsed), 2500);
      } else if (data.next_question) {
        setTimeout(() => {
          stop();
          setQuestion(data.next_question);
          setQIndex((i) => i + 1);
          setCode(BOILERPLATE[language]);
          setFeedback(null);
          setTranscript("");
          speak(data.next_question);
        }, 3500);
      }
    } catch (e) {
      setError(e.message || "Submission failed. Please retry.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex flex-col overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-white/[0.06] bg-[#0e0e16] flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-white text-sm font-semibold">
            {session.name}
          </span>
          <span className="text-slate-500 text-xs font-mono">·</span>
          <span className="text-slate-400 text-xs font-mono">
            {session.role}
          </span>
          <span className="text-slate-500 text-xs font-mono">·</span>
          <span className="text-slate-400 text-xs font-mono">
            {session.experience} yrs
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-mono">
            <Clock size={12} />
            {fmtTime(elapsed)}
          </div>
          <span className="text-[10px] font-mono text-slate-500 bg-white/[0.04] px-2 py-1 rounded-md border border-white/[0.06]">
            {qIndex + 1} / 3
          </span>
        </div>
      </div>

      {/* Main area */}
      <div className="flex-1 flex overflow-hidden" style={{ minHeight: 0 }}>
        {/* LEFT — question */}
        <div className="w-[38%] min-w-[280px] flex flex-col overflow-hidden">
          <QuestionPanel
            raw={question}
            isSpeaking={isSpeaking}
            onSpeak={speak}
            onStop={stop}
            qIndex={qIndex}
          />
        </div>

        {/* RIGHT — editor + controls */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Editor toolbar */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-white/[0.06] bg-[#0e0e16] flex-shrink-0">
            <div className="flex items-center gap-1">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang}
                  onClick={() => handleLangChange(lang)}
                  className={`px-3 py-1 rounded-md text-xs font-mono transition-all ${
                    language === lang
                      ? "bg-violet-600/30 text-violet-300 border border-violet-500/40"
                      : "text-slate-500 hover:text-slate-300"
                  }`}
                >
                  {lang}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-1.5 text-slate-600 text-xs font-mono">
              <Code2 size={11} />
              editor
            </div>
          </div>

          {/* Monaco */}
          <div className="flex-1 overflow-hidden">
            <Editor
              height="100%"
              language={language}
              value={code}
              onChange={(v) => setCode(v || "")}
              theme="vs-dark"
              options={{
                fontSize: 13,
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                lineNumbers: "on",
                renderLineHighlight: "all",
                padding: { top: 16, bottom: 16 },
                wordWrap: "on",
                automaticLayout: true,
              }}
            />
          </div>

          {/* Voice + feedback + submit row */}
          <div className="flex-shrink-0 border-t border-white/[0.06] bg-[#0e0e16] p-4 space-y-3">
            {/* Voice notes */}
            <VoicePanel
              isListening={isListening}
              interim={interim}
              transcript={transcript}
              onStart={startSTT}
              onStop={stopSTT}
              onClear={() => setTranscript("")}
            />

            {/* Feedback card */}
            {feedback && (
              <div
                className={`rounded-xl border p-4 text-sm space-y-2 transition-all ${
                  feedback.score >= 8
                    ? "bg-emerald-500/10 border-emerald-500/30"
                    : feedback.score >= 5
                      ? "bg-amber-500/10 border-amber-500/30"
                      : "bg-red-500/10 border-red-500/30"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {feedback.score >= 8 ? (
                      <CheckCircle size={14} className="text-emerald-400" />
                    ) : feedback.score >= 5 ? (
                      <AlertCircle size={14} className="text-amber-400" />
                    ) : (
                      <XCircle size={14} className="text-red-400" />
                    )}
                    <span className={`font-bold ${scoreColor(feedback.score)}`}>
                      {feedback.score}/10
                    </span>
                  </div>
                  <span className="text-xs font-mono text-slate-400">
                    {feedback.passed}/{feedback.total} tests passed
                  </span>
                </div>
                <p className="text-slate-300 text-xs leading-relaxed">
                  {feedback.feedback}
                </p>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="flex items-center gap-2 text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
                <AlertCircle size={13} /> {error}
              </div>
            )}

            {/* Submit */}
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm flex items-center justify-center gap-2 transition-all shadow-lg shadow-violet-900/20 active:scale-[0.98]"
            >
              {submitting ? (
                <>
                  <Loader2 size={15} className="animate-spin" /> Evaluating…
                </>
              ) : (
                <>
                  <Terminal size={15} /> Run &amp; Submit
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Summary Screen ───────────────────────────────────────────────────────────

function SummaryScreen({ session, results, totalTime, onRestart }) {
  const avg = results.length
    ? (results.reduce((s, r) => s + r.score, 0) / results.length).toFixed(1)
    : 0;
  const total = results.length;
  const { isSpeaking, speak, stop } = useTTS();

  const summary = `Great effort, ${session.name}! You completed ${total} questions with an average score of ${avg} out of 10. ${
    avg >= 8
      ? "Excellent performance!"
      : avg >= 5
        ? "Good work, keep practising!"
        : "Keep grinding — you'll get there!"
  }`;

  useEffect(() => {
    speak(summary);
  }, []); // eslint-disable-line

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex flex-col items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full bg-violet-900/15 blur-[100px] pointer-events-none" />

      <div className="relative w-full max-w-2xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-600 shadow-lg shadow-violet-900/40 mx-auto">
            <Trophy size={28} className="text-white" />
          </div>
          <h1
            className="text-3xl font-bold text-white"
            style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}
          >
            Interview Complete
          </h1>
          <p className="text-slate-400 text-sm">
            Here's how you performed, {session.name}
          </p>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4">
          {[
            {
              label: "Avg Score",
              value: `${avg}/10`,
              icon: <Star size={16} className="text-amber-400" />,
              color: scoreColor(Number(avg)),
            },
            {
              label: "Questions",
              value: total,
              icon: <Brain size={16} className="text-violet-400" />,
              color: "text-violet-300",
            },
            {
              label: "Total Time",
              value: fmtTime(totalTime),
              icon: <Clock size={16} className="text-indigo-400" />,
              color: "text-indigo-300",
            },
          ].map((s) => (
            <div
              key={s.label}
              className="bg-[#13131a] border border-white/[0.06] rounded-2xl p-5 text-center"
            >
              <div className="flex justify-center mb-2">{s.icon}</div>
              <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
              <div className="text-xs text-slate-500 font-mono mt-1">
                {s.label}
              </div>
            </div>
          ))}
        </div>

        {/* Per-question breakdown */}
        <div className="bg-[#13131a] border border-white/[0.06] rounded-2xl p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-white font-semibold text-sm flex items-center gap-2">
              <BarChart3 size={15} className="text-violet-400" /> Per-Question
              Breakdown
            </h2>
            <button
              onClick={isSpeaking ? stop : () => speak(summary)}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-all ${
                isSpeaking
                  ? "border-violet-500/50 bg-violet-500/15 text-violet-300"
                  : "border-white/[0.08] text-slate-400 hover:text-violet-300"
              }`}
            >
              {isSpeaking ? (
                <>
                  <VolumeX size={12} /> Stop
                </>
              ) : (
                <>
                  <Volume2 size={12} /> Summary
                </>
              )}
            </button>
          </div>

          {results.map((r, i) => (
            <div key={i} className="space-y-2">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <span className="flex-shrink-0 w-6 h-6 rounded-lg bg-white/[0.04] border border-white/[0.06] text-xs text-slate-400 font-mono flex items-center justify-center">
                    {i + 1}
                  </span>
                  <div className="min-w-0">
                    <p className="text-white text-sm font-medium truncate">
                      {r.question}
                    </p>
                    <p className="text-slate-400 text-xs mt-0.5 leading-relaxed line-clamp-2">
                      {r.feedback}
                    </p>
                  </div>
                </div>
                <div className="flex-shrink-0 text-right">
                  <span className={`text-lg font-bold ${scoreColor(r.score)}`}>
                    {r.score}
                  </span>
                  <span className="text-slate-500 text-xs">/10</span>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                    {r.passed}/{r.total} tests
                  </div>
                </div>
              </div>

              {/* Progress bar */}
              <div className="h-1.5 rounded-full bg-white/[0.04] overflow-hidden ml-9">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${scoreBar(r.score)}`}
                  style={{ width: `${(r.score / 10) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onRestart}
            className="flex-1 py-3 rounded-xl border border-white/[0.08] text-slate-300 hover:border-white/20 hover:text-white text-sm font-medium flex items-center justify-center gap-2 transition-all bg-white/[0.02]"
          >
            <RefreshCw size={14} /> Try Again
          </button>
          <button
            onClick={onRestart}
            className="flex-1 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white text-sm font-semibold flex items-center justify-center gap-2 transition-all shadow-lg shadow-violet-900/20"
          >
            New Interview <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Root App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [phase, setPhase] = useState("welcome"); // welcome | coding | summary
  const [session, setSession] = useState(null);
  const [results, setResults] = useState([]);
  const [totalTime, setTotalTime] = useState(0);

  function handleStart(info) {
    setSession(info);
    setResults([]);
    setPhase("coding");
  }

  function handleEnd(finalResults, elapsed) {
    setResults(finalResults);
    setTotalTime(elapsed);
    setPhase("summary");
  }

  function handleRestart() {
    setSession(null);
    setResults([]);
    setPhase("welcome");
  }

  if (phase === "welcome") return <WelcomeScreen onStart={handleStart} />;
  if (phase === "coding")
    return <CodingScreen session={session} onEnd={handleEnd} />;
  if (phase === "summary")
    return (
      <SummaryScreen
        session={session}
        results={results}
        totalTime={totalTime}
        onRestart={handleRestart}
      />
    );
}
