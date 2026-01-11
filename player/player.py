#!/usr/bin/env python3
"""
Player Client - Loup-Garou Distribué
Client TCP avec IA automatique pour jouer
"""

import socket
import json
import random
import time
import os

# Configuration
BUFFER_SIZE = 4096


class PlayerClient:
    """Client joueur avec IA automatique"""

    def __init__(self, player_id: str, narrator_host: str, narrator_port: int):
        self.player_id = player_id
        self.narrator_host = narrator_host
        self.narrator_port = narrator_port
        self.sock = None
        self.role = None
        self.alive = True
        self.known_wolves = []  # Pour la voyante

    def connect(self):
        """Se connecte au serveur narrator"""
        print(f"[{self.player_id}] Connexion au narrator {self.narrator_host}:{self.narrator_port}...")

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.narrator_host, self.narrator_port))

            # Envoyer le message de connexion
            connect_msg = {
                'type': 'CONNECT',
                'data': {'player_id': self.player_id}
            }
            self.send_message(connect_msg)

            print(f"[{self.player_id}] ✅ Connecté au narrator\n")
            return True

        except Exception as e:
            print(f"[{self.player_id}] ❌ Erreur de connexion: {e}")
            return False

    def send_message(self, message: dict):
        """Envoie un message JSON au narrator"""
        try:
            self.sock.sendall(json.dumps(message).encode('utf-8') + b'\n')
        except Exception as e:
            print(f"[{self.player_id}] Erreur d'envoi: {e}")

    def receive_message(self) -> dict:
        """Reçoit un message JSON du narrator"""
        try:
            data = self.sock.recv(BUFFER_SIZE).decode('utf-8').strip()
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"[{self.player_id}] Erreur de réception: {e}")
        return None

    def run(self):
        """Boucle principale du client"""
        if not self.connect():
            return

        print(f"[{self.player_id}] En attente du début de la partie...\n")

        try:
            while True:
                message = self.receive_message()
                if not message:
                    continue

                self.handle_message(message)

        except KeyboardInterrupt:
            print(f"\n[{self.player_id}] Déconnexion...")
        except Exception as e:
            print(f"[{self.player_id}] Erreur: {e}")
        finally:
            if self.sock:
                self.sock.close()

    def handle_message(self, message: dict):
        """Traite un message reçu du narrator"""
        msg_type = message.get('type')
        data = message.get('data', {})

        if msg_type == 'CONNECTED':
            print(f"[{self.player_id}] Connexion confirmée, status: {data.get('status')}")

        elif msg_type == 'WELCOME':
            self.role = data.get('role')
            role_name = data.get('role_name')
            description = data.get('description')
            print(f"\n{'='*60}")
            print(f"[{self.player_id}] 🎭 Vous êtes : {role_name}")
            print(f"[{self.player_id}] 📜 {description}")
            print(f"{'='*60}\n")

        elif msg_type == 'NIGHT_PHASE':
            alive_players = data.get('alive_players', [])
            print(f"\n[{self.player_id}] 🌙 NUIT - Joueurs vivants: {', '.join(alive_players)}")

        elif msg_type == 'DAY_PHASE':
            dead_last_night = data.get('dead_last_night', [])
            alive_players = data.get('alive_players', [])
            if dead_last_night:
                print(f"\n[{self.player_id}] ☀️  JOUR - Morts cette nuit: {', '.join(dead_last_night)}")
            else:
                print(f"\n[{self.player_id}] ☀️  JOUR - Personne n'est mort cette nuit")
            print(f"[{self.player_id}] Joueurs vivants: {', '.join(alive_players)}")

        elif msg_type == 'REQUEST_ACTION':
            action = data.get('action')
            targets = data.get('targets', [])
            self.handle_action_request(action, targets)

        elif msg_type == 'SEER_RESULT':
            target = data.get('target')
            is_werewolf = data.get('is_werewolf')
            if is_werewolf:
                self.known_wolves.append(target)
                print(f"[{self.player_id}] 🔮 {target} est un LOUP-GAROU ! 🐺")
            else:
                print(f"[{self.player_id}] 🔮 {target} est innocent.")

        elif msg_type == 'VOTE_RESULT':
            eliminated = data.get('eliminated')
            role = data.get('role')
            votes = data.get('votes', {})
            print(f"\n[{self.player_id}] 🗳️  {eliminated} éliminé (était {role})")
            print(f"[{self.player_id}] Votes: {votes}")
            if eliminated == self.player_id:
                self.alive = False
                print(f"[{self.player_id}] ⚰️  Vous êtes mort !")

        elif msg_type == 'GAME_OVER':
            winner = data.get('winner')
            players_state = data.get('players', {})
            print(f"\n{'='*60}")
            print(f"[{self.player_id}] 🏁 GAME OVER - Vainqueur: {winner}")
            print(f"[{self.player_id}] État final:")
            for pid, state in players_state.items():
                status = "✅ Vivant" if state['alive'] else "⚰️  Mort"
                print(f"  - {pid}: {state['role']} ({status})")
            print(f"{'='*60}\n")

    def handle_action_request(self, action: str, targets: list):
        """Gère une demande d'action avec IA simple"""
        if not targets:
            print(f"[{self.player_id}] Aucune cible disponible pour {action}")
            return

        chosen_target = self.ai_choose_target(action, targets)

        print(f"[{self.player_id}] 🤖 IA décide : {action} → {chosen_target}")

        # Petit délai pour simuler la réflexion
        time.sleep(random.uniform(0.5, 1.5))

        # Envoyer la réponse
        response = {
            'type': 'ACTION',
            'data': {
                'action': action,
                'target': chosen_target
            }
        }
        self.send_message(response)

    def ai_choose_target(self, action: str, targets: list) -> str:
        """IA pour choisir une cible selon le rôle et l'action"""

        if action == 'KILL':
            # Loup-Garou : attaque aléatoire
            return random.choice(targets)

        elif action == 'SPY':
            # Voyante : espionne quelqu'un qu'elle ne connaît pas encore
            unknown_targets = [t for t in targets if t not in self.known_wolves]
            if unknown_targets:
                return random.choice(unknown_targets)
            return random.choice(targets)

        elif action == 'VOTE':
            # Vote intelligent selon le rôle
            if self.role == 'SEER' and self.known_wolves:
                # La voyante vote contre les loups connus
                wolves_alive = [w for w in self.known_wolves if w in targets]
                if wolves_alive:
                    return random.choice(wolves_alive)

            # Vote aléatoire sinon
            return random.choice(targets)

        # Par défaut
        return random.choice(targets)


def main():
    """Point d'entrée principal"""
    player_id = os.getenv('PLAYER_ID', f'player{random.randint(1000, 9999)}')
    narrator_host = os.getenv('NARRATOR_HOST', 'narrator')
    narrator_port = int(os.getenv('NARRATOR_PORT', 5000))

    print(f"""
    ╔═══════════════════════════════════════╗
    ║   LOUP-GAROU DISTRIBUÉ - PLAYER      ║
    ║      Client TCP avec IA auto         ║
    ║      ID: {player_id:<26} ║
    ╚═══════════════════════════════════════╝
    """)

    client = PlayerClient(player_id, narrator_host, narrator_port)
    client.run()


if __name__ == '__main__':
    main()
