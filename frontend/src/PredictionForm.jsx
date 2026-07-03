import { useState } from 'react';
import { api } from './api';
import { StatusBadge } from './StatusBadge';

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun',
                 'Jul','Aug','Sep','Oct','Nov','Dec'];

export function PredictionForm({ onNewPrediction }) {
  const now = new Date();
  const [form, setForm] = useState({
    year: now.getFullYear(),
    month: now.getMonth() + 1,
    arrFlights: 150,
    isSummer: [6,7,8].includes(now.getMonth()+1) ? 1 : 0,
    isWinterHoliday: [12,1].includes(now.getMonth()+1) ? 1 : 0,
    yearsSince2013: now.getFullYear() - 2013,
    airportAvgDelayRate: 0.183,
    carrierAvgDelayRate: 0.165,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function handleChange(e) {
    const { name, value } = e.target;
    setForm(f => {
      const updated = { ...f, [name]: parseFloat(value) || value };
      // Auto-derive computed fields when year/month change
      if (name === 'year') {
        updated.yearsSince2013 = parseFloat(value) - 2013;
      }
      if (name === 'month') {
        const m = parseInt(value);
        updated.isSummer = [6,7,8].includes(m) ? 1 : 0;
        updated.isWinterHoliday = [12,1].includes(m) ? 1 : 0;
      }
      return updated;
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const { data } = await api.predict(form);
      setResult(data);
      if (onNewPrediction) onNewPrediction();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const fieldStyle = {
    width: '100%', padding: '9px 12px', borderRadius: 8,
    border: '1px solid #e2e8f0', fontSize: '0.85rem', outline: 'none',
    background: '#fff',
  };
  const labelStyle = {
    display: 'block', marginBottom: 5,
    fontSize: '0.78rem', fontWeight: 600, color: '#475569',
  };

  return (
    <div style={{ background: '#fff', border: '1px solid #e2e8f0',
      borderRadius: 12, padding: 24 }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 600,
        color: '#1e293b', marginBottom: 4 }}>
        Delay Risk Prediction
      </h3>
      <p style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: 18 }}>
        Inputs feed directly into the XGBoost model (ROC-AUC 0.8296, real US DOT data).
      </p>

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <div>
            <label style={labelStyle}>Year</label>
            <input name="year" type="number" min="2013" max="2030"
              value={form.year} onChange={handleChange} style={fieldStyle} />
          </div>
          <div>
            <label style={labelStyle}>Month</label>
            <select name="month" value={form.month}
              onChange={handleChange} style={fieldStyle}>
              {MONTHS.map((m, i) => (
                <option key={m} value={i+1}>{m}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Total arriving flights</label>
            <input name="arrFlights" type="number" min="1"
              value={form.arrFlights} onChange={handleChange} style={fieldStyle} />
          </div>
          <div>
            <label style={labelStyle}>Airport avg delay rate</label>
            <input name="airportAvgDelayRate" type="number"
              min="0" max="1" step="0.001"
              value={form.airportAvgDelayRate} onChange={handleChange}
              style={fieldStyle} />
          </div>
          <div style={{ gridColumn: '1/-1' }}>
            <label style={labelStyle}>Carrier avg delay rate</label>
            <input name="carrierAvgDelayRate" type="number"
              min="0" max="1" step="0.001"
              value={form.carrierAvgDelayRate} onChange={handleChange}
              style={fieldStyle} />
          </div>
        </div>

        <div style={{ marginTop: 12, padding: '10px 12px',
          background: '#f8fafc', borderRadius: 8, fontSize: '0.75rem',
          color: '#64748b' }}>
          Auto-derived: is_summer={form.isSummer},
          is_winter_holiday={form.isWinterHoliday},
          years_since_2013={form.yearsSince2013}
        </div>

        <button type="submit" disabled={loading} style={{
          marginTop: 16, width: '100%', padding: '11px',
          background: loading ? '#94a3b8' : '#1e293b',
          color: '#fff', border: 'none', borderRadius: 8,
          fontWeight: 600, fontSize: '0.85rem',
          transition: 'background 0.2s',
        }}>
          {loading ? 'Running model…' : 'Run prediction'}
        </button>
      </form>

      {error && (
        <div style={{ marginTop: 14, padding: '10px 14px',
          background: '#fef2f2', border: '1px solid #fecaca',
          borderRadius: 8, fontSize: '0.82rem', color: '#991b1b' }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 16, padding: '16px',
          background: result.status === 'disruption_risk' ? '#fef2f2' : '#f0fdf4',
          border: `1px solid ${result.status === 'disruption_risk' ? '#fecaca' : '#bbf7d0'}`,
          borderRadius: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between',
            alignItems: 'center', marginBottom: 10 }}>
            <StatusBadge status={result.status} />
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
              ID #{result.historyId}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div style={{ background: '#fff', padding: '10px 12px',
              borderRadius: 8, border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                Delay probability
              </div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700,
                color: '#1e293b' }}>
                {(result.highDelayProbability * 100).toFixed(1)}%
              </div>
            </div>
            <div style={{ background: '#fff', padding: '10px 12px',
              borderRadius: 8, border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                Model version
              </div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700,
                color: '#1e293b' }}>
                {result.modelVersion}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
