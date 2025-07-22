from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
                           QMessageBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
import datetime

class GroupScoreStatsDialog(QDialog):
    """小组分数统计对话框"""
    
    def __init__(self, parent, db, group_id):
        super().__init__(parent)
        self.db = db
        self.group_id = group_id
        
        # 获取小组信息
        groups = self.db.get_groups()
        self.group_info = next((g for g in groups if g['id'] == group_id), None)
        
        group_name = self.group_info['name'] if self.group_info else f"小组 {group_id}"
        self.setWindowTitle(f"小组分数统计 - {group_name}")
        self.setMinimumSize(600, 400)
        
        self.init_ui()
        self.update_stats()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 时间段选择区域
        date_layout = QHBoxLayout()
        
        date_layout.addWidget(QLabel("选择锁定时间段:"))
        self.period_combo = QComboBox()
        self.load_locked_periods()
        date_layout.addWidget(self.period_combo)
        
        self.query_btn = QPushButton("查询")
        self.query_btn.clicked.connect(self.update_stats)
        date_layout.addWidget(self.query_btn)
        
        layout.addLayout(date_layout)
        
        # 统计结果表格
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(3)
        self.stats_table.setHorizontalHeaderLabels(["学生姓名", "学号", "加分总和"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.stats_table)
        
        # 总计区域
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("小组总分:"))
        self.total_score_label = QLabel("0")
        self.total_score_label.setStyleSheet("font-weight: bold; color: blue;")
        total_layout.addWidget(self.total_score_label)
        total_layout.addStretch()
        
        layout.addLayout(total_layout)
        
        self.setLayout(layout)
        
    def load_locked_periods(self):
        """加载锁定时间段列表"""
        self.period_combo.clear()
        
        # 获取所有锁定时间段
        locked_periods = self.db.get_locked_time_periods()
        
        # 获取从加分记录中提取的时间段
        addition_periods = self.db.get_addition_time_periods()
        
        # 合并时间段列表
        self.periods = locked_periods + addition_periods
        
        if not self.periods:
            self.period_combo.addItem("没有可用的时间段", None)
            return
            
        # 填充下拉框
        # 先添加加分记录中提取的时间段
        if addition_periods:
            self.period_combo.addItem("--- 加分记录时间段 ---", None)
            for period in addition_periods:
                display_text = f"{period['name']} ({period['start_date']} 至 {period['end_date']})"
                self.period_combo.addItem(display_text, period['id'])
        
        # 再添加锁定时间段
        if locked_periods:
            self.period_combo.addItem("--- 手动锁定时间段 ---", None)
            for period in locked_periods:
                display_text = f"{period['name']} ({period['start_date']} 至 {period['end_date']})"
                self.period_combo.addItem(display_text, period['id'])
        
    def update_stats(self):
        """更新统计数据"""
        # 获取选中的时间段ID
        current_index = self.period_combo.currentIndex()
        period_id = self.period_combo.itemData(current_index)
        
        if period_id is None:
            QMessageBox.warning(self, "警告", "请选择有效的时间段")
            return
            
        # 获取选中的时间段信息
        period = None
        for p in self.periods:
            if p['id'] == period_id:
                period = p
                break
                
        if not period:
            QMessageBox.warning(self, "错误", "无法获取选中的时间段信息")
            return
            
        # 解析开始日期和结束日期
        try:
            # 打印日期格式以便调试
            print(f"开始日期: {period['start_date']}, 结束日期: {period['end_date']}")
            
            # 处理各种可能的日期格式
            def parse_date(date_str):
                """解析日期字符串，支持多种格式"""
                if isinstance(date_str, str):
                    # 处理ISO格式 (YYYY-MM-DDTHH:MM:SS)
                    if 'T' in date_str:
                        date_str = date_str.split('T')[0]
                    # 处理空格分隔的日期时间
                    elif ' ' in date_str:
                        date_str = date_str.split(' ')[0]
                    # 处理纯日期格式
                    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                elif isinstance(date_str, datetime.date):
                    return date_str
                else:
                    raise ValueError(f"不支持的日期格式: {date_str}")
            
            # 解析开始日期和结束日期
            start_date = parse_date(period['start_date'])
            end_date = parse_date(period['end_date'])
            
            # 转换为数据库查询需要的字符串格式 (YYYY-MM-DD)
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # 确保结束日期是当天的23:59:59
            end_date = datetime.datetime.combine(end_date, datetime.time(23, 59, 59))
        except ValueError as e:
            QMessageBox.warning(self, "错误", f"日期格式无效: {e}")
            return
        
        # 获取小组成员
        members = self.db.get_group_members(self.group_id)
        member_count = len(members)
        
        if member_count == 0:
            return
        
        # 获取小组在指定时间段内的加分记录
        addition_records = self.db.get_group_addition_records(
            self.group_id, 
            start_date_str,  # 使用格式化后的日期字符串
            end_date_str     # 使用格式化后的日期字符串
        )
        
        # 计算总分
        group_total_score = sum(record.get('points', 0) for record in addition_records)
        
        # 清空表格
        self.stats_table.setRowCount(0)
        
        # 获取每个学生的个人得分
        student_scores = {}
        for member in members:
            student_id = member['student_id']
            # 获取学生在指定时间段内的个人加分记录
            student_records = self.db.get_student_addition_records(
                student_id,
                start_date_str,
                end_date_str
            )
            # 计算学生个人得分
            student_scores[student_id] = sum(record.get('points', 0) for record in student_records)
        
        # 填充表格
        for i, member in enumerate(members):
            # 直接使用成员信息，不需要再次查询
            student_name = member['student_name']
            student_id = member['student_id']
            
            # 获取学生个人得分
            student_score = student_scores.get(student_id, 0)
            
            # 添加行
            row_position = self.stats_table.rowCount()
            self.stats_table.insertRow(row_position)
            
            # 设置单元格内容
            self.stats_table.setItem(row_position, 0, QTableWidgetItem(student_name))
            self.stats_table.setItem(row_position, 1, QTableWidgetItem(str(student_id)))
            
            score_item = QTableWidgetItem(f"{student_score:.2f}")
            score_item.setTextAlignment(Qt.AlignCenter)
            if student_score > 0:
                score_item.setForeground(QColor(0, 128, 0))  # 绿色表示正分
            elif student_score < 0:
                score_item.setForeground(QColor(255, 0, 0))  # 红色表示负分
            self.stats_table.setItem(row_position, 2, score_item)
        
        # 更新总分
        self.total_score_label.setText(f"{group_total_score:.2f}")
        
        # 根据总分设置颜色
        if group_total_score > 0:
            self.total_score_label.setStyleSheet("font-weight: bold; color: green;")
        elif group_total_score < 0:
            self.total_score_label.setStyleSheet("font-weight: bold; color: red;")
        else:
            self.total_score_label.setStyleSheet("font-weight: bold; color: black;")