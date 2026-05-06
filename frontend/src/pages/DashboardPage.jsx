import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusCircle, TrendingUp, BarChart2, Award, Clock, Briefcase, Flame } from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';

const EXPRESS = 'http://localhost:5000';

// ─── Custom Tooltip ───────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-900 border border-emerald-500/30 rounded-lg px-4 py-2 shadow-xl text-sm">
        <p className="text-gray-400 mb-1">{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color }} className="font-bold">
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// ─── Score colour helper ───────────────────────────────────────────
const scoreColor = (s) =>
  parseFloat(s) >= 8 ? 'text-emerald-400' : parseFloat(s) >= 6 ? 'text-yellow-400' : 'text-red-400';

// ─── Stat Card ────────────────────────────────────────────────────
const StatCard = ({ icon: Icon, label, value, sub, accent }) => (
  <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 backdrop-blur-md flex items-start gap-4">
    <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${accent}`}>
      <Icon size={22} className="text-white" />
    </div>
    <div>
      <p className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">{label}</p>
      <p className="text-3xl font-extrabold text-white">{value}</p>
      {sub && <p className="text-gray-500 text-xs mt-0.5">{sub}</p>}
    </div>
  </div>
);

// ─── Empty State ──────────────────────────────────────────────────
const EmptyState = ({ navigate }) => (
  <div className="col-span-full flex flex-col items-center justify-center py-20 text-center">
    <div className="text-6xl mb-4">🎯</div>
    <h3 className="text-white text-xl font-bold mb-2">No interview data yet</h3>
    <p className="text-gray-500 text-sm mb-6 max-w-sm">
      Upload your resume and complete an interview to see your analytics dashboard come alive.
    </p>
    <div className="flex gap-4">
      <button
        onClick={() => navigate('/role-selection')}
        className="px-8 py-3 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-xl font-bold hover:from-emerald-400 hover:to-cyan-400 transition-all active:scale-95"
      >
        Start First Interview →
      </button>
      <button
        onClick={() => navigate('/job-search')}
        className="px-8 py-3 bg-gray-900 border border-gray-800 text-white rounded-xl font-bold hover:bg-gray-800 transition-all active:scale-95"
      >
        Browse Jobs
      </button>
    </div>
  </div>
);

// ─── Main Component ───────────────────────────────────────────────
const DashboardPage = () => {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${EXPRESS}/api/analytics`, {
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

  // Derive chart data from metrics
  const scoreTrend  = metrics?.score_trend || [];
  const recentSessions = metrics?.recent_sessions || [];

  // Build type breakdown bar data from recent sessions
  const typeMap = {};
  recentSessions.forEach(s => {
    const t = s.type || 'Unknown';
    if (!typeMap[t]) typeMap[t] = { type: t, count: 0, total: 0 };
    typeMap[t].count++;
    typeMap[t].total += parseFloat(s.score) || 0;
  });
  const typeBreakdown = Object.values(typeMap).map(t => ({
    name: t.type,
    'Avg Score': parseFloat((t.total / t.count).toFixed(1)),
    Sessions: t.count,
  }));

  // Real skill breakdown — only populated from actual completed interview types
  const sb = metrics?.skill_breakdown || {};
  const radarSkills = [
    { skill: 'DSA',           A: sb.dsa       ?? 0 },
    { skill: 'Technical',     A: sb.technical  ?? 0 },
    { skill: 'System Design', A: sb.case_study ?? 0 },
  ].filter(s => s.A > 0); // only show skills with real scores

  const hasRadarData = radarSkills.length > 0;

  const hasData = (metrics?.total_interviews || 0) > 0;

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
          <button onClick={handleLogout} className="text-sm text-red-400 hover:text-red-300 transition-colors">
            Logout
          </button>
        </div>
      </nav>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-10">

        {/* Header */}
        <div className="mb-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
              Analytics Dashboard
            </h1>
            <p className="text-gray-400 mt-2">Track your interview progress across all sessions.</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/job-search')}
              className="px-6 py-3.5 bg-gray-900 border border-gray-800 hover:bg-gray-800 text-white rounded-xl font-bold transition-all hover:-translate-y-0.5 flex items-center gap-2"
            >
              <Briefcase size={18} className="text-cyan-400" /> Jobs
            </button>
            <button
              onClick={() => navigate('/resume-roaster')}
              className="px-6 py-3.5 bg-gray-900 border border-gray-800 hover:bg-orange-500/10 text-white rounded-xl font-bold transition-all hover:-translate-y-0.5 flex items-center gap-2 group"
            >
              <Flame size={18} className="text-orange-500 group-hover:animate-bounce" /> Roast
            </button>
            <button
              onClick={() => navigate('/role-selection')}
              className="px-8 py-3.5 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-white rounded-xl font-bold shadow-[0_0_30px_rgba(16,185,129,0.3)] transition-all hover:-translate-y-0.5 flex items-center gap-2"
            >
              <PlusCircle size={18} /> Start Interview
            </button>
          </div>
        </div>

        {loading ? (
          /* Skeleton */
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 animate-pulse h-28" />
            ))}
          </div>
        ) : hasData ? (
          <>
            {/* ── Stat Cards ─────────────────────────────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
              <StatCard
                icon={BarChart2}
                label="Total Sessions"
                value={metrics.total_interviews}
                sub="Across all interview types"
                accent="bg-gradient-to-br from-emerald-600 to-emerald-800"
              />
              <StatCard
                icon={TrendingUp}
                label="Average Score"
                value={`${metrics.average_score}/10`}
                sub={metrics.average_score >= 8 ? 'Excellent' : metrics.average_score >= 6 ? 'Good' : 'Needs work'}
                accent="bg-gradient-to-br from-cyan-600 to-cyan-800"
              />
              <StatCard
                icon={Award}
                label="Best Score"
                value={`${Math.max(...recentSessions.map(s => parseFloat(s.score) || 0), 0).toFixed(1)}/10`}
                sub="Personal best"
                accent="bg-gradient-to-br from-violet-600 to-violet-800"
              />
              <StatCard
                icon={Clock}
                label="Last Interview"
                value={recentSessions[0]?.date || '—'}
                sub={recentSessions[0]?.type || 'No sessions yet'}
                accent="bg-gradient-to-br from-amber-600 to-amber-800"
              />
            </div>

            {/* ── Charts Row 1 ───────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

              {/* Score Trend Line Chart */}
              <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 backdrop-blur-md">
                <h2 className="text-white font-semibold text-lg mb-5 flex items-center gap-2">
                  <TrendingUp size={18} className="text-emerald-400" /> Score Trend
                </h2>
                {scoreTrend.length >= 1 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={scoreTrend} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                      <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} />
                      <YAxis domain={[0, 10]} tick={{ fill: '#6b7280', fontSize: 11 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Line
                        type="monotone"
                        dataKey="score"
                        name="Score"
                        stroke="#10b981"
                        strokeWidth={2.5}
                        dot={{ fill: '#10b981', r: 4 }}
                        activeDot={{ r: 6, fill: '#34d399' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-56 flex items-center justify-center text-gray-600 text-sm">
                    Complete at least 2 sessions to see your trend.
                  </div>
                )}
              </div>

              {/* Type Breakdown Bar Chart */}
              <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 backdrop-blur-md">
                <h2 className="text-white font-semibold text-lg mb-5 flex items-center gap-2">
                  <BarChart2 size={18} className="text-cyan-400" /> Performance by Interview Type
                </h2>
                {typeBreakdown.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={typeBreakdown} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                      <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} />
                      <YAxis domain={[0, 10]} tick={{ fill: '#6b7280', fontSize: 11 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
                      <Bar dataKey="Avg Score" fill="#06b6d4" radius={[6, 6, 0, 0]} />
                      <Bar dataKey="Sessions" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-56 flex items-center justify-center text-gray-600 text-sm">
                    No breakdown data yet.
                  </div>
                )}
              </div>
            </div>

            {/* ── Charts Row 2 ───────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

              {/* Skill Radar */}
              <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 backdrop-blur-md">
                <h2 className="text-white font-semibold text-lg mb-5 flex items-center gap-2">
                  <Award size={18} className="text-violet-400" /> Skill Breakdown
                </h2>
                {hasRadarData ? (
                  <ResponsiveContainer width="100%" height={230}>
                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarSkills}>
                      <PolarGrid stroke="#1f2937" />
                      <PolarAngleAxis dataKey="skill" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fill: '#6b7280', fontSize: 10 }} />
                      <Radar name="Score" dataKey="A" stroke="#10b981" fill="#10b981" fillOpacity={0.25} strokeWidth={2} />
                    </RadarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-56 flex flex-col items-center justify-center text-center gap-3">
                    <span className="text-4xl">🎯</span>
                    <p className="text-gray-400 text-sm font-medium">Complete interviews to unlock</p>
                    <div className="flex gap-2 flex-wrap justify-center">
                      {[
                        { label: 'DSA', done: !!metrics?.skill_breakdown?.dsa },
                        { label: 'Technical', done: !!metrics?.skill_breakdown?.technical },
                        { label: 'Case Study', done: !!metrics?.skill_breakdown?.case_study }
                      ].map(({ label, done }) => (
                        <span key={label} className={`px-3 py-1 rounded-full text-xs font-semibold ${done ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-700' : 'bg-gray-800 text-gray-500 border border-gray-700'}`}>
                          {done ? '✓' : '○'} {label}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Recent Sessions Table */}
              <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 backdrop-blur-md">
                <h2 className="text-white font-semibold text-lg mb-5">Recent Sessions</h2>
                <div className="space-y-3">
                  {recentSessions.slice(0, 5).map((s, i) => (
                    <div key={i} className="flex items-center justify-between p-3.5 bg-black/40 rounded-xl border border-gray-800/50">
                      <div>
                        <span className="font-semibold text-white">{s.type} Interview</span>
                        <div className="text-gray-500 text-xs mt-0.5">{s.company} · {s.date}</div>
                      </div>
                      <span className={`text-xl font-bold ${scoreColor(s.score)}`}>
                        {typeof s.score === 'number' ? s.score.toFixed(1) : s.score}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="grid grid-cols-1">
            <EmptyState navigate={navigate} />
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
