// src/components/VisualLesson.jsx

import React, { useState, useEffect, useRef } from 'react';

export default function VisualLesson({ lessonPayload }) {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [feedback, setFeedback] = useState(null);
  const svgContainerRef = useRef(null);

  const slides = lessonPayload?.slides || [];
  const currentSlide = slides[currentSlideIndex];

  // Force-reset visibility on diagram SVG target elements on slide mounts/transitions
  useEffect(() => {
    if (!svgContainerRef.current) return;

    const hiddenElements = svgContainerRef.current.querySelectorAll('[id]');
    hiddenElements.forEach((el) => {
      if (el.id !== 'answer_reveal') {
        el.style.opacity = '1';
        el.style.visibility = 'visible';
      }
    });
  }, [currentSlideIndex, lessonPayload]);

  if (!slides.length || !currentSlide) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 text-slate-500 font-mono text-xs">
        No visual slides available for this topic.
      </div>
    );
  }

  const rawSvg = currentSlide.svgCache || currentSlide.svgContent || currentSlide.svg || '';

  const handleNext = () => {
    if (currentSlideIndex < slides.length - 1) {
      setCurrentSlideIndex((prev) => prev + 1);
      setUserAnswer('');
      setFeedback(null);
    }
  };

  const handlePrev = () => {
    if (currentSlideIndex > 0) {
      setCurrentSlideIndex((prev) => prev - 1);
      setUserAnswer('');
      setFeedback(null);
    }
  };

  const handleCheckAnswer = (e) => {
    e.preventDefault();
    if (!userAnswer.trim()) return;

    const expectedAnswer = String(currentSlide.answer || '').trim();
    const isCorrect = userAnswer.trim().toLowerCase() === expectedAnswer.toLowerCase();

    if (isCorrect) {
      setFeedback({ success: true, message: 'Correct!' });
      // Reveal answer text element in the SVG if present
      if (svgContainerRef.current && currentSlide.revealTarget) {
        const revealEl = svgContainerRef.current.querySelector(`#${currentSlide.revealTarget}`);
        if (revealEl) {
          revealEl.style.opacity = '1';
          revealEl.style.visibility = 'visible';
        }
      }
    } else {
      setFeedback({ success: false, message: currentSlide.hint || 'Try again!' });
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top Header Controls */}
      <div className="flex items-center justify-between p-4 border-b border-slate-900 bg-slate-900/40">
        <div>
          <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-widest block">
            {lessonPayload.metadata?.topic || 'Visual Interactive Stage'}
          </span>
          <h2 className="text-sm font-bold text-slate-200">
            {currentSlide.title || `Slide ${currentSlideIndex + 1}`}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrev}
            disabled={currentSlideIndex === 0}
            className="px-3 py-1 bg-slate-900 border border-slate-800 rounded text-xs font-mono text-slate-300 disabled:opacity-40 hover:bg-slate-800 transition-colors"
          >
            ← Prev
          </button>
          <span className="text-xs font-mono text-slate-500">
            {currentSlideIndex + 1} / {slides.length}
          </span>
          <button
            onClick={handleNext}
            disabled={currentSlideIndex === slides.length - 1}
            className="px-3 py-1 bg-slate-900 border border-slate-800 rounded text-xs font-mono text-slate-300 disabled:opacity-40 hover:bg-slate-800 transition-colors"
          >
            Next →
          </button>
        </div>
      </div>

      {/* Main Interactive Stage */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 overflow-hidden">
        {/* Left / Top 2 Cols: SVG Visual Canvas */}
        <div className="md:col-span-2 flex items-center justify-center p-6 bg-black border-r border-slate-900 overflow-hidden">
          {rawSvg ? (
            <div
              ref={svgContainerRef}
              className="w-full h-full max-h-[480px] flex items-center justify-center [&>svg]:w-full [&>svg]:h-auto [&>svg]:max-h-[480px]"
              dangerouslySetInnerHTML={{ __html: rawSvg }}
            />
          ) : (
            <div className="text-xs font-mono text-slate-600">No visual element found</div>
          )}
        </div>

        {/* Right / Bottom Col: Narration & Interaction Sidebar */}
        <div className="flex flex-col justify-between p-6 bg-slate-950 overflow-y-auto border-t md:border-t-0 border-slate-900">
          <div>
            <div className="border-b border-slate-800 pb-2 mb-4">
              <span className="text-[10px] font-mono uppercase text-slate-500 tracking-widest">
                Explanation & Audio Narration
              </span>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed font-sans mb-6">
              {currentSlide.narration || currentSlide.question}
            </p>

            {/* Question Mode Input Section */}
            {currentSlide.sceneType === 'question' && (
              <div className="mt-4 p-4 rounded bg-slate-900/60 border border-slate-800">
                <p className="text-xs font-mono text-emerald-400 mb-2 font-bold">
                  {currentSlide.question}
                </p>
                <form onSubmit={handleCheckAnswer} className="space-y-3">
                  <input
                    type="text"
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    placeholder="Type answer..."
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-xs font-mono text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                  <button
                    type="submit"
                    className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-xs font-mono text-white transition-colors"
                  >
                    Submit Answer
                  </button>
                </form>

                {feedback && (
                  <div
                    className={`mt-3 p-2 rounded text-xs font-mono border ${
                      feedback.success
                        ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                        : 'bg-amber-950/40 border-amber-800 text-amber-300'
                    }`}
                  >
                    {feedback.message}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Navigation Footer Action */}
          <div className="pt-4 border-t border-slate-900">
            {currentSlideIndex < slides.length - 1 ? (
              <button
                onClick={handleNext}
                className="w-full py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded text-xs font-mono text-slate-300 transition-colors"
              >
                Continue Slide →
              </button>
            ) : (
              <div className="text-center text-xs font-mono text-emerald-400">
                Lesson Completed
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}