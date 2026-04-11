import React, { useState } from 'react';
import LandingPage from './LandingPage';
import VideoLesson from './VideoLesson';
import AdminDashboard from './components/AdminDashboard';

/**
 * Verified Production URL from Railway Settings
 */
export const API_BASE = "https://ascenda-production.up.railway.app"; 

function App() {
  const [view, setView] = useState('landing');

  const startLesson = () => {
    window.scrollTo(0, 0);
    setView('lesson');
  };

  const goBackHome = () => {
    window.scrollTo(0, 0);
    setView('landing');
  };

  const openAdmin = () => {
    window.scrollTo(0, 0);
    setView('admin');
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {view === 'admin' ? (
        <div className="relative">
          <button 
            onClick={goBackHome}
            className="fixed top-6 left-6 z-[100] flex items-center gap-2 bg-slate-800/80 hover:bg-slate-700 text-white px-5 py-2 rounded-full backdrop-blur-md border border-slate-700 transition-all font-bold shadow-xl"
          >
            <span>←</span> <span>Exit Admin</span>
          </button>
          <AdminDashboard apiBase={API_BASE} />
        </div>
      ) : view === 'lesson' ? (
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
        <>
          <LandingPage onStartLesson={startLesson} />
          <footer className="py-12 text-center bg-slate-950">
            <button 
              onClick={openAdmin}
              className="text-slate-800 hover:text-slate-600 text-[10px] transition-colors tracking-widest uppercase"
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