# CLAUDE.md — opXEN Burner / ANALTEN

## Projekt

**Nazwa:** opXEN Burner x ANALTEN  
**GitHub:** https://github.com/xenkonieczny/opxen-burn_xen_get_analten  
**VPS:** 141.95.19.237 (Ubuntu)  
**Stack:** Python / Flask / SQLite / Docker / Nginx  

Aplikacja webowa umożliwiająca:
1. Spalenie tokenów **opXEN** na sieci **Optimism** przez kontrakt XENBurner
2. Powiązanie portfela **EVM** (MetaMask) z portfelem **SVM** (Backpack / X1 Wallet) za opłatą 0.1 XNT
3. Rejestrację alokacji tokenów **ANALTEN** (airdrop na X1/Solana) proporcjonalnie do spalonych opXEN

---

## Architektura

```
templates/index.html    — single-page frontend (HTML/CSS/JS, ~32KB)
app.py                  — Flask backend (8 endpointów API)
burns.db                — SQLite (NIE w git, montowana jako Docker volume)
Dockerfile              — python:3.12-slim, gunicorn, port 8001
docker-compose.yml      — kontener z volume ./data:/app/data
```

### API Endpoints

| Endpoint | Metoda | Opis |
|---|---|---|
| `/` | GET | Frontend |
| `/api/burn` | POST | Rejestracja spalenia (evm_address, burn_tx, burn_amount) |
| `/api/link` | POST | Powiązanie portfeli EVM↔SVM (evm_address, svm_address, xnt_tx) |
| `/api/status/<evm>` | GET | Status portfela i spalenia w bieżącej epoce |
| `/api/leaderboard` | GET | Top 25 spalaczy epoki |
| `/api/stats` | GET | Globalne statystyki i epoki |
| `/api/db/burns` | GET | Surowe dane burns (debug) |
| `/api/db/links` | GET | Surowe dane wallet_links (debug) |
| `/api/export/csv` | GET | Eksport CSV do airdropa |

### Baza danych (SQLite)

```sql
burns(id, evm_address, burn_tx, burn_amount, epoch_date, created_at)
wallet_links(id, evm_address UNIQUE, svm_address, xnt_tx, created_at)
```

**Epoka** = 1 dzień UTC (format `YYYY-MM-DD`). Alokacja ANALTEN liczona per epoka.

---

## Smart Kontrakty

| Kontrakt | Adres | Sieć |
|---|---|---|
| XENBurner (v2, wrapper) | `0xdDd1A839b790Aa4A12C665417Ff37F2Ab39F4FE2` | Optimism |
| XENBurner (v1, deprecated) | `0x83E96ff0944BD10aF19A054902225357DccE6d91` | Optimism |

Pliki: [contracts/XENBurner.sol](contracts/XENBurner.sol), [contracts/IBurnRedeemable.sol](contracts/IBurnRedeemable.sol), [contracts/IBurnableToken.sol](contracts/IBurnableToken.sol)

---

## Deploy na VPS

### Pierwsze uruchomienie

```bash
ssh root@141.95.19.237

# Instalacja Docker (jeśli brak)
curl -fsSL https://get.docker.com | sh
sudo apt install -y docker-compose-plugin
sudo usermod -aG docker $USER

# Klonowanie i start
git clone https://github.com/xenkonieczny/opxen-burn_xen_get_analten.git
cd opxen-burn_xen_get_analten
mkdir -p data
docker compose up -d --build

# Weryfikacja
curl http://localhost:8001/api/stats
```

### Update (po każdym push)

```bash
ssh root@141.95.19.237 "cd ~/opxen-burn_xen_get_analten && git pull && docker compose up -d --build"
```

### Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name TWOJA_DOMENA;
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo certbot --nginx -d TWOJA_DOMENA
sudo ufw allow 22,80,443/tcp && sudo ufw enable
```

> **HTTPS jest wymagane** — MetaMask i Backpack nie działają bez SSL.

---

## Znane TODOs / Niedokończone

- `XNT_FEE_REQUIRED = 0.1` — opłata nie jest weryfikowana on-chain (mock)
- Brak weryfikacji transakcji spalenia na blockchainie (trusted client)
- Brak rate-limitingu na API
- Brak autentykacji na `/api/db/*` (debug endpoints publiczne)
- `XNT_MINT` i `treasury` adresy są hardcoded placeholderami

---

## Środowisko lokalne

```
Projekt: /Users/pawelkonieczny/Documents/XEN /ATENA/prodNewAtenaApp-PERPLEXITY+CLAUDE
GitHub CLI: zalogowany jako xenkonieczny
```

### Uruchomienie lokalne

```bash
pip install flask gunicorn
python app.py
# lub
docker compose up --build
```

---

## Struktura plików (produkcja)

```
.
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── KONTRAKTY               # adres kontraktu XENBurner
├── INSTRUKCJA_VPS.md
├── CLAUDE.md               # ten plik
├── templates/
│   └── index.html
├── contracts/
│   ├── XENBurner.sol
│   ├── IBurnRedeemable.sol
│   └── IBurnableToken.sol
└── data/                   # NIE w git — Docker volume
    ├── burns.db
    └── burns_export.csv
```

Stare wersje i notatki są w `archiwum/` (lokalnie, poza git).
