"""
Seed script for the Mutual Fund Overlap & Concentration Risk graph.

Design notes (read this before editing):
- All the "content" (funds, stocks, sectors, overlap behavior) lives in the
  DATA block below as plain Python. Edit that block, rerun the script -
  nothing else needs to change.
- Uses MERGE everywhere, so the script is idempotent: rerun it as many times
  as you want after edits, it will not create duplicates.
- Call clear_db() first if you want a totally fresh slate instead of an
  incremental update.

Usage:
    python seed.py            # merge/update seed data
    python seed.py --clear    # wipe the whole graph, then seed fresh
"""

import os
import random
import sys
from faker import Faker
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
fake = Faker("en_IN")
random.seed(42)  # reproducible runs while you're tuning the data

# ---------------------------------------------------------------------------
# DATA BLOCK - edit this to change what gets seeded
# ---------------------------------------------------------------------------

# Real, recognizable large-cap/flexi-cap stock names (Nifty-ish universe)
STOCKS = [
    ("HDFC Bank", "Financial Services"),
    ("ICICI Bank", "Financial Services"),
    ("Reliance Industries", "Energy"),
    ("Infosys", "IT"),
    ("TCS", "IT"),
    ("Larsen & Toubro", "Infrastructure"),
    ("Bharti Airtel", "Telecom"),
    ("ITC", "FMCG"),
    ("Axis Bank", "Financial Services"),
    ("Kotak Mahindra Bank", "Financial Services"),
    ("Hindustan Unilever", "FMCG"),
    ("State Bank of India", "Financial Services"),
    ("Bajaj Finance", "Financial Services"),
    ("Maruti Suzuki", "Automobile"),
    ("Sun Pharma", "Pharma"),
    ("Titan Company", "Consumer Durables"),
    ("Asian Paints", "Consumer Durables"),
    ("Wipro", "IT"),
    ("UltraTech Cement", "Cement"),
    ("Tata Motors", "Automobile"),
    ("Divi's Laboratories", "Pharma"),
    ("Nestle India", "FMCG"),
    ("Adani Ports", "Infrastructure"),
    ("Power Grid Corp", "Utilities"),
    ("NTPC", "Utilities"),
]

# Real, recognizable fund names, each tagged with an AMC
FUNDS = [
    ("Axis Bluechip Fund", "Axis Mutual Fund", "Large Cap"),
    ("Mirae Asset Large Cap Fund", "Mirae Asset MF", "Large Cap"),
    ("Parag Parikh Flexi Cap Fund", "PPFAS MF", "Flexi Cap"),
    ("HDFC Flexi Cap Fund", "HDFC Mutual Fund", "Flexi Cap"),
    ("ICICI Pru Bluechip Fund", "ICICI Prudential MF", "Large Cap"),
    ("SBI Flexicap Fund", "SBI Mutual Fund", "Flexi Cap"),
    ("Kotak Flexicap Fund", "Kotak Mutual Fund", "Flexi Cap"),
    ("Nippon India Large Cap Fund", "Nippon India MF", "Large Cap"),
    ("UTI Flexi Cap Fund", "UTI Mutual Fund", "Flexi Cap"),
    ("Canara Robeco Bluechip Fund", "Canara Robeco MF", "Large Cap"),
    ("DSP Midcap Fund", "DSP Mutual Fund", "Mid Cap"),
    ("Motilal Oswal Midcap Fund", "Motilal Oswal MF", "Mid Cap"),
    ("Quant Active Fund", "Quant Mutual Fund", "Flexi Cap"),
    ("Franklin India Bluechip Fund", "Franklin Templeton MF", "Large Cap"),
]

# These stocks show up in most large/flexi cap funds with meaningful weight -
# this is what real large-cap fund overlap looks like, and it's what makes
# the "hidden overlap" query in the app return something interesting.
POPULAR_STOCKS = [
    "HDFC Bank", "ICICI Bank", "Reliance Industries", "Infosys", "TCS",
    "Larsen & Toubro", "Bharti Airtel", "Axis Bank",
]

OVERLAP_PROBABILITY = 0.7   # chance a fund holds a "popular" stock
UNIQUE_STOCK_COUNT = (3, 6)  # range of extra, fund-specific stocks per fund
HOLDING_WEIGHT_RANGE = (2.0, 9.5)  # % weight per holding, roughly realistic

NUM_INVESTORS = 12
FUNDS_PER_INVESTOR = (2, 5)
INVESTMENT_AMOUNT_RANGE = (10000, 500000)  # INR


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_driver():
    uri = os.environ["COGNODB_URI"]
    user = os.environ["COGNODB_USER"]
    password = os.environ["COGNODB_PASSWORD"]
    return GraphDatabase.driver(uri, auth=(user, password))


def clear_db(session):
    session.run("MATCH (n) DETACH DELETE n")
    print("Cleared all nodes and relationships.")


def create_constraints(session):
    # Uniqueness constraints double as indexes - keeps MERGE fast and safe.
    session.run("CREATE CONSTRAINT stock_name IF NOT EXISTS FOR (s:Stock) REQUIRE s.name IS UNIQUE")
    session.run("CREATE CONSTRAINT sector_name IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE")
    session.run("CREATE CONSTRAINT fund_name IF NOT EXISTS FOR (f:Fund) REQUIRE f.name IS UNIQUE")
    session.run("CREATE CONSTRAINT amc_name IF NOT EXISTS FOR (a:AMC) REQUIRE a.name IS UNIQUE")
    session.run("CREATE CONSTRAINT investor_id IF NOT EXISTS FOR (i:Investor) REQUIRE i.id IS UNIQUE")


def seed_stocks_and_sectors(session):
    for name, sector in STOCKS:
        session.run(
            """
            MERGE (sec:Sector {name: $sector})
            MERGE (s:Stock {name: $name})
            MERGE (s)-[:BELONGS_TO]->(sec)
            """,
            name=name, sector=sector,
        )
    print(f"Seeded {len(STOCKS)} stocks across sectors.")


def seed_funds_and_holdings(session):
    stock_names = [s[0] for s in STOCKS]
    for fund_name, amc_name, category in FUNDS:
        session.run(
            """
            MERGE (a:AMC {name: $amc_name})
            MERGE (f:Fund {name: $fund_name})
            SET f.category = $category
            MERGE (a)-[:MANAGES]->(f)
            """,
            amc_name=amc_name, fund_name=fund_name, category=category,
        )

        # Deliberate overlap: each fund gets some popular stocks + some unique ones
        holdings = set()
        for stock in POPULAR_STOCKS:
            if random.random() < OVERLAP_PROBABILITY:
                holdings.add(stock)

        remaining = [s for s in stock_names if s not in holdings]
        n_unique = random.randint(*UNIQUE_STOCK_COUNT)
        holdings.update(random.sample(remaining, min(n_unique, len(remaining))))

        for stock in holdings:
            weight = round(random.uniform(*HOLDING_WEIGHT_RANGE), 2)
            session.run(
                """
                MATCH (f:Fund {name: $fund_name})
                MATCH (s:Stock {name: $stock})
                MERGE (f)-[h:HOLDS]->(s)
                SET h.weight = $weight
                """,
                fund_name=fund_name, stock=stock, weight=weight,
            )
    print(f"Seeded {len(FUNDS)} funds with holdings.")


def seed_investors(session):
    fund_names = [f[0] for f in FUNDS]
    for i in range(1, NUM_INVESTORS + 1):
        investor_id = f"INV{i:03d}"
        name = fake.name()
        session.run(
            """
            MERGE (inv:Investor {id: $id})
            SET inv.name = $name
            """,
            id=investor_id, name=name,
        )

        n_funds = random.randint(*FUNDS_PER_INVESTOR)
        chosen_funds = random.sample(fund_names, n_funds)
        for fund_name in chosen_funds:
            amount = random.randint(*INVESTMENT_AMOUNT_RANGE)
            session.run(
                """
                MATCH (inv:Investor {id: $id})
                MATCH (f:Fund {name: $fund_name})
                MERGE (inv)-[r:INVESTS_IN]->(f)
                SET r.amount = $amount
                """,
                id=investor_id, fund_name=fund_name, amount=amount,
            )
    print(f"Seeded {NUM_INVESTORS} investors with fund investments.")


def main():
    driver = get_driver()
    try:
        with driver.session() as session:
            if "--clear" in sys.argv:
                clear_db(session)
            create_constraints(session)
            seed_stocks_and_sectors(session)
            seed_funds_and_holdings(session)
            seed_investors(session)
        print("Seeding complete.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()