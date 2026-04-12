import React, { useState, useEffect } from 'react';
import LandingPage from './LandingPage';
import VideoLesson from './VideoLesson';
import AdminDashboard from './components/AdminDashboard';

// Verified Production URL from your Railway settings
export const API_BASE = "https://ascenda-production.up.railway.app"; 

function App() {
  const [view, setView] = useState('landing');

  // Logs to browser console to confirm the endpoint connection
  useEffect(() => {
    console.log("🚀 Ascenda is connecting to:", API_BASE);
  }, []);

  // Navigation Handlers with Scroll Reset
  const startLesson = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setView('lesson');
  };

  const goBackHome = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setView('landing');
  };

  const openAdmin = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setView('admin');
  };

  return (
    <div className="min-h-screen bg-slate-950 font-sans selection:bg-indigo-500/30">
      
      {/* 1. ADMIN PANEL VIEW */}
      {view === 'admin' ? (
        <div className="relative animate-in fade-in slide-in-from-bottom-2 duration-500">
          <button 
            onClick={goBackHome}
            className="fixed top-6 left-6 z-[100] flex items-center gap-2 bg-slate-800/80 hover:bg-slate-700 text-white px-5 py-2 rounded-full backdrop-blur-md border border-slate-700 transition-all font-bold shadow-2xl hover:scale-105 active:scale-95"
          >
            <span className="text-lg">←</span> <span>Exit Admin</span>
          </button>
          
          {/* Passing the correct API_BASE to the dashboard */}
          <AdminDashboard apiBase={API_BASE} />
        </div>
      ) : 
      
      /* 2. LESSON PLAYER VIEW */
      view === 'lesson' ? (
        <div className="relative animate-in fade-in zoom-in-95 duration-500">
          <button 
            onClick={goBackHome}
            className="absolute top-6 left-6 z-[100] flex items-center gap-2 bg-slate-800/80 hover:bg-slate-700 text-white px-5 py-2 rounded-full backdrop-blur-md border border-slate-700 transition-all font-bold shadow-xl hover:scale-105"
          >
            <span className="text-xl">←</span> <span>Back to Courses</span>
          </button>
          
          <VideoLesson />
          
          <footer className="py-10 text-center text-slate-600 text-sm border-t border-slate-900">
            © 2026 Ascenda Pro — Modular Learning Systems
          </footer>
        </div>
      ) : (

        /* 3. LANDING PAGE VIEW (Default) */
        <div className="animate-in fade-in duration-700">
          <LandingPage onStartLesson={startLesson} />
          
          <footer className="py-12 text-center bg-slate-950 border-t border-slate-900/50">
            <button 
              onClick={openAdmin}
              className="text-slate-800 hover:text-indigo-400 text-[10px] transition-all tracking-[0.2em] uppercase font-medium group"
            >
              <span className="opacity-50 group-hover:opacity-100">Access</span> Admin Portal
            </button>
            <p className="mt-4 text-slate-900 text-[9px] uppercase tracking-widest">
              Build Version 1.0.4-Stable
            </p>
          </footer>
        </div>
      )}
    </div>
  );
}

export default App;