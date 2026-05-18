import React from 'react';

const UserLearningHub = ({ subjects, loading, trackName, gradeName, onCourseSelect }) => {

  if (loading) {
    return (
      <div className="flex-grow flex items-center justify-center min-h-[50vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
          <p className="text-slate-500 font-mono text-xs tracking-wider uppercase animate-pulse">
            Connecting to Ascenda Database...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto w-full p-8 flex-grow">
      {/* Active Filter Context Portfolio Subheading */}
      <div className="mb-8">
        <h2 className="text-2xl font-black tracking-tight text-white uppercase">
          Your Curriculum
        </h2>
        <p className="text-xs font-bold font-mono text-slate-500 uppercase tracking-widest mt-1">
          Active Portfolio: <span className="text-slate-400">{trackName}</span> 
          {gradeName && gradeName !== "Global" && <> // <span className="text-slate-400">{gradeName}</span></>}
        </p>
      </div>
      
      {subjects.length === 0 ? (
        <div className="flex flex-col items-center justify-center border-2 border-dashed border-slate-900 rounded-3xl p-20 text-center min-h-[35vh]">
          <p className="text-slate-500 font-medium">
            No active course blueprints found matching this selection matrix.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {subjects.map((sub) => (
            <div 
              key={sub.id} 
              onClick={() => {
                if (onCourseSelect) {
                  // Safely routes directly to your nested CourseReader interface
                  onCourseSelect(sub);
                }
              }}
              className="group bg-slate-900/40 border border-slate-900 hover:border-slate-800 rounded-2xl p-6 flex flex-col items-center justify-center text-center transition-all duration-300 hover:translate-y-[-2px] hover:bg-slate-900 cursor-pointer select-none"
            >
              {/* Central Geometric Icon Layout */}
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 mb-4 group-hover:scale-105 transition-transform duration-300 shadow-lg">
                <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              
              <h3 className="font-bold text-base text-slate-200 group-hover:text-white transition-colors">
                {sub.name}
              </h3>
              
              {/* Dynamic Database Badge String Layout */}
              <span className="text-[10px] mt-3 px-2.5 py-0.5 font-mono font-black rounded bg-slate-950 border border-slate-800 text-slate-400 uppercase tracking-widest shadow-inner">
                {sub.meta_tag || trackName}-{sub.subject_code}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UserLearningHub;