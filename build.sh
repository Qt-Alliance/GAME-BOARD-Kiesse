#! /bin/bash

# Fichier servant :
# - Lors de la creation du paquet sources
# - Apres la creation d'un paquet source, les fichiers sont supprimés, il faut donc les recréer


# Dependancy : pyqt5-dev-tools qttools5-dev-tools python3-pyqt5


### Déplacement dans le bon dossier
chemin="$(cd "$(dirname "$0")"; pwd)"
cd "${chemin}"

### Mise à jour des fichiers ts
pylupdate5 ui_Kiesse.ui Kiesse.py -ts Kiesse_fr_FR.ts Kiesse_en_EN.ts #-noobsolete

### Création d'un fichier source python (contient les icones)
pyrcc5 Kiesse.qrc -o Kiesse_rc.py

### Convertion des fichiers ts en qm
[[ -e "/usr/lib/x86_64-linux-gnu/qt5/bin/lrelease" ]] && /usr/lib/x86_64-linux-gnu/qt5/bin/lrelease *.ts
[[ -e "/usr/lib/i386-linux-gnu/qt5/bin/lrelease" ]] && /usr/lib/i386-linux-gnu/qt5/bin/lrelease *.ts

### Conversion de l'interface graphique en fichier python
pyuic5 ui_Kiesse.ui -o ui_Kiesse.py

### Creation d'un systeme d'icone de secoure sur le fichier python ci-dessus
# Modification du systeme des icones en utilisant la fonction ci-dessous
while read line
do
    before="${line%%(*}"
    icon="${line##*/}"
    icon="${icon%%.*}"
    new_line="${before}(IconBis('${icon}'))"

    sed -i "s@${line}@${new_line}@" ui_Kiesse.py
done < <(grep "QtGui.QPixmap" ui_Kiesse.py)

# Création d'une fonction
echo """
def IconBis(Icon):
    if QtGui.QIcon().hasThemeIcon(Icon):
        return QtGui.QPixmap(QtGui.QIcon().fromTheme(Icon).pixmap(24))
    else:
        return QtGui.QPixmap(':/Icons/{}.png'.format(Icon))""" >> ui_Kiesse.py
