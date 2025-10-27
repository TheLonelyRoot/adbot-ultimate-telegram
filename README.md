# Hybrid Telegram Ad Bot

> **Credit:** All code and logic by [@TheLonelyRoot](https://github.com/TheLonelyRoot)

---

<p align="center">
  <img src="https://user-images.githubusercontent.com/76848676/235312345-7e2e2e2e-7e2e-4e2e-8e2e-2e2e2e2e2e2e.png" width="120" alt="AdBot Logo"/>
</p>

<h2 align="center">🚀 Hybrid Telegram Ad Sender Bot</h2>

<p align="center">
  <b>Control via Bot Commands • Operate via User Client • Full Group Scraping • Automated Ad Delivery</b>
</p>

---

## 🌟 Features

- **Dual Client:** Operates with both bot and user accounts for maximum reach.
- **Automated Group Scraping:** Finds and targets only valid groups, supergroups, and forums.
- **Deduplication & Filtering:** Ensures only unique, valid targets are used.
- **Robust Error Handling:** Auto-reconnect, skip blocked groups, and detailed diagnostics.
- **JSON Logging:** Sends logs in JSON format for easy parsing.
- **Auto Bio Update:** Keeps your Telegram bio fresh and relevant.
- **Easy Setup:** One-command deployment for Termux, VPS, or local.
- **Full Data Reset:** Instantly clear all sessions, groups, and targets.
- **Beautiful Terminal UI:** Rich, color-coded output for clarity.

---

## 🖥️ Terminal UI Preview

```
 ,--.   ,--.,------. ,--.  ,--. ,-----. ,--.         ,---.  ,------.  ,-----.   ,-----. ,--------. 
 |   `.'   ||  .--. '|  ,'.|  |'  .-.  '|  |        /  O  \ |  .-.  \ |  |) /_ '  .-.  ''--.  .--' 
 |  |'.'|  ||  '--'.'|  |' '  ||  | |  ||  |       |  .-.  ||  |  \  :|  .-.  \|  | |  |   |  |    
 |  |   |  ||  |\  \ |  | `   |'  '-'  '|  '--.    |  | |  ||  '--'  /|  '--' /'  '-'  '   |  |    
 `--'   `--'`--' '--'`--'  `--' `-----' `-----'    `--' `--'`-------' `------'  `-----'    `--'    
```

---

## ⚡ Quick Start

```bash
# Termux (Android)
chmod +x termux_setup.sh && ./termux_setup.sh

# Linux/VPS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

---

## 🛠️ Configuration

Edit `config.json` to set your bot token, admin users, ad message, and other options.

---

## 📂 File Structure

```
ADBOT 10-4-25/
├── bot.py
├── config.json
├── credentials.csv
├── fix_groups_db.py
├── fix_stats.py
├── get_user_id.py
├── groups_database.json
├── groups.json
├── requirements.txt
├── sanitize_for_sale.sh
├── stats.json
├── termux_setup.sh
└── __pycache__/
```

---

## 💬 Support & Credit

- All code and logic by [@TheLonelyRoot](https://github.com/TheLonelyRoot)
- For issues, open a GitHub issue or contact @TheLonelyRoot on Telegram.

---

<p align="center">
  <b>Made with ❤️ for Telegram automation</b>
</p>
