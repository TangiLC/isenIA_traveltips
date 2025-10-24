import os
import signal
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait


class MonoRepoLauncher:
    """
    Mais pourquoi faire ça ?
       Pour appliquer le multi-threading
    Est-ce nécessaire et plus efficace que lancer indépendamment les deux serveurs ou avec Docker ?
       Ni l'un ni l'autre
    Donc c'est indispensable !
    """

    def __init__(self):
        root = Path(__file__).resolve().parent
        self.targets = [
            {"path": root / "backend" / "fastapi_main.py", "type": "python"},
            {"path": root / "streamlit_front" / "app.py", "type": "streamlit"},
        ]
        self.processes = []

    def run_script(self, target: dict):
        path = target["path"]

        if target["type"] == "streamlit":
            # Lancer avec streamlit run
            cmd = ["streamlit", "run", str(path.name)]
        else:
            # Lancer avec python
            cmd = [sys.executable, "-u", str(path)]

        p = subprocess.Popen(
            cmd,
            cwd=path.parent,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        self.processes.append(p)
        return p.wait()

    def stop(self, *_):
        print("\n🛑 Arrêt des serveurs...")
        for p in self.processes:
            if p.poll() is None:
                p.terminate()

        for p in self.processes:
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()

        print("✅ Tous les serveurs sont arrêtés")

    def start(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        print("🚀 Démarrage des serveurs...")
        print(f"   - Backend FastAPI: {self.targets[0]['path']}")
        print(f"   - Frontend Streamlit: {self.targets[1]['path']}")

        with ThreadPoolExecutor(max_workers=len(self.targets)) as pool:
            futures = [pool.submit(self.run_script, t) for t in self.targets]
            wait(futures)


if __name__ == "__main__":
    MonoRepoLauncher().start()
