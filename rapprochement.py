import csv
from toolkit import coordinates
from collections import defaultdict

from toolkit import input_files


# ============================================================
# CONFIGURATION
# ============================================================

FICHIER_VOLONTAIRES = "csv\\test\\signataires-26septembre-2026-09-01.csv"
FICHIER_VILLES = "csv\\public\\recensements-26septembre-2026-09-01.csv"
FICHIER_CODES_POSTAUX = "csv\\public\\base-officielle-codes-postaux.csv"
FICHIER_SORTIE = "csv\\test\\OUT_volontaires_avec_ville.csv"



# ============================================================
# 1. CHARGEMENT DES COORDONNÉES DES CODES POSTAUX
# ============================================================
communes_par_code_postal = input_files.read_csv_codes_postaux(FICHIER_CODES_POSTAUX)


# ============================================================
# 2. CHARGEMENT DES VILLES RECENSÉES
# ============================================================
villes = input_files.read_csv_villes(FICHIER_VILLES)


# ============================================================
# 3. CHARGEMENT DES VOLONTAIRES
# ============================================================
volontaires, colonnes_originales = input_files.read_csv_volontaires(FICHIER_VOLONTAIRES)


# ============================================================
# 4. RECHERCHE DE LA VILLE LA PLUS PROCHE
# ============================================================

print("Recherche des villes les plus proches...")

resultats = []

nombre_sans_coordonnees = 0

for index, volontaire in enumerate(volontaires, start=1):

    code_postal = coordinates.normaliser_code_postal(
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

        distance = coordinates.distance_km(
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