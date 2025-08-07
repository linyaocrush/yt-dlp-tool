from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QListWidget, QGroupBox, QMessageBox)
import os
from common import CommonFunctions

class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        # YT-DLP路径设置
        ytdlp_group = QGroupBox("YT-DLP 配置")
        ytdlp_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("YT-DLP路径:"))
        self.ytdlp_path_edit = QLineEdit()
        self.ytdlp_path_edit.setPlaceholderText("输入yt-dlp可执行文件路径")
        path_layout.addWidget(self.ytdlp_path_edit)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_ytdlp)
        path_layout.addWidget(browse_btn)
        ytdlp_layout.addLayout(path_layout)
        
        # 输出路径设置
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出路径:"))
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("输入视频保存路径")
        output_layout.addWidget(self.output_path_edit)
        browse_output_btn = QPushButton("浏览...")
        browse_output_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(browse_output_btn)
        ytdlp_layout.addLayout(output_layout)
        
        # Cookie文件管理
        cookie_group = QGroupBox("Cookie文件管理")
        cookie_group_layout = QVBoxLayout()
        
        self.cookie_list = QListWidget()
        cookie_group_layout.addWidget(self.cookie_list)
        
        cookie_btn_layout = QHBoxLayout()
        add_cookie_btn = QPushButton("添加Cookie文件")
        add_cookie_btn.clicked.connect(self.add_cookie_file)
        remove_cookie_btn = QPushButton("删除选中Cookie")
        remove_cookie_btn.clicked.connect(self.remove_selected_cookie)
        cookie_btn_layout.addWidget(add_cookie_btn)
        cookie_btn_layout.addWidget(remove_cookie_btn)
        
        cookie_group_layout.addLayout(cookie_btn_layout)
        cookie_group.setLayout(cookie_group_layout)
        layout.addWidget(cookie_group)
        
        ytdlp_group.setLayout(ytdlp_layout)
        layout.addWidget(ytdlp_group)
        
        # 保存按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        self.setLayout(layout)

    def browse_ytdlp(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择YT-DLP程序", "", "可执行文件 (*.exe)")
        if path:
            self.ytdlp_path_edit.setText(path)

    def browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_path_edit.setText(path)

    def add_cookie_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择Cookie文件", "", "文本文件 (*.txt)")
        if path and path not in [self.cookie_list.item(i).text() for i in range(self.cookie_list.count())]:
            self.cookie_list.addItem(path)
    
    def remove_selected_cookie(self):
        selected_items = self.cookie_list.selectedItems()
        if selected_items:
            for item in selected_items:
                self.cookie_list.takeItem(self.cookie_list.row(item))

    def save_settings(self):
        settings = {
            'ytdlp_path': self.ytdlp_path_edit.text().strip(),
            'output_path': self.output_path_edit.text().strip(),
            'cookie_files': [self.cookie_list.item(i).text() for i in range(self.cookie_list.count())]
        }
        # 保存到配置文件
        import json
        config_path = os.path.join(os.path.expanduser("~"), ".yt_dlp_gui_config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            CommonFunctions.log_message(self.parent.current_view.log_output, "设置已保存")
            # 通知主窗口更新配置
            if self.parent:
                self.parent.update_config(settings)
        except Exception as e:
            CommonFunctions.log_message(self.parent.current_view.log_output, f"保存设置失败: {str(e)}")

    def load_settings(self):
        import json
        config_path = os.path.join(os.path.expanduser("~"), ".yt_dlp_gui_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.ytdlp_path_edit.setText(settings.get('ytdlp_path', ''))
                    self.output_path_edit.setText(settings.get('output_path', ''))
                cookie_files = settings.get('cookie_files', [])
                self.cookie_list.clear()
                for path in cookie_files:
                    self.cookie_list.addItem(path)
                # 通知主窗口更新配置
                if self.parent:
                    self.parent.update_config(settings)
            except Exception as e:
                CommonFunctions.log_message(self.parent.current_view.log_output, f"加载设置失败: {str(e)}")