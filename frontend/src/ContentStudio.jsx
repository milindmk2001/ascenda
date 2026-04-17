import React, { useState } from 'react';

const ContentStudio = ({ onBack, apiBase }) => {
  const [lessonData, setLessonData] = useState({
    title: '',
    variables: { u: 0, a: 9.8, t: 0, s: 0 },
    formula: 's = ut + \\frac{1}{2}at^2',
    videoAssetId: ''
  });

  const handleSync = async () => {
    try {
      const response = await fetch(`${apiBase}/api/studio/lesson`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lessonData)
      });
      if (response.ok) alert("🚀 Lesson Synced to Master DB!");
    } catch (err) {
      console.error("Sync failed", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 p-8 text-white animate-in fade-in duration-500">
      <header className="flex justify-between items-center mb-12">
        <div>
          <button onClick={onBack} className="text-slate-500 hover:text-white mb-2 block">← Back to Home</button>
          <h1 className="text-4xl font-black tracking-tight">Ascenda <span className="text-indigo-500">Content Studio</span></h1>
        </div>
        <button onClick={handleSync} className="bg-indigo-600 hover:bg-indigo-500 px-8 py-4 rounded-2xl font-bold shadow-lg shadow-indigo-500/20 transition-all">
          Sync to Master Database
        }
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* FORM SECTION */}
        <div className="space-y-8 bg-slate-900/50 p-8 rounded-3xl border border-slate-800">
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase mb-3">Lesson Title</label>
            <input 
              type="text" className="w-full bg-slate-950 border border-slate-700 rounded-xl p-4 outline-none focus:border-indigo-500"
              placeholder="e.g., Kinematics: Constant Acceleration"
              onChange={(e) => setLessonData({...lessonData, title: e.target.value})}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            {['u', 'a', 't', 's'].map(v => (
              <div key={v}>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Variable ({v})</label>
                <input 
                  type="number" className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3"
                  onChange={(e) => setLessonData({
                    ...lessonData, 
                    variables: {...lessonData.variables, [v]: parseFloat(e.target.value)}
                  })}
                />
              </div>
            ))}
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase mb-3">Formula (LaTeX)</label>
            <input 
              type="text" className="w-full bg-slate-950 border border-slate-700 rounded-xl p-4 font-mono text-indigo-400"
              value={lessonData.formula}
              onChange={(e) => setLessonData({...lessonData, formula: e.target.value})}
            />
          </div>
        </div>

        {/* PREVIEW SIDEBAR */}
        <div className="flex flex-col gap-6">
          <div className="aspect-video bg-black rounded-3xl border-2 border-dashed border-slate-800 flex items-center justify-center relative overflow-hidden">
            <div className="text-center z-10">
              <span className="text-4xl mb-4 block">🎬</span>
              <p className="text-slate-500 font-medium">Remotion Player Preview</p>
              <p className="text-[10px] text-slate-700 uppercase tracking-widest mt-2">Waiting for Asset: {lessonData.videoAssetId || 'None'}</p>
            </div>
            {/* Visualizing the Physics Variable state */}
            <div className="absolute bottom-6 left-6 text-[10px] font-mono text-indigo-500/50">
              STATE: {JSON.stringify(lessonData.variables)}
            </div>
          </div>
          
          <div className="bg-indigo-500/5 border border-indigo-500/20 p-6 rounded-2xl">
            <h4 className="text-sm font-bold mb-2">Asset Linking</h4>
            <input 
              type="text" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs"
              placeholder="Veo Video ID (e.g., veo_92834)"
              onChange={(e) => setLessonData({...lessonData, videoAssetId: e.target.value})}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContentStudio;