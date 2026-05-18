import React, { useState, useEffect } from 'react';

const API_BASE = "https://ascenda-production.up.railway.app";

// Helper components for UI layout rendering icons cleanly
const ChevronIcon = ({ isOpen }) => (
  <svg 
    className={`w-3.5 h-3.5 text-slate-500 transition-transform duration-200 shrink-0 ${isOpen ? 'rotate-90 text-emerald-400' : ''}`} 
    fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3"
  >
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
  </svg>
);

const LeafIcon = ({ type }) => {
  switch (type) {
    case 'concept': return <span className="text-sm shrink-0 select-none">📖</span>;
    case 'solved_problems': return <span className="text-sm shrink-0 select-none">✅</span>;
    case 'unsolved_problems': return <span className="text-sm shrink-0 select-none">📝</span>;
    case 'concept_test': return <span className="text-sm shrink-0 select-none">🧪</span>;
    default: return <span className="text-sm shrink-0 select-none">📄</span>;
  }
};

const CourseReader = ({ subject, onBack }) => {
  const [curriculumTree, setCurriculumTree] = useState(null);
  const [treeLoading, setTreeLoading] = useState(true);
  const [treeError, setTreeError] = useState(null);

  // Layout expansion states tracking open folders/units
  const [expandedUnits, setExpandedUnits] = useState({});
  const [expandedTopics, setExpandedTopics] = useState({});
  const [selectedLeafId, setSelectedLeafId] = useState(null);

  // Content Canvas Engine panel render states
  const [canvasLoading, setCanvasLoading] = useState(false);
  const [activeContent, setActiveContent] = useState(null);

  // Lifecycle Initialization Layer: Fetch full curriculum tree structure
  useEffect(() => {
    const fetchTreeData = async () => {
      // Safely default down to path slugs if data items lack custom keys
      const subjectSlug = subject?.name?.toLowerCase() || "physics";
      
      try {
        setTreeLoading(true);
        setTreeError(null);
        
        const response = await fetch(`${API_BASE}/api/curriculum/iitjee/${subjectSlug}`);
        if (!response.ok) {
          throw new Error(`Data transmission failed with status index code: ${response.status}`);
        }
        
        const data = await response.json();
        setCurriculumTree(data);
      } catch (err) {
        console.error("Critical error parsing curriculum system matrix:", err);
        setTreeError(err.message);
      } finally {
        setTreeLoading(false);
      }
    };

    fetchTreeData();
  }, [subject]);

  // Action Click Handler: Manages leaf selections and API content fetching
  const handleLeafSelect = async (leaf, topicTitle, unitTitle) => {
    setSelectedLeafId(leaf.id);
    
    // Construct core contextual payload to emit upward if required
    const trackingPayload = {
      leaf_id: leaf.id,
      content_type: leaf.content_type,
      content_id: leaf.content_id,
      topic: topicTitle,
      unit: unitTitle
    };
    
    console.log("Emitting Active Content Anchor Context Portfolio:", trackingPayload);

    // Context execution guard: Check if content payload exists in structural dictionary
    if (!leaf.content_id) {
      setActiveContent(null); // Displays placeholder panel for unsolved problems/tests
      return;
    }

    try {
      setCanvasLoading(true);
      const res = await fetch(`${API_BASE}/api/content/${leaf.content_id}`);
      if (!res.ok) {
        throw new Error("Unable to recover downstream database structural text assets.");
      }
      const data = await res.json();
      setActiveContent(data);
    } catch (err) {
      console.error("Content payload collection error:", err);
      setActiveContent({
        content: `### Connection Error\nCould not resolve content payload definitions: ${err.message}`,
        content_type: leaf.content_type,
        topic: topicTitle,
        unit: unitTitle
      });
    } finally {
      setCanvasLoading(false);
    }
  };

  const toggleUnit = (id) => {
    setExpandedUnits(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleTopic = (id) => {
    setExpandedTopics(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="flex flex-col md:flex-row flex-grow min-h-[calc(100vh-73px)] bg-[#0a0f1e] text-white overflow-hidden">
      
      {/* ────────────────────────────────────────────────────────
          LEFT PANEL: COLLAPSIBLE CURRICULUM STRUCTURAL TREE
          ──────────────────────────────────────────────────────── */}
      <div className="w-full md:w-85 border-r border-slate-900 bg-[#0a0f1e] p-5 flex flex-col shrink-0 select-none overflow-y-auto custom-scrollbar">
        
        {/* Navigation Context Card Block */}
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-900/60">
          <button 
            onClick={onBack}
            className="p-2 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-all duration-200"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
          </button>
          <div>
            <h4 className="font-black text-sm tracking-tight text-slate-100 uppercase">
              {curriculumTree?.subject || subject?.name || "Physics"}
            </h4>
            <p className="text-[10px] font-mono uppercase tracking-widest text-emerald-500 font-bold">
              {curriculumTree?.exam_type || "IITJEE"} Core Syllabus
            </p>
          </div>
        </div>

        {/* Dynamic Tree Loading Engine States */}
        {treeLoading ? (
          <div className="flex-grow flex flex-col items-center justify-center gap-2 py-20">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-emerald-500"></div>
            <p className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">Parsing Core Tree branches...</p>
          </div>
        ) : treeError ? (
          <div className="p-4 border border-dashed border-red-900/40 rounded-xl bg-red-950/10 text-center py-8">
            <p className="text-xs font-mono text-red-400 leading-relaxed">System Sync Fault: {treeError}</p>
          </div>
        ) : !curriculumTree || !curriculumTree.units || curriculumTree.units.length === 0 ? (
          <div className="text-center p-6 border border-dashed border-slate-900 rounded-xl py-12">
            <p className="text-xs text-slate-500 font-mono">No mapped syllabus branches detected.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {curriculumTree.units.map((unit) => {
              const isUnitOpen = !!expandedUnits[unit.id];
              return (
                <div key={unit.id} className="border border-slate-900/30 rounded-xl overflow-hidden bg-slate-900/5">
                  
                  {/* LEVEL 1: UNIT HEADER CARD */}
                  <div 
                    onClick={() => toggleUnit(unit.id)}
                    className={`flex items-center gap-2.5 px-3 py-3 cursor-pointer transition-colors duration-200 rounded-xl ${
                      isUnitOpen ? 'bg-slate-900/60 text-white' : 'hover:bg-slate-900/30 text-slate-300'
                    }`}
                  >
                    <ChevronIcon isOpen={isUnitOpen} />
                    <span className="text-xs font-bold tracking-tight text-left leading-tight">
                      {unit.title}
                    </span>
                  </div>

                  {/* LEVEL 2: TOPICS INTERMEDIARY LIST */}
                  {isUnitOpen && (
                    <div className="pl-4 pr-1 py-1 bg-slate-950/40 border-t border-slate-900/40 space-y-1">
                      {unit.topics && unit.topics.map((topic) => {
                        const isTopicOpen = !!expandedTopics[topic.id];
                        return (
                          <div key={topic.id} className="space-y-0.5">
                            
                            <div 
                              onClick={() => toggleTopic(topic.id)}
                              className={`flex items-center gap-2 px-2.5 py-2 cursor-pointer rounded-lg transition-colors duration-150 ${
                                isTopicOpen ? 'text-slate-100 font-semibold' : 'text-slate-400 hover:bg-slate-900/40 hover:text-slate-200'
                              }`}
                            >
                              <ChevronIcon isOpen={isTopicOpen} />
                              <span className="text-xs truncate">{topic.title}</span>
                            </div>

                            {/* LEVEL 3: ACTIVE LEAF CLUSTERS */}
                            {isTopicOpen && (
                              <div className="pl-5 pr-1 py-0.5 space-y-0.5 border-l border-slate-900 ml-4">
                                {topic.leaves && topic.leaves.map((leaf) => {
                                  const isSelected = selectedLeafId === leaf.id;
                                  return (
                                    <button
                                      key={leaf.id}
                                      onClick={() => handleLeafSelect(leaf, topic.title, unit.title)}
                                      className={`w-full flex items-center gap-2.5 text-left text-xs px-3 py-2 rounded-lg transition-all duration-150 group ${
                                        isSelected
                                          ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold shadow-inner shadow-emerald-500/5'
                                          : 'text-slate-400 hover:bg-slate-900/50 hover:text-slate-200 border border-transparent'
                                      }`}
                                    >
                                      <LeafIcon type={leaf.content_type} />
                                      <span className="truncate flex-grow">{leaf.title}</span>
                                      
                                      {leaf.content_id && (
                                        <span className={`text-[9px] font-mono uppercase px-1 rounded scale-90 tracking-wider font-bold ${
                                          isSelected ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-900 text-slate-500 group-hover:text-slate-400'
                                        }`}>
                                          Data
                                        </span>
                                      )}
                                    </button>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        );
                      })}
                      {(!unit.topics || unit.topics.length === 0) && (
                        <div className="text-[11px] font-mono text-slate-600 p-2 italic">No topics structural tags loaded.</div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ────────────────────────────────────────────────────────
          RIGHT PANEL: THE CORE DISPLAY CONTENT WORKSPACE CANVAS
          ──────────────────────────────────────────────────────── */}
      <div className="flex-grow bg-[#050814] flex flex-col p-6 md:p-10 overflow-y-auto custom-scrollbar">
        {canvasLoading ? (
          <div className="flex-grow flex flex-col items-center justify-center gap-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
            <p className="text-xs font-mono text-slate-500 uppercase tracking-widest animate-pulse">
              Pulling Core Asset Vectors from Supabase...
            </p>
          </div>
        ) : activeContent ? (
          <div className="max-w-4xl w-full mx-auto space-y-6 animate-fadeIn">
            {/* Breadcrumb Context Path Indicator */}
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-[10px] font-mono font-black tracking-widest text-slate-500 uppercase">
                <span className="truncate max-w-[180px]">{activeContent.unit}</span>
                <span>//</span>
                <span className="text-slate-400 truncate max-w-[200px]">{activeContent.topic}</span>
              </div>
              <h1 className="text-2xl md:text-3xl font-black tracking-tight text-white mt-1">
                {activeContent.content_type === 'concept' ? 'Concept Theory Workbook' : 'Solved Problem Matrix'}
              </h1>
            </div>

            {/* Content Display Panel Layout Container */}
            <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-6 md:p-8 min-h-[50vh] shadow-xl">
              {/* Preserves formatting arrays cleanly */}
              <p className="text-slate-300 text-sm md:text-base leading-relaxed whitespace-pre-wrap font-sans">
                {activeContent.content}
              </p>
            </div>
            
            {/* 10-Second Code Animation Video Placeholder Anchor Frame */}
            <div className="aspect-video w-full bg-slate-950 border border-slate-900 rounded-2xl flex flex-col items-center justify-center relative overflow-hidden group shadow-inner">
              <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/5 via-transparent to-transparent"></div>
              <div className="w-11 h-11 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20 mb-2 group-hover:scale-105 transition-transform duration-300">
                <svg className="w-5 h-5 translate-x-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </div>
              <span className="text-xs font-bold text-slate-400 tracking-wide">10-Sec Core Micro-Animation Presenter Canvas</span>
              <span className="text-[10px] font-mono text-slate-600 mt-0.5">Asset Reference Key: Active Frame Context Loaded</span>
            </div>
          </div>
        ) : (
          /* DEFAULT BLANK VIEW SCREEN: INITIAL WATERMARK PLACEHOLDER STATE */
          <div className="flex-grow flex flex-col items-center justify-center text-center max-w-sm mx-auto select-none">
            <div className="w-16 h-16 rounded-3xl bg-slate-900/50 border border-slate-800/80 flex items-center justify-center text-3xl mb-4 shadow-xl">
              🧭
            </div>
            <h3 className="font-black text-xs text-slate-300 uppercase tracking-widest font-mono">
              SELECT LEARNING ANCHOR
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed mt-2">
              Choose an structural node item branch from the sidebar index panel workspace to compile live text vectors and interactive video modules.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CourseReader;