import React, { useState, useEffect } from 'react';
import { Layout, Database, BookOpen, Plus, Trash2, Edit3, Layers, GraduationCap, Microscope } from 'lucide-react';

const AdminDashboard = ({ apiBase }) => {
  const [activeTab, setActiveTab] = useState('boards');
  const [data, setData] = useState({ boards: [], grades: [], regSubjects: [], examSubjects: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const endpoints = {
        boards: '/api/admin/organizations/',
        grades: '/api/admin/curriculum/grades',
        regSubjects: '/api/admin/curriculum/regular/subjects',
        examSubjects: '/api/admin/curriculum/exam/subjects'
      };
      const res = await fetch(`${apiBase}${endpoints[activeTab]}`);
      const result = await res.json();
      setData(prev => ({ ...prev, [activeTab]: result }));
    } catch (err) {
      console.error("Fetch failed:", err);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex">
      {/* Sidebar Navigation */}
      <nav className="w-72 bg-slate-900 border-r border-slate-800 p-6 flex flex-col gap-2">
        <div className="flex items-center gap-3 mb-10 px-2">
          <div className="bg-indigo-600 p-2 rounded-lg">
            <Layout className="text-white" size={24} />
          </div>
          <h2 className="text-xl font-bold tracking-tight text-white uppercase">Ascenda Admin</h2>
        </div>
        
        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-2 mb-2">Structure</p>
        <TabButton id="boards" icon={<Database size={18}/>} label="Boards" active={activeTab} onClick={setActiveTab} />
        <TabButton id="grades" icon={<Layers size={18}/>} label="Grades" active={activeTab} onClick={setActiveTab} />
        
        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-2 mt-6 mb-2">Curriculum</p>
        <TabButton id="regSubjects" icon={<GraduationCap size={18}/>} label="Regular K-12" active={activeTab} onClick={setActiveTab} />
        <TabButton id="examSubjects" icon={<Microscope size={18}/>} label="Exam Prep" active={activeTab} onClick={setActiveTab} />
      </nav>

      {/* Main Viewport */}
      <main className="flex-1 p-12 overflow-y-auto">
        <header className="flex justify-between items-end mb-10">
          <div>
            <h1 className="text-4xl font-extrabold text-white capitalize">{activeTab.replace('reg', 'Regular ')}</h1>
            <p className="text-slate-400 mt-2">Manage your educational baseline and subject hierarchy.</p>
          </div>
          <button className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-xl flex items-center gap-2 font-bold transition-all shadow-lg shadow-indigo-500/20">
            <Plus size={20} /> Add Item
          </button>
        </header>

        {/* Data Grid */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-800/50 border-b border-slate-800">
              <tr className="text-slate-400 text-[11px] font-black uppercase tracking-widest">
                <th className="p-6">Entity Name</th>
                <th className="p-6">System Code</th>
                <th className="p-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {data[activeTab]?.map((item) => (
                <tr key={item.id} className="group hover:bg-indigo-500/[0.03] transition-colors">
                  <td className="p-6">
                    <div className="font-bold text-white text-lg">{item.name || item.level}</div>
                    <div className="text-xs text-slate-500 mt-1 uppercase font-medium">{activeTab} Entity</div>
                  </td>
                  <td className="p-6">
                    <code className="bg-slate-950 px-3 py-1 rounded-md border border-slate-800 text-indigo-400 text-xs">
                      {item.subject_code || item.org_type || 'SYSTEM_NODE'}
                    </code>
                  </td>
                  <td className="p-6 text-right">
                    <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-2.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition-colors"><Edit3 size={16}/></button>
                      <button className="p-2.5 bg-slate-800 hover:bg-red-900/40 rounded-lg text-slate-500 hover:text-red-400 transition-colors"><Trash2 size={16}/></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {loading && <div className="p-20 text-center animate-pulse text-slate-500 font-medium">Synchronizing with Database...</div>}
        </div>
      </main>
    </div>
  );
};

const TabButton = ({ id, icon, label, active, onClick }) => (
  <button 
    onClick={() => onClick(id)} 
    className={`flex items-center gap-3 p-3.5 rounded-xl font-bold transition-all duration-200 ${active === id ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`}
  >
    {icon} {label}
  </button>
);

export default AdminDashboard;