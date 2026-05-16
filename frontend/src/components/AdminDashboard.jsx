import React, { useState, useEffect } from 'react';

export default function AdminDashboard({ apiBase, onExit }) {
  const [activeTab, setActiveTab] = useState('exams');
  const [exams, setExams] = useState([]);
  const [examSubjects, setExamSubjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Form Fields
  const [examName, setExamName] = useState('');
  const [examCode, setExamCode] = useState('');
  const [selectedExamId, setSelectedExamId] = useState('');
  const [subjectName, setSubjectName] = useState('');
  const [subjectCode, setSubjectCode] = useState('');
  const [discipline, setDiscipline] = useState('Competitive Exam');

  // Load context structures safely
  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      if (activeTab === 'exams') {
        const res = await fetch(`${apiBase}/api/admin/curriculum/exams`).catch(() => {
          throw new Error("Unable to establish communication channel to Exams infrastructure service mapping.");
        });
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`Server execution variance (${res.status}): ${text}`);
        }
        const data = await res.json();
        setExams(Array.isArray(data) ? data : []);
      } else {
        const res = await fetch(`${apiBase}/api/admin/curriculum/exam/subjects`).catch(() => {
          throw new Error("Unable to settle connection path with Exam Subjects database partition.");
        });
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`Server execution variance (${res.status}): ${text}`);
        }
        const data = await res.json();
        setExamSubjects(Array.isArray(data) ? data : []);

        // Also refresh selection keys dropdown cleanly
        const examRes = await fetch(`${apiBase}/api/admin/curriculum/exams`).catch(() => null);
        if (examRes && examRes.ok) {
          const examData = await examRes.json();
          const safeExams = Array.isArray(examData) ? examData : [];
          setExams(safeExams);
          if (safeExams.length > 0 && !selectedExamId) {
            setSelectedExamId(safeExams[0].id);
          }
        }
      }
    } catch (err) {
      console.error("Administrative Fetch Core Failure:", err);
      setErrorMsg(err.message || "Failed to cleanly synchronize administrative asset matrix entries.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExam = async (e) => {
    e.preventDefault();
    if (!examName || !examCode) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/exams`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: examName, code: examCode })
      });
      if (!res.ok) throw new Error("Could not register unique core target assessment system profile model tracking data.");
      setExamName('');
      setExamCode('');
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleCreateExamSubject = async (e) => {
    e.preventDefault();
    if (!selectedExamId || !subjectName || !subjectCode) {
      alert("Please ensure an explicit target testing schema track mapping association parameter is bounded.");
      return;
    }
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/exam/subjects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exam_id: selectedExamId,
          name: subjectName,
          subject_code: subjectCode,
          discipline: discipline,
          video_url: ""
        })
      });
      if (!res.ok) throw new Error("Could not associate custom examination content node onto target data repository structural array.");
      setSubjectName('');
      setSubjectCode('');
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="flex-grow p-6 bg-slate-900 text-white flex flex-col font-sans">
      <header className="flex justify-between items-center border-b border-slate-800 pb-4 mb-6">
        <div>
          <h1 className="text-xl font-black tracking-tight text-emerald-400 uppercase">Ascenda Ingestion Console</h1>
          <p className="text-xs text-slate-400 font-mono">Environment Status Monitor Matrix & Configuration Portal</p>
        </div>
        <button 
          onClick={onExit}
          className="px-4 py-1.5 bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 rounded-lg text-xs font-bold transition"
        >
          Return to Hub Engine
        </button>
      </header>

      <div className="flex gap-2 mb-6 bg-slate-950 p-1 border border-slate-800 rounded-lg max-w-xs">
        <button
          onClick={() => setActiveTab('exams')}
          className={`flex-1 text-center py-1.5 text-xs font-bold rounded-md transition ${activeTab === 'exams' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Assessment Tracks
        </button>
        <button
          onClick={() => setActiveTab('subjects')}
          className={`flex-1 text-center py-1.5 text-xs font-bold rounded-md transition ${activeTab === 'subjects' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Track Subjects
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 mb-6 bg-red-950/50 border border-red-800 text-red-300 rounded-lg text-xs font-mono">
          <strong>Initialization Override Alert:</strong> {errorMsg}
        </div>
      )}

      {loading ? (
        <div className="flex-grow flex items-center justify-center text-slate-500 font-mono text-xs tracking-widest animate-pulse">
          FETCHING CLUSTER CONTEXT ENTRIES DEPLOYMENT CHANNELS...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-grow items-start">
          
          {/* Form Action Management Cards */}
          <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-2xl">
            <h2 className="text-sm font-bold tracking-wide uppercase mb-4 text-slate-300">
              {activeTab === 'exams' ? 'Provision Testing Track' : 'Inject Subject Module Node'}
            </h2>
            
            {activeTab === 'exams' ? (
              <form onSubmit={handleCreateExam} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Track Nomenclature Title</label>
                  <input type="text" value={examName} onChange={e => setExamName(e.target.value)} placeholder="e.g., IIT JEE Advanced" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">System Validation Tracking Code</label>
                  <input type="text" value={examCode} onChange={e => setExamCode(e.target.value)} placeholder="e.g., IITJEE" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-slate-800 hover:bg-slate-700 font-bold rounded-lg text-xs tracking-wide uppercase text-white transition border border-slate-700">Commit Core Track Blueprint</button>
              </form>
            ) : (
              <form onSubmit={handleCreateExamSubject} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Target Blueprint Association</label>
                  <select value={selectedExamId} onChange={e => setSelectedExamId(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-slate-700 cursor-pointer">
                    <option value="">-- Connect Core Target Track --</option>
                    {exams.map(ex => <option key={ex.id} value={ex.id}>{ex.name} ({ex.code})</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Module Content Name</label>
                  <input type="text" value={subjectName} onChange={e => setSubjectName(e.target.value)} placeholder="e.g., Advanced Physical Chemistry" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Operational System Code</label>
                  <input type="text" value={subjectCode} onChange={e => setSubjectCode(e.target.value)} placeholder="e.g., JEE_CHEM" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 font-mono">Discipline Domain Category</label>
                  <input type="text" value={discipline} onChange={e => setDiscipline(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-slate-700" />
                </div>
                <button type="submit" className="w-full py-2 bg-slate-800 hover:bg-slate-700 font-bold rounded-lg text-xs tracking-wide uppercase text-white transition border border-slate-700">Commit Subject Track Blueprint</button>
              </form>
            )}
          </div>

          {/* Operational Verification Display Stream Grid tables */}
          <div className="lg:col-span-2 bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-2xl self-stretch overflow-y-auto max-h-[68vh]">
            <h2 className="text-sm font-bold tracking-wide uppercase mb-4 text-slate-300">Live Active Node Streams</h2>
            {activeTab === 'exams' ? (
              <div className="space-y-2">
                {exams.length === 0 ? (
                  <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg border border-slate-900">No active operational target testing frameworks returned.</p>
                ) : (
                  exams.map(ex => (
                    <div key={ex.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex justify-between items-center hover:border-slate-700 transition">
                      <span className="text-xs font-bold text-slate-200 tracking-wide">{ex.name}</span>
                      <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-emerald-400 font-mono text-[10px] font-bold rounded uppercase tracking-widest">{ex.code}</span>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div className="space-y-2">
                {examSubjects.length === 0 ? (
                  <p className="text-slate-600 text-xs italic font-mono p-4 bg-slate-900 rounded-lg border border-slate-900">No content structure nodes currently bound onto tracking routes.</p>
                ) : (
                  examSubjects.map(sub => (
                    <div key={sub.id} className="p-3 bg-slate-900 border border-slate-800/60 rounded-lg flex flex-col sm:flex-row justify-between sm:items-center gap-2 hover:border-slate-700 transition">
                      <div>
                        <div className="text-xs font-bold text-slate-200 tracking-wide">{sub.name}</div>
                        <div className="text-[10px] font-mono text-slate-500 mt-0.5">Parent Scope: <span className="text-slate-400 font-semibold">{sub.exam?.name || "Global Core Pool Base"}</span></div>
                      </div>
                      <div className="flex gap-2 items-center self-start sm:self-center">
                        <span className="text-[10px] px-2 py-0.5 bg-slate-950 text-slate-400 border border-slate-800 rounded-full font-bold uppercase tracking-wider">{sub.discipline}</span>
                        <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 text-slate-300 font-mono text-[10px] font-bold rounded uppercase tracking-widest">{sub.subject_code}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}