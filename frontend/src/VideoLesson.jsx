import React, { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { interactWithVideoFrame } from './services/api';

export default function VideoLesson({ videoUrl }) {
  const videoRef = useRef(null);
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAskTutor = async (e) => {
    e.preventDefault();
    if (!query.trim() || !videoRef.current) return;

    const timestamp = videoRef.current.currentTime;
    setLoading(true);
    setResponse('');

    try {
      const data = await interactWithVideoFrame(timestamp, query);
      setResponse(data.explanation || data.response || 'No explanation generated.');
    } catch (err) {
      console.error('Video interaction error:', err);
      setResponse('*[Error connecting to Video AI Tutor service]*');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-64px)] w-full bg-slate-950 text-slate-100 overflow-hidden">
      {/* LEFT: Video Player */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 border-r border-slate-900 bg-black">
        <video
          ref={videoRef}
          controls
          className="w-full max-h-[70vh] rounded-lg shadow-2xl border border-slate-800"
          src={videoUrl}
        />
      </div>

      {/* RIGHT: Interactive AI Frame Panel */}
      <div className="w-96 flex flex-col bg-slate-950 p-4 border-l border-slate-900">
        <div className="border-b border-slate-800 pb-2 mb-4">
          <span className="text-[10px] font-mono uppercase text-emerald-400 tracking-widest">
            Video Frame AI Assistant
          </span>
        </div>

        {/* Response Box */}
        <div className="flex-1 overflow-y-auto mb-4 p-3 bg-slate-900/40 rounded border border-slate-800 text-slate-300 text-sm">
          {loading ? (
            <div className="text-xs font-mono text-emerald-400 animate-pulse">
              Analyzing video frame context...
            </div>
          ) : response ? (
            <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
              {response}
            </ReactMarkdown>
          ) : (
            <span className="text-xs font-mono text-slate-600">
              Pause the video at any point and ask a question about the current frame context.
            </span>
          )}
        </div>

        {/* Input Form */}
        <form onSubmit={handleAskTutor} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about this moment..."
            className="flex-1 px-3 py-2 bg-slate-900 border border-slate-800 rounded text-xs text-slate-100 focus:outline-none focus:border-emerald-500 font-mono"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded text-xs font-mono text-white transition-colors"
          >
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}