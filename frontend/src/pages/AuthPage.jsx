import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const AuthPage = ({ mode }) => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const isLogin = mode === 'login';

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const endpoint = isLogin
            ? 'http://localhost:5000/api/auth/login'
            : 'http://localhost:5000/api/auth/signup';

        const body = isLogin ? { email, password } : { name, email, password };

        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Auth failed');

            localStorage.setItem('token', data.token);
            if (data.user) localStorage.setItem('user', JSON.stringify(data.user));
            // Clear stale resume data on fresh login
            localStorage.removeItem('resumeData');
            navigate('/dashboard');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-black flex items-center justify-center px-4">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/20 via-black to-cyan-900/10 pointer-events-none" />

            <div className="relative z-10 w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                        {isLogin ? 'Welcome Back' : 'Get Started'}
                    </h1>
                    <p className="text-gray-400 mt-2">
                        {isLogin ? 'Sign in to resume your prep' : 'Create your free account'}
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="bg-gray-900/70 backdrop-blur-xl border border-gray-800 rounded-2xl p-8 space-y-5 shadow-2xl">
                    {!isLogin && (
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Full Name</label>
                            <input
                                value={name} onChange={e => setName(e.target.value)}
                                placeholder="John Doe"
                                required
                                className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition-colors"
                            />
                        </div>
                    )}
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Email</label>
                        <input
                            type="email" value={email} onChange={e => setEmail(e.target.value)}
                            placeholder="you@example.com"
                            required
                            className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition-colors"
                        />
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Password</label>
                        <input
                            type="password" value={password} onChange={e => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                            className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition-colors"
                        />
                    </div>

                    {error && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-3 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 disabled:opacity-50 text-white font-bold rounded-lg transition-all transform hover:-translate-y-0.5 shadow-lg shadow-emerald-500/20"
                    >
                        {loading ? 'Please wait...' : isLogin ? 'Sign In' : 'Create Account'}
                    </button>

                    <p className="text-center text-gray-500 text-sm">
                        {isLogin ? "Don't have an account? " : 'Already have an account? '}
                        <Link to={isLogin ? '/signup' : '/login'} className="text-emerald-400 hover:text-emerald-300 font-medium">
                            {isLogin ? 'Sign up' : 'Sign in'}
                        </Link>
                    </p>
                </form>
            </div>
        </div>
    );
};

export default AuthPage;
