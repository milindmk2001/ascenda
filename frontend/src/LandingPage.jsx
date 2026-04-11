import React from 'react';

const LandingPage = ({ onStartLesson }) => {
  const subjects = [
    { name: 'Physics', icon: '⚛️' },
    { name: 'Maths', icon: '📐' },
    { name: 'Chemistry', icon: '🧪' },
    { name: 'Biology', icon: '🧬' },
    { name: 'English', icon: '📖' },
    { name: 'SST', icon: '🌍' }
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-indigo-500/30">
      {/* Navigation */}
      <nav className="p-4 border-b border-slate-800 flex justify-between items-center sticky top-0 bg-slate-950/80 backdrop-blur-md z-50">
        <div className="text-2xl font-black tracking-tighter">
          ASCENDA<span className="text-indigo-500">PRO</span>
        </div>
        <div className="flex gap-4 items-center">
          <select className="bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-sm outline-none">
            <option>CBSE</option>
            <option>ICSE</option>
          </select>
          <button className="bg-indigo-600 hover:bg-indigo-500 px-5 py-2 rounded-full text-sm font-bold transition-all">
            Login
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-6 max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-12">
        <div className="flex-1 text-center lg:text-left">
          <div className="inline-block px-4 py-1 mb-6 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-400 text-xs font-bold uppercase tracking-widest">
            India's First AI-Interactive Tutor
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold leading-tight mb-6">
            Class 3-12 <br /> 
            <span className="text-indigo-500">Visual Learning</span>
          </h1>
          <p className="text-slate-400 text-lg mb-10 max-w-xl">
            Don't just watch a video. Ask questions and let our AI point exactly 
            to the concepts on screen.
          </p>
          <button 
            onClick={onStartLesson} 
            className="bg-white text-black px-10 py-4 rounded-xl font-bold hover:bg-slate-200 transition-transform active:scale-95"
          >
            Try Free Demo Lesson
          </button>
        </div>
        
        <div className="flex-1 w-full aspect-video bg-slate-900 rounded-3xl border border-slate-800 shadow-2xl overflow-hidden relative">
            <div className="absolute inset-0 flex items-center justify-center bg-indigo-500/5">
                <span className="text-indigo-500/20 text-8xl font-black">VEO</span>
            </div>
        </div>
      </section>

      {/* Subject Grid */}
      <section className="py-20 bg-slate-900/30 px-6">
        <div className="max-w-7xl mx-auto">
          <h3 className="text-2xl font-bold mb-10">Select Subject (Class 10)</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {subjects.map((sub) => (
              <div 
                key={sub.name} 
                onClick={onStartLesson} 
                className="group bg-slate-900 border border-slate-800 p-8 rounded-2xl text-center hover:border-indigo-500 hover:bg-indigo-500/10 transition-all cursor-pointer"
              >
                <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">{sub.icon}</div>
                <div className="font-bold">{sub.name}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;