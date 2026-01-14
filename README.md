#  Loup-Garou Distribué - Projet Systèmes & Réseaux

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Protocol](https://img.shields.io/badge/Protocol-TCP/JSON-green)

**Projet pédagogique** de jeu du Loup-Garou entièrement distribué via containers Docker et communication TCP/JSON pure.

---

## 📋 Table des matières

- [Architecture](#-architecture)
- [Protocole réseau](#-protocole-réseau)
- [Structure du projet](#-structure-du-projet)
- [Installation](#-installation)
- [Déploiement](#-déploiement)
- [Démonstration](#-démonstration)
- [Explications techniques](#-explications-techniques)

---

## 🏗 Architecture

### Schéma d'infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                         VM1 (Proxmox)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          Container: garou-narrator                     │ │
│  │                                                        │ │
│  │  • Serveur TCP (0.0.0.0:5000)                         │ │
│  │  • Orchestration du jeu                               │ │
│  │  • Attribution des rôles                              │ │
│  │  • Gestion des phases (nuit/jour)                     │ │
│  │  • Calcul des votes                                   │ │
│  │                                                        │ │
│  │  Langage: Python 3.11                                 │ │
│  │  Protocole: TCP Socket + JSON                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                         ↑                                    │
│                         │ Port 5000                          │
└─────────────────────────┼──────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┬────────────────┐
          │               │               │                │
          │ TCP           │ TCP           │ TCP            │
          │ JSON          │ JSON          │ JSON           │
          ↓               ↓               ↓                ↓
┌──────────────────┐ ┌──────────────────────────────────┐ ┌─────────────┐
│   VM2 (Proxmox)  │ │        VM2 (Proxmox)            │ │   Windows   │
│ ┌──────────────┐ │ │ ┌──────────────┐ ┌────────────┐ │ │ ┌─────────┐ │
│ │   player1    │ │ │ │   player2    │ │  player3   │ │ │ │   AI    │ │
│ │              │ │ │ │              │ │            │ │ │ │ (bonus) │ │
│ │ Client TCP   │ │ │ │ Client TCP   │ │ Client TCP │ │ │ │ Client  │ │
│ │ Ordinateur auto      │ │ │ │ Ordinateur auto      │ │ Ordinateur auto    │ │ │ │ TCP     │ │
│ └──────────────┘ │ │ └──────────────┘ └────────────┘ │ │ └─────────┘ │
└──────────────────┘ └──────────────────────────────────┘ └─────────────┘
```

### Composants

| Composant | Type | VM | Rôle |
|-----------|------|----|----- |
| **narrator** | Serveur TCP | VM1 | Orchestrateur du jeu, gère toutes les phases |
| **player1, 2, 3** | Clients TCP | VM2 | Joueurs avec Ordinateur automatique |
| **decision_ai** | Client TCP | Windows (bonus) | Ordinateur d'analyse avancée |

---

## 🌐 Protocole réseau

### Pourquoi TCP et pas HTTP ?

1. **Communication persistante** : Les connexions restent ouvertes toute la partie
2. **Bidirectionnel natif** : Le serveur peut pousser des événements à tout moment
3. **Léger et rapide** : Pas de overhead HTTP (headers, méthodes, statuts)
4. **Pédagogique** : Démonstration de sockets bas niveau
5. **Réellement distribué** : Communication inter-VM sans dépendances web

### Format des messages

Tous les messages sont en **JSON** suivis d'un `\n`.

#### Messages Narrator → Players

```json
// Attribution du rôle
{
  "type": "WELCOME",
  "data": {
    "role": "LOUPGAROU",
    "role_name": "Loup-Garou",
    "description": "Vous êtes un Loup-Garou..."
  }
}

// Phase de nuit
{
  "type": "NIGHT_PHASE",
  "data": {
    "alive_players": ["player1", "player2", "player3"]
  }
}

// Demande d'action
{
  "type": "REQUEST_ACTION",
  "data": {
    "action": "VOTE",  // ou "KILL", "SPY"
    "targets": ["player2", "player3"]
  }
}

// Résultat du vote
{
  "type": "VOTE_RESULT",
  "data": {
    "eliminated": "player2",
    "role": "VILLAGEOIS",
    "votes": {"player2": 2, "player3": 1}
  }
}

// Fin de partie
{
  "type": "GAME_OVER",
  "data": {
    "winner": "WEREWOLVES",
    "players": {...}
  }
}
```

#### Messages Players → Narrator

```json
// Connexion initiale
{
  "type": "CONNECT",
  "data": {
    "player_id": "player1"
  }
}

// Action (vote, kill, spy)
{
  "type": "ACTION",
  "data": {
    "action": "VOTE",
    "target": "player3"
  }
}
```

### Flux de communication

```
Player1                  Narrator                  Player2
  │                          │                          │
  ├─── CONNECT ────────────→ │                          │
  │                          │ ←──── CONNECT ───────────┤
  │                          │                          │
  │ ←──── WELCOME ───────────┤                          │
  │                          ├────── WELCOME ──────────→│
  │                          │                          │
  │ ←─ NIGHT_PHASE ──────────┤                          │
  │                          ├──── NIGHT_PHASE ────────→│
  │                          │                          │
  ├─── ACTION (KILL) ───────→│                          │
  │                          │                          │
  │ ←─ DAY_PHASE ────────────┤                          │
  │                          ├───── DAY_PHASE ─────────→│
  │                          │                          │
  ├─── ACTION (VOTE) ───────→│                          │
  │                          │ ←──── ACTION (VOTE) ─────┤
  │                          │                          │
  │ ←─ VOTE_RESULT ──────────┤                          │
  │                          ├──── VOTE_RESULT ────────→│
  ...
```

---

## 📁 Structure du projet

```
project/
├── narrator/
│   ├── narrator.py        # Serveur TCP orchestrateur
│   └── Dockerfile
├── player/
│   ├── player.py          # Client TCP avec Ordinateur
│   └── Dockerfile
├── windows_ai/
│   ├── ai.py              # Ordinateur d'analyse avancée
│   └── Dockerfile
├── docker-compose-vm1.yml     # Déploiement VM1
├── docker-compose-vm2.yml     # Déploiement VM2
├── docker-compose-windows.yml # Déploiement Windows
├── docker-compose-local.yml   # Test local
└── README.md
```

---

## 🔧 Installation

### Prérequis

- Docker + Docker Compose
- Python 3.11+ (pour tests hors Docker)
- Réseau entre VM1 et VM2 (Proxmox)

### 1. Cloner le projet

```bash
git clone <repository>
cd garou-distribue
```

### 2. Construire les images

Sur **VM1** :
```bash
cd narrator/
docker build -t garou-narrator .
```

Sur **VM2** :
```bash
cd player/
docker build -t garou-player .
```

Sur **Windows** (optionnel) :
```bash
cd windows_ai/
docker build -t garou-ai .
```

---

## 🚀 Déploiement

### Configuration réseau

1. Récupérer l'**IP de VM1** :
   ```bash
   ip addr show  # Exemple: 192.168.1.100
   ```

2. Modifier `docker-compose-vm2.yml` :
   ```yaml
   environment:
     - NARRATOR_HOST=192.168.1.100  # ⚠️ Remplacer par l'IP de VM1
   ```

3. Modifier `docker-compose-windows.yml` de la même façon

### Lancement

#### 1. Démarrer le serveur (VM1)

```bash
docker-compose -f docker-compose-vm1.yml up
```

Vous devriez voir :
```
[NARRATOR] Serveur démarré sur 0.0.0.0:5000
[NARRATOR] En attente de 3 joueurs...
```

#### 2. Démarrer les joueurs (VM2)

```bash
docker-compose -f docker-compose-vm2.yml up
```

Les 3 joueurs se connectent automatiquement.

#### 3. (Optionnel) Démarrer l'Ordinateur (Windows)

```bash
docker-compose -f docker-compose-windows.yml up
```

### Test en local (sans multi-VM)

```bash
docker-compose -f docker-compose-local.yml up
```

Tous les containers tournent sur la même machine.

---

## 🎮 Démonstration

### Scénario type

1. **Démarrage** :
   - VM1 : Le narrator attend les connexions
   - VM2 : Les 3 players se connectent

2. **Attribution des rôles** :
   ```
   [NARRATOR] Attribution des rôles...
   [NARRATOR] player1 → Loup-Garou
   [NARRATOR] player2 → Voyante
   [NARRATOR] player3 → Villageois
   ```

3. **Tour 1 - Nuit** :
   ```
   [NUIT]  La nuit tombe...
   [NUIT]  Les loups attaquent player3
   [NUIT]  La Voyante espionne player1
   ```

4. **Tour 1 - Jour** :
   ```
   [JOUR]  Le jour se lève...
   [JOUR] player3 a été dévoré !
   [JOUR]  Vote du village...
   [JOUR] player1 vote contre player2
   [JOUR] player2 vote contre player1
   [JOUR] player1 est éliminé (rôle: Loup-Garou)
   ```

5. **Fin de partie** :
   ```
   [GAME OVER]  Les Villageois ont gagné !
   ```

### Logs observables

Chaque message TCP est loggé :
```
[SEND → player1] NIGHT_PHASE: {'alive_players': ['player1', 'player2']}
[RECV ← player1] ACTION: {'action': 'KILL', 'target': 'player2'}
```

---

## 🧠 Explications techniques

### 1. Communication TCP vs HTTP

| Aspect | TCP Sockets | HTTP/REST |
|--------|-------------|-----------|
| **Connexion** | Persistante | Stateless (nouvelle à chaque requête) |
| **Direction** | Bidirectionnelle | Client → Serveur uniquement |
| **Overhead** | Minimal | Headers, cookies, statuts |
| **Temps réel** | Natif | Nécessite polling/websockets |
| **Complexité** | Bas niveau | Haut niveau |

### 2. Choix de Python

- `socket` : Module natif, pas de dépendances
- `threading` : Gère plusieurs clients simultanément
- `json` : Format d'échange standard et lisible
- Simplicité pour la démonstration pédagogique

### 3. Architecture multithread

```python
# Le narrator crée un thread par joueur
threading.Thread(target=self.handle_player_connection, args=(conn, addr))
```

Chaque client a sa propre connexion TCP gérée en parallèle.

### 4. Ordinateur automatique

Les joueurs prennent des décisions seuls :
- **Loup-Garou** : Cible aléatoire
- **Voyante** : Espionne les inconnus
- **Villageois** : Vote aléatoire (ou contre loups connus si voyante)

### 5. Gestion d'état

Le narrator maintient :
- Liste des joueurs connectés
- Rôles attribués
- Statut vivant/mort
- Historique des votes

### 6. Robustesse

- Gestion des erreurs réseau (`try/except`)
- Logs détaillés pour le debug
- Délais pour éviter la saturation
- Fermeture propre des connexions

---

## 📊 Diagramme de séquence complet

```
Narrator          Player1(Loup)     Player2(Voyante)   Player3(Villageois)
   │                  │                   │                    │
   ├──WELCOME─────────→                   │                    │
   ├──────────WELCOME────────────────────→                    │
   ├──────────────────────WELCOME─────────────────────────────→
   │                  │                   │                    │
   ├─NIGHT_PHASE──────→                   │                    │
   ├─────────NIGHT_PHASE─────────────────→                    │
   ├────────────────────NIGHT_PHASE───────────────────────────→
   │                  │                   │                    │
   ├─REQUEST_ACTION───→                   │                    │
   │   (KILL)         │                   │                    │
   │←─────ACTION──────┤                   │                    │
   │  (target:player3)│                   │                    │
   │                  │                   │                    │
   ├────────────────REQUEST_ACTION────────→                    │
   │                (SPY)                 │                    │
   │←────────────────ACTION────────────────┤                   │
   │               (target:player1)       │                    │
   │                  │                   │                    │
   ├─DAY_PHASE────────→                   │                    │
   ├─────────DAY_PHASE───────────────────→                    │
   ├────────────────────DAY_PHASE─────────────────────────────→
   │                  │                   │                    │
   ├─REQUEST_ACTION───→                   │                    │
   │   (VOTE)         │                   │                    │
   │←─────ACTION──────┤                   │                    │
   │                  │                   │                    │
   ├────────────────REQUEST_ACTION────────→                    │
   │                (VOTE)                │                    │
   │←────────────────ACTION────────────────┤                   │
   │                  │                   │                    │
   ├─VOTE_RESULT──────→                   │                    │
   ├─────────VOTE_RESULT─────────────────→                    │
   │                  │                   │                    │
   │                 ...                 ...                  ...
   │                  │                   │                    │
   ├─GAME_OVER────────→                   │                    │
   ├─────────GAME_OVER───────────────────→                    │
   └──────────────────────────────────────┴────────────────────┘
```

---

## 🔒 Sécurité et limitations

### Limitations actuelles

- Pas d'authentification
- Pas de chiffrement (TLS)
- Pas de reconnexion automatique
- IDs joueurs non vérifiés

### Améliorations possibles

- Ajouter TLS avec certificats
- Implémenter un système de tokens
- Ajouter la reconnexion en cas de déconnexion
- Chiffrer les messages sensibles

---

## 📝 Utilisation pour la soutenance

### Points à expliquer

1. **Architecture distribuée** :
   - "Voici les 2 VMs Proxmox et la machine Windows"
   - "Le narrator est sur VM1, les players sur VM2"

2. **Communication TCP** :
   - "Les containers communiquent en TCP pur, pas de HTTP"
   - "Voici un message JSON transitant sur le socket"

3. **Protocole maison** :
   - "J'ai défini un protocole JSON avec des types de messages"
   - "Chaque action du jeu correspond à un échange réseau"

4. **Démonstration live** :
   - Lancer le narrator
   - Lancer les players
   - Montrer les logs en temps réel
   - Pointer les connexions TCP actives : `netstat -tan | grep 5000`

5. **Exploration du code** :
   - Montrer le code du serveur (acceptation de connexions)
   - Montrer le code client (envoi de messages)
   - Expliquer le format JSON

### Commandes utiles pour la démo

```bash
# Voir les connexions TCP actives
netstat -tan | grep 5000

# Voir les logs d'un container
docker logs -f garou-narrator

# Inspecter le réseau Docker
docker network inspect garou-network

# Tester la connectivité
ping <IP_VM1>
telnet <IP_VM1> 5000
```

---

## 🎯 Objectifs pédagogiques atteints

- Communication réseau bas niveau (sockets TCP)
- Protocole applicatif personnalisé (JSON)
- Architecture distribuée multi-VM
- Containerisation avec Docker
- Orchestration avec docker-compose
- Gestion de l'état distribué
- Programmation concurrente (threads)

---

## 📚 Ressources

- [Documentation Python socket](https://docs.python.org/3/library/socket.html)
- [Docker networking](https://docs.docker.com/network/)
- [Règles du Loup-Garou](https://fr.wikipedia.org/wiki/Les_Loups-garous_de_Thiercelieux)

---

## 👥 Auteur

Projet pédagogique - Systèmes & Réseaux

**Technologies** : Python 3.11 • Docker • TCP/IP • JSON

---

## 📄 Licence

Projet éducatif - Usage libre
