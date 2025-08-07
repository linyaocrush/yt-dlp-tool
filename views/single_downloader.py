import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QSlider, QProgressBar, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt
from common import AnalyzeWorker, DownloadWorker, CommonFunctions

class SingleDownloader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.analyze_worker = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

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
        self.analyze_btn.setStyleSheet("background-color: #f0f0f0; border: 1px solid #d0d0d0; padding: 5px 10px;")
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
        browse_output_btn.setStyleSheet("background-color: #f0f0f0; border: 1px solid #d0d0d0; padding: 5px 10px;")
        browse_output_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(browse_output_btn)
        download_layout.addLayout(output_layout)

        # 下载类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("下载类型:"))
        self.download_type_combo = QComboBox()
        self.download_type_combo.addItems(["仅音频", "仅视频", "全部下载"])
        type_layout.addWidget(self.download_type_combo)
        type_layout.addStretch()
        download_layout.addLayout(type_layout)

        # Cookie设置
        cookie_layout = QHBoxLayout()
        self.use_cookie_checkbox = QCheckBox("使用Cookie")
        self.use_cookie_checkbox.stateChanged.connect(self.on_use_cookie_changed)
        cookie_layout.addWidget(self.use_cookie_checkbox)

        self.cookie_combo = QComboBox()
        # 从主窗口加载Cookie文件列表
        if hasattr(self.parent, 'cookie_files'):
            self.cookie_combo.addItems(self.parent.cookie_files)
        # 连接主窗口Cookie更新信号
        self.parent.cookie_updated.connect(self.update_cookie_combo)
        self.cookie_combo.setEnabled(False)
        cookie_layout.addWidget(self.cookie_combo)


        cookie_layout.addStretch()
        download_layout.addLayout(cookie_layout)

        # 线程数选择
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("线程数:"))
        self.thread_count_slider = QSlider(Qt.Horizontal)
        self.thread_count_slider.setMinimum(1)
        self.thread_count_slider.setMaximum(64)
        self.thread_count_slider.setValue(4)
        self.thread_count_slider.setTickPosition(QSlider.TicksBelow)
        self.thread_count_slider.setTickInterval(5)
        self.thread_count_slider.valueChanged.connect(self.on_thread_count_changed)

        self.thread_count_label = QLabel("4")
        self.thread_count_label.setFixedWidth(30)

        thread_layout.addWidget(self.thread_count_slider)
        thread_layout.addWidget(self.thread_count_label)
        thread_layout.addStretch()
        download_layout.addLayout(thread_layout)

        # 音频质量选择
        self.audio_quality_label = QLabel("音频质量:")
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(["最高质量", "中等质量", "低质量"])

        # 视频质量选择
        self.video_quality_label = QLabel("视频质量:")
        self.video_quality_combo = QComboBox()
        self.video_quality_combo.addItems(["最高质量", "中等质量", "低质量"])

        # 合成选项
        self.merge_checkbox = QCheckBox("下载后合成为一个视频")
        self.merge_checkbox.setChecked(True)

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

        download_group.setLayout(download_layout)
        main_layout.addWidget(download_group)

        # 控制按钮
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        self.download_btn = QPushButton("开始下载")
        self.download_btn.setObjectName("downloadBtn")
        self.download_btn.setStyleSheet("background-color: #f0f0f0; border: 1px solid #d0d0d0; padding: 5px 10px;")
        self.download_btn.clicked.connect(self.start_download)

        control_layout.addWidget(self.download_btn)
        control_layout.addStretch()

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

        # 初始隐藏音频质量选项
        self.audio_quality_label.setVisible(False)
        self.audio_quality_combo.setVisible(False)
        self.merge_checkbox.setVisible(False)
        self.cookie_paths = []  # 存储cookie文件路径

        # 连接下载类型选择变化信号
        self.download_type_combo.currentTextChanged.connect(self.on_download_type_changed)

    def on_thread_count_changed(self, value):
        self.thread_count_label.setText(str(value))

    def browse_output(self):
        directory = CommonFunctions.browse_directory("选择保存目录")
        if directory:
            self.output_path_edit.setText(directory)

    def on_use_cookie_changed(self, state):
        enabled = state == Qt.Checked
        self.cookie_combo.setEnabled(enabled)

    def update_config(self, config):
        # 更新下载器配置
        self.download_dir = config.get('download_dir', self.download_dir)
        self.quality = config.get('quality', self.quality)
        
    def update_cookie_combo(self, cookie_files):
        self.cookie_combo.clear()
        # 添加Cookie名称到下拉框
        self.cookie_combo.addItems(cookie_files)



    def analyze_video(self):
        ytdlp_path = self.parent.ytdlp_path_edit.text().strip()
        url = self.url_edit.text().strip()

        if not ytdlp_path or not os.path.exists(ytdlp_path):
            CommonFunctions.show_message("警告", "请先设置有效的YT-DLP路径!", QMessageBox.Warning)
            return

        if not url:
            CommonFunctions.show_message("警告", "请输入视频URL!", QMessageBox.Warning)
            return

        self.analyze_btn.setEnabled(False)
        CommonFunctions.log_message(self.log_output, "正在分析视频信息...")

        self.analyze_worker = AnalyzeWorker(ytdlp_path, url)
        self.analyze_worker.analysis_finished.connect(self.on_analysis_finished)
        self.analyze_worker.start()

    def on_analysis_finished(self, video_info):
        self.analyze_btn.setEnabled(True)

        if "error" in video_info:
            CommonFunctions.log_message(self.log_output, f"分析失败: {video_info['error']}")
            CommonFunctions.show_message("错误", f"分析失败: {video_info['error']}", QMessageBox.Critical)
            return

        CommonFunctions.log_message(self.log_output, "视频分析完成")
        self.update_quality_options(video_info)

    def update_quality_options(self, video_info):
        # 清空现有质量选项
        self.audio_quality_combo.clear()
        self.video_quality_combo.clear()

        formats = video_info.get("formats", [])
        audio_formats = []
        video_formats = []

        for fmt in formats:
            if fmt.get("vcodec") == "none":
                audio_formats.append(fmt)
            elif fmt.get("acodec") == "none":
                video_formats.append(fmt)

        audio_formats.sort(key=lambda x: x.get("abr", 0) or 0, reverse=True)
        video_formats.sort(key=lambda x: x.get("height", 0) or 0, reverse=True)

        for fmt in audio_formats:
            abr = fmt.get("abr", "Unknown")
            ext = fmt.get("ext", "Unknown")
            self.audio_quality_combo.addItem(f"音频: {abr}kbps ({ext})", fmt)

        seen_formats = {}
        unique_video_formats = []
        for fmt in video_formats:
            height = fmt.get("height", "Unknown")
            if height not in seen_formats:
                seen_formats[height] = True
                unique_video_formats.append(fmt)

        for fmt in unique_video_formats:
            height = fmt.get("height", "Unknown")
            ext = fmt.get("ext", "Unknown")
            self.video_quality_combo.addItem(f"视频: {height}p ({ext})", fmt)

        # 添加默认选项
        if not audio_formats:
            self.audio_quality_combo.addItems(["最高质量", "中等质量", "低质量"])
        if not video_formats:
            self.video_quality_combo.addItems(["最高质量", "中等质量", "低质量"])

    def on_download_type_changed(self, download_type):
        if download_type == "仅音频":
            self.audio_quality_label.setVisible(True)
            self.audio_quality_combo.setVisible(True)
            self.video_quality_label.setVisible(False)
            self.video_quality_combo.setVisible(False)
            self.merge_checkbox.setVisible(False)
        elif download_type == "仅视频":
            self.audio_quality_label.setVisible(False)
            self.audio_quality_combo.setVisible(False)
            self.video_quality_label.setVisible(True)
            self.video_quality_combo.setVisible(True)
            self.merge_checkbox.setVisible(False)
        else:
            self.audio_quality_label.setVisible(True)
            self.audio_quality_combo.setVisible(True)
            self.video_quality_label.setVisible(True)
            self.video_quality_combo.setVisible(True)
            self.merge_checkbox.setVisible(True)

    def start_download(self):
        ytdlp_path = self.parent.ytdlp_path_edit.text().strip()
        url = self.url_edit.text().strip()
        output_path = self.output_path_edit.text().strip()
        download_type = self.download_type_combo.currentText()
        thread_count = self.thread_count_slider.value()

        if not ytdlp_path or not os.path.exists(ytdlp_path):
            CommonFunctions.show_message("警告", "请设置有效的YT-DLP路径!", QMessageBox.Warning)
            return

        if not url:
            CommonFunctions.show_message("警告", "请输入视频URL!", QMessageBox.Warning)
            return

        if not output_path:
            CommonFunctions.show_message("警告", "请选择保存目录!", QMessageBox.Warning)
            return

        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.log_output.clear()

        audio_format_data = self.audio_quality_combo.currentData()
        video_format_data = self.video_quality_combo.currentData()
        merge_output = self.merge_checkbox.isChecked()

        # 获取选中的cookie文件路径
        cookie_name = self.cookie_combo.currentText() if self.use_cookie_checkbox.isChecked() and self.cookie_combo.currentIndex() != -1 else None
        cookie_path = self.parent.cookie_files.get(cookie_name) if cookie_name else None

        self.worker = DownloadWorker(
            ytdlp_path, url, download_type, output_path,
            cookie_path,
            audio_format_data if self.audio_quality_combo.isVisible() else None,
            video_format_data if self.video_quality_combo.isVisible() else None,
            merge_output if self.merge_checkbox.isVisible() else None,
            thread_count
        )
        self.worker.progress_updated.connect(lambda msg: CommonFunctions.log_message(self.log_output, msg))
        self.worker.progress_changed.connect(lambda val: CommonFunctions.update_progress_bar(self.progress_bar, val))
        self.worker.download_finished.connect(self.on_download_finished)
        self.worker.start()

    def on_download_finished(self, success, message):
        self.download_btn.setEnabled(True)
        CommonFunctions.log_message(self.log_output, message)
        if success:
            CommonFunctions.show_message("成功", "下载完成!", QMessageBox.Information)
        else:
            CommonFunctions.show_message("失败", message, QMessageBox.Critical)