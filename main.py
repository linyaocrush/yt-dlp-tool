import sys
import os
import configparser
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, 
                             QTextEdit, QFileDialog, QMessageBox, QGroupBox, QProgressBar)
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
    
    def __init__(self, ytdlp_path, url, download_type, output_path, cookie_path=None, audio_quality=None, video_quality=None, merge_output=None):
        super().__init__()
        self.ytdlp_path = ytdlp_path
        self.url = url
        self.download_type = download_type
        self.output_path = output_path
        self.cookie_path = cookie_path
        self.audio_quality = audio_quality
        self.video_quality = video_quality
        self.merge_output = merge_output
    
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
    def __init__(self):
        super().__init__()
        self.config_file = "ytdlp_config.ini"
        self.ytdlp_path = ""
        self.output_path = ""
        self.cookie_path = ""
        self.init_ui()
        self.load_config()
        self.apply_styles()
        
        # 初始化UI状态
        self.on_download_type_changed(self.download_type_combo.currentText())
    
    def init_ui(self):
        self.setWindowTitle("YT-DLP 下载工具")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # YT-DLP路径设置组
        ytdlp_group = QGroupBox("YT-DLP 设置")
        ytdlp_layout = QHBoxLayout()
        ytdlp_layout.setSpacing(10)
        
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
        download_layout.setSpacing(12)
        
        # URL输入
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("视频URL:"))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("请输入视频链接")
        url_layout.addWidget(self.url_edit)
        
        # 添加分析按钮
        self.analyze_btn = QPushButton("分析")
        self.analyze_btn.clicked.connect(self.analyze_video)
        url_layout.addWidget(self.analyze_btn)
        
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
        
        # Cookie使用选项
        cookie_option_layout = QHBoxLayout()
        self.use_cookie_checkbox = QCheckBox("使用Cookie文件")
        self.use_cookie_checkbox.setChecked(False)  # 默认不使用Cookie
        cookie_option_layout.addWidget(self.use_cookie_checkbox)
        cookie_option_layout.addStretch()
        download_layout.addLayout(cookie_option_layout)
        
        # 下载类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("下载类型:"))
        self.download_type_combo = QComboBox()
        self.download_type_combo.addItems(["仅音频", "仅视频", "全部下载"])
        type_layout.addWidget(self.download_type_combo)
        type_layout.addStretch()
        download_layout.addLayout(type_layout)
        
        # 连接下载类型选择变化信号
        self.download_type_combo.currentTextChanged.connect(self.on_download_type_changed)
        
        # 添加音频质量选择
        self.audio_quality_label = QLabel("音频质量:")
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(["最高质量", "中等质量", "低质量"])
        
        # 添加视频质量选择
        self.video_quality_label = QLabel("视频质量:")
        self.video_quality_combo = QComboBox()
        self.video_quality_combo.addItems(["最高质量", "中等质量", "低质量"])
        
        # 添加合成选项
        self.merge_checkbox = QCheckBox("下载后合成为一个视频")
        self.merge_checkbox.setChecked(True)  # 默认合并
        
        # 创建布局并添加UI元素
        # 音频质量布局
        audio_quality_layout = QHBoxLayout()
        audio_quality_layout.addWidget(self.audio_quality_label)
        audio_quality_layout.addWidget(self.audio_quality_combo)
        audio_quality_layout.addStretch()
        download_layout.addLayout(audio_quality_layout)
        
        # 视频质量布局
        video_quality_layout = QHBoxLayout()
        video_quality_layout.addWidget(self.video_quality_label)
        video_quality_layout.addWidget(self.video_quality_combo)
        video_quality_layout.addStretch()
        download_layout.addLayout(video_quality_layout)
        
        # 合成选项布局
        merge_option_layout = QHBoxLayout()
        merge_option_layout.addWidget(self.merge_checkbox)
        merge_option_layout.addStretch()
        download_layout.addLayout(merge_option_layout)
        
        # 初始隐藏音频质量选项
        self.audio_quality_label.setVisible(False)
        self.audio_quality_combo.setVisible(False)
        self.merge_checkbox.setVisible(False)  # 合并选项默认隐藏
        
        download_group.setLayout(download_layout)
        main_layout.addWidget(download_group)
        # 保存下载组引用以便后续使用
        self.download_group = download_group
        
        # 控制按钮
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setObjectName("downloadBtn")
        self.download_btn.clicked.connect(self.start_download)
        
        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.setObjectName("saveConfigBtn")
        self.save_config_btn.clicked.connect(self.save_config)
        
        control_layout.addWidget(self.download_btn)
        control_layout.addWidget(self.save_config_btn)
        control_layout.addStretch()
        
        # 清除Cookie按钮
        clear_cookie_btn = QPushButton("清除Cookie设置")
        clear_cookie_btn.setObjectName("saveConfigBtn")
        clear_cookie_btn.clicked.connect(self.clear_cookie)
        control_layout.addWidget(clear_cookie_btn)
        
        main_layout.addLayout(control_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFormat("下载进度: %p%")
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
    
    def analyze_video(self):
        self.ytdlp_path = self.ytdlp_path_edit.text().strip()
        url = self.url_edit.text().strip()
        
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
        
        # 禁用分析按钮
        self.analyze_btn.setEnabled(False)
        self.log_message("正在分析视频信息...")
        
        # 创建并启动分析线程
        self.analyze_worker = AnalyzeWorker(self.ytdlp_path, url)
        self.analyze_worker.analysis_finished.connect(self.on_analysis_finished)
        self.analyze_worker.start()
    
    def log_message(self, message):
        self.log_output.append(message)
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )
    
    def update_progress_bar(self, value):
        # 更新进度条的值
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"下载进度: {value}%")
        
        # 如果进度达到100%，设置为确定状态
        if value >= 100:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("下载完成: 100%")
    
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
        if self.use_cookie_checkbox.isChecked() and self.cookie_path and not os.path.exists(self.cookie_path):
            QMessageBox.warning(self, "警告", "Cookie文件不存在，请检查路径!")
            return
        
        # 禁用下载按钮，显示进度条
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)  # 设置进度条为确定状态
        self.progress_bar.setValue(0)  # 重置进度条
        
        # 清空日志
        self.log_output.clear()
        
        # 获取用户选择的格式
        audio_format_data = self.audio_quality_combo.currentData()
        video_format_data = self.video_quality_combo.currentData()
        merge_output = self.merge_checkbox.isChecked()
        
        # 创建并启动下载线程
        cookie_path = self.cookie_path if self.use_cookie_checkbox.isChecked() else None
        self.worker = DownloadWorker(
            self.ytdlp_path, url, download_type, self.output_path, cookie_path, audio_format_data, video_format_data, merge_output
        )
        self.worker.progress_updated.connect(self.log_message)
        self.worker.progress_changed.connect(self.update_progress_bar)  # 连接进度变化信号
        self.worker.download_finished.connect(self.on_download_finished)
        self.worker.start()
        
        self.statusBar().showMessage("正在下载...")
    
    def on_analysis_finished(self, video_info):
        # 恢复分析按钮状态
        self.analyze_btn.setEnabled(True)
        
        # 检查是否有错误
        if "error" in video_info:
            self.log_message(f"分析失败: {video_info['error']}")
            QMessageBox.critical(self, "错误", f"分析失败: {video_info['error']}")
            return
        
        # 更新日志
        self.log_message("视频分析完成")
        
        # 更新质量选择选项
        self.update_quality_options(video_info)
    
    def update_quality_options(self, video_info):
        # 清空现有的质量选项
        self.audio_quality_combo.clear()
        self.video_quality_combo.clear()
        
        # 获取可用的音频和视频格式
        formats = video_info.get("formats", [])
        
        # 分离音频和视频格式
        audio_formats = []
        video_formats = []
        
        for fmt in formats:
            # 检查是否为音频格式
            if fmt.get("vcodec") == "none":
                audio_formats.append(fmt)
            # 检查是否为视频格式
            elif fmt.get("acodec") == "none":
                video_formats.append(fmt)
        
        # 按比特率排序，处理None值
        audio_formats.sort(key=lambda x: x.get("abr", 0) or 0, reverse=True)
        video_formats.sort(key=lambda x: x.get("height", 0) or 0, reverse=True)
        
        # 添加音频质量选项
        for fmt in audio_formats:
            abr = fmt.get("abr", "Unknown")
            ext = fmt.get("ext", "Unknown")
            self.audio_quality_combo.addItem(f"音频: {abr}kbps ({ext})", fmt)
        
        # 去重视频格式
        seen_formats = {}
        unique_video_formats = []
        
        for fmt in video_formats:
            height = fmt.get("height", "Unknown")
            width = fmt.get("width", "Unknown")
            fps = fmt.get("fps", "Unknown")
            ext = fmt.get("ext", "Unknown")
            # 使用分辨率、帧率和扩展名作为唯一键
            key = (height, width, fps, ext)
            
            if key not in seen_formats:
                seen_formats[key] = True
                unique_video_formats.append(fmt)
        
        # 添加视频质量选项
        for fmt in unique_video_formats:
            height = fmt.get("height", "Unknown")
            width = fmt.get("width", "Unknown")
            fps = fmt.get("fps", "Unknown")
            ext = fmt.get("ext", "Unknown")
            vcodec = fmt.get("vcodec", "Unknown")
            format_id = fmt.get("format_id", "Unknown")
            self.video_quality_combo.addItem(f"视频: {width}x{height} {fps}fps ({ext}) [{vcodec}]", fmt)
        
        self.log_message(f"找到 {len(audio_formats)} 个音频格式和 {len(video_formats)} 个视频格式")
    
    def on_download_type_changed(self, text):
        # 根据下载类型显示或隐藏质量选项
        if text == "仅音频":
            # 显示音频质量选项，隐藏视频质量选项
            self.audio_quality_label.setVisible(True)
            self.audio_quality_combo.setVisible(True)
            self.video_quality_label.setVisible(False)
            self.video_quality_combo.setVisible(False)
            # 隐藏合并选项
            self.merge_checkbox.setVisible(False)
                
        elif text == "仅视频":
            # 显示视频质量选项，隐藏音频质量选项
            self.audio_quality_label.setVisible(False)
            self.audio_quality_combo.setVisible(False)
            self.video_quality_label.setVisible(True)
            self.video_quality_combo.setVisible(True)
            # 隐藏合并选项
            self.merge_checkbox.setVisible(False)
                
        elif text == "全部下载":
            # 显示音频和视频质量选项
            self.audio_quality_label.setVisible(True)
            self.audio_quality_combo.setVisible(True)
            self.video_quality_label.setVisible(True)
            self.video_quality_combo.setVisible(True)
            # 显示合并选项
            self.merge_checkbox.setVisible(True)
    
    def on_download_finished(self, success, message):
        # 恢复UI状态
        self.download_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)  # 重置进度条
        
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
            'download_type': self.download_type_combo.currentText(),
            'audio_quality': self.audio_quality_combo.currentText(),  # 保存音频质量设置
            'video_quality': self.video_quality_combo.currentText(),  # 保存视频质量设置
            'use_cookie': str(self.use_cookie_checkbox.isChecked()),
            'merge_output': str(self.merge_checkbox.isChecked())  # 保存合并选项
        }
        
        try:
            with open(self.config_file, 'w') as configfile:
                config.write(configfile)
            QMessageBox.information(self, "成功", "配置已保存!")
            self.statusBar().showMessage("配置已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
    
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
                    
                    download_type = settings.get('download_type', '全部下载')
                    index = self.download_type_combo.findText(download_type)
                    if index >= 0:
                        self.download_type_combo.setCurrentIndex(index)

                    audio_quality = settings.get('audio_quality', '最高质量')
                    index = self.audio_quality_combo.findText(audio_quality)
                    if index >= 0:
                        self.audio_quality_combo.setCurrentIndex(index)
                        
                    video_quality = settings.get('video_quality', '最高质量')
                    index = self.video_quality_combo.findText(video_quality)
                    if index >= 0:
                        self.video_quality_combo.setCurrentIndex(index)
                    
                    use_cookie = settings.get('use_cookie', 'False')
                    self.use_cookie_checkbox.setChecked(use_cookie.lower() == 'true')
                    
                    merge_output = settings.get('merge_output', 'True')
                    self.merge_checkbox.setChecked(merge_output.lower() == 'true')
                
                self.statusBar().showMessage("配置已加载")
            except Exception as e:
                self.statusBar().showMessage(f"加载配置失败: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序字体
    try:
        font = QFont("Segoe UI", 9)
        app.setFont(font)
    except Exception as e:
        print(f"设置字体时出现错误: {e}")
    
    window = YTDLPGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()