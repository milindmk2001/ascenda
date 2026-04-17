import React, { useState } from 'react';

const UserLearningHub = ({ subjects, loading }) => {
  const [activeVideo, setActiveVideo] = useState(null);
  const [selectedName, setSelectedName] = useState("");

  if (loading) return <div className="p-20 text-center animate-pulse text-gray-500">Connecting to Ascenda Database...</div>;

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-8">Your Curriculum</h2>
      
      {subjects.length === 0 ? (
        <div className="p-20 border-2 border-dashed border-slate-800 rounded-3xl text-center text-slate-600">
          No subjects found for this selection.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {subjects.map((sub) => (
            <div 
              key={sub.id} 
              onClick={() => {
                setActiveVideo(sub.video_url);
                setSelectedName(sub.name);
              }}
              className="bg-slate-900 p-6 rounded-2xl border border-slate-800 hover:border-indigo-500 cursor-pointer transition-all"
            >
              <div className="text-3xl mb-4">📚</div>
              <h3 className="font-bold text-lg">{sub.name}</h3>
              <p className="text-slate-500 text-sm uppercase">{sub.subject_code}</p>
            </div>
          ))}
        </div>
      )}

      {activeVideo && (
        <div className="mt-12 bg-black rounded-3xl overflow-hidden border border-slate-800 shadow-2xl">
          <div className="p-6 flex justify-between items-center bg-slate-900/50">
            <h3 className="text-xl font-bold">{selectedName}</h3>
            <button onClick={() => setActiveVideo(null)} className="text-slate-400 hover:text-white">
               {/* FIXED SVG PATH */}
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="aspect-video">
            <iframe className="w-full h-full" src={activeVideo} allowFullScreen title="video"></iframe>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserLearningHub;