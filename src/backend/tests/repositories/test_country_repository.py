import pytest
import src.backend.orm.country_orm as repo

CountryRepository = repo.CountryRepository


@pytest.fixture
def call_log():
    # Enregistre toutes les requêtes pour assertions
    return {
        "execute_query": [],
        "execute_update": [],
    }


@pytest.fixture(autouse=True)
def patch_mysql(monkeypatch, call_log):
    """
    Remplace MySQLConnection.execute_query / execute_update par des fakes.
    On adapte la réponse en fonction du contenu de la requête pour simuler
    les différents SELECT utilisés par get_by_alpha2().
    """

    def fake_execute_query(query, params=()):
        q = " ".join(query.split())
        call_log["execute_query"].append((q, params))

        # Base pays
        if "FROM Pays p WHERE p.iso3166a2 = %s" in q:
            iso = params[0]
            return [
                {
                    "iso3166a2": iso,
                    "iso3166a3": iso.upper() + "X",
                    "name_en": "Country EN",
                    "name_fr": "Pays FR",
                    "name_local": "Local",
                    "lat": 1.23,
                    "lng": 3.21,
                }
            ]

        # Langues
        if "FROM Pays_Langues pl" in q and "INNER JOIN Langues l" in q:
            return [
                {
                    "iso639_2": "eng",
                    "name_en": "English",
                    "name_fr": "Anglais",
                    "name_local": "English",
                    "is_in_mongo": 1,
                    "famille_en": "Indo-European",
                    "famille_fr": "Indo-européen",
                },
                {
                    "iso639_2": "fra",
                    "name_en": "French",
                    "name_fr": "Français",
                    "name_local": "Français",
                    "is_in_mongo": 1,
                    "famille_en": "Indo-European",
                    "famille_fr": "Indo-européen",
                },
            ]

        # Monnaies
        if "FROM Pays_Monnaies pm" in q and "INNER JOIN Monnaies m" in q:
            return [
                {"iso4217": "EUR", "name": "Euro", "symbol": "€"},
                {"iso4217": "USD", "name": "US Dollar", "symbol": "$"},
            ]

        # Frontières
        if "FROM Pays_Borders pb" in q and "LEFT JOIN Pays p1" in q:
            return [
                {
                    "iso3166a2": "de",
                    "name_en": "Germany",
                    "name_fr": "Allemagne",
                    "name_local": "Deutschland",
                },
                {
                    "iso3166a2": "it",
                    "name_en": "Italy",
                    "name_fr": "Italie",
                    "name_local": "Italia",
                },
            ]

        # Electricité
        if "FROM Pays_Electricite pe" in q and "INNER JOIN Electricite e" in q:
            return [
                {
                    "plug_type": "C",
                    "plug_png": "c.png",
                    "sock_png": "c_s.png",
                    "voltage": "230",
                    "frequency": "50",
                },
                {
                    "plug_type": "F",
                    "plug_png": "f.png",
                    "sock_png": "f_s.png",
                    "voltage": "230",
                    "frequency": "50",
                },
            ]

        # Villes
        if "FROM Villes v WHERE v.country_3166a2 = %s" in q:
            return [
                {
                    "geoname_id": 1,
                    "name_en": "Capital",
                    "latitude": 1.0,
                    "longitude": 2.0,
                    "is_capital": 1,
                },
                {
                    "geoname_id": 2,
                    "name_en": "Other",
                    "latitude": 1.5,
                    "longitude": 2.5,
                    "is_capital": 0,
                },
            ]

        # Recherche ISO par nom pour get_by_name
        if "SELECT DISTINCT p.iso3166a2 FROM Pays p WHERE" in q:
            # on renvoie deux codes pour déclencher les appels imbriqués
            return [{"iso3166a2": "fr"}, {"iso3166a2": "de"}]

        # Pagination get_all
        if (
            "SELECT iso3166a2, iso3166a3, name_en, name_fr, name_local, lat, lng FROM Pays"
            in q
        ):
            limit, offset = params
            data = [
                {
                    "iso3166a2": "ad",
                    "iso3166a3": "AND",
                    "name_en": "Andorra",
                    "name_fr": "Andorre",
                    "name_local": "Andorra",
                    "lat": 42.5,
                    "lng": 1.5,
                },
                {
                    "iso3166a2": "ae",
                    "iso3166a3": "ARE",
                    "name_en": "United Arab Emirates",
                    "name_fr": "Émirats arabes unis",
                    "name_local": "al-Imārāt",
                    "lat": 24.0,
                    "lng": 54.0,
                },
                {
                    "iso3166a2": "af",
                    "iso3166a3": "AFG",
                    "name_en": "Afghanistan",
                    "name_fr": "Afghanistan",
                    "name_local": "Afġānistān",
                    "lat": 33.0,
                    "lng": 65.0,
                },
            ]
            return data[offset : offset + limit]

        # get_countries_by_plug_type
        if (
            "FROM Pays p INNER JOIN Pays_Electricite pe" in q
            and "WHERE pe.plug_type = %s" in q
        ):
            plug = params[0]
            return (
                [
                    {
                        "iso3166a2": "fr",
                        "name_en": "France",
                        "name_fr": "France",
                        "voltage": "230",
                        "frequency": "50",
                    },
                    {
                        "iso3166a2": "de",
                        "name_en": "Germany",
                        "name_fr": "Allemagne",
                        "voltage": "230",
                        "frequency": "50",
                    },
                ]
                if plug in ("C", "F")
                else []
            )

        # Par défaut
        return []

    def fake_execute_update(query, params=()):
        q = " ".join(query.split())
        call_log["execute_update"].append((q, params))

        # delete / update / replace retournent un compte de lignes affectées
        if q.startswith("DELETE FROM Pays WHERE"):
            return 1 if params and params[0] else 0
        if q.startswith("UPDATE Pays SET"):
            return 1
        if q.startswith("REPLACE INTO Pays"):
            return 1

        # Inserts en lot: si on reçoit une liste de tuples, on renvoie sa taille
        if isinstance(params, list):
            return len(params)

        # Inserts unitaires
        return 1

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_query", staticmethod(fake_execute_query)
    )
    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(fake_execute_update)
    )


def test_normalize_string():
    assert CountryRepository._normalize_string("  Éléphant  ") == "elephant"
    assert CountryRepository._normalize_string("Ça") == "ca"


def test_get_by_alpha2_enrichit_relations(call_log):
    data = CountryRepository.get_by_alpha2("FR")
    assert data["iso3166a2"] == "fr"
    assert isinstance(data.get("langues"), list) and len(data["langues"]) >= 1
    assert isinstance(data.get("currencies"), list) and len(data["currencies"]) >= 1
    assert isinstance(data.get("borders"), list) and len(data["borders"]) >= 1
    assert isinstance(data.get("electricity"), list) and len(data["electricity"]) >= 1
    assert isinstance(data.get("cities"), list) and len(data["cities"]) >= 1
    # Vérifie l'ordre et les paramètres des appels SELECT
    qs = [q for q, _ in call_log["execute_query"]]
    assert any("FROM Pays p WHERE p.iso3166a2 = %s" in q for q in qs)


def test_get_by_alpha2_not_found(monkeypatch):
    def empty_query(q, p=()):
        if "FROM Pays p WHERE p.iso3166a2 = %s" in " ".join(q.split()):
            return []
        return []

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_query", staticmethod(empty_query)
    )
    assert CountryRepository.get_by_alpha2("zz") is None


def test_get_all_pagine():
    out = CountryRepository.get_all(skip=1, limit=1)
    assert isinstance(out, list) and len(out) == 1


def test_get_by_name_appelle_get_by_alpha2(monkeypatch):
    # on force get_by_alpha2 pour ne pas retaper les requêtes internes
    calls = {"by_alpha2": []}

    def fake_by_alpha2(iso2):
        calls["by_alpha2"].append(iso2)
        return {"iso3166a2": iso2, "name_en": f"X-{iso2}"}

    monkeypatch.setattr(
        CountryRepository, "get_by_alpha2", staticmethod(fake_by_alpha2)
    )
    res = CountryRepository.get_by_name("  PÁYS  ")
    assert isinstance(res, list) and len(res) == 2
    assert set(calls["by_alpha2"]) == {"fr", "de"}  # vient du fake SELECT DISTINCT


def test_upsert_pays():
    n = CountryRepository.upsert_pays(
        "fr", "FRA", "France", "France", "France", "48.85", "2.35"
    )
    assert n == 1


def test_delete_pays():
    ok = CountryRepository.delete_pays("FR")
    assert ok is True


def test_update_pays_avec_champs():
    ok = CountryRepository.update_pays("fr", {"name_en": "France", "lat": 48.8})
    assert ok is True


def test_update_pays_sans_champ_ne_fait_rien(call_log):
    ok = CountryRepository.update_pays("fr", {})
    assert ok is False
    # aucun UPDATE ne doit avoir été appelé
    assert not any(
        q.startswith("UPDATE Pays SET") for q, _ in call_log["execute_update"]
    )


def test_delete_relations_declenche_4_updates(call_log):
    CountryRepository.delete_relations("FR")
    ups = [q for q, _ in call_log["execute_update"]]
    assert sum(q.startswith("DELETE FROM ") for q in ups) >= 4


def test_insert_langues_ignore_vides_et_compte_lignes():
    n = CountryRepository.insert_langues("fr", ["eng", "", " fra ", None, "deu"])
    assert n == 3  # "eng", "fra", "deu"


def test_insert_monnaies_uppercase_et_compte_lignes():
    n = CountryRepository.insert_monnaies("fr", [" eur ", "", "usd", None])
    assert n == 2  # "EUR", "USD"


def test_insert_borders_applique_regles():
    # fr avec doublons, self-loop et désordre; ne doivent rester que paires triées uniques
    n = CountryRepository.insert_borders("fr", ["de", "fr", "it", "de", "  ES  "])
    # paires uniques attendues: ('de','fr')->('de','fr'), ('es','fr'), ('fr','it')->('fr','it') => 3
    assert n == 3


def test_insert_electricite_ignores_vides_et_compte_lignes():
    n = CountryRepository.insert_electricite("fr", [" c ", "", None, "F"], "230", "50")
    assert n == 2  # C, F


def test_get_countries_by_plug_type():
    res = CountryRepository.get_countries_by_plug_type("C")
    assert isinstance(res, list) and len(res) >= 1
