import csv
import math
from collections import defaultdict


# ============================================================
# CONFIGURATION
# ============================================================

FICHIER_VOLONTAIRES = "csv\\test\\signataires-26septembre-2026-09-01.csv"
FICHIER_VILLES = "csv\\public\\recensements-26septembre-2026-09-01.csv"
FICHIER_CODES_POSTAUX = "csv\\public\\base-officielle-codes-postaux.csv"
FICHIER_SORTIE = "csv\\test\\OUT_volontaires_avec_ville.csv"


# ============================================================
# OUTILS
# ============================================================

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


# ============================================================
# 1. CHARGEMENT DES COORDONNÉES DES CODES POSTAUX
# ============================================================

print("Chargement de la base des codes postaux...")

# code postal -> liste de communes
communes_par_code_postal = defaultdict(list)

with open(
    FICHIER_CODES_POSTAUX,
    "r",
    encoding="utf-8-sig",
    newline=""
) as fichier:

    lecteur = csv.DictReader(fichier)

    for ligne in lecteur:
        code_postal = normaliser_code_postal(ligne["code_postal"])

        try:
            latitude = float(ligne["latitude"])
            longitude = float(ligne["longitude"])
        except (ValueError, TypeError):
            continue

        communes_par_code_postal[code_postal].append({
            "commune": ligne["nom_de_la_commune"],
            "latitude": latitude,
            "longitude": longitude,
        })


print(
    f"{len(communes_par_code_postal)} codes postaux chargés."
)


# ============================================================
# 2. CHARGEMENT DES VILLES DU FICHIER B
# ============================================================

print("Chargement des villes recensées...")

villes = []

with open(
    FICHIER_VILLES,
    "r",
    encoding="utf-8-sig",
    newline=""
) as fichier:

    # Le fichier commence par "sep=;" : on l'ignore
    premiere_ligne = fichier.readline()

    lecteur = csv.DictReader(fichier, delimiter=";")
    #lecteur.line_number = 1  # Le fichier commence par "sep=;" : on l'ignore

    for ligne in lecteur:
        code_postal = normaliser_code_postal(ligne["Code postal"])

        communes = communes_par_code_postal.get(code_postal)

        if not communes:
            print(
                f"Attention : aucun géopoint trouvé pour "
                f"le code postal {code_postal} "
                f"({ligne['Ville']})"
            )
            continue

        # Pour B, on utilise également la première commune
        # correspondant au code postal.
        commune = communes[0]

        villes.append({
            "ville": ligne["Ville"],
            "code_postal": code_postal,
            "latitude": commune["latitude"],
            "longitude": commune["longitude"],
        })


print(f"{len(villes)} villes recensées chargées.")


# ============================================================
# 3. CHARGEMENT DES VOLONTAIRES
# ============================================================

print("Chargement des volontaires...")

volontaires = []

with open(
    FICHIER_VOLONTAIRES,
    "r",
    encoding="utf-8-sig",
    newline=""
) as fichier:

    # Le fichier commence par "sep=;" : on l'ignore
    premiere_ligne = fichier.readline()

    lecteur = csv.DictReader(fichier, delimiter=";")

    # On conserve exactement les colonnes originales de A
    colonnes_originales = lecteur.fieldnames

    for ligne in lecteur:
        volontaires.append(ligne)


print(f"{len(volontaires)} volontaires chargés.")


# ============================================================
# 4. RECHERCHE DE LA VILLE LA PLUS PROCHE
# ============================================================

print("Recherche des villes les plus proches...")

resultats = []

nombre_sans_coordonnees = 0

for index, volontaire in enumerate(volontaires, start=1):

    code_postal = normaliser_code_postal(
        volontaire["Code postal"]
    )

    communes = communes_par_code_postal.get(code_postal)

    if not communes:
        volontaire["Ville la plus proche"] = ""
        volontaire["Code postal ville"] = ""
        volontaire["Distance km"] = ""

        nombre_sans_coordonnees += 1
        resultats.append(volontaire)
        continue

    # --------------------------------------------------------
    # On choisit la première commune correspondant au CP.
    # --------------------------------------------------------

    commune = communes[0]

    latitude = commune["latitude"]
    longitude = commune["longitude"]

    # --------------------------------------------------------
    # Recherche de la ville B la plus proche
    # --------------------------------------------------------

    ville_proche = None
    distance_min = float("inf")

    for ville in villes:

        distance = distance_km(
            latitude,
            longitude,
            ville["latitude"],
            ville["longitude"],
        )

        if distance < distance_min:
            distance_min = distance
            ville_proche = ville

    # --------------------------------------------------------
    # Ajout du résultat
    # --------------------------------------------------------

    if ville_proche:
        volontaire["Ville la plus proche"] = ville_proche["ville"]
        volontaire["Code postal ville"] = ville_proche["code_postal"]
        volontaire["Distance km"] = f"{distance_min:.1f}".replace(".", ",")
    else:
        volontaire["Ville la plus proche"] = ""
        volontaire["Code postal ville"] = ""
        volontaire["Distance km"] = ""

    resultats.append(volontaire)

    if index % 100 == 0:
        print(f"  {index}/{len(volontaires)} volontaires traités")


# ============================================================
# 5. ÉCRITURE DU CSV FINAL
# ============================================================

print("Écriture du fichier résultat...")

colonnes_sortie = list(colonnes_originales) + [
    "Ville la plus proche",
    "Code postal ville",
    "Distance km",
]

with open(
    FICHIER_SORTIE,
    "w",
    encoding="utf-8-sig",
    newline=""
) as fichier:

    ecrivain = csv.DictWriter(
        fichier,
        fieldnames=colonnes_sortie,
        delimiter=";",
        extrasaction="ignore",
    )

    ecrivain.writeheader()
    ecrivain.writerows(resultats)


# ============================================================
# 6. RÉSUMÉ
# ============================================================

print()
print("Terminé !")
print(f"Résultat : {FICHIER_SORTIE}")
print(f"Volontaires : {len(volontaires)}")

if nombre_sans_coordonnees:
    print(
        f"Sans coordonnées : {nombre_sans_coordonnees}"
    )