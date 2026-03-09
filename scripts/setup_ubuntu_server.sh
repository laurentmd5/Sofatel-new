#!/bin/bash
################################################################################
# SCRIPT D'INSTALLATION AUTOMATISÉE - SOFATELCOM STAGING SERVER
# 
# Usage: bash setup_ubuntu_server.sh
# 
# Ce script:
# ✓ Met à jour le système
# ✓ Installe Docker et Docker Compose
# ✓ Crée l'utilisateur deployer
# ✓ Configure SSH
# ✓ Prépare les répertoires
# ✓ Configure le firewall
# ✓ Teste la configuration
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    log_error "Ce script doit être exécuté avec sudo!"
    exit 1
fi

# Start
log_info "=========================================="
log_info "SOFATELCOM - Configuration Serveur Ubuntu"
log_info "=========================================="
echo ""

# STEP 1: Update system
log_info "Étape 1: Mise à jour du système..."
apt-get update
apt-get upgrade -y
apt-get install -y curl wget git openssh-server openssh-client net-tools
log_success "Système à jour"
echo ""

# STEP 2: Install Docker
log_info "Étape 2: Installation de Docker..."
if command -v docker &> /dev/null; then
    log_warning "Docker déjà installé: $(docker --version)"
else
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sh /tmp/get-docker.sh
    log_success "Docker installé: $(docker --version)"
fi
echo ""

# STEP 3: Install Docker Compose
log_info "Étape 3: Installation de Docker Compose..."
if command -v docker-compose &> /dev/null; then
    log_warning "Docker Compose déjà installé: $(docker-compose --version)"
else
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
    COMPOSE_URL="https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)"
    curl -L "$COMPOSE_URL" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log_success "Docker Compose installé: $(docker-compose --version)"
fi
echo ""

# STEP 4: Create deployer user
log_info "Étape 4: Création de l'utilisateur deployer..."
if id -u "deployer" &> /dev/null; then
    log_warning "L'utilisateur deployer existe déjà"
else
    adduser --disabled-password --gecos "" deployer
    # Set a random password for security
    DEPLOY_PASS=$(openssl rand -base64 12)
    echo "deployer:$DEPLOY_PASS" | chpasswd
    log_success "Utilisateur deployer créé (mot de passe généré)"
    log_warning "Mot de passe: $DEPLOY_PASS (à sauvegarder)"
fi

# Add deployer to docker group
usermod -aG docker deployer
log_success "Utilisateur deployer ajouté au groupe docker"
echo ""

# STEP 5: Configure SSH
log_info "Étape 5: Configuration SSH..."
mkdir -p /home/deployer/.ssh
chmod 700 /home/deployer/.ssh
touch /home/deployer/.ssh/authorized_keys
chmod 600 /home/deployer/.ssh/authorized_keys
chown -R deployer:deployer /home/deployer/.ssh
log_success "SSH configuré"
echo ""

# STEP 6: Create application directories
log_info "Étape 6: Création des répertoires d'application..."
mkdir -p /opt/sofatelcom
mkdir -p /opt/sofatelcom-backups
mkdir -p /var/log/sofatelcom

chown -R deployer:deployer /opt/sofatelcom
chown -R deployer:deployer /opt/sofatelcom-backups
chown -R deployer:deployer /var/log/sofatelcom

chmod 755 /opt/sofatelcom
chmod 755 /opt/sofatelcom-backups
chmod 755 /var/log/sofatelcom

log_success "Répertoires créés"
echo ""

# STEP 7: Configure logrotate
log_info "Étape 7: Configuration de la rotation des logs..."
cat > /etc/logrotate.d/sofatelcom << 'EOF'
/var/log/sofatelcom/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deployer deployer
    sharedscripts
}
EOF
log_success "Logrotate configuré"
echo ""

# STEP 8: Configure UFW Firewall
log_info "Étape 8: Configuration du Firewall..."
apt-get install -y ufw

# Permet les ports essentiels
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp
ufw allow 3306/tcp
ufw allow 6379/tcp

# Enable UFW
ufw --force enable
log_success "Firewall configuré"
echo ""

# STEP 9: Configure SSH hardening
log_info "Étape 9: Renforcement SSH..."
SSH_CONFIG="/etc/ssh/sshd_config"

# Backup original
cp "$SSH_CONFIG" "$SSH_CONFIG.bak"

# Disable root login
sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' "$SSH_CONFIG"
sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' "$SSH_CONFIG"

# Disable password auth (key-only)
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication no/' "$SSH_CONFIG"
sed -i 's/^PasswordAuthentication.*/PasswordAuthentication no/' "$SSH_CONFIG"

# Enable pubkey auth
sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' "$SSH_CONFIG"
sed -i 's/^PubkeyAuthentication.*/PubkeyAuthentication yes/' "$SSH_CONFIG"

# Restart SSH
systemctl restart ssh
log_success "SSH renforcé"
echo ""

# STEP 10: Create initialization script
log_info "Étape 10: Création du script d'initialisation..."
cat > /opt/sofatelcom/init.sh << 'EOF'
#!/bin/bash
# Script d'initialisation pour les déploiements

echo "Initialisation SOFATELCOM Deployment..."

# Attendre que MySQL soit prêt
echo "Attente de MySQL..."
for i in {1..30}; do
    if docker-compose exec -T db mysqladmin ping -h localhost &>/dev/null; then
        echo "MySQL prêt!"
        break
    fi
    sleep 1
done

# Attendre que Redis soit prêt
echo "Attente de Redis..."
for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping &>/dev/null; then
        echo "Redis prêt!"
        break
    fi
    sleep 1
done

echo "Initialisation complétée!"
EOF

chmod +x /opt/sofatelcom/init.sh
chown deployer:deployer /opt/sofatelcom/init.sh
log_success "Script d'initialisation créé"
echo ""

# STEP 11: Diagnostic
log_info "Étape 11: Diagnostic final..."
echo ""
log_info "Informations du serveur:"
echo "  - Hostname: $(hostname)"
echo "  - IP: $(hostname -I)"
echo "  - OS: $(lsb_release -d | cut -f2)"
echo "  - Docker: $(docker --version)"
echo "  - Docker Compose: $(docker-compose --version)"
echo "  - Utilisateur deployer: $(id deployer)"
echo ""

# Final summary
echo ""
log_success "=========================================="
log_success "Installation complétée avec succès! ✅"
log_success "=========================================="
echo ""
log_info "Prochaines étapes:"
echo "  1. Récupérer votre clé SSH publique depuis Windows:"
echo "     cat ~/.ssh/github_deploy.pub"
echo ""
echo "  2. Ajouter la clé à authorized_keys:"
echo "     cat >> /home/deployer/.ssh/authorized_keys << 'PUBKEY'"
echo "     [votre clé publique]"
echo "     PUBKEY"
echo ""
echo "  3. Configurer les secrets GitHub:"
echo "     - STAGING_SERVER_IP: $(hostname -I | awk '{print $1}')"
echo "     - STAGING_USER: deployer"
echo "     - STAGING_SSH_PRIVATE_KEY: [clé privée]"
echo ""
echo "  4. Créer la branche dev et faire un push test:"
echo "     git checkout -b dev"
echo "     git push -u origin dev"
echo ""
log_warning "⚠️  Sauvegarder le mot de passe deployer généré!"
echo ""
