import sys
sys.dont_write_bytecode = True
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, 
                             QTextEdit, QFileDialog, QMessageBox, QGroupBox, QProgressBar, QSlider, QStackedWidget)
from views.single_downloader import SingleDownloader
from views.playlist_downloader import PlaylistDownloader
from views.settings import SettingsView
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
import json

class AnalyzeWorker(QThread):
    analysis_finished = pyqtSignal(dict)
    
    def __init__(self, ytdlp_path, url):
        super().__init__()
        self.ytdlp_path = ytdlp_path
        self.url = url
    
    def run(self):
        try:
            # 构建yt-dlp命令获取视频信息
            cmd = [self.ytdlp_path, self.url, '--dump-json']
            
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            output, _ = process.communicate()
            
            if process.returncode == 0:
                # 解析JSON输出
                video_info = json.loads(output)
                self.analysis_finished.emit(video_info)
            else:
                self.analysis_finished.emit({"error": f"分析失败，返回码: {process.returncode}"})
                
        except Exception as e:
            self.analysis_finished.emit({"error": f"分析出错: {str(e)}"})

class DownloadWorker(QThread):
    progress_updated = pyqtSignal(str)
    progress_changed = pyqtSignal(int)  # 新增进度变化信号
    download_finished = pyqtSignal(bool, str)
    
    def __init__(self, ytdlp_path, url, download_type, output_path, cookie_path=None, audio_quality=None, video_quality=None, merge_output=None, thread_count=4):
        super().__init__()
        self.ytdlp_path = ytdlp_path
        self.url = url
        self.download_type = download_type
        self.output_path = output_path
        self.cookie_path = cookie_path
        self.audio_quality = audio_quality
        self.video_quality = video_quality
        self.merge_output = merge_output
        self.thread_count = thread_count
    
    def run(self):
        try:
            # 构建yt-dlp命令
            cmd = [self.ytdlp_path, self.url]
            
            # 添加线程数参数
            cmd.extend(['--concurrent-fragments', str(self.thread_count)])
            
            # 设置输出路径
            if self.output_path:
                cmd.extend(['-o', os.path.join(self.output_path, '%(title)s.%(ext)s')])
            
            # 根据下载类型设置参数
            if self.download_type == "仅音频":
                cmd.extend(['-x', '--audio-format', 'mp3'])
            elif self.download_type == "仅视频":
                # 使用用户选择的具体视频格式
                if hasattr(self, 'video_quality') and self.video_quality:
                    # 如果video_quality是字典（包含格式信息），则使用format_id
                    if isinstance(self.video_quality, dict) and 'format_id' in self.video_quality:
                        cmd.extend(['-f', self.video_quality['format_id']])
                    else:
                        # 向后兼容，处理旧的字符串格式
                        if self.video_quality == "最高质量":
                            cmd.extend(['-f', 'bv*+ba/b'])
                        elif self.video_quality == "中等质量":
                            cmd.extend(['-f', 'bv*[height<=720]+ba/b'])
                        elif self.video_quality == "低质量":
                            cmd.extend(['-f', 'bv*[height<=480]+ba/b'])
                        else:
                            cmd.extend(['-f', self.video_quality])
                else:
                    cmd.extend(['-f', 'bv*+ba/b'])
            elif self.download_type == "全部下载":
                # 根据是否合并选择不同的参数
                if hasattr(self, 'merge_output') and self.merge_output:
                    # 合并音视频
                    if hasattr(self, 'video_quality') and self.video_quality:
                        # 如果video_quality是字典（包含格式信息），则使用format_id
                        if isinstance(self.video_quality, dict) and 'format_id' in self.video_quality:
                            cmd.extend(['-f', self.video_quality['format_id']])
                        else:
                            # 向后兼容，处理旧的字符串格式
                            if self.video_quality == "最高质量":
                                cmd.extend(['-f', 'bv*+ba/b'])
                            elif self.video_quality == "中等质量":
                                cmd.extend(['-f', 'bv*[height<=720]+ba/b'])
                            elif self.video_quality == "低质量":
                                cmd.extend(['-f', 'bv*[height<=480]+ba/b'])
                            else:
                                cmd.extend(['-f', self.video_quality])
                    else:
                        cmd.extend(['-f', 'bv*+ba/b'])
                    cmd.extend(['--merge-output-format', 'mp4'])
                else:
                    # 分别下载音视频
                    format_parts = []
                    
                    # 添加视频格式
                    if hasattr(self, 'video_quality') and self.video_quality:
                        if isinstance(self.video_quality, dict) and 'format_id' in self.video_quality:
                            format_parts.append(self.video_quality['format_id'])
                        else:
                            # 向后兼容，处理旧的字符串格式
                            if self.video_quality == "最高质量":
                                format_parts.append('bv*')
                            elif self.video_quality == "中等质量":
                                format_parts.append('bv*[height<=720]')
                            elif self.video_quality == "低质量":
                                format_parts.append('bv*[height<=480]')
                            else:
                                format_parts.append(self.video_quality)
                    else:
                        format_parts.append('bv*')
                    
                    # 添加音频格式
                    if hasattr(self, 'audio_quality') and self.audio_quality:
                        if isinstance(self.audio_quality, dict) and 'format_id' in self.audio_quality:
                            format_parts.append(self.audio_quality['format_id'])
                        else:
                            # 向后兼容，处理旧的字符串格式
                            if self.audio_quality == "最高质量":
                                format_parts.append('ba')
                            elif self.audio_quality == "中等质量":
                                format_parts.append('ba[abr<=128]')
                            elif self.audio_quality == "低质量":
                                format_parts.append('ba[abr<=64]')
                            else:
                                format_parts.append(self.audio_quality)
                    else:
                        format_parts.append('ba')
                    
                    cmd.extend(['-f', ','.join(format_parts)])
            
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
            
            # 实时读取输出并解析进度
            for line in process.stdout:
                line = line.strip()
                if line:
                    # 尝试解析进度百分比
                    if '[download]' in line and '%' in line:
                        # 提取百分比数字
                        import re
                        percent_match = re.search(r'\b(\d+(?:\.\d+)?)\s*%', line)
                        if percent_match:
                            try:
                                percent = float(percent_match.group(1))
                                self.progress_changed.emit(int(percent))
                            except ValueError:
                                pass
                    
                    self.progress_updated.emit(line)
            
            process.wait()
            
            if process.returncode == 0:
                self.download_finished.emit(True, "下载完成!")
            else:
                self.download_finished.emit(False, f"下载失败，返回码: {process.returncode}")
                
        except Exception as e:
            self.download_finished.emit(False, f"下载出错: {str(e)}")

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