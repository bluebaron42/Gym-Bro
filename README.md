# Gym-Bro: install on your Android phone

The app is 8 files: `index.html`, `profile.js`, `data.js`, `guides.js`, `manifest.webmanifest`, `sw.js`, `icon-192.png`, `icon-512.png`. Keep them together in one folder.

## 1. Put it on GitHub Pages (free, about 10 minutes)

1. Sign in or sign up at github.com.
2. Tap **+** (top right) → **New repository**. Name it `Gym-Bro`, set it to **Public**, tick **Add a README**, then **Create repository**.
3. On the repository page: **Add file** → **Upload files**. Drag in all 8 files (not the folder itself, and not the zip). Tap **Commit changes**.
4. Go to **Settings** → **Pages**. Under **Build and deployment**, set Source to **Deploy from a branch**, Branch to **main**, folder **/ (root)**, then **Save**.
5. Wait 1–2 minutes and refresh the Pages screen. It shows your link, something like `https://bluebaron42.github.io/Gym-Bro/`.

The repository is public, so anyone with the link can see the plan. Your logged data is not in it: that stays on your phone.

## 2. Install it on your phone

1. Open your link in **Chrome** on your phone.
2. Tap the **⋮** menu → **Install app** (on some phones it says **Add to Home screen**, then **Install**).
3. The barbell icon appears on your home screen and in your app drawer. It opens full screen, with no browser bar, and works offline at the gym.

## 3. Using it with Claude

- **Review:** Progress tab → **Copy data for Claude**, then paste it into our chat and ask for a review or plan changes.
- **Backup:** Progress tab → **Back up** saves a file to your Downloads. Do this every couple of weeks.
- **Restore:** Progress tab → **Restore** and pick the backup file. It replaces what's on the phone.

Your data is lost if you uninstall the app or clear Chrome's site data, so keep a recent backup.

## Sharing menus with your partner

- **Food tab → Copy my menu**, then send the message on WhatsApp.
- When your partner sends theirs, copy the whole message, then **Food tab → Paste partner's menu**.
- **Shopping list: Together** combines both weeks into one list; **Just mine** shows only yours.

`index.html`, `data.js` and `guides.js` are shared with Gym-Gyal. `profile.js` holds the settings that make this app yours.

## Updating the app later

When I send you an update zip, unzip it, then in your repository tap **Add file → Upload files**, drop in every file from the zip and tap **Commit changes**. Same-named files are replaced. I bump the version in `sw.js` for you each time.

Give GitHub a minute or two, then open the app with signal. If you don't see the change, close it fully and reopen. Your logs, menu choices and ticks are kept.
