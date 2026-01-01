import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { 
  Upload, Database, LineChart, MessageSquare, 
  AlertCircle, CheckCircle, Download, FileText, Sparkles 
} from 'lucide-react';

const API_BASE = "http://localhost:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [query, setQuery] = useState("");
  const [chat, setChat] = useState([]);
  const [timestamp, setTimestamp] = useState(Date.now()); // Used for cache busting
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_BASE}/analyze`, formData);
      setData(res.data);
      setTimestamp(Date.now()); // Update timestamp on every new analysis
      setChat([{ 
        role: 'assistant', 
        content: "### Analysis Complete! \nI've audited the data, cleaned missing values, and generated executive visualizations. What specific trends would you like to dive into?" 
      }]);
    } catch (err) {
      console.error(err);
      alert("Analysis failed. Ensure the Python backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async (e) => {
    e.preventDefault();
    if (!query || !data?.thread_id) return;

    const userMsg = { role: 'user', content: query };
    setChat(prev => [...prev, userMsg]);
    const currentQuery = query;
    setQuery("");

    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        thread_id: data.thread_id,
        user_query: currentQuery
      });
      setChat(prev => [...prev, { role: 'assistant', content: res.data.answer }]);
    } catch (err) {
      setChat(prev => [...prev, { role: 'assistant', content: "**Error:** Could not connect to the AI agent." }]);
    }
  };

  if (loading) return (
    <div className="h-screen w-full flex flex-col items-center justify-center bg-[#0a0c10] text-white">
      <div className="relative">
        <div className="animate-spin rounded-full h-24 w-24 border-t-2 border-b-2 border-blue-500"></div>
        <Database className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-blue-500" size={32} />
      </div>
      <p className="mt-8 text-xl font-medium tracking-tight text-slate-300">DataOracle is synthesizing your data...</p>
      <p className="mt-2 text-sm text-slate-500 italic">Cleaning Dataset • Plotting Trends • Generating Insights</p>
    </div>
  );

  return (
    <div className="h-screen w-full bg-[#0d1117] text-slate-200 flex flex-col overflow-hidden font-sans">
      {/* HEADER */}
      <header className="h-20 border-b border-slate-800/60 flex items-center justify-between px-10 bg-[#161b22]/80 backdrop-blur-xl z-50">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600/20 p-2 rounded-lg border border-blue-500/30">
            <Database className="text-blue-500" size={24} />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tighter text-white">
            DATA<span className="text-blue-500">ORACLE</span> <span className="text-xs font-mono bg-slate-800 px-2 py-0.5 rounded ml-2 text-slate-400 uppercase">v1.0</span>
          </h1>
        </div>
        
        {data && (
          <div className="flex items-center gap-6">
            <a 
              href={`${data.pdf_report_url}?t=${timestamp}`} 
              target="_blank" 
              rel="noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-semibold transition-all border border-slate-700 text-white"
            >
              <Download size={18} /> Download Report
            </a>
          </div>
        )}
      </header>

      {data ? (
        <div className="flex-1 flex overflow-hidden">
          {/* LEFT PANEL: DATA STATS */}
          <aside className="w-80 border-r border-slate-800 bg-[#0d1117] overflow-y-auto p-6 scrollbar-hide">
            <div className="space-y-8">
              <section>
                <h2 className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4">Dataset Integrity</h2>
                <div className="p-5 bg-gradient-to-br from-slate-800/40 to-slate-900/40 rounded-2xl border border-slate-800 shadow-xl">
                  <div className="flex justify-between items-end mb-3">
                    <span className="text-sm font-medium text-slate-400">Health Score</span>
                    <span className="text-2xl font-black text-blue-400">{data.data_profile.health_score}%</span>
                  </div>
                  <div className="w-full bg-slate-700/50 h-1.5 rounded-full">
                    <div 
                      className="bg-blue-500 h-full rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-1000" 
                      style={{ width: `${data.data_profile.health_score}%` }}
                    ></div>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-sm font-bold mb-4 flex items-center gap-2 text-slate-300">
                  <CheckCircle size={16} className="text-emerald-500"/> Dimensions
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800 text-center">
                    <div className="text-[10px] text-slate-500 uppercase">Rows</div>
                    <div className="text-lg font-bold text-white">{data.data_profile.shape[0]}</div>
                  </div>
                  <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800 text-center">
                    <div className="text-[10px] text-slate-500 uppercase">Cols</div>
                    <div className="text-lg font-bold text-white">{data.data_profile.shape[1]}</div>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-sm font-bold mb-4 flex items-center gap-2 text-slate-300">
                   Numerical Features
                </h3>
                <div className="flex flex-wrap gap-2">
                  {data.data_profile.columns.numerical.map(col => (
                    <span key={col} className="px-3 py-1 bg-blue-500/5 text-blue-400 text-[11px] font-medium rounded-full border border-blue-500/20">
                      {col}
                    </span>
                  ))}
                </div>
              </section>
            </div>
          </aside>

          {/* CENTER PANEL: VISUALS */}
          <main className="flex-1 overflow-y-auto bg-[#0a0c10] p-12 scroll-smooth">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-center gap-3 mb-12">
                <Sparkles className="text-yellow-500" />
                <h2 className="text-3xl font-bold text-white tracking-tight">Intelligence Feed</h2>
              </div>

              <div className="space-y-24">
                {data.viz_results.map((viz, idx) => (
                  <div key={idx} className="relative group animate-in fade-in slide-in-from-bottom-10 duration-700">
                    <div className="mb-6">
                      <span className="text-blue-500 font-mono text-xs mb-2 block uppercase tracking-widest font-bold">Analysis 0{idx + 1}</span>
                      <h3 className="text-2xl font-bold text-slate-100 leading-tight">{viz.title}</h3>
                    </div>
                    
                    <div className="bg-[#161b22] rounded-3xl p-6 border border-slate-800 shadow-2xl transition-all hover:border-blue-500/40">
                      <img 
                        // FIXED: Added ?t= for Cache Busting and an onError handler
                        src={`${viz.path}?t=${timestamp}`} 
                        alt={viz.title} 
                        className="w-full h-auto rounded-xl grayscale-[20%] hover:grayscale-0 transition-all duration-500" 
                        onError={(e) => {
                          e.target.onerror = null; 
                          e.target.src="https://via.placeholder.com/800x450?text=Visualization+Loading...";
                        }}
                      />
                    </div>
                    
                    <div className="mt-8 flex gap-6 items-start">
                      <div className="w-1 bg-blue-500/30 rounded-full self-stretch" />
                      <div className="flex-1 text-slate-400 text-lg leading-relaxed italic font-serif">
                        {viz.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </main>

          {/* RIGHT PANEL: CHAT */}
          <aside className="w-96 border-l border-slate-800 bg-[#0d1117] flex flex-col shadow-2xl">
            <div className="p-6 border-b border-slate-800 bg-[#161b22]/50">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                <h2 className="font-bold text-sm uppercase tracking-widest text-slate-300">AI Consultant</h2>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
              {chat.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] p-4 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-tr-none shadow-lg shadow-blue-500/20' 
                    : 'bg-slate-800 text-slate-300 border border-slate-700 rounded-tl-none prose prose-invert prose-sm'
                  }`}>
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            <form onSubmit={handleChat} className="p-6 border-t border-slate-800 bg-[#161b22]/50">
              <input 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about trends or anomalies..."
                className="w-full bg-[#0d1117] border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              />
            </form>
          </aside>
        </div>
      ) : (
        /* HERO STATE */
        <div className="flex-1 flex flex-col items-center justify-center bg-gradient-to-b from-[#0d1117] to-[#0a0c10]">
          <div className="max-w-2xl w-full px-8 text-center">
            <div className="mb-10 inline-flex items-center justify-center w-24 h-24 bg-blue-600/10 rounded-3xl border border-blue-500/20 shadow-inner">
              <Upload className="text-blue-500" size={40} />
            </div>
            <h2 className="text-5xl font-black mb-6 text-white tracking-tight leading-tight">
              Analyze your data with <br/> <span className="text-blue-500">Autonomous Intelligence.</span>
            </h2>
            <p className="text-slate-400 text-lg mb-10 leading-relaxed">
              Upload a CSV file and our multi-agent system will perform auditing, automated cleaning, and generate executive-ready visualizations.
            </p>
            
            <div className="flex flex-col items-center gap-4">
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={(e) => setFile(e.target.files[0])} 
                className="hidden" 
                accept=".csv"
              />
              <button 
                onClick={() => fileInputRef.current.click()}
                className="w-full max-w-sm flex items-center justify-center gap-3 px-8 py-4 bg-white text-black font-bold rounded-xl hover:bg-slate-200 transition-all text-lg"
              >
                {file ? <FileText size={20}/> : <Upload size={20} />}
                {file ? file.name : "Choose CSV File"}
              </button>
              
              {file && (
                <button 
                  onClick={handleUpload}
                  className="w-full max-w-sm flex items-center justify-center gap-3 px-8 py-4 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-500 transition-all shadow-xl shadow-blue-600/20 text-lg animate-bounce"
                >
                  Run Full Analysis
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}