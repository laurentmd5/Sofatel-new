-- ============================================================
-- SCRIPT DE CORRECTION - TABLE USER (Serveur o2switch)
-- A exécuter dans phpMyAdmin sur la base de données de production
-- ============================================================

-- 1. Vérifier et ajouter la colonne 'commune' si elle n'existe pas
ALTER TABLE `user` 
ADD COLUMN IF NOT EXISTS `commune` VARCHAR(50) DEFAULT NULL;

-- 2. Vérifier et ajouter la colonne 'quartier' si elle n'existe pas
ALTER TABLE `user` 
ADD COLUMN IF NOT EXISTS `quartier` VARCHAR(50) DEFAULT NULL;

-- 3. Vérifier et ajouter la colonne 'technologies' si elle n'existe pas
ALTER TABLE `user` 
ADD COLUMN IF NOT EXISTS `technologies` VARCHAR(100) DEFAULT NULL;

-- 4. Vérifier et ajouter la colonne 'zone_id' si elle n'existe pas
--    (FK vers la table zone - module stock)
ALTER TABLE `user` 
ADD COLUMN IF NOT EXISTS `zone_id` INT DEFAULT NULL;

-- 5. Si la table 'zone' existe, ajouter la FK (sinon ignorer)
-- ALTER TABLE `user` ADD CONSTRAINT `fk_user_zone` FOREIGN KEY (`zone_id`) REFERENCES `zone`(`id`) ON DELETE SET NULL;

-- 6. S'assurer que 'actif' existe avec une valeur par défaut
ALTER TABLE `user` 
MODIFY COLUMN `actif` TINYINT(1) NOT NULL DEFAULT 1;

-- 7. S'assurer que le champ password_hash est assez grand (werkzeug génère des hash bcrypt longs)
ALTER TABLE `user` 
MODIFY COLUMN `password_hash` VARCHAR(512) NOT NULL;

-- Vérifier la structure finale de la table user
DESCRIBE `user`;
