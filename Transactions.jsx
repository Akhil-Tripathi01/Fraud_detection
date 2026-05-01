import { useEffect, useMemo, useState } from 'react';
import { Plus, RefreshCw, Search } from 'lucide-react';
import { transactionsApi } from './api';

const emptyForm = {
  sender_id: '',
  receiver_id: '',
  merchant_id: '',
  device_id: '',
  amount: '',
  currency: 'INR',
  location: 'Mumbai',
  latitude: '19.076',
  longitude: '72.8777',
  transaction_type: 'transfer',
};

const formatMoney = (value) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0);

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [reference, setReference] = useState({ customers: [], merchants: [], devices: [], transaction_types: [] });
  const [form, setForm] = useState(emptyForm);
  const [filters, setFilters] = useState({ risk_category: 'all', search: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [txData, refData] = await Promise.all([
        transactionsApi.list({ limit: 100, ...filters }),
        transactionsApi.reference(),
      ]);
      setTransactions(txData);
      setReference(refData);
      setForm((prev) => ({
        ...prev,
        sender_id: prev.sender_id || refData.customers[0]?.id || '',
        receiver_id: prev.receiver_id || refData.customers[1]?.id || '',
        merchant_id: prev.merchant_id,
        device_id: prev.device_id || refData.devices[0]?.id || '',
        transaction_type: prev.transaction_type || refData.transaction_types[0] || 'transfer',
      }));
    } catch (err) {
      setError(err.response?.data?.detail || 'Transactions could not be loaded.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setResult(null);
    try {
      const payload = {
        ...form,
        receiver_id: form.receiver_id || null,
        merchant_id: form.merchant_id || null,
        device_id: form.device_id || null,
        amount: Number(form.amount),
        latitude: form.latitude ? Number(form.latitude) : null,
        longitude: form.longitude ? Number(form.longitude) : null,
      };
      const analysis = await transactionsApi.create(payload);
      setResult(analysis);
      setForm((prev) => ({ ...prev, amount: '' }));
      const txData = await transactionsApi.list({ limit: 100, ...filters });
      setTransactions(txData);
    } catch (err) {
      setError(err.response?.data?.detail || 'Transaction could not be created.');
    } finally {
      setSaving(false);
    }
  };

  const selectedCounterparty = useMemo(() => {
    if (form.merchant_id) return 'merchant';
    if (form.receiver_id) return 'receiver';
    return 'none';
  }, [form]);

  return (
    <div className="page-stack">
      <div className="page-header split">
        <div>
          <p className="eyebrow">Ledger</p>
          <h1>Transactions</h1>
        </div>
        <button className="secondary-button" type="button" onClick={load}>
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {error && <div className="state-panel error">{error}</div>}

      <section className="two-column">
        <form className="panel form-panel" onSubmit={submit}>
          <div className="panel-title">
            <h2>Create transaction</h2>
            <span>{selectedCounterparty}</span>
          </div>

          <label>
            Sender
            <select value={form.sender_id} onChange={(event) => setForm((prev) => ({ ...prev, sender_id: event.target.value }))}>
              {reference.customers.map((customer) => (
                <option key={customer.id} value={customer.id}>{customer.name}</option>
              ))}
            </select>
          </label>

          <div className="form-grid">
            <label>
              Receiver
              <select
                value={form.receiver_id}
                onChange={(event) => setForm((prev) => ({ ...prev, receiver_id: event.target.value, merchant_id: '' }))}
              >
                <option value="">None</option>
                {reference.customers
                  .filter((customer) => customer.id !== form.sender_id)
                  .map((customer) => (
                    <option key={customer.id} value={customer.id}>{customer.name}</option>
                  ))}
              </select>
            </label>

            <label>
              Merchant
              <select
                value={form.merchant_id}
                onChange={(event) => setForm((prev) => ({ ...prev, merchant_id: event.target.value, receiver_id: '' }))}
              >
                <option value="">None</option>
                {reference.merchants.map((merchant) => (
                  <option key={merchant.id} value={merchant.id}>{merchant.name}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="form-grid">
            <label>
              Device
              <select value={form.device_id} onChange={(event) => setForm((prev) => ({ ...prev, device_id: event.target.value }))}>
                {reference.devices.map((device) => (
                  <option key={device.id} value={device.id}>{device.device_type} · {device.device_hash.slice(0, 8)}</option>
                ))}
              </select>
            </label>
            <label>
              Type
              <select value={form.transaction_type} onChange={(event) => setForm((prev) => ({ ...prev, transaction_type: event.target.value }))}>
                {reference.transaction_types.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="form-grid">
            <label>
              Amount
              <input
                type="number"
                min="1"
                value={form.amount}
                onChange={(event) => setForm((prev) => ({ ...prev, amount: event.target.value }))}
                required
              />
            </label>
            <label>
              Location
              <input value={form.location} onChange={(event) => setForm((prev) => ({ ...prev, location: event.target.value }))} />
            </label>
          </div>

          <div className="form-grid">
            <label>
              Latitude
              <input value={form.latitude} onChange={(event) => setForm((prev) => ({ ...prev, latitude: event.target.value }))} />
            </label>
            <label>
              Longitude
              <input value={form.longitude} onChange={(event) => setForm((prev) => ({ ...prev, longitude: event.target.value }))} />
            </label>
          </div>

          <button className="primary-button" type="submit" disabled={saving}>
            <Plus size={18} />
            {saving ? 'Analyzing...' : 'Create and analyze'}
          </button>

          {result && (
            <div className="analysis-result">
              <strong>{Math.round(result.risk_score)} risk score</strong>
              <span>{result.risk_category} risk · {result.alert_created ? 'alert created' : 'no alert'}</span>
              <p>{result.explanation}</p>
            </div>
          )}
        </form>

        <section className="panel">
          <div className="panel-title">
            <h2>Transaction ledger</h2>
            <span>{transactions.length} rows</span>
          </div>
          <div className="filters">
            <div className="search-box">
              <Search size={17} />
              <input
                value={filters.search}
                placeholder="Search id, sender, location"
                onChange={(event) => setFilters((prev) => ({ ...prev, search: event.target.value }))}
              />
            </div>
            <select value={filters.risk_category} onChange={(event) => setFilters((prev) => ({ ...prev, risk_category: event.target.value }))}>
              <option value="all">All risk</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
            <button className="secondary-button compact" type="button" onClick={load}>Apply</button>
          </div>

          {loading ? (
            <div className="state-panel">Loading transactions...</div>
          ) : (
            <div className="data-table">
              <div className="data-head">
                <span>ID</span>
                <span>Amount</span>
                <span>Type</span>
                <span>Risk</span>
                <span>Status</span>
              </div>
              {transactions.map((tx) => (
                <div className="data-row" key={tx.transaction_id}>
                  <span title={tx.transaction_id}>{tx.transaction_id}</span>
                  <span>{formatMoney(tx.amount)}</span>
                  <span>{tx.transaction_type}</span>
                  <span className={`risk-pill ${tx.risk_category}`}>{tx.risk_category}</span>
                  <span>{tx.status}</span>
                </div>
              ))}
            </div>
          )}
        </section>
      </section>
    </div>
  );
};

export default Transactions;
