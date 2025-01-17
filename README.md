# Network Scanner

## Description

Le **Network Scanner** est une application Python qui utilise le module `nmap` pour détecter les dispositifs connectés à un réseau local. L'application fournit une interface web conviviale développée avec Flask, permettant aux utilisateurs d'afficher des informations sur les appareils détectés, d'ajouter des notes et de gérer les informations relatives à chaque appareil.

### Fonctionnalités
- **Détection des appareils** : Scanne le réseau local pour identifier tous les appareils connectés, y compris leur adresse IP, nom d'hôte et adresse MAC.
- **Interface Web** : Offre une interface utilisateur intuitive pour afficher les résultats du scan en temps réel.
- **Gestion des appareils** :
  - Affiche le type d'appareil (Serveur, Ordinateur, etc.).
  - Permet aux utilisateurs d’ajouter des informations comme le propriétaire, l'emplacement et des notes.
- **Mise à jour automatique** : La page se rafraîchit toutes les 30 secondes pour refléter les changements dans le réseau.

## Technologies Utilisées
- Python 3.x
- Flask : Un micro-framework pour construire l'application web.
- nmap : Une bibliothèque Python pour interagir avec le scanner de réseau Nmap.
- Jinja2 : Moteur de templates pour gérer le rendu de l'interface utilisateur.
- HTML/CSS/JavaScript : Technologies de base pour construire l'interface utilisateur.

## Prérequis
Avant de commencer, assurez-vous d'avoir installé Python 3 et les packages requis. Vous aurez également besoin d'installer `nmap` sur votre système.

### Installation des dépendances
Vous pouvez installer les dépendances requises avec `pip`. Exécutez la commande suivante dans votre terminal :

```bash
pip install flask python-nmap netifaces
Configuration

    Installation de Nmap : Assurez-vous que Nmap est installé sur votre système et que son chemin est accessible dans votre variable d'environnement.

        Pour installer Nmap sous Ubuntu/Debian :

        sudo apt-get install nmap

        Pour installer Nmap sous Windows, téléchargez-le à partir du site officiel Nmap.

    Fichier de données : L'application utilisera un fichier device_data.json pour stocker les informations relatives aux appareils. Ce fichier sera créé automatiquement à la première exécution de l'application.

Exécution de l'application

Après avoir installé les dépendances et configuré Nmap, vous pouvez exécuter l'application en utilisant la commande :

python network_scanner.py

L'application sera accessible sur http://0.0.0.0:8080 dans votre navigateur web.
Contributions

Les contributions sont les bienvenues ! Si vous souhaitez contribuer à cette application, veuillez suivre ces étapes :

    Forkez le projet.
    Créez une nouvelle branche (git checkout -b feature-branch).
    Effectuez vos modifications et enregistrez-les (git commit -am 'Add some feature').
    Envoyez vos modifications (git push origin feature-branch).
    Ouvrez une demande de tirage (Pull Request).
