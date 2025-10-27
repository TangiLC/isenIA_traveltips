import pandas as pd
import json
import yaml
import sys
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parents[3])
from connexion.mysql_connect import MySQLConnection
from repositories.country_repository import CountryRepository
from utils.utils import ETLUtils


class CountryETL:
    """Classe pour gérer l'ETL des pays depuis multiples sources"""

    def __init__(self):
        """Initialisation des chemins de fichiers"""
        self.base_dir = Path(__file__).resolve().parents[5]
        self.raw_dir = self.base_dir / "raw_sources"
        self.csv_path = self.raw_dir / "countries_en.csv"
        self.json_path = self.raw_dir / "countries_stefangabos.json"
        self.yaml_path = self.raw_dir / "countries_mledoze.yml"
        self.elec_path = self.base_dir / "src" / "db" / "normes_elec_pays.csv"
        self.output_path = self.base_dir / "src" / "db" / "countries.csv"
        self.alter_script_path = self.base_dir / "src" / "db" / "alter_script.sql"

    def extract_csv(self):
        """Extraction du fichier CSV countries_en

        Returns:
            pd.DataFrame: DataFrame avec colonnes alpha2, alpha3, name
        """
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Fichier {self.csv_path} introuvable")

        df = pd.read_csv(self.csv_path)
        print(f"CSV chargé : {len(df)} lignes")
        return df

    def extract_json(self):
        """Extraction du fichier JSON countries_stefanos

        Returns:
            dict: Dictionnaire {alpha2: nom_français}
        """
        if not self.json_path.exists():
            raise FileNotFoundError(f"Fichier {self.json_path} introuvable")

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"JSON chargé : {len(data)} pays")
        return data

    def extract_yaml(self):
        """Extraction du fichier YAML countries_mledos

        Returns:
            list: Liste de dictionnaires représentant les pays
        """
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"Fichier {self.yaml_path} introuvable")

        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        print(f"YAML chargé : {len(data)} pays")
        return data

    def extract_elec_csv(self):
        """Extraction du fichier CSV normes électriques

        Returns:
            pd.DataFrame: DataFrame avec country, type, voltage, frequency
        """
        if not self.elec_path.exists():
            raise FileNotFoundError(f"Fichier {self.elec_path} introuvable")

        df = pd.read_csv(self.elec_path)
        print(f"Normes électriques chargées : {len(df)} lignes")
        return df

    def merge_csv_json(self, df_csv, dict_json):
        """Combine CSV et JSON pour créer le DataFrame de base

        Args:
            df_csv (pd.DataFrame): DataFrame issu du CSV
            dict_json (dict): Dictionnaire issu du JSON

        Returns:
            pd.DataFrame: DataFrame avec alpha2, alpha3, name_en, name_fr
        """
        # Normaliser les clés alpha2 en minuscules pour le matching
        df_csv["alpha2_lower"] = df_csv["alpha2"].str.lower()

        # Ajouter la colonne name_fr via le mapping JSON
        df_csv["name_fr"] = df_csv["alpha2_lower"].map(dict_json)

        # Renommer et réorganiser les colonnes
        df = df_csv[["alpha2", "alpha3", "name", "name_fr"]].copy()
        df.rename(columns={"name": "name_en"}, inplace=True)

        print(f"Fusion CSV/JSON : {len(df)} lignes")
        return df

    def iso3_to_iso2(self, iso3_code, df_base):
        """Convertit un code ISO3 en ISO2 via le DataFrame de base

        Args:
            iso3_code (str): Code ISO3 (ex: 'COD')
            df_base (pd.DataFrame): DataFrame avec alpha2 et alpha3

        Returns:
            str: Code ISO2 ou chaîne vide si non trouvé
        """
        result = df_base[df_base["alpha3"] == iso3_code.lower()]
        if not result.empty:
            return result.iloc[0]["alpha2"]
        return ""

    def process_yaml_data(self, yaml_data, df_base):
        """Traite les données YAML pour extraire les informations nécessaires

        Args:
            yaml_data (list): Données YAML
            df_base (pd.DataFrame): DataFrame de base pour conversion ISO3->ISO2

        Returns:
            pd.DataFrame: DataFrame avec cca2, currencies, latlng, borders, langues, name_local
        """
        rows = []

        for country in yaml_data:
            cca2 = country.get("cca2", "").lower()

            # Extraction des monnaies (clés de currencies)
            currencies = country.get("currencies", {})
            currency_codes = ",".join(currencies.keys()).lower() if currencies else ""

            # Extraction latitude longitude (latlng)
            latlng = country.get("latlng", [])
            latlng_str = ",".join([f"{float(x):.2f}" for x in latlng]) if latlng else ""

            # Extraction borders (ISO3 -> ISO2)
            borders_iso3 = country.get("borders", [])
            borders_iso2 = [self.iso3_to_iso2(b, df_base) for b in borders_iso3]
            borders_str = ",".join([b for b in borders_iso2 if b])

            # Extraction langues (clés de languages)
            languages = country.get("languages", {})
            langues_str = ",".join(languages.keys()) if languages else ""

            # Extraction name_local (premier common de native)
            native = country.get("name", {}).get("native", {})
            name_local = ""
            if native:
                first_lang = next(iter(native.values()), {})
                name_local = first_lang.get("common", "")

            rows.append(
                {
                    "cca2": cca2,
                    "currencies": currency_codes,
                    "latlng": latlng_str,
                    "borders": borders_str,
                    "langues": langues_str,
                    "name_local": name_local,
                }
            )

        df = pd.DataFrame(rows)
        print(f"Traitement YAML : {len(df)} lignes")
        return df

    def transform(self, df_csv, dict_json, yaml_data, df_elec):
        """Pipeline complet de transformation

        Args:
            df_csv (pd.DataFrame): DataFrame CSV
            dict_json (dict): Dictionnaire JSON
            yaml_data (list): Données YAML
            df_elec (pd.DataFrame): DataFrame normes électriques

        Returns:
            pd.DataFrame: DataFrame final
        """
        print("\n--- DÉBUT DES TRANSFORMATIONS ---")

        # Étape 1 & 2 : Fusion CSV + JSON
        df_base = self.merge_csv_json(df_csv, dict_json)

        # Étape 3 : Traitement YAML
        df_yaml = self.process_yaml_data(yaml_data, df_base)

        # Fusion finale sur alpha2/cca2
        df_base["alpha2_lower"] = df_base["alpha2"].str.lower()
        df_final = df_base.merge(
            df_yaml, left_on="alpha2_lower", right_on="cca2", how="left"
        )

        # Fusion avec les normes électriques sur name_en
        df_final = df_final.merge(
            df_elec[["country", "type", "voltage", "frequency"]],
            left_on="name_en",
            right_on="country",
            how="left",
        ).drop(columns=["country"])

        # Renommer la colonne 'type' en 'elec_type'
        df_final.rename(columns={"type": "elec_type"}, inplace=True)

        # Supprimer les colonnes temporaires et réorganiser
        df_final = df_final[
            [
                "alpha2",
                "alpha3",
                "name_en",
                "name_fr",
                "name_local",
                "langues",
                "currencies",
                "latlng",
                "borders",
                "elec_type",
                "voltage",
                "frequency",
            ]
        ]

        # Étape 4 : Supprimer les lignes avec alpha2 vide
        df_final = df_final[df_final["alpha2"].notna() & (df_final["alpha2"] != "")]

        # Remplacer les NaN par chaînes vides
        df_final = df_final.fillna("")

        print(
            f"DataFrame final : {len(df_final)} lignes x {len(df_final.columns)} colonnes"
        )
        return df_final

    def load(self, df):
        """
        1) Sauvegarde CSV
        2) Insertion/MAJ BDD:
           - Pays
           - Pays_Langues
           - Pays_Monnaies
           - Pays_Borders (a<b, pas de doublons, pas de a=a)
           - Pays_Electricite (avec voltage/frequency)
        """

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.output_path, index=False, encoding="utf-8")
        print(f"Fichier CSV sauvegardé : {self.output_path}")

        inserted_pays = 0
        l_lang = l_cur = l_bor = l_elec = 0
        try:
            MySQLConnection.connect()
            print("\n--- INSERTION DANS MYSQL (via CountryRepository) ---")

            for _, row in df.iterrows():
                iso2 = (row.get("alpha2") or "").strip().lower()
                iso3 = (row.get("alpha3") or "").strip().lower()
                if not iso2 or not iso3:
                    continue

                name_en = (row.get("name_en") or "").strip()
                name_fr = (row.get("name_fr") or "").strip()
                name_local = (row.get("name_local") or "").strip()

                lat_str, lng_str = ETLUtils.parse_lat_lng(row.get("latlng") or "")

                # upsert dans Pays
                inserted_pays += CountryRepository.upsert_pays(
                    iso2, iso3, name_en, name_fr, name_local, lat_str, lng_str
                )

                # langues
                langues = ETLUtils.split_csv_field(row.get("langues") or "")
                l_lang += CountryRepository.insert_langues(iso2, langues)

                # monnaies (FK vers Monnaies) – on insère seulement la liaison
                currencies = ETLUtils.split_csv_field(row.get("currencies") or "")
                l_cur += CountryRepository.insert_monnaies(iso2, currencies)

                # frontières avec contrainte de symétrie
                borders = ETLUtils.split_csv_field(row.get("borders") or "")
                l_bor += CountryRepository.insert_borders(iso2, borders)

                # électricité: types 'C,F', plus voltage/frequency
                plug_types = ETLUtils.split_csv_field(row.get("elec_type") or "")
                voltage = (row.get("voltage") or "").strip()
                frequency = (row.get("frequency") or "").strip()
                l_elec += CountryRepository.insert_electricite(
                    iso2, plug_types, voltage, frequency
                )

            MySQLConnection.commit()
            print(f"Pays upsert: {inserted_pays}")
            print(
                f"Liaisons langues: {l_lang}, monnaies: {l_cur}, frontières: {l_bor}, électricité: {l_elec}"
            )

        except Exception as e:
            MySQLConnection.rollback()
            print(f"Erreur lors de l'insertion MySQL: {e}")
            raise
        finally:
            MySQLConnection.close()

    def run(self):
        """Exécute le pipeline ETL complet"""
        print("=== ETL COUNTRIES ===\n")

        # EXTRACTION
        print("--- PHASE EXTRACTION ---")
        try:
            df_csv = self.extract_csv()
            dict_json = self.extract_json()
            yaml_data = self.extract_yaml()
            df_elec = self.extract_elec_csv()
        except FileNotFoundError as e:
            print(e)
            return None

        # TRANSFORMATION
        print("\n--- PHASE TRANSFORMATION ---")
        df_transformed = self.transform(df_csv, dict_json, yaml_data, df_elec)

        # LOAD
        print("\n--- PHASE LOAD ---")
        self.load(df_transformed)

        try:
            MySQLConnection.connect()
            MySQLConnection.run_sql_script(str(self.alter_script_path))
            MySQLConnection.commit()
            print(f"Script SQL exécuté : {str(self.alter_script_path)}")
        except Exception as e:
            MySQLConnection.rollback()
            print(f"Erreur lors de l’exécution du script : {e}")
        finally:
            MySQLConnection.close()
        return df_transformed


def main():
    etl = CountryETL()
    return etl.run()


if __name__ == "__main__":
    df_result = main()
