#!/usr/bin/python3
# -*- coding: utf-8 -*-


#############################################################################
# Pyqt5
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

# Autres modules
import sys
from pathlib import Path # Necessaire pour la recherche de fichier
import configparser # Pour charger les informations de config
from functools import partial # Utilisé pour envoyer plusieurs infos via les connexions
import random # Permet de séléctionner un personnage pour l'ordinateur
from datetime import datetime # Pour le debug
from time import time # Pour le debug

from ui_Kiesse import Ui_Kiesse # Utilisé pour la fentre principale


KiesseVersion = 5.0


#========================================================================
def IconBis(Icon, Type):
    """Fonction créant le code pour afficher l'icone du theme avec une icone des ressources si la 1ere n'existe pas."""
    # http://standards.freedesktop.org/icon-theme-spec/icon-theme-spec-latest.html
    # http://standards.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html

    # Si l'icone existe dans le theme
    if QIcon().hasThemeIcon(Icon):
        # S'il faut un pixmap
        if Type == "Pixmap":
            return QPixmap(QIcon().fromTheme(Icon).pixmap(24))

        # S'il faut une icone
        elif Type == "Icon":
            return QIcon().fromTheme(Icon)

    # Si l'icone n'existe pas, on utilise celle des ressources
    else:
        # S'il faut un pixmap
        if Type == "Pixmap":
            return QPixmap(":/Icons/{}.png".format(Icon))

        # S'il faut une icone
        elif Type == "Icon":
            return QIcon(QPixmap(":/Icons/{}.png".format(Icon)))



#############################################################################
class Kiesse(QMainWindow):
    def __init__(self, parent=None):
        """Fonction d'initialisation appellée au lancement de la classe."""
        ### Commandes à ne pas toucher
        super(Kiesse, self).__init__(parent)
        self.ui = Ui_Kiesse()
        self.ui.setupUi(self) # Lance la fonction definissant tous les widgets du fichier UI
        self.show() # Affichage de la fenêtre principale


        ### Fichier de configuration
        self.PathHere = Path(sys.argv[0]).resolve().parent # Dossier actuel
        self.ConfigFolder = Path(QDir.homePath(), '.config/Kiesse')
        self.ConfigFile = Path(self.ConfigFolder, 'Kiesse.cfg')
        self.KiesseCfg= {}


        ### ATTENTION : Temporaire
        OldFile = Path(QDir.homePath(), '.config/Kiesse.cfg')
        if OldFile.exists():
            OldFile.unlink()


        ### Création du dossier de configuration
        if not Path(self.ConfigFolder, "Games").exists():
            Path(self.ConfigFolder, "Games").mkdir(mode=0o755, parents=True)


        ### Configs du logiciel
        # Pas de try car avec optionxform on a une liste vide, pas une erreur
        # Chargement des configs
        Config = configparser.ConfigParser() # Chargement du fichier de cfg
        Config.optionxform = lambda option: option # Conserve le nom des variables
        Config.read(str(self.ConfigFile)) # Lecture du fichier de cfg


        if len(Config['DEFAULT']) == 15:
            for Item, Value in Config['DEFAULT'].items():
                if Item in ["DebugMode", "WinMax", "DoubleOrNothing"]:
                    self.KiesseCfg[Item] = Config['DEFAULT'].getboolean(Item)

                elif Item in ["WithMax", "Width", "Height", "SizeCharacters", "NumberCharacters", "NumberColumns", "NumberPlayer"]:
                    self.KiesseCfg[Item] = int(Value)

                elif Item in ["ColorPlayer1", "ColorPlayer2"]:
                    self.KiesseCfg[Item] = QColor(Value)

                elif Item == 'ChoiceGame':
                    self.KiesseCfg[Item] = Path(Value)

                else:
                    self.KiesseCfg[Item] = Value

            # Resolution de la fenetre
            if self.KiesseCfg['Width'] != 630 and self.KiesseCfg['Height'] != 620:
                self.resize(self.KiesseCfg['Width'], self.KiesseCfg['Height']) # Resize de la fenetre si les valeurs sont differentes

        else:
            # Valeurs par defaut
            self.KiesseCfg= {}
            self.KiesseCfg['ChoiceGame'] = Path(self.PathHere, "Games/Faces")
            self.KiesseCfg['NumberColumns'] = 3
            self.KiesseCfg['NumberCharacters'] = 6
            self.KiesseCfg['SizeCharacters'] = 5
            self.KiesseCfg['NamePlayer1'] = "Player 1"
            self.KiesseCfg['ColorPlayer1'] = QColor("#0000FF")
            self.KiesseCfg['NamePlayer2'] = "Player 2"
            self.KiesseCfg['ColorPlayer2'] = QColor("#FF0000")
            self.KiesseCfg['DoubleOrNothing'] = True
            self.KiesseCfg['LangUi'] = QLocale.system().name()
            self.KiesseCfg['Width'] = 630
            self.KiesseCfg['Height'] = 620
            self.KiesseCfg['WinMax'] = False
            self.KiesseCfg['DebugMode'] = True
            self.KiesseCfg['NumberPlayer'] = 1 # N'est ii que pour eviter une fonction de plus


        ### Centrage de la fenêtre
        if self.KiesseCfg['WinMax']:
            self.showMaximized() # Maximise la fenetre
        else:
            SizeScreen = QDesktopWidget().screenGeometry() # Taille de l'ecran
            self.move((SizeScreen.width() - self.geometry().width()) / 2, (SizeScreen.height() - self.geometry().height()) / 2) # Place la fenetre en fonction de sa taille et de la taille de l'ecran


        ### Création de variables utiles par la suite
        self.ListeWidgetCharacters = [] # Création ici vide, afin d'eviter les erreurs lors de la 1ere partie
        self.InGame = False # Variable indiquant si une partie est commencée
        self.InOption = False # Variable indiquant si on est dans les options
        self.ScorePlayer1 = 0 # Variable indiquant le score du joueur 1
        self.ScorePlayer2 = 0 # Variable indiquant le score du joueur 2
        self.FisrtPlayer = 1 # Joueur commencant la partie
        self.QuestionsLang = "" # Nom de la section question à utiliser pour le fichier de config
        self.CurrentPlayer = 1 # joueur actuel
        self.BlockQuestion1 = [] # Variable indiquant les mot clés à ne pas prendre en charge
        self.BlockQuestion2 = [] # Variable indiquant les mot clés à ne pas prendre en charge
        self.ExtensionImages = None # Extension des images


        ### Redimensionnement du tableau des questions
        # Mise à jour du nom dans l'header
        self.ui.tableWidget.setHorizontalHeaderLabels(("Value", self.KiesseCfg['NamePlayer1'], "Question", self.KiesseCfg['NamePlayer2']))
        self.ui.tableWidget.hideColumn(0) # Cache la 1ere colonne
        Value = self.ui.tableWidget.size().width() - 165
        self.ui.tableWidget.setColumnWidth(1, 75) # Definit la colonne 1 à 25px
        self.ui.tableWidget.setColumnWidth(2, Value) # Definit la colonne 2 à 25px
        self.ui.tableWidget.setColumnWidth(3, 75) # Definit la colonne 2 à 25px
        self.ui.tableWidget.installEventFilter(self)


        ### Creation, implentation et connexion du bouton quiter dans la barre d'info
        self.ButtonQuit = QPushButton() # Création du bouton
        self.ButtonQuit.setIcon(IconBis("application-exit", "Icon")) # Affectation de l'icone au bouton
        self.ui.statusbar.addPermanentWidget(self.ButtonQuit) # Implentation du widget en fin de ligne


        ### Mise à jour des widgets en fonctions des variables
        for Item, Value in self.KiesseCfg.items():
            # Chargement de la langue
            if Item == 'LangUi':
                if "fr_" in Value:
                    self.ui.lang_francaise.setChecked(True) # Selection de la langue français
                    self.TranslationUi("fr_FR", False) # Necessaire car l'item ci-dessus n'est pas encore connecté
                else:
                    self.TranslationUi("en_EN", False) # Force le chargement de traduction si c'est la langue english (par defaut)

            # Gestion du nom du joueur 1
            elif Item == 'NamePlayer1':
                Palette = QPalette(self.ui.name_player1.palette()) # Création d'une palette de couleur pour la coloration du nom du perso
                Palette.setColor(QPalette.Text, self.KiesseCfg['ColorPlayer1']) # Envoie de la couleur
                self.ui.name_player1.setPalette(Palette) # Envoie de la couleur
                self.ui.name_player1.setText(self.KiesseCfg['NamePlayer1'])

            # Gestion du nom du joueur 2
            elif Item == 'NamePlayer2':
                Palette = QPalette(self.ui.name_player2.palette()) # Création d'une palette de couleur pour la coloration du nom du perso
                Palette.setColor(QPalette.Text, self.KiesseCfg['ColorPlayer2']) # Envoie de la couleur
                self.ui.name_player2.setPalette(Palette) # Envoie de la couleur
                self.ui.name_player2.setText(self.KiesseCfg['NamePlayer2'])

            # Gestion du nombre de colonnes
            elif Item == 'NumberColumns':
                self.ui.number_columns.setValue(self.KiesseCfg['NumberColumns'])

            # Gestion du nombre de personnages
            elif Item == 'NumberCharacters':
                self.ui.number_characters.setValue(self.KiesseCfg['NumberCharacters'])

            # Gestion de la taille des images
            elif Item == 'SizeCharacters':
                self.ui.size_characters.setValue(self.KiesseCfg['SizeCharacters'])

            # Gestion du type de jeu
            elif Item == 'DoubleOrNothing':
                self.ui.double_or_nothing.setChecked(self.KiesseCfg['DoubleOrNothing'])

            # Gestion du mode debug
            elif Item == 'DebugMode':
                self.ui.debug_mode.setChecked(self.KiesseCfg['DoubleOrNothing'])

                # Supprime les fichiers ayant plus de 48h
                for File in self.ConfigFolder.glob("2*"):
                    Date = int(File.stat().st_mtime)
                    if Date + 172800 < int(time()):
                        File.unlink()

        ### Création et implentation d'actions dans les menus
        # Création de la liste des jeux dispo
        ActionGroup = QActionGroup(self, exclusive=True) # Creation d'un actiongroup

        GameList = list()
        for Folder in Path(self.ConfigFolder / "Games").iterdir():
            if Folder.is_dir(): GameList.append(Folder)
        for Folder in Path(self.PathHere / "Games").iterdir():
            if Folder.is_dir(): GameList.append(Folder)

        for Folder in GameList:
            try:
                Config.read("{}/Config.cfg".format(Folder)) # Lecture du fichier de cfg
            except:
                QMessageBox(1, self.Translation["LoadGameErrorTitle"], self.Translation["LoadGameErrorText"].format(Folder), QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()
                continue

            # Recup de l'extension à utiliser
            ExtensionImages = Config["GAME"]["extension"]

            # Création d'une action avec une icone (1ere image du jeu) et l'adresse en statustip
            Icon = QIcon(str(list(Folder.glob("*." + ExtensionImages))[0]))
            Action = QAction(Icon, Folder.stem, self, checkable=True)
            Action.setStatusTip(str(Folder))

            # Coche si besoin l'action
            if Folder == self.KiesseCfg['ChoiceGame']: Action.setChecked(True)

            # Création de la connexion
            Action.triggered.connect(partial(self.ChoiceGameDef, Folder))

            # Ajout de l'action dans le menu
            self.ui.menu_Choix_du_jeu.addAction(ActionGroup.addAction(Action))


        ### Chargement du dossier des persos
        self.ChoiceGameDef(self.KiesseCfg['ChoiceGame'])


        ### Connexion des widgets
        # Options
        self.ui.size_characters.valueChanged['int'].connect(partial(self.VarDef, "SizeCharacters"))
        self.ui.number_characters.valueChanged['int'].connect(partial(self.VarDef, "NumberCharacters"))
        self.ui.number_columns.valueChanged['int'].connect(partial(self.VarDef, "NumberColumns"))
        self.ui.name_player1.textChanged.connect(partial(self.VarDef, "NamePlayer1"))
        self.ui.name_player2.textChanged.connect(partial(self.VarDef, "NamePlayer2"))
        self.ui.color_player1.clicked.connect(partial(self.VarDef, "ColorPlayer1", self.ui.name_player1))
        self.ui.color_player2.clicked.connect(partial(self.VarDef, "ColorPlayer2", self.ui.name_player2))
        self.ui.debug_mode.clicked.connect(partial(self.VarDef, "DebugMode"))
        self.ui.double_or_nothing.toggled.connect(partial(self.VarDef, "DoubleOrNothing"))
        self.ui.lang_english.triggered.connect(partial(self.VarDef, "LangUi", "en_EN"))
        self.ui.lang_francaise.triggered.connect(partial(self.VarDef, "LangUi", "fr_FR"))
        self.ui.jeu_1j.triggered.connect(partial(self.VarDef, "NumberPlayer", 1)) # Affiche la liste des persos parmis lesquels le J1 doit trouver le choix du J2
        self.ui.jeu_2j.triggered.connect(partial(self.VarDef, "NumberPlayer", 2)) # Affiche la liste des persos parmis lesquels le J2 doit trouver le choix du J1

        # Bouton quitter
        self.ButtonQuit.clicked.connect(self.close) # Boutons

        # Liste des questions
        self.ui.tableWidget.itemDoubleClicked.connect(self.ChoiceQuestion) # Au double clic sur les questions

        # Fenetres d'aide
        self.ui.about_qt.triggered.connect(lambda: QMessageBox.aboutQt(Kiesse)) # A propos de Qt
        self.ui.about_kiesse.triggered.connect(lambda: QMessageBox.about(self, self.Translation["AboutTitle"].format(KiesseVersion), self.Translation["AboutText"])) # A propos de Qt
        self.ui.about_game.triggered.connect(self.AboutGame)

        # Changement de page
        self.ui.page_du_j1.triggered.connect(lambda: self.ui.j1_j2.setCurrentIndex(0))
        self.ui.page_du_j2.triggered.connect(lambda: self.ui.j1_j2.setCurrentIndex(1))
        self.ui.more_config.triggered.connect(lambda: self.ui.j1_j2.setCurrentIndex(2))




    #========================================================================
    def TranslationUi(self, Lang, ReloadWidget):
        """Fonction de traduction du logiciel."""
        ### Mise à jour de la variable
        self.KiesseCfg['LangUi'] = Lang

        ### Chargement du fichier qm de traduction (anglais utile pour les textes singulier/pluriel)
        AppTranslator = QTranslator() # Création d'un QTranslator

        if "fr_" in Lang:
            find = AppTranslator.load("Kiesse_fr_FR", str(self.PathHere))

            # Si le fichier n'a pas été trouvé,relance la fonction en EN
            if not find:
                QMessageBox(3, "Erreur de traduction", "Aucun fichier de traduction <b>française</b> trouvé.<br/>Utilisation de la langue <b>anglaise</b>.", QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()
                self.ui.lang_english.setChecked(True)

            else:
                ### Chargement de la traduction
                app.installTranslator(AppTranslator)

        elif "en_" in Lang:
            # Utile pour utiliser victoiries ou victory
            find = AppTranslator.load("Kiesse_en_EN", str(self.PathHere))

            if find:
                ### Chargement de la traduction
                app.installTranslator(AppTranslator)


        ### Mise à jour du fichier langage de Qt
        global translator_qt
        translator_qt = QTranslator() # Création d'un QTranslator
        if translator_qt.load("qt_" + Lang, QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
            app.installTranslator(translator_qt)


        ### Mise à jour du dictionnaire des textes
        self.Translation = {
"ButtonQuitText" : self.tr("Exit"),
"ButtonQuitTip" : self.tr("Stop the work in progress, save the configurations and close the software."),
"ButtonChoiceTip" : self.tr("Click to propose this character"),
"ButtonGrayingTip" : self.tr("Click to remove {} from the characters' list"),

"AboutTitle" : self.tr("About Kiesse ? v{} for qt5"),
"AboutText" : self.tr("""<p align="center"><b>Kiesse ?</b> is a game based on the famous <b>WHo is-it?</b>.<br><br>The principle is simple, each player chooses a character among the list of characters of the opponent.<br><br>Players will then ask questions (in alternence) to the opponent on the physical aspect of the character he has chosen.<br><br>Depending on the answers, the characters who are not comply with the criteria are to remove.<br><br>When a player is sure of the character chosen by the opponent, he propose a response.<br><br>Once a proposed answer makes the game end on the victory or defeat of the player who made the proposal.</p><br><p align="left">This software is licensed under </span><span style=" font-size:8pt; font-weight:600;"><a href="http://www.gnu.org/copyleft/gpl.html">GNU GPL v3</a></span></p><br><p align="right">Game created by Belleguic Terence aka <a href="mailto:hizo@free.fr">Hizo</a><br>Characters created by <a href="http://www.jojomendoza.com">Jojo Mendoza</a>, <a href="https://twitter.com/hopstarter">Twitter</a><br>Icons created by <a href="http://kde-look.org/usermanager/search.php?username=mentalrey">Alessandro Rei</a></p>"""),

"KeyTitle" : self.tr("Keyword error"),
"KeyText" : self.tr("The keyword <b>{}</b> of the <b>{}</b> character doesn't exists in the questions."),
"CharacterTitleOk" : self.tr("It's alright"),
"CharacterTextOk" : self.tr("No problem detected with the characters."),

"Yes" : self.tr("Yes"),
"No" : self.tr("No"),
"Unknown" : self.tr("Unknown"),
"Question" : self.tr("Question"),
"PlayAgain" : self.tr("Play again"),

"ToolTipYes" : self.tr("{}: Yes\n"),
"ToolTipNo" : self.tr("{}: No\n"),
"CharacterSearched" : self.tr("""<p align="center">Character searched <br>by <span style="color:{};">{}</span></p>"""),
"ImageStatusTip" : self.tr("Leave the mouse over the image to display the characteristics of the character"),

"LoadGameErrorTitle" : self.tr("Error during the config load"),
"LoadGameErrorText" : self.tr("An error occurred while loading the configuration file: {}/Config.cfg"),

"LabelInfo1" : self.tr("""<html><head/><body><p align="center"><span style="font-weight:600; color:#000000;"><span style="color:{};">{}</span>: Choose the character that <span style="color:{};">{}</span> has to find out in this list</span></p></body></html>"""),
"LabelInfo2" : self.tr("""<html><head/><body><p align="center"><span style="font-weight:600; color:#000000;"><span style="color:{};">{}</span>: Find the character chosen by <span style="color:{};">{}</span> in this characters' list asking the right questions</span></p></body></html>"""),

"EndGameTitle" : self.tr("It's over"),
"EndGameText" : self.tr("Game is over.\n\nPlease start a new one."),

"victoiry1" : self.tr("%n victory(ies)", "", self.ScorePlayer1),
"victoiry2" : self.tr("%n victory(ies)", "", self.ScorePlayer2),
"CharacterProposalWin" : self.tr("""Congratulations, <span style="color:{0};">{1}</span> won !<br><br><span style="color:{0};">{1}</span> has found out {4}.<br><br><span style="color:{0};">{1}</span>: {5}<br><span style="color:{2};">{3}</span>: {6}"""),
"CharacterProposalLost" : self.tr("""Too bad, <span style="color:{0};">{1}</span> lost !<br><br><span style="color:{2};">{3}</span> has picked out {4}.<br><br><span style="color:{0};">{1}</span>: {5}<br><span style="color:{2};">{3}</span>: {6}"""),
"CharacterProposalComputer" : self.tr("""Too bad, you lost !<br><br><span style="color:{0};">{1}</span> understood that you picked up {2}.<br><br><span style="color:{0};">{1}</span>: {3}<br><span style="color:{4};">{5}</span>: {6}"""),
"CharacterProposalErrorTitle" : self.tr("Logical error"),
"CharacterProposalError" : self.tr("""<b><span style="color:{};">{}</span></b> picked up <b>{}</b> but it was <b>{}</b>...<br>There is a problem somewhere..."""),

"AboutGameTitle" : self.tr("How-to add a set of characters in Kiesse ?"),
"AboutGameClose" : self.tr("Close"),
"AboutGameTest" : self.tr("Search errors"),
"AboutGameTestText" : self.tr("""<p align="center">For helping, there is a search errors in game config function.</p>"""),
"AboutGameInfo" : self.tr("""To add a game (set of characters), you must:<br/> - Images with the same format and same resolutions (square format)<br/> - A <b>Config.cfg</b> file containing all the information<br/> - All files in Games/Subfolder<br/><br/>This configuration file must be as follows:"""),

"AboutGameTime" : self.tr("That can take few seconds"),
"AboutGameTitleError1" : self.tr("Configuration missing"),
"AboutGameTitleText1" : self.tr("The following images have been found but have no correspondence in the configuration file:<br/>{}"),
"AboutGameTitleError2" : self.tr("Image(s) missing"),
"AboutGameTitleText2" : self.tr("The following characters have been found in the configuration file but do not have linked images:<br/>{}"),
"AboutGameTitleError3" : self.tr("Configuration error of the characters"),
"AboutGameTitleText3" : self.tr("These characters have the same configuration:<br>{}"),
"AboutGameTitleError4" : self.tr("Character double"),
"AboutGameTitleText4" : self.tr("In the configuration file, this characters is present in double:<br>{}"),
"AboutGameTitleError5" : self.tr("No extension"),
"AboutGameTitleText5" : self.tr("The configuration file need to know what is the extension of the images files of the characters.\nLook the demo.\n\n[GAME]\nextension = png"),

"AboutGameText" : self.tr("""<b>[GAME]</b><br/>
<span style="color:#0000ff;"># Extension of the images : <i>png, jpg, tif...</i><br/>
# If the extension is not the right extension file, there is a crash of Kiesse</span><br/>
extension = <i>png</i><br/>
<br/>
<br/>
<b>[QUESTIONS_EN]</b><br/>
<span style="color:#0000ff;"># Questions with the language info : QUESTIONS_EN for English<br/>
# Every question have a KeyWord : KeyWord = Question<br/>
# These KeyWords are the link between the question and the answer for every character<br/>
# The KeyWords who start by "null" are not used into questions, they serve of aesthetic separations<br/>
# No limit in the number of questions or in the number of languages</span><br/>
<span style="color:#aa00ff;">masculin</span> = <i>The character is he a male?</i><br/>
null3 = <i>------------------------ Iris ------------------------</i><br/>
<span style="color:#008000;">iris_vertes</span> = <i>Is the character green-eyed?</i><br/>
<span style="color:#C00000;">iris_marrons</span> = <i>Is the character brown-eyed?</i><br/>
<span style="color:#00C0C0;">iris_bleues</span> = <i>Is the character blue-eyed?</i><br/>
<br/>
<br/>
<b>[QUESTIONS_FR]</b><br/>
<span style="color:#0000ff;"># Same questions in French...</span><br/>
<span style="color:#aa00ff;">masculin</span> = <i>Le personnage est-il masculin ?</i><br/>
null3 = <i>------------------------ Iris ------------------------</i><br/>
<span style="color:#008000;">iris_vertes</span> = <i>Le personnage a-t-il des iris vertes ?</i><br/>
<span style="color:#C00000;">iris_marrons</span> = <i>Le personnage a-t-il des iris marron ?</i><br/>
<span style="color:#00C0C0;">iris_bleues</span> = <i>Le personnage a-t-il des iris bleues ?</i><br/>
<br/>
<br/>
<b>[DEFAULT]</b><br/>
<span style="color:#0000ff;"># For a best reading, the <b>DEFAULT</b> section is very useful<br/>
# Every KeyWord (except the null* KeyWords) is add here with the default value (the most common value) : KeyWord = DefaultValue<br/>
# If you must choose between several colors for example, use <b>False</b> for every default value.</span><br/>
<span style="color:#aa00ff;">masculin</span> = <i>True</i><br/>
<span style="color:#008000;">iris_vertes</span> = <i>True</i><br/>
<span style="color:#C00000;">iris_marrons</span> = <i>False</i><br/>
<span style="color:#00C0C0;">iris_bleues</span> = <i>False</i><br/>
<br/>
<br/>
<b>[CAMILLE]</b><br/>
<span style="color:#0000ff;"># <b>NAME</b> of the character, this name <b>MUST BE</b> the same as that of the image (the letter case is not important)<br/>
# If a file exists but has not section with its name, there is a crash in Kiesse<br/>
# No limit in the number of character<br/>
# <span style="color:#aa00ff;">masculin</span> = <i>True</i> by default<br/>
# <span style="color:#C00000;">iris_marrons</span> = <i>False</i> by default<br/>
# <span style="color:#00C0C0;">iris_bleues</span> = <i>False</i> by default</span><br/>
<span style="color:#008000;">iris_vertes</span> = <i>True</i><br/>
<br/>
<br/>
<b>[ALICE]</b><br/>
<span style="color:#0000ff;">
# <span style="color:#008000;">iris_vertes</span> = <i>False</i> by default<br/>
# <span style="color:#00C0C0;">iris_bleues</span> = <i>False</i> by default</span><br/>
<span style="color:#aa00ff;">masculin</span> = <i>False</i><br/>
<span style="color:#C00000;">iris_marrons</span> = <i>True</i>""")}


        ### Recharge les textes de l'application graphique du fichier ui.py
        self.ui.retranslateUi(self)


        ### Mise à jour des textes des widgets
        self.ButtonQuit.setText(self.Translation["ButtonQuitText"])
        self.ButtonQuit.setStatusTip(self.Translation["ButtonQuitTip"])


    #========================================================================
    def AboutGame(self):
        """Fonction d'affichage de la fenetre d'aide à la création d'un jeu de personnage."""
        ### Création de la fenetre
        Window = QDialog(self)
        Window.resize(self.geometry().width() - 20 , self.geometry().height() - 20)
        Window.setWindowTitle(self.Translation["AboutGameTitle"])

        ### Création des Layout
        VerticalLayout = QVBoxLayout(Window)
        HorizontalLayout = QHBoxLayout()
        HorizontalLayout2 = QHBoxLayout()

        ### Création de l'image
        Image = QLabel()
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        Image.setSizePolicy(sizePolicy)
        Image.setPixmap(IconBis("kiesse", "Pixmap"))

        ### Création du texte à coté de l'image
        MiniText = QLabel()
        MiniText.setTextFormat(Qt.RichText)
        MiniText.setText(self.Translation["AboutGameInfo"])

        ### Création du texte complet d'exemple
        TextEdit = QTextEdit()
        TextEdit.setHtml(self.Translation["AboutGameText"])

        ### Création du texte d'explication du test
        TestText = QLabel(self.Translation["AboutGameTestText"])
        MiniText.setTextFormat(Qt.RichText)

        ### Bouton de test du jeu
        ButtonTest = QPushButton(self.Translation["AboutGameTest"])
        ButtonTest.setIcon(IconBis("edit-find", "Icon")) # Affectation de l'icone au bouton
        ButtonTest.clicked.connect(self.DiffCharacter)

        ### Combo des jeux
        self.ComboGames = QComboBox()
        GameList = list()
        for Folder in Path(self.ConfigFolder / "Games").iterdir():
            if Folder.is_dir(): GameList.append(Folder)
        for Folder in Path(self.PathHere / "Games").iterdir():
            if Folder.is_dir(): GameList.append(Folder)
        for Folder in GameList: self.ComboGames.addItem(str(Folder))

        Label = QLabel(self.Translation["AboutGameTime"])

        ### Création du bouton de fermeture de la fenetre
        ButtonClose = QPushButton(self.Translation["AboutGameClose"])
        ButtonClose.setIcon(IconBis("dialog-close", "Icon")) # Affectation de l'icone au bouton
        ButtonClose.clicked.connect(Window.close)

        ### Remplissage du layout HorizontalLayout
        HorizontalLayout.addWidget(Image)
        HorizontalLayout.addWidget(MiniText)

        ### Remplissage du layout HorizontalLayout2
        HorizontalLayout2.addWidget(self.ComboGames)
        HorizontalLayout2.addWidget(ButtonTest)
        HorizontalLayout2.addWidget(Label)

        ### Remplissage du layout VerticalLayout
        VerticalLayout.addLayout(HorizontalLayout)
        VerticalLayout.addWidget(TextEdit)
        VerticalLayout.addWidget(TestText)
        VerticalLayout.addLayout(HorizontalLayout2)
        VerticalLayout.addWidget(ButtonClose)

        ### Affichage de la fenetre
        Window.exec()


    #========================================================================
    def DiffCharacter(self):
        """Fonction recherchant les perso ayant les memes indicateurs, des doublons."""
        # Choix du dossier à tester
        Folder = Path(self.ComboGames.currentText())

        try:
            ### Chargement du fichier de config des perso :
            TestGameCfg = configparser.ConfigParser() # Chargement du fichier de cfg
            TestGameCfg.read(str(Folder) + "/Config.cfg") # Lecture du fichier de cfg

        except configparser.DuplicateSectionError as info:
            # S'il y a un perso en double
            info = str(info).split("]: ")[-1].split("'")[1]
            QMessageBox(1, self.Translation["AboutGameTitleError4"], self.Translation["AboutGameTitleText4"].format(info), QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()
            return


        # Verification de la présence de l'extension => y a t il un vrai interet a ca ?
        try:
            ExtensionImages = TestGameCfg["GAME"]["extension"]
        except:
            QMessageBox(1, self.Translation["AboutGameTitleError5"], self.Translation["AboutGameTitleText5"], QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()
            return


        ### Liste des infos posant problemes
        Errors = []

        ### Liste des personnages depuis le fichier de config
        ConfigCharacterList = list(TestGameCfg.keys())

        # Suppression des clés non personnages
        try: ConfigCharacterList.remove("GAME")
        except: pass
        try: ConfigCharacterList.remove("DEFAULT")
        except: pass
        try: ConfigCharacterList.remove("QUESTIONS")
        except: pass
        try: ConfigCharacterList.remove("QUESTIONS_EN")
        except: pass
        try: ConfigCharacterList.remove("QUESTIONS_FR")
        except: pass

        ### Liste des personnages depuis les images
        ImageCharacterList = []
        for Character in list(Folder.glob("*." + ExtensionImages)):
            ImageCharacterList.append(Character.stem.upper())

        ### Vérifie que les personnages existants en images, existent aussi dans le fichier de config
        for Character in ImageCharacterList:
            ### Verifie que chaque mot clé des perso existe dans les questions
            try:
                for Key in TestGameCfg[Character].keys():
                    test = TestGameCfg[self.QuestionsLang].get(Key)

                    if not test:
                        # Si le mot clé d'une réponse d'un perso n'existe pas dans les questions
                        QMessageBox(3, self.Translation["KeyTitle"], self.Translation["KeyText"].format(Key, Character), QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()
                        return

            except:
                Errors.append(Character)

        if Errors:
            QMessageBox(1, self.Translation["AboutGameTitleError1"], self.Translation["AboutGameTitleText1"].format("<br/>".join(Errors)), QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()
            return


        ### Vérifie que les personnages du fichier de configuration ont bien une image associée
        for Character in ConfigCharacterList:
            if not Character.upper() in ImageCharacterList:
                Errors.append(Character.upper())

        if Errors:
            QMessageBox(1, self.Translation["AboutGameTitleError2"], self.Translation["AboutGameTitleText2"].format("<br/>".join(Errors)), QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()
            return


        ### Recherche les personnages ayant les mêmes caractéristiques
        for CharacterFrom in ImageCharacterList:
            # Recup des infos du personnage à tester
            InfosFrom = dict(TestGameCfg[CharacterFrom].items())

            for CharacterTo in ImageCharacterList:
                # Si les persos à comparer sont les memes, on saute le tour
                if CharacterFrom == CharacterTo: continue

                # Recup des infos du personnage à tester
                InfosTo = dict(TestGameCfg[CharacterTo].items())

                # Si les persos ont les mêmes caractéristiques et qu'ils ne sont pas déja dans la liste, on les ajoute
                if InfosFrom == InfosTo and not (CharacterTo, CharacterFrom) in Errors:
                    Errors.append((CharacterFrom, CharacterTo))

        # Si la liste n'est pas vide, on l'affiche
        if Errors:
            test = ""
            for Perso in Errors: test += "<br/>" + " &harr; ".join(Perso)
            QMessageBox(1, self.Translation["AboutGameTitleError3"], self.Translation["AboutGameTitleText3"].format(test), QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()
            return


        ### Message si tout est ok
        QMessageBox(1, self.Translation["CharacterTitleOk"], self.Translation["CharacterTextOk"], QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()


    #========================================================================
    def VarDef(self, Item, Value=None, X=None):
        """Fonction de mise à jour des variables, X utile pour les langues."""
        ### Mise à jour de la variable
        if Item in ['ColorPlayer1', 'ColorPlayer2']:
            # Coloration des noms
            Palette = QPalette(Value.palette())
            self.KiesseCfg[Item] = QColorDialog.getColor(self.KiesseCfg[Item])
            Palette.setColor(Palette.Text, self.KiesseCfg[Item])
            Value.setPalette(Palette)
        else:
            self.KiesseCfg[Item] = Value # Valeurs simples


        ### Action spécifique en fonction de l'item
        if Item in ['NamePlayer1', 'NamePlayer2']:
            self.ui.tableWidget.setHorizontalHeaderLabels(("Value", self.KiesseCfg['NamePlayer1'], self.Translation["Question"], self.KiesseCfg['NamePlayer2'])) # Mise à jour des noms dans l'header

        elif Item in ['NumberColumns', 'NumberCharacters']:
            self.InOption = True # Variable n'affichant pas la nouvelle partie

            # Rechargement des perso s'il y a une partie en cours
            if self.InGame: self.FaceFiles()

            self.InOption = False

        elif Item == 'NumberPlayer':
            self.FaceFiles() # Lancement d'une nouvelle partie

        elif Item == "LangUi":
            self.TranslationUi(Value, True) # Changement de langue
            self.ChoiceGameDef(self.KiesseCfg['ChoiceGame'])

        elif Item == "SizeCharacters":
            # Définit la taille en fonction de la valeur
            if Value == 1:
                self.Size = QSize(50, 50)
            elif Value == 2:
                self.Size = QSize(75, 75)
            elif Value == 3:
                self.Size = QSize(100, 100)
            elif Value == 4:
                self.Size = QSize(125, 125)
            elif Value == 5:
                self.Size = QSize(150, 150)
            elif Value == 6:
                self.Size = QSize(175, 175)
            elif Value == 7:
                self.Size = QSize(200, 200)
            elif Value == 8:
                self.Size = QSize(225, 225)
            elif Value == 9:
                self.Size = QSize(250, 250)
            elif Value == 10:
                self.Size = QSize(275, 275)
            elif Value == 11:
                self.Size = QSize(300, 300)

            # Calcul et changement de valeur
            try:
                # Modification de chaque label image avec la nouvelle valeure
                for Frame in self.ListeWidgetCharacters:
                    Image = Frame.findChild(QLabel, "image")
                    Image.setFixedSize(self.Size)

            except:
                pass

            self.ui.Preview.setFixedSize(self.Size)


    #========================================================================
    def ChoiceGameDef(self, ChoiceGame, Value=True):
        """Chargement du dossier contenant les images."""
        ### Value est indiqué uniquement par les actions des options
        if not Value:
            return

        ### Si le dossier n'existe pas, on utilise une valeur de base
        if not ChoiceGame.exists():
            self.KiesseCfg['ChoiceGame'] = Path(self.PathHere, "Games/Faces")
        else:
            self.KiesseCfg['ChoiceGame'] = ChoiceGame

        ### Chargement du fichier de config des perso
        self.GameCfg = configparser.ConfigParser() # Chargement du fichier de cfg

        try:
            self.GameCfg.read(str(self.KiesseCfg['ChoiceGame'] / "Config.cfg")) # Lecture du fichier de cfg
        except:
            QMessageBox(1, self.Translation["LoadGameErrorTitle"], self.Translation["LoadGameErrorText"].format(self.KiesseCfg['ChoiceGame']), QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()
            return

        ### Taille indiqué
        self.ExtensionImages = self.GameCfg["GAME"]["extension"]

        ### Taille indiqué
        self.VarDef('SizeCharacters', self.KiesseCfg['SizeCharacters'])

        ### Récupération des langues des questions
        SmallList = []
        for Section in self.GameCfg.sections():
            if "QUESTIONS" in Section:
                SmallList.append(Section)

        # Si on est en francais et qu'il y a des questions en français
        if "fr_" in self.KiesseCfg['LangUi'] and 'QUESTIONS_FR' in SmallList:
            self.QuestionsLang = 'QUESTIONS_FR'

        # Si on est pas en francais, on utilise l'anglais
        else:
            # S'il y a des questions anglaises
            if 'QUESTIONS_EN' in SmallList:
                self.QuestionsLang = 'QUESTIONS_EN'

            # Au pire, on prend une liste de question sans langue
            elif 'QUESTIONS' in SmallList:
                self.QuestionsLang = 'QUESTIONS'

        ### Rechargement des perso s'il y a une partie en cours
        if self.InGame:
            self.FaceFiles()


    #========================================================================
    def FaceFiles(self):
        """Chargement aléatoire des personnages."""
        ### Reinitialisation du jeu
        # Mise au propore de grilles des 2 joueurs
        self.ui.label_bienvenue.setParent(None)
        self.ui.intro_jeu1.setParent(None)
        self.ui.intro_jeu2.setParent(None)
        for Frame in self.ListeWidgetCharacters:
            try:
                Frame.setParent(None)
            except:
                pass

        # Nettoyage du tableau aux questions
        while self.ui.tableWidget.rowCount() != 0:
            self.ui.tableWidget.removeRow(0)

        # Grise le tableau
        self.ui.tableWidget.setEnabled(False)

        # Dévérouille le menu
        self.ui.menu_perso.setEnabled(True)

        ### Création de variables
        self.InGame = True # Variable indiquant qu'une partie est en cours

        # Liste contenant les frames des persos
        self.ListeWidgetCharacters = []

        # Listes des noms des persos présent (utile pour rechercher le personnage par l'ordinateur)
        self.ListCharacterP1 = [] # Contient les personnages que le joueur 2 voit
        self.ListCharacterP2 = [] # Contient les personnages que le joueur 1 voit

        # Variables indiquant les mot clés à ne pas prendre en charge
        self.BlockQuestion1 = []
        self.BlockQuestion2 = []

        # Variables contenant le nom du perso choisi
        self.CharacterChosenP1 = "" # Contient le personnage choisit parmis ceux de self.ListCharacterP1
        self.CharacterChosenP2 = "" # Contient le personnage choisit parmis ceux de self.ListCharacterP2

        ### Liste complete des perso avec leur adresse de fichier
        self.ListCharacterFull = {}
        for Character in self.KiesseCfg['ChoiceGame'].glob("*." + self.ExtensionImages):
            self.ListCharacterFull[Character.stem] = Character

        ### Compare le nombre de perso max et le nombre de perso trouvé pour eviter les plantages
        if len(self.ListCharacterFull) < self.KiesseCfg['NumberCharacters'] or self.KiesseCfg['NumberCharacters'] == 0:
            # S'il y a moins de perso que le max, on diminue le max
            # Mais dans le cas où il n'y a pas de limite au max, on le met au nombre de perso
            NumberCharactersTemp = len(self.ListCharacterFull)
        else:
            NumberCharactersTemp = self.KiesseCfg['NumberCharacters']

        ### Boucle lancant le chargement de perso pour les 2 joueurs
        for ListeCharacter, Grid, PlayerX in [(self.ListCharacterP1, self.ui.grille_j1, "P1"),
                                          (self.ListCharacterP2, self.ui.grille_j2, "P2")]:
            x, y = 0, 0 # Valeur de placement des perso

            ### Prends NumberCharactersTemp perso au hasard
            for Character, Link in random.sample(list(self.ListCharacterFull.items()), NumberCharactersTemp):
                ### Remplissage des listes de perso
                ListeCharacter.append(Character)

                ### Récupération des infos sur le perso qui servira de tooltip
                ToolTip = ""
                for Key, Value in self.GameCfg[Character.upper()].items():
                    if Value == "True":
                        ToolTip += self.Translation["ToolTipYes"].format(Key)
                    else:
                        ToolTip += self.Translation["ToolTipNo"].format(Key)

                ### Création des differents widgets
                Frame = QFrame() # Création d'une frame pour plus de lisibilité
                Frame.setFrameShadow(QFrame.Raised) # Config de la frame
                Frame.setFrameShape(QFrame.StyledPanel) # Config de la frame
                VerticalLayout = QVBoxLayout(Frame) # Creation du layout qui contiendra le label et le layout
                HorizontalLayout = QHBoxLayout() # Creation du layout qui contiendra les boutons
                ImageLayout = QHBoxLayout() # Creation du layout qui contiendra l'image, obligatoire pour le centrage

                ### Bouton indiquant le perso choisi au final
                ButtonChoice = QPushButton(IconBis("dialog-ok", "Icon"), "")
                ButtonChoice.setObjectName("ButtonChoice") # Donne un no faciliter la recherche des boutons
                ButtonChoice.setEnabled(False) # Grisage du bouton
                ButtonChoice.setFixedSize(QSize(28, 28)) # Taille du bouton
                ButtonChoice.setStatusTip(self.Translation["ButtonChoiceTip"])
                HorizontalLayout.addWidget(ButtonChoice) # Ajout du bouton de nom au layout

                ### Bouton avec le nom du perso
                ButtonCharacter = QPushButton(Character) # Création du bouton
                ButtonCharacter.setObjectName("ButtonCharacter") # Donne un no faciliter la recherche des boutons
                HorizontalLayout.addWidget(ButtonCharacter) # Ajout du bouton de nom au layout

                ### Bouton de grisage de l'image du perso
                ButtonGraying = QPushButton(IconBis("edit-delete", "Icon"), "")
                ButtonGraying.setObjectName("ButtonGraying") # Donne un no faciliter la recherche des boutons
                ButtonGraying.setCheckable(True) # Affectation de l'icone au bouton
                ButtonGraying.setEnabled(False) # Grisage du bouton
                ButtonGraying.setFixedSize(QSize(28, 28)) # Taille du bouton
                ButtonGraying.setStatusTip(self.Translation["ButtonGrayingTip"].format(Character))
                HorizontalLayout.addWidget(ButtonGraying) # Ajout du bouton de nom au layout

                ### Image du perso
                Image = QLabel() # Création du label
                Image.setObjectName("image") # Donne un no faciliter la recherche des boutons
                Image.setPixmap(QPixmap(str(Link))) # Utilisation d'une image au lieu du texte
                Image.setFixedSize(self.Size)
                Image.setScaledContents(True) # Adapte l'image à la taille du label
                Image.setToolTip(ToolTip[:-1]) # InfoBulle du perso sur le label
                Image.setStatusTip(self.Translation["ImageStatusTip"])
                ImageLayout.addWidget(Image) # Ajout du label de nom au layout

                ### Remplissage du layout et du frame
                VerticalLayout.addWidget(QSplitter(Qt.Vertical)) # Utile pour centrer verticalement l'image
                VerticalLayout.addLayout(ImageLayout)
                VerticalLayout.addWidget(QSplitter(Qt.Vertical)) # Utile pour centrer verticalement l'image
                VerticalLayout.addLayout(HorizontalLayout)
                Grid.addWidget(Frame, x, y) # Implentation du widget dans le grindlayout

                ### Connexion des boutons
                ButtonChoice.clicked.connect(partial(self.CharacterProposal, Character, PlayerX)) # Au clic sur la coche
                ButtonCharacter.clicked.connect(partial(self.ChoiceCharacter, Character, PlayerX)) # Au clic sur la coche
                ButtonGraying.toggled.connect(partial(self.BadCharacter, Image)) # Au clic sur la coche

                ### Remplissage des dictionnaires
                self.ListeWidgetCharacters.append(Frame)

                ### Valeur de placement des frames dans la grille
                if y == self.KiesseCfg['NumberColumns'] - 1:
                    y = 0 # Changement de ligne
                    x += 1
                else:
                    y += 1 # Changement de colonne


        ### Debug Mode
        if self.KiesseCfg['DebugMode']:
            self.DebugFile = Path(self.ConfigFolder, str(datetime.today()))
            with self.DebugFile.open('w') as File:
                File.write("Joueur ayant commencé la partie : {}\n\n".format(self.FisrtPlayer))
                File.write("Nom et couleur du joueur 1 : {} - {}\n\n".format(self.KiesseCfg['NamePlayer1'], self.KiesseCfg['ColorPlayer1'].name()))
                File.write("Nom et couleur du joueur 2 : {} - {}\n\n".format(self.KiesseCfg['NamePlayer2'], self.KiesseCfg['ColorPlayer2'].name()))
                File.write("Liste des personnages du joueur 1 :\n{}\n\n".format(self.ListCharacterP1))
                File.write("Liste des personnages du joueur 2 :\n{}\n\n".format(self.ListCharacterP2))


        ### Si la fonction n'a pas été lancée depuis les options
        if not self.InOption:
            ### Affichage de la page du joueur 2
            self.ui.j1_j2.setCurrentIndex(1)

            # Modification de l'aide
            self.ui.label_info.setText(self.Translation["LabelInfo1"].format(self.KiesseCfg['ColorPlayer1'].name(), self.KiesseCfg['NamePlayer1'], self.KiesseCfg['ColorPlayer2'].name(), self.KiesseCfg['NamePlayer2']))


    #========================================================================
    def ChoiceCharacter(self, Character, Player):
        """Lorsqu'un personnage est choisi par les joueurs."""
        ### Une fois le perso choisi par le joueur 1, J2 car le choix a eu lieu sur la page du J2
        if Player == "P2":
            # Choix personnage
            self.CharacterChosenP1 = Character

            # Si c'est l'odrdi ou un joueur ce n'est pas la meme chose
            if self.KiesseCfg['NumberPlayer'] == 1:
                ### Séléction aléatoire d'un personnage dans la liste du J1
                self.CharacterChosenP2 = random.choice(self.ListCharacterP1)

                ### Lance de suite la suite
                self.ChoiceCharacterSuite()


            # Si c'est l'odrdi ou un joueur ce n'est pas la meme chose
            elif self.KiesseCfg['NumberPlayer'] == 2:
                ### Affichage de la page du joueur 1
                self.ui.j1_j2.setCurrentIndex(0)

                # Modification de l'aide
                self.ui.label_info.setText(self.Translation["LabelInfo1"].format(self.KiesseCfg['ColorPlayer2'].name(), self.KiesseCfg['NamePlayer2'], self.KiesseCfg['ColorPlayer1'].name(), self.KiesseCfg['NamePlayer1']))

        elif Player == "P1": # Quand la selection du Joueur2 a été fait sur les perso du joueur1
            # Choix personnage
            self.CharacterChosenP2 = Character

            ### Lancement de la suite
            self.ChoiceCharacterSuite()


    #========================================================================
    def ChoiceCharacterSuite(self):
        ### Récupération des infos sur le perso qui servira de tooltip
        ToolTip = ""
        for Key, Value in self.GameCfg[self.CharacterChosenP1.upper()].items():
            if Value == "True":
                ToolTip += self.Translation["ToolTipYes"].format(Key)
            else:
                ToolTip += self.Translation["ToolTipNo"].format(Key)

        ### Modification et affichage
        # Changement du texte d'aide
        self.ui.label_info.setText(self.Translation["LabelInfo2"].format(self.KiesseCfg['ColorPlayer1'].name(), self.KiesseCfg['NamePlayer1'], self.KiesseCfg['ColorPlayer2'].name(), self.KiesseCfg['NamePlayer2']))

        # Bloque et débloque les boutons des persos du J1
        for Frame in self.ListeWidgetCharacters:
            try:
                Frame.findChild(QPushButton, "ButtonGraying").setEnabled(True)
                Frame.findChild(QPushButton, "ButtonChoice").setEnabled(True)
                Frame.findChild(QPushButton, "ButtonCharacter").setEnabled(False)
            except:
                pass

        # Chargement des questions dans la bonne langue et mise à jour des mot clés bloqués
        for Value, Question in self.GameCfg[self.QuestionsLang].items():
            count = self.ui.tableWidget.rowCount()
            item = QTableWidgetItem(Question)
            item.setTextAlignment(Qt.AlignHCenter|Qt.AlignVCenter|Qt.AlignCenter)
            self.ui.tableWidget.insertRow(count)
            self.ui.tableWidget.setItem(count, 0, QTableWidgetItem(Value))
            self.ui.tableWidget.setItem(count, 2, item)

            if "null" == Value[0:4]:
                self.BlockQuestion1.append(Value)
                self.BlockQuestion2.append(Value)

        # Dégrise le tableau
        self.ui.tableWidget.setEnabled(True)


        ### Si c'est le 2e joueur qui commence
        if self.FisrtPlayer == 2:
            # Si c'est l'ordi
            if self.KiesseCfg['NumberPlayer'] == 1:
                # Pose de la question de l'ordi
                self.IA()

                # Affichage de la page du joueur 1
                self.ui.j1_j2.setCurrentIndex(0)

            # Si c'est un joueur
            else:
                # Changement du texte d'aide
                self.ui.label_info.setText(self.Translation["LabelInfo2"].format(self.KiesseCfg['ColorPlayer2'].name(), self.KiesseCfg['NamePlayer2'], self.KiesseCfg['ColorPlayer1'].name(), self.KiesseCfg['NamePlayer1']))

                # Affichage de la page du joueur 2
                self.ui.j1_j2.setCurrentIndex(1)

        ### Si c'est le 1er joueur qui commence
        else:
            # Affichage de la page du joueur 1
            self.ui.j1_j2.setCurrentIndex(0)


    #========================================================================
    def BadCharacter(self, Image, Value):
        """Lorsqu'un personnage est éliminé ou remis en jeu."""
        # Grise le perso
        if Value:
            Image.setEnabled(False)

        # Dégrise le perso
        else:
            Image.setEnabled(True)


    #========================================================================
    def CharacterProposal(self, Character, Player):
        """Lorsqu'un personnage est proposé en réponse."""
        ### Si le jeu est terminé
        if not self.InGame:
            QMessageBox(3, self.Translation["EndGameTitle"], self.Translation["EndGameText"], QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()
            return()


        ### Mode debug
        if self.KiesseCfg['DebugMode']:
            with self.DebugFile.open('a') as File:
                File.write("Personnage choisi par le joueur 1 : {}\n\n".format(self.CharacterChosenP1))
                File.write("Personnage choisi par le joueur 2 : {}\n\n".format(self.CharacterChosenP2))

                if not self.CharacterChosenP1 in self.ListCharacterP2:
                    File.write("ATTENTION : Le personnage choisi par le joueur 1 n'est pas présent dans sa liste.\n\n")

                elif not self.CharacterChosenP2 in self.ListCharacterP1:
                    File.write("ATTENTION : Le personnage choisi par le joueur 2 n'est pas présent dans sa liste.\n\n")

                elif self.CharacterChosenP2 in self.ListCharacterP1:
                    File.write("Le personnage choisi par le joueur 1 est bien présent dans sa liste.\n\n")

                elif self.CharacterChosenP1 in self.ListCharacterP2:
                    File.write("Le personnage choisi par le joueur 2 est bien présent dans sa liste.\n\n")

                File.write("Personnage proposé par {} : {}\n\n".format(Player, Character))

                if Player == "P1":
                    if Character == self.CharacterChosenP2:
                        File.write("Le joueur 1 a donc gagné.\n\n")
                    else:
                        File.write("Le joueur 1 a donc perdu.\n\n")

                elif Player == "P2":
                    if Character == self.CharacterChosenP1:
                        File.write("Le joueur 2 a donc gagné.\n\n")
                    else:
                        File.write("Le joueur 2 a donc perdu.\n\n")

                elif Player == "PC":
                    if Character == self.CharacterChosenP1:
                        File.write("L'ordinateur a donc gagné.\n\n")
                    else:
                        File.write("L'ordinateur a donc perdu.\n\n")


        ### Changement du joueur qui commencera
        if self.FisrtPlayer == 1:
            self.FisrtPlayer = 2
            self.CurrentPlayer = 2

        elif self.FisrtPlayer == 2:
            self.FisrtPlayer = 1
            self.CurrentPlayer = 1


        ### Si c'est le joueur 1 qui fait la proposition
        if Player == "P1":
            Icon = str(self.ListCharacterFull[self.CharacterChosenP2]) # Icon du perso

            if Character == self.CharacterChosenP2:
                self.ScorePlayer1 += 1 # Mise à jour du score

                ### Mise à jour de la traduction pour la prise en charge singulier/pluriel
                self.TranslationUi(self.KiesseCfg['LangUi'], False)

                Text = self.Translation["CharacterProposalWin"].format(self.KiesseCfg['ColorPlayer1'].name(), self.KiesseCfg['NamePlayer1'], self.KiesseCfg['ColorPlayer2'].name(), self.KiesseCfg['NamePlayer2'], self.CharacterChosenP2, self.Translation["victoiry1"], self.Translation["victoiry2"])
            else:
                self.ScorePlayer2 += 1 # Mise à jour du score
                ### Mise à jour de la traduction pour la prise en charge singulier/pluriel
                self.TranslationUi(self.KiesseCfg['LangUi'], False)

                Text = self.Translation["CharacterProposalLost"].format(self.KiesseCfg['ColorPlayer1'].name(), self.KiesseCfg['NamePlayer1'], self.KiesseCfg['ColorPlayer2'].name(), self.KiesseCfg['NamePlayer2'], self.CharacterChosenP2, self.Translation["victoiry1"], self.Translation["victoiry2"])

        ### Si c'est le joueur 2 qui fait la proposition
        elif Player == "P2":
            Icon = str(self.ListCharacterFull[self.CharacterChosenP1]) # Icon du perso

            if Character == self.CharacterChosenP1:
                self.ScorePlayer2 += 1 # Mise à jour du score

                ### Mise à jour de la traduction pour la prise en charge singulier/pluriel
                self.TranslationUi(self.KiesseCfg['LangUi'], False)

                Text = self.Translation["CharacterProposalWin"].format(self.KiesseCfg['ColorPlayer2'].name(), self.KiesseCfg['NamePlayer2'], self.KiesseCfg['ColorPlayer1'].name(), self.KiesseCfg['NamePlayer1'], self.CharacterChosenP1, self.Translation["victoiry2"], self.Translation["victoiry1"])
            else:
                self.ScorePlayer1 += 1 # Mise à jour du score

                ### Mise à jour de la traduction pour la prise en charge singulier/pluriel
                self.TranslationUi(self.KiesseCfg['LangUi'], False)


                Text = self.Translation["CharacterProposalLost"].format(self.KiesseCfg['ColorPlayer2'].name(), self.KiesseCfg['NamePlayer2'], self.KiesseCfg['ColorPlayer1'].name(), self.KiesseCfg['NamePlayer1'], self.CharacterChosenP1, self.Translation["victoiry2"], self.Translation["victoiry1"])


        ### Si c'est l'ordi qui fait la proposition
        elif Player == "PC":
            Icon = str(self.ListCharacterFull[self.CharacterChosenP1]) # Icon du perso

            if Character == self.CharacterChosenP1:
                self.ScorePlayer2 += 1 # Mise à jour du score

                ### Mise à jour de la traduction pour la prise en charge singulier/pluriel
                self.TranslationUi(self.KiesseCfg['LangUi'], False)

                Text = self.Translation["CharacterProposalComputer"].format(self.KiesseCfg['ColorPlayer2'].name(), self.KiesseCfg['NamePlayer2'], self.CharacterChosenP1, self.Translation["victoiry2"], self.KiesseCfg['ColorPlayer1'].name(), self.KiesseCfg['NamePlayer1'], self.Translation["victoiry1"])

            # Si l'ordi s'est planté, il affiche un message l'indiquant...
            else:
                QMessageBox(3, self.Translation["CharacterProposalErrorTitle"], self.Translation["CharacterProposalError"].format(self.KiesseCfg['ColorPlayer2'], self.KiesseCfg['NamePlayer2'], Character, self.CharacterChosenP1), QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()

                self.InGame = False # Indique que la partie est terminée

                return # Arret de la fonction


        ### Affichage de la fenetre
        Window = QMessageBox(QMessageBox.NoIcon, self.Translation["EndGameTitle"], Text, QMessageBox.Close, self, Qt.WindowSystemMenuHint)
        Window.setIconPixmap(QPixmap(Icon).scaled(self.Size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        PlayAgain = QPushButton(IconBis("view-refresh", "Icon"), self.Translation["PlayAgain"])
        Window.addButton(PlayAgain, QMessageBox.YesRole)
        Window.setDefaultButton(PlayAgain)
        Window.exec() # Message d'information


        ### Recuperation et traitement du choix
        # recuperation de la reponse
        Reply = Window.buttonRole(Window.clickedButton())

        # En cas d'arret
        if Reply == 1: self.InGame = False # Indique que la partie est terminée

        # En cas de restart
        else: self.FaceFiles()


    #========================================================================
    def ChoiceQuestion(self, Row):
        """Fonction lors de l'envoie de la question sur le personnage adverse."""
        ### Si la partie est terminée, on arrete là en affichant un message
        if not self.InGame:
            QMessageBox(3, self.Translation["EndGameTitle"], self.Translation["EndGameText"], QMessageBox.Close, self, Qt.WindowSystemMenuHint).exec()
            return()

        ### Recup du numero de ligne puis du mot clé
        Line = Row.row()
        KeyWord = self.ui.tableWidget.item(Line,0).text()

        ### Si c'est une question bloquée, cela ne compte pas
        # Si c'est actuellement le joueur 1 qui joue
        if self.CurrentPlayer == 1:
            if not KeyWord in self.BlockQuestion1:
                self.ViewAnswer(KeyWord, Line)

        # Si c'est actuellement le joueur 2 qui joue
        else:
            if not KeyWord in self.BlockQuestion2:
                self.ViewAnswer(KeyWord, Line)


    #========================================================================
    def ViewAnswer(self, KeyWord, Line):
        """Fonction affichant la réponse à la question posée dans le tableau."""
        ### Variables en fonction du joueur
        # Si c'est actuellement le joueur 1 qui joue
        if self.CurrentPlayer == 1:
            Brush = QBrush(self.KiesseCfg['ColorPlayer1'])
            CharacterChosen = self.CharacterChosenP2.upper()
            self.BlockQuestion1.append(KeyWord) # Mise à jour des mots clés bloquant

        # Si c'est actuellement le joueur 2 qui joue
        else:
            Brush = QBrush(self.KiesseCfg['ColorPlayer2'])
            CharacterChosen = self.CharacterChosenP1.upper()
            self.BlockQuestion2.append(KeyWord) # Mise à jour des mots clés bloquant


        ### Création des items avec coloration
        Brush.setStyle(Qt.NoBrush)
        Answer = QTableWidgetItem()
        Answer.setForeground(Brush)
        Answer.setTextAlignment(Qt.AlignHCenter|Qt.AlignVCenter|Qt.AlignCenter)


        ### Réccupération de la réponse
        try:
            if self.GameCfg[CharacterChosen].getboolean(KeyWord) is True: # Lecture de la valeur du personnage
                Answer.setText(self.Translation["Yes"])
            else:
                Answer.setText(self.Translation["No"])
        except:
            Answer.setText(self.Translation["Unknown"])


        ### Changement de joueur
        if self.CurrentPlayer == 1:
            # Affichage de la réponse
            self.ui.tableWidget.setItem(Line, 1, Answer)

            # Mise à jour de la variable du joueur actuel
            self.CurrentPlayer = 2

            # Si on joue avec l'ordi
            if self.KiesseCfg['NumberPlayer'] == 1:
                self.IA()

            # Si on joue contre un autre joueur
            elif self.KiesseCfg['NumberPlayer'] == 2:
                # Changement du texte d'aide
                self.ui.label_info.setText(self.Translation["LabelInfo2"].format(self.KiesseCfg['ColorPlayer2'].name(), self.KiesseCfg['NamePlayer2'], self.KiesseCfg['ColorPlayer1'].name(), self.KiesseCfg['NamePlayer1']))

                # Affichage de la page du joueur 1
                self.ui.j1_j2.setCurrentIndex(0)


        elif self.CurrentPlayer == 2:
            # Affichage de la réponse
            self.ui.tableWidget.setItem(Line, 3, Answer)

            # Mise à jour de la variable du joueur actuel
            self.CurrentPlayer = 1

            # Si on joue contre un autre joueur
            if self.KiesseCfg['NumberPlayer'] == 2:
                # Changement du texte d'aide
                self.ui.label_info.setText(self.Translation["LabelInfo2"].format(self.KiesseCfg['ColorPlayer1'].name(), self.KiesseCfg['NamePlayer1'], self.KiesseCfg['ColorPlayer2'].name(), self.KiesseCfg['NamePlayer2']))

                # Affichage de la page du joueur 2
                self.ui.j1_j2.setCurrentIndex(1)



    #========================================================================
    def IA(self):
        """Fonction pseudo IA qui 'réfléchit' à la question la plus pertinente à poser."""
        ### Variables qui seront utiles dans la fonction
        DictValues = {} # Recupére les mots_clé et leur valeur : [mot_clé] : nombre de True
        ListValues = [] # Liste contenant des sous listes [nombre de true, mot_clé] triée utile pour poser la question

        ### S'il ne reste plus qu'un seul nom, l'ordinateur renvoie son nom
        if len(self.ListCharacterP2) == 1:
            self.CharacterProposal(self.ListCharacterP2[0], "PC")

        ### Dans le cas contraire on recherche le perso
        else:
            ### Création du dictionnaire
            # Création des clées
            for Value in self.GameCfg[self.QuestionsLang].keys():
                DictValues[Value] = 0

            # Création des valeurs en incémentant
            for Character in self.ListCharacterP2:
                for Value, Answer in self.GameCfg[Character.upper()].items():
                    if Answer == "True":
                        DictValues[Value] += 1

            ### Création de la liste
            # Convertion du dictionnaire en liste en supprimant les valeurs communes et les valeurs absentes
            for Value, Number in DictValues.items():
                if Number < len(self.ListCharacterP2) and Number > 0:
                    ListValues.append([Number, Value])

            # Rangement dans l'odre des questions les plus présentes
            ListValues.sort(reverse=True)

            ### Renvoie le mot clé à utiliser
            if self.KiesseCfg['DoubleOrNothing']: # Mode quitte ou double
                Value = ListValues[0][1]

            else: # Mode moyenne
                # Character / 2 = valeure la plus recherchée
                Average = int(len(self.ListCharacterP2) / 2)

                # S'il n'y a rien d'aussi haut, on prend le 1er
                if ListValues[0][0] < Average:
                    Value = ListValues[0][0]

                # S'il n'y a rien d'aussi bas, on prend le dernier
                elif ListValues[-1][0] > Average:
                    Value = ListValues[-1][0]

                else:
                    a = ListValues[-1][0]
                    b = ListValues[-1][1]
                    for Number, Key in ListValues:
                        # Si on trouve le bon chiffre, on s'arrete là
                        if Number == Average:
                            Value = Key
                            break

                        # Si on est descendu trop bas, on regarde lequel à utiliser entre les 2
                        elif Number < Average:
                            if a - Average < Number - Average:
                                Value = a
                            else:
                                Value = b
                            break

                        a = Number
                        b = Key


            ### Liste des persos n'ayant pas le meme critere
            ToRemove = []
            for Character in self.ListCharacterP2:
                if self.GameCfg[self.CharacterChosenP1.upper()][Value] != self.GameCfg[Character.upper()][Value]:
                    ToRemove.append(Character)

            ### Suppression des persos inadaptés de la liste
            for Character in ToRemove:
                self.ListCharacterP2.remove(Character)

            ### Recup de la ligne du tableau ayant ce mot clé
            Line = self.ui.tableWidget.findItems(Value, Qt.MatchExactly)[0].row()

            ### Pose la question
            self.ViewAnswer(Value, Line)


    #========================================================================
    def eventFilter(self, Watched, Event):
        """Filtre les Event du tableau afin d'adapter au mieu la taile des colonnes."""
        ### Redimensionnement du tableau des questions
        if Watched.objectName() == "tableWidget":
            if Event.type() == QEvent.Resize:
                Player1, Player2 = len(self.KiesseCfg['NamePlayer1']) * 7, len(self.KiesseCfg['NamePlayer2']) * 7
                Value = self.ui.tableWidget.size().width() - Player1 - Player2 - 35

                self.ui.tableWidget.setColumnWidth(1, Player1)
                self.ui.tableWidget.setColumnWidth(2, Value)
                self.ui.tableWidget.setColumnWidth(3, Player2)

        ### Autorise l'evenement
        return False


    #========================================================================
    def closeEvent(self, Event):
        """Fonction appelée lors de la fermeture du logiciel."""
        ### Sauvegarde des préférences
        Config = configparser.ConfigParser()
        Config.optionxform = lambda option: option # Conserve le nom des variables
        Config['DEFAULT'] = { "NumberColumns" : self.KiesseCfg['NumberColumns'],
                              "NumberCharacters" : self.KiesseCfg['NumberCharacters'],
                              "ChoiceGame" : str(self.KiesseCfg['ChoiceGame']),
                              "DebugMode" : str(self.KiesseCfg['DebugMode']),
                              "NamePlayer1" : self.KiesseCfg['NamePlayer1'],
                              "NamePlayer2" : self.KiesseCfg['NamePlayer2'],
                              "ColorPlayer1" : self.KiesseCfg['ColorPlayer1'].name(),
                              "ColorPlayer2" : self.KiesseCfg['ColorPlayer2'].name(),
                              "DoubleOrNothing" : self.KiesseCfg['DoubleOrNothing'],
                              "Width" : self.geometry().width(),
                              "Height" : self.geometry().height(),
                              "WinMax" : self.isMaximized(),
                              "LangUi" : self.KiesseCfg['LangUi'],
                              "NumberPlayer" : str(self.KiesseCfg['NumberPlayer']),
                              "SizeCharacters" : self.KiesseCfg['SizeCharacters']}

        with self.ConfigFile.open('w') as file:
            Config.write(file)

        Event.accept() # Acceptation de l'arret du logiciel


#############################################################################
if __name__ == '__main__':
    app = QApplication(sys.argv)
    Kiesse = Kiesse()
    app.exec_()
