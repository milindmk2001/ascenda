import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css'; // Enforce math equation styling

export default function CourseReader({ selectedLeafId }) {
  const [coreContent, setCoreContent] = useState('');
  const [aiExplanation, setAiExplanation] = useState('');
  const [loadingCore, setLoadingCore] = useState(false);
  const [loadingAI, setLoadingAI] = useState(false);
  const [error, setError] = useState(null);

  // Trigger content fetching whenever a new syllabus leaf node is clicked
  useEffect(() => {
    if (!selectedLeafId) return;
    
    // Reset reader panels
    setCoreContent('');
    setAiExplanation('');
    setError(null);
    setLoadingCore(true);

    // Fetch textbook core content
    fetch(`/api/curriculum/leaf/${selectedLeafId}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load textbook core lesson text.');
        return res.json();
      })
      .then((data) => {
        // Safe check for null/undefined content text fields
        setCoreContent(data?.content_text || '*No core text has been generated for this module yet.*');
        setLoadingCore(false);
        
        // Immediately kick off streaming the pedagogically configured AI Tutor Deep Dive
        triggerAiExplanation(selectedLeafId);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
        setLoadingCore(false);
      });
  }, [selectedLeafId]);

  // Handle server-side streaming chunk allocations
  const triggerAiExplanation = async (leafId) => {
    setLoadingAI(true);
    try {
      const response = await fetch('/api/ai_tutor/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ curriculum_tree_id: leafId }),
      });

      if (!response.ok) throw new Error('AI Tutor server endpoint unreachable.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          setAiExplanation((prev) => prev + chunk);
        }
      }
    } catch (err) {
      console.error(err);
      setAiExplanation('⚠️ *Could not establish connection stream with Ascenda AI Tutor.*');
    } finally {
      setLoadingAI(false);
    }
  };

  if (!selectedLeafId) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400 p-8">
        <p className="text-lg font-medium">Select a module topic folder on the left layout directory to start reading.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-950/40 border border-red-800 rounded-lg m-6 text-red-200">
        <h4 className="font-bold text-lg mb-1">Initialization Exception Encountered</h4>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row gap-6 p-6 h-full w-full overflow-hidden bg-slate-950 text-slate-100">
      
      {/* LEFT PANE: Core Textbook Lesson Material */}
      <div className="flex-1 bg-slate-900/50 border border-slate-800 rounded-xl p-6 overflow-y-auto max-h-[85vh]">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <span className="text-xs uppercase tracking-widest font-bold text-emerald-400">Standard Lesson Text</span>
          {loadingCore && <span className="text-xs text-slate-400 animate-pulse">Syncing...</span>}
        </div>
        
        <div className="prose prose-invert max-w-none text-slate-300 leading-relaxed space-y-4">
          {loadingCore ? (
            <div className="space-y-3">
              <div className="h-4 bg-slate-800 rounded w-3/4 animate-pulse"></div>
              <div className="h-4 bg-slate-800 rounded animate-pulse"></div>
              <div className="h-4 bg-slate-800 rounded w-5/6 animate-pulse"></div>
            </div>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
              {coreContent}
            </ReactMarkdown>
          )}
        </div>
      </div>

      {/* RIGHT PANE: Interactive Pedagogical AI Tutor Deep Dive */}
      <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl p-6 overflow-y-auto max-h-[85vh] shadow-2xl relative">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
            <span className="text-xs uppercase tracking-widest font-bold text-blue-400">Ascenda Socratic AI Tutor</span>
          </div>
          {loadingAI && <span className="text-xs text-blue-400 animate-pulse">Streaming Insights...</span>}
        </div>

        <div className="prose prose-invert max-w-none text-slate-200 leading-relaxed space-y-4 markdown-ai-zone">
          {aiExplanation ? (
            <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
              {aiExplanation}
            </ReactMarkdown>
          ) : loadingAI ? (
            <div className="space-y-4">
              <p className="text-sm text-slate-400 italic">Synthesizing textbook data with IITJEE target parameter mapping matrices...</p>
              <div className="space-y-2">
                <div className="h-3 bg-slate-800 rounded animate-pulse"></div>
                <div className="h-3 bg-slate-800 rounded w-5/6 animate-pulse"></div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500 italic">Waiting for textbook core mapping resolution to trigger tutor pipeline output.</p>
          )}
        </div>
      </div>

    </div>
  );
}