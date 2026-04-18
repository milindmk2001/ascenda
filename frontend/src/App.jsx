import React, { useState, useEffect } from 'react';
import UserLearningHub from './UserLearningHub';
import ContentStudio from './ContentStudio'; 
import AdminDashboard from './components/AdminDashboard';
// Assuming you will create this component next for your text-based learning
// import AcademicArchitect from './AcademicArchitect'; 

export const API_BASE = "https://ascenda-production.up.railway.app"; 

function App() {
  const [view, setView] = useState('landing');
  const [subjects, setSubjects] = useState([]);
  const [grades, setGrades] = useState([]);
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  
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
      } catch (e) { console.error("Data fetch error", e); } 
      finally { setLoading(false); }
    };
    fetchData();
  }, []);

  const filteredGrades = grades.filter(g => g.org_id === selectedOrgId);
  const filteredSubjects = subjects.filter(s => s.grade_id === selectedGradeId);

  return (
    <div className="min-h-screen bg-slate-950 text-white selection:bg-indigo-500/30 flex flex-col">
      {view === 'admin' ? (
        <AdminDashboard apiBase={API_BASE} onExit={() => setView('landing')} />
      ) : view === 'studio' ? (
        <ContentStudio apiBase={API_BASE} onBack={() => setView('landing')} />
      ) : view === 'architect' ? (
        /* This is where your new text-based learning builder will go */
        <div className="p-10 text-center">
          <h2 className="text-2xl font-bold mb-4">Academic Architect</h2>
          <p className="text-slate-400 mb-6">Text-based course editor coming soon.</p>
          <button onClick={() => setView('landing')} className="text-indigo-500 underline">Go Back</button>
        </div>
      ) : (
        <>
          <nav className="p-4 border-b border-slate-800 flex justify-between items-center sticky top-0 bg-slate-950/90 backdrop-blur-md z-50">
            <div className="flex items-center gap-6">
              <div className="text-2xl font-black tracking-tighter cursor-pointer" onClick={() => setView('landing')}>
                ASCENDA<span className="text-indigo-500">PRO</span>
              </div>
              
              <div className="flex gap-2">
                {/* Content Studio Link */}
                <button 
                  onClick={() => setView('studio')}
                  className="hidden md:block text-[10px] font-bold uppercase tracking-widest border border-slate-700 px-4 py-2 rounded-lg hover:border-indigo-500 transition-all"
                >
                  🎬 Content Studio
                </button>

                {/* NEW: Academic Architect Link */}
                <button 
                  onClick={() => setView('architect')}
                  className="hidden md:block text-[10px] font-bold uppercase tracking-widest border border-slate-700 px-4 py-2 rounded-lg hover:border-emerald-500 transition-all"
                >
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

          <main className="flex-grow">
            <UserLearningHub 
              subjects={filteredSubjects} 
              loading={loading}
              selectedBoard={organizations.find(o => o.id === selectedOrgId)?.name}
              selectedGrade={grades.find(g => g.id === selectedGradeId)?.name}
            />
          </main>

          {/* NEW: Admin Link Footer */}
          <footer className="p-8 border-t border-slate-900 text-center">
            <button 
              onClick={() => setView('admin')}
              className="text-[9px] uppercase tracking-[0.4em] text-slate-600 hover:text-slate-400 transition-colors"
            >
              Systems Management
            </button>
          </footer>
        </>
      )}
    </div>
  );
}

export default App;