import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

const BACKEND = 'http://localhost:8000';

const ResumeUploadPage = () => {
    const [file, setFile] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const [status, setStatus] = useState('idle'); // idle | uploading | success | error
    const [parsedData, setParsedData] = useState(null);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setDragOver(false);
        const dropped = e.dataTransfer.files[0];
        if (dropped?.type === 'application/pdf') setFile(dropped);
        else setError('Please upload a PDF file only.');
    }, []);

    const handleFileChange = (e) => {
        const selected = e.target.files[0];
        if (selected?.type === 'application/pdf') { setFile(selected); setError(''); }
        else setError('Please upload a PDF file only.');
    };

    const handleUpload = async () => {
        if (!file) return;
        setStatus('uploading');
        setError('');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const token = localStorage.getItem('token');
            const res = await fetch('http://localhost:5000/api/resume/upload', {
                method: 'POST',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
                body: formData,
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || data.error || 'Upload failed');

            // Set data into local storage exactly as user required
            const resumeContext = {
                skills: data.data?.skills || [],
                projects: data.data?.projects || []
            };
            localStorage.setItem('resumeData', JSON.stringify(resumeContext));
            localStorage.setItem('resumeUploaded', 'true');
            
            setParsedData(data.data);
            setStatus('success');
        } catch (err) {
            setError(err.message || 'Failed to parse resume. Please try again.');
            setStatus('error');
        }
    };

    const handleContinue = () => navigate('/interview-type');

    return (
        <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center px-4 py-12">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-900/10 via-black to-emerald-900/10 pointer-events-none" />

            <div className="relative z-10 w-full max-w-2xl">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 mb-4 shadow-lg shadow-emerald-500/30">
                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                    </div>
                    <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                        Upload Your Resume
                    </h1>
                    <p className="text-gray-400 mt-2 max-w-lg mx-auto">
                        Your resume is the foundation of your interview experience. All questions will be tailored to your skills and projects.
                    </p>
                </div>

                {/* Step Indicator */}
                <div className="flex items-center justify-center gap-2 mb-8 text-sm">
                    <span className="px-3 py-1 rounded-full bg-gray-800 text-gray-500">1. Login</span>
                    <span className="text-gray-700">→</span>
                    <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold">2. Upload Resume</span>
                    <span className="text-gray-700">→</span>
                    <span className="px-3 py-1 rounded-full bg-gray-800 text-gray-500">3. Start Interview</span>
                </div>

                {status !== 'success' ? (
                    <div className="bg-gray-900/70 backdrop-blur-xl border border-gray-800 rounded-2xl p-8 space-y-6 shadow-2xl">
                        {/* Drag & Drop Zone */}
                        <div
                            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                            onDragLeave={() => setDragOver(false)}
                            onDrop={handleDrop}
                            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
                                dragOver
                                    ? 'border-emerald-400 bg-emerald-500/10'
                                    : file
                                    ? 'border-emerald-600 bg-emerald-900/10'
                                    : 'border-gray-700 hover:border-gray-600'
                            }`}
                            onClick={() => document.getElementById('file-input').click()}
                        >
                            <input
                                id="file-input"
                                type="file"
                                accept=".pdf"
                                onChange={handleFileChange}
                                className="hidden"
                            />
                            {file ? (
                                <div>
                                    <div className="text-4xl mb-2">📄</div>
                                    <p className="text-emerald-400 font-semibold text-lg">{file.name}</p>
                                    <p className="text-gray-500 text-sm mt-1">{(file.size / 1024).toFixed(1)} KB — Click to change</p>
                                </div>
                            ) : (
                                <div>
                                    <div className="text-4xl mb-3">☁️</div>
                                    <p className="text-gray-300 font-semibold">Drag & drop your PDF here</p>
                                    <p className="text-gray-500 text-sm mt-1">or click to browse</p>
                                </div>
                            )}
                        </div>

                        {error && (
                            <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
                                ⚠ {error}
                            </div>
                        )}

                        <button
                            onClick={handleUpload}
                            disabled={!file || status === 'uploading'}
                            className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all transform hover:-translate-y-0.5 shadow-lg shadow-emerald-500/20"
                        >
                            {status === 'uploading' ? '🔍 Parsing Resume with AI...' : '🚀 Upload & Parse Resume'}
                        </button>
                    </div>
                ) : (
                    /* Parsed Result Preview */
                    <div className="bg-gray-900/70 backdrop-blur-xl border border-emerald-800/40 rounded-2xl p-8 space-y-6 shadow-2xl">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center text-white font-bold">✓</div>
                            <h2 className="text-xl font-bold text-emerald-400">Resume Parsed Successfully!</h2>
                        </div>

                        <div className="space-y-4">
                            <div className="bg-black/40 rounded-xl p-4 border border-gray-800">
                                <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-2">Role & Experience</h3>
                                <p className="text-white font-medium">{parsedData?.role || 'Software Engineer'}</p>
                                <p className="text-emerald-400 text-sm">{parsedData?.experience || 'Entry-level'}</p>
                            </div>

                            <div className="bg-black/40 rounded-xl p-4 border border-gray-800">
                                <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-3">Skills Detected</h3>
                                <div className="flex flex-wrap gap-2">
                                    {(parsedData?.skills || []).map((skill, i) => (
                                        <span key={i} className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-300 text-sm">
                                            {skill}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div className="bg-black/40 rounded-xl p-4 border border-gray-800">
                                <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-2">Projects</h3>
                                <ul className="space-y-1">
                                    {(parsedData?.projects || []).map((proj, i) => (
                                        <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                                            <span className="text-cyan-400 mt-0.5">▸</span>
                                            {proj}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>

                        <button
                            onClick={handleContinue}
                            className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-white font-bold rounded-xl transition-all transform hover:-translate-y-0.5 shadow-lg shadow-emerald-500/20"
                        >
                            Continue to Interview Setup →
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ResumeUploadPage;
