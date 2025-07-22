#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialogButtonBox
)
from PyQt5.QtCore import Qt

from database import Database
from models import STUDENT_LIST


class InitialScoreDialog(QDialog):
    """设置初始分数对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        
        self.setWindowTitle("设置初始分数")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)
        
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # 设置表头
        headers = ["学生", "初始分数"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 批量设置
        batch_group_layout = QHBoxLayout()
        batch_group_layout.addWidget(QLabel("批量设置初始分数:"))
        
        self.batch_score_edit = QLineEdit()
        self.batch_score_edit.setPlaceholderText("请输入初始分数")
        batch_group_layout.addWidget(self.batch_score_edit)
        
        batch_button = QPushButton("应用")
        batch_button.clicked.connect(self.apply_batch_score)
        batch_group_layout.addWidget(batch_button)
        
        layout.addLayout(batch_group_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_scores)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 存储初始分数
        self.initial_scores = {}
        
    def load_data(self):
        """加载数据"""
        # 获取所有学生的初始分数
        for student_name in STUDENT_LIST:
            student = self.db.get_student(student_name)
            if student:
                self.initial_scores[student_name] = student.initial_score
            else:
                self.initial_scores[student_name] = 100.0  # 默认初始分数
                
        # 设置表格行数
        self.table.setRowCount(len(STUDENT_LIST))
        
        # 填充数据
        for i, student_name in enumerate(STUDENT_LIST):
            # 学生名称
            name_item = QTableWidgetItem(student_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # 设置为不可编辑
            self.table.setItem(i, 0, name_item)
            
            # 初始分数
            score_item = QTableWidgetItem(f"{self.initial_scores[student_name]:.1f}")
            score_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, score_item)
            
    def apply_batch_score(self):
        """应用批量设置的初始分数"""
        try:
            score = float(self.batch_score_edit.text())
            if score < 0:
                raise ValueError("初始分数不能为负数")
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))
            return
            
        # 确认批量设置
        reply = QMessageBox.question(
            self,
            "确认批量设置",
            f"确定要将所有学生的初始分数设置为 {score:.1f} 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # 更新表格中的初始分数
        for i in range(self.table.rowCount()):
            score_item = QTableWidgetItem(f"{score:.1f}")
            score_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, score_item)
            
    def save_scores(self):
        """保存初始分数"""
        # 收集表格中的初始分数
        updated_scores = {}
        for i in range(self.table.rowCount()):
            student_name = self.table.item(i, 0).text()
            try:
                score = float(self.table.item(i, 1).text())
                if score < 0:
                    raise ValueError(f"学生 {student_name} 的初始分数不能为负数")
                updated_scores[student_name] = score
            except ValueError as e:
                QMessageBox.warning(self, "错误", str(e))
                return
                
        # 更新数据库
        success_count = 0
        for student_name, score in updated_scores.items():
            if self.db.update_student_initial_score(student_name, score):
                success_count += 1
                
        if success_count == len(updated_scores):
            QMessageBox.information(self, "成功", "所有学生的初始分数已更新")
            super().accept()
        else:
            QMessageBox.warning(
                self,
                "警告",
                f"成功更新 {success_count} 名学生的初始分数，失败 {len(updated_scores) - success_count} 名"
            )