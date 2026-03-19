-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Hôte : localhost:3306
-- Généré le : mer. 18 mars 2026 à 15:09
-- Version du serveur : 11.4.10-MariaDB
-- Version de PHP : 8.3.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `qirm8908_sofatel-sn`
--

-- --------------------------------------------------------

--
-- Structure de la table `activity_log`
--

CREATE TABLE `activity_log` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `action` varchar(50) NOT NULL,
  `module` varchar(50) NOT NULL,
  `entity_id` int(11) DEFAULT NULL,
  `entity_name` varchar(255) DEFAULT NULL,
  `details` text DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `timestamp` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `activity_log`
--

INSERT INTO `activity_log` (`id`, `user_id`, `action`, `module`, `entity_id`, `entity_name`, `details`, `ip_address`, `timestamp`) VALUES
(1, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '41.82.176.211', '2026-03-10 18:35:13'),
(2, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '41.82.176.211', '2026-03-10 18:35:14'),
(3, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '41.82.176.211', '2026-03-10 18:35:19'),
(4, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '41.82.176.211', '2026-03-10 18:57:04'),
(5, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.125.138.37', '2026-03-11 15:46:45'),
(6, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-11 15:53:00'),
(7, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-11 16:30:03'),
(8, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-11 17:16:49'),
(9, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-11 17:17:53'),
(10, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-11 17:18:23'),
(11, 1, 'view_dashboard', 'rh', NULL, 'System Administrateur', '{\"year\": 2026, \"month\": 3}', '196.207.231.232', '2026-03-11 17:18:51'),
(12, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-11 17:59:11'),
(13, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-12 14:04:53'),
(14, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-12 14:40:49'),
(15, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-12 19:55:34'),
(16, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-12 20:32:54'),
(17, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-12 20:43:09'),
(18, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '41.82.171.242', '2026-03-12 20:49:44'),
(19, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '196.207.231.232', '2026-03-12 21:14:12'),
(20, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '41.82.171.242', '2026-03-12 21:47:39'),
(21, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.107.112', '2026-03-13 14:59:53'),
(22, 567, 'login', 'auth', NULL, 'test1 test1', '{\"username\": \"test1\"}', '41.82.74.216', '2026-03-16 09:04:12'),
(23, 567, 'logout', 'auth', NULL, 'test1 test1', '{\"username\": \"test1\"}', '41.82.74.216', '2026-03-16 09:26:45'),
(24, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '41.82.74.216', '2026-03-16 10:20:02'),
(25, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.67', '2026-03-16 11:15:23'),
(26, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.67', '2026-03-16 11:15:23'),
(27, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.67', '2026-03-16 11:15:28'),
(28, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.67', '2026-03-16 11:44:19'),
(29, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '41.82.74.216', '2026-03-16 12:27:39'),
(30, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '41.82.74.216', '2026-03-16 12:48:32'),
(31, 8, 'login', 'auth', NULL, 'Jean Marie NDIONE', '{\"username\": \"jmndione\"}', '154.124.75.67', '2026-03-16 12:49:26'),
(32, 8, 'logout', 'auth', NULL, 'Jean Marie NDIONE', '{\"username\": \"jmndione\"}', '154.124.75.67', '2026-03-16 12:49:26'),
(33, 8, 'login', 'auth', NULL, 'Jean Marie NDIONE', '{\"username\": \"jmndione\"}', '154.124.75.67', '2026-03-16 12:49:30'),
(34, 8, 'logout', 'auth', NULL, 'Jean Marie NDIONE', '{\"username\": \"jmndione\"}', '154.124.75.67', '2026-03-16 12:49:38'),
(35, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.67', '2026-03-16 12:49:44'),
(36, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.67', '2026-03-16 13:16:28'),
(37, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.67', '2026-03-16 13:23:37'),
(38, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.67', '2026-03-16 13:44:11'),
(39, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '41.82.74.216', '2026-03-16 15:26:59'),
(40, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.125.126.69', '2026-03-17 10:25:07'),
(41, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.125.126.69', '2026-03-17 10:27:08'),
(42, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.125.126.69', '2026-03-17 10:27:23'),
(43, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.125.126.69', '2026-03-17 10:57:24'),
(44, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.100', '2026-03-17 11:36:10'),
(45, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.100', '2026-03-17 11:36:13'),
(46, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.100', '2026-03-17 11:36:20'),
(47, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.7', '2026-03-17 11:59:56'),
(48, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.7', '2026-03-18 10:20:35'),
(49, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.7', '2026-03-18 10:20:35'),
(50, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.7', '2026-03-18 10:20:39'),
(51, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.7', '2026-03-18 10:49:52'),
(52, 1, 'login', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.7', '2026-03-18 11:06:52'),
(53, 1, 'logout', 'auth', NULL, 'System Administrateur', '{\"username\": \"admin\"}', '154.124.75.7', '2026-03-18 11:42:38');

-- --------------------------------------------------------

--
-- Structure de la table `alembic_version`
--

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `alembic_version`
--

INSERT INTO `alembic_version` (`version_num`) VALUES
('8d5157421e44');

-- --------------------------------------------------------

--
-- Structure de la table `audit_log`
--

CREATE TABLE `audit_log` (
  `id` int(11) NOT NULL,
  `actor_id` int(11) NOT NULL,
  `action` varchar(100) NOT NULL,
  `entity_type` varchar(50) NOT NULL,
  `entity_id` int(11) NOT NULL,
  `old_value` text DEFAULT NULL,
  `new_value` text DEFAULT NULL,
  `details` text DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `audit_log`
--

INSERT INTO `audit_log` (`id`, `actor_id`, `action`, `entity_type`, `entity_id`, `old_value`, `new_value`, `details`, `ip_address`, `user_agent`, `created_at`) VALUES
(1, 1, 'stock_entry', 'stock', 2, NULL, '{\"quantity_added\": 1.0}', '{\"supplier\": null, \"invoice\": null}', '127.0.0.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36', '2026-02-27 13:12:18'),
(2, 79, 'stock_removal', 'stock', 2, NULL, '{\"quantity_removed\": 10.0}', '{\"reason\": \"[VENTE_CLIENT] - vente\"}', '127.0.0.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36', '2026-02-27 13:21:56'),
(3, 79, 'stock_removal', 'stock', 2, NULL, '{\"quantity_removed\": 10.0}', '{\"reason\": \"[AUTRE_ZONE] - VENTE\"}', '127.0.0.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36', '2026-02-27 13:23:06'),
(4, 79, 'stock_removal', 'stock', 2, NULL, '{\"quantity_removed\": 10.0}', '{\"reason\": \"[VENTE_CLIENT]\"}', '127.0.0.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36', '2026-02-27 13:30:33');

-- --------------------------------------------------------

--
-- Structure de la table `categorie`
--

CREATE TABLE `categorie` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `date_creation` datetime DEFAULT NULL,
  `date_maj` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `client`
--

CREATE TABLE `client` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(100) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `adresse` varchar(255) NOT NULL,
  `quartier` varchar(100) DEFAULT NULL,
  `commune` varchar(100) DEFAULT NULL,
  `numero_ligne_sonatel` varchar(50) DEFAULT NULL,
  `numero_demande` varchar(50) DEFAULT NULL,
  `offre` varchar(100) DEFAULT NULL,
  `statut_contrat` varchar(50) DEFAULT NULL,
  `date_souscription` datetime DEFAULT NULL,
  `date_resilition` datetime DEFAULT NULL,
  `date_creation` datetime NOT NULL,
  `date_modification` datetime DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `demande_intervention`
--

CREATE TABLE `demande_intervention` (
  `id` int(11) NOT NULL,
  `nd` varchar(50) NOT NULL,
  `demandee` varchar(50) DEFAULT NULL,
  `zone` varchar(50) NOT NULL,
  `priorite_traitement` varchar(50) DEFAULT NULL,
  `origine` varchar(100) DEFAULT NULL,
  `offre` varchar(100) DEFAULT NULL,
  `type_techno` varchar(50) NOT NULL,
  `produit` varchar(100) DEFAULT NULL,
  `age` varchar(10) DEFAULT NULL,
  `nom_client` varchar(100) NOT NULL,
  `prenom_client` varchar(100) DEFAULT NULL,
  `rep_srp` varchar(100) DEFAULT NULL,
  `constitution` varchar(100) DEFAULT NULL,
  `specialite` varchar(100) DEFAULT NULL,
  `resultat_essai` varchar(100) DEFAULT NULL,
  `commentaire_essai` text DEFAULT NULL,
  `agent_essai` varchar(100) DEFAULT NULL,
  `date_demande_intervention` datetime NOT NULL,
  `commentaire_interv` text DEFAULT NULL,
  `id_ot` varchar(50) DEFAULT NULL,
  `fichier_importe_id` int(11) DEFAULT NULL,
  `equipe` varchar(100) DEFAULT NULL,
  `section_id` varchar(50) DEFAULT NULL,
  `statut` varchar(50) DEFAULT NULL,
  `technicien_id` int(11) DEFAULT NULL,
  `libelle_commune` varchar(100) DEFAULT NULL,
  `libelle_quartier` varchar(255) DEFAULT NULL,
  `prestataire` varchar(50) DEFAULT NULL,
  `taches` varchar(100) DEFAULT NULL,
  `service` varchar(50) NOT NULL,
  `date_creation` datetime DEFAULT NULL,
  `date_affectation` datetime DEFAULT NULL,
  `date_completion` datetime DEFAULT NULL,
  `date_echeance` date DEFAULT NULL,
  `contact_client` varchar(100) DEFAULT NULL,
  `commentaire_contact` text DEFAULT NULL,
  `zone_rs` varchar(100) DEFAULT NULL,
  `id_drgt` varchar(50) DEFAULT NULL,
  `libel_sig` varchar(100) DEFAULT NULL,
  `date_sig` datetime DEFAULT NULL,
  `compteur` varchar(50) DEFAULT NULL,
  `commande_client` varchar(100) DEFAULT NULL,
  `date_validation` datetime DEFAULT NULL,
  `heure` varchar(50) DEFAULT NULL,
  `rbs` varchar(100) DEFAULT NULL,
  `pilotes` varchar(100) DEFAULT NULL,
  `st` varchar(100) DEFAULT NULL,
  `ci_prcl` varchar(100) DEFAULT NULL,
  `coordonnees_gps` varchar(100) DEFAULT NULL,
  `sr` varchar(100) DEFAULT NULL,
  `adresse` text DEFAULT NULL,
  `sla_hours_override` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `dossier_sav`
--

CREATE TABLE `dossier_sav` (
  `id` int(11) NOT NULL,
  `numero_dossier` varchar(50) NOT NULL,
  `numero_serie_id` int(11) NOT NULL,
  `client_id` int(11) NOT NULL,
  `intervention_id` int(11) DEFAULT NULL,
  `motif_retour` varchar(255) NOT NULL,
  `description_probleme` text DEFAULT NULL,
  `date_ouverture` datetime NOT NULL,
  `statut` varchar(50) DEFAULT NULL,
  `date_resolution` datetime DEFAULT NULL,
  `resolution` text DEFAULT NULL,
  `numero_serie_remplacement_id` int(11) DEFAULT NULL,
  `cree_par_id` int(11) NOT NULL,
  `date_creation` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `emplacement_stock`
--

CREATE TABLE `emplacement_stock` (
  `id` int(11) NOT NULL,
  `code` varchar(20) NOT NULL,
  `designation` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `actif` tinyint(1) DEFAULT NULL,
  `date_creation` datetime DEFAULT NULL,
  `date_maj` datetime DEFAULT NULL,
  `zone_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `emplacement_stock`
--

INSERT INTO `emplacement_stock` (`id`, `code`, `designation`, `description`, `actif`, `date_creation`, `date_maj`, `zone_id`) VALUES
(4, 'EMP001', 'Entrepot Centrale', '', 1, '2026-01-07 10:26:11', '2026-01-07 10:26:11', NULL),
(5, 'EMP002', 'Stock Véhicule', '', 1, '2026-01-07 10:26:11', '2026-01-07 10:26:11', NULL),
(6, 'EMP003', 'Stock Personnel', '', 1, '2026-01-07 10:26:11', '2026-01-07 10:26:11', NULL),
(7, 'EMP004', 'Stock Dakar', '', 1, '2026-01-07 10:26:11', '2026-01-07 10:26:11', NULL),
(8, 'EMP005', 'Stock Mbour', '', 1, '2026-01-07 10:26:11', '2026-01-07 10:26:11', NULL),
(9, 'EMP006', 'Stock Kaolack', '', 1, '2026-01-07 10:26:11', '2026-01-07 10:26:11', NULL),
(10, 'EMP007', 'Autres', '', 1, '2026-01-07 10:26:11', '2026-01-07 10:26:11', NULL);

-- --------------------------------------------------------

--
-- Structure de la table `equipe`
--

CREATE TABLE `equipe` (
  `id` int(11) NOT NULL,
  `nom_equipe` varchar(100) NOT NULL,
  `date_creation` date NOT NULL,
  `chef_zone_id` int(11) NOT NULL,
  `zone` varchar(50) NOT NULL,
  `prestataire` varchar(50) DEFAULT NULL,
  `technologies` varchar(100) NOT NULL,
  `service` varchar(50) NOT NULL,
  `actif` tinyint(1) DEFAULT NULL,
  `publie` tinyint(1) DEFAULT NULL,
  `date_publication` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `fiche_technique`
--

CREATE TABLE `fiche_technique` (
  `id` int(11) NOT NULL,
  `nom_raison_sociale` varchar(255) NOT NULL,
  `contact` varchar(255) NOT NULL,
  `represente_par` varchar(255) DEFAULT NULL,
  `date_installation` date NOT NULL,
  `tel1` varchar(20) NOT NULL,
  `tel2` varchar(20) DEFAULT NULL,
  `adresse_demandee` varchar(255) NOT NULL,
  `etage` varchar(50) DEFAULT NULL,
  `gps_lat` varchar(50) DEFAULT NULL,
  `gps_long` varchar(50) DEFAULT NULL,
  `type_logement_avec_bpi` text DEFAULT NULL,
  `type_logement_sans_bpi` text DEFAULT NULL,
  `h_arrivee` time DEFAULT NULL,
  `h_depart` time DEFAULT NULL,
  `n_ligne` varchar(50) DEFAULT NULL,
  `n_demande` varchar(50) DEFAULT NULL,
  `technicien_structure` varchar(100) DEFAULT NULL,
  `pilote_structure` varchar(100) DEFAULT NULL,
  `offre` varchar(100) DEFAULT NULL,
  `debit` varchar(50) DEFAULT NULL,
  `type_mc` tinyint(1) DEFAULT NULL,
  `type_na` tinyint(1) DEFAULT NULL,
  `type_transfert` tinyint(1) DEFAULT NULL,
  `type_autre` tinyint(1) DEFAULT NULL,
  `backoffice_structure` varchar(100) DEFAULT NULL,
  `type_ont` varchar(100) DEFAULT NULL,
  `nature_ont` varchar(100) DEFAULT NULL,
  `numero_serie_ont` varchar(100) DEFAULT NULL,
  `type_decodeur` varchar(100) DEFAULT NULL,
  `nature_decodeur` varchar(100) DEFAULT NULL,
  `numero_serie_decodeur` varchar(100) DEFAULT NULL,
  `disque_dur` tinyint(1) DEFAULT NULL,
  `telephone` tinyint(1) DEFAULT NULL,
  `recepteur_wifi` tinyint(1) DEFAULT NULL,
  `cpl` tinyint(1) DEFAULT NULL,
  `carte_vaccess` tinyint(1) DEFAULT NULL,
  `type_cable_lc` varchar(100) DEFAULT NULL,
  `type_cable_bti` varchar(100) DEFAULT NULL,
  `type_cable_pto_one` varchar(100) DEFAULT NULL,
  `kit_pto` tinyint(1) DEFAULT NULL,
  `piton` tinyint(1) DEFAULT NULL,
  `arobase` tinyint(1) DEFAULT NULL,
  `malico` tinyint(1) DEFAULT NULL,
  `ds6` tinyint(1) DEFAULT NULL,
  `autre_accessoire` varchar(255) DEFAULT NULL,
  `appel_sortant_ok` tinyint(1) DEFAULT NULL,
  `appel_sortant_nok` tinyint(1) DEFAULT NULL,
  `appel_entrant_ok` tinyint(1) DEFAULT NULL,
  `appel_entrant_nok` tinyint(1) DEFAULT NULL,
  `tvo_mono_ok` tinyint(1) DEFAULT NULL,
  `tvo_mono_nok` tinyint(1) DEFAULT NULL,
  `tvo_multi_ok` tinyint(1) DEFAULT NULL,
  `tvo_multi_nok` tinyint(1) DEFAULT NULL,
  `enregistreur_dd_ok` tinyint(1) DEFAULT NULL,
  `enregistreur_dd_nok` tinyint(1) DEFAULT NULL,
  `par_cable_salon` varchar(50) DEFAULT NULL,
  `par_cable_chambres` varchar(50) DEFAULT NULL,
  `par_cable_bureau` varchar(50) DEFAULT NULL,
  `par_cable_autres` varchar(50) DEFAULT NULL,
  `par_cable_vitesse_wifi` varchar(50) DEFAULT NULL,
  `par_cable_mesure_mbps` int(11) DEFAULT NULL,
  `par_wifi_salon` varchar(50) DEFAULT NULL,
  `par_wifi_chambres` varchar(50) DEFAULT NULL,
  `par_wifi_bureau` varchar(50) DEFAULT NULL,
  `par_wifi_autres` varchar(50) DEFAULT NULL,
  `par_wifi_vitesse_wifi` varchar(50) DEFAULT NULL,
  `par_wifi_mesure_mbps` int(11) DEFAULT NULL,
  `etiquetage_colliers_serres` tinyint(1) DEFAULT NULL,
  `etiquetage_pbo_normalise` tinyint(1) DEFAULT NULL,
  `nettoyage_depose` tinyint(1) DEFAULT NULL,
  `nettoyage_tutorat` tinyint(1) DEFAULT NULL,
  `rattachement_nro` varchar(100) DEFAULT NULL,
  `rattachement_type` varchar(100) DEFAULT NULL,
  `rattachement_num_carte` varchar(100) DEFAULT NULL,
  `rattachement_num_port` varchar(100) DEFAULT NULL,
  `rattachement_plaque` varchar(100) DEFAULT NULL,
  `rattachement_bpi_pbo` varchar(100) DEFAULT NULL,
  `rattachement_coupleur` varchar(100) DEFAULT NULL,
  `rattachement_fibre` varchar(100) DEFAULT NULL,
  `rattachement_ref_dbm` varchar(50) DEFAULT NULL,
  `rattachement_mesure_dbm` varchar(50) DEFAULT NULL,
  `commentaires` text DEFAULT NULL,
  `photos` text DEFAULT NULL,
  `signature_equipe` text DEFAULT NULL,
  `signature_client` text DEFAULT NULL,
  `client_tres_satisfait` tinyint(1) DEFAULT NULL,
  `client_satisfait` tinyint(1) DEFAULT NULL,
  `client_pas_satisfait` tinyint(1) DEFAULT NULL,
  `date_creation` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `technicien_id` int(11) DEFAULT NULL,
  `intervention_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `fichier_import`
--

CREATE TABLE `fichier_import` (
  `id` int(11) NOT NULL,
  `nom_fichier` varchar(255) NOT NULL,
  `date_import` datetime DEFAULT NULL,
  `importe_par` int(11) NOT NULL,
  `nb_lignes` int(11) DEFAULT NULL,
  `nb_erreurs` int(11) DEFAULT NULL,
  `statut` varchar(20) DEFAULT NULL,
  `service` varchar(20) DEFAULT NULL,
  `actif` tinyint(1) DEFAULT 1,
  `date_suppression` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `fournisseur`
--

CREATE TABLE `fournisseur` (
  `id` int(11) NOT NULL,
  `code` varchar(20) NOT NULL,
  `raison_sociale` varchar(200) NOT NULL,
  `contact` varchar(100) DEFAULT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `adresse` text DEFAULT NULL,
  `actif` tinyint(1) DEFAULT NULL,
  `date_creation` datetime DEFAULT NULL,
  `date_maj` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `fournisseur`
--

INSERT INTO `fournisseur` (`id`, `code`, `raison_sociale`, `contact`, `telephone`, `email`, `adresse`, `actif`, `date_creation`, `date_maj`) VALUES
(76, '1000', 'SONATEL', '', '', 'sonatel@gmail.com', '', 1, '2026-02-27 14:04:20', '2026-02-27 14:04:20');

-- --------------------------------------------------------

--
-- Structure de la table `historique_etat_numero_serie`
--

CREATE TABLE `historique_etat_numero_serie` (
  `id` int(11) NOT NULL,
  `numero_serie_id` int(11) NOT NULL,
  `ancien_statut` enum('EN_MAGASIN','ALLOUE_ZONE','ALLOUE_TECHNICIEN','INSTALLEE','RETOURNEE','REBUT') NOT NULL,
  `nouveau_statut` enum('EN_MAGASIN','ALLOUE_ZONE','ALLOUE_TECHNICIEN','INSTALLEE','RETOURNEE','REBUT') NOT NULL,
  `date_transition` datetime NOT NULL,
  `utilisateur_id` int(11) NOT NULL,
  `raison` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `import_historique_numero_serie`
--

CREATE TABLE `import_historique_numero_serie` (
  `id` int(11) NOT NULL,
  `nom_fichier` varchar(255) NOT NULL,
  `bon_livraison_ref` varchar(100) NOT NULL,
  `produit_id` int(11) NOT NULL,
  `nb_lignes_fichier` int(11) NOT NULL,
  `nb_importe` int(11) NOT NULL,
  `nb_erreurs` int(11) NOT NULL,
  `nb_doublons` int(11) NOT NULL,
  `rapport` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`rapport`)),
  `date_import` datetime NOT NULL,
  `utilisateur_id` int(11) NOT NULL,
  `contenu_fichier` blob DEFAULT NULL,
  `statut` varchar(50) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `intervention`
--

CREATE TABLE `intervention` (
  `id` int(11) NOT NULL,
  `demande_id` int(11) NOT NULL,
  `technicien_id` int(11) NOT NULL,
  `equipe_id` int(11) DEFAULT NULL,
  `motif_rejet` varchar(512) DEFAULT NULL,
  `accuse_reception` tinyint(1) DEFAULT NULL,
  `numero` varchar(50) DEFAULT NULL,
  `constitutions` varchar(100) DEFAULT NULL,
  `valeur_pB0` varchar(50) DEFAULT NULL,
  `nature_signalisation` varchar(100) DEFAULT NULL,
  `diagnostic_technicien` text DEFAULT NULL,
  `cause_derangement` text DEFAULT NULL,
  `action_releve` text DEFAULT NULL,
  `gps_lat` varchar(50) DEFAULT NULL,
  `gps_long` varchar(50) DEFAULT NULL,
  `materiel_livre` varchar(100) DEFAULT NULL,
  `materiel_recup` varchar(100) DEFAULT NULL,
  `numero_serie_livre` varchar(100) DEFAULT NULL,
  `numero_serie_recup` varchar(100) DEFAULT NULL,
  `jarretiere` varchar(50) DEFAULT NULL,
  `nombre_type_bpe` varchar(50) DEFAULT NULL,
  `coupleur_c1` varchar(50) DEFAULT NULL,
  `coupleur_c2` varchar(50) DEFAULT NULL,
  `arobase` varchar(50) DEFAULT NULL,
  `malico` varchar(50) DEFAULT NULL,
  `type_cable` varchar(50) DEFAULT NULL,
  `lc_metre` varchar(50) DEFAULT NULL,
  `bti_metre` varchar(50) DEFAULT NULL,
  `pto_one` varchar(50) DEFAULT NULL,
  `kitpto_metre` varchar(50) DEFAULT NULL,
  `piton` varchar(50) DEFAULT NULL,
  `ds6` varchar(50) DEFAULT NULL,
  `autres_accessoires` varchar(100) DEFAULT NULL,
  `appel_sortant` tinyint(1) DEFAULT NULL,
  `envoi_numero` varchar(20) DEFAULT NULL,
  `appel_entrant` tinyint(1) DEFAULT NULL,
  `affichage_numero` varchar(20) DEFAULT NULL,
  `tvo_mono_ok` tinyint(1) DEFAULT NULL,
  `pieces` text DEFAULT NULL,
  `communes` varchar(100) DEFAULT NULL,
  `chambres` int(11) DEFAULT NULL,
  `bureau` int(11) DEFAULT NULL,
  `wifi_extender` tinyint(1) DEFAULT NULL,
  `debit_cable_montant` varchar(50) DEFAULT NULL,
  `debit_mbs_descendant` varchar(50) DEFAULT NULL,
  `debit_mbs_ping` varchar(50) DEFAULT NULL,
  `debit_ms` varchar(50) DEFAULT NULL,
  `statut` varchar(20) DEFAULT NULL,
  `date_debut` datetime DEFAULT NULL,
  `date_fin` datetime DEFAULT NULL,
  `date_creation` datetime DEFAULT NULL,
  `date_validation` datetime DEFAULT NULL,
  `satisfaction` varchar(20) DEFAULT NULL,
  `signature_equipe` text DEFAULT NULL,
  `signature_client` text DEFAULT NULL,
  `valide_par` int(11) DEFAULT NULL,
  `commentaire_validation` text DEFAULT NULL,
  `photos` text DEFAULT NULL,
  `survey_ok` tinyint(1) DEFAULT NULL,
  `survey_date` datetime DEFAULT NULL,
  `fichier_technique_accessible` tinyint(1) DEFAULT NULL,
  `mesure_dbm` varchar(10) DEFAULT NULL,
  `sla_escalation_level` int(11) DEFAULT 0,
  `sla_last_alerted_at` datetime DEFAULT NULL,
  `sla_acknowledged_by` int(11) DEFAULT NULL,
  `sla_acknowledged_at` datetime DEFAULT NULL,
  `completeness_score` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `intervention_history`
--

CREATE TABLE `intervention_history` (
  `id` int(11) NOT NULL,
  `intervention_id` int(11) NOT NULL,
  `action` varchar(50) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `details` text DEFAULT NULL,
  `timestamp` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `kpi_alerte`
--

CREATE TABLE `kpi_alerte` (
  `id` int(11) NOT NULL,
  `technicien_id` int(11) NOT NULL,
  `kpi_score_id` int(11) DEFAULT NULL,
  `type_alerte` varchar(50) NOT NULL,
  `metrique` varchar(100) DEFAULT NULL,
  `severite` varchar(20) DEFAULT NULL,
  `titre` varchar(255) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `valeur_actuelle` float DEFAULT NULL,
  `valeur_seuil` float DEFAULT NULL,
  `recommandations` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`recommandations`)),
  `active` tinyint(1) DEFAULT NULL,
  `date_creation` datetime DEFAULT NULL,
  `date_resolution` datetime DEFAULT NULL,
  `resolu_par` varchar(100) DEFAULT NULL,
  `date_modification` datetime DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `kpi_historique`
--

CREATE TABLE `kpi_historique` (
  `id` int(11) NOT NULL,
  `technicien_id` int(11) NOT NULL,
  `date` date NOT NULL,
  `score_total` float DEFAULT NULL,
  `score_resolution_1ere_visite` float DEFAULT NULL,
  `score_respect_sla` float DEFAULT NULL,
  `score_qualite_rapports` float DEFAULT NULL,
  `score_satisfaction_client` float DEFAULT NULL,
  `score_consommation_stock` float DEFAULT NULL,
  `nombre_interventions` int(11) DEFAULT NULL,
  `nombre_sla_respectes` int(11) DEFAULT NULL,
  `nombre_sla_violes` int(11) DEFAULT NULL,
  `satisfaction_moyenne` float DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `kpi_metric`
--

CREATE TABLE `kpi_metric` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `description` varchar(500) DEFAULT NULL,
  `poids` float DEFAULT NULL,
  `seuil_min` float DEFAULT NULL,
  `seuil_max` float DEFAULT NULL,
  `seuil_alerte` float DEFAULT NULL,
  `formule` varchar(500) DEFAULT NULL,
  `unite` varchar(50) DEFAULT NULL,
  `actif` tinyint(1) DEFAULT NULL,
  `date_creation` datetime DEFAULT NULL,
  `date_modification` datetime DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `kpi_objectif`
--

CREATE TABLE `kpi_objectif` (
  `id` int(11) NOT NULL,
  `technicien_id` int(11) NOT NULL,
  `objectif_score_total` float DEFAULT NULL,
  `objectif_resolution_1ere_visite` float DEFAULT NULL,
  `objectif_respect_sla` float DEFAULT NULL,
  `objectif_qualite_rapports` float DEFAULT NULL,
  `objectif_satisfaction_client` float DEFAULT NULL,
  `objectif_consommation_stock` float DEFAULT NULL,
  `annee` int(11) NOT NULL,
  `date_debut` date DEFAULT NULL,
  `date_fin` date DEFAULT NULL,
  `remarques` text DEFAULT NULL,
  `date_creation` datetime DEFAULT NULL,
  `date_modification` datetime DEFAULT NULL,
  `modifie_par` varchar(100) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `kpi_score`
--

CREATE TABLE `kpi_score` (
  `id` int(11) NOT NULL,
  `technicien_id` int(11) NOT NULL,
  `equipe_id` int(11) DEFAULT NULL,
  `periode_debut` date NOT NULL,
  `periode_fin` date NOT NULL,
  `periode_type` varchar(20) DEFAULT NULL,
  `score_total` float DEFAULT NULL,
  `score_resolution_1ere_visite` float DEFAULT NULL,
  `score_respect_sla` float DEFAULT NULL,
  `score_qualite_rapports` float DEFAULT NULL,
  `score_satisfaction_client` float DEFAULT NULL,
  `score_consommation_stock` float DEFAULT NULL,
  `details_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`details_json`)),
  `rang_equipe` int(11) DEFAULT NULL,
  `rang_global` int(11) DEFAULT NULL,
  `tendance` varchar(20) DEFAULT NULL,
  `variation_periode_precedente` float DEFAULT NULL,
  `alerte_active` tinyint(1) DEFAULT NULL,
  `anomalie_detectee` tinyint(1) DEFAULT NULL,
  `date_calcul` datetime DEFAULT NULL,
  `date_modification` datetime DEFAULT NULL,
  `calcule_par` varchar(100) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `leave_request`
--

CREATE TABLE `leave_request` (
  `id` int(11) NOT NULL,
  `technicien_id` int(11) NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `type` varchar(50) NOT NULL,
  `statut` varchar(20) DEFAULT NULL,
  `reason` text DEFAULT NULL,
  `manager_id` int(11) DEFAULT NULL,
  `manager_comment` text DEFAULT NULL,
  `approved_at` datetime DEFAULT NULL,
  `business_days_count` float DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `ligne_mouvement_stock`
--

CREATE TABLE `ligne_mouvement_stock` (
  `id` int(11) NOT NULL,
  `mouvement_id` int(11) NOT NULL,
  `produit_id` int(11) NOT NULL,
  `quantite` float NOT NULL,
  `prix_unitaire` float DEFAULT NULL,
  `montant_total` float DEFAULT NULL,
  `numero_serie` varchar(100) DEFAULT NULL,
  `numero_lot` varchar(100) DEFAULT NULL,
  `date_peremption` date DEFAULT NULL,
  `quantite_reelle` float DEFAULT NULL,
  `ecart` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `membre_equipe`
--

CREATE TABLE `membre_equipe` (
  `id` int(11) NOT NULL,
  `equipe_id` int(11) NOT NULL,
  `technicien_id` int(11) DEFAULT NULL,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(100) NOT NULL,
  `telephone` varchar(20) NOT NULL,
  `type_membre` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `mouvement_numero_serie`
--

CREATE TABLE `mouvement_numero_serie` (
  `id` int(11) NOT NULL,
  `numero_serie_id` int(11) NOT NULL,
  `type_transition` enum('AFFECTATION_ZONE','AFFECTATION_TECH','INSTALLATION','RETOUR','REBUT_DESTRUCTION') NOT NULL,
  `ancien_emplacement_id` int(11) DEFAULT NULL,
  `nouvel_emplacement_id` int(11) DEFAULT NULL,
  `ancien_technicien_id` int(11) DEFAULT NULL,
  `nouveau_technicien_id` int(11) DEFAULT NULL,
  `date_mouvement` datetime NOT NULL,
  `utilisateur_id` int(11) NOT NULL,
  `commentaire` text DEFAULT NULL,
  `reference` varchar(100) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `mouvement_stock`
--

CREATE TABLE `mouvement_stock` (
  `id` int(11) NOT NULL,
  `type_mouvement` enum('entree','sortie','inventaire','ajustement','retour') NOT NULL,
  `reference` varchar(100) DEFAULT NULL,
  `date_reference` date DEFAULT NULL,
  `produit_id` int(11) NOT NULL,
  `quantite` float NOT NULL,
  `prix_unitaire` float DEFAULT NULL,
  `montant_total` float DEFAULT NULL,
  `utilisateur_id` int(11) NOT NULL,
  `fournisseur_id` int(11) DEFAULT NULL,
  `emplacement_id` int(11) DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  `date_mouvement` datetime NOT NULL,
  `quantite_reelle` float DEFAULT NULL,
  `ecart` float DEFAULT NULL,
  `workflow_state` varchar(20) NOT NULL,
  `date_approbation` datetime DEFAULT NULL,
  `date_execution` datetime DEFAULT NULL,
  `date_validation` datetime DEFAULT NULL,
  `approuve_par_id` int(11) DEFAULT NULL,
  `motif_rejet` text DEFAULT NULL,
  `anomalies` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`anomalies`)),
  `applique_au_stock` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `note_rh`
--

CREATE TABLE `note_rh` (
  `id` int(11) NOT NULL,
  `titre` varchar(200) NOT NULL,
  `contenu` text NOT NULL,
  `author_id` int(11) NOT NULL,
  `date_creation` datetime NOT NULL,
  `date_publication` datetime DEFAULT NULL,
  `destinataires` varchar(50) DEFAULT NULL,
  `zone_cible` varchar(100) DEFAULT NULL,
  `service_cible` varchar(50) DEFAULT NULL,
  `actif` tinyint(1) DEFAULT NULL,
  `date_archivage` datetime DEFAULT NULL,
  `updated_at` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `notification_sms`
--

CREATE TABLE `notification_sms` (
  `id` int(11) NOT NULL,
  `technicien_id` int(11) NOT NULL,
  `demande_id` int(11) DEFAULT NULL,
  `message` text NOT NULL,
  `type_notification` varchar(20) NOT NULL,
  `envoye` tinyint(1) DEFAULT NULL,
  `date_creation` datetime DEFAULT NULL,
  `date_envoi` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `numero_serie`
--

CREATE TABLE `numero_serie` (
  `id` int(11) NOT NULL,
  `numero` varchar(100) NOT NULL,
  `produit_id` int(11) NOT NULL,
  `statut` enum('EN_MAGASIN','ALLOUE_ZONE','ALLOUE_TECHNICIEN','INSTALLEE','RETOURNEE','REBUT') NOT NULL,
  `date_entree` datetime NOT NULL,
  `emplacement_id` int(11) DEFAULT NULL,
  `zone_id` int(11) DEFAULT NULL,
  `technicien_id` int(11) DEFAULT NULL,
  `date_affectation_tech` datetime DEFAULT NULL,
  `date_installation` datetime DEFAULT NULL,
  `adresse_client` varchar(255) DEFAULT NULL,
  `numero_ligne_sonatel` varchar(50) DEFAULT NULL,
  `client_id` int(11) DEFAULT NULL,
  `date_retour` datetime DEFAULT NULL,
  `motif_retour` varchar(255) DEFAULT NULL,
  `dossier_sav_id` int(11) DEFAULT NULL,
  `date_destruction` datetime DEFAULT NULL,
  `motif_destruction` varchar(255) DEFAULT NULL,
  `cree_par_id` int(11) NOT NULL,
  `date_creation` datetime NOT NULL,
  `modifie_par_id` int(11) DEFAULT NULL,
  `date_modification` datetime DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `produits`
--

CREATE TABLE `produits` (
  `id` int(11) NOT NULL,
  `reference` varchar(100) NOT NULL,
  `code_barres` varchar(100) DEFAULT NULL,
  `nom` varchar(200) NOT NULL,
  `description` text DEFAULT NULL,
  `categorie_id` int(11) DEFAULT NULL,
  `emplacement_id` int(11) DEFAULT NULL,
  `fournisseur_id` int(11) DEFAULT NULL,
  `prix_achat` decimal(10,2) DEFAULT NULL,
  `prix_vente` decimal(10,2) DEFAULT NULL,
  `tva` decimal(5,2) DEFAULT NULL,
  `unite_mesure` varchar(20) DEFAULT NULL,
  `stock_min` int(11) DEFAULT NULL,
  `stock_max` int(11) DEFAULT NULL,
  `actif` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `reservation_piece`
--

CREATE TABLE `reservation_piece` (
  `id` int(11) NOT NULL,
  `intervention_id` int(11) NOT NULL,
  `produit_id` int(11) NOT NULL,
  `quantite` float NOT NULL,
  `statut` varchar(20) NOT NULL,
  `statut_technicien` varchar(20) NOT NULL,
  `commentaire` text DEFAULT NULL,
  `utilisateur_id` int(11) NOT NULL,
  `date_creation` datetime NOT NULL,
  `date_maj` datetime DEFAULT NULL,
  `date_validation` datetime DEFAULT NULL,
  `date_annulation` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `survey`
--

CREATE TABLE `survey` (
  `id` int(11) NOT NULL,
  `date_survey` date NOT NULL,
  `nom_raison_sociale` varchar(255) NOT NULL,
  `contact` varchar(100) NOT NULL,
  `represente_par` varchar(100) DEFAULT NULL,
  `tel1` varchar(20) NOT NULL,
  `tel2` varchar(20) DEFAULT NULL,
  `adresse_demande` varchar(255) NOT NULL,
  `etage` varchar(20) DEFAULT NULL,
  `gps_lat` varchar(50) DEFAULT NULL,
  `gps_long` varchar(50) DEFAULT NULL,
  `h_debut` varchar(20) DEFAULT NULL,
  `h_fin` varchar(20) DEFAULT NULL,
  `n_ligne` varchar(50) DEFAULT NULL,
  `n_demande` varchar(50) NOT NULL,
  `service_demande` varchar(50) NOT NULL,
  `etat_client` varchar(50) DEFAULT NULL,
  `nature_local` varchar(50) DEFAULT NULL,
  `type_logement` varchar(50) DEFAULT NULL,
  `fibre_dispo` tinyint(1) DEFAULT NULL,
  `cuivre_dispo` tinyint(1) DEFAULT NULL,
  `gpon_olt` varchar(50) DEFAULT NULL,
  `splitter` varchar(50) DEFAULT NULL,
  `distance_fibre` int(11) DEFAULT NULL,
  `etat_fibre` varchar(20) DEFAULT NULL,
  `sr` varchar(50) DEFAULT NULL,
  `pc` varchar(50) DEFAULT NULL,
  `distance_cuivre` int(11) DEFAULT NULL,
  `etat_cuivre` varchar(20) DEFAULT NULL,
  `modem` tinyint(1) DEFAULT NULL,
  `ont` tinyint(1) DEFAULT NULL,
  `nb_prises` int(11) DEFAULT NULL,
  `quantite_cable` int(11) DEFAULT NULL,
  `observation_tech` text DEFAULT NULL,
  `observation_client` text DEFAULT NULL,
  `conclusion` varchar(50) NOT NULL,
  `photos` text DEFAULT NULL,
  `technicien_structure` varchar(100) DEFAULT NULL,
  `backoffice_structure` varchar(100) DEFAULT NULL,
  `offre` varchar(100) DEFAULT NULL,
  `debit` varchar(50) DEFAULT NULL,
  `type_mi` tinyint(1) DEFAULT NULL,
  `type_na` tinyint(1) DEFAULT NULL,
  `type_transfer` tinyint(1) DEFAULT NULL,
  `type_autre` tinyint(1) DEFAULT NULL,
  `nro` varchar(50) DEFAULT NULL,
  `type_reseau` varchar(50) DEFAULT NULL,
  `plaque` varchar(50) DEFAULT NULL,
  `bpi` varchar(50) DEFAULT NULL,
  `pbo` varchar(50) DEFAULT NULL,
  `coupleur` varchar(50) DEFAULT NULL,
  `fibre` varchar(50) DEFAULT NULL,
  `nb_clients` int(11) DEFAULT NULL,
  `valeur_pbo_dbm` varchar(20) DEFAULT NULL,
  `bpi_b1` varchar(50) DEFAULT NULL,
  `pbo_b1` varchar(50) DEFAULT NULL,
  `coupleur_b1` varchar(50) DEFAULT NULL,
  `nb_clients_b1` int(11) DEFAULT NULL,
  `valeur_pbo_dbm_b1` varchar(20) DEFAULT NULL,
  `description_logement_avec_bpi` text DEFAULT NULL,
  `description_logement_sans_bpi` text DEFAULT NULL,
  `emplacement_pto` varchar(100) DEFAULT NULL,
  `passage_cable` text DEFAULT NULL,
  `longueur_tirage_pbo_bti` varchar(50) DEFAULT NULL,
  `longueur_tirage_bti_pto` varchar(50) DEFAULT NULL,
  `materiel_existant_decodeur_carte` tinyint(1) DEFAULT NULL,
  `materiel_existant_wifi_extender` tinyint(1) DEFAULT NULL,
  `materiel_existant_fax` tinyint(1) DEFAULT NULL,
  `materiel_existant_videosurveillance` tinyint(1) DEFAULT NULL,
  `qualite_ligne_adsl_defaut_couverture` tinyint(1) DEFAULT NULL,
  `qualite_ligne_adsl_lenteurs` tinyint(1) DEFAULT NULL,
  `qualite_ligne_adsl_deconnexions` tinyint(1) DEFAULT NULL,
  `qualite_ligne_adsl_ras` tinyint(1) DEFAULT NULL,
  `niveau_wifi_salon` varchar(20) DEFAULT NULL,
  `niveau_wifi_chambre1` varchar(20) DEFAULT NULL,
  `niveau_wifi_bureau1` varchar(20) DEFAULT NULL,
  `niveau_wifi_autres_pieces` varchar(20) DEFAULT NULL,
  `choix_bf_hall` tinyint(1) DEFAULT NULL,
  `choix_bf_chambre2` tinyint(1) DEFAULT NULL,
  `choix_bf_bureau2` tinyint(1) DEFAULT NULL,
  `choix_bf_mesure_dbm` varchar(20) DEFAULT NULL,
  `cuisine_chambre3` tinyint(1) DEFAULT NULL,
  `cuisine_bureau3` tinyint(1) DEFAULT NULL,
  `cuisine_mesure_dbm` varchar(20) DEFAULT NULL,
  `repeteur_wifi_oui` tinyint(1) DEFAULT NULL,
  `repeteur_wifi_non` tinyint(1) DEFAULT NULL,
  `repeteur_wifi_quantite` int(11) DEFAULT NULL,
  `repeteur_wifi_emplacement` varchar(100) DEFAULT NULL,
  `cpl_oui` tinyint(1) DEFAULT NULL,
  `cpl_non` tinyint(1) DEFAULT NULL,
  `cpl_quantite` int(11) DEFAULT NULL,
  `cpl_emplacement` varchar(100) DEFAULT NULL,
  `cable_local_type` varchar(50) DEFAULT NULL,
  `cable_local_longueur` varchar(20) DEFAULT NULL,
  `cable_local_connecteurs` varchar(50) DEFAULT NULL,
  `goulottes_oui` tinyint(1) DEFAULT NULL,
  `goulottes_non` tinyint(1) DEFAULT NULL,
  `goulottes_quantite` int(11) DEFAULT NULL,
  `goulottes_nombre_x2m` int(11) DEFAULT NULL,
  `survey_ok` tinyint(1) DEFAULT NULL,
  `survey_nok` tinyint(1) DEFAULT NULL,
  `motif` text DEFAULT NULL,
  `commentaires` text DEFAULT NULL,
  `signature_equipe` text DEFAULT NULL,
  `signature_client` text DEFAULT NULL,
  `client_tres_satisfait` tinyint(1) DEFAULT NULL,
  `client_satisfait` tinyint(1) DEFAULT NULL,
  `client_pas_satisfait` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `intervention_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `token_blacklist`
--

CREATE TABLE `token_blacklist` (
  `id` int(11) NOT NULL,
  `jti` varchar(36) NOT NULL,
  `token_type` varchar(10) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `blacklisted_on` datetime NOT NULL,
  `revoke_reason` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `user`
--

CREATE TABLE `user` (
  `id` int(11) NOT NULL,
  `username` varchar(64) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password_hash` varchar(256) NOT NULL,
  `role` varchar(20) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(100) NOT NULL,
  `telephone` varchar(20) NOT NULL,
  `zone` varchar(50) DEFAULT NULL,
  `commune` varchar(50) DEFAULT NULL,
  `quartier` varchar(50) DEFAULT NULL,
  `service` varchar(20) DEFAULT NULL,
  `technologies` varchar(100) DEFAULT NULL,
  `actif` tinyint(1) DEFAULT NULL,
  `date_creation` datetime DEFAULT NULL,
  `zone_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `user`
--

INSERT INTO `user` (`id`, `username`, `email`, `password_hash`, `role`, `nom`, `prenom`, `telephone`, `zone`, `commune`, `quartier`, `service`, `technologies`, `actif`, `date_creation`, `zone_id`) VALUES
(1, 'admin', 'admin@sofatelcom.sn', 'scrypt:32768:8:1$bUSJ25HPWuS7p77j$e1bb818751d98f9d65c238dad44e87cfb672c7fc99c48dde1cf9ed248c92a32c38cf17f36c8e55891135bf61815102ed045683b30a88f54bacf1f8cd7c0c307f', 'chef_pur', 'Administrateur', 'System', '221000000000', NULL, NULL, NULL, NULL, NULL, 1, '2025-08-18 11:15:40', NULL),
(8, 'jmndione', 'jmndione@gmail.com', 'scrypt:32768:8:1$zxdY5Hx186VWjuPJ$3e02180bd75266d36b878fafbe2e6a1e419729698fd114ec2bda0899cd562788857a9b2f3440ca61fb1f73b3c37ad49ef3358c6d11c03b19c43aec6a7e609cf4', 'chef_zone', 'NDIONE', 'Jean Marie', '+221774236661', 'Dakar', NULL, NULL, 'SAV', NULL, 1, '2025-08-19 14:32:11', 3),
(9, 'ousmanendong', 'ousmane.ndong@sofatelcom.com', 'scrypt:32768:8:1$RLONdjZwdzngCHON$305d58d480a005477e1b27f26d0e583425ced057109cc9f9f1de7f3331f04079b076003392ff01adf50676675152d99fe8c08c373c8be3bb876a876216a0e841', 'chef_pilote', 'NDONG', 'OUSMANE', '771780101', NULL, NULL, NULL, 'SAV', NULL, 1, '2025-08-19 14:40:43', NULL),
(10, 'assanendiaye', 'assane.ndiaye@sofatelcom.com', 'scrypt:32768:8:1$lgsDjsz58C7lukCt$58939b7dc1ea51d9db1d0e790d479605653d796c9e728612401d72d4d05753fd4cdf1c80a121dca3033bf81c94788ad09c402adec9e452fb6c3f4342ceb37ac2', 'chef_pilote', 'Ndiaye', 'Assane', '772489052', NULL, NULL, NULL, 'Production', NULL, 1, '2025-08-19 15:18:23', NULL),
(11, 'massarfall', 'boubacarmassar.fall@sofatelcom.com', 'scrypt:32768:8:1$2SkN3jzKi8Hkf3DZ$da2d8fdba7c5d89b371d9cf3d59699cd4bd190bb3e0d6cd32295fde4c7edb2e4b6505b1f3f476a682dea469f8fd6d43df872bcaefe407470eb73cbebb6293fba', 'chef_zone', 'FALL', 'MASSAR', '772185597', 'Dakar', NULL, NULL, NULL, NULL, 1, '2025-08-19 15:31:19', NULL),
(12, 'issasow', 'issa.sow@sofatelcom.com', 'scrypt:32768:8:1$BuktlGPD19Yd244Z$b27ef138ffa9a4ffe9de39ea95a3dede30f9b311d982060d4fd5fabd8c62a8ca2a59b602c6b2ec936e73cc3b481157b489ad14694812876029879d127eaa0193', 'chef_pilote', 'SOW', 'ISSA', '778164601', NULL, NULL, NULL, 'SAV', NULL, 1, '2025-08-19 15:45:56', NULL),
(13, 'khadimdiop', 'khadim.diop@sofatelcom.com', 'scrypt:32768:8:1$HNWdsgVmtvDImGUS$d29361839a1d2c20925b5ddcf5e53602884aeb6b3a4d77179ad7228951f20cfd97a990202762ddec146f3eab04abc69a3090a2926c0b008dd7124d4761abd00f', 'chef_pilote', 'DIOP', 'Khadim', '775096923', NULL, NULL, NULL, 'Production', NULL, 1, '2025-08-19 15:49:59', NULL),
(16, 'serignembackendiaye', 'serignembacke.ndiaye@sofatelcom.com', 'scrypt:32768:8:1$BNQsBuMMA0e9jP6s$ac22516a21216e2f21946c07dbc90a08d79d0bda3bc0bd4dc828f7b7bf1accc7f6a0d9ac059061a4b15e3305b9f7a569352903298662918a4ef603ace02fb9b3', 'technicien', 'Ndiaye', 'Serigne Mbacke', '775993631', 'Dakar', NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2025-08-20 09:39:21', 1),
(17, 'moussagueye', 'moussa.gueye@sofatelcom.com', 'scrypt:32768:8:1$lFOaesUXA2GsZird$b7bbba018c3b29fd82208c3eedfe77f74108816e29d53903f4a8d8a85d1bd8a53e8fb2bf4cc94878fd9e5053b16618550d04e6484d6af2a6beac806120c276c9', 'chef_pur', 'GUEYE', 'MOUSSA', '776395567', NULL, NULL, NULL, NULL, NULL, 1, '2025-08-20 13:26:29', NULL),
(18, 'youssouphasonko', 'youssoupha.sonko@sofatelcom.com', 'scrypt:32768:8:1$C5jKIwEj1nDyxTwQ$1a0bf5d364e8261ee6f14196d0735c71674a48e36a55e82384bc57df4abb9209459bc7d1507dd4365c526aa18e85602b426cd5050cd75cefff795fca61078a43', 'chef_pur', 'SONKO', 'YOUSSOUPHA', '783022525', NULL, NULL, NULL, NULL, NULL, 1, '2025-08-20 13:27:28', NULL),
(21, 'wagane', 'papewagane.faye@sofatelcom.com', 'scrypt:32768:8:1$0x78SaLqRzXXBcdB$3aa2f4d18e62bd17e92645944ef0561035d76f054b1faa595c99907b61e5772a621056720a0f0d092ca991ca90347f9eda5c8502b9daca060be21c6aa460e0d1', 'chef_pur', 'FAYE', 'Pape Wagane', '+221772484361', NULL, NULL, NULL, NULL, NULL, 1, '2025-08-21 15:48:18', NULL),
(22, 'saratafaye', 'sarata.faye@sofatelcom.com', 'scrypt:32768:8:1$8BKXTe1xnuArVG5p$851c4d172aa461b983ea9b244d0ed860ab3061806f8bfc5455673cd1523ce4a23c5d5bae7e746d97a5a3c3041a836d05cf720ee057bcc17f26c541cbdc5c3738', 'chef_pilote', 'FAYE', 'SARATA', '775269188', NULL, NULL, NULL, 'SAV', NULL, 1, '2025-08-26 14:37:04', NULL),
(23, 'thiabengom', 'thiabe.ngom@sofatelcom.com', 'scrypt:32768:8:1$s1n36ety88ayQyVf$5f0f6de0c6c11509c5069dd56b94f06f4ee885c443910bc88766da205c782c2d0a546a027774fc5eaf4b1d3139faf6f56b66feae7d8dc339468bc9dc8aa01931', 'chef_pilote', 'Ngom', 'Thiabe', '771058355', NULL, NULL, NULL, 'SAV', NULL, 1, '2025-08-26 14:40:27', NULL),
(24, 'mamadouthiaw', 'mamadou.thiaw@sofatelcom.com', 'scrypt:32768:8:1$92lmltB1tdKMMNCR$024ae688cb95a43b4ce0311d19a851d79ed5ec614879f67735b58ddfeebaad1e4e1e0474103642a824b1f249b607c12fcbc7a7153165c012bf4e197548cf9997', 'chef_pur', 'THIAW', 'MAMADOU', '771054483', NULL, NULL, NULL, NULL, NULL, 1, '2025-08-26 15:11:00', NULL),
(25, 'badaragueye', 'badara.gueye@sofatelcom.com', 'scrypt:32768:8:1$NavG5CgI4aqFAcCC$e28eeb1d35dd6d4e1ba59170a44d4465b1472afac5b37a0d841ff5f21848eae6836a8f3cde401ee15afa167fa49a0c36bda8f8b35aaea02d4f2324c0e2d05e82', 'technicien', 'GUEYE', 'BADARA', '771059304', 'Dakar', NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2025-08-26 15:13:47', NULL),
(26, 'BALLA SONKO', 'balla.sonko@sofatelcom.com', 'scrypt:32768:8:1$SohHiLDjZPkhLPJi$2e9a1b9f537a36ef113b38f14c8bf6f943db8fb1c1884a2b856b826b9ffe60df532751689cf45251867fd820d2f732eea0e73332b7519c9da5507e7eca2e05d6', 'technicien', 'SONKO', 'BALLA', '772484485', 'Dakar', NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2025-08-26 15:15:28', 1),
(27, 'serignefalloudiagne', 'serignefallou.diagne@sofatelcom.com', 'scrypt:32768:8:1$occ84CdjHvNGojYd$2089958a24b89c5f4eddf499df05bf2471ad5bc7afe53b4a581dc2ac1201133ac952c59c69851e2932d58813dff1ebe2a710e46e2d30e70bc83cdc31da344df4', 'chef_pur', 'DIAGNE', 'SERIGNE FALLOU', '771800368', NULL, NULL, NULL, NULL, NULL, 1, '2025-09-04 14:27:06', NULL),
(28, 'ABABCAR LATYR SARR', 'ababacarlatyrsarr8@gmail.com', 'scrypt:32768:8:1$CO3vs7DAF0DAMrsr$56b8bc62a8f44e34478b01046916f32e2d3c0cfd89ca43d7eb5cb3cad4dceb721842b1d5a58818e6722e3d00b586bd92124a84b2f83406fcf465d71e2a55c8d8', 'technicien', 'SARR', 'ABABCAR LATYR', '783846067', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:02:24', NULL),
(29, 'ABABCAR NABY SYLLA', 'aboubacarnaby.sylla@unchk.edu.sn', 'scrypt:32768:8:1$lRqXYFEWSybMYd74$32b7efbd140705c36f4bd2e2efddb7c5594c7de24e2fed1b29ec0f0ce5f8547e93842f586c216a5eb63edfb2fb1ed49b86c7358fe07ac9a81b14e41f6e60788c', 'technicien', 'SYLLA', 'ABABCAR NABY', '788683515', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:04:53', NULL),
(30, 'ABDOULAYE SAMBA DIOP', 'diopabdoulayesamba630@gmail.com', 'scrypt:32768:8:1$n1eNgbO4I9rSIvSx$9ce80733daae735112a4214d18f25af33f4995137dde0d2049031b9b92f3359bb5c7c854e18a178aa155d782eb0287ff98e0c8036e667dee9946f0a9d57ec493', 'technicien', 'DIOP', 'ABDOULAYE SAMBA', '+221784816942', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:06:42', NULL),
(32, 'AHMADOU BAMBA BA', 'bambabamessi@gmail.com', 'scrypt:32768:8:1$tabcSTPDokg8fFCM$0d3ba94e6ead897fbf9079bd084c5da08b2092aec7afa556dad5a4c04780737b352ae3c041e2aa80f01827e3f9c99a8764b199d1c14b6918c4f3673540b5fe47', 'technicien', 'BA', 'AHMADOU BAMBA', '+221784582890', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:10:29', NULL),
(33, 'AHMADOU BAMBA NDIAYE', 'ahmadoubamban50@gmail.com', 'scrypt:32768:8:1$T2HARIROdzyVwCAm$9d7788389d2b71d71054dcedcbb20363826d6cfda4bca6ace9ee940c93710a1af7e3bfbab5cdad8e4952d6b4595f821d723c7c2fe75c28d29a916b2ee5e0b43f', 'technicien', 'NDIAYE', 'AHMADOU BAMBA', '771605820', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:12:23', NULL),
(34, 'ALBOURY NDIAYE', 'nalboury988@gmail.com', 'scrypt:32768:8:1$u7SqPoQJY3RL2RWY$6e4d74f130f0dbd07a49583e3f0f1d388a33a38898af6dc0c154a9a84630b16e85eb05b08836e551317eba231382e5b0769fe78624bef559635c2b41a9f5f314', 'technicien', 'NDIAYE', 'ALBOURY', '+221773781558', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:13:33', NULL),
(35, 'ALE BOYE', 'aleboye1@gmail.com', 'scrypt:32768:8:1$gGEW5lsp1GxrYf7i$a004dbb7b7322202dcdfc84e2c153555006fa5aebd0ca2dc4742cacfb6727a85c2a84b27bafb1c76f0ed80619686ff7388ff42b12ff1ca8d72574c3f8ab59c1f', 'technicien', 'BOYE', 'ALE', '+221781544237', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:14:49', NULL),
(37, 'BABACAR GUEYE', 'suivieconso@gmail.com', 'scrypt:32768:8:1$v7CptCs9j6ip7slf$3beb77545f0f80230231e52569747ce381f381d77d54d633ac751aeb560fed65aa305150126b300f61cf1211042139d811910696d8b71b724160336060cbd82d', 'technicien', 'GUEYE', 'BABACAR', '+221772789834', 'Dakar', NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2025-10-08 11:17:36', 1),
(38, 'BOUNA SALL', 'bounasall347@gmail.com', 'scrypt:32768:8:1$MnRJXFNTnKYYUMGu$e268f6dbe87565c95b5cddaec6f168254c28bfcef48a0661a4b812eb6a730d7bacc7819a84e9cf4533adb7448162cdbbc260a96ae95e315e3429e71237117ff0', 'technicien', 'SALL', 'BOUNA', '+221782395544', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:19:24', NULL),
(39, 'CESAR MENDY', 'roicesarito2@gmail.com', 'scrypt:32768:8:1$8OrqtEqOxss5Epf7$4e3800bf05e906a5fc8a606fb15bee05b2c6e92fad56ad311f7dacc1b388e4fd2a56bac78dcc6006bc71ea0c68ab92bc0199e485c98c2b61967ca1091b39cf22', 'technicien', 'MENDY', 'CESAR', '+221772238075', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:20:47', NULL),
(40, 'DJIBY NDIAYE ', 'seydouna93@gmail.com', 'scrypt:32768:8:1$yhNI4bqUdJ4au3xm$a8506be827aed47febec8f484a6c430047d59419b871598bb8945d8ca9953075e67bea58acf347b16b95d408804c7d82f5b639c9ff42344c3d6c478c96b863b9', 'technicien', 'NDIAYE', 'DJIBY', '750121336', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:22:20', NULL),
(41, 'EL HADJI IBRAHIMA SEYE ', 'elhadjiibrahima98@gmail.com', 'scrypt:32768:8:1$fjx5azvxqAY00Rfy$84a965835a739b1897217d9a61e29289eeea371ac58b1325193a859763483e6c79e54ef1a9110502888a969f304d3c3085a68b5190fcb48a84349de8dd3ee55b', 'technicien', 'SEYE', 'EL HADJI IBRAHIMA', '776972803', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:24:15', NULL),
(42, 'EL HADJI MAMADOU SAVANE', 'savanee07@gmail.com', 'scrypt:32768:8:1$NqtGlTa9RIq352gy$7aa1009e05a301a494f79434efdf29f3992620dcb8cb55f038464df7aef39bcf817b3013dece3ef6ede3abc5a52cd3c097708f1262ef93f4d16406ae45ebe020', 'technicien', 'SAVANE', 'EL HADJI MAMADOU', '775926988', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:25:27', NULL),
(43, 'GORA GUEYE', 'gorakaddu999@gmail.com', 'scrypt:32768:8:1$5gWejZTxfgIIU3Ix$eeb90403b897d46db5b0721a2fdd9b665a97744d3474fad39267b284fa4a3ec0332cc5dc3790f6c4b30a0e19988533134fe012d9efd89d54f6d290ecf4cb8733', 'technicien', 'GUEYE', 'GORA', '+221771815530', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:26:57', NULL),
(44, 'IBRAHIMA ABDALAH DIALLO', 'lloyd.banks.abdallah@gmail.com', 'scrypt:32768:8:1$mZQwDtTkR10lUKaC$5861f9073a6ac8937fdacd80aa0ac47071f92060ff4d8d750f4c6f82b2e281ddf824f4c4abadd859a028e28f193b23a5426030863d7842f98b4348b9d2e1123f', 'technicien', 'DIALLO', 'IBRAHIMA ABDALAH', '+221777268691', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:28:30', NULL),
(45, 'IBRAHIMA MARONE', 'maroneibrahima288@gmail.com', 'scrypt:32768:8:1$4F9ppE8iO0FD7dA5$5531293bcb70504e5294139e0a84ac32d4a663d7b3b5e5cd24ff7826879766cba45c6e763b011a311788ea2a7b93b253ab5f96cb687c6114612f87e25e1579d1', 'technicien', 'MARONE', 'IBRAHIMA', '+221784621983', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:29:37', NULL),
(46, 'KHADIM DIOP', 'diopkhadim682@gmail.com', 'scrypt:32768:8:1$5O0Mpk1iHV0Dm9Vo$0dcc45203bc1766a61ef249c0fcaaa158507e83f56f334062c4566b7502aa80a4c8895f40aae34ff841ee8d9141e585720231bdacb3f104e6c695dc17deb3b60', 'technicien', 'DIOP', 'KHADIM', '+221774935418', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:30:39', NULL),
(47, 'KHADIM RASSOUL NIANG', 'khadimrniang96@gmail.com', 'scrypt:32768:8:1$hfKdtQDWgYf3gZ01$4b0484c58ccbe773faeb93498efba78de4ae96ec1750884d77fd7257decd8584ec3ba86b1a17c17d1a3eaa26abe075267de5ba8c96a68ca0aaa6f0155ee7c555', 'technicien', 'NIANG', 'KHADIM RASSOUL', '+221779514430', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:31:43', NULL),
(48, 'KHALIDOU IBRAHIMA TOURE', 'ibrahimatoure511@gmail.com', 'scrypt:32768:8:1$KuMTKP08q8sXfOH2$3f396f32f3f6804ced0c8d08f67d35a4af9d074a8d686741598ce12c1f4b00b1a5e89237ca2776ebbe70debb53504abf3f649f6552b376e776c9940f2f3d580a', 'technicien', 'TOURE', 'KHALIDOU IBRAHIMA', '+221770867461', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:32:38', NULL),
(49, 'LAMINE DIABANG ', 'diabanglamine31@gmail.com', 'scrypt:32768:8:1$UFWQonbg0ltUNbE5$d2916e353064a555c623de400cee1054480dec36eabcc9b81ca619c58ba37721529376e885f81241dd393b77889a455557b21e6c417e0d837a0aa223a5c2ae77', 'technicien', 'DIABANG', 'LAMINE', '771059420', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:34:41', NULL),
(50, 'LAMINE DIAFOUNE', 'diafoune95@gmail.com', 'scrypt:32768:8:1$E3XOm2l6iR35eFST$c20380415305946d4b8965de90db9a5c4aa0d56124fbe4cf2dd677bbf67c2e4a1065cedc0fca573bb7b0dba3ea90cded3dbdf53d954478baabad2f726f1165c8', 'technicien', 'DIAFOUNE', 'LAMINE', '+221783558403', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:36:03', NULL),
(52, 'MAMA DIENE FAYE', 'dienemama2016@gmail.com', 'scrypt:32768:8:1$toBQd3wOpsjO82LC$fb8e33e7ca0837b319c8f12b2e5874bec66b77a689c01453e0a12f55aaa957d072a31c9bb69aa4ac0d14a829c354393babd83c683b5bb9fbf569527c341f9581', 'technicien', 'FAYE', 'MAMA DIENE', '+221781131751', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:38:43', NULL),
(56, 'MASSAR SECK', 'amethciss942@gmail.com', 'scrypt:32768:8:1$cosnDBed6aySgeFe$132f25f384cbb0f937edca3e635a467fd196177c2647fb0ec8d16df361e838a4913dcd61ca9359a291a7ba384d67eb73ee16cfec14bc2c3d3c8f14eb1b7d07c8', 'technicien', 'SECK', 'MASSAR', '+221773360633', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:46:41', NULL),
(57, 'MBAYE BABACAR ', 'mbayewally096@gmail.com', 'scrypt:32768:8:1$6Cx3XJ30QbKPQxk6$777d51cb23df33971b09d378545304c79281ea5e806a4e5bd06e384e14e621c94e8632ab01a313ff9a00025598ea929bba1db0cd3aec6d6c1ddaebe0782cbd47', 'technicien', 'MBAYE', 'BABACAR', '+221784177204', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:47:47', NULL),
(58, 'MBAYE NDIONE', 'doondione44@gmail.com', 'scrypt:32768:8:1$DInTlwbhaxeFmdl9$ef85bd10d937987d994a50400cbf417c79c748c0bae0d431df80d9b2fdea0370f8c35538e44d262e2119d6ddae89b49891ec370dc97d5b7172e7e2de266d25d4', 'technicien', 'NDIONE', 'MBAYE', '+221775234363', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:49:04', 4),
(59, 'MOUHAMADOU MBACKE NDIAYE', 'mouhamadn142@gmail.com', 'scrypt:32768:8:1$gVXtrTr7ZmPMs3D9$47997b40a693be3dcf527e30ef727d0133d6cb497ed47342a0797b56912935ac9fb4304ae2a66f5e131b50135425243e1d0cdca001a6993136155debe1813b82', 'technicien', 'NDIAYE', 'MOUHAMADOU MBACKE', '780159768', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:53:37', NULL),
(60, 'MOUCTAR DIALLO', 'diallomouctar31@gmail.com', 'scrypt:32768:8:1$3iQH6I4WImcvm1DH$dde5ec7505905eb0f8c1350d8ad7bcd3a12fd3c8f73f11f13d00d77f5f677223e88d7721b5d939e24270550856b6ab5b515bcfb387a14ea8d10151a5ef1a9034', 'technicien', 'DIALLO', 'MOUCTAR', '+221772410146', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:54:52', NULL),
(61, 'MOUSSA BALAKE FAYE', 'cosflex0@gmail.com', 'scrypt:32768:8:1$gyy2nbX9rjMq5uKA$d0543a29b7a9acbda255a220346d2e1c12254ed1add457c6294550e672215bbb5947e2bec91861967823e4f3b7f937946f4ac9b0f42beeb1059afb92aa86fcb7', 'technicien', 'FAYE', 'MOUSSA BALAKE', '771907700', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:55:56', NULL),
(62, 'MOUSSA CISS', 'papemoussaciss80@gmail.com', 'scrypt:32768:8:1$YBk0ejdf7PqemyFC$afb082a40d7e58fbb3d77e0f783aeab3c81dfa0a7f2fe640606e737a061e97c8502928b86c62f3bbc1d4eebde66e61d817745cd069d0a3b3f9a3c913a934297c', 'technicien', 'CISS', 'MOUSSA', '774639287', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:57:01', NULL),
(63, 'OMAR FALL', 'oumarfall719@gmail.com', 'scrypt:32768:8:1$quovuXa2i7KrQo2o$7ed9e7c7e6f2b7bd064933abbf52ee352f2c0e271c19e3c7c724916892d29056a547d24fb07598ead80555763e9aa34ea3dd99ce5f42b7d3a6ddecce13a92470', 'technicien', 'FALL', 'OMAR', '784786073', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 11:58:21', NULL),
(64, 'OUMAR NIANG', 'pasdemail2@exemple.com', 'scrypt:32768:8:1$fy0sgSzG0sVzv7iG$10949794f8423c5f2bba60facdb93f2de699ca0362710a21579278b300d8d88d381a83b5b141152b216ff7f6e21951714f1c78ebca77cad619662921be38d0ec', 'technicien', 'NIANG', 'OUMAR', '774549253', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 12:00:57', NULL),
(65, 'OUMAR YAYA SALL', 'oumaryaya1991@gmail.com', 'scrypt:32768:8:1$uJ5PTytV24VrNmSJ$b8285b596134c22e24a09ebd894b7c8f73d7cf287318a7eafd0c8373fc571cd8fde67c54770d73938bef78149b7ef2f9e393b9ce44cdc377d11295349286599a', 'technicien', 'SALL', 'OUMAR YAYA', '+221778143684', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 12:02:08', NULL),
(66, 'OUSMANE GUEYE', 'oussapple2002icloud@gmail.com', 'scrypt:32768:8:1$gFSN3lFisbXpbLKU$9e3f87a471d538a793e9a8c724e367126a9204571fdbfee5c38e51fd7fb3e355ea726cf4c86a9f1c0b42446b022cecc4b7f1150197d28698dccf4c48a787cfda', 'technicien', 'GUEYE', 'OUSMANE', '788309133', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 12:03:14', NULL),
(67, 'PAPA ABDOULAYE CISSE', 'palayecisse85@gmail.com', 'scrypt:32768:8:1$mwkh7eKxcHrtWkqN$aba8fb8c662ae77de2c8e6143f7b0829163fc2c9840b65bbbbfa380e7e6ea7e1ca6115cfdd34961cead5065f02b63dc1566731296f4252974e21d92e581059b5', 'technicien', 'CISSE', 'PAPA ABDOULAYE', '772063677', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 12:04:29', NULL),
(68, 'PAPA ALIOUNE CISS', 'papyalioune21@gmail.com', 'scrypt:32768:8:1$v5Kqdsi1wlgB4oEM$1274edf295bbb19dc138204cdb6e5f6d0a7197ad288d2d20dbccabb779fbdb5415b7dd258f503fe2bb768ca3ad8f876bbe53ddd9cbcec9e05a870e748b1b5550', 'technicien', 'CISS', 'PAPA ALIOUNE', '+221774080620', 'Dakar', NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2025-10-08 12:05:45', 4),
(69, 'PAPA NDIOGOU CISSE', 'seticom2023@gmail.com', 'scrypt:32768:8:1$ZOmPBR33KtbL2KfK$946b896e6ccfe376e05c3092a5751cfd625c69d188957608ee0ab0365a064dc70614725ca0b3d556748fca0aa18f22135d9d1f6bb639619ecc28a317ada8e2b1', 'technicien', 'CISSE', 'PAPA NDIOGOU ', '+221784808343', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 12:07:12', NULL),
(70, 'AL KHASSIMOU DIALLO', 'pasdemail3@exemple.com', 'scrypt:32768:8:1$Cnu8m9RIy1sneuSa$4813a0765d7627069e43af8884002b229d38b1f0f56d5411b7161b3d6091097b40aecd2eb2ffe6d8697fea614f2e0114e3deb29d0110706c0f03199fe0d7be75', 'technicien', 'DIALLO', 'AL KHASSIMOU', '+221773472185', 'Dakar', NULL, NULL, NULL, 'Fibre,5G', 1, '2025-10-08 12:09:01', NULL),
(71, 'alassanediallo', 'alassane.diallo@sofatelcom.com', 'pbkdf2:sha256:600000$ZTkFhdYKXv0yqmXG$2178dd53281debc58137113ee16a09804830f5994f735d76eae195aaef43ba48', 'chef_zone', 'DIALLO', 'ALASSANE', '781700055', 'Dakar', NULL, NULL, NULL, NULL, 1, '2025-10-10 08:42:28', 3),
(72, 'SALIOU FAYE', 'SALIOU.FAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$PZeKagKhPWUHsCjp$a261a252c24fafb023fad08c99ed857f2967d92a5e43f9fe9e0b262c696cb7c25b93eec1eb677c0aa4f81bb1ad7bd52a08d84b0c19e7e5f1dcbe58cd724e4eaf', 'technicien', 'FAYE', 'SALIOU ', '770457269', 'Dakar', NULL, NULL, NULL, 'Cuivre', 1, '2025-10-13 09:05:36', 1),
(73, 'BACHIR BALDE', 'bachirbalde60@gmail.com', 'scrypt:32768:8:1$7jt8PCALGav32rjo$158273a7b90beea68dfdfc410e4e52ac955517073d0e58bf1adac407ff821b9d9745736efdaa1f850e7e041aac7e891a513ba558bcbfac50240aae7bb369c9f9', 'technicien', 'BALDE', 'BACHIR', '773581944', 'Dakar', NULL, NULL, NULL, 'Cuivre', 1, '2025-10-13 09:09:50', NULL),
(74, 'ABOU TALL', 'tallabou004@gmail.com', 'scrypt:32768:8:1$AjxXFNNJCdyWhWS2$a194699cc9724cc3629f36cd1bd60fe735a52510ec86c84e809d69cdee4376441a7b821d23b6f1c31d6d14f12b672d68b73b5656a06ebcd1a6f64f58a4354655', 'technicien', 'TALL', 'ABOU', '+221783621070', 'Dakar', NULL, NULL, NULL, 'Cuivre,5G', 1, '2025-10-14 10:18:37', NULL),
(75, 'KHADIM THIAW', 'khadimthiaw0120@gmail.com', 'scrypt:32768:8:1$XwqXAiMo2rfyaY0C$d05b8e078dbc41716a81d6a270db911bd9135baa9ce1030c62c7743f2625b7884ebdee14cc967164fc556c2cf5ea3d05e9b87d8a62a503d4cbc95aa248fe1f92', 'technicien', 'THIAW', 'KHADIM', '786363512', 'Dakar', NULL, NULL, NULL, 'Cuivre,5G', 1, '2025-10-14 10:21:07', NULL),
(76, 'BIRAHIM DIALLO', 'diallo.bira9@gmail.com', 'scrypt:32768:8:1$bGcgzx5XbKD3U4iB$037eeeead741f4ec89dc51f5504fdeb4a7abf6f492a2ada769923827356e420f1ba881aff8d8d42ba5a1c09c25250f9fbc11d8a4f11731afe57923eeac4f22b2', 'technicien', 'DIALLO', 'BIRAHIM', '774395196', 'Dakar', NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2025-10-14 10:22:35', 1),
(471, 'ABDOU AZIZ SANE', 'ABDOUAZIZ.SANE@SOFATELCOM.COM', 'scrypt:32768:8:1$uvKHMSXvYEggx8hx$10fa2ac05809d58b4b73ec75944460da97b9968eccf3725c9a36b418f8104876d7f8bd5d2a9b084aa09dacd70cfc7652e46618d63c53c8039756c58f2cd2c47b', 'technicien', 'SANE', 'ABDOU AZIZ', '776916644', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-02 19:03:30', 3),
(472, 'ABDOU NDIAYE', 'ABDOU.NDIAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$n4fYhQi1JfoIbnT7$294d07c47d26fadee546d569c74c2c614c24972c2f9e6d421889bb30f0ea3059e59be4b18cd485f4c2516cc151e7c9c1da4239e2f8f1717376f3f41475b1a7cf', 'technicien', 'NDIAYE', 'ABDOU', '781299313', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-02 19:07:03', 3),
(473, 'ABDOUL CAMARA', 'ABDOUL.CAMARA@SOFATELCOM.COM', 'scrypt:32768:8:1$cfumFmwhGLDGKDDK$80fd52a7f55d0ab020a956e9d0f82ff476ca972cbf700277160efffa9e62cf04555c25dc5c0f43a4e76e9f0106283e7e1481d97c7b7819008466a4832f33fee1', 'technicien', 'CAMARA', 'ABDOUL', '772363426', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-02 19:09:04', 3),
(474, 'ABDOULAYE TRAORE', 'ABDOULAYE.TRAORE@SOFATELCOM.COM', 'scrypt:32768:8:1$PBfYD8uzYOoieniJ$30fb5b4bbd75a821fb57ee212bb15f6e966bdd21a263ea1f09475c87c10821acc739e150b3999d4e08f41e976ef98e7ce047cea78b0d9a5bd2f08a78263df123', 'technicien', 'TRAORE', 'ABDOULAYE', '775081158', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-02 19:15:03', 2),
(475, 'AHMADOU BA', 'AHMADOU.BA@SOFATELCOM.COM', 'scrypt:32768:8:1$8b7PPEHcqErVOnyC$c88f47dbd09d701a42c4b338f1d71bff5dc62086e6f64f9032e420c8791c4c0800ca7fd2fa225450bf1a0e326d3aa4209c43c8bb847690511122b2207efa932a', 'technicien', 'BA', 'AHMADOU', '770880924', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-02 19:19:30', 1),
(476, 'DANIEL ALIS NDEKI', 'DANIELALIS.NDEKI@SOFATELCOM.COM', 'scrypt:32768:8:1$3keokgp6aOrBoL94$3e5f4990cde9da9ac009794b8ccb542220805f61a6d1e1314413afddf299678d1f276eb0faa1497671799c2d68598bc047006d9f2771937d07b057ddf0fea67d', 'technicien', 'NDEKI', 'DANIEL ALIS', '775785100', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-02 19:50:39', 1),
(477, 'EL HADJI SAGNA', 'ELHADJI.SAGNA@SOFATELCOM.COM', 'scrypt:32768:8:1$bINK6rrlAL5VIxDb$bc476d9f548858f6e2bd3c1ebfe1668d19c35c66be62068941c3e80e049214d58c5e4def6c77cfad3216fc3062c5a00291890eff701f00c721ab9fb08b0716b4', 'technicien', 'SAGNA', ' EL HADJI', '776358234', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-02 19:55:55', 1),
(478, 'IBRAHIMA DIEYE', 'IBRAHIMA.DIEYE@SOFATELCOM.COM', 'scrypt:32768:8:1$FulI0ltuFWx1c4Dn$dc45cd091568dd8cc74c4eb2d40367c9ef92c43c12e56c394f0f46c802e82f2371796ca7ac5d570a6db5143ed369752452e64db198bff5b4970bfc540e2564e3', 'technicien', 'DIEYE', 'IBRAHIMA', '773049697', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-02 20:05:15', 1),
(479, 'MALANG SANE ', 'MALANG.SANE@SOFATELCOM.COM', 'scrypt:32768:8:1$hvxqkmteAGLhPp8d$46aba224c7f39be398f5dd39837e50d248381fee38dc80be9afc567544d0edbe7ae07f112e063043ff29da7321239840d158d7848fd3bc42bdb3088e5570f64b', 'technicien', 'SANE ', 'MALANG', '776369011', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-02 20:07:12', 1),
(480, 'MANDIO MENDY', 'MANDIO.MENDY@SOFATELCOM.COM', 'scrypt:32768:8:1$rbLjvFZuLerGXzLd$ff17f384bd205f01579aa4f558bd08e895c951c8cd0c225317f6eddb4a43a6c382eeb3367f0c23029cf557d66261355e9761bfa6040718b7e5ab26cabbb9db12', 'technicien', 'MENDY', 'MANDIO', '776285465', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-02 20:14:33', 1),
(481, 'MOUSTAPHA DIENG', 'MOUSTAPHA.DIENG@SOFATELCOM.COM', 'scrypt:32768:8:1$MGhjBtK9P4twP3VM$358dbeae80056a24aeff57103be5ffb41eb090941008802143d093e172eefb9153e98c612f2cd02108e75a3af6daf629e8986916ef43b20402fbef4e11bb7c8e', 'technicien', 'DIENG', 'MOUSTAPHA', '783313301', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-02 20:17:49', 1),
(482, 'ibrahimasall', 'ibrahima.sall@sofatelcom.com', 'scrypt:32768:8:1$STXA4HpSF9Rb0Wia$9474133ef5c8079e0cb793157790b65fc185979030d4febf91c033207087fae5f838b2f83b3a1674447f87ad2821c3288ec4f63a60dd2d8524e6e46b1a55424d', 'gestionnaire_stock', 'Sall', 'ibrahima', '776626969', NULL, NULL, NULL, NULL, NULL, 1, '2026-03-03 13:01:23', NULL),
(483, 'bassiroudaoudandiaye', 'bassiroudaouda.ndiaye@sofatelcom.com', 'scrypt:32768:8:1$5MMyvSSgzszobRHy$bbccfd4a6ba067208c0d62d30973819096c2e08478bd92881d8ce1097ab077f33fa8e638a907b6d06213a265505496c616954c71cc2b84dc5e66985dc687fa19', 'gestionnaire_stock', 'Ndiaye', 'Bassirou Daouda', '772483539', NULL, NULL, NULL, NULL, NULL, 1, '2026-03-03 13:05:40', NULL),
(484, 'AMADOU SYLLA', 'AMADOU.SYLLA@SOFATELCOM.COM', 'scrypt:32768:8:1$ixXE2hfuTTaGQVa7$d9744e56651d8fe4b9abe1951e232c09a7a12b7b8a64a7facaf125cc729f66e95bf59e7ad84acf23fce0ba936719f1eff519eff877b5dfac5c566e788b7d0dc0', 'technicien', 'SYLLA', 'AMADOU', '779302522', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:11:43', 1),
(485, 'AMADOU TIDIANE DIALLO', 'AMADOUTIDIANE.DIALLO@SOFATELCOM.COM', 'scrypt:32768:8:1$GO5Ca2Kt6kez5SKy$82714831a880a96a69413ba579e54a458e5d61d48a1b1590b0ad1718b978aa91c91e23d4de398bbc574a098e96dc84463e46c71c9125943c80f45da59560c00e', 'technicien', 'DIALLO', 'AMADOU TIDIANE', '778960554', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:19:08', 4),
(486, 'AMADOU SADIO DIAGNE', 'AMADOUSADIO.DIAGNE@SOFATELCOM.COM', 'scrypt:32768:8:1$2pR7rV6QpeBsHIJh$824eb828e09d65c39fa9b1306e92e46a0d636f60287fcd95f959dc1b02d03a436ebd4f4beb1b00cfefbe2b172a6bd52f36458de91c7259879856ac86c06cc16a', 'technicien', 'DIAGNE', 'AMADOU SADIO', '773740760', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:21:07', 4),
(487, 'ALIOUNE NDIAYE', 'ALIOUNE.NDIAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$ADY4wmt2aE7rtvfs$544623bd8bf5005fdd08325b4ffd159c605b30cb8309cca4e7020a9637e102dad2e952008b67089a0cc1ca5cf006f3309849a96f6b78762305b843b5aead4756', 'technicien', 'NDIAYE', 'ALIOUNE', '781219053', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:22:25', 4),
(488, 'AMATH BA', 'AMATH.BA@SOFATELCOM.COM', 'scrypt:32768:8:1$ltABwrZiqMpFO2FK$7eb1776e20ee3f906f9ff45690e4324befbf6cd8f56e808a051695344e533eb692c65e218add82d81f9b73d589476a8aa5e44d7c39f024db35be8b7d711c51a6', 'technicien', 'BA', 'AMATH', '777908448', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:23:57', 4),
(489, 'ASSANE NDOUR', 'ASSANE.NDOUR@SOFATELCOM.COM', 'scrypt:32768:8:1$jya0jnuM7Duh9yHY$7e77fd9f5859c1984b341617e523af189fd175a45ad42999d1e2908d17f615067b3705a290dceef36a310f73cf8f5b82d5eb2696f79183f1aa09e3d84da10e8d', 'technicien', 'NDOUR', 'ASSANE', '774263048', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:26:25', NULL),
(490, 'BIRAME MANE', 'BIRAME.MANE@SOFATELCOM.COM', 'scrypt:32768:8:1$yCmFzcZq8dYfXtJu$d2a501db2c5efdf2c6a58ca2e4e312cab8dce505ef0d477f090e5751e161ac7dc6c477c920526c9887a9bb4db692dcc4001bbfab036b0628437bbd19657d3ed3', 'technicien', 'MANE', 'BIRAME', '775140775', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:28:35', 4),
(491, 'CHEIKH BECAYE NDIAYE', 'CHEIKHBECAYE.NDIAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$lBAMRrkkLBpHhFhU$510ad59620a2c42e8a2eaad0b84ff130057f18e02f48c247dcca1196ff309e121f79e94384d659a7f0d32e5312e84c85fd113835692d57a9938c15198862bd9e', 'technicien', 'NDIAYE', 'CHEIKH BECAYE', '773838190', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:35:13', 4),
(492, 'CHEIKH BOUNAMA DIOP', 'CHEIKHBOUNAMA.DIOP@SOFATELCOM.COM', 'scrypt:32768:8:1$ElRjN2Kl0n3v83Te$20fdc93fb9b8c62f8e86483c787d1bff351501e50f4b1cefbfe32364ba1ece599286614a6af49e208208d20c9ee794ee84475d21d44cf14b5d11bb153e8f2e41', 'technicien', 'DIOP', 'CHEIKH BOUNAMA', '778797455', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:37:13', 4),
(493, 'CHEIKH DRAME', 'CHEIKHDRAME@SOFATELCOM.COM', 'scrypt:32768:8:1$h9SaKjxj6WEGe5WE$b5684e71a70072abc072fda0a9ab692f20604c3b4a27ce2f824994e23b4eb28a1a106a0193401d10c4b3a25841ca4d89a04eb3bab00cc63617f11596b683ec8a', 'technicien', 'DRAME', 'CHEIKH', '774012288', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:39:04', 4),
(494, 'CHEIKH GAYE', 'CHEIKH.GAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$nP2foTqaxwc01wWu$1916cd702b15e77382052b0dd614ce471cb0201e174fcc712b66859681d4f31c21ef461f14365420c4f53459a17dee4cead899b44436d9e79dcdd379b47b4f42', 'technicien', 'GAYE', 'CHEIKH', '777944579', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:40:45', 4),
(495, 'CHEIKH SAVANE', 'CHEIKH.SAVANE@SOFATELCOM.COM', 'scrypt:32768:8:1$WCvJeD0CknDP1KDq$6a46bdb13592422e7fd981c5739a0b4ace37910fef52f34b74beafd85ba08252b7cb4157ff0c69ddfe0ca7e5fb40eef04eff1fbde62f5406d458faa9702958d8', 'technicien', 'SAVANE', 'CHEIKH ', '778797455', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:42:14', 4),
(496, 'FALLOU NGOM', 'FALLOU.NGOM@SOFATELCOM.COM', 'scrypt:32768:8:1$MLa3s83Kql8crV54$14c74c0c0cc01cc7c00dc923d1e11f73fb89db353ca902e5831ce9656e842243cd99d0e3219d15f29d2feb77cc0cd0370c3ca3cd3fff438552ee57204864d985', 'technicien', 'NGOM', 'FALLOU', '778089579', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:43:34', 4),
(497, 'IDRISSA THIAM', 'IDRISSA.THIAM@SOFATELCOM.COM', 'scrypt:32768:8:1$mqvBoPbqqWTNV650$e9c198660deb5c05a2db5a0108ad0f5d5e5ff23953f4c8afa1f9adcf5e02e838c84c6118f8c38c8c795d4a57b3bdb6e82c2cde4b77ee46d84e27dae812d359fe', 'technicien', 'THIAM', 'IDRISSA', '784540664', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:46:29', 4),
(498, 'KOLE TOURE', 'KOLE.TOURE@SOFATELCOM.COM', 'scrypt:32768:8:1$08x38DUhh8ayPSeq$614521dbfb633ef7f6dd424a4329c29e295320f605f36c1f4da9906647e9308f4c344c50ca3f2bea53772f2a1d6667d5dda066ee3d1ad2aed3f35c66b30359dc', 'technicien', 'TOURE', 'KOLE', '776886479', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:47:45', 4),
(499, 'LAMINE SOW', 'LAMINE.SOW@SOFATELCOM.COM', 'scrypt:32768:8:1$QrkNCTUGFLonwv48$cd423559be704a1a9f45003176e780a2fc555b0771f286b3b25fad2e2bad9766d339f9aefc8fb4c3185b32b096cbb32c85fededaf281621ba7270c9b0c080b1a', 'technicien', 'SOW', 'LAMINE', '771244410', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:49:01', 4),
(500, 'MAMADOU AMATH NDIAYE', 'MAMADOUAMATH.NDIAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$NYUBLFQvavw7CuRr$fde69ead16dd44d9266ca910a1832967c1871486b5eaa8653a012bb7d737de4b765d645f5d722a74ae9bd68fbf0e9b3672de958d7dc97ed1a343fb074d703469', 'technicien', 'NDIAYE', 'MAMADOU AMATH', '775979525', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:50:20', 4),
(501, 'MODOU GAYE FALL', 'MODOUGAYE.FALL@SOFATELCOM.COM', 'scrypt:32768:8:1$ptvwRTAQEOYQWdSm$01f71f0998d2b53f92126529368bef416b806827817d2b2f4a5fb654cd635a8edaa918794a8e613fb3ae4c0c1d1cefb3cf1806f3e30c996331986698ccaee502', 'technicien', 'FALL', 'MODOU GAYE', '774792557', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:52:22', 4),
(502, 'MODY NDIAYE', 'MODY.NDIAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$vlHI7wZLKpNuNudB$1952058cc4d7efb68de47685c003d9253ebfc4329d1e3a450e14b77d18722a2fdc9b1b56b0ba2e8b187a659bf38243cd3fe7a21f7addc3114559b2efd4928994', 'technicien', 'NDIAYE', 'MODY', '785568557', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:53:31', 4),
(503, 'MOUHAMED THIAM', 'MOUHAMED.THIAM@SOFATELCOM.COM', 'scrypt:32768:8:1$2tBiAfGXJUcqKl7r$4819a0a0eec4f48a4dc7161a197d76531b615aa58bc8859e8fc6136ce99c7da8b9aa7c6cc147d18cc4daef3e7286be19d8b5f65c510181dee9294be52dff5cf6', 'technicien', 'THIAM', 'MOUHAMED', '772270637', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:54:50', 4),
(504, 'MOUSTAPHA NIANG', 'MOUSTAPHA.NIANG@SOFATELCOM.COM', 'scrypt:32768:8:1$1xzAsG3GiMm4xw9n$3f09fdeb453ec5b88fcddc1dabdf1baa1417d587015d3806c40be44284c4d04b37d71f6a54bd4d84999c787a84c2fd13d1e441bdd6ca2fe9e86a410734e0c9bf', 'technicien', 'NIANG', 'MOUSTAPHA', '771476355', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:55:57', 4),
(505, 'OMAR DIA', 'OMAR.DIA@SOFATELCOM.COM', 'scrypt:32768:8:1$Ou9t1ITc08yVcXvV$3e2f7e9fdb93ec096e9a9c53b151c85165f3e4800c333978e0873032479387d2eec24e8e0a32fb8ce8a8adbc3eccf3e15e9c012abd921430c846d00915cb8924', 'technicien', 'DIA', 'OMAR', '782952811', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:57:20', 4),
(506, 'PAPE FAYE', 'PAPE.FAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$Xj3gHu3eZLETef34$a8bb90eea9bda13993565668b66eed26ee0e19afffbbbcae77e5ae20628e40e38babe3644d6cfed40d0b59b390549d37bafb445b4129dce599222ba2a16a8ccb', 'technicien', 'FAYE', 'PAPE', '781956884', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 16:59:46', 4),
(507, 'PAPE RIEYE NDIAYE', 'PAPERIEYE.NDIAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$FN2vQPOgviShDTDL$101327db57e7263c74f05e971556f3f6d6ff08c12cb8d6e38532c243d33549ed1af8df2442b9c0367c86c746b169dfce941adfe6c0ed454f8909b409e5d4ae38', 'technicien', 'NDIAYE', 'PAPE RIEYE', '776949393', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:01:19', 4),
(508, 'SALIF NDIAYE', 'SALIF.NDIAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$XWyqX3luCI76hG7l$f591564bc43ef39a4e0113e59747e196b0a43320ee5792f4b5a1ebcb6fa4d19691b0acccfcbac46d7249b8caf0145828c17e2805391f53827563ab393d0a4ad3', 'technicien', 'NDIAYE', 'SALIF', '774116701', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:02:39', 4),
(509, 'SALIOU GUEYE', 'SALIOU.GUEYE@SOFATELCOM.COM', 'scrypt:32768:8:1$jsRxK27gYX7xnVC4$c838138e4cac491c6a0c982042627929dcc228d3bfe0ddc0a0c1336913c0e72666fb76946d5fa01a2d6e92651fc5cce61da71121937ab8ea48199858ce987da8', 'technicien', 'GUEYE', 'SALIOU', '771933255', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:03:59', 4),
(510, 'SALIOU NDIAYE', 'SALIOU.NDIAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$RmqspCI7HY2RTRB9$0189d84114151db31a24681c374f3e60e5b07a70ea1deea807f0efe6871d028d116c0b40afa1d33771a880604c64ed74de426d9e9e5db42933aeb5f4d43219fc', 'technicien', 'NDIAYE', 'SALIOU', '781956893', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:05:12', 4),
(511, 'SANKOUM BODJAN', 'SANKOUM.BODJAN@SOFATELCOM.COM', 'scrypt:32768:8:1$gi1Z0qK0OVu88VCX$5b3e9cfe52bdc009451115624f476d918028339748a74e2d0eb35457819c9e55c0a1d5c42f13320fcbcd77bd3ab6937196d126976f5023e2fbca2e863bc14179', 'technicien', 'BODJAN', 'SANKOUM', '781150691', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:06:33', 4),
(512, 'SIDY LAMINE DIABANG', 'SIDYLAMINE.DIABANG@SOFATELCOM.COM', 'scrypt:32768:8:1$vkTrVKlSEqThVHBT$122e10c4fbec4d96ad0ee700fab668980dd6c855604fb4c0192672e6b03a2b90e68e5cf904e71162a1f5e0d88e5954d46b2a1b82beae9091b7c9f0db7a39ba76', 'technicien', 'DIABANG', 'SIDY LAMINE', '777748475', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:07:50', 4),
(513, 'ADBOU KARIM DIAWARA', 'ADBOUKARIM.DIAWARA@SOFATELCOM.COM', 'scrypt:32768:8:1$iYAom9krHihrYkTE$f7379da38335944e04529bda681d7f1a93de96f3f71af0e4e2f33b8a76b9d5eb778948a6b17dba2f871d012adcdb0b4fb5a106cd51bb1525e88fe6bed38bd46a', 'technicien', 'DIAWARA', 'ADBOU KARIM', '771820566', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:26:20', 3),
(514, 'ALIOU DIOUF', 'ALIOU.DIOUF@SOFATELCOM.COM', 'scrypt:32768:8:1$O6BAaprOcnlNSOZF$877c408a5efef043a9a951b628580e1e0b3ccb886a7f94c4b22248c01096860a751aff38bf433ccccb5a7665cbb6a23deadfd35e95a32e422e1075756f13a609', 'technicien', 'DIOUF', 'ALIOU', '775957514', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:27:57', 3),
(515, 'ALY SOW DJIBA', 'ALYSOW.DJIBA@SOFATELCOM.COM', 'scrypt:32768:8:1$PjrshWTKW3CGLU2T$26d4705c2cc5b70f7cba91ad1efcc4fb23136554f9aa4eee808e262defe5ff2a6e7291f2db05f5aa28d027b1a410b059dc84e7338094601afcb0995b5bf4cedf', 'technicien', 'DJIBA', 'ALY SOW', '779973838', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:29:36', 3),
(516, 'ANTOINE WALY DIAGNE', 'ANTOINEWALY.DIAGNE@SOFATELCOM.COM', 'scrypt:32768:8:1$cKfSFl1h6gBgYSYs$6414255d1500d0e71589ea92c1dc2383cbf6e576306bf343240b345d0a6e8f4fc9062e82b4919cda002551e98556aa09b7d4a7cafb8e02bb130e37eb710b1980', 'technicien', 'DIAGNE', 'ANTOINE WALY', '777396606', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:31:18', 3),
(517, 'ASSANE DIENG', 'ASSANE.DIENG@SOFATELCOM.COM', 'scrypt:32768:8:1$xF4ZqKKBJtHCKjY2$cdd7f6b515fc954b75705f8f4661298e9fb1713f04df3b9b4578ceb04b954dbc89db2efda610f65c95f35d85d3d0a4a0e55091a51768996a1b625a12517bcb57', 'technicien', 'DIENG', 'ASSANE', '772976333', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:32:41', 3),
(518, 'ASSANE POUYE', 'ASSANE.POUYE@SOFATELCOM.COM', 'scrypt:32768:8:1$Ka1jlAoUeYdsk4z0$f5a2f461e666fa45265950a6127f43459a4990a502b3a8950e562d8277d63dcc8242f0bc2bdda3494aeaa81a81c1830536811586b985abe37f082fc3a5ab0779', 'technicien', 'POUYE', 'ASSANE', '771516800', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:34:00', 3),
(519, 'AWA SANGARE', 'AWA.SANGARE@SOFATELCOM.COM', 'scrypt:32768:8:1$Kf3w6ctdRZ2XZz9D$bef025e6b3b2b498aa4b4e84db2613904a3aafe3f6856d8bbac7e2d04267922824baef65f01a1437c2e44c5c38d9baf6a010cfec6f8dece9611c09595cc5bd4c', 'technicien', 'SANGARE', 'AWA', '777761930', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:35:56', 3),
(520, 'BABACAR DIOUF', 'BABACAR.DIOUF@SOFATELCOM.COM', 'scrypt:32768:8:1$IydjS9QTDmjnm5gB$18799ee1820e49b33284795c84d9636454b2b810a2629fc77c648ce84242e2a707f5f96e4be0d114137bec89a998bcda7c1de90214cae7d0100ccfea2409a2af', 'technicien', 'DIOUF', 'BABACAR', '776214432', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:37:31', 3),
(521, 'BAKARY DIATTA', 'BAKARY.DIATTA@SOFATELCOM.COM', 'scrypt:32768:8:1$BvQiVTJHd4hLlOug$0e1bce55daea5f1c57f32c87361aef098fe59da52ae02c6e3d5a625015b083b17a614bc411c15fe554060a388537abc662f9cd72ebe373341ea21c01ac64c85e', 'technicien', 'DIATTA', 'BAKARY', '783278136', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:39:03', 3),
(522, 'CHEIKH AMATH DIOUF', 'CHEIKHAMATH.DIOUF@SOFATELCOM.COM', 'scrypt:32768:8:1$awPImBdk9OkzOCAK$e9f881209b0ce16bd879ba49692fc709fc7f9671acf5d54c8823e827202b370131b633794182a78a5fef07bcac26af05089efc3f47dde8cb48de3c938dcbcbb3', 'technicien', 'DIOUF', 'CHEIKH AMATH', '786105540', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:40:15', 3),
(523, 'CHEIKH CISSE', 'CHEIKH.CISSE@SOFATELCOM.COM', 'scrypt:32768:8:1$UCpjEl5W2GVxI0Mz$54855588dd9fc81079efe0c1edb5968abd83a462a4c140fca8dd55237c82d00a62bbc530cf8fba6ade5b944eefa3fa83156de876e77c368b7bf07d354d2a6755', 'technicien', 'CISSE', 'CHEIKH', '779586996', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:41:32', 3),
(524, 'CHEIKH DEME', 'CHEIKH.DEME@SOFATELCOM.COM', 'scrypt:32768:8:1$uM6JEmtfQhE5SPu0$571eef099d11977aace7a94f6439af744e5b50966393b48c51851565522f91f6b803e76126749f99e89ca96e6b19ca8f1c6b2fafc1e7b112637bf3766c6884e0', 'technicien', 'DEME', 'CHEIKH', '783753040', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:42:46', 3),
(525, 'CHEIKH NIANG', 'CHEIKH.NIANG@SOFATELCOM.COM', 'scrypt:32768:8:1$e7Gu8eVIiWEviCcT$550eaf6446d2bf37edf4b89483850e69f24a7322cc9bfc45b53c8b62d802e204036c3091af17e1fa0c4ce1307f0a02a15ebc492f2ba3c249c50e82a8f7974aae', 'technicien', 'NIANG', 'CHEIKH', '775236352', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:44:05', 3),
(526, 'CHEIKH TIDIANE HANE', 'CHEIKHTIDIANE.HANE@SOFATELCOM.COM', 'scrypt:32768:8:1$oPDDcql5mePFxyqm$a3a463f4324ad3a261adad122e6a756975124dfd8a1299c67b1dc0d4b03e209e38c3a07504c24155a04c19fe50b59a124e837359aacf1e2ad182b10b9e80ad42', 'technicien', 'HANE', 'CHEIKH TIDIANE', '771927034', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:45:52', 3),
(527, 'DAME WADE', 'DAME.WADE@SOFATELCOM.COM', 'scrypt:32768:8:1$oniAd44ze4AVfhmU$58bf113b956d5925f302a59beec4ede1b3ffefcbb302491237788205e220939ab5220b828c524ac6294a987c8e9ef0c9c4d70554aadac7edb31877c16d43f97a', 'technicien', 'WADE', 'DAME', '781103361', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:46:52', 3),
(528, 'DJIDJACK JEAN PAUL DIOME', 'DJIDJACKJEANPAUL.DIOME@SOFATELCOM.COM', 'scrypt:32768:8:1$IopJhHxcaR2jo6Wd$72188edf5ce1e1a0c9a2d7f5bb0a59d21e782f4afa55e3cd4babc64055fb3a33a7587e5a57698430e423fb6c0a24638a0170ba3032a5ae1077cd11cd3e90fb8d', 'technicien', 'DIOME', 'DJIDJACK JEAN PAUL', '772652716', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:48:17', 3),
(529, 'DOUDOU POUYE', 'DOUDOU.POUYE@SOFATELCOM.COM', 'scrypt:32768:8:1$qjTNSU5YasG6Byu5$80e11f7047979d48bb662ef212591a4ddaffeb741832c9c497c9ed90245169e7db5767c918752b2cc155ba66a6be109f9c97d3fd33a88d7181a756a391c749b3', 'technicien', 'POUYE', 'DOUDOU', '773694917', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:49:48', 3),
(530, 'EL HADJI MOUSSA NDIAYE', 'ELHADJIMOUSSA.NDIAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$qDqwh5wpOlvYvCMO$acfa46a70943df59781584d730dd9889d49d2977a122e046e13361b86f2c9aa04658bd692f86dc6de2129d373233c83913abbe925f5ced571e7f1af92de4d74d', 'technicien', 'NDIAYE', 'EL HADJI MOUSSA', '781456912', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:51:25', 3),
(531, 'EL HADJI MOUSSA SAKHO', 'ELHADJIMOUSSA.SAKHO@SOFATELCOM.COM', 'scrypt:32768:8:1$Doiu8raQPTyW7Rwa$e9c7e3c3373e6a7e73f9f82a801c0839a9ed0f38e1db3990e037b4826262e052c138c1e06de1060012fa557decbcfa6abef0b1c0da8e91d3277f75b8c1dd072c', 'technicien', 'SAKHO', 'EL HADJI MOUSSA', '775218141', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:53:09', 3),
(532, 'GORA DIOP', 'GORA.DIOP@SOFATELCOM.COM', 'scrypt:32768:8:1$EYTEKA9PwuAk8vrE$3cdeb362007ac68dfd3dd9323365b96a6bafdf63ef31a85330a12a1d543124be5ae46a3da0375d1db449ba345c136fe05d5dab42ec7baabc6d143fdffd2e61f1', 'technicien', 'DIOP', 'GORA', '777042256', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:54:29', 3),
(533, 'IBRAHIMA KHALIL NDIAYE', 'IBRAHIMAKHALIL.NDIAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$c7rGehmsg81zzVkO$c0d75643f2787d0cd843709faa0468ed5c4829405c92425fec052a86b36dfda66ebc6ff7bbc379a820351de24554184b6f80efb646ba0c85bd6455ec92596c92', 'technicien', 'NDIAYE', 'IBRAHIMA KHALIL', '771066218', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:56:16', 3),
(534, 'IBRAHIMA TRAORE', 'IBRAHIMA.TRAORE@SOFATELCOM.COM', 'scrypt:32768:8:1$7KtDRqFBRKK7b6QP$b60eab561380136f27b70266edbac1864bb0ae569dc76a8c2b88d3a4e807f61c0bcada932fcf61cd1450a2614fe90b1087d4e8ee85fbf4c20cfbba88df6c9cb5', 'technicien', 'TRAORE', 'IBRAHIMA', '778477655', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:57:52', 3),
(535, 'ISMAILA DIOUF', 'ISMAILA.DIOUF@SOFATELCOM.COM', 'scrypt:32768:8:1$Wkg9XOroyAd58n04$ee559216cb65bb371c136c90f294ed1332d5905c58476cb2cb47367bc27e9bfa202cd6bd18974a57e47cc9f7ad9446872e8eba31fd99270ffded47f31f3b0c54', 'technicien', 'DIOUF', 'ISMAILA', '783077994', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 17:59:23', 3),
(536, 'JEAN TOUPANE', 'JEAN.TOUPANE@SOFATELCOM.COM', 'scrypt:32768:8:1$rEAfwJiGDNRwuvBt$61998d43543c2fd863c7766c73911a392b9754e4ca054437aea4fb3ad25cefb1b0a20f97624fd62bb96359a39a9729129cafe8d356c50b785ae7a34d7adb8b38', 'technicien', 'TOUPANE', 'JEAN', '775228499', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:29:50', 3),
(537, 'KASSA DIEYE', 'KASSA.DIEYE@SOFATELCOM.COM', 'scrypt:32768:8:1$zcax8NxzQ7uA3sv2$f85cb7d63021c46c2563afe75d357727ae1984e6386a9e14c56ed757f7a2ca3cb4fd393a22b30d821b26fc1e7913ccdb4a40e8d5b573d554cedf9af40608b9f5', 'technicien', 'DIEYE', 'KASSA', '772813081', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:31:10', 3),
(538, 'LAMINE WADE', 'LAMINE.WADE@SOFATELCOM.COM', 'scrypt:32768:8:1$tn8Ybo5asRr0EyCC$ba55b806ddef75fa54a997b45f6f955fc58fd36d292146a84c2fcb6b48ad0582c86d6fe033c8d087edf144424c207bee42672a9197d555e2ffe9485125ff7a4b', 'technicien', 'WADE', 'LAMINE', '782437709', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:32:22', 3),
(539, 'MALAMINE SIGNATE', 'MALAMINE.SIGNATE@SOFATELCOM.COM', 'scrypt:32768:8:1$myZfbn3Fxk5ln9Qg$10d51d5c54e1e20435c0beca7df4f2bfed8604d2f0de5af62d95aa76c06ca62e39140e4b78c728f0a4c3e21d9378fdac1ec2f46d3043f007fbc6ea85b821ba8b', 'technicien', 'SIGNATE', 'MALAMINE', '776808717', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:34:06', 3),
(540, 'MATY TALL', 'MATY.TALL@SOFATELCOM.COM', 'scrypt:32768:8:1$hXQYl26S5krckz4s$dbc1930c879e40e715de744f6fbc7f6961acdb53f5eb0bc13244bf7827455b0fe1a1a69cbaccf2287d40e2ea9c5887ad88841ed6fabed8c5a190f80ab943bf5e', 'technicien', 'TALL', 'MATY', '788050664', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:40:56', 3),
(541, 'MBAYE POUYE', 'MBAYE.POUYE@SOFATELCOM.COM', 'scrypt:32768:8:1$MeT2yLNSt98h0T3B$616038a2fcf298ff57abb7d5fa403346ce7817d3164289db66a4a1d25a9a96cc052e681713a73fcaf938015d66f69921789dc0695191bd62f297e134b9792d1f', 'technicien', 'POUYE', 'MBAYE', '777512912', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:42:05', 3),
(542, 'MOHAMADOU MOUSTAPHA DIENG', 'MOHAMADOUMOUSTAPHA.DIENG@SOFATELCOM.COM', 'scrypt:32768:8:1$O4bYFb6T4MJt9Koc$2e1feca4ae1b23df3c92e7ff26a8988b290c2aa510fae96ae6ca95cd3696626bb598e6808b64221658a5c35d8de3afcb94cd02a7fa9fc875ccdc9769fdd7cd97', 'technicien', 'DIENG', 'MOHAMADOU MOUSTAPHA ', '778908477', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:44:12', 3),
(543, 'MOUHAMADOU NDOUR', 'MOUHAMADOU.NDOUR@SOFATELCOM.COM', 'scrypt:32768:8:1$DcSW8JsImMkWttTc$b136b21277e91a6c3c9398178f84738ecde9bbcf0bd9e0e48c39e4bb303964595826ee317942ab21e1c6accc7df6d2075311527c132b9963b11b637050a870a3', 'technicien', 'NDOUR ', 'MOUHAMADOU', '784869790', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:45:17', 3),
(544, 'MOUHAMED BA', 'MOUHAMED.BA@SOFATELCOM.COM', 'scrypt:32768:8:1$dFSPr16F67awVdLj$ac375a3a0192db3a8550066636d05a77fe0f398ae4a2c9822593c144efc2416bc1cfd44a8600ce91668de216b71f5b7e2ee57f81776700c7853bc6739d4e3347', 'technicien', 'BA ', 'MOUHAMED', '772465442', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:46:21', 3),
(545, 'MOUHAMED CIRE DIA', 'MOUHAMEDCIRE.DIA@SOFATELCOM.COM', 'scrypt:32768:8:1$jBWvEiBeK5b55kGj$41650ab18133909a5f3320a8f893cd77dc36a5456a080ecf170a5f3f082a5186ad929799106f856799a30040c68f9d1e87de1d839950b1ccb84d865004eca512', 'technicien', 'DIA', 'MOUHAMED CIRE', '776620510', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:47:44', 3),
(546, 'MOUHAMED NIANG', 'MOUHAMED.NIANG@SOFATELCOM.COM', 'scrypt:32768:8:1$7tYLISQINsg1FoHy$3fd0157d9fa6534f55d5efcf1c7ec276cba3a1eedd802d68c9a32914cad3624954a04f4e794431a0d0c80c1552bc8521990a3dad6bdff9f0225a08d63b081288', 'technicien', 'NIANG', 'MOUHAMED ', '775642416', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:48:52', 3),
(547, 'MOUNIROU KANTE', 'MOUNIROU.KANTE@SOFATELCOM.COM', 'scrypt:32768:8:1$Ytjg7qcUQorBslMx$a4eb5a3a7de8675e4bdc71e6e85661bc2af6ad9870b4ffab8b90ca2bb5b9c304a88798b5c9bdc1c6646b61e79fbb979e58ec5ff530d4619cf2643fd6d1766250', 'technicien', 'KANTE', 'MOUNIROU', '773810795', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:49:50', 3),
(548, 'MOUSTAPHA CAMARA', 'MOUSTAPHA.CAMARA@SOFATELCOM.COM', 'scrypt:32768:8:1$AiCxmaSP2ip10OW1$8f92e28ca44e2bcf04c170b9e663ea76cd67571dc51af0f4f272b39c3daa5cb1553465fc0729a3a7a56752a95709773d0164cfb83fddb0361e9b478c19783bd4', 'technicien', 'CAMARA', 'CAMARA', '777647895', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:51:56', 3),
(549, 'NGAGNE DEMBA NDIR', 'NGAGNEDEMBA.NDIR@SOFATELCOM.COM', 'scrypt:32768:8:1$c07AQzdpFO5sD0FC$245be970ae7bc9ed0e471d427f3795dd6f0096bddbb883b1c3a20aabd7629c2ef0aee8efe93ab5f97b08f68990c000c6969102fc1562b54cdc6797e3dbd96531', 'technicien', ' NDIR', 'NGAGNE DEMBA', '785209603', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:53:20', 3),
(550, 'OUSMANE FALL', 'OUSMANE.FALL@SOFATELCOM.COM', 'scrypt:32768:8:1$dTEb1wS0zfwQd0OE$9761d01082124951c9bdbaafcfac1c4ca723f10625480c26867a30094ebb93e61a38a5e654e33ae23d781ed3c60026b62aa462f4f04d7b5072f048e796459c52', 'technicien', 'FALL', 'OUSMANE', '784459560', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:54:19', 3),
(551, 'OUSSEYNOU NIANG', 'OUSSEYNOU.NIANG@SOFATELCOM.COM', 'scrypt:32768:8:1$7ebPRMYC0kpbTlRY$28f375d2c4e7e1de83cb7a5e1e79bfd86d1522aaf5f10144b4004e7d1b7b912cb96e7f754f13c9e04fc36390e3b5618558085fff4f11e40fd60fee5568388eb5', 'technicien', 'NIANG', 'OUSSEYNOU', '771325428', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:55:19', 3),
(552, 'OUSSEYNOU THIAM', 'OUSSEYNOU.THIAM@SOFATELCOM.COM', 'scrypt:32768:8:1$p90oLDRK0yoZc27W$7212231c5cd875046b76a6903bd3bddf8b0d59a0c0d81d224a38d882447029da4dd759e924215721542ab4bce2cbe18a3be9a68f3ecf6bebd3a09134cc1c5fb2', 'technicien', 'THIAM', 'OUSSEYNOU', '778601872', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:56:28', 3),
(553, 'PAPA ASSANE GAYE', 'PAPAASSANE.GAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$AncCzdbNBf99lZaN$39f51b52fad634ab9dd157b43af882634871dd239650fdfe3f434f8d1028fa5ef82832ae73bd796cbd6543c6220644199caec68633670bba7fa3c59fff26d295', 'technicien', 'GAYE', 'PAPA ASSANE', '776250324', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:57:49', 3),
(554, 'PAPA MAMADOU CISSE', 'PAPAMAMADOU.CISSE@SOFATELCOM.COM', 'scrypt:32768:8:1$3FVw9iDn2GQGjlsh$77029d177b20dd0447d564dda95d58efadf793f2d812a1210d4d53e359ea1284d17ac42ac13c83f2672c07068decccf2e74ddbfd88a18b91fdadfd53f2d1608c', 'technicien', 'CISSE', 'PAPA MAMADOU', '772001723', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 18:58:51', 3),
(555, 'SOULEYMANE LY GUEYE', 'SOULEYMANELY.GUEYE@SOFATELCOM.COM', 'scrypt:32768:8:1$Rb8X1Sb8T2Rc2rwL$b8e29426152919ec298a4b62ca0e99948f50b6188058a95d97ecdb7be136f5399fee1f961a2ab0ab58a4d654c658e739f29f3cae7ca68a5e3386af7c9dc21f2e', 'technicien', 'GUEYE', 'SOULEYMANE LY', '774790523', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 19:00:02', 3),
(556, 'TENING MARONE', 'TENING.MARONE@SOFATELCOM.COM', 'scrypt:32768:8:1$KkIuhj6MJ7TR5sBI$33b8afc5c649ce886efeb58478cb94c49bb64474b0bb9bd72c2ec8c32fc7ce0a5dacbae2582c94fddaa82589d0325d2b5412561762860b4e84aff276caa6c0cd', 'technicien', 'MARONE ', 'TENING ', '779258938', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 19:01:06', 3);
INSERT INTO `user` (`id`, `username`, `email`, `password_hash`, `role`, `nom`, `prenom`, `telephone`, `zone`, `commune`, `quartier`, `service`, `technologies`, `actif`, `date_creation`, `zone_id`) VALUES
(557, 'TOUMANI DIAKHATE', 'TOUMANI.DIAKHATE@SOFATELCOM.COM', 'scrypt:32768:8:1$ZbxxS4GmyJEc4Xt5$58ba17498d346cd9c5888ba78069c100a4a8645ad0cf7c31fd9887ac360dbccfd7ab1e601f6f1ed58f9177c5ffb6732609064683aa09d59f73c23a1564794ed7', 'technicien', 'DIAKHATE', 'TOUMANI', '782133614', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 19:02:15', 3),
(558, 'MOUSSA GUEYE1', 'MOUSSAGUEYE1@SOFATELCOM.COM', 'scrypt:32768:8:1$Y7dOfERzhXpDEg13$8ad532c70becc6cc71ac059335cd00c94f8a691e9bd7be0fd6f381b8032de5ff121c749b269a6cfcd9f6ab5e09b6896f81614bfd467824c18978ea0e241d4209', 'technicien', 'GUEYE1', 'MOUSSA', '773023504', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 19:03:34', 3),
(559, 'IBRAHIM NDIAYE', 'IBRAHIM.NDIAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$Mcis8AGUji1LSQd7$a65f8bec46ace0de060cae0ec285328f916f83b7594b6d4e432191ab01661207430c3a4913054cfd93dba8d170be73ccb7d404c23ec0ca5005b5e926b2dd16fe', 'technicien', 'NDIAYE', 'IBRAHIM ', '784431515', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-03 19:04:54', 3),
(560, 'CHEIKH DIENG', 'CHEIKH.DIENG@SOFATELCOM.COM', 'scrypt:32768:8:1$Y8cb80NMS4lHBedN$ba2a7110c37fb812937c0eea5b1d671a9701ab4b4dbdd93e9fa8b03712965f75db246a2594f55c521868b09c2d57bdd1de3d266c49fe114715260c220cc6e514', 'technicien', 'DIENG', 'CHEIKH', '775927478', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-04 08:35:50', 1),
(561, 'CHERIF SY', 'CHERIF.SY@SOFATELCOM.COM', 'scrypt:32768:8:1$fjLNsGcsRGmh62AZ$9b3a6b7623eb503a42a3c1066fd15b9995e657cbd42f4db91fcf99d962fc8d8095cc977684c1f716523b9a80f3f7fbd84e9f2a1651e02b392cbeb9c3522ca943', 'technicien', 'SY', 'CHERIF', '783056432', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-04 08:38:32', 1),
(562, 'DJIBY TALL', 'DJIBY.TALL@SOFATELCOM.COM', 'scrypt:32768:8:1$ICRjR7a9fbrw6NSl$fe2b78203f950eb1d713218d38392bd40b948170d08bd55f46c9b62dd73deca40935274b5b60c3f9f5d60a3d15301e80777b09b3ce52f95e5a098ec9bb6e942f', 'technicien', 'TALL', 'DJIBY', '784916468', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-04 08:41:30', NULL),
(563, 'IBRAHIMA DIOP', 'IBRAHIMA.DIOP@SOFATELCOM.COM', 'scrypt:32768:8:1$yvOibLXI52nEsURL$5097bc908930d209c0e0b72a34c3a172be8addc5b81c9d4c0aaabb15e84a5ddcbd8bbc21b94499f8c5f34c743ef575f844ab9cabb5a5571df38649d1cb42e515', 'technicien', 'DIOP', 'IBRAHIMA', '778355015', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-04 08:45:55', NULL),
(564, 'NDIOGOU DIA', 'NDIOGOU.DIA@SOFATELCOM.COM', 'scrypt:32768:8:1$7PDhic2ljMJrF0M2$85cb34d57577731fdd8e0a84b555920f6f3e4261574aeccc096e4c181a111391ea5c731c625a064d6eb84561df8de8700ac1c30a475cf5c653f400dfdc1c21a2', 'technicien', 'DIA', 'NDIOGOU', '777633048', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-04 09:17:17', NULL),
(565, 'ADAMA MBAYE', 'ADAMA.MBAYE@SOFATELCOM.COM', 'scrypt:32768:8:1$AYpn60t6THKSyFrz$86341562e61db20ff352f690a7203e5af3a9369a4c5a50538587b17949f4a71aa5ad64b96e1c4f276cc1706645e7c866581b94c29a07c256ebc2cf12580d2bb9', 'technicien', 'MBAYE', 'ADAMA', '785618196', NULL, NULL, NULL, NULL, 'Fibre,Cuivre,5G', 1, '2026-03-04 09:50:27', 3),
(566, 'abdoukhadirsamb', 'abdoukhadir.samb@sofatelcom.com', 'scrypt:32768:8:1$WpEqzT53EoWlvI5t$5ff9b5c7b69e924f411b5e2875f07f070792815afba8dffbd9e35b789f458198be0eedf347c89fe1344a5a71b1530bc8df09b76255e23b70fd0f150d6e628686', 'chef_zone', 'SAMB', 'ABDOU KHADIR', '781700102', NULL, NULL, NULL, NULL, NULL, 1, '2026-03-04 11:42:54', 3),
(567, 'test1', 'test1@gmail.com', 'scrypt:32768:8:1$8VFCQn0SmfaWiOX3$164d1199805b82209f32d28addb07c7c8a23fa0cb7d6de952589e944661998524c2c4c9fc927eaa993e25bf95746e1c5ec53cdb0668e0f9346dec981263026ac', 'chef_zone', 'test1', 'test1', '787878787', 'DAKAR', NULL, NULL, NULL, NULL, 1, '2026-03-09 13:33:42', 1);

-- --------------------------------------------------------

--
-- Structure de la table `user_connection_log`
--

CREATE TABLE `user_connection_log` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `action` varchar(20) NOT NULL,
  `timestamp` datetime NOT NULL,
  `ip_address` varchar(45) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `zone`
--

CREATE TABLE `zone` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `code` varchar(20) NOT NULL,
  `description` text DEFAULT NULL,
  `chef_zone_id` int(11) DEFAULT NULL,
  `region` varchar(100) DEFAULT NULL,
  `actif` tinyint(1) DEFAULT NULL,
  `date_creation` datetime NOT NULL,
  `date_modification` datetime DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `zone`
--

INSERT INTO `zone` (`id`, `nom`, `code`, `description`, `chef_zone_id`, `region`, `actif`, `date_creation`, `date_modification`) VALUES
(1, 'DAKAR', 'DK', NULL, NULL, 'Dakar', 1, '2026-01-27 10:27:39', NULL),
(2, 'PIKINE', 'PK', NULL, NULL, 'Pikine', 1, '2026-01-27 10:27:39', NULL),
(3, 'Mbour', 'MBOUR', 'Zone de Mbour', NULL, 'Thiès', 1, '2026-03-03 10:49:40', NULL),
(4, 'Kaolack', 'KAOLACK', 'Zone de Kaolack', NULL, 'Kaolack', 1, '2026-03-03 10:49:40', NULL),
(5, 'Autres', 'AUTRES', 'Autres zones', NULL, NULL, 1, '2026-03-03 10:49:40', NULL);

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `activity_log`
--
ALTER TABLE `activity_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Index pour la table `alembic_version`
--
ALTER TABLE `alembic_version`
  ADD PRIMARY KEY (`version_num`);

--
-- Index pour la table `audit_log`
--
ALTER TABLE `audit_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_audit_log_created_at` (`created_at`),
  ADD KEY `actor_id` (`actor_id`);

--
-- Index pour la table `categorie`
--
ALTER TABLE `categorie`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nom` (`nom`);

--
-- Index pour la table `client`
--
ALTER TABLE `client`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `ix_client_numero_ligne_sonatel` (`numero_ligne_sonatel`),
  ADD KEY `ix_client_nom` (`nom`);

--
-- Index pour la table `demande_intervention`
--
ALTER TABLE `demande_intervention`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fichier_importe_id` (`fichier_importe_id`),
  ADD KEY `technicien_id` (`technicien_id`);

--
-- Index pour la table `dossier_sav`
--
ALTER TABLE `dossier_sav`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `numero_dossier` (`numero_dossier`),
  ADD KEY `numero_serie_id` (`numero_serie_id`),
  ADD KEY `numero_serie_remplacement_id` (`numero_serie_remplacement_id`),
  ADD KEY `client_id` (`client_id`),
  ADD KEY `intervention_id` (`intervention_id`),
  ADD KEY `cree_par_id` (`cree_par_id`);

--
-- Index pour la table `emplacement_stock`
--
ALTER TABLE `emplacement_stock`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `code` (`code`);

--
-- Index pour la table `equipe`
--
ALTER TABLE `equipe`
  ADD PRIMARY KEY (`id`),
  ADD KEY `chef_zone_id` (`chef_zone_id`);

--
-- Index pour la table `fiche_technique`
--
ALTER TABLE `fiche_technique`
  ADD PRIMARY KEY (`id`),
  ADD KEY `technicien_id` (`technicien_id`),
  ADD KEY `intervention_id` (`intervention_id`);

--
-- Index pour la table `fichier_import`
--
ALTER TABLE `fichier_import`
  ADD PRIMARY KEY (`id`),
  ADD KEY `importe_par` (`importe_par`),
  ADD KEY `idx_fichier_import_actif` (`actif`);

--
-- Index pour la table `fournisseur`
--
ALTER TABLE `fournisseur`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `code` (`code`);

--
-- Index pour la table `historique_etat_numero_serie`
--
ALTER TABLE `historique_etat_numero_serie`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_historique_etat_numero_serie_date_transition` (`date_transition`),
  ADD KEY `ix_historique_etat_numero_serie_numero_serie_id` (`numero_serie_id`),
  ADD KEY `utilisateur_id` (`utilisateur_id`);

--
-- Index pour la table `import_historique_numero_serie`
--
ALTER TABLE `import_historique_numero_serie`
  ADD PRIMARY KEY (`id`),
  ADD KEY `utilisateur_id` (`utilisateur_id`),
  ADD KEY `produit_id` (`produit_id`);

--
-- Index pour la table `intervention`
--
ALTER TABLE `intervention`
  ADD PRIMARY KEY (`id`),
  ADD KEY `demande_id` (`demande_id`),
  ADD KEY `technicien_id` (`technicien_id`),
  ADD KEY `equipe_id` (`equipe_id`),
  ADD KEY `valide_par` (`valide_par`),
  ADD KEY `sla_acknowledged_by` (`sla_acknowledged_by`);

--
-- Index pour la table `intervention_history`
--
ALTER TABLE `intervention_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `intervention_id` (`intervention_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Index pour la table `kpi_alerte`
--
ALTER TABLE `kpi_alerte`
  ADD PRIMARY KEY (`id`),
  ADD KEY `kpi_score_id` (`kpi_score_id`),
  ADD KEY `technicien_id` (`technicien_id`);

--
-- Index pour la table `kpi_historique`
--
ALTER TABLE `kpi_historique`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_kpi_historique_date` (`date`),
  ADD KEY `technicien_id` (`technicien_id`);

--
-- Index pour la table `kpi_metric`
--
ALTER TABLE `kpi_metric`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nom` (`nom`);

--
-- Index pour la table `kpi_objectif`
--
ALTER TABLE `kpi_objectif`
  ADD PRIMARY KEY (`id`),
  ADD KEY `technicien_id` (`technicien_id`);

--
-- Index pour la table `kpi_score`
--
ALTER TABLE `kpi_score`
  ADD PRIMARY KEY (`id`),
  ADD KEY `equipe_id` (`equipe_id`),
  ADD KEY `technicien_id` (`technicien_id`);

--
-- Index pour la table `leave_request`
--
ALTER TABLE `leave_request`
  ADD PRIMARY KEY (`id`),
  ADD KEY `technicien_id` (`technicien_id`),
  ADD KEY `manager_id` (`manager_id`);

--
-- Index pour la table `ligne_mouvement_stock`
--
ALTER TABLE `ligne_mouvement_stock`
  ADD PRIMARY KEY (`id`),
  ADD KEY `mouvement_id` (`mouvement_id`),
  ADD KEY `produit_id` (`produit_id`);

--
-- Index pour la table `membre_equipe`
--
ALTER TABLE `membre_equipe`
  ADD PRIMARY KEY (`id`),
  ADD KEY `equipe_id` (`equipe_id`),
  ADD KEY `technicien_id` (`technicien_id`);

--
-- Index pour la table `mouvement_numero_serie`
--
ALTER TABLE `mouvement_numero_serie`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_mouvement_numero_serie_date_mouvement` (`date_mouvement`),
  ADD KEY `ix_mouvement_numero_serie_numero_serie_id` (`numero_serie_id`),
  ADD KEY `ancien_emplacement_id` (`ancien_emplacement_id`),
  ADD KEY `nouvel_emplacement_id` (`nouvel_emplacement_id`),
  ADD KEY `utilisateur_id` (`utilisateur_id`),
  ADD KEY `nouveau_technicien_id` (`nouveau_technicien_id`),
  ADD KEY `ancien_technicien_id` (`ancien_technicien_id`);

--
-- Index pour la table `mouvement_stock`
--
ALTER TABLE `mouvement_stock`
  ADD PRIMARY KEY (`id`),
  ADD KEY `produit_id` (`produit_id`),
  ADD KEY `utilisateur_id` (`utilisateur_id`),
  ADD KEY `fournisseur_id` (`fournisseur_id`),
  ADD KEY `emplacement_id` (`emplacement_id`),
  ADD KEY `ix_mouvement_stock_workflow_state` (`workflow_state`),
  ADD KEY `approuve_par_id` (`approuve_par_id`);

--
-- Index pour la table `note_rh`
--
ALTER TABLE `note_rh`
  ADD PRIMARY KEY (`id`),
  ADD KEY `author_id` (`author_id`),
  ADD KEY `ix_note_rh_actif` (`actif`);

--
-- Index pour la table `notification_sms`
--
ALTER TABLE `notification_sms`
  ADD PRIMARY KEY (`id`),
  ADD KEY `technicien_id` (`technicien_id`),
  ADD KEY `demande_id` (`demande_id`);

--
-- Index pour la table `numero_serie`
--
ALTER TABLE `numero_serie`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_numero_serie_numero` (`numero`),
  ADD KEY `ix_numero_serie_statut` (`statut`),
  ADD KEY `ix_numero_serie_produit_id` (`produit_id`),
  ADD KEY `dossier_sav_id` (`dossier_sav_id`),
  ADD KEY `modifie_par_id` (`modifie_par_id`),
  ADD KEY `technicien_id` (`technicien_id`),
  ADD KEY `client_id` (`client_id`),
  ADD KEY `emplacement_id` (`emplacement_id`),
  ADD KEY `zone_id` (`zone_id`),
  ADD KEY `cree_par_id` (`cree_par_id`);

--
-- Index pour la table `produits`
--
ALTER TABLE `produits`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `reference` (`reference`),
  ADD UNIQUE KEY `code_barres` (`code_barres`),
  ADD KEY `categorie_id` (`categorie_id`),
  ADD KEY `emplacement_id` (`emplacement_id`),
  ADD KEY `fournisseur_id` (`fournisseur_id`);

--
-- Index pour la table `reservation_piece`
--
ALTER TABLE `reservation_piece`
  ADD PRIMARY KEY (`id`),
  ADD KEY `intervention_id` (`intervention_id`),
  ADD KEY `produit_id` (`produit_id`),
  ADD KEY `utilisateur_id` (`utilisateur_id`);

--
-- Index pour la table `survey`
--
ALTER TABLE `survey`
  ADD PRIMARY KEY (`id`),
  ADD KEY `intervention_id` (`intervention_id`);

--
-- Index pour la table `token_blacklist`
--
ALTER TABLE `token_blacklist`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_token_blacklist_jti` (`jti`),
  ADD KEY `user_id` (`user_id`);

--
-- Index pour la table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Index pour la table `user_connection_log`
--
ALTER TABLE `user_connection_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Index pour la table `zone`
--
ALTER TABLE `zone`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `code` (`code`),
  ADD UNIQUE KEY `ix_zone_nom` (`nom`),
  ADD KEY `chef_zone_id` (`chef_zone_id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `activity_log`
--
ALTER TABLE `activity_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=54;

--
-- AUTO_INCREMENT pour la table `audit_log`
--
ALTER TABLE `audit_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT pour la table `categorie`
--
ALTER TABLE `categorie`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `client`
--
ALTER TABLE `client`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `demande_intervention`
--
ALTER TABLE `demande_intervention`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `dossier_sav`
--
ALTER TABLE `dossier_sav`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `emplacement_stock`
--
ALTER TABLE `emplacement_stock`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=123;

--
-- AUTO_INCREMENT pour la table `equipe`
--
ALTER TABLE `equipe`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `fiche_technique`
--
ALTER TABLE `fiche_technique`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `fichier_import`
--
ALTER TABLE `fichier_import`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `fournisseur`
--
ALTER TABLE `fournisseur`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=77;

--
-- AUTO_INCREMENT pour la table `historique_etat_numero_serie`
--
ALTER TABLE `historique_etat_numero_serie`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `import_historique_numero_serie`
--
ALTER TABLE `import_historique_numero_serie`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `intervention`
--
ALTER TABLE `intervention`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `intervention_history`
--
ALTER TABLE `intervention_history`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `kpi_alerte`
--
ALTER TABLE `kpi_alerte`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `kpi_historique`
--
ALTER TABLE `kpi_historique`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `kpi_metric`
--
ALTER TABLE `kpi_metric`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `kpi_objectif`
--
ALTER TABLE `kpi_objectif`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `kpi_score`
--
ALTER TABLE `kpi_score`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `leave_request`
--
ALTER TABLE `leave_request`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `ligne_mouvement_stock`
--
ALTER TABLE `ligne_mouvement_stock`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `membre_equipe`
--
ALTER TABLE `membre_equipe`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `mouvement_numero_serie`
--
ALTER TABLE `mouvement_numero_serie`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `mouvement_stock`
--
ALTER TABLE `mouvement_stock`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `note_rh`
--
ALTER TABLE `note_rh`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `notification_sms`
--
ALTER TABLE `notification_sms`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `numero_serie`
--
ALTER TABLE `numero_serie`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT pour la table `produits`
--
ALTER TABLE `produits`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `reservation_piece`
--
ALTER TABLE `reservation_piece`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `survey`
--
ALTER TABLE `survey`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `token_blacklist`
--
ALTER TABLE `token_blacklist`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `user`
--
ALTER TABLE `user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=568;

--
-- AUTO_INCREMENT pour la table `user_connection_log`
--
ALTER TABLE `user_connection_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `zone`
--
ALTER TABLE `zone`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `activity_log`
--
ALTER TABLE `activity_log`
  ADD CONSTRAINT `activity_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);

--
-- Contraintes pour la table `demande_intervention`
--
ALTER TABLE `demande_intervention`
  ADD CONSTRAINT `demande_intervention_ibfk_1` FOREIGN KEY (`fichier_importe_id`) REFERENCES `fichier_import` (`id`),
  ADD CONSTRAINT `demande_intervention_ibfk_2` FOREIGN KEY (`technicien_id`) REFERENCES `user` (`id`);

--
-- Contraintes pour la table `equipe`
--
ALTER TABLE `equipe`
  ADD CONSTRAINT `equipe_ibfk_1` FOREIGN KEY (`chef_zone_id`) REFERENCES `user` (`id`);

--
-- Contraintes pour la table `fiche_technique`
--
ALTER TABLE `fiche_technique`
  ADD CONSTRAINT `fiche_technique_ibfk_1` FOREIGN KEY (`technicien_id`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `fiche_technique_ibfk_2` FOREIGN KEY (`intervention_id`) REFERENCES `intervention` (`id`);

--
-- Contraintes pour la table `fichier_import`
--
ALTER TABLE `fichier_import`
  ADD CONSTRAINT `fichier_import_ibfk_1` FOREIGN KEY (`importe_par`) REFERENCES `user` (`id`);

--
-- Contraintes pour la table `intervention`
--
ALTER TABLE `intervention`
  ADD CONSTRAINT `intervention_ibfk_1` FOREIGN KEY (`demande_id`) REFERENCES `demande_intervention` (`id`),
  ADD CONSTRAINT `intervention_ibfk_2` FOREIGN KEY (`technicien_id`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `intervention_ibfk_3` FOREIGN KEY (`equipe_id`) REFERENCES `equipe` (`id`),
  ADD CONSTRAINT `intervention_ibfk_4` FOREIGN KEY (`valide_par`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `intervention_ibfk_5` FOREIGN KEY (`sla_acknowledged_by`) REFERENCES `user` (`id`);

--
-- Contraintes pour la table `ligne_mouvement_stock`
--
ALTER TABLE `ligne_mouvement_stock`
  ADD CONSTRAINT `ligne_mouvement_stock_ibfk_1` FOREIGN KEY (`mouvement_id`) REFERENCES `mouvement_stock` (`id`),
  ADD CONSTRAINT `ligne_mouvement_stock_ibfk_2` FOREIGN KEY (`produit_id`) REFERENCES `produits` (`id`);

--
-- Contraintes pour la table `membre_equipe`
--
ALTER TABLE `membre_equipe`
  ADD CONSTRAINT `membre_equipe_ibfk_1` FOREIGN KEY (`equipe_id`) REFERENCES `equipe` (`id`),
  ADD CONSTRAINT `membre_equipe_ibfk_2` FOREIGN KEY (`technicien_id`) REFERENCES `user` (`id`);

--
-- Contraintes pour la table `mouvement_stock`
--
ALTER TABLE `mouvement_stock`
  ADD CONSTRAINT `mouvement_stock_ibfk_1` FOREIGN KEY (`produit_id`) REFERENCES `produits` (`id`),
  ADD CONSTRAINT `mouvement_stock_ibfk_2` FOREIGN KEY (`utilisateur_id`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `mouvement_stock_ibfk_3` FOREIGN KEY (`fournisseur_id`) REFERENCES `fournisseur` (`id`),
  ADD CONSTRAINT `mouvement_stock_ibfk_4` FOREIGN KEY (`emplacement_id`) REFERENCES `emplacement_stock` (`id`),
  ADD CONSTRAINT `mouvement_stock_ibfk_5` FOREIGN KEY (`approuve_par_id`) REFERENCES `user` (`id`);

--
-- Contraintes pour la table `notification_sms`
--
ALTER TABLE `notification_sms`
  ADD CONSTRAINT `notification_sms_ibfk_1` FOREIGN KEY (`technicien_id`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `notification_sms_ibfk_2` FOREIGN KEY (`demande_id`) REFERENCES `demande_intervention` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `produits`
--
ALTER TABLE `produits`
  ADD CONSTRAINT `produits_ibfk_1` FOREIGN KEY (`categorie_id`) REFERENCES `categorie` (`id`),
  ADD CONSTRAINT `produits_ibfk_2` FOREIGN KEY (`emplacement_id`) REFERENCES `emplacement_stock` (`id`),
  ADD CONSTRAINT `produits_ibfk_3` FOREIGN KEY (`fournisseur_id`) REFERENCES `fournisseur` (`id`);

--
-- Contraintes pour la table `reservation_piece`
--
ALTER TABLE `reservation_piece`
  ADD CONSTRAINT `reservation_piece_ibfk_1` FOREIGN KEY (`intervention_id`) REFERENCES `intervention` (`id`),
  ADD CONSTRAINT `reservation_piece_ibfk_2` FOREIGN KEY (`produit_id`) REFERENCES `produits` (`id`),
  ADD CONSTRAINT `reservation_piece_ibfk_3` FOREIGN KEY (`utilisateur_id`) REFERENCES `user` (`id`);

--
-- Contraintes pour la table `survey`
--
ALTER TABLE `survey`
  ADD CONSTRAINT `survey_ibfk_1` FOREIGN KEY (`intervention_id`) REFERENCES `intervention` (`id`);

--
-- Contraintes pour la table `user_connection_log`
--
ALTER TABLE `user_connection_log`
  ADD CONSTRAINT `user_connection_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
