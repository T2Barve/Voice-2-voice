import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusCircle } from 'lucide-react';

const DASHBOARD_ENDPOINT = 'http://localhost:5000/api/analytics';

const DashboardPage = () => {
    const navigate = useNavigate();
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);

    const user = JSON.parse(localStorage.getItem('user') || '{}');

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const token = localStorage.getItem('token');
                const res = await fetch(DASHBOARD_ENDPOINT, {
                    headers: token ? { Authorization: `Bearer ${token}` } : {},
                });
                const data = await res.json();
                if (data.status === 'success') setMetrics(data.data);
            } catch (e) {
                console.error('Analytics fetch failed:', e);
            } finally {
                setLoading(false);
            }
        };
        fetchMetrics();
    }, []);

    const handleLogout = () => {
        localStorage.clear();
        navigate('/');
    };

    return (
        <div className="min-h-screen bg-black text-white">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/10 via-black to-cyan-900/10 pointer-events-none" />

            {/* Navbar */}
            <nav className="relative z-10 flex items-center justify-between px-8 py-5 border-b border-gray-900">
                <span className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                    InterviewAI
                </span>
                <div className="flex items-center gap-6">
                    <span className="text-gray-400 text-sm">👋 {user?.name || 'Candidate'}</span>
                    <button onClick={handleLogout} className="text-sm text-red-400 hover:text-red-300 transition-colors">Logout</button>
                </div>
            </nav>

            <div className="relative z-10 max-w-6xl mx-auto px-6 py-12">
                <div className="mb-10 flex flex-col md:flex-row items-start md:items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                            Analytics Dashboard
                        </h1>
                        <p className="text-gray-400 mt-2">Track your interview progress and jump into your next session.</p>
                    </div>
                    
                    {/* MUST HAVE BUTTON */}
                    <button 
                        onClick={() => navigate("/role-selection")} 
                        className="mt-6 md:mt-0 px-8 py-4 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-white rounded-xl font-bold text-lg shadow-[0_0_30px_rgba(16,185,129,0.3)] transition-all transform hover:-translate-y-1"
                    >
                        Start Interview →
                    </button>
                </div>

                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                        {[1,2,3].map(i => (
                            <div key={i} className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 animate-pulse">
                                <div className="h-4 bg-gray-800 rounded w-1/2 mb-3"></div>
                                <div className="h-8 bg-gray-800 rounded w-1/3"></div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                        <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 backdrop-blur-md">
                            <h3 className="text-gray-400 font-medium text-sm uppercase tracking-wider mb-2">Total Sessions</h3>
                            <div className="text-4xl font-bold text-white">{metrics?.total_interviews ?? 0}</div>
                        </div>
                        <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 backdrop-blur-md">
                            <h3 className="text-gray-400 font-medium text-sm uppercase tracking-wider mb-2">Average Score</h3>
                            <div className="text-4xl font-bold text-emerald-400">
                                {metrics?.average_score ?? '—'}<span className="text-lg text-gray-500">/10</span>
                            </div>
                        </div>
                        <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 backdrop-blur-md flex items-center justify-center">
                            <button 
                              onClick={() => navigate('/role-selection')}
                              className="bg-emerald-500 hover:bg-emerald-400 text-black px-6 py-2 rounded-lg font-bold flex items-center gap-2 transition-colors"
                            >
                              <PlusCircle size={20} />
                              Start New Interview
                            </button>
                        </div>
                    </div>
                )}
                
                <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 max-w-4xl mx-auto">
                    <h2 className="text-lg font-semibold mb-4 text-white">Recent Sessions</h2>
                    {metrics?.recent_sessions?.length > 0 ? (
                        <div className="space-y-3">
                            {metrics.recent_sessions.map((s, i) => (
                                <div key={i} className="flex items-center justify-between p-4 bg-black/40 rounded-xl border border-gray-800/50">
                                    <div>
                                        <span className="font-semibold text-lg">{s.type} Interview</span>
                                        <div className="text-gray-500 text-sm mt-0.5">{s.company} · {s.date}</div>
                                    </div>
                                    <span className={`text-xl font-bold ${parseFloat(s.score) >= 8 ? 'text-emerald-400' : parseFloat(s.score) >= 6 ? 'text-yellow-400' : 'text-red-400'}`}>
                                        {s.score}
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12">
                            <p className="text-gray-500 text-sm mb-4">No sessions yet. Upload your resume and start an interview to see data here.</p>
                            <button onClick={() => navigate("/role-selection")} className="px-6 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-emerald-400 transition-colors">Start Prep</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
