import React, { useState, useEffect } from 'react';
import { GraduationCap, Microscope, BookOpen, Layers, Filter, Search } from 'lucide-react';

const UserLearningHub = ({ apiBase, onStartLesson }) => {
  // 1. State Management
  const [mode, setMode] = useState('regular'); // 'regular' (K-12) or 'exam' (Competitive)
  const [loading, setLoading] = useState(true);
  
  const [subjects, setSubjects] = useState([]);
  const [boards, setBoards] = useState([]);
  const [grades, setGrades] = useState([]);
  const [subjectAreas, setSubjectAreas] = useState([]);
  
  const [selectedBoard, setSelectedBoard] = useState('all');
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [selectedSubject, setSelectedSubject] = useState(null);

  // 2. Initial Data Load (Boards & Grades)
  useEffect(() => {
    const fetchInitialMetadata = async () => {
      try {
        const [bRes, gRes] = await Promise.all([
          fetch(`${apiBase}/api/admin/organizations/`),
          fetch(`${apiBase}/api/admin/curriculum/grades`)
        ]);
        
        const bData = await bRes.json();
        const gData = await gRes.json();

        setBoards(Array.isArray(bData) ? bData : []);
        setGrades(Array.isArray(gData) ? gData : []);
      } catch (err) {
        console.error("❌ Metadata fetch failed:", err);
      }
    };
    fetchInitialMetadata();
  }, [apiBase]);

  // 3. Subject Filtering Logic
  useEffect(() => {
    const fetchFilteredContent = async () => {
      setLoading(true);
      try {
        const endpoint = mode === 'regular' ? 'regular' : 'exam';
        const res = await fetch(`${apiBase}/api/admin/curriculum/${endpoint}/subjects`);
        let data = await res.json();

        if (Array.isArray(data)) {
          // Apply strict string-based UUID filtering
          if (mode === 'regular' && selectedGrade !== 'all') {
            data = data.filter(s => String(s.grade_id) === String(selectedGrade));
          }
          if (mode === 'exam' && selectedBoard !== 'all') {
            data = data.filter(s => String(s.organization_id) === String(selectedBoard));
          }
          setSubjects(data);
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

  // 4. Handle Subject Selection (Fetch Units)
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
      console.error("❌ Failed to fetch subject units:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#05070a] text-white">
      <section className="max-w-7xl mx-auto px-6 py-12">
        
        {/* TOP FILTER BAR */}
        <div className="flex flex-col md:flex-row justify-between items-end gap-6 mb-12 bg-slate-900/40 p-6 rounded-3xl border border-slate-800 backdrop-blur-md">
          <div className="space-y-4">
            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-500 flex items-center gap-2">
              <Filter size={14} className="text-indigo-500"/> Learning Path
            </h3>
            <div className="bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex w-fit shadow-2xl">
              <button 
                onClick={() => { setMode('regular'); setSelectedBoard('all'); setSelectedGrade('all'); }} 
                className={`px-6 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${mode === 'regular' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-500 hover:text-slate-300'}`}
              >
                <GraduationCap size={18}/> K-12 Schooling
              </button>
              <button 
                onClick={() => { setMode('exam'); setSelectedBoard('all'); setSelectedGrade('all'); }} 
                className={`px-6 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${mode === 'exam' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-500 hover:text-slate-300'}`}
              >
                <Microscope size={18}/> Competitive Exams
              </button>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 w-full md:w-auto">
            {/* Organization Dropdown */}
            <div className="flex flex-col gap-2 flex-1 md:flex-none min-w-[180px]">
                <label className="text-[10px] uppercase tracking-widest text-slate-500 font-black ml-1">Select Board/Exam</label>
                <select 
                  value={selectedBoard}
                  onChange={(e) => { setSelectedBoard(e.target.value); setSelectedGrade('all'); }} 
                  className="bg-slate-950 border border-slate-800 text-slate-300 rounded-xl px-4 py-3 text-sm outline-none focus:border-indigo-500 transition-colors cursor-pointer"
                >
                  <option value="all">All Organizations</option>
                  {boards.map(b => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
            </div>

            {/* Grade Dropdown (Only for Regular Mode) */}
            {mode === 'regular' && (
              <div className="flex flex-col gap-2 flex-1 md:flex-none min-w-[180px]">
                <label className="text-[10px] uppercase tracking-widest text-slate-500 font-black ml-1">Grade Level</label>
                <select 
                  value={selectedGrade}
                  onChange={(e) => setSelectedGrade(e.target.value)} 
                  className="bg-slate-950 border border-slate-800 text-slate-300 rounded-xl px-4 py-3 text-sm outline-none focus:border-indigo-500 transition-colors cursor-pointer"
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
             [...Array(6)].map((_, i) => (
                <div key={i} className="h-40 bg-slate-900/50 rounded-3xl animate-pulse border border-slate-800" />
             ))
          ) : subjects.length > 0 ? (
            subjects.map((sub) => (
              <button 
                key={sub.id} 
                onClick={() => handleSubjectClick(sub)}
                className={`group p-8 border rounded-3xl flex flex-col items-center gap-4 transition-all active:scale-95 ${
                  selectedSubject?.id === sub.id 
                  ? 'bg-indigo-600/20 border-indigo-500 shadow-2xl shadow-indigo-500/10' 
                  : 'bg-slate-900/30 border-slate-800 hover:border-slate-600'
                }`}
              >
                <div className={`p-5 rounded-2xl transition-colors ${
                  selectedSubject?.id === sub.id ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 group-hover:text-white'
                }`}>
                  <BookOpen size={28} />
                </div>
                <span className={`font-bold text-sm tracking-tight text-center ${
                  selectedSubject?.id === sub.id ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
                }`}>
                  {sub.name}
                </span>
              </button>
            ))
          ) : (
            <div className="col-span-full py-20 text-center border-2 border-dashed border-slate-800 rounded-[3rem]">
              <div className="bg-slate-900 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="text-slate-700" size={24} />
              </div>
              <p className="text-slate-500 font-medium">No subjects found for this selection.</p>
              <p className="text-slate-700 text-xs mt-2 uppercase tracking-widest">Try changing the Grade or Board filter</p>
            </div>
          )}
        </div>

        {/* UNITS / SUBJECT AREAS SECTION */}
        {selectedSubject && (
          <div className="animate-in fade-in slide-in-from-bottom-6 duration-500 bg-indigo-600/5 border border-indigo-500/20 p-10 rounded-[3rem]">
            <div className="flex items-center justify-between mb-8">
                <div className="space-y-1">
                    <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-indigo-500">Curriculum Structure</h4>
                    <h2 className="text-2xl font-bold flex items-center gap-3 italic">
                        <Layers size={22} className="text-indigo-400" /> {selectedSubject.name} Units
                    </h2>
                </div>
                <div className="px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-black uppercase tracking-tighter">
                   {subjectAreas.length} Total Units
                </div>
            </div>

            <div className="flex flex-wrap gap-4">
              {subjectAreas.length > 0 ? subjectAreas.map(area => (
                <button 
                  key={area.id} 
                  onClick={onStartLesson} 
                  className="group relative px-8 py-4 bg-slate-950 border border-slate-800 hover:border-indigo-500/50 rounded-2xl text-sm font-bold text-slate-300 transition-all hover:shadow-xl hover:shadow-indigo-500/5 active:scale-95 overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-indigo-600/0 via-indigo-600/5 to-indigo-600/0 opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="relative z-10">{area.name}</span>
                </button>
              )) : (
                <p className="text-slate-600 italic text-sm py-4">Loading units for this subject...</p>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
};

export default UserLearningHub;