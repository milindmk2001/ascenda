import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit, X } from 'lucide-react';

const AdminDashboard = ({ apiBase }) => {
  const [organizations, setOrganizations] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: '', org_type: 'board' });

  // 1. Fetch Organizations
  const fetchOrgs = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiBase}/api/admin/organizations/`);
      const data = await response.json();
      setOrganizations(data);
    } catch (error) {
      console.error("Failed to fetch:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (apiBase) fetchOrgs();
  }, [apiBase]);

  // 2. Handle Form Submission (Create or Update)
  const handleSubmit = async (e) => {
    e.preventDefault();
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
        fetchOrgs();
      } else {
        alert("Error saving organization. Please check your backend.");
      }
    } catch (error) {
      alert("Error saving organization");
    }
  };

  // 3. Handle Delete with UI Refresh
  const handleDelete = async (id) => {
    if (window.confirm("Are you sure you want to delete this organization?")) {
      try {
        const response = await fetch(`${apiBase}/api/admin/organizations/${id}`, { 
          method: 'DELETE' 
        });
        if (response.ok) {
          fetchOrgs(); // Refresh table immediately after delete
        }
      } catch (error) {
        console.error("Delete failed:", error);
      }
    }
  };

  // 4. Modal Helpers
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
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Organization Manager</h1>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-lg transition"
          >
            <Plus size={20} /> Add New Organization
          </button>
        </div>

        <div className="bg-slate-800 rounded-xl overflow-hidden border border-slate-700">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-700/50">
              <tr>
                <th className="p-4 border-b border-slate-700">Name</th>
                <th className="p-4 border-b border-slate-700">Type</th>
                <th className="p-4 border-b border-slate-700 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="3" className="p-10 text-center text-slate-400">Loading data...</td></tr>
              ) : organizations.map((org) => (
                <tr key={org.id} className="hover:bg-slate-700/30 transition">
                  <td className="p-4 border-b border-slate-700 font-medium">{org.name}</td>
                  <td className="p-4 border-b border-slate-700">
                    <span className="px-2 py-1 rounded bg-slate-900 text-xs uppercase tracking-wider text-slate-400">
                      {org.org_type}
                    </span>
                  </td>
                  <td className="p-4 border-b border-slate-700 text-right">
                    <div className="flex justify-end gap-3">
                      <button 
                        onClick={() => openEditModal(org)}
                        className="text-slate-400 hover:text-white transition"
                      >
                        <Edit size={18} />
                      </button>
                      <button 
                        onClick={() => handleDelete(org.id)}
                        className="text-slate-400 hover:text-red-400 transition"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-800 p-6 rounded-2xl w-full max-w-md border border-slate-700 shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">
                {editingId ? 'Edit Organization' : 'New Organization'}
              </h2>
              <button onClick={closeModal} className="text-slate-400 hover:text-white">
                <X size={24} />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Organization Name</label>
                <input 
                  autoFocus
                  required
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-indigo-500"
                  placeholder="e.g. CBSE"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Type</label>
                <select 
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-indigo-500"
                  value={formData.org_type}
                  onChange={(e) => setFormData({...formData, org_type: e.target.value})}
                >
                  <option value="board">Educational Board</option>
                  <option value="competitive">Competitive Exam</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <button 
                type="submit"
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-lg mt-4 transition"
              >
                {editingId ? 'Update Organization' : 'Save Organization'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;