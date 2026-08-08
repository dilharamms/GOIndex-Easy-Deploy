import sys
import os
import json
import zipfile
import platform
import urllib.request
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QStackedWidget,
    QListWidget, QFrame, QMessageBox, QProgressBar, QComboBox,
    QCheckBox, QScrollArea, QFileDialog, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

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
                zip_path = "rclone.zip"
                exe_name = "rclone.exe"
            elif "darwin" in system:
                url = "https://downloads.rclone.org/rclone-current-osx-amd64.zip"
                zip_path = "rclone.zip"
                exe_name = "rclone"
            else:
                url = "https://downloads.rclone.org/rclone-current-linux-amd64.zip"
                zip_path = "rclone.zip"
                exe_name = "rclone"

            def report_hook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = int((block_num * block_size / total_size) * 100)
                    self.progress.emit(min(percent, 100))

            urllib.request.urlretrieve(url, zip_path, reporthook=report_hook)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith(exe_name):
                        zip_ref.extract(file, ".")
                        extracted_exe = os.path.join(".", file)
                        final_exe = os.path.join(".", exe_name)
                        if os.path.exists(final_exe):
                            os.remove(final_exe)
                        os.rename(extracted_exe, final_exe)
                        break

            if os.path.exists(zip_path):
                os.remove(zip_path)

            self.finished.emit(os.path.abspath(exe_name))
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

    def run(self):
        try:
            cmd = [
                self.rclone_path, "authorize", "drive",
                self.client_id, self.client_secret
            ]
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.finished.emit(stdout)
            else:
                self.error.emit(stderr if stderr else "Authorization failed.")
        except Exception as e:
            self.error.emit(str(e))


# --- MAIN APPLICATION WINDOW ---
class RcloneConfiguratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoIndex Extended Worker Code Generator")
        self.resize(960, 740)
        self.setStyleSheet(MODERN_STYLE)

        self.rclone_bin = "rclone.exe" if platform.system().lower() == "windows" else "rclone"

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

        header = QLabel("GoIndex Worker Code Generator")
        header.setObjectName("HeaderLabel")
        subheader = QLabel("Perform local OAuth authorization, extract refresh token, and generate Cloudflare Worker code.")
        subheader.setObjectName("SubHeaderLabel")

        # Rclone Status
        rclone_layout = QHBoxLayout()
        self.lbl_rclone_status = QLabel("Checking Rclone binary...")
        rclone_layout.addWidget(self.lbl_rclone_status)
        rclone_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # --- GROUP 1: GOOGLE OAUTH CREDENTIALS & AUTHORIZATION ---
        grp_auth = QGroupBox("1. Google OAuth Credentials & Local Auth")
        layout_auth = QVBoxLayout(grp_auth)
        
        grid_oauth = QGridLayout()
        grid_oauth.addWidget(QLabel("Client ID:"), 0, 0)
        self.txt_client_id = QLineEdit("202264815644.apps.googleusercontent.com")
        grid_oauth.addWidget(self.txt_client_id, 0, 1)

        grid_oauth.addWidget(QLabel("Client Secret:"), 1, 0)
        self.txt_client_secret = QLineEdit("X4Z3ca8xfWDb1Voo-F9a7ZxJ")
        self.txt_client_secret.setEchoMode(QLineEdit.Password)
        grid_oauth.addWidget(self.txt_client_secret, 1, 1)

        self.btn_authorize = QPushButton("Start Local OAuth Authorization")
        self.btn_authorize.clicked.connect(self.start_auth)

        layout_auth.addLayout(grid_oauth)
        layout_auth.addWidget(self.btn_authorize)

        # --- GROUP 2: REFRESH TOKEN ---
        grp_token = QGroupBox("2. Refresh Token")
        layout_token = QHBoxLayout(grp_token)
        
        self.txt_refresh_token = QLineEdit()
        self.txt_refresh_token.setPlaceholderText("Refresh token will automatically appear here after authorization...")
        
        self.btn_copy_token = QPushButton("Copy Token")
        self.btn_copy_token.setObjectName("SecondaryButton")
        self.btn_copy_token.clicked.connect(self.copy_refresh_token)

        layout_token.addWidget(self.txt_refresh_token)
        layout_token.addWidget(self.btn_copy_token)

        # --- GROUP 3: DRIVE CONFIGURATION ---
        grp_drive = QGroupBox("3. Drive Configuration")
        grid_drive = QGridLayout(grp_drive)

        grid_drive.addWidget(QLabel("Site Name:"), 0, 0)
        self.txt_site_name = QLineEdit("GoIndex Extended by Cheems")
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
        self.txt_password = QLineEdit("")
        self.txt_password.setEchoMode(QLineEdit.Password)
        grid_drive.addWidget(self.txt_password, 2, 1)

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
        self.btn_generate = QPushButton("Generate GoIndex Worker Code")
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
        self.txt_index_code.setPlaceholderText("Generated worker code will appear here after authorization or clicking 'Generate GoIndex Worker Code'...")

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
        layout.addWidget(header)
        layout.addWidget(subheader)
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

        header = QLabel("Google Drive & Worker Deployment Guide")
        header.setObjectName("HeaderLabel")

        guide_text = QTextEdit()
        guide_text.setReadOnly(True)
        guide_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #334155;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 12px;
            }
        """)

        guide_content = """
        <h2>Why is local auth needed?</h2>
        <p>Google deprecated Out-Of-Band (OOB) OAuth flow (<code>urn:ietf:wg:oauth:2.0:oob</code>), preventing remote environments from pasting an auth code directly.</p>
        <p>This desktop application runs <b>Rclone</b> locally on your computer to open a local web server (<code>http://127.0.0.1:53682/</code>), allowing you to safely authenticate with Google and automatically capture your <b>Refresh Token</b>.</p>

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;">

        <h3>Step-by-Step Setup:</h3>
        <ol>
            <li><b>Create Google Credentials:</b>
                <ul>
                    <li>Go to the <a style="color: #2563eb;" href="https://console.cloud.google.com/">Google Cloud Console</a>.</li>
                    <li>Create a project and enable the <b>Google Drive API</b>.</li>
                    <li>Go to <b>Credentials</b> &rarr; <b>Create Credentials</b> &rarr; <b>OAuth Client ID</b>.</li>
                    <li>Select Application type: <b>Desktop App</b>.</li>
                    <li>Copy your <b>Client ID</b> and <b>Client Secret</b> into this app.</li>
                </ul>
            </li>
            <br>
            <li><b>Perform Local OAuth:</b>
                <ul>
                    <li>Click <b>Start Local OAuth Authorization</b>.</li>
                    <li>Your default browser will open automatically for Google login.</li>
                    <li>Grant permissions and return here—your <b>Refresh Token</b> and <b>Worker Code</b> will generate automatically!</li>
                </ul>
            </li>
            <br>
            <li><b>Deploy to Cloudflare Workers:</b>
                <ul>
                    <li>Go to the <a style="color: #2563eb;" href="https://dash.cloudflare.com/">Cloudflare Dashboard</a> &rarr; <b>Workers & Pages</b>.</li>
                    <li>Create a new Worker script.</li>
                    <li>Click <b>Copy Worker Code</b> or <b>Download index.js</b> in this app.</li>
                    <li>Paste the code into the Cloudflare Worker editor and click <b>Save and Deploy</b>!</li>
                </ul>
            </li>
        </ol>
        """
        guide_text.setHtml(guide_content)

        layout.addWidget(header)
        layout.addWidget(guide_text)

        return page

    # --- HELPER METHODS ---
    def find_rclone(self):
        rclone_name = "rclone.exe" if platform.system().lower() == "windows" else "rclone"
        
        # 1. Check parent folder first
        parent_path = os.path.abspath(os.path.join("..", rclone_name))
        if os.path.exists(parent_path):
            return parent_path

        # 2. Check current folder
        current_path = os.path.abspath(os.path.join(".", rclone_name))
        if os.path.exists(current_path):
            return current_path

        # 3. Check system PATH
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

    def on_download_finished(self, path):
        self.rclone_bin = path
        self.progress_bar.setVisible(False)
        self.lbl_rclone_status.setText(f"Status: Rclone Ready ({path})")
        self.lbl_rclone_status.setStyleSheet("color: #16a34a; font-weight: bold;")
        self.txt_output.append(f"Rclone downloaded successfully to:\n{path}\n")

    def on_download_error(self, err):
        self.progress_bar.setVisible(False)
        self.lbl_rclone_status.setText("Status: Automatic Download Failed")
        self.lbl_rclone_status.setStyleSheet("color: #dc2626; font-weight: bold;")
        QMessageBox.critical(self, "Error", f"Failed to download Rclone automatically:\n{err}")

    def start_auth(self):
        client_id = self.txt_client_id.text().strip()
        client_secret = self.txt_client_secret.text().strip()

        if not client_id or not client_secret:
            QMessageBox.warning(self, "Input Error", "Please provide both Client ID and Client Secret.")
            return

        rclone_path = self.find_rclone()
        if not rclone_path and not os.path.exists(self.rclone_bin):
            QMessageBox.warning(self, "Rclone Missing", "Rclone binary is not available yet. Please wait for the automatic download to finish.")
            return

        active_rclone = rclone_path if rclone_path else self.rclone_bin

        self.btn_authorize.setEnabled(False)
        self.txt_output.setText("Starting Rclone auth server...\nYour default browser should open shortly.")

        self.auth_worker = AuthWorker(active_rclone, client_id, client_secret)
        self.auth_worker.finished.connect(self.on_auth_finished)
        self.auth_worker.error.connect(self.on_auth_error)
        self.auth_worker.start()

    def on_auth_finished(self, output):
        self.btn_authorize.setEnabled(True)
        self.txt_output.setText(output)

        extracted_token = ""
        try:
            if "{" in output and "}" in output:
                json_str = output[output.find("{"):output.rfind("}")+1]
                data = json.loads(json_str)
                extracted_token = data.get("refresh_token", "")
        except Exception:
            pass

        if extracted_token:
            self.txt_refresh_token.setText(extracted_token)
            self.txt_output.append(f"\n--- EXTRACTED REFRESH TOKEN ---\n{extracted_token}\n")
            self.generate_worker_code()
            QMessageBox.information(self, "Success", "Authorization completed successfully!\nRefresh Token extracted and Worker Code generated.")
        else:
            QMessageBox.warning(self, "Auth Output", "Authorization completed, but refresh_token could not be parsed automatically. If output contains a token, copy it into the Refresh Token field manually.")

    def on_auth_error(self, err):
        self.btn_authorize.setEnabled(True)
        self.txt_output.setText(f"Error:\n{err}")
        QMessageBox.critical(self, "Authorization Error", f"Failed to authorize:\n{err}")

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
        site_name = self.txt_site_name.text().strip() or "GoIndex Extended by Cheems"
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
            QMessageBox.warning(self, "Missing Refresh Token", "Please start local authorization first to generate a refresh token, or enter one manually.")
            return

        template_content = self.load_template()
        if not template_content:
            QMessageBox.critical(self, "Error", "Could not load GoIndex template file.")
            return

        replacements = {
            "{cheems_site_name}": site_name,
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RcloneConfiguratorApp()
    window.show()
    sys.exit(app.exec())