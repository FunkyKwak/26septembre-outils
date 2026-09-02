import os

from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import config
import rapprochement
from toolkit import input_files




class DropLineEdit(QLineEdit):

    file_dropped = Signal(str)

    def __init__(self):
        super().__init__()

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):

        urls = event.mimeData().urls()

        if urls:
            chemin = urls[0].toLocalFile()

            if chemin:
                self.setText(chemin)
                self.file_dropped.emit(chemin)


class MultiSelectList(QListWidget):

    TOUS = "Toutes les villes"

    def __init__(self):
        super().__init__()

        self.itemChanged.connect(self._item_changed)

    def definir_villes(self, villes):
        self.blockSignals(True)
        self.clear()

        # Option "Toutes"
        item = QListWidgetItem(self.TOUS)
        item.setFlags(
            item.flags() | Qt.ItemIsUserCheckable
        )
        item.setCheckState(Qt.Checked)

        self.addItem(item)

        # Villes
        for ville in sorted(
            set(villes),
            key=str.lower
        ):
            item = QListWidgetItem(ville)
            item.setFlags(
                item.flags() | Qt.ItemIsUserCheckable
            )
            item.setCheckState(Qt.Checked)

            self.addItem(item)

        self.blockSignals(False)

    def _item_changed(self, item):
        self.blockSignals(True)

        # "Toutes les villes"
        if item == self.item(0):

            coche = (
                item.checkState()
                == Qt.Checked
            )

            for i in range(1, self.count()):
                self.item(i).setCheckState(
                    Qt.Checked
                    if coche
                    else Qt.Unchecked
                )

        else:

            # Si une ville est décochée,
            # "Toutes" est décochée.
            if item.checkState() == Qt.Unchecked:
                self.item(0).setCheckState(
                    Qt.Unchecked
                )

            # Si toutes les villes sont cochées,
            # "Toutes" est cochée.
            else:

                toutes_cochees = all(
                    self.item(i).checkState()
                    == Qt.Checked
                    for i in range(1, self.count())
                )

                self.item(0).setCheckState(
                    Qt.Checked
                    if toutes_cochees
                    else Qt.Unchecked
                )

        self.blockSignals(False)

    def villes_selectionnees(self):
        """
        Retourne [] si "Toutes les villes" est sélectionné.
        Sinon retourne la liste des villes cochées.
        """

        if (
            self.count() == 0
            or self.item(0).checkState()
            == Qt.Checked
        ):
            return []

        return [
            self.item(i).text()
            for i in range(1, self.count())
            if self.item(i).checkState()
            == Qt.Checked
        ]


class Worker(QThread):

    progress = Signal(int)
    log = Signal(str)
    finished_ok = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        fichier_signataires,
        fichier_volontaires,
        fichier_villes,
        fichier_codes_postaux,
        dossier_sortie,
        villes_selectionnees,
        separer_fichiers,
    ):
        super().__init__()
        self.fichier_signataires = (fichier_signataires)
        self.fichier_volontaires = (fichier_volontaires)
        self.fichier_villes = fichier_villes
        self.fichier_codes_postaux = (fichier_codes_postaux)
        self.dossier_sortie = dossier_sortie
        self.villes_selectionnees = (villes_selectionnees)
        self.separer_fichiers = separer_fichiers

    def run(self):
        try:
            finished_message = rapprochement.executer(
                self.fichier_signataires,
                self.fichier_volontaires,
                self.fichier_villes,
                self.fichier_codes_postaux,
                self.dossier_sortie,
                self.villes_selectionnees,
                self.separer_fichiers,
                progress_callback=self.progress.emit,
                log_callback=self.log.emit,
            )
            self.finished_ok.emit(finished_message)

        except Exception as e:
            self.error.emit(f"{type(e).__name__}: {e}")


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signataires et volontaires les plus proches de chaque mobilisation")
        self.resize(750, 600)
        self.worker = None
        self._construire_interface()

    def _construire_interface(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # -----------------------------------------------------
        # Fichier signataires
        # -----------------------------------------------------
        layout.addWidget(QLabel("<b>Fichier des signataires</b>"))
        ligne = QHBoxLayout()
        self.fichier_signataires = DropLineEdit()
        self.fichier_signataires.setPlaceholderText("Choisir ou déposer le fichier CSV...")
        self.fichier_signataires.setText(os.getenv("DEFAULT_FICHIER_SIGNATAIRES", ""))
        bouton = QPushButton("Parcourir…")
        bouton.clicked.connect(self.choisir_signataires)
        ligne.addWidget(self.fichier_signataires)
        ligne.addWidget(bouton)
        layout.addLayout(ligne)

        # -----------------------------------------------------
        # Fichier volontaires
        # -----------------------------------------------------
        layout.addWidget(QLabel("<b>Fichier des volontaires</b>"))
        ligne = QHBoxLayout()
        self.fichier_volontaires = DropLineEdit()
        self.fichier_volontaires.setPlaceholderText("Choisir ou déposer le fichier CSV...")
        self.fichier_volontaires.setText(os.getenv("DEFAULT_FICHIER_VOLONTAIRES", ""))
        bouton = QPushButton("Parcourir…")
        bouton.clicked.connect(self.choisir_volontaires)
        ligne.addWidget(self.fichier_volontaires)
        ligne.addWidget(bouton)
        layout.addLayout(ligne)

        # -----------------------------------------------------
        # Fichier villes
        # -----------------------------------------------------
        layout.addWidget(QLabel("<b>Fichier des villes recensées</b>"))
        ligne = QHBoxLayout()
        self.fichier_villes = DropLineEdit()
        self.fichier_villes.setPlaceholderText("Choisir ou déposer le fichier CSV...")
        self.fichier_villes.setText(os.getenv("DEFAULT_FICHIER_VILLES", ""))
        bouton = QPushButton("Parcourir…")
        bouton.clicked.connect(self.choisir_villes)
        ligne.addWidget(self.fichier_villes)
        ligne.addWidget(bouton)
        layout.addLayout(ligne)

        # -----------------------------------------------------
        # Sélection villes
        # -----------------------------------------------------
        layout.addWidget(QLabel("<b>Villes à traiter</b>"))
        self.selection_villes = (MultiSelectList())
        self.selection_villes.setEnabled(False)
        layout.addWidget(self.selection_villes)
        self.fichier_villes.file_dropped.connect(self.charger_liste_villes)

        # -----------------------------------------------------
        # Dossier sortie
        # -----------------------------------------------------
        layout.addWidget(QLabel("<b>Dossier de sortie</b>"))
        ligne = QHBoxLayout()
        self.dossier_sortie = DropLineEdit()
        self.dossier_sortie.setPlaceholderText("Choisir le dossier de sortie...")
        self.dossier_sortie.setText(os.getenv("DEFAULT_DOSSIER_SORTIE", ""))
        bouton = QPushButton("Parcourir…")
        bouton.clicked.connect(self.choisir_dossier)
        ligne.addWidget(self.dossier_sortie)
        ligne.addWidget(bouton)
        layout.addLayout(ligne)

        # -----------------------------------------------------
        # Option fichiers séparés
        # -----------------------------------------------------
        self.separer_fichiers = QCheckBox("Créer un fichier CSV séparé pour chaque ville")
        layout.addWidget(self.separer_fichiers)

        # -----------------------------------------------------
        # Bouton lancement
        # -----------------------------------------------------
        self.bouton_lancer = QPushButton("Trouver les signataires/volontaires les plus proches des villes sélectionées")
        self.bouton_lancer.setMinimumHeight(40)
        self.bouton_lancer.clicked.connect(self.lancer)
        layout.addWidget(self.bouton_lancer)

        # -----------------------------------------------------
        # Progression
        # -----------------------------------------------------
        self.progression = QProgressBar()
        layout.addWidget(self.progression)

        # -----------------------------------------------------
        # Logs
        # -----------------------------------------------------
        layout.addWidget(QLabel("<b>Journal</b>"))
        self.logs = QListWidget()
        layout.addWidget(self.logs)
        self.setCentralWidget(widget)


        if self.fichier_villes.text():
            self.charger_liste_villes(self.fichier_villes.text())


    def log(self, message):
        self.logs.addItem(message)

    # =========================================================
    # CHOIX FICHIERS
    # =========================================================

    def choisir_signataires(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self,
            "Fichier des signataires",
            "",
            "Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )
        if chemin:
            self.fichier_signataires.setText(chemin)

    def choisir_volontaires(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self,
            "Fichier des volontaires",
            "",
            "Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )
        if chemin:
            self.fichier_volontaires.setText(chemin)

    def choisir_villes(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self,
            "Fichier des villes",
            "",
            "Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )

        if chemin:
            self.fichier_villes.setText(chemin)
            self.charger_liste_villes(chemin)

    def choisir_codes_postaux(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self,
            "Base officielle des codes postaux",
            "",
            "Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )
        if chemin:
            self.fichier_codes_postaux.setText(chemin)

    def choisir_dossier(self):
        chemin = QFileDialog.getExistingDirectory(self, "Dossier de sortie")
        if chemin:
            self.dossier_sortie.setText(chemin)

    # =========================================================
    # CHARGEMENT DES VILLES
    # =========================================================

    def charger_liste_villes(self, chemin):

        fichier_codes = (config.FICHIER_CODES_POSTAUX)

        if not fichier_codes:
            self.logs.addItem(
                "Sélectionnez d'abord la base "
                "des codes postaux."
            )
            return

        try:

            codes_postaux = input_files.read_csv_codes_postaux(fichier_codes, log=self.log)

            villes = input_files.read_csv_villes(chemin, codes_postaux, log=self.log)

            noms = [
                ville["ville"]
                for ville in villes
            ]

            self.selection_villes.definir_villes(noms)
            self.selection_villes.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de charger les villes :\n\n{e}"
            )

    # =========================================================
    # LANCEMENT
    # =========================================================

    def lancer(self):

        fichier_signataires = (self.fichier_signataires.text())
        fichier_volontaires = (self.fichier_volontaires.text())
        fichier_villes = (self.fichier_villes.text())
        fichier_codes = (config.FICHIER_CODES_POSTAUX)
        dossier_sortie = (self.dossier_sortie.text())

        if not fichier_signataires and not fichier_volontaires:
            QMessageBox.warning(
                self,
                "Fichier manquant",
                "Sélectionnez le fichier des signataires ou des volontaires."
            )
            return

        if not fichier_villes:
            QMessageBox.warning(
                self,
                "Fichier manquant",
                "Sélectionnez le fichier des villes."
            )
            return

        if not fichier_codes:
            QMessageBox.warning(
                self,
                "Fichier manquant",
                "Sélectionnez la base des codes postaux."
            )
            return

        if not dossier_sortie:
            QMessageBox.warning(
                self,
                "Dossier manquant",
                "Sélectionnez le dossier de sortie."
            )
            return

        villes = (self.selection_villes.villes_selectionnees())

        self.logs.clear()
        self.progression.setValue(0)

        self.bouton_lancer.setEnabled(False)

        self.worker = Worker(
            fichier_signataires,
            fichier_volontaires,
            fichier_villes,
            fichier_codes,
            dossier_sortie,
            villes,
            self.separer_fichiers.isChecked(),
        )

        self.worker.progress.connect(self.progression.setValue)
        self.worker.log.connect(self.logs.addItem)
        self.worker.finished_ok.connect(self.termine)
        self.worker.error.connect(self.erreur)
        self.worker.start()

    def termine(self, message=""):
        self.bouton_lancer.setEnabled(True)
        QMessageBox.information(
            self,
            "Terminé",
            message
        )

    def erreur(self, message):
        self.bouton_lancer.setEnabled(True)
        QMessageBox.critical(
            self,
            "Erreur",
            message
        )


if __name__ == "__main__":

    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec()