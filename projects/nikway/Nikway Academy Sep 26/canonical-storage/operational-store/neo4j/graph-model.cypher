CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT fact_id IF NOT EXISTS FOR (n:Fact) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (n:Evidence) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (n:Decision) REQUIRE n.id IS UNIQUE;

MERGE (nikway:Entity {id: 'NIKWAY', name: 'NIKWAY', type: 'System'})
MERGE (army:Entity {id: 'AGENTIC-ARMY', name: 'Agentic Army', type: 'System'})
MERGE (fact:Fact {id: 'FACT-NIKWAY-001', status: 'confirmed'})
MERGE (evidence:Evidence {id: 'EVID-001', reference: 'projects/nikway/INDEX.md'})
MERGE (nikway)-[:DESCRIBED_BY]->(fact)
MERGE (evidence)-[:SUPPORTS]->(fact)
MERGE (army)-[:COORDINATES]->(nikway);
