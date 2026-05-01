import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, LockKeyhole, ShieldCheck } from 'lucide-react';
import { authApi } from './api';
import { useAuth } from './authContext';

const Login = () => {
  const navigate = useNavigate();
  const { signIn } = useAuth();
  const [credentials, setCredentials] = useState({ username: 'admin', password: 'admin123' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const session = await authApi.login(credentials);
      signIn(session);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to sign in.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-brand">
          <div className="brand-mark large">FD</div>
          <div>
            <h1>FraudDesk</h1>
            <p>Graph-led transaction monitoring</p>
          </div>
        </div>

        <form className="login-form" onSubmit={submit}>
          <label>
            Username
            <input
              value={credentials.username}
              onChange={(event) => setCredentials((prev) => ({ ...prev, username: event.target.value }))}
              autoComplete="username"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={credentials.password}
              onChange={(event) => setCredentials((prev) => ({ ...prev, password: event.target.value }))}
              autoComplete="current-password"
            />
          </label>

          {error && (
            <div className="inline-alert">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <button className="primary-button" type="submit" disabled={loading}>
            <LockKeyhole size={18} />
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <div className="demo-strip">
          <ShieldCheck size={18} />
          <span>admin / admin123</span>
        </div>
      </section>
    </main>
  );
};

export default Login;
