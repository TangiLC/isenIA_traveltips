# TravelTips API — README

Version OpenAPI : 3.1.0  
Objet : gestion d’informations pays (pays, langues, monnaies, électricité, villes, météo agrégée, conversations).  
Sécurité : routes publiques et routes protégées par **JWT Bearer** (`Authorization: Bearer <token>`).  
Obtention d’un token : `/auth/test_token` (dev), `/auth/login` (authentification).

## Table des matières

1. [Authentification](#authentification)
2. [Pays (Countries)](#pays-countries)
3. [Langues](#langues)
4. [Monnaies (Currencies)](#monnaies-currencies)
5. [Électricité (Types de prises)](#électricité-types-de-prises)
6. [Villes](#villes)
7. [Météo — Hebdo](#météo--hebdo)
8. [Conversations](#conversations)
9. [Racine & Santé](#racine--santé)
10. [Sécurité — Rappels](#sécurité--rappels)

---

## Authentification

| Méthode | Chemin                   | Rôle                                | Sécurité | Codes de réponse                         |
| ------- | ------------------------ | ----------------------------------- | -------- | ---------------------------------------- |
| GET     | `/api/auth/test_token`   | Générer un JWT de test (dev)        | Public   | `200`, `403`, `500`                      |
| GET     | `/api/auth/user/by_name` | Récupérer un utilisateur par pseudo | **JWT**  | `200`, `403`, `404`, `500`, `422`        |
| POST    | `/api/auth/login`        | Authentifier et obtenir un JWT      | Public   | `200`, `403`, `404`, `500`, `422`        |
| PUT     | `/api/auth/user`         | Créer un utilisateur                | **JWT**  | `201`, `200`, `403`, `404`, `500`, `422` |
| PATCH   | `/api/auth/user/{id}`    | Mise à jour partielle utilisateur   | **JWT**  | `200`, `403`, `404`, `500`, `422`        |
| DELETE  | `/api/auth/user/{id}`    | Supprimer un utilisateur            | **JWT**  | `204`, `200`, `403`, `404`, `500`, `422` |

---

## Pays (Countries)

| Méthode | Chemin                               | Rôle                                      | Sécurité | Codes de réponse                         |
| ------- | ------------------------------------ | ----------------------------------------- | -------- | ---------------------------------------- | --- |
| GET     | `/api/countries/by_id/{alpha2}`      | Détails d’un pays par code ISO alpha-2    | Public   | `200`, `404`, `422`, `500`               |
| GET     | `/api/countries/by_name/{name}`      | Recherche par nom (en/fr/local)           | Public   | `200`, `404`, `422`, `500`               |
| GET     | `/api/countries/`                    | Liste paginée des pays (sans relations)   | Public   | `200`, `422`, `500`                      |
| GET     | `/api/countries/by_plug_type/{type}` | Liste des pays utilisant un type de prise | Public   | `200`, `404`, `500`, `422`               |     |
| POST    | `/api/countries/`                    | Ajouter un pays (avec relations)          | **JWT**  | `200`, `201`, `400`, `403`, `422`, `500` |
| PUT     | `/api/countries/{alpha2}`            | Modifier un pays                          | **JWT**  | `200`, `403`, `404`, `422`, `500`        |
| DELETE  | `/api/countries/{alpha2}`            | Supprimer un pays (cascade)               | **JWT**  | `200`, `403`, `404`, `500`, `422`        |

---

## Langues

| Méthode | Chemin                     | Rôle                                   | Sécurité | Codes de réponse                  |
| ------- | -------------------------- | -------------------------------------- | -------- | --------------------------------- |
| GET     | `/api/langues/by_code_iso` | Chercher une langue par code ISO 639-2 | Public   | `200`, `404`, `500`, `422`        |
| GET     | `/api/langues/by_name`     | Rechercher des langues par nom         | Public   | `200`, `404`, `500`, `422`        |
| GET     | `/api/langues/by_famille`  | Rechercher des langues par famille     | Public   | `200`, `404`, `500`, `422`        |
| PUT     | `/api/langues`             | Créer/remplacer une langue (upsert)    | **JWT**  | `201`, `500`, `422`               |
| PATCH   | `/api/langues/{iso639_2}`  | Mise à jour partielle d’une langue     | **JWT**  | `200`, `404`, `500`, `422`        |
| DELETE  | `/api/langues/{iso639_2}`  | Supprimer une langue                   | **JWT**  | `200`, `403`, `404`, `500`, `422` |

---

## Monnaies (Currencies)

| Méthode | Chemin                      | Rôle                                        | Sécurité | Codes de réponse           |
| ------- | --------------------------- | ------------------------------------------- | -------- | -------------------------- |
| GET     | `/api/monnaies/by_code_iso` | Chercher une devise par code ISO 4217       | Public   | `200`, `404`, `500`, `422` |
| GET     | `/api/monnaies/by_name`     | Rechercher des devises par nom/symbole/code | Public   | `200`, `500`, `422`        |
| PUT     | `/api/monnaies`             | Créer/remplacer une devise (upsert)         | **JWT**  | `201`, `500`, `422`        |
| PATCH   | `/api/monnaies/{iso4217}`   | Mise à jour partielle d’une devise          | **JWT**  | `200`, `404`, `500`, `422` |
| DELETE  | `/api/monnaies/{iso4217}`   | Supprimer une devise                        | **JWT**  | `200`, `404`, `500`, `422` |

---

## Électricité (Types de prises)

| Méthode | Chemin                         | Rôle                                      | Sécurité | Codes de réponse                  |
| ------- | ------------------------------ | ----------------------------------------- | -------- | --------------------------------- |
| GET     | `/api/electricite`             | Lister tous les types de prises           | Public   | `200`, `500`                      |
| GET     | `/api/electricite/{plug_type}` | Obtenir un type de prise (A–O)            | Public   | `200`, `404`, `500`, `422`        |
| PUT     | `/api/electricite`             | Créer/remplacer un type de prise (upsert) | **JWT**  | `201`, `403`, `500`, `422`        |
| PATCH   | `/api/electricite/{plug_type}` | Mise à jour partielle (images)            | **JWT**  | `200`, `403`, `404`, `500`, `422` |
| DELETE  | `/api/electricite/{plug_type}` | Supprimer un type de prise                | **JWT**  | `200`, `403`, `404`, `500`, `422` |

---

## Villes

| Méthode | Chemin                                    | Rôle                                  | Sécurité | Codes de réponse                         |
| ------- | ----------------------------------------- | ------------------------------------- | -------- | ---------------------------------------- |
| GET     | `/api/villes/{geoname_id}`                | Récupérer une ville par GeoNames ID   | Public   | `200`, `404`, `422`, `500`               |
| GET     | `/api/villes/by_name/{name_en}`           | Rechercher des villes par nom         | Public   | `200`, `404`, `422`, `500`               |
| GET     | `/api/villes/by_country/{country_3166a2}` | Lister les villes d’un pays           | Public   | `200`, `400`, `422`, `500`               |
| GET     | `/api/villes/`                            | Lister toutes les villes (pagination) | Public   | `200`, `422`, `500`                      |
| POST    | `/api/villes/`                            | Ajouter une ville                     | **JWT**  | `200`, `400`, `403`, `422`, `500`        |
| PUT     | `/api/villes/{geoname_id}`                | Modifier une ville                    | **JWT**  | `200`, `201`, `403`, `404`, `500`, `422` |
| DELETE  | `/api/villes/{geoname_id}`                | Supprimer une ville                   | **JWT**  | `200`, `403`, `404`, `500`, `422`        |

---

## Météo — Hebdo

| Méthode | Chemin                                      | Rôle                                        | Sécurité | Codes de réponse           |
| ------- | ------------------------------------------- | ------------------------------------------- | -------- | -------------------------- |
| GET     | `/api/meteo/{geoname_id}`                   | Lister les semaines d’une ville (filtrable) | Public   | `200`, `404`, `422`        |
| GET     | `/api/meteo/`                               | Parcourir toutes les semaines (pagination)  | Public   | `200`, `422`               |
| POST    | `/api/meteo/`                               | Créer/mettre à jour une semaine (upsert)    | **JWT**  | `201`, `401`, `422`        |
| POST    | `/api/meteo/bulk`                           | Upsert en masse (nb de lignes)              | **JWT**  | `201`, `401`, `422`        |
| PUT     | `/api/meteo/{geoname_id}/{week_start_date}` | Mise à jour partielle d’une semaine         | **JWT**  | `200`, `401`, `404`, `422` |
| DELETE  | `/api/meteo/{geoname_id}/{week_start_date}` | Supprimer une semaine                       | **JWT**  | `204`, `401`, `404`, `422` |

---

## Conversations

| Méthode | Chemin                                   | Rôle                               | Sécurité | Codes de réponse                  |
| ------- | ---------------------------------------- | ---------------------------------- | -------- | --------------------------------- |
| GET     | `/api/conversations`                     | Lister toutes les conversations    | Public   | `200`, `500`, `422`               |
| GET     | `/api/conversations/by_lang/{lang_code}` | Lister par code langue (ISO 639-2) | Public   | `200`, `500`, `422`               |
| GET     | `/api/conversations/{conversation_id}`   | Récupérer une conversation par ID  | Public   | `200`, `404`, `500`, `422`        |
| PATCH   | `/api/conversations/{conversation_id}`   | Mise à jour partielle              | **JWT**  | `200`, `404`, `400`, `500`, `422` |
| PUT     | `/api/conversations/{conversation_id}`   | Remplacement complet               | **JWT**  | `200`, `404`, `400`, `500`, `422` |
| POST    | `/api/conversations`                     | Créer une conversation (MongoDB)   | **JWT**  | `201`, `400`, `500`, `422`        |
| DELETE  | `/api/conversations/{conversation_id}`   | Supprimer une conversation         | **JWT**  | `200`, `404`, `400`, `500`, `422` |

---

## Racine, Santé & Crédits

| Méthode | Chemin         | Rôle                    | Sécurité | Codes de réponse |
| ------- | -------------- | ----------------------- | -------- | ---------------- |
| GET     | `/`            | Point d’entrée de l’API | Public   | `200`            |
| GET     | `/health`      | Health check            | Public   | `200`            |
| GET     | `/api/credits` | Sources des données     | Public   | `200`            |

---

## Sécurité — Rappels

Les routes marquées **JWT** exigent un en-tête `Authorization: Bearer <token>` valide.  
Absence/invalidité du token : `401`.  
Accès refusé (rôle/droits) : `403`.
