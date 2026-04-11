import React, { useState } from 'react';
import LandingPage from './LandingPage';
import VideoLesson from './VideoLesson';

/**
 * App Component
 * Manages the top-level navigation state between the 
 * Marketing/Course Discovery (LandingPage) and the 
 * Learning Environment (VideoLesson).
 */
function App() {
  // 'landing' shows the Course Catalog (CBSE/ICSE Class 3-12)
  // 'lesson' shows the Interactive AI Video Player
  const [view, setView] = useState('landing');

  // Function to handle moving from Landing Page to a specific lesson
  const startLesson = () => {
    window.scrollTo(0, 0); // Reset scroll position for the new view
    setView('lesson');
  };

  // Function to return to the course catalog
  const goBackHome = () => {
    setView('landing');
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {view === 'landing' ? (
        /* The Landing Page view. 
           We pass startLesson as a prop so the "Subject Cards" 
           can trigger the view change.
        */
        <LandingPage onStartLesson={startLesson} />
      ) : (
        /* The Interactive Lesson view.
           We wrap it in a relative container to place the "Back" button.
        */
        <div className="relative animate-in fade-in duration-500">
          {/* Floating Back Button */}
          <button 
            onClick={goBackHome}
            className="absolute top-6 left-6 z-[100] flex items-center gap-2 bg-slate-800/80 hover:bg-slate-700 text-white px-5 py-2 rounded-full backdrop-blur-md border border-slate-700 transition-all font-bold shadow-xl"
          >
            <span className="text-xl">←</span> 
            <span>Back to Courses</span>
          </button>

          {/* The Video Player with "Raise Hand" logic */}
          <VideoLesson />
          
          {/* Optional Footer for the Lesson View */}
          <footer className="py-10 text-center text-slate-500 text-sm">
            © 2026 Ascenda Pro - Powered by Veo & Gemini
          </footer>
        </div>
      )}
    </div>
  );
}

export default App;