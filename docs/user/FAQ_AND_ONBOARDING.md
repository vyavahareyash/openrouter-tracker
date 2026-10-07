# Onboarding & FAQ

---

## 3-Step Quickstart

### Step 1: Install & Launch
Download `OpenRouterTracker.dmg` from [GitHub Releases](https://github.com/vyavahareyash/openrouter-tracker/releases/latest) (or build locally via `./build.sh`). Drag `OpenRouterTracker.app` into `/Applications` and launch it once.

> **Gatekeeper Notice**: Because this open-source build is ad-hoc signed, macOS may show a developer security prompt on first launch. If prompted, run:
> ```bash
> xattr -cr /Applications/OpenRouterTracker.app
> ```
> Or go to **System Settings > Privacy & Security** and click **Open Anyway**.

### Step 2: Add your OpenRouter API Key
1. Generate an API Key at [openrouter.ai/keys](https://openrouter.ai/keys).
2. In the app, click **"+ Add API Key"** in the bottom left sidebar.
3. Paste your key (`sk-or-v1-...`) and assign a recognizable label (e.g., "Main Production").
4. Ensure **"Show on Desktop Widget"** is toggled ON.
5. Click **"Save Key"**.

> 🔐 **Keychain Prompt**: macOS will display: *"OpenRouter Tracker wants to use your login keychain."*
> Enter your Mac user account password and click **"Always Allow"**.
> 
> *Why?* Keys are never stored in unencrypted files. OpenRouter Tracker securely delegates key storage to **Apple Keychain Services** (AES-256). Choosing "Always Allow" permits the companion app and the widget extension to read the encrypted credential without prompting you on every refresh.

### Step 3: Add Widget to Desktop
1. Right-click any open space on your macOS Desktop and click **"Edit Widgets..."**.
2. In the widget gallery search bar, type **"OpenRouter"**.
3. Select either **Small** or **Medium** and drag it directly onto your desktop or Notification Center.

---

## Frequently Asked Questions

### Why is my widget blank or showing `$0.00`?
1. Open the companion app to ensure your key has verified successfully and received metrics from OpenRouter.
2. Click the `🔄 Refresh` button on the widget to trigger an explicit fetch.
3. If still blank, verify internet connectivity and ensure your key has not expired.

### Does the widget drain battery?
No. OpenRouter Tracker does **not** run any continuous background scripts, Daemons, or helper processes. macOS's built-in `chronod` scheduling system wakes the widget timeline only when necessary or when you explicitly click the refresh button.

### Can I track multiple keys on my desktop?
Yes. You can add multiple keys in the host app. Currently, the desktop widget displays the key marked as the active widget key. In the companion app, click **"Set as Desktop Widget Key"** on any key to swap which key is rendered.

### What permissions are needed?
None beyond standard outbound HTTPS internet access. No screen recording, file access, or accessibility permissions are requested.
