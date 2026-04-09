# Prompt dla Claude Code — auto-deploy na VPS

## Jak użyć

Na VPS wpisz `claude` i wklej poniższy prompt:

---

## PROMPT (skopiuj całość i wklej do claude na VPS)

```
Zainstaluj i uruchom aplikację opXEN Burner na tym serwerze Ubuntu.

Wykonaj kolejno:

1. Sprawdź czy Docker jest zainstalowany (`docker --version`). Jeśli nie — zainstaluj:
   curl -fsSL https://get.docker.com | sh
   sudo apt install -y docker-compose-plugin
   sudo usermod -aG docker ubuntu

2. Sprawdź czy git jest zainstalowany. Jeśli nie: sudo apt install -y git

3. Utwórz użytkownika ATENA jeśli nie istnieje:
   mkdir -p /home/ubuntu/ATENA

4. Sklonuj repozytorium do katalogu /home/ubuntu/ATENA/opxen:
   git clone https://github.com/xenkonieczny/opxen-burn_xen_get_analten.git /home/ubuntu/ATENA/opxen

5. Utwórz katalog data:
   mkdir -p /home/ubuntu/ATENA/opxen/data

6. Uruchom aplikację:
   cd /home/ubuntu/ATENA/opxen && docker compose up -d --build

7. Sprawdź czy działa:
   docker compose ps
   curl http://localhost:8001/api/stats

8. Zainstaluj Nginx jeśli nie ma: sudo apt install -y nginx

9. Utwórz plik /etc/nginx/sites-available/opxen z konfiguracją proxy na port 8001:
   server {
       listen 80;
       server_name _;
       location / {
           proxy_pass http://127.0.0.1:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }

10. Włącz konfigurację Nginx:
   ln -sf /etc/nginx/sites-available/opxen /etc/nginx/sites-enabled/opxen
   rm -f /etc/nginx/sites-enabled/default
   nginx -t && systemctl reload nginx

11. Skonfiguruj firewall:
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable

12. Na końcu wyświetl:
    - status kontenera (docker compose ps)
    - wynik curl http://localhost:8001/api/stats
    - status nginx (systemctl status nginx --no-pager)
    - IP serwera (curl -s ifconfig.me)

Raportuj każdy krok — co zrobiłeś i jaki był wynik.
```
