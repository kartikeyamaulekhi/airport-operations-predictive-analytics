import { useState, useCallback } from 'react';
import { api } from './api';
import { useAutoRefresh } from './useAutoRefresh';
import { MetricCard } from './MetricCard';
import { AlertPanel } from './AlertPanel';
import { ForecastChart } from './ForecastChart';
import { PredictionForm } from './PredictionForm';
import { HistoryTable } from './HistoryTable';
import './index.css';

const REFRESH_MS = 5 * 60 * 1000; // 5 minutes

export default function App() {
  const [health,   setHealth]   = useState(null);
  const [summary,  setSummary]  = useState(null);
  const [alerts,   setAlerts]   = useState([]);
  const [history,  setHistory]  = useState([]);
  const [forecast, setForecast] = useState([]);
  const [forecastMeta, setForecastMeta] = useState({});
  const [lastRefresh, setLastRefresh] = useState(null);
  const [error,    setError]    = useState('');

  const [loadingHealth,   setLoadingHealth]   = useState(true);
  const [loadingSummary,  setLoadingSummary]  = useState(true);
  const [loadingAlerts,   setLoadingAlerts]   = useState(true);
  const [loadingHistory,  setLoadingHistory]  = useState(true);
  const [loadingForecast, setLoadingForecast] = useState(true);

  const fetchAll = useCallback(async () => {
    setError('');

    // Health
    setLoadingHealth(true);
    try {
      const { data } = await api.health();
      setHealth(data);
    } catch {
      setHealth({ status: 'unreachable', backend: 'DOWN', ml_service: 'DOWN' });
      setError('Backend unreachable — ensure Spring Boot is running on :8080');
    } finally { setLoadingHealth(false); }

    // Dashboard summary
    setLoadingSummary(true);
    try {
      const { data } = await api.dashboardSummary();
      setSummary(data);
    } catch { setSummary(null); }
    finally { setLoadingSummary(false); }

    // Alerts
    setLoadingAlerts(true);
    try {
      const { data } = await api.alerts();
      setAlerts(data);
    } catch { setAlerts([]); }
    finally { setLoadingAlerts(false); }

    // History
    setLoadingHistory(true);
    try {
      const { data } = await api.history();
      setHistory(data);
    } catch { setHistory([]); }
    finally { setLoadingHistory(false); }

    // Forecast
    setLoadingForecast(true);
    try {
      const { data } = await api.forecast(30);
      setForecast(data.forecast || []);
      setForecastMeta({ mae: data.modelMae, mape: data.modelMapePct });
    } catch { setForecast([]); }
    finally { setLoadingForecast(false); }

    setLastRefresh(new Date());
  }, []);

  // Auto-refresh every 5 minutes — no human needed
  useAutoRefresh(fetchAll, REFRESH_MS);

  const mlUp = health?.ml_service === 'UP';
  const beUp = health?.backend   === 'UP';

  return (
    <div style={{ minHeight: '100vh', background: '#f1f5f9' }}>
      {/* Top bar */}
      <div style={{ background: '#0f172a', padding: '0 32px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        height: 56 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
            ✈ Airport Operations Analytics
          </span>
          <span style={{ fontSize: '0.72rem', background: '#1e293b',
            color: '#94a3b8', padding: '2px 8px', borderRadius: 6 }}>
            Lucknow International · Adani Group
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <ServiceDot label="ML Service" up={mlUp} loading={loadingHealth} />
          <ServiceDot label="Backend"    up={beUp} loading={loadingHealth} />
          {lastRefresh && (
            <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
              Refreshed {lastRefresh.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      <div style={{ padding: '28px 32px', maxWidth: 1400, margin: '0 auto' }}>
        {/* Page title */}
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a',
            margin: 0 }}>
            Operations Dashboard
          </h1>
          <p style={{ fontSize: '0.83rem', color: '#64748b', marginTop: 4 }}>
            XGBoost delay model · ROC-AUC 0.8296 · Prophet traffic forecast ·
            MAPE {forecastMeta.mape ? forecastMeta.mape.toFixed(2) : '3.18'}% ·
            Auto-refreshes every 5 min
          </p>
        </div>

        {error && (
          <div style={{ marginBottom: 20, padding: '12px 16px',
            background: '#fef2f2', border: '1px solid #fecaca',
            borderRadius: 8, fontSize: '0.83rem', color: '#991b1b' }}>
            ⚠ {error}
          </div>
        )}

        {/* Metric cards */}
        <div style={{ display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
          <MetricCard
            label="Total predictions"
            value={loadingSummary ? '…' : (summary?.totalPredictions ?? 0)}
            sub="stored in database"
            accent="blue"
          />
          <MetricCard
            label="High-risk detections"
            value={loadingSummary ? '…' : (summary?.highRiskCount ?? 0)}
            sub={summary ? `${summary.highRiskPercentage}% of total` : ''}
            accent="red"
          />
          <MetricCard
            label="Model ROC-AUC"
            value="0.8296"
            sub="XGBoost · real DOT data"
            accent="green"
          />
          <MetricCard
            label="Forecast MAPE"
            value={forecastMeta.mape ? `${forecastMeta.mape.toFixed(2)}%` : '3.18%'}
            sub={forecastMeta.mae ? `MAE ${forecastMeta.mae.toLocaleString()} pax/day` : 'Prophet model'}
            accent="slate"
          />
        </div>

        {/* Forecast chart */}
        <div style={{ background: '#fff', border: '1px solid #e2e8f0',
          borderRadius: 12, padding: 24, marginBottom: 24 }}>
          <div style={{ marginBottom: 16 }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600,
              color: '#1e293b', margin: 0 }}>
              30-Day Passenger Traffic Forecast
            </h3>
            <p style={{ fontSize: '0.78rem', color: '#64748b', marginTop: 4 }}>
              Prophet time-series model · shaded area = 95% confidence interval ·
              updated automatically
            </p>
          </div>
          <ForecastChart data={forecast} loading={loadingForecast} />
        </div>

        {/* Middle row: form + alerts */}
        <div style={{ display: 'grid',
          gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
          <PredictionForm onNewPrediction={fetchAll} />
          <AlertPanel alerts={alerts} loading={loadingAlerts} />
        </div>

        {/* History table */}
        <HistoryTable rows={history} loading={loadingHistory} />

        {/* Footer */}
        <div style={{ marginTop: 24, textAlign: 'center',
          fontSize: '0.75rem', color: '#94a3b8' }}>
          Airport Operations Predictive Analytics ·
          Python FastAPI + Java Spring Boot + React ·
          Real US DOT/BTS data (2013–2023) ·
          Built during internship at Lucknow International Airport (Adani Group)
        </div>
      </div>
    </div>
  );
}

function ServiceDot({ label, up, loading }) {
  const color = loading ? '#64748b' : up ? '#22c55e' : '#ef4444';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%',
        background: color }} />
      <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{label}</span>
    </div>
  );
}
