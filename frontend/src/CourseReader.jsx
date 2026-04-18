import React, { useState, useEffect } from 'react';

const CourseReader = ({ subject, onBack }) => {
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [content, setContent] = useState("");
  const [loadingContent, setLoadingContent] = useState(false);
  const [completedTopics, setCompletedTopics] = useState([]);

  // Fetch AI content when a topic is selected
  useEffect(() => {
    if (!selectedTopic) return;

    const fetchAIContent = async () => {
      setLoadingContent(true);
      try {
        const response = await fetch(`https://ascenda-production.up.railway.app/api/content/fetch/${selectedTopic.id}`);
        if (response.ok) {
          const data = await response.json();
          setContent(data.body);
          // Mark as "In Progress" if not already completed
          if (!completedTopics.includes(selectedTopic.id)) {
            // Future logic: setProgress(selectedTopic.id, 'reading')
          }
        } else {
          setContent("### Content is on the way!\n\nOur AI Architect is currently drafting this specific lesson. Please check back in a few hours.");
        }
      } catch (err) {
        setContent("Unable to connect to the Content Repository. Please check your internet connection.");
      } finally {
        setLoadingContent(false);
      }
    };

    fetchAIContent();
  }, [selectedTopic]);

  const toggleComplete = (topicId) => {
    setCompletedTopics(prev => 
      prev.includes(topicId) ? prev.filter(id => id !== topicId) : [...prev, topicId]
    );
  };

  return (
    <div className="flex h-screen bg-slate-950 text-white overflow-hidden font-sans">
      {/* LEFT SIDEBAR: Table of Contents */}
      <aside className="w-80 border-r border-slate-800 bg-slate-900/30 flex flex-col">
        <div className="p-6 border-b border-slate-800 bg-slate-950">
          <button onClick={onBack} className="text-[10px] font-bold text-slate-500 hover:text-indigo-400 mb-4 uppercase tracking-[0.2em] transition-colors">
            ← Back to Architect
          </button>
          <h2 className="text-xl font-black text-white tracking-tight">{subject.name}</h2>
          <div className="mt-2 h-1 w-12 bg-indigo-500 rounded-full"></div>
        </div>
        
        <nav className="flex-grow overflow-y-auto p-4 space-y-1 custom-scrollbar">
          {subject.topics?.map((topic) => (
            <div key={topic.id} className="group flex items-center gap-2">
              <button
                onClick={() => setSelectedTopic(topic)}
                className={`flex-grow text-left p-3 rounded-xl transition-all text-sm font-medium ${
                  selectedTopic?.id === topic.id 
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' 
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                }`}
              >
                {topic.title}
              </button>
              {/* Status Indicator */}
              <button 
                onClick={() => toggleComplete(topic.id)}
                className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                  completedTopics.includes(topic.id) 
                    ? 'bg-emerald-500 border-emerald-500' 
                    : 'border-slate-700 group-hover:border-slate-500'
                }`}
              >
                {completedTopics.includes(topic.id) && <span className="text-[10px]">✓</span>}
              </button>
            </div>
          ))}
          {!subject.topics?.length && (
            <div className="p-8 text-center text-slate-600 text-sm italic">
              No modules indexed yet.
            </div>
          )}
        </nav>
      </aside>

      {/* RIGHT CONTENT PANEL */}
      <main className="flex-grow overflow-y-auto bg-slate-950 p-8 md:p-16 custom-scrollbar">
        <div className="max-w-3xl mx-auto">
          {selectedTopic ? (
            <div className={`transition-all duration-500 ${loadingContent ? 'opacity-30 translate-y-2' : 'opacity-100 translate-y-0'}`}>
              <div className="flex justify-between items-start mb-8">
                 <div>
                    <span className="text-xs font-bold text-indigo-500 uppercase tracking-widest">Current Module</span>
                    <h1 className="text-4xl font-black mt-2 leading-tight">{selectedTopic.title}</h1>
                 </div>
                 <div className="bg-slate-900 border border-slate-800 px-4 py-2 rounded-lg text-[10px] font-mono text-slate-500">
                    ID: {selectedTopic.id}
                 </div>
              </div>

              {/* LESSON CONTENT AREA */}
              <div className="prose prose-invert prose-indigo max-w-none text-slate-300 leading-relaxed text-lg space-y-6">
                {/* Rendering raw content - Integration with ReactMarkdown recommended later */}
                <div className="whitespace-pre-wrap font-light">
                  {content}
                </div>
              </div>

              {/* Completion Action */}
              {!completedTopics.includes(selectedTopic.id) && !loadingContent && content && (
                <div className="mt-16 pt-8 border-t border-slate-800">
                  <button 
                    onClick={() => toggleComplete(selectedTopic.id)}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-4 rounded-xl font-bold transition-all shadow-lg shadow-emerald-500/10"
                  >
                    Mark as Completed
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-6 animate-in fade-in zoom-in duration-700">
              <div className="w-24 h-24 bg-indigo-500/10 rounded-3xl flex items-center justify-center text-4xl border border-indigo-500/20">
                📖
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white mb-2">Select a Topic</h3>
                <p className="text-slate-500 max-w-sm">Choose a module from the sidebar to begin your {subject.name} training session.</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default CourseReader;