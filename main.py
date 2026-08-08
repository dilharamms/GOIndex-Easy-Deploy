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
    QListWidget, QFrame, QMessageBox, QProgressBar
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
QLabel {
    font-size: 13px;
    color: #334155;
}
QLabel#HeaderLabel {
    font-size: 20px;
    font-weight: bold;
    color: #0f172a;
    margin-bottom: 5px;
}
QLabel#SubHeaderLabel {
    font-size: 13px;
    color: #64748b;
    margin-bottom: 15px;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 10px 12px;
    color: #0f172a;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #2563eb;
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
            arch = platform.machine().lower()
            
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
        self.setWindowTitle("Rclone Google Drive Configurator")
        self.resize(850, 580)
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
        self.sidebar.addItem("Setup & Config")
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
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(12)

        header = QLabel("Google Drive Configurator")
        header.setObjectName("HeaderLabel")
        subheader = QLabel("Execute local OAuth authorization and obtain your Google Drive refresh token.")
        subheader.setObjectName("SubHeaderLabel")

        # Rclone Status
        rclone_layout = QHBoxLayout()
        self.lbl_rclone_status = QLabel("Checking Rclone binary...")
        rclone_layout.addWidget(self.lbl_rclone_status)
        rclone_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # Form Inputs
        self.txt_client_id = QLineEdit()
        self.txt_client_id.setPlaceholderText("Enter Client ID (e.g., 202264815644-...apps.googleusercontent.com)")

        self.txt_client_secret = QLineEdit()
        self.txt_client_secret.setPlaceholderText("Enter Client Secret")
        self.txt_client_secret.setEchoMode(QLineEdit.Password)

        # Action Button
        self.btn_authorize = QPushButton("Start Local OAuth Authorization")
        self.btn_authorize.clicked.connect(self.start_auth)

        # Console Output
        lbl_output = QLabel("Authorization Output & Tokens:")
        lbl_output.setStyleSheet("font-weight: bold; margin-top: 10px; color: #0f172a;")
        
        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setPlaceholderText("Output and token JSON will appear here after authentication...")

        # Assembly
        layout.addWidget(header)
        layout.addWidget(subheader)
        layout.addLayout(rclone_layout)
        layout.addWidget(self.progress_bar)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e2e8f0; border: none; min-height: 1px; max-height: 1px;")
        layout.addWidget(line)

        layout.addWidget(QLabel("Client ID:"))
        layout.addWidget(self.txt_client_id)
        layout.addWidget(QLabel("Client Secret:"))
        layout.addWidget(self.txt_client_secret)
        layout.addWidget(self.btn_authorize)
        layout.addWidget(lbl_output)
        layout.addWidget(self.txt_output)

        self.check_local_rclone()

        return page

    # --- PAGE 2: GUIDE PAGE ---
    def create_guide_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        header = QLabel("Google Drive API Guide")
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
                padding: 10px;
            }
        """)

        guide_content = """
        <h2>Why is this tool needed?</h2>
        <p>Google has deprecated the Out-Of-Band (OOB) OAuth flow (<code>urn:ietf:wg:oauth:2.0:oob</code>). Remote environments like Google Colab can no longer display a code to copy manually.</p>
        <p>This desktop application runs <b>Rclone</b> locally on your computer to open a local web server (e.g., <code>http://127.0.0.1:53682/</code>), allowing you to sign in with Google safely and generate a <b>Refresh Token</b>.</p>

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;">

        <h3>Step-by-Step Setup:</h3>
        <ol>
            <li><b>Create Google Credentials:</b>
                <ul>
                    <li>Go to the <a style="color: #2563eb;" href="https://console.cloud.google.com/">Google Cloud Console</a>.</li>
                    <li>Create a project and enable the <b>Google Drive API</b>.</li>
                    <li>Go to <b>Credentials</b> &rarr; <b>Create Credentials</b> &rarr; <b>OAuth Client ID</b>.</li>
                    <li>Select Application type: <b>Desktop App</b>.</li>
                    <li>Copy your <b>Client ID</b> and <b>Client Secret</b>.</li>
                </ul>
            </li>
            <br>
            <li><b>Run Authorization:</b>
                <ul>
                    <li>Paste your Client ID and Client Secret in the <i>Setup & Config</i> tab.</li>
                    <li>Click <b>Start Local OAuth Authorization</b>.</li>
                    <li>Your browser will open automatically asking you to log into Google.</li>
                    <li>Grant permissions and return to this app to copy the resulting token block.</li>
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
            self.lbl_rclone_status.setText("Status: Rclone not found in parent/local folder. Downloading automatically...")
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

        # Attempt to parse refresh token from output JSON
        try:
            if "{" in output and "}" in output:
                json_str = output[output.find("{"):output.rfind("}")+1]
                data = json.loads(json_str)
                refresh_token = data.get("refresh_token", "")
                if refresh_token:
                    self.txt_output.append(f"\n--- EXTRACTED REFRESH TOKEN ---\n{refresh_token}")
        except Exception:
            pass

        QMessageBox.information(self, "Success", "Authorization completed successfully!")

    def on_auth_error(self, err):
        self.btn_authorize.setEnabled(True)
        self.txt_output.setText(f"Error:\n{err}")
        QMessageBox.critical(self, "Authorization Error", f"Failed to authorize:\n{err}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RcloneConfiguratorApp()
    window.show()
    sys.exit(app.exec())