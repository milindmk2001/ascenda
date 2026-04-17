import React, { useState, useEffect } from 'react';
import UserLearningHub from './UserLearningHub';
import AdminDashboard from './components/AdminDashboard';

export const API_BASE = "https://ascenda-production.up.railway.app"; 

function App() {
  const [view, setView] = useState('landing');
  const [subjects, setSubjects] = useState([]);
  const [grades, setGrades] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Filter States
  const [selectedGradeId, setSelectedGradeId] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch both grades and subjects
        const [subRes, gradeRes] = await Promise.all([
          fetch(`${API_BASE}/api/admin/curriculum/regular/subjects`),
          fetch(`${API_BASE}/api/admin/curriculum/grades`)
        ]);
        
        const subData = await subRes.json();
        const gradeData = await gradeRes.json();
        
        setSubjects(subData);
        setGrades(gradeData);
        
        // Default to first grade if available
        if (gradeData.length > 0) setSelectedGradeId(gradeData[0].id);
        
      } catch (error) {
        console.error("❌ Fetch error:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const openAdmin = () => setView('admin');
  const goBackHome = () => setView('landing');

  // Filter subjects based on the dropdown selection
  const filteredSubjects = subjects.filter(s => s.grade_id === selectedGradeId);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {view === 'admin' ? (
        <AdminDashboard apiBase={API_BASE} onExit={goBackHome} />
      ) : (
        <>
          {/* Navigation with WORKING Filters */}
          <nav className="p-4 border-b border-slate-800 flex justify-between items-center sticky top-0 bg-slate-950/80 backdrop-blur-md z-50">
            <div className="text-2xl font-black tracking-tighter">
              ASCENDA<span className="text-indigo-500">PRO</span>
            </div>
            <div className="flex gap-4 items-center">
              <select 
                className="bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-sm"
                value={selectedGradeId}
                onChange={(e) => setSelectedGradeId(e.target.value)}
              >
                {grades.map(g => (
                  <option key={g.id} value={g.id}>{g.name || `Grade ${g.level}`}</option>
                ))}
              </select>
            </div>
          </nav>

          <UserLearningHub 
            subjects={filteredSubjects} 
            loading={loading} 
          />
          
          <footer className="py-10 text-center opacity-20">
            <button onClick={openAdmin} className="text-[10px] uppercase tracking-widest">Admin</button>
          </footer>
        </>
      )}
    </div>
  );
}

export default App;