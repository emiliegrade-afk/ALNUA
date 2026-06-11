#!/bin/bash
# setup_vps.sh — Installation initiale sur VPS Ubuntu 22.04 Hopela
# Lancer en tant que root : bash setup_vps.sh

set -e  # Arrêter si erreur

echo "🚀 Installation ALNUA Hub sur VPS..."

# Mise à jour système
apt-get update && apt-get upgrade -y

# Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER

# Docker Compose v2
apt-get install -y docker-compose-plugin

# Git + essentiels
apt-get install -y git curl wget htop nano ufw

# Firewall
ufw allow ssh
ufw allow 80
ufw allow 443
ufw --force enable

# Créer utilisateur alnua
useradd -m -s /bin/bash alnua
usermod -aG docker alnua

# Clé SSH pour GitHub (à configurer après)
mkdir -p /home/alnua/.ssh
chmod 700 /home/alnua/.ssh
# ssh-keygen -t ed25519 -C "alnua-vps" -f /home/alnua/.ssh/id_ed25519 -N ""
# cat /home/alnua/.ssh/id_ed25519.pub  # Ajouter cette clé dans GitHub Settings > SSH Keys

# Répertoire projet
mkdir -p /home/alnua/hub
chown -R alnua:alnua /home/alnua/hub

echo "✅ VPS prêt. Prochaines étapes :"
echo "1. Copier le code : git clone ton-repo /home/alnua/hub"
echo "2. Créer .env.prod depuis le template"
echo "3. cd /home/alnua/hub && docker compose up -d"
echo "4. (Optionnel) Configurer SSL : certbot --nginx -d ton-domaine.fr"
