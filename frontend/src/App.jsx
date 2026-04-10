import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const App = () => {
  const videoRef = useRef(null);
  const [isAsking, setIsAsking] = useState(false);
  const [aiResponse, setAiResponse] = useState("");
  const [svgElements, setSvgElements] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleRaiseHand = async () => {
    setLoading(true);
    videoRef.current.pause(); // Pause the 'Udemy' video
    setIsAsking(true);
    
    const currentTime = videoRef.current.currentTime;

    try {
      const res = await fetch("https://ascenda-production.up.railway.app/api/interact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          timestamp: currentTime,
          query: "What's happening in this frame?" 
        }),
      });
      
      const data = await res.json();
      setAiResponse(data.explanation);
      setSvgElements(data.visuals);
    } catch (err) {
      setAiResponse("Connection error. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const resume = () => {
    setIsAsking(false);
    setSvgElements([]);
    setAiResponse("");
    videoRef.current.play();
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.logo}>A</div>
        <h2 style={{margin: 0}}>Ascenda Pro</h2>
      </header>

      <div style={styles.stage}>
        <div style={styles.videoWrapper}>
          {/* THE BASE LESSON VIDEO */}
          <video 
            ref={videoRef}
            src="https://www.w3schools.com/html/mov_bbb.mp4" 
            style={styles.video}
            controls={!isAsking}
          />

          {/* THE INTERACTIVE DRAWING LAYER */}
          <AnimatePresence>
            {isAsking && (
              <motion.svg 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                style={styles.svgLayer}
                viewBox="0 0 800 450"
              >
                {svgElements.map((el, i) => (
                  el.type === 'arrow' ? (
                    <motion.line
                      key={i} x1={el.x1} y1={el.y1} x2={el.x2} y2={el.y2}
                      stroke="#fbbf24" strokeWidth="6" strokeLinecap="round"
                      initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}
                    />
                  ) : (
                    <motion.circle
                      key={i} cx={el.cx} cy={el.cy} r={el.r}
                      fill="transparent" stroke="#60a5fa" strokeWidth="4"
                      initial={{ scale: 0 }} animate={{ scale: 1 }}
                    />
                  )
                ))}
              </motion.svg>
            )}
          </AnimatePresence>
        </div>

        {/* INTERACTIVE UI PANEL */}
        <div style={styles.uiPanel}>
          {!isAsking ? (
            <button onClick={handleRaiseHand} style={styles.askBtn}>
              ✋ RAISE HAND TO ASK AI
            </button>
          ) : (
            <motion.div initial={{ y: 20 }} animate={{ y: 0 }} style={styles.responseBox}>
              <h4 style={{color: '#fbbf24', marginTop: 0}}>AI TUTOR</h4>
              <p style={{fontSize: '0.95rem', lineHeight: '1.5'}}>
                {loading ? "Analyzing frame..." : aiResponse}
              </p>
              <button onClick={resume} style={styles.resumeBtn}>Got it, Continue Lesson</button>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: { padding: '20px', backgroundColor: '#0f172a', minHeight: '100vh', color: 'white', fontFamily: 'Inter, sans-serif' },
  header: { display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '30px' },
  logo: { backgroundColor: '#6366f1', padding: '10px 15px', borderRadius: '8px', fontWeight: 'bold' },
  stage: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' },
  videoWrapper: { position: 'relative', width: '100%', maxWidth: '854px', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 20px 50px rgba(0,0,0,0.5)' },
  video: { width: '100%', display: 'block' },
  svgLayer: { position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none', backgroundColor: 'rgba(0,0,0,0.4)' },
  uiPanel: { width: '100%', maxWidth: '854px' },
  askBtn: { width: '100%', padding: '20px', borderRadius: '12px', border: 'none', backgroundColor: '#6366f1', color: 'white', fontWeight: 'bold', cursor: 'pointer', fontSize: '1rem' },
  responseBox: { backgroundColor: '#1e293b', padding: '25px', borderRadius: '16px', borderLeft: '6px solid #fbbf24' },
  resumeBtn: { marginTop: '15px', padding: '10px 25px', borderRadius: '8px', border: 'none', backgroundColor: '#10b981', color: 'white', cursor: 'pointer', fontWeight: 'bold' }
};

export default App;