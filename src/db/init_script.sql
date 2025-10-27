-- Script d'initialisation pour la base de données traveltips
-- Tables : Famille et Langue

-- Sélection de la base de données
USE traveltips;

-- ============================================
-- Table Utilisateurs (pour la sécurité JWT)
-- ============================================
CREATE TABLE IF NOT EXISTS Utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pseudo VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','user') NOT NULL DEFAULT 'user'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Table Famille
-- ============================================
CREATE TABLE IF NOT EXISTS Familles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    branche_en VARCHAR(40) NOT NULL UNIQUE,
    branche_fr VARCHAR(40) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Table Langue
-- ============================================
CREATE TABLE IF NOT EXISTS Langues (
    iso639_2 CHAR(3) PRIMARY KEY,
    name_en VARCHAR(100) NOT NULL,
    name_fr VARCHAR(100) NOT NULL,
    name_local VARCHAR(100) NOT NULL,
    famille_id INT,
    is_in_mongo BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_langue_famille 
        FOREIGN KEY (famille_id) 
        REFERENCES Familles(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    INDEX idx_famille (famille_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Table Monnaies
-- ============================================
CREATE TABLE IF NOT EXISTS Monnaies (
    iso4217 CHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================
-- Table Electricité
-- ============================================
CREATE TABLE IF NOT EXISTS Electricite (
    plug_type CHAR(1) PRIMARY KEY,
    plug_png VARCHAR(10) NOT NULL,
    sock_png VARCHAR(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================
-- Table Villes
-- ============================================
CREATE TABLE IF NOT EXISTS Villes (
    geoname_id INT UNSIGNED PRIMARY KEY NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    country_3166a2 VARCHAR(2) NULL,
    is_capital BOOLEAN DEFAULT FALSE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Table Météo hebdomadaire par Villes
-- ============================================
CREATE TABLE IF NOT EXISTS Meteo_Weekly (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    geoname_id INT UNSIGNED NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    temperature_max_avg DECIMAL(5,2),
    temperature_min_avg DECIMAL(5,2),
    precipitation_sum DECIMAL(7,2),
        
    FOREIGN KEY (geoname_id) REFERENCES Villes(geoname_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    UNIQUE KEY unique_location_week (geoname_id, week_start_date),
    INDEX idx_week_dates (week_start_date, week_end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Sélection de la base
USE traveltips;

-- ============================================
-- Table Pays (ISO 3166-1 alpha-2 / alpha-3)
-- ============================================
CREATE TABLE IF NOT EXISTS Pays (
    iso3166a2 CHAR(2) PRIMARY KEY,                        
    iso3166a3 CHAR(3) NOT NULL UNIQUE,                     
    name_en    VARCHAR(100) NOT NULL,
    name_fr    VARCHAR(100) NOT NULL,
    name_local VARCHAR(100) NOT NULL,
    lat DECIMAL(8,5) NULL,                                 
    lng DECIMAL(8,5) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Liaisons : Pays <-> Langues (N:N)
-- ============================================
CREATE TABLE IF NOT EXISTS Pays_Langues (
    country_iso3166a2 CHAR(2) NOT NULL,
    iso639_2 CHAR(3) NOT NULL,
    PRIMARY KEY (country_iso3166a2, iso639_2),
    CONSTRAINT fk_pl_pays
        FOREIGN KEY (country_iso3166a2)
        REFERENCES Pays(iso3166a2)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_pl_langue
        FOREIGN KEY (iso639_2)
        REFERENCES Langues(iso639_2)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    INDEX idx_pl_langue (iso639_2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Liaisons : Pays <-> Pays (frontières N:N) 
-- Attention lors des insertions :
--   1) Interdire doublons fr=fr
--   2) Insérer dans l'ordre alphabétique pour
--      éviter la symétrie  es/fr X fr/es
-- ============================================
CREATE TABLE IF NOT EXISTS Pays_Borders (
    country_iso3166a2 CHAR(2) NOT NULL,
    border_iso3166a2  CHAR(2) NOT NULL,

    PRIMARY KEY (country_iso3166a2, border_iso3166a2),

    CONSTRAINT fk_pb_pays_self_a
        FOREIGN KEY (country_iso3166a2)
        REFERENCES Pays(iso3166a2)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_pb_pays_self_b
        FOREIGN KEY (border_iso3166a2)
        REFERENCES Pays(iso3166a2)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    INDEX idx_pb_border (border_iso3166a2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================
-- Liaisons : Pays <-> Monnaies (N:N)
-- ============================================
CREATE TABLE IF NOT EXISTS Pays_Monnaies (
    country_iso3166a2   CHAR(2) NOT NULL,
    currency_iso4217    CHAR(3) NOT NULL,
    PRIMARY KEY (country_iso3166a2, currency_iso4217),
    CONSTRAINT fk_pm_pays
        FOREIGN KEY (country_iso3166a2)
        REFERENCES Pays(iso3166a2)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_pm_monnaie
        FOREIGN KEY (currency_iso4217)
        REFERENCES Monnaies(iso4217)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    INDEX idx_pm_currency (currency_iso4217)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Liaisons : Pays <-> Electricité (N:N)
-- ============================================
CREATE TABLE IF NOT EXISTS Pays_Electricite (
    country_iso3166a2 CHAR(2) NOT NULL,
    plug_type CHAR(1) NOT NULL,             
    voltage   VARCHAR(20) NULL,             
    frequency VARCHAR(20) NULL,             
    PRIMARY KEY (country_iso3166a2, plug_type),
    CONSTRAINT fk_pe_pays
        FOREIGN KEY (country_iso3166a2)
        REFERENCES Pays(iso3166a2)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_pe_plug
        FOREIGN KEY (plug_type)
        REFERENCES Electricite(plug_type)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    INDEX idx_pe_plug (plug_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Table Credits
-- ============================================
CREATE TABLE IF NOT EXISTS Credits (
    target_element VARCHAR(20) PRIMARY KEY NOT NULL,
    source_element VARCHAR(100) NOT NULL,
    source_type VARCHAR(40) NOT NULL,
    source_url VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================
-- Données Utilisateurs
-- ============================================
-- Password hashé = 'pass123'
INSERT IGNORE INTO Utilisateurs (id,pseudo,password,role) VALUES
    (1,'Test_user','$2b$12$Y2xHClIe4bR6R7uloRTtQuXPbSZVVBYlYraB7DijGGLbeM.mnvp0C','admin');

-- ============================================
-- Données Crédits (pour info)
-- ============================================
INSERT IGNORE INTO Credits (target_element,source_element,source_type, source_url) VALUES
    ('Langue636.2','Langue (code iso 636-2)','CSV','https://github.com/haliaeetus/iso-639/tree/master/data'),
    ('Pays3166a2','Pays (code iso 3166) -Fr','JSON','https://stefangabos.github.io/'),
    ('Flags48','Pays (assets png 48x48)','PNG','https://stefangabos.github.io/'),
    ('Pays_data','Pays (multiples data)','YML','https://github.com/mledoze/countries'),
    ('Currency4217','Monnaie (nom, symbole, code)','API','https://www.apicountries.com/alpha'),
    ('Elec_type','Normes électriques (types, images)','SCRAP','https://www.iec.ch/world-plugs'),
    ('Elec_pays','Normes électriques (par pays)','SCRAP','https://www.worldstandards.eu/electricity/plug-voltage-by-country/'),
    ('Ville_geo','Villes (nom, geonameid, lat-long...)','TXT','https://download.geonames.org/export/dump/cities15000.zip'),
    ('Ville_capital','Capitales (nom)','API','https://restcountries.com/v3.1/alpha/{code}?fields=capital'),
    ('Ville_meteo','Météo hebdomadaire par ville (geonameid)','API','https://archive-api.open-meteo.com/v1/archive'),
    ('Conversations','Phrases types en langue locale','CSV','https://docs.google.com/spreadsheets/d/1hVa7vtHCc7WGkf0idxU0j5YWX0eX0jzavMR5GncG-nU'),
    ('Langue_famille','Familles linguistiques','MySQL','Base locale (dérivée ISO 639)');
    
    

-- ============================================
-- Données Famille (par ordre alphabétique)
-- ============================================
INSERT IGNORE INTO Familles (branche_en, branche_fr) VALUES
    ('Afro-Asiatic', 'afro-asiatique'), ('Algonquian', 'algonquienne'),
    ('Austroasiatic', 'austroasiatique'), ('Austronesian', 'austronésienne'),
    ('Aymaran', 'aymara'), ('Constructed', 'construite'),
    ('Creole', 'créole'), ('Dené–Yeniseian', 'déné-iénisséienne'),
    ('Dravidian', 'dravidienne'), ('Eskimo–Aleut', 'esquimaude-aléoute'),
    ('Indo-European', 'indo-européenne'), ('Japonic', 'japonique'),
    ('Koreanic', 'coréenne'), ('Language isolate', 'isolat linguistique'),
    ('Mongolic', 'mongole'), ('Niger–Congo', 'nigéro-congolaise'),
    ('Nilo-Saharan', 'nilo-saharienne'), ('Northeast Caucasian', 'caucasienne du nord-est'),
    ('Northwest Caucasian', 'caucasienne du nord-ouest'), ('Quechuan', 'quechua'),
    ('Sino-Tibetan', 'sino-tibétaine'), ('South Caucasian', 'caucasienne du sud'),
    ('Tai–Kadai', 'taï-kadaï'), ('Tupian', 'tupi'),
    ('Turkic', 'turque'), ('Uralic', 'ouralienne');

