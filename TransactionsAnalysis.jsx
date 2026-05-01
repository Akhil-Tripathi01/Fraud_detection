import { useEffect, useState } from 'react';
import { Play, RefreshCw } from 'lucide-react';
import { fraudApi, transactionsApi } from './api';

const flagLabels = [
  'high_amount_flag',
  'velocity_flag',
  'device_sharing_flag',
  'location_anomaly_flag',
  'ring_pattern_flag',
  'unusual_hours_flag',
  'new_merchant_flag',
];

const TransactionsAnalysis = () => {
  const [risks, setRisks] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [riskData, txData] = await Promise.all([
        fraudApi.riskScores({ limit: 100 }),
        transactionsApi.list({ limit: 100 }),
      ]);
      setRisks(riskData);
      setTransactions(txData);
      setSelectedId((prev) => prev || txData[0]?.transaction_id || '');
    } catch (err) {
      setError(err.response?.data?.detail || 'Risk analysis could not be loaded.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const runAnalysis = async () => {
    if (!selectedId) return;
    setRunning(true);
    setError('');
    try {
      const result = await fraudApi.analyze(selectedId);
      setAnalysis(result);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis could not be completed.');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="page-stack">
      <div className="page-header split">
        <div>
          <p className="eyebrow">Scoring engine</p>
          <h1>Transaction risk analysis</h1>
        </div>
        <button className="secondary-button" type="button" onClick={load}>
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {error && <div className="state-panel error">{error}</div>}

      <section className="two-column analysis-layout">
        <article className="panel form-panel">
          <div className="panel-title">
            <h2>Run analysis</h2>
            <span>{transactions.length} transactions</span>
          </div>
          <label>
            Transaction
            <select value={selectedId} onChange={(event) => setSelectedId(event.target.value)}>
              {transactions.map((tx) => (
                <option key={tx.transaction_id} value={tx.transaction_id}>
                  {tx.transaction_id} · {tx.risk_category} · INR {Math.round(tx.amount)}
                </option>
              ))}
            </select>
          </label>
          <button className="primary-button" type="button" onClick={runAnalysis} disabled={running || !selectedId}>
            <Play size={18} />
            {running ? 'Analyzing...' : 'Analyze selected'}
          </button>
          {analysis && (
            <div className="analysis-result wide">
              <strong>{Math.round(analysis.risk_score)} overall score</strong>
              <span>{analysis.risk_category} risk · rules {analysis.rule_score} · ML {analysis.ml_score} · graph {analysis.graph_score}</span>
              <p>{analysis.explanation}</p>
            </div>
          )}
        </article>

        <article className="panel">
          <div className="panel-title">
            <h2>Risk score records</h2>
            <span>{risks.length} rows</span>
          </div>
          {loading ? (
            <div className="state-panel">Loading scores...</div>
          ) : (
            <div className="risk-score-list">
              {risks.map((risk) => (
                <div className="risk-score-row" key={risk.transaction_id}>
                  <div className="score-ring">
                    <strong>{Math.round(risk.overall_score)}</strong>
                    <span>{risk.risk_category}</span>
                  </div>
                  <div>
                    <h3>{risk.transaction_id}</h3>
                    <p>{risk.explanation}</p>
                    <div className="flag-list">
                      {flagLabels.map((flag) => (
                        <span key={flag} className={risk[flag] ? 'on' : ''}>{flag.replaceAll('_', ' ')}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>
    </div>
  );
};

export default TransactionsAnalysis;
