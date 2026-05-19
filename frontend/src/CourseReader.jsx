import React, { useState } from 'react';
import CurriculumPane from './CurriculumPane';

export default function CourseReader({ subject, onBack }) {
  const [selectedAnchor, setSelectedAnchor] = useState(null);
  const [contentPayload, setContentPayload] = useState('');
  const [loading, setLoading] = useState(false);

  // Extract metadata safely out of the subject node passed from App.jsx landing selections
  const subjectName = subject?.name || 'Physics';
  const subjectCode = subject?.subject_code || 'physics';
  
  // Parse active global tracks dynamically from metadata tags (e.g. "IITJEE-11" -> "IITJEE")
  const rawMetaTag = subject?.meta_tag || 'IITJEE';
  const examType = rawMetaTag.split('-')[0];

  const handleLeafSelection = async (anchorMeta) => {
    setSelectedAnchor(anchorMeta);
    setContentPayload('');

    // If content_id is null (Unsolved Problems / Concept Test), clear center view immediately
    if (!anchorMeta.content_id) {
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`https://ascenda-production.up.railway.app/api/curriculum/content/${anchorMeta.content_id}`);
      if (res.ok) {
        const data = await res.json();
        setContentPayload(data.content);
      } else {
        setContentPayload('⚠️ Error executing text content artifact call.');
      }
    } catch (err) {
      setContentPayload('⚠️ Connection timeout calling active gateway.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#0a0f1e] overflow-hidden flex-col">
      {/* Sub-Navigation Control Bar */}
      <div className="h-12 border-b border-slate-800/80 bg-[#0d1426] flex items-center px-4 justify-between flex-shrink-0">
        <button 
          onClick={onBack}
          className="text-xs text-slate-400 hover:text-white flex items-center space-x-1 font-medium transition-colors"
        >
          <span>← Back to Learning Hub</span>
        </button>
        <div className="text-xs font-bold text-slate-400 tracking-wide">
          Workspace Mode: <span className="text-teal-400">{subjectName}</span>
        </div>
      </div>

      {/* Main Core Screen Interface Grid Splits */}
      <div className="flex flex-1 overflow-hidden">
        {/* LEFT COMPONENT SIDEBAR */}
        <CurriculumPane 
          examType={examType} 
          subjectCode={subjectCode} 
          onLeafSelect={handleLeafSelection} 
        />

        {/* CENTER MAIN WORKSPACE CANVAS PANEL */}
        <div className="flex-1 h-full flex flex-col bg-[#070b16] text-white overflow-y-auto p-8">
          {!selectedAnchor ? (
            <div className="m-auto text-slate-600 tracking-wider text-xs font-bold select-none uppercase">
              SELECT LEARNING ANCHOR
            </div>
          ) : !selectedAnchor.content_id ? (
            <div className="m-auto flex flex-col items-center space-y-2 select-none">
              <div className="text-slate-600 tracking-wider text-xs font-bold uppercase">
                SELECT LEARNING ANCHOR
              </div>
              <p className="text-[11px] text-slate-500 max-w-xs text-center leading-relaxed">
                Target module placeholder link resolved. Live questions and runtime test search channels will connect in the next development sprint.
              </p>
            </div>
          ) : loading ? (
            <div className="m-auto text-xs text-slate-400 animate-pulse font-medium">
              Ingesting content asset matrix...
            </div>
          ) : (
            <div className="max-w-3xl mx-auto w-full space-y-4">
              {/* Context breadcrumb header location maps */}
              <div className="text-[10px] font-mono text-slate-500 uppercase border-b border-slate-800/40 pb-3">
                {selectedAnchor.unit} &gt; {selectedAnchor.topic}
              </div>
              <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wide text-teal-400 text-sm">
                {selectedAnchor.content_type.replace('_', ' ')}
              </h1>
              {/* Clean layout text content viewer frame */}
              <div className="text-sm text-slate-300 leading-relaxed font-normal whitespace-pre-wrap bg-[#0d1426] p-6 rounded-lg border border-slate-800/50">
                {contentPayload}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}