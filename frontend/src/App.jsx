import React, { useState, useEffect } from 'react';
import { getTracks, fetchGrades, fetchResolveHub } from './services/api';
import CourseReader from './CourseReader';

export default function App() {
  const [tracks, setTracks] = useState([]);
  const [grades, setGrades] = useState([]);
  const [subjects, setSubjects] = useState([]);
  
  const [selectedTrack, setSelectedTrack] = useState('');
  const [selectedGrade, setSelectedGrade] = useState('');
  const [activeSubject, setActiveSubject] = useState(null);
  
  const [loadingTracks, setLoadingTracks] = useState(false);
  const [loadingGrades, setLoadingGrades] = useState(false);
  const [loadingHub, setLoadingHub] = useState(false);

  // Load Tracks on mount
  useEffect(() => {
    setLoadingTracks(true);
    getTracks()
      .then((data) => {
        setTracks(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error("Failed to load tracks:", err);
        setTracks([]);
      })
      .finally(() => setLoadingTracks(false));
  }, []);

  // Fetch Grades whenever selectedTrack changes
  useEffect(() => {
    if (!selectedTrack) {
      setGrades([]);
      setSelectedGrade('');
      setSubjects([]);
      return;
    }

    setLoadingGrades(true);
    fetchGrades(selectedTrack)
      .then((data) => {
        setGrades(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error("Failed to load grades:", err);
        setGrades([]);
      })
      .finally(() => setLoadingGrades(false));
  }, [selectedTrack]);

  // Resolve Curriculum Hub Subjects when track and grade are selected
  useEffect(() => {
    if (!selectedTrack || !selectedGrade) {
      setSubjects([]);
      return;
    }

    setLoadingHub(true);
    fetchResolveHub(selectedTrack, selectedGrade)
      .then((data) => {
        setSubjects(Array.isArray(data) ? data : data?.subjects || []);
      })
      .catch((err) => {
        console.error("Failed to resolve hub subjects:", err);
        setSubjects([]);
      })
      .finally(() => setLoadingHub(false));
  }, [selectedTrack, selectedGrade]);

  if (activeSubject) {
    return (
      <CourseReader 
        subject={activeSubject} 
        onBack={() => setActiveSubject(null)} 
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* HEADER */}
      <header className="h-16 border-b border-slate-900 bg-slate-950/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <h1 className="font-mono text-xs font-black tracking-widest text-slate-200 uppercase">
            Ascenda Learning Platform
          </h1>
        </div>
        <button className="px-3 py-1.5 text-[10px] font-mono tracking-widest uppercase bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded text-slate-300 transition-all">
          Curriculum Hub
        </button>
      </header>

      {/* MAIN HUB BODY */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-8 flex flex-col">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8 border-b border-slate-900 pb-6">
          <div>
            <h2 className="text-2xl font-black text-slate-100 tracking-tight font-mono uppercase mb-2">
              Curriculum Index
            </h2>
            <p className="text-xs text-slate-400 font-mono">
              Select a target exam track and grade level to browse available subjects.
            </p>
          </div>

          {/* DROPDOWNS */}
          <div className="flex items-center gap-3">
            {/* TRACK SELECT */}
            <select
              value={selectedTrack}
              onChange={(e) => {
                setSelectedTrack(e.target.value);
                setSelectedGrade('');
              }}
              disabled={loadingTracks}
              className="bg-slate-900 border border-slate-800 text-slate-200 text-xs font-mono rounded px-3 py-2 outline-none focus:border-emerald-500 transition-colors"
            >
              <option value="">Select Track</option>
              {tracks.map((track) => (
                <option key={track} value={track}>
                  {track}
                </option>
              ))}
            </select>

            {/* GRADE SELECT */}
            <select
              value={selectedGrade}
              onChange={(e) => setSelectedGrade(e.target.value)}
              disabled={!selectedTrack || loadingGrades}
              className="bg-slate-900 border border-slate-800 text-slate-200 text-xs font-mono rounded px-3 py-2 outline-none focus:border-emerald-500 transition-colors disabled:opacity-50"
            >
              <option value="">
                {loadingGrades ? "Loading Grades..." : "Select Grade"}
              </option>
              {grades.map((grade) => (
                <option key={grade.id || grade.name} value={grade.name}>
                  {grade.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* MODULE CARDS / SUBJECT LIST */}
        <div className="flex-1 flex flex-col justify-center">
          {loadingHub ? (
            <div className="text-center font-mono text-xs text-slate-500 animate-pulse">
              Resolving curriculum modules...
            </div>
          ) : subjects.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {subjects.map((sub) => (
                <div
                  key={sub.id}
                  onClick={() => setActiveSubject(sub)}
                  className="p-5 border border-slate-900 bg-slate-900/40 rounded-lg hover:border-emerald-500/50 hover:bg-slate-900 transition-all cursor-pointer group"
                >
                  <div className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider mb-2">
                    {sub.code || sub.subject_code || "MODULE"}
                  </div>
                  <h3 className="text-base font-bold text-slate-200 group-hover:text-emerald-400 transition-colors">
                    {sub.name}
                  </h3>
                  {sub.description && (
                    <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                      {sub.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 border border-dashed border-slate-900 rounded-lg text-center bg-slate-900/10">
              <span className="text-xs font-mono uppercase text-slate-500 tracking-wider">
                {selectedTrack && selectedGrade 
                  ? "No Active Modules Found for Selection" 
                  : "No Active Modules Selected"}
              </span>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}