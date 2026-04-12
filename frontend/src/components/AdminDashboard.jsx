import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit, X, RefreshCw, BookOpen, Layers, AlertCircle } from 'lucide-react';

const AdminDashboard = ({ apiBase }) => {
  const [activeTab, setActiveTab] = useState('orgs');
  const [organizations, setOrganizations] = useState([]);
  const [grades, setGrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState('org');
  const [formData, setFormData] = useState({ org_type: 'board', type: 'regular' });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch Organizations
      const orgRes = await fetch(`${apiBase}/api/admin/organizations/`);
      if (orgRes.ok) {
        setOrganizations(await orgRes.json());
      } else {
        console.error("Failed to load organizations");
      }

      // 2. Fetch Grades (Wrapped in try/catch to prevent 500s from breaking UI)
      try {
        const gradeRes = await fetch(`${apiBase}/api/admin/curriculum/grades`);
        if (gradeRes.ok) {
          setGrades(await gradeRes.json());
        } else {
          console.warn("Grades table might be missing the 'level' column in Supabase.");
          setGrades([]);
        }
      } catch (err) {
        setGrades([]);
      }

    } catch (e) {
      setError("Connection to Railway failed. Please check backend logs.");
      console.error("Fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [apiBase]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    let endpoint = `${apiBase}/api/admin/organizations/`;
    if (modalType === 'grade') endpoint = `${apiBase}/api/admin/curriculum/grades`;
    if (modalType === 'subject') {
      const subType = formData.type === 'regular' ? 'regular' : 'exam';
      endpoint = `${apiBase}/api/admin/curriculum/subjects/${subType}`;
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setIsModalOpen(false);
        setFormData({ org_type: 'board', type: 'regular' }); // Reset with defaults
        fetchData();
      } else {
        const errData = await response.json();
        alert(`Error: ${JSON.stringify(errData.detail)}`);
      }
    } catch (err) {
      alert("Failed to send data to server.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-6">
          <div>
            <h1 className="text-4xl font-black tracking-tight mb-2 bg-gradient-to-r from-white to-slate-500 bg-clip-text text-transparent">
              Ascenda Admin
            </h1>
            <p className="text-slate-500 text-sm mb-4 italic">Manage your database architecture from Supabase via Railway</p>
            
            <div className="flex gap-2 p-1 bg-slate-900 rounded-xl border border-slate-800 w-fit">
              <button 
                onClick={() => setActiveTab('orgs')}
                className={`flex items-center gap-2 px-6 py-2 rounded-lg font-bold transition-all ${activeTab === 'orgs' ? 'bg-indigo-600 shadow-lg' : 'text-slate-500 hover:text-white'}`}
              >
                <Layers size={18} /> Organizations
              </button>
              <button 
                onClick={() => setActiveTab('curriculum')}
                className={`flex items-center gap-2 px-6 py-2 rounded-lg font-bold transition-all ${activeTab === 'curriculum' ? 'bg-indigo-600 shadow-lg' : 'text-slate-500 hover:text-white'}`}
              >
                <BookOpen size={18} /> Curriculum
              </button>
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={() => { setModalType(activeTab === 'orgs' ? 'org' : 'grade'); setIsModalOpen(true); }} 
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 px-6 py-3 rounded-xl font-bold transition shadow-indigo-500/20 shadow-xl active:scale-95">
              <Plus size={20} /> Add {activeTab === 'orgs' ? 'Organization' : 'Grade'}
            </button>
            {activeTab === 'curriculum' && (
              <button onClick={() => { setModalType('subject'); setIsModalOpen(true); }} 
                      className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 px-6 py-3 rounded-xl font-bold transition shadow-emerald-500/20 shadow-xl active:scale-95">
                <Plus size={20} /> Add Subject
              </button>
            )}
            <button onClick={fetchData} className="p-3 bg-slate-800 rounded-xl hover:bg-slate-700 transition">
              <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-xl flex items-center gap-3 text-red-400">
            <AlertCircle size={20} /> {error}
          </div>
        )}

        {/* Content Table */}
        {activeTab === 'orgs' ? (
          <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden backdrop-blur-md">
            <table className="w-full text-left">
              <thead className="bg-slate-900 text-slate-500 text-xs font-bold uppercase tracking-widest border-b border-slate-800">
                <tr><th className="p-6">Organization Name</th><th className="p-6">Category</th><th className="p-6 text-right">Control</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {organizations.length > 0 ? organizations.map(org => (
                  <tr key={org.id} className="group hover:bg-white/5 transition-colors">
                    <td className="p-6 font-semibold text-slate-200">{org.name}</td>
                    <td className="p-6">
                      <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter ${org.org_type === 'competitive' ? 'bg-orange-500/20 text-orange-400' : 'bg-indigo-500/20 text-indigo-400'}`}>
                        {org.org_type}
                      </span>
                    </td>
                    <td className="p-6 text-right">
                      <button className="p-2 text-slate-600 hover:text-red-400 transition-colors">
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                )) : (
                  <tr><td colSpan="3" className="p-10 text-center text-slate-600">No organizations found. Click "Add Organization" to begin.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          /* Curriculum View */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-slate-900/50 p-8 rounded-2xl border border-slate-800">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2"><Layers className="text-indigo-400" /> Grade Levels</h3>
              <div className="space-y-3">
                {grades.length > 0 ? grades.map(g => (
                  <div key={g.id} className="p-4 bg-slate-950 rounded-xl border border-slate-800 flex justify-between items-center group hover:border-indigo-500/50 transition-all">
                    <span className="font-bold text-slate-300">{g.level}</span>
                    <Trash2 size={16} className="text-slate-700 group-hover:text-red-400 cursor-pointer" />
                  </div>
                )) : (
                  <div className="text-slate-600 text-sm italic">No grades configured.</div>
                )}
              </div>
            </div>
            <div className="bg-slate-900/50 p-8 rounded-2xl border border-slate-800">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2"><BookOpen className="text-emerald-400" /> Subjects</h3>
              <div className="bg-slate-950/50 p-6 rounded-xl border border-slate-800 border-dashed text-center">
                <p className="text-slate-500 text-sm">Subjects are mapped to grades or exams. Use the "Add Subject" button to populate this list.</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Dynamic Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/90 backdrop-blur-md flex items-center justify-center p-4 z-[200] animate-in fade-in duration-200">
          <div className="bg-slate-900 p-8 rounded-3xl w-full max-w-md border border-slate-800 shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold uppercase tracking-tighter">Add {modalType}</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-500 hover:text-white"><X /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {modalType === 'org' && (
                <>
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Organization Name</label>
                  <input required className="w-full bg-slate-950 p-4 rounded-xl border border-slate-800 focus:border-indigo-500 outline-none transition" 
                         placeholder="e.g. CBSE" onChange={e => setFormData({...formData, name: e.target.value})} />
                  
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Category</label>
                  <select className="w-full bg-slate-950 p-4 rounded-xl border border-slate-800 outline-none" onChange={e => setFormData({...formData, org_type: e.target.value})}>
                    <option value="board">Board</option>
                    <option value="competitive">Competitive</option>
                  </select>
                </>
              )}
              {modalType === 'grade' && (
                <>
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Level Name</label>
                  <input required className="w-full bg-slate-950 p-4 rounded-xl border border-slate-800 focus:border-indigo-500 outline-none transition" 
                         placeholder="e.g. Class 10" onChange={e => setFormData({...formData, level: e.target.value})} />
                </>
              )}
              {modalType === 'subject' && (
                <>
                  <input required className="w-full bg-slate-950 p-4 rounded-xl border border-slate-800" 
                         placeholder="Subject Name (e.g. Physics)" onChange={e => setFormData({...formData, name: e.target.value})} />
                  <input required className="w-full bg-slate-950 p-4 rounded-xl border border-slate-800" 
                         placeholder="Unique Code (e.g. PHY-10)" onChange={e => setFormData({...formData, subject_code: e.target.value})} />
                  
                  <select className="w-full bg-slate-950 p-4 rounded-xl border border-slate-800" onChange={e => setFormData({...formData, type: e.target.value})}>
                    <option value="regular">Regular (Links to Grade)</option>
                    <option value="exam">Exam (Links to Org)</option>
                  </select>
                  
                  <select required className="w-full bg-slate-950 p-4 rounded-xl border border-slate-800" onChange={e => setFormData({
                    ...formData, 
                    [formData.type === 'exam' ? 'organization_id' : 'grade_id']: e.target.value
                  })}>
                    <option value="">Select Parent Container</option>
                    {(formData.type === 'exam' ? organizations : grades).map(item => (
                      <option key={item.id} value={item.id}>{item.name || item.level}</option>
                    ))}
                  </select>
                </>
              )}
              <button className="w-full bg-indigo-600 py-4 rounded-xl font-bold mt-4 hover:bg-indigo-500 transition shadow-lg">Save to Database</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;