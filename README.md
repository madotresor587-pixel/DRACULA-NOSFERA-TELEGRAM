# DRACULA NOSFERA TELEGRAM

Bot Telegram en Python avec menu interactif, commandes utiles, panneau administrateur et journalisation.

## Fonctionnalités
- Menu avec boutons interactifs
- Commandes : /start, /menu, /help, /ping, /id, /info, /rules, /contact
- Panneau administrateur privé : /admin et /stats
- Enregistrement des utilisateurs dans SQLite
- Gestion centralisée des erreurs et journaux
- Compatible avec un hébergement Python en mode polling

## Configuration

| Variable | Obligatoire | Description |
|---|---:|---|
| TELEGRAM_BOT_TOKEN | Oui | Token du bot obtenu auprès de BotFather |
| OWNER_ID | Non | Identifiant numérique du propriétaire |
| ADMIN_IDS | Non | Identifiants administrateurs séparés par des virgules |
| BOT_NAME | Non | Nom affiché, par défaut DRACULA NOSFERA |
| BOT_DEVELOPER | Non | Signature, par défaut MADO DEV |
| BOT_CONTACT | Non | Contact affiché, par défaut @MadoPhantomAI |
| DATABASE_PATH | Non | Chemin SQLite, par défaut data/bot.sqlite3 |
| LOG_LEVEL | Non | Niveau de logs, par défaut INFO |

Ne place jamais le token dans le code ou dans GitHub. Ajoute-le uniquement dans les variables secrètes de l'hébergeur.

## Lancement local

```bash
python -m pip install -r requirements.txt
TELEGRAM_BOT_TOKEN="TON_TOKEN" python main.py
```

## FadeHost

- Runtime : Python
- Branche : main
- Build command : `pip install -r requirements.txt`
- Start command : `python main.py`
- Variable secrète : `TELEGRAM_BOT_TOKEN`
- Variable recommandée : `OWNER_ID` avec ton identifiant Telegram numérique

Le bot utilise le polling Telegram : aucun port HTTP n'est nécessaire. Pour conserver les données SQLite après un redémarrage, configure un stockage persistant si l'hébergeur en propose un.

## Sécurité
- /admin et /stats sont réservées aux identifiants configurés dans OWNER_ID ou ADMIN_IDS.
- N'ajoute jamais le token à un commit.
- Révoque immédiatement tout token qui aurait été publié par erreur.
