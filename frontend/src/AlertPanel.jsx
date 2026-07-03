import { StatusBadge } from './StatusBadge';

export function AlertPanel({ alerts, loading }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e2e8f0',
      borderRadius: 12, padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', marginBottom: 16 }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#1e293b' }}>
          High-Risk Alerts
        </h3>
        <span style={{ background: '#fee2e2', color: '#991b1b',
          fontSize: '0.75rem', fontWeight: 700,
          padding: '2px 8px', borderRadius: 8 }}>
          {loading ? '…' : alerts.length} active
        </span>
      </div>

      {loading && (
        <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Loading alerts…</p>
      )}

      {!loading && alerts.length === 0 && (
        <div style={{ textAlign: 'center', padding: '24px 0',
          color: '#64748b', fontSize: '0.85rem' }}>
          ✅ No high-risk predictions in history
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {alerts.map(a => (
          <div key={a.id} style={{
            background: '#fef2f2', border: '1px solid #fecaca',
            borderRadius: 8, padding: '12px 14px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#1e293b' }}>
                {a.year}/{String(a.month).padStart(2,'0')} — Prob: {(a.highDelayProbability * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 2 }}>
                {new Date(a.createdAt).toLocaleString()}
              </div>
            </div>
            <StatusBadge status={a.status} />
          </div>
        ))}
      </div>
    </div>
  );
}
