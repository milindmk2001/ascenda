import React, { useState, useMemo } from 'react';

/**
 * Clean inline SVG icons to keep the component self-contained 
 * and avoid external asset installation breaking the layout.
 */
const ChevronDownIcon = () => (
  <svg className="w-4 h-4 shrink-0 text-gray-400" fill=\"none\" viewBox=\"0 0 24 24\" stroke=\"currentColor\" strokeWidth={2}>
    <path strokeLinecap=\"round\" strokeLinejoin=\"round\" d=\"M19 9l-7 7-7-7\" />
  </svg>
);

const ChevronRightIcon = () => (
  <svg className="w-4 h-4 shrink-0 text-gray-400" fill=\"none\" viewBox=\"0 0 24 24\" stroke=\"currentColor\" strokeWidth={2}>
    <path strokeLinecap=\"round\" strokeLinejoin=\"round\" d=\"M9 5l7 7-7 7\" />
  </svg>
);

// FIX 3: Content-type color token mapping for leaf indicators
const getContentTypeColor = (type) => {
  switch (type?.toLowerCase()) {
    case 'concept': return '#3b82f6';         // Vivid Blue (Learn)
    case 'rules': return '#f97316';           // Warning Orange (Rules)
    case 'worked_example': return '#10b981';   // Emerald Green (Examples)
    case 'practice': return '#eab308';         // Bright Yellow (Practice)
    case 'common_mistakes': return '#ef4444';  // Crimson Red (Watch Out)
    case 'real_life': return '#a855f7';        // Purple (Real Life Applications)
    default: return '#64748b';                 // Muted Slate Gray Base
  }
};

export default function CurriculumPane({ treeData = [], selectedLeafId, onSelectLeaf }) {
  const [expandedNodes, setExpandedNodes] = useState({});

  const toggleNode = (nodeId) => {
    setExpandedNodes((prev) => ({
      ...prev,
      [nodeId]: !prev[nodeId],
    }));
  };

  const renderNode = (node) => {
    const isExpanded = !!expandedNodes[node.id];
    const isSelected = selectedLeafId === node.id;

    const handleNodeClick = () => {
      if (node.is_leaf) {
        if (onSelectLeaf) onSelectLeaf(node.id);
      } else {
        toggleNode(node.id);
      }
    };

    return (
      <div key={node.id} className="w-full select-none">
        {/* Row Element Container */}
        <div
          onClick={handleNodeClick}
          className={`group flex items-center justify-between py-2 px-2.5 mx-1 rounded-md text-xs transition-all duration-200 cursor-pointer ${
            isSelected
              ? 'bg-slate-900 text-emerald-400 font-bold border-l-2 border-emerald-500 pl-1.5'
              : 'hover:bg-white/5 text-gray-300'
          }`}
        >
          <div className="flex items-center gap-2 truncate">
            {node.children && node.children.length > 0 ? (
              isExpanded ? <ChevronDownIcon /> : <ChevronRightIcon />
            ) : node.is_leaf ? (
              /* FIX 3: Dynamic content indicator colored badge dot */
              <span 
                className="w-1.5 h-1.5 rounded-full shrink-0 ml-1 mr-1 transition-transform group-hover:scale-125" 
                style={{ backgroundColor: getContentTypeColor(node.content_type) }}
              />
            ) : (
              <div className="w-4" />
            )}
            <span className="truncate">
              {node.level === 1 && node.unit_number > 0 ? `Unit ${node.unit_number} — ` : ''}
              {node.title}
            </span>
          </div>
          {node.children && node.children.length > 0 && (
            <span className="text-[10px] text-gray-500 font-normal bg-white/5 px-1.5 py-0.5 rounded-full shrink-0">
              {node.children.length}
            </span>
          )}
        </div>

        {/* Animated Subtree Container Expansion */}
        {isExpanded && node.children && node.children.length > 0 && (
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
        {treeData.length > 0 ? (
          treeData.map((node) => renderNode(node))
        ) : (
          <div className="p-3 text-xs text-gray-500 italic text-center">
            No curriculum nodes active
          </div>
        )}
      </div>
    </div>
  );
}