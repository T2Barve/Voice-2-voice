import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin, Briefcase, ExternalLink, Filter, Loader2, ArrowLeft, Building2, Clock } from 'lucide-react';

const EXPRESS = 'http://localhost:5000';

const JobSearchPage = () => {
    const navigate = useNavigate();
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchParams, setSearchParams] = useState({
        role: '',
        location: '',
        country: 'in'
    });
    const [searched, setSearched] = useState(false);

    // Initial search based on user's last role if available
    useEffect(() => {
        const storedRole = localStorage.getItem('selectedRole');
        if (storedRole) {
            setSearchParams(prev => ({ ...prev, role: storedRole }));
            handleSearch(null, { ...searchParams, role: storedRole });
        }
    }, []);

    const handleSearch = async (e, overrideParams = null) => {
        if (e) e.preventDefault();
        
        const params = overrideParams || searchParams;
        if (!params.role) return;

        setLoading(true);
        setSearched(true);
        try {
            const token = localStorage.getItem('token');
            const queryString = new URLSearchParams({
                role: params.role,
                location: params.location,
                country: params.country,
                permanent: params.permanent || '0',
                contract: params.contract || '0'
            }).toString();

            const res = await fetch(`${EXPRESS}/api/jobs/search?${queryString}`, {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            });
            const data = await res.json();
            
            if (data.success) {
                setJobs(data.results);
            }
        } catch (error) {
            console.error('Job search failed:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-black text-white font-sans selection:bg-emerald-500/30">
            {/* Header / Nav */}
            <nav className="border-b border-gray-800 bg-black/50 backdrop-blur-xl sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button 
                            onClick={() => navigate('/dashboard')}
                            className="p-2 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-white"
                        >
                            <ArrowLeft size={20} />
                        </button>
                        <div>
                            <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                                Job Opportunities
                            </h1>
                            <p className="text-xs text-gray-500 font-medium uppercase tracking-widest">Powered by Adzuna</p>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-5xl mx-auto px-6 py-12">
                {/* Search Hero Section */}
                <section className="mb-16">
                    <div className="text-center mb-10">
                        <h2 className="text-4xl font-black mb-4">Find your next <span className="text-emerald-500">Big Break</span></h2>
                        <p className="text-gray-400 max-w-lg mx-auto">Browse live job openings from top companies around the world, tailored to your interview preparation.</p>
                    </div>

                    <form 
                        onSubmit={handleSearch}
                        className="bg-gray-900/40 border border-gray-800 p-2 rounded-3xl backdrop-blur-xl shadow-2xl flex flex-col gap-2"
                    >
                        <div className="flex flex-col md:flex-row gap-2">
                            <div className="flex-1 flex items-center px-4 py-3 gap-3 border-b md:border-b-0 md:border-r border-gray-800 bg-gray-800/20 rounded-2xl md:rounded-r-none">
                                <Search className="text-emerald-500" size={20} />
                                <input 
                                    type="text"
                                    placeholder="Job Role (e.g. SDE, Frontend)"
                                    value={searchParams.role}
                                    onChange={(e) => setSearchParams({...searchParams, role: e.target.value})}
                                    className="bg-transparent border-none outline-none w-full text-white placeholder:text-gray-600 font-medium"
                                />
                            </div>
                            <div className="flex-1 flex items-center px-4 py-3 gap-3 border-b md:border-b-0 md:border-r border-gray-800 bg-gray-800/20 rounded-2xl md:rounded-none">
                                <MapPin className="text-cyan-500" size={20} />
                                <input 
                                    type="text"
                                    placeholder="Location (City, Country)"
                                    value={searchParams.location}
                                    onChange={(e) => setSearchParams({...searchParams, location: e.target.value})}
                                    className="bg-transparent border-none outline-none w-full text-white placeholder:text-gray-600 font-medium"
                                />
                            </div>
                            <div className="md:w-32 flex items-center px-4 py-3 gap-2 bg-gray-800/20 rounded-2xl md:rounded-l-none">
                                <select 
                                    value={searchParams.country}
                                    onChange={(e) => setSearchParams({...searchParams, country: e.target.value})}
                                    className="bg-transparent border-none outline-none w-full text-gray-400 font-bold appearance-none cursor-pointer hover:text-white transition-colors"
                                >
                                    <option value="in">India</option>
                                    <option value="gb">UK</option>
                                    <option value="us">USA</option>
                                    <option value="ca">Canada</option>
                                    <option value="au">Australia</option>
                                </select>
                            </div>
                        </div>
                        
                        <div className="flex flex-col md:flex-row items-center justify-between gap-4 px-4 py-2">
                            <div className="flex items-center gap-6">
                                <label className="flex items-center gap-2 cursor-pointer group">
                                    <input 
                                        type="checkbox" 
                                        checked={searchParams.permanent === '1'}
                                        onChange={(e) => setSearchParams({...searchParams, permanent: e.target.checked ? '1' : '0'})}
                                        className="w-4 h-4 rounded border-gray-800 bg-gray-900 text-emerald-500 focus:ring-emerald-500" 
                                    />
                                    <span className="text-xs font-bold text-gray-500 group-hover:text-gray-300">Full-time Only</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer group">
                                    <input 
                                        type="checkbox" 
                                        checked={searchParams.contract === '1'}
                                        onChange={(e) => setSearchParams({...searchParams, contract: e.target.checked ? '1' : '0'})}
                                        className="w-4 h-4 rounded border-gray-800 bg-gray-900 text-cyan-500 focus:ring-cyan-500" 
                                    />
                                    <span className="text-xs font-bold text-gray-500 group-hover:text-gray-300">Contractual</span>
                                </label>
                            </div>

                            <button 
                                type="submit"
                                disabled={loading}
                                className="w-full md:w-auto bg-emerald-500 hover:bg-emerald-400 text-black px-12 py-4 rounded-2xl font-black transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-50"
                            >
                                {loading ? <Loader2 className="animate-spin" size={20} /> : "Search Opportunities"}
                            </button>
                        </div>
                    </form>
                </section>

                {/* Results Section */}
                <section>
                    {!searched ? (
                        <div className="text-center py-20 bg-gray-900/20 rounded-3xl border border-dashed border-gray-800">
                            <div className="w-16 h-16 bg-gray-900 rounded-2xl flex items-center justify-center mx-auto mb-4 text-3xl">🔍</div>
                            <h3 className="text-xl font-bold mb-2">Search to see listings</h3>
                            <p className="text-gray-500 text-sm">Enter a role and location to browse live opportunities.</p>
                        </div>
                    ) : loading ? (
                        <div className="flex flex-col items-center justify-center py-32">
                            <div className="w-12 h-12 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin mb-4"></div>
                            <p className="text-gray-400 font-medium">Fetching the latest opportunities...</p>
                        </div>
                    ) : jobs.length === 0 ? (
                        <div className="text-center py-20">
                            <p className="text-gray-500">No jobs found matching your criteria. Try adjusting your search.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {jobs.map((job, idx) => (
                                <div 
                                    key={job.id || idx} 
                                    className="group bg-gray-900/40 border border-gray-800 rounded-3xl p-6 hover:border-emerald-500/50 transition-all hover:shadow-[0_0_30px_rgba(16,185,129,0.05)] flex flex-col justify-between"
                                >
                                    <div>
                                        <div className="flex justify-between items-start mb-4">
                                            <div className="p-3 bg-gray-800 rounded-2xl text-emerald-500">
                                                <Building2 size={24} />
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="text-[10px] font-bold px-2 py-1 bg-emerald-500/10 rounded-full text-emerald-400 uppercase tracking-widest border border-emerald-500/20">
                                                    {job.source?.display_name || job.category?.label || "Verified"}
                                                </div>
                                                {new Date(job.created) > new Date(Date.now() - 48*60*60*1000) && (
                                                    <div className="text-[10px] font-bold px-2 py-1 bg-amber-500/10 rounded-full text-amber-400 uppercase tracking-widest border border-amber-500/20">
                                                        New
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <h3 className="text-lg font-bold text-white mb-1 leading-tight group-hover:text-emerald-400 transition-colors">
                                            {job.title?.replace(/<\/?[^>]+(>|$)/g, "")}
                                        </h3>
                                        <p className="text-emerald-500 font-bold text-sm mb-3">
                                            {job.company?.display_name}
                                        </p>
                                        <div className="flex flex-wrap gap-4 text-xs text-gray-500 font-medium">
                                            <div className="flex items-center gap-1.5">
                                                <MapPin size={14} className="text-gray-600" />
                                                {job.location?.display_name}
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <Clock size={14} className="text-gray-600" />
                                                {new Date(job.created).toLocaleDateString()}
                                            </div>
                                        </div>
                                        <div className="mt-4 text-sm text-gray-400 line-clamp-3">
                                            {job.description?.replace(/<\/?[^>]+(>|$)/g, "")}
                                        </div>
                                    </div>
                                    
                                    <div className="mt-6 flex items-center justify-between pt-6 border-t border-gray-800/50">
                                        <div className="text-white font-black">
                                            {job.salary_min ? `₹${(job.salary_min/1).toLocaleString()}+` : "Salary Undisclosed"}
                                        </div>
                                        <a 
                                            href={job.redirect_url} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-2 text-xs font-bold bg-white text-black px-4 py-2 rounded-xl hover:bg-emerald-500 transition-all active:scale-95"
                                        >
                                            Apply Now <ExternalLink size={14} />
                                        </a>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            </main>
        </div>
    );
};

export default JobSearchPage;
