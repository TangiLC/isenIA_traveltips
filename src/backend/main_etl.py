"""
Orchestrateur principal pour l'exécution des ETL
Gère l'ordre des dépendances et le multithreading pour les ETL indépendants
"""

import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable, Dict, List, Tuple

from services.etl import (
    elec_scrap2,
    etl_conversations,
    etl_countries,
    etl_currencies,
    etl_elec1,
    etl_langues,
    etl_meteo,
    etl_villes,
)

# Ajout du chemin pour les imports
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


class ETLOrchestrator:
    """Orchestrateur pour l'exécution séquentielle et parallèle des ETL"""

    def __init__(self):
        self.results: Dict[str, bool] = {}
        self.errors: Dict[str, Exception] = {}
        self.start_time = None
        self.end_time = None

    def _log(self, message: str, level: str = "INFO"):
        """Logger simple avec timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "INFO": "34m",
            "SUCCESS": "32m",
            "ERROR": "31m",
            "WARNING": "33m",
            "START": "44m",
            "END": "7m",
        }.get(level, "  ")
        print(f"\033[{prefix}{timestamp} : {message}\033[0m")

    def _execute_etl(
        self, name: str, etl_func: Callable
    ) -> Tuple[str, bool, Exception]:
        """Exécute un ETL et capture le résultat"""
        try:
            self._log(f"Démarrage de {name}", "START")
            result = etl_func()
            self._log(f"{name} terminé avec succès", "SUCCESS")
            return name, True, None
        except Exception as e:
            self._log(f"Erreur dans {name}: {str(e)}", "ERROR")
            return name, False, e

    def run_parallel(
        self, etl_configs: List[Tuple[str, Callable]], max_workers: int = 2
    ):
        """Exécute plusieurs ETL en parallèle"""
        self._log(
            f"Exécution parallèle de {len(etl_configs)} ETL avec {max_workers} threads",
            "INFO",
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._execute_etl, name, func): name
                for name, func in etl_configs
            }

            for future in as_completed(futures):
                name, success, error = future.result()
                self.results[name] = success
                if error:
                    self.errors[name] = error

    def run_sequential(self, etl_configs: List[Tuple[str, Callable]]):
        """Exécute plusieurs ETL de manière séquentielle"""
        self._log(f"Exécution séquentielle de {len(etl_configs)} ETL", "INFO")

        for name, func in etl_configs:
            name, success, error = self._execute_etl(name, func)
            self.results[name] = success
            if error:
                self.errors[name] = error

    def run_all(self):
        """Exécute tous les ETL dans l'ordre des dépendances"""
        self.start_time = datetime.now()
        self._log("=" * 80, "INFO")
        self._log("DÉMARRAGE DU PIPELINE ETL COMPLET", "START")
        self._log("=" * 80, "INFO")

        # Phase 1: ETL indépendants en parallèle (batch 1)
        self._log("\n### PHASE 1: ETL Indépendants (Batch 1) ###", "INFO")
        phase1_batch1 = [
            ("ETL Currencies", etl_currencies.main),
            ("ETL Conversations", etl_conversations.main),
        ]
        self.run_parallel(phase1_batch1, max_workers=2)

        # Phase 1: ETL indépendants en parallèle (batch 2)
        self._log("\n### PHASE 1: ETL Indépendants (Batch 2) ###", "INFO")
        phase1_batch2 = [
            ("ETL Scraping Électricité", elec_scrap2.main),
            ("ETL Langues", etl_langues.main),
        ]
        self.run_parallel(phase1_batch2, max_workers=2)

        # Phase 2: ETL avec dépendances - Électricité
        self._log("\n### PHASE 2: ETL Électricité (images) ###", "INFO")
        phase2 = [
            ("ETL Plug Types", etl_elec1.main),
        ]
        self.run_sequential(phase2)

        # Phase 3: ETL Villes (indépendant de countries)
        self._log("\n### PHASE 3: ETL Villes ###", "INFO")
        phase3 = [
            ("ETL Villes", etl_villes.main),
        ]
        self.run_sequential(phase3)

        # Phase 4: ETL Countries (dépend de currencies, langues, élec)
        self._log("\n### PHASE 4: ETL Countries (final) ###", "INFO")
        phase4 = [
            ("ETL Countries", etl_countries.main),
        ]
        self.run_sequential(phase4)

        # Phase 5: ETL Météo (dépend de villes)
        self._log("\n### PHASE 5: ETL Météo ###", "INFO")

        phase5 = [("ETL Météo", etl_meteo.main)]
        self.run_sequential(phase5)

        # Fin du pipeline
        self.end_time = datetime.now()
        self._print_summary()

    def _print_summary(self):
        """Affiche un résumé de l'exécution"""
        duration = self.end_time - self.start_time

        self._log("\n" + "=" * 80, "INFO")
        self._log("RÉSUMÉ DU PIPELINE ETL", "END")
        self._log("=" * 80, "INFO")

        self._log(f"Durée totale: {duration}", "INFO")
        self._log(f"ETL exécutés: {len(self.results)}", "INFO")

        successes = sum(1 for v in self.results.values() if v)
        failures = len(self.results) - successes

        self._log(f"Succès: {successes}", "SUCCESS")
        if failures > 0:
            self._log(f"Échecs: {failures}", "ERROR")

        # Détail des échecs
        if self.errors:
            self._log("\nDétail des erreurs:", "ERROR")
            for name, error in self.errors.items():
                self._log(f"  - {name}: {str(error)}", "ERROR")

        # Statut final
        if failures == 0:
            self._log("\nPipeline ETL terminé avec succès!", "SUCCESS")
        else:
            self._log(f"\nPipeline ETL terminé avec {failures} erreur(s)", "WARNING")

        self._log("=" * 80, "INFO")


def main():
    """Point d'entrée principal"""
    orchestrator = ETLOrchestrator()

    try:
        orchestrator.run_all()
    except KeyboardInterrupt:
        print("\nPipeline interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\nErreur fatale: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
