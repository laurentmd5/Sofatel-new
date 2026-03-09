-- Script d'initialisation MySQL pour SOFATELCOM
-- Créé automatiquement au démarrage du conteneur

-- Créer les tables de base si nécessaire
USE sofatelcom_db;

-- Table users (si elle n'existe pas)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(120) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(120),
    last_name VARCHAR(120),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Créer un utilisateur système par défaut
INSERT IGNORE INTO users (username, email, password_hash, first_name, last_name, role, is_active)
VALUES ('system', 'system@sofatelcom.local', 'system_hash', 'System', 'Account', 'admin', TRUE);

-- Créer un utilisateur administrateur par défaut
INSERT IGNORE INTO users (username, email, password_hash, first_name, last_name, role, is_active)
VALUES ('admin', 'admin@sofatelcom.local', 'admin_hash', 'Admin', 'User', 'admin', TRUE);

-- Activer les index pour les performances
ALTER TABLE users ENGINE=InnoDB;

-- Vérification
SELECT COUNT(*) as total_users FROM users;
