# Le Loulou Phone

> Jeu multijoueur en ligne développé pour le projet de Développement Web et Base de données inspiré par le jeu Gartic Phone.

## Description (Français)

Le Loulou Phone est un petit jeu web multijoueur où les joueurs interagissent en temps réel.
L'interface front-end (HTML/CSS/JS) et les assets graphiques ont été dessinés à la main et intégrés au projet.
Le code serveur est entièrement réalisé en Python/Flask et utilise WebSocket (via Flask-SocketIO) pour la communication en temps réel.

<img width="2048" height="1424" alt="Screenshot from 2026-03-04 10-40-33" src="https://github.com/user-attachments/assets/c44375b7-ada3-47c6-a3d0-9b8f510c57d9" />
<img width="2048" height="1424" alt="Screenshot from 2026-03-04 10-40-57" src="https://github.com/user-attachments/assets/c367ed81-bd38-4226-ab8a-d242f3635967" />

Caractéristiques principales :
- Multijoueur en temps réel (Socket.IO)
- Interface réalisée avec des assets dessinés à la main
- Hébergement local possible et accès depuis d'autres appareils sur le même réseau (LAN)

## Technologies
- Python 3
- Flask
- Flask-SocketIO (python-socketio + python-engineio)
- eventlet (pour le serveur WSGI asynchrone)
- HTML, CSS, JavaScript
- (Possiblement SQLite via `database.py` pour la gestion des utilisateurs/classements)

## Exigences
- Python 3.8+ (ou la version Python 3 disponible sur votre machine)
- Accès réseau local entre les appareils (même réseau Wi‑Fi)

## Installation et exécution (local)
Ouvrez un terminal dans le dossier du projet et exécutez :

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask flask-socketio eventlet
# ensuite lancer le serveur
python3 server.py
```

Par défaut le serveur écoute sur le port 8080 et affiche à l'exécution l'adresse LAN à utiliser depuis un autre appareil, par exemple : `http://192.168.x.x:8080/`.

Si votre téléphone est sur le même réseau Wi‑Fi, entrez cette adresse dans le navigateur pour accéder au jeu.

## Remarques
- Les assets sont dessinés à la main par l'auteur du projet.
- Si vous rencontrez des problèmes pour accéder au serveur depuis un autre appareil, vérifiez que le pare-feu ne bloque pas le port 8080 et que les deux appareils sont bien sur le même réseau.

---

## The Loulou Phone (English)

> Multiplayer online game developed as a Web & Database course final project inspire by the game Gartic Phone.

## Description (English)

The Loulou Phone is a small web multiplayer game where players interact in real time.
The front-end (HTML/CSS/JS) and graphical assets were hand-drawn and integrated into the project.
The server is written in Python using Flask and uses WebSocket (via Flask-SocketIO) for real-time communication.

Key features:
- Real-time multiplayer (Socket.IO)
- Hand-drawn UI/assets
- Local hosting with access from other devices on the same LAN

## Technologies
- Python 3
- Flask
- Flask-SocketIO (python-socketio + python-engineio)
- eventlet (async WSGI server)
- HTML, CSS, JavaScript
- (Possibly SQLite via `database.py` for user/leaderboard storage)

## Requirements
- Python 3.8+ (or your system Python 3)
- Local network connectivity between devices (same Wi‑Fi)

## Install and run (local)
Open a terminal in the project folder and run:

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask flask-socketio eventlet
# then start the server
python3 server.py
```

By default the server listens on port 8080 and prints the LAN address to use from other devices, e.g. `http://192.168.x.x:8080/`.

If your phone is on the same Wi‑Fi network, open that address in the browser to reach the game.


## Notes
- All graphical assets were hand-drawn by the project author.
- If you cannot reach the server from another device, check firewall rules and ensure both devices are on the same subnet.
