export function sanitiseSvg(rawSvgString) {
  if (!rawSvgString) return "";
  
  // 1. Remove script inject structures
  let clean = rawSvgString.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "");
  
  // 2. Strip standard forbidden functional containers
  clean = clean.replace(/<foreignObject[\s\S]*?>[\s\S]*?<\/foreignObject>/gi, "");
  
  // 3. Extinguish operational event handlers inline
  clean = clean.replace(/on\w+\s*=\s*".*?"/gi, "");
  clean = clean.replace(/on\w+\s*=\s*'.*?'/gi, "");
  
  // 4. Remove external references
  clean = clean.replace(/href\s*=\s*["'](http:\/\/|https:\/\/).*?["']/gi, 'href="#"');
  
  return clean;
}