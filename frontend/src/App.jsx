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
  
  // State for the W3Schools-style reader
  const [activeSubject, setActiveSubject] = useState(null);
  
  const [selectedOrgId, setSelectedOrgId] = useState("");
  const [selectedGradeId, setSelectedGradeId] = useState("");

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
        
        if (orgData.length > 0) setSelectedOrgId(orgData[0].id);
      } catch (e) { 
        console.error("Data fetch error", e); 
      } finally { 
        setLoading(false); 
      }
    };
    fetchData();
  }, []);

  const filteredGrades = grades.filter(g => g.org_id === selectedOrgId);
  const filteredSubjects = subjects.filter(s => s.grade_id === selectedGradeId);

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      {/* Global Nav hidden in Reader for maximum focus */}
      {view !== 'admin' && view !== 'reader' && (
        <nav className="p-4 border-b border-slate-800 flex justify-between items-center sticky top-0 bg-slate-950/90 backdrop-blur-md z-50">
          <div className="flex items-center gap-6">
            <div className="text-2xl font-black tracking-tighter cursor-pointer" onClick={() => setView('landing')}>
              ASCENDA<span className="text-indigo-500">PRO</span>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setView('studio')} className="hidden md:block text-[10px] font-bold uppercase tracking-widest border border-slate-700 px-4 py-2 rounded-lg hover:border-indigo-500 transition-all">
                🎬 Content Studio
              </button>
              <button onClick={() => setView('architect')} className={`hidden md:block text-[10px] font-bold uppercase tracking-widest border px-4 py-2 rounded-lg transition-all ${view === 'architect' ? 'border-emerald-500 bg-emerald-500/10' : 'border-slate-700 hover:border-emerald-500'}`}>
                ✍️ Academic Architect
              </button>
            </div>
          </div>
          
          <div className="flex gap-4 items-center">
            <select className="bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs outline-none" value={selectedOrgId} onChange={(e) => setSelectedOrgId(e.target.value)}>
              {organizations.map(org => <option key={org.id} value={org.id}>{org.name}</option>)}
            </select>
            <select className="bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs outline-none" value={selectedGradeId} onChange={(e) => setSelectedGradeId(e.target.value)}>
              {filteredGrades.map(g => <option key={g.id} value={g.id}>{g.name || `Grade ${g.level}`}</option>)}
            </select>
          </div>
        </nav>
      )}

      <main className="flex-grow">
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
            subjects={filteredSubjects} 
            loading={loading} 
            onCourseSelect={(sub) => {
              setActiveSubject(sub);
              setView('reader');
            }}
            onBack={() => setView('landing')} 
          />
        ) : (
          <UserLearningHub 
            subjects={filteredSubjects} 
            loading={loading}
          />
        )}
      </main>
    </div>
  );
}

export default App;