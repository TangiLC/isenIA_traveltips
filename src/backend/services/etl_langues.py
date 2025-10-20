import pandas as pd
import os
from pathlib import Path


class LanguageETL:
    """Classe pour gérer l'ETL des langues ISO 639"""

    def __init__(self):
        """Initialisation des chemins de fichiers"""
        # Le fichier Python est dans ./src/backend/services
        # On remonte de 3 niveaux pour atteindre la racine du projet
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.iso1_path = self.base_dir / "raw_sources" / "iso_639-1.csv"
        self.iso2_path = self.base_dir / "raw_sources" / "iso_639-2.csv"
        self.output_path = self.base_dir / "src" / "db" / "iso_languages.csv"

    def extract_csv_to_df(self, file_path):
        """Extraction d'un fichier CSV vers DataFrame

        Args:
            file_path (Path): chemin du fichier CSV

        Returns:
            pd.DataFrame: le DataFrame extrait
        """
        if not file_path.exists():
            raise FileNotFoundError(f"⌠Le fichier {file_path} n'existe pas.")

        df = pd.read_csv(file_path)
        print(f"✅ Fichier {file_path.name} chargé : {len(df)} lignes")
        return df

    def remove_rows_without_key(self, df, key_column):
        """Supprime les lignes sans valeur dans la colonne clé

        Args:
            df (pd.DataFrame): DataFrame à nettoyer
            key_column (str): nom de la colonne clé

        Returns:
            pd.DataFrame: DataFrame nettoyé
        """
        lignes_avant = len(df)
        df_cleaned = df.dropna(subset=[key_column])
        lignes_supprimees = lignes_avant - len(df_cleaned)
        return df_cleaned, lignes_supprimees

    def merge_dataframes(self, df1, df2, key_column):
        """Fusionne deux DataFrames sur une clé commune

        Args:
            df1 (pd.DataFrame): premier DataFrame
            df2 (pd.DataFrame): second DataFrame
            key_column (str): colonne de fusion

        Returns:
            pd.DataFrame: DataFrame fusionné
        """
        df_merged = pd.merge(df1, df2, on=key_column, how="inner")
        print(f"✅ Fusion réalisée : {len(df_merged)} lignes résultantes")
        return df_merged

    def select_and_rename_columns(self, df):
        """Sélectionne et renomme les colonnes

        Args:
            df (pd.DataFrame): DataFrame à traiter

        Returns:
            pd.DataFrame: DataFrame avec colonnes renommées
        """
        colonnes_a_garder = ["639-2", "name", "fr", "nativeName", "family"]

        # Vérifier que toutes les colonnes existent
        colonnes_manquantes = [
            col for col in colonnes_a_garder if col not in df.columns
        ]
        if colonnes_manquantes:
            print(f"⚠️  Colonnes manquantes : {colonnes_manquantes}")
            colonnes_a_garder = [col for col in colonnes_a_garder if col in df.columns]

        df_final = df[colonnes_a_garder].copy()

        # Renommage des colonnes
        df_final = df_final.rename(
            columns={
                "639-2": "639-2",
                "name": "name_en",
                "fr": "name_fr",
                "nativeName": "name_local",
                "family": "family",
            }
        )

        print(f"✅ Colonnes sélectionnées et renommées : {list(df_final.columns)}")
        return df_final

    def remove_duplicates(self, df):
        """Étape 6: Supprime les lignes en doublon

        Args:
            df (pd.DataFrame): DataFrame à traiter

        Returns:
            pd.DataFrame: DataFrame sans doublons
        """
        lignes_avant = len(df)
        df_no_dup = df.drop_duplicates()
        lignes_supprimees = lignes_avant - len(df_no_dup)
        print(f"✅ Étape 6 : {lignes_supprimees} doublon(s) supprimé(s)")
        return df_no_dup

    def split_multiple_values(self, df):
        """Étape 7: Convertit les séparateurs ";" en "," et conserve le premier élément

        Args:
            df (pd.DataFrame): DataFrame à traiter

        Returns:
            pd.DataFrame: DataFrame avec valeurs uniques
        """
        colonnes_a_traiter = ["name_en", "name_fr", "name_local"]

        for col in colonnes_a_traiter:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(";", ",")
                    .str.split(",")
                    .str[0]
                    .str.strip()
                )

        print("✅ Étape 7 : Valeurs multiples traitées (premier élément conservé)")
        return df

    def format_names(self, df):
        """Étape 8: Mise en forme des noms
        - name_en: Majuscule initiale (capitalize)
        - name_fr: tout en minuscules
        - name_local: pas de modification

        Args:
            df (pd.DataFrame): DataFrame à traiter

        Returns:
            pd.DataFrame: DataFrame formaté
        """
        if "name_en" in df.columns:
            df["name_en"] = df["name_en"].str.capitalize()

        if "name_fr" in df.columns:
            df["name_fr"] = df["name_fr"].str.lower()

        print("✅ Étape 8 : Formatage des noms appliqué")
        return df

    def transform(self, df_iso1, df_iso2):
        """Pipeline complet de transformation

        Args:
            df_iso1 (pd.DataFrame): DataFrame du fichier iso1.csv
            df_iso2 (pd.DataFrame): DataFrame du fichier iso2.csv

        Returns:
            pd.DataFrame: DataFrame transformé et nettoyé
        """
        print("\n--- DÉBUT DES TRANSFORMATIONS ---")

        # Vérification des données
        print(f"Colonnes ISO1 : {list(df_iso1.columns)}")
        print(f"Colonnes ISO2 : {list(df_iso2.columns)}")

        # Étape 1-2: Suppression des lignes sans clé "639-2"
        df_iso1_cleaned, supp_iso1 = self.remove_rows_without_key(df_iso1, "639-2")
        df_iso2_cleaned, supp_iso2 = self.remove_rows_without_key(df_iso2, "639-2")
        print(f"✅ ISO1 : {supp_iso1} ligne(s) sans '639-2' supprimée(s)")
        print(f"✅ ISO2 : {supp_iso2} ligne(s) sans '639-2' supprimée(s)")

        # Étape 3: Fusion
        df_merged = self.merge_dataframes(df_iso1_cleaned, df_iso2_cleaned, "639-2")

        # Étape 4-5: Sélection et renommage
        df_final = self.select_and_rename_columns(df_merged)

        # Étape 6: Suppression des doublons
        df_final = self.remove_duplicates(df_final)

        # Étape 7: Traitement des valeurs multiples
        df_final = self.split_multiple_values(df_final)

        # Étape 8: Formatage des noms
        df_final = self.format_names(df_final)

        print(
            f"✅ DataFrame final : {len(df_final)} lignes × {len(df_final.columns)} colonnes"
        )

        return df_final

    def load(self, df):
        """Étape 9: Sauvegarde du DataFrame dans le fichier de destination

        Args:
            df (pd.DataFrame): DataFrame à sauvegarder
        """
        # Créer le dossier de destination s'il n'existe pas
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(self.output_path, index=False, encoding="utf-8")
        print(f"\n✅ Étape 9 : Fichier sauvegardé : {self.output_path}")

    def run(self):
        """Exécute le pipeline ETL complet"""
        print("=== ETL LANGUES ISO 639 (POO) ===\n")

        # EXTRACTION
        print("--- PHASE EXTRACTION ---")
        try:
            df_iso1 = self.extract_csv_to_df(self.iso1_path)
            df_iso2 = self.extract_csv_to_df(self.iso2_path)
        except FileNotFoundError as e:
            print(e)
            print("\n⚠️  Assurez-vous que les fichiers sont présents.")
            return None

        # TRANSFORMATION
        print("\n--- PHASE TRANSFORMATION ---")
        df_transformed = self.transform(df_iso1, df_iso2)

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
    """Fonction principale pour exécuter l'ETL"""
    etl = LanguageETL()
    return etl.run()


if __name__ == "__main__":
    df_result = main()
