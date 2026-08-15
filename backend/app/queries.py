"""Parameterized Cypher queries for fund overlap and sector concentration."""

from neo4j.exceptions import Neo4jError, ServiceUnavailable, AuthError

from .db import get_driver


class DatabaseUnavailable(Exception):
    """Raised when CognoDB cannot be reached or the query fails."""


def _run(query: str, **params):
    try:
        with get_driver().session() as session:
            result = session.run(query, **params)
            return [record.data() for record in result]
    except (ServiceUnavailable, AuthError, Neo4jError, OSError) as exc:
        raise DatabaseUnavailable(str(exc)) from exc


def fetch_funds() -> list[dict]:
    query = """
    MATCH (f:Fund)
    RETURN f.name AS name, f.category AS category
    ORDER BY f.category, f.name
    """
    return _run(query)


def fetch_exposure(fund_names: list[str]) -> dict:
    """Return stock overlap + sector rollup for the selected funds.

    Weight method (equal-weighted portfolio):
    Each selected fund is treated as an equal slice of the investor's
    portfolio. A stock's `avg_weight` is the sum of its HOLDS.weight
    values across the selected funds, divided by the number of selected
    funds (funds that do not hold the stock contribute 0). Sector
    concentration is the sum of those equal-weighted stock averages.
    """
    stocks = _stock_overlap(fund_names)
    sectors = _sector_concentration(fund_names)

    headline = None
    if stocks:
        top = stocks[0]
        headline = {
            "stock": top["stock"],
            "funds_holding": top["funds_holding"],
            "fund_count": top["fund_count"],
        }

    return {
        "headline": headline,
        "stocks": stocks,
        "sectors": sectors,
        "fund_count": len(fund_names),
    }


def _stock_overlap(fund_names: list[str]) -> list[dict]:
    # Awkward in SQL: aggregating overlap across a variable-length list of
    # funds (count how many hold each stock, weighted by allocation %) needs
    # self-joins or a subquery per fund pair that grows with fund count. In
    # Cypher it's a single pattern match + aggregation over $fund_names.
    query = """
    UNWIND $fund_names AS fund_name
    MATCH (f:Fund {name: fund_name})-[h:HOLDS]->(s:Stock)
    WITH s,
         count(DISTINCT f) AS funds_holding,
         sum(h.weight) AS weight_sum,
         size($fund_names) AS fund_count
    RETURN s.name AS stock,
           funds_holding,
           fund_count,
           weight_sum / fund_count AS avg_weight
    ORDER BY funds_holding DESC, avg_weight DESC
    """
    rows = _run(query, fund_names=fund_names)
    for row in rows:
        row["avg_weight"] = round(float(row["avg_weight"]), 2)
    return rows


def _sector_concentration(fund_names: list[str]) -> list[dict]:
    # Genuine 2-hop traversal: Fund -[:HOLDS]-> Stock -[:BELONGS_TO]-> Sector
    query = """
    UNWIND $fund_names AS fund_name
    MATCH (f:Fund {name: fund_name})-[h:HOLDS]->(s:Stock)-[:BELONGS_TO]->(sec:Sector)
    WITH sec.name AS sector,
         sum(h.weight) / size($fund_names) AS total_weight
    RETURN sector, total_weight
    ORDER BY total_weight DESC
    """
    rows = _run(query, fund_names=fund_names)
    for row in rows:
        row["total_weight"] = round(float(row["total_weight"]), 1)
    return rows
