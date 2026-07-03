export function StatusBadge({ status }) {
  const isRisk = status === 'disruption_risk';
  const style = {
    display: 'inline-block',
    padding: '3px 10px',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: 600,
    background: isRisk ? '#fee2e2' : '#dcfce7',
    color: isRisk ? '#991b1b' : '#166534',
  };
  return <span style={style}>{isRisk ? 'High Risk' : 'Nominal'}</span>;
}
