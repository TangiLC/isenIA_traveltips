# Sources des données

## Info Langues

code iso 636-2
CSV source : https://github.com/haliaeetus/iso-639/tree/master/data
fichier iso_639-1.csv et iso_639-2.csv
ETL_langue pour fusionner les infos, parser, vérifier cohérence, supprimer doublons

## Info Pays

code iso 3166 alpha2 et assets
json source : https://stefangabos.github.io/
csv source : https://mledoze.github.io/countries/dist/countries.csv
flags 48x48 png assets : icondrawer.com / https://stefangabos.github.io/

## Info Monnaie

nom, symbol, code international
requête API : https://www.apicountries.com/docs/api GET api/countries/?name
