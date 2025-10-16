# Projet TravelTips

## Contexte

Ce projet est un agrégateur de données, avec création d’une base de données alimentée par différentes sources, et exposée à travers une API.  
La donnée principale concerne le tourisme et le voyage, structurée autour d’une liste de pays, avec pour satellites les villes principales, leur météo moyenne annuelle, la monnaie locale, les normes électriques, les langues officielles et parlées, ainsi que quelques phrases utiles.

## Technologies

Le projet est développé principalement en **Python**, avec les outils suivants :

- **FastAPI** : framework pour la création d’API RESTful
- **BeautifulSoup** : bibliothèque de scraping web
- **Pandas** : manipulation et structuration des données
- **Requests** : interrogation d’API et gestion des appels HTTP

## Sources

- **Pays** : fichier CSV depuis [geocounties.com](https://geocounties.com)
- **Normes électriques** : scraping de [Wikipedia – _Mains electricity by country_](https://en.wikipedia.org/wiki/Mains_electricity_by_country)
- **Villes principales** : appels à l’API [GeoNames](https://api.geonames.org)
- **Météo moyenne annuelle** : appels à l’API [Meteostat](https://api.meteostat.net)
- **Monnaie** : _à définir_
- **Langue** : _à définir_
- **Phrases utiles** : _à définir_

## Bases de données

### MongoDB

Les _phrases utiles par langue_ présentent une structure souple, non normalisée et potentiellement variable selon les contextes linguistiques.
Elles sont donc stockées dans une **collection MongoDB**, adaptée aux données semi-structurées et aux schémas évolutifs.

### MySQL

Les _données d’informations par pays_ reposent sur des relations claires et des structures de données normalisées.
Elles seront gérées dans une **base relationnelle MySQL**, dont la structure permet la mise en place de jointures, de contraintes d’intégrité et d’un schéma cohérent.

### Containerisation

Les deux bases de données sont conteneurisées au sein d’un même **environnement Docker**.
Chaque service (MongoDB et MySQL) dispose de son propre conteneur, défini dans un `docker-compose.yml` commun, facilitant le déploiement, l’isolation et la maintenance.

## Architecture

L’architecture du projet suit une organisation modulaire, inspirée des standards modernes de développement backend (notamment FastAPI).
Elle favorise la lisibilité, la maintenabilité et l’évolution du code grâce à une séparation claire des responsabilités.

### Arborescence générale

```
src/
 └── backend/
      ├── models/       # Modèles de données : définitions ORM (SQLAlchemy) ou entités métiers
      ├── schemas/      # Schémas Pydantic : validation, sérialisation et désérialisation des données
      ├── routers/      # Routes et endpoints de l’API, regroupés par domaine fonctionnel
      ├── services/     # Logique métier, traitements applicatifs et interactions avec les modèles
      ├── security/     # Mécanismes d’authentification, d’autorisation et gestion des tokens
      ├── connexion/    # Configuration et gestion des connexions aux ressources externes (DB, cache, API)
      ├── utils/        # Fonctions d’aide et utilitaires génériques (logs, formatage, conversions)
      └── main.py       # Point d’entrée principal de l’application
```
