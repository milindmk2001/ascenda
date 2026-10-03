import React, { useEffect, useRef } from 'react';

export function sanitizeSvgString(rawSvg) {
  if (typeof rawSvg !== 'string') return '';
  return rawSvg
    .replace(/\\n/g, '\n')
    .replace(/\\"/g, '"')
    .replace(/\u00a0/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .trim();
}

export default function VisualRenderer({ svgContent, hostRef }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const targetRef = hostRef || containerRef;
    if (!targetRef.current || !svgContent) return;

    const cleanedSvg = sanitizeSvgString(svgContent);
    const parser = new DOMParser();
    const doc = parser.parseFromString(cleanedSvg, 'image/svg+xml');
    const svgElement = doc.querySelector('svg');

    // Handle potential XML parsing errors cleanly
    const parserError = doc.querySelector('parsererror');
    if (parserError || !svgElement) {
      console.error('SVG Parsing Failed:', parserError ? parserError.textContent : 'No SVG element found');
      targetRef.current.innerHTML = `<div class="p-4 text-xs font-mono text-red-400">Failed to render visual content</div>`;
      return;
    }

    // Enforce responsive sizing and aspect ratio constraints
    svgElement.setAttribute('width', '100%');
    svgElement.setAttribute('height', '100%');
    svgElement.style.display = 'block';
    svgElement.style.maxWidth = '100%';
    svgElement.style.maxHeight = '100%';

    // Clear and mount SVG node into the host DOM ref
    targetRef.current.innerHTML = '';
    targetRef.current.appendChild(svgElement);

  }, [svgContent, hostRef]);

  return (
    <div 
      ref={hostRef || containerRef} 
      className="w-full h-full flex items-center justify-center overflow-hidden"
    />
  );
}