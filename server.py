from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room
import database
import random
import time

"""
Coquard-Morel
Lou-Ann
L2-Y

-Développement Web et Base de données-

                 Projet Final :
                Le Loulou Phone
"""

app = Flask(__name__)
app.secret_key = "secret_key"
socketio = SocketIO(app, cors_allowed_origins="*")

groups = {}  # Stocke les groupes et leurs joueurs
game_sessions = {}  # Stocke les joueurs en jeu avec leur ID

#L'accueil et login :

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if "register" in request.form:
            if database.create_user(username, password):
                session["user"] = username
                return redirect("/home")
            else:
                return "Utilisateur déjà existant."
        elif "login" in request.form:
            if database.check_user(username, password):
                session["user"] = username
                return redirect("/home")
            else:
                return "Nom d'utilisateur ou mot de passe incorrect."

    return render_template("login.html")

@app.route("/home", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect("/")
    if request.method == "POST":
        if "create_group" in request.form:
            group_code = str(random.randint(1000, 9999))
            groups[group_code] = [session["user"]]
            return redirect(f"/lobby/{group_code}")
        elif "join_group" in request.form:
            group_code = request.form["group_code"]
            if group_code in groups and len(groups[group_code]) < 6:
                groups[group_code].append(session["user"])
                return redirect(f"/lobby/{group_code}")
            else:
                return render_template("oups.html")
    points = database.get_points(session["user"])
    return render_template("home.html", username=session["user"], points=points)

#Le lobby : 

@app.route("/lobby/<group_code>")
def lobby(group_code):
    if "user" not in session or group_code not in groups or session["user"] not in groups[group_code]:
        return redirect("/home")
    return render_template("lobby.html", group_code=group_code, players=groups[group_code])

@app.route("/lobby/<group_code>/players")
def lobby_players(group_code):
    return jsonify(groups.get(group_code, []))

@socketio.on("join_lobby")
def handle_join_lobby(data):
    group_code = data["group_code"]
    join_room(group_code)  # Ajoute l'utilisateur à une "salle" WebSocket

# Démarrer le jeu : 

@socketio.on("start_game")
def handle_start_game(data):
    group_code = data["group_code"]
    if group_code in groups and len(groups[group_code]) >= 4:
        players = groups[group_code]
        total_players = len(players)
        game_sessions[group_code] = {
            "players": {player: i+1 for i, player in enumerate(players)},
            "state": "countdown",
            "sentences": [None] * total_players,  # Initialiser avec des espaces pour le premier tour
            "drawings": [],   
            "tours": 1,
            "completed_players": 0,  # Compteur pour synchroniser la fin des tours
            "current_phase": "enter_sentence",  # Phase actuelle du jeu
            "total_players": total_players  # Stocker le nombre total de joueurs
        }
        # Rediriger vers la page `game.html` pour tous les joueurs
        emit("redirect_to_game", {"url": f"/game/{group_code}"}, room=group_code)
        # Démarrer le premier tour avec un timer centralisé
        start_new_phase(group_code)
        del groups[group_code]  # Supprime le groupe après démarrage

def start_new_phase(group_code):
    """Démarre une nouvelle phase du jeu avec un timer centralisé"""
    if group_code not in game_sessions:
        return
    # Réinitialiser le compteur de joueurs ayant terminé
    game_sessions[group_code]["completed_players"] = 0
    # Envoyer l'information du tour à tous les joueurs
    socketio.emit("sync_tour", {
        "tours": game_sessions[group_code]["tours"]
    }, room=group_code)

@app.route("/game/<group_code>")
def game(group_code):
    if "user" not in session or group_code not in game_sessions or session["user"] not in game_sessions[group_code]["players"]:
        return redirect("/home")  # Assure que l'utilisateur fait partie du jeu avant d'afficher game.html
    player_id = game_sessions[group_code]["players"][session["user"]]
    return render_template("game.html", group_code=group_code, player_id=player_id,tours=game_sessions[group_code]["tours"])

#Début du jeu : entrer une phrase

@app.route("/enter_sentence/<group_code>")
def enter(group_code):
    if "user" not in session or group_code not in game_sessions or session["user"] not in game_sessions[group_code]["players"]:
        return redirect("/home")
    player_id = game_sessions[group_code]["players"][session["user"]]
    return render_template("enter_sentence.html", group_code=group_code, tours=game_sessions[group_code]["tours"], player_id=player_id)

@socketio.on("sentence_finished")
def handle_sentence_finished(data):
    group_code = data["group_code"]
    if group_code in game_sessions:
        # Une fois le timer terminé, stocke la phrase et redirige vers la page de dessin
        user = session["user"]
        sentence = data["sentence"]  # Récupère la phrase entrée
        player_id = game_sessions[group_code]["players"][user]
        total_players = game_sessions[group_code]["total_players"]
        tour_actuel = game_sessions[group_code]["tours"]
        # Calculer l'index correct pour stocker la phrase
        if tour_actuel == 1:
            # Premier tour: stocker par ordre de player_id
            index = player_id - 1
        else:
            # Tours impairs (3, 5, etc.) pour les phrases
            round_offset = ((tour_actuel - 1) // 2) * total_players
            index = round_offset + (player_id - 1)
        # S'assurer que la liste sentences est assez grande
        while len(game_sessions[group_code]["sentences"]) <= index:
            game_sessions[group_code]["sentences"].append(None)
        # Stocker la phrase à l'index correct
        game_sessions[group_code]["sentences"][index] = sentence
        # Incrémenter le compteur des joueurs ayant terminé
        game_sessions[group_code]["completed_players"] += 1
        # Informer tous les joueurs du progrès
        emit("progress_update", {
            "completed": game_sessions[group_code]["completed_players"],
            "total": total_players
        }, room=group_code)
        # Vérifier si tous les joueurs ont fini
        if game_sessions[group_code]["completed_players"] == total_players:
            game_sessions[group_code]["completed_players"] = 0  # Réinitialiser le compteur
            # Incrémenter le tour après chaque phase
            game_sessions[group_code]["tours"] += 1
            # Vérifier si c'est la fin du jeu
            max_tours = total_players # Nombre de tours égal au nombre de joueurs
            if game_sessions[group_code]["tours"] > max_tours:
                print(f"Contenu de sentences pour {group_code} :", game_sessions[group_code]["sentences"])  # Affiche les phrases en console
                emit("all_completed", {"next_page": f"/fin/{group_code}/0"}, room=group_code)
            else:
                # Après drawing, on passe toujours à guess
                emit("all_completed", {"next_page": "drawing"}, room=group_code)
                
                # Synchroniser le numéro du tour pour tous les joueurs
                emit("sync_tour", {"tours": game_sessions[group_code]["tours"]}, room=group_code)


#Partie dessin :

@app.route("/drawing/<group_code>")
def drawing(group_code):
    if "user" not in session or group_code not in game_sessions or session["user"] not in game_sessions[group_code]["players"]:
        return redirect("/home")
    # Récupérer l'ID du joueur actuel
    player_id = game_sessions[group_code]["players"][session["user"]]
    total_players = game_sessions[group_code]["total_players"]
    # Vérifier si c'est la fin du jeu
    max_tours = total_players 
    if game_sessions[group_code]["tours"] > max_tours:
        print(f"Contenu de sentences pour {group_code} :", game_sessions[group_code]["sentences"])  # Affiche les phrases en console
        return redirect(f"/fin/{group_code}/0")
    tour_actuel = game_sessions[group_code]["tours"]
    # Calculer l'index du joueur précédent 
    if player_id==1 :
        previous_player_index = (total_players*((tour_actuel)//2 - 1)) + (total_players - 1)
        #previous_player_index = (player_id - 2) % total_players
    else :
        previous_player_index = (total_players*((tour_actuel)//2 - 1)) + (player_id - 1) - 1
    # Calculer l'index de la phrase à dessiner
    sentence_index = previous_player_index
    # S'assurer que l'index est valide
    sentence = "Phrase indisponible pour le moment."
    if len(game_sessions[group_code]["sentences"]) > sentence_index:
        sentence = game_sessions[group_code]["sentences"][sentence_index]
    return render_template("drawing.html", group_code=group_code, player_id=player_id, sentence=sentence, tours=game_sessions[group_code]["tours"])

@socketio.on("get_previous_sentence")
def handle_get_previous_sentence(data):
    group_code = data["group_code"]
    player_id = int(data["player_id"])  # Convert to int
    if group_code not in game_sessions:
        return
    total_players = game_sessions[group_code]["total_players"]
    tour_actuel = game_sessions[group_code]["tours"]
    # Calculer l'index du joueur précédent 
    if player_id==1 :
        previous_player_index = (total_players*((tour_actuel)//2 - 1)) + (total_players - 1)
        #previous_player_index = (player_id - 2) % total_players
    else :
        previous_player_index = (total_players*((tour_actuel)//2 - 1)) + (player_id - 1) - 1
    # Récupérer la phrase du joueur précédent
    sentence = "Phrase indisponible pour le moment."
    if len(game_sessions[group_code]["sentences"]) > previous_player_index:
        sentence = game_sessions[group_code]["sentences"][previous_player_index]
    emit("previous_sentence", {"sentence": sentence})

@socketio.on("drawing_submitted")
def handle_drawing_submission(data):
    group_code = data["group_code"]
    user = session["user"]
    drawing = data["drawing"]
    if group_code not in game_sessions:
        return
    player_id = game_sessions[group_code]["players"][user]
    total_players = game_sessions[group_code]["total_players"]
    tour_actuel = game_sessions[group_code]["tours"]
    # Calculer l'index correct pour stocker le dessin
    # Tours pairs (2, 4, etc.) pour les dessins
    round_offset = ((tour_actuel - 2) // 2) * total_players
    index = round_offset + (player_id - 1)
    # S'assurer que la liste drawings est assez grande
    while len(game_sessions[group_code]["drawings"]) <= index:
        game_sessions[group_code]["drawings"].append(None)
    # Stocker le dessin à l'index correct
    game_sessions[group_code]["drawings"][index] = drawing
    # Incrémenter le compteur des joueurs ayant terminé
    game_sessions[group_code]["completed_players"] += 1
    # Informer tous les joueurs du progrès
    emit("progress_update", {
        "completed": game_sessions[group_code]["completed_players"],
        "total": total_players
    }, room=group_code)
    # Vérifier si tous les joueurs ont fini
    if game_sessions[group_code]["completed_players"] == total_players:
        game_sessions[group_code]["completed_players"] = 0  # Réinitialiser le compteur
        # Incrémenter le tour après chaque phase
        game_sessions[group_code]["tours"] += 1
        # Vérifier si c'est la fin du jeu
        max_tours = total_players # Nombre de tours égal au nombre de joueurs
        if game_sessions[group_code]["tours"] > max_tours:
            print(f"Contenu de sentences pour {group_code} :", game_sessions[group_code]["sentences"])  # Affiche les phrases en console
            emit("all_completed", {"next_page": f"/fin/{group_code}/0"}, room=group_code)
        else:
            # Après drawing, on passe toujours à guess
            emit("all_completed", {"next_page": "guess"}, room=group_code)
            # Synchroniser le numéro du tour pour tous les joueurs
            emit("sync_tour", {"tours": game_sessions[group_code]["tours"]}, room=group_code)


# Partie deviner :

@app.route("/guess/<group_code>")
def enter_guess(group_code):
    if "user" not in session or group_code not in game_sessions or session["user"] not in game_sessions[group_code]["players"]:
        return redirect("/home")
    player_id = game_sessions[group_code]["players"][session["user"]]
    total_players = game_sessions[group_code]["total_players"]
    # Vérifier si c'est la fin du jeu
    max_tours = total_players # Nombre total de tours: players * 2
    if game_sessions[group_code]["tours"] > max_tours:
        print(f"Contenu de sentences pour {group_code} :", game_sessions[group_code]["sentences"])  # Affiche les phrases en console
        return redirect(f"/fin/{group_code}/0")
    tour_actuel = game_sessions[group_code]["tours"]
    # Calculer l'index du joueur précédent
    if player_id==1 :
        previous_player_index = (total_players*((tour_actuel - 1)//2 - 1)) + (total_players - 1)
        #previous_player_index = (player_id - 2) % total_players
    else :
        previous_player_index = (total_players*((tour_actuel - 1)//2 - 1)) + (player_id - 1) - 1
    # Calculer l'index du dessin à deviner
    drawing_index = previous_player_index
    # S'assurer que l'index est valide
    drawing = ""
    if len(game_sessions[group_code]["drawings"]) > drawing_index:
        drawing = game_sessions[group_code]["drawings"][drawing_index]
    return render_template("guess.html", group_code=group_code, player_id=player_id, tours=game_sessions[group_code]["tours"], drawing=drawing)

@socketio.on("get_previous_drawing")
def handle_get_previous_drawing(data):
    group_code = data["group_code"]
    player_id = int(data["player_id"])  # Convert to int
    if group_code not in game_sessions:
        return
    total_players = game_sessions[group_code]["total_players"]
    # Calculer l'index du joueur précédent
    tour_actuel = game_sessions[group_code]["tours"]
    if player_id==1 :
        previous_player_index = (total_players*((tour_actuel)//2 - 1)) + (total_players - 1)
        #previous_player_index = (player_id - 2) % total_players
    else :
        previous_player_index = (total_players*((tour_actuel)//2 - 1)) + (player_id - 1) - 1
    # Récupérer le dessin du joueur précédent
    drawing = ""
    if len(game_sessions[group_code]["drawings"]) > previous_player_index:
        drawing = game_sessions[group_code]["drawings"][previous_player_index]
    emit("previous_drawing", {"drawing": drawing})


@socketio.on("guess_submitted")
def handle_guess_submission(data):
    group_code = data["group_code"]
    user = session["user"]
    guess = data["guess"]
    if group_code not in game_sessions:
        return
    player_id = game_sessions[group_code]["players"][user]
    total_players = game_sessions[group_code]["total_players"]
    tour_actuel = game_sessions[group_code]["tours"]
    # Calculer l'index correct pour stocker la phrase devinée
    # Tours impairs (3, 5, etc.) pour les phrases
    round_offset = ((tour_actuel - 1) // 2) * total_players
    index = round_offset + (player_id - 1)
    # S'assurer que la liste sentences est assez grande
    while len(game_sessions[group_code]["sentences"]) <= index:
        game_sessions[group_code]["sentences"].append(None)
    # Stocker la phrase devinée à l'index correct
    game_sessions[group_code]["sentences"][index] = guess
    # Incrémenter le compteur des joueurs ayant terminé
    game_sessions[group_code]["completed_players"] += 1
    # Informer tous les joueurs du progrès
    emit("progress_update", {
        "completed": game_sessions[group_code]["completed_players"],
        "total": total_players
    }, room=group_code)
    # Vérifier si tous les joueurs ont fini
    if game_sessions[group_code]["completed_players"] == total_players:
        # Incrémenter le tour après chaque phase
        game_sessions[group_code]["tours"] += 1
        game_sessions[group_code]["completed_players"] = 0  # Réinitialiser le compteur
        # Vérifier si c'est la fin du jeu
        max_tours = total_players  # Nombre de tours égal au nombre de joueurs
        if game_sessions[group_code]["tours"] > max_tours:
            print(f"Contenu de sentences pour {group_code} :", game_sessions[group_code]["sentences"])  # Affiche les phrases en console
            emit("all_completed", {"next_page": f"/fin/{group_code}/0"}, room=group_code)
        else:
            # Après guess, on passe toujours à drawing
            emit("all_completed", {"next_page": "drawing"}, room=group_code)
            # Synchroniser le numéro du tour pour tous les joueurs
            emit("sync_tour", {"tours": game_sessions[group_code]["tours"]}, room=group_code)

#Fin :
@app.route("/fin/<group_code>/<int:current>")
def fin_jeu(group_code, current):
    if group_code not in game_sessions:
        return "Partie non trouvée", 404

    # Récupération des données du groupe
    session_data = game_sessions[group_code]

    players_list = list(session_data["players"].keys())  # Liste des joueurs (ordre de jeu)
    sentences_list = session_data["sentences"]  # Liste des phrases
    drawings_list = session_data["drawings"]  # Liste des dessins
    total_players = session_data["total_players"]  # Nombre total de joueurs

    # Récupérer les points de chaque joueur
    players_points = {player: database.get_points(player) for player in players_list}

    return render_template(
        "fin.html",
        players_list=players_list,
        sentences_list=sentences_list,
        drawings_list=drawings_list,
        current=current,
        total_players=total_players,
        group_code=group_code,
        players_points=players_points  # Ajouter les points des joueurs
    )

# Ajout de la route /ending pour correspondre au lien dans fin.html
@app.route("/ending/<group_code>/<int:current>")
def ending(group_code, current):
    # Rediriger vers la route /fin pour maintenir la cohérence
    return redirect(f"/fin/{group_code}/{current}")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/vote", methods=["POST"])
def vote():
    """Route pour gérer les votes des dessins"""
    data = request.get_json()
    player = data.get("player")
    points = int(data.get("points", 0))
    
    # Ajouter les points au joueur dans la base de données
    database.add_points(player, points)
    
    return jsonify({"success": True})

@app.route("/classement")
def classement():
    if "user" not in session:
        return redirect("/")
    # Récupérer tous les utilisateurs et leurs points, triés par points décroissants
    users_ranking = database.get_all_users_points()
    return render_template("classement.html", ranking=users_ranking, current_user=session["user"])

@app.route("/regles")
def regles():
    if "user" not in session:
        return redirect("/")
    # Récupérer tous les utilisateurs et leurs points, triés par points décroissants
    users_ranking = database.get_all_users_points()
    return render_template("regles.html", ranking=users_ranking, current_user=session["user"])

if __name__ == "__main__":
    import eventlet
    import eventlet.wsgi
    import socket
    import os
    # Determine LAN IP (not a loopback) by opening a UDP socket to a public IP
    # This doesn't send packets but reveals the outbound interface's IP.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        # Fallback to hostname resolution if the above fails
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"
    finally:
        s.close()

    # When Flask's debug reloader is active the process is started twice
    # (a parent watcher and a child serving process). Avoid running
    # duplicate startup actions (like printing) in the parent by
    # printing only in the actual server process.
    # The WERKZEUG_RUN_MAIN env var is set to 'true' in the child process
    # started by the reloader; when it's None the reloader is disabled.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or os.environ.get("WERKZEUG_RUN_MAIN") is None:
        print(">>> Serveur démarré !")
        print(f"Accès depuis ce PC : http://127.0.0.1:8080/")
        print(f"Accès depuis un autre appareil du même réseau : http://{local_ip}:8080/")
    # Disable the reloader to avoid starting the app twice (parent monitor + child server).
    socketio.run(app, host="0.0.0.0", port=8080, debug=True, use_reloader=False)