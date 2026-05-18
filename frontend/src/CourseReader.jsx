import React, { useState, useEffect } from 'react';

const API_BASE = "https://ascenda-production.up.railway.app";

const CourseReader = ({ subject, onBack }) => {
  const [curriculumTree, setCurriculumTree] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(null);

  useEffect(() => {
    const fetchCurriculumTree = async () => {
      if (!subject?.id) return;
      
      try {
        setLoading(true);
        setError(null);
        
        const res = await fetch(`${API_BASE}/api/curriculum/subjects/${subject.id}/tree`);
        
        if (!res.ok) {
          throw new Error(`Server responded with status ${res.status}: Curriculum configuration pending backend assembly.`);
        }
        
        const data = await res.json();
        
        // CRITICAL DEFENSIVE CHECK: Ensure data layer is an array before setting state
        if (Array.isArray(data)) {
          setCurriculumTree(data);
        } else {
          console.error("API payload structured improperly, expected array:", data);
          setCurriculumTree([]);
          setError("Curriculum tree data is currently undergoing layout mapping structural validation.");
        }
      } catch (err) {
        console.error("Failed to load curriculum tree navigation structure:", err);
        setCurriculumTree([]); // Reset to empty array to prevent rendering maps from throwing errors
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCurriculumTree();
  }, [subject]);

  return (
    <div className="flex flex-col md:flex-row flex-grow min-h-[calc(100vh-73px)] bg-slate-950 text-white">
      {/* Left Sidebar Pane: Navigation Architecture Tree */}
      <div className="w-full md:w-80 border-r border-slate-900 bg-slate-950 p-6 flex flex-col shrink-0">
        <div className="flex items-center gap-3 mb-6">
          <button 
            onClick={onBack}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
          </button>
          <div>
            <h4 className="font-bold text-sm tracking-tight text-slate-200 line-clamp-1">
              {subject?.name || "Course Subject"}
            </h4>
            <p className="text-[10px] font-mono uppercase tracking-widest text-emerald-500 font-bold mt-0.5">
              Curriculum Tree
            </p>
          </div>
        </div>

        {/* Dynamic Tree Loading Engine States */}
        {loading ? (
          <div className="flex-grow flex flex-col items-center justify-center gap-2 py-12">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-emerald-500"></div>
            <p className="text-[11px] font-mono text-slate-500 uppercase tracking-wider">Parsing Tree Hierarchy...</p>
          </div>
        ) : error ? (
          <div className="flex-grow flex flex-col items-center justify-center text-center p-4 border border-dashed border-slate-900 rounded-xl bg-slate-900/10 py-8">
            <div className="w-8 h-8 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-400 mb-2 font-bold font-mono text-xs">!</div>
            <p className="text-xs font-medium text-slate-400 max-w-[200px] leading-relaxed">
              {error.includes("404") ? "This competitive exam module is awaiting configuration mapping on your FastAPI server." : error}
            </p>
          </div>
        ) : curriculumTree.length === 0 ? (
          <div className="flex-grow flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-900 rounded-xl py-12">
            <p className="text-xs text-slate-500">No core instructional branches maps populated for this topic framework matrix.</p>
          </div>
        ) : (
          <div className="flex-grow overflow-y-auto space-y-4 pr-1 custom-scrollbar">
            {/* Safe array render loop */}
            {curriculumTree.map((unit, uIdx) => (
              <div key={unit.id || uIdx} className="space-y-1">
                <h5 className="text-xs font-black font-mono text-slate-500 uppercase tracking-wider px-2 py-1">
                  Unit {uIdx + 1}: {unit.name}
                </h5>
                
                {Array.isArray(unit.topics) && unit.topics.map((topic, tIdx) => (
                  <div key={topic.id || tIdx} className="pl-2 space-y-0.5">
                    <div className="text-xs font-bold text-slate-400 px-2 py-1 flex items-center gap-1.5">
                      <span className="w-1 h-1 rounded-full bg-slate-700"></span>
                      {topic.name}
                    </div>

                    {Array.isArray(topic.chapters) && topic.chapters.map((chapter) => (
                      <button
                        key={chapter.id}
                        onClick={() => setSelectedChapter(chapter)}
                        className={`w-full text-left text-xs px-3 py-2 rounded-lg transition-all duration-200 flex items-center justify-between group ${
                          selectedChapter?.id === chapter.id
                            ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold'
                            : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200 border border-transparent'
                        }`}
                      >
                        <span className="truncate pr-2">{chapter.name}</span>
                        <svg 
                          className={`w-3 h-3 shrink-0 opacity-0 group-hover:opacity-100 transition-all ${selectedChapter?.id === chapter.id ? 'opacity-100 text-emerald-400' : 'text-slate-500'}`} 
                          fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right Content Presentation Window Area Workspace */}
      <div className="flex-grow bg-slate-950 flex flex-col p-8 items-center justify-center min-h-[50vh]">
        {selectedChapter ? (
          <div className="max-w-4xl w-full space-y-6 animate-fadeIn">
            <div>
              <span className="text-[10px] font-mono font-black tracking-widest px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                Active Chapter Workspace
              </span>
              <h2 className="text-3xl font-black tracking-tight text-white mt-2">
                {selectedChapter.name}
              </h2>
            </div>
            
            {/* Media Canvas Deck Frame Placeholder */}
            <div className="aspect-video w-full bg-slate-900 rounded-2xl border border-slate-800 shadow-2xl flex flex-col items-center justify-center p-8 group relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-transparent"></div>
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3 shadow-lg group-hover:scale-115 transition-transform duration-300">
                <svg className="w-6 h-6 translate-x-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </div>
              <p className="text-sm font-bold text-slate-300 tracking-wide text-center">
                10-Second Visual Concept Presenter Deck
              </p>
              <p className="text-xs text-slate-500 font-mono mt-1 text-center">
                Asset Target Reference: {selectedChapter.video_url || "Core-Curriculum-Default-Placeholder.mp4"}
              </p>
            </div>
          </div>
        ) : (
          <div className="text-center space-y-2 border border-slate-900/60 rounded-3xl p-12 bg-slate-900/10 max-w-sm">
            <div className="text-2xl mb-2">🧭</div>
            <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wide">Select Learning Anchor</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Choose an available chapter from the curriculum tree array node selection column sidebar to start running interactive AI visualizations.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CourseReader;