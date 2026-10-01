import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import VisualLesson from './components/VisualLesson';
import { syncLessonToStudio } from './services/api';

export default function ContentStudio() {
  const [nodeId, setNodeId] = useState('');
  const [title, setTitle] = useState('');
  const [jsonSpec, setJsonSpec] = useState('');
  const [markdownContent, setMarkdownContent] = useState('');
  const [mode, setMode] = useState('visual'); // 'visual' or 'markdown'
  const [statusMsg, setStatusMsg] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Parse JSON for live visual preview mode
  let parsedPayload = null;
  let jsonError = null;

  if (mode === 'visual' && jsonSpec.trim()) {
    try {
      parsedPayload = JSON.parse(jsonSpec);
    } catch (err) {
      jsonError = err.message;
    }
  }

  const handleSave = async (e) => {
    e.preventDefault();
    if (!nodeId.trim()) {
      setStatusMsg('Error: Node ID is required.');
      return;
    }

    setIsSaving(true);
    setStatusMsg('Syncing content to database...');

    const payload = {
      curriculum_node_id: nodeId,
      title,
      mode,
      payload: mode === 'visual' ? (parsedPayload || {}) : null,
      fallback_explanation: mode === 'markdown' ? markdownContent : null,
    };

    try {
      await syncLessonToStudio(payload);
      setStatusMsg('Lesson successfully saved to database.');
    } catch (err) {
      console.error('Save error:', err);
      setStatusMsg(`Error: ${err.message || 'Failed to sync content.'}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-64px)] w-full bg-slate-950 text-slate-100 overflow-hidden">
      {/* LEFT: Editor Panel */}
      <div className="w-1/2 flex flex-col border-r border-slate-900 p-6 overflow-y-auto">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-6">
          <h2 className="text-sm font-black font-mono uppercase text-slate-200">
            Content Authoring Studio
          </h2>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setMode('visual')}
              className={`px-3 py-1 text-xs font-mono rounded ${
                mode === 'visual'
                  ? 'bg-emerald-600 text-white font-bold'
                  : 'bg-slate-900 text-slate-400 hover:text-white'
              }`}
            >
              Visual Mode
            </button>
            <button
              type="button"
              onClick={() => setMode('markdown')}
              className={`px-3 py-1 text-xs font-mono rounded ${
                mode === 'markdown'
                  ? 'bg-blue-600 text-white font-bold'
                  : 'bg-slate-900 text-slate-400 hover:text-white'
              }`}
            >
              Markdown Mode
            </button>
          </div>
        </div>

        <form onSubmit={handleSave} className="flex-1 flex flex-col space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] font-mono text-slate-400 uppercase mb-1">
                Curriculum Node ID *
              </label>
              <input
                type="text"
                value={nodeId}
                onChange={(e) => setNodeId(e.target.value)}
                placeholder="e.g. leaf_snell_law_01"
                required
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded text-xs text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono text-slate-400 uppercase mb-1">
                Lesson Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Refraction & Snell's Law"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded text-xs text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {mode === 'visual' ? (
            <div className="flex-1 flex flex-col">
              <label className="block text-[10px] font-mono text-slate-400 uppercase mb-1">
                Visual Engine JSON Specification
              </label>
              <textarea
                value={jsonSpec}
                onChange={(e) => setJsonSpec(e.target.value)}
                placeholder='{ "canvas": { ... }, "elements": [ ... ] }'
                className="flex-1 w-full min-h-[300px] p-3 bg-slate-900 border border-slate-800 rounded text-xs text-slate-100 font-mono focus:outline-none focus:border-emerald-500 resize-none"
              />
              {jsonError && (
                <span className="text-[10px] font-mono text-red-400 mt-1">
                  JSON Parse Error: {jsonError}
                </span>
              )}
            </div>
          ) : (
            <div className="flex-1 flex flex-col">
              <label className="block text-[10px] font-mono text-slate-400 uppercase mb-1">
                Markdown Explanation
              </label>
              <textarea
                value={markdownContent}
                onChange={(e) => setMarkdownContent(e.target.value)}
                placeholder="Write lesson material with LaTeX support ($n_1 \sin \theta_1 = n_2 \sin \theta_2$)..."
                className="flex-1 w-full min-h-[300px] p-3 bg-slate-900 border border-slate-800 rounded text-xs text-slate-100 font-mono focus:outline-none focus:border-emerald-500 resize-none"
              />
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs font-mono text-slate-400">{statusMsg}</span>
            <button
              type="submit"
              disabled={isSaving}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-xs font-mono font-bold text-white rounded transition-colors"
            >
              {isSaving ? 'Syncing...' : 'Save to Studio'}
            </button>
          </div>
        </form>
      </div>

      {/* RIGHT: Live Preview Panel */}
      <div className="w-1/2 flex flex-col bg-slate-900/20 overflow-hidden">
        <div className="border-b border-slate-800 p-3 bg-slate-950">
          <span className="text-[10px] font-mono uppercase text-slate-500 tracking-widest">
            Live Preview Stage ({mode.toUpperCase()})
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {mode === 'visual' ? (
            parsedPayload ? (
              <VisualLesson lessonPayload={parsedPayload} />
            ) : (
              <div className="h-full flex items-center justify-center text-xs font-mono text-slate-600">
                Enter valid JSON specification to render live canvas preview.
              </div>
            )
          ) : (
            <div className="prose prose-invert max-w-none text-slate-300">
              <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                {markdownContent || '*Live Markdown preview will render here...*'}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}