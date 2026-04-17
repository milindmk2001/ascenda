import React, { useState, useEffect } from 'react';
import UserLearningHub from './UserLearningHub';
import AdminDashboard from './components/AdminDashboard';

export const API_BASE = "https://ascenda-production.up.railway.app"; 

function App() {
  const [view, setView] = useState('landing');
  const [subjects, setSubjects] = useState([]);
  const [grades, setGrades] = useState([]);
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Selection States
  const [selectedOrgId, setSelectedOrgId] = useState("");
  const [selectedGradeId, setSelectedGradeId] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch All Data: Organizations, Grades, and Subjects
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
        
        // Set initial defaults
        if (orgData.length > 0) setSelectedOrgId(orgData[0].id);
        if (gradeData.length > 0) setSelectedGradeId(gradeData[0].id);
        
      } catch (error) {
        console.error("❌ Connection Error:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const openAdmin = () => setView('admin');
  const goBackHome = () => setView('landing');

  // Logic: Filter grades by selected Board, then subjects by selected Grade
  const filteredGrades = grades.filter(g => g.org_id === selectedOrgId);
  const filteredSubjects = subjects.filter(s => s.grade_id === selectedGradeId);

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans">
      {view === 'admin' ? (
        <AdminDashboard apiBase={API_BASE} onExit={goBackHome} />
      ) : (
        <>
          {/* Navigation with CLEAR LABELS and FILTERS */}
          <nav className="p-4 border-b border-slate-800 flex flex-wrap justify-between items-center sticky top-0 bg-slate-950/90 backdrop-blur-md z-50 gap-4">
            <div className="text-2xl font-black tracking-tighter">
              ASCENDA<span className="text-indigo-500">PRO</span>
            </div>
            
            <div className="flex gap-6 items-center">
              {/* Board Selection */}
              <div className="flex flex-col">
                <label className="text-[10px] uppercase text-slate-500 font-bold mb-1">Select Board</label>
                <select 
                  className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500 transition-colors"
                  value={selectedOrgId}
                  onChange={(e) => setSelectedOrgId(e.target.value)}
                >
                  {organizations.map(org => (
                    <option key={org.id} value={org.id}>{org.name}</option>
                  ))}
                </select>
              </div>

              {/* Grade Selection */}
              <div className="flex flex-col">
                <label className="text-[10px] uppercase text-slate-500 font-bold mb-1">Select Grade</label>
                <select 
                  className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500 transition-colors"
                  value={selectedGradeId}
                  onChange={(e) => setSelectedGradeId(e.target.value)}
                >
                  {filteredGrades.length > 0 ? (
                    filteredGrades.map(g => (
                      <option key={g.id} value={g.id}>{g.name || `Grade ${g.level}`}</option>
                    ))
                  ) : (
                    <option value="">No Grades Found</option>
                  )}
                </select>
              </div>
            </div>
          </nav>

          {/* Main Hub */}
          <UserLearningHub 
            subjects={filteredSubjects} 
            loading={loading} 
          />
          
          <footer className="py-10 text-center border-t border-slate-900 mt-20">
            <button onClick={openAdmin} className="text-slate-800 hover:text-indigo-500 text-[10px] uppercase tracking-[0.3em] transition-all">
              Systems Management
            </button>
          </footer>
        </>
      )}
    </div>
  );
}

export default App;