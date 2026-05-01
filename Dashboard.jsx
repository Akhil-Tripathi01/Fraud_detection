import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  BadgeIndianRupee,
  CheckCircle2,
  CircleDollarSign,
  ShieldAlert,
  Users,
} from 'lucide-react';
import { dashboardApi, fraudApi, transactionsApi } from './api';

const formatMoney = (value) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0);

const RiskPill = ({ value }) => <span className={`risk-pill ${value}`}>{value}</span>;

const MetricCard = ({ title, value, detail, icon: Icon, tone }) => (
  <article className={`metric-card ${tone || ''}`}>
    <div>
      <span>{title}</span>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </div>
    <Icon size={24} />
  </article>
);

const MiniBars = ({ rows }) => {
  const max = Math.max(1, ...rows.map((row) => row.count));
  return (
    <div className="mini-bars">
      {rows.map((row) => (
        <div className="bar-row" key={row.date}>
          <span>{row.date.slice(5)}</span>
          <div>
            <i style={{ width: `${(row.count / max) * 100}%` }} />
          </div>
          <b>{row.count}</b>
        </div>
      ))}
    </div>
  );
};

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [stats, setStats] = useState(null);
  const [risk, setRisk] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const [summaryData, statsData, riskData, txData, alertData] = await Promise.all([
          dashboardApi.summary(),
          dashboardApi.stats(),
          dashboardApi.riskDistribution(),
          transactionsApi.list({ limit: 6 }),
          fraudApi.alerts({ limit: 5 }),
        ]);
        setSummary(summaryData);
        setStats(statsData);
        setRisk(riskData);
        setTransactions(txData);
        setAlerts(alertData);
      } catch (err) {
        setError(err.response?.data?.detail || 'Dashboard data could not be loaded.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const riskRows = useMemo(
    () => [
      { label: 'Low', value: risk?.low || 0, percent: risk?.low_percent || 0, className: 'low' },
      { label: 'Medium', value: risk?.medium || 0, percent: risk?.medium_percent || 0, className: 'medium' },
      { label: 'High', value: risk?.high || 0, percent: risk?.high_percent || 0, className: 'high' },
    ],
    [risk]
  );

  if (loading) return <div className="state-panel">Loading dashboard...</div>;
  if (error) return <div className="state-panel error">{error}</div>;

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="eyebrow">Command center</p>
          <h1>Fraud monitoring dashboard</h1>
        </div>
      </div>

      <section className="metric-grid">
        <MetricCard title="Transactions" value={summary.total_transactions} detail="seeded and live" icon={CircleDollarSign} />
        <MetricCard title="Open alerts" value={summary.open_alerts} detail={`${summary.total_alerts} total alerts`} icon={AlertTriangle} tone="warn" />
        <MetricCard title="Fraud rate" value={`${summary.fraud_rate_percent}%`} detail="high-risk labels" icon={ShieldAlert} tone="danger" />
        <MetricCard title="Customers" value={summary.total_customers} detail={`${summary.total_merchants} merchants`} icon={Users} />
        <MetricCard title="Flagged amount" value={formatMoney(summary.total_flagged_amount)} detail="score 50 and above" icon={BadgeIndianRupee} tone="accent" />
        <MetricCard title="Resolved" value={summary.resolved_alerts} detail="closed investigations" icon={CheckCircle2} tone="good" />
      </section>

      <section className="dashboard-grid">
        <article className="panel">
          <div className="panel-title">
            <h2>Risk distribution</h2>
            <span>{risk.total} transactions</span>
          </div>
          <div className="risk-bars">
            {riskRows.map((row) => (
              <div key={row.label} className="risk-line">
                <div>
                  <span>{row.label}</span>
                  <b>{row.value}</b>
                </div>
                <div className="progress-track">
                  <i className={row.className} style={{ width: `${Math.max(row.percent, 3)}%` }} />
                </div>
                <small>{row.percent}%</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-title">
            <h2>Daily volume</h2>
            <span>Last 14 days</span>
          </div>
          <MiniBars rows={stats.daily_transaction_volume} />
        </article>

        <article className="panel">
          <div className="panel-title">
            <h2>Recent transactions</h2>
            <span>Latest activity</span>
          </div>
          <div className="table-list">
            {transactions.map((tx) => (
              <div className="table-row" key={tx.transaction_id}>
                <div>
                  <strong>{tx.transaction_id}</strong>
                  <span>{tx.location || 'Unknown'} · {formatMoney(tx.amount)}</span>
                </div>
                <RiskPill value={tx.risk_category} />
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-title">
            <h2>Alert queue</h2>
            <span>{alerts.length} latest</span>
          </div>
          <div className="table-list">
            {alerts.map((alert) => (
              <div className="table-row" key={alert.id}>
                <div>
                  <strong>{alert.alert_type}</strong>
                  <span>{alert.transaction_id} · score {Math.round(alert.risk_score || 0)}</span>
                </div>
                <span className={`severity ${alert.severity}`}>{alert.severity}</span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
};

export default Dashboard;
