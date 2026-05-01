import { useEffect, useMemo, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { graphApi } from './api';

const colors = {
  customer: '#2563eb',
  merchant: '#7c3aed',
  device: '#0891b2',
  location: '#16a34a',
  unknown: '#64748b',
};

const GraphNetwork = () => {
  const [graph, setGraph] = useState({ nodes: [], edges: [], suspicious_nodes: [], fraud_clusters: [] });
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await graphApi.network({ limit: 250 });
      setGraph(data);
      setSelected(data.nodes[0] || null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Graph could not be loaded.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const layout = useMemo(() => {
    const width = 920;
    const height = 560;
    const centerX = width / 2;
    const centerY = height / 2;
    const byId = {};
    graph.nodes.forEach((node, index) => {
      const angle = (index / Math.max(graph.nodes.length, 1)) * Math.PI * 2;
      const radius = node.node_type === 'customer' ? 190 : node.node_type === 'merchant' ? 245 : 135;
      byId[node.id] = {
        ...node,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      };
    });
    return { width, height, nodes: Object.values(byId), byId };
  }, [graph.nodes]);

  return (
    <div className="page-stack">
      <div className="page-header split">
        <div>
          <p className="eyebrow">Behavior graph</p>
          <h1>Network topology</h1>
        </div>
        <button className="secondary-button" type="button" onClick={load}>
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {error && <div className="state-panel error">{error}</div>}
      {loading ? (
        <div className="state-panel">Loading graph...</div>
      ) : (
        <section className="graph-layout">
          <article className="panel graph-panel">
            <div className="panel-title">
              <h2>{graph.total_nodes} nodes, {graph.total_edges} edges</h2>
              <span>{graph.suspicious_nodes.length} suspicious nodes</span>
            </div>
            <svg viewBox={`0 0 ${layout.width} ${layout.height}`} role="img" aria-label="Transaction graph">
              {graph.edges.map((edge, index) => {
                const source = layout.byId[edge.source];
                const target = layout.byId[edge.target];
                if (!source || !target) return null;
                const risky = edge.properties?.fraud_label || graph.suspicious_nodes.includes(edge.target);
                return (
                  <line
                    key={`${edge.source}-${edge.target}-${index}`}
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    className={risky ? 'graph-edge risky' : 'graph-edge'}
                  />
                );
              })}
              {layout.nodes.map((node) => {
                const suspicious = graph.suspicious_nodes.includes(node.id);
                return (
                  <g key={node.id} onClick={() => setSelected(node)} className="graph-node" tabIndex="0">
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={suspicious ? 17 : 13}
                      fill={colors[node.node_type] || colors.unknown}
                      className={selected?.id === node.id ? 'selected' : ''}
                    />
                    <text x={node.x} y={node.y + 31}>{node.label.slice(0, 14)}</text>
                  </g>
                );
              })}
            </svg>
          </article>

          <aside className="panel inspector">
            <div className="panel-title">
              <h2>Node inspector</h2>
              <span>{selected?.node_type || 'none'}</span>
            </div>
            {selected ? (
              <>
                <div className="node-badge" style={{ borderColor: colors[selected.node_type] || colors.unknown }}>
                  <strong>{selected.label}</strong>
                  <span>{selected.id}</span>
                </div>
                <div className="property-list">
                  {Object.entries(selected.properties || {}).map(([key, value]) => (
                    <div key={key}>
                      <span>{key}</span>
                      <b>{String(value)}</b>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p>No node selected.</p>
            )}
            <div className="legend">
              {Object.entries(colors).filter(([key]) => key !== 'unknown').map(([key, value]) => (
                <span key={key}><i style={{ background: value }} />{key}</span>
              ))}
            </div>
          </aside>
        </section>
      )}
    </div>
  );
};

export default GraphNetwork;
