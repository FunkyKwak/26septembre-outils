

import math


def distance_km(lat1, lon1, lat2, lon2):
    """
    Calcule la distance à vol d'oiseau entre deux coordonnées
    GPS avec la formule de Haversine.
    """
    rayon_terre_km = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * rayon_terre_km * math.asin(math.sqrt(a))


def normaliser_code_postal(code):
    """
    Normalise un code postal pour éviter les problèmes de
    valeurs comme 54000.0 ou espaces.
    """
    if not code:
        return ""

    code = str(code).strip()

    # Cas éventuel où Excel aurait transformé 54000 en 54000.0
    if code.endswith(".0"):
        code = code[:-2]

    # Les codes postaux français ont normalement 5 chiffres.
    # On complète éventuellement avec des zéros à gauche.
    return code.zfill(5)