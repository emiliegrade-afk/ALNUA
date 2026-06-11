# Dockerfile — Hub ALNUA
# Base : Python 3.11 slim (léger, compatible Arm64 pour Hetzner CAX/Hopela Ryzen)
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="ALNUA"
LABEL version="1.0"

# Variables build
ARG DEBIAN_FRONTEND=noninteractive

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    gnupg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installer gh CLI (GitHub)
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
    gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
    tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && apt-get install -y gh && \
    rm -rf /var/lib/apt/lists/*

# Installer Claude Code CLI
RUN curl -fsSL https://claude.ai/install.sh | sh || \
    npm install -g @anthropic-ai/claude-code 2>/dev/null || true

# Répertoire de travail
WORKDIR /app

# Copier requirements en premier (cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer Playwright browsers (pour QA)
RUN python -m playwright install chromium --with-deps 2>/dev/null || true

# Copier le code
COPY . .

# Créer le répertoire worktrees (pour skill_coding_agent)
RUN mkdir -p worktrees

# Utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 alnua && chown -R alnua:alnua /app
USER alnua

# Exposer le port API
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Commande par défaut : API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
