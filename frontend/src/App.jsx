import React, { useState, useEffect } from 'react';
import CourseReader from './CourseReader';
import ContentStudio from './ContentStudio';
import VideoLesson from './VideoLesson';
import { fetchGrades, resolveHubSubjects } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('hub'); // 'hub', 'studio', 'video'
  const [selectedTrack, setSelectedTrack] = useState('IIT-JEE');
  const [selectedGrade, setSelectedGrade] = useState('Grade 11');
  const [grades, setGrades] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [loading, setLoading] = useState(false);

  // Step 1: Fetch available grades on component mount
  useEffect(() => {
    fetchGrades()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setGrades(data);
          setSelectedGrade(data[0].name || 'Grade 11');
        }
      })
      .catch((err) => {
        console.error('Failed to fetch grades:', err);
      });
  }, []);

  // Step 2: Fetch hub subjects whenever selectedTrack or selectedGrade changes
  useEffect(() => {
    if (!selectedTrack || !selectedGrade) return;

    setLoading(true);
    resolveHubSubjects(selectedTrack, selectedGrade)
      .then((data) => {
        setSubjects(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to resolve hub subjects:', err);
        setSubjects([]);
        setLoading(false);
      });
  }, [selectedTrack, selectedGrade]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <header className="h-16 border-b border-slate-900 bg-slate-950 px-6 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-3 w-3 bg-emerald-500 rounded-full animate-pulse" />
          <h1 className="text-sm font-black font-mono uppercase tracking-widest text-slate-100">
            Ascenda Learning Platform
          </h1>
        </div>

        <nav className="flex space-x-2">
          <button
            onClick={() => {
              setActiveTab('hub');
              setSelectedSubject(null);
            }}
            className={`px-4 py-1.5 rounded text-xs font-mono uppercase transition-colors ${
              activeTab === 'hub'
                ? 'bg-slate-800 text-emerald-400 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Curriculum Hub
          </button>
          <button
            onClick={() => setActiveTab('studio')}
            className={`px-4 py-1.5 rounded text-xs font-mono uppercase transition-colors ${
              activeTab === 'studio'
                ? 'bg-slate-800 text-emerald-400 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Authoring Studio
          </button>
          <button
            onClick={() => setActiveTab('video')}
            className={`px-4 py-1.5 rounded text-xs font-mono uppercase transition-colors ${
              activeTab === 'video'
                ? 'bg-slate-800 text-emerald-400 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Video AI Player
          </button>
        </nav>
      </header>

      {/* Main View Area */}
      <main className="flex-1 overflow-hidden">
        {activeTab === 'hub' && (
          selectedSubject ? (
            <CourseReader
              subject={selectedSubject}
              onBack={() => setSelectedSubject(null)}
            />
          ) : (
            <div className="max-w-6xl mx-auto p-8 space-y-8">
              {/* Controls Header */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-900 pb-6">
                <div>
                  <h2 className="text-xl font-black font-mono uppercase tracking-tight text-slate-100">
                    Curriculum Index
                  </h2>
                  <p className="text-xs font-mono text-slate-500 mt-1">
                    Select a target exam track and grade level to browse available subjects.
                  </p>
                </div>

                <div className="flex space-x-4">
                  {/* Track Selector */}
                  <select
                    value={selectedTrack}
                    onChange={(e) => setSelectedTrack(e.target.value)}
                    className="bg-slate-900 border border-slate-800 text-xs font-mono text-slate-200 px-3 py-2 rounded focus:outline-none focus:border-emerald-500"
                  >
                    <option value="IIT-JEE">IIT-JEE</option>
                    <option value="NEET">NEET</option>
                  </select>

                  {/* Grade Selector */}
                  <select
                    value={selectedGrade}
                    onChange={(e) => setSelectedGrade(e.target.value)}
                    className="bg-slate-900 border border-slate-800 text-xs font-mono text-slate-200 px-3 py-2 rounded focus:outline-none focus:border-emerald-500"
                  >
                    {grades.length > 0 ? (
                      grades.map((g) => (
                        <option key={g.id || g.name} value={g.name}>
                          {g.name}
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="Grade 11">Grade 11</option>
                        <option value="Grade 12">Grade 12</option>
                      </>
                    )}
                  </select>
                </div>
              </div>

              {/* Subject Cards Grid */}
              {loading ? (
                <div className="text-xs font-mono text-slate-500 animate-pulse text-center py-12">
                  Resolving curriculum hub metadata...
                </div>
              ) : subjects.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {subjects.map((sub) => (
                    <div
                      key={sub.id}
                      onClick={() => setSelectedSubject(sub)}
                      className="p-6 bg-slate-900/50 border border-slate-900 hover:border-emerald-500/50 rounded-lg cursor-pointer transition-all hover:bg-slate-900 flex flex-col justify-between group"
                    >
                      <div>
                        <span className="text-[10px] font-mono uppercase text-emerald-400 tracking-wider">
                          {sub.meta_tag || 'Core Module'}
                        </span>
                        <h3 className="text-lg font-bold text-slate-200 group-hover:text-emerald-400 transition-colors mt-2">
                          {sub.name}
                        </h3>
                      </div>
                      <div className="mt-6 flex items-center justify-between text-xs font-mono text-slate-500">
                        <span>Launch Reader</span>
                        <span className="group-hover:translate-x-1 transition-transform">→</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-12 border border-dashed border-slate-900 rounded-lg text-center bg-slate-950">
                  <div className="text-xs font-mono text-slate-500 uppercase font-bold">
                    No active modules found
                  </div>
                  <div className="text-[11px] font-mono text-slate-600 mt-1">
                    Select a different grade or track configuration.
                  </div>
                </div>
              )}
            </div>
          )
        )}

        {activeTab === 'studio' && <ContentStudio />}

        {activeTab === 'video' && (
          <VideoLesson videoUrl="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4" />
        )}
      </main>
    </div>
  );
}