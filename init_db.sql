-- ============================================================================
-- Script d'initialisation de la base de données FPMsigm | Inspections
-- ============================================================================

-- Création de la base de données
CREATE DATABASE IF NOT EXISTS fpm_inspections
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE fpm_inspections;

-- ============================================================================
-- TABLE: analysis_log
-- Historique des analyses effectuées
-- ============================================================================
CREATE TABLE IF NOT EXISTS analysis_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom_utilisateur VARCHAR(100) NOT NULL COMMENT 'Nom de l''utilisateur ayant effectué l''analyse',
    intitule VARCHAR(255) NOT NULL COMMENT 'Titre de l''analyse',
    motif TEXT COMMENT 'Motif / Commentaire de l''analyse',
    scenario_id INT NOT NULL COMMENT 'ID du scénario utilisé (1, 2, 3...)',
    parametres JSON COMMENT 'Paramètres de recherche utilisés (JSON)',
    metriques JSON COMMENT 'Métriques calculées (total actes, montant, etc.)',
    date_analyse DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Date et heure de l''analyse',

    INDEX idx_date (date_analyse),
    INDEX idx_scenario (scenario_id),
    INDEX idx_utilisateur (nom_utilisateur)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Historique des analyses DICT';

-- ============================================================================
-- TABLES DE DONNÉES MÉDICALES (EXEMPLES)
-- À adapter selon votre schéma existant
-- ============================================================================

-- Structure de santé
CREATE TABLE IF NOT EXISTS structure_sante (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    nom_structure VARCHAR(255) NOT NULL,
    type_structure VARCHAR(100) COMMENT 'Hôpital, Clinique, Centre de santé, etc.',
    region VARCHAR(100),
    ville VARCHAR(100),
    actif BOOLEAN DEFAULT TRUE,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_code (code),
    INDEX idx_nom (nom_structure),
    INDEX idx_type (type_structure)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Structures de santé exécutantes';

-- Prise en charge (PEC / Dossier)
CREATE TABLE IF NOT EXISTS pec (
    id INT AUTO_INCREMENT PRIMARY KEY,
    num_pec VARCHAR(50) UNIQUE NOT NULL COMMENT 'Numéro de prise en charge',
    adherent_id INT COMMENT 'ID de l''adhérent (référence externe)',
    date_ouverture DATE,
    date_cloture DATE,
    statut VARCHAR(50) DEFAULT 'OUVERT' COMMENT 'OUVERT, CLOS, SUSPENDU',
    montant_total DECIMAL(14, 2) DEFAULT 0,

    INDEX idx_num_pec (num_pec),
    INDEX idx_adherent (adherent_id),
    INDEX idx_statut (statut),
    INDEX idx_date_ouverture (date_ouverture)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Dossiers de prise en charge';

-- Actes médicaux exécutés
CREATE TABLE IF NOT EXISTS acte_trans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pec_id INT NOT NULL COMMENT 'Référence au dossier PEC',
    structure_id INT NOT NULL COMMENT 'Structure ayant exécuté l''acte',
    date_execution DATE NOT NULL COMMENT 'Date d''exécution de l''acte',
    code_acte VARCHAR(50) COMMENT 'Code de l''acte médical',
    libelle_acte VARCHAR(255) COMMENT 'Libellé de l''acte',
    montant_demande DECIMAL(14, 2) COMMENT 'Montant demandé',
    montant_execute DECIMAL(14, 2) NOT NULL COMMENT 'Montant réellement exécuté',
    quantite INT DEFAULT 1,
    statut VARCHAR(50) DEFAULT 'VALIDE' COMMENT 'VALIDE, REJETE, EN_CONTROLE',
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_pec (pec_id),
    INDEX idx_structure (structure_id),
    INDEX idx_date_execution (date_execution),
    INDEX idx_montant (montant_execute),
    INDEX idx_statut (statut),

    FOREIGN KEY (pec_id) REFERENCES pec(id) ON DELETE CASCADE,
    FOREIGN KEY (structure_id) REFERENCES structure_sante(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Actes médicaux exécutés';

-- ============================================================================
-- DONNÉES DE TEST (OPTIONNEL)
-- ============================================================================

-- Insertion de structures de santé de test
INSERT INTO structure_sante (code, nom_structure, type_structure, region, ville) VALUES
('STRUCT001', 'Hôpital Central de Cotonou', 'Hôpital', 'Littoral', 'Cotonou'),
('STRUCT002', 'Clinique Saint-Luc', 'Clinique', 'Littoral', 'Cotonou'),
('STRUCT003', 'Centre de Santé de Godomey', 'Centre de santé', 'Atlantique', 'Godomey'),
('STRUCT004', 'Polyclinique les Cocotiers', 'Polyclinique', 'Littoral', 'Cotonou'),
('STRUCT005', 'Hôpital de Zone de Parakou', 'Hôpital', 'Borgou', 'Parakou');

-- Insertion de PEC de test
INSERT INTO pec (num_pec, adherent_id, date_ouverture, statut) VALUES
('PEC-2024-001', 1001, '2024-01-15', 'CLOS'),
('PEC-2024-002', 1002, '2024-02-10', 'CLOS'),
('PEC-2024-003', 1003, '2024-03-05', 'OUVERT'),
('PEC-2024-004', 1004, '2024-03-20', 'OUVERT'),
('PEC-2024-005', 1005, '2024-04-01', 'OUVERT');

-- Insertion d'actes de test
INSERT INTO acte_trans (pec_id, structure_id, date_execution, code_acte, libelle_acte, montant_demande, montant_execute, quantite) VALUES
-- PEC-2024-001
(1, 1, '2024-01-16', 'CONS001', 'Consultation générale', 5000, 5000, 1),
(1, 1, '2024-01-16', 'EXAM001', 'Examen radiologique', 15000, 15000, 1),
(1, 2, '2024-01-18', 'LABO001', 'Analyse sanguine', 8000, 8000, 1),

-- PEC-2024-002
(2, 3, '2024-02-11', 'CONS001', 'Consultation générale', 5000, 5000, 1),
(2, 3, '2024-02-11', 'MED001', 'Médicaments', 25000, 22000, 1),

-- PEC-2024-003
(3, 4, '2024-03-06', 'CONS002', 'Consultation spécialisée', 10000, 10000, 1),
(3, 4, '2024-03-07', 'CHIR001', 'Intervention chirurgicale mineure', 150000, 150000, 1),

-- PEC-2024-004
(4, 5, '2024-03-21', 'HOSP001', 'Hospitalisation', 50000, 50000, 3),
(4, 5, '2024-03-22', 'EXAM002', 'Scanner', 45000, 45000, 1),

-- PEC-2024-005
(5, 1, '2024-04-02', 'CONS001', 'Consultation générale', 5000, 5000, 1),
(5, 2, '2024-04-03', 'LABO002', 'Test COVID-19', 12000, 12000, 1);

-- ============================================================================
-- VUES UTILES (OPTIONNEL)
-- ============================================================================

-- Vue: Synthèse par structure
CREATE OR REPLACE VIEW v_synthese_structure AS
SELECT
    s.id AS structure_id,
    s.nom_structure,
    s.type_structure,
    COUNT(DISTINCT a.pec_id) AS nb_dossiers,
    COUNT(a.id) AS nb_actes,
    SUM(a.montant_execute) AS montant_total,
    AVG(a.montant_execute) AS montant_moyen,
    MIN(a.date_execution) AS premiere_date,
    MAX(a.date_execution) AS derniere_date
FROM structure_sante s
LEFT JOIN acte_trans a ON s.id = a.structure_id
GROUP BY s.id, s.nom_structure, s.type_structure;

-- Vue: Synthèse par PEC
CREATE OR REPLACE VIEW v_synthese_pec AS
SELECT
    p.id AS pec_id,
    p.num_pec,
    p.adherent_id,
    p.statut,
    COUNT(a.id) AS nb_actes,
    SUM(a.montant_execute) AS montant_total,
    MIN(a.date_execution) AS premiere_date,
    MAX(a.date_execution) AS derniere_date
FROM pec p
LEFT JOIN acte_trans a ON p.id = a.pec_id
GROUP BY p.id, p.num_pec, p.adherent_id, p.statut;

-- ============================================================================
-- PROCÉDURES STOCKÉES UTILES (OPTIONNEL)
-- ============================================================================

DELIMITER //

-- Procédure: Nettoyage des logs anciens
CREATE PROCEDURE sp_clean_old_logs(IN jours_retention INT)
BEGIN
    DELETE FROM analysis_log
    WHERE date_analyse < DATE_SUB(NOW(), INTERVAL jours_retention DAY);

    SELECT ROW_COUNT() AS lignes_supprimees;
END //

DELIMITER ;

-- ============================================================================
-- PERMISSIONS (À ADAPTER SELON VOS BESOINS)
-- ============================================================================

-- Exemple: Créer un utilisateur en lecture seule pour l'application
-- CREATE USER 'fpm_app'@'localhost' IDENTIFIED BY 'mot_de_passe_securise';
-- GRANT SELECT ON fpm_inspections.* TO 'fpm_app'@'localhost';
-- GRANT INSERT, UPDATE ON fpm_inspections.analysis_log TO 'fpm_app'@'localhost';
-- FLUSH PRIVILEGES;

-- ============================================================================
-- FIN DU SCRIPT
-- ============================================================================

SELECT 'Base de données initialisée avec succès!' AS message;
