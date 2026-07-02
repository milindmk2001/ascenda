import React, { useState, useEffect, useMemo, useRef } from 'react';
import VisualRenderer from './VisualRenderer';
import { AnimationController } from '../utils/AnimationController';
import { SceneExecutor } from '../utils/SceneExecutor';
import { NarrationPlayer } from '../utils/NarrationPlayer';

export default function VisualLesson({ lessonPayload, onFinished }) {
  const executor = useMemo(() => new SceneExecutor(lessonPayload), [lessonPayload]);
  const player = useMemo(() => new NarrationPlayer(), []);
  
  const [currentSceneId, setCurrentSceneId] = useState(() => executor.getInitialScene());
  const [studentAnswer, setStudentAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const [hintCount, setHintCount] = useState(0);
  const [score, setScore] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [customResponse, setCustomResponse] = useState("");
  const [customQuestion, setCustomQuestion] = useState("");
  const [tutorLoading, setTutorLoading] = useState(false);

  const svgHostRef = useRef(null);
  const animator = useRef(null);

  const slide = useMemo(() => executor.getSlide(currentSceneId), [currentSceneId, executor]);

  useEffect(() => {
    if (lessonPayload.schemaVersion !== '1.0') {
      console.warn(`Version mismatch: Expected 1.0, got ${lessonPayload.schemaVersion}`);
    }
    animator.current = new AnimationController(svgHostRef);
    return () => {
      player.stop();
      if (animator.current) animator.current.clear();
    };
  }, [lessonPayload, player]);

  const runVisualTimeline = async () => {
    if (!slide || isAnimating) return;
    setIsAnimating(true);
    
    if (slide.animationTimeline) {
      await animator.current.runTimeline(slide.animationTimeline, (stepText) => {
        player.speak(stepText);
      });
    }
    
    setIsAnimating(false);
    if (slide.narration) {
      player.speak(slide.narration, () => {
        const next = executor.getNextSceneId(slide, "animation_complete");
        if (next) setCurrentSceneId(next);
      });
    }
  };

  useEffect(() => {
    runVisualTimeline();
  }, [currentSceneId, slide]);

  const handleSubmitAnswer = () => {
    if (!slide) return;
    const isCorrect = studentAnswer.trim().toLowerCase() === slide.answer?.toLowerCase();
    setTotalQuestions(p => p + 1);

    if (isCorrect) {
      setScore(p => p + 1);
      setFeedback("🎉 Correct! Fantastic tracking.");
      player.speak("Correct! Outstanding job.");
      
      if (slide.revealTarget) {
        const el = svgHostRef.current?.querySelector(`#${CSS.escape(slide.revealTarget)}`);
        if (el) el.style.opacity = "1";
      }
      
      setTimeout(() => {
        const next = executor.getNextSceneId(slide, "student_correct");
        if (next) navigateToScene(next);
      }, 1500);
    } else {
      const maxHints = lessonPayload.interactionPolicy?.maxHintsPerSlide || 2;
      if (hintCount < maxHints) {
        setHintCount(p => p + 1);
        setFeedback(`💡 Hint: ${slide.hint}`);
        player.speak(slide.hint);
        const next = executor.getNextSceneId(slide, "student_wrong");
        if (next) navigateToScene(next);
      } else {
        setFeedback(`Let's take a look at the solution together.`);
        const fallback = executor.getNextSceneId(slide, "max_attempts");
        if (fallback) navigateToScene(fallback);
      }
    }
  };

  const handleAskCustomQuestion = async () => {
    if (!customQuestion.trim()) return;
    setTutorLoading(true);
    try {
      const res = await fetch("https://ascenda-production.up.railway.app/api/visual-lesson/tutor-action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lessonId: lessonPayload.lessonId,
          slideId: currentSceneId,
          curriculumNodeId: lessonPayload.metadata?.curriculumNodeId,
          studentQuestion: customQuestion,
          currentState: { visibleElements: [], currentAnimationStep: 0, studentAnswer }
        })
      });
      const data = await res.json();
      setCustomResponse(data.narration);
      player.speak(data.narration);
    } catch (e) {
      console.error(e);
    } finally {
      setTutorLoading(false);
    }
  };

  const navigateToScene = (nextId) => {
    setFeedback("");
    setStudentAnswer("");
    setCustomResponse("");
    setCustomQuestion("");
    setHintCount(0);
    setCurrentSceneId(nextId);
  };

  if (slide?.sceneType === 'lesson_summary') {
    const finalRatio = score / (totalQuestions || 1);
    const passed = finalRatio >= (lessonPayload.masteryCriteria?.minimumScore || 0.7);
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-[#070b14] h-full">
        <h2 className="text-xl font-bold text-slate-200">Lesson Complete!</h2>
        <p className="text-sm text-slate-400 mt-2">Accuracy Matrix: {score} / {totalQuestions}</p>
        {passed ? (
          <p className="text-emerald-400 font-mono text-xs mt-4">🏆 Node Mastery Verified!</p>
        ) : (
          lessonPayload.assessmentPolicy?.allowRetry && (
            <button 
              onClick={() => navigateToScene(executor.getInitialScene())}
              className="mt-6 bg-emerald-500 text-slate-950 font-mono text-xs font-bold px-4 py-2 rounded"
            >
              Try Again
            </button>
          )
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-1 overflow-hidden bg-[#070b14] h-full w-full">
      <div className="flex-1 flex flex-col p-6 justify-between border-r border-slate-900">
        <h3 className="text-xs font-mono uppercase text-slate-500 tracking-wider">{slide?.title || "Explanation Stage"}</h3>
        <div className="flex-1 my-4">
          {slide?.svgCache && <VisualRenderer svgContent={slide.svgCache} hostRef={svgHostRef} />}
        </div>
        <div className="flex justify-between items-center bg-[#090f1c]/40 border border-slate-900 p-3 rounded-lg">
          <button onClick={runVisualTimeline} disabled={isAnimating} className="bg-slate-900 text-slate-300 font-mono text-xs px-4 py-2 border border-slate-800 rounded">
            {isAnimating ? "Playing..." : "🔄 Replay Animation"}
          </button>
          <div className="flex gap-2">
            <button onClick={() => { player.pause(); }} className="text-[11px] font-mono text-slate-600 hover:text-slate-400">Pause</button>
            <button onClick={() => { player.resume(); }} className="text-[11px] font-mono text-slate-600 hover:text-slate-400">Resume</button>
          </div>
        </div>
      </div>
      
      <aside className="w-[380px] p-6 bg-[#090f1c]/10 flex flex-col gap-6 overflow-y-auto">
        <div>
          <span className="text-[9px] font-mono text-emerald-400 tracking-widest uppercase font-black block mb-2">Tutor Narration</span>
          <div className="bg-[#090f1c] border border-slate-900 rounded-xl p-4 italic text-xs text-slate-300">
            "{slide?.narration || "Reviewing layout structure..."}"
          </div>
        </div>

        {slide?.question && (
          <div className="border-t border-slate-900 pt-4 space-y-3">
            <h4 className="text-xs font-bold font-mono text-slate-300">{slide.question}</h4>
            <input 
              type="text" 
              value={studentAnswer} 
              onChange={e => setStudentAnswer(e.target.value)}
              placeholder="Your answer..." 
              className="w-full bg-[#070b14] border border-slate-800 text-xs rounded p-2 text-slate-200 font-mono focus:outline-none focus:border-emerald-500/50"
            />
            <button onClick={handleSubmitAnswer} className="w-full bg-emerald-500 text-slate-950 font-bold font-mono text-xs py-2 rounded">Submit Answer</button>
            {feedback && <div className="p-3 bg-slate-900/40 border border-slate-900 rounded text-xs font-mono text-slate-400">{feedback}</div>}
          </div>
        )}

        <div className="border-t border-slate-900 pt-4 mt-auto space-y-2">
          <div className="flex gap-2">
            <input 
              type="text" 
              value={customQuestion} 
              onChange={e => setCustomQuestion(e.target.value)} 
              placeholder="Ask a question..." 
              className="flex-1 bg-[#070b14] border border-slate-800 text-xs rounded p-2 text-slate-200 font-mono focus:outline-none"
            />
            <button onClick={handleAskCustomQuestion} disabled={tutorLoading} className="bg-slate-900 text-slate-300 font-mono text-xs px-3 rounded border border-slate-800">{tutorLoading ? "..." : "Ask"}</button>
          </div>
          {customResponse && <p className="text-xs text-slate-400 bg-slate-950 p-2 rounded border border-slate-900 font-sans leading-relaxed">{customResponse}</p>}
        </div>
      </aside>
    </div>
  );
}