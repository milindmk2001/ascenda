import React, { useState, useEffect } from 'react';

// Map database content types to appropriate UI icons
const getLeafIcon = (type) => {
  switch (type) {
    case 'concept': return '📖';
    case 'solved_problems': return '✅';
    case 'unsolved_problems': return '📝';
    case 'concept_test': return '🧪';
    default: return '📄';
  }
};

export default function CurriculumPane({ examType = 'iitjee', subjectCode = 'physics', onLeafSelect }) {
  const [treeData, setTreeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [expandedUnits, setExpandedUnits] = useState({});
  const [expandedTopics, setExpandedTopics] = useState({});
  const [selectedLeafId, setSelectedLeafId] = useState(null);

  useEffect(() => {
    async function fetchCurriculum() {
      try {
        setLoading(true);
        // Normalize names to match backend expectations (e.g., IIT-JEE -> iitjee)
        const cleanExam = examType.toLowerCase().replace('-', '');
        const cleanSubject = subjectCode.toLowerCase();
        
        const response = await fetch(
          `https://ascenda-production.up.railway.app/api/curriculum/${cleanExam}/${cleanSubject}`
        );
        if (!response.ok) {
          throw new Error(`Server returned error status code: ${response.status}`);
        }
        const data = await response.json();
        setTreeData(data);
      } catch (err) {
        console.error("Failed fetching curriculum navigation map:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchCurriculum();
  }, [examType, subjectCode]);

  const toggleUnit = (id) => {
    setExpandedUnits(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleTopic = (id) => {
    setExpandedTopics(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleLeafClick = (leaf, topicTitle, unitTitle) => {
    setSelectedLeafId(leaf.id);
    if (onLeafSelect) {
      onLeafSelect({
        leaf_id: leaf.id,
        content_type: leaf.content_type,
        content_id: leaf.content_id,
        topic: topicTitle,
        unit: unitTitle
      });
    }
  };

  if (loading) {
    return (
      <div className="w-80 h-full bg-[#0a0f1e] text-slate-400 border-r border-slate-800/80 p-4 flex items-center justify-center text-sm font-medium flex-shrink-0">
        <div className="animate-pulse flex space-x-2">
          <div className="h-2 w-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="h-2 w-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="h-2 w-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    );
  }

  if (error || !treeData || !treeData.units || treeData.units.length === 0) {
    return (
      <div className="w-80 h-full bg-[#0a0f1e] text-slate-500 border-r border-slate-800/80 p-6 text-xs text-center select-none flex-shrink-0">
        This competitive exam module is awaiting configuration mapping on your FastAPI server.
      </div>
    );
  }

  return (
    <div className="w-80 h-full bg-[#0a0f1e] text-white border-r border-slate-800/80 flex flex-col select-none overflow-y-auto flex-shrink-0">
      {/* Header Metadata Title */}
      <div className="p-4 border-b border-slate-800/80 bg-[#0d1527]">
        <div className="text-[10px] uppercase tracking-widest font-black text-teal-400">{treeData.exam_type} Module</div>
        <h2 className="text-sm font-bold text-slate-200 mt-0.5">{treeData.subject} Core Directory</h2>
      </div>

      {/* Main Structural Navigation List */}
      <div className="flex-1 p-2 space-y-1 text-xs">
        {treeData.units.map((unit) => {
          const isUnitOpen = !!expandedUnits[unit.id];
          return (
            <div key={unit.id} className="rounded-md overflow-hidden">
              {/* LEVEL 1: UNIT HEADER */}
              <button
                onClick={() => toggleUnit(unit.id)}
                className="w-full text-left p-2.5 flex items-center justify-between hover:bg-[#121b30] transition-colors font-bold text-slate-200 bg-[#0d1426] border border-slate-800/40 rounded"
              >
                <span className="truncate pr-2 text-[12px]">{unit.title}</span>
                <span className="text-[10px] text-slate-500 font-mono">{isUnitOpen ? '▼' : '►'}</span>
              </button>

              {/* LEVEL 2: TOPICS CONTAINER */}
              {isUnitOpen && (
                <div className="mt-1 ml-2 pl-1 border-l border-slate-800/60 space-y-1">
                  {unit.topics.map((topic) => {
                    const isTopicOpen = !!expandedTopics[topic.id];
                    return (
                      <div key={topic.id}>
                        <button
                          onClick={() => toggleTopic(topic.id)}
                          className="w-full text-left p-2 flex items-center justify-between hover:bg-[#121b30] text-slate-300 rounded font-medium transition-colors"
                        >
                          <span className="truncate pr-2">{topic.title}</span>
                          <span className="text-[9px] text-slate-600 font-mono">{isTopicOpen ? '▼' : '►'}</span>
                        </button>

                        {/* LEVEL 3: CONTENT ACTION LEAVES */}
                        {isTopicOpen && (
                          <div className="mt-0.5 ml-3 pl-1 border-l border-slate-800/30 space-y-0.5">
                            {topic.leaves.map((leaf) => {
                              const isSelected = selectedLeafId === leaf.id;
                              return (
                                <button
                                  key={leaf.id}
                                  onClick={() => handleLeafClick(leaf, topic.title, unit.title)}
                                  className={`w-full text-left py-1.5 px-2.5 flex items-center space-x-2 rounded transition-all group duration-150 ${
                                    isSelected 
                                      ? 'bg-teal-500/10 text-teal-400 font-semibold border-l-2 border-teal-400 pl-2' 
                                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#11192c]'
                                  }`}
                                >
                                  <span className={`text-xs ${isSelected ? 'scale-110' : 'opacity-80 group-hover:opacity-100'}`}>
                                    {getLeafIcon(leaf.content_type)}
                                  </span>
                                  <span className="truncate">{leaf.title}</span>
                                </button>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}