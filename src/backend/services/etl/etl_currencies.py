import pandas as pd
import requests
import time
import sys
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parents[2])

from connexion.mysql_connect import MySQLConnection
from src.backend.orm.currency_orm import CurrencyOrm
from utils.utils import ETLUtils


class CurrencyETL:
    """Classe pour gérer l'ETL des devises par pays"""

    def __init__(self):
        """Initialisation des chemins de fichiers"""
        # Le fichier Python est dans ./src/backend/services
        # On remonte de 3 niveaux pour atteindre la racine du projet
        self.base_dir = Path(__file__).resolve().parents[4]
        self.input_path = self.base_dir / "raw_sources" / "countries_en.csv"
        self.output_path = self.base_dir / "src" / "db" / "currencies.csv"
        self.api_base_url = "https://www.apicountries.com/alpha"

    def extract_csv_to_df(self, file_path):
        """Extraction d'un fichier CSV vers DataFrame

        Args:
            file_path (Path): chemin du fichier CSV

        Returns:
            pd.DataFrame: le DataFrame extrait
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas.")

        df = pd.read_csv(file_path)
        print(f"Fichier {file_path.name} chargé : {len(df)} lignes")
        return df

    def remove_columns(self, df, columns_to_remove):
        """Supprime les colonnes spécifiées du DataFrame

        Args:
            df (pd.DataFrame): DataFrame à traiter
            columns_to_remove (list): liste des colonnes à supprimer

        Returns:
            pd.DataFrame: DataFrame sans les colonnes supprimées
        """
        existing_columns = [col for col in columns_to_remove if col in df.columns]
        df_cleaned = df.drop(columns=existing_columns)
        print(f"Colonnes supprimées : {existing_columns}")
        return df_cleaned

    def add_currency_columns(self, df):
        """Ajoute les colonnes pour les devises

        Args:
            df (pd.DataFrame): DataFrame à traiter

        Returns:
            pd.DataFrame: DataFrame avec nouvelles colonnes
        """
        df["currency_name"] = None
        df["currency_symbol"] = None
        df["currency_code"] = None
        print(
            "Colonnes de devises ajoutées : currency_name, currency_symbol, currency_code"
        )
        return df

    def fetch_currency_data(self, alpha2_code):
        """Interroge l'API pour récupérer les données de devise d'un pays

        Args:
            alpha2_code (str): code alpha2 du pays (ex: 'IL', 'FR', 'US')

        Returns:
            dict: données de devise ou None si erreur
        """
        try:
            url = f"{self.api_base_url}/{alpha2_code}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Récupérer les données de devise depuis l'objet currencies
                currencies = data.get("currencies", [])

                if currencies and len(currencies) > 0:
                    # Prendre la première devise
                    currency = currencies[0]
                    return {
                        "currency_name": currency.get("name", "-"),
                        "currency_symbol": currency.get("symbol", "-"),
                        "currency_code": currency.get("code", "-"),
                    }
                else:
                    print(f"Aucune devise trouvée pour {alpha2_code}")
                    return None

            else:
                print(f"Erreur {response.status_code} pour {alpha2_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Erreur de requête pour {alpha2_code}: {e}")
            return None
        except Exception as e:
            print(f"Erreur inattendue pour {alpha2_code}: {e}")
            return None

    def enrich_with_currency_data(self, df):
        """Enrichit le DataFrame avec les données de devises via l'API

        Args:
            df (pd.DataFrame): DataFrame à enrichir

        Returns:
            pd.DataFrame: DataFrame enrichi
        """
        print("\n--- ENRICHISSEMENT AVEC L'API ---")
        total_rows = len(df)

        for index, row in df.iterrows():
            alpha2_code = row["alpha2"]
            country_name = row.get("name", "N/A")
            print(
                f"[{index + 1}/{total_rows}] Traitement : {country_name} ({alpha2_code})"
            )

            currency_data = self.fetch_currency_data(alpha2_code)

            if currency_data:
                df.at[index, "currency_name"] = currency_data["currency_name"]
                df.at[index, "currency_symbol"] = currency_data["currency_symbol"]
                df.at[index, "currency_code"] = currency_data["currency_code"]
                print(
                    f"{currency_data['currency_code']} - {currency_data['currency_name']}"
                )
            else:
                df.at[index, "currency_name"] = "-"
                df.at[index, "currency_symbol"] = "-"
                df.at[index, "currency_code"] = "-"
                print(f"Données non disponibles")

            # Pause de politesse entre les requêtes (sauf pour la dernière)
            if index < total_rows - 1:
                time.sleep(0.1)

        print(f"Enrichissement terminé : {total_rows} pays traités")
        return df

    def transform(self, df):
        """Pipeline complet de transformation

        Args:
            df (pd.DataFrame): DataFrame source

        Returns:
            pd.DataFrame: DataFrame transformé
        """
        print("\n--- DÉBUT DES TRANSFORMATIONS ---")

        # Vérifier que la colonne alpha2 existe
        if "alpha2" not in df.columns:
            raise ValueError("La colonne 'alpha2' est requise dans le fichier source")

        # Étape 1: Suppression des colonnes
        df_cleaned = self.remove_columns(df, ["id", "alpha3"])

        # Étape 2: Ajout des colonnes de devises
        df_with_columns = self.add_currency_columns(df_cleaned)

        # Étape 3: Enrichissement via API
        df_enriched = self.enrich_with_currency_data(df_with_columns)

        print(
            f"DataFrame final : {len(df_enriched)} lignes x {len(df_enriched.columns)} colonnes"
        )

        return df_enriched

    def load(self, df):
        """Sauvegarde du DataFrame dans le fichier CSV et MySQL via le Repository

        Args:
            df (pd.DataFrame): DataFrame à sauvegarder
        """
        # 1. Sauvegarde CSV
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.output_path, index=False, encoding="utf-8")
        print(f"\nFichier CSV sauvegardé : {self.output_path}")

        # 2. Insertion dans MySQL via le Repository
        try:
            MySQLConnection.connect()
            print("\n--- INSERTION DANS MYSQL (via Repository) ---")

            inserted_count = 0
            error_count = 0

            for index, row in df.iterrows():
                try:
                    # Certaines lignes peuvent contenir '-' (absence de données)
                    code = (row.get("currency_code") or "").strip()
                    name = (row.get("currency_name") or "").strip()
                    symbol = (row.get("currency_symbol") or "").strip()

                    if not code or code == "-":
                        # Pas de code ISO 4217 -> on ignore proprement
                        continue

                    rc = CurrencyOrm.insert_ignore(
                        iso4217=code,
                        name=name if name and name != "-" else code,
                        symbol=symbol if symbol and symbol != "-" else "",
                    )
                    if rc > 0:
                        inserted_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Erreur pour {row.get('currency_code')}: {e}")

            MySQLConnection.commit()
            print(f"MySQL - {inserted_count} monnaie(s) insérée(s)")
            if error_count > 0:
                print(f"{error_count} erreur(s) rencontrée(s)")

        except Exception as e:
            print(f"Erreur lors de l'insertion MySQL: {e}")
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()

    def run(self):
        """Exécute le pipeline ETL complet"""
        print("=== ETL CURRENCIES ===\n")

        # EXTRACTION
        print("--- PHASE EXTRACTION ---")
        try:
            df_countries = self.extract_csv_to_df(self.input_path)
        except FileNotFoundError as e:
            print(e)
            print("\nAssurez-vous que le fichier est présent.")
            return None

        # TRANSFORMATION
        print("\n--- PHASE TRANSFORMATION ---")
        try:
            df_transformed = self.transform(df_countries)
        except ValueError as e:
            print(e)
            return None

        # LOAD
        print("\n--- PHASE LOAD ---")
        self.load(df_transformed)

        # Affichage du résultat
        print("\n--- APERÇU DU RÉSULTAT FINAL ---")
        print(df_transformed.head(10))
        print(f"\nDimensions finales : {df_transformed.shape}")
        print("\n=== ETL TERMINÉ ===")

        return df_transformed


def main():
    etl = CurrencyETL()
    return etl.run()


if __name__ == "__main__":
    df_result = main()
