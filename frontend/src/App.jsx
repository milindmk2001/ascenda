import React, { useState, useEffect } from 'react';
import { motion, useMotionValue, useTransform } from 'framer-motion';

const App = () => {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  // Animation state for the charges
  const x1 = useMotionValue(100);
  const x2 = useMotionValue(300);

  const handleStartLesson = async () => {
    setLoading(true);
    setResponse(""); // Clear previous text
    
    try {
      const res = await fetch("https://ascenda-production.up.railway.app/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "Explain Coulomb's Law using Gen Z slang." }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        setResponse((prev) => prev + chunk); // Stream text to UI
      }
    } catch (err) {
      setResponse("Failed to connect to AI service.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '40px', fontFamily: 'sans-serif', backgroundColor: '#121212', color: 'white', minHeight: '100vh' }}>
      <h1>Ascenda: Electrostatics</h1>
      
      {/* PHYSICS SANDBOX */}
      <div style={{ height: '200px', background: '#1e1e1e', borderRadius: '15px', position: 'relative', overflow: 'hidden', marginBottom: '20px', border: '1px solid #333' }}>
        <p style={{ textAlign: 'center', color: '#666' }}>Drag the charges to feel the force</p>
        
        {/* Positive Charge (Red) */}
        <motion.div
          drag="x"
          style={{ x: x1, width: 50, height: 50, borderRadius: '50%', background: '#ff4d4d', position: 'absolute', top: 75, cursor: 'grab', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 20px #ff4d4d' }}
          whileTap={{ scale: 0.9 }}
        > + </motion.div>

        {/* Negative Charge (Green) */}
        <motion.div
          drag="x"
          style={{ x: x2, width: 50, height: 50, borderRadius: '50%', background: '#2ecc71', position: 'absolute', top: 75, cursor: 'grab', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 20px #2ecc71' }}
          whileTap={{ scale: 0.9 }}
        > - </motion.div>
      </div>

      <button 
        onClick={handleStartLesson} 
        disabled={loading}
        style={{ padding: '12px 24px', borderRadius: '8px', border: 'none', background: '#6200ee', color: 'white', fontWeight: 'bold', cursor: 'pointer' }}
      >
        {loading ? "AI is typing..." : "Start Coulomb's Law Lesson"}
      </button>

      <div style={{ marginTop: '30px', lineHeight: '1.6', fontSize: '1.1rem', whiteSpace: 'pre-wrap' }}>
        {response}
      </div>
    </div>
  );
};

export default App;