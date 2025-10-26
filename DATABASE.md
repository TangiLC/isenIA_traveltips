# Schéma de la Base de Données TravelTips

## Vue d'ensemble

Base de données MySQL pour une application de conseils de voyage, incluant des informations sur les pays, langues, monnaies, normes électriques, villes et météo.

---

## Tables Principales

### Utilisateurs

**Authentification et autorisation**

| Colonne    | Type                 | Contraintes              | Description        |
| ---------- | -------------------- | ------------------------ | ------------------ |
| `id`       | INT                  | PK, AUTO_INCREMENT       | Identifiant unique |
| `pseudo`   | VARCHAR(255)         | NOT NULL, UNIQUE         | Nom d'utilisateur  |
| `password` | VARCHAR(255)         | NOT NULL                 | Mot de passe hashé |
| `role`     | ENUM('admin','user') | NOT NULL, DEFAULT 'user' | Rôle utilisateur   |

---

### Familles

**Familles linguistiques**

| Colonne      | Type        | Contraintes        | Description        |
| ------------ | ----------- | ------------------ | ------------------ |
| `id`         | INT         | PK, AUTO_INCREMENT | Identifiant unique |
| `branche_en` | VARCHAR(40) | NOT NULL, UNIQUE   | Nom en anglais     |
| `branche_fr` | VARCHAR(40) | NOT NULL, UNIQUE   | Nom en français    |

**Données incluses :** 26 familles linguistiques (Indo-Européenne, Sino-Tibétaine, Afro-Asiatique, etc.)

---

### Langues

**Langues mondiales (ISO 639-2)**

| Colonne      | Type         | Contraintes       | Description          |
| ------------ | ------------ | ----------------- | -------------------- |
| `iso639_2`   | CHAR(3)      | PK                | Code ISO 639-2       |
| `name_en`    | VARCHAR(100) | NOT NULL          | Nom en anglais       |
| `name_fr`    | VARCHAR(100) | NOT NULL          | Nom en français      |
| `name_local` | VARCHAR(100) | NOT NULL          | Nom local            |
| `famille_id` | INT          | FK → Familles(id) | Famille linguistique |

**Index :** `idx_famille`

**Relations :**

- `famille_id` → Familles(id) - ON DELETE SET NULL

**Données incluses :** 180+ langues parlées dans le monde (nom, code iso, famille)

---

### Pays

**Pays du monde (ISO 3166)**

| Colonne      | Type         | Contraintes      | Description             |
| ------------ | ------------ | ---------------- | ----------------------- |
| `iso3166a2`  | CHAR(2)      | PK               | Code ISO 3166-1 alpha-2 |
| `iso3166a3`  | CHAR(3)      | NOT NULL, UNIQUE | Code ISO 3166-1 alpha-3 |
| `name_en`    | VARCHAR(100) | NOT NULL         | Nom en anglais          |
| `name_fr`    | VARCHAR(100) | NOT NULL         | Nom en français         |
| `name_local` | VARCHAR(100) | NOT NULL         | Nom local               |
| `lat`        | DECIMAL(8,5) | NULL             | Latitude                |
| `lng`        | DECIMAL(8,5) | NULL             | Longitude               |

**Données incluses :** 190+ pays (nom, code iso, position)

---

### Monnaies

**Devises mondiales (ISO 4217)**

| Colonne   | Type         | Contraintes | Description             |
| --------- | ------------ | ----------- | ----------------------- |
| `iso4217` | CHAR(3)      | PK          | Code ISO 4217           |
| `name`    | VARCHAR(100) | NOT NULL    | Nom de la devise        |
| `symbol`  | VARCHAR(10)  | NOT NULL    | Symbole ($, €, £, etc.) |

**Données incluses :** 140+ Monnaies en cours dans les pays (nom, symbole, code iso)

---

### Electricite

**Types de prises électriques**

| Colonne     | Type        | Contraintes | Description              |
| ----------- | ----------- | ----------- | ------------------------ |
| `plug_type` | CHAR(1)     | PK          | Type de prise (A-O)      |
| `plug_png`  | VARCHAR(10) | NOT NULL    | Nom fichier image prise  |
| `sock_png`  | VARCHAR(10) | NOT NULL    | Nom fichier image socket |

**Données incluses :** Les 15 types normées de prises électriques mondiales, avec lien vers fichier png

---

### Villes

**Villes mondiales (GeoNames)**

| Colonne          | Type         | Contraintes          | Description    |
| ---------------- | ------------ | -------------------- | -------------- |
| `geoname_id`     | INT UNSIGNED | PK                   | ID GeoNames    |
| `name_en`        | VARCHAR(100) | NOT NULL             | Nom en anglais |
| `latitude`       | FLOAT        | NULL                 | Latitude       |
| `longitude`      | FLOAT        | NULL                 | Longitude      |
| `country_3166a2` | VARCHAR(2)   | FK → Pays(iso3166a2) | Code pays      |
| `is_capital`     | BOOLEAN      | DEFAULT FALSE        | Est capitale ? |

**Index :** `idx_villes_country`

**Relations :**

- `country_3166a2` → Pays(iso3166a2) - ON DELETE SET NULL

**Données incluses :** ~700 Villes dans le monde -Capitale +4 villes principales /pays-(geonameid, position, nom, pays)

---

### Meteo_Weekly

**Données météo hebdomadaires par ville**

| Colonne               | Type         | Contraintes             | Description             |
| --------------------- | ------------ | ----------------------- | ----------------------- |
| `id`                  | INT UNSIGNED | PK, AUTO_INCREMENT      | Identifiant unique      |
| `geoname_id`          | INT UNSIGNED | FK → Villes(geoname_id) | Ville concernée         |
| `week_start_date`     | DATE         | NOT NULL                | Début de semaine        |
| `week_end_date`       | DATE         | NOT NULL                | Fin de semaine          |
| `temperature_max_avg` | DECIMAL(5,2) | NULL                    | Température max moyenne |
| `temperature_min_avg` | DECIMAL(5,2) | NULL                    | Température min moyenne |
| `precipitation_sum`   | DECIMAL(7,2) | NULL                    | Précipitations totales  |

**Index :** `idx_week_dates`, `unique_location_week`

**Relations :**

- `geoname_id` → Villes(geoname_id) - ON DELETE CASCADE

**Données incluses :** 45.000+ données météo bi-hebdomadaires pour les villes sur l'année 2024 (température min, max, précipitation)

---

### Credits

**Sources de données**

| Colonne          | Type         | Contraintes | Description           |
| ---------------- | ------------ | ----------- | --------------------- |
| `target_element` | VARCHAR(20)  | PK          | Élément concerné      |
| `source_element` | VARCHAR(100) | NOT NULL    | Description source    |
| `source_type`    | VARCHAR(40)  | NOT NULL    | Type (CSV, API, etc.) |
| `source_url`     | VARCHAR(100) | NOT NULL    | URL de la source      |

**Données incluses :** Cette base est un rappel pour les sources libres.

---

## Tables de Liaison (N:N)

### Pays_Langues

**Langues parlées par pays**

| Colonne             | Type    | Contraintes      |
| ------------------- | ------- | ---------------- |
| `country_iso3166a2` | CHAR(2) | PK, FK → Pays    |
| `iso639_2`          | CHAR(3) | PK, FK → Langues |

**Relations :**

- ON DELETE CASCADE (pays)
- ON DELETE RESTRICT (langue)

- Relation de plusieurs à plusieurs (N:N) entre Pays et langues

---

### Pays_Borders

**Frontières terrestres entre pays**

| Colonne             | Type    | Contraintes   |
| ------------------- | ------- | ------------- |
| `country_iso3166a2` | CHAR(2) | PK, FK → Pays |
| `border_iso3166a2`  | CHAR(2) | PK, FK → Pays |

**Note :** Insertion en ordre alphabétique pour éviter les doublons symétriques (ex: FR-ES / ES-FR)

- Relation de plusieurs à plusieurs (N:N) entre Pays et Pays (auto-référencement)

---

### Pays_Monnaies

**Devises utilisées par pays**

| Colonne             | Type    | Contraintes       |
| ------------------- | ------- | ----------------- |
| `country_iso3166a2` | CHAR(2) | PK, FK → Pays     |
| `currency_iso4217`  | CHAR(3) | PK, FK → Monnaies |

**Relations :**

- ON DELETE CASCADE (pays)
- ON DELETE RESTRICT (monnaie)

- Relation de plusieurs à plusieurs (N:N) entre Monnaie et Pays

---

### Pays_Electricite

**Normes électriques par pays**

| Colonne             | Type        | Contraintes          | Description            |
| ------------------- | ----------- | -------------------- | ---------------------- |
| `country_iso3166a2` | CHAR(2)     | PK, FK → Pays        | Code pays              |
| `plug_type`         | CHAR(1)     | PK, FK → Electricite | Type de prise          |
| `voltage`           | VARCHAR(20) | NULL                 | Voltage (ex: "220V")   |
| `frequency`         | VARCHAR(20) | NULL                 | Fréquence (ex: "50Hz") |

**Relations :**

- ON DELETE CASCADE (pays)
- ON DELETE RESTRICT (électricité)

- Relation de plusieurs à plusieurs (N:N) entre Norme électrique et Pays. Info supplémentaire : voltage, fréquence

---

## Diagramme des Relations

![Diagramme de la base de données](./src/static/assets/schema_bdd.png)

---

## Sources de Données

| Élément                | Source                | Type     | URL                       |
| ---------------------- | --------------------- | -------- | ------------------------- |
| Familles linguistiques | BDD locale            | MySQL    | local                     |
| Langues ISO 639-2      | GitHub (haliaeetus)   | CSV      | iso-639 repository        |
| Pays ISO 3166          | stefangabos.github.io | JSON     | Countries data            |
| Drapeaux               | stefangabos.github.io | PNG      | 48x48 flags               |
| Données pays           | mledoze/countries     | YML      | GitHub                    |
| Monnaies               | apicountries.com      | API      | Alpha endpoint            |
| Normes électriques     | IEC / World Standards | Scraping | iec.ch, worldstandards.eu |
| Villes                 | GeoNames              | TXT      | cities15000.zip           |
| Capitales              | REST Countries        | API      | restcountries.com         |
| Météo                  | Open-Meteo Archive    | API      | open-meteo.com            |
| Conversations          | Google Sheets         | CSV      | Phrases types             |

---

## Configuration Technique

- **Moteur :** InnoDB
- **Charset :** utf8mb4
- **Collation :** utf8mb4_unicode_ci
- **ON DELETE :** CASCADE (liaisons) / SET NULL (références optionnelles) / RESTRICT (données référentielles)
- **ON UPDATE :** CASCADE (propagation des modifications)
