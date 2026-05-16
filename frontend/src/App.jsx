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
  
  const [activeSubject, setActiveSubject] = useState(null);
  
  const [selectedOrgId, setSelectedOrgId] = useState("");
  const [selectedGradeId, setSelectedGradeId] = useState("");

  // Global Sync Hooks
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [orgRes, gradeRes, subRes] = await Promise.all([
          fetch(`${API_BASE}/api/admin/organizations/`),
          fetch(`${API_BASE}/api/admin/curriculum/grades`),
          fetch(`${API_BASE}/api/admin/curriculum/regular/subjects`)
        ]);
        
        const orgData = await orgRes.json();
        const gradeData = await gradeRes.json();
        const subData = await subRes.json();

        setOrganizations(orgData);
        setGrades(gradeData);
        setSubjects(subData);

        // Auto-select defaults to prevent blank states
        if (orgData.length > 0) setSelectedOrgId(orgData[0].id);
        if (gradeData.length > 0) setSelectedGradeId(gradeData[0].id);

      } catch (err) {
        console.error("Error running application startup layout sync:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [view]); // Triggers auto-refresh whenever switching views (e.g., exiting admin panel)

  // Dynamic Filtering Logic
  const filteredGrades = grades.filter(g => String(g.org_id) === String(selectedOrgId));
  
  // If no grade matches the filter, fallback to showing all subjects to ensure nothing appears blank
  const filteredSubjects = subjects.filter(sub => String(sub.grade_id) === String(selectedGradeId));
  const displayedSubjects = filteredSubjects.length > 0 ? filteredSubjects : subjects;

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
            selectedBoard={organizations.find(o => o.id === selectedOrgId)?.name || "Select Board"}
            selectedGrade={grades.find(g => g.id === selectedGradeId)?.name || ""}
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
          />
        )}
      </main>
    </div>
  );
}

export default App;