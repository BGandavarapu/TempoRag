const ACTION_STYLES = {
  answer: 'bg-green-950 text-green-400 border-green-800',
  warn_stale: 'bg-amber-950 text-amber-400 border-amber-800',
  surface_conflict: 'bg-red-950 text-red-400 border-red-800',
  surface_supersession: 'bg-orange-950 text-orange-400 border-orange-800',
  refuse: 'bg-gray-800 text-gray-500 border-gray-700',
};

function ActionBadge({ action }) {
  const styles = ACTION_STYLES[action] ?? 'bg-gray-800 text-gray-500 border-gray-700';
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium border flex-shrink-0 ${styles}`}>
      {action.replace(/_/g, ' ')}
    </span>
  );
}

function FreshnessBar({ score }) {
  const color =
    score > 0.7 ? 'bg-green-500' : score >= 0.4 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2 flex-shrink-0">
      <div className="w-16 bg-gray-800 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full`} style={{ width: `${score * 100}%` }} />
      </div>
      <span className="text-xs text-gray-600 w-8 text-right">
        {(score * 100).toFixed(0)}%
      </span>
    </div>
  );
}

export default function QueryAuditTrail({ queries }) {
  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">
        Query Audit Trail
      </h2>
      {queries.length === 0 ? (
        <p className="text-gray-600 text-sm">No queries yet</p>
      ) : (
        <div className="space-y-2">
          {queries.map((q, i) => (
            <div
              key={i}
              className="flex items-center gap-3 border border-gray-800 rounded-lg px-3 py-2.5"
            >
              <p className="text-sm text-gray-200 truncate flex-1 min-w-0">{q.query}</p>
              <ActionBadge action={q.recommended_action} />
              <FreshnessBar score={q.freshness_score} />
              <span className="text-xs text-gray-700 flex-shrink-0 hidden xl:block">
                {q.source_count} src
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
