import React, { useState, useEffect } from 'react';

export default function AdminDashboard({ apiBase, onExit }) {
  // Mode Selection: 'k12' or 'competitive'
  const [mode, setMode] = useState('k12');
  
  // Tab Trackers
  const [k12Tab, setK12Tab] = useState('boards');
  const [compTab, setCompTab] = useState('exams');
  
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // --- DATA STATES ---
  // K-12 Structures
  const [organizations, setOrganizations] = useState([]);
  const [grades, setGrades] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [areas, setAreas] = useState([]);
  const [chapters, setChapters] = useState([]);

  // Competitive Exam Structures
  const [exams, setExams] = useState([]);
  const [examSubjects, setExamSubjects] = useState([]);

  // --- FORM FIELD STATES ---
  // K-12 Provisioning Inputs
  const [orgName, setOrgName] = useState('');
  const [selectedOrgId, setSelectedOrgId] = useState('');
  const [gradeLevel, setGradeLevel] = useState('');
  const [gradeName, setGradeName] = useState('');
  const [selectedGradeId, setSelectedGradeId] = useState('');
  const [subjectName, setSubjectName] = useState('');
  const [subjectCode, setSubjectCode] = useState('');
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [areaTitle, setAreaTitle] = useState('');
  const [areaOrder, setAreaOrder] = useState('1');
  const [selectedAreaId, setSelectedAreaId] = useState('');
  const [chapterTitle, setChapterTitle] = useState('');
  const [chapterOrder, setChapterOrder] = useState('1');

  // Competitive Provisioning Inputs
  const [examName, setExamName] = useState('');
  const [examCode, setExamCode] = useState('');
  const [selectedExamId, setSelectedExamId] = useState(''); 
  const [compSubjectName, setCompSubjectName] = useState('');
  const [compSubjectCode, setCompSubjectCode] = useState('');
  const [discipline, setDiscipline] = useState('Competitive Exam');

  // Automatically compute Competitive Subject Code when track or subject changes
  useEffect(() => {
    if (selectedExamId && compSubjectName) {
      const selectedExam = exams.find(e => String(e.id) === String(selectedExamId));
      if (selectedExam && selectedExam.code) {
        // Formats clean strings like: IITJEE_Physics
        const cleanSubjectName = compSubjectName.replace(/\s+/g, '_');
        setCompSubjectCode(`${selectedExam.code}_${cleanSubjectName}`);
      }
    } else {
      setCompSubjectCode('');
    }
  }, [selectedExamId, compSubjectName, exams]);

  // Sync data whenever mode or sub-tabs change
  useEffect(() => {
    fetchData();
  }, [mode, k12Tab, compTab]);

  const fetchData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      if (mode === 'k12') {
        if (k12Tab === 'boards') {
          const res = await fetch(`${apiBase}/api/admin/organizations/`);
          if (!res.ok) throw new Error(`Status ${res.status}`);
          const data = await res.json();
          setOrganizations(Array.isArray(data) ? data : []);
        } else if (k12Tab === 'grades') {
          const [orgRes, gradeRes] = await Promise.all([
            fetch(`${apiBase}/api/admin/organizations/`),
            fetch(`${apiBase}/api/admin/curriculum/grades`)
          ]);
          const orgs = await orgRes.json();
          const grds = await gradeRes.json();
          setOrganizations(Array.isArray(orgs) ? orgs : []);
          setGrades(Array.isArray(grds) ? grds : []);
          if (orgs.length > 0 && !selectedOrgId) setSelectedOrgId(orgs[0].id);
        } else if (k12Tab === 'subjects') {
          const [gradeRes, subRes] = await Promise.all([
            fetch(`${apiBase}/api/admin/curriculum/grades`),
            fetch(`${apiBase}/api/admin/curriculum/regular/subjects`)
          ]);
          const grds = await gradeRes.json();
          const subs = await subRes.json();
          setGrades(Array.isArray(grds) ? grds : []);
          setSubjects(Array.isArray(subs) ? subs : []);
          if (grds.length > 0 && !selectedGradeId) setSelectedGradeId(grds[0].id);
        } else if (k12Tab === 'areas') {
          const [subRes, areaRes] = await Promise.all([
            fetch(`${apiBase}/api/admin/curriculum/regular/subjects`),
            fetch(`${apiBase}/api/admin/curriculum/regular/subject-areas`)
          ]);
          const subs = await subRes.json();
          const ars = await areaRes.json();
          setSubjects(Array.isArray(subs) ? subs : []);
          setAreas(Array.isArray(ars) ? ars : []);
          if (subs.length > 0 && !selectedSubjectId) setSelectedSubjectId(subs[0].id);
        } else if (k12Tab === 'chapters') {
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
      } else {
        // Competitive Mode Data Layer Sync
        if (compTab === 'exams') {
          const res = await fetch(`${apiBase}/api/admin/curriculum/exams`);
          if (!res.ok) throw new Error(`Status ${res.status}`);
          const data = await res.json();
          setExams(Array.isArray(data) ? data : []);
        } else if (compTab === 'subjects') {
          const [examRes, subRes] = await Promise.all([
            fetch(`${apiBase}/api/admin/curriculum/exams`),
            fetch(`${apiBase}/api/admin/curriculum/exam/subjects`)
          ]);
          const examData = await examRes.json();
          const subData = await subRes.json();
          const safeExams = Array.isArray(examData) ? examData : [];
          
          setExams(safeExams);
          setExamSubjects(Array.isArray(subData) ? subData : []);
          
          if (safeExams.length > 0 && !selectedExamId) {
            setSelectedExamId(safeExams[0].id);
          }
        }
      }
    } catch (err) {
      console.error("Fetch Failure Matrix Configuration Route:", err);
      setErrorMsg(err.message || "Failed to parse database table nodes.");
    } finally {
      setLoading(false);
    }
  };

  // --- SUBMISSION MUTATIONS ---
  const handleCreateBoard = async (e) => {
    e.preventDefault();
    if (!orgName) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/organizations/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: orgName, org_type: 'School Board' })
      });
      if (!res.ok) throw new Error("Could not commit Board record entry.");
      setOrgName('');
      fetchData();
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
      if (!res.ok) throw new Error("Could not commit Grade container.");
      setGradeLevel('');
      setGradeName('');
      fetchData();
    } catch (err) { alert(err.message); }
  };

  const handleCreateSubject = async (e) => {
    e.preventDefault();
    if (!selectedGradeId || !subjectName || !subjectCode) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/regular/subjects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grade_id: selectedGradeId, name: subjectName, subject_code: subjectCode, discipline: 'Science' })
      });
      if (!res.ok) throw new Error("Could not register Subject architecture.");
      setSubjectName('');
      setSubjectCode('');
      fetchData();
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
      if (!res.ok) throw new Error("Could not append Unit Area profile.");
      setAreaTitle('');
      fetchData();
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
      if (!res.ok) throw new Error("Could not link active Chapter block.");
      setChapterTitle('');
      fetchData();
    } catch (err) { alert(err.message); }
  };

  // Competitive Form Handlers
  const handleCreateExam = async (e) => {
    e.preventDefault();
    if (!examName || !examCode) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/exams`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: examName, code: examCode })
      });
      if (!res.ok) throw new Error("Could not register competitive exam track blueprints.");
      setExamName('');
      setExamCode('');
      fetchData();
    } catch (err) { alert(err.message); }
  };

  const handleCreateExamSubject = async (e) => {
    e.preventDefault();
    if (!selectedExamId || !compSubjectName || !compSubjectCode) {
      alert("Please designate a parent Track/Board association container.");
      return;
    }
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/exam/subjects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exam_id: selectedExamId,
          name: compSubjectName,
          subject_code: compSubjectCode,
          discipline: discipline,
          video_url: ""
        })
      });
      if (!res.ok) throw new Error("Failed to write competitive exam subject reference configuration.");
      setCompSubjectName('');
      fetchData();
    } catch (err) { alert(err.message); }
  };

  // Client-side execution filtering layer for Competitive tracks based on active selection choice
  const displayedExamSubjects = examSubjects.filter(sub => String(sub.exam_id) === String(selectedExamId));

  return (
    <div className="flex-grow p-6 bg-slate-900 text-white flex flex-col font-sans">
      
      {/* HEADER ROW */}
      <header className="flex justify-between items-center border-b border-slate-800 pb-4 mb-6">
        <div>
          <h1 className="text-xl font-black tracking-tight text-emerald-400 uppercase">Ascenda Ingestion Console</h1>
          <p className="text-xs text-slate-400 font-mono">Unified Data Matrix Routing Center</p>
        </div>
        <button onClick={onExit} className="px-4 py-1.5 bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 rounded-lg text-xs font-bold transition">
          Return to Hub Engine
        </button>
      </header>

      {/* TOP-LEVEL MODE SELECTION PILOTS */}
      <div className="flex gap-4 mb-6 border-b border-slate-800/60 pb-4">
        <button
          onClick={() => setMode('k12')}
          className={`px-4 py-2 text-xs font-extrabold tracking-wider rounded-lg uppercase transition ${mode === 'k12' ? 'bg-emerald-600 text-white border border-emerald-500 shadow-md shadow-emerald-950' : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'}`}
        >
          ⚙️ K-12 System Mode
        </button>
        <button
          onClick={() => setMode('competitive')}
          className={`px-4 py-2 text-xs font-extrabold tracking-wider rounded-lg uppercase transition ${mode === 'competitive' ? 'bg-purple-600 text-white border border-purple-500 shadow-md shadow-purple-950' : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'}`}
        >
          🎯 Competitive Tracks (IITJEE/NEET)
        </button>
      </div>

      {/* DYNAMIC CHILD SUB-TAB SELECTORS PANEL */}
      <div className="flex flex-wrap gap-2 mb-6 bg-slate-950 p-1 border border-slate-800 rounded-lg max-w-xl">
        {mode === 'k12' ? (
          ['boards', 'grades', 'subjects', 'areas', 'chapters'].map((tab) => (
            <button
              key={tab}
              onClick={() => setK12Tab(tab)}
              className={`flex-1 px-3 py-1.5 text-center text-xs font-bold rounded-md transition uppercase tracking-wider ${k12Tab === tab ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-200'}`}
            >
              {tab}
            </button>
          ))
        ) : (
          ['exams', 'subjects'].map((tab) => (
            <button
              key={tab}
              onClick={() => setCompTab(tab)}
              className={`flex-1 px-4 py-1.5 text-center text-xs font-bold rounded-md transition uppercase tracking-wider ${compTab === tab ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-200'}`}
            >
              {tab === 'exams' ? 'Tracks / Boards' : 'Track Subjects'}
            </button>
          ))
        )}
      </div>

      {errorMsg && (
        <div className="p-4 mb-6 bg-red-950/50 border border-red-800 text-red-300 rounded-lg text-xs font-mono">
          <strong>Initialization Notice Pipeline Flag:</strong> {errorMsg}
        </div>
      )}

      {loading ? (
        <div className="flex-grow flex items-center justify-center text-slate-500 font-mono text-xs tracking-widest animate-pulse">
          FETCHING TARGET DATA CLUSTER MATRIX STREAMS...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-grow items-start">
          
          {/* LEFT PANEL: INPUT SUBMISSION FORMS ENGINE */}
          <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-2xl">
            <h2 className="text-sm font-bold tracking-wide uppercase mb-4 text-slate-300">
              Provision {mode === 'k12' ? k12Tab.slice(0, -1) : compTab === 'exams' ? 'Competitive Track' : 'Track Subject'}
            </h2>

            {/* --- K-12 FORMS DISPATCH MATRIX --- */}
            {mode === 'k12' && k12Tab === 'boards' && (
              <form onSubmit={handleCreateBoard} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Board Nomenclature Name</label>
                  <input type="text" value={orgName} onChange={e => setOrgName(e.target.value)} placeholder="e.g., CBSE" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-bold rounded-lg text-xs uppercase text-white transition">Commit K12 Board Profile</button>
              </form>
            )}

            {mode === 'k12' && k12Tab === 'grades' && (
              <form onSubmit={handleCreateGrade} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Parent Organization Anchor</label>
                  <select value={selectedOrgId} onChange={e => setSelectedOrgId(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-slate-700 cursor-pointer">
                    {organizations.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Grade Level Int Vector</label>
                  <input type="number" value={gradeLevel} onChange={e => setGradeLevel(e.target.value)} placeholder="e.g., 11" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Custom Label (Optional)</label>
                  <input type="text" value={gradeName} onChange={e => setGradeName(e.target.value)} placeholder="e.g., Class 11-Science" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-bold rounded-lg text-xs uppercase text-white transition">Commit Grade Framework</button>
              </form>
            )}

            {mode === 'k12' && k12Tab === 'subjects' && (
              <form onSubmit={handleCreateSubject} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Target Level Mapping Anchor</label>
                  <select value={selectedGradeId} onChange={e => setSelectedGradeId(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-slate-700 cursor-pointer">
                    {grades.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Subject System Title</label>
                  <input type="text" value={subjectName} onChange={e => setSubjectName(e.target.value)} placeholder="e.g., Physics" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">System Code String</label>
                  <input type="text" value={subjectCode} onChange={e => setSubjectCode(e.target.value)} placeholder="e.g., K12_PHYS" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-bold rounded-lg text-xs uppercase text-white transition">Commit Subject Node</button>
              </form>
            )}

            {mode === 'k12' && k12Tab === 'areas' && (
              <form onSubmit={handleCreateArea} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Parent Subject Core Base</label>
                  <select value={selectedSubjectId} onChange={e => setSelectedSubjectId(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-slate-700 cursor-pointer">
                    {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Unit Title</label>
                  <input type="text" value={areaTitle} onChange={e => setAreaTitle(e.target.value)} placeholder="e.g., Kinematics" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Sequence Order Position</label>
                  <input type="number" value={areaOrder} onChange={e => setAreaOrder(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-bold rounded-lg text-xs uppercase text-white transition">Commit Area Node</button>
              </form>
            )}

            {mode === 'k12' && k12Tab === 'chapters' && (
              <form onSubmit={handleCreateChapter} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Parent Unit Scope Area</label>
                  <select value={selectedAreaId} onChange={e => setSelectedAreaId(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-slate-700 cursor-pointer">
                    {areas.map(a => <option key={a.id} value={a.id}>{a.title}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Chapter Content Title</label>
                  <input type="text" value={chapterTitle} onChange={e => setChapterTitle(e.target.value)} placeholder="e.g., Vector Motion" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Sequence Order Positioning</label>
                  <input type="number" value={chapterOrder} onChange={e => setChapterOrder(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-bold rounded-lg text-xs uppercase text-white transition">Commit Chapter Core</button>
              </form>
            )}


            {/* --- COMPETITIVE FORMS DISPATCH MATRIX --- */}
            {mode === 'competitive' && compTab === 'exams' && (
              <form onSubmit={handleCreateExam} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Competitive Track / Board Title</label>
                  <input type="text" value={examName} onChange={e => setExamName(e.target.value)} placeholder="e.g., IIT JEE Advanced" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Operational Track Key Identifier</label>
                  <input type="text" value={examCode} onChange={e => setExamCode(e.target.value)} placeholder="e.g., IITJEE" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-purple-600 hover:bg-purple-500 font-bold rounded-lg text-xs uppercase text-white transition border border-purple-500">Commit Track Model Blueprint</button>
              </form>
            )}

            {mode === 'competitive' && compTab === 'subjects' && (
              <form onSubmit={handleCreateExamSubject} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Target Active Track Filter</label>
                  <select value={selectedExamId} onChange={e => setSelectedExamId(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-slate-700 cursor-pointer">
                    {exams.map(ex => <option key={ex.id} value={ex.id}>{ex.name} ({ex.code})</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Competitive Subject Module Title</label>
                  <input type="text" value={compSubjectName} onChange={e => setCompSubjectName(e.target.value)} placeholder="e.g., Physics" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Unique Identifier Code</label>
                  <input 
                    type="text" 
                    value={compSubjectCode} 
                    onChange={e => setCompSubjectCode(e.target.value)} 
                    placeholder="Auto-generated (e.g., IITJEE_Physics)" 
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-slate-700 font-mono" 
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Discipline Domain Classification</label>
                  <input type="text" value={discipline} onChange={e => setDiscipline(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-purple-600 hover:bg-purple-500 font-bold rounded-lg text-xs uppercase text-white transition border border-purple-500">Commit Exam Subject Blueprint</button>
              </form>
            )}
          </div>

          {/* RIGHT PANEL: LIVE STREAM RECORD VERIFICATIONS */}
          <div className="lg:col-span-2 bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-2xl self-stretch overflow-y-auto max-h-[68vh]">
            
            {/* Context Header for Subject views under Competitive Mode */}
            {mode === 'competitive' && compTab === 'subjects' && (
              <div className="mb-4 p-3 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold tracking-wider font-mono text-slate-400">Filtering view context by active target:</span>
                <select 
                  value={selectedExamId} 
                  onChange={e => setSelectedExamId(e.target.value)}
                  className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs outline-none text-purple-400 font-bold cursor-pointer"
                >
                  {exams.map(ex => <option key={ex.id} value={ex.id}>{ex.name}</option>)}
                </select>
              </div>
            )}

            <h2 className="text-sm font-bold tracking-wide uppercase mb-4 text-slate-300">
              Active Database Table Stream ({mode.toUpperCase()})
            </h2>
            
            <div className="space-y-2">
              {/* --- K-12 REALTIME MONITOR VIEWS --- */}
              {mode === 'k12' && k12Tab === 'boards' && (
                organizations.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg">No K12 organization profiles found.</p> :
                organizations.map(o => (
                  <div key={o.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-200">{o.name}</span>
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-emerald-400 font-mono text-[10px] rounded uppercase tracking-wider">{o.org_type || 'System Board'}</span>
                  </div>
                ))
              )}

              {mode === 'k12' && k12Tab === 'grades' && (
                grades.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg">No grade system frames detected.</p> :
                grades.map(g => (
                  <div key={g.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-200">{g.name}</span>
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-slate-400 font-mono text-[10px] rounded">Lvl {g.level}</span>
                  </div>
                ))
              )}

              {mode === 'k12' && k12Tab === 'subjects' && (
                subjects.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg">No core academic subject tracks bound.</p> :
                subjects.map(s => (
                  <div key={s.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-200">{s.name}</span>
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-slate-300 font-mono text-[10px] font-bold rounded uppercase tracking-wider">{s.subject_code}</span>
                  </div>
                ))
              )}

              {mode === 'k12' && k12Tab === 'areas' && (
                areas.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg">No instruction units map found.</p> :
                areas.map(a => (
                  <div key={a.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-200">{a.title}</span>
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-slate-400 font-mono text-[10px] rounded">Seq {a.sequence_order}</span>
                  </div>
                ))
              )}

              {mode === 'k12' && k12Tab === 'chapters' && (
                chapters.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg">No content learning modules verified.</p> :
                chapters.map(c => (
                  <div key={c.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-200">{c.title}</span>
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-slate-400 font-mono text-[10px] rounded">Seq {c.sequence_order}</span>
                  </div>
                ))
              )}

              {/* --- COMPETITIVE MONITOR TRACK VIEWS --- */}
              {mode === 'competitive' && compTab === 'exams' && (
                exams.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg">No competitive exam board frameworks discovered.</p> :
                exams.map(ex => (
                  <div key={ex.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center hover:border-slate-700 transition">
                    <span className="text-xs font-bold text-slate-200 tracking-wide">{ex.name}</span>
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-purple-400 font-mono text-[10px] font-bold rounded uppercase tracking-widest">{ex.code}</span>
                  </div>
                ))
              )}

              {mode === 'competitive' && compTab === 'subjects' && (
                displayedExamSubjects.length === 0 ? <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg border border-slate-900">No active subject records bound to this track yet.</p> :
                displayedExamSubjects.map(sub => (
                  <div key={sub.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex flex-col sm:flex-row justify-between sm:items-center gap-2 hover:border-slate-700 transition">
                    <div>
                      <div className="text-xs font-bold text-slate-200 tracking-wide">{sub.name}</div>
                      <div className="text-[10px] font-mono text-slate-500 mt-0.5">Parent Scope ID: <span className="text-slate-400 font-semibold">{sub.exam_id}</span></div>
                    </div>
                    <div className="flex gap-2 items-center self-start sm:self-center">
                      <span className="text-[10px] px-2 py-0.5 bg-slate-950 text-slate-400 border border-slate-800 rounded-full font-bold uppercase tracking-wider">{sub.discipline}</span>
                      <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-purple-400 font-mono text-[10px] font-bold rounded uppercase tracking-widest">{sub.subject_code}</span>
                    </div>
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