import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit2, RefreshCw, Layers, X } from 'lucide-react';

const AdminDashboard = ({ apiBase }) => {
  const [grades, setGrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ level: '' });

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/admin/curriculum/grades`);
      if (res.ok) setGrades(await res.json());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [apiBase]);

  const handleDelete = async (id) => {
    if (window.confirm("Delete this grade?")) {
      await fetch(`${apiBase}/api/admin/curriculum/grades/${id}`, { method: 'DELETE' });
      fetchData();
    }
  };

  const handleEdit = (grade) => {
    setEditingId(grade.id);
    setFormData({ level: grade.level });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const method = editingId ? 'PUT' : 'POST';
    const url = editingId ? `${apiBase}/api/admin/curriculum/grades/${editingId}` : `${apiBase}/api/admin/curriculum/grades`;
    
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    if (res.ok) {
      setIsModalOpen(false);
      setEditingId(null);
      fetchData();
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-10">
          <h1 className="text-3xl font-black">Curriculum Management</h1>
          <button onClick={() => { setEditingId(null); setFormData({level:''}); setIsModalOpen(true); }} className="bg-indigo-600 px-6 py-2 rounded-xl font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/20">
            <Plus size={18} /> Add Grade
          </button>
        </div>

        <div className="bg-slate-900 rounded-3xl border border-slate-800 p-6">
          <h3 className="text-indigo-400 font-bold mb-6 flex items-center gap-2 uppercase tracking-widest text-xs"><Layers size={16}/> Active Grade Levels</h3>
          <div className="grid gap-3">
            {grades.map(g => (
              <div key={g.id} className="bg-slate-950 p-5 rounded-2xl border border-slate-800 flex justify-between items-center group hover:border-indigo-500/50 transition-all">
                <span className="font-bold text-slate-300">{g.level}</span>
                <div className="flex gap-4 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Edit2 size={18} className="text-slate-500 hover:text-white cursor-pointer" onClick={() => handleEdit(g)} />
                  <Trash2 size={18} className="text-slate-500 hover:text-red-500 cursor-pointer" onClick={() => handleDelete(g.id)} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 p-8 rounded-3xl w-full max-w-sm">
            <h2 className="text-xl font-bold mb-6 uppercase tracking-tighter">{editingId ? 'Edit Grade' : 'New Grade'}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <input required className="w-full bg-slate-950 p-4 rounded-xl border border-slate-800 focus:border-indigo-500 outline-none" placeholder="e.g. Class 10" value={formData.level} onChange={e => setFormData({level: e.target.value})} />
              <button className="w-full bg-indigo-600 py-4 rounded-xl font-bold shadow-lg shadow-indigo-500/20">{editingId ? 'Update' : 'Create'}</button>
              <button type="button" onClick={() => setIsModalOpen(false)} className="w-full text-slate-500 text-sm font-medium">Cancel</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;