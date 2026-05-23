import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

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

  // Step 1: Fetch structural navigation tree for current subject with strict validation guards
  useEffect(() => {
    if (!subject?.id) return;
    
    setLoadingTree(true);
    fetch(`${API_BASE}/api/curriculum/subjects/${subject.id}/tree`)
      .then(res => {
        if (!res.ok) throw new Error("Network response encountered structural failure errors.");
        return res.json();
      })
      .then(data => {
        // Assert array layout contracts explicitly to avoid crashing on .map() operations
        if (data && Array.isArray(data)) {
          setTreeNodes(data);
        } else if (data && Array.isArray(data.tree)) {
          setTreeNodes(data.tree);
        } else {
          console.warn("Expected list array metadata payload, received:", data);
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

  // Step 2: Leaf token click handler to fetch core documentation and run AI streaming mechanics
  const handleLeafSelect = (nodeId) => {
    setSelectedLeafId(nodeId);
    setLoadingCore(true);
    setLoadingAI(true);
    setCoreContent('');
    setAiExplanation('');

    // Fetch primary specification core Markdown block
    fetch(`${API_BASE}/api/curriculum/nodes/${nodeId}/core`)
      .then(res => res.json())
      .then(data => {
        setCoreContent(data.markdown || '*No structural document tracking found on this index reference.*');
        setLoadingCore(false);
      })
      .catch(err => {
        console.error("Failed fetching core node data layout payload:", err);
        setCoreContent('*Failed executing core content loading actions.*');
        setLoadingCore(false);
      });

    // Fetch companion contextual explanation stream
    fetch(`${API_BASE}/api/curriculum/nodes/${nodeId}/explain`)
      .then(res => res.json())
      .then(data => {
        setAiExplanation(data.explanation || '*AI engine could not generate concept logs for this leaf node.*');
        setLoadingAI(false);
      })
      .catch(err => {
        console.error("Socratic generation tracking engine timeout failure:", err);
        setAiExplanation('*Failed processing engine prompt vector pipelines.*');
        setLoadingAI(false);
      });
  };

  const toggleExpand = (nodeId) => {
    setExpandedNodes(prev => ({
      ...prev,
      [nodeId]: !prev[nodeId]
    }));
  };

  // Recursive directory engine generator UI layout mapping blocks
  const renderTree = (nodes) => {
    if (!Array.isArray(nodes)) return null;

    return nodes.map(node => {
      const hasChildren = node.children && node.children.length > 0;
      const isExpanded = !!expandedNodes[node.id];
      const isSelected = selectedLeafId === node.id;

      return (
        <div key={node.id} className="pl-3 my-1 select-none font-mono">
          <div 
            className={`flex items-center gap-1.5 py-1 px-2 rounded cursor-pointer text-xs tracking-tight transition-all duration-150 ${
              isSelected 
                ? 'bg-emerald-500/20 text-emerald-400 border-l-2 border-emerald-500 font-medium' 
                : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
            }`}
            onClick={() => node.is_leaf ? handleLeafSelect(node.id) : toggleExpand(node.id)}
          >
            {!node.is_leaf && (
              <span className="text-[10px] text-slate-600 font-bold w-3 inline-block">
                {isExpanded ? '▼' : '►'}
              </span>
            )}
            {node.is_leaf && <span className="text-[9px] text-emerald-600/80">●</span>}
            <span className="truncate">{node.title}</span>
            {node.content_type && (
              <span className="text-[8px] opacity-40 uppercase tracking-widest bg-slate-800 px-1 rounded ml-auto">
                {node.content_type}
              </span>
            )}
          </div>

          {!node.is_leaf && hasChildren && isExpanded && (
            <div className="border-l border-slate-800/60 ml-1.5 mt-0.5">
              {renderTree(node.children)}
            </div>
          )}
        </div>
      );
    });
  };

  return (
    <div className="grid grid-cols-[320px_1fr_1fr] h-screen w-full bg-slate-950 text-slate-100 overflow-hidden divide-x divide-slate-900">
      
      {/* LEFT COLUMN PANEL: Dynamic Hierarchical Syllabus Workspace Menu */}
      <div className="flex flex-col bg-slate-950 h-full overflow-hidden">
        <div className="p-4 border-b border-slate-900 flex items-center justify-between">
          <button 
            onClick={onBack}
            className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500 hover:text-slate-300 uppercase tracking-wider transition-all"
          >
            ← Back to Hub
          </button>
          <span className="text-xs font-bold text-emerald-400 tracking-wider uppercase bg-emerald-500/5 px-2 py-0.5 rounded border border-emerald-500/10">
            {subject?.name || "Syllabus Index"}
          </span>
        </div>

        <div className="p-3 overflow-y-auto flex-1 custom-scrollbar">
          {loadingTree ? (
            <div className="p-4 text-center text-xs font-mono text-slate-600 animate-pulse">
              Parsing asset tree layout data matrices...
            </div>
          ) : treeNodes.length === 0 ? (
            <div className="p-6 text-center rounded border border-dashed border-slate-900 my-4">
              <p className="text-xs font-mono text-slate-500 tracking-wide">NO COURSES FOUND</p>
              <p className="text-[10px] font-mono text-slate-600 mt-1">No mapping entries found matches for this index hierarchy tracker selection.</p>
            </div>
          ) : (
            <div className="mt-2">
              {renderTree(treeNodes)}
            </div>
          )}
        </div>
      </div>

      {/* MIDDLE COLUMN PANEL: Core Technical Curriculum Notebook */}
      <div className="p-6 overflow-y-auto bg-slate-900/20">
        <div className="flex items-center border-b border-slate-800 pb-2 mb-4">
          <span className="text-[10px] font-mono uppercase text-emerald-400 tracking-widest">Core Curriculum Specification Documentation</span>
        </div>
        {loadingCore ? (
          <div className="text-sm text-slate-500 animate-pulse font-mono">Reading record blocks...</div>
        ) : (
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
          <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
            {aiExplanation || (loadingAI ? "" : "*Awaiting active content generation pipeline trigger signals......*")}
          </ReactMarkdown>
        </div>
      </div>

    </div>
  );
}