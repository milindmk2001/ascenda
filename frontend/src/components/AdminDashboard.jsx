import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit, X, RefreshCw } from 'lucide-react';

const AdminDashboard = ({ apiBase }) => {
  const [organizations, setOrganizations] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: '', org_type: 'board' });

  // 1. Fetch Organizations
  const fetchOrgs = async () => {
    if (!apiBase) return;
    try {
      setLoading(true);
      const response = await fetch(`${apiBase}/api/admin/organizations/`);
      if (!response.ok) throw new Error("Failed to fetch data");
      const data = await response.json();
      setOrganizations(data);
    } catch (error) {
      console.error("Fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgs();
  }, [apiBase]);

  // 2. Create or Update Logic
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Determine if we are updating or creating
    const url = editingId 
      ? `${apiBase}/api/admin/organizations/${editingId}`
      : `${apiBase}/api/admin/organizations/`;
    
    const method = editingId ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        closeModal();
        fetchOrgs(); // Refresh list
      } else {
        const errData = await response.json();
        alert(`Error: ${errData.detail || "Could not save organization"}`);
      }
    } catch (error) {
      alert("Network error: Check if backend is running.");
    }
  };

  // 3. Delete Logic
  const handleDelete = async (id) => {
    if (window.confirm("Delete this organization? This cannot be undone.")) {
      try {
        const response = await fetch(`${apiBase}/api/admin/organizations/${id}`, { 
          method: 'DELETE' 
        });
        if (response.ok) {
          fetchOrgs();
        }
      } catch (error) {
        console.error("Delete failed:", error);
      }
    }
  };

  // 4. Modal Management
  const openEditModal = (org) => {
    setEditingId(org.id);
    setFormData({ name: org.name, org_type: org.org_type });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingId(null);
    setFormData({ name: '', org_type: 'board' });
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8">
      <div className="max-w-5xl mx-auto">
        
        {/* Header */}
        <div className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-white mb-2">Ascenda Admin</h1>
            <p className="text-slate-400">Manage your educational boards and competitive exams.</p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={fetchOrgs}
              className="p-3 bg-slate-800 hover:bg-slate-700 rounded-lg transition border border-slate-700"
              title="Refresh Data"
            >
              <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
            </button>
            <button 
              onClick={() => setIsModalOpen(true)}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 px-6 py-3 rounded-xl font-bold transition shadow-lg shadow-indigo-500/20"
            >
              <Plus size={20} /> Add New
            </button>
          </div>
        </div>

        {/* Content Table */}
        <div className="bg-slate-800/50 rounded-2xl overflow-hidden border border-slate-700 backdrop-blur-sm">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-800 text-slate-400 uppercase text-xs font-bold tracking-widest">
                <th className="p-5">Organization Name</th>
                <th className="p-5">Category</th>
                <th className="p-5 text-right">Control</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {loading && organizations.length === 0 ? (
                <tr>
                  <td colSpan="3" className="p-20 text-center">
                    <div className="flex flex-col items-center gap-4 text-slate-500">
                      <RefreshCw size={40} className="animate-spin" />
                      <p>Loading records from Railway...</p>
                    </div>
                  </td>
                </tr>
              ) : organizations.map((org) => (
                <tr key={org.id} className="hover:bg-slate-700/20 transition group">
                  <td className="p-5">
                    <div className="font-semibold text-lg text-slate-200">{org.name}</div>
                  </td>
                  <td className="p-5">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-tighter ${
                      org.org_type === 'competitive' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' : 
                      org.org_type === 'board' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                      'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                    }`}>
                      {org.org_type}
                    </span>
                  </td>
                  <td className="p-5 text-right">
                    <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button 
                        onClick={() => openEditModal(org)}
                        className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition"
                      >
                        <Edit size={18} />
                      </button>
                      <button 
                        onClick={() => handleDelete(org.id)}
                        className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {!loading && organizations.length === 0 && (
                <tr>
                  <td colSpan="3" className="p-20 text-center text-slate-500 italic">
                    No organizations found. Click "Add New" to begin.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Overlay */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 z-[200]">
          <div className="bg-slate-800 p-8 rounded-3xl w-full max-w-md border border-slate-700 shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-2xl font-bold">
                {editingId ? 'Edit Record' : 'Create New'}
              </h2>
              <button onClick={closeModal} className="text-slate-400 hover:text-white transition">
                <X size={24} />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-500 mb-2 ml-1">Name</label>
                <input 
                  autoFocus
                  required
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-4 text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                  placeholder="e.g. UPSC, CBSE, or Harvard"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-slate-500 mb-2 ml-1">Category Type</label>
                <select 
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-4 text-white focus:outline-none focus:border-indigo-500 transition appearance-none"
                  value={formData.org_type}
                  onChange={(e) => setFormData({...formData, org_type: e.target.value})}
                >
                  <option value="board">Educational Board</option>
                  <option value="competitive">Competitive Exam</option>
                  <option value="other">Other / Special</option>
                </select>
              </div>
              <button 
                type="submit"
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-indigo-500/20 transition-all active:scale-[0.98]"
              >
                {editingId ? 'Save Changes' : 'Create Organization'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;