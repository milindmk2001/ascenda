import React, { useState, useEffect } from 'react';

interface ExamSubject {
  id: string;
  exam_id: string;
  name: string;
  subject_code: string;
  discipline: string;
  video_url?: string;
  exam?: {
    id: string;
    name: string;
    code: string;
  };
}

interface Exam {
  id: string;
  name: string;
  code: string;
}

interface AdminDashboardProps {
  apiBase: string;
  onExit: () => void;
}

export default function AdminDashboard({ apiBase, onExit }: AdminDashboardProps) {
  const [activeTab, setActiveTab] = useState<'exams' | 'subjects'>('exams');
  const [exams, setExams] = useState<Exam[]>([]);
  const [examSubjects, setExamSubjects] = useState<ExamSubject[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form Fields
  const [examName, setExamName] = useState('');
  const [examCode, setExamCode] = useState('');
  const [selectedExamId, setSelectedExamId] = useState('');
  const [subjectName, setSubjectName] = useState('');
  const [subjectCode, setSubjectCode] = useState('');
  const [discipline, setDiscipline] = useState('Competitive Exam');

  // Load configuration options cleanly
  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      if (activeTab === 'exams') {
        const res = await fetch(`${apiBase}/api/admin/curriculum/exams`);
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`Server returned ${res.status}: ${text}`);
        }
        const data = await res.json();
        setExams(Array.isArray(data) ? data : []);
      } else {
        const res = await fetch(`${apiBase}/api/admin/curriculum/exam/subjects`);
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`Server returned ${res.status}: ${text}`);
        }
        const data = await res.json();
        setExamSubjects(Array.isArray(data) ? data : []);

        // Populate selection dropdown and set initial default selection configuration binding
        const examRes = await fetch(`${apiBase}/api/admin/curriculum/exams`);
        if (examRes.ok) {
          const examData = await examRes.json();
          const safeExams = Array.isArray(examData) ? examData : [];
          setExams(safeExams);
          if (safeExams.length > 0 && !selectedExamId) {
            setSelectedExamId(safeExams[0].id);
          }
        }
      }
    } catch (err: any) {
      console.error("Administrative Ingestion Engine Fetch Failure:", err);
      setErrorMsg(err.message || "An error occurred while loading content.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!examName || !examCode) return;
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/exams`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: examName, code: examCode })
      });
      if (!res.ok) throw new Error("Could not construct standard exam model framework reference.");
      setExamName('');
      setExamCode('');
      fetchData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleCreateExamSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedExamId || !subjectName || !subjectCode) {
      alert("Please ensure a core target exam track track association link is specified.");
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
      if (!res.ok) throw new Error("Failed to register structural subject profile context mapping object.");
      setSubjectName('');
      setSubjectCode('');
      fetchData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="flex-grow p-6 bg-slate-900 text-white flex flex-col font-sans">
      <header className="flex justify-between items-center border-b border-slate-700 pb-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-emerald-400">Ascenda Curriculum Content Studio</h1>
          <p className="text-sm text-slate-400">Administrative Target Mapping & Strategy Ingestion Portal</p>
        </div>
        <button 
          onClick={onExit}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 rounded transition"
        >
          Exit Dashboard
        </button>
      </header>

      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveTab('exams')}
          className={`px-4 py-2 font-medium rounded transition ${activeTab === 'exams' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
        >
          Competitive Exams
        </button>
        <button
          onClick={() => setActiveTab('subjects')}
          className={`px-4 py-2 font-medium rounded transition ${activeTab === 'subjects' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
        >
          Exam Content Subjects
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 mb-6 bg-red-900/40 border border-red-700 text-red-200 rounded text-sm">
          <strong>Initialization Notice:</strong> {errorMsg}
        </div>
      )}

      {loading ? (
        <div className="flex-grow flex items-center justify-center text-slate-400 text-sm tracking-widest animate-pulse">
          SYNCHRONIZING CURRICULUM ASSETS ENGINE...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-grow items-start">
          
          {/* Action Formulation Panel Form entries */}
          <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 shadow-xl">
            <h2 className="text-lg font-semibold mb-4 text-slate-200">
              {activeTab === 'exams' ? 'Register Competitive Core Track' : 'Append Subject Matrix Area'}
            </h2>
            
            {activeTab === 'exams' ? (
              <form onSubmit={handleCreateExam} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Exam Track Name</label>
                  <input type="text" value={examName} onChange={e => setExamName(e.target.value)} placeholder="e.g., IIT JEE Advanced" className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-emerald-500" />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Unique Identifier Code</label>
                  <input type="text" value={examCode} onChange={e => setExamCode(e.target.value)} placeholder="e.g., IITJEE" className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-emerald-500" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-medium rounded text-white transition shadow-lg shadow-emerald-900/20">Commit Entry Asset</button>
              </form>
            ) : (
              <form onSubmit={handleCreateExamSubject} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Target Assessment Track</label>
                  <select value={selectedExamId} onChange={e => setSelectedExamId(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-emerald-500">
                    <option value="">-- Connect Core Target Track --</option>
                    {exams.map(ex => <option key={ex.id} value={ex.id}>{ex.name} ({ex.code})</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Subject Nomenclature Title</label>
                  <input type="text" value={subjectName} onChange={e => setSubjectName(e.target.value)} placeholder="e.g., Advanced Physical Chemistry" className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-emerald-500" />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Subject Tracking Code</label>
                  <input type="text" value={subjectCode} onChange={e => setSubjectCode(e.target.value)} placeholder="e.g., JEE_CHEM" className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-emerald-500" />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Discipline Segment Category</label>
                  <input type="text" value={discipline} onChange={e => setDiscipline(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-emerald-500" />
                </div>
                <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 font-medium rounded text-white transition shadow-lg shadow-emerald-900/20">Commit Subject Asset</button>
              </form>
            )}
          </div>

          {/* Active Structural Assets Real-Time Verification Tables */}
          <div className="lg:col-span-2 bg-slate-800 p-5 rounded-lg border border-slate-700 shadow-xl self-stretch overflow-y-auto max-h-[70vh]">
            <h2 className="text-lg font-semibold mb-4 text-slate-200">Active Live Ingestions Monitor</h2>
            {activeTab === 'exams' ? (
              <div className="space-y-2">
                {exams.length === 0 ? (
                  <p className="text-slate-500 text-sm italic">No core exam tracks discovered in operational context data store links.</p>
                ) : (
                  exams.map(ex => (
                    <div key={ex.id} className="p-3 bg-slate-900 border border-slate-700 rounded flex justify-between items-center hover:border-slate-500 transition">
                      <span className="font-medium text-slate-100">{ex.name}</span>
                      <span className="px-2 py-0.5 bg-slate-800 border border-slate-600 text-emerald-400 font-mono text-xs rounded uppercase tracking-wider">{ex.code}</span>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div className="space-y-2">
                {examSubjects.length === 0 ? (
                  <p className="text-slate-500 text-sm italic">No active specialized test matrix modules discovered.</p>
                ) : (
                  examSubjects.map(sub => (
                    <div key={sub.id} className="p-3 bg-slate-900 border border-slate-700 rounded flex flex-col sm:flex-row justify-between sm:items-center gap-2 hover:border-slate-500 transition">
                      <div>
                        <div className="font-medium text-slate-100">{sub.name}</div>
                        <div className="text-xs text-slate-400 mt-0.5">Parent Association: <span className="text-slate-300 font-semibold">{sub.exam?.name || "Global / Base Track Pool"}</span></div>
                      </div>
                      <div className="flex gap-2 items-center self-start sm:self-center">
                        <span className="text-xs px-2 py-0.5 bg-emerald-950/50 text-emerald-400 border border-emerald-800/40 rounded-full font-medium">{sub.discipline}</span>
                        <span className="px-2 py-0.5 bg-slate-800 border border-slate-600 text-slate-300 font-mono text-xs rounded uppercase tracking-wider">{sub.subject_code}</span>
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