import { useEffect, useMemo, useState } from 'react';
import { MessageSquarePlus, RefreshCw } from 'lucide-react';
import { investigationApi } from './api';

const statusOptions = ['open', 'investigating', 'resolved', 'false_positive'];

const InvestigatorDashboard = () => {
  const [cases, setCases] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [note, setNote] = useState('');
  const [action, setAction] = useState('reviewed');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await investigationApi.cases();
      setCases(data);
      setSelectedId((prev) => prev || data[0]?.alert.id || '');
    } catch (err) {
      setError(err.response?.data?.detail || 'Investigation cases could not be loaded.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const selectedCase = useMemo(
    () => cases.find((item) => item.alert.id === selectedId),
    [cases, selectedId]
  );

  const addNote = async (event) => {
    event.preventDefault();
    if (!selectedCase || note.trim().length < 5) return;
    setSaving(true);
    setError('');
    try {
      await investigationApi.addNote({
        alert_id: selectedCase.alert.id,
        note_text: note,
        action_taken: action,
      });
      setNote('');
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Note could not be saved.');
    } finally {
      setSaving(false);
    }
  };

  const updateStatus = async (status) => {
    if (!selectedCase) return;
    try {
      await investigationApi.updateStatus(selectedCase.alert.id, {
        status,
        note: `Case marked ${status}.`,
      });
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Status could not be updated.');
    }
  };

  return (
    <div className="page-stack">
      <div className="page-header split">
        <div>
          <p className="eyebrow">Casework</p>
          <h1>Investigator dashboard</h1>
        </div>
        <button className="secondary-button" type="button" onClick={load}>
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {error && <div className="state-panel error">{error}</div>}
      {loading ? (
        <div className="state-panel">Loading investigations...</div>
      ) : (
        <section className="investigation-layout">
          <aside className="panel case-list">
            <div className="panel-title">
              <h2>Cases</h2>
              <span>{cases.length}</span>
            </div>
            {cases.map((item) => (
              <button
                className={`case-button ${item.alert.id === selectedId ? 'active' : ''}`}
                key={item.alert.id}
                type="button"
                onClick={() => setSelectedId(item.alert.id)}
              >
                <strong>{item.alert.alert_type}</strong>
                <span>{item.alert.status} · score {Math.round(item.alert.risk_score || 0)}</span>
              </button>
            ))}
          </aside>

          <article className="panel case-detail">
            {selectedCase ? (
              <>
                <div className="panel-title">
                  <h2>{selectedCase.alert.alert_type}</h2>
                  <span className={`severity ${selectedCase.alert.severity}`}>{selectedCase.alert.severity}</span>
                </div>
                <p className="case-description">{selectedCase.alert.description}</p>
                <div className="case-facts">
                  <div>
                    <span>Transaction</span>
                    <b>{selectedCase.alert.transaction_id}</b>
                  </div>
                  <div>
                    <span>Amount</span>
                    <b>INR {Math.round(selectedCase.transaction?.amount || 0)}</b>
                  </div>
                  <div>
                    <span>Risk</span>
                    <b>{selectedCase.risk_score?.risk_category || 'unknown'}</b>
                  </div>
                </div>
                <div className="toolbar">
                  <select value={selectedCase.alert.status} onChange={(event) => updateStatus(event.target.value)}>
                    {statusOptions.map((status) => <option key={status} value={status}>{status}</option>)}
                  </select>
                </div>

                <form className="note-form" onSubmit={addNote}>
                  <textarea
                    value={note}
                    onChange={(event) => setNote(event.target.value)}
                    placeholder="Investigation note"
                    rows="4"
                  />
                  <div className="form-grid">
                    <select value={action} onChange={(event) => setAction(event.target.value)}>
                      <option value="reviewed">reviewed</option>
                      <option value="contacted_customer">contacted customer</option>
                      <option value="blocked_account">blocked account</option>
                      <option value="escalated">escalated</option>
                    </select>
                    <button className="primary-button" type="submit" disabled={saving}>
                      <MessageSquarePlus size={18} />
                      {saving ? 'Saving...' : 'Add note'}
                    </button>
                  </div>
                </form>

                <div className="notes">
                  {selectedCase.notes.map((item) => (
                    <div className="note" key={item.id}>
                      <strong>{item.action_taken || 'note'}</strong>
                      <p>{item.note_text}</p>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="state-panel">No case selected.</div>
            )}
          </article>
        </section>
      )}
    </div>
  );
};

export default InvestigatorDashboard;
