-- Verify schema after Alembic migrations (MySQL syntax)

-- 1) Columns existence
SELECT 'intervention.sla_escalation_level' AS item, COUNT(*) AS found
FROM information_schema.columns
WHERE table_schema = DATABASE() AND table_name='intervention' AND column_name='sla_escalation_level';

SELECT 'intervention.sla_last_alerted_at' AS item, COUNT(*) AS found
FROM information_schema.columns
WHERE table_schema = DATABASE() AND table_name='intervention' AND column_name='sla_last_alerted_at';

SELECT 'demande_intervention.sla_hours_override' AS item, COUNT(*) AS found
FROM information_schema.columns
WHERE table_schema = DATABASE() AND table_name='demande_intervention' AND column_name='sla_hours_override';

-- 2) Table existence
SELECT 'intervention_history' AS table_name, COUNT(*) AS found FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'intervention_history';

-- 3) NULL checks for critical columns
SELECT 'intervention.statut NULLs' AS item, COUNT(*) AS null_count FROM intervention WHERE statut IS NULL;
SELECT 'demande_intervention.statut NULLs' AS item, COUNT(*) AS null_count FROM demande_intervention WHERE statut IS NULL;

-- 4) Index checks (information_schema.statistics)
SELECT 'ix_intervention_statut' AS idx, COUNT(*) AS found FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='intervention' AND index_name='ix_intervention_statut';
SELECT 'ix_demande_zone' AS idx, COUNT(*) AS found FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='demande_intervention' AND index_name='ix_demande_zone';
SELECT 'ix_mouvement_produit' AS idx, COUNT(*) AS found FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='mouvement_stock' AND index_name='ix_mouvement_produit';

-- 5) Foreign key existence checks
SELECT 'fk_intervention_sla_ack_by_user' AS fk, COUNT(*) AS found FROM information_schema.key_column_usage WHERE table_schema=DATABASE() AND table_name='intervention' AND referenced_table_name='user' AND referenced_column_name='id' AND column_name='sla_acknowledged_by';
SELECT 'intervention_history.fk_intervention' AS fk, COUNT(*) AS found FROM information_schema.key_column_usage WHERE table_schema=DATABASE() AND table_name='intervention_history' AND referenced_table_name='intervention' AND referenced_column_name='id' AND column_name='intervention_id';

-- 6) Quick data sanity checks
SELECT 'recent_interventions_count' AS item, COUNT(*) AS cnt FROM intervention WHERE date_creation >= DATE_SUB(NOW(), INTERVAL 30 DAY);
SELECT 'interventions_with_geo' AS item, COUNT(*) AS cnt FROM intervention WHERE gps_lat IS NOT NULL AND gps_long IS NOT NULL;

-- End of verification script
