import React, { useState, useEffect } from 'react';
import { GraduationCap, Microscope, ChevronRight, PlayCircle, Filter, BookOpen } from 'lucide-react';

const UserLearningHub = ({ apiBase, onStartLesson }) => {
  const [mode, setMode] = useState('regular'); 
  const [loading, setLoading] = useState(true);
  
  // Data State
  const [subjects, setSubjects] = useState([]);
  const [boards, setBoards] = useState([]);
  const [grades, setGrades] = useState([]);
  const [areas, setAreas] = useState([]);
  
  // Selection State
  const [selectedBoard, setSelectedBoard] = useState('all');
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [selectedSubject, setSelectedSubject] = useState(null);

  useEffect(() => {
    fetchInitialMetadata();
  }, []);

  useEffect(() => {
    fetchFilteredContent();
  }, [mode, selectedBoard, selectedGrade]);

  const fetchInitialMetadata = async () => {
    try {
      const [bRes, gRes] = await Promise.all([
        fetch(`${apiBase}/api/admin/organizations/`),
        fetch(`${apiBase}/api/admin/curriculum/grades`)
      ]);
      setBoards(await bRes.json());
      setGrades(await gRes.json());
    } catch (err) { console.error("Metadata fetch failed", err); }
  };

  const fetchFilteredContent = async () => {
    setLoading(true);
    try {
      const endpoint = mode === 'regular' 
        ? `/api/admin/curriculum/regular/subjects` 
        : `/api/admin/curriculum/exam/subjects`;
      
      const res = await fetch(`${apiBase}${endpoint}`);
      let data = await res.json();

      // Apply Filters
      if (Array.isArray(data)) {
        if (mode === 'regular' && selectedGrade !== 'all') {
          data = data.filter(s => s.grade_id === selectedGrade);
        }
        if (mode === 'exam' && selectedBoard !== 'all') {
          data = data.filter(s => s.organization_id === selectedBoard);
        }
        setSubjects(data);
      }
    } catch (err) { console.error("Content fetch failed", err); }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#05070a] text-white font-sans">
      {/* Hero Section remains same as previous */}
      
      <section className="max-w-7xl mx-auto px-6 py-20 border-t border-slate-900">
        <div className="flex flex-col gap-8 mb-12">
          <div className="flex flex-col md:flex-row justify-between items-end gap-6">
            <div className="space-y-4">
              <h3 className="text-2xl font-bold">Explore Curriculum</h3>
              {/* Mode Switcher */}
              <div className="bg-slate-900 p-1 rounded-xl border border-slate-800 flex w-fit">
                <button onClick={() => setMode('regular')} className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 ${mode === 'regular' ? 'bg-indigo-600 text-white' : 'text-slate-500'}`}><GraduationCap size={16}/> K-12</button>
                <button onClick={() => setMode('exam')} className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 ${mode === 'exam' ? 'bg-indigo-600 text-white' : 'text-slate-500'}`}><Microscope size={16}/> Exams</button>
              </div>
            </div>

            {/* Primary Filters (Board/Grade) */}
            <div className="flex gap-3">
              <select 
                onChange={(e) => setSelectedBoard(e.target.value)}
                className="bg-slate-900 border border-slate-800 text-slate-300 rounded-xl px-4 py-2.5 text-sm font-bold outline-none"
              >
                <option value="all">All Boards</option>
                {boards.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>

              {mode === 'regular' && (
                <select 
                  onChange={(e) => setSelectedGrade(e.target.value)}
                  className="bg-slate-900 border border-slate-800 text-slate-300 rounded-xl px-4 py-2.5 text-sm font-bold outline-none"
                >
                  <option value="all">Select Grade</option>
                  {grades.map(g => <option key={g.id} value={g.id}>{g.level}</option>)}
                </select>
              )}
            </div>
          </div>
        </div>

        {/* Subject Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
          {subjects.length > 0 ? subjects.map((sub) => (
            <button 
              key={sub.id}
              onClick={() => setSelectedSubject(sub)}
              className={`group p-8 border rounded-3xl flex flex-col items-center gap-4 transition-all ${selectedSubject?.id === sub.id ? 'bg-indigo-600/20 border-indigo-500' : 'bg-slate-900/30 border-slate-800/50 hover:border-slate-700'}`}
            >
              <div className="p-4 bg-slate-800 rounded-2xl group-hover:scale-110 transition-transform">
                <BookOpen className="text-indigo-400" size={24} />
              </div>
              <span className="font-bold text-slate-300 group-hover:text-white">{sub.name}</span>
            </button>
          )) : !loading && (
            <div className="col-span-full py-20 text-center text-slate-600 italic border border-dashed border-slate-800 rounded-3xl">
              No subjects found for this selection. Check your Admin settings.
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default UserLearningHub;