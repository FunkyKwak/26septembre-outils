




from collections import defaultdict
import csv

from toolkit import coordinates


def  read_csv_codes_postaux(fichier_codes_postaux):

    print("Chargement de la base des codes postaux...")

    # code postal -> liste de communes
    communes_par_code_postal = defaultdict(list)

    with open(
        fichier_codes_postaux,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as fichier:

        lecteur = csv.DictReader(fichier)

        for ligne in lecteur:
            code_postal = coordinates.normaliser_code_postal(ligne["code_postal"])

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

    return communes_par_code_postal




def read_csv_villes(fichier_villes, communes_par_code_postal):
    
    print("Chargement des villes recensées...")

    villes = []

    with open(
        fichier_villes,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as fichier:

        # Le fichier commence par "sep=;" : on l'ignore
        premiere_ligne = fichier.readline()

        lecteur = csv.DictReader(fichier, delimiter=";")

        for ligne in lecteur:
            code_postal = coordinates.normaliser_code_postal(ligne["Code postal"])

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

    return villes



def read_csv_volontaires(fichier_volontaires):

    print("Chargement des volontaires...")

    volontaires = []

    with open(
        fichier_volontaires,
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

    return volontaires, colonnes_originales