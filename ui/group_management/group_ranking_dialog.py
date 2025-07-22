#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QDialogButtonBox, QDateEdit, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from database import Database
from ui.ranking_dialog import RankingDialogBase


class GroupRankingByDateRangeDialog(RankingDialogBase):
    """按时间段查询小组排名对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(db, "小组排名", parent)
        self.setup_date_controls()
        self.load_locked_periods()
        
    def setup_date_controls(self):
        """设置日期选择控件"""
        # 日期选择区域
        date_layout = QHBoxLayout()
        
        date_layout.addWidget(QLabel("开始日期:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(self.start_date_edit)
        
        date_layout.addWidget(QLabel("结束日期:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date_edit)
        
        self.query_btn = QPushButton("查询")
        self.query_btn.clicked.connect(self.load_data)
        date_layout.addWidget(self.query_btn)
        
        # 锁定时间段选择
        date_layout.addWidget(QLabel("锁定时间段:"))
        self.locked_period_combo = QComboBox()
        self.locked_period_combo.addItem("自定义", None)
        self.locked_period_combo.currentIndexChanged.connect(self.on_locked_period_changed)
        date_layout.addWidget(self.locked_period_combo)
        
        # 将日期控件添加到主布局
        self.layout().insertLayout(0, date_layout)
        
    def load_locked_periods(self):
        """加载锁定时间段"""
        locked_periods = self.db.get_locked_time_periods()
        for period in locked_periods:
            display_text = f"{period['name']} ({period['start_date']} - {period['end_date']})"
            self.locked_period_combo.addItem(display_text, period)
            
    def on_locked_period_changed(self, index):
        """锁定时间段选择变化时的处理"""
        if index == 0:  # 自定义
            self.start_date_edit.setEnabled(True)
            self.end_date_edit.setEnabled(True)
            return
            
        period = self.locked_period_combo.currentData()
        if period:
            self.start_date_edit.setDate(QDate.fromString(period['start_date'], "yyyy-MM-dd"))
            self.end_date_edit.setDate(QDate.fromString(period['end_date'], "yyyy-MM-dd"))
            self.start_date_edit.setEnabled(False)
            self.end_date_edit.setEnabled(False)
        
    def load_data(self):
        """加载数据"""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        # 检查日期范围
        if self.start_date_edit.date() > self.end_date_edit.date():
            QMessageBox.warning(self, "日期错误", "开始日期不能晚于结束日期")
            return
            
        # 检查锁定时间段
        if self.locked_period_combo.currentIndex() == 0:  # 自定义
            if not self.db.is_date_range_in_locked_period(start_date, end_date):
                QMessageBox.warning(
                    self,
                    "日期范围错误",
                    "所选日期范围不在任何锁定时间段内。\n请选择一个锁定时间段或确保自定义日期范围在锁定时间段内。"
                )
                return
        
        # 设置表头
        headers = ["排名", "小组名称", "成员数", f"总分 ({start_date} 至 {end_date})"]
        self.setup_table(headers)
        
        # 获取指定时间段内的小组排名
        ranking = self.db.get_group_ranking_by_date_range(start_date, end_date)
        
        # 设置行数
        self.table.setRowCount(len(ranking))
        
        # 填充数据
        for i, group in enumerate(ranking):
            # 获取小组ID
            group_id = group['id']
            
            # 查询小组成员数量
            self.db.cursor.execute(
                'SELECT COUNT(*) as member_count FROM student_groups WHERE group_id = ?',
                (group_id,)
            )
            member_count = self.db.cursor.fetchone()['member_count']
            
            # 排名
            rank = str(i + 1)
            
            # 小组名称
            group_name = group['name']
            
            # 总分
            try:
                total_points = float(group['total_points'])
                total_points_str = f"{total_points:.1f}"
            except (ValueError, TypeError):
                total_points_str = str(group['total_points'])
                
            data = [
                rank,
                group_name,
                str(member_count),
                total_points_str
            ]
            self.add_table_row(i, data)
            
            # 设置前三名的字体为粗体
            if i < 3:
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)