import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Flame, Target, Zap, ArrowRight, Loader2, Info } from 'lucide-react';

const EXPRESS = 'http://localhost:5000';

const ResumeAnalysisPage = () => {
    const navigate = useNavigate();
    const [analysis, setAnalysis] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchAnalysis = async () => {
            // Priority 1: Dedicated Roaster Upload
            let storedData = sessionStorage.getItem('roastResumeText');
            
            // Priority 2: Interview Resume (Fallback)
            if (!storedData) {
                storedData = localStorage.getItem('resumeData');
            }

            if (!storedData) {
                navigate('/roaster-upload');
                return;
            }

            const parsedData = JSON.parse(storedData);
            const resumeText = JSON.stringify(parsedData); // Use the parsed JSON as context for the roaster

            try {
                const token = localStorage.getItem('token');
                const res = await fetch(`${EXPRESS}/api/resume/analyze`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token ? { Authorization: `Bearer ${token}` } : {})
                    },
                    body: JSON.stringify({ resume_text: resumeText })
                });

                const data = await res.json();
                if (data.status === 'success') {
                    setAnalysis(data.data);
                } else {
                    throw new Error(data.error || 'Analysis failed');
                }
            } catch (err) {
                console.error('Roast failed:', err);
                setError('Our AI recruiter had a breakdown reading your resume. Using fallback analysis.');
                setAnalysis({
                    ats_score: 55,
                    roast: "This resume looks like it was written in the dark by someone who has only seen a computer twice. It's safe, generic, and completely forgettable.",
                    strengths: ["Proper File Format", "Has a Name"],
                    weaknesses: ["Lack of Impact", "Generic Phrasing"],
                    ats_optimization_tips: ["Use Action Verbs", "Quantify Results"]
                });
            } finally {
                setLoading(false);
            }
        };

        fetchAnalysis();
    }, [navigate]);

    if (loading) {
        return (
            <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6">
                <div className="relative w-24 h-24 mb-8">
                    <div className="absolute inset-0 border-4 border-emerald-500/20 rounded-full"></div>
                    <div className="absolute inset-0 border-4 border-t-emerald-500 rounded-full animate-spin"></div>
                    <Flame className="absolute inset-0 m-auto text-orange-500 animate-pulse" size={32} />
                </div>
                <h2 className="text-2xl font-black mb-2 tracking-tight">AI Recruiter is judging you...</h2>
                <p className="text-gray-500 font-medium">Scanning for cliches and lack of experience.</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black text-white font-sans selection:bg-emerald-500/30">
            {/* Ambient Background */}
            <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(16,185,129,0.1),transparent_50%)] pointer-events-none" />
            
            <main className="relative z-10 max-w-4xl mx-auto px-6 py-12 md:py-20">
                
                {/* Score Section */}
                <div className="text-center mb-16">
                    <div className="inline-block relative mb-6">
                        <div className="w-32 h-32 rounded-full border-8 border-gray-900 flex items-center justify-center">
                            <span className={`text-5xl font-black ${analysis.ats_score > 80 ? 'text-emerald-500' : analysis.ats_score > 60 ? 'text-cyan-500' : 'text-rose-500'}`}>
                                {analysis.ats_score}
                            </span>
                        </div>
                        <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-white text-black text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-tighter">
                            ATS Score
                        </div>
                    </div>
                    <h1 className="text-4xl md:text-6xl font-black mb-4 tracking-tighter">
                        Resume <span className="text-emerald-400 italic">Roasted</span>.
                    </h1>
                    <p className="text-gray-400 text-lg font-medium">Here's what our AI recruiter really thinks.</p>
                </div>

                {/* The Roast Card */}
                <div className="bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20 rounded-[2.5rem] p-8 md:p-12 mb-12 relative overflow-hidden group">
                    <Flame className="absolute -right-8 -top-8 text-emerald-500/10 group-hover:scale-125 transition-transform duration-700" size={240} />
                    <div className="relative z-10">
                        <div className="flex items-center gap-2 mb-6">
                            <div className="p-2 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-lg text-white">
                                <Flame size={20} />
                            </div>
                            <span className="font-black uppercase tracking-widest text-xs text-emerald-400">The Brutal Truth</span>
                        </div>
                        <p className="text-xl md:text-2xl font-bold leading-relaxed text-emerald-100 italic">
                            "{analysis.roast}"
                        </p>
                    </div>
                </div>

                {/* Analysis Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
                    {/* Strengths */}
                    <div className="bg-gray-900/40 border border-gray-800 rounded-3xl p-8 backdrop-blur-xl">
                        <div className="flex items-center gap-3 mb-6">
                            <Shield className="text-emerald-500" size={24} />
                            <h3 className="text-lg font-bold">Strengths</h3>
                        </div>
                        <ul className="space-y-4">
                            {analysis.strengths.map((s, i) => (
                                <li key={i} className="flex items-start gap-3 text-gray-400 font-medium">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 shrink-0" />
                                    {s}
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Weaknesses */}
                    <div className="bg-gray-900/40 border border-gray-800 rounded-3xl p-8 backdrop-blur-xl">
                        <div className="flex items-center gap-3 mb-6">
                            <Target className="text-red-500" size={24} />
                            <h3 className="text-lg font-bold">Critical Flaws</h3>
                        </div>
                        <ul className="space-y-4">
                            {analysis.weaknesses.map((w, i) => (
                                <li key={i} className="flex items-start gap-3 text-gray-400 font-medium">
                                    <div className="w-1.5 h-1.5 rounded-full bg-red-500 mt-2 shrink-0" />
                                    {w}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Optimization Tips */}
                <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-3xl p-8 mb-12">
                    <div className="flex items-center gap-3 mb-6">
                        <Zap className="text-emerald-400" size={24} />
                        <h3 className="text-lg font-bold">ATS Optimization Tips</h3>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {analysis.ats_optimization_tips.map((tip, i) => (
                            <div key={i} className="flex items-center gap-3 bg-black/40 p-4 rounded-2xl border border-emerald-500/10 text-sm font-medium text-emerald-200">
                                <Info size={16} className="text-emerald-500 shrink-0" />
                                {tip}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Call to Action */}
                <div className="flex flex-col items-center gap-6">
                    <button 
                        onClick={() => navigate('/interview-type')}
                        className="group w-full md:w-auto bg-white text-black px-12 py-5 rounded-2xl font-black text-lg flex items-center justify-center gap-3 hover:bg-emerald-400 transition-all active:scale-95 shadow-xl shadow-emerald-500/10"
                    >
                        Proceed to Interview Setup <ArrowRight className="group-hover:translate-x-1 transition-transform" />
                    </button>
                    <button 
                        onClick={() => navigate('/resume-upload')}
                        className="text-gray-500 font-bold hover:text-white transition-colors"
                    >
                        Wait, let me fix it and re-upload
                    </button>
                </div>

            </main>
        </div>
    );
};

export default ResumeAnalysisPage;
