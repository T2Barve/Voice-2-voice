import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Editor from "@monaco-editor/react";
import { Mic, MicOff, Send, Volume2, VolumeX, Play, RotateCcw, ChevronRight, Settings, Code, MessageSquareText, Cpu, CheckCircle2 } from 'lucide-react';

const EXPRESS_BACKEND = 'http://localhost:5000';

const InterviewPage = () => {
    const navigate = useNavigate();

    // Setup State
    const [phase, setPhase] = useState('setup'); // setup | active | ended
    const [company, setCompany] = useState('Google');
    const [role] = useState(() => localStorage.getItem('role') || 'SDE');
    const [interviewType, setInterviewType] = useState(() => localStorage.getItem('interviewType') || 'technical');

    // Interview State
    const [messages, setMessages] = useState([]);
    const [answer, setAnswer] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionId] = useState(() => `sess_${Date.now()}`);
    const [isListening, setIsListening] = useState(false);
    const [feedback, setFeedback] = useState(null);

    // Code Editor State
    const [code, setCode] = useState('// Write your solution here...\n\nfunction solution() {\n  \n}');
    const [language, setLanguage] = useState('javascript');
    const [isAutoVoice, setIsAutoVoice] = useState(true);

    const recognitionRef = useRef(null);
    const scrollRef = useRef(null);
    const synthRef = useRef(window.speechSynthesis);

    const resumeData = JSON.parse(localStorage.getItem('resumeData') || '{}');
    const token = localStorage.getItem('token');

    useEffect(() => {
        if (!resumeData || (!resumeData.skills && !resumeData.data?.skills)) {
            navigate('/resume');
            return;
        }
        setupSpeechRecognition();
        return () => {
            recognitionRef.current?.stop();
            synthRef.current.cancel();
        };
    }, []);

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
        
        // Auto-speak latest AI message
        const lastMsg = messages[messages.length - 1];
        if (lastMsg && lastMsg.role === 'interviewer' && isAutoVoice) {
            speakText(lastMsg.text);
        }
    }, [messages]);

    const speakText = (text) => {
        if (!synthRef.current) return;
        synthRef.current.cancel(); // Stop current speech
        
        const cleanText = text.replace(/```[\s\S]*?```/g, " [Code Block Hidden] "); // Don't speak large code blocks
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        // Try to find a nice female English voice
        const voices = synthRef.current.getVoices();
        const preferredVoice = voices.find(v => v.lang.includes('en') && v.name.includes('Google')) || voices[0];
        if (preferredVoice) utterance.voice = preferredVoice;
        
        synthRef.current.speak(utterance);
    };

    const setupSpeechRecognition = () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return;

        const rec = new SpeechRecognition();
        rec.continuous = true;
        rec.interimResults = true;
        rec.onresult = (e) => {
            let final = '';
            for (let i = e.resultIndex; i < e.results.length; i++) {
                if (e.results[i].isFinal) final += e.results[i][0].transcript + ' ';
            }
            if (final) setAnswer(prev => prev + final);
        };
        rec.onend = () => setIsListening(false);
        recognitionRef.current = rec;
    };

    const startInterview = async () => {
        setLoading(true);
        try {
            const userId = localStorage.getItem('userId') || 'user_default';
            // We ensure we send Exactly what the FastAPI StartInterviewRequest expects
            const payload = {
                user_id: userId,
                session_id: sessionId,
                company: company,
                role: role,
                interview_type: interviewType,
                resume_data: {
                    skills: resumeData.skills || [],
                    projects: resumeData.projects || []
                }
            };

            const res = await fetch(`${EXPRESS_BACKEND}/api/${interviewType}/start`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(token && { Authorization: `Bearer ${token}` })
                },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || data.error || 'Failed to start');

            setMessages([{ role: 'interviewer', text: data.question }]);
            setPhase('active');
        } catch (err) {
            setMessages([{ role: 'system', text: `❌ Error: ${err.message}` }]);
            setPhase('active');
        } finally {
            setLoading(false);
        }
    };

    const submitAnswer = async () => {
        if (!answer.trim() || loading) return;
        const userAns = answer.trim();
        setAnswer('');
        setIsListening(false);
        recognitionRef.current?.stop();

        setMessages(prev => [...prev, { role: 'user', text: userAns }]);
        setLoading(true);

        try {
            const res = await fetch(`${EXPRESS_BACKEND}/api/${interviewType}/submit`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(token && { Authorization: `Bearer ${token}` })
                },
                body: JSON.stringify({ user_answer: userAns, thread_id: sessionId }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || data.error || 'Submit failed');

            if (data.final_response) {
                setMessages(prev => [...prev, { role: 'interviewer', text: data.final_response }]);
            }

            if (data.status === 'ended') {
                setFeedback({ score: data.score, strengths: data.strengths, weakness: data.weakness });
                setPhase('ended');
            } else if (data.next_question) {
                setMessages(prev => [...prev, { role: 'interviewer', text: data.next_question }]);
            }
        } catch (err) {
            setMessages(prev => [...prev, { role: 'system', text: `❌ ${err.message}` }]);
        } finally {
            setLoading(false);
        }
    };

    const toggleListen = () => {
        if (isListening) {
            recognitionRef.current?.stop();
            setIsListening(false);
        } else {
            try {
                recognitionRef.current?.start();
                setIsListening(true);
            } catch (_) {}
        }
    };

    const handleEditorChange = (value) => {
        setCode(value);
    };

    const getLanguageDefaultValue = (lang) => {
        const defaults = {
            javascript: '// Javascript Solution\n\nfunction solve() {\n  \n}',
            python: '# Python Solution\n\ndef solve():\n    pass',
            java: '// Java Solution\n\nclass Solution {\n    public void solve() {\n        \n    }\n}',
            cpp: '// C++ Solution\n\n#include <iostream>\nusing namespace std;\n\nint main() {\n    return 0;\n}'
        };
        return defaults[lang] || '';
    };

    const onLanguageChange = (newLang) => {
        setLanguage(newLang);
        setCode(getLanguageDefaultValue(newLang));
    };

    // Submitting code together with text for better context
    const submitFullContext = async () => {
        const userAns = answer.trim();
        const payloadText = interviewType === 'dsa' 
            ? `[CODE SOLUTION IN ${language.toUpperCase()}]\n${code}\n\n[USER COMMENT]\n${userAns || "No comment provided."}`
            : userAns;

        if (!payloadText && !code) return;

        setMessages(prev => [...prev, { 
            role: 'user', 
            text: interviewType === 'dsa' ? (userAns ? `Modified code and said: ${userAns}` : "Updated code solution.") : userAns 
        }]);
        
        setLoading(true);
        setAnswer('');
        setIsListening(false);
        recognitionRef.current?.stop();

        try {
            const res = await fetch(`${EXPRESS_BACKEND}/api/${interviewType}/submit`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(token && { Authorization: `Bearer ${token}` })
                },
                body: JSON.stringify({ user_answer: payloadText, thread_id: sessionId }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || data.error || 'Submit failed');

            if (data.final_response) {
                setMessages(prev => [...prev, { role: 'interviewer', text: data.final_response }]);
            }

            if (data.status === 'ended') {
                setFeedback({ score: data.score, strengths: data.strengths, weakness: data.weakness });
                setPhase('ended');
            } else if (data.next_question) {
                setMessages(prev => [...prev, { role: 'interviewer', text: data.next_question }]);
            }
        } catch (err) {
            setMessages(prev => [...prev, { role: 'system', text: `❌ ${err.message}` }]);
        } finally {
            setLoading(false);
        }
    };

    if (phase === 'setup') {
        const safeResumeData = resumeData.data ? resumeData.data : resumeData;
        
        return (
            <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 relative">
                 {/* Animated Background */}
                 <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-[100px] animate-pulse" />
                    <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: '2s' }} />
                 </div>

                 <div className="relative z-10 max-w-xl w-full bg-gray-900/40 border border-white/5 rounded-3xl p-10 backdrop-blur-2xl shadow-2xl">
                    <div className="flex justify-center mb-6">
                        <div className="w-16 h-16 bg-gradient-to-tr from-emerald-500 to-cyan-500 rounded-2xl flex items-center justify-center">
                            <Settings className="w-8 h-8 text-black" />
                        </div>
                    </div>

                    <h2 className="text-4xl font-black text-center mb-2 tracking-tight">
                        Session Setup
                    </h2>
                    <p className="text-gray-500 text-center mb-10 text-sm">Choose your round and company to begin.</p>
                    
                    <div className="space-y-8">
                        <div>
                            <label className="block text-xs font-black uppercase tracking-widest text-emerald-500 mb-3">Target Company</label>
                            <div className="relative">
                                <select 
                                    value={company} onChange={e => setCompany(e.target.value)}
                                    className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer"
                                >
                                    {['Google', 'Amazon', 'Microsoft', 'Meta', 'Apple', 'Netflix', 'Tesla', 'OpenAI'].map(c => (
                                        <option key={c} value={c} className="bg-gray-900">{c}</option>
                                    ))}
                                </select>
                                <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500 pointer-events-none rotate-90" />
                            </div>
                        </div>
                        
                        <div>
                            <label className="block text-xs font-black uppercase tracking-widest text-emerald-500 mb-3">Interview Focus</label>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {[
                                    { id: 'dsa', label: 'Algorithms', icon: <Code className="w-4 h-4" /> },
                                    { id: 'technical', label: 'Technical', icon: <Settings className="w-4 h-4" /> },
                                    { id: 'case-study', label: 'Case Study', icon: <MessageSquareText className="w-4 h-4" /> }
                                ].map(type => (
                                    <button
                                        key={type.id}
                                        onClick={() => setInterviewType(type.id)}
                                        className={`flex flex-col items-center gap-3 p-4 rounded-2xl border transition-all ${interviewType === type.id ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.1)]' : 'bg-white/5 border-white/10 text-gray-500 hover:border-white/20 hover:text-white'}`}
                                    >
                                        {type.icon}
                                        <span className="text-xs font-bold">{type.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="bg-white/5 border border-white/5 rounded-2xl p-5">
                            <div className="flex items-center gap-2 mb-3">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                <span className="text-[10px] font-black uppercase text-emerald-500 tracking-widest">Candidate DNA Active</span>
                            </div>
                            <p className="text-gray-400 text-xs">Matching specialized agent for <span className="text-white font-bold">{safeResumeData?.role || 'Software Engineer'}</span> role.</p>
                        </div>

                        <button 
                            onClick={startInterview}
                            disabled={loading}
                            className="w-full py-5 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-black text-lg rounded-2xl transition-all shadow-[0_0_30px_rgba(16,185,129,0.2)]"
                        >
                            {loading ? 'Initializing RAG System...' : 'Start Session'}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen bg-black text-white flex flex-col overflow-hidden">
            {/* Header */}
            <nav className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-black/80 backdrop-blur-md shrink-0">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center text-black font-black text-sm">IA</div>
                        <span className="text-lg font-black tracking-tighter">
                            {interviewType.toUpperCase()} ROUND
                        </span>
                    </div>
                    <div className="h-4 w-[1px] bg-white/10 hidden md:block" />
                    <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-gray-400 text-[10px] font-black uppercase tracking-widest hidden md:block">
                        {company}
                    </span>
                </div>
                
                <div className="flex items-center gap-4">
                    <button 
                        onClick={() => setIsAutoVoice(!isAutoVoice)} 
                        className={`p-2 rounded-lg border transition-all ${isAutoVoice ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400' : 'bg-white/5 border-white/10 text-gray-500'}`}
                        title={isAutoVoice ? "Mute AI Voice" : "Unmute AI Voice"}
                    >
                        {isAutoVoice ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                    </button>
                    <button onClick={() => navigate('/dashboard')} className="text-[10px] font-black uppercase text-gray-500 hover:text-red-400 transition-colors tracking-widest">End Session</button>
                </div>
            </nav>

            {/* Main Content Area */}
            <div className={`flex-1 flex overflow-hidden ${interviewType === 'dsa' ? 'flex-col lg:flex-row' : 'flex-col items-center'}`}>
                
                {/* Left Pane: Chat & Description */}
                <div className={`flex flex-col ${interviewType === 'dsa' ? 'lg:w-[40%] border-r border-white/5' : 'w-full max-w-4xl'} h-full bg-black`}>
                    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 scrollbar-hide">
                        {messages.map((msg, i) => (
                            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                                {msg.role !== 'user' && (
                                    <div className="w-8 h-8 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0 mr-3 mt-1">
                                        <Cpu className="w-4 h-4 text-emerald-500" />
                                    </div>
                                )}
                                <div className={`max-w-[85%] rounded-3xl px-5 py-3 text-sm leading-relaxed whitespace-pre-wrap ${msg.role === 'user' ? 'bg-emerald-500 text-black font-medium' : msg.role === 'system' ? 'bg-red-500/10 border border-red-500/20 text-red-500' : 'bg-white/[0.03] border border-white/5'}`}>
                                    {msg.text}
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex justify-start">
                                <div className="w-8 h-8 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0 mr-3">
                                    <Cpu className="w-4 h-4 text-emerald-500 animate-pulse" />
                                </div>
                                <div className="bg-white/[0.03] border border-white/5 rounded-3xl px-5 py-3 flex gap-1.5 items-center">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce" />
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce delay-75" />
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce delay-150" />
                                </div>
                            </div>
                        )}
                        {phase === 'ended' && feedback && (
                            <div className="bg-emerald-500 border border-emerald-400 rounded-3xl p-8 mt-6 text-black">
                                <h3 className="text-2xl font-black mb-6 flex items-center gap-2">
                                    Round Over! <RotateCcw className="w-5 h-5" />
                                </h3>
                                <div className="flex items-baseline gap-2 mb-8">
                                    <span className="text-6xl font-black">{feedback.score}</span>
                                    <span className="text-xl font-bold opacity-60">/10</span>
                                </div>
                                <div className="space-y-4 mb-8">
                                    <p className="font-bold flex gap-2"><CheckCircle2 className="w-5 h-5 shrink-0" /> {feedback.strengths}</p>
                                    <p className="font-medium flex gap-2 opacity-80 underline decoration-black/20">📈 Needs focus on: {feedback.weakness}</p>
                                </div>
                                <button onClick={() => navigate('/dashboard')} className="w-full py-4 bg-black text-white rounded-2xl font-black text-lg transition-all hover:scale-[1.02] active:scale-95">Go to Dashboard</button>
                            </div>
                        )}
                        <div ref={scrollRef} />
                    </div>

                    {/* Chat Controls (Voice + Text combined) */}
                    {phase === 'active' && (
                        <div className="p-6 border-t border-white/5 bg-black/50 backdrop-blur-md">
                            <div className="relative group">
                                <textarea 
                                    value={answer} 
                                    onChange={e => setAnswer(e.target.value)} 
                                    placeholder={isListening ? "Listening to your voice..." : "Type your answer or use voice..."} 
                                    className={`w-full bg-white/[0.03] border ${isListening ? 'border-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.1)]' : 'border-white/10'} rounded-3xl px-6 py-4 outline-none text-sm resize-none transition-all pr-32 placeholder:text-gray-600`} 
                                    rows={2} 
                                    onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitFullContext(); }}} 
                                />
                                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                                    <button 
                                        onClick={toggleListen} 
                                        className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${isListening ? 'bg-emerald-500 text-black animate-pulse' : 'hover:bg-white/10 text-gray-400'}`}
                                    >
                                        {isListening ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
                                    </button>
                                    <button 
                                        onClick={submitFullContext} 
                                        disabled={!answer.trim() && (interviewType !== 'dsa' || !code)} 
                                        className="w-12 h-12 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-black flex items-center justify-center disabled:opacity-20 transition-all shadow-[0_0_20px_rgba(16,185,129,0.2)]"
                                    >
                                        <Send className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                            <p className="mt-3 text-[10px] text-gray-600 font-bold uppercase tracking-widest text-center">Press Enter to send context</p>
                        </div>
                    )}
                </div>

                {/* Right Pane: Monaco Editor (Only for DSA) */}
                {interviewType === 'dsa' && phase === 'active' && (
                    <div className="flex-1 flex flex-col h-full bg-[#1e1e1e]">
                        {/* Editor Header */}
                        <div className="flex items-center justify-between px-6 py-3 bg-[#252526] border-b border-white/5">
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                                    <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                    <select 
                                        value={language} 
                                        onChange={(e) => onLanguageChange(e.target.value)}
                                        className="bg-transparent text-emerald-400 text-xs font-black uppercase outline-none cursor-pointer"
                                    >
                                        <option value="javascript">Javascript</option>
                                        <option value="python">Python</option>
                                        <option value="java">Java</option>
                                        <option value="cpp">C++</option>
                                    </select>
                                </div>
                                <span className="text-[10px] text-gray-500 font-black tracking-widest uppercase">main.code</span>
                            </div>
                            
                            <div className="flex items-center gap-3">
                                <button className="p-2 hover:bg-white/5 rounded-lg text-gray-400">
                                    <RotateCcw className="w-4 h-4" />
                                </button>
                                <button 
                                    onClick={submitFullContext}
                                    className="flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-black text-[10px] font-black uppercase tracking-widest rounded-lg transition-all"
                                >
                                    <Play className="w-3 h-3 fill-black" /> Run Solution
                                </button>
                            </div>
                        </div>

                        {/* Editor Canvas */}
                        <div className="flex-1 w-full bg-[#1e1e1e]">
                            <Editor
                                height="100%"
                                language={language}
                                theme="vs-dark"
                                value={code}
                                onChange={handleEditorChange}
                                options={{
                                    fontSize: 14,
                                    minimap: { enabled: false },
                                    scrollBeyondLastLine: false,
                                    automaticLayout: true,
                                    padding: { top: 20 },
                                    lineNumbers: 'on',
                                    glyphMargin: false,
                                    folding: true,
                                    lineDecorationsWidth: 0,
                                    lineNumbersMinChars: 3
                                }}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default InterviewPage;
