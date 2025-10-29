import re
import unicodedata
import pandas as pd
from pathlib import Path
from typing import List, Dict
import sys
import requests
import time

sys.path.insert(0, Path(__file__).resolve().parents[3])
from connexion.mysql_connect import MySQLConnection
from src.backend.orm.ville_orm import VilleOrm
from utils.utils import ETLUtils


class ETLVille:
    """ETL pour charger les villes depuis cities15000.txt vers la BDD"""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parents[5]
        self.input_path = self.base_dir / "raw_sources" / "cities15000.txt"
        self.countries_path = self.base_dir / "raw_sources" / "countries_en.csv"
        self.output_path = self.base_dir / "src" / "db" / "villes.csv"
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Colonnes du fichier GeoNames cities15000.txt (19 colonnes)
        self.columns = [
            "geoname_id",
            "name_en",
            "ascii_name",
            "alternates_names",
            "latitude",
            "longitude",
            "c1",
            "c2",
            "country_3166a2",
            "alt_c",
            "a1",
            "a2",
            "a3",
            "a4",
            "pop",
            "altitude",
            "d",
            "timezone",
            "edit_date",
        ]

        # Colonnes à conserver
        self.keep_columns = [
            "geoname_id",
            "name_en",
            "latitude",
            "longitude",
            "pop",
            "country_3166a2",
        ]

    def get_country_capitals(self, country_codes: List[str]) -> Dict[str, List[str]]:
        """Récupère les capitales pour une liste de codes pays"""

        capitals_dict = {}

        for code in country_codes:
            try:
                url = f"https://restcountries.com/v3.1/alpha/{code}?fields=capital"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    capitals = data.get("capital", [])
                    print(f"{code}:{capitals}")
                    capitals_dict[code.lower()] = [c.strip() for c in capitals]
                else:
                    capitals_dict[code.lower()] = []

                time.sleep(0.02)  # politesse API

            except Exception as e:
                print(f" Error {code.upper()}: {e}")
                capitals_dict[code.lower()] = []
        return capitals_dict

    def extract(self) -> pd.DataFrame:
        """Lit le fichier cities15000.txt et retourne un DataFrame"""
        print(f"Lecture de {self.input_path}...")

        if not self.input_path.exists():
            raise FileNotFoundError(f"Fichier introuvable: {self.input_path}")

        df = pd.read_csv(
            self.input_path,
            sep="\t",
            names=self.columns,
            index_col=False,  # la première colonne est une donnée, pas index
            header=None,
            encoding="utf-8",
            low_memory=False,
            dtype=str,
            na_values=[""],
            keep_default_na=False,
        )

        print(f"{len(df)} lignes extraites")

        df_countries = pd.read_csv(self.countries_path, dtype=str)
        print(df_countries)

        return {"villes": df, "pays": df_countries}

    def transform(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Transforme le DataFrame: ne garde que les colonnes nécessaires"""
        print("Transformation des données...")
        df = data["villes"]
        df_countries = data["pays"]
        # Ne garder que les colonnes utiles
        df = df[self.keep_columns].copy()

        # Convertir geoname_id en int
        df["geoname_id"] = pd.to_numeric(df["geoname_id"], errors="coerce")

        # Supprimer les lignes où geoname_id est invalide
        invalid_ids = df["geoname_id"].isna().sum()
        if invalid_ids > 0:
            print(f"{invalid_ids} lignes avec geoname_id invalide supprimées")
            df = df.dropna(subset=["geoname_id"])

        # filtrage country_3166a2
        valid_alpha2 = df_countries["alpha2"].dropna().str.strip().str.lower().tolist()
        df["country_3166a2"] = df["country_3166a2"].fillna("").str.strip().str.lower()
        df = df[df["country_3166a2"].isin(valid_alpha2)]

        # Nettoyer les valeurs textuelles
        df["name_en"] = df["name_en"].fillna("").str.strip()

        # Convertir latitude et longitude en float
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

        # Convertir pop en int pour le tri
        df["pop"] = pd.to_numeric(df["pop"], errors="coerce").fillna(0).astype(int)

        # Supprimer les lignes sans nom
        initial_count = len(df)
        df = df[df["name_en"] != ""]
        removed = initial_count - len(df)
        if removed > 0:
            print(f"{removed} lignes sans nom supprimées")

        # Enrichissement: déterminer les capitales
        unique_countries = df["country_3166a2"].unique().tolist()
        capitals_dict = self.get_country_capitals(unique_countries)

        # Fonction pour vérifier si une ville est capitale
        def is_capital(row):
            country_code = row["country_3166a2"]
            city_name = row["name_en"]
            candidates = capitals_dict.get(country_code, [])
            return any(ETLUtils.similarity(city_name, cap) >= 0.8 for cap in candidates)

        df["is_capital"] = df.apply(is_capital, axis=1)

        # Trier par pays et population, puis ne garder que les 4 plus peuplées par pays
        # La V2 pourra avoir une base plus importante...
        df = df.sort_values(["country_3166a2", "pop"], ascending=[True, False])

        # Pour chaque pays : garder la capitale + les 3 villes les plus peuplées (ou 4 si pas de capitale)
        def select_cities_per_country(group):
            capitals = group[group["is_capital"] == True]
            non_capitals = group[group["is_capital"] == False]

            if len(capitals) > 0:
                return pd.concat([capitals.head(1), non_capitals.head(3)])
            else:
                return non_capitals.head(4)

        df = (
            df.groupby("country_3166a2", group_keys=False)
            .apply(select_cities_per_country)
            .reset_index(drop=True)
        )

        print(f"{len(df)} lignes transformées")
        return df

    def load_csv(self, df: pd.DataFrame) -> Path:
        """Sauvegarde le DataFrame dans villes.csv"""
        print(f"Sauvegarde dans {self.output_path}...")
        df.to_csv(self.output_path, index=False, encoding="utf-8")
        print(f"CSV sauvegardé: {len(df)} lignes")
        return self.output_path

    def load_database(self, df: pd.DataFrame) -> int:
        """Charge les données dans la table Villes avec INSERT IGNORE"""
        print("Chargement dans la base de données...")
        try:
            MySQLConnection.connect()
            df["is_capital"] = df["is_capital"].astype(int)
            records = df.where(pd.notnull(df), None).to_dict("records")
            batch_size = 1000
            total_inserted = 0
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                rows_affected = VilleOrm.bulk_insert_ignore(batch)
                total_inserted += rows_affected
                if (i + batch_size) % 10000 == 0:
                    print(f"{i + batch_size}/{len(records)} lignes traitées...")
                MySQLConnection.commit()
            print(f"{total_inserted} villes insérées (doublons ignorés)")
            return total_inserted
        except Exception as e:
            MySQLConnection.rollback()
            print(f"Erreur lors du chargement: {e}")
            raise
        finally:
            MySQLConnection.close()

    def run(self) -> pd.DataFrame:
        """Execute le pipeline ETL complet"""
        print("\n" + "=" * 60)
        print("Démarrage ETL Villes")
        print("=" * 60 + "\n")

        data = self.extract()
        df = self.transform(data)
        self.load_csv(df)
        self.load_database(df)

        print("\n" + "=" * 60)
        print("ETL Villes terminé avec succès")
        print("=" * 60 + "\n")

        return df


# Méthode helper pour MySQLConnection
def _escape_string(s: str) -> str:
    """Échappe les caractères spéciaux pour MySQL"""
    if s is None:
        return ""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')


# Ajouter la méthode à MySQLConnection
MySQLConnection._escape_string = staticmethod(_escape_string)


def main():
    etl = ETLVille()
    etl.run()


if __name__ == "__main__":
    main()
