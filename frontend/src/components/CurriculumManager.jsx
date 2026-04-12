import React, { useState, useEffect } from 'react';

const CurriculumManager = ({ apiBase }) => {
  const [grades, setGrades] = useState([]);
  const [organizations, setOrganizations] = useState([]);
  const [gradeLevel, setGradeLevel] = useState('');
  const [subjectData, setSubjectData] = useState({ name: '', code: '', targetId: '', type: 'regular' });

  useEffect(() => {
    const loadInitialData = async () => {
      const gRes = await fetch(`${apiBase}/api/admin/curriculum/grades`);
      const oRes = await fetch(`${apiBase}/api/admin/organizations/`);
      setGrades(await gRes.json());
      setOrganizations(await oRes.json());
    };
    loadInitialData();
  }, [apiBase]);

  const addGrade = async () => {
    await fetch(`${apiBase}/api/admin/curriculum/grades`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ level: gradeLevel })
    });
    setGradeLevel('');
  };

  const addSubject = async () => {
    const endpoint = subjectData.type === 'regular' ? 'regular' : 'exam';
    const payload = {
      name: subjectData.name,
      subject_code: subjectData.code,
      [subjectData.type === 'regular' ? 'grade_id' : 'organization_id']: subjectData.targetId
    };
    
    await fetch(`${apiBase}/api/admin/curriculum/subjects/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  };

  return (
    <div className="p-8 bg-slate-900 text-white min-h-screen">
      <h2 className="text-2xl font-bold mb-6">Curriculum Configuration</h2>
      
      {/* Grade Section */}
      <div className="bg-slate-800 p-6 rounded-xl mb-8 border border-slate-700">
        <h3 className="text-lg font-semibold mb-4 text-indigo-400">Add New Grade Level</h3>
        <div className="flex gap-4">
          <input className="bg-slate-950 p-3 rounded-lg flex-1 border border-slate-700" 
                 placeholder="e.g. Class 10" value={gradeLevel} onChange={e => setGradeLevel(e.target.value)} />
          <button onClick={addGrade} className="bg-indigo-600 px-6 py-3 rounded-lg font-bold">Add Grade</button>
        </div>
      </div>

      {/* Subject Section */}
      <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
        <h3 className="text-lg font-semibold mb-4 text-indigo-400">Add New Subject</h3>
        <div className="grid grid-cols-2 gap-4">
          <input className="bg-slate-950 p-3 rounded-lg border border-slate-700" 
                 placeholder="Subject Name" onChange={e => setSubjectData({...subjectData, name: e.target.value})} />
          <input className="bg-slate-950 p-3 rounded-lg border border-slate-700" 
                 placeholder="Code (e.g. PHY-10)" onChange={e => setSubjectData({...subjectData, code: e.target.value})} />
          <select className="bg-slate-950 p-3 rounded-lg border border-slate-700" 
                  onChange={e => setSubjectData({...subjectData, type: e.target.value})}>
            <option value="regular">Regular (School)</option>
            <option value="exam">Competitive (Exam)</option>
          </select>
          <select className="bg-slate-950 p-3 rounded-lg border border-slate-700" 
                  onChange={e => setSubjectData({...subjectData, targetId: e.target.value})}>
            <option value="">Select Grade or Org</option>
            {(subjectData.type === 'regular' ? grades : organizations).map(item => (
              <option key={item.id} value={item.id}>{item.level || item.name}</option>
            ))}
          </select>
        </div>
        <button onClick={addSubject} className="mt-6 w-full bg-indigo-600 py-3 rounded-lg font-bold">Save Subject</button>
      </div>
    </div>
  );
};

export default CurriculumManager;