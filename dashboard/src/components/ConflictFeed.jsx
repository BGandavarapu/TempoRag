function ConflictBadge({ type }) {
  const styles =
    type === 'flat'
      ? 'bg-red-950 text-red-400 border border-red-800'
      : 'bg-amber-950 text-amber-400 border border-amber-800';
  const label = type === 'temporal_supersession' ? 'superseded' : type;
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles}`}>{label}</span>
  );
}

export default function ConflictFeed({ conflicts }) {
  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 h-full">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">
        Recent Conflicts
      </h2>
      {conflicts.length === 0 ? (
        <p className="text-gray-600 text-sm">No conflicts detected yet</p>
      ) : (
        <ul className="space-y-3">
          {conflicts.map((c, i) => (
            <li key={i} className="border border-gray-800 rounded-lg p-3 space-y-2">
              <div className="flex items-center gap-2">
                <ConflictBadge type={c.conflict_type} />
                <span className="text-xs text-gray-600">{c.date_delta_days}d apart</span>
              </div>
              <p className="text-xs text-gray-300 truncate font-medium">{c.source_a}</p>
              <p className="text-xs text-gray-600 leading-none">vs</p>
              <p className="text-xs text-gray-300 truncate font-medium">{c.source_b}</p>
              <p className="text-xs text-gray-700">
                {c.date_a} &rarr; {c.date_b}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
