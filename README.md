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
