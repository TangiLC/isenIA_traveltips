# Sources des Données

Ce document référence toutes les sources de données utilisées dans le projet, leurs formats, licences et contraintes d'utilisation.

---

## Vue d'ensemble

| Catégorie              | Source                | Format   | Méthode  |
| ---------------------- | --------------------- | -------- | -------- |
| Langues                | ISO 639-2             | CSV      | Import   |
| Pays                   | ISO 3166 + mledoze    | JSON/YML | Import   |
| Drapeaux               | Stefan Gabos          | PNG      | Import   |
| Monnaies               | API Countries         | API      | Requête  |
| Électricité            | IEC + World Standards | HTML     | Scraping |
| Villes                 | GeoNames              | TXT      | Import   |
| Capitales              | REST Countries        | API      | Requête  |
| Météo                  | Open-Meteo            | API      | Requête  |
| Conversations          | Refugee Phrasebook    | CSV      | Import   |
| Familles Linguistiques | Base locale           | MySQL    | Requête  |

---

## Données Géographiques

### Pays (ISO 3166)

**Codes et noms des pays**

- **Source** : https://stefangabos.github.io/
- **Format** : JSON
- **Fichier** : `countries_stefangabos.json`
- **Contenu** : Codes ISO 3166 alpha-2 et noms en français
- **ETL** : `etl_countries.py`

**Métadonnées étendues**

- **Source** : https://github.com/mledoze/countries
- **Format** : YAML
- **Fichier** : `countries_mledoze.yml`
- **Contenu** : Monnaies, langues, frontières, coordonnées, noms locaux
- **ETL** : `etl_countries.py`

**Drapeaux (48x48px)**

- **Source** : https://stefangabos.github.io/ + icondrawer.com
- **Format** : PNG
- **Résolution** : 48×48 pixels
- **Naming** : `{ISO_alpha2}.png`
- **ETL** : Import manuel dans `/src/static/assets/flags/`

### Villes

**Base de données GeoNames**

- **Source** : https://download.geonames.org/export/dump/cities15000.zip
- **Format** : TXT (tab-separated)
- **Fichier** : `cities15000.txt`
- **Contenu** :
  - geoname_id (identifiant unique)
  - Noms (anglais, ASCII, alternatifs)
  - Coordonnées (latitude, longitude)
  - Codes pays, population
- **Critères** : Base exhaustive de villes à population significative
- **Traitement** : Filtrage sur top 4 villes par pays (dont capitale)
- **ETL** : `etl_villes.py`
- **Licence** : Creative Commons Attribution 4.0

**Capitales**

- **Source** : https://restcountries.com/v3.1/alpha/{code}?fields=capital
- **Format** : API REST JSON
- **Méthode** : Requête GET par code pays ISO alpha-2
- **Rate Limit** : Politesse (20ms entre requêtes)
- **ETL** : `etl_villes.py` (enrichissement)

---

## Données Économiques

### Monnaies (ISO 4217)

- **Source** : https://www.apicountries.com/alpha
- **Format** : API REST JSON
- **Endpoint** : `GET /alpha/{code_iso_alpha2}`
- **Contenu** :
  - Code ISO 4217 (ex: EUR, USD)
  - Nom complet (ex: Euro, Dollard US)
  - Symbole (ex: €, $)
- **Rate Limit** : 100ms entre requêtes (politesse)
- **ETL** : `etl_currencies.py`
- **Documentation** : https://www.apicountries.com/docs/api

---

## Données Linguistiques

### Langues (ISO 639-2)

- **Source** : https://github.com/haliaeetus/iso-639/tree/master/data
- **Format** : CSV
- **Fichiers** :
  - `iso_639-1.csv` (codes à 2 lettres)
  - `iso_639-2.csv` (codes à 3 lettres)
- **Contenu** :
  - Codes ISO 639-2 (3 lettres)
  - Noms en anglais, français, natif
  - Famille linguistique
- **Traitement** :
  - Fusion des deux fichiers sur clé `639-2`
  - Dédoublonnage
  - Normalisation (valeurs multiples → première valeur)
- **ETL** : `etl_langues.py`
- **Licence** : MIT

### Familles Linguistiques

- **Source** : Base de données locale (dérivée des données ISO 639)
- **Format** : MySQL
- **Table** : `Familles`
- **Relation** : 1:N avec `Langues` (clé étrangère `famille_id`)
- **Méthode** : Extraction et insertion automatique
- **Contenu** :
  - Identifiants uniques (PRIMARY KEY AUTO_INCREMENT)
  - Noms en anglais des branches (ex: Indo-European, Sino-Tibetan)
- **Origine** : Extrait du champ `family` des fichiers ISO 639-2
- **Traitement** :
  - Extraction des valeurs uniques de `family`
  - Normalisation des noms
  - Insertion dans `Langue_Branche`
  - Mise à jour de la FK `branche_id` dans `Langues`
- **Contrainte** : NOT NULL (toutes les langues ont une famille)
- **ETL** : Phase LOAD de `etl_langues.py`
- **Usage** : Classification et filtrage des langues par famille linguistique

### Conversations Multilingues

- **Source** : Refugee Phrasebook
- **URL** : https://docs.google.com/spreadsheets/d/1hVa7vtHCc7WGkf0idxU0j5YWX0eX0jzavMR5GncG-nU
- **Format** : CSV (sauvegarde locale)
- **Fichier** : `RPB Main Phrases.csv`
- **Contenu** : Phrases types traduites dans ~80 langues
- **Contexte** : Outil d'aide aux réfugiés pour communication de base
- **Traitement** :
  - Transposition (langues en lignes)
  - Filtrage lignes vides (>85% NaN)
  - Validation codes ISO 639-2
- **Storage** : MongoDB (`conversations` collection)
- **ETL** : `etl_conversations.py`
- **Attribution** : Refugee Phrasebook Project

---

## Données Électriques

### Normes par Pays

- **Source** : https://www.worldstandards.eu/electricity/plug-voltage-by-country/
- **Format** : HTML (scraping)
- **Méthode** : BeautifulSoup sur table `#tablepress-1`
- **Contenu** :
  - Types de prises (A, B, C, ..., N)
  - Voltage (ex: 230V, 110V / 220V)
  - Fréquence (50Hz, 60Hz)
- **Traitement** :
  - Extraction avant "(note...)"
  - Suppression parenthèses
  - Normalisation espaces
- **ETL** : `elec_scrap2.py`
- **Output** : `normes_elec_pays.csv`

### Types de Prises (Images)

- **Source** : https://www.iec.ch/world-plugs
- **Format** : HTML (scraping) + PNG download
- **Méthode** : BeautifulSoup + requests avec Referer
- **Contenu** :
  - Images 3D des prises (plug)
  - Images 3D des sockets (sock)
- **Assets** : `/src/static/assets/elec/{TYPE}_{plug|sock}.png`
- **Traitement** :
  - Retry logic (3 tentatives)
  - Session cookies persistante
  - Rate limiting (400ms)
- **ETL** : `etl_elec1.py`
- **Organisation** : IEC (International Electrotechnical Commission)

---

## Données Météorologiques

### Historique Météo 2024

- **Source** : Open-Meteo Archive API
- **URL** : https://archive-api.open-meteo.com/v1/archive
- **Format** : API REST JSON
- **Période** : 1er janvier 2024 → 31 décembre 2024
- **Granularité** : Quotidienne (daily)
- **Variables** :
  - `temperature_2m_max` (°C)
  - `temperature_2m_min` (°C)
  - `precipitation_sum` (mm)
- **Traitement** :
  - Agrégation glissante sur 14 jours
  - Échantillonnage par semaine ISO
  - Calcul week_start_date et week_end_date
- **Contraintes API** :
  - Rate limit : < 10,000 requêtes/jour
  - Politesse : 350ms entre requêtes (50 requêtes /min)
  - Batch : 40 villes par batch avec sleep(5s)
  - Retry : 3 tentatives avec backoff exponentiel
- **ETL** : `etl_meteo.py`
- **Storage** : MySQL (`Meteo_Weekly` table)
- **Licence** : CC BY 4.0 (Attribution requise)
- **Attribution** : "Weather data by Open-Meteo.com"

---

## Architecture ETL

### Pipeline d'Exécution

```
Phase 1 (parallèle) : Currencies + Langues
                      Scraping Électricité + Conversations
                      ↓
Phase 2 (séquentiel): Plug Types (images)
                      ↓
Phase 3 (séquentiel): Villes
                      ↓
Phase 4 (séquentiel): Countries (agrégation finale)
                      ↓
Phase 5 (séquentiel): Météo
```

### Orchestration

- **Script** : `main_etl.py`
- **Multithreading** : 2×2 threads pour ETL indépendants
- **Gestion erreurs** : Continue en cas d'échec (logging)
- **Durée estimée** : ~20 min (dépend de l'accès API météo)

---

## Licences et Crédits

### Licences Globales

- **Projet** : Non commercial (usage éducatif)
- **Données** : Principalement licences ouvertes (MIT, CC BY 4.0)
- **Attribution** : Crédits stockés en base de données et affichés en frontend

### Crédits Spécifiques

Les crédits sont gérés via la table `Credits` :

```sql
CREATE TABLE Credits (
    id INT PRIMARY KEY AUTO_INCREMENT,
    target_element VARCHAR(50),
    source_element VARCHAR(100),
    source_type VARCHAR(20),
    source_url TEXT
);
```

**Sources créditées** :

- ISO 639-2 (haliaeetus/iso-639)
- Familles linguistiques (dérivées ISO 639)
- Stefan Gabos (country data + flags)
- mledoze/countries
- API Countries
- IEC World Plugs
- World Standards EU
- GeoNames
- REST Countries
- Open-Meteo
- Refugee Phrasebook

---

## Maintenance

### Fréquence de Mise à Jour

**Aucune mise à jour automatique prévue.**

Les données sont chargées ponctuellement lors de l'initialisation de la base de données. Pour mettre à jour :

1. Télécharger les nouvelles sources
2. Placer dans `/raw_sources/`
3. Exécuter `python3 main_etl.py`

### Vérification des Sources

Avant une mise à jour majeure, vérifier :

- URLs des sources toujours actives
- Formats de données inchangés
- Licences toujours valides
- Rate limits API respectés

---

- Vérifier d'abord la documentation des sources originales
- Consulter les issues des repositories GitHub cités
- Pour Open-Meteo : https://open-meteo.com/en/docs

---

**Dernière mise à jour** : Octobre 2025  
**Version du pipeline ETL** : 1.0
