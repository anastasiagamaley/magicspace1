# ✨ MagicSpace – Inštalácia a spustenie

## Súbory projektu

```
magicspace/
├── app.py           ← Python server (HLAVNÝ SÚBOR)
├── api.js           ← Spoločné API volania pre všetky stránky
├── index.html       ← Hlavná stránka
├── dula.html        ← Dula, joga pre tehotné, rebozo, kurz
├── soundhealing.html
├── joga-park.html   ← Samostatný projekt Joga v parku
├── firmy.html       ← Firemná joga + Sound pre firmy
├── admin.html       ← Adminpanel (heslo: admin123)
└── magicspace.db    ← Databáza (vytvorí sa automaticky)
```

---

## 🖥 Spustenie lokálne (na počítači)

### 1. Nainštalujte Python (ak ešte nemáte)
Stiahnite z https://python.org → verzia 3.10 alebo vyššia

### 2. Nainštalujte Flask
Otvorte terminál (cmd / PowerShell / Terminal) a napíšte:
```bash
pip install flask
```

### 3. Spustite server
```bash
cd magicspace
python app.py
```

### 4. Otvorte v prehliadači
```
http://localhost:5000          ← web
http://localhost:5000/admin.html  ← adminpanel
```

---

## ☁️ Nasadenie na cloud (PythonAnywhere) – ODPORÚČANÉ

**PythonAnywhere** je bezplatný hosting pre Python aplikácie.
Váš doménu magicspace.sk tam jednoducho nasmerujete.

### Krok 1 – Registrácia
Idite na https://www.pythonanywhere.com → **Sign up Free**
(bezplatný účet stačí na začiatok)

### Krok 2 – Nahrajte súbory
V PythonAnywhere kliknite na **Files** → **Upload a file**
Nahrajte VŠETKY súbory z priečinka `magicspace/`

### Krok 3 – Nainštalujte Flask
V PythonAnywhere kliknite na **Bash console** a napíšte:
```bash
pip install flask --user
```

### Krok 4 – Nastavte Web App
1. Kliknite na **Web** → **Add a new web app**
2. Vyberte **Flask**
3. Python version: **3.10**
4. Source code: `/home/VASE_MENO/magicspace`
5. WSGI file: PythonAnywhere ho vygeneruje, upravte ho:

```python
import sys
sys.path.insert(0, '/home/VASE_MENO/magicspace')
from app import app as application
```

### Krok 5 – Reloadnite
Kliknite **Reload** → váš web beží na `VASE_MENO.pythonanywhere.com`

### Krok 6 – Vlastná doména magicspace.sk
1. V PythonAnywhere → Web → **Custom domain** → zadajte `magicspace.sk`
2. U vášho registrátora domény (kde ste kupili .sk) nastavte DNS:
   ```
   CNAME  www    →  VASE_MENO.pythonanywhere.com
   A      @      →  IP adresa z PythonAnywhere
   ```
3. Počkajte 1–24 hodín na propagáciu DNS

---

## 🔒 Zmena hesla do adminu

V súbore `admin.html` nájdite riadok:
```javascript
const PASS = 'admin123';  // zmeňte toto heslo!
```
Zmeňte `admin123` na vaše heslo.

---

## 📧 E-mail notifikácie (voliteľné)

Ak chcete dostávať e-mail pri každej rezervácii, pridajte do `app.py`:

```python
import smtplib
from email.mime.text import MIMEText

def send_notification(booking):
    msg = MIMEText(f"Nová rezervácia od {booking['name']} ({booking['email']})")
    msg['Subject'] = 'Nová rezervácia – MagicSpace'
    msg['From'] = 'vas@email.sk'
    msg['To'] = 'info@magicspace.sk'
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login('vas@email.sk', 'heslo_aplikacie')
        s.send_message(msg)
```

---

## ❓ Problémy?

| Problém | Riešenie |
|---------|----------|
| `ModuleNotFoundError: flask` | Spustite `pip install flask` |
| Port 5000 je obsadený | Zmeňte port: `app.run(port=8080)` |
| Databáza sa nevytvorí | Skontrolujte práva na zápis v priečinku |
| Web nefunguje na PythonAnywhere | Skontrolujte error log vo Web → Log files |
