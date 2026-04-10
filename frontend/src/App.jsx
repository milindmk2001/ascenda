import React, { useState } from 'react';
import { motion, useMotionValue } from 'framer-motion';

const App = () => {
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  // Animation values for the red and green dots
  const x1 = useMotionValue(100);
  const x2 = useMotionValue(300);

  const handleStartLesson = async () => {
    setLoading(true);
    setError(false);
    setResponse(""); // Clear old text
    
    try {
      const res = await fetch("https://ascenda-production.up.railway.app/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "Explain Coulomb's Law using Gen Z slang." }),
      });

      if (!res.ok) throw new Error("Connection failed");

      // FIX: Instead of res.json(), we use a Reader to handle the stream
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        // Decode binary chunk to text ("Okay, bet...")
        const chunk = decoder.decode(value, { stream: true });
        
        // Append text word-by-word
        setResponse((prev) => prev + chunk); 
      }
    } catch (err) {
      console.error("Stream error:", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.badge}>A</div>
        <h1 style={styles.title}>Ascenda</h1>
        <div style={styles.statusBadge}>● API: Online</div>
      </header>

      {/* PHYSICS INTERACTIVE SANDBOX */}
      <div style={styles.sandbox}>
        <p style={styles.sandboxHint}>Drag the charges to feel the "vibe power"</p>
        
        {/* Positive Charge (Red) */}
        <motion.div
          drag="x"
          dragConstraints={{ left: 0, right: 400 }}
          style={{ ...styles.charge, x: x1, backgroundColor: '#ff4d4d', boxShadow: '0 0 20px #ff4d4d' }}
        >
          +
        </motion.div>

        {/* Negative Charge (Green) */}
        <motion.div
          drag="x"
          dragConstraints={{ left: 0, right: 400 }}
          style={{ ...styles.charge, x: x2, backgroundColor: '#2ecc71', boxShadow: '0 0 20px #2ecc71' }}
        >
          -
        </motion.div>
      </div>

      <div style={styles.lessonCard}>
        <h3 style={styles.lessonTitle}>Current Lesson: Electrostatics</h3>
        
        <div style={styles.textContent}>
          {error ? (
            <span style={{ color: '#ff4d4d' }}>
              Connection failed. Check if Railway CORS is set to this URL.
            </span>
          ) : (
            response || "Ready for a vibe check on physics?"
          )}
        </div>

        <button 
          onClick={handleStartLesson} 
          disabled={loading}
          style={{
            ...styles.button,
            backgroundColor: loading ? '#444' : '#6366f1',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? "AI is typing..." : "Start Coulomb's Law Lesson"}
        </button>
      </div>

      <footer style={styles.footer}>
        BACKEND: HTTPS://ASCENDA-PRODUCTION.UP.RAILWAY.APP<br />
        PHYSICS EDTECH PLATFORM • 2026
      </footer>
    </div>
  );
};

// Simplified CSS-in-JS
const styles = {
  container: { padding: '20px', fontFamily: 'Inter, sans-serif', backgroundColor: '#f8fafc', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center' },
  header: { display: 'flex', alignItems: 'center', width: '100%', maxWidth: '600px', marginBottom: '20px' },
  badge: { backgroundColor: '#6366f1', color: 'white', padding: '8px 12px', borderRadius: '8px', fontWeight: 'bold', marginRight: '10px' },
  title: { fontSize: '1.5rem', color: '#1e293b', flexGrow: 1 },
  statusBadge: { backgroundColor: '#ecfdf5', color: '#059669', padding: '4px 10px', borderRadius: '20px', fontSize: '0.8rem' },
  sandbox: { width: '100%', maxWidth: '600px', height: '180px', backgroundColor: '#ffffff', borderRadius: '16px', position: 'relative', marginBottom: '20px', border: '1px solid #e2e8f0', overflow: 'hidden' },
  sandboxHint: { textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem', marginTop: '10px' },
  charge: { width: '50px', height: '50px', borderRadius: '50%', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', fontWeight: 'bold', position: 'absolute', top: '60px', cursor: 'grab' },
  lessonCard: { width: '100%', maxWidth: '600px', backgroundColor: 'white', padding: '24px', borderRadius: '16px', border: '1px solid #e2e8f0' },
  lessonTitle: { color: '#6366f1', marginBottom: '15px', fontSize: '1rem' },
  textContent: { minHeight: '150px', backgroundColor: '#f1f5f9', padding: '15px', borderRadius: '12px', color: '#334155', lineHeight: '1.6', marginBottom: '20px', whiteSpace: 'pre-wrap' },
  button: { width: '100%', padding: '14px', borderRadius: '10px', border: 'none', color: 'white', fontWeight: 'bold' },
  footer: { marginTop: 'auto', textAlign: 'center', fontSize: '0.7rem', color: '#94a3b8', letterSpacing: '1px', lineHeight: '2' }
};

export default App;