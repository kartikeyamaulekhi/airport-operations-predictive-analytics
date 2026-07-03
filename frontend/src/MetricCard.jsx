export function MetricCard({ label, value, sub, accent }) {
  const colors = {
    blue:  { bg: '#eff6ff', border: '#bfdbfe', val: '#1d4ed8' },
    green: { bg: '#f0fdf4', border: '#bbf7d0', val: '#15803d' },
    red:   { bg: '#fef2f2', border: '#fecaca', val: '#b91c1c' },
    slate: { bg: '#f8fafc', border: '#e2e8f0', val: '#1e293b' },
  };
  const c = colors[accent] || colors.slate;
  return (
    <div style={{
      background: c.bg, border: `1px solid ${c.border}`,
      borderRadius: 12, padding: '20px 24px',
    }}>
      <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b',
        textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: '1.8rem', fontWeight: 700, color: c.val, lineHeight: 1 }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: 4 }}>{sub}</div>}
    </div>
  );
}
