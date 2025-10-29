import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import openmeteo_requests
import pandas as pd
import requests
import requests_cache
from retry_requests import retry
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from models.week_meteo import WeekMeteo
from src.backend.orm.week_meteo_orm import WeekMeteoRepository
from utils.utils import ETLUtils


@dataclass
class MeteoETL:
    start_date: str  # "YYYY-MM-DD"
    end_date: str  # "YYYY-MM-DD"
    timezone: str = "UTC"
    use_cache: bool = True
    batch_size: int = 40  # Nombre de villes par batch
    api_delay: float = 0.35  # Délai entre appels API (secondes)
    max_retries: int = 3  # Tentatives max par ville

    # Internes
    client: Optional[openmeteo_requests.Client] = None
    session: Optional[requests.Session] = None
    daily_df: Optional[pd.DataFrame] = None
    weekly_df: Optional[pd.DataFrame] = None
    villes_df: Optional[pd.DataFrame] = None

    def __post_init__(self):
        if self.use_cache:
            cache = requests_cache.CachedSession(".openmeteo_cache", expire_after=3600)
            self.session = retry(cache, retries=3, backoff_factor=0.2)
        else:
            self.session = retry(
                requests_cache.CachedSession(), retries=3, backoff_factor=0.2
            )
        self.client = openmeteo_requests.Client(session=self.session)

    # ======================= EXTRACT =======================
    def extract_from_csv(
        self, csv_path: Optional[Path] = None, skip_existing: bool = False
    ) -> pd.DataFrame:
        """
        Charge les villes depuis un CSV (par défaut: ROOT/src/db/villes.csv).
        Prépare self.villes_df avec colonnes ['geoname_id', 'latitude', 'longitude'].

        Args:
            csv_path: Chemin vers le CSV des villes
            skip_existing: Si True, exclut les villes déjà présentes dans Meteo_Weekly
        """
        if csv_path is None:
            csv_path = ROOT.parent / "db" / "villes.csv"

        df = pd.read_csv(csv_path)

        # Vérification de schéma (insensible à la casse)
        lower_cols = {c.lower(): c for c in df.columns}
        required = {"geoname_id", "latitude", "longitude"}
        missing = required - set(lower_cols.keys())
        if missing:
            raise ValueError(
                f"Colonnes manquantes dans {csv_path}: {', '.join(sorted(missing))}"
            )

        s = df[
            [lower_cols["geoname_id"], lower_cols["latitude"], lower_cols["longitude"]]
        ].copy()
        s.columns = ["geoname_id", "latitude", "longitude"]

        # Nettoyage
        s = s.dropna(subset=["geoname_id", "latitude", "longitude"])
        s["geoname_id"] = s["geoname_id"].astype(int)
        s["latitude"] = s["latitude"].astype(float)
        s["longitude"] = s["longitude"].astype(float)
        s = s.drop_duplicates(subset=["geoname_id"]).reset_index(drop=True)

        initial_count = len(s)

        # Filtrage des villes déjà présentes en base
        if skip_existing:
            existing_ids = self._get_existing_geoname_ids()
            if existing_ids:
                s = s[~s["geoname_id"].isin(existing_ids)].reset_index(drop=True)
                skipped = initial_count - len(s)
                print(f"{skipped} villes déjà en base (ignorées)")

        self.villes_df = s
        print(f"{len(s)} villes chargées depuis {csv_path}")
        return self.villes_df

    def _get_existing_geoname_ids(self) -> set:
        """
        Récupère la liste des geoname_id déjà présents dans Meteo_Weekly.
        Renvoie un set vide si la table est vide ou n'existe pas.
        """
        try:
            existing = WeekMeteoRepository.get_existing_geoname_ids()
            print(f"{len(existing)} villes trouvées en base")
            return existing
        except Exception as e:
            print(f"Impossible de récupérer les villes existantes: {e}")
            return set()

    def fetch_data_for_ville(
        self, latitude: float, longitude: float, geoname_id: int
    ) -> Optional[pd.DataFrame]:
        """
        Appelle l'Archive API d'Open-Meteo pour une ville avec retry.
        Renvoie un DataFrame quotidien ou None en cas d'échec définitif.
        """
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
            ],
            "timezone": self.timezone,
        }

        for attempt in range(self.max_retries):
            try:
                responses = self.client.weather_api(url, params=params)
                om = responses[0]
                daily = om.Daily()

                # Variables par ordre de requête
                tmax = daily.Variables(0).ValuesAsNumpy()
                tmin = daily.Variables(1).ValuesAsNumpy()
                prcp = daily.Variables(2).ValuesAsNumpy()

                start = pd.to_datetime(daily.Time(), unit="s")
                end = pd.to_datetime(daily.TimeEnd(), unit="s")
                step = pd.Timedelta(seconds=daily.Interval())
                dates = pd.date_range(start=start, end=end - step, freq=step)

                df = pd.DataFrame(
                    {
                        "date": dates,
                        "tmax": tmax,
                        "tmin": tmin,
                        "precip_sum": prcp,
                    }
                ).sort_values("date")

                df["geoname_id"] = int(geoname_id)
                df["lat"] = float(latitude)
                df["lon"] = float(longitude)
                df["date"] = pd.to_datetime(df["date"]).dt.date

                print(f"Données météo récupérées pour la ville id {int(geoname_id)}")
                return df

            except Exception as e:
                wait_time = 5**attempt  # Backoff exponentiel: 5s, 10s, 15s
                if attempt < self.max_retries - 1:
                    print(
                        f"Tentative {attempt+1}/{self.max_retries} échouée pour ville {geoname_id}, "
                        f"retry dans {wait_time}s... ({e})"
                    )
                    time.sleep(wait_time)
                else:
                    print(f"Échec définitif pour ville {int(geoname_id)}: {e}")
                    return None

    # ======================= TRANSFORM =======================
    def transform_weekly_14d(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Produit des agrégats glissants sur 14 jours, puis échantillonne par semaine ISO.
        Calcule week_start_date et week_end_date (période de 14 jours).

        Règles :
          - tmax_14d_avg, tmin_14d_avg : moyenne mobile 14j
          - precip_14d_sum : somme mobile 14j
          - week_start_date : date - 13 jours (début de la fenêtre)
          - week_end_date : date (fin de la fenêtre)
        """
        s = df.copy()
        s["date"] = pd.to_datetime(s["date"])
        s = s.set_index("date").sort_index()

        win = 14
        s["tmax_14d_avg"] = s["tmax"].rolling(window=win, min_periods=7).mean()
        s["tmin_14d_avg"] = s["tmin"].rolling(window=win, min_periods=7).mean()
        s["precip_14d_sum"] = s["precip_sum"].rolling(window=win, min_periods=7).sum()

        # Calculer les dates de début/fin de période
        s = s.reset_index()
        s["week_end_date"] = s["date"]
        s["week_start_date"] = s["date"] - pd.Timedelta(days=13)

        # Une seule ligne par semaine ISO (on garde la dernière date de chaque semaine)
        s["iso_year"], s["iso_week"] = zip(*s["date"].apply(ETLUtils.iso_week_key))
        idx = s.groupby(["geoname_id", "iso_year", "iso_week"])["date"].idxmax()
        weekly = s.loc[idx].sort_values(["geoname_id", "iso_year", "iso_week"])

        # Colonnes ordonnées
        weekly = weekly[
            [
                "geoname_id",
                "week_start_date",
                "week_end_date",
                "iso_year",
                "iso_week",
                "lat",
                "lon",
                "tmax_14d_avg",
                "tmin_14d_avg",
                "precip_14d_sum",
            ]
        ]

        return weekly

    # ======================= LOAD =======================
    def load_weekly(self, weekly_df: pd.DataFrame) -> int:
        """
        Charge/merge en base via bulk_upsert pour performance.
        Renvoie le nombre de lignes upsert.
        """
        if weekly_df.empty:
            return 0

        repo = WeekMeteoRepository()

        # Conversion en objets WeekMeteo
        items = []
        for _, r in weekly_df.iterrows():
            wm = WeekMeteo(
                geoname_id=int(r["geoname_id"]),
                week_start_date=pd.to_datetime(r["week_start_date"]).date(),
                week_end_date=pd.to_datetime(r["week_end_date"]).date(),
                temperature_max_avg=(
                    None if pd.isna(r["tmax_14d_avg"]) else float(r["tmax_14d_avg"])
                ),
                temperature_min_avg=(
                    None if pd.isna(r["tmin_14d_avg"]) else float(r["tmin_14d_avg"])
                ),
                precipitation_sum=(
                    None if pd.isna(r["precip_14d_sum"]) else float(r["precip_14d_sum"])
                ),
            )
            items.append(wm)

        # Insertion bulk (transaction unique)
        try:
            rows = repo.bulk_upsert(items)
            print(f"{rows} lignes upsert en base... attente 5s")
            time.sleep(5)
            return rows
        except Exception as e:
            print(f"Erreur bulk upsert: {e}")
            raise

    # ======================= ORCHESTRATION =======================
    def _get_batches(self, batch_size: int):
        """Générateur de batches de villes."""
        for i in range(0, len(self.villes_df), batch_size):
            yield self.villes_df.iloc[i : i + batch_size]

    def _process_batch(
        self, batch: pd.DataFrame
    ) -> Tuple[List[pd.DataFrame], List[pd.DataFrame]]:
        """
        Traite un batch de villes : Extract + Transform.
        Renvoie (daily_batch, weekly_batch).
        """
        daily_batch = []
        weekly_batch = []

        for idx, row in batch.iterrows():
            try:
                daily = self.fetch_data_for_ville(
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    geoname_id=row["geoname_id"],
                )

                if daily is not None:
                    weekly = self.transform_weekly_14d(daily)
                    daily_batch.append(daily)
                    weekly_batch.append(weekly)

                # Rate limiting prudent
                time.sleep(self.api_delay)

            except Exception as e:
                print(f"Erreur ville {row['geoname_id']}: {e}")
                # Continue avec les autres villes du batch

        return daily_batch, weekly_batch

    def _load_batch(self, weekly_batch: List[pd.DataFrame]) -> int:
        """Charge un batch complet en base."""
        if not weekly_batch:
            return 0

        weekly_df = pd.concat(weekly_batch, ignore_index=True)
        return self.load_weekly(weekly_df)

    def run(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Exécute l'ETL pour toutes les villes avec batching.
        Renvoie un tuple de DataFrames (daily, weekly) concaténés.

        Stratégie :
        - Traite les villes par batch (batch_size)
        - Load immédiat après chaque batch (résilience)
        - Continue même si des villes échouent
        """
        if self.villes_df is None:
            raise ValueError(
                "Aucune ville chargée. Exécutez extract_from_csv() avant run()."
            )

        print(f"Démarrage ETL pour {len(self.villes_df)} villes")
        print(f"Batch size: {self.batch_size} villes")
        print(f"Délai API: {self.api_delay}s entre appels\n")

        all_daily = []
        all_weekly = []
        total_loaded = 0
        batch_num = 0

        for batch in self._get_batches(self.batch_size):
            batch_num += 1
            print(f"\n--- Batch {batch_num} ({len(batch)} villes) ---")

            daily_batch, weekly_batch = self._process_batch(batch)
            all_daily.extend(daily_batch)
            all_weekly.extend(weekly_batch)

            # Load immédiat après chaque batch
            loaded = self._load_batch(weekly_batch)
            total_loaded += loaded
            print(f"Batch {batch_num} terminé : {loaded} lignes chargées")

        # Concaténation finale
        self.daily_df = (
            pd.concat(all_daily, ignore_index=True) if all_daily else pd.DataFrame()
        )
        self.weekly_df = (
            pd.concat(all_weekly, ignore_index=True) if all_weekly else pd.DataFrame()
        )

        print(f"\nETL terminé : {total_loaded} lignes totales en base")
        return self.daily_df, self.weekly_df

    def print_summary(self) -> None:
        """Affiche un résumé de l'ETL."""
        if self.daily_df is None or self.weekly_df is None:
            print("Pas de données à résumer. Exécutez run() d'abord.")
            return

        d0 = ETLUtils.to_date(self.start_date)
        d1 = ETLUtils.to_date(self.end_date)
        nb_villes = self.daily_df["geoname_id"].nunique()

        print("\n" + "=" * 60)
        print("RÉSUMÉ ETL MÉTÉO")
        print("=" * 60)
        print(f"Période       : {d0} → {d1}")
        print(f"Villes traitées : {nb_villes}/{len(self.villes_df)}")
        print(f"Jours         : {len(self.daily_df)} lignes")
        print(f"Semaines      : {len(self.weekly_df)} lignes (échantillonnées)")
        print("=" * 60 + "\n")


# ======================= ENTRÉE SCRIPT =======================
def main():
    """Fonction principale pour exécuter l'ETL météo"""
    etl = MeteoETL(
        start_date="2024-01-01",
        end_date="2024-12-31",
        timezone="Europe/Paris",
        batch_size=40,
        api_delay=0.35,
    )

    # Extract
    etl.extract_from_csv(skip_existing=True)
    # Transform + Load (avec batching automatique)
    daily_df, weekly_df = etl.run()
    # Résumé
    etl.print_summary()

    return daily_df, weekly_df


if __name__ == "__main__":
    main()
