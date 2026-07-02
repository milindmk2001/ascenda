import React from 'react';

export default function CanvasUiSample() {
  // Mock data representing a typical active state inside the application
  const mockSlide = {
    title: "SPOTTING SIMPLE PATTERNS",
    slideIndex: 0,
    totalSlides: 4,
  };

  return (
    <div className="w-full max-w-3xl mx-auto p-6 bg-[#0d1527] rounded-2xl border border-slate-900 shadow-2xl">
      <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-2">
        Preview Workspace Frame
      </div>

      {/* --- THE ARTIFICIAL APP CANVAS INNER WRAPPER --- */}
      <div className="w-full min-h-[360px] bg-white rounded-xl shadow-inner relative overflow-hidden border border-slate-200 flex flex-col justify-between">
        
        {/* FIX 1: THE FLOATING HEADER — Pinned absolutely to the top edge inside the canvas boundaries */}
        <div className="absolute top-0 left-0 right-0 bg-slate-950/90 backdrop-blur border-b border-slate-800 px-4 py-2.5 flex items-center justify-between z-10">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-mono font-black uppercase tracking-wider text-emerald-400">
              {mockSlide.title}
            </span>
          </div>
          <span className="text-[9px] font-mono uppercase bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700/60">
            Interactive Node
          </span>
        </div>

        {/* COMPONENT BODY: Where your dynamic custom SVG injection content executes safely */}
        <div className="flex-1 pt-14 pb-10 flex flex-col items-center justify-center p-6 text-center">
          {/* Simulated SVG Graphic Asset Elements */}
          <div className="space-y-4">
            <div className="flex justify-center items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold text-sm shadow">5</div>
              <span className="text-slate-400 font-bold">➔</span>
              <div className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold text-sm shadow">10</div>
              <span className="text-slate-400 font-bold">➔</span>
              <div className="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center text-slate-400 font-bold text-sm border border-dashed border-slate-300">?</div>
            </div>
            <p className="text-xs text-slate-400 font-medium font-sans">
              [Your vectorized dynamic content sits securely here in an isolated viewing track]
            </p>
          </div>
        </div>

        {/* FIX 8: SLIDE PROGRESS BAR TRACKER — Anchored directly across the base coordinates */}
        <div className="absolute bottom-0 left-0 right-0 bg-slate-950/95 border-t border-slate-800/80 px-4 py-2 flex items-center gap-4 z-10">
          <span className="text-[10px] font-mono tracking-mono text-slate-400 font-bold whitespace-nowrap">
            Slide {mockSlide.slideIndex + 1} of {mockSlide.totalSlides}
          </span>
          
          {/* Progress fill bar configuration container */}
          <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden relative">
            <div 
              className="absolute top-0 bottom-0 left-0 bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]"
              style={{ width: `${((mockSlide.slideIndex + 1) / mockSlide.totalSlides) * 100}%` }}
            />
          </div>
        </div>

      </div>

      {/* Bottom Workspace System Controls Deck Wrapper */}
      <div className="mt-4 flex items-center justify-between text-[11px] font-mono text-slate-500">
        <span>Framework Context: v1 Engine Active</span>
        <span>Aesthetic Tone: Unified App-Frame</span>
      </div>
    </div>
  );
}