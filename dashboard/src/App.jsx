import { useEffect, useRef, useState } from 'react';
import ConfidenceCard from './components/ConfidenceCard';
import ConflictFeed from './components/ConflictFeed';
import DecayHeatmap from './components/DecayHeatmap';
import QueryAuditTrail from './components/QueryAuditTrail';

export default function App() {
  const [snapshot, setSnapshot] = useState(null);
  const [snapshotError, setSnapshotError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState(null);

  const inputRef = useRef(null);

  const fetchSnapshot = async () => {
    try {
      const res = await fetch('/api/dashboard/snapshot');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSnapshot(await res.json());
      setLastUpdated(new Date());
      setSnapshotError(null);
    } catch (e) {
      setSnapshotError(e.message);
    }
  };

  useEffect(() => {
    fetchSnapshot();
    const id = setInterval(fetchSnapshot, 10000);
    return () => clearInterval(id);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;

    setQueryLoading(true);
    setQueryResult(null);
    setQueryError(null);

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setQueryResult(data);
      fetchSnapshot();
    } catch (e) {
      setQueryError(e.message);
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Temporal Knowledge RAG</h1>
          <p className="text-xs text-gray-500 mt-0.5">Knowledge Decay Dashboard</p>
        </div>
        <div className="text-right text-xs">
          {snapshotError && <p className="text-red-400 mb-0.5">API error: {snapshotError}</p>}
          {snapshot && (
            <p className="text-gray-400">
              {snapshot.total_chunks} chunks &middot;{' '}
              {(snapshot.avg_freshness_overall * 100).toFixed(1)}% avg freshness
            </p>
          )}
          {lastUpdated && (
            <p className="text-gray-600 mt-0.5">updated {lastUpdated.toLocaleTimeString()}</p>
          )}
        </div>
      </header>

      <main className="p-6 space-y-6">
        {/* Query input */}
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about the knowledge base…"
            disabled={queryLoading}
            className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm
                       text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500
                       disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={queryLoading || !query.trim()}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40
                       disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors
                       whitespace-nowrap"
          >
            {queryLoading ? 'Querying…' : 'Submit'}
          </button>
        </form>

        {/* Query result */}
        {queryError && (
          <div className="bg-red-950 border border-red-800 rounded-xl p-4 text-sm text-red-400">
            Query failed: {queryError}
          </div>
        )}

        {queryResult && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">Answer</h2>
              <p className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
                {queryResult.answer}
              </p>
            </div>
            <div className="lg:col-span-1">
              <ConfidenceCard confidence={queryResult} />
            </div>
          </div>
        )}

        {/* Snapshot panels */}
        {!snapshot ? (
          <div className="flex items-center justify-center h-64 text-gray-600 text-sm">
            {snapshotError ? 'Failed to connect to API — is the backend running?' : 'Connecting…'}
          </div>
        ) : (
          <>
            <DecayHeatmap domains={snapshot.domains} />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <ConflictFeed conflicts={snapshot.recent_conflicts} />
              </div>
              <div className="lg:col-span-2">
                <QueryAuditTrail queries={snapshot.recent_queries} />
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
