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
  
  const [selectedOrgId, setSelectedOrgId] = useState("");
  const [selectedGradeId, setSelectedGradeId] = useState("");

  // Global Sync Hooks
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setErrorMsg(null);
        
        const [orgRes, gradeRes, subRes] = await Promise.all([
          fetch(`${API_BASE}/api/admin/organizations/`),
          fetch(`${API_BASE}/api/admin/curriculum/grades`),
          fetch(`${API_BASE}/api/admin/curriculum/regular/subjects`)
        ]);
        
        // Defensive validation text-checking to prevent "Unauthorized" crashes
        if (!orgRes.ok) throw new Error(`Organizations API returned status ${orgRes.status}`);
        if (!gradeRes.ok) throw new Error(`Grades API returned status ${gradeRes.status}`);
        if (!subRes.ok) throw new Error(`Subjects API returned status ${subRes.status}`);

        const orgData = await orgRes.json();
        const gradeData = await gradeRes.json();
        const subData = await subRes.json();

        const safeOrgs = Array.isArray(orgData) ? orgData : [];
        const safeGrades = Array.isArray(gradeData) ? gradeData : [];
        const safeSubs = Array.isArray(subData) ? subData : [];

        setOrganizations(safeOrgs);
        setGrades(safeGrades);
        setSubjects(safeSubs);

        // Auto-select defaults cleanly using local variable space to bypass state lag
        if (safeOrgs.length > 0) {
          setSelectedOrgId(safeOrgs[0].id);
          
          // Match matching grades for this specific organization immediately
          const matchingGrades = safeGrades.filter(g => String(g.org_id) === String(safeOrgs[0].id));
          if (matchingGrades.length > 0) {
            setSelectedGradeId(matchingGrades[0].id);
          }
        }

      } catch (err) {
        console.error("Error running application startup layout sync:", err);
        setErrorMsg(err.message || "Failed to connect to backend context channels.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [view]); 

  // Side-effect to keep grades and selected subject matrix in sync during manual dropdown mutations
  useEffect(() => {
    if (selectedOrgId && grades.length > 0) {
      const filtered = grades.filter(g => String(g.org_id) === String(selectedOrgId));
      if (filtered.length > 0) {
        // Only override if the current selection is no longer a part of the active organization
        const stillValid = filtered.some(g => String(g.id) === String(selectedGradeId));
        if (!stillValid) {
          setSelectedGradeId(filtered[0].id);
        }
      } else {
        setSelectedGradeId("");
      }
    }
  }, [selectedOrgId, grades]);

  // Dynamic Filtering Logic with structural safeguards
  const filteredGrades = (grades || []).filter(g => String(g.org_id) === String(selectedOrgId));
  const filteredSubjects = (subjects || []).filter(sub => String(sub.grade_id) === String(selectedGradeId));
  const displayedSubjects = filteredSubjects.length > 0 ? filteredSubjects : (subjects || []);

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col font-sans">
      {/* Dynamic Navigation Header */}
      {view !== 'reader' && (
        <nav className="p-4 bg-slate-900/60 backdrop-blur border-b border-slate-800 flex flex-wrap justify-between items-center gap-4 z-50 sticky top-0">
          <div 
            onClick={() => setView('landing')} 
            className="text-xl font-black tracking-tighter text-white cursor-pointer select-none"
          >
            ASCENDA<span className="text-indigo-500">PRO</span>
          </div>

          <div className="flex items-center gap-3">
            <button 
              onClick={() => setView('landing')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${view === 'landing' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
            >
              Hub View
            </button>
            <button 
              onClick={() => setView('architect')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${view === 'architect' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
            >
              Academic Architect
            </button>
            <button 
              onClick={() => setView('studio')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${view === 'studio' ? 'bg-purple-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
            >
              Content Studio
            </button>
            <button 
              onClick={() => setView('admin')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${view === 'admin' ? 'bg-amber-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
            >
              Admin Dashboard
            </button>
          </div>

          {/* Filtering Dropdowns */}
          <div className="flex gap-2">
            <select 
              className="bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs outline-none text-white cursor-pointer" 
              value={selectedOrgId} 
              onChange={(e) => setSelectedOrgId(e.target.value)}
            >
              {organizations.map(org => <option key={org.id} value={org.id}>{org.name}</option>)}
            </select>
            <select 
              className="bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs outline-none text-white cursor-pointer" 
              value={selectedGradeId} 
              onChange={(e) => setSelectedGradeId(e.target.value)}
            >
              {filteredGrades.map(g => (
                <option key={g.id} value={g.id}>
                  {g.name || `Grade ${g.level}`}
                </option>
              ))}
              {filteredGrades.length === 0 && <option value="">No grades found</option>}
            </select>
          </div>
        </nav>
      )}

      {/* Global Error Notice Banner */}
      {errorMsg && (
        <div className="bg-red-950/80 border-b border-red-800 text-red-200 px-6 py-2 text-xs flex justify-between items-center">
          <span><strong>System Engine Notice:</strong> {errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-red-400 hover:text-white font-bold">&times;</button>
        </div>
      )}

      {/* Main Core View Engine Routing */}
      <main className="flex-grow flex flex-col">
        {view === 'admin' ? (
          <AdminDashboard apiBase={API_BASE} onExit={() => setView('landing')} />
        ) : view === 'studio' ? (
          <ContentStudio apiBase={API_BASE} onBack={() => setView('landing')} />
        ) : view === 'reader' ? (
          <CourseReader 
            subject={activeSubject} 
            onBack={() => setView('architect')} 
          />
        ) : view === 'architect' ? (
          <AcademicArchitect 
            subjects={displayedSubjects} 
            loading={loading} 
            selectedBoard={organizations.find(o => String(o.id) === String(selectedOrgId))?.name || "Select Board"}
            selectedGrade={grades.find(g => String(g.id) === String(selectedGradeId))?.name || ""}
            onCourseSelect={(sub) => {
              setActiveSubject(sub);
              setView('reader');
            }}
            onBack={() => setView('landing')} 
          />
        ) : (
          <UserLearningHub 
            subjects={displayedSubjects} 
            loading={loading} 
            onCourseSelect={(sub) => {
              setActiveSubject(sub);
              setView('reader');
            }}
            onExploreArchitect={() => setView('architect')}
          />
        )}
      </main>
    </div>
  );
}

export default App;