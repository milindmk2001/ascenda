import React, { useState, useEffect } from 'react';
import { Plus, Trash2, BookOpen, Layers, RefreshCw, AlertCircle, X } from 'lucide-react';

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
      // Fetch Organizations
      const orgRes = await fetch(`${apiBase}/api/admin/organizations/`);
      if (orgRes.ok) {
        setOrganizations(await orgRes.json());
      }

      // Fetch Grades - Independent try/catch to prevent blocking the UI
      try {
        const gradeRes = await fetch(`${apiBase}/api/admin/curriculum/grades`);
        if (gradeRes.ok) {
          setGrades(await gradeRes.json());
        } else {
          console.warn("Grades endpoint returned an error. Check backend logs.");
        }
      } catch (gradeErr) {
        console.error("Grades fetch error:", gradeErr);
      }

    } catch (e) {
      setError("Network error: Backend unreachable.");
      console.error("Fetch error:", e);
    } finally {
      // Always stop loading, even on failure
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [apiBase]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    let endpoint = `${apiBase}/api/admin/organizations/`;
    if (modalType === 'grade') endpoint = `${apiBase}/api/admin/curriculum/grades`;
    if (modalType === 'subject') {
      endpoint = `${apiBase}/api/admin/curriculum/subjects/${formData.type}`;
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setIsModalOpen(false);
        setFormData({ org_type: 'board', type: 'regular' });
        fetchData();
      } else {
        alert("Failed to save. Check if all required fields are filled.");
      }
    } catch (err) {
      alert("Submission error. Server might be down.");
    }
  };

  if (loading && organizations.length === 0) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white">
        <RefreshCw className="animate-spin mb-4 text-indigo-500" size={32} />
        <p className="font-bold tracking-widest text-slate-500 uppercase text-xs">Initializing Database Connection...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-4xl font-black mb-4 bg-gradient-to-r from-white to-slate-500 bg-clip-text text-transparent">Ascenda Admin</h1>
            <div className="flex gap-2 p-1 bg-slate-900 rounded-xl w-fit border border-slate-800">
              <button 
                onClick={() => setActiveTab('orgs')}
                className={`px-6 py-2 rounded-lg font-bold transition ${activeTab === 'orgs' ? 'bg-indigo-600 shadow-lg' : 'text-slate-500'}`}
              >
                Organizations
              </button>
              <button 
                onClick={() => setActiveTab('curriculum')}
                className={`px-6 py-2 rounded-lg font-bold transition ${activeTab === 'curriculum' ? 'bg-indigo-600 shadow-lg' : 'text-slate-500'}`}
              >
                Curriculum
              </button>
            </div>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={() => { setModalType(activeTab === 'orgs' ? 'org' : 'grade'); setIsModalOpen(true); }}
              className="bg-indigo-600 px-6 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-indigo-500 transition shadow-xl shadow-indigo-500/10"
            >
              <Plus size={20} /> Add {activeTab === 'orgs' ? 'Org' : 'Grade'}
            </button>
            <button onClick={fetchData} className="p-3 bg-slate-900 rounded-xl border border-slate-800 hover:bg-slate-800 transition">
              <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 p-4 rounded-xl mb-6 text-red-400 flex items-center gap-3">
            <AlertCircle size={20} /> {error}
          </div>
        )}

        {activeTab === 'orgs' ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
            <table className="w-full text-left">
              <thead className="bg-slate-800/50 text-slate-500 text-xs uppercase font-black tracking-widest border-b border-slate-800">
                <tr><th className="p-6">Organization Name</th><th className="p-6">Category</th><th className="p-6 text-right">Action</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {organizations.map(org => (
                  <tr key={org.id} className="hover:bg-white/5 transition-colors">
                    <td className="p-6 font-bold text-slate-300">{org.name}</td>
                    <td className="p-6">
                      <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase ${org.org_type === 'competitive' ? 'bg-orange-500/20 text-orange-400' : 'bg-indigo-500/20 text-indigo-400'}`}>
                        {org.org_type}
                      </span>
                    </td>
                    <td className="p-6 text-right"><Trash2 size={18} className="inline text-slate-600 hover:text-red-400 cursor-pointer" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800 shadow-2xl">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2 text-indigo-400"><Layers /> Grade Levels</h3>
              <div className="space-y-3">
                {grades.length > 0 ? grades.map(g => (
                  <div key={g.id} className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex justify-between items-center group hover:border-indigo-500/50 transition">
                    <span className="font-bold text-slate-300">{g.level}</span>
                    <Trash2 size={16} className="text-slate-700 group-hover:text-red-400 cursor-pointer" />
                  </div>
                )) : (
                  <p className="text-slate-600 italic">No grades found in database.</p>
                )}
              </div>
            </div>
            <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800 border-dashed flex flex-col items-center justify-center text-slate-600">
              <BookOpen size={48} className="mb-4 opacity-10" />
              <p className="text-sm">Subject management coming soon.</p>
            </div>
          </div>
        )}
      </div>

      {/* Modal Overlay */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/90 backdrop-blur-md flex items-center justify-center z-[100] p-4">
          <div className="bg-slate-900 p-8 rounded-3xl w-full max-w-sm border border-slate-800 shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-black uppercase tracking-tighter">Add {modalType}</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-500 hover:text-white"><X /></button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              {modalType === 'org' && (
                <>
                  <input required className="w-full bg-slate-950 p-4 rounded-xl border border-slate-800 focus:border-indigo-500 outline-none" 
                         placeholder="Organization Name" onChange={e => setFormData({...formData, name: e.target.value})} />
                  <select className="w-full bg-slate-950 p-4 rounded-xl border border-slate-800 outline-none" onChange={e => setFormData({...formData, org_type: e.target.value})}>
                    <option value="board">Board</option>
                    <option value="competitive">Competitive</option>
                  </select>
                </>
              )}
              {modalType === 'grade' && (
                <input required className="w-full bg-slate-950 p-4 rounded-xl border border-slate-800 focus:border-indigo-500 outline-none" 
                       placeholder="e.g. Class 12" onChange={e => setFormData({...formData, level: e.target.value})} />
              )}
              <button className="w-full bg-indigo-600 py-4 rounded-xl font-bold mt-4 hover:bg-indigo-500 transition shadow-lg shadow-indigo-500/20">Save Entry</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;