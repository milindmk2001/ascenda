import React, { useState, useEffect } from 'react';
import UserLearningHub from './UserLearningHub'; 
import CourseReader from './CourseReader';

const API_BASE = "https://ascenda-production.up.railway.app";

export default function App() {
  const [selectedGradeName, setSelectedGradeName] = useState('6');
  const [selectedTrack, setSelectedTrack] = useState('CBSE');
  const [grades, setGrades] = useState([]);
  
  // Restored states expected by UserLearningHub
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeCourse, setActiveCourse] = useState(null);

  const isCompetitiveTrack = selectedTrack === 'IIT-JEE' || selectedTrack === 'NEET';

  // Dropdown Fetch: Fetch all available structural grade levels
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
  }, []);

  // Restored Course Fetch: Pulls hub course cards when filters change
  useEffect(() => {
    setLoading(true);
    
    // Construct search params based on track and grade parameters
    const params = new URLSearchParams({
      track_code: selectedTrack,
      grade_name: selectedGradeName
    });

    fetch(`${API_BASE}/api/curriculum/resolve-hub?${params.toString()}`)
      .then((res) => {
        if (!res.ok) throw new Error("Hub resolution endpoint returned an operational error.");
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data)) {
          setSubjects(data);
        } else {
          setSubjects([]);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error updating active hub courses:", err);
        setSubjects([]);
        setLoading(false);
      });
  }, [selectedTrack, selectedGradeName]);

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
              {(() => {
                const seenLevels = new Set();
                return grades
                  .filter(g => g.level !== null && g.level !== undefined)
                  .sort((a, b) => Number(a.level) - Number(b.level))
                  .filter(g => {
                    if (seenLevels.has(g.level)) return false;
                    seenLevels.add(g.level);
                    return true;
                  })
                  .map((g) => (
                    <option key={g.id} value={String(g.level)} className="bg-[#0d1527]">
                      {g.name}
                    </option>
                  ));
              })()}
            </select>
          </div>
        </div>
      </header>

      {/* RENDER MAIN PANEL VIEWER */}
      <main className="w-full">
        {activeCourse ? (
          <CourseReader 
            subject={activeCourse} 
            onBack={() => setActiveCourse(null)} 
          />
        ) : (
          <UserLearningHub 
            subjects={subjects}
            loading={loading}
            trackName={selectedTrack}
            gradeName={selectedGradeName}
            onCourseSelect={setActiveCourse}
          />
        )}
      </main>
    </div>
  );
}