import pandas as pd
import requests
import io
import sys
from pathlib import Path

# Ajouter le répertoire parent pour importer les modules
sys.path.append(str(Path(__file__).resolve().parents[1]))

from connexion.mongo_connect import MongoDBConnection
from repositories.conversation_repository import ConversationRepository

csv_url = "https://docs.google.com/spreadsheets/d/1hVa7vtHCc7WGkf0idxU0j5YWX0eX0jzavMR5GncG-nU/export?format=csv&gid=1711448956"

print("=== ETL Conversations - Extract, Transform, Load ===\n")

# ========================================
# EXTRACT - Chargement des données
# ========================================
print("📥 EXTRACT - Téléchargement du CSV...")
r = requests.get(csv_url, timeout=20)
r.raise_for_status()
df = pd.read_csv(io.BytesIO(r.content), header=None, encoding="utf-8")
print(f"✅ CSV téléchargé : {df.shape[0]} lignes x {df.shape[1]} colonnes\n")

# ========================================
# TRANSFORM - Nettoyage et transformation
# ========================================
print("🔄 TRANSFORM - Nettoyage des données...")

# 1) Nettoyage initial (suppr. entêtes/colonnes parasites)
df = (
    df.drop(index=[0, 1, 100, 122, 123, 158, 170, 171, 183, 184])
    .drop(columns=0)
    .reset_index(drop=True)
    .drop(index=1)
)

# 2) Transpose
df_t = df.transpose()

# 3) Première cellule = "lang639-2"
df_t.iloc[0, 0] = "lang639-2"

# 4) Promouvoir la première ligne comme en-têtes, puis l'enlever du corps
df_t.columns = df_t.iloc[0]
df_t = df_t.iloc[1:].reset_index(drop=True)

# 5) Supprimer les lignes vides (toutes cellules vides/NaN)
df_t = df_t.dropna(how="all")
df_t = df_t[~df_t.apply(lambda row: all(str(x).strip() == "" for x in row), axis=1)]

# 6) Ne garder que les lignes dont lang639-2 est un code ISO 3 lettres
first_col = df_t.columns[0]  # "lang639-2"
df_t[first_col] = df_t[first_col].astype(str).str.strip()
df_t = df_t[df_t[first_col].str.fullmatch(r"[A-Za-z]{3}", na=False)]
df_t[first_col] = df_t[first_col].str.lower()  # normalise en minuscules

# 7) Nettoyer les espaces et retours à la ligne
df_t = df_t.map(
    lambda x: (
        str(x).strip().replace("\n", " ").replace("\r", " ") if pd.notnull(x) else x
    )
)

print(f"✅ Transformation terminée : {len(df_t)} conversations valides\n")

# ========================================
# LOAD - Insertion dans MongoDB
# ========================================
print("💾 LOAD - Insertion dans MongoDB...")

try:
    # Connexion à MongoDB
    MongoDBConnection.connect()

    # Préparer les documents à insérer
    documents = []

    for _, row in df_t.iterrows():
        lang_code = row[first_col]
        row_clean = row.drop(labels=[first_col]).map(
            lambda v: None if pd.isna(v) else str(v).strip()
        )
        sentences = {k: v for k, v in row_clean.items() if v and v.lower() != "nan"}
        documents.append({"lang639-2": lang_code, "sentences": sentences})

    # Vider la collection avant l'import (optionnel - à adapter selon vos besoins)
    print(f"⚠️  Suppression des conversations existantes...")
    collection = MongoDBConnection.get_collection(
        ConversationRepository.COLLECTION_NAME
    )
    delete_result = collection.delete_many({})
    print(f"✅ {delete_result.deleted_count} documents supprimés\n")

    # Insertion en masse
    if documents:
        print(f"📤 Insertion de {len(documents)} conversations...")
        result = MongoDBConnection.insert_many(
            ConversationRepository.COLLECTION_NAME, documents
        )
        print(f"✅ {len(result.inserted_ids)} conversations insérées avec succès")

        # Afficher quelques exemples
        print("\n📋 Exemples de conversations insérées :")
        for i, doc in enumerate(documents[:3], 1):
            print(f"\n  {i}. Langue : {doc['lang639-2']}")
            print(f"     Nombre de phrases : {len(doc['sentences'])}")
            if doc["sentences"]:
                first_key = list(doc["sentences"].keys())[0]
                print(f"     Exemple : {first_key} = '{doc['sentences'][first_key]}'")
    else:
        print("⚠️  Aucune conversation à insérer")

    # Statistiques finales
    print("\n📊 Statistiques finales :")
    total = ConversationRepository.count_all()
    print(f"   Total conversations dans la base : {total}")

    stats_by_lang = ConversationRepository.aggregate_by_lang()
    print(f"   Nombre de langues : {len(stats_by_lang)}")

    if stats_by_lang:
        print("\n   Top 5 langues :")
        for stat in stats_by_lang[:5]:
            print(f"     - {stat['lang_code']} : {stat['count']} conversation(s)")

except Exception as e:
    print(f"❌ Erreur lors du chargement dans MongoDB : {e}")
    import traceback

    traceback.print_exc()
finally:
    MongoDBConnection.close()

print("\n✅ ETL terminé avec succès !")

# Export CSV optionnel (pour vérification)
output_filename = "conversation.csv"
df_t.to_csv(output_filename, index=False, encoding="utf-8-sig")
print(f"📁 Fichier CSV de vérification enregistré sous : {output_filename}")
