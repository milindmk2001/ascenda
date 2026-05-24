import React, { useState, useEffect } from 'react';
import UserLearningHub from './UserLearningHub';
import ContentStudio from './ContentStudio'; 
import AdminDashboard from './components/AdminDashboard';
import AcademicArchitect from './AcademicArchitect'; 
import CourseReader from './CourseReader'; 

export const API_BASE = "https://ascenda-production.up.railway.app"; 

function App() {
  const [view, setView] = useState('landing');
  const [subjects, setSubjects] = useState([]);
  const [grades, setGrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);
  
  const [activeSubject, setActiveSubject] = useState(null);
  
  // Selection matrices tracking states
  const [selectedTrackCode, setSelectedTrackCode] = useState("CBSE");
  const [selectedGradeName, setSelectedGradeName] = useState("11");

  // Determine if competitive track rules override K-12 grading mechanics
  const isCompetitiveTrack = 
    selectedTrackCode === "IIT-JEE" || 
    selectedTrackCode === "NEET" || 
    selectedTrackCode === "IITJEE";

  // Fetch active grade structural attributes for dashboard filter configurations
  useEffect(() => {
    const fetchMetadataLayer = async () => {
      try {
        setErrorMsg(null);
        const gradeRes = await fetch(`${API_BASE}/api/admin/curriculum/grades`);

        if (gradeRes.ok) {
          const gradeData = await gradeRes.json();
          setGrades(gradeData);
        } else {
          console.warn("Grades verification system returned an unexpected non-200 state code.");
        }
      } catch (err) {
        console.error("Meta system parameters connection dropped:", err);
      }
    };
    fetchMetadataLayer();
  }, []);

  // System Sync Engine: Live monitors runtime states to load course cards dynamically
 useEffect(() => {
    const resolveActiveCurriculum = async () => {
      try {
        setLoading(true);
        setErrorMsg(null);

        let trackQueryParam = selectedTrackCode;
        if (selectedTrackCode === "IIT-JEE") trackQueryParam = "IITJEE";

        let endpoint = `${API_BASE}/api/curriculum/resolve-hub?track_code=${trackQueryParam}`;
        if (!isCompetitiveTrack && selectedGradeName) {
          endpoint += `&grade_name=${selectedGradeName}`;
        }

        const res = await fetch(endpoint);
        if (!res.ok) {
          throw new Error(`Failed to resolve active course components from the server.`);
        }
        const activeSubjects = await res.json();
        setSubjects(activeSubjects);
      } catch (err) {
        console.error("Error patching track mapping components:", err);
        setSubjects([]);
        setErrorMsg(err.message);
      } finally {
        setLoading(false);
      }
    };

    resolveActiveCurriculum();
  }, [selectedTrackCode, selectedGradeName, isCompetitiveTrack]);

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-300 flex flex-col font-sans selection:bg-emerald-500/20 selection:text-emerald-400 antialiased">
      
      {/* Top Header Application Dock Bar Layout */}
      <nav className="border-b border-slate-900 bg-[#090f1c]/80 backdrop-blur-md px-8 py-4 sticky top-0 z-50 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setView('landing')}>
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center text-white font-black shadow-lg shadow-emerald-500/10 tracking-tighter">
            A
          </div>
          <span className="text-white font-black uppercase text-sm tracking-widest font-mono">
            Ascenda<span className="text-emerald-400 text-xs">.Pro</span>
          </span>
        </div>

        {/* Realtime Grid Control Workspace Dropdown Filters */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-[#0d1527] border border-slate-900 rounded-xl px-3 py-1.5 shadow-inner">
            <span className="text-[10px] font-mono font-bold tracking-wider text-slate-500 uppercase">Track</span>
            <select
              value={selectedTrackCode}
              onChange={(e) => setSelectedTrackCode(e.target.value)}
              className="bg-transparent text-xs font-bold text-slate-200 outline-none cursor-pointer focus:text-white select-none"
            >
              <option value="CBSE" className="bg-[#0d1527]">CBSE Board</option>
              <option value="IIT-JEE" className="bg-[#0d1527]">IIT-JEE Advance</option>
              <option value="NEET" className="bg-[#0d1527]">NEET Medical</option>
            </select>
          </div>

          <div className={`flex items-center gap-2 bg-[#0d1527] border border-slate-900 rounded-xl px-3 py-1.5 transition-opacity duration-200 ${isCompetitiveTrack ? 'opacity-25 pointer-events-none' : 'opacity-100'}`}>
            <span className="text-[10px] font-mono font-bold tracking-wider text-slate-500 uppercase">Grade</span>
            <select
              value={selectedGradeName}
              disabled={isCompetitiveTrack}
              onChange={(e) => setSelectedGradeName(e.target.value)}
              className="bg-transparent text-xs font-bold text-slate-200 outline-none cursor-pointer focus:text-white select-none"
            >
              <option value="11" className="bg-[#0d1527]">Class 11</option>
              <option value="12" className="bg-[#0d1527]">Class 12</option>
            </select>
          </div>

          <div className="h-4 w-[1px] bg-slate-800 mx-2" />

          <button 
            onClick={() => setView(view === 'studio' ? 'landing' : 'studio')}
            className="text-xs font-bold font-mono px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 hover:text-white transition-all text-slate-400"
          >
            {view === 'studio' ? 'Exit Studio' : 'Content Studio'}
          </button>
          
          <button 
            onClick={() => setView(view === 'admin' ? 'landing' : 'admin')}
            className="text-xs font-bold font-mono px-4 py-2 bg-gradient-to-r from-slate-900 to-slate-950 text-slate-400 border border-slate-800/80 rounded-xl hover:text-white"
          >
            {view === 'admin' ? 'Exit Console' : 'Admin Panel'}
          </button>
        </div>
      </nav>

      {/* Global Sync Error Messaging Alert Box Banner */}
      {errorMsg && (
        <div className="bg-red-950/40 border-b border-red-900/50 text-red-400 text-xs px-8 py-2 flex justify-between items-center font-mono">
          <span>System Synchronization Error Layer: {errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-white font-bold">&times;</button>
        </div>
      )}

      {/* Canvas Router Wrapper Context Frame Viewport */}
      <main className="flex-grow flex flex-col">
        {view === 'admin' ? (
          <AdminDashboard apiBase={API_BASE} onExit={() => setView('landing')} />
        ) : view === 'studio' ? (
          <ContentStudio apiBase={API_BASE} onBack={() => setView('landing')} />
        ) : view === 'reader' ? (
          <CourseReader 
            subject={activeSubject} 
            onBack={() => setView('landing')} 
          />
        ) : (
          <UserLearningHub 
            subjects={subjects} 
            loading={loading} 
            trackName={selectedTrackCode}
            gradeName={isCompetitiveTrack ? "Global" : `Class ${selectedGradeName}`}
            onCourseSelect={(sub) => {
              // Strip structural data table prefixes dynamically (e.g., 'cbse_physics' -> 'physics')
              let cleanSubjectCode = sub.subject_code.toLowerCase();
              if (cleanSubjectCode.includes('_')) {
                cleanSubjectCode = cleanSubjectCode.split('_')[1];
              }

              let cleanExamToken = selectedTrackCode.toLowerCase().replace("-", "");

              setActiveSubject({
                ...sub,
                subject_code: cleanSubjectCode,
                meta_tag: `${cleanExamToken}-${selectedGradeName}`
              });
              
              setView('reader');
            }}
          />
        )}
      </main>
    </div>
  );
}

export default App;