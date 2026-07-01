import React, { useState } from 'react';

export default function LessonCanvas({ lessonPayload }) {
  const slides = lessonPayload?.slides || [];
  const [currentIdx, setCurrentIdx] = useState(0);

  if (slides.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 font-mono text-xs">
        No active visual sequences found inside this cache block.
      </div>
    );
  }

  const activeSlide = slides[currentIdx];

  const handleNext = () => {
    if (currentIdx < slides.length - 1) setCurrentIdx(currentIdx + 1);
  };

  const handlePrev = () => {
    if (currentIdx > 0) setCurrentIdx(currentIdx - 2);
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 p-4 rounded-xl border border-slate-800/60 shadow-2xl">
      {/* Canvas Top Bar Controls */}
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-3 mb-4">
        <div>
          <span className="text-[10px] font-mono bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded border border-purple-500/20 mr-2 uppercase tracking-wide">
            {activeSlide.title || "Interactive Concept"}
          </span>
          <span className="text-xs font-mono text-slate-400">
            Slide {currentIdx + 1} of {slides.length}
          </span>
        </div>
        
        {/* Navigation Arrows */}
        <div className="flex gap-2">
          <button
            onClick={handlePrev}
            disabled={currentIdx === 0}
            className="px-3 py-1 bg-slate-900 border border-slate-800 text-xs font-mono rounded hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 transition-all"
          >
            ◀ Prev
          </button>
          <button
            onClick={handleNext}
            disabled={currentIdx === slides.length - 1}
            className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono rounded hover:bg-emerald-500/20 disabled:opacity-40 disabled:hover:bg-emerald-500/10 transition-all"
          >
            Next ▶
          </button>
        </div>
      </div>

      {/* Main SVG Render Core */}
      <div className="flex-grow flex items-center justify-center bg-white rounded-lg p-6 min-h-[280px] shadow-inner overflow-hidden border border-slate-800">
        <div 
          className="w-full max-w-[480px] h-auto drop-shadow-md transition-all duration-300"
          dangerouslySetInnerHTML={{ __html: activeSlide.svg }} 
        />
      </div>

      {/* Academic Lesson Metadata Block */}
      <div className="mt-4 bg-slate-900/40 border border-slate-800/60 rounded-lg p-4 space-y-2">
        <p className="text-xs text-slate-300 leading-relaxed font-sans">
          <strong className="text-slate-400 font-mono text-[11px] block uppercase tracking-wider mb-0.5">Context Instruction:</strong>
          {activeSlide.narration}
        </p>
        <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-800/40 text-[11px] font-mono">
          <div>
            <span className="text-amber-400 block font-bold">💡 HINT:</span>
            <span className="text-slate-400">{activeSlide.hint}</span>
          </div>
          <div>
            <span className="text-blue-400 block font-bold">🎯 TARGET OBJECTIVE:</span>
            <span className="text-slate-400">{activeSlide.learningObjective}</span>
          </div>
        </div>
      </div>
    </div>
  );
}