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

  useEffect(() => {
    fetchInitialMetadata();
  }, []);

  useEffect(() => {
    fetchFilteredContent();
    setSelectedSubject(null);
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
      const endpoint = mode === 'regular' ? 'regular' : 'exam';
      const res = await fetch(`${apiBase}/api/admin/curriculum/${endpoint}/subjects`);
      let data = await res.json();

      if (Array.isArray(data)) {
        // FIX: Convert both IDs to Strings before comparing
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
      // Filter units belonging to this specific subject
      const filtered = allAreas.filter(area => 
        String(area.subject_id || area.exam_subject_id) === String(subject.id)
      );
      setSubjectAreas(filtered);
    } catch (err) { console.error("Failed to fetch sub-topics", err); }
  };

  return (
    <div className="min-h-screen bg-[#05070a] text-white">
      <section className="max-w-7xl mx-auto px-6 py-20">
        
        {/* Filter Bar */}
        <div className="flex flex-col md:flex-row justify-between items-end gap-6 mb-12 bg-slate-900/40 p-6 rounded-3xl border border-slate-800">
          <div className="space-y-4">
            <h3 className="text-xl font-bold flex items-center gap-2"><Filter size={18} className="text-indigo-500"/> Select Path</h3>
            <div className="bg-slate-950 p-1 rounded-xl border border-slate-800 flex w-fit">
              <button onClick={() => setMode('regular')} className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${mode === 'regular' ? 'bg-indigo-600 text-white' : 'text-slate-500'}`}><GraduationCap size={16}/> K-12</button>
              <button onClick={() => setMode('exam')} className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${mode === 'exam' ? 'bg-indigo-600 text-white' : 'text-slate-500'}`}><Microscope size={16}/> Exams</button>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex flex-col gap-2">
                <label className="text-[10px] uppercase tracking-widest text-slate-500 font-bold ml-1">Board / Exam</label>
                <select onChange={(e) => setSelectedBoard(e.target.value)} className="bg-slate-950 border border-slate-800 text-slate-300 rounded-xl px-4 py-2.5 text-sm font-bold outline-none hover:border-indigo-500 transition-colors">
                <option value="all">All Organizations</option>
                {boards.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
            </div>
            {mode === 'regular' && (
              <div className="flex flex-col gap-2">
                <label className="text-[10px] uppercase tracking-widest text-slate-500 font-bold ml-1">Grade Level</label>
                <select onChange={(e) => setSelectedGrade(e.target.value)} className="bg-slate-950 border border-slate-800 text-slate-300 rounded-xl px-4 py-2.5 text-sm font-bold outline-none hover:border-indigo-500 transition-colors">
                  <option value="all">Any Grade</option>
                  {grades.map(g => <option key={g.id} value={g.id}>{g.level}</option>)}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Subjects Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6 mb-12">
          {subjects.length > 0 ? subjects.map((sub) => (
            <button key={sub.id} onClick={() => handleSubjectClick(sub)} className={`group p-8 border rounded-3xl flex flex-col items-center gap-4 transition-all duration-300 ${selectedSubject?.id === sub.id ? 'bg-indigo-600/20 border-indigo-500 shadow-[0_0_30px_rgba(79,70,229,0.1)]' : 'bg-slate-900/30 border-slate-800/50 hover:border-slate-700'}`}>
              <div className={`p-4 rounded-2xl transition-all ${selectedSubject?.id === sub.id ? 'bg-indigo-600 scale-110' : 'bg-slate-800'}`}>
                <BookOpen className={selectedSubject?.id === sub.id ? 'text-white' : 'text-indigo-400'} size={24} />
              </div>
              <span className={`font-bold ${selectedSubject?.id === sub.id ? 'text-white' : 'text-slate-400'}`}>{sub.name}</span>
            </button>
          )) : !loading && (
            <div className="col-span-full py-16 text-center text-slate-600 border border-dashed border-slate-800 rounded-3xl">
              No subjects found for this selection. Link subjects to this Grade in Admin.
            </div>
          )}
        </div>

        {/* Sub-Topics (Units) Filter */}
        {selectedSubject && (
          <div className="bg-indigo-600/5 border border-indigo-500/20 p-8 rounded-[2rem] animate-in fade-in slide-in-from-bottom-4">
            <h4 className="text-sm font-black uppercase tracking-[0.2em] text-indigo-400 mb-6 flex items-center gap-2">
              <Layers size={16} /> Course Units: {selectedSubject.name}
            </h4>
            <div className="flex flex-wrap gap-3">
              {subjectAreas.length > 0 ? subjectAreas.map(area => (
                <button key={area.id} onClick={onStartLesson} className="px-6 py-3 bg-slate-900 border border-slate-800 hover:border-indigo-500 hover:bg-indigo-600 hover:text-white rounded-2xl text-sm font-bold text-slate-300 transition-all active:scale-95">
                  {area.name}
                </button>
              )) : (
                <p className="text-slate-600 italic">No units uploaded for this subject yet.</p>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
};

export default UserLearningHub;