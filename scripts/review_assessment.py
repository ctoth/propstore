"""Assess the code review's recommendations against the live knowledge base."""

import sqlite3
from pathlib import Path

db = Path("knowledge/sidecar/propstore.sqlite")
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row

print("=" * 60)
print("REVIEW ASSESSMENT: propstore knowledge base vs review-v0.md")
print("=" * 60)

# Basic stats
concepts = conn.execute("SELECT COUNT(*) FROM concept").fetchone()[0]
claims = conn.execute("SELECT COUNT(*) FROM claim").fetchone()[0]
stances = conn.execute("SELECT COUNT(*) FROM claim_stance WHERE stance_type != 'none'").fetchone()[0]
conflicts = conn.execute("SELECT COUNT(*) FROM conflicts").fetchone()[0]
print(f"\nKnowledge base: {concepts} concepts, {claims} claims, {stances} stances, {conflicts} conflicts")

# Claim type distribution
print("\n--- Claim types ---")
for row in conn.execute("SELECT type, COUNT(*) n FROM claim GROUP BY type ORDER BY n DESC"):
    print(f"  {row['type']}: {row['n']}")

# Cross-paper stances
print("\n--- Cross-paper stances (different source papers) ---")
rows = conn.execute("""
    SELECT cs.stance_type, COUNT(*) n
    FROM claim_stance cs
    JOIN claim c1 ON cs.claim_id = c1.id
    JOIN claim c2 ON cs.target_claim_id = c2.id
    WHERE c1.source_paper != c2.source_paper
    AND cs.stance_type != 'none'
    GROUP BY cs.stance_type ORDER BY n DESC
""").fetchall()
total_cross = sum(r['n'] for r in rows)
for row in rows:
    print(f"  {row['stance_type']}: {row['n']}")
print(f"  TOTAL cross-paper: {total_cross}")

# Within-paper stances
rows2 = conn.execute("""
    SELECT cs.stance_type, COUNT(*) n
    FROM claim_stance cs
    JOIN claim c1 ON cs.claim_id = c1.id
    JOIN claim c2 ON cs.target_claim_id = c2.id
    WHERE c1.source_paper = c2.source_paper
    AND cs.stance_type != 'none'
    GROUP BY cs.stance_type ORDER BY n DESC
""").fetchall()
total_within = sum(r['n'] for r in rows2)
print(f"  TOTAL within-paper: {total_within}")

# Concepts referenced by most papers
print("\n--- Most cross-referenced concepts ---")
for row in conn.execute("""
    SELECT c.concept_id, COUNT(DISTINCT c.source_paper) papers, COUNT(*) claims
    FROM claim c WHERE c.concept_id IS NOT NULL
    GROUP BY c.concept_id HAVING papers >= 2
    ORDER BY papers DESC LIMIT 15
"""):
    print(f"  {row['concept_id']}: {row['papers']} papers, {row['claims']} claims")

# Observation claims that share concepts across papers
print("\n--- Observation overlap: concepts appearing in observations from 2+ papers ---")
for row in conn.execute("""
    SELECT concept_id, COUNT(DISTINCT source_paper) papers
    FROM claim
    WHERE type = 'observation' AND concept_id IS NOT NULL
    GROUP BY concept_id HAVING papers >= 2
    ORDER BY papers DESC LIMIT 10
"""):
    print(f"  {row['concept_id']}: {row['papers']} papers")

# Top rebuts/undercuts (the most interesting relationships)
print("\n--- Top cross-paper attacks (rebuts/undercuts/undermines) ---")
for row in conn.execute("""
    SELECT cs.stance_type, c1.source_paper src, c2.source_paper tgt, cs.note
    FROM claim_stance cs
    JOIN claim c1 ON cs.claim_id = c1.id
    JOIN claim c2 ON cs.target_claim_id = c2.id
    WHERE c1.source_paper != c2.source_paper
    AND cs.stance_type IN ('rebuts', 'undercuts', 'undermines')
    AND cs.confidence >= 0.8
    ORDER BY cs.confidence DESC
    LIMIT 10
"""):
    src = row['src'].split('_')[0] + ' ' + row['src'].split('_')[1]
    tgt = row['tgt'].split('_')[0] + ' ' + row['tgt'].split('_')[1]
    print(f"  {row['stance_type']}: {src} -> {tgt}")
    print(f"    {row['note'][:120]}")

# Embedding similarity: find closest cross-paper pairs
print("\n--- Highest similarity cross-paper claim pairs ---")
try:
    from propstore.embed import find_similar, _load_vec_extension, get_registered_models
    _load_vec_extension(conn)
    models = get_registered_models(conn)
    if models:
        model = models[0]['model_name']
        # Sample a few claims and find cross-paper similar
        sample = conn.execute("SELECT id, source_paper FROM claim ORDER BY RANDOM() LIMIT 5").fetchall()
        for s in sample:
            similar = find_similar(conn, s['id'], model, top_k=3)
            for sim in similar:
                sim_paper = conn.execute("SELECT source_paper FROM claim WHERE id = ?", (sim['id'],)).fetchone()
                if sim_paper and sim_paper['source_paper'] != s['source_paper']:
                    print(f"  {s['id'][:40]} <-> {sim['id'][:40]} (dist={sim['distance']:.3f})")
except Exception as e:
    print(f"  (embedding search unavailable: {e})")

conn.close()
