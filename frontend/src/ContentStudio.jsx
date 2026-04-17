import React, { useState } from 'react';

const ContentStudio = ({ onBack, apiBase }) => {
  const [lesson, setLesson] = useState({
    title: '',
    variables: { u: 0, a: 9.8, t: 0, s: 0 },
    formula: 's = ut + 1/2at^2',
    videoAssetId: ''
  });

  const syncToDB = async () => {
    try {
      const res = await fetch(`${apiBase}/api/studio/lesson`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lesson)
      });
      if (res.ok) alert("Lesson Synced Successfully!");
    } catch (err) {
      alert("Error syncing to database");
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto min-h-screen">
      {/* Header Section */}
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-black">
          CONTENT <span className="text-indigo-500">STUDIO</span>
        </h1>
        <button 
          onClick={onBack} 
          className="text-slate-400 hover:text-white transition-colors p-2"
        >
          ✕ Close
        </button>
      </header>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        
        {/* Editor Column */}
        <div className="space-y-6 bg-slate-900/50 p-6 rounded-2xl border border-slate-800">
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Lesson Title</label>
            <input 
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 mt-2 focus:border-indigo-500 outline-none transition-all"
              placeholder="e.g. Gravity and Motion"
              onChange={e => setLesson({...lesson, title: e.target.value})}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            {Object.keys(lesson.variables).map(key => (
              <div key={key}>
                <label className="text-xs font-bold text-slate-500 uppercase">Variable {key}</label>
                <input 
                  type="number"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 mt-2 focus:border-indigo-500 outline-none transition-all"
                  value={lesson.variables[key]}
                  onChange={e => setLesson({
                    ...lesson, 
                    variables: {...lesson.variables, [key]: parseFloat(e.target.value) || 0}
                  })}
                />
              </div>
            ))}
          </div>

          <button 
            onClick={syncToDB}
            className="w-full bg-indigo-600 py-4 rounded-xl font-bold shadow-lg shadow-indigo-500/20 hover:bg-indigo-500 transition-all active:scale-[0.98]"
          >
            Sync to Master Database
          </button>
        </div>

        {/* Preview Column */}
        <div className="space-y-4">
          <div className="bg-black rounded-3xl border border-slate-800 aspect-video flex flex-col items-center justify-center relative overflow-hidden">
             <div className="text-center">
                <div className="text-indigo-500 text-5xl mb-4 font-black tracking-tighter">VEO</div>
                <p className="text-slate-500 text-sm font-medium">Physics Engine Preview</p>
             </div>
             
             {/* Dynamic Overlay for Debugging */}
             <div className="absolute bottom-6 left-6 font-mono text-[10px] text-indigo-400/40 bg-indigo-400/5 p-2 rounded-md">
                STATE: {JSON.stringify(lesson.variables)}
             </div>
          </div>
          <p className="text-center text-slate-600 text-xs italic">
            Visual output is rendered via Remotion using the JSON parameters defined on the left.
          </p>
        </div>

      </div> {/* End of Grid */}
    </div> // End of Parent Container
  );
};

export default ContentStudio;