import os
import sys
import configparser
import subprocess
import re
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, QProgressBar, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette


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
                import json
                video_info = json.loads(output)
                self.analysis_finished.emit(video_info)
            else:
                self.analysis_finished.emit({"error": f"分析失败，返回码: {process.returncode}"})
                
        except Exception as e:
            self.analysis_finished.emit({"error": f"分析出错: {str(e)}"})


class DownloadWorker(QThread):
    progress_updated = pyqtSignal(str)
    progress_changed = pyqtSignal(int)
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
                format_parts = []
                if hasattr(self, 'video_quality') and self.video_quality:
                    if isinstance(self.video_quality, dict) and 'format_id' in self.video_quality:
                        format_parts.append(self.video_quality['format_id'])
                    else:
                        # 向后兼容，处理旧的字符串格式
                        if self.video_quality == "最高质量":
                            format_parts.append('bv*+ba/b')
                        elif self.video_quality == "中等质量":
                            format_parts.append('bv*[height<=720]+ba/b')
                        elif self.video_quality == "低质量":
                            format_parts.append('bv*[height<=480]+ba/b')
                        else:
                            format_parts.append(self.video_quality)
                else:
                    format_parts.append('bv*+ba/b')
                cmd.extend(['-f', '+'.join(format_parts)])
            else:  # 全部下载
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


class CommonFunctions:
    @staticmethod
    def load_config(config_file, widgets):
        if os.path.exists(config_file):
            try:
                config = configparser.ConfigParser()
                # 设置编码为utf-8以正确处理中文字符
                config.read(config_file, encoding='utf-8')
                
                if 'Settings' in config:
                    settings = config['Settings']
                    for widget_name, widget in widgets.items():
                        if widget_name in settings:
                            value = settings[widget_name]
                            if isinstance(widget, QLineEdit):
                                widget.setText(value)
                            elif isinstance(widget, QComboBox):
                                index = widget.findText(value)
                                if index >= 0:
                                    widget.setCurrentIndex(index)
                            elif isinstance(widget, QCheckBox):
                                widget.setChecked(value.lower() == 'true')
                            elif isinstance(widget, QSlider):
                                widget.setValue(int(value))
                
                return True, "配置已加载"
            except Exception as e:
                return False, f"加载配置失败: {str(e)}"
        return False, "配置文件不存在"
    
    @staticmethod
    def save_config(config_file, widgets):
        try:
            config = configparser.ConfigParser()
            config['Settings'] = {}
            
            for widget_name, widget in widgets.items():
                if isinstance(widget, QLineEdit):
                    config['Settings'][widget_name] = widget.text().strip()
                elif isinstance(widget, QComboBox):
                    config['Settings'][widget_name] = widget.currentText()
                elif isinstance(widget, QCheckBox):
                    config['Settings'][widget_name] = str(widget.isChecked())
                elif isinstance(widget, QSlider):
                    config['Settings'][widget_name] = str(widget.value())
            
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            
            return True, "配置已保存"
        except Exception as e:
            return False, f"保存配置失败: {str(e)}"
    
    @staticmethod
    def apply_styles(widget):
        widget.setStyleSheet(""".QGroupBox {
    border: 1px solid #ccc;
    border-radius: 8px;
    margin-top: 10px;
    padding: 10px;
}

.QGroupBox::title {
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

QPushButton#downloadBtn {
    background-color: #0078d4;
    color: white;
    font-weight: bold;
    padding: 10px 20px;
    border: none;
}

QPushButton#downloadBtn:hover {
    background-color: #0066b4;
}

QPushButton#downloadBtn:pressed {
    background-color: #005a9e;
}

QPushButton#saveConfigBtn {
    background-color: #f5f5f5;
    border: 1px solid #d0d0d0;
}

QPushButton#saveConfigBtn:hover {
    background-color: #e0e0e0;
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
    
    @staticmethod
    def log_message(text_edit, message):
        text_edit.append(message)
        text_edit.verticalScrollBar().setValue(
            text_edit.verticalScrollBar().maximum()
        )
    
    @staticmethod
    def update_progress_bar(progress_bar, value):
        # 更新进度条的值
        progress_bar.setValue(value)
        progress_bar.setFormat(f"下载进度: {value}%")
        
        # 如果进度达到100%，设置为确定状态
        if value >= 100:
            progress_bar.setRange(0, 100)
            progress_bar.setValue(100)
            progress_bar.setFormat("下载完成: 100%")
    
    @staticmethod
    def browse_file(title, file_filter):
        file_path, _ = QFileDialog.getOpenFileName(
            None, title, "", file_filter
        )
        return file_path
    
    @staticmethod
    def browse_directory(title):
        directory = QFileDialog.getExistingDirectory(None, title)
        return directory
    
    @staticmethod
    def show_message(title, message, icon=QMessageBox.Information):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.exec_()
    
    @staticmethod
    def apply_windows_style(app):
        # 设置应用程序字体
        try:
            font = QFont("Segoe UI", 9)
            app.setFont(font)
        except Exception as e:
            print(f"设置字体时出现错误: {e}")
        
        # 应用样式
        app.setStyle('Fusion')
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        app.setPalette(palette)