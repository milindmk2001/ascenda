import React from 'react';

function AcademicArchitect({ subjects, loading, onBack }) {
  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Academic Architect</h1>
          <p className="text-slate-400 mt-2">Drafting text-based curriculum and W3Schools-style documentation.</p>
        </div>
        <button 
          onClick={onBack}
          className="text-xs uppercase tracking-widest text-slate-500 hover:text-white transition-colors"
        >
          ← Back to Hub
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {subjects.map((subject) => (
            <div 
              key={subject.id} 
              className="group relative bg-slate-900/50 border border-slate-800 rounded-2xl p-6 hover:border-emerald-500/50 transition-all cursor-pointer"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-emerald-500/10 rounded-xl group-hover:bg-emerald-500/20 transition-colors">
                  <span className="text-2xl">✍️</span>
                </div>
                <span className="text-[10px] font-mono text-slate-500 uppercase">{subject.code}</span>
              </div>
              
              <h3 className="text-xl font-bold mb-1">{subject.name}</h3>
              <p className="text-sm text-slate-400 mb-6">Manage text modules and interactive articles.</p>
              
              <div className="flex items-center text-emerald-400 text-xs font-bold uppercase tracking-widest group-hover:gap-2 transition-all">
                Open Editor <span>→</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default AcademicArchitect;