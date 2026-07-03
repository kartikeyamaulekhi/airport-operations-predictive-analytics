import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from 'recharts';

function fmt(dateStr) {
  const d = new Date(dateStr);
  return `${d.getMonth()+1}/${d.getDate()}`;
}

export function ForecastChart({ data, loading }) {
  if (loading) return (
    <div style={{ height: 260, display: 'flex', alignItems: 'center',
      justifyContent: 'center', color: '#94a3b8', fontSize: '0.85rem' }}>
      Loading forecast…
    </div>
  );

  if (!data || data.length === 0) return (
    <div style={{ height: 260, display: 'flex', alignItems: 'center',
      justifyContent: 'center', color: '#94a3b8', fontSize: '0.85rem' }}>
      No forecast data available
    </div>
  );

  const chartData = data.map(p => ({
    date: fmt(p.date),
    predicted: p.predictedFootfall,
    upper: p.upperBound,
    lower: p.lowerBound,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={chartData}
        margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="gradPred" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25}/>
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
          </linearGradient>
          <linearGradient id="gradConf" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.15}/>
            <stop offset="95%" stopColor="#94a3b8" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }}
          tickLine={false} axisLine={false} />
        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }}
          tickLine={false} axisLine={false}
          tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
        <Tooltip
          formatter={(v, name) => [v.toLocaleString(), name]}
          contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0',
            fontSize: '0.8rem' }} />
        <Legend wrapperStyle={{ fontSize: '0.8rem' }} />
        <Area type="monotone" dataKey="upper" stroke="none"
          fill="url(#gradConf)" name="Upper bound" />
        <Area type="monotone" dataKey="lower" stroke="none"
          fill="#fff" name="Lower bound" />
        <Area type="monotone" dataKey="predicted" stroke="#3b82f6"
          strokeWidth={2} fill="url(#gradPred)" name="Predicted footfall" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
