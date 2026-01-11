#!/usr/bin/env python3
"""
Decision AI - Loup-Garou Distribué
IA observatrice qui analyse la partie et suggère des décisions
Client TCP passif qui écoute et commente (bonus Windows)
"""

import socket
import json
import random
import os
from typing import Dict, List


class DecisionAI:
    """IA qui observe la partie et analyse les décisions"""

    def __init__(self, player_id: str, narrator_host: str, narrator_port: int):
        self.player_id = player_id
        self.narrator_host = narrator_host
        self.narrator_port = narrator_port
        self.sock = None
        self.role = None
        self.game_state = {
            'alive_players': [],
            'dead_players': [],
            'voting_history': [],
            'suspicious_players': {}
        }

    def connect(self):
        """Se connecte au serveur narrator en tant qu'observateur"""
        print(f"[{self.player_id}] 🤖 Connexion au narrator {self.narrator_host}:{self.narrator_port}...")

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.narrator_host, self.narrator_port))

            # Envoyer le message de connexion
            connect_msg = {
                'type': 'CONNECT',
                'data': {'player_id': self.player_id}
            }
            self.send_message(connect_msg)

            print(f"[{self.player_id}] ✅ Connecté en mode observation\n")
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
            data = self.sock.recv(4096).decode('utf-8').strip()
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"[{self.player_id}] Erreur de réception: {e}")
        return None

    def run(self):
        """Boucle principale de l'IA"""
        if not self.connect():
            return

        print(f"[{self.player_id}] 🧠 IA d'analyse activée...\n")

        try:
            while True:
                message = self.receive_message()
                if not message:
                    continue

                self.analyze_message(message)

        except KeyboardInterrupt:
            print(f"\n[{self.player_id}] Déconnexion...")
        except Exception as e:
            print(f"[{self.player_id}] Erreur: {e}")
        finally:
            if self.sock:
                self.sock.close()

    def analyze_message(self, message: dict):
        """Analyse les messages et fournit des insights"""
        msg_type = message.get('type')
        data = message.get('data', {})

        if msg_type == 'WELCOME':
            self.role = data.get('role')
            role_name = data.get('role_name')
            print(f"\n[AI 🤖] Rôle assigné: {role_name}")
            print(f"[AI 🤖] Stratégie: {'Éliminer villageois' if self.role == 'WEREWOLF' else 'Identifier les loups'}\n")

        elif msg_type == 'NIGHT_PHASE':
            alive = data.get('alive_players', [])
            self.game_state['alive_players'] = alive
            print(f"\n[AI 🤖] 🌙 ANALYSE NUIT")
            print(f"[AI 🤖] Joueurs vivants: {len(alive)}")

        elif msg_type == 'DAY_PHASE':
            dead = data.get('dead_last_night', [])
            if dead:
                self.game_state['dead_players'].extend(dead)
                print(f"\n[AI 🤖] ☀️  ANALYSE JOUR")
                print(f"[AI 🤖] Morts cette nuit: {dead}")
                self.analyze_deaths(dead)

        elif msg_type == 'REQUEST_ACTION':
            action = data.get('action')
            targets = data.get('targets', [])
            recommendation = self.ai_recommend_action(action, targets)
            print(f"\n[AI 🤖] 💡 RECOMMANDATION:")
            print(f"[AI 🤖] Action: {action}")
            print(f"[AI 🤖] Cible suggérée: {recommendation}")
            self.execute_action(action, recommendation)

        elif msg_type == 'VOTE_RESULT':
            eliminated = data.get('eliminated')
            role = data.get('role')
            votes = data.get('votes', {})
            self.game_state['voting_history'].append({
                'eliminated': eliminated,
                'role': role,
                'votes': votes
            })
            print(f"\n[AI 🤖] 📊 ANALYSE DU VOTE:")
            print(f"[AI 🤖] Éliminé: {eliminated} (rôle: {role})")
            print(f"[AI 🤖] Distribution des votes: {votes}")
            self.analyze_voting_pattern(votes, eliminated, role)

        elif msg_type == 'SEER_RESULT':
            target = data.get('target')
            is_werewolf = data.get('is_werewolf')
            if is_werewolf:
                self.game_state['suspicious_players'][target] = 'CONFIRMED_WOLF'
                print(f"\n[AI 🤖] 🔮 {target} est confirmé LOUP-GAROU!")
            else:
                print(f"\n[AI 🤖] 🔮 {target} est innocent")

        elif msg_type == 'GAME_OVER':
            winner = data.get('winner')
            print(f"\n{'='*60}")
            print(f"[AI 🤖] 🏁 FIN DE PARTIE - Vainqueur: {winner}")
            self.final_analysis()
            print(f"{'='*60}\n")

    def analyze_deaths(self, dead_players: List[str]):
        """Analyse les patterns de morts"""
        print(f"[AI 🤖] Hypothèse: Cibles probablement stratégiques")
        if len(self.game_state['dead_players']) > 1:
            print(f"[AI 🤖] Total éliminés: {len(self.game_state['dead_players'])}")

    def analyze_voting_pattern(self, votes: Dict[str, int], eliminated: str, role: str):
        """Analyse les patterns de vote"""
        if role == 'WEREWOLF':
            print(f"[AI 🤖] ✅ Bon vote ! Un loup éliminé.")
        else:
            print(f"[AI 🤖] ⚠️  Un innocent éliminé, les loups progressent.")

        # Marquer les joueurs suspects
        for player, vote_count in votes.items():
            if player != eliminated and vote_count > 1:
                self.game_state['suspicious_players'][player] = \
                    self.game_state['suspicious_players'].get(player, 0) + 1

    def ai_recommend_action(self, action: str, targets: List[str]) -> str:
        """Recommandation intelligente basée sur l'historique"""
        if not targets:
            return None

        if action == 'KILL':
            # Loup : cibler les joueurs influents
            return random.choice(targets)

        elif action == 'SPY':
            # Voyante : espionner les suspects
            unknown = [t for t in targets if t not in self.game_state['suspicious_players']]
            if unknown:
                return random.choice(unknown)
            return random.choice(targets)

        elif action == 'VOTE':
            # Voter contre les loups confirmés
            if self.role == 'SEER':
                confirmed_wolves = [
                    p for p, status in self.game_state['suspicious_players'].items()
                    if status == 'CONFIRMED_WOLF' and p in targets
                ]
                if confirmed_wolves:
                    return confirmed_wolves[0]

            # Sinon voter contre le plus suspect
            suspects = {
                p: score for p, score in self.game_state['suspicious_players'].items()
                if p in targets and isinstance(score, int)
            }
            if suspects:
                return max(suspects, key=suspects.get)

            return random.choice(targets)

        return random.choice(targets)

    def execute_action(self, action: str, target: str):
        """Envoie l'action recommandée"""
        if not target:
            return

        response = {
            'type': 'ACTION',
            'data': {
                'action': action,
                'target': target
            }
        }
        self.send_message(response)
        print(f"[AI 🤖] ✉️  Action envoyée: {action} → {target}")

    def final_analysis(self):
        """Analyse finale de la partie"""
        print(f"\n[AI 🤖] 📈 ANALYSE FINALE:")
        print(f"[AI 🤖] Total de tours: {len(self.game_state['voting_history'])}")
        print(f"[AI 🤖] Joueurs éliminés: {len(self.game_state['dead_players'])}")
        if self.game_state['voting_history']:
            print(f"[AI 🤖] Historique des votes:")
            for i, vote in enumerate(self.game_state['voting_history'], 1):
                print(f"[AI 🤖]   Tour {i}: {vote['eliminated']} ({vote['role']})")


def main():
    """Point d'entrée principal"""
    player_id = os.getenv('PLAYER_ID', 'decision_ai')
    narrator_host = os.getenv('NARRATOR_HOST', 'narrator')
    narrator_port = int(os.getenv('NARRATOR_PORT', 5000))

    print(f"""
    ╔═══════════════════════════════════════╗
    ║   LOUP-GAROU DISTRIBUÉ - AI          ║
    ║      IA d'analyse et décision        ║
    ║      Mode: Observation + Action      ║
    ╚═══════════════════════════════════════╝
    """)

    ai = DecisionAI(player_id, narrator_host, narrator_port)
    ai.run()


if __name__ == '__main__':
    main()
