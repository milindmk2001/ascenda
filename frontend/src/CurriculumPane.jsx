import React, { useState, useMemo } from 'react';

/**
 * Clean inline SVG icons to keep the component self-contained 
 * and avoid external asset installation breaking the layout.
 */
const ChevronDownIcon = () => (
  <svg className="w-4 h-4 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
  </svg>
);

const ChevronRightIcon = () => (
  <svg className="w-4 h-4 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
  </svg>
);

const ConceptIcon = () => (
  <svg className="w-4 h-4 shrink-0 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const SolvedIcon = () => (
  <svg className="w-4 h-4 shrink-0 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const UnsolvedIcon = () => (
  <svg className="w-4 h-4 shrink-0 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const TestIcon = () => (
  <svg className="w-4 h-4 shrink-0 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

// Map content types to recognizable standard strings and icons
const getLeafMetadata = (contentType) => {
  switch (contentType) {
    case 'concept':
      return { label: 'Concept Study', icon: <ConceptIcon /> };
    case 'solved_problems':
      return { label: 'Solved Problems', icon: <SolvedIcon /> };
    case 'unsolved_problems':
      return { label: 'Unsolved Exercises', icon: <UnsolvedIcon /> };
    case 'concept_test':
      return { label: 'Concept Test', icon: <TestIcon /> };
    default:
      return { label: 'Study Material', icon: <ConceptIcon /> };
  }
};

export default function CurriculumPane({ nodes = [], onLeafClick, activeLeafId }) {
  // Global expansion state map using individual node IDs as lookup keys
  const [expandedNodes, setExpandedNodes] = useState({});

  const toggleNode = (id) => {
    setExpandedNodes((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  /**
   * Transforms flat API nodes array into a nested relational object structure.
   * Leverages useMemo to perform linear O(N) mapping, safeguarding client-side
   * render loops from depth calculation stuttering.
   */
  const treeData = useMemo(() => {
    if (!nodes || nodes.length === 0) return [];

    const nodeMap = {};
    const roots = [];

    // Step 1: Clone entry data points into workspace memory ledger
    nodes.forEach((node) => {
      nodeMap[node.id] = { ...node, children: [] };
    });

    // Step 2: Establish hierarchical parent-child relationships
    nodes.forEach((node) => {
      const currentElement = nodeMap[node.id];
      if (node.parent_id && nodeMap[node.parent_id]) {
        nodeMap[node.parent_id].children.push(currentElement);
      } else if (node.level === 1 || !node.parent_id) {
        roots.push(currentElement);
      }
    });

    // Step 3: Sort branches systematically using display_order properties
    const sortTreeBranches = (branches) => {
      branches.sort((a, b) => (a.display_order || 0) - (b.display_order || 0));
      branches.forEach((branch) => {
        if (branch.children.length > 0) {
          sortTreeBranches(branch.children);
        }
      });
    };

    sortTreeBranches(roots);
    return roots;
  }, [nodes]);

  // Recursive Element Builder
  const renderNode = (node) => {
    const isExpanded = !!expandedNodes[node.id];
    
    // LEVEL 3: Core Clickable Leaves
    if (node.is_leaf || node.level === 3) {
      const { label, icon } = getLeafMetadata(node.content_type);
      const isActive = activeLeafId === node.id;

      return (
        <div
          key={node.id}
          onClick={() => onLeafClick && onLeafClick(node.id)}
          className={`flex items-center gap-2.5 pl-9 pr-3 py-1.5 text-xs font-medium rounded-md cursor-pointer transition-all duration-150 select-none ${
            isActive
              ? 'bg-blue-600/10 text-blue-400 border-l-2 border-blue-500 pl-8.5'
              : 'text-gray-400 hover:bg-white/5 hover:text-white'
          }`}
        >
          {icon}
          <span className="truncate">{node.title || label}</span>
        </div>
      );
    }

    // LEVEL 1 & 2: Collapsible Group Structural Branches
    return (
      <div key={node.id} className="w-full">
        <div
          onClick={() => toggleNode(node.id)}
          className={`flex items-center justify-between w-full pr-2 py-2 text-left cursor-pointer transition-colors duration-150 select-none ${
            node.level === 1
              ? 'pl-2 text-gray-200 font-semibold text-sm hover:bg-white/5 rounded-md mt-3'
              : 'pl-6 text-gray-300 font-medium text-xs hover:bg-white/5 rounded-md mt-0.5'
          }`}
        >
          <div className="flex items-center gap-1.5 truncate">
            {node.children.length > 0 ? (
              isExpanded ? <ChevronDownIcon /> : <ChevronRightIcon />
            ) : (
              <div className="w-4" />
            )}
            <span className="truncate">
              {node.level === 1 && node.unit_number > 0 ? `Unit ${node.unit_number} — ` : ''}
              {node.title}
            </span>
          </div>
          {node.children.length > 0 && (
            <span className="text-[10px] text-gray-500 font-normal bg-white/5 px-1.5 py-0.5 rounded-full shrink-0">
              {node.children.length}
            </span>
          )}
        </div>

        {/* Animated Subtree Container Expansion */}
        {isExpanded && node.children.length > 0 && (
          <div className="mt-0.5 border-l border-white/5 ml-4 pl-1 space-y-0.5">
            {node.children.map((child) => renderNode(child))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-full h-full overflow-y-auto bg-[#0B0F19] text-gray-300 px-2 py-3 custom-sidebar-scroll">
      <div className="px-2 pb-2 mb-2 border-b border-white/5">
        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Syllabus Tree</h3>
      </div>
      
      <div className="space-y-0.5">
        {treeData.length === 0 ? (
          <div className="text-center text-xs text-gray-500 py-6">
            No curriculum nodes matched this selection track.
          </div>
        ) : (
          treeData.map((rootNode) => renderNode(rootNode))
        )}
      </div>
    </div>
  );
}