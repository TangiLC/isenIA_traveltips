import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from connexion.mongo_connect import MongoDBConnection
from repositories.conversation_repository import ConversationRepository


class ConversationETL:
    """Classe pour gérer l'ETL des conversations multilingues"""

    def __init__(self):
        """Initialisation des chemins de fichiers"""
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.source_path = self.base_dir / "raw_sources" / "RPB Main Phrases.csv"
        self.output_path = self.base_dir / "src" / "db" / "conversation.csv"

    def extract(self):
        """Extraction du fichier CSV vers DataFrame

        Returns:
            pd.DataFrame: DataFrame brut extrait
        """
        if not self.source_path.exists():
            raise FileNotFoundError(f"Le fichier {self.source_path} n'existe pas.")

        print(f"📥 EXTRACT - Chargement du fichier {self.source_path.name}...")
        df = pd.read_csv(self.source_path, header=None, encoding="utf-8")
        print(f"CSV chargé : {df.shape[0]} lignes x {df.shape[1]} colonnes\n")
        return df

    def transform(self, df):
        """Pipeline complet de transformation

        Args:
            df (pd.DataFrame): DataFrame brut à transformer

        Returns:
            pd.DataFrame: DataFrame transformé et nettoyé
        """
        print("🔄 TRANSFORM - Nettoyage des données...")

        # 1) Insérer "lang639-2" en case (2,1) avant tout nettoyage
        df.iloc[2, 1] = "lang639-2"

        # 2) Supprimer les 2 premières lignes (en-têtes)
        df = df.drop(index=[0, 1, 3]).reset_index(drop=True)

        # 3) Transpose
        df_t = df.transpose()

        # 4) Supprimer les lignes avec >95% de colonnes vides
        print("\n🔍 Analyse des lignes vides (>85% NaN)...")
        threshold = 0.85
        lignes_a_supprimer = []

        for idx in df_t.index:
            row = df_t.loc[idx]
            pct_vide = row.isna().sum() / len(row)
            if pct_vide > threshold:
                lignes_a_supprimer.append(idx)
                print(f"   Ligne {idx} -> {pct_vide*100:.1f}% vide")

        if lignes_a_supprimer:
            print(f"\n Lignes à supprimer (index originaux) : {lignes_a_supprimer}")
            df_t = df_t.drop(index=lignes_a_supprimer).reset_index(drop=True)

        # 5) Promouvoir la première ligne comme en-têtes, puis l'enlever du corps
        # df_t = df_t.drop(index=[0]).reset_index(drop=True)
        # df_t = df_t.drop(index=[0]).reset_index(drop=True)

        df_t = df_t.drop(index=[0]).reset_index(drop=True)
        print(f"Lignes 0-4 (4 premiers éléments) :\n{df_t.iloc[0:5, 0:4]}\n")
        df_t.columns = df_t.iloc[0]
        df_t = df_t.iloc[1:].reset_index(drop=True)

        # Supprimer les colonnes sans en-tête (vides ou NaN)
        df_t = df_t.loc[
            :, df_t.columns.notna() & (df_t.columns.astype(str).str.strip() != "")
        ]

        # 6) Supprimer les lignes vides restantes (toutes cellules vides/NaN)
        df_t = df_t.dropna(how="all")
        df_t = df_t[
            ~df_t.apply(lambda row: all(str(x).strip() == "" for x in row), axis=1)
        ]

        # 7) Ne garder que les lignes dont lang639-2 est un code ISO 3 lettres
        first_col = df_t.columns[0]  # "lang639-2"
        df_t[first_col] = df_t[first_col].astype(str).str.strip()
        df_t = df_t[df_t[first_col].str.fullmatch(r"[A-Za-z]{3}", na=False)]
        df_t[first_col] = df_t[first_col].str.lower()  # normalise en minuscules

        # 8) Nettoyer les espaces et retours à la ligne
        df_t = df_t.map(
            lambda x: (
                str(x).strip().replace("\n", " ").replace("\r", " ")
                if pd.notnull(x)
                else x
            )
        )

        print(f"Transformation terminée : {len(df_t)} conversations valides\n")
        return df_t

    def load(self, df):
        """Sauvegarde du DataFrame dans le fichier CSV et MongoDB

        Args:
            df (pd.DataFrame): DataFrame à sauvegarder
        """
        # 1. Sauvegarde CSV
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.output_path, index=False, encoding="utf-8")
        print(f"\nFichier CSV sauvegardé : {self.output_path}")

        # 2. Insertion dans MongoDB
        try:
            MongoDBConnection.connect()
            print("\n--- INSERTION DANS MONGODB ---")

            # Préparer les documents à insérer
            first_col = df.columns[0]  # "lang639-2"
            documents = []

            for _, row in df.iterrows():
                lang_code = row[first_col]
                row_clean = row.drop(labels=[first_col]).map(
                    lambda v: None if pd.isna(v) else str(v).strip()
                )
                sentences = {
                    str(k): v
                    for k, v in row_clean.items()
                    if pd.notna(k)
                    and str(k).strip()
                    and str(k).lower() != "nan"
                    and v
                    and v.lower() != "nan"
                }
                documents.append({"lang639-2": lang_code, "sentences": sentences})

            # Vider la collection avant l'import
            print(f" Suppression des conversations existantes...")
            collection = MongoDBConnection.get_collection(
                ConversationRepository.COLLECTION_NAME
            )
            delete_result = collection.delete_many({})
            print(f"{delete_result.deleted_count} documents supprimés")

            # Insertion en masse
            if documents:
                print(f"📤 Insertion de {len(documents)} conversations...")
                result = MongoDBConnection.insert_many(
                    ConversationRepository.COLLECTION_NAME, documents
                )
                print(f"{len(result.inserted_ids)} conversations insérées avec succès")
            else:
                print(" Aucune conversation à insérer")

        except Exception as e:
            print(f"Erreur lors de l'insertion MongoDB: {e}")
            import traceback

            traceback.print_exc()
            raise
        finally:
            MongoDBConnection.close()

    def run(self):
        """Exécute le pipeline ETL complet"""
        print("=== ETL CONVERSATIONS (POO) ===\n")

        # EXTRACTION
        print("--- PHASE EXTRACTION ---")
        try:
            df_raw = self.extract()
        except FileNotFoundError as e:
            print(e)
            print("\n Assurez-vous que le fichier est présent dans raw_sources/")
            return None
        except Exception as e:
            print(f"Erreur lors de l'extraction: {e}")
            return None

        # TRANSFORMATION
        print("--- PHASE TRANSFORMATION ---")
        df_transformed = self.transform(df_raw)

        # LOAD
        print("--- PHASE LOAD ---")
        self.load(df_transformed)

        # Affichage du résultat
        print("\n--- APERÇU DU RÉSULTAT FINAL ---")
        print(df_transformed.head(10))
        print(f"\nDimensions finales : {df_transformed.shape}")
        print("\n=== ETL TERMINÉ ===")

        return df_transformed


def main():
    """Fonction principale pour exécuter l'ETL"""
    etl = ConversationETL()
    return etl.run()


if __name__ == "__main__":
    df_result = main()
