import pandas as pd
from pathlib import Path
from typing import List, Dict
import sys
import requests
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from connexion.mysql_connect import MySQLConnection
from repositories.ville_repository import VilleRepository


class ETLVille:
    """ETL pour charger les villes depuis cities15000.txt vers la BDD"""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.input_path = self.base_dir / "raw_sources" / "cities15000.txt"
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
        print(capitals_dict)
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
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforme le DataFrame: ne garde que les colonnes nécessaires"""
        print("Transformation des données...")

        # Ne garder que les colonnes utiles
        df = df[self.keep_columns].copy()

        # Convertir geoname_id en int
        df["geoname_id"] = pd.to_numeric(df["geoname_id"], errors="coerce")

        # Supprimer les lignes où geoname_id est invalide
        invalid_ids = df["geoname_id"].isna().sum()
        if invalid_ids > 0:
            print(f"{invalid_ids} lignes avec geoname_id invalide supprimées")
            df = df.dropna(subset=["geoname_id"])

        # Nettoyer les valeurs textuelles
        df["name_en"] = df["name_en"].fillna("").str.strip()
        df["country_3166a2"] = df["country_3166a2"].fillna("").str.strip().str.lower()

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

        # Trier par pays et population, puis ne garder que les 4 plus peuplées par pays
        # La V2 pourra avoir une base plus importante...
        df = df.sort_values(["country_3166a2", "pop"], ascending=[True, False])
        df = df.groupby("country_3166a2").head().reset_index(drop=True)

        # Enrichissement: déterminer les capitales
        unique_countries = df["country_3166a2"].unique().tolist()
        capitals_dict = self.get_country_capitals(unique_countries)

        # Fonction pour vérifier si une ville est capitale
        def is_capital(row):
            country_code = row["country_3166a2"]
            city_name = row["name_en"]
            capitals = capitals_dict.get(country_code, [])
            return city_name in capitals

        df["is_capital"] = df.apply(is_capital, axis=1)

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
                rows_affected = VilleRepository.bulk_insert_ignore(batch)
                total_inserted += rows_affected
                if (i + batch_size) % 10000 == 0:
                    print(f"{i + batch_size}/{len(records)} lignes traitées...")
                MySQLConnection.commit()
            print(f"✅ {total_inserted} villes insérées (doublons ignorés)")
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

        df = self.extract()
        df = self.transform(df)
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
