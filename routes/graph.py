from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import models
from auth_utils import get_current_user
from database import get_db
from graph_builder import (
    build_transaction_graph,
    detect_fraud_clusters,
    detect_suspicious_nodes,
    get_customer_subgraph,
    get_graph_edges,
    get_graph_nodes,
)

router = APIRouter()


@router.get("/network")
def network(
    limit: int = Query(200, ge=10, le=1000),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    graph = build_transaction_graph(db, limit=limit)
    return {
        "nodes": get_graph_nodes(graph),
        "edges": get_graph_edges(graph),
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges(),
        "suspicious_nodes": detect_suspicious_nodes(graph),
        "fraud_clusters": detect_fraud_clusters(graph),
    }


@router.get("/customer/{customer_id}")
def customer_graph(
    customer_id: str,
    depth: int = Query(2, ge=1, le=4),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return get_customer_subgraph(customer_id, db, depth=depth)


@router.get("/metrics")
def metrics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    graph = build_transaction_graph(db, limit=500)
    node_types = {}
    for _, attrs in graph.nodes(data=True):
        node_type = attrs.get("node_type", "unknown")
        node_types[node_type] = node_types.get(node_type, 0) + 1

    top_nodes = sorted(
        (
            {
                "id": node,
                "label": attrs.get("label", node),
                "node_type": attrs.get("node_type", "unknown"),
                "degree": graph.degree(node),
            }
            for node, attrs in graph.nodes(data=True)
        ),
        key=lambda item: item["degree"],
        reverse=True,
    )[:10]

    return {
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges(),
        "node_types": node_types,
        "top_nodes": top_nodes,
    }
