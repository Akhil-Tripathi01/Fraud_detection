import { LogOut, Menu, ShieldCheck } from 'lucide-react';
import { useAuth } from './authContext';

const Navbar = ({ toggleSidebar }) => {
  const { user, signOut } = useAuth();

  return (
    <header className="topbar">
      <button className="icon-button" type="button" onClick={toggleSidebar} aria-label="Toggle sidebar">
        <Menu size={20} />
      </button>
      <div className="topbar-title">
        <ShieldCheck size={20} />
        <span>Predictive Financial Fraud Detection</span>
      </div>
      <div className="user-chip">
        <div>
          <strong>{user?.username || 'Investigator'}</strong>
          <span>{user?.role || 'analyst'}</span>
        </div>
        <button className="icon-button" type="button" onClick={signOut} aria-label="Sign out" title="Sign out">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
};

export default Navbar;
