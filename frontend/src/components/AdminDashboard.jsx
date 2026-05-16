import React, { useState, useEffect } from 'react';
import { Layout, Database, BookOpen, Trash2, Layers, GraduationCap, Microscope, Book, Edit3, Check, X } from 'lucide-react';

const AdminDashboard = ({ apiBase, onExit }) => {
  const [activeTab, setActiveTab] = useState('boards');
  const [loading, setLoading] = useState(true);
  
  // Data vectors tracking architecture states
  const [data, setData] = useState({ 
    boards: [], grades: [], exams: [], regSubjects: [], regAreas: [], examSubjects: [], examAreas: [] 
  });

  // Inline editor states
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', subject_code: '', video_url: '' });

  // Input ingestion forms state management
  const [boardForm, setBoardForm] = useState({ name: '', org_type: 'Exam Board' });
  const [gradeForm, setGradeForm] = useState({ level: '', name: '', org_id: '' });
  const [subjectForm, setSubjectForm] = useState({ 
    name: '', subject_code: '', grade_id: '', discipline: 'Competitive Exam', video_url: '' 
  });

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const endpoints = {
        boards: '/api/admin/organizations/',
        grades: '/api/admin/curriculum/grades',
        exams: '/api/admin/curriculum/exams',
        regSubjects: '/api/admin/curriculum/regular/subjects',
        regAreas: '/api/admin/curriculum/regular/subject-areas',
        examSubjects: '/api/admin/curriculum/exam/subjects',
        examAreas: '/api/admin/curriculum/exam/subject-areas'
      };

      // 1. Fetch active view data layer
      const res = await fetch(`${apiBase}${endpoints[activeTab]}`);
      const result = await res.json();

      // 2. Multi-tenant drop-down collection synchronization
      const [exRes, grRes, brRes] = await Promise.all([
        fetch(`${apiBase}/api/admin/curriculum/exams`),
        fetch(`${apiBase}/api/admin/curriculum/grades`),
        fetch(`${apiBase}/api/admin/organizations/`)
      ]);
      const exData = await exRes.json();
      const grData = await grRes.json();
      const brData = await brRes.json();

      setData({
        boards: Array.isArray(brData) ? brData : [],
        grades: Array.isArray(grData) ? grData : [],
        exams: Array.isArray(exData) ? exData : [],
        regSubjects: activeTab === 'regSubjects' ? (Array.isArray(result) ? result : []) : [],
        regAreas: activeTab === 'regAreas' ? (Array.isArray(result) ? result : []) : [],
        examSubjects: activeTab === 'examSubjects' ? (Array.isArray(result) ? result : []) : [],
        examAreas: activeTab === 'examAreas' ? (Array.isArray(result) ? result : []) : [],
        [activeTab]: Array.isArray(result) ? result : []
      });

    } catch (err) {
      console.error("Cluster context synchronization failure:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (url, body, resetForm) => {
    try {
      const res = await fetch(`${apiBase}${url}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (res.ok) {
        resetForm();
        fetchData();
      } else {
        const errorDetails = await res.json();
        console.error("Ingestion server rejection payload:", errorDetails);
        alert(`Failed to save record: ${JSON.stringify(errorDetails.detail || "Validation Error")}`);
      }
    } catch (err) {
      console.error("Ingestion channel transmission issue:", err);
    }
  };

  const handleUpdate = async (id, updatedFields) => {
    try {
      let targetUrl = `/api/admin/curriculum/regular/subjects/${id}`;
      let bodyPayload = { ...updatedFields };

      if (activeTab === 'examSubjects') {
        targetUrl = `/api/admin/curriculum/exam/subjects/${id}`;
        const selectedItem = data.examSubjects.find(item => item.id === id);
        bodyPayload.exam_id = selectedItem.exam_id; 
        bodyPayload.discipline = selectedItem.discipline || 'Competitive Exam';
      }

      const res = await fetch(`${apiBase}${targetUrl}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyPayload)
      });
      if (res.ok) {
        setEditingId(null);
        fetchData();
      }
    } catch (err) {
      console.error("Pipeline target mutation patch issue:", err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Confirm permanent removal action against selected configuration row node?")) return;
    try {
      const endpoints = {
        regSubjects: `/api/admin/curriculum/regular/subjects/${id}`,
        examSubjects: `/api/admin/curriculum/exam/subjects/${id}`
      };
      const targetUrl = endpoints[activeTab] || `/api/admin/curriculum/${activeTab}/${id}`;
      const res = await fetch(`${apiBase}${targetUrl}`, { method: 'DELETE' });
      if (res.ok) fetchData();
    } catch (err) {
      console.error("Destruction runtime execution crash:", err);
    }
  };

  const startInlineEditing = (item) => {
    setEditingId(item.id);
    setEditForm({
      name: item.name,
      subject_code: item.subject_code || '',
      video_url: item.video_url || ''
    });
  };

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
            <form onSubmit={(e) => { e.preventDefault(); if(boardForm.name) handleCreate('/api/admin/organizations/', boardForm, () => setBoardForm({ name: '', org_type: 'Exam Board' })); }} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Board / Org Name</label>
                <input type="text" placeholder="e.g., CBSE, IITJEE, NEET" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none focus:border-indigo-500" value={boardForm.name} onChange={e => setBoardForm({...boardForm, name: e.target.value})} />
              </div>
              <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all">Save Board</button>
            </form>
          )}

          {activeTab === 'grades' && (
            <form onSubmit={(e) => { e.preventDefault(); if(gradeForm.level && gradeForm.org_id) handleCreate('/api/admin/curriculum/grades', { ...gradeForm, name: gradeForm.name || `Grade ${gradeForm.level}` }, () => setGradeForm({ level: '', name: '', org_id: '' })); }} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Target Parent Board</label>
                <select className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none" value={gradeForm.org_id} onChange={e => setGradeForm({...gradeForm, org_id: e.target.value})}>
                  <option value="">Select Board</option>
                  {data.boards?.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Grade Level</label>
                <input type="text" placeholder="e.g., 10, 12" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none" value={gradeForm.level} onChange={e => setGradeForm({...gradeForm, level: e.target.value})} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Display Title (Optional)</label>
                <input type="text" placeholder="e.g., Class 10 Foundation" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none" value={gradeForm.name} onChange={e => setGradeForm({...gradeForm, name: e.target.value})} />
              </div>
              <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all">Save Grade</button>
            </form>
          )}

          {(activeTab === 'regSubjects' || activeTab === 'examSubjects') && (
            <form 
              onSubmit={(e) => { 
                e.preventDefault(); 
                if (subjectForm.name && subjectForm.grade_id) {
                  let parsedPayload = {};
                  let targetUrl = '';

                  if (activeTab === 'examSubjects') {
                    const selectedExam = data.exams.find(ex => ex.id === subjectForm.grade_id);
                    const examCode = selectedExam ? selectedExam.code : 'EXAM';
                    
                    // FIXED: Ensure strict mapping to exam_id to satisfy Pydantic Schema validations
                    parsedPayload = {
                      name: subjectForm.name,
                      exam_id: subjectForm.grade_id, 
                      subject_code: `${examCode}_${subjectForm.name.toUpperCase()}`,
                      discipline: 'Competitive Exam',
                      video_url: subjectForm.video_url || ""
                    };
                    targetUrl = '/api/admin/curriculum/exam/subjects';
                  } else {
                    parsedPayload = {
                      name: subjectForm.name,
                      grade_id: subjectForm.grade_id,
                      subject_code: subjectForm.subject_code,
                      discipline: subjectForm.discipline || 'General',
                      video_url: subjectForm.video_url || ""
                    };
                    targetUrl = '/api/admin/curriculum/regular/subjects';
                  }

                  handleCreate(targetUrl, parsedPayload, () => 
                    setSubjectForm({ name: '', subject_code: '', grade_id: '', discipline: 'Competitive Exam', video_url: '' })
                  ); 
                } else {
                  alert("Please complete the required form fields before saving.");
                }
              }} 
              className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end"
            >
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">
                  {activeTab === 'examSubjects' ? 'Target Exam Stream' : 'Container Grade'}
                </label>
                <select 
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none focus:border-indigo-500" 
                  value={subjectForm.grade_id} 
                  onChange={e => setSubjectForm({...subjectForm, grade_id: e.target.value})}
                >
                  <option value="">{activeTab === 'examSubjects' ? 'Select Exam Stream' : 'Select Target Grade'}</option>
                  {activeTab === 'examSubjects' 
                    ? data.exams?.map(ex => <option key={ex.id} value={ex.id}>{ex.name} ({ex.code})</option>)
                    : data.grades?.map(g => <option key={g.id} value={g.id}>Grade {g.level} ({g.name})</option>)
                  }
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Subject Name</label>
                <input type="text" placeholder="e.g., Physics, Chemistry, Maths" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none focus:border-indigo-500" value={subjectForm.name} onChange={e => setSubjectForm({...subjectForm, name: e.target.value})} />
              </div>
              
              {activeTab === 'regSubjects' ? (
                <div>
                  <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Subject Code</label>
                  <input type="text" placeholder="e.g., PHY-QM" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none focus:border-indigo-500" value={subjectForm.subject_code} onChange={e => setSubjectForm({...subjectForm, subject_code: e.target.value})} />
                </div>
              ) : (
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Auto Code Preview</label>
                  <div className="w-full bg-slate-900/50 border border-slate-800/40 rounded-xl p-3 text-xs text-slate-500 font-mono select-none h-[42px] flex items-center">
                    {subjectForm.grade_id && subjectForm.name 
                      ? `${(data.exams.find(ex => ex.id === subjectForm.grade_id)?.code || 'EXAM')}_${subjectForm.name.toUpperCase()}`
                      : 'Waiting for stream allocation...'}
                  </div>
                </div>
              )}

              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Video Asset URL</label>
                <input type="text" placeholder="https://..." className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none focus:border-indigo-500" value={subjectForm.video_url} onChange={e => setSubjectForm({...subjectForm, video_url: e.target.value})} />
              </div>
              <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all">Save Subject</button>
            </form>
          )}
        </div>

        {/* WORKSPACE DATA RECORDING SHEETS */}
        <div className="flex-grow bg-slate-900/10 border border-slate-900 rounded-2xl overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800/80 bg-slate-900/40">
                <th className="p-4 text-[10px] font-black uppercase tracking-widest text-slate-400">Subject / Code</th>
                <th className="p-4 text-[10px] font-black uppercase tracking-widest text-slate-400">System Entity Key</th>
                <th className="p-4 text-right text-[10px] font-black uppercase tracking-widest text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              {currentItems.map((item) => (
                <tr key={item.id} className="border-b border-slate-900/60 hover:bg-slate-900/20 transition-all">
                  <td className="p-4">
                    {editingId === item.id ? (
                      <div className="flex flex-col md:flex-row gap-2">
                        <input type="text" className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white outline-none" value={editForm.name} onChange={e => setEditForm({...editForm, name: e.target.value})} />
                        <input type="text" className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white font-mono outline-none" value={editForm.subject_code} onChange={e => setEditForm({...editForm, subject_code: e.target.value})} />
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-200">{item.name || `Level ${item.level}`}</span>
                        {item.subject_code && (
                          <span className="px-2 py-0.5 text-[9px] font-bold tracking-wider bg-slate-800 text-indigo-400 rounded border border-slate-700/60 uppercase">
                            {item.subject_code}
                          </span>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="p-4 font-mono text-xs text-slate-500">{item.id}</td>
                  <td className="p-4 text-right">
                    {editingId === item.id ? (
                      <div className="flex justify-end gap-1">
                        <button onClick={() => handleUpdate(item.id, editForm)} className="p-2 text-green-400 hover:bg-green-500/10 rounded transition-all"><Check size={14} /></button>
                        <button onClick={() => setEditingId(null)} className="p-2 text-slate-400 hover:bg-slate-800 rounded transition-all"><X size={14} /></button>
                      </div>
                    ) : (
                      <div className="flex justify-end gap-1">
                        {(activeTab === 'regSubjects' || activeTab === 'examSubjects') && (
                          <button onClick={() => startInlineEditing(item)} className="p-2 text-slate-400 hover:text-indigo-400 transition-all"><Edit3 size={14} /></button>
                        )}
                        <button onClick={() => handleDelete(item.id)} className="p-2 text-slate-500 hover:text-red-400 transition-all"><Trash2 size={14} /></button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
              {currentItems.length === 0 && !loading && (
                <tr>
                  <td colSpan="3" className="p-20 text-center text-slate-600 font-medium italic text-xs">
                    No matching records linked in current structural context.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
};

const TabButton = ({ id, icon, label, active, onClick }) => (
  <button 
    onClick={() => onClick(id)} 
    className={`w-full flex items-center gap-3 p-3.5 rounded-xl font-bold transition-all duration-200 ${
      active === id ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
    }`}
  >
    {icon}
    <span className="text-xs tracking-wide">{label}</span>
  </button>
);

export default AdminDashboard;