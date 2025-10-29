import time
import re
import sys
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parents[3])
from connexion.mysql_connect import MySQLConnection
from src.backend.orm.electricity_orm import ElectriciteRepository
from utils.utils import ETLUtils


class PlugTypesETL:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parents[5]
        self.output_path = self.base_dir / "src" / "db" / "plug_types.csv"
        self.assets_dir = self.base_dir / "src" / "static" / "assets" / "elec"
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        self.base_url = "https://www.iec.ch"
        self.url = "https://www.iec.ch/world-plugs"

        # Session persistante pour conserver cookies + headers
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "keep-alive",
            }
        )

    # ---------- SCRAP ----------
    def extract(self) -> BeautifulSoup:
        # 1ère requête: récupère la page et initialise les cookies de session
        resp = self.session.get(self.url, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    def _find_target_container(self, soup: BeautifulSoup) -> BeautifulSoup:
        target_h3 = None
        for h3 in soup.select("h3.world-plugs-title"):
            if h3.get_text(strip=True) == "Plug Details":
                target_h3 = h3
                break
        if target_h3 is None:
            raise RuntimeError("Section 'Plug Details' introuvable.")
        container = target_h3.find_next("div", class_="world-plugs-plug-container")
        if container is None:
            raise RuntimeError("Conteneur '.world-plugs-plug-container' introuvable.")
        return container

    @staticmethod
    def _img_src(tag, base_url: str) -> str:
        src = tag.get("src") or tag.get("data-src") or ""
        return urljoin(base_url, src)

    def transform(self, soup: BeautifulSoup) -> pd.DataFrame:
        container = self._find_target_container(soup)
        items = container.select("div.item.plug-item-wrap")
        rows = []
        for it in items:
            title_tag = it.select_one("h4.plug-item-title")
            title = title_tag.get_text(strip=True) if title_tag else ""
            content = it.select_one("div.plug-item-content")
            if not content:
                continue
            imgs = content.select("img")
            while len(imgs) < 4:
                imgs.append(BeautifulSoup("<img>", "html.parser").img)
            rows.append(
                {
                    "Title": title,
                    "3d-plug": self._img_src(imgs[0], self.base_url),
                    "3d-sock": self._img_src(imgs[1], self.base_url),
                    "dia-plug": self._img_src(imgs[2], self.base_url),
                    "dia-sock": self._img_src(imgs[3], self.base_url),
                }
            )
        return pd.DataFrame(
            rows, columns=["Title", "3d-plug", "3d-sock", "dia-plug", "dia-sock"]
        )

    def load(self, df: pd.DataFrame) -> Path:
        """Sauvegarde du DataFrame dans le fichier CSV et MySQL via le Repository"""
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
                    # Extraction du type de prise depuis le titre (ex: "Plug type A" -> "A")
                    title = row.get("Title", "")
                    plug_type = self._suffix_from_title(title)

                    # Nom des fichiers images
                    plug_png = f"{plug_type}_plug.png"
                    sock_png = f"{plug_type}_sock.png"

                    # Insertion ou remplacement dans la base
                    rc = ElectriciteRepository.insert_ignore(
                        plug_type=plug_type,
                        plug_png=plug_png,
                        sock_png=sock_png,
                    )
                    if rc > 0:
                        inserted_count += 1
                        print(f"Type {plug_type} inséré")
                    else:
                        print(f"Type {plug_type} déjà existant")

                except Exception as e:
                    error_count += 1
                    print(f"Erreur pour {title}: {e}")

            MySQLConnection.commit()
            print(f"\nMySQL - {inserted_count} type(s) de prise(s) inséré(s)")
            if error_count > 0:
                print(f"{error_count} erreur(s) rencontrée(s)")

        except Exception as e:
            print(f"Erreur lors de l'insertion MySQL: {e}")
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()

        return self.output_path

    # ---------- DOWNLOAD ----------

    def _download_file(
        self, url: str, path: Path, max_retries: int = 3, sleep_s: float = 0.4
    ):
        # Ajoute un Referer explicite pour contourner le hotlinking
        headers = {
            "Referer": self.url,
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        }
        for attempt in range(1, max_retries + 1):
            try:
                r = self.session.get(
                    url, headers=headers, timeout=30, allow_redirects=True, stream=True
                )
                if r.status_code == 200:
                    path.write_bytes(r.content)
                    print(f"  OK {path.name}")
                    return True
                elif r.status_code in (301, 302, 303, 307, 308):
                    pass
                elif r.status_code == 403 and attempt < max_retries:
                    _ = self.session.get(self.url, timeout=30)
                else:
                    print(f"  HTTP {r.status_code} pour {url}")
                    return False
            except requests.RequestException as e:
                if attempt == max_retries:
                    print(f"  Erreur réseau finale pour {url}: {e}")
                    return False
            time.sleep(sleep_s)
        return False

    def download_images(self, df: pd.DataFrame):
        print(f"\n--- Téléchargement images: {len(df)} lignes ---")
        for _, row in df.iterrows():
            suffix = ETLUtils.suffix_from_title(row.get("Title", ""))
            plug_url = row.get("3d-plug", "")
            sock_url = row.get("3d-sock", "")

            if isinstance(plug_url, str) and plug_url.startswith("http"):
                self._download_file(plug_url, self.assets_dir / f"{suffix}_plug.png")
            if isinstance(sock_url, str) and sock_url.startswith("http"):
                self._download_file(sock_url, self.assets_dir / f"{suffix}_sock.png")

    # ---------- PIPELINE ----------
    def run(self):
        print("=== ETL PLUG TYPES ===\n")
        soup = self.extract()
        df = self.transform(soup)
        self.load(df)
        self.download_images(df)
        print(f"\n=== ETL TERMINÉ: {len(df)} entrées ===")
        return df


def main():
    etl = PlugTypesETL()
    return etl.run()


if __name__ == "__main__":
    main()
