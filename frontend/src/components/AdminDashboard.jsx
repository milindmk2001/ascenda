import React, { useState, useEffect } from 'react';
import { Layout, Database, BookOpen, Plus, Trash2, Edit3, Layers, GraduationCap, Microscope, Book } from 'lucide-react';

const AdminDashboard = ({ apiBase }) => {
  const [activeTab, setActiveTab] = useState('boards');
  // Updated state to include subdivision areas for both regular and exam branches
  const [data, setData] = useState({ 
    boards: [], 
    grades: [], 
    regSubjects: [], 
    regAreas: [],
    examSubjects: [],
    examAreas: [] 
  });
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
        regAreas: '/api/admin/curriculum/regular/subject-areas',
        examSubjects: '/api/admin/curriculum/exam/subjects',
        examAreas: '/api/admin/curriculum/exam/subject-areas'
      };
      
      const res = await fetch(`${apiBase}${endpoints[activeTab]}`);
      
      // Safety check: if backend returns an error or 404, default to an empty array
      if (!res.ok) {
        console.warn(`Fetch failed for ${activeTab}: ${res.status}`);
        setData(prev => ({ ...prev, [activeTab]: [] }));
        setLoading(false);
        return;
      }

      const result = await res.json();
      // Ensure the result is an array before mapping in the render block
      setData(prev => ({ ...prev, [activeTab]: Array.isArray(result) ? result : [] }));
    } catch (err) {
      console.error("Fetch failed:", err);
      setData(prev => ({ ...prev, [activeTab]: [] }));
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
          <h2 className="text-xl font-bold tracking-tight text-white uppercase italic">Ascenda Admin</h2>
        </div>
        
        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-2 mb-2">Core Structure</p>
        <TabButton id="boards" icon={<Database size={18}/>} label="Boards" active={activeTab} onClick={setActiveTab} />
        <TabButton id="grades" icon={<Layers size={18}/>} label="Grades" active={activeTab} onClick={setActiveTab} />
        
        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-2 mt-6 mb-2">Regular K-12</p>
        <TabButton id="regSubjects" icon={<GraduationCap size={18}/>} label="Subjects" active={activeTab} onClick={setActiveTab} />
        <TabButton id="regAreas" icon={<Book size={18}/>} label="Subject Areas" active={activeTab} onClick={setActiveTab} />

        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-2 mt-6 mb-2">Exam Prep</p>
        <TabButton id="examSubjects" icon={<Microscope size={18}/>} label="Exam Subjects" active={activeTab} onClick={setActiveTab} />
        <TabButton id="examAreas" icon={<BookOpen size={18}/>} label="Exam Areas" active={activeTab} onClick={setActiveTab} />
      </nav>

      {/* Main Viewport */}
      <main className="flex-1 p-12 overflow-y-auto">
        <header className="flex justify-between items-end mb-10">
          <div>
            <h1 className="text-4xl font-extrabold text-white capitalize">
              {activeTab.replace('reg', 'Regular ').replace('exam', 'Exam ')}
            </h1>
            <p className="text-slate-400 mt-2 font-medium">Manage hierarchical educational data for the Ascenda platform.</p>
          </div>
          <button className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-xl flex items-center gap-2 font-bold transition-all shadow-lg shadow-indigo-500/20 active:scale-95">
            <Plus size={20} /> Add New {activeTab.slice(0, -1)}
          </button>
        </header>

        {/* Data Grid with Error Protection */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-800/50 border-b border-slate-800">
              <tr className="text-slate-400 text-[11px] font-black uppercase tracking-widest">
                <th className="p-6">Entry Name</th>
                <th className="p-6">Unique Code / Type</th>
                <th className="p-6 text-right">Management</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {data[activeTab] && data[activeTab].length > 0 ? (
                data[activeTab].map((item) => (
                  <tr key={item.id} className="group hover:bg-indigo-500/[0.03] transition-colors">
                    <td className="p-6">
                      <div className="font-bold text-white text-lg">{item.name || item.level}</div>
                      <div className="text-[10px] text-slate-500 mt-1 uppercase font-bold tracking-tight">
                        ID: {item.id.slice(0, 8)}...
                      </div>
                    </td>
                    <td className="p-6">
                      <code className="bg-slate-950 px-3 py-1.5 rounded-md border border-slate-800 text-indigo-400 text-xs font-mono">
                        {item.subject_code || item.area_code || item.org_type || 'SYSTEM_NODE'}
                      </code>
                    </td>
                    <td className="p-6 text-right">
                      <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button title="Edit" className="p-2.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition-colors">
                          <Edit3 size={16}/>
                        </button>
                        <button title="Delete" className="p-2.5 bg-slate-800 hover:bg-red-900/40 rounded-lg text-slate-500 hover:text-red-400 transition-colors">
                          <Trash2 size={16}/>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                !loading && (
                  <tr>
                    <td colSpan="3" className="p-20 text-center text-slate-600 font-medium italic">
                      No records found for this category.
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
          {loading && (
            <div className="p-20 text-center flex flex-col items-center gap-4 bg-slate-900/50">
              <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="animate-pulse text-slate-500 font-bold uppercase tracking-widest text-[10px]">Synchronizing...</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

const TabButton = ({ id, icon, label, active, onClick }) => (
  <button 
    onClick={() => onClick(id)} 
    className={`flex items-center gap-3 p-3.5 rounded-xl font-bold transition-all duration-200 ${
      active === id 
        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' 
        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
    }`}
  >
    {icon} {label}
  </button>
);

export default AdminDashboard;