# GOIndex Easy Deploy

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/GUI-PySide6%2FQt-brightgreen.svg)](https://pypi.org/project/PySide6/)
[![Backend Engine](https://img.shields.io/badge/OAuth-Rclone-orange.svg)](https://rclone.org/)
[![Deployment Target](https://img.shields.io/badge/Deploy-Cloudflare%20Workers-f38020.svg)](https://workers.cloudflare.com/)

**GOIndex Easy Deploy** is a modern desktop application built with Python and PySide6 that simplifies configuring and deploying **GOIndex** (Google Drive Indexer) on **Cloudflare Workers**.

It solves the issue caused by Google's deprecation of the Out-Of-Band (OOB) OAuth flow (`urn:ietf:wg:oauth:2.0:oob`) by running a local authorization loopback server (`http://127.0.0.1:53682/`) via **Rclone**, automatically retrieving your Google Drive **Refresh Token**, and generating a fully styled, customizable Cloudflare Worker script (`index.js`).

---

## 🌟 Key Features

- 🔐 **Automated Local OAuth Authorization**: Runs a local loopback web server via Rclone to safely sign into Google Drive and capture your `refresh_token`.
- ⚙️ **Automatic Binary Management**: Automatically detects or downloads the latest `rclone` binary for Windows, macOS, or Linux.
- 🎨 **Full GOIndex Customization**:
  - **Drive Options**: Root drive or specific Shared/Team Drive ID.
  - **Security**: Optional password protection with HTTP Basic Auth.
  - **Themes & Styling**: Dark / Light mode toggle, 19 main theme colors, 16 accent colors, custom footer text, and help URL.
  - **UI Options**: Hide or show direct download / copy actions tab.
- 🧠 **Smart Refresh Token Parser**: Automatically parses and extracts `refresh_token` from raw JSON strings or Rclone CLI outputs pasted into the application.
- ⚠️ **Token Warning System**: Detects when Google returns a temporary 1-hour access token (`ya29...`) instead of a refresh token (`1//...`) and provides step-by-step instructions to fix it.
- 📖 **Embedded Step-by-Step Guide**: Includes built-in instructions to solve Google OAuth 403 `access_denied` errors, setup credentials, and deploy to Cloudflare Workers.
- 📋 **One-Click Export**: Easily copy the generated Cloudflare Worker JavaScript code to clipboard or export it directly as `index.js`.

---

## 🛠️ Prerequisites & Installation

### Requirements
- **Python 3.8+** installed on your system.
- **PySide6** (Qt for Python).

### Installation Steps

1. **Clone or Download the Repository**:
   ```bash
   git clone https://github.com/dilharamms/GOIndex-Easy-Deploy.git
   cd GOIndex-Easy-Deploy
   ```

2. **Install Dependencies**:
   ```bash
   pip install PySide6
   ```

3. **Run the Application**:
   ```bash
   python main.py
   ```

---

## 🚀 How to Use

### Step 1: Create Google OAuth Credentials
1. Open the [Google Cloud Console Credentials Page](https://console.cloud.google.com/apis/credentials).
2. Click **+ CREATE CREDENTIALS** &rarr; **OAuth client ID**.
3. Choose **Desktop app** (Recommended - requires zero redirect URI setup) or **Web application**.
   > *Note: If using "Web application", add `http://127.0.0.1:53682/` and `http://localhost:53682/` under **Authorized redirect URIs**.*
4. Copy your **Client ID** and **Client Secret**.

### Step 2: Authenticate & Capture Refresh Token
1. Paste your **Client ID** and **Client Secret** into Section 1 of the app.
2. Click **Start OAuth Authorization**.
3. Your web browser will open automatically. Sign in with your Google account and grant permissions.
4. Once completed, your **Refresh Token** will be automatically extracted into the app.

### Step 3: Configure & Generate Worker Code
1. Set your **Site Name**, **Drive ID** (`root` or Shared Drive ID), **Username**, **Password**, and **Appearance Theme**.
2. Click **Generate GOIndex Worker Code**.
3. Click **Copy Worker Code** or **Download index.js**.

### Step 4: Deploy to Cloudflare Workers
1. Log into your [Cloudflare Dashboard](https://dash.cloudflare.com/) &rarr; **Workers & Pages**.
2. Create a new Worker.
3. Replace the default code with the generated `index.js` content.
4. Click **Save and Deploy**.

---

## ❓ Troubleshooting & FAQs

<details>
<summary><b>Error 403: access_denied / App has not completed Google verification</b></summary>
<br>

This happens when your Google Cloud project is in **Testing** publishing status and your Google account hasn't been added as a test user.

**Fix:**
1. Go to [Google Cloud Console OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent).
2. Under **Test users**, click **+ ADD USERS**.
3. Add your Google account email and click **SAVE**.
4. Re-run authorization in the app.
</details>

<details>
<summary><b>App receives a temporary Access Token (ya29...) instead of a Refresh Token (1//...)</b></summary>
<br>

Google only issues a `refresh_token` the **first time** an app is authorized. If you've previously authorized this Client ID, Google will issue a short-lived 1-hour access token (`ya29...`), which causes Cloudflare Worker to hang on a green loading bar after 1 hour.

**Fix:**
1. Go to your [Google Account Permissions](https://myaccount.google.com/permissions).
2. Select your app and click **Remove Access** / **Delete all connections**.
3. Return to GOIndex Easy Deploy and click **Start OAuth Authorization** again.
</details>

<details>
<summary><b>Error 400: redirect_uri_mismatch</b></summary>
<br>

This occurs if you use a "Web application" credential type without configuring loopback redirect URIs.

**Fix:**
Add both `http://127.0.0.1:53682/` and `http://localhost:53682/` under **Authorized redirect URIs** in Google Cloud Console.
</details>

---

## 📁 Repository Structure

```
GOIndex-Easy-Deploy/
├── main.py                         # Main PySide6 GUI Application
├── index_template_for_installer.js # GOIndex Worker template file
├── template_cache.js               # Cached template fallback
├── rclone/                         # Rclone binaries and docs directory
│   ├── rclone.exe                  # Rclone executable (auto-downloaded if missing)
│   ├── rclone.1                    # Rclone manual man page
│   ├── README.txt                  # Rclone text documentation
│   └── README.html                 # Rclone HTML documentation
└── README.md                       # Main Project Documentation
```

---

## 🙏 Credits & Acknowledgments

- **GOIndex / GOIndex Extended**: Developed by [menukaonline](https://github.com/menukaonline/goindex-extended) and original GOIndex authors.
- **Rclone**: The versatile cloud storage tool created by [Nick Craig-Wood](https://rclone.org/).


---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more details.
