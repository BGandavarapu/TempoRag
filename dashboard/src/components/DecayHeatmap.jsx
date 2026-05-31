import { ResponsiveContainer, Tooltip, Treemap } from 'recharts';

function freshColor(f) {
  if (f > 0.7) return '#22c55e';
  if (f >= 0.4) return '#f59e0b';
  return '#ef4444';
}

function renderCell(props) {
  const { x, y, width, height, name, avg_freshness } = props;
  return (
    <g>
      <rect
        x={x} y={y} width={width} height={height}
        fill={freshColor(avg_freshness ?? 0)}
        stroke="#030712"
        strokeWidth={3}
      />
      {width > 56 && height > 28 && (
        <>
          <text
            x={x + width / 2} y={y + height / 2 - 7}
            textAnchor="middle" fill="#fff" fontSize={13} fontWeight="600"
          >
            {name}
          </text>
          <text
            x={x + width / 2} y={y + height / 2 + 9}
            textAnchor="middle" fill="rgba(255,255,255,0.7)" fontSize={11}
          >
            {((avg_freshness ?? 0) * 100).toFixed(0)}%
          </text>
        </>
      )}
    </g>
  );
}

function HeatmapTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm shadow-xl">
      <p className="font-semibold text-white capitalize mb-1">{d.name}</p>
      <p className="text-gray-300">{d.size} chunks</p>
      <p style={{ color: freshColor(d.avg_freshness) }}>
        {(d.avg_freshness * 100).toFixed(1)}% fresh
      </p>
      <p className="text-gray-500">{d.stale_count} stale (&lt;40%)</p>
    </div>
  );
}

export default function DecayHeatmap({ domains }) {
  const data = domains.map((d) => ({
    name: d.domain.toUpperCase(),
    size: d.chunk_count,
    avg_freshness: d.avg_freshness,
    stale_count: d.stale_count,
  }));

  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">
        Knowledge Decay by Domain
      </h2>
      {data.length === 0 ? (
        <div className="h-36 flex items-center justify-center text-gray-600 text-sm">
          No chunks ingested yet — run seed_data.py
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <Treemap data={data} dataKey="size" content={renderCell}>
            <Tooltip content={<HeatmapTooltip />} />
          </Treemap>
        </ResponsiveContainer>
      )}
    </div>
  );
}
