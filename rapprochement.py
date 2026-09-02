import csv
from toolkit import coordinates
from collections import defaultdict

from toolkit import input_files




def executer(
        fichier_volontaires, fichier_villes, fichier_codes_postaux,
        dossier_sortie,
        villes_selectionnees, separer_fichiers,
        progress_callback=None,
        log_callback=None
    ):


    def log(message):
        if log_callback:
            log_callback(message)

    def progress(value):
        if progress_callback:
            progress_callback(value)


    # ============================================================
    # 1. CHARGEMENT DES COORDONNÉES DES CODES POSTAUX
    # ============================================================
    log("Chargement de la base des codes postaux...")
    communes_par_code_postal = input_files.read_csv_codes_postaux(fichier_codes_postaux)
    log(f"{len(communes_par_code_postal)} codes postaux chargés.")


    # ============================================================
    # 2. CHARGEMENT DES VILLES RECENSÉES
    # ============================================================
    log("Chargement des villes recensées...")
    villes = input_files.read_csv_villes(fichier_villes, communes_par_code_postal)
    log(f"{len(villes)} villes recensées chargées.")


    # ============================================================
    # 3. CHARGEMENT DES VOLONTAIRES
    # ============================================================
    log("Chargement des volontaires...")
    volontaires, colonnes_originales = input_files.read_csv_volontaires(fichier_volontaires)
    log(f"{len(volontaires)} volontaires chargés.")


    # ============================================================
    # 4. RECHERCHE DE LA VILLE LA PLUS PROCHE
    # ============================================================

    log("Recherche des villes les plus proches...")

    resultats = defaultdict(list)

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

            if (villes_selectionnees == []):
                resultats["toutes_villes"].append(volontaire)
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

        if (villes_selectionnees == []):
            resultats["toutes_villes"].append(volontaire)
        elif (ville_proche["ville"] in villes_selectionnees):
            resultats[ville_proche["ville"]].append(volontaire)

        if index % 100 == 0:
            log(f"  {index}/{len(volontaires)} volontaires traités")


    # ============================================================
    # 5. ÉCRITURE DU CSV FINAL
    # ============================================================

    log("Écriture du fichier résultat...")

    colonnes_sortie = list(colonnes_originales) + [
        "Ville la plus proche",
        "Code postal ville",
        "Distance km",
    ]

    if separer_fichiers:
        for ville, volontaires_ville in resultats.items():

            if ville:
                nom_fichier = f"volontaires_{ville}.csv"
            else:
                nom_fichier = "volontaires_sans_ville.csv"

            fichier_sortie = dossier_sortie + "/" + nom_fichier

            with open(
                fichier_sortie,
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
                ecrivain.writerows(volontaires_ville)
    else:
        if (villes_selectionnees == []):
            fichier_sortie = dossier_sortie + "/volontaires_toutes_villes.csv"
        elif (len(villes_selectionnees) == 1):
            fichier_sortie = dossier_sortie + f"/volontaires_{villes_selectionnees[0]}.csv"
        else:
            fichier_sortie = dossier_sortie + "/volontaires_villes_selectionnees.csv"

        with open(
            fichier_sortie,
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
            for ville, volontaires_ville in resultats.items():
                ecrivain.writerows(volontaires_ville)


    # ============================================================
    # 6. RÉSUMÉ
    # ============================================================

    log("Terminé !")
    log(f"Résultat : {fichier_sortie}")
    log(f"Volontaires : {len(volontaires)}")

    if nombre_sans_coordonnees:
        log(f"Sans coordonnées : {nombre_sans_coordonnees}")