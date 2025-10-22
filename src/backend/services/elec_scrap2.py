import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path


class CountryPlugsETL:
    """Scrape https://www.worldstandards.eu/electricity/plug-voltage-by-country/
    et produit src/db/normes_elec_pays.csv avec les colonnes:
      - country   (texte du <a> en column-1)
      - type      (liste des <a> en column-2 avant '(note...', ex: 'A,B,C')
      - voltage   (texte de column-3 sans parenthèses)
      - frequency (texte de column-4)
    """

    def __init__(self):
        self.url = "https://www.worldstandards.eu/electricity/plug-voltage-by-country/"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "keep-alive",
            }
        )
        # même logique d’arborescence que tes autres ETL
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.output_path = self.base_dir / "src" / "db" / "normes_elec_pays.csv"
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def extract(self) -> BeautifulSoup:
        r = self.session.get(self.url, timeout=30)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")

    @staticmethod
    def _strip_parentheses(text: str) -> str:
        # supprime toute portion " ( ... ) "
        s = re.sub(r"\s*\([^)]*\)", "", text or "")
        # normalise espaces autour des slashs
        s = re.sub(r"\s*/\s*", " / ", s)
        # condense espaces
        s = re.sub(r"\s{2,}", " ", s).strip()
        return s

    @staticmethod
    def _pre_note_html(td: BeautifulSoup) -> str:
        """Retourne l'HTML de column-2 avant '(note' (case-insensible)."""
        html = str(td)
        # on coupe dès '(note' pour exclure tout ce qui suit
        parts = re.split(r"\(note", html, flags=re.IGNORECASE)
        return parts[0] if parts else html

    def _types_from_td(self, td: BeautifulSoup) -> str:
        """Récupère les lettres de type (A, B, ...) avant '(note...)', jointes par des virgules."""
        pre_html = self._pre_note_html(td)
        tmp = BeautifulSoup(pre_html, "html.parser")
        types = [
            a.get_text(strip=True) for a in tmp.select("a") if a.get_text(strip=True)
        ]
        # filtre de sécurité: ne garder que A..Z (1 lettre) si besoin
        types = [t for t in types if re.fullmatch(r"[A-Z]", t)]
        return ",".join(types)

    def transform(self, soup: BeautifulSoup) -> pd.DataFrame:
        table = soup.select_one("#tablepress-1 tbody")
        if table is None:
            raise RuntimeError("Table #tablepress-1 introuvable.")
        rows = []
        for tr in table.select("tr"):
            td1 = tr.select_one("td.column-1")
            td2 = tr.select_one("td.column-2")
            td3 = tr.select_one("td.column-3")
            td4 = tr.select_one("td.column-4")

            if not (td1 and td2 and td3 and td4):
                continue

            a1 = td1.select_one("a")
            country_raw = a1.get_text(strip=True) if a1 else td1.get_text(strip=True)
            country = self._strip_parentheses(country_raw)

            type_list = self._types_from_td(td2)

            voltage_raw = td3.get_text(" ", strip=True)
            voltage = self._strip_parentheses(voltage_raw)

            frequency_raw = td4.get_text(" ", strip=True)
            frequency = self._strip_parentheses(
                frequency_raw
            )  # Supprime les parenthèses

            rows.append(
                {
                    "country": country,
                    "type": type_list,
                    "voltage": voltage,
                    "frequency": frequency,
                }
            )

        return pd.DataFrame(rows, columns=["country", "type", "voltage", "frequency"])

    def load(self, df: pd.DataFrame) -> Path:
        df.to_csv(self.output_path, index=False, encoding="utf-8")
        return self.output_path

    def run(self) -> pd.DataFrame:
        soup = self.extract()
        df = self.transform(soup)
        self.load(df)
        print(f"Enregistré {len(df)} lignes dans {self.output_path}")
        return df


def main():
    etl = CountryPlugsETL()
    etl.run()


if __name__ == "__main__":
    main()
