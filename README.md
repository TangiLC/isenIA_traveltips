# TravelTips

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green.svg)
![Docker](https://img.shields.io/badge/Docker-compose-blue.svg)

> **Agrégateur de données touristiques multilingues**  
> Une API RESTful complète fournissant des informations essentielles pour voyageurs : pays, villes, météo, monnaies, normes électriques, langues et phrases utiles.

---

## Table des matières

- [Vue d'ensemble](#-vue-densemble)
- [Fonctionnalités](#-fonctionnalités)
- [Technologies](#-technologies)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Démarrage rapide](#-démarrage-rapide)
- [Utilisation](#-utilisation)
- [Structure de la base de données](#-structure-de-la-base-de-données)
- [API Endpoints](#-api-endpoints)
- [Sources de données](#-sources-de-données)
- [Licence](#-licence)

---

## Vue d'ensemble

**TravelTips** est un projet d'agrégation et d'exposition de données touristiques structurées, conçu pour faciliter l'accès à des informations essentielles lors de voyages internationaux. C'est un projet académique MVP développé dans le cadre du module Extraction, Transformation, Chargement (ETL) de la formation Développeur IA ISEN / Simplon.co.

Le système collecte, normalise et expose via une API RESTful des données provenant de multiples sources ouvertes :

- **190+ pays** avec métadonnées complètes (codes ISO, coordonnées, frontières)
- **700+ villes** principales (4 par pays dont capitales)
- **45.000+ Météo historique 2024 par ville** (agrégations bi-hebdomadaires)
- **200+ monnaies** (ISO 4217)
- **180+ langues** (ISO 639-2) avec familles linguistiques
- **15 types de prises électriques** (IEC A à O)
- **Phrases utiles** traduites dans ~40 langues

### Contexte du projet

Ce projet a été développé dans un contexte éducatif, inspiré par des ressources comme le **Refugee Phrasebook**, pour faciliter la communication interculturelle et la préparation de voyages.

---

## Fonctionnalités

### API Backend (FastAPI)

- **CRUD complet** sur toutes les ressources (pays, villes, langues, etc.)
- **Authentification JWT** avec gestion de tokens
- **Routes sécurisées** (GET publiques, PUT/PATCH/DELETE protégées)
- **Documentation OpenAPI** interactive (Swagger UI)
- **Recherche multicritères** (nom, code ISO, population, etc.)
- **Relations complexes** (frontières, langues parlées, monnaies)

### Frontend (Streamlit)

- Interface utilisateur intuitive
- Consultation des données par pays puis [Carte,Villes,Électricité,Langues,Monnaies]
- Visualisations météo et statistiques
- Guide de conversation (vocabulaire utiles)

### Pipeline ETL

- **Orchestration multithreadée** (phases parallèles et séquentielles)
- **Extraction** depuis APIs, scraping web, fichiers CSV/JSON/YAML/TXT, MySQL, MongoDB
- **Transformation** avec Pandas (nettoyage, normalisation, jointures)
- **Chargement** vers MySQL et MongoDB avec gestion d'erreurs

---

## Technologies

### Backend

| Technologie            | Usage                                   |
| ---------------------- | --------------------------------------- |
| **Python 3.11+**       | Langage principal                       |
| **FastAPI**            | Framework API RESTful                   |
| **Pydantic**           | Validation et sérialisation des données |
| **SQLAlchemy**         | ORM pour MySQL                          |
| **PyMongo**            | Client MongoDB                          |
| **PyJWT**              | Génération et validation JWT            |
| **bcrypt**             | Hashage de mots de passe                |
| **pandas**             | Manipulation de données (ETL)           |
| **requests**           | Appels HTTP (APIs externes)             |
| **BeautifulSoup4**     | Scraping web                            |
| **PyYAML**             | Parsing fichiers YAML                   |
| **openmeteo-requests** | Client API Open-Meteo                   |

### Frontend

| Technologie   | Usage                             |
| ------------- | --------------------------------- |
| **Streamlit** | Framework d'interface utilisateur |
| **requests**  | Communication avec l'API backend  |

### Bases de données

| Base            | Usage                                                 |
| --------------- | ----------------------------------------------------- |
| **MySQL 8.0**   | Données relationnelles (pays, villes, langues, météo) |
| **MongoDB 7.0** | Données semi-structurées (conversations multilingues) |

### DevOps

| Outil                       | Usage                              |
| --------------------------- | ---------------------------------- |
| **Docker & Docker Compose** | Containerisation des services      |
| **Adminer**                 | Interface d'administration MySQL   |
| **Mongo Express**           | Interface d'administration MongoDB |

### Documentation

| Outil       | Usage                               |
| ----------- | ----------------------------------- |
| **pdoc**    | Génération documentation API Python |
| **OpenAPI** | Documentation interactive FastAPI   |

---

## Architecture

### Arborescence du projet

```
TravelTips/
│
├── docker-compose.yml          # Orchestration des conteneurs (MySQL, MongoDB, Adminer, Mongo Express)
├── .env.template               # Template des variables d'environnement
├── .env                        # Variables d'environnement (ignoré par git)
├── requirements.txt            # Dépendances Python
├── LICENSE                     # Licence MIT
├── README.md                   # _Ce fichier_
├── RAW_SOURCES.md              # Documentation détaillée des sources
├── DATABASE.md                 # Schéma et structure de la base de données
├── API_ENDPOINTS.md            # Liste complète des endpoints
│
├── raw_sources/                # Fichiers sources bruts (CSV, JSON, YAML, TXT)
│   ├── countries_en.csv
│   ├── countries_stefangabos.json
│   ├── countries_mledoze.yml
│   ├── iso_639-1.csv
│   ├── iso_639-2.csv
│   ├── cities15000.txt
│   └── RPB Main Phrases.csv
│
└── src/
    │
    ├── main_etl.py             #  Point d'entrée ETL (population BDD)
    ├── main_multithread.py     #  Lancement simultané API + Frontend
    │
    ├── backend/
    │   ├── fastapi_main.py     #  Point d'entrée FastAPI
    │   ├── models/             # Modèles SQLAlchemy & MongoDB
    │   ├── schemas/            # Schémas Pydantic (validation)
    │   ├── routers/            # Routes API (endpoints)
    │   ├── services/           # ETL et logique métier
    │   ├── orms/               # Couche d'accès aux données
    │   ├── connexion/          # Gestion des connexions BDD
    │   ├── security/           # Authentification & autorisation
    │   └── utils/              # Utilitaires génériques
    ├── streamlit_front/
    │   ├── app.py              # Point d'entrée Streamlit
    │   ├── pages/              # Pages de l'interface
    │   ├── components/         # Composants réutilisables
    │   └── services/           # Requêtes vers l'API backend
    ├── db/
    │   ├── xx.csv              #  Archives des fichiers après traitement ETL
    │   ├── init_script.sql     #  Création initiale des tables
    │   └── alter_script.sql    #  Ajout des contraintes FK (après ETL)
    └── static/
        └── assets/
            ├── flags48/        # Drapeaux 48x48px (PNG)
            └── elec/           # Images prises électriques (PNG)
```

### Flux de données

```
┌────────────────────────────────────────────────────────┐
│                     SOURCES EXTERNES                   │
│  APIs · Scraping · CSV · JSON · YAML · TXT             │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│                    PIPELINE ETL                        │
│      ┌──────────┐    ┌───────────┐   ┌──────────┐      │
│      │ Extract  │──▶│ Transform │──▶│  Load    │      │
│      └──────────┘    └───────────┘   └──────────┘      │
│  • Multithreadé pour sources indépendantes             │
│  • Séquentiel pour dépendances                         │
│  • Gestion erreurs & logging                           │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│                  BASES DE DONNÉES                      │
│  ┌─────────────────────┐    ┌──────────────────────┐   │
│  │   MySQL 8.0         │    │   MongoDB 7.0        │   │
│  │  • Pays             │    │  • Conversations     │   │
│  │  • Villes           │    │    multilingues      │   │
│  │  • Langues          │    │                      │   │
│  │  • Monnaies         │    └──────────────────────┘   │
│  │  • Électricité      │                               │
│  │  • Météo            │                               │
│  └─────────────────────┘                               │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│                    API BACKEND                         │
│  FastAPI · JWT Auth · OpenAPI Docs                     │
│     ┌──────────┐    ┌──────────┐   ┌──────────┐        │
│     │ Routers  │──▶│ Services │──▶│   ORMs   │        │
│     └──────────┘    └──────────┘   └──────────┘        │
│         │                                              │
│         └─── Port 8000 (http://localhost:8000)         │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│                  FRONTEND STREAMLIT                    │
│  Interface utilisateur · Visualisations                │
│         Port 8501 (http://localhost:8501)              │
└────────────────────────────────────────────────────────┘
```

---

## Installation

### Prérequis

- **Python 3.11+** ([Télécharger](https://www.python.org/downloads/))
- **Docker & Docker Compose** ([Installation](https://docs.docker.com/get-docker/))
- **Git** (optionnel, pour cloner le projet)

### Étapes d'installation

#### 1. Cloner le repository

```bash
git clone https://github.com/TangiLC/traveltips.git
cd traveltips
```

#### 2. Créer et activer l'environnement virtuel

```bash
# Création
python3 -m venv .venv

# Activation (Linux/Mac)
source .venv/bin/activate

```

#### 3. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

#### 4. Configurer les variables d'environnement

```bash
# Copier le template
cp .env.template .env

# Éditer avec vos paramètres
nano .env
```

#### 5. Télécharger les sources de données

Vérifier la présence des fichiers suivants dans `/raw_sources/` :

- `countries_en.csv`
- `countries_stefangabos.json`
- `countries_mledoze.yml`
- `iso_639-1.csv`
- `iso_639-2.csv`
- `cities15000.txt`
- `RPB Main Phrases.csv`
- `currencies.json`

**Note** : Voir [RAW_SOURCES.md](./documentation/RAW_SOURCES.md) pour les liens de téléchargement.

#### 6. Lancer les conteneurs Docker

```bash
docker-compose up -d
```

Vérification :

```bash
docker-compose ps
```

Vous devriez voir 4 conteneurs actifs :

- `tt_mysql`
- `tt_mongo`
- `tt_admsql` (interface MySQL: Adminer)
- `tt_mgxp` (interface MongoDB: MongoExpress)

---

## Démarrage rapide

### 1. Peupler la base de données (ETL) Le script d'initialisation est lancé à la connexion

```bash
# Depuis /src
python main_etl.py
```

**Durée estimée** : 20 min (selon disponibilité de l'API météo)

**Phases d'exécution** :

1.  Phase 1 : ETL parallèles (Currencies, Langues, Électricité, Conversations)
2.  Phase 2 : Images prises électriques
3.  Phase 3 : Villes
4.  Phase 4 : Countries (agrégation)
5.  Phase 5 : Données Météo par villes x365j (longue durée)

### 2. Lancer l'application

**Option A : Tout en un (recommandé)**

```bash
# Depuis /src
python main_multithread.py
```

**Option B : Services séparés**

```bash
# Terminal 1 - API Backend
cd src/backend
uvicorn fastapi_main:app --reload --port 8000

# Terminal 2 - Frontend Streamlit
cd src/streamlit_front
streamlit run app.py --server.port 8501
```

### 3. Accéder aux interfaces

| Service                   | URL                        | Description             |
| ------------------------- | -------------------------- | ----------------------- |
| **API Backend**           | http://localhost:8000      | Endpoint racine         |
| **Documentation OpenAPI** | http://localhost:8000/docs | Swagger UI interactif   |
| **Frontend Streamlit**    | http://localhost:8501      | Interface utilisateur   |
| **Adminer (MySQL)**       | http://localhost:8080      | Interface admin MySQL   |
| **Mongo Express**         | http://localhost:8081      | Interface admin MongoDB |

---

## Utilisation

### Documentation API interactive

La documentation complète de l'API est accessible via **Swagger UI** à l'adresse :

**http://localhost:8000/docs**

Cette interface permet de :

- Visualiser tous les endpoints disponibles
- Tester les requêtes directement dans le navigateur
- Voir les schémas de données (request/response)
- Gérer l'authentification JWT

### Authentification

Les routes de modification (PUT, PATCH, DELETE) nécessitent un token JWT.

**Obtenir un token** :

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"pseudo": "votre_username", "password": "votre_password"}'
```

**Token en mode dev (sans passer par la table Utilisateurs)** :_cette route sera supprimée à l'avenir !_

```bash
curl -X GET "http://localhost:8000/api/auth/test_token" \
  -H "accept: application/json"
```

### Frontend Streamlit

L'interface Streamlit propose :

- **Exploration par pays, Onglet Carte** : Visualisation des données complètes
- **Onglet villes** : Météo, coordonnées
- **Onglet Langues** : Infos générales sur la langue, et vocabulaire utile (si présent en BDD)
- **Onglet Électricité** : Type de prise, voltage, fréquence
- **Onglet Monnaies** : Infos générales sur la monnaie en cours

---

## Structure de la base de données

Pour une description détaillée du schéma relationnel, des tables, contraintes et relations, consultez :

**[DATABASE.md](./documentation/DATABASE.md)**

**Résumé des principales tables** :

- `Pays` : Informations pays (ISO 3166)
- `Villes` : Villes principales avec coordonnées
- `Langues` : Codes ISO 639-2 et familles linguistiques
- `Monnaies` : Codes ISO 4217
- `Electricite` : Types de prises (IEC)
- `Meteo_Weekly` : Données météo hebdomadaires
- `Pays_Langues`, `Pays_Monnaies`, `Pays_Borders` : Tables de liaison
- Collection MongoDB `conversations` : Phrases multilingues

---

## API Endpoints

Pour la liste complète et détaillée de tous les endpoints, consultez :

**[API_ENDPOINTS.md](./documentation/API_ENDPOINTS.md)**

### Exemples de endpoints principaux

#### Pays

```http
GET  /api/countries/by_name/{name}      # Recherche par nom
GET  /api/countries/by_code/{code}      # Par code ISO alpha-2
GET  /api/countries/                    # Liste complète
POST /api/countries/                    # Création (sécurisé JWT)
PUT  /api/countries/{id}                # Modification (sécurisé JWT)
DELETE /api/countries/{id}              # Suppression (sécurisé JWT)
```

#### Authentification

```http
POST /api/auth/login                    # Connexion (username + password → JWT)
```

#### Langues

```http
GET  /api/langues/by_code_iso/{code}    # Par code ISO 639-2
GET  /api/langues/by_famille/{family}   # Par famille linguistique
```

#### Villes

```http
GET  /api/villes/by_name/{name}         # Recherche par nom
GET  /api/villes/by_country/{code}      # Villes d'un pays
GET  /api/villes/                       # Liste complète des villes en base
```

**Règle générale** :

- Routes **GET** : Publiques (lecture seule)
- Routes **POST/PUT/PATCH/DELETE** : Sécurisées (JWT requis)

---

## Sources de données

Ce projet agrège des données depuis multiples sources ouvertes (APIs, scraping, fichiers publics).

Pour la documentation complète des sources, licences et attributions :

**[RAW_SOURCES.md](./documentation/RAW_SOURCES.md)**

**Crédits principaux** :

- **Pays** : mledoze/countries, Stefan Gabos
- **Langues** : ISO 639 (haliaeetus/iso-639)
- **Villes** : GeoNames
- **Monnaies** : API Countries
- **Électricité** : IEC, World Standards EU
- **Météo** : Open-Meteo (CC BY 4.0)
- **Conversations** : Refugee Phrasebook

---

## Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](./LICENSE) pour plus de détails.

**Résumé** : Vous êtes libre d'utiliser, modifier et distribuer ce code, à condition de conserver l'attribution et la notice de licence.

---

## Remerciements

- Toutes les sources de données ouvertes et leurs mainteneurs
- La communauté FastAPI et Streamlit
- Le projet Refugee Phrasebook, Le projet RestCountries

---

**Développé avec ❤️ pour faciliter les voyages et la communication interculturelle**
