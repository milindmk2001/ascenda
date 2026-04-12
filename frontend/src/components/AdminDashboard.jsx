import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit, X, RefreshCw, BookOpen, Layers } from 'lucide-react';

const AdminDashboard = ({ apiBase }) => {
  const [activeTab, setActiveTab] = useState('orgs'); // 'orgs' or 'curriculum'
  const [organizations, setOrganizations] = useState([]);
  const [grades, setGrades] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState('org'); // 'org', 'grade', or 'subject'
  const [formData, setFormData] = useState({});

  const fetchData = async () => {
    setLoading(true);
    try {
      const [orgRes, gradeRes] = await Promise.all([
        fetch(`${apiBase}/api/admin/organizations/`),
        fetch(`${apiBase}/api/admin/curriculum/grades`)
      ]);
      setOrganizations(await orgRes.json());
      setGrades(await gradeRes.json());
    } catch (e) {
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

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    if (response.ok) {
      setIsModalOpen(false);
      setFormData({});
      fetchData();
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-4xl font-black tracking-tight mb-2">Ascenda Admin</h1>
            <div className="flex gap-4 mt-4">
              <button 
                onClick={() => setActiveTab('orgs')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition ${activeTab === 'orgs' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'}`}
              >
                <Layers size={18} /> Organizations
              </button>
              <button 
                onClick={() => setActiveTab('curriculum')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition ${activeTab === 'curriculum' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'}`}
              >
                <BookOpen size={18} /> Curriculum
              </button>
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={() => { setModalType(activeTab === 'orgs' ? 'org' : 'grade'); setIsModalOpen(true); }} 
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 px-6 py-3 rounded-xl font-bold transition">
              <Plus size={20} /> Add {activeTab === 'orgs' ? 'Organization' : 'Grade'}
            </button>
            {activeTab === 'curriculum' && (
              <button onClick={() => { setModalType('subject'); setIsModalOpen(true); }} 
                      className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 px-6 py-3 rounded-xl font-bold transition">
                <Plus size={20} /> Add Subject
              </button>
            )}
          </div>
        </div>

        {/* Organizations Table */}
        {activeTab === 'orgs' ? (
          <div className="bg-slate-800/50 rounded-2xl border border-slate-700 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-800 text-slate-400 text-xs font-bold uppercase">
                <tr><th className="p-5">Name</th><th className="p-5">Category</th><th className="p-5 text-right">Control</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {organizations.map(org => (
                  <tr key={org.id} className="hover:bg-slate-700/20">
                    <td className="p-5 font-semibold">{org.name}</td>
                    <td className="p-5"><span className="px-3 py-1 rounded-full text-[10px] bg-slate-700 uppercase font-bold">{org.org_type}</span></td>
                    <td className="p-5 text-right"><Trash2 size={18} className="inline text-slate-500 hover:text-red-400 cursor-pointer" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          /* Curriculum View */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2"><Layers className="text-indigo-400" /> Grade Levels</h3>
              <div className="space-y-2">
                {grades.map(g => (
                  <div key={g.id} className="p-4 bg-slate-900 rounded-xl border border-slate-800 flex justify-between">
                    <span className="font-bold">{g.level}</span>
                    <Trash2 size={16} className="text-slate-600 hover:text-red-400 cursor-pointer" />
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2"><BookOpen className="text-emerald-400" /> Subjects</h3>
              <p className="text-slate-500 text-sm italic">Subjects are linked to Grades or Exams via the "Add Subject" button.</p>
            </div>
          </div>
        )}
      </div>

      {/* Dynamic Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-[200]">
          <div className="bg-slate-800 p-8 rounded-3xl w-full max-w-md border border-slate-700">
            <h2 className="text-2xl font-bold mb-6 uppercase tracking-tighter">Add {modalType}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              {modalType === 'org' && (
                <>
                  <input className="w-full bg-slate-900 p-4 rounded-xl border border-slate-700" placeholder="Org Name" onChange={e => setFormData({...formData, name: e.target.value})} />
                  <select className="w-full bg-slate-900 p-4 rounded-xl border border-slate-700" onChange={e => setFormData({...formData, org_type: e.target.value})}>
                    <option value="board">Board</option>
                    <option value="competitive">Competitive</option>
                  </select>
                </>
              )}
              {modalType === 'grade' && (
                <input className="w-full bg-slate-900 p-4 rounded-xl border border-slate-700" placeholder="Grade Level (e.g. Class 10)" onChange={e => setFormData({...formData, level: e.target.value})} />
              )}
              {modalType === 'subject' && (
                <>
                  <input className="w-full bg-slate-900 p-4 rounded-xl border border-slate-700" placeholder="Subject Name" onChange={e => setFormData({...formData, name: e.target.value})} />
                  <input className="w-full bg-slate-900 p-4 rounded-xl border border-slate-700" placeholder="Code (BIO-10)" onChange={e => setFormData({...formData, subject_code: e.target.value})} />
                  <select className="w-full bg-slate-900 p-4 rounded-xl border border-slate-700" onChange={e => setFormData({...formData, type: e.target.value})}>
                    <option value="regular">Regular (Links to Grade)</option>
                    <option value="exam">Exam (Links to Org)</option>
                  </select>
                  <select className="w-full bg-slate-900 p-4 rounded-xl border border-slate-700" onChange={e => setFormData({
                    ...formData, 
                    [formData.type === 'exam' ? 'organization_id' : 'grade_id']: e.target.value
                  })}>
                    <option value="">Select Target</option>
                    {(formData.type === 'exam' ? organizations : grades).map(item => (
                      <option key={item.id} value={item.id}>{item.name || item.level}</option>
                    ))}
                  </select>
                </>
              )}
              <button className="w-full bg-indigo-600 py-4 rounded-xl font-bold mt-4">Save Entry</button>
              <button type="button" onClick={() => setIsModalOpen(false)} className="w-full text-slate-500 mt-2">Cancel</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;