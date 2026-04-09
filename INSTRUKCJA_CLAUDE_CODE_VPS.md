# Instalacja Claude Code na VPS (Ubuntu)

## Wymagania

- Ubuntu 20.04+
- Node.js 18+
- Klucz API Anthropic

---

## 1. Instalacja Node.js (jeśli brak)

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node --version   # powinno być 18+
```

---

## 2. Instalacja Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Weryfikacja:

```bash
claude --version
```

---

## 3. Logowanie (klucz API)

```bash
claude
```

Przy pierwszym uruchomieniu zostaniesz poproszony o klucz API.  
Klucz pobierz z: https://console.anthropic.com/settings/api-keys

Lub ustaw zmienną środowiskową (trwalsze):

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
source ~/.bashrc
```

---

## 4. Użycie w projekcie

```bash
cd ~/opxen-burn_xen_get_analten
claude
```

Claude Code automatycznie wczyta `CLAUDE.md` jako kontekst projektu.

### Przydatne komendy

```bash
claude                        # tryb interaktywny
claude "opisz co robi app.py" # jednorazowe pytanie
claude --help                 # lista opcji
```

---

## 5. Aktualizacja Claude Code

```bash
npm update -g @anthropic-ai/claude-code
```

---

## Uwagi

- Claude Code na VPS działa bez GUI — tylko terminal
- `CLAUDE.md` w katalogu projektu zawiera pełny kontekst aplikacji
- Nie commituj klucza API do gita — używaj zmiennych środowiskowych
