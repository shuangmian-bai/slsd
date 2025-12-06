#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI版本的湖南水利水电信息检索工具主程序
"""

import sys
import os
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon
from PyQt6 import uic

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from get_data import get_links, process_article
from concurrent.futures import ThreadPoolExecutor, as_completed

# 获取资源文件的函数，用于处理PyInstaller打包后的资源路径
def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        # PyInstaller创建临时文件夹，并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


class WorkerSignals(QObject):
    """工作线程信号类"""
    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(list, list, list)  # success_list, failed_list, external_links
    # 实时更新结果的信号
    result_item = pyqtSignal(dict, str)  # item, type (success or failed)
    external_link = pyqtSignal(str)  # external link
    error = pyqtSignal(str)


class SearchWorker(threading.Thread):
    """搜索工作线程"""
    
    def __init__(self, search_key, max_threads):
        super().__init__()
        self.search_key = search_key
        self.max_threads = max_threads
        self.signals = WorkerSignals()
        
    def run(self):
        try:
            print(f"正在搜索关键词: {self.search_key}")
            print(f"使用线程数: {self.max_threads}")
            
            data, external_links = get_links(self.search_key)
            self.signals.progress.emit(0, len(data), f"总共找到 {len(data)} 个内部链接")
            
            # 统计变量
            success_list = []
            failed_list = []
            
            # 实时发送外部链接
            for link in external_links:
                self.signals.external_link.emit(link)
            
            # 使用线程池处理文章
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                # 提交所有任务
                future_to_url = {executor.submit(process_article, url): url for url in data}
                
                processed_count = 0
                # 处理完成的任务
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result, error_msg, message, title = future.result()
                        processed_count += 1
                        self.signals.progress.emit(
                            processed_count, 
                            len(data), 
                            f"[{processed_count}/{len(data)}] {message}"
                        )
                        
                        # 检查是否是文件已存在的情况
                        if result or (not result and "已存在" in message):
                            # 成功保存或文件已存在都算作成功
                            if '已保存为 ' in message:
                                path = message.split('已保存为 ')[-1]
                            elif '已存在' in message:
                                # 提取文件路径，去掉前面的"文件 "和后面的"，跳过保存"部分
                                path = message.replace('文件 ', '').split(' 已存在，跳过保存')[0]
                            else:
                                path = ''
                            
                            # 转换为绝对路径
                            if path:
                                abs_path = os.path.abspath(path)
                                item = {'title': title, 'url': url, 'path': abs_path}
                                success_list.append(item)
                                # 实时发送成功结果
                                self.signals.result_item.emit(item, 'success')
                        else:
                            # 如果处理失败，记录失败信息
                            if error_msg:  # 只有真正出错的情况才记录
                                item = {'title': title, 'url': url, 'error': error_msg}
                                failed_list.append(item)
                                # 实时发送失败结果
                                self.signals.result_item.emit(item, 'failed')
                    except Exception as e:
                        processed_count += 1
                        error_message = f"[{processed_count}/{len(data)}] 处理 {url} 时发生异常: {e}"
                        self.signals.progress.emit(processed_count, len(data), error_message)
                        item = {'title': "未知标题", 'url': url, 'error': str(e)}
                        failed_list.append(item)
                        # 实时发送失败结果
                        self.signals.result_item.emit(item, 'failed')
            
            self.signals.finished.emit(success_list, failed_list, external_links)
            
        except Exception as e:
            self.signals.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 加载UI文件
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Gui.ui')
        self.ui = uic.loadUi(ui_path, self)
        
        # 设置窗口图标
        icon_path = resource_path(os.path.join("icon", "shuangmian.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 连接信号和槽
        self.setup_connections()
        
        # 初始化界面
        self.init_ui()
        
    def truncate_text(self, text, max_length=100):
        """截断过长的文本并添加省略号"""
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text
        
    def setup_connections(self):
        """连接信号和槽"""
        self.ui.startButton.clicked.connect(self.start_search)
        self.ui.openFolderButton.clicked.connect(self.open_save_folder)
        self.ui.exitButton.clicked.connect(self.close)
        self.ui.actionOpenFolder.triggered.connect(self.open_save_folder)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionAbout.triggered.connect(self.show_about)
        
        # 连接回车键事件到搜索功能
        self.ui.keywordLineEdit.returnPressed.connect(self.start_search)
        
        # 连接列表双击事件
        self.ui.successListWidget.itemDoubleClicked.connect(self.open_success_item)
        self.ui.failedListWidget.itemDoubleClicked.connect(self.open_failed_item)
        self.ui.externalListWidget.itemDoubleClicked.connect(self.open_external_link)
        
    def init_ui(self):
        """初始化界面"""
        # 设置默认关键词和线程数
        self.ui.keywordLineEdit.setText("信息安全")
        self.ui.threadSpinBox.setValue(5)
        
        # 设置进度条初始状态
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setFormat("准备就绪")
        
        # 设置窗口大小
        self.resize(1000, 800)
        
    def start_search(self):
        """开始搜索"""
        search_key = self.ui.keywordLineEdit.text().strip()
        if not search_key:
            QMessageBox.warning(self, "警告", "请输入搜索关键词")
            return
            
        max_threads = self.ui.threadSpinBox.value()
        
        # 禁用开始按钮，防止重复点击
        self.ui.startButton.setEnabled(False)
        self.ui.progressBar.setFormat("正在获取链接...")
        
        # 创建并启动工作线程
        self.worker = SearchWorker(search_key, max_threads)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.finished.connect(self.search_finished)
        self.worker.signals.error.connect(self.search_error)
        self.worker.signals.result_item.connect(self.add_result_item)
        self.worker.signals.external_link.connect(self.add_external_link)
        self.worker.start()
        
    def update_progress(self, current, total, message):
        """更新进度"""
        if total > 0:
            progress = int((current / total) * 100)
            self.ui.progressBar.setValue(progress)
            self.ui.progressBar.setFormat(f"{progress}% ({current}/{total})")
        
    def search_finished(self, success_list, failed_list, external_links):
        """搜索完成"""
        # 更新界面
        self.ui.startButton.setEnabled(True)
        self.ui.progressBar.setFormat("搜索完成")
        
        # 填充结果列表
        self.populate_results(success_list, failed_list, external_links)
        
        # 显示完成消息
        QMessageBox.information(
            self, 
            "搜索完成", 
            f"处理完成!\n成功保存: {len(success_list)} 篇\n处理失败: {len(failed_list)} 篇\n外部链接: {len(external_links)} 个"
        )
        
    def search_error(self, error_msg):
        """搜索出错"""
        self.ui.startButton.setEnabled(True)
        self.ui.progressBar.setFormat("搜索出错")
        QMessageBox.critical(self, "错误", f"搜索过程中出现错误:\n{error_msg}")
        
    def add_result_item(self, item, item_type):
        """添加单个结果项到列表"""
        if item_type == 'success':
            title = self.truncate_text(item['title'], 80)
            # 只显示标题，添加分隔符
            list_item = QListWidgetItem(f"{title}\n{'─' * 50}")
            # 保存文件路径到UserRole角色中
            list_item.setData(Qt.ItemDataRole.UserRole, item['path'])
            self.ui.successListWidget.addItem(list_item)
        elif item_type == 'failed':
            title = self.truncate_text(item['title'], 80)
            error = self.truncate_text(item['error'], 100)
            url = self.truncate_text(item['url'], 100)
            list_item = QListWidgetItem(f"{title}\n错误: {error}\n链接: {url}\n{'─' * 50}")
            # 保存链接到UserRole角色中
            list_item.setData(Qt.ItemDataRole.UserRole, item['url'])
            self.ui.failedListWidget.addItem(list_item)
            
    def add_external_link(self, link):
        """添加外部链接到列表"""
        truncated_link = self.truncate_text(link, 120)
        list_item = QListWidgetItem(f"{truncated_link}\n{'─' * 50}")
        # 保存链接到UserRole角色中
        list_item.setData(Qt.ItemDataRole.UserRole, link)
        self.ui.externalListWidget.addItem(list_item)
        
    def populate_results(self, success_list, failed_list, external_links):
        """填充结果列表"""
        # 注意：这里不清空列表，因为在搜索过程中已经实时添加了结果
        # 只有在需要重新填充所有结果时才调用此方法
        
        # 填充成功列表（仅在列表为空时）
        if self.ui.successListWidget.count() == 0:
            for item in success_list:
                title = self.truncate_text(item['title'], 80)
                # 只显示标题，添加分隔符
                list_item = QListWidgetItem(f"{title}\n{'─' * 50}")
                # 保存文件路径到UserRole角色中（转换为绝对路径）
                abs_path = os.path.abspath(item['path'])
                list_item.setData(Qt.ItemDataRole.UserRole, abs_path)
                self.ui.successListWidget.addItem(list_item)
            
        # 填充失败列表（仅在列表为空时）
        if self.ui.failedListWidget.count() == 0:
            for item in failed_list:
                title = self.truncate_text(item['title'], 80)
                error = self.truncate_text(item['error'], 100)
                url = self.truncate_text(item['url'], 100)
                list_item = QListWidgetItem(f"{title}\n错误: {error}\n链接: {url}\n{'─' * 50}")
                # 保存链接到UserRole角色中
                list_item.setData(Qt.ItemDataRole.UserRole, item['url'])
                self.ui.failedListWidget.addItem(list_item)
            
        # 填充外部链接列表（仅在列表为空时）
        if self.ui.externalListWidget.count() == 0:
            for link in external_links:
                truncated_link = self.truncate_text(link, 120)
                list_item = QListWidgetItem(f"{truncated_link}\n{'─' * 50}")
                # 保存链接到UserRole角色中
                list_item.setData(Qt.ItemDataRole.UserRole, link)
                self.ui.externalListWidget.addItem(list_item)
            
    def open_save_folder(self):
        """打开保存目录"""
        data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        if os.path.exists(data_folder):
            # 在Windows上使用资源管理器打开目录
            os.startfile(data_folder)
        else:
            QMessageBox.warning(self, "警告", "数据目录不存在，请先进行搜索")
            
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, 
            "关于", 
            "湖南水利水电信息检索工具\n\n"
            "这是一个用于检索湖南水利水电职业技术学院官网信息的工具。\n\n"
            "版本: 1.0\n"
            "作者: 双面的"
        )
        
    def open_success_item(self, item):
        """打开成功的文件"""
        # 获取存储在UserRole中的文件路径
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.exists(file_path):
            try:
                # 在Windows上打开文件
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开文件: {file_path}\n错误信息: {str(e)}")
        elif file_path:
            QMessageBox.warning(self, "警告", f"文件不存在: {file_path}")
        else:
            QMessageBox.warning(self, "警告", "无效的文件路径")
            
    def open_failed_item(self, item):
        """打开失败项的链接"""
        # 获取存储在UserRole中的链接
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            # 使用系统默认浏览器打开链接
            import webbrowser
            webbrowser.open(url)
            
    def open_external_link(self, item):
        """打开外部链接"""
        # 获取存储在UserRole中的链接
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            # 使用系统默认浏览器打开链接
            import webbrowser
            webbrowser.open(url)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()