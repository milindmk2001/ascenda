import React from 'react';

const UserLearningHub = ({ subjects, loading, trackName, gradeName, onCourseSelect }) => {

  if (loading) {
    return (
      <div className="flex-grow flex items-center justify-center min-h-[50vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500" />
          <p className="text-slate-500 font-mono text-xs tracking-wider uppercase animate-pulse">
            Loading Courses...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto w-full p-8 flex-grow">

      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-black tracking-tight text-white uppercase">
          Your Curriculum
        </h2>
        <p className="text-xs font-bold font-mono text-slate-500 uppercase tracking-widest mt-1">
          Active Portfolio:{' '}
          <span className="text-slate-400">{trackName}</span>
          {gradeName && gradeName !== "Global" && (
            <> // <span className="text-slate-400">{gradeName}</span></>
          )}
        </p>
      </div>

      {/* Empty state */}
      {!subjects || subjects.length === 0 ? (
        <div className="flex flex-col items-center justify-center border-2 border-dashed border-slate-900/60 rounded-3xl p-20 text-center min-h-[35vh]">
          <svg
            className="w-8 h-8 text-slate-700 mb-3"
            fill="none" stroke="currentColor" strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
          </svg>
          <p className="text-slate-500 font-mono text-xs uppercase tracking-wide">
            No courses found for this selection.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {subjects.map((sub) => (
            <div
              key={sub.id}
              onClick={() => onCourseSelect && onCourseSelect(sub)}
              className="group p-6 bg-[#0a101f]/70 border border-slate-900 rounded-2xl hover:border-emerald-500/30 hover:bg-[#0d1527] transition-all duration-300 cursor-pointer select-none relative overflow-hidden"
            >
              {/* Top accent line on hover */}
              <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-emerald-500/0 to-transparent group-hover:via-emerald-500/40 transition-all duration-500" />

              {/* Icon */}
              <div className="w-12 h-12 rounded-xl bg-emerald-500/5 border border-emerald-500/10 flex items-center justify-center text-emerald-400 mb-5 group-hover:scale-105 group-hover:bg-emerald-500/10 transition-all duration-300">
                <svg
                  className="w-6 h-6"
                  fill="none" stroke="currentColor" strokeWidth="1.75"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>

              {/*
                FIX: API returns subject_name (e.g. "Physics") and title (e.g. "IIT JEE Physics")
                     Old code used sub.name which doesn't exist → blank card
              */}
              <h3 className="font-bold text-lg text-slate-100 group-hover:text-emerald-400 transition-colors duration-200">
                {sub.subject_name || sub.title}
              </h3>

              {/* Full course title below subject name */}
              <p className="text-xs font-medium text-slate-400 leading-relaxed mt-1.5 group-hover:text-slate-300 transition-colors duration-200">
                {sub.title}
              </p>

              {/* Subject code badge */}
              <div className="mt-3">
                <span className="text-[10px] font-mono text-slate-600 bg-slate-900/60 px-2 py-0.5 rounded-md">
                  {sub.subject_code}
                </span>
              </div>

              {/* Enter arrow */}
              <div className="mt-4 flex items-center gap-1.5 text-[10px] font-bold font-mono uppercase tracking-widest text-slate-600 group-hover:text-emerald-400/80 transition-colors duration-300">
                <span>Enter Canvas</span>
                <svg
                  className="w-3 h-3 transform group-hover:translate-x-1 transition-transform duration-200"
                  fill="none" stroke="currentColor" strokeWidth="2.5"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UserLearningHub;
