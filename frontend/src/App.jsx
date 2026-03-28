import React, { useState } from 'react'

function App() {
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(false);

  // Use the environment variable from Vercel, or fallback to your Railway URL
  const API_URL = import.meta.env.VITE_API_URL || 'https://ascenda-production.up.railway.app';

  const startLesson = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: "Explain Coulomb's Law using a Gen-Z analogy." })
      });
      const data = await response.json();
      setLesson(data.response); // Adjust this based on your exact backend JSON structure
    } catch (error) {
      console.error("Error connecting to Physics Brain:", error);
      setLesson("Connection failed. Check if Railway CORS is set to this URL.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-xl shadow-lg p-8 border border-slate-200">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">
              A
            </div>
            <h1 className="text-2xl font-bold text-slate-800">Ascenda</h1>
          </div>
          <div className="flex items-center p-2 bg-green-50 rounded-lg border border-green-100">
            <div className="h-2 w-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
            <span className="text-xs font-medium text-green-700">API: Online</span>
          </div>
        </div>

        {/* Lesson Display Area */}
        <div className="min-h-[200px] bg-slate-100 rounded-lg p-6 mb-8 border-dashed border-2 border-slate-200">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-400">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-2"></div>
              <p>Consulting the Physics Brain...</p>
            </div>
          ) : lesson ? (
            <div className="prose prose-slate text-slate-700">
              <h3 className="text-lg font-semibold text-indigo-600 mb-2">Current Lesson: Electrostatics</h3>
              <p className="leading-relaxed">{lesson}</p>
            </div>
          ) : (
            <p className="text-center text-slate-400 mt-10">
              Click below to generate your first AI Physics lesson.
            </p>
          )}
        </div>

        {/* Action Button */}
        <button 
          className="w-full py-4 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white font-semibold rounded-lg transition duration-200 shadow-md"
          onClick={startLesson}
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Start Coulomb\'s Law Lesson'}
        </button>
      </div>

      <footer className="mt-8 text-slate-400 text-xs tracking-widest uppercase text-center">
        Backend: {API_URL}<br/>
        <span className="mt-2 block font-bold text-indigo-500">Physics EdTech Platform • 2026</span>
      </footer>
    </div>
  )
}

export default App