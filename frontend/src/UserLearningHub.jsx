import React, { useState } from 'react';

const UserLearningHub = ({ subjects }) => {
  // 1. State to track which video is currently playing
  const [activeVideo, setActiveVideo] = useState(null);
  const [selectedSubjectName, setSelectedSubjectName] = useState("");

  const handleSubjectClick = (subject) => {
    // 2. Check if the subject from the API has the new video_url field
    if (subject.video_url) {
      setActiveVideo(subject.video_url);
      setSelectedSubjectName(subject.name);
      
      // Optional: Smooth scroll down to the video player
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    } else {
      alert("No video link found for this subject. Did you run the SQL update?");
    }
  };

  return (
    <div className="p-6">
      {/* Your existing Subject Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {subjects.map((sub) => (
          <div 
            key={sub.id} 
            onClick={() => handleSubjectClick(sub)}
            className="cursor-pointer p-4 bg-gray-800 rounded-xl hover:border-blue-500 border-2 border-transparent transition-all"
          >
            <div className="text-3xl mb-2">📖</div>
            <h3 className="font-bold text-white">{sub.name}</h3>
            <p className="text-sm text-gray-400">{sub.subject_code}</p>
          </div>
        ))}
      </div>

      {/* 3. The "Udemy-style" Video Player Frame */}
      {activeVideo && (
        <div className="mt-12 p-6 bg-black rounded-2xl border border-gray-700 shadow-2xl">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-white">Now Playing: {selectedSubjectName}</h2>
            <button 
              onClick={() => setActiveVideo(null)}
              className="text-gray-400 hover:text-white text-xl"
            >
              ✖
            </button>
          </div>
          
          <div className="relative pb-[56.25%] h-0 overflow-hidden rounded-lg">
            <iframe
              className="absolute top-0 left-0 w-full h-full"
              src={activeVideo}
              title="Subject Video"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserLearningHub;