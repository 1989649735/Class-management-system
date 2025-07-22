#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import Database


class RankingDialogBase(QDialog):
    """排名对话框基类"""
    
    def __init__(self, db: Database, title: str, parent=None):
        super().__init__(parent)
        self.db = db
        
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_data(self):
        """加载数据（子类实现）"""
        pass
        
    def setup_table(self, headers):
        """设置表格"""
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
    def add_table_row(self, row_index, data):
        """添加表格行"""
        for col_index, text in enumerate(data):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_index, col_index, item)


class DeductionRankingDialog(RankingDialogBase):
    """扣分排名对话框"""
    
    def __init__(self, db: Database, parent=None):
        self.sort_by = "total"  # 默认按总扣分排序
        super().__init__(db, "扣分排名", parent)
        
    def init_ui(self):
        """初始化UI"""
        # 创建排序选项布局
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("排序方式:"))
        
        self.total_radio = QPushButton("总扣分")
        self.total_radio.setCheckable(True)
        self.total_radio.setChecked(True)
        self.total_radio.clicked.connect(lambda: self.set_sort_by("total"))
        sort_layout.addWidget(self.total_radio)
        
        self.violation_radio = QPushButton("违规扣分")
        self.violation_radio.setCheckable(True)
        self.violation_radio.clicked.connect(lambda: self.set_sort_by("violation"))
        sort_layout.addWidget(self.violation_radio)
        
        self.non_violation_radio = QPushButton("非违规扣分")
        self.non_violation_radio.setCheckable(True)
        self.non_violation_radio.clicked.connect(lambda: self.set_sort_by("non_violation"))
        sort_layout.addWidget(self.non_violation_radio)
        
        # 调用父类的init_ui
        super().init_ui()
        
        # 在表格上方添加排序选项
        self.layout().insertLayout(0, sort_layout)
        
    def set_sort_by(self, sort_by):
        """设置排序方式"""
        self.sort_by = sort_by
        
        # 更新按钮状态
        self.total_radio.setChecked(sort_by == "total")
        self.violation_radio.setChecked(sort_by == "violation")
        self.non_violation_radio.setChecked(sort_by == "non_violation")
        
        self.load_data()
        
    def load_data(self):
        """加载数据"""
        # 设置表头
        headers = ["排名", "学生", "违规扣分", "非违规扣分", "总扣分"]
        self.setup_table(headers)
        
        # 获取扣分排名
        ranking = self.db.get_deduction_ranking(self.sort_by)
        
        # 设置行数
        self.table.setRowCount(len(ranking))
        
        # 填充数据
        for i, (student_name, violation_points, non_violation_points, total_points) in enumerate(ranking):
            rank = str(i + 1)
            
            # 确保所有点数都是浮点数类型
            try:
                v_points = float(violation_points)
                v_points_str = f"{v_points:.1f}"
            except (ValueError, TypeError):
                v_points_str = str(violation_points)
                
            try:
                nv_points = float(non_violation_points)
                nv_points_str = f"{nv_points:.1f}"
            except (ValueError, TypeError):
                nv_points_str = str(non_violation_points)
                
            try:
                t_points = float(total_points)
                t_points_str = f"{t_points:.1f}"
            except (ValueError, TypeError):
                t_points_str = str(total_points)
                
            data = [
                rank,
                student_name,
                v_points_str,
                nv_points_str,
                t_points_str
            ]
            self.add_table_row(i, data)
            
            # 设置前三名的字体为粗体
            if i < 3:
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)


class AdditionRankingDialog(RankingDialogBase):
    """加分排名对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(db, "加分排名", parent)
        
    def load_data(self):
        """加载数据"""
        # 设置表头
        headers = ["排名", "学生", "加分总分"]
        self.setup_table(headers)
        
        # 获取加分排名
        ranking = self.db.get_addition_ranking()
        
        # 设置行数
        self.table.setRowCount(len(ranking))
        
        # 填充数据
        for i, student_data in enumerate(ranking):
            rank = str(i + 1)
            student_name = student_data['name']
            points = student_data['addition_points']
            
            # 确保points是浮点数类型
            try:
                points_float = float(points)
                points_str = f"{points_float:.1f}"
            except (ValueError, TypeError):
                # 如果无法转换为浮点数，则直接使用原始值
                points_str = str(points)
                
            data = [
                rank,
                student_name,
                points_str
            ]
            self.add_table_row(i, data)
            
            # 设置前三名的字体为粗体
            if i < 3:
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)


class TotalScoreRankingDialog(RankingDialogBase):
    """总分排名对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(db, "总分排名", parent)
        
    def load_data(self):
        """加载数据"""
        # 设置表头
        headers = ["排名", "学生", "初始分数", "扣分总分", "加分总分", "总分"]
        self.setup_table(headers)
        
        # 获取总分排名
        ranking = self.db.get_total_score_ranking()
        
        # 设置行数
        self.table.setRowCount(len(ranking))
        
        # 填充数据
        for i, student_data in enumerate(ranking):
            rank = str(i + 1)
            student_name = student_data['name']
            initial_score = student_data['initial_score']
            deduction_points = student_data['deduction_points']
            addition_points = student_data['addition_points']
            total_score = student_data['total_score']
            
            # 确保所有分数都是浮点数类型
            try:
                initial = float(initial_score)
                initial_str = f"{initial:.1f}"
            except (ValueError, TypeError):
                initial_str = str(initial_score)
                
            try:
                deduction = float(deduction_points)
                deduction_str = f"{deduction:.1f}"
            except (ValueError, TypeError):
                deduction_str = str(deduction_points)
                
            try:
                addition = float(addition_points)
                addition_str = f"{addition:.1f}"
            except (ValueError, TypeError):
                addition_str = str(addition_points)
                
            try:
                total = float(total_score)
                total_str = f"{total:.1f}"
            except (ValueError, TypeError):
                total_str = str(total_score)
                
            data = [
                rank,
                student_name,
                initial_str,
                deduction_str,
                addition_str,
                total_str
            ]
            self.add_table_row(i, data)
            
            # 设置前三名的字体为粗体
            if i < 3:
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)