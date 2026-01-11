#!/usr/bin/env python3
"""
Narrator Server - Loup-Garou Distribué
Serveur TCP qui orchestre la partie complète
"""

import socket
import threading
import json
import random
import time
from typing import Dict, List, Optional

# Configuration
HOST = '0.0.0.0'
PORT = 5000
BUFFER_SIZE = 4096

# Rôles disponibles
ROLES = {
    'WEREWOLF': 'Loup-Garou',
    'VILLAGER': 'Villageois',
    'SEER': 'Voyante'
}


class Player:
    """Représente un joueur connecté"""
    def __init__(self, conn: socket.socket, addr: tuple, player_id: str):
        self.conn = conn
        self.addr = addr
        self.player_id = player_id
        self.role = None
        self.alive = True

    def send_message(self, msg_type: str, data: dict = None):
        """Envoie un message JSON au joueur"""
        message = {
            'type': msg_type,
            'data': data or {}
        }
        try:
            self.conn.sendall(json.dumps(message).encode('utf-8') + b'\n')
            print(f"[SEND → {self.player_id}] {msg_type}: {data}")
        except Exception as e:
            print(f"[ERROR] Erreur d'envoi vers {self.player_id}: {e}")


class NarratorServer:
    """Serveur principal du jeu"""

    def __init__(self, host: str, port: int, expected_players: int = 3):
        self.host = host
        self.port = port
        self.expected_players = expected_players
        self.players: Dict[str, Player] = {}
        self.lock = threading.Lock()
        self.game_started = False

    def start(self):
        """Démarre le serveur TCP"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(10)

        print(f"[NARRATOR] Serveur démarré sur {self.host}:{self.port}")
        print(f"[NARRATOR] En attente de {self.expected_players} joueurs...\n")

        try:
            while len(self.players) < self.expected_players:
                conn, addr = server_socket.accept()
                threading.Thread(target=self.handle_player_connection, args=(conn, addr), daemon=True).start()

            # Tous les joueurs sont connectés
            print(f"\n[NARRATOR] Tous les joueurs sont connectés ! Démarrage de la partie...\n")
            time.sleep(2)
            self.start_game()

        except KeyboardInterrupt:
            print("\n[NARRATOR] Arrêt du serveur...")
        finally:
            server_socket.close()

    def handle_player_connection(self, conn: socket.socket, addr: tuple):
        """Gère la connexion d'un nouveau joueur"""
        try:
            # Réception du message de connexion
            data = conn.recv(BUFFER_SIZE).decode('utf-8').strip()
            message = json.loads(data)

            if message['type'] == 'CONNECT':
                player_id = message['data']['player_id']

                with self.lock:
                    player = Player(conn, addr, player_id)
                    self.players[player_id] = player
                    print(f"[CONNECTION] {player_id} connecté depuis {addr}")

                    # Confirmation de connexion
                    player.send_message('CONNECTED', {'player_id': player_id, 'status': 'waiting'})

                # Garder la connexion ouverte
                while True:
                    time.sleep(1)

        except Exception as e:
            print(f"[ERROR] Erreur avec {addr}: {e}")
            conn.close()

    def start_game(self):
        """Démarre la partie"""
        self.game_started = True

        # Attribution aléatoire des rôles
        self.assign_roles()
        time.sleep(2)

        # Boucle de jeu
        turn = 1
        while not self.check_game_over():
            print(f"\n{'='*60}")
            print(f"TOUR {turn}")
            print(f"{'='*60}\n")

            # Phase Nuit
            self.night_phase()
            time.sleep(3)

            if self.check_game_over():
                break

            # Phase Jour
            self.day_phase()
            time.sleep(3)

            turn += 1

        # Fin de partie
        self.end_game()

    def assign_roles(self):
        """Attribue les rôles aléatoirement"""
        print("[GAME] Attribution des rôles...\n")

        player_list = list(self.players.values())
        random.shuffle(player_list)

        # 1 Loup-Garou, 1 Voyante, le reste Villageois
        roles_to_assign = ['WEREWOLF', 'SEER'] + ['VILLAGER'] * (len(player_list) - 2)

        for player, role in zip(player_list, roles_to_assign):
            player.role = role
            player.send_message('WELCOME', {
                'role': role,
                'role_name': ROLES[role],
                'description': self.get_role_description(role)
            })
            print(f"[ROLE] {player.player_id} → {ROLES[role]}")

        print()

    def get_role_description(self, role: str) -> str:
        """Retourne la description d'un rôle"""
        descriptions = {
            'WEREWOLF': 'Vous êtes un Loup-Garou. Chaque nuit, désignez une victime.',
            'SEER': 'Vous êtes la Voyante. Chaque nuit, espionnez un joueur.',
            'VILLAGER': 'Vous êtes un Villageois. Votez le jour pour éliminer les loups.'
        }
        return descriptions.get(role, '')

    def night_phase(self):
        """Phase de nuit : actions des loups et voyante"""
        print("[NIGHT] 🌙 La nuit tombe sur le village...\n")

        # Notifier tous les joueurs
        alive_players = [p.player_id for p in self.players.values() if p.alive]
        for player in self.players.values():
            if player.alive:
                player.send_message('NIGHT_PHASE', {'alive_players': alive_players})

        time.sleep(1)

        # Actions des Loups-Garous
        werewolf_target = self.request_werewolf_action()

        # Action de la Voyante
        seer_target = self.request_seer_action()

        # Résultats de la nuit
        if werewolf_target:
            victim = self.players.get(werewolf_target)
            if victim and victim.alive:
                victim.alive = False
                print(f"[NIGHT] ⚰️  {werewolf_target} a été dévoré par les loups !\n")

        if seer_target:
            target = self.players.get(seer_target)
            if target:
                seer = next((p for p in self.players.values() if p.role == 'SEER' and p.alive), None)
                if seer:
                    seer.send_message('SEER_RESULT', {
                        'target': seer_target,
                        'is_werewolf': target.role == 'WEREWOLF'
                    })
                    print(f"[NIGHT] 🔮 La Voyante a espionné {seer_target}\n")

    def request_werewolf_action(self) -> Optional[str]:
        """Demande aux loups de choisir une victime"""
        werewolves = [p for p in self.players.values() if p.role == 'WEREWOLF' and p.alive]
        if not werewolves:
            return None

        wolf = werewolves[0]
        alive_others = [p.player_id for p in self.players.values() if p.alive and p.player_id != wolf.player_id]

        wolf.send_message('REQUEST_ACTION', {
            'action': 'KILL',
            'targets': alive_others
        })

        # Attendre la réponse
        try:
            response = wolf.conn.recv(BUFFER_SIZE).decode('utf-8').strip()
            message = json.loads(response)
            if message['type'] == 'ACTION':
                target = message['data']['target']
                print(f"[NIGHT] 🐺 Les loups attaquent {target}")
                return target
        except Exception as e:
            print(f"[ERROR] Erreur réception action loup: {e}")

        return None

    def request_seer_action(self) -> Optional[str]:
        """Demande à la voyante d'espionner quelqu'un"""
        seers = [p for p in self.players.values() if p.role == 'SEER' and p.alive]
        if not seers:
            return None

        seer = seers[0]
        alive_others = [p.player_id for p in self.players.values() if p.alive and p.player_id != seer.player_id]

        seer.send_message('REQUEST_ACTION', {
            'action': 'SPY',
            'targets': alive_others
        })

        # Attendre la réponse
        try:
            response = seer.conn.recv(BUFFER_SIZE).decode('utf-8').strip()
            message = json.loads(response)
            if message['type'] == 'ACTION':
                target = message['data']['target']
                print(f"[NIGHT] 🔮 La Voyante espionne {target}")
                return target
        except Exception as e:
            print(f"[ERROR] Erreur réception action voyante: {e}")

        return None

    def day_phase(self):
        """Phase de jour : vote pour éliminer quelqu'un"""
        print("[DAY] ☀️  Le jour se lève...\n")

        # Annoncer les morts de la nuit
        dead_last_night = [p.player_id for p in self.players.values() if not p.alive]
        alive_players = [p.player_id for p in self.players.values() if p.alive]

        for player in self.players.values():
            player.send_message('DAY_PHASE', {
                'dead_last_night': dead_last_night,
                'alive_players': alive_players
            })

        time.sleep(1)

        # Vote du village
        votes = self.request_village_vote()

        # Décompte des votes
        if votes:
            vote_counts = {}
            for target in votes:
                vote_counts[target] = vote_counts.get(target, 0) + 1

            eliminated = max(vote_counts, key=vote_counts.get)
            eliminated_player = self.players.get(eliminated)
            if eliminated_player:
                eliminated_player.alive = False
                print(f"\n[DAY] 🗳️  Le village a voté : {eliminated} est éliminé (rôle: {ROLES[eliminated_player.role]})\n")

                # Notifier tous les joueurs
                for player in self.players.values():
                    player.send_message('VOTE_RESULT', {
                        'eliminated': eliminated,
                        'role': eliminated_player.role,
                        'votes': vote_counts
                    })

    def request_village_vote(self) -> List[str]:
        """Demande à tous les joueurs vivants de voter"""
        votes = []
        alive = [p for p in self.players.values() if p.alive]

        print("[DAY] 🗳️  Vote du village en cours...\n")

        for player in alive:
            alive_others = [p.player_id for p in self.players.values() if p.alive and p.player_id != player.player_id]

            player.send_message('REQUEST_ACTION', {
                'action': 'VOTE',
                'targets': alive_others
            })

            # Attendre le vote
            try:
                response = player.conn.recv(BUFFER_SIZE).decode('utf-8').strip()
                message = json.loads(response)
                if message['type'] == 'ACTION':
                    target = message['data']['target']
                    votes.append(target)
                    print(f"[DAY] {player.player_id} vote contre {target}")
            except Exception as e:
                print(f"[ERROR] Erreur réception vote de {player.player_id}: {e}")

        return votes

    def check_game_over(self) -> bool:
        """Vérifie si la partie est terminée"""
        alive = [p for p in self.players.values() if p.alive]
        werewolves_alive = [p for p in alive if p.role == 'WEREWOLF']
        villagers_alive = [p for p in alive if p.role != 'WEREWOLF']

        if len(werewolves_alive) == 0:
            print("\n[GAME OVER] 🎉 Les Villageois ont gagné !\n")
            return True

        if len(werewolves_alive) >= len(villagers_alive):
            print("\n[GAME OVER] 🐺 Les Loups-Garous ont gagné !\n")
            return True

        return False

    def end_game(self):
        """Termine la partie"""
        winner = 'VILLAGERS' if not any(p.alive and p.role == 'WEREWOLF' for p in self.players.values()) else 'WEREWOLVES'

        final_state = {
            'winner': winner,
            'players': {
                p.player_id: {
                    'role': ROLES[p.role],
                    'alive': p.alive
                } for p in self.players.values()
            }
        }

        for player in self.players.values():
            player.send_message('GAME_OVER', final_state)

        print("[GAME] Partie terminée. Fermeture des connexions...")
        time.sleep(3)

        for player in self.players.values():
            player.conn.close()


def main():
    """Point d'entrée principal"""
    import os

    host = os.getenv('NARRATOR_HOST', HOST)
    port = int(os.getenv('NARRATOR_PORT', PORT))
    expected_players = int(os.getenv('EXPECTED_PLAYERS', 3))

    print("""
    ╔═══════════════════════════════════════╗
    ║   LOUP-GAROU DISTRIBUÉ - NARRATOR    ║
    ║     Serveur TCP d'orchestration      ║
    ╚═══════════════════════════════════════╝
    """)

    narrator = NarratorServer(host, port, expected_players)
    narrator.start()


if __name__ == '__main__':
    main()
