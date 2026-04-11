import React, { useState } from 'react';
import LandingPage from './LandingPage';
import VideoLesson from './VideoLesson';
import AdminDashboard from './components/AdminDashboard'; // Ensure path is correct

/**
 * App Component
 * Manages navigation between Landing, Video Lessons, and the Admin Panel.
 */
function App() {
  // Views: 'landing', 'lesson', or 'admin'
  const [view, setView] = useState('landing');

  const startLesson = () => {
    window.scrollTo(0, 0);
    setView('lesson');
  };

  const goBackHome = () => {
    setView('landing');
  };

  const openAdmin = () => {
    window.scrollTo(0, 0);
    setView('admin');
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* 1. ADMIN VIEW */}
      {view === 'admin' ? (
        <div className="relative">
          <button 
            onClick={goBackHome}
            className="fixed top-6 left-6 z-[100] flex items-center gap-2 bg-slate-800/80 hover:bg-slate-700 text-white px-5 py-2 rounded-full backdrop-blur-md border border-slate-700 transition-all font-bold shadow-xl"
          >
            <span>←</span> <span>Exit Admin</span>
          </button>
          <AdminDashboard />
        </div>
      ) : 
      
      /* 2. LESSON VIEW */
      view === 'lesson' ? (
        <div className="relative animate-in fade-in duration-500">
          <button 
            onClick={goBackHome}
            className="absolute top-6 left-6 z-[100] flex items-center gap-2 bg-slate-800/80 hover:bg-slate-700 text-white px-5 py-2 rounded-full backdrop-blur-md border border-slate-700 transition-all font-bold shadow-xl"
          >
            <span className="text-xl">←</span> <span>Back to Courses</span>
          </button>
          <VideoLesson />
          <footer className="py-10 text-center text-slate-500 text-sm">
            © 2026 Ascenda Pro - Powered by Veo & Gemini
          </footer>
        </div>
      ) : (

        /* 3. LANDING PAGE (DEFAULT) */
        <>
          <LandingPage onStartLesson={startLesson} />
          {/* Secret Admin Button in Footer */}
          <footer className="py-8 text-center">
            <button 
              onClick={openAdmin}
              className="text-slate-800 hover:text-slate-700 text-[10px] transition-colors"
            >
              Admin Portal
            </button>
          </footer>
        </>
      )}
    </div>
  );
}

export default App;