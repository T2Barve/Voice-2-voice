import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Code2, Settings2, Laptop } from 'lucide-react';

const types = [
  { 
    id: 'dsa', 
    title: 'Algorithms & Data Structures', 
    icon: Code2, 
    description: 'LeetCode-style problems focusing on time/space complexity and logic.',
    color: 'from-amber-400 to-orange-500'
  },
  { 
    id: 'technical', 
    title: 'Technical Round', 
    icon: Settings2, 
    description: 'Deep-dive into tech stack, internals, and domain-specific knowledge.',
    color: 'from-blue-400 to-indigo-500'
  },
  { 
    id: 'case-study', 
    title: 'Case Study / System Design', 
    icon: Laptop, 
    description: 'Architecting systems, scaling solutions, and real-world engineering trade-offs.',
    color: 'from-emerald-400 to-teal-500'
  },
];

const InterviewTypePage = () => {
  const navigate = useNavigate();

  const handleSelect = (typeId) => {
    localStorage.setItem('interviewType', typeId);
    navigate('/interview');
  };

  return (
    <div className="min-h-screen bg-black text-white p-8 flex flex-col items-center justify-center">
      <div className="max-w-4xl w-full">
        <h1 className="text-4xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
          Choose Your Workflow
        </h1>
        <p className="text-gray-400 mb-12 text-lg">Pick the interview category you'd like to practice today.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {types.map((type) => (
            <div 
              key={type.id}
              onClick={() => handleSelect(type.id)}
              className="group cursor-pointer"
            >
              <div className="relative h-full p-8 bg-zinc-900 border border-zinc-800 rounded-2xl transition-all duration-300 group-hover:border-white/20 group-hover:-translate-y-2 overflow-hidden">
                {/* Background Glow */}
                <div className={`absolute -right-12 -top-12 w-32 h-32 bg-gradient-to-br ${type.color} opacity-10 blur-3xl group-hover:opacity-20 transition-opacity`} />
                
                <div className={`mb-6 p-4 bg-zinc-800 rounded-xl w-fit group-hover:bg-gradient-to-br ${type.color} transition-all duration-500`}>
                  <type.icon size={32} className="group-hover:scale-110 transition-transform" />
                </div>
                
                <h3 className="text-2xl font-bold mb-4 group-hover:text-white transition-colors">{type.title}</h3>
                <p className="text-gray-500 leading-relaxed group-hover:text-gray-400 transition-colors">{type.description}</p>
                
                <div className="mt-8 flex items-center text-sm font-medium text-white/40 group-hover:text-white transition-colors">
                  Start Session
                  <svg className="ml-2 w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default InterviewTypePage;
