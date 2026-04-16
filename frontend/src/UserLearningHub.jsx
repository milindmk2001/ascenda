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
      const [bRes, gRes] = await Promise.all([
        fetch(`${apiBase}/api/admin/organizations/`),
        fetch(`${apiBase}/api/admin/curriculum/grades`)
      ]);
      const bData = await bRes.json();
      const gData = await gRes.json();
      setBoards(Array.isArray(bData) ? bData : []);
      setGrades(Array.isArray(gData) ? gData : []);
    } catch (err) { console.error("Metadata fetch failed", err); }
  };

  const fetchFilteredContent = async () => {
    setLoading(true);
    try {
      const endpoint = mode === 'regular' ? 'regular' : 'exam';
      const res = await fetch(`${apiBase}/api/admin/curriculum/${endpoint}/subjects`);
      let data = await res.json();
      if (Array.isArray(data)) {
        if (mode === 'regular' && selectedGrade !== 'all') {
          data = data.filter(s => String(s.grade_id) === String(selectedGrade));
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
      const filtered = allAreas.filter(area => String(area.subject_id || area.exam_subject_id) === String(subject.id));
      setSubjectAreas(filtered);
    } catch (err) { console.error("Failed to fetch units", err); }
  };

  return (
    <div className="min-h-screen bg-[#05070a] text-white p-10">
      <div className="flex gap-6 mb-10 bg-slate-900/50 p-6 rounded-3xl border border-slate-800">
        <select onChange={(e) => setSelectedBoard(e.target.value)} className="bg-slate-950 border border-slate-800 p-3 rounded-xl text-sm">
          <option value="all">All Boards</option>
          {boards.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
        <select onChange={(e) => setSelectedGrade(e.target.value)} className="bg-slate-950 border border-slate-800 p-3 rounded-xl text-sm">
          <option value="all">Any Grade</option>
          {grades.filter(g => selectedBoard === 'all' || String(g.org_id) === String(selectedBoard)).map(g => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-4 gap-6">
        {subjects.map((sub) => (
          <button key={sub.id} onClick={() => handleSubjectClick(sub)} className="p-8 bg-slate-900 border border-slate-800 rounded-3xl flex flex-col items-center gap-4 hover:border-indigo-500 transition-all">
            <BookOpen size={32} />
            <span className="font-bold">{sub.name}</span>
          </button>
        ))}
      </div>

      {selectedSubject && (
        <div className="mt-10 p-10 bg-indigo-600/5 border border-indigo-500/20 rounded-[3rem]">
          <h4 className="mb-6 font-bold uppercase text-indigo-400">Units for {selectedSubject.name}</h4>
          <div className="flex flex-wrap gap-4">
            {subjectAreas.map(area => (
              <button key={area.id} onClick={() => onStartLesson(area)} className="px-6 py-3 bg-slate-900 border border-slate-800 rounded-2xl text-sm font-bold">
                {area.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default UserLearningHub;