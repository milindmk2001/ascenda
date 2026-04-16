import React, { useState, useEffect } from 'react';
import { GraduationCap, Microscope, BookOpen, Layers, Filter } from 'lucide-react';

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
      // Fetching from the endpoints defined in your backend
      const [bRes, gRes] = await Promise.all([
        fetch(`${apiBase}/api/admin/organizations/`),
        fetch(`${apiBase}/api/admin/curriculum/grades`)
      ]);
      const bData = await bRes.json();
      const gData = await gRes.json();
      
      setBoards(Array.isArray(bData) ? bData : []);
      setGrades(Array.isArray(gData) ? gData : []);
    } catch (err) { 
      console.error("Failed to load filter metadata:", err); 
    }
  };

  const fetchFilteredContent = async () => {
    setLoading(true);
    try {
      const endpoint = mode === 'regular' ? 'regular' : 'exam';
      const res = await fetch(`${apiBase}/api/admin/curriculum/${endpoint}/subjects`);
      let data = await res.json();

      if (Array.isArray(data)) {
        // Fix: Convert IDs to Strings to match the UUIDs from PostgreSQL
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
      // Filter units belonging to the selected subject
      const filtered = allAreas.filter(area => 
        String(area.subject_id || area.exam_subject_id) === String(subject.id)
      );
      setSubjectAreas(filtered);
    } catch (err) { console.error("Failed to fetch units", err); }
  };

  return (
    <div className="min-h-screen bg-[#05070a] text-white">
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="flex flex-col md:flex-row justify-between items-end gap-6 mb-12 bg-slate-900/40 p-6 rounded-3xl border border-slate-800">
          <div className="space-y-4">
            <h3 className="text-xl font-bold flex items-center gap-2"><Filter size={18} className="text-indigo-500"/> Path</h3>
            <div className="bg-slate-950 p-1 rounded-xl border border-slate-800 flex w-fit">
              <button onClick={() => setMode('regular')} className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 ${mode === 'regular' ? 'bg-indigo-600 text-white' : 'text-slate-500'}`}><GraduationCap size={16}/> K-12</button>
              <button onClick={() => setMode('exam')} className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 ${mode === 'exam' ? 'bg-indigo-600 text-white' : 'text-slate-500'}`}><Microscope size={16}/> Exams</button>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex flex-col gap-2">
                <label className="text-[10px] uppercase text-slate-500 font-bold">Organization</label>
                <select onChange={(e) => setSelectedBoard(e.target.value)} className="bg-slate-950 border border-slate-800 text-slate-300 rounded-xl px-4 py-2.5 text-sm outline-none">
                  <option value="all">All Boards</option>
                  {boards.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
            </div>
            {mode === 'regular' && (
              <div className="flex flex-col gap-2">
                <label className="text-[10px] uppercase text-slate-500 font-bold">Grade</label>
                <select onChange={(e) => setSelectedGrade(e.target.value)} className="bg-slate-950 border border-slate-800 text-slate-300 rounded-xl px-4 py-2.5 text-sm outline-none">
                  <option value="all">Any Grade</option>
                  {/* Filter grades by the selected organization */}
                  {grades.filter(g => selectedBoard === 'all' || String(g.org_id) === String(selectedBoard)).map(g => (
                    <option key={g.id} value={g.id}>{g.name}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
          {subjects.map((sub) => (
            <button key={sub.id} onClick={() => handleSubjectClick(sub)} className={`group p-8 border rounded-3xl flex flex-col items-center gap-4 transition-all ${selectedSubject?.id === sub.id ? 'bg-indigo-600/20 border-indigo-500' : 'bg-slate-900/30 border-slate-800'}`}>
              <div className={`p-4 rounded-2xl ${selectedSubject?.id === sub.id ? 'bg-indigo-600' : 'bg-slate-800'}`}><BookOpen size={24} /></div>
              <span className="font-bold">{sub.name}</span>
            </button>
          ))}
        </div>

        {selectedSubject && (
          <div className="mt-12 bg-indigo-600/5 border border-indigo-500/20 p-8 rounded-[2rem]">
            <h4 className="text-sm font-black uppercase text-indigo-400 mb-6 flex items-center gap-2"><Layers size={16} /> Units: {selectedSubject.name}</h4>
            <div className="flex flex-wrap gap-3">
              {subjectAreas.map(area => (
                <button key={area.id} onClick={onStartLesson} className="px-6 py-3 bg-slate-900 border border-slate-800 hover:bg-indigo-600 rounded-2xl text-sm font-bold transition-all">{area.name}</button>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
};

export default UserLearningHub;