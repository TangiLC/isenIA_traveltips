import pandas as pd
import json
import yaml
from pathlib import Path


class ExtractUtils:
    """Classe utilitaire pour extraire des données depuis différents formats"""

    # ========== CSV ==========

    @staticmethod
    def extract_csv(file_path, verbose=True):
        """
        Extrait un fichier CSV simple.
        Méthodes issues de etl_langues.py, etl_currencies.py, etl_countries.py

        Args:
            file_path: Chemin du fichier CSV
            verbose: Afficher le log (défaut: True)

        Returns:
            DataFrame pandas

        Example:
            df = ExtractUtils.extract_csv("data/countries.csv")
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Le fichier {path} n'existe pas.")

        df = pd.read_csv(path)

        if verbose:
            print(f"Fichier {path.name} chargé : {len(df)} lignes")

        return df

    @staticmethod
    def extract_tsv(file_path, column_names, verbose=True):
        """
        Extrait un fichier TSV (tab-separated) sans header.
        Méthode issue de etl_villes.py

        Args:
            file_path: Chemin du fichier TSV
            column_names: Liste des noms de colonnes
            verbose: Afficher le log

        Returns:
            DataFrame pandas

        Example:
            columns = ["geoname_id", "name", "latitude", "longitude"]
            df = ExtractUtils.extract_tsv("cities15000.txt", columns)
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Le fichier {path} n'existe pas.")

        df = pd.read_csv(
            path,
            sep="\t",
            names=column_names,
            header=None,
            encoding="utf-8",
            dtype=str,
            na_values=[""],
            keep_default_na=False,
        )

        if verbose:
            print(f"Fichier {path.name} chargé : {len(df)} lignes")

        return df

    # ========== JSON ==========

    @staticmethod
    def extract_json(file_path, verbose=True):
        """
        Extrait un fichier JSON.
        Méthode issue de etl_countries.py

        Args:
            file_path: Chemin du fichier JSON
            verbose: Afficher le log

        Returns:
            Dict ou List Python

        Example:
            data = ExtractUtils.extract_json("countries.json")
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Fichier {path} introuvable")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if verbose:
            if isinstance(data, dict):
                print(f"JSON chargé : {len(data)} entrées")
            elif isinstance(data, list):
                print(f"JSON chargé : {len(data)} éléments")

        return data

    # ========== YAML ==========

    @staticmethod
    def extract_yaml(file_path, verbose=True):
        """
        Extrait un fichier YAML.
        Méthode issue de etl_countries.py

        Args:
            file_path: Chemin du fichier YAML
            verbose: Afficher le log

        Returns:
            Structure Python (dict, list, etc.)

        Example:
            data = ExtractUtils.extract_yaml("countries.yml")
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Fichier {path} introuvable")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if verbose:
            if isinstance(data, dict):
                print(f"YAML chargé : {len(data)} entrées")
            elif isinstance(data, list):
                print(f"YAML chargé : {len(data)} éléments")

        return data

    # ========== WEB / HTML ==========

    @staticmethod
    def extract_soup(url, session=None, timeout=30, verbose=True):
        """
        Extrait et parse une page HTML en BeautifulSoup.
        Méthodes issues de etl_elec1.py, elec_scrap2.py

        Args:
            url: URL à charger
            session: Session requests (optionnel)
            timeout: Timeout en secondes
            verbose: Afficher le log

        Returns:
            Objet BeautifulSoup

        Example:
            soup = ExtractUtils.extract_soup("https://www.iec.ch/world-plugs")
        """
        import requests
        from bs4 import BeautifulSoup

        if session is None:
            session = requests.Session()

        response = session.get(url, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        if verbose:
            print(f"HTML chargé depuis {url}")

        return soup

    # ========== HELPERS ==========

    @staticmethod
    def extract_multiple_csv(file_dict, verbose=True):
        """
        Extrait plusieurs fichiers CSV d'un coup.

        Args:
            file_dict: Dictionnaire {nom: chemin}
            verbose: Afficher les logs

        Returns:
            Dictionnaire {nom: DataFrame}

        Example:
            dfs = ExtractUtils.extract_multiple_csv({
                "iso1": "iso_639-1.csv",
                "iso2": "iso_639-2.csv"
            })
            df_iso1 = dfs["iso1"]
            df_iso2 = dfs["iso2"]
        """
        result = {}
        for name, path in file_dict.items():
            result[name] = ExtractUtils.extract_csv(path, verbose=verbose)
        return result
