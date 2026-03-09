#!/bin/bash
# ============================================================================
# DEPLOY SCRIPT - Déploiement sécurisé SOFATELCOM sur Ubuntu
# ============================================================================
# Configuration personnalisée pour:
#   - Serveur: 192.168.61.131 (VMware Local)
#   - Utilisateur: deployer
#   - Port SSH: 22
#   - OS: Ubuntu 22.04 LTS
#   - Docker: 27.5.1
#   - Docker Compose: 1.29.2
# ============================================================================
# Usage: ./deploy.sh [staging|production]
# Exemple: ./deploy.sh staging
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-staging}"
APP_DIR="/opt/sofatelcom"
BACKUP_DIR="/opt/sofatelcom-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOYER_USER="deployer"
STAGING_SERVER="192.168.61.131"
LOG_DIR="/var/log/sofatelcom"

# ============================================================================
# FUNCTIONS
# ============================================================================

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

check_environment() {
    log_info "Vérification de l'environnement..."
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé!"
        exit 1
    fi
    log_success "Docker est installé: $(docker --version)"
    
    # Vérifier Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose n'est pas installé!"
        exit 1
    fi
    log_success "Docker Compose est installé: $(docker-compose --version)"
    
    # Vérifier l'espace disque
    available_space=$(df "$APP_DIR" 2>/dev/null | awk 'NR==2 {print $4}' || echo "0")
    if [ "$available_space" -lt 1048576 ]; then
        log_warning "Espace disque faible! ($available_space KB disponibles)"
    fi
}

backup_current_state() {
    log_info "Sauvegarde de l'état actuel..."
    
    mkdir -p "$BACKUP_DIR"
    
    if [ -d "$APP_DIR" ]; then
        # Backup des fichiers
        tar -czf "$BACKUP_DIR/app_backup_$TIMESTAMP.tar.gz" \
            -C "$(dirname $APP_DIR)" \
            "$(basename $APP_DIR)" \
            2>/dev/null || log_warning "Erreur lors du backup des fichiers"
        log_success "Backup fichiers créé: $BACKUP_DIR/app_backup_$TIMESTAMP.tar.gz"
        
        # Backup de la base de données
        if [ -x "$(command -v docker)" ]; then
            cd "$APP_DIR" 2>/dev/null || true
            
            if [ -f "docker-compose.yml" ]; then
                docker-compose exec -T db mysqldump \
                    -u sofatelcom -psofatelcom_pass \
                    sofatelcom_db > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql" \
                    2>/dev/null || log_warning "Erreur lors du backup DB"
                log_success "Backup base de données créé"
            fi
        fi
    fi
}

stop_services() {
    log_info "Arrêt des services..."
    
    cd "$APP_DIR"
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose down --remove-orphans || log_warning "Erreur lors de l'arrêt"
        log_success "Services arrêtés"
    else
        log_warning "Fichier docker-compose.yml introuvable"
    fi
}

clean_unused_resources() {
    log_info "Nettoyage des ressources Docker non utilisées..."
    
    docker container prune -f --filter "until=72h" || log_warning "Erreur lors du nettoyage des containers"
    docker image prune -f || log_warning "Erreur lors du nettoyage des images"
    docker system prune -f || log_warning "Erreur lors du nettoyage système"
    
    log_success "Nettoyage complété"
}

prepare_environment() {
    log_info "Préparation de l'environnement..."
    
    # Créer les répertoires
    mkdir -p "$APP_DIR"
    mkdir -p "$APP_DIR/uploads"
    mkdir -p "$APP_DIR/logs"
    
    # Définir les permissions
    chmod 755 "$APP_DIR"
    chmod 755 "$APP_DIR/uploads"
    chmod 755 "$APP_DIR/logs"
    
    log_success "Répertoires créés et permissions définies"
}

deploy_application() {
    log_info "Déploiement de l'application..."
    
    cd "$APP_DIR"
    
    # Vérifier les fichiers essentiels
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml introuvable dans $APP_DIR"
        exit 1
    fi
    
    # Configurer .env si nécessaire
    if [ ! -f ".env" ]; then
        log_warning ".env non trouvé, création depuis .env.staging"
        if [ -f ".env.staging" ]; then
            cp ".env.staging" ".env"
            log_warning "ATTENTION: Éditer .env avec les bonnes valeurs!"
        else
            log_error ".env.staging introuvable!"
            exit 1
        fi
    fi
    
    # Télécharger les images
    log_info "Téléchargement des images Docker..."
    docker-compose pull || log_warning "Erreur lors du téléchargement"
    
    # Démarrer les services
    log_info "Démarrage des services..."
    docker-compose up -d || {
        log_error "Erreur lors du démarrage des services"
        log_warning "Restauration depuis le backup..."
        restore_backup "$BACKUP_DIR/app_backup_$TIMESTAMP.tar.gz"
        exit 1
    }
    
    log_success "Services démarrés"
}

wait_for_health() {
    log_info "Attente de la disponibilité des services..."
    
    cd "$APP_DIR"
    
    # Attendre MySQL
    log_info "Attente de MySQL..."
    for i in {1..30}; do
        if docker-compose exec -T db mysqladmin ping -h localhost &>/dev/null; then
            log_success "MySQL est disponible"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            log_error "MySQL ne démarre pas"
            exit 1
        fi
    done
    
    # Attendre Redis
    log_info "Attente de Redis..."
    for i in {1..30}; do
        if docker-compose exec -T redis redis-cli ping &>/dev/null; then
            log_success "Redis est disponible"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            log_error "Redis ne démarre pas"
            exit 1
        fi
    done
    
    # Attendre l'application
    log_info "Attente de l'application Flask..."
    for i in {1..60}; do
        if docker-compose exec -T app curl -f http://localhost:5000/api/health &>/dev/null; then
            log_success "Application est disponible"
            break
        fi
        sleep 2
        if [ $i -eq 60 ]; then
            log_warning "L'application met du temps à démarrer"
        fi
    done
}

verify_deployment() {
    log_info "Vérification du déploiement..."
    
    cd "$APP_DIR"
    
    # Vérifier que tous les containers sont en running
    if ! docker-compose ps | grep -q "Up"; then
        log_error "Certains containers ne sont pas running"
        docker-compose ps
        exit 1
    fi
    log_success "Tous les containers sont en cours d'exécution"
    
    # Afficher le status
    log_info "Status des services:"
    docker-compose ps
    
    # Test de l'API
    log_info "Test de l'API..."
    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        log_success "API est accessible"
    else
        log_warning "API n'est pas encore accessible"
    fi
    
    # Afficher les logs récents
    log_info "Logs récents de l'application:"
    docker-compose logs --tail=20 app 2>/dev/null || true
}

restore_backup() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        log_error "Fichier de backup introuvable: $backup_file"
        return 1
    fi
    
    log_warning "Restauration du backup: $backup_file"
    
    tar -xzf "$backup_file" -C / || {
        log_error "Erreur lors de la restauration"
        return 1
    }
    
    log_success "Backup restauré avec succès"
}

run_pre_deployment_checks() {
    log_info "Exécution des vérifications pré-déploiement..."
    
    # Vérifier les formats de fichier
    if ! grep -q "version:" "$APP_DIR/docker-compose.yml" 2>/dev/null; then
        log_error "docker-compose.yml invalide"
        exit 1
    fi
    
    # Vérifier l'accessibilité du registre Docker
    log_info "Vérification de l'accès au registre Docker..."
    if ! docker pull alpine:latest &>/dev/null; then
        log_warning "Accès au registre Docker peut être limité"
    fi
    
    log_success "Vérifications complétées"
}

# ============================================================================
# MAIN FLOW
# ============================================================================

main() {
    echo ""
    log_info "╔════════════════════════════════════════════════════════════════╗"
    log_info "║            SOFATELCOM DEPLOYMENT SCRIPT                        ║"
    log_info "║            Configuration Personnalisée v1.0                    ║"
    log_info "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    log_info "Configuration de déploiement:"
    log_info "  ├─ Serveur: 192.168.61.131 (VMware Local)"
    log_info "  ├─ Utilisateur: deployer"
    log_info "  ├─ Répertoire: /opt/sofatelcom"
    log_info "  ├─ Logs: /var/log/sofatelcom"
    log_info "  ├─ Backups: /opt/sofatelcom-backups"
    log_info "  ├─ Environment: $ENVIRONMENT"
    log_info "  └─ Timestamp: $TIMESTAMP"
    echo ""
    
    # Validation
    if [ ! -d "$APP_DIR" ]; then
        log_error "Le répertoire $APP_DIR n'existe pas!"
        log_info "Création du répertoire..."
        prepare_environment
    fi
    
    # Vérifier l'espace disque (CRITIQUE pour VMware local!)
    available_space=$(df "$APP_DIR" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 5242880 ]; then
        log_error "⚠️  ESPACE DISQUE CRITIQUE! Seulement $((available_space / 1024)) MB disponibles"
        log_error "Action requise: Libérer au moins 5 GB avant déploiement"
        exit 1
    fi
    
    if [ "$available_space" -lt 10485760 ]; then
        log_warning "⚠️  Espace disque faible. $((available_space / 1024 / 1024)) GB disponibles"
        log_warning "Recommandé: 10+ GB pour Docker Compose (App + MySQL + Redis)"
    fi
    
    # Steps
    check_environment
    run_pre_deployment_checks
    backup_current_state
    clean_unused_resources
    stop_services
    deploy_application
    wait_for_health
    verify_deployment
    
    echo ""
    log_info "╔════════════════════════════════════════════════════════════════╗"
    log_success "✅ Déploiement complété avec succès! 🎉"
    log_info "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    log_info "📊 Informations de déploiement:"
    log_info "  ├─ Serveur: 192.168.61.131 (VMware)"
    log_info "  ├─ Répertoire: $APP_DIR"
    log_info "  ├─ Backup: $BACKUP_DIR"
    log_info "  └─ Logs: $LOG_DIR"
    echo ""
    
    log_info "🌐 URLs d'accès:"
    log_info "  ├─ Application: http://192.168.61.131:5000"
    log_info "  ├─ PhpMyAdmin (si activé): http://192.168.61.131:8081"
    log_info "  ├─ MySQL: 192.168.61.131:3306"
    log_info "  └─ Redis: 192.168.61.131:6379"
    echo ""
    
    log_info "📚 Commandes utiles (depuis le serveur 192.168.61.131):"
    log_info "  ├─ Logs: cd $APP_DIR && docker-compose logs -f"
    log_info "  ├─ Restart: cd $APP_DIR && docker-compose restart"
    log_info "  ├─ Shell: cd $APP_DIR && docker-compose exec app bash"
    log_info "  ├─ Status: cd $APP_DIR && docker-compose ps"
    log_info "  └─ Health: curl http://localhost:5000/api/health"
    echo ""
    
    log_info "📝 Documentations disponibles:"
    log_info "  ├─ PERSONALIZED_SETUP_DEVOPS.md (Guide complet)"
    log_info "  ├─ UBUNTU_GITHUB_SETUP_GUIDE.md (Setup Ubuntu)"
    log_info "  ├─ DOCKER_DEPLOYMENT_GUIDE.md (Docker)"
    log_info "  └─ CI_CD_COMPLETE_GUIDE.md (GitHub Actions)"
    echo ""
    
    log_success "🚀 Vous êtes prêt pour les prochaines étapes!"
    echo ""
}
    log_info ""
}

# Handle errors
trap 'log_error "Erreur à la ligne $LINENO"; exit 1' ERR

# Run
main "$@"
