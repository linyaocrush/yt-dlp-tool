import sys
sys.dont_write_bytecode = True
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, 
                             QTextEdit, QFileDialog, QMessageBox, QGroupBox, QProgressBar, QSlider, QStackedWidget)
from views.single_downloader import SingleDownloader
from views.playlist_downloader import PlaylistDownloader
from views.settings import SettingsView
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
from utils import AnalyzeWorker, DownloadWorker

class YTDLPGUI(QMainWindow):
    cookie_updated = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        self.playlist_window = None
        self.analyze_worker = None
        self.worker = None
        self.config = {}
        self.cookie_files = []
        self.init_ui()
        self.apply_styles()

    def closeEvent(self, event):
        # 终止所有运行中的工作线程
        if self.analyze_worker and self.analyze_worker.isRunning():
            self.analyze_worker.terminate()
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
        event.accept()
        
        # 移除对已移动控件的引用
    pass
    
    def init_ui(self):
        self.setWindowTitle("YT-DLP 下载工具")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建页面容器
        self.stacked_widget = QStackedWidget()
        self.single_downloader = SingleDownloader(self)
        self.current_view = self.single_downloader  # 设置当前视图为单文件下载器
        self.playlist_downloader = PlaylistDownloader(self)
        self.settings_view = SettingsView(self)

        # 添加页面到容器
        self.stacked_widget.addWidget(self.single_downloader)
        self.stacked_widget.addWidget(self.playlist_downloader)
        self.stacked_widget.addWidget(self.settings_view)

        # 页面切换控制
        page_control_layout = QHBoxLayout()
        page_control_layout.setSpacing(10)
        page_control_layout.addStretch()

        self.single_btn = QPushButton("单个视频下载")
        self.single_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        page_control_layout.addWidget(self.single_btn)

        self.playlist_btn = QPushButton("播放列表下载")
        self.playlist_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        page_control_layout.addWidget(self.playlist_btn)

        self.settings_btn = QPushButton("设置")
        self.settings_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        page_control_layout.addWidget(self.settings_btn)

        main_layout.addLayout(page_control_layout)
        main_layout.addWidget(self.stacked_widget)
        

        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def update_config(self, config):
        self.config = config
        self.cookie_files = config.get('cookie_files', [])
        self.cookie_updated.emit(self.cookie_files)
        # 更新所有视图的配置
        if hasattr(self, 'single_downloader'):
            self.single_downloader.update_config(config)
        if hasattr(self, 'playlist_downloader'):
            self.playlist_downloader.update_config(config)

    def apply_styles(self):
        # 应用现代化样式表
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #202020;
            }
            
            QLabel {
                color: #333333;
                font-size: 10pt;
            }
            
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-size: 10pt;
                background-color: #ffffff;
            }
            
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
            
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 10pt;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-size: 10pt;
                background-color: white;
                min-width: 400px;
                width: fit-content;
            }
            
            QComboBox::drop-down {
                border: none;
                border-radius: 6px;
            }
            
            QCheckBox {
                spacing: 5px;
                font-size: 10pt;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 1px solid #888;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                border: 1px solid #0078d4;
                border-radius: 3px;
                background-color: #0078d4;
            }
            
            QCheckBox::indicator:checked:pressed {
                background-color: #005a9e;
            }
            
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                font-family: Consolas, monospace;
                font-size: 9pt;
                background-color: #ffffff;
            }
            
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 6px;
                text-align: center;
                font-size: 9pt;
                height: 20px;
            }
            
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 5px;
            }
        """)
    
    
    def open_playlist_downloader(self):
        self.stacked_widget.setCurrentIndex(1)

def main():
    try:
        app = QApplication(sys.argv)
        
        # 设置应用程序字体
        try:
            font = QFont("sans-serif", 9)
            app.setFont(font)
        except Exception as e:
            print(f"设置字体时出现错误: {e}")
        
        window = YTDLPGUI()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        import traceback
        error_msg = f"程序出现未捕获的异常:\n{str(e)}\n\n详细信息:\n{traceback.format_exc()}"
        print(error_msg)
        # 尝试显示错误对话框
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "严重错误", error_msg)
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()