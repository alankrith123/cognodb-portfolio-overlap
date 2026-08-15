
A tool for mutual fund investors to see what they're **actually** exposed to once overlapping holdings across their funds are accounted for. Most large-cap and flexi-cap funds hold the same 8-10 blue-chip stocks, so someone holding 4-5 "different" funds is often far more concentrated in a handful of companies and sectors than they realize. This app takes the funds an investor holds and surfaces that hidden concentration.

Backed by CognoDB (a managed graph database, openCypher over Bolt).

---

## Why a graph database?

As someone who actually invests through SIPs across multiple funds, I used to assume that holding 4-5 "different" funds meant I was diversified. I never sat down and checked what was actually inside them. The core question this app answers, "across the funds I hold, what am I actually exposed to, once overlapping holdings are accounted for?", is fundamentally about relationships between entities, not rows in a table.

In a relational schema, computing overlap exposure means joining `investors → investor_funds → fund_holdings → stocks → sectors`, aggregating across a **variable number** of funds. Two funds selected vs. six funds selected changes the join cardinality, not just a WHERE clause. A relational query either needs a self-join per fund pair (grows combinatorially) or a query built dynamically to match the selection size.

In Cypher, the same question is a natural pattern match that doesn't change shape regardless of how many funds are selected:

```cypher
MATCH (f:Fund)-[h:HOLDS]->(s:Stock)
WHERE f.name IN $fund_names
WITH s, count(DISTINCT f) AS fund_count, avg(h.weight) AS avg_weight
RETURN s.name AS stock, fund_count, avg_weight
ORDER BY fund_count DESC
```

The sector rollup (`Fund → Stock → Sector`) is a second hop on top of this. In SQL that's a compounding join; in Cypher it's just extending the same pattern. The underlying insight, that investors are connected to concentration risk through *indirect*, multi-hop relationships (fund → stock → sector) rather than direct ones, is exactly the kind of question graph databases are built for, and relational schemas get progressively more awkward as more hops are added.

---

## Data model

**Nodes**
- `Stock {name}`
- `Sector {name}`
- `Fund {name, category}`
- `AMC {name}` (fund house)
- `Investor {id, name}`

**Relationships**
- `(Stock)-[:BELONGS_TO]->(Sector)`
- `(AMC)-[:MANAGES]->(Fund)`
- `(Fund)-[:HOLDS {weight}]->(Stock)`, where weight is the % of the fund allocated to that stock
- `(Investor)-[:INVESTS_IN {amount}]->(Fund)`

```
(Investor)-[:INVESTS_IN]->(Fund)-[:HOLDS]->(Stock)-[:BELONGS_TO]->(Sector)
                              ^
                    (AMC)-[:MANAGES]->(Fund)
```

<!-- TODO: paste a simple diagram image here, e.g. from a quick draw.io / Excalidraw sketch of the model above, or a screenshot of the Visualizer diagram if you export one -->

---

## Seed data

`seed.py` loads 25 real, recognizable large-cap stock names mapped to sectors, 14 real fund names mapped to AMCs, and 12 synthetic investors. Fund-stock holdings are generated with deliberate overlap logic (a set of "popular" stocks appears in ~70% of funds, mirroring how real large-cap funds behave) rather than pure randomness, so the overlap and concentration queries return realistic, non-trivial results.

Run it with:
```bash
python seed.py --clear
```
`--clear` wipes the graph first; omit it to merge or update without wiping. The script is idempotent (uses `MERGE`), so it's safe to rerun.

---

## Setup & run

### 1. Create a CognoDB instance
1. Sign up at [console.cognodb.com/signup](https://console.cognodb.com/signup) (free, no card required)
2. Create a free (c0) instance, pick a region
3. Copy the `bolt+s://...` URI and the generated password (shown once)

### 2. Configure environment
Copy `.env.example` to `.env` and fill in your credentials:
```
COGNODB_URI=bolt+s://<your-instance-id>.databases.cognodb.cloud
COGNODB_USER=cognodb
COGNODB_PASSWORD=<your-password>
```

### 3. Seed the database
```bash
pip install neo4j faker python-dotenv
python seed.py --clear
```

### 4. Run the backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 5. Run the frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Main queries explained

**1. Fund exposure (2-hop traversal)**
```cypher
MATCH (f:Fund)-[h:HOLDS]->(s:Stock)-[:BELONGS_TO]->(sec:Sector)
WHERE f.name IN $fund_names
RETURN sec.name AS sector, sum(h.weight) AS total_weight
ORDER BY total_weight DESC
```
Rolls up stock-level holdings to sector-level concentration across the selected funds. This is a genuine 2-hop traversal (`Fund → Stock → Sector`).

**2. Overlap exposure (relational-awkward)**
```cypher
MATCH (f:Fund)-[h:HOLDS]->(s:Stock)
WHERE f.name IN $fund_names
WITH s, count(DISTINCT f) AS fund_count, avg(h.weight) AS avg_weight
RETURN s.name AS stock, fund_count, avg_weight
ORDER BY fund_count DESC, avg_weight DESC
```
For each stock, counts how many of the selected funds hold it and averages the weight across those funds. See "Why a graph database?" above for why this is awkward relationally.

Both queries are parameterized via the official `neo4j` Python driver (`session.run(query, fund_names=fund_names)`). There's no string-concatenated Cypher anywhere in the codebase.

---

## Screenshots

<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/a207ab38-f6d5-4753-b41c-3063da1864e9" />
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/292d31e6-00a6-4085-94e6-cb5db277d636" />
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/d70b92a7-1890-447c-8aa7-5c90cd7a5dac" />


---

## Demo

- Hosted app: https://cognodb-portfolio-overlap.vercel.app/
- Screen recording: https://drive.google.com/file/d/1VfcrVt3YRUNA2nJdsAmapQow_4mlEa1p/view?usp=sharing

---

## Project structure

```
backend/
  app/
    main.py       # FastAPI app, routes
    db.py          # driver singleton, connection logic
    queries.py      # parameterized Cypher query functions
  requirements.txt
frontend/
  src/
    App.jsx
    components/
      FundSelector.jsx
      ResultsView.jsx
    api.js
seed.py
.env.example
README.md
```
