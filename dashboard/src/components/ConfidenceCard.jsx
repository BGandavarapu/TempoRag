const ACTION_STYLES = {
  answer: { bg: 'bg-green-950', text: 'text-green-400', border: 'border-green-800' },
  warn_stale: { bg: 'bg-amber-950', text: 'text-amber-400', border: 'border-amber-800' },
  surface_conflict: { bg: 'bg-red-950', text: 'text-red-400', border: 'border-red-800' },
  surface_supersession: { bg: 'bg-orange-950', text: 'text-orange-400', border: 'border-orange-800' },
  refuse: { bg: 'bg-gray-800', text: 'text-gray-500', border: 'border-gray-700' },
};

function Meter({ label, value }) {
  const pct = Math.max(0, Math.min(1, value));
  const color = pct > 0.7 ? 'bg-green-500' : pct >= 0.4 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-gray-500">
        <span>{label}</span>
        <span className="text-gray-300">{(pct * 100).toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${pct * 100}%` }} />
      </div>
    </div>
  );
}

export default function ConfidenceCard({ confidence }) {
  if (!confidence) return null;

  const {
    semantic_score = 0,
    freshness_score = 0,
    source_agreement = 0,
    conflict_type = 'none',
    recommended_action = 'answer',
    sources_used = [],
  } = confidence;

  const style = ACTION_STYLES[recommended_action] ?? ACTION_STYLES.answer;

  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
          Response Confidence
        </h2>
        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${style.bg} ${style.text} ${style.border}`}>
          {recommended_action.replace(/_/g, ' ')}
        </span>
      </div>

      <div className="space-y-3">
        <Meter label="Semantic relevance" value={semantic_score} />
        <Meter label="Source freshness" value={freshness_score} />
        <Meter label="Source agreement" value={source_agreement} />
      </div>

      {conflict_type !== 'none' && (
        <p className="text-xs text-amber-400 bg-amber-950 border border-amber-800 rounded px-2 py-1">
          Conflict detected: {conflict_type.replace(/_/g, ' ')}
        </p>
      )}

      {sources_used.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-gray-600">Sources used</p>
          <ul className="space-y-0.5">
            {sources_used.map((s) => (
              <li key={s} className="text-xs text-gray-400 truncate">{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
