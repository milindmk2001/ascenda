import React, { useState, useEffect } from 'react';

export default function AdminDashboard({ apiBase, onExit }) {
  const [activeTab, setActiveTab] = useState('boards');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Data Matrices from Backend
  const [organizations, setOrganizations] = useState([]);
  const [grades, setGrades] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [areas, setAreas] = useState([]);
  const [chapters, setChapters] = useState([]);

  // Ingestion Form Target Values
  const [orgName, setOrgName] = useState('');
  const [orgType, setOrgType] = useState('School Board');
  
  const [selectedOrgId, setSelectedOrgId] = useState('');
  const [gradeName, setGradeName] = useState('');
  const [gradeLevel, setGradeLevel] = useState('');

  const [selectedGradeId, setSelectedGradeId] = useState('');
  const [subjectName, setSubjectName] = useState('');
  const [subjectCode, setSubjectCode] = useState('');
  const [discipline, setDiscipline] = useState('Science');

  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [areaTitle, setAreaTitle] = useState('');
  const [areaOrder, setAreaOrder] = useState('1');

  const [selectedAreaId, setSelectedAreaId] = useState('');
  const [chapterTitle, setChapterTitle] = useState('');
  const [chapterOrder, setChapterOrder] = useState('1');

  // Automatically synchronize active view tab dataset dependencies
  useEffect(() => {
    fetchActiveTabData();
  }, [activeTab]);

  const fetchActiveTabData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      if (activeTab === 'boards') {
        const res = await fetch(`${apiBase}/api/admin/organizations/`);
        if (!res.ok) throw new Error(`Failed to load Boards: ${res.status}`);
        const data = await res.json();
        setOrganizations(Array.isArray(data) ? data : []);
      } 
      
      else if (activeTab === 'grades') {
        const [orgRes, gradeRes] = await Promise.all([
          fetch(`${apiBase}/api/admin/organizations/`),
          fetch(`${apiBase}/api/admin/curriculum/grades`)
        ]);
        const orgs = await orgRes.json();
        const grds = await gradeRes.json();
        setOrganizations(Array.isArray(orgs) ? orgs : []);
        setGrades(Array.isArray(grds) ? grds : []);
        if (orgs.length > 0 && !selectedOrgId) setSelectedOrgId(orgs[0].id);
      } 
      
      else if (activeTab === 'subjects') {
        const [gradeRes, subRes] = await Promise.all([
          fetch(`${apiBase}/api/admin/curriculum/grades`),
          fetch(`${apiBase}/api/admin/curriculum/regular/subjects`)
        ]);
        const grds = await gradeRes.json();
        const subs = await subRes.json();
        setGrades(Array.isArray(grds) ? grds : []);
        setSubjects(Array.isArray(subs) ? subs : []);
        if (grds.length > 0 && !selectedGradeId) setSelectedGradeId(grds[0].id);
      } 
      
      else if (activeTab === 'areas') {
        const [subRes, areaRes] = await Promise.all([
          fetch(`${apiBase}/api/admin/curriculum/regular/subjects`),
          fetch(`${apiBase}/api/admin/curriculum/regular/subject-areas`)
        ]);
        const subs = await subRes.json();
        const ars = await areaRes.json();
        setSubjects(Array.isArray(subs) ? subs : []);
        setAreas(Array.isArray(ars) ? ars : []);
        if (subs.length > 0 && !selectedSubjectId) setSelectedSubjectId(subs[0].id);
      } 
      
      else if (activeTab === 'chapters') {
        const [areaRes, chapRes] = await Promise.all([
          fetch(`${apiBase}/api/admin/curriculum/regular/subject-areas`),
          fetch(`${apiBase}/api/admin/curriculum/regular/chapters`)
        ]);
        const ars = await areaRes.json();
        const chaps = await chapRes.json();
        setAreas(Array.isArray(ars) ? ars : []);
        setChapters(Array.isArray(chaps) ? chaps : []);
        if (ars.length > 0 && !selectedAreaId) setSelectedAreaId(ars[0].id);
      }
    } catch (err) {
      console.error("Dashboard Sync Exception Error:", err);
      setErrorMsg(err.message || "Pipeline structural synchronization failed.");
    } finally {
      setLoading(false);
    }
  };

  // Submission Mutation Actions Handlers
  const handleCreateBoard = async (e) => {
    e.preventDefault();
    if (!orgName) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/organizations/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: orgName, org_type: orgType })
      });
      if (!res.ok) throw new Error("Could not commit Board record entry.");
      setOrgName('');
      fetchActiveTabData();
    } catch (err) { alert(err.message); }
  };

  const handleCreateGrade = async (e) => {
    e.preventDefault();
    if (!selectedOrgId || !gradeLevel) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/grades`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ org_id: selectedOrgId, level: parseInt(gradeLevel), name: gradeName || `Grade ${gradeLevel}` })
      });
      if (!res.ok) throw new Error("Could not commit Grade tracking node.");
      setGradeLevel('');
      setGradeName('');
      fetchActiveTabData();
    } catch (err) { alert(err.message); }
  };

  const handleCreateSubject = async (e) => {
    e.preventDefault();
    if (!selectedGradeId || !subjectName || !subjectCode) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/regular/subjects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grade_id: selectedGradeId, name: subjectName, subject_code: subjectCode, discipline })
      });
      if (!res.ok) throw new Error("Could not register subject architectural node.");
      setSubjectName('');
      setSubjectCode('');
      fetchActiveTabData();
    } catch (err) { alert(err.message); }
  };

  const handleCreateArea = async (e) => {
    e.preventDefault();
    if (!selectedSubjectId || !areaTitle) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/regular/subject-areas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject_id: selectedSubjectId, title: areaTitle, sequence_order: parseInt(areaOrder) })
      });
      if (!res.ok) throw new Error("Could not append subject unit blueprint.");
      setAreaTitle('');
      fetchActiveTabData();
    } catch (err) { alert(err.message); }
  };

  const handleCreateChapter = async (e) => {
    e.preventDefault();
    if (!selectedAreaId || !chapterTitle) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/regular/chapters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject_area_id: selectedAreaId, title: chapterTitle, sequence_order: parseInt(chapterOrder) })
      });
      if (!res.ok) throw new Error("Could not link active chapter cell block.");
      setChapterTitle('');
      fetchActiveTabData();
    } catch (err) { alert(err.message); }
  };

  return (
    <div className="flex-grow p-6 bg-slate-900 text-white flex flex-col font-sans">
      <header className="flex justify-between items-center border-b border-slate-800 pb-4 mb-6">
        <div>
          <h1 className="text-xl font-black tracking-tight text-emerald-400 uppercase">Ascenda Ingestion Console</h1>
          <p className="text-xs text-slate-400 font-mono">Curriculum Node Architecture & Processing Base</p>
        </div>
        <button onClick={onExit} className="px-4 py-1.5 bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 rounded-lg text-xs font-bold transition">
          Return to Hub Engine
        </button>
      </header>

      {/* Navigation Sub-Tabs */}
      <div className="flex flex-wrap gap-2 mb-6 bg-slate-950 p-1 border border-slate-800 rounded-lg max-w-xl">
        {['boards', 'grades', 'subjects', 'areas', 'chapters'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-3 py-1.5 text-center text-xs font-bold rounded-md transition uppercase tracking-wider ${activeTab === tab ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-200'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {errorMsg && (
        <div className="p-4 mb-6 bg-red-950/50 border border-red-800 text-red-300 rounded-lg text-xs font-mono">
          <strong>Pipeline Alert:</strong> {errorMsg}
        </div>
      )}

      {loading ? (
        <div className="flex-grow flex items-center justify-center text-slate-500 font-mono text-xs tracking-widest animate-pulse">
          FETCHING CLUSTER NODE MATRICES FROM SUPABASE CLOUD DEPLOYMENT...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-grow items-start">
          
          {/* LEFT COLUMN: Dynamic contextual submission generation forms */}
          <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-2xl">
            <h2 className="text-sm font-bold tracking-wide uppercase mb-4 text-slate-300">
              Provision {activeTab.slice(0, -1)} Structure Node
            </h2>
            
            {activeTab === 'boards' && (
              <form onSubmit={handleCreateBoard} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Board / Organization Title</label>
                  <input type="text" value={orgName} onChange={e => setOrgName(e.target.value)} placeholder="e.g., CBSE, NEET Track" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-bold rounded-lg text-xs uppercase text-white transition">Commit Organization Node</button>
              </form>
            )}

            {activeTab === 'grades' && (
              <form onSubmit={handleCreateGrade} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Parent Framework Scope</label>
                  <select value={selectedOrgId} onChange={e => setSelectedOrgId(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-slate-700 cursor-pointer">
                    {organizations.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Grade Level Integer</label>
                  <input type="number" value={gradeLevel} onChange={e => setGradeLevel(e.target.value)} placeholder="e.g., 11" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Custom Label (Optional)</label>
                  <input type="text" value={gradeName} onChange={e => setGradeName(e.target.value)} placeholder="e.g., Class 11-Medical" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-bold rounded-lg text-xs uppercase text-white transition">Commit Grade Frame</button>
              </form>
            )}

            {activeTab === 'subjects' && (
              <form onSubmit={handleCreateSubject} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Target Level Mapping</label>
                  <select value={selectedGradeId} onChange={e => setSelectedGradeId(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-slate-700 cursor-pointer">
                    {grades.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Subject System Name</label>
                  <input type="text" value={subjectName} onChange={e => setSubjectName(e.target.value)} placeholder="e.g., Physics" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Identifier System Code</label>
                  <input type="text" value={subjectCode} onChange={e => setSubjectCode(e.target.value)} placeholder="e.g., K12_PHYS" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-bold rounded-lg text-xs uppercase text-white transition">Commit Subject Track</button>
              </form>
            )}

            {activeTab === 'areas' && (
              <form onSubmit={handleCreateArea} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Parent Subject Anchor</label>
                  <select value={selectedSubjectId} onChange={e => setSelectedSubjectId(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-slate-700 cursor-pointer">
                    {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Unit Title Naming</label>
                  <input type="text" value={areaTitle} onChange={e => setAreaTitle(e.target.value)} placeholder="e.g., Mechanics & Kinematics" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Order Index Sequence Position</label>
                  <input type="number" value={areaOrder} onChange={e => setAreaOrder(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-bold rounded-lg text-xs uppercase text-white transition">Commit Area Unit</button>
              </form>
            )}

            {activeTab === 'chapters' && (
              <form onSubmit={handleCreateChapter} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Parent Unit Category</label>
                  <select value={selectedAreaId} onChange={e => setSelectedAreaId(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-slate-700 cursor-pointer">
                    {areas.map(a => <option key={a.id} value={a.id}>{a.title}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Chapter Content Heading Title</label>
                  <input type="text" value={chapterTitle} onChange={e => setChapterTitle(e.target.value)} placeholder="e.g., Rotational Dynamics" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Sequence Positioning Index</label>
                  <input type="number" value={chapterOrder} onChange={e => setChapterOrder(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-bold rounded-lg text-xs uppercase text-white transition">Commit Chapter Block</button>
              </form>
            )}
          </div>

          {/* RIGHT COLUMN: Active dataset records verification engine lists */}
          <div className="lg:col-span-2 bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-2xl self-stretch overflow-y-auto max-h-[68vh]">
            <h2 className="text-sm font-bold tracking-wide uppercase mb-4 text-slate-300">Supabase Ingested Node Stream</h2>
            
            <div className="space-y-2">
              {activeTab === 'boards' && (
                organizations.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg">No organization node profiles matching structural paths.</p> :
                organizations.map(o => (
                  <div key={o.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-200">{o.name}</span>
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-emerald-400 font-mono text-[10px] rounded uppercase tracking-wider">{o.org_type || 'System Board'}</span>
                  </div>
                ))
              )}

              {activeTab === 'grades' && (
                grades.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg">No educational class containers registered.</p> :
                grades.map(g => (
                  <div key={g.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center">
                    <div>
                      <div className="text-xs font-bold text-slate-200">{g.name}</div>
                      <div className="text-[10px] font-mono text-slate-500 mt-0.5">Parent ID: {g.org_id || 'System Base Global'}</div>
                    </div>
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-slate-400 font-mono text-[10px] rounded">Lvl {g.level}</span>
                  </div>
                ))
              )}

              {activeTab === 'subjects' && (
                subjects.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg">No educational core courses registered.</p> :
                subjects.map(s => (
                  <div key={s.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center">
                    <div>
                      <div className="text-xs font-bold text-slate-200">{s.name}</div>
                      <div className="text-[10px] font-mono text-slate-500 mt-0.5">Discipline Domain: <span className="text-slate-400">{s.discipline || 'General'}</span></div>
                    </div>
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-slate-300 font-mono text-[10px] font-bold rounded uppercase tracking-wider">{s.subject_code}</span>
                  </div>
                ))
              )}

              {activeTab === 'areas' && (
                areas.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg">No instructional units or syllabus divisions map registered.</p> :
                areas.map(a => (
                  <div key={a.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-200">{a.title}</span>
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-slate-400 font-mono text-[10px] rounded">Seq Position {a.sequence_order}</span>
                  </div>
                ))
              )}

              {activeTab === 'chapters' && (
                chapters.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg">No delivery core learning target content chapters found.</p> :
                chapters.map(c => (
                  <div key={c.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-200">{c.title}</span>
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-slate-400 font-mono text-[10px] rounded">Seq Position {c.sequence_order}</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}