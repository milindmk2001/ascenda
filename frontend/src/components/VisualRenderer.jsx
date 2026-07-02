import React, { useMemo, useRef, useEffect } from 'react';
import { sanitiseSvg } from '../utils/svgSanitiser';

export default function VisualRenderer({ svgContent, hostRef }) {
  const safeContent = useMemo(() => {
    return sanitiseSvg(svgContent);
  }, [svgContent]);

  return (
    <div className="w-full h-full flex items-center justify-center p-4 bg-white rounded-xl shadow-inner select-none min-h-[320px]">
      <div 
        ref={hostRef}
        className="w-full h-full max-w-[850px] max-h-[450px] text-slate-900 transition-all duration-300"
        dangerouslySetInnerHTML={{ __html: safeContent }}
      />
    </div>
  );
}