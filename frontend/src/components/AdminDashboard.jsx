import React, { useState, useEffect } from 'react';
import { Layout, Database, BookOpen, Plus, Trash2, Edit3, Layers, GraduationCap, Microscope, Book } from 'lucide-react';

const AdminDashboard = ({ apiBase, onExit }) => {
  const [activeTab, setActiveTab] = useState('boards');
  const [data, setData] = useState({ 
    boards: [], 
    grades: [], 
    regSubjects: [], 
    regAreas: [],
    examSubjects: [],
    examAreas: [] 
  });
  const [loading, setLoading] = useState(true);

  // Form States
  const [boardForm, setBoardForm] = useState({ name: '', org_type: 'Exam Board' });
  const [gradeForm, setGradeForm] = useState({ level: '', name: '', org_id: '' });
  const [subjectForm, setSubjectForm] = useState({ name: '', subject_code: '', grade_id: '', discipline: 'General', video_url: '' });

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
     const endpoints = {
            boards: '/api/admin/organizations/',
            grades: '/api/admin/curriculum/grades',
            regSubjects: '/api/admin/curriculum/regular/subjects',
            regAreas: '/api/admin/curriculum/regular/subject-areas',
            examSubjects: '/api/admin/curriculum/exam/subjects',      // Now pointing safely to the new endpoints
            examAreas: '/api/admin/curriculum/exam/subject-areas'     // Now pointing safely to the new endpoints
          };
      
      const res = await fetch(`${apiBase}${endpoints[activeTab]}`);
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const result = await res.json();
      
      // Safe state updates to prevent undefined mapping crashes
      setData(prev => ({
        ...prev,
        [activeTab]: Array.isArray(result) ? result : []
      }));
    } catch (err) {
      console.error("Layout engine database sync crash prevented:", err);
      setData(prev => ({
        ...prev,
        [activeTab]: [] // Safe fallback mapping
      }));
    } finally {
      setLoading(false);
    }
  };

  // Create Handlers
  const handleCreateBoard = async (e) => {
    e.preventDefault();
    if (!boardForm.name) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/organizations/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(boardForm)
      });
      if (res.ok) {
        setBoardForm({ name: '', org_type: 'Exam Board' });
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateGrade = async (e) => {
    e.preventDefault();
    if (!gradeForm.level || !gradeForm.org_id) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/grades`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...gradeForm,
          name: gradeForm.name || `Grade ${gradeForm.level}`
        })
      });
      if (res.ok) {
        setGradeForm({ level: '', name: '', org_id: '' });
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateSubject = async (e) => {
    e.preventDefault();
    if (!subjectForm.name || !subjectForm.subject_code || !subjectForm.grade_id) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/subjects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(subjectForm)
      });
      if (res.ok) {
        setSubjectForm({ name: '', subject_code: '', grade_id: '', discipline: 'General', video_url: '' });
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Helper safely gathering current tab elements
  const currentItems = data[activeTab] || [];

  return (
    <div className="flex h-screen bg-slate-950 text-white font-sans overflow-hidden">
      {/* SIDEBAR NAVIGATION PANE */}
      <aside className="w-72 bg-slate-900 border-r border-slate-800/60 flex flex-col justify-between">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2 bg-indigo-600/10 rounded-xl border border-indigo-500/20 text-indigo-400">
              <Layout size={20} />
            </div>
            <div>
              <h2 className="font-black text-sm tracking-wider uppercase">Ascenda Architecture</h2>
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Admin Control Cluster</p>
            </div>
          </div>

          <div className="space-y-1">
            <TabButton id="boards" icon={<Database size={16} />} label="Exam Boards" active={activeTab} onClick={setActiveTab} />
            <TabButton id="grades" icon={<GraduationCap size={16} />} label="Grade Containers" active={activeTab} onClick={setActiveTab} />
            <div className="pt-4 pb-1 px-3 text-[10px] font-black text-slate-500 tracking-widest uppercase">Regular Streams</div>
            <TabButton id="regSubjects" icon={<BookOpen size={16} />} label="Core Subjects" active={activeTab} onClick={setActiveTab} />
            <TabButton id="regAreas" icon={<Layers size={16} />} label="Subject Units" active={activeTab} onClick={setActiveTab} />
            <div className="pt-4 pb-1 px-3 text-[10px] font-black text-slate-500 tracking-widest uppercase">Exam Streams</div>
            <TabButton id="examSubjects" icon={<Microscope size={16} />} label="Exam Subjects" active={activeTab} onClick={setActiveTab} />
            <TabButton id="examAreas" icon={<Book size={16} />} label="Exam Specialties" active={activeTab} onClick={setActiveTab} />
          </div>
        </div>

        <div className="p-4 border-t border-slate-800/40">
          <button onClick={onExit} className="w-full py-3 bg-slate-950 border border-slate-800 rounded-xl text-xs font-bold text-slate-400 hover:text-white hover:bg-slate-800 transition-all">
            ← Exit Architect Terminal
          </button>
        </div>
      </aside>

      {/* WORKSPACE CONTENT AREA */}
      <main className="flex-grow p-8 overflow-y-auto flex flex-col gap-6">
        <div className="bg-slate-900/30 p-6 rounded-2xl border border-slate-900">
          <h2 className="text-xl font-bold flex items-center gap-2 mb-4">
            <span className="text-indigo-500">⊕</span> Form Ingestion Control
          </h2>

          {activeTab === 'boards' && (
            <form onSubmit={handleCreateBoard} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Board / Org Name</label>
                <input type="text" placeholder="e.g., CBSE, IITJEE, NEET" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs outline-none focus:border-indigo-500 text-white" value={boardForm.name} onChange={e => setBoardForm({...boardForm, name: e.target.value})} />
              </div>
              <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all">Save Board</button>
            </form>
          )}

          {activeTab === 'grades' && (
            <form onSubmit={handleCreateGrade} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Target Parent Board</label>
                <select className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white" value={gradeForm.org_id} onChange={e => setGradeForm({...gradeForm, org_id: e.target.value})}>
                  <option value="">Select Board</option>
                  {data.boards?.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Grade Level Identifier</label>
                <input type="text" placeholder="e.g., 10, 12" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white" value={gradeForm.level} onChange={e => setGradeForm({...gradeForm, level: e.target.value})} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Display Title (Optional)</label>
                <input type="text" placeholder="e.g., Class 10 Foundation" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white" value={gradeForm.name} onChange={e => setGradeForm({...gradeForm, name: e.target.value})} />
              </div>
              <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all">Save Grade</button>
            </form>
          )}

          {(activeTab === 'regSubjects' || activeTab === 'examSubjects') && (
            <form onSubmit={handleCreateSubject} className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Container Grade</label>
                <select className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white" value={subjectForm.grade_id} onChange={e => setSubjectForm({...subjectForm, grade_id: e.target.value})}>
                  <option value="">Select Target Grade</option>
                  {data.grades?.map(g => <option key={g.id} value={g.id}>Grade {g.level} ({g.name})</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Subject Name</label>
                <input type="text" placeholder="e.g., Quantum Mechanics" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white" value={subjectForm.name} onChange={e => setSubjectForm({...subjectForm, name: e.target.value})} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Subject Code</label>
                <input type="text" placeholder="e.g., PHY-QM" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white" value={subjectForm.subject_code} onChange={e => setSubjectForm({...subjectForm, subject_code: e.target.value})} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Video Asset URL</label>
                <input type="text" placeholder="https://..." className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white" value={subjectForm.video_url} onChange={e => setSubjectForm({...subjectForm, video_url: e.target.value})} />
              </div>
              <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all">Save Subject</button>
            </form>
          )}
        </div>

        {/* DATA CONTAINER ELEMENT VIEW TABLE */}
        <div className="flex-grow bg-slate-900/10 border border-slate-900 rounded-2xl overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800/80 bg-slate-900/40">
                <th className="p-4 text-[10px] font-black uppercase tracking-widest text-slate-400">Node Properties</th>
                <th className="p-4 text-[10px] font-black uppercase tracking-widest text-slate-400">System Entity Key</th>
                <th className="p-4 text-right text-[10px] font-black uppercase tracking-widest text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              {currentItems.map((item) => (
                <tr key={item.id} className="border-b border-slate-900/60 hover:bg-slate-900/20 transition-all">
                  <td className="p-4">
                    <span className="font-bold text-sm text-slate-200">{item.name || `Level ${item.level}`}</span>
                  </td>
                  <td className="p-4 font-mono text-xs text-slate-500">{item.id}</td>
                  <td className