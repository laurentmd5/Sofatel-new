#!/bin/bash
################################################################################
# SCRIPT DIAGNOSTIC - Vérifier la configuration du serveur Ubuntu
# 
# Usage: bash check_server_requirements.sh
# 
# Ce script vérifie:
# ✓ Système d'exploitation
# ✓ Espace disque et RAM
# ✓ Docker et Docker Compose
# ✓ Utilisateur deployer
# ✓ Répertoires d'application
# ✓ SSH configuration
# ✓ Firewall
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((CHECKS_PASSED++))
}

log_fail() {
    echo -e "${RED}[✗]${NC} $1"
    ((CHECKS_FAILED++))
}

log_warn() {
    echo -e "${YELLOW}[⚠]${NC} $1"
    ((CHECKS_WARNING++))
}

# Header
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        DIAGNOSTIC SERVEUR SOFATELCOM                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# SECTION 1: System Information
log_info "=== SECTION 1: Système d'exploitation ==="
echo ""

# Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    log_pass "OS: $ID $VERSION_ID"
    
    if [[ "$ID" == "ubuntu" ]]; then
        VERSION_NUM=$(echo "$VERSION_ID" | cut -d. -f1)
        if [ "$VERSION_NUM" -ge 18 ]; then
            log_pass "Ubuntu version acceptable (>= 18.04)"
        else
            log_warn "Ubuntu version recommandée: >= 18.04"
        fi
    else
        log_warn "OS non Ubuntu détecté, compatibilité peut être limitée"
    fi
else
    log_fail "Impossible de déterminer l'OS"
fi

# Kernel
KERNEL=$(uname -r)
log_pass "Kernel: $KERNEL"

echo ""

# SECTION 2: Hardware
log_info "=== SECTION 2: Ressources matérielles ==="
echo ""

# RAM
RAM_TOTAL=$(free -h | awk '/^Mem:/{print $2}')
RAM_AVAILABLE=$(free -h | awk '/^Mem:/{print $7}')
log_pass "RAM totale: $RAM_TOTAL (disponible: $RAM_AVAILABLE)"

if [ $(free -m | awk '/^Mem:/{print $2}') -lt 2048 ]; then
    log_warn "RAM faible (< 2GB), déploiement peut être lent"
fi

# Disk
DISK_TOTAL=$(df -h / | awk 'NR==2{print $2}')
DISK_AVAILABLE=$(df -h / | awk 'NR==2{print $4}')
DISK_USAGE=$(df -h / | awk 'NR==2{print $5}')
log_pass "Disque: $DISK_TOTAL total, $DISK_AVAILABLE disponible (utilisation: $DISK_USAGE)"

DISK_AVAILABLE_MB=$(df -m / | awk 'NR==2{print $4}')
if [ "$DISK_AVAILABLE_MB" -lt 10240 ]; then
    log_warn "Espace disque faible (< 10GB)"
fi

# CPU
CPU_COUNT=$(nproc)
log_pass "Processeurs: $CPU_COUNT"

echo ""

# SECTION 3: Docker
log_info "=== SECTION 3: Docker et Docker Compose ==="
echo ""

# Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    log_pass "$DOCKER_VERSION"
    
    # Check if docker service is running
    if systemctl is-active --quiet docker; then
        log_pass "Service Docker: actif"
    else
        log_fail "Service Docker: inactif (lancer: sudo systemctl start docker)"
    fi
    
    # Check docker daemon
    if docker info &> /dev/null; then
        log_pass "Docker daemon: opérationnel"
    else
        log_fail "Docker daemon: non accessible (vérifier permissions)"
    fi
else
    log_fail "Docker: non installé (installer: curl -fsSL https://get.docker.com | sh)"
fi

# Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    log_pass "$COMPOSE_VERSION"
else
    log_fail "Docker Compose: non installé"
fi

echo ""

# SECTION 4: User and Permissions
log_info "=== SECTION 4: Utilisateurs et permissions ==="
echo ""

# Check deployer user
if id "deployer" &> /dev/null; then
    log_pass "Utilisateur deployer: existe"
    
    # Check docker group
    if groups deployer | grep &> /dev/null "\bdocker\b"; then
        log_pass "Utilisateur deployer: dans groupe docker"
    else
        log_warn "Utilisateur deployer: NOT dans groupe docker"
    fi
    
    # Check SSH key
    if [ -f /home/deployer/.ssh/authorized_keys ]; then
        KEY_COUNT=$(wc -l < /home/deployer/.ssh/authorized_keys)
        log_pass "authorized_keys: $KEY_COUNT clé(s) configurée(s)"
    else
        log_warn "authorized_keys: fichier manquant"
    fi
else
    log_fail "Utilisateur deployer: n'existe pas"
fi

# Current user permissions
if groups $USER | grep &> /dev/null "\bdocker\b"; then
    log_pass "Utilisateur courant ($USER): dans groupe docker"
else
    log_warn "Utilisateur courant: NOT dans groupe docker"
fi

echo ""

# SECTION 5: Directories
log_info "=== SECTION 5: Répertoires d'application ==="
echo ""

# Check directories
DIRS=("/opt/sofatelcom" "/opt/sofatelcom-backups" "/var/log/sofatelcom")

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        OWNER=$(ls -ld "$dir" | awk '{print $3":"$4}')
        PERMS=$(ls -ld "$dir" | awk '{print $1}')
        log_pass "$dir: existe (propriétaire: $OWNER, perms: $PERMS)"
    else
        log_fail "$dir: n'existe pas (créer: sudo mkdir -p $dir)"
    fi
done

echo ""

# SECTION 6: SSH Configuration
log_info "=== SECTION 6: Configuration SSH ==="
echo ""

# Check SSH service
if systemctl is-active --quiet ssh; then
    log_pass "Service SSH: actif"
else
    log_warn "Service SSH: inactif"
fi

# Check SSH port
SSH_PORT=$(sudo grep -i "^Port" /etc/ssh/sshd_config 2>/dev/null | awk '{print $2}' || echo "22")
log_pass "Port SSH: $SSH_PORT"

# Check key-based auth
if grep -q "^PubkeyAuthentication yes" /etc/ssh/sshd_config; then
    log_pass "Authentification par clé: activée"
else
    log_warn "Authentification par clé: vérifier configuration"
fi

# Check password auth
if grep -q "^PasswordAuthentication no" /etc/ssh/sshd_config; then
    log_pass "Authentification par mot de passe: désactivée ✓"
else
    log_warn "Authentification par mot de passe: vérifier configuration"
fi

echo ""

# SECTION 7: Firewall
log_info "=== SECTION 7: Firewall (UFW) ==="
echo ""

if command -v ufw &> /dev/null; then
    if sudo ufw status | grep -q "Status: active"; then
        log_pass "UFW: activé"
        
        # Check essential ports
        PORTS=(22 80 443 5000 3306 6379)
        for port in "${PORTS[@]}"; do
            if sudo ufw status | grep -q "$port"; then
                log_pass "Port $port: ouvert"
            else
                log_warn "Port $port: vérifié (peut ne pas être ouvert)"
            fi
        done
    else
        log_warn "UFW: désactivé (recommandé: sudo ufw enable)"
    fi
else
    log_warn "UFW: non installé"
fi

echo ""

# SECTION 8: Network
log_info "=== SECTION 8: Réseau ==="
echo ""

# IP Address
IP_ADDRESSES=$(hostname -I)
log_pass "Adresses IP: $IP_ADDRESSES"

# DNS
NAMESERVERS=$(cat /etc/resolv.conf | grep -i "nameserver" | head -2)
log_pass "DNS configuré"

# Internet connectivity
if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
    log_pass "Connectivité Internet: OK"
else
    log_warn "Connectivité Internet: vérifier"
fi

echo ""

# SECTION 9: Python (if needed)
log_info "=== SECTION 9: Python (optionnel) ==="
echo ""

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    log_pass "$PYTHON_VERSION"
else
    log_warn "Python3: non installé"
fi

echo ""

# SECTION 10: Git
log_info "=== SECTION 10: Git ==="
echo ""

if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    log_pass "$GIT_VERSION"
else
    log_warn "Git: non installé"
fi

echo ""

# Summary
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        RÉSUMÉ                           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "Vérifications réussies:  ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Avertissements:         ${YELLOW}$CHECKS_WARNING${NC}"
echo -e "Vérifications échouées:  ${RED}$CHECKS_FAILED${NC}"

echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    log_pass "Serveur configuré correctement! ✅"
    EXIT_CODE=0
else
    log_fail "Certains problèmes détectés, voir ci-dessus"
    EXIT_CODE=1
fi

echo ""
echo "Pour corriger les problèmes, lancer:"
echo "  sudo bash setup_ubuntu_server.sh"
echo ""

exit $EXIT_CODE
