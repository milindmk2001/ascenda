import React, { useState, useEffect } from 'react';
import { GraduationCap, Microscope, BookOpen, Layers, Search, Filter } from 'lucide-react';

const UserLearningHub = ({ apiBase, onStartLesson }) => {
  const [mode, setMode] = useState('regular'); 
  const [loading, setLoading] = useState(true);
  
  const [subjects, setSubjects] = useState([]);
  const [boards, setBoards] = useState([]);
  const [grades, setGrades] = useState([]);
  const [subjectAreas, setSubjectAreas] = useState([]);
  
  const [selectedBoard, setSelectedBoard] = useState('all');
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [selectedSubject, setSelectedSubject] = useState(null);

  // 1. Fetch Metadata (Boards & Grades) on Mount
  useEffect(() => {
    const fetchInitialMetadata = async () => {
      try {
        console.log("Fetching from:", `${apiBase}/api/admin/organizations`);
        
        // Remove trailing slashes to prevent 307 redirect issues
        const [bRes, gRes] = await Promise.all([
          fetch(`${apiBase}/api/admin/organizations`),
          fetch(`${apiBase}/api/admin/curriculum/grades`)
        ]);

        if (!bRes.ok || !gRes.ok) {
          throw new Error(`Server responded with error: ${bRes.status} / ${gRes.status}`);
        }

        const bData = await bRes.json();
        const gData = await gRes.json();

        console.log("✅ Boards received:", bData);
        console.log("✅ Grades received:", gData);

        setBoards(Array.isArray(bData) ? bData : []);
        setGrades(Array.isArray(gData) ? gData : []);
      } catch (err) {
        console.error("❌ Metadata fetch failed:", err);
      }
    };
    fetchInitialMetadata();
  }, [apiBase]);

  // 2. Fetch Subjects whenever filters change
  useEffect(() => {
    const fetchFilteredContent = async () => {
      setLoading(true);
      try {
        const endpoint = mode === 'regular' ? 'regular' : 'exam';
        const res = await fetch(`${apiBase}/api/admin/curriculum/${endpoint}/subjects`);
        const data = await res.json();

        if (Array.isArray(data)) {
          let filtered = data;
          // UUIDs from DB often need String() conversion for comparison with JS state
          if (mode === 'regular' && selectedGrade !== 'all') {
            filtered = data.filter(s => String(s.grade_id) === String(selectedGrade));
          }
          if (mode === 'exam' && selectedBoard !== 'all') {
            filtered = data.filter(s => String(s.organization_id) === String(selectedBoard));
          }
          setSubjects(filtered);
        }
      } catch (err) {
        console.error("❌ Content fetch failed:", err);
      }
      setLoading(false);
    };

    fetchFilteredContent();
    setSelectedSubject(null);
    setSubjectAreas([]);
  }, [mode, selectedBoard, selectedGrade, apiBase]);

  // 3. Handle Subject Click to load units
  const handleSubjectClick = async (subject) => {
    setSelectedSubject(subject);
    try {
      const endpoint = mode === 'regular' ? 'regular' : 'exam';
      const res = await fetch(`${apiBase}/api/admin/curriculum/${endpoint}/subject-areas`);
      const allAreas = await res.json();
      
      if (Array.isArray(allAreas)) {
        const filtered = allAreas.filter(area => 
          String(area.subject_id || area.exam_subject_id) === String(subject.id)
        );
        setSubjectAreas(filtered);
      }
    } catch (err) {
      console.error("❌ Failed to fetch units:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#05070a] text-white">
      <div className="max-w-7xl mx-auto px-6 py-12">
        
        {/* HEADER & MODE SWITCHER */}
        <div className="flex flex-col md:flex-row justify-between items-end gap-6 mb-12 bg-slate-900/40 p-6 rounded-3xl border border-slate-800 backdrop-blur-md">
          <div className="space-y-4">
            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 flex items-center gap-2">
              <Filter size={14} className="text-indigo-500"/> Select Your Path
            </h3>
            <div className="bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex w-fit">
              <button 
                onClick={() => { setMode('regular'); setSelectedBoard('all'); setSelectedGrade('all'); }} 
                className={`px-6 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${mode === 'regular' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}
              >
                <GraduationCap size={18}/> K-12
              </button>
              <button 
                onClick={() => { setMode('exam'); setSelectedBoard('all'); setSelectedGrade('all'); }} 
                className={`px-6 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${mode === 'exam' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}
              >
                <Microscope size={18}/> Competitive
              </button>
            </div>
          </div>

          <div className="flex gap-4 w-full md:w-auto">
            {/* Board Dropdown */}
            <div className="flex flex-col gap-2 min-w-[200px]">
              <label className="text-[10px] uppercase tracking-widest text-slate-500 font-bold ml-1">Board / Organization</label>
              <select 
                value={selectedBoard}
                onChange={(e) => { setSelectedBoard(e.target.value); setSelectedGrade('all'); }}
                className="bg-slate-950 border border-slate-800 text-slate-300 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none cursor-pointer"
              >
                <option value="all">All Boards</option>
                {boards.length > 0 ? boards.map(b => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                )) : <option disabled>No boards found</option>}
              </select>
            </div>

            {/* Grade Dropdown (Regular Mode Only) */}
            {mode === 'regular' && (
              <div className="flex flex-col gap-2 min-w-[150px]">
                <label className="text-[10px] uppercase tracking-widest text-slate-500 font-bold ml-1">Grade</label>
                <select 
                  value={selectedGrade}
                  onChange={(e) => setSelectedGrade(e.target.value)}
                  className="bg-slate-950 border border-slate-800 text-slate-300 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none cursor-pointer"
                >
                  <option value="all">Any Grade</option>
                  {grades
                    .filter(g => selectedBoard === 'all' || String(g.org_id) === String(selectedBoard))
                    .map(g => (
                      <option key={g.id} value={g.id}>{g.name || g.level}</option>
                    ))
                  }
                </select>
              </div>
            )}
          </div>
        </div>

        {/* SUBJECTS GRID */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6 mb-12">
          {loading ? (
            [...Array(6)].map((_, i) => <div key={i} className="h-40 bg-slate-900/50 rounded-3xl animate-pulse border border-slate-800" />)
          ) : subjects.length > 0 ? (
            subjects.map((sub) => (
              <button 
                key={sub.id} 
                onClick={() => handleSubjectClick(sub)}
                className={`p-8 border rounded-3xl flex flex-col items-center gap-4 transition-all active:scale-95 ${selectedSubject?.id === sub.id ? 'bg-indigo-600/20 border-indigo-500 shadow-xl shadow-indigo-500/10' : 'bg-slate-900/30 border-slate-800 hover:border-slate-600'}`}
              >
                <div className={`p-4 rounded-2xl ${selectedSubject?.id === sub.id ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
                  <BookOpen size={24} />
                </div>
                <span className={`font-bold text-xs text-center ${selectedSubject?.id === sub.id ? 'text-white' : 'text-slate-400'}`}>{sub.name}</span>
              </button>
            ))
          ) : (
            <div className="col-span-full py-16 text-center text-slate-600 border border-dashed border-slate-800 rounded-3xl font-medium uppercase tracking-widest text-[10px]">
              No subjects found for this selection.
            </div>
          )}
        </div>

        {/* UNITS SECTION */}
        {selectedSubject && (
          <div className="bg-indigo-600/5 border border-indigo-500/20 p-10 rounded-[3rem] animate-in fade-in slide-in-from-bottom-4">
            <h4 className="text-xs font-black uppercase tracking-[0.2em] text-indigo-400 mb-8 flex items-center gap-2">
              <Layers size={18} /> Course Units: {selectedSubject.name}
            </h4>
            <div className="flex flex-wrap gap-4">
              {subjectAreas.length > 0 ? subjectAreas.map(area => (
                <button 
                  key={area.id} 
                  onClick={() => onStartLesson(area)} 
                  className="px-8 py-4 bg-slate-950 border border-slate-800 hover:border-indigo-500 hover:bg-indigo-600 hover:text-white rounded-2xl text-sm font-bold text-slate-300 transition-all shadow-lg active:scale-95"
                >
                  {area.name}
                </button>
              )) : <p className="text-slate-600 italic">No units listed for this subject.</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserLearningHub;