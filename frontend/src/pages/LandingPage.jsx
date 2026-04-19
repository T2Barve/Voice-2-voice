import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Cpu, Database, BarChart3, ArrowRight, CheckCircle2 } from 'lucide-react';

const LandingPage = () => {
    return (
        <div className="min-h-screen bg-black text-white selection:bg-emerald-500/30">
            {/* Navigation */}
            <nav className="fixed top-0 w-full z-50 bg-black/50 backdrop-blur-xl border-b border-white/5">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-tr from-emerald-500 to-cyan-500 rounded-lg flex items-center justify-center">
                            <Cpu className="w-5 h-5 text-black" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">InterviewAI</span>
                    </div>
                    <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
                        <a href="#features" className="hover:text-white transition-colors">Features</a>
                        <a href="#how-it-works" className="hover:text-white transition-colors">How it Works</a>
                        <a href="#pricing" className="hover:text-white transition-colors">Enterprise</a>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link to="/login" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Log in</Link>
                        <Link to="/signup" className="px-4 py-2 bg-white text-black text-sm font-bold rounded-full hover:bg-gray-200 transition-all">
                            Get Started
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 px-6 overflow-hidden">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-6xl h-full pointer-events-none">
                    <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/10 rounded-full blur-[120px]" />
                    <div className="absolute bottom-[20%] right-[-10%] w-[30%] h-[30%] bg-cyan-500/10 rounded-full blur-[100px]" />
                </div>

                <div className="max-w-7xl mx-auto text-center relative z-10">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold mb-8 animate-fade-in">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                        </span>
                        New: Gemini 2.0 Integration
                    </div>
                    
                    <h1 className="text-5xl md:text-8xl font-black tracking-tighter mb-8 leading-[1.1]">
                        Practice Interviews <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-500">
                            Like It's Real.
                        </span>
                    </h1>
                    
                    <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
                        The world's most advanced AI mock interview platform. Personalized feedback, 
                        resume-aware agents, and real company datasets.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <Link to="/signup" className="group px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-black font-black text-lg rounded-2xl flex items-center gap-2 transition-all shadow-[0_0_40px_rgba(16,185,129,0.2)]">
                            Start Free Practice <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <Link to="/login" className="px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 backdrop-blur-md rounded-2xl font-bold transition-all">
                            View Demo
                        </Link>
                    </div>

                    {/* Trusted By / Stats */}
                    <div className="mt-24 pt-10 border-t border-white/5 flex flex-wrap justify-center gap-12 text-gray-500 grayscale opacity-50">
                        <span className="font-bold text-xl tracking-widest">GOOGLE</span>
                        <span className="font-bold text-xl tracking-widest">AMAZON</span>
                        <span className="font-bold text-xl tracking-widest">MICROSOFT</span>
                        <span className="font-bold text-xl tracking-widest">META</span>
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section id="features" className="py-24 px-6 bg-black relative">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-5xl font-bold mb-4">FAANG-Level Preparation</h2>
                        <p className="text-gray-400">Everything you need to land your dream technical role.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {[
                            {
                                icon: <ShieldCheck className="w-6 h-6 text-emerald-400" />,
                                title: "Real Company Questions",
                                desc: "Our RAG engine pulls from verified datasets for Google, Amazon, and Microsoft."
                            },
                            {
                                icon: <Cpu className="w-6 h-6 text-cyan-400" />,
                                title: "Resume-Aware AI",
                                desc: "No generic questions. Our agents parse your resume to ask about your specific tech stack."
                            },
                            {
                                icon: <BarChart3 className="w-6 h-6 text-blue-400" />,
                                title: "In-Depth Analytics",
                                desc: "Get scored on DSA, communication, and problem-solving with a personalized dashboard."
                            }
                        ].map((f, i) => (
                            <div key={i} className="group p-8 rounded-3xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] hover:border-white/[0.1] transition-all">
                                <div className="w-12 h-12 rounded-2xl bg-white/[0.05] flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                                    {f.icon}
                                </div>
                                <h3 className="text-xl font-bold mb-3">{f.title}</h3>
                                <p className="text-gray-500 leading-relaxed text-sm">
                                    {f.desc}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* How it Works */}
            <section id="how-it-works" className="py-24 px-6 border-t border-white/5">
                <div className="max-w-7xl mx-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
                        <div>
                            <h2 className="text-4xl font-bold mb-8">From Upload to <br />Offer Letter.</h2>
                            <div className="space-y-8">
                                {[
                                    { step: "01", title: "Upload Resume", text: "Our LangChain service extracts your core skills and projects." },
                                    { step: "02", title: "Select Focus", text: "Choose from DSA, Technical, or Case Study interviews." },
                                    { step: "03", title: "Real-time Practice", text: "Interact with AI agents that challenge your edge-case thinking." },
                                    { step: "04", title: "Analyze Performance", text: "Review your strengths and areas to improve in your dashboard." }
                                ].map((s, i) => (
                                    <div key={i} className="flex gap-4">
                                        <span className="text-emerald-500 font-black text-lg">{s.step}</span>
                                        <div>
                                            <h4 className="font-bold mb-1">{s.title}</h4>
                                            <p className="text-gray-500 text-sm leading-relaxed">{s.text}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="relative">
                            <div className="absolute inset-0 bg-emerald-500/20 blur-[100px] rounded-full" />
                            <div className="relative bg-gray-900 border border-white/10 rounded-3xl p-8 shadow-2xl overflow-hidden">
                                <div className="flex items-center gap-2 mb-6">
                                    <div className="w-3 h-3 rounded-full bg-red-500" />
                                    <div className="w-3 h-3 rounded-full bg-yellow-500" />
                                    <div className="w-3 h-3 rounded-full bg-green-500" />
                                </div>
                                <div className="space-y-4 font-mono text-sm text-gray-400">
                                    <p className="text-emerald-400"># Start your interview</p>
                                    <p>$ ai-interviewer start --company google</p>
                                    <p className="text-white">🚀 Initializing Google DSA Agent...</p>
                                    <p className="text-cyan-400">🤖 "Given an array of intervals, merge all overlapping intervals..."</p>
                                    <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                                        <div className="h-full w-2/3 bg-emerald-500" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-20 px-6 border-t border-white/5">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
                    <div className="flex items-center gap-2">
                        <Cpu className="w-6 h-6 text-emerald-500" />
                        <span className="text-lg font-bold">InterviewAI</span>
                    </div>
                    <div className="text-gray-500 text-sm">
                        © 2026 InterviewAI Platform. All rights reserved.
                    </div>
                    <div className="flex items-center gap-6 text-gray-500 text-sm font-medium">
                        <a href="#" className="hover:text-white transition-colors">Privacy</a>
                        <a href="#" className="hover:text-white transition-colors">Terms</a>
                        <a href="#" className="hover:text-white transition-colors">Twitter</a>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
