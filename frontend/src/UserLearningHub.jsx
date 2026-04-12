import React, { useState, useEffect } from 'react';
import { GraduationCap, Microscope, ChevronRight, PlayCircle, Filter } from 'lucide-react';

const UserLearningHub = ({ apiBase, onStartLesson }) => {
  const [mode, setMode] = useState('regular'); // 'regular' or 'exam'
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Metadata for filters
  const [boards, setBoards] = useState([]);
  const [grades, setGrades] = useState([]);
  
  // Selection state
  const [selectedBoard, setSelectedBoard] = useState('all');
  const [selectedGrade, setSelectedGrade] = useState('all');

  useEffect(() => {
    fetchMetadata();
  }, []);

  useEffect(() => {
    fetchSubjects();
  }, [mode, selectedBoard, selectedGrade]);

  const fetchMetadata = async () => {
    try {
      const [boardRes, gradeRes] = await Promise.all([
        fetch(`${apiBase}/api/admin/organizations/`),
        fetch(`${apiBase}/api/admin/curriculum/grades`)
      ]);
      const boardData = await boardRes.json();
      const gradeData = await gradeRes.json();
      setBoards(Array.isArray(boardData) ? boardData : []);
      setGrades(Array.isArray(gradeData) ? gradeData : []);
    } catch (err) {
      console.error("Failed to load metadata", err);
    }
  };

  const fetchSubjects = async () => {
    setLoading(true);
    try {
      const endpoint = mode === 'regular' 
        ? '/api/admin/curriculum/regular/subjects' 
        : '/api/admin/curriculum/exam/subjects';
      
      const res = await fetch(`${apiBase}${endpoint}`);
      let data = await res.json();
      
      if (Array.isArray(data)) {
        // Filter subjects on the frontend based on selection
        if (mode === 'regular' && selectedGrade !== 'all') {
          data = data.filter(s => s.grade_id === selectedGrade);
        }
        if (mode === 'exam' && selectedBoard !== 'all') {
          data = data.filter(s => s.organization_id === selectedBoard);
        }
        setSubjects(data);
      } else {
        setSubjects([]);
      }
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
          <button onClick={onStartLesson} className="bg-white text-black px-8 py-4 rounded-xl font-bold flex items-center gap-2 hover:bg-slate-200 transition-all shadow-xl shadow-white/5">
            Try Free Demo Lesson <ChevronRight size={20} />
          </button>
        </div>

        <div className="flex-1 w-full aspect-video bg-slate-900/50 border border-slate-800 rounded-3xl flex items-center justify-center relative group overflow-hidden shadow-2xl">
          <h2 className="text-8xl font-black text-slate-800 group-hover:text-slate-700 transition-colors tracking-tighter">VEO</h2>
          <PlayCircle className="absolute text-indigo-500/20 group-hover:text-indigo-500/40 transition-all duration-500" size={120} />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        </div>
      </section>

      {/* Subject Selector Section */}
      <section className="max-w-7xl mx-auto px-6 py-20 border-t border-slate-900">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
          <div>
            <h3 className="text-2xl font-bold mb-2">Explore Curriculum</h3>
            <div className="flex gap-4">
               {/* Mode Switcher */}
              <div className="bg-slate-900 p-1 rounded-xl border border-slate-800 flex gap-1">
                <button 
                  onClick={() => { setMode('regular'); setSelectedBoard('all'); }}
                  className={`px-4 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${mode === 'regular' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-500 hover:text-slate-300'}`}
                >
                  <GraduationCap size={16} /> K-12
                </button>
                <button 
                  onClick={() => { setMode('exam'); setSelectedGrade('all'); }}
                  className={`px-4 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${mode === 'exam' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-500 hover:text-slate-300'}`}
                >
                  <Microscope size={16} /> Exams
                </button>
              </div>
            </div>
          </div>

          {/* Filtering Controls */}
          <div className="flex flex-wrap gap-3 items-center">
            <Filter size={18} className="text-slate-500 mr-2" />
            
            {mode === 'regular' ? (
              <select 
                value={selectedGrade} 
                onChange={(e) => setSelectedGrade(e.target.value)}
                className="bg-slate-900 border border-slate-800 text-slate-300 rounded-xl px-4 py-2 text-sm font-bold focus:border-indigo-500 outline-none cursor-pointer"
              >
                <option value="all">All Grades</option>
                {grades.map(g => <option key={g.id} value={g.id}>{g.level}</option>)}
              </select>
            ) : (
              <select 
                value={selectedBoard} 
                onChange={(e) => setSelectedBoard(e.target.value)}
                className="bg-slate-900 border border-slate-800 text-slate-300 rounded-xl px-4 py-2 text-sm font-bold focus:border-indigo-500 outline-none cursor-pointer"
              >
                <option value="all">All Boards/Exams</option>
                {boards.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            )}
          </div>
        </div>

        {/* Dynamic Subject Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          {loading ? (
            [...Array(6)].map((_, i) => (
              <div key={i} className="h-40 bg-slate-900/50 rounded-2xl animate-pulse border border-slate-800" />
            ))
          ) : subjects.length > 0 ? (
            subjects.map((sub) => (
              <button 
                key={sub.id}
                className="group p-8 bg-slate-900/30 border border-slate-800/50 rounded-3xl flex flex-col items-center gap-4 hover:bg-indigo-600/10 hover:border-indigo-500/50 transition-all duration-300 active:scale-95"
              >
                <div className="p-5 bg-slate-800 group-hover:bg-indigo-600 rounded-2xl transition-all duration-300 group-hover:rotate-6">
                  <BookIcon name={sub.name} />
                </div>
                <span className="font-bold text-slate-400 group-hover:text-white transition-colors text-center">
                  {sub.name}
                </span>
              </button>
            ))
          ) : (
            <div className="col-span-full py-20 text-center text-slate-600 font-medium italic border border-dashed border-slate-800 rounded-3xl">
              No subjects match your current filter.
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

const BookIcon = ({ name }) => {
  const n = name.toLowerCase();
  if (n.includes('physic')) return <div className="w-6 h-6 bg-purple-500 rounded-md" />;
  if (n.includes('math')) return <div className="w-6 h-6 bg-blue-500 rounded-md" />;
  if (n.includes('chem')) return <div className="w-6 h-6 bg-emerald-500 rounded-md" />;
  if (n.includes('biol') || n.includes('science')) return <div className="w-6 h-6 bg-pink-500 rounded-md" />;
  return <div className="w-6 h-6 bg-slate-600 rounded-md" />;
};

export default UserLearningHub;