from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                           QMessageBox, QLineEdit)
from PyQt5.QtCore import Qt, QDate
import datetime

class LockedTimePeriodDialog(QDialog):
    """锁定时间段管理对话框"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        
        self.setWindowTitle("锁定时间段管理")
        self.setMinimumSize(600, 400)
        
        self.init_ui()
        self.load_periods()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 添加时间段区域
        add_layout = QHBoxLayout()
        
        add_layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit()
        add_layout.addWidget(self.name_edit)
        
        add_layout.addWidget(QLabel("开始日期:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))  # 默认为一周前
        add_layout.addWidget(self.start_date)
        
        add_layout.addWidget(QLabel("结束日期:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())  # 默认为今天
        add_layout.addWidget(self.end_date)
        
        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self.add_period)
        add_layout.addWidget(self.add_btn)
        
        layout.addLayout(add_layout)
        
        # 时间段列表
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "名称", "开始日期", "结束日期"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        
        # 删除按钮
        delete_layout = QHBoxLayout()
        delete_layout.addStretch()
        self.delete_btn = QPushButton("删除选中")
        self.delete_btn.clicked.connect(self.delete_period)
        delete_layout.addWidget(self.delete_btn)
        layout.addLayout(delete_layout)
        
        self.setLayout(layout)
        
    def load_periods(self):
        """加载锁定时间段列表"""
        # 清空表格
        self.table.setRowCount(0)
        
        # 获取所有锁定时间段
        periods = self.db.get_locked_time_periods()
        
        # 填充表格
        for i, period in enumerate(periods):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(period['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(period['name']))
            self.table.setItem(i, 2, QTableWidgetItem(period['start_date']))
            self.table.setItem(i, 3, QTableWidgetItem(period['end_date']))
        
    def add_period(self):
        """添加锁定时间段"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入时间段名称")
            return
            
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        
        # 检查日期是否有效
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "警告", "开始日期不能晚于结束日期")
            return
            
        try:
            # 添加到数据库
            self.db.add_locked_time_period(name, start_date, end_date)
            
            # 刷新列表
            self.load_periods()
            
            # 清空输入框
            self.name_edit.clear()
            
            QMessageBox.information(self, "成功", "锁定时间段添加成功")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加锁定时间段失败: {str(e)}")
            
    def delete_period(self):
        """删除锁定时间段"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的时间段")
            return
            
        # 获取选中行的ID
        row = selected_rows[0].row()
        period_id = int(self.table.item(row, 0).text())
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除选中的锁定时间段吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 从数据库中删除
                self.db.delete_locked_time_period(period_id)
                
                # 刷新列表
                self.load_periods()
                
                QMessageBox.information(self, "成功", "锁定时间段删除成功")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除锁定时间段失败: {str(e)}")