import { NavLink } from 'react-router-dom';
import {
  AlertTriangle,
  BarChart3,
  FileSearch,
  GitBranch,
  LayoutDashboard,
  ReceiptText,
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/transactions', label: 'Transactions', icon: ReceiptText },
  { to: '/analysis', label: 'Risk Analysis', icon: BarChart3 },
  { to: '/alerts', label: 'Fraud Alerts', icon: AlertTriangle },
  { to: '/graph', label: 'Graph Network', icon: GitBranch },
  { to: '/investigation', label: 'Investigation', icon: FileSearch },
];

const Sidebar = ({ isOpen }) => (
  <aside className={`sidebar ${isOpen ? 'sidebar-open' : 'sidebar-collapsed'}`}>
    <div className="brand">
      <div className="brand-mark">FD</div>
      {isOpen && (
        <div>
          <p>FraudDesk</p>
          <span>Behavioral graph risk</span>
        </div>
      )}
    </div>

    <nav className="side-nav" aria-label="Primary navigation">
      {navItems.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}
            title={!isOpen ? item.label : undefined}
          >
            <Icon size={20} />
            {isOpen && <span>{item.label}</span>}
          </NavLink>
        );
      })}
    </nav>
  </aside>
);

export default Sidebar;
