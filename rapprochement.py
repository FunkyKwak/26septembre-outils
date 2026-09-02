from asyncio import log
import csv
from toolkit import coordinates
from collections import defaultdict

from toolkit import input_files


def add_missing_cols (data, original_columns, missing_columns):
    for col in missing_columns:
        if col not in original_columns and col not in ("Type de contact", "Ville la plus proche", "Code postal ville", "Distance km"):
            data[col] = ""

def get_output_cols (signataire_columns=None, volontaire_columns=None):

    if signataire_columns and volontaire_columns:
        return ["Type de contact"] + list(signataire_columns) + [
            col for col in volontaire_columns if col not in signataire_columns
        ] + [
            "Ville la plus proche",
            "Code postal ville",
            "Distance km",
        ]
    elif signataire_columns:
        return list(signataire_columns) + [
            "Ville la plus proche",
            "Code postal ville",
            "Distance km",
        ]
    else:
        return list(volontaire_columns) + [
            "Ville la plus proche",
            "Code postal ville",
            "Distance km",
        ]


def extend_output_dicts(signataire_villes, volontaire_villes):
    persons_villes = defaultdict(list)

    for ville, signataires in signataire_villes.items():
        persons_villes[ville].extend(signataires)

    for ville, volontaires in volontaire_villes.items():
        persons_villes[ville].extend(volontaires)
    return persons_villes


def get_closest_city(persons, type,
                     communes_par_code_postal,
                     villes, villes_selectionnees,
                     signataire_columns=None, volontaire_columns=None,
                     log=None):

    if log is None:
        log = print

    log("Recherche des villes les plus proches...")
    
    person_villes = defaultdict(list)

    nombre_sans_coordonnees = 0

    for index, person in enumerate(persons, start=1):

        person["Type de contact"] = type

        if signataire_columns and volontaire_columns:
            if (type=="signataire"):
                person["Signé/Inscrit le"] = person["Signé le"]
                add_missing_cols(person, signataire_columns, volontaire_columns)
            if (type=="volontaire"):
                person["Signé/Inscrit le"] = person["Inscrit le"]
                add_missing_cols(person, volontaire_columns, signataire_columns)

        code_postal = coordinates.normaliser_code_postal(
            person["Code postal"]
        )

        communes = communes_par_code_postal.get(code_postal)

        if not communes:
            person["Ville la plus proche"] = ""
            person["Code postal ville"] = ""
            person["Distance km"] = ""

            nombre_sans_coordonnees += 1

            if (villes_selectionnees == []):
                person_villes["toutes_villes"].append(person)
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
            person["Ville la plus proche"] = ville_proche["ville"]
            person["Code postal ville"] = ville_proche["code_postal"]
            person["Distance km"] = f"{distance_min:.1f}".replace(".", ",")
        else:
            person["Ville la plus proche"] = ""
            person["Code postal ville"] = ""
            person["Distance km"] = ""

        if (villes_selectionnees == []):
            person_villes["toutes_villes"].append(person)
        elif (ville_proche["ville"] in villes_selectionnees):
            person_villes[ville_proche["ville"]].append(person)

        if index % 100 == 0:
            log(f"  {index}/{len(persons)} signataires traités")

    return person_villes, nombre_sans_coordonnees

def executer(
        fichier_signataires, fichier_volontaires, fichier_villes, fichier_codes_postaux,
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
    # 3. CHARGEMENT DES SIGNATAIRES / VOLONTAIRES
    # ============================================================
    signataire_columns, volontaire_columns = None, None
    signataires, volontaires = [], []
    if fichier_signataires:
        log("Chargement des signataires...")
        signataires, signataire_columns = input_files.read_csv_signataires(fichier_signataires)
        log(f"{len(signataires)} signataires chargés.")
        if fichier_volontaires:
            signataire_columns[signataire_columns.index("Signé le")] = "Signé/Inscrit le"

    if fichier_volontaires: 
        log("Chargement des volontaires...")
        volontaires, volontaire_columns = input_files.read_csv_volontaires(fichier_volontaires)
        log(f"{len(volontaires)} volontaires chargés.")
        if fichier_signataires:
            volontaire_columns[volontaire_columns.index("Inscrit le")] = "Signé/Inscrit le"

    # ============================================================
    # 4. RECHERCHE DE LA VILLE LA PLUS PROCHE
    # ============================================================

    signataire_villes, signataires_sans_coordonnees = get_closest_city(
        signataires, "signataire",
        communes_par_code_postal,
        villes, villes_selectionnees,
        signataire_columns, volontaire_columns,
        log
    )
    volontaire_villes, volontaires_sans_coordonnees = get_closest_city(
        volontaires, "volontaire",
        communes_par_code_postal,
        villes, villes_selectionnees,
        signataire_columns, volontaire_columns,
        log
    )

    persons_villes = extend_output_dicts(signataire_villes, volontaire_villes)


    # ============================================================
    # 5. ÉCRITURE DU CSV FINAL
    # ============================================================

    log("Écriture du fichier résultat...")

    colonnes_sortie = get_output_cols(signataire_columns, volontaire_columns)

    fichier_sorties = []

    if (fichier_signataires and fichier_volontaires):
        prefix = "signataires_volontaires"
    elif (fichier_signataires):
        prefix = "signataires"
    elif (fichier_volontaires):
        prefix = "volontaires"

    if separer_fichiers:
        for ville, person_ville in persons_villes.items():

            if ville:
                nom_fichier = f"{prefix}_{ville}.csv"
            else:
                nom_fichier = f"{prefix}_sans_ville.csv"

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
                ecrivain.writerows(person_ville)

            fichier_sorties.append(fichier_sortie)
    else:
        if (villes_selectionnees == []):
            fichier_sortie = dossier_sortie + f"/{prefix}_toutes_villes.csv"
        elif (len(villes_selectionnees) == 1):
            fichier_sortie = dossier_sortie + f"/{prefix}_{villes_selectionnees[0]}.csv"
        else:
            fichier_sortie = dossier_sortie + f"/{prefix}_villes_selectionnees.csv"

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
            for ville, person_ville in persons_villes.items():
                ecrivain.writerows(person_ville)

            fichier_sorties.append(fichier_sortie)


    # ============================================================
    # 6. RÉSUMÉ
    # ============================================================

    log("Terminé !")

    if len(fichier_sorties) == 1:
        rtn = f"Résultat : {fichier_sorties[0]}"
    else:
        rtn = f"Résultat : {len(fichier_sorties)} fichiers générés"
    log(rtn)
    log(f"Signataires : {len(signataires)}")
    log(f"Volontaires : {len(volontaires)}")

    if signataires_sans_coordonnees:
        log(f"Signataires sans coordonnées : {signataires_sans_coordonnees}")

    if volontaires_sans_coordonnees:
        log(f"Volontaires sans coordonnées : {volontaires_sans_coordonnees}")

    return rtn