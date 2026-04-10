import React, { useState, useEffect } from 'react'

function App() {
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // AUDIT FIX: Ensure API_URL never ends in a trailing slash to prevent double-slashes in fetch
  const API_URL = (import.meta.env.VITE_API_URL || 'https://ascenda-production.up.railway.app').replace(/\/$/, "");

  const startLesson = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s Timeout for performance audit

      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: "Explain Coulomb's Law like a Physics Mentor." }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) throw new Error(`Server responded with ${response.status}`);

      const data = await response.json();
      setLesson(data.response);
    } catch (err) {
      console.error("Audit Log - Connection Error:", err);
      setError(err.name === 'AbortError' ? "Request timed out. Is the AI overloaded?" : "Connection failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 antialiased">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8 border border-slate-200 transition-all duration-500">
        
        {/* Header - Scalable for more subjects */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-indigo-200 shadow-lg">
              A
            </div>
            <div>
              <h1 className="text-2xl font-black text-slate-800 tracking-tight">Ascenda</h1>
              <p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">K-12 EdTech India</p>
            </div>
          </div>
          <div className={`flex items-center px-3 py-1 rounded-full border ${error ? 'bg-red-50 border-red-100' : 'bg-green-50 border-green-100'}`}>
            <div className={`h-2 w-2 rounded-full mr-2 ${error ? 'bg-red-500' : 'bg-green-500 animate-pulse'}`}></div>
            <span className={`text-[10px] font-bold uppercase ${error ? 'text-red-700' : 'text-green-700'}`}>
              {error ? 'API: Error' : 'API: Online'}
            </span>
          </div>
        </div>

        {/* Dynamic Lesson Display Area */}
        <div className="min-h-[250px] bg-slate-50 rounded-2xl p-6 mb-8 border-2 border-slate-100 relative overflow-hidden">
          {loading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm z-10">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-slate-200 border-t-indigo-600 mb-4"></div>
              <p className="text-sm font-medium text-slate-500">Synthesizing Physics Concept...</p>
            </div>
          ) : null}

          {error ? (
            <div className="text-center py-10">
              <p className="text-red-500 font-medium mb-2">Oops! Something went wrong.</p>
              <p className="text-xs text-slate-400">{error}</p>
            </div>
          ) : lesson ? (
            <article className="animate-in fade-in slide-in-from-bottom-2 duration-700">
              <h3 className="text-xs font-black text-indigo-500 uppercase tracking-widest mb-4">Unit 1: Electrostatics</h3>
              <div className="text-slate-700 leading-relaxed text-lg font-medium whitespace-pre-wrap">
                {lesson}
              </div>
            </article>
          ) : (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl text-slate-300">⚛️</span>
              </div>
              <p className="text-slate-400 font-medium">Ready to start Class 12 Physics?</p>
            </div>
          )}
        </div>

        <button 
          className="w-full py-4 px-6 bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] disabled:bg-slate-300 text-white font-bold rounded-xl transition-all duration-200 shadow-lg shadow-indigo-100 disabled:shadow-none"
          onClick={startLesson}
          disabled={loading}
        >
          {loading ? 'Consulting Brain...' : 'Launch Coulomb\'s Law Lesson'}
        </button>
      </div>

      <p className="mt-8 text-slate-300 text-[10px] font-bold tracking-[0.2em] uppercase">
        Authenticated Shell v1.0 • Secure Environment
      </p>
    </div>
  )
}

export default App
