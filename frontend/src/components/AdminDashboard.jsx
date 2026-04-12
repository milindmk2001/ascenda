import React, { useState, useEffect } from 'react';
import { Plus, Trash2, BookOpen, Layers, RefreshCw, AlertCircle } from 'lucide-react';

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
    
    // Independent Fetching
    try {
      const orgRes = await fetch(`${apiBase}/api/admin/organizations/`);
      if (orgRes.ok) setOrganizations(await orgRes.json());

      const gradeRes = await fetch(`${apiBase}/api/admin/curriculum/grades`);
      if (gradeRes.ok) setGrades(await gradeRes.json());
      else console.warn("Grades table check failed.");

    } catch (e) {
      setError("Backend unreachable. Check Railway logs.");
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
      endpoint = `${apiBase}/api/admin/curriculum/subjects/${formData.type}`;
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    if (response.ok) {
      setIsModalOpen(false);
      fetchData();
    } else {
      alert("Save failed. Check console for details.");
    }
  };

  if (loading && organizations.length === 0) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">
      <RefreshCw className="animate-spin mr-2" /> Initializing...
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-4xl font-black mb-4">Ascenda Admin</h1>
            <div className="flex gap-2 p-1 bg-slate-900 rounded-lg w-fit">
              <button onClick={() => setActiveTab('orgs')} className={`px-4 py-2 rounded-md ${activeTab === 'orgs' ? 'bg-indigo-600' : 'text-slate-400'}`}>Organizations</button>
              <button onClick={() => setActiveTab('curriculum')} className={`px-4 py-2 rounded-md ${activeTab === 'curriculum' ? 'bg-indigo-600' : 'text-slate-400'}`}>Curriculum</button>
            </div>
          </div>
          <button onClick={() => { setModalType(activeTab === 'orgs' ? 'org' : 'grade'); setIsModalOpen(true); }} className="bg-indigo-600 px-6 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-indigo-500">
            <Plus size={20} /> Add New
          </button>
        </div>

        {error && <div className="bg-red-500/10 border border-red-500/50 p-4 rounded-xl mb-6 text-red-400 flex items-center gap-2"><AlertCircle size={18}/> {error}</div>}

        {activeTab === 'orgs' ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
             <table className="w-full text-left">
              <thead className="bg-slate-800/50 text-slate-500 text-xs uppercase font-bold">
                <tr><th className="p-4">Name</th><th className="p-4">Category</th><th className="p-4 text-right">Action</th></tr>
              </thead>
              <tbody>
                {organizations.map(org => (
                  <tr key={org.id} className="border-t border-slate-800 hover:bg-white/5">
                    <td className="p-4 font-medium">{org.name}</td>
                    <td className="p-4 text-xs font-bold text-indigo-400 uppercase">{org.org_type}</td>
                    <td className="p-4 text-right"><Trash2 size={16} className="inline text-slate-600 hover:text-red-400 cursor-pointer" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800">
              <h3 className="font-bold mb-4 flex items-center gap-2 text-indigo-400"><Layers size={18}/> Grades</h3>
              {grades.map(g => <div key={g.id} className="bg-slate-950 p-3 mb-2 rounded-lg border border-slate-800 flex justify-between"><span>{g.level}</span><Trash2 size={14} className="text-slate-600"/></div>)}
            </div>
            <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 flex flex-col items-center justify-center text-slate-500">
              <BookOpen size={48} className="mb-2 opacity-20" />
              <p>Add subjects via the Add New button</p>
            </div>
          </div>
        )}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100]">
          <div className="bg-slate-900 p-8 rounded-2xl w-full max-w-sm border border-slate-800">
            <h2 className="text-xl font-bold mb-6">Add {modalType}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              {modalType === 'org' && (
                <>
                  <input required className="w-full bg-slate-950 p-3 rounded-lg border border-slate-800" placeholder="Name" onChange={e => setFormData({...formData, name: e.target.value})} />
                  <select className="w-full bg-slate-950 p-3 rounded-lg border border-slate-800" onChange={e => setFormData({...formData, org_type: e.target.value})}>
                    <option value="board">Board</option>
                    <option value="competitive">Competitive</option>
                  </select>
                </>
              )}
              {modalType === 'grade' && (
                <input required className="w-full bg-slate-950 p-3 rounded-lg border border-slate-800" placeholder="Level (e.g. Class 10)" onChange={e => setFormData({...formData, level: e.target.value})} />
              )}
              <button className="w-full bg-indigo-600 py-3 rounded-lg font-bold">Save</button>
              <button type="button" onClick={() => setIsModalOpen(false)} className="w-full text-slate-500 text-sm">Cancel</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;