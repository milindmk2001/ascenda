import React, { useState, useEffect } from 'react';
import UserLearningHub from './UserLearningHub'; 
import CourseReader from './CourseReader';

const API_BASE = "https://ascenda-production.up.railway.app";

export default function App() {
  // Fix 1.4: Change the default initialization token from '11' to '6'
  const [selectedGradeName, setSelectedGradeName] = useState('6');
  const [selectedTrack, setSelectedTrack] = useState('CBSE');
  
  // Fix 1.1: Utilizing the single existing state variable for grades array
  const [grades, setGrades] = useState([]);
  const [activeCourse, setActiveCourse] = useState(null);

  const isCompetitiveTrack = selectedTrack === 'IIT-JEE' || selectedTrack === 'NEET';

  // Fix 1.2: Wire up the global grades useEffect to fetch dynamically from the API
  useEffect(() => {
    fetch(`${API_BASE}/api/admin/curriculum/grades`)
      .then((res) => {
        if (!res.ok) throw new Error("Grades database interface responded with an error.");
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data)) {
          setGrades(data);
        }
      })
      .catch((err) => console.error("Error populating curriculum grades dropdown:", err));
  }, []); // Empty dependencies array preserved per specification

  return (
    <div className="min-h-screen bg-[#070b14] text-white antialiased font-sans">
      {/* GLOBAL NAVBAR HEADER */}
      <header className="flex items-center justify-between px-8 py-4 border-b border-slate-900 bg-[#090f1c]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="h-7 w-7 rounded bg-emerald-500 flex items-center justify-center font-black text-xs text-slate-950 font-mono shadow-md shadow-emerald-500/20">
            A
          </div>
          <span className="text-xs font-black tracking-widest uppercase font-mono bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Ascenda<span className="text-emerald-400">.pro</span>
          </span>
        </div>

        {/* CONTROLS HUB */}
        <div className="flex items-center gap-4">
          {/* TRACK SELECTOR */}
          <div className="flex flex-col">
            <span className="text-[9px] font-mono uppercase text-slate-500 tracking-wider mb-1">Track</span>
            <select
              value={selectedTrack}
              onChange={(e) => setSelectedTrack(e.target.value)}
              className="bg-[#090f1c] border border-slate-800 text-xs rounded px-3 py-1.5 text-slate-300 font-mono focus:outline-none focus:border-emerald-500/50 transition-colors"
            >
              <option value="CBSE" className="bg-[#0d1527]">CBSE Board</option>
              <option value="IIT-JEE" className="bg-[#0d1527]">IIT-JEE</option>
              <option value="NEET" className="bg-[#0d1527]">NEET</option>
            </select>
          </div>

          {/* GRADE SELECTOR */}
          {/* Fix 1.5: Tailwind conditional styling and layout state preserved perfectly */}
          <div 
            className="flex flex-col transition-all duration-300"
            style={{
              opacity: isCompetitiveTrack ? 0.3 : 1,
              pointerEvents: isCompetitiveTrack ? 'none' : 'auto'
            }}
          >
            <span className="text-[9px] font-mono uppercase text-slate-500 tracking-wider mb-1">Grade</span>
            <select
              value={selectedGradeName}
              onChange={(e) => setSelectedGradeName(e.target.value)}
              className="bg-[#090f1c] border border-slate-800 text-xs rounded px-3 py-1.5 text-slate-300 font-mono focus:outline-none focus:border-emerald-500/50 transition-colors min-w-[120px]"
            >
              {/* Fix 1.3 & Fix 3: Dynamic option generation, sorted numerically, presenting name vs level */}
              {grades
                .filter(g => g.level !== null && g.level !== undefined)
                .sort((a, b) => Number(a.level) - Number(b.level))
                .map((g) => (
                  <option key={g.id} value={String(g.level)} className="bg-[#0d1527]">
                    {g.name}
                  </option>
                ))
              }
            </select>
          </div>
        </div>
      </header>

      {/* RENDER MAIN CONTROLLER */}
      <main className="w-full">
        {activeCourse ? (
          <CourseReader 
            subject={activeCourse} 
            onBack={() => setActiveCourse(null)} 
          />
        ) : (
          <UserLearningHub 
            trackCode={selectedTrack}
            gradeName={selectedGradeName}
            isCompetitive={isCompetitiveTrack}
            onSelectCourse={setActiveCourse}
          />
        )}
      </main>
    </div>
  );
}