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
  const [organizations, setOrganizations] = useState([]);
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

  // Boot Layout Component Sync: Fetch metadata containers
  useEffect(() => {
    const fetchMetadataLayer = async () => {
      try {
        setErrorMsg(null);
        const [orgRes, gradeRes] = await Promise.all([
          fetch(`${API_BASE}/api/admin/organizations/`),
          fetch(`${API_BASE}/api/admin/curriculum/grades`)
        ]);
        
        if (orgRes.ok && gradeRes.ok) {
          const orgs = await orgRes.json();
          const grds = await gradeRes.json();
          setOrganizations(orgs);
          setGrades(grds);
          
          // Auto-select the first grade dynamically if available to avoid unaligned states
          if (grds.length > 0) {
            setSelectedGradeName(grds[0].name);
          }
        }
      } catch (err) {
        console.error("Metadata initialization failed:", err);
      }
    };
    fetchMetadataLayer();
  }, []);

  // Content Resolver Hook: Triggers when selectors change
  useEffect(() => {
    const resolveActiveCurriculum = async () => {
      try {
        setLoading(true);
        setErrorMsg(null);

        // Build parameters dynamically depending on track context
        const queryParams = isCompetitiveTrack
          ? `track_code=${selectedTrackCode}`
          : `track_code=${selectedTrackCode}&grade_name=${selectedGradeName}`;

        const res = await fetch(`${API_BASE}/api/curriculum/resolve-hub?${queryParams}`);
        
        if (!res.ok) {
          throw new Error(`Data resolve engine responded with status code: ${res.status}`);
        }

        const resolvedSubjects = await res.json();
        setSubjects(resolvedSubjects);
      } catch (err) {
        console.error("Curriculum engine resolution failure:", err);
        setErrorMsg(err.message);
      } finally {
        setLoading(false);
      }
    };

    resolveActiveCurriculum();
  }, [selectedTrackCode, selectedGradeName, isCompetitiveTrack]);

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col font-sans">
      {/* Dynamic Header Component Block */}
      <nav className="p-4 border-b border-slate-900 flex justify-between items-center sticky top-0 bg-slate-950/80 backdrop-blur-md z-50">
        <div 
          onClick={() => setView('landing')} 
          className="text-2xl font-black tracking-tighter cursor-pointer select-none"
        >
          ASCENDA<span className="text-emerald-500">PRO</span>
        </div>
        
        <div className="flex gap-4 items-center">
          {/* Main Core Tracking Dropdown */}
          <select 
            value={selectedTrackCode}
            onChange={(e) => setSelectedTrackCode(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-sm font-bold text-slate-200 outline-none focus:border-emerald-500 cursor-pointer"
          >
            <option value="CBSE">CBSE</option>
            <option value="ICSE">ICSE</option>
            <option value="IIT-JEE">IIT-JEE</option>
            <option value="NEET">NEET</option>
          </select>

          {/* Grade Selector Dropdown: Dynamically maps database values */}
          <select 
            value={isCompetitiveTrack ? "ALL" : selectedGradeName}
            onChange={(e) => setSelectedGradeName(e.target.value)}
            disabled={isCompetitiveTrack}
            className={`bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-sm font-bold text-slate-200 outline-none focus:border-emerald-500 transition-all ${
              isCompetitiveTrack 
                ? "opacity-30 cursor-not-allowed border-dashed text-slate-500 bg-slate-950" 
                : "opacity-100 cursor-pointer"
            }`}
          >
            {isCompetitiveTrack ? (
              <option value="ALL">Global Track</option>
            ) : (
              <>
                {grades.map((grade) => (
                  <option key={grade.id} value={grade.name}>
                    Class {grade.name}
                  </option>
                ))}
              </>
            )}
          </select>

          {/* Router Action Links */}
          <button 
            onClick={() => setView(view === 'admin' ? 'landing' : 'admin')}
            className="text-xs font-semibold px-3 py-1.5 rounded-md border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-white"
          >
            {view === 'admin' ? 'Exit Console' : 'Admin Panel'}
          </button>
        </div>
      </nav>

      {/* Global Framework Status Banners */}
      {errorMsg && (
        <div className="bg-red-950/40 border-b border-red-900 text-red-400 text-xs px-4 py-2 flex justify-between items-center font-mono">
          <span>System Synchronization Error: {errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-white font-bold">&times;</button>
        </div>
      )}

      {/* Main Core View Engine Routing Layout */}
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
              setActiveSubject(sub);
              setView('reader');
            }}
          />
        )}
      </main>
    </div>
  );
}

export default App;