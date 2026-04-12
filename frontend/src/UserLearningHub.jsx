import React, { useState, useEffect } from 'react';
import { GraduationCap, Microscope, BookOpen, ChevronRight, PlayCircle, Layers } from 'lucide-react';

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

  useEffect(() => {
    fetchInitialMetadata();
  }, []);

  useEffect(() => {
    fetchFilteredContent();
    setSelectedSubject(null); // Reset sub-selection when main filters change
    setSubjectAreas([]);
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

      if (Array.isArray(data)) {
        if (mode === 'regular' && selectedGrade !== 'all') {
          data = data.filter(s => String(s.grade_id) === String(selectedGrade));
        }
        if (mode === 'exam' && selectedBoard !== 'all') {
          data = data.filter(s => String(s.organization_id) === String(selectedBoard));
        }
        setSubjects(data);
      }
    } catch (err) { console.error("Content fetch failed", err); }
    setLoading(false);
  };

  const handleSubjectClick = async (subject) => {
    setSelectedSubject(subject);
    try {
      const endpoint = mode === 'regular' ? 'regular' : 'exam';
      const res = await fetch(`${apiBase}/api/admin/curriculum/${endpoint}/subject-areas`);
      const allAreas = await res.json();
      const filtered = allAreas.filter(area => 
        String(area.subject_id || area.exam_subject_id) === String(subject.id)
      );
      setSubjectAreas(filtered);
    } catch (err) { console.error("Failed to fetch sub-topics", err); }
  };

  return (
    <div className="min-h-screen bg-[#05070a] text-white font-sans">
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="flex flex-col md:flex-row justify-between items-end gap-6 mb-12">
          <div className="space-y-4">
            <h3 className="text-2xl font-bold italic tracking-tight">Explore Curriculum</h3>
            <div className="bg-slate-900 p-1 rounded-xl border border-slate-800 flex w-fit">
              <button onClick={() => setMode('regular')} className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${mode === 'regular' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-500 hover:text-slate-300'}`}><GraduationCap size={16}/> K-12</button>
              <button onClick={() => setMode('exam')} className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${mode === 'exam' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-500 hover:text-slate-300'}`}><Microscope size={16}/> Exams</button>
            </div>
          </div>

          <div className="flex gap-3">
            <select onChange={(e) => setSelectedBoard(e.target.value)} className="bg-slate-900 border border-slate-800 text-slate-300 rounded-xl px-4 py-2.5 text-sm font-bold outline-none cursor-pointer hover:border-slate-600 transition-colors">
              <option value="all">All Boards</option>
              {boards.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
            {mode === 'regular' && (
              <select onChange={(e) => setSelectedGrade(e.target.value)} className="bg-slate-900 border border-slate-800 text-slate-300 rounded-xl px-4 py-2.5 text-sm font-bold outline-none cursor-pointer hover:border-slate-600 transition-colors">
                <option value="all">Select Grade</option>
                {grades.map(g => <option key={g.id} value={g.id}>{g.level}</option>)}
              </select>
            )}
          </div>
        </div>

        {/* Primary Subject Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6 mb-12">
          {subjects.map((sub) => (
            <button key={sub.id} onClick={() => handleSubjectClick(sub)} className={`group p-8 border rounded-3xl flex flex-col items-center gap-4 transition-all duration-300 ${selectedSubject?.id === sub.id ? 'bg-indigo-600/20 border-indigo-500 shadow-[0_0_30px_rgba(79,70,229,0.1)]' : 'bg-slate-900/30 border-slate-800/50 hover:border-slate-700'}`}>
              <div className={`p-4 rounded-2xl transition-all ${selectedSubject?.id === sub.id ? 'bg-indigo-600 scale-110' : 'bg-slate-800 group-hover:bg-slate-700'}`}>
                <BookOpen className={selectedSubject?.id === sub.id ? 'text-white' : 'text-indigo-400'} size={24} />
              </div>
              <span className={`font-bold transition-colors ${selectedSubject?.id === sub.id ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}`}>{sub.name}</span>
            </button>
          ))}
        </div>

        {/* Sub-topic Filter (Subject Areas) */}
        {selectedSubject && (
          <div className="animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="flex items-center gap-2 text-slate-500 mb-6 px-2">
              <Layers size={16} />
              <span className="text-xs font-black uppercase tracking-[0.2em]">Select Unit for {selectedSubject.name}</span>
            </div>
            <div className="flex flex-wrap gap-3">
              {subjectAreas.length > 0 ? subjectAreas.map(area => (
                <button key={area.id} onClick={onStartLesson} className="px-6 py-3 bg-slate-900 border border-slate-800 hover:border-indigo-500/50 hover:bg-indigo-500/10 rounded-2xl text-sm font-bold text-slate-300 hover:text-white transition-all active:scale-95">
                  {area.name}
                </button>
              )) : (
                <div className="text-slate-600 text-sm italic py-4 px-2">No units currently available for this subject.</div>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
};

export default UserLearningHub;