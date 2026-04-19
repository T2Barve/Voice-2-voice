import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, Code, Database, Cpu, Brain } from 'lucide-react';

const roles = [
  { id: 'SDE', title: 'Software Engineer', icon: Code, description: 'General full-stack or systems software engineering role.' },
  { id: 'Backend Engineer', title: 'Backend Engineer', icon: Database, description: 'Focus on APIs, databases, and microservices architecture.' },
  { id: 'Frontend Engineer', title: 'Frontend Engineer', icon: Briefcase, description: 'Focus on UI/UX, React, and modern web interfaces.' },
  { id: 'ML Engineer', title: 'ML Engineer', icon: Brain, description: 'Focus on machine learning pipelines and model deployment.' },
  { id: 'Data Engineer', title: 'Data Engineer', icon: Cpu, description: 'Focus on data pipelines, ETL, and big data processing.' },
];

const RoleSelectionPage = () => {
  const navigate = useNavigate();

  const handleSelect = (roleId) => {
    localStorage.setItem('role', roleId);
    navigate('/resume-upload');
  };

  return (
    <div className="min-h-screen bg-black text-white p-8 flex flex-col items-center justify-center">
      <div className="max-w-4xl w-full">
        <h1 className="text-4xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
          Target Your Interview
        </h1>
        <p className="text-gray-400 mb-12 text-lg">Select the role you are interviewing for to customize the experience.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {roles.map((role) => (
            <div 
              key={role.id}
              onClick={() => handleSelect(role.id)}
              className="group relative p-6 bg-zinc-900 border border-zinc-800 rounded-2xl cursor-pointer hover:border-blue-500 transition-all duration-300 transform hover:-translate-y-1"
            >
              <div className="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity" />
              <div className="mb-4 p-3 bg-zinc-800 rounded-lg w-fit group-hover:bg-blue-500/20 group-hover:text-blue-400 transition-colors">
                <role.icon size={28} />
              </div>
              <h3 className="text-xl font-semibold mb-2">{role.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{role.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RoleSelectionPage;
