import React from 'react'

function App() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      {/* Main Card */}
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 border border-slate-200">
        
        <div className="flex items-center space-x-3 mb-6">
          <div className="h-10 w-10 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">
            A
          </div>
          <h1 className="text-2xl font-bold text-slate-800">Ascenda</h1>
        </div>

        <p className="text-slate-600 mb-8">
          Your React frontend is now successfully configured with Vite and Tailwind CSS. 
          The backend connection is the next step!
        </p>

        <div className="space-y-4">
          <div className="flex items-center p-3 bg-green-50 rounded-lg border border-green-100">
            <div className="h-2 w-2 bg-green-500 rounded-full mr-3 animate-pulse"></div>
            <span className="text-sm font-medium text-green-700 underline">Tailwind Active</span>
          </div>

          <button 
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition duration-200 shadow-md hover:shadow-lg"
            onClick={() => alert('Ascenda Project Initialized!')}
          >
            Project Dashboard
          </button>
        </div>
      </div>

      <footer className="mt-8 text-slate-400 text-xs tracking-widest uppercase">
        Development Environment • Localhost:5173
      </footer>
    </div>
  )
}

export default App