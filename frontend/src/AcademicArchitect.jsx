import React from 'react';

/**
 * Academic Architect Component
 * Fixed version: Now triggers onCourseSelect when a card is clicked.
 */
function AcademicArchitect({ 
  subjects, 
  loading, 
  selectedBoard, 
  selectedGrade, 
  onBack,
  onCourseSelect // Added missing prop to handle navigation
}) {
  return (
    <div className="p-8 max-w-7xl mx-auto flex-grow">
      {/* Header Section mirrored from homepage style */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Academic <span className="text-emerald-500">Architect</span></h1>
          <p className="text-slate-400 mt-1 font-medium">
            Drafting {selectedBoard} {selectedGrade} Curriculum
          </p>
        </div>
        <button 
          onClick={onBack}
          className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs font-bold uppercase tracking-widest hover:bg-slate-800 transition-all text-slate-400 hover:text-white"
        >
          ← Return to Hub
        </button>
      </div>

      {/* Subjects Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-500"></div>
          <p className="text-slate-500 font-mono text-xs uppercase tracking-widest">Loading Architect Data...</p>
        </div>
      ) : subjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {subjects.map((subject) => (
            <div 
              key={subject.id} 
              onClick={() => onCourseSelect(subject)} // Fixed: Triggers view change in App.jsx
              className="group relative bg-slate-900/40 border border-slate-800/50 rounded-2xl p-6 hover:border-emerald-500/50 transition-all cursor-pointer backdrop-blur-sm"
            >
              <div className="flex justify-between items-start mb-6">
                <div className="p-3 bg-emerald-500/10 rounded-xl group-hover:bg-emerald-500/20 transition-colors">
                  <span className="text-2xl">📖</span>
                </div>
                <div className="text-right">
                  <span className="block text-[10px] font-mono text-slate-500 uppercase tracking-tighter">
                    {subject.subject_code || 'DOC-GEN'} {/* Updated to match backend field 'subject_code' */}
                  </span>
                </div>
              </div>
              
              <h3 className="text-xl font-bold mb-2 group-hover:text-emerald-400 transition-colors">
                {subject.name}
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed mb-8">
                Build text modules, articles, and interactive documentation for {subject.name}.
              </p>
              
              <div className="flex items-center gap-2 text-emerald-500 text-[10px] font-black uppercase tracking-[0.2em] opacity-70 group-hover:opacity-100 transition-all">
                Launch Editor <span className="group-hover:translate-x-1 transition-transform">→</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-20 text-center border-2 border-dashed border-slate-900 rounded-3xl">
          <p className="text-slate-500 uppercase text-xs font-bold tracking-widest">
            No subjects found for this selection
          </p>
        </div>
      )}
    </div>
  );
}

export default AcademicArchitect;