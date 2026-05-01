import { useMemo, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthContext } from './authContext';
import Layout from './Layout';
import Login from './Login';
import Dashboard from './Dashboard';
import Transactions from './Transactions';
import FraudAlerts from './FraudAlerts';
import GraphNetwork from './GraphNetwork';
import TransactionsAnalysis from './TransactionsAnalysis';
import InvestigatorDashboard from './InvestigatorDashboard';

const readStoredUser = () => {
  try {
    return JSON.parse(localStorage.getItem('fraud_user'));
  } catch {
    return null;
  }
};

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('fraud_token');
  return token ? children : <Navigate to="/login" replace />;
};

const App = () => {
  const [user, setUser] = useState(readStoredUser);
  const [token, setToken] = useState(localStorage.getItem('fraud_token'));

  const auth = useMemo(
    () => ({
      user,
      token,
      signIn: (session) => {
        localStorage.setItem('fraud_token', session.access_token);
        localStorage.setItem(
          'fraud_user',
          JSON.stringify({
            id: session.user_id,
            username: session.username,
            role: session.role,
          })
        );
        setToken(session.access_token);
        setUser({ id: session.user_id, username: session.username, role: session.role });
      },
      signOut: () => {
        localStorage.removeItem('fraud_token');
        localStorage.removeItem('fraud_user');
        setToken(null);
        setUser(null);
      },
    }),
    [token, user]
  );

  return (
    <AuthContext.Provider value={auth}>
      <Routes>
        <Route path="/login" element={token ? <Navigate to="/" replace /> : <Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="analysis" element={<TransactionsAnalysis />} />
          <Route path="alerts" element={<FraudAlerts />} />
          <Route path="graph" element={<GraphNetwork />} />
          <Route path="investigation" element={<InvestigatorDashboard />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthContext.Provider>
  );
};

export default App;
