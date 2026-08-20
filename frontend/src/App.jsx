import { useState, useRef, useEffect } from 'react';

const API_URL = 'http://localhost:3000/api';

function LoginScreen({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    const endpoint = isRegister ? '/auth/register' : '/auth/login';
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.token) {
      localStorage.setItem('token', data.token);
      onLogin(data.token);
    } else {
      alert(data.error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-800 via-slate-900 to-black text-white">
      <form onSubmit={handleSubmit} className="glass-panel p-8 w-96 flex flex-col gap-4">
        <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
          {isRegister ? 'Register' : 'Login'}
        </h2>
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} className="bg-slate-800/50 border border-slate-700 p-3 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" required />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className="bg-slate-800/50 border border-slate-700 p-3 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" required />
        <button type="submit" className="premium-btn-primary mt-2">{isRegister ? 'Sign Up' : 'Sign In'}</button>
        <button type="button" onClick={() => setIsRegister(!isRegister)} className="text-sm text-indigo-400 mt-2">
          {isRegister ? 'Already have an account? Login' : 'Need an account? Register'}
        </button>
      </form>
    </div>
  );
}

function Controls({ ticker, setTicker, question, setQuestion, onRun, isStreaming }) {
  return (
    <div className="glass-panel p-6 mb-8 w-full">
      <h2 className="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
        LetsFin AI Equity Analyst
      </h2>
      <div className="flex flex-col gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Ticker</label>
          <input 
            type="text" 
            value={ticker} 
            onChange={e => setTicker(e.target.value.toUpperCase())}
            placeholder="AAPL"
            className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            disabled={isStreaming}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Research Question</label>
          <textarea 
            value={question} 
            onChange={e => setQuestion(e.target.value)}
            placeholder="Analyse AAPL: give me its ROE, free cash flow, and 1-year price range."
            className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none min-h-[100px]"
            disabled={isStreaming}
          />
        </div>
        {/* We removed the explicit threadId input because Express owns it now (Requirement 2) */}
        <button 
          onClick={onRun} 
          disabled={isStreaming || !ticker || !question}
          className="premium-btn-primary w-full mt-2 flex justify-center items-center gap-2"
        >
          {isStreaming ? (
            <><span className="animate-pulse">●</span> Researching...</>
          ) : (
            'Run New Research'
          )}
        </button>
      </div>
    </div>
  );
}

function EventLog({ events }) {
  if (events.length === 0) return null;
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  return (
    <div className="glass-panel p-6 mb-8 w-full">
      <h3 className="text-lg font-semibold mb-4 text-slate-300">Activity Log</h3>
      <div className="space-y-3 max-h-60 overflow-y-auto pr-2">
        {events.map((ev, i) => (
          <div key={i} className="flex items-start gap-3 text-sm">
            <span className="text-indigo-400 font-mono mt-0.5">❯</span>
            <div>
              <span className="font-semibold text-slate-200">{ev.node}</span>
              {ev.summary && <span className="text-slate-400 ml-2">{ev.summary}</span>}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

function MemoView({ draft, isFinal, onResume, isStreaming }) {
  if (!draft) return null;

  return (
    <div className="glass-panel p-8 w-full mb-12 relative overflow-hidden">
      {!isFinal && (
        <div className="absolute top-0 left-0 w-full bg-amber-500/20 border-b border-amber-500/30 text-amber-200 text-center py-2 text-sm font-semibold">
          Draft Pending Human Approval
        </div>
      )}
      <div className={`mt-${!isFinal ? '6' : '0'}`}>
        <h1 className="text-3xl font-bold mb-6 text-white text-center">Investment Memo</h1>
        
        <div className="space-y-8 text-slate-300">
          <section>
            <h3 className="text-xl font-semibold text-indigo-300 mb-3 border-b border-white/10 pb-2">Thesis</h3>
            <p className="leading-relaxed">{draft.thesis}</p>
          </section>

          <div className="grid md:grid-cols-2 gap-8">
            <section>
              <h3 className="text-xl font-semibold text-emerald-400 mb-3 border-b border-white/10 pb-2">Strengths</h3>
              <ul className="list-disc list-inside space-y-2">
                {(draft.strengths || []).map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </section>

            <section>
              <h3 className="text-xl font-semibold text-rose-400 mb-3 border-b border-white/10 pb-2">Risks</h3>
              <ul className="list-disc list-inside space-y-2">
                {(draft.risks || []).map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </section>
          </div>

          <section>
            <h3 className="text-xl font-semibold text-amber-300 mb-3 border-b border-white/10 pb-2">Valuation</h3>
            <p className="leading-relaxed">{draft.valuation_summary}</p>
          </section>
        </div>

        {!isFinal && (
          <div className="mt-10 flex gap-4 justify-center">
            <button 
              onClick={() => onResume('approve')} 
              disabled={isStreaming}
              className="premium-btn bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 hover:bg-emerald-500/30"
            >
              Approve Memo
            </button>
            <button 
              onClick={() => onResume('reject')} 
              disabled={isStreaming}
              className="premium-btn bg-rose-500/20 text-rose-400 border border-rose-500/50 hover:bg-rose-500/30"
            >
              Request Changes
            </button>
          </div>
        )}

        <footer className="mt-12 pt-6 border-t border-white/10 text-center text-xs text-slate-500">
          Generated analysis. Not investment advice. • {new Date().toLocaleString()}
        </footer>
      </div>
    </div>
  );
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  
  // Warm-up ping to mitigate Render free-tier cold starts
  useEffect(() => {
    fetch(`${API_URL}/health`).catch(() => {});
  }, []);
  
  const [ticker, setTicker] = useState('AAPL');
  const [question, setQuestion] = useState('Analyse AAPL: give me its ROE, free cash flow, and 1-year price range.');
  
  const [activeReportId, setActiveReportId] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [events, setEvents] = useState([]);
  const [draft, setDraft] = useState(null);
  const [isFinal, setIsFinal] = useState(false);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (token) fetchHistory();
  }, [token]);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/reports`, { headers: { 'Authorization': `Bearer ${token}` } });
      const data = await res.json();
      setHistory(data);
    } catch (e) {
      console.error(e);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  if (!token) return <LoginScreen onLogin={setToken} />;

  const readStream = async (response, reportId) => {
    if (!response.body) return;
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';

      for (const part of parts) {
        if (part.startsWith('data: ')) {
          try {
            const data = JSON.parse(part.slice(6));
            
            if (data.type === 'node') {
              setEvents(prev => [...prev, data]);
            } else if (data.type === 'interrupt') {
              let parsedDraft = data.draft;
              if (typeof parsedDraft === 'string') {
                try { parsedDraft = JSON.parse(parsedDraft); } catch(e) {}
              }
              setDraft(parsedDraft);
              setIsStreaming(false);
              fetchHistory();
              return;
            } else if (data.type === 'final') {
              let parsedMemo = data.memo;
              if (typeof parsedMemo === 'string') {
                try { parsedMemo = JSON.parse(parsedMemo); } catch(e) {}
              }
              setDraft(parsedMemo);
              setIsFinal(true);
              setIsStreaming(false);
              fetchHistory();
              return;
            } else if (data.type === 'error') {
              setEvents(prev => [...prev, { node: 'Error', summary: data.message }]);
              setIsStreaming(false);
              fetchHistory();
              return;
            }
          } catch (err) {
            console.error('JSON Parse error', err, part);
          }
        }
      }
    }
    setIsStreaming(false);
    fetchHistory();
  };

  const startResearch = async () => {
    setIsStreaming(true);
    setEvents([]);
    setDraft(null);
    setIsFinal(false);
    setActiveReportId(null);
    
    try {
      const res = await fetch(`${API_URL}/research`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ ticker, question })
      });
      // The backend should return the new Report ID either in a header or as the first SSE chunk,
      // but for simplicity, we let the history refresh pick it up.
      await readStream(res, null);
    } catch (err) {
      console.error(err);
      setIsStreaming(false);
    }
  };

  const handleResume = async (decision) => {
    if (!activeReportId) {
      alert("Please select a report from the history to resume.");
      return;
    }
    setIsStreaming(true);
    setDraft(null); 
    setEvents(prev => [...prev, { node: 'human_approval', summary: `Decision: ${decision}` }]);

    try {
      const res = await fetch(`${API_URL}/research/${activeReportId}/approve`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ decision })
      });
      await readStream(res, activeReportId);
    } catch (err) {
      console.error(err);
      setIsStreaming(false);
    }
  };

  const loadReport = (rep) => {
    setActiveReportId(rep._id);
    setTicker(rep.ticker);
    setQuestion(rep.question);
    
    // Check if it's already complete or awaiting approval
    if (rep.status === 'complete') {
      setIsFinal(true);
      setDraft(rep.memo);
      setEvents([{ node: 'System', summary: 'Loaded completed report from history' }]);
    } else if (rep.status === 'awaiting_approval') {
      setIsFinal(false);
      setDraft(rep.memo);
      setEvents([{ node: 'System', summary: 'Loaded draft awaiting approval from history' }]);
    } else {
      setIsFinal(false);
      setDraft(null);
      setEvents([{ node: 'System', summary: `Report status is ${rep.status}` }]);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-800 via-slate-900 to-black flex">
      {/* Sidebar for History */}
      <div className="w-80 bg-slate-900/80 border-r border-white/10 p-4 flex flex-col h-screen sticky top-0">
        <div className="flex justify-between items-center mb-6">
          <h3 className="font-bold text-white text-lg">History</h3>
          <button onClick={logout} className="text-xs text-indigo-400 hover:text-indigo-300">Logout</button>
        </div>
        <div className="flex-1 overflow-y-auto space-y-2 pr-2">
          {history.map(rep => (
            <div 
              key={rep._id} 
              onClick={() => loadReport(rep)}
              className={`p-3 rounded-lg cursor-pointer border ${activeReportId === rep._id ? 'bg-indigo-500/20 border-indigo-500/50' : 'bg-slate-800/50 border-white/5 hover:bg-slate-800'}`}
            >
              <div className="flex justify-between">
                <span className="font-bold text-slate-200">{rep.ticker}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${rep.status === 'complete' ? 'bg-emerald-500/20 text-emerald-400' : rep.status === 'awaiting_approval' ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-500/20 text-slate-400'}`}>
                  {rep.status}
                </span>
              </div>
              <div className="text-xs text-slate-500 mt-1 truncate">{new Date(rep.createdAt).toLocaleString()}</div>
            </div>
          ))}
          {history.length === 0 && <p className="text-slate-500 text-sm italic">No past reports</p>}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8 overflow-y-auto h-screen">
        <div className="max-w-4xl mx-auto">
          <Controls 
            ticker={ticker} setTicker={setTicker}
            question={question} setQuestion={setQuestion}
            onRun={startResearch} isStreaming={isStreaming}
          />
          <EventLog events={events} />
          <MemoView draft={draft} isFinal={isFinal} onResume={handleResume} isStreaming={isStreaming} />
        </div>
      </div>
    </div>
  );
}
