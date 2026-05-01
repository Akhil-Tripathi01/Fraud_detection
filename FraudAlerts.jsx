import { useEffect, useState } from 'react';
import { CheckCircle2, RefreshCw } from 'lucide-react';
import { fraudApi } from './api';

const statusOptions = ['open', 'investigating', 'resolved', 'false_positive'];

const FraudAlerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [status, setStatus] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fraudApi.alerts({ status, limit: 100 });
      setAlerts(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Alerts could not be loaded.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const updateStatus = async (alertId, nextStatus) => {
    try {
      const updated = await fraudApi.updateAlert(alertId, { status: nextStatus, note: `Marked ${nextStatus} from alert queue.` });
      setAlerts((prev) => prev.map((alert) => (alert.id === alertId ? updated : alert)));
    } catch (err) {
      setError(err.response?.data?.detail || 'Alert status could not be updated.');
    }
  };

  return (
    <div className="page-stack">
      <div className="page-header split">
        <div>
          <p className="eyebrow">Triage</p>
          <h1>Fraud alerts</h1>
        </div>
        <div className="toolbar">
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="all">All statuses</option>
            {statusOptions.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <button className="secondary-button" type="button" onClick={load}>
            <RefreshCw size={18} />
            Load
          </button>
        </div>
      </div>

      {error && <div className="state-panel error">{error}</div>}
      {loading ? (
        <div className="state-panel">Loading alerts...</div>
      ) : (
        <section className="alert-grid">
          {alerts.map((alert) => (
            <article className="alert-card" key={alert.id}>
              <div className="alert-top">
                <span className={`severity ${alert.severity}`}>{alert.severity}</span>
                <span className="score">{Math.round(alert.risk_score || 0)}</span>
              </div>
              <h2>{alert.alert_type}</h2>
              <p>{alert.description}</p>
              <dl>
                <div>
                  <dt>Transaction</dt>
                  <dd>{alert.transaction_id}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{alert.status}</dd>
                </div>
              </dl>
              <div className="card-actions">
                <select value={alert.status} onChange={(event) => updateStatus(alert.id, event.target.value)}>
                  {statusOptions.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
                <button className="icon-button success" type="button" onClick={() => updateStatus(alert.id, 'resolved')} title="Resolve alert">
                  <CheckCircle2 size={18} />
                </button>
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
};

export default FraudAlerts;
