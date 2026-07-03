import { StatusBadge } from './StatusBadge';

export function HistoryTable({ rows, loading }) {
  const thStyle = {
    padding: '10px 14px', textAlign: 'left',
    fontSize: '0.75rem', fontWeight: 600,
    color: '#64748b', textTransform: 'uppercase',
    letterSpacing: '0.04em', borderBottom: '2px solid #f1f5f9',
  };
  const tdStyle = {
    padding: '11px 14px', fontSize: '0.83rem',
    color: '#334155', borderBottom: '1px solid #f8fafc',
  };

  return (
    <div style={{ background: '#fff', border: '1px solid #e2e8f0',
      borderRadius: 12, padding: 24 }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 600,
        color: '#1e293b', marginBottom: 16 }}>
        Recent Predictions (last 20)
      </h3>

      {loading && (
        <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Loading…</p>
      )}

      {!loading && rows.length === 0 && (
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', textAlign: 'center',
          padding: '24px 0' }}>
          No predictions yet — run one above
        </p>
      )}

      {rows.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={thStyle}>ID</th>
                <th style={thStyle}>Year / Month</th>
                <th style={thStyle}>Probability</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>Recorded at</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.id} style={{ transition: 'background 0.1s' }}
                  onMouseEnter={e => e.currentTarget.style.background='#f8fafc'}
                  onMouseLeave={e => e.currentTarget.style.background='transparent'}>
                  <td style={{ ...tdStyle, fontFamily: 'monospace',
                    color: '#94a3b8' }}>#{r.id}</td>
                  <td style={tdStyle}>{r.year} / {String(r.month).padStart(2,'0')}</td>
                  <td style={tdStyle}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ flex: 1, height: 6, background: '#f1f5f9',
                        borderRadius: 3, maxWidth: 80 }}>
                        <div style={{
                          height: '100%', borderRadius: 3,
                          width: `${r.highDelayProbability * 100}%`,
                          background: r.highDelayProbability > 0.5
                            ? '#ef4444' : '#22c55e',
                        }} />
                      </div>
                      <span style={{ fontSize: '0.78rem', fontWeight: 600 }}>
                        {(r.highDelayProbability * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td style={tdStyle}>
                    <StatusBadge status={r.status} />
                  </td>
                  <td style={{ ...tdStyle, color: '#94a3b8', fontSize: '0.78rem' }}>
                    {new Date(r.createdAt).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
