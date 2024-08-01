# Raspberry Pi - Guide d'Installation

Ce guide fournit des instructions pour installer différents logiciels de programmation sur votre Raspberry Pi.

## Prérequis

Avant de commencer, assurez-vous d'avoir accès à un Raspberry Pi fonctionnel et d'être connecté à Internet.

## Installation des Logiciels

### 1. Python

Python est un langage de programmation populaire et largement utilisé. Sur Raspberry Pi, Python est généralement préinstallé. Vous pouvez vérifier la version de Python avec la commande suivante dans le terminal :

```bash
python --version
```
Si Python n'est pas installé, vous pouvez l'installer en exécutant les commandes suivantes :

```bash
sudo apt update
sudo apt install python3
```

### 2. Visual Studio Code (VS Code)
Visual Studio Code est un éditeur de code open-source très populaire développé par Microsoft. Il offre une prise en charge étendue pour de nombreux langages de programmation.

Pour installer Visual Studio Code sur votre Raspberry Pi, suivez ces étapes :

```bash

sudo apt update
sudo apt install code
```
Après l'installation, vous pouvez lancer VS Code à partir du menu ou en utilisant la commande code dans le terminal.

### 3. Thonny
Thonny est un environnement de développement intégré (IDE) convivial pour Python qui est particulièrement adapté aux débutants. Pour l'installer, suivez ces étapes :

```bash
sudo apt update
sudo apt install thonny
```
Après l'installation, vous pouvez lancer Thonny à partir du menu ou en utilisant la commande thonny dans le terminal.

## Installation des librairies

Pour installer les librairies, ouvrer d'abord un terminal. Les sections suivantes présentent comment installer les librairies.

Mais avant, vous pouvez regarder quelles librairies sont déjà installer. Pour cela, entrer la ligne de commande :
```bash
sudo apt install python-
```

Pour vérifier l'installation de la librairie, vous pouvez utiliser la ligne :
```bash
pip show <nom_bibliothèque>
```
Il suffit de remplacer <nom_bibliothèque> par le nom de la librairie.

### numpy

```bash
sudo apt install python-numpy
```

### matplotlib
```bash
sudo apt install python-matplotlib
```

### picamera2

Si vous avez besoin de mettre à jour Picamera2, vous pouvez le faire en effectuant une mise à jour complète du système ou en l'installant spécifiquement via le terminal :

```bash
sudo apt update
sudo apt install -y python3-picamera2
```

Cette commande assure que Picamera2 est mis à jour vers la dernière version disponible dans les dépôts.

Si vous utilisez la version complète de Raspberry Pi OS et avez besoin des dépendances GUI pour Picamera2, vous pouvez les installer avec :
```bash
sudo apt install -y python3-pyqt5 python3-opengl
```
Cette commande installe PyQt5 et les dépendances OpenGL nécessaires pour les fonctionnalités graphiques de Picamera2.

Si vous utilisez Raspberry Pi OS Lite et souhaitez utiliser les fonctionnalités GUI avec Picamera2, vous devrez installer PyQt5 et OpenGL séparément :
```bash
sudo apt install -y python3-pyqt5 python3-opengl
```

Si vous souhaitez installer Picamera2 sans les dépendances GUI supplémentaires, utilisez la commande suivante :

```bash
sudo apt install -y python3-picamera2 --no-install-recommends
```

### openCV

```bash
sudo apt-get install python3-opencv
```

### ArduArducamDepthCamera
Pour installer cette librairie, rendez-vous sur la page ToF.md
