import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Flame, Upload, ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';

const RoasterUploadPage = () => {
    const [file, setFile] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setDragOver(false);
        const dropped = e.dataTransfer.files[0];
        if (dropped?.type === 'application/pdf') setFile(dropped);
        else setError('PDF files only, please.');
    }, []);

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true);
        setError('');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const token = localStorage.getItem('token');
            // Step 1: Parse the resume (using existing endpoint but just for the roaster)
            const res = await fetch('http://localhost:5000/api/resume/upload', {
                method: 'POST',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
                body: formData,
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Upload failed');

            // Store in a SPECIAL session storage for the roaster to keep it separate from the interview system
            sessionStorage.setItem('roastResumeText', JSON.stringify(data.data));
            
            // Navigate to results
            navigate('/roaster-results');
        } catch (err) {
            setError(err.message || 'Failed to analyze resume.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
            {/* Ambient background effect */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-emerald-600/10 blur-[120px] rounded-full pointer-events-none" />
            
            <div className="relative z-10 w-full max-w-xl text-center">
                <div className="mb-8 flex flex-col items-center">
                    <div className="w-20 h-20 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-3xl flex items-center justify-center shadow-2xl shadow-emerald-500/20 mb-6">
                        <Flame size={40} className="text-white" />
                    </div>
                    <h1 className="text-5xl font-black tracking-tighter mb-4 text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                        RESUME <span className="">ROASTER</span>
                    </h1>
                    <p className="text-gray-400 font-medium text-lg">
                        Upload your resume and let our AI recruiter <br /> scan for cliches and lack of experience.
                    </p>
                </div>

                <div className="bg-gray-900/40 border border-gray-800 p-8 rounded-[2.5rem] backdrop-blur-xl shadow-2xl">
                    <div
                        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={handleDrop}
                        onClick={() => document.getElementById('roast-input').click()}
                        className={`border-2 border-dashed rounded-3xl p-12 mb-6 transition-all cursor-pointer ${
                            dragOver ? 'border-emerald-500 bg-emerald-500/5' : 'border-gray-800 hover:border-gray-700'
                        }`}
                    >
                        <input 
                            id="roast-input" 
                            type="file" 
                            accept=".pdf" 
                            className="hidden" 
                            onChange={(e) => setFile(e.target.files[0])} 
                        />
                        {file ? (
                            <div className="flex flex-col items-center">
                                <div className="p-4 bg-emerald-500/10 rounded-2xl mb-4">
                                    <ShieldCheck className="text-emerald-500" size={32} />
                                </div>
                                <p className="font-bold text-emerald-100">{file.name}</p>
                                <p className="text-gray-500 text-xs mt-1">Ready for analysis</p>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center">
                                <div className="p-4 bg-gray-800 rounded-2xl mb-4">
                                    <Upload className="text-gray-400" size={32} />
                                </div>
                                <p className="font-bold text-gray-300">Drop your resume here</p>
                                <p className="text-gray-500 text-xs mt-1">PDF format only</p>
                            </div>
                        )}
                    </div>

                    {error && (
                        <div className="flex items-center gap-2 text-red-400 text-sm font-bold justify-center mb-6">
                            <AlertCircle size={16} /> {error}
                        </div>
                    )}

                    <button 
                        onClick={handleUpload}
                        disabled={!file || loading}
                        className="w-full bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 disabled:opacity-30 text-white py-5 rounded-2xl font-black text-lg transition-all active:scale-95 shadow-xl shadow-emerald-500/20 flex items-center justify-center gap-3"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="animate-spin" /> Analyzing Resume...
                            </>
                        ) : (
                            "Start Analysis"
                        )}
                    </button>
                </div>

                <button 
                    onClick={() => navigate('/dashboard')}
                    className="mt-8 text-gray-500 font-bold hover:text-white transition-colors"
                >
                    Nevermind, I'm too sensitive
                </button>
            </div>
        </div>
    );
};

export default RoasterUploadPage;
