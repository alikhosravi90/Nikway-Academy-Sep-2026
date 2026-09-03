INSERT INTO facts (id, statement, domain, status, confidence, source_refs, evidence_refs)
VALUES
('FACT-NIKWAY-001', 'NIKWAY is a knowledge, learning, improvement, and digital operations system.', 'identity', 'confirmed', 'high', '["projects/nikway/INDEX.md"]', '["EVID-001"]'),
('FACT-NIKWAY-002', 'NIKWAY transforms knowledge into capability, capability into action, and action into learning and continuous improvement.', 'philosophy', 'confirmed', 'high', '["projects/nikway/INDEX.md"]', '["EVID-001"]'),
('FACT-ARMY-001', 'Agentic Army defines Commander, Architect, Builder, Reviewer, Researcher, and Tester roles.', 'agentic-army', 'confirmed', 'high', '["README.md"]', '["EVID-004"]')
ON CONFLICT (id) DO NOTHING;
