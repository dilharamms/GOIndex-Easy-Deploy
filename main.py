import sys
import os
import json
import re
import zipfile
import platform
import urllib.request
import base64
import ctypes
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTextBrowser, QStackedWidget,
    QListWidget, QFrame, QMessageBox, QProgressBar, QComboBox,
    QCheckBox, QScrollArea, QFileDialog, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QByteArray, QSize, QBuffer, QIODevice
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

def find_logo_file():
    candidates = ["logo.png", "go index logo.png", "logo.ico", "favicon.png"]
    for cand in candidates:
        if os.path.exists(cand):
            return os.path.abspath(cand)
        parent_cand = os.path.abspath(os.path.join(".", cand))
        if os.path.exists(parent_cand):
            return parent_cand
    return None

# --- SVG ICONS ---
SVG_EYE = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
  <circle cx="12" cy="12" r="3"/>
</svg>"""

SVG_EYE_OFF = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
  <line x1="1" y1="1" x2="23" y2="23"/>
</svg>"""

def create_svg_icon(svg_content, size=24):
    renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

# --- STYLESHEET (Minimal & Modern Light Theme) ---
MODERN_STYLE = """
QMainWindow {
    background-color: #f8fafc;
}
QWidget {
    color: #0f172a;
    font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
}
QScrollArea {
    background-color: #f8fafc;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background-color: #f8fafc;
}
QListWidget {
    background-color: #ffffff;
    border: none;
    border-right: 1px solid #e2e8f0;
    outline: none;
    font-size: 14px;
    font-weight: 500;
    padding-top: 10px;
}
QListWidget::item {
    height: 45px;
    padding-left: 15px;
    color: #475569;
    border-radius: 6px;
    margin: 4px 8px;
}
QListWidget::item:hover {
    background-color: #f1f5f9;
    color: #0f172a;
}
QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: bold;
}
QGroupBox {
    font-weight: bold;
    font-size: 13px;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    margin-top: 12px;
    padding: 15px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    background-color: #ffffff;
    color: #2563eb;
    font-weight: bold;
}
QLabel {
    font-size: 13px;
    color: #334155;
}
QLabel#HeaderLabel {
    font-size: 22px;
    font-weight: bold;
    color: #0f172a;
    margin-bottom: 2px;
}
QLabel#SubHeaderLabel {
    font-size: 13px;
    color: #64748b;
    margin-bottom: 12px;
}
QLabel#HelpTip {
    font-size: 12px;
    color: #64748b;
    font-style: italic;
}
QLineEdit, QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 10px;
    color: #0f172a;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #2563eb;
}
QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}
QCheckBox {
    font-size: 13px;
    color: #0f172a;
    spacing: 8px;
}
QPushButton {
    background-color: #2563eb;
    color: white;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
}
QPushButton#SecondaryButton {
    background-color: #f1f5f9;
    color: #0f172a;
    border: 1px solid #cbd5e1;
}
QPushButton#SecondaryButton:hover {
    background-color: #e2e8f0;
}
QPushButton#SuccessButton {
    background-color: #16a34a;
    color: white;
}
QPushButton#SuccessButton:hover {
    background-color: #15803d;
}
QTextEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    color: #0f172a;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    padding: 10px;
}
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #e2e8f0;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 4px;
}
"""

# --- WORKER THREAD FOR DOWNLOADING RCLONE ---
class DownloadWorker(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def run(self):
        try:
            system = platform.system().lower()
            if "win" in system:
                url = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
                exe_name = "rclone.exe"
            elif "darwin" in system:
                url = "https://downloads.rclone.org/rclone-current-osx-amd64.zip"
                exe_name = "rclone"
            else:
                url = "https://downloads.rclone.org/rclone-current-linux-amd64.zip"
                exe_name = "rclone"

            rclone_dir = os.path.abspath("rclone")
            os.makedirs(rclone_dir, exist_ok=True)
            zip_path = os.path.join(rclone_dir, "rclone.zip")

            def report_hook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = int((block_num * block_size / total_size) * 100)
                    self.progress.emit(min(percent, 100))

            urllib.request.urlretrieve(url, zip_path, reporthook=report_hook)

            final_exe = os.path.join(rclone_dir, exe_name)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith(exe_name):
                        zip_ref.extract(file, rclone_dir)
                        extracted_exe = os.path.join(rclone_dir, file)
                        if os.path.exists(final_exe) and os.path.abspath(extracted_exe) != os.path.abspath(final_exe):
                            os.remove(final_exe)
                        if os.path.abspath(extracted_exe) != os.path.abspath(final_exe):
                            os.rename(extracted_exe, final_exe)
                        break

            if os.path.exists(zip_path):
                os.remove(zip_path)

            self.finished.emit(os.path.abspath(final_exe))
        except Exception as e:
            self.error.emit(str(e))

# --- WORKER THREAD FOR AUTHORIZATION ---
class AuthWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, rclone_path, client_id, client_secret):
        super().__init__()
        self.rclone_path = rclone_path
        self.client_id = client_id
        self.client_secret = client_secret
        self.process = None

    def run(self):
        try:
            cmd = [
                self.rclone_path, "authorize", "drive",
                self.client_id, self.client_secret
            ]
            
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdout, stderr = self.process.communicate()

            if self.process and self.process.returncode == 0:
                self.finished.emit(stdout)
            else:
                self.error.emit(stderr if stderr else "Authorization failed.")
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.kill()
            except Exception:
                pass


# --- MAIN APPLICATION WINDOW ---
class RcloneConfiguratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GOIndex Easy Deploy")
        self.resize(980, 750)
        self.setStyleSheet(MODERN_STYLE)

        self.logo_path = find_logo_file()

        if self.logo_path:
            app_icon = QIcon(self.logo_path)
            self.setWindowIcon(app_icon)
            if QApplication.instance():
                QApplication.instance().setWindowIcon(app_icon)

        rclone_exe_name = "rclone.exe" if platform.system().lower() == "windows" else "rclone"
        self.rclone_bin = os.path.abspath(os.path.join(".", "rclone", rclone_exe_name))

        self.icon_eye = create_svg_icon(SVG_EYE)
        self.icon_eye_off = create_svg_icon(SVG_EYE_OFF)

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Navigation
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.addItem("Setup & Generator")
        self.sidebar.addItem("Guide & Instructions")
        self.sidebar.currentRowChanged.connect(self.switch_page)

        # Stacked Pages
        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_config_page())
        self.pages.addWidget(self.create_guide_page())

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages)

        self.sidebar.setCurrentRow(0)

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)

    # --- PAGE 1: SETUP & CONFIG ---
    def create_config_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        if self.logo_path:
            lbl_hdr_logo = QLabel()
            lbl_hdr_logo.setPixmap(QPixmap(self.logo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            header_layout.addWidget(lbl_hdr_logo, 0, Qt.AlignVCenter)

        header_text_box = QVBoxLayout()
        header = QLabel("GOIndex Easy Deploy")
        header.setObjectName("HeaderLabel")
        subheader = QLabel("Perform local OAuth authorization, extract refresh token, and generate Cloudflare Worker code.")
        subheader.setObjectName("SubHeaderLabel")
        header_text_box.addWidget(header)
        header_text_box.addWidget(subheader)

        header_layout.addLayout(header_text_box)
        header_layout.addStretch()

        # Rclone Status
        rclone_layout = QHBoxLayout()
        self.lbl_rclone_status = QLabel("Checking Rclone binary...")
        self.btn_manual_rclone = QPushButton("Manual Rclone Guide")
        self.btn_manual_rclone.setObjectName("SecondaryButton")
        self.btn_manual_rclone.clicked.connect(self.show_manual_rclone_guide)

        rclone_layout.addWidget(self.lbl_rclone_status)
        rclone_layout.addStretch()
        rclone_layout.addWidget(self.btn_manual_rclone)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # --- GROUP 1: GOOGLE OAUTH CREDENTIALS & AUTHORIZATION ---
        grp_auth = QGroupBox("1. Google OAuth Credentials & Local Auth")
        layout_auth = QVBoxLayout(grp_auth)
        
        grid_oauth = QGridLayout()
        grid_oauth.addWidget(QLabel("Client ID:"), 0, 0)
        self.txt_client_id = QLineEdit()
        self.txt_client_id.setPlaceholderText("Enter Client ID")
        grid_oauth.addWidget(self.txt_client_id, 0, 1)

        grid_oauth.addWidget(QLabel("Client Secret:"), 1, 0)
        secret_layout = QHBoxLayout()
        secret_layout.setContentsMargins(0, 0, 0, 0)
        secret_layout.setSpacing(6)
        self.txt_client_secret = QLineEdit()
        self.txt_client_secret.setPlaceholderText("Enter Client Secret")
        self.txt_client_secret.setEchoMode(QLineEdit.Password)
        self.btn_toggle_client_secret = QPushButton()
        self.btn_toggle_client_secret.setIcon(self.icon_eye)
        self.btn_toggle_client_secret.setIconSize(QSize(18, 18))
        self.btn_toggle_client_secret.setObjectName("SecondaryButton")
        self.btn_toggle_client_secret.setFixedWidth(38)
        self.btn_toggle_client_secret.setToolTip("Show/Hide Client Secret")
        self.btn_toggle_client_secret.setCheckable(True)
        self.btn_toggle_client_secret.toggled.connect(
            lambda checked: self.toggle_password_visibility(self.txt_client_secret, self.btn_toggle_client_secret, checked)
        )
        secret_layout.addWidget(self.txt_client_secret)
        secret_layout.addWidget(self.btn_toggle_client_secret)
        grid_oauth.addLayout(secret_layout, 1, 1)

        lbl_tip = QLabel("Supports both 'Desktop App' (Recommended) & 'Web Application' credentials. See Guide tab for details.")
        lbl_tip.setObjectName("HelpTip")

        self.btn_authorize = QPushButton("Start OAuth Authorization")
        self.btn_authorize.clicked.connect(self.start_auth)

        layout_auth.addLayout(grid_oauth)
        layout_auth.addWidget(lbl_tip)
        layout_auth.addWidget(self.btn_authorize)

        # --- GROUP 2: REFRESH TOKEN (AUTOMATIC OR MANUAL) ---
        grp_token = QGroupBox("2. Refresh Token (Auto-captured or Paste Manually)")
        layout_token = QVBoxLayout(grp_token)

        token_row = QHBoxLayout()
        self.txt_refresh_token = QLineEdit()
        self.txt_refresh_token.setPlaceholderText("Refresh token will auto-appear after OAuth, or paste token / raw JSON here...")
        self.txt_refresh_token.textChanged.connect(self.on_token_text_changed)

        self.btn_copy_token = QPushButton("Copy Token")
        self.btn_copy_token.setObjectName("SecondaryButton")
        self.btn_copy_token.clicked.connect(self.copy_refresh_token)

        token_row.addWidget(self.txt_refresh_token)
        token_row.addWidget(self.btn_copy_token)

        lbl_manual_tip = QLabel("Tip: You can also paste raw JSON from Rclone CLI here—the app will automatically parse the refresh_token!")
        lbl_manual_tip.setObjectName("HelpTip")

        layout_token.addLayout(token_row)
        layout_token.addWidget(lbl_manual_tip)

        # --- GROUP 3: DRIVE CONFIGURATION ---
        grp_drive = QGroupBox("3. Drive Configuration")
        grid_drive = QGridLayout(grp_drive)

        grid_drive.addWidget(QLabel("Site Name:"), 0, 0)
        self.txt_site_name = QLineEdit("goindex by dilharamms")
        grid_drive.addWidget(self.txt_site_name, 0, 1)

        grid_drive.addWidget(QLabel("Drive ID:"), 0, 2)
        self.txt_drive_id = QLineEdit("root")
        grid_drive.addWidget(self.txt_drive_id, 0, 3)

        grid_drive.addWidget(QLabel("Drive Name:"), 1, 0)
        self.txt_drive_name = QLineEdit("My Drive")
        grid_drive.addWidget(self.txt_drive_name, 1, 1)

        grid_drive.addWidget(QLabel("Username (Optional):"), 1, 2)
        self.txt_username = QLineEdit("")
        grid_drive.addWidget(self.txt_username, 1, 3)

        grid_drive.addWidget(QLabel("Password (Optional):"), 2, 0)
        pass_layout = QHBoxLayout()
        pass_layout.setContentsMargins(0, 0, 0, 0)
        pass_layout.setSpacing(6)
        self.txt_password = QLineEdit("")
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.btn_toggle_password = QPushButton()
        self.btn_toggle_password.setIcon(self.icon_eye)
        self.btn_toggle_password.setIconSize(QSize(18, 18))
        self.btn_toggle_password.setObjectName("SecondaryButton")
        self.btn_toggle_password.setFixedWidth(38)
        self.btn_toggle_password.setToolTip("Show/Hide Password")
        self.btn_toggle_password.setCheckable(True)
        self.btn_toggle_password.toggled.connect(
            lambda checked: self.toggle_password_visibility(self.txt_password, self.btn_toggle_password, checked)
        )
        pass_layout.addWidget(self.txt_password)
        pass_layout.addWidget(self.btn_toggle_password)
        grid_drive.addLayout(pass_layout, 2, 1)

        # --- GROUP 4: THEME & APPEARANCE ---
        grp_theme = QGroupBox("4. Theme & Appearance Settings")
        grid_theme = QGridLayout(grp_theme)

        grid_theme.addWidget(QLabel("Theme Mode:"), 0, 0)
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItems(["dark", "light"])
        grid_theme.addWidget(self.cmb_theme, 0, 1)

        grid_theme.addWidget(QLabel("Main Color:"), 0, 2)
        self.cmb_main_color = QComboBox()
        self.cmb_main_color.addItems([
            "blue-grey", "red", "pink", "purple", "deep-purple", "indigo",
            "blue", "light-blue", "cyan", "teal", "green", "light-green",
            "lime", "yellow", "amber", "orange", "deep-orange", "brown", "grey"
        ])
        grid_theme.addWidget(self.cmb_main_color, 0, 3)

        grid_theme.addWidget(QLabel("Accent Color:"), 1, 0)
        self.cmb_accent_color = QComboBox()
        self.cmb_accent_color.addItems([
            "blue", "red", "pink", "purple", "deep-purple", "indigo",
            "light-blue", "cyan", "teal", "green", "light-green", "lime",
            "yellow", "amber", "orange", "deep-orange"
        ])
        grid_theme.addWidget(self.cmb_accent_color, 1, 1)

        grid_theme.addWidget(QLabel("Footer Text:"), 1, 2)
        self.txt_footer_text = QLineEdit("Made with <3")
        grid_theme.addWidget(self.txt_footer_text, 1, 3)

        grid_theme.addWidget(QLabel("Help Page URL:"), 2, 0)
        self.txt_help_url = QLineEdit("")
        grid_theme.addWidget(self.txt_help_url, 2, 1)

        self.chk_hide_actions = QCheckBox("Hide Actions Tab (Direct download/copy links)")
        grid_theme.addWidget(self.chk_hide_actions, 2, 2, 1, 2)

        # Generate Button
        self.btn_generate = QPushButton("Generate GOIndex Worker Code")
        self.btn_generate.setObjectName("SuccessButton")
        self.btn_generate.clicked.connect(self.generate_worker_code)

        # --- GROUP 5: WORKER CODE OUTPUT ---
        grp_output = QGroupBox("5. Generated Cloudflare Worker Code (index.js)")
        layout_output_box = QVBoxLayout(grp_output)

        action_bar = QHBoxLayout()
        action_bar.addStretch()
        self.btn_copy_code = QPushButton("Copy Worker Code")
        self.btn_copy_code.setObjectName("SecondaryButton")
        self.btn_copy_code.clicked.connect(self.copy_worker_code)

        self.btn_download_code = QPushButton("Download index.js")
        self.btn_download_code.setObjectName("SecondaryButton")
        self.btn_download_code.clicked.connect(self.download_worker_code)

        action_bar.addWidget(self.btn_copy_code)
        action_bar.addWidget(self.btn_download_code)

        self.txt_index_code = QTextEdit()
        self.txt_index_code.setReadOnly(True)
        self.txt_index_code.setMinimumHeight(240)
        self.txt_index_code.setPlaceholderText("Generated worker code will appear here after authorization or clicking 'Generate GOIndex Worker Code'...")

        layout_output_box.addLayout(action_bar)
        layout_output_box.addWidget(self.txt_index_code)

        # Console / Auth Output
        lbl_console = QLabel("Console Logs:")
        lbl_console.setStyleSheet("font-weight: bold; margin-top: 5px;")
        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setMaximumHeight(90)
        self.txt_output.setPlaceholderText("Console logs will appear here...")

        # Assembly
        layout.addLayout(header_layout)
        layout.addLayout(rclone_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(grp_auth)
        layout.addWidget(grp_token)
        layout.addWidget(grp_drive)
        layout.addWidget(grp_theme)
        layout.addWidget(self.btn_generate)
        layout.addWidget(grp_output)
        layout.addWidget(lbl_console)
        layout.addWidget(self.txt_output)

        scroll.setWidget(container)

        self.check_local_rclone()

        return scroll

    # --- PAGE 2: GUIDE PAGE ---
    def create_guide_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)

        guide_hdr_layout = QHBoxLayout()
        guide_hdr_layout.setSpacing(16)

        if self.logo_path:
            lbl_guide_logo = QLabel()
            lbl_guide_logo.setPixmap(QPixmap(self.logo_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            guide_hdr_layout.addWidget(lbl_guide_logo, 0, Qt.AlignVCenter)

        header = QLabel("Google OAuth & Worker Deployment Guide")
        header.setObjectName("HeaderLabel")
        guide_hdr_layout.addWidget(header)
        guide_hdr_layout.addStretch()

        guide_text = QTextBrowser()
        guide_text.setOpenExternalLinks(True)
        guide_text.setReadOnly(True)
        guide_text.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                color: #334155;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 15px;
            }
        """)

        guide_content = """
        <h2>Google OAuth Setup Guide (Both Credentials Methods Supported)</h2>
        <p>Because Google deprecated the Out-Of-Band (OOB) OAuth flow (<code>urn:ietf:wg:oauth:2.0:oob</code>), remote environments like Google Colab can no longer display an auth code to copy manually.</p>
        <p>This desktop application runs <b>Rclone</b> locally on your computer to open a local web server (<code>http://127.0.0.1:53682/</code>), allowing you to safely authenticate with Google and automatically capture your <b>Refresh Token</b>.</p>

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;">

        <h3 style="color: #dc2626;">CRITICAL: Fixing Error 403: access_denied / Verification Error</h3>
        <p>If you get <i>"Access blocked: [App Name] has not completed the Google verification process / Error 403: access_denied"</i>, your Google OAuth project is in <b>Testing</b> mode and your Google account is not added as a test user.</p>
        <p><b>How to Fix (Choose Option 1 or Option 2):</b></p>
        <ol>
            <li><b>OPTION 1: Add your Email to "Test Users" (Recommended - Instant)</b>
                <ul>
                    <li>Go to <a style="color: #2563eb; font-weight: bold;" href="https://console.cloud.google.com/apis/credentials/consent">Google Cloud Console &rarr; OAuth consent screen</a>.</li>
                    <li>Scroll down to the <b>Test users</b> section.</li>
                    <li>Click <b>+ ADD USERS</b>, enter your Google account email, and click <b>SAVE</b>.</li>
                    <li>Return here and click <b>Start OAuth Authorization</b> again.</li>
                </ul>
            </li>
            <li style="margin-top: 8px;"><b>OPTION 2: Publish the App to Production</b>
                <ul>
                    <li>Go to <a style="color: #2563eb; font-weight: bold;" href="https://console.cloud.google.com/apis/credentials/consent">Google Cloud Console &rarr; OAuth consent screen</a>.</li>
                    <li>Under <b>Publishing status</b>, click <b>PUBLISH APP</b>.</li>
                    <li>During login, if Google shows a warning, click <b>Advanced</b> &rarr; <b>Go to App (unsafe)</b> to proceed.</li>
                </ul>
            </li>
        </ol>

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;">

        <h3 style="color: #2563eb;">METHOD 1: Desktop Application Credentials (Recommended - Zero Configuration)</h3>
        <p><i>Desktop credentials automatically allow local loopback authorization (<code>http://127.0.0.1:53682/</code>) without needing any manual redirect URIs configured.</i></p>
        <ol>
            <li>Go to the <a style="color: #2563eb; font-weight: bold;" href="https://console.cloud.google.com/apis/credentials">Google Cloud Console Credentials Page</a>.</li>
            <li>Click <b>+ CREATE CREDENTIALS</b> at the top and select <b>OAuth client ID</b>.</li>
            <li>Under <b>Application type</b>, select <b>Desktop app</b>.</li>
            <li>Enter any name (e.g., <i>GoIndex Generator</i>) and click <b>CREATE</b>.</li>
            <li>Copy your new <b>Client ID</b> and <b>Client Secret</b> into Section 1 of this app.</li>
            <li>Click <b>Start OAuth Authorization</b>. Your browser will open, sign in to Google, and your token will be captured automatically!</li>
        </ol>

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;">

        <h3 style="color: #0284c7;">METHOD 2: Web Application Credentials (If Using Existing Web Client ID)</h3>
        <p><i>If your Client ID is created as a "Web application", Google requires adding the local Rclone redirect URI manually to prevent <b>Error 400: redirect_uri_mismatch</b>.</i></p>
        <ol>
            <li>Go to the <a style="color: #2563eb; font-weight: bold;" href="https://console.cloud.google.com/apis/credentials">Google Cloud Console Credentials Page</a>.</li>
            <li>Under <b>OAuth 2.0 Client IDs</b>, click your existing Client ID to edit it.</li>
            <li>Scroll down to <b>Authorized redirect URIs</b> and click <b>+ ADD URI</b>.</li>
            <li>Add both of the following URIs:
                <ul style="margin-top: 5px;">
                    <li><code>http://127.0.0.1:53682/</code></li>
                    <li><code>http://localhost:53682/</code></li>
                </ul>
            </li>
            <li>Click <b>SAVE</b> at the bottom and wait ~60 seconds for Google to update settings.</li>
            <li>Return to this app and click <b>Start OAuth Authorization</b>.</li>
        </ol>

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;">

        <h3 style="color: #16a34a;">METHOD 3: Direct Refresh Token or JSON Paste</h3>
        <p>If you already have a <b>Refresh Token</b> (or raw JSON output from Rclone CLI), you can simply paste it directly into the <b>Refresh Token</b> field (Section 2) or paste the full JSON block. The app will automatically extract the token and let you click <b>Generate GoIndex Worker Code</b> immediately!</p>

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;">

        <h3 style="color: #6366f1;">Manual Rclone Installation (Fallback / Offline Setup)</h3>
        <p>If automatic Rclone download fails due to network restrictions, proxy, or firewall settings:</p>
        <ol>
            <li>Go to the official <a style="color: #2563eb; font-weight: bold;" href="https://rclone.org/downloads/">Rclone Downloads Page</a>.</li>
            <li>Download the zip package for your operating system (e.g. <i>Windows 64-bit</i>).</li>
            <li>Extract the downloaded zip file.</li>
            <li>Copy <code>rclone.exe</code> (Windows) or <code>rclone</code> (macOS/Linux) directly into either:
                <ul>
                    <li>The root directory of <b>GOIndex Easy Deploy</b> (next to <code>main.py</code>).</li>
                    <li>Or inside the <code>./rclone/</code> subfolder.</li>
                </ul>
            </li>
            <li>The application will automatically detect it and display <b>Status: Rclone Ready</b>!</li>
        </ol>

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;">

        <h3>Deploying to Cloudflare Workers:</h3>
        <ol>
            <li>Log into the <a style="color: #2563eb;" href="https://dash.cloudflare.com/">Cloudflare Dashboard</a> &rarr; <b>Workers & Pages</b>.</li>
            <li>Create a new Worker script.</li>
            <li>Click <b>Copy Worker Code</b> or <b>Download index.js</b> in this app.</li>
            <li>Paste the generated code into the Cloudflare Worker editor and click <b>Save and Deploy</b>!</li>
        </ol>
        """
        guide_text.setHtml(guide_content)

        layout.addLayout(guide_hdr_layout)
        layout.addWidget(guide_text)

        return page

    # --- HELPER METHODS ---
    def find_rclone(self):
        rclone_name = "rclone.exe" if platform.system().lower() == "windows" else "rclone"
        
        # 1. Check ./rclone/ subfolder first
        subfolder_path = os.path.abspath(os.path.join(".", "rclone", rclone_name))
        if os.path.exists(subfolder_path):
            return subfolder_path

        # 2. Check current root folder
        current_path = os.path.abspath(os.path.join(".", rclone_name))
        if os.path.exists(current_path):
            return current_path

        # 3. Check parent folder
        parent_path = os.path.abspath(os.path.join("..", rclone_name))
        if os.path.exists(parent_path):
            return parent_path

        # 4. Check system PATH
        from shutil import which
        path_in_env = which(rclone_name)
        if path_in_env:
            return path_in_env

        return None

    def check_local_rclone(self):
        found_path = self.find_rclone()
        if found_path:
            self.rclone_bin = found_path
            self.lbl_rclone_status.setText(f"Status: Rclone Ready ({found_path})")
            self.lbl_rclone_status.setStyleSheet("color: #16a34a; font-weight: bold;")
        else:
            self.lbl_rclone_status.setText("Status: Rclone missing. Downloading automatically...")
            self.lbl_rclone_status.setStyleSheet("color: #2563eb; font-weight: bold;")
            self.download_rclone()

    def download_rclone(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.dl_worker = DownloadWorker()
        self.dl_worker.progress.connect(self.progress_bar.setValue)
        self.dl_worker.finished.connect(self.on_download_finished)
        self.dl_worker.error.connect(self.on_download_error)
        self.dl_worker.start()

    def show_manual_rclone_guide(self):
        rclone_exe_name = "rclone.exe" if platform.system().lower() == "windows" else "rclone"
        msg = (
            "MANUAL RCLONE INSTALLATION GUIDE:\n\n"
            "If automatic download failed or you are offline:\n\n"
            f"1. Download Rclone for your OS from: https://rclone.org/downloads/\n"
            f"2. Extract the zip file and find '{rclone_exe_name}'.\n"
            f"3. Copy '{rclone_exe_name}' directly into either:\n"
            f"   - The root folder of this software (next to main.py)\n"
            f"   - Or inside the './rclone/' subfolder\n"
            "4. Re-run or click 'Start OAuth Authorization'.\n\n"
            "Would you like to open the official Rclone downloads page in your web browser now?"
        )
        reply = QMessageBox.information(
            self,
            "Manual Rclone Setup Guide",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            import webbrowser
            webbrowser.open("https://rclone.org/downloads/")

    def on_download_finished(self, path):
        self.rclone_bin = path
        self.progress_bar.setVisible(False)
        self.lbl_rclone_status.setText(f"Status: Rclone Ready ({path})")
        self.lbl_rclone_status.setStyleSheet("color: #16a34a; font-weight: bold;")
        self.txt_output.append(f"Rclone downloaded successfully to:\n{path}\n")

    def on_download_error(self, err):
        self.progress_bar.setVisible(False)
        self.lbl_rclone_status.setText("Status: Automatic Download Failed (Manual setup needed)")
        self.lbl_rclone_status.setStyleSheet("color: #dc2626; font-weight: bold;")
        self.txt_output.append(
            f"\n--- RCLONE AUTOMATIC DOWNLOAD FAILED ---\n"
            f"Error: {err}\n"
            f"Please download rclone.exe manually from https://rclone.org/downloads/ and place it in the project root folder.\n"
        )
        self.show_manual_rclone_guide()

    def kill_existing_rclone_processes(self):
        try:
            system = platform.system().lower()
            if "win" in system:
                subprocess.run(["taskkill", "/F", "/IM", "rclone.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-9", "-f", "rclone"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def closeEvent(self, event):
        if hasattr(self, 'auth_worker') and self.auth_worker and self.auth_worker.isRunning():
            self.auth_worker.stop()
            self.auth_worker.wait(1000)
        self.kill_existing_rclone_processes()
        event.accept()

    def start_auth(self):
        client_id = self.txt_client_id.text().strip()
        client_secret = self.txt_client_secret.text().strip()

        if not client_id or not client_secret:
            QMessageBox.warning(self, "Input Error", "Please provide both Client ID and Client Secret.")
            return

        rclone_path = self.find_rclone()
        if not rclone_path and not os.path.exists(self.rclone_bin):
            rclone_exe_name = "rclone.exe" if platform.system().lower() == "windows" else "rclone"
            QMessageBox.warning(
                self,
                "Rclone Binary Missing",
                f"Rclone executable ('{rclone_exe_name}') was not found and automatic download failed.\n\n"
                f"Please place '{rclone_exe_name}' directly into the project root folder (next to main.py) or inside the './rclone/' directory."
            )
            self.show_manual_rclone_guide()
            return

        # Clean up any lingering rclone processes holding port 53682
        self.kill_existing_rclone_processes()

        active_rclone = rclone_path if rclone_path else self.rclone_bin

        self.btn_authorize.setEnabled(False)
        self.txt_output.setText("Starting Rclone auth server...\nYour default browser should open shortly.")

        self.auth_worker = AuthWorker(active_rclone, client_id, client_secret)
        self.auth_worker.finished.connect(self.on_auth_finished)
        self.auth_worker.error.connect(self.on_auth_error)
        self.auth_worker.start()

    def parse_token_from_text(self, text):
        if not text:
            return "", "empty"
        text = text.strip()

        # 1. Look for explicit refresh token starting with 1//
        match_goog = re.search(r'1//[a-zA-Z0-9_\-]+', text)
        if match_goog:
            return match_goog.group(0).strip(), "refresh_token"

        # 2. Look for JSON refresh_token key
        if "{" in text and "}" in text:
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                json_str = text[start:end]
                data = json.loads(json_str)
                if isinstance(data, dict):
                    ref_tok = str(data.get("refresh_token") or "").strip()
                    if ref_tok:
                        if ref_tok.startswith("ya29."):
                            return "", "access_token_only"
                        return ref_tok, "refresh_token"

                    acc_tok = str(data.get("access_token") or "").strip()
                    if acc_tok:
                        return "", "access_token_only"
            except Exception:
                pass

        # 3. Check regex for "refresh_token":"..."
        match_ref = re.search(r'"refresh_token"\s*:\s*"([^"]+)"', text)
        if match_ref:
            val = match_ref.group(1).strip()
            if val.startswith("ya29."):
                return "", "access_token_only"
            return val, "refresh_token"

        # 4. Check if output contains access_token (ya29...) without refresh_token
        if "access_token" in text or "ya29." in text:
            return "", "access_token_only"

        # 5. Check if text is a single line without spaces
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) == 1 and " " not in lines[0]:
            if lines[0].startswith("ya29."):
                return "", "access_token_only"
            return lines[0], "refresh_token"

        return "", "unknown"

    def on_auth_finished(self, output):
        self.btn_authorize.setEnabled(True)
        self.txt_output.setText(output)

        extracted_token, token_type = self.parse_token_from_text(output)

        if token_type == "refresh_token" and extracted_token:
            self.txt_refresh_token.setText(extracted_token)
            self.txt_output.append(f"\n--- EXTRACTED REFRESH TOKEN ---\n{extracted_token}\n")
            self.generate_worker_code()
            QMessageBox.information(self, "Success", "Authorization completed successfully!\nRefresh Token extracted and Worker Code generated.")
        elif token_type == "access_token_only":
            msg = (
                "CRITICAL WARNING: Google returned a temporary Access Token (ya29...) instead of a Refresh Token (1//...).\n\n"
                "Why this happens:\n"
                "Google only issues a true Refresh Token on the FIRST time you authorize an app.\n"
                "Because your account already authorized this Client ID before, Google sent a short-lived 1-hour Access Token (ya29...), which causes Cloudflare Worker to hang ('green loading line')!\n\n"
                "HOW TO FIX AND GET A REFRESH TOKEN (Choose Option 1 or Option 2):\n\n"
                "OPTION 1: Revoke App Access in Google Account (Instant & Recommended)\n"
                "1. Open https://myaccount.google.com/permissions in your browser.\n"
                "2. Find your app name and click 'Delete all connections' / 'Remove Access'.\n"
                "3. Return here and click 'Start OAuth Authorization' again.\n"
                "   Google will prompt for permissions again and issue a true Refresh Token (starts with 1//)!\n\n"
                "OPTION 2: Create a fresh OAuth Client ID\n"
                "1. Go to Google Cloud Console -> Credentials.\n"
                "2. Create a new OAuth Client ID (Desktop App).\n"
                "3. Paste the new Client ID & Secret into Section 1 and re-authorize."
            )
            self.txt_output.append(f"\n--- ATTENTION REQUIRED ---\n{msg}\n")
            QMessageBox.warning(self, "Temporary Access Token Received (ya29...)", msg)
        else:
            QMessageBox.warning(self, "Auth Output", "Authorization completed, but refresh_token could not be parsed automatically. If output contains a token starting with 1//, copy it into the Refresh Token field manually.")

    def on_auth_error(self, err):
        self.btn_authorize.setEnabled(True)
        self.txt_output.append(f"\n--- AUTHORIZATION ERROR ---\n{err}\n")
        QMessageBox.critical(self, "Authorization Error", f"OAuth authorization failed:\n{err}")

    def on_token_text_changed(self, text):
        text = text.strip()
        if "{" in text or '"access_token"' in text or '"refresh_token"' in text or text.startswith("Got code"):
            parsed_tok, token_type = self.parse_token_from_text(text)
            if token_type == "refresh_token" and parsed_tok and parsed_tok != text:
                self.txt_refresh_token.blockSignals(True)
                self.txt_refresh_token.setText(parsed_tok)
                self.txt_refresh_token.blockSignals(False)
                self.txt_output.append(f"Parsed refresh token from input: {parsed_tok}\n")
                self.generate_worker_code()

    def copy_refresh_token(self):
        token = self.txt_refresh_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Warning", "No refresh token to copy.")
            return
        QApplication.clipboard().setText(token)
        QMessageBox.information(self, "Copied", "Refresh token copied to clipboard!")

    def copy_worker_code(self):
        code = self.txt_index_code.toPlainText()
        if not code:
            QMessageBox.warning(self, "Warning", "No worker code generated yet.")
            return
        QApplication.clipboard().setText(code)
        QMessageBox.information(self, "Copied", "Cloudflare Worker code copied to clipboard!")

    def download_worker_code(self):
        code = self.txt_index_code.toPlainText()
        if not code:
            QMessageBox.warning(self, "Warning", "No worker code generated yet.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Worker Code", "index.js", "JavaScript Files (*.js);;Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                QMessageBox.information(self, "Success", f"Worker code saved successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def load_template(self):
        template_files = ["index_template_for_installer.js", "template_cache.js"]
        for tf in template_files:
            if os.path.exists(tf):
                try:
                    with open(tf, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    pass

        url = "https://raw.githubusercontent.com/cheems/goindex-extended/master/template/index_template_for_installer.js"
        try:
            req = urllib.request.urlopen(url)
            content = req.read().decode("utf-8")
            with open("index_template_for_installer.js", "w", encoding="utf-8") as f:
                f.write(content)
            return content
        except Exception as e:
            self.txt_output.append(f"Error loading online template: {e}\n")
            return None

    def generate_worker_code(self):
        client_id = self.txt_client_id.text().strip()
        client_secret = self.txt_client_secret.text().strip()
        refresh_token = self.txt_refresh_token.text().strip()
        site_name = self.txt_site_name.text().strip() or "goindex by dilharamms"
        site_icon = "https://raw.githubusercontent.com/dilharamms/GOIndex-Easy-Deploy/refs/heads/main/logo.png"
        repo_url = "https://github.com/dilharamms/GOIndex-Easy-Deploy"
        repo_owner = "dilharamms"
        repo_name = "GOIndex-Easy-Deploy"
        drive_id = self.txt_drive_id.text().strip() or "root"
        drive_name = self.txt_drive_name.text().strip() or "My Drive"
        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()
        theme = self.cmb_theme.currentText()
        main_color = self.cmb_main_color.currentText()
        accent_color = self.cmb_accent_color.currentText()
        help_url = self.txt_help_url.text().strip()
        footer_text = self.txt_footer_text.text().strip()
        hide_actions_tab = self.chk_hide_actions.isChecked()

        if not refresh_token:
            QMessageBox.warning(self, "Missing Refresh Token", "Please start local authorization first to generate a refresh token, or enter/paste one manually.")
            return

        template_content = self.load_template()
        if not template_content:
            QMessageBox.critical(self, "Error", "Could not load GoIndex template file.")
            return

        replacements = {
            "{cheems_site_name}": site_name,
            "{cheems_site_icon}": site_icon,
            "{cheems_repo_url}": repo_url,
            "{cheems_repo_owner}": repo_owner,
            "{cheems_repo_name}": repo_name,
            "{cheems_client_id}": client_id,
            "{cheems_client_secret}": client_secret,
            "{cheems_refresh_token}": refresh_token,
            "{cheems_drive_id}": drive_id,
            "{cheems_drive_name}": drive_name,
            "{cheems_username}": username,
            "{cheems_password}": password,
            "{cheems_theme}": "true" if theme == "dark" else "false",
            "{cheems_main_color}": main_color,
            "{cheems_accent_color}": accent_color,
            "{cheems_help_url}": help_url,
            "{cheems_footer_text}": footer_text,
            "{cheems_hide_actions_tab}": "true" if hide_actions_tab else "false"
        }

        code = template_content
        for k, v in replacements.items():
            code = code.replace(k, str(v))

        self.txt_index_code.setText(code)
        self.txt_output.append("GoIndex Cloudflare Worker code generated successfully!\n")

    def toggle_password_visibility(self, line_edit, button, checked):
        if checked:
            line_edit.setEchoMode(QLineEdit.Normal)
            button.setIcon(self.icon_eye_off)
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            button.setIcon(self.icon_eye)


if __name__ == "__main__":
    if platform.system().lower() == "windows":
        try:
            myappid = 'dilharamms.goindex.easydeploy.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    window = RcloneConfiguratorApp()
    app.aboutToQuit.connect(window.kill_existing_rclone_processes)
    window.show()
    sys.exit(app.exec())