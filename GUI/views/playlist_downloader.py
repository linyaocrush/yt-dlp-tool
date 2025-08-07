import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QGroupBox, QProgressBar, QTextEdit, QDateEdit, QSpinBox, QFormLayout)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from ..common import AnalyzeWorker, DownloadWorker, CommonFunctions


class PlaylistDownloader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
        self.analyze_worker = None
        self.worker = None
        self.init_ui()
        self.load_config()
        CommonFunctions.apply_styles(self)

    def closeEvent(self, event):
        # 终止所有运行中的工作线程
        if self.analyze_worker and self.analyze_worker.isRunning():
            self.analyze_worker.terminate()
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
        event.accept()

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题
        title_label = QLabel("播放列表/频道/用户视频下载")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # URL输入区域
        url_group = QGroupBox("资源链接")
        url_layout = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("输入播放列表、频道或用户页面URL")
        self.analyze_btn = QPushButton("分析资源")
        self.analyze_btn.clicked.connect(self.analyze_resource)
        url_layout.addWidget(self.url_edit)
        url_layout.addWidget(self.analyze_btn)
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)

        # 筛选条件区域
        filter_group = QGroupBox("筛选条件")
        filter_layout = QFormLayout()
        filter_layout.setSpacing(10)

        # 数量限制
        self.limit_count = QSpinBox()
        self.limit_count.setRange(0, 999)
        self.limit_count.setValue(0)
        self.limit_count.setSpecialValueText("无限制")
        filter_layout.addRow("最大下载数量:", self.limit_count)

        # 日期范围筛选
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("至"))
        date_layout.addWidget(self.end_date)
        filter_layout.addRow("发布日期范围:", date_layout)

        # 下载类型选择
        self.download_type_combo = QComboBox()
        self.download_type_combo.addItems(["全部下载", "仅音频", "仅视频"])
        filter_layout.addRow("下载类型:", self.download_type_combo)

        # 线程数设置
        self.thread_count_slider = QSpinBox()
        self.thread_count_slider.setRange(1, 16)
        self.thread_count_slider.setValue(4)
        filter_layout.addRow("下载线程数:", self.thread_count_slider)

        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)

        # Cookie设置
        cookie_layout = QHBoxLayout()
        self.use_cookie_checkbox = QCheckBox("使用Cookie")
        cookie_layout.addWidget(self.use_cookie_checkbox)
        main_layout.addLayout(cookie_layout)

        # 下载按钮
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setObjectName("downloadBtn")
        self.download_btn.clicked.connect(self.start_download)
        main_layout.addWidget(self.download_btn, alignment=Qt.AlignCenter)

        # 日志输出
        log_group = QGroupBox("下载日志")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.setLayout(main_layout)
        self.setWindowTitle("YT-DLP 播放列表下载器")
        self.resize(800, 700)

    def update_config(self, config):
        self.config = config

    def analyze_resource(self):
        ytdlp_path = self.config.get('ytdlp_path', '').strip() if hasattr(self, 'config') else ""
        url = self.url_edit.text().strip()

        # 验证输入
        if not ytdlp_path:
            CommonFunctions.show_message("警告", "请先在主窗口设置YT-DLP路径!", QMessageBox.Warning)
            return

        if not os.path.exists(ytdlp_path):
            CommonFunctions.show_message("警告", "YT-DLP程序不存在，请检查路径!", QMessageBox.Warning)
            return

        if not url:
            CommonFunctions.show_message("警告", "请输入资源URL!", QMessageBox.Warning)
            return

        # 禁用分析按钮
        self.analyze_btn.setEnabled(False)
        CommonFunctions.log_message(self.log_output, "正在分析资源信息...")

        # 创建并启动分析线程
        self.analyze_worker = AnalyzeWorker(ytdlp_path, url)
        self.analyze_worker.analysis_finished.connect(self.on_analysis_finished)
        self.analyze_worker.start()

    def on_analysis_finished(self, resource_info):
        # 恢复分析按钮状态
        self.analyze_btn.setEnabled(True)

        # 检查是否有错误
        if "error" in resource_info:
            CommonFunctions.log_message(self.log_output, f"分析失败: {resource_info['error']}")
            CommonFunctions.show_message("错误", f"分析失败: {resource_info['error']}", QMessageBox.Critical)
            return

        # 更新日志
        CommonFunctions.log_message(self.log_output, "资源分析完成")
        CommonFunctions.log_message(self.log_output, f"标题: {resource_info.get('title', '未知')}")
        CommonFunctions.log_message(self.log_output, f"视频总数: {resource_info.get('_total', '未知')}")

    def start_download(self):
        if not self.parent:
            CommonFunctions.show_message("错误", "无法获取主窗口配置!", QMessageBox.Critical)
            return

        ytdlp_path = self.config.get('ytdlp_path', '').strip()
        url = self.url_edit.text().strip()
        output_path = self.config.get('output_path', '').strip()
        cookie_path = self.config.get('cookie_path', '') if self.use_cookie_checkbox.isChecked() else None
        download_type = self.download_type_combo.currentText()
        thread_count = self.thread_count_slider.value()
        max_count = self.limit_count.value()
        start_date = self.start_date.date().toString("yyyyMMdd")
        end_date = self.end_date.date().toString("yyyyMMdd")

        # 验证输入
        if not ytdlp_path or not os.path.exists(ytdlp_path):
            CommonFunctions.show_message("警告", "YT-DLP程序不存在，请检查路径!", QMessageBox.Warning)
            return

        if not url:
            CommonFunctions.show_message("警告", "请输入资源URL!", QMessageBox.Warning)
            return

        if not output_path:
            CommonFunctions.show_message("警告", "请选择保存目录!", QMessageBox.Warning)
            return

        # 禁用下载按钮
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        CommonFunctions.log_message(self.log_output, "开始下载资源...")

        # 构建yt-dlp命令参数
        extra_params = []
        
        # 添加数量限制参数
        if max_count > 0:
            extra_params.extend(['--max-downloads', str(max_count)])

        # 添加日期范围筛选
        extra_params.extend(['--dateafter', start_date])
        extra_params.extend(['--datebefore', end_date])

        # 创建并启动下载线程
        self.worker = DownloadWorker(
            ytdlp_path, url, download_type, output_path,
            cookie_path if cookie_path else None,
            thread_count=thread_count,
            extra_params=extra_params
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

    def load_config(self):
        widgets = {
            'playlist_download_type': self.download_type_combo,
            'playlist_thread_count': self.thread_count_slider,
            'playlist_limit_count': self.limit_count
        }
        success, msg = CommonFunctions.load_config(self.config_file, widgets)
        if success:
            CommonFunctions.log_message(self.log_output, msg)

    def save_config(self):
        widgets = {
            'playlist_output_path': self.output_path_edit,
            'playlist_cookie_path': self.cookie_path_edit,
            'playlist_download_type': self.download_type_combo,
            'playlist_thread_count': self.thread_count_slider,
            'playlist_limit_count': self.limit_count
        }
        success, msg = CommonFunctions.save_config(self.config_file, widgets)
        CommonFunctions.log_message(self.log_output, msg)
        return success