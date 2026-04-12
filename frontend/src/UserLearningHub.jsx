import React, { useState, useEffect } from 'react';
import { GraduationCap, Microscope, ChevronRight, PlayCircle } from 'lucide-react';

const UserLearningHub = ({ apiBase }) => {
  const [mode, setMode] = useState('regular'); // 'regular' or 'exam'
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubjects();
  }, [mode]);

  const fetchSubjects = async () => {
    setLoading(true);
    try {
      const endpoint = mode === 'regular' 
        ? '/api/admin/curriculum/regular/subjects' 
        : '/api/admin/curriculum/exam/subjects';
      const res = await fetch(`${apiBase}${endpoint}`);
      const data = await res.json();
      setSubjects(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load subjects", err);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#05070a] text-white font-sans">
      {/* Hero Section */}
      <section className="pt-20 pb-12 px-6 max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-12">
        <div className="flex-1 space-y-6">
          <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-4 py-1.5 rounded-full text-xs font-bold tracking-widest uppercase">
            India's First AI-Interactive Tutor
          </span>
          <h1 className="text-6xl font-black leading-tight">
            Class 3-12 <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-500">
              Visual Learning
            </span>
          </h1>
          <p className="text-slate-400 text-lg max-w-md">
            Don't just watch a video. Ask questions and let our AI point exactly to the concepts on screen.
          </p>
          <button className="bg-white text-black px-8 py-4 rounded-xl font-bold flex items-center gap-2 hover:bg-slate-200 transition-all">
            Try Free Demo Lesson <ChevronRight size={20} />
          </button>
        </div>

        <div className="flex-1 w-full aspect-video bg-slate-900/50 border border-slate-800 rounded-3xl flex items-center justify-center relative group overflow-hidden shadow-2xl">
          <h2 className="text-8xl font-black text-slate-800 group-hover:text-slate-700 transition-colors">VEO</h2>
          <PlayCircle className="absolute text-indigo-500/20 group-hover:text-indigo-500/40 transition-colors" size={120} />
        </div>
      </section>

      {/* Subject Selector Section */}
      <section className="max-w-7xl mx-auto px-6 py-20 border-t border-slate-900">
        <div className="flex justify-between items-center mb-12">
          <h3 className="text-2xl font-bold">Select Subject <span className="text-slate-500 font-medium">(Class 10)</span></h3>
          
          {/* Mode Switcher */}
          <div className="bg-slate-900 p-1 rounded-xl border border-slate-800 flex gap-1">
            <button 
              onClick={() => setMode('regular')}
              className={`px-4 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${mode === 'regular' ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:text-slate-300'}`}
            >
              <GraduationCap size={16} /> K-12
            </button>
            <button 
              onClick={() => setMode('exam')}
              className={`px-4 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${mode === 'exam' ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:text-slate-300'}`}
            >
              <Microscope size={16} /> Exams
            </button>
          </div>
        </div>

        {/* Dynamic Subject Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          {loading ? (
            [...Array(6)].map((_, i) => (
              <div key={i} className="h-40 bg-slate-900/50 rounded-2xl animate-pulse border border-slate-800" />
            ))
          ) : (
            subjects.map((sub) => (
              <button 
                key={sub.id}
                className="group p-8 bg-slate-900/30 border border-slate-800/50 rounded-2xl flex flex-col items-center gap-4 hover:bg-indigo-600/10 hover:border-indigo-500/50 transition-all duration-300 active:scale-95"
              >
                <div className="p-4 bg-slate-800 group-hover:bg-indigo-600 rounded-xl transition-colors">
                  <BookIcon name={sub.name} />
                </div>
                <span className="font-bold text-slate-300 group-hover:text-white transition-colors">
                  {sub.name}
                </span>
              </button>
            ))
          )}
        </div>
      </section>
    </div>
  );
};

// Helper component to map subject names to icons
const BookIcon = ({ name }) => {
  const n = name.toLowerCase();
  if (n.includes('physic')) return <div className="w-6 h-6 bg-purple-500 rounded-sm" />;
  if (n.includes('math')) return <div className="w-6 h-6 bg-blue-500 rounded-sm" />;
  if (n.includes('chem')) return <div className="w-6 h-6 bg-emerald-500 rounded-sm" />;
  if (n.includes('biol')) return <div className="w-6 h-6 bg-pink-500 rounded-sm" />;
  return <div className="w-6 h-6 bg-slate-500 rounded-sm" />;
};

export default UserLearningHub;