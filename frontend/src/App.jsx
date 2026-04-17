import React, { useState, useEffect } from 'react';
import UserLearningHub from './UserLearningHub';
import VideoLesson from './VideoLesson';
import AdminDashboard from './components/AdminDashboard';

// Verified Production URL
export const API_BASE = "https://ascenda-production.up.railway.app"; 

function App() {
  const [view, setView] = useState('landing');
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);

  // 1. NEW: Fetch subjects from backend on load
  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        console.log("🚀 Fetching subjects from:", `${API_BASE}/api/admin/curriculum/regular/subjects`);
        const response = await fetch(`${API_BASE}/api/admin/curriculum/regular/subjects`);
        if (!response.ok) throw new Error("Failed to fetch");
        const data = await response.json();
        setSubjects(data);
      } catch (error) {
        console.error("❌ Error loading subjects:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchSubjects();
  }, []);

  // Navigation Handlers
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
    <div className="min-h-screen bg-slate-950 font-sans selection:bg-indigo-500/30 text-white">
      
      {/* 1. ADMIN PANEL VIEW */}
      {view === 'admin' ? (
        <div className="relative animate-in fade-in slide-in-from-bottom-2 duration-500">
          <button 
            onClick={goBackHome}
            className="fixed top-6 left-6 z-50 flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg font-bold shadow-lg transition-all"
          >
            ← Exit Admin
          </button>
          <AdminDashboard apiBase={API_BASE} />
        </div>
      ) : view === 'lesson' ? (
        
        /* 2. VIDEO LESSON VIEW */
        <div className="max-w-6xl mx-auto pt-24 px-6">
          <button 
            onClick={goBackHome}
            className="mb-8 flex items-center gap-2 bg-slate-800/80 hover:bg-slate-700 text-white px-5 py-2 rounded-full backdrop-blur-md border border-slate-700 transition-all font-bold shadow-xl hover:scale-105"
          >
            <span className="text-xl">←</span> <span>Back to Courses</span>
          </button>
          
          <VideoLesson />
          
          <footer className="py-10 text-center text-slate-600 text-sm border-t border-slate-900">
            © 2026 Ascenda Pro — Modular Learning Systems
          </footer>
        </div>
      ) : (

        /* 3. LEARNING HUB VIEW (The Primary User View) */
        <div className="animate-in fade-in duration-700">
          <UserLearningHub 
            subjects={subjects} 
            loading={loading} 
            onStartLesson={startLesson} 
          />
          
          <footer className="py-12 text-center bg-[#05070a] border-t border-slate-900/50">
            <button 
              onClick={openAdmin}
              className="text-slate-800 hover:text-indigo-400 text-[10px] transition-all tracking-[0.2em] uppercase font-medium group"
            >
              <span className="opacity-50 group-hover:opacity-100">Access</span> Admin Portal
            </button>
          </footer>
        </div>
      )}
    </div>
  );
}

export default App;