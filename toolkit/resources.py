import os
import sys


def resource_path(relative_path):
    """
    Retourne le chemin absolu vers une ressource embarquée
    par PyInstaller ou vers une ressource du projet en développement.
    """

    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                ".."
            )
        )

    print(f"[RESOURCE] frozen={getattr(sys, 'frozen', False)}")
    print(f"[RESOURCE] base_path={base_path}")
    print(f"[RESOURCE] relative_path={relative_path}")
    print(f"[RESOURCE] exists={os.path.join(base_path, relative_path).exists()}")

    return os.path.join(base_path, relative_path)