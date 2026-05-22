import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeReplayMath from 'rehype-katex';
import 'katex/dist/katex.min.css'; // Standard equations styling injection

export default function CourseReaderPanel({ activeLeafNodeId }) {
  const [content, setContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const abortControllerRef = useRef(null);

  useEffect(() => {
    if (activeLeafNodeId) {
      triggerExplanationStream(activeLeafNodeId);
    }
    return () => disconnectActiveStreams();
  }, [activeLeafNodeId]);

  const disconnectActiveStreams = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const triggerExplanationStream = async (leafNodeId) => {
    disconnectActiveStreams();
    setIsStreaming(true);
    setContent("");
    setErrorMessage("");

    abortControllerRef.current = new AbortController();

    try {
      // Points straight to Railway deployed production environment endpoints configuration matrix
      const response = await fetch(`https://ascenda-production.up.railway.app/api/explain/${leafNodeId}`, {
        method: 'POST',
        signal: abortControllerRef.current.signal,
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`Server returned error metrics: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || ""; // Retain incomplete chunk line parameters boundary markers

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const token = line.replace("data: ", "");
            if (token === "[DONE]") {
              setIsStreaming(false);
              return;
            }
            if (token.startsWith("[ERROR]")) {
              setErrorMessage(token);
              setIsStreaming(false);
              return;
            }
            setContent((prev) => prev + token);
          }
        }
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        setErrorMessage(`Stream network connection broken: ${error.message}`);
        setIsStreaming(false);
      }
    }
  };

  const handleForceRegenerateCache = async () => {
    if (!activeLeafNodeId) return;
    try {
      setIsStreaming(true);
      await fetch(`https://ascenda-production.up.railway.app/api/explain/${activeLeafNodeId}/cache`, {
        method: 'DELETE'
      });
      triggerExplanationStream(activeLeafNodeId);
    } catch (err) {
      setErrorMessage(`Failed to clear structural storage cache tokens: ${err.message}`);
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 text-slate-100 font-sans border-l border-slate-800 shadow-2xl overflow-hidden relative">
      {/* Dynamic Header Toolbar Operations Block */}
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60 backdrop-blur-md sticky top-0 z-10">
        <div>
          <h3 className="text-base font-semibold tracking-wide text-indigo-400">Core Concept Deep Dive</h3>
          <p className="text-xs text-slate-400">Interactive Socratic Intuition Sandbox Engine</p>
        </div>
        {activeLeafNodeId && (
          <button
            onClick={handleForceRegenerateCache}
            disabled={isStreaming}
            className="px-3 py-1.5 rounded-md bg-slate-800 text-xs font-medium text-slate-300 hover:bg-slate-700 transition duration-150 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 border border-slate-700"
          >
            🔄 Clear Cache & Regenerate
          </button>
        )}
      </div>

      {/* Primary Rendering Stream Content Stage Container */}
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6 leading-relaxed selection:bg-indigo-500/30 scroll-smooth">
        {errorMessage && (
          <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 text-sm font-medium">
            ⚠️ {errorMessage}
          </div>
        )}

        <div className="prose prose-invert max-w-none prose-p:text-slate-300 prose-headings:text-slate-100 prose-strong:text-indigo-400 prose-code:text-emerald-400 text-sm md:text-base">
          <ReactMarkdown 
            remarkPlugins={[remarkMath]} 
            rehypePlugins={[rehypeReplayMath]}
          >
            {content}
          </ReactMarkdown>
        </div>

        {/* Dynamic Streaming Footprint Indicators Layout */}
        {isStreaming && (
          <div className="flex items-center gap-2.5 text-xs text-indigo-400 font-medium py-2 bg-slate-900/40">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            Synthesizing concepts, grounding equations context...
          </div>
        )}
      </div>

      {/* Compliance Attribution Status Footer Anchor */}
      <div className="px-6 py-2.5 border-t border-slate-800/60 bg-slate-950/80 text-[11px] text-slate-500 flex items-center justify-between tracking-wide font-mono">
        <span>PLATFORM ID: {activeLeafNodeId || "UNSELECTED"}</span>
        <span className="text-slate-400 font-sans">⚡ Powered by Gemini 2.0 Flash Engine</span>
      </div>
    </div>
  );
}