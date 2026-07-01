import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import LessonCanvas from './LessonCanvas'; // Custom slide interactive component template

const API_BASE = "https://ascenda-production.up.railway.app";

export default function CourseReader({ subject, onBack }) {
  const [treeNodes, setTreeNodes] = useState([]);
  const [selectedLeafId, setSelectedLeafId] = useState(null);
  const [coreContent, setCoreContent] = useState('');
  const [aiExplanation, setAiExplanation] = useState('');
  const [loadingTree, setLoadingTree] = useState(false);
  const [loadingCore, setLoadingCore] = useState(false);
  const [loadingAI, setLoadingAI] = useState(false);
  const [expandedNodes, setExpandedNodes] = useState({});
  const [visualLessonPayload, setVisualLessonPayload] = useState(null);

  // Step 1: Fetch the whole structural navigation tree for the current subject
  useEffect(() => {
    if (!subject?.id) return;
    
    setLoadingTree(true);
    fetch(`${API_BASE}/api/curriculum/subjects/${subject.id}/tree`)
      .then(res => {
        if (!res.ok) throw new Error("Server tree interface responded with an error status.");
        return res.json();
      })
      .then(data => {
        // Defensive Check: Ensure the data is strictly an array before modifying state
        if (Array.isArray(data)) {
          setTreeNodes(data);
        } else {
          console.error("Malformed payload received at Tree Endpoint. Expected Array:", data);
          setTreeNodes([]);
        }
        setLoadingTree(false);
      })
      .catch(err => {
        console.error("Error ingestion downstream tree:", err);
        setTreeNodes([]);
        setLoadingTree(false);
      });
  }, [subject]);

  // Step 2: Fetch specific unit content when a leaf node is selected
  useEffect(() => {
    if (!selectedLeafId) return;

    setCoreContent('');
    setAiExplanation('');
    setVisualLessonPayload(null);
    setLoadingCore(true);

    // 1. Check if a structured Visual SVG Lesson template exists for this concept node
    fetch(`${API_BASE}/api/visual-lesson/${selectedLeafId}`)
      .then(res => res.json())
      .then(visualData => {
        if (visualData.mode === "visual" && visualData.payload) {
          // Found a pre-constructed slide package! Save payload and flip the rendering mode flag
          console.log("Visual Asset Found:", visualData.payload);
          setVisualLessonPayload(visualData.payload);
          setCoreContent("VISUAL_MODE_ACTIVE"); 
          setLoadingCore(false);
        } else {
          // Fallback: No visual match found. Ingest the core markdown text block natively
          fetch(`${API_BASE}/api/curriculum/leaf/${selectedLeafId}`)
            .then(res => res.json())
            .then(data => {
              setCoreContent(data?.content_text || '*No core text module configured for this node yet.*');
              setLoadingCore(false);
            })
            .catch(err => {
              console.error("Error fetching text fallback:", err);
              setLoadingCore(false);
            });
        }
        
        // 2. Trigger the explanatory audio companion stream concurrently
        triggerAiStream(selectedLeafId);
      })
      .catch(err => {
        console.error("Visual check failed, dropping to text defaults:", err);
        setLoadingCore(false);
      });
  }, [selectedLeafId]);

  const triggerAiStream = async (leafId) => {
    setLoadingAI(true);
    try {
      const response = await fetch(`${API_BASE}/api/ai_tutor/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          leaf_id: leafId,
          subject_meta: subject?.meta_tag || "general"
        })
      });

      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Cancel any ongoing or leftover browser speech buffers before beginning a new lecture
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const token = decoder.decode(value, { stream: true });
        setAiExplanation(prev => prev + token);

        // Read out incoming chunk tokens immediately
        if ('speechSynthesis' in window) {
          // Clean out markdown markers and latex math syntax tags ($...$) so it reads smoothly
          const cleanToken = token.replace(/[*#$`\-]/g, " ").trim();
          if (cleanToken) {
            const utterance = new SpeechSynthesisUtterance(cleanToken);
            
            // Force the browser to grab the live up-to-date voice list
            let voices = window.speechSynthesis.getVoices();
            
            // Map to a premium, high-quality female narrator profile
            const femaleVoice = voices.find(v => 
              v.name.includes("Google US English Female") || 
              v.name.includes("Samantha") || 
              v.name.includes("Zira") ||
              v.name.includes("Hazel")
            );
            
            if (femaleVoice) utterance.voice = femaleVoice;
            utterance.rate = 0.92;  // Steady textbook/academic lecture pacing velocity
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
          }
        }
      }
    } catch (e) {
      setAiExplanation(prev => prev + "\n\n*[AI Tutor Streaming Pipeline Disconnected]*");
    } finally {
      setLoadingAI(false);
    }
  };

  const toggleNode = (id) => {
    setExpandedNodes(prev => ({ ...prev, [id]: !prev[id] }));
  };

  // Recursive Renderer Engine for Tree Sidebar Nodes
  const renderTree = (nodes) => {
    if (!Array.isArray(nodes)) return null;

    return (
      <ul className="pl-4 border-l border-slate-800 space-y-1 font-mono text-xs text-slate-400">
        {nodes.map(node => {
          const hasChildren = node.children && node.children.length > 0;
          const isExpanded = expandedNodes[node.id];

          return (
            <li key={node.id} className="py-1">
              <div 
                onClick={() => hasChildren ? toggleNode(node.id) : setSelectedLeafId(node.id)}
                className={`flex items-center gap-2 cursor-pointer p-1 rounded hover:bg-slate-900 transition-all ${selectedLeafId === node.id ? 'text-emerald-400 bg-slate-900 font-bold' : ''}`}
              >
                {hasChildren && (<span>{isExpanded ? '▼' : '►'}</span>)}
                <span className={node.is_leaf ? "text-slate-300" : "text-slate-500 font-bold uppercase tracking-wide text-[10px]"}>
                  {node.title}
                </span>
              </div>
              {hasChildren && isExpanded && renderTree(node.children)}
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <div className="flex h-[calc(100vh-64px)] w-full bg-slate-950 text-slate-100 overflow-hidden">
      {/* SIDEBAR NAVIGATION COLUMN */}
      <div className="w-80 min-w-[20rem] flex-shrink-0 border-r border-slate-900 bg-slate-950 p-4 flex flex-col overflow-y-auto">
        <button onClick={onBack} className="mb-6 text-left text-[10px] font-mono tracking-widest text-slate-500 hover:text-emerald-400 transition-colors uppercase">
          ← Back to Hub
        </button>
        <h2 className="text-sm font-black tracking-tight text-slate-200 mb-4 uppercase font-mono">
          {subject?.name || 'Syllabus Tree'}
        </h2>
        
        {loadingTree ? (
          <div className="space-y-2 animate-pulse text-xs font-mono text-slate-600">Processing Tree Metatags...</div>
        ) : treeNodes.length > 0 ? (
          renderTree(treeNodes)
        ) : (
          <div className="p-4 border border-dashed border-slate-900 rounded text-center my-2 bg-slate-950">
            <div className="text-[10px] text-slate-500 font-mono tracking-wider uppercase font-bold">No Syllabus Items Found</div>
            <div className="text-[9px] text-slate-600 font-mono mt-1">No operational chapters or topics found matching this index.</div>
          </div>
        )}
      </div>

      {/* CORE CONTENT MAIN RETRIEVAL VIEWER */}
      <div className="flex-grow grid grid-cols-2 overflow-hidden bg-slate-900/20">
        {/* LEFT COLUMN PANEL: Core Lesson Materials */}
        <div className="p-6 overflow-y-auto border-r border-slate-900">
          <div className="border-b border-slate-800 pb-2 mb-4">
            <span className="text-[10px] font-mono uppercase text-slate-500 tracking-widest">Core Curriculum Specification Documentation</span>
          </div>
          {loadingCore ? (
            <div className="text-sm text-slate-500 animate-pulse font-mono">Reading record blocks...</div>
          ) : coreContent === "VISUAL_MODE_ACTIVE" ? (
            /* Safe interactive presentation mode mount point */
            <LessonCanvas lessonPayload={visualLessonPayload} />
          ) : (
            /* Default Text View fallback markdown view */
            <div className="prose prose-invert max-w-none text-slate-300">
              <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                {coreContent || "*Select a specific core lesson concept token from the sidebar hierarchy navigation to spin up content views.*"}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN PANEL: AI Interactive Tutor Companion */}
        <div className="p-6 overflow-y-auto bg-slate-950/40">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-4">
            <span className="text-[10px] font-mono uppercase text-blue-400 tracking-widest">Ascenda Socratic Engine Pipeline</span>
            {loadingAI && <span className="text-[9px] font-mono bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded animate-pulse">STREAMING INTERACTIVE VECTOR TOKENS</span>}
          </div>
          <div className="prose prose-invert max-w-none text-slate-300">
            <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>{aiExplanation || (loadingAI ? "" : "*Awaiting active content generation pipeline trigger signals...*")}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}