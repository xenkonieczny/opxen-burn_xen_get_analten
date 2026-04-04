# Deploy opXEN Burner — Docker + GitHub

## Requirements

- VPS with Ubuntu 22.04+ (1 CPU, 512MB RAM minimum)
- Domain name pointed to VPS IP (e.g. `burn.analtena.com`)
- GitHub account
- SSH access to VPS

---

## Part 1 — GitHub Repository

### 1.1 Initialize git locally

```bash
cd "/Users/pawelkonieczny/Documents/XEN /ATENA/NewAtenaApp-PERPLEXITY+CLAUDE"
git init
git add .
git commit -m "Initial commit: opXEN Burner app"
```

### 1.2 Create GitHub repo and push

```bash
# Create repo on GitHub (public or private)
gh repo create opxen-burner --private --source=. --push

# Or manually:
# 1. Create repo on github.com
# 2. Then:
git remote add origin git@github.com:YOUR_USERNAME/opxen-burner.git
git branch -M main
git push -u origin main
```

---

## Part 2 — VPS Setup

### 2.1 Install Docker on VPS

```bash
ssh user@YOUR_VPS_IP

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose plugin
sudo apt install -y docker-compose-plugin

# Add your user to docker group (logout/login after)
sudo usermod -aG docker $USER
```

### 2.2 Install Nginx + Certbot

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### 2.3 Clone repo on VPS

```bash
cd ~
git clone git@github.com:YOUR_USERNAME/opxen-burner.git
cd opxen-burner
```

> If private repo — add VPS SSH key to GitHub: `ssh-keygen -t ed25519` then add `~/.ssh/id_ed25519.pub` to GitHub Settings > SSH Keys.

---

## Part 3 — Run with Docker

### 3.1 Build and start

```bash
cd ~/opxen-burner

# Create data directory for persistent storage
mkdir -p data

# Build and run
docker compose up -d --build
```

### 3.2 Verify

```bash
# Check container is running
docker compose ps

# Check logs
docker compose logs -f

# Test endpoint
curl http://localhost:8001/api/stats
```

---

## Part 4 — Nginx + HTTPS

### 4.1 Nginx config

```bash
sudo nano /etc/nginx/sites-available/burner
```

Paste (replace `YOUR_DOMAIN`):

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/burner /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 4.2 SSL certificate

**Required** — wallets (MetaMask, Rabby, Backpack) require HTTPS.

```bash
sudo certbot --nginx -d YOUR_DOMAIN
```

### 4.3 Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Part 5 — Updating (deploy workflow)

### Push changes from local

```bash
# Local machine:
cd "/Users/pawelkonieczny/Documents/XEN /ATENA/NewAtenaApp-PERPLEXITY+CLAUDE"
git add .
git commit -m "description of changes"
git push
```

### Pull and rebuild on VPS

```bash
# VPS:
cd ~/opxen-burner
git pull
docker compose up -d --build
```

### One-liner deploy from local

```bash
ssh user@YOUR_VPS_IP "cd ~/opxen-burner && git pull && docker compose up -d --build"
```

---

## Common Operations

### View logs
```bash
docker compose logs -f
```

### Restart
```bash
docker compose restart
```

### Stop
```bash
docker compose down
```

### Backup database
```bash
cp ~/opxen-burner/data/burns.db ~/burns_backup_$(date +%Y%m%d).db
```

### Reset database (clean start)
```bash
docker compose down
rm ~/opxen-burner/data/burns.db ~/opxen-burner/data/burns_export.csv
docker compose up -d
```

### Export CSV
```bash
# Browser
https://YOUR_DOMAIN/api/export/csv

# Terminal
curl https://YOUR_DOMAIN/api/export/csv > burns.csv
```

### Enter container shell
```bash
docker compose exec burner sh
```

---

## Project Structure

```
opxen-burner/
├── app.py                # Flask backend
├── templates/
│   └── index.html        # Frontend
├── contracts/            # Solidity contracts (reference)
│   ├── XENBurner.sol
│   ├── IBurnRedeemable.sol
│   └── IBurnableToken.sol
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose config
├── requirements.txt      # Python dependencies
├── .gitignore            # Git ignore rules
├── data/                 # Persistent data (not in git)
│   ├── burns.db          # SQLite database
│   └── burns_export.csv  # CSV export
└── INSTRUKCJA_VPS.md     # This file
```

---

## Important Notes

- **HTTPS is mandatory** — EVM/SVM wallets require secure context
- **data/ directory** is mounted as Docker volume — database and CSV persist across container rebuilds
- **SQLite** works fine for this scale. For high traffic consider PostgreSQL
- **`.gitignore`** excludes `*.db`, `*.csv`, `data/`, `.DS_Store`, old files
- Container auto-restarts on crash (`restart: always` in docker-compose.yml)
- Gunicorn runs with 2 workers — increase if needed in docker-compose.yml
