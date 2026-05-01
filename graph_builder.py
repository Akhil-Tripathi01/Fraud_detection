"""
Graph Builder
Models financial transactions as a dynamic graph using NetworkX.
Nodes: customers, merchants, devices, locations.
Edges: transactions and relationships.
"""

import networkx as nx
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Tuple
import models
import logging

logger = logging.getLogger(__name__)


def build_transaction_graph(db: Session, limit: int = 200) -> nx.DiGraph:
    """
    Build a directed transaction graph from the database.
    
    Node types:
    - C_<id>  → Customer
    - M_<id>  → Merchant
    - D_<id>  → Device
    - L_<loc> → Location

    Edge types:
    - SENT_TO     : customer → customer (transfer)
    - PAID        : customer → merchant (payment/purchase)
    - USED_DEVICE : customer → device
    - AT_LOCATION : customer → location
    """
    G = nx.DiGraph()

    transactions = (
        db.query(models.Transaction)
        .order_by(models.Transaction.timestamp.desc())
        .limit(limit)
        .all()
    )

    customers = {c.id: c for c in db.query(models.Customer).all()}
    merchants = {m.id: m for m in db.query(models.Merchant).all()}
    devices   = {d.id: d for d in db.query(models.Device).all()}

    for txn in transactions:
        sender_node   = f"C_{txn.sender_id}"
        receiver_node = f"C_{txn.receiver_id}" if txn.receiver_id else None
        merchant_node = f"M_{txn.merchant_id}" if txn.merchant_id else None
        device_node   = f"D_{txn.device_id}"   if txn.device_id   else None
        location_node = f"L_{txn.location}"    if txn.location    else None

        # Add sender node
        if txn.sender_id in customers:
            c = customers[txn.sender_id]
            G.add_node(sender_node, node_type="customer", label=c.name,
                       risk_score=c.risk_score, is_flagged=c.is_flagged)

        # Add receiver node
        if receiver_node and txn.receiver_id in customers:
            c = customers[txn.receiver_id]
            G.add_node(receiver_node, node_type="customer", label=c.name,
                       risk_score=c.risk_score, is_flagged=c.is_flagged)

        # Add merchant node
        if merchant_node and txn.merchant_id in merchants:
            m = merchants[txn.merchant_id]
            G.add_node(merchant_node, node_type="merchant", label=m.name,
                       category=m.category, is_flagged=m.is_flagged)

        # Add device node
        if device_node and txn.device_id in devices:
            d = devices[txn.device_id]
            G.add_node(device_node, node_type="device",
                       label=f"{d.device_type}:{d.device_hash[:8]}",
                       device_type=d.device_type, is_flagged=d.is_flagged)

        # Add location node
        if location_node:
            G.add_node(location_node, node_type="location", label=txn.location)

        # Add edges
        edge_attrs = {
            "transaction_id": txn.transaction_id,
            "amount":         txn.amount,
            "risk_score":     txn.risk_score,
            "fraud_label":    txn.fraud_label,
            "timestamp":      str(txn.timestamp),
            "txn_type":       str(txn.transaction_type).split(".")[-1],
        }

        if receiver_node:
            G.add_edge(sender_node, receiver_node, edge_type="SENT_TO", **edge_attrs)
        if merchant_node:
            G.add_edge(sender_node, merchant_node, edge_type="PAID", **edge_attrs)
        if device_node:
            G.add_edge(sender_node, device_node, edge_type="USED_DEVICE",
                       transaction_id=txn.transaction_id)
        if location_node:
            G.add_edge(sender_node, location_node, edge_type="AT_LOCATION",
                       transaction_id=txn.transaction_id)

    logger.info(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def get_graph_nodes(G: nx.DiGraph) -> List[Dict[str, Any]]:
    """Extract nodes with attributes for API response."""
    nodes = []
    for node_id, attrs in G.nodes(data=True):
        nodes.append({
            "id":         node_id,
            "label":      attrs.get("label", node_id),
            "node_type":  attrs.get("node_type", "unknown"),
            "properties": {k: v for k, v in attrs.items() if k not in ("label", "node_type")},
        })
    return nodes


def get_graph_edges(G: nx.DiGraph) -> List[Dict[str, Any]]:
    """Extract edges with attributes for API response."""
    edges = []
    for source, target, attrs in G.edges(data=True):
        edges.append({
            "source":    source,
            "target":    target,
            "edge_type": attrs.get("edge_type", "RELATED"),
            "weight":    attrs.get("amount", 1.0),
            "properties": {k: v for k, v in attrs.items() if k != "edge_type"},
        })
    return edges


def detect_suspicious_nodes(G: nx.DiGraph) -> List[str]:
    """
    Identify suspicious nodes using graph metrics.
    - High in-degree merchant (many senders) → potential money collector
    - High out-degree customer (many receivers) → potential money mule
    - Devices connecting many customers
    """
    suspicious = set()

    for node, attrs in G.nodes(data=True):
        ntype = attrs.get("node_type", "")

        # Suspicious merchant: many unique customers paying it
        if ntype == "merchant":
            in_customers = len({
                s for s, _ in G.in_edges(node)
                if G.nodes[s].get("node_type") == "customer"
            })
            if in_customers >= 5:
                suspicious.add(node)

        # Suspicious customer: sending to many different people quickly
        if ntype == "customer":
            if G.out_degree(node) >= 6:
                suspicious.add(node)
            if attrs.get("is_flagged"):
                suspicious.add(node)

        # Suspicious device: used by multiple customers
        if ntype == "device":
            customer_users = [
                s for s, _ in G.in_edges(node)
                if G.nodes.get(s, {}).get("node_type") == "customer"
            ]
            if len(set(customer_users)) >= 3:
                suspicious.add(node)

    return list(suspicious)


def detect_fraud_clusters(G: nx.DiGraph) -> List[List[str]]:
    """
    Detect strongly connected communities that could be fraud rings.
    Uses weakly connected components on the undirected projection.
    """
    undirected = G.to_undirected()
    clusters = []

    for component in nx.connected_components(undirected):
        # Only flag clusters with ≥ 3 nodes that include suspicious activity
        if len(component) >= 3:
            subgraph = G.subgraph(component)
            fraud_edges = [
                (u, v) for u, v, d in subgraph.edges(data=True)
                if d.get("fraud_label")
            ]
            if fraud_edges:
                clusters.append(list(component))

    return clusters


def get_customer_subgraph(
    customer_id: str,
    db: Session,
    depth: int = 2
) -> Dict[str, Any]:
    """Build an ego graph centered on a specific customer."""
    G = build_transaction_graph(db)
    node_id = f"C_{customer_id}"

    if node_id not in G:
        return {"nodes": [], "edges": [], "message": "Customer not found in graph"}

    ego = nx.ego_graph(G, node_id, radius=depth, undirected=True)
    return {
        "nodes": get_graph_nodes(ego),
        "edges": get_graph_edges(ego),
        "center": node_id,
        "depth":  depth,
    }
