-- Migration: Add SLA fields and intervention_history table
-- Run on MySQL (backup your DB first)

ALTER TABLE demande_intervention
  ADD COLUMN sla_hours_override INT NULL;

ALTER TABLE intervention
  ADD COLUMN sla_escalation_level INT NOT NULL DEFAULT 0,
  ADD COLUMN sla_last_alerted_at DATETIME NULL,
  ADD COLUMN sla_acknowledged_by INT NULL,
  ADD COLUMN sla_acknowledged_at DATETIME NULL;

CREATE TABLE IF NOT EXISTS intervention_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  intervention_id INT NOT NULL,
  action VARCHAR(64) NOT NULL,
  user_id INT NULL,
  details TEXT,
  timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (intervention_id) REFERENCES intervention(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Notes:
-- 1) If you use SQLAlchemy+Flask-Migrate in your environment, prefer generating an Alembic migration instead:
--    flask db migrate -m "Add SLA fields and intervention_history"
--    flask db upgrade
-- 2) After running, restart the Flask application so SQLAlchemy metadata matches the DB.
