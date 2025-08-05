import sys
import os
import configparser
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, 
                             QTextEdit, QFileDialog, QMessageBox, QGroupBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class DownloadWorker(QThread):
    progress_updated = pyqtSignal(str)
    download_finished = pyqtSignal(bool, str)
    
    def __init__(self, ytdlp_path, url, download_type, output_path, cookie_path=None):
        super().__init__()
        self.ytdlp_path = ytdlp_path
        self.url = url
        self.download_type = download_type
        self.output_path = output_path
        self.cookie_path = cookie_path
    
    def run(self):
        try:
            # 构建yt-dlp命令
            cmd = [self.ytdlp_path, self.url]
            
            # 设置输出路径
            if self.output_path:
                cmd.extend(['-o', os.path.join(self.output_path, '%(title)s.%(ext)s')])
            
            # 根据下载类型设置参数
            if self.download_type == "仅音频":
                cmd.extend(['-x', '--audio-format', 'mp3'])
            elif self.download_type == "仅视频":
                cmd.extend(['-f', 'bv*+ba/b'])
            elif self.download_type == "全部合成":
                cmd.extend(['-f', 'bv*+ba/b', '--merge-output-format', 'mp4'])
            
            # 添加cookie文件参数
            if self.cookie_path and os.path.exists(self.cookie_path):
                cmd.extend(['--cookies', self.cookie_path])
            
            # 添加进度钩子
            cmd.extend(['--newline', '--no-check-certificate'])
            
            self.progress_updated.emit(f"执行命令: {' '.join(cmd)}")
            
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 实时读取输出
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.progress_updated.emit(line)
            
            process.wait()
            
            if process.returncode == 0:
                self.download_finished.emit(True, "下载完成!")
            else:
                self.download_finished.emit(False, f"下载失败，返回码: {process.returncode}")
                
        except Exception as e:
            self.download_finished.emit(False, f"下载出错: {str(e)}")

class YTDLPGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_file = "ytdlp_config.ini"
        self.ytdlp_path = ""
        self.output_path = ""
        self.cookie_path = ""
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        self.setWindowTitle("YT-DLP 下载工具")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # YT-DLP路径设置组
        ytdlp_group = QGroupBox("YT-DLP 设置")
        ytdlp_layout = QHBoxLayout()
        
        self.ytdlp_path_edit = QLineEdit()
        self.ytdlp_path_edit.setPlaceholderText("请输入 yt-dlp.exe 的路径")
        ytdlp_layout.addWidget(self.ytdlp_path_edit)
        
        browse_ytdlp_btn = QPushButton("浏览")
        browse_ytdlp_btn.clicked.connect(self.browse_ytdlp)
        ytdlp_layout.addWidget(browse_ytdlp_btn)
        
        ytdlp_group.setLayout(ytdlp_layout)
        main_layout.addWidget(ytdlp_group)
        
        # 下载设置组
        download_group = QGroupBox("下载设置")
        download_layout = QVBoxLayout()
        
        # URL输入
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("视频URL:"))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("请输入视频链接")
        url_layout.addWidget(self.url_edit)
        download_layout.addLayout(url_layout)
        
        # 输出路径
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("保存路径:"))
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("请选择下载保存路径")
        output_layout.addWidget(self.output_path_edit)
        
        browse_output_btn = QPushButton("浏览")
        browse_output_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(browse_output_btn)
        download_layout.addLayout(output_layout)
        
        # Cookie文件路径
        cookie_layout = QHBoxLayout()
        cookie_layout.addWidget(QLabel("Cookie文件:"))
        self.cookie_path_edit = QLineEdit()
        self.cookie_path_edit.setPlaceholderText("请选择cookie.txt文件路径")
        cookie_layout.addWidget(self.cookie_path_edit)
        
        browse_cookie_btn = QPushButton("浏览")
        browse_cookie_btn.clicked.connect(self.browse_cookie)
        cookie_layout.addWidget(browse_cookie_btn)
        download_layout.addLayout(cookie_layout)
        
        # 下载类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("下载类型:"))
        self.download_type_combo = QComboBox()
        self.download_type_combo.addItems(["仅音频", "仅视频", "全部合成"])
        type_layout.addWidget(self.download_type_combo)
        type_layout.addStretch()
        download_layout.addLayout(type_layout)
        
        download_group.setLayout(download_layout)
        main_layout.addWidget(download_group)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        self.download_btn = QPushButton("开始下载")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.clicked.connect(self.save_config)
        
        control_layout.addWidget(self.download_btn)
        control_layout.addWidget(self.save_config_btn)
        control_layout.addStretch()
        
        # 清除Cookie按钮
        clear_cookie_btn = QPushButton("清除Cookie设置")
        clear_cookie_btn.clicked.connect(self.clear_cookie)
        control_layout.addWidget(clear_cookie_btn)
        
        main_layout.addLayout(control_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 日志输出
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)
        main_layout.addWidget(self.log_output)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def browse_ytdlp(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 YT-DLP 程序", "", "Executable Files (*.exe);;All Files (*)"
        )
        if file_path:
            self.ytdlp_path_edit.setText(file_path)
    
    def browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if directory:
            self.output_path_edit.setText(directory)
    
    def browse_cookie(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Cookie文件", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.cookie_path_edit.setText(file_path)
    
    def clear_cookie(self):
        self.cookie_path_edit.clear()
        self.statusBar().showMessage("Cookie设置已清除")
    
    def log_message(self, message):
        self.log_output.append(message)
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )
    
    def start_download(self):
        self.ytdlp_path = self.ytdlp_path_edit.text().strip()
        url = self.url_edit.text().strip()
        self.output_path = self.output_path_edit.text().strip()
        self.cookie_path = self.cookie_path_edit.text().strip()
        download_type = self.download_type_combo.currentText()
        
        # 验证输入
        if not self.ytdlp_path:
            QMessageBox.warning(self, "警告", "请设置 YT-DLP 路径!")
            return
        
        if not os.path.exists(self.ytdlp_path):
            QMessageBox.warning(self, "警告", "YT-DLP 程序不存在，请检查路径!")
            return
        
        if not url:
            QMessageBox.warning(self, "警告", "请输入视频URL!")
            return
        
        # 验证Cookie文件是否存在
        if self.cookie_path and not os.path.exists(self.cookie_path):
            QMessageBox.warning(self, "警告", "Cookie文件不存在，请检查路径!")
            return
        
        # 禁用下载按钮，显示进度条
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # 清空日志
        self.log_output.clear()
        
        # 创建并启动下载线程
        self.worker = DownloadWorker(
            self.ytdlp_path, url, download_type, self.output_path, self.cookie_path
        )
        self.worker.progress_updated.connect(self.log_message)
        self.worker.download_finished.connect(self.on_download_finished)
        self.worker.start()
        
        self.statusBar().showMessage("正在下载...")
    
    def on_download_finished(self, success, message):
        # 恢复UI状态
        self.download_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        
        # 显示结果消息
        if success:
            self.statusBar().showMessage("下载完成!")
            QMessageBox.information(self, "成功", message)
        else:
            self.statusBar().showMessage("下载失败!")
            QMessageBox.critical(self, "错误", message)
    
    def save_config(self):
        config = configparser.ConfigParser()
        config['Settings'] = {
            'ytdlp_path': self.ytdlp_path_edit.text(),
            'output_path': self.output_path_edit.text(),
            'cookie_path': self.cookie_path_edit.text(),
            'download_type': self.download_type_combo.currentText()
        }
        
        try:
            with open(self.config_file, 'w') as configfile:
                config.write(configfile)
            QMessageBox.information(self, "成功", "配置已保存!")
            self.statusBar().showMessage("配置已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                config = configparser.ConfigParser()
                config.read(self.config_file)
                
                if 'Settings' in config:
                    settings = config['Settings']
                    self.ytdlp_path_edit.setText(settings.get('ytdlp_path', ''))
                    self.output_path_edit.setText(settings.get('output_path', ''))
                    self.cookie_path_edit.setText(settings.get('cookie_path', ''))
                    
                    download_type = settings.get('download_type', '全部合成')
                    index = self.download_type_combo.findText(download_type)
                    if index >= 0:
                        self.download_type_combo.setCurrentIndex(index)
                
                self.statusBar().showMessage("配置已加载")
            except Exception as e:
                self.statusBar().showMessage(f"加载配置失败: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = YTDLPGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()