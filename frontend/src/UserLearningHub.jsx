import React, { useState } from 'react';

const UserLearningHub = ({ subjects }) => {
  // 1. State for the video player
  const [activeVideo, setActiveVideo] = useState(null);
  const [selectedSubjectName, setSelectedSubjectName] = useState("");

  // 2. Defensive Check: Prevent "reading 'map' of undefined" error
  // This handles the gap between the page loading and the API returning data
  if (!subjects || subjects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-20 text-gray-400">
        <div className="animate-spin text-4xl mb-4">🔄</div>
        <p className="text-xl">Loading your curriculum subjects...</p>
      </div>
    );
  }

  const handleSubjectClick = (subject) => {
    // 3. Logic to trigger video player
    if (subject.video_url) {
      setActiveVideo(subject.video_url);
      setSelectedSubjectName(subject.name);
      
      // Smooth scroll to player for better mobile UX
      setTimeout(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
      }, 100);
    } else {
      alert("No video link found for this subject. Ensure you updated the database.");
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-white mb-6">Select a Subject to Start Learning</h2>
      
      {/* Subject Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {subjects.map((sub) => (
          <div 
            key={sub.id} 
            onClick={() => handleSubjectClick(sub)}
            className={`cursor-pointer p-6 rounded-2xl border-2 transition-all duration-300 bg-gray-900/50 backdrop-blur-sm
              ${activeVideo && selectedSubjectName === sub.name 
                ? 'border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]' 
                : 'border-gray-800 hover:border-gray-600 hover:scale-105'}`}
          >
            <div className="bg-blue-600/20 w-12 h-12 rounded-lg flex items-center justify-center text-2xl mb-4">
              📚
            </div>
            <h3 className="font-bold text-lg text-white">{sub.name}</h3>
            <p className="text-sm text-gray-500 mt-1 uppercase tracking-wider">
              {sub.subject_code}
            </p>
          </div>
        ))}
      </div>

      {/* 4. The "Udemy-style" Video Player Frame */}
      {activeVideo && (
        <div className="mt-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="bg-black rounded-3xl border border-gray-800 shadow-2xl overflow-hidden">
            {/* Player Header */}
            <div className="flex justify-between items-center p-6 bg-gray-900/80 border-b border-gray-800">
              <div>
                <span className="text-blue-400 text-xs font-bold uppercase tracking-widest">Now Learning</span>
                <h2 className="text-2xl font-bold text-white">{selectedSubjectName}</h2>
              </div>
              <button 
                onClick={() => setActiveVideo(null)}
                className="p-2 hover:bg-gray-800 rounded-full text-gray-400 hover:text-white transition-colors"
                title="Close Player"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Video Container */}
            <div className="relative pb-[56.25%] h-0 bg-black">
              <iframe
                className="absolute top-0 left-0 w-full h-full"
                src={activeVideo}
                title={`Learning: ${selectedSubjectName}`}
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              ></iframe>
            </div>
            
            {/* Course Details Placeholder (Visible in your image_e7d8ef.png) */}
            <div className="p-8 bg-gray-900/30">
              <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-tighter mb-4">Course Units & Lessons</h4>
              <div className="p-4 rounded-xl bg-black/40 border border-dashed border-gray-700 text-center text-gray-500 italic">
                Units for {selectedSubjectName} are currently being updated in the curriculum database.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserLearningHub;