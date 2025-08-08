"""\u5de5\u5177\u51fd\u6570\u6587\u4ef6\uff0c\u5305\u542b\u5404\u79cd\u516c\u5171\u7684\u5de5\u5177\u51fd\u6570\u548c\u7c7b
"""
import os
import configparser
import subprocess
import re
import json
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, QProgressBar, QTextEdit, 
                             QLineEdit, QComboBox, QCheckBox, QSlider)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

class WorkerBase(QThread):
    """\u5de5\u4f5c\u7ebf\u7a0b\u57fa\u7c7b\uff0c\u63d0\u4f9b\u516c\u5171\u7684\u9519\u8bef\u5904\u7406\u65b9\u6cd5
    """
    error_occurred = pyqtSignal(str)
    
    def handle_error(self, error_msg):
        """\u5904\u7406\u9519\u8bef\u5e76\u53d1\u9001\u4fe1\u53f7
        """
        self.error_occurred.emit(error_msg)


class AnalyzeWorker(WorkerBase):
    """\u89c6\u9891\u5206\u6790\u5de5\u4f5c\u7ebf\u7a0b
    """
    analysis_finished = pyqtSignal(dict)
    
    def __init__(self, ytdlp_path, url):
        super().__init__()
        self.ytdlp_path = ytdlp_path
        self.url = url
    
    def run(self):
        try:
            # \u6784\u5efayt-dlp\u547d\u4ee4\u83b7\u53d6\u89c6\u9891\u4fe1\u606f
            cmd = [self.ytdlp_path, self.url, '--dump-json']
            
            # \u6267\u884c\u547d\u4ee4
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
                # \u89e3\u6790JSON\u8f93\u51fa
                video_info = json.loads(output)
                self.analysis_finished.emit(video_info)
            else:
                self.handle_error(f"\u5206\u6790\u5931\u8d25\uff0c\u8fd4\u56de\u7801: {process.returncode}")
                
        except Exception as e:
            self.handle_error(f"\u5206\u6790\u51fa\u9519: {str(e)}")


class DownloadWorker(WorkerBase):
    """\u4e0b\u8f7d\u5de5\u4f5c\u7ebf\u7a0b
    """
    progress_updated = pyqtSignal(str)
    progress_changed = pyqtSignal(int)
    download_finished = pyqtSignal(bool, str)
    
    def __init__(self, ytdlp_path, url, download_type, output_path, cookie_path=None, 
                 audio_quality=None, video_quality=None, merge_output=None, thread_count=4):
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
            # \u6784\u5efayt-dlp\u547d\u4ee4
            cmd = [self.ytdlp_path, self.url]
            
            # \u6dfb\u52a0\u7ebf\u7a0b\u6570\u53c2\u6570
            cmd.extend(['--concurrent-fragments', str(self.thread_count)])
            
            # \u8bbe\u7f6e\u8f93\u51fa\u8def\u5f84
            if self.output_path:
                cmd.extend(['-o', os.path.join(self.output_path, '%(title)s.%(ext)s')])
            
            # \u6839\u636e\u4e0b\u8f7d\u7c7b\u578b\u8bbe\u7f6e\u53c2\u6570
            self._add_format_options(cmd)
            
            # \u6dfb\u52a0cookie\u6587\u4ef6\u53c2\u6570
            if self.cookie_path and os.path.exists(self.cookie_path):
                cmd.extend(['--cookies', self.cookie_path])
            
            # \u6dfb\u52a0\u8fdb\u5ea6\u94a9\u5b50
            cmd.extend(['--newline', '--no-check-certificate'])
            
            self.progress_updated.emit(f"\u6267\u884c\u547d\u4ee4: {' '.join(cmd)}")
            
            # \u6267\u884c\u547d\u4ee4
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # \u5b9e\u65f6\u8bfb\u53d6\u8f93\u51fa\u5e76\u89e3\u6790\u8fdb\u5ea6
            for line in process.stdout:
                line = line.strip()
                if line:
                    # \u5c1d\u8bd5\u89e3\u6790\u8fdb\u5ea6\u767e\u5206\u6bd4
                    if '[download]' in line and '%' in line:
                        # \u63d0\u53d6\u767e\u5206\u6bd4\u6570\u5b57
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
                self.download_finished.emit(True, "\u4e0b\u8f7d\u5b8c\u6210!")
            else:
                self.handle_error(f"\u4e0b\u8f7d\u5931\u8d25\uff0c\u8fd4\u56de\u7801: {process.returncode}")
        except Exception as e:
            self.handle_error(f"\u4e0b\u8f7d\u51fa\u9519: {str(e)}")
    
    def _add_format_options(self, cmd):
        """\u6839\u636e\u4e0b\u8f7d\u7c7b\u578b\u6dfb\u52a0\u683c\u5f0f\u53c2\u6570
        """
        if self.download_type == "\u4ec5\u97f3\u9891":
            cmd.extend(['-x', '--audio-format', 'mp3'])
        elif self.download_type == "\u4ec5\u89c6\u9891":
            # \u4f7f\u7528\u7528\u6237\u9009\u62e9\u7684\u5177\u4f53\u89c6\u9891\u683c\u5f0f
            format_id = self._get_format_id(self.video_quality)
            cmd.extend(['-f', format_id])
        else:  # \u5168\u90e8\u4e0b\u8f7d
            format_parts = []
            # \u6dfb\u52a0\u89c6\u9891\u683c\u5f0f
            video_format = self._get_format_id(self.video_quality, 'video')
            format_parts.append(video_format)
            
            # \u6dfb\u52a0\u97f3\u9891\u683c\u5f0f
            audio_format = self._get_format_id(self.audio_quality, 'audio')
            format_parts.append(audio_format)
            
            cmd.extend(['-f', ','.join(format_parts)])
    
    def _get_format_id(self, quality, format_type='video'):
        """\u83b7\u53d6\u683c\u5f0fID\uff0c\u652f\u6301\u5411\u540e\u517c\u5bb9
        """
        if isinstance(quality, dict) and 'format_id' in quality:
            return quality['format_id']
        elif isinstance(quality, str):
            # \u5411\u540e\u517c\u5bb9\uff0c\u5904\u7406\u65e7\u7684\u5b57\u7b26\u4e32\u683c\u5f0f
            if quality == "\u6700\u9ad8\u8d28\u91cf":
                return 'bv*+ba/b' if format_type == 'video' and self.download_type == "\u4ec5\u89c6\u9891" else 'bv*' if format_type == 'video' else 'ba'
            elif quality == "\u4e2d\u7b49\u8d28\u91cf":
                return 'bv*[height<=720]+ba/b' if format_type == 'video' and self.download_type == "\u4ec5\u89c6\u9891" else 'bv*[height<=720]' if format_type == 'video' else 'ba[abr<=128]'
            elif quality == "\u4f4e\u8d28\u91cf":
                return 'bv*[height<=480]+ba/b' if format_type == 'video' and self.download_type == "\u4ec5\u89c6\u9891" else 'bv*[height<=480]' if format_type == 'video' else 'ba[abr<=64]'
            else:
                return quality
        else:
            # \u9ed8\u8ba4\u503c
            return 'bv*+ba/b' if format_type == 'video' and self.download_type == "\u4ec5\u89c6\u9891" else 'bv*' if format_type == 'video' else 'ba'


class ConfigManager:
    """\u914d\u7f6e\u6587\u4ef6\u7ba1\u7406\u5668
    """
    @staticmethod
    def load_config(config_file, widgets):
        """\u52a0\u8f7d\u914d\u7f6e\u6587\u4ef6
        """
        if os.path.exists(config_file):
            try:
                config = configparser.ConfigParser()
                # \u8bbe\u7f6e\u7f16\u7801\u4e3autf-8\u4ee5\u6b63\u786e\u5904\u7406\u4e2d\u6587\u5b57\u7b26
                config.read(config_file, encoding='utf-8')
                
                if 'Settings' in config:
                    settings = config['Settings']
                    for widget_name, widget in widgets.items():
                        if widget_name in settings:
                            value = settings[widget_name]
                            ConfigManager._set_widget_value(widget, value)
                
                return True, "\u914d\u7f6e\u5df2\u52a0\u8f7d"
            except Exception as e:
                return False, f"\u52a0\u8f7d\u914d\u7f6e\u5931\u8d25: {str(e)}"
        return False, "\u914d\u7f6e\u6587\u4ef6\u4e0d\u5b58\u5728"
    
    @staticmethod
    def save_config(config_file, widgets):
        """\u4fdd\u5b58\u914d\u7f6e\u6587\u4ef6
        """
        try:
            config = configparser.ConfigParser()
            config['Settings'] = {}
            
            for widget_name, widget in widgets.items():
                value = ConfigManager._get_widget_value(widget)
                if value is not None:
                    config['Settings'][widget_name] = str(value)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            
            return True, "\u914d\u7f6e\u5df2\u4fdd\u5b58"
        except Exception as e:
            return False, f"\u4fdd\u5b58\u914d\u7f6e\u5931\u8d25: {str(e)}"
    
    @staticmethod
    def _set_widget_value(widget, value):
        """\u6839\u636e\u63a7\u4ef6\u7c7b\u578b\u8bbe\u7f6e\u503c
        """
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
    
    @staticmethod
    def _get_widget_value(widget):
        """\u6839\u636e\u63a7\u4ef6\u7c7b\u578b\u83b7\u53d6\u503c
        """
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, QCheckBox):
            return str(widget.isChecked())
        elif isinstance(widget, QSlider):
            return str(widget.value())
        return None

class UIManager:
    """\u754c\u9762\u7ba1\u7406\u5668
    """
    @staticmethod
    def apply_styles(widget):
        """\u5e94\u7528\u6837\u5f0f\u8868
        """
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
        """\u5728\u6587\u672c\u6846\u4e2d\u6dfb\u52a0\u6d88\u606f\u5e76\u6eda\u52a8\u5230\u6700\u540e
        """
        text_edit.append(message)
        text_edit.verticalScrollBar().setValue(
            text_edit.verticalScrollBar().maximum()
        )
    
    @staticmethod
    def update_progress_bar(progress_bar, value):
        """\u66f4\u65b0\u8fdb\u5ea6\u6761
        """
        # \u66f4\u65b0\u8fdb\u5ea6\u6761\u7684\u503c
        progress_bar.setValue(value)
        progress_bar.setFormat(f"\u4e0b\u8f7d\u8fdb\u5ea6: {value}%")
        
        # \u5982\u679c\u8fdb\u5ea6\u8fbe\u5230100%\uff0c\u8bbe\u7f6e\u4e3a\u786e\u5b9a\u72b6\u6001
        if value >= 100:
            progress_bar.setRange(0, 100)
            progress_bar.setValue(100)
            progress_bar.setFormat("\u4e0b\u8f7d\u5b8c\u6210: 100%")
    
    @staticmethod
    def browse_file(title, file_filter):
        """\u6587\u4ef6\u9009\u62e9\u5bf9\u8bdd\u6846
        """
        file_path, _ = QFileDialog.getOpenFileName(
            None, title, "", file_filter
        )
        return file_path
    
    @staticmethod
    def browse_directory(title):
        """\u76ee\u5f55\u9009\u62e9\u5bf9\u8bdd\u6846
        """
        directory = QFileDialog.getExistingDirectory(None, title)
        return directory
    
    @staticmethod
    def show_message(title, message, icon=QMessageBox.Information):
        """\u663e\u793a\u6d88\u606f\u5bf9\u8bdd\u6846
        """
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.exec_()
    
    @staticmethod
    def apply_windows_style(app):
        """\u5e94\u7528Windows\u6837\u5f0f
        """
        # \u8bbe\u7f6e\u5e94\u7528\u7a0b\u5e8f\u5b57\u4f53
        try:
            font = QFont("Segoe UI", 9)
            app.setFont(font)
        except Exception as e:
            print(f"\u8bbe\u7f6e\u5b57\u4f53\u65f6\u51fa\u73b0\u9519\u8bef: {e}")
        
        # \u5e94\u7528\u6837\u5f0f
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