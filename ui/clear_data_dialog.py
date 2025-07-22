#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt

class ClearDataDialog(QDialog):
    """清除数据对话框"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        
        # 设置窗口属性
        self.setWindowTitle("清除数据")
        self.setMinimumWidth(400)
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 提示信息
        warning_label = QLabel("警告：清除的数据将无法恢复！请谨慎操作。")
        warning_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(warning_label)
        
        # 清除选项
        self.deduction_check = QCheckBox("清除所有扣分记录")
        self.addition_check = QCheckBox("清除所有加分记录")
        self.group_check = QCheckBox("清除所有小组数据")
        
        layout.addWidget(self.deduction_check)
        layout.addWidget(self.addition_check)
        layout.addWidget(self.group_check)
        
        # 按钮区域
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
    def on_accept(self):
        """确认清除数据"""
        # 检查是否选择了任何选项
        if not (self.deduction_check.isChecked() or 
                self.addition_check.isChecked() or 
                self.group_check.isChecked()):
            QMessageBox.warning(self, "警告", "请至少选择一项要清除的数据")
            return
            
        # 确认对话框
        confirm_text = "确定要清除以下数据吗？\n"
        if self.deduction_check.isChecked():
            confirm_text += "- 所有扣分记录\n"
        if self.addition_check.isChecked():
            confirm_text += "- 所有加分记录\n"
        if self.group_check.isChecked():
            confirm_text += "- 所有小组数据\n"
            
        reply = QMessageBox.question(
            self,
            "确认清除",
            confirm_text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 执行清除操作
                if self.deduction_check.isChecked():
                    self.db.clear_deduction_records()
                    
                if self.addition_check.isChecked():
                    self.db.clear_addition_records()
                    
                if self.group_check.isChecked():
                    self.db.clear_group_data()
                    
                QMessageBox.information(self, "成功", "数据清除完成")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清除数据失败: {str(e)}")