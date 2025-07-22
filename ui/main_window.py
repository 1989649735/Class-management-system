#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QAction, QToolBar, QStatusBar, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog,
    QLineEdit, QComboBox, QPushButton, QFileDialog, QDialogButtonBox,
    QDialog
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from database import Database
from models import Student, DeductionRecord, CompensationRecord, AdditionRecord, DeductionType, STUDENT_LIST
from ui.deduction_dialog import ViolationDeductionDialog, NonViolationDeductionDialog, CompensationDialog
from ui.search_dialog import DeductionSearchDialog, AdditionSearchDialog
from ui.violation_count_dialog import ViolationCountDialog
from ui.addition_dialog import AdditionDialog, DeleteAdditionDialog
from ui.ranking_dialog import DeductionRankingDialog, AdditionRankingDialog, TotalScoreRankingDialog
from ui.student_dialog import InitialScoreDialog

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, db=None):
        super().__init__()
        
        # 初始化数据库
        self.db = db if db is not None else Database()
        
        # 设置窗口属性
        self.setWindowTitle("学生积分管理系统")
        self.setMinimumSize(800, 600)
        
        # 初始化UI
        self.init_ui()
        
        # 加载数据
        self.load_data()
        
    def init_ui(self):
        """初始化UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 创建学生选择区域
        selection_layout = QHBoxLayout()
        student_label = QLabel("选择学生:")
        self.student_combo = QComboBox()
        self.student_combo.addItems(STUDENT_LIST)
        self.student_combo.currentIndexChanged.connect(self.on_student_changed)
        selection_layout.addWidget(student_label)
        selection_layout.addWidget(self.student_combo)
        selection_layout.addStretch()
        main_layout.addLayout(selection_layout)
        
        # 创建学生信息表格
        self.create_student_table()
        main_layout.addWidget(self.student_table)
        
        # 创建记录表格
        self.create_records_table()
        main_layout.addWidget(self.records_table)
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 学生菜单
        student_menu = menu_bar.addMenu("学生")
        
        initial_score_action = QAction("设置初始分数", self)
        initial_score_action.triggered.connect(self.show_initial_score_dialog)
        student_menu.addAction(initial_score_action)
        
        # 扣分菜单
        deduction_menu = menu_bar.addMenu("扣分")
        
        violation_action = QAction("违规扣分", self)
        violation_action.triggered.connect(self.show_violation_deduction_dialog)
        deduction_menu.addAction(violation_action)
        
        non_violation_action = QAction("非违规扣分", self)
        non_violation_action.triggered.connect(self.show_non_violation_deduction_dialog)
        deduction_menu.addAction(non_violation_action)
        
        compensation_action = QAction("修改违规扣分", self)
        compensation_action.triggered.connect(self.show_compensation_dialog)
        deduction_menu.addAction(compensation_action)
        
        # 添加查询扣分记录
        search_action = QAction("查询扣分记录", self)
        search_action.triggered.connect(self.show_deduction_search_dialog)
        deduction_menu.addAction(search_action)
        
        # 添加违规次数查询
        violation_count_action = QAction("违规次数查询", self)
        violation_count_action.triggered.connect(self.show_violation_count_dialog)
        deduction_menu.addAction(violation_count_action)
        
        # 加分菜单
        addition_menu = menu_bar.addMenu("加分")
        
        add_addition_action = QAction("添加加分", self)
        add_addition_action.triggered.connect(self.show_addition_dialog)
        addition_menu.addAction(add_addition_action)
        
        delete_addition_action = QAction("删除加分", self)
        delete_addition_action.triggered.connect(self.show_delete_addition_dialog)
        addition_menu.addAction(delete_addition_action)
        
        # 添加查询加分记录
        search_action = QAction("查询加分记录", self)
        search_action.triggered.connect(self.show_addition_search_dialog)
        addition_menu.addAction(search_action)
        
        # 排名菜单
        ranking_menu = menu_bar.addMenu("排名")
        
        deduction_ranking_action = QAction("扣分排名", self)
        deduction_ranking_action.triggered.connect(self.show_deduction_ranking_dialog)
        ranking_menu.addAction(deduction_ranking_action)
        
        addition_ranking_action = QAction("加分排名", self)
        addition_ranking_action.triggered.connect(self.show_addition_ranking_dialog)
        ranking_menu.addAction(addition_ranking_action)
        
        total_ranking_action = QAction("总分排名", self)
        total_ranking_action.triggered.connect(self.show_total_ranking_dialog)
        ranking_menu.addAction(total_ranking_action)
        
        # 设置菜单
        settings_menu = menu_bar.addMenu("设置")
        
        # 小组管理菜单项
        group_action = QAction("小组管理", self)
        group_action.triggered.connect(self.show_group_management)
        settings_menu.addAction(group_action)
        
        # 锁定时间段管理菜单项
        locked_period_action = QAction("锁定时间段管理", self)
        locked_period_action.triggered.connect(self.show_locked_time_period_dialog)
        settings_menu.addAction(locked_period_action)
        
        settings_menu.addSeparator()
        
        # 数据管理子菜单
        data_menu = settings_menu.addMenu("数据管理")
        
        export_action = QAction("导出数据", self)
        export_action.triggered.connect(self.export_data)
        data_menu.addAction(export_action)
        
        import_action = QAction("导入数据", self)
        import_action.triggered.connect(self.import_data)
        data_menu.addAction(import_action)
        
        # 清除数据选项
        clear_action = QAction("清除数据", self)
        clear_action.triggered.connect(self.show_clear_data_dialog)
        data_menu.addAction(clear_action)
        
        delete_action = QAction("删除所有数据", self)
        delete_action.triggered.connect(self.delete_all_data)
        data_menu.addAction(delete_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
    def create_tool_bar(self):
        """创建工具栏"""
        tool_bar = QToolBar("工具栏")
        tool_bar.setIconSize(QSize(32, 32))
        self.addToolBar(tool_bar)
        
        # 违规扣分
        violation_action = QAction("违规扣分", self)
        violation_action.triggered.connect(self.show_violation_deduction_dialog)
        tool_bar.addAction(violation_action)
        
        # 非违规扣分
        non_violation_action = QAction("非违规扣分", self)
        non_violation_action.triggered.connect(self.show_non_violation_deduction_dialog)
        tool_bar.addAction(non_violation_action)
        
        # 修改违规扣分
        compensation_action = QAction("修改违规扣分", self)
        compensation_action.triggered.connect(self.show_compensation_dialog)
        tool_bar.addAction(compensation_action)
        
        tool_bar.addSeparator()
        
        # 添加加分
        add_addition_action = QAction("添加加分", self)
        add_addition_action.triggered.connect(self.show_addition_dialog)
        tool_bar.addAction(add_addition_action)
        
        # 删除加分
        delete_addition_action = QAction("删除加分", self)
        delete_addition_action.triggered.connect(self.show_delete_addition_dialog)
        tool_bar.addAction(delete_addition_action)
        
        # 查询加分
        search_addition_action = QAction("查询加分", self)
        search_addition_action.triggered.connect(self.show_addition_search_dialog)
        tool_bar.addAction(search_addition_action)
        
        tool_bar.addSeparator()
        
        # 总分排名
        total_ranking_action = QAction("总分排名", self)
        total_ranking_action.triggered.connect(self.show_total_ranking_dialog)
        tool_bar.addAction(total_ranking_action)
        
        tool_bar.addSeparator()
        
        # 查询扣分记录
        search_action = QAction("查询扣分", self)
        search_action.triggered.connect(self.show_deduction_search_dialog)
        tool_bar.addAction(search_action)
        
        # 违规次数查询
        violation_count_action = QAction("违规次数", self)
        violation_count_action.triggered.connect(self.show_violation_count_dialog)
        tool_bar.addAction(violation_count_action)
        
    def create_student_table(self):
        """创建学生信息表格"""
        self.student_table = QTableWidget()
        self.student_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.student_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.student_table.setAlternatingRowColors(True)
        
        # 设置表头
        headers = ["姓名", "初始分数", "扣分总分", "加分总分", "总分"]
        self.student_table.setColumnCount(len(headers))
        self.student_table.setRowCount(1)  # 只显示当前选中的学生
        self.student_table.setHorizontalHeaderLabels(headers)
        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
    def create_records_table(self):
        """创建记录表格"""
        self.records_table = QTableWidget()
        self.records_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.records_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.records_table.setAlternatingRowColors(True)
        
        # 设置表头
        headers = ["类型", "姓名", "分数", "原因", "日期", "违规类型"]
        self.records_table.setColumnCount(len(headers))
        self.records_table.setHorizontalHeaderLabels(headers)
        self.records_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
    def load_data(self):
        """加载数据"""
        self.on_student_changed()
        
    def on_student_changed(self):
        """学生选择变化时更新数据"""
        student_name = self.student_combo.currentText()
        if not student_name:
            return
            
        # 更新学生信息表格
        self.update_student_table(student_name)
        
        # 更新记录表格
        self.update_records_table(student_name)
        
    def update_student_table(self, student_name: str):
        """更新学生信息表格"""
        student = self.db.get_student(student_name)
        if not student:
            return
            
        # 获取扣分总分
        deduction_records = self.db.get_deduction_records(student_name)
        deduction_points = sum(record.points for record in deduction_records)
        
        # 获取加分总分
        addition_records = self.db.get_addition_records(student_name)
        addition_points = sum(record.points for record in addition_records)
        
        # 计算总分
        total_score = student.initial_score - deduction_points + addition_points
        
        # 更新表格
        self.student_table.setItem(0, 0, QTableWidgetItem(student_name))
        self.student_table.setItem(0, 1, QTableWidgetItem(f"{student.initial_score:.1f}"))
        self.student_table.setItem(0, 2, QTableWidgetItem(f"{deduction_points:.1f}"))
        self.student_table.setItem(0, 3, QTableWidgetItem(f"{addition_points:.1f}"))
        self.student_table.setItem(0, 4, QTableWidgetItem(f"{total_score:.1f}"))
        
        # 设置文本居中
        for col in range(self.student_table.columnCount()):
            item = self.student_table.item(0, col)
            if item:
                item.setTextAlignment(Qt.AlignCenter)
                
    def update_records_table(self, student_name: str):
        """更新记录表格"""
        # 获取扣分记录
        deduction_records = self.db.get_deduction_records(student_name)
        
        # 获取加分记录
        addition_records = self.db.get_addition_records(student_name)
        
        # 合并所有记录
        all_records = []
        
        # 添加扣分记录
        for record in deduction_records:
            record_type = "违规扣分" if record.deduction_type == DeductionType.VIOLATION else "非违规扣分"
            type_str = ""
            if record.deduction_type == DeductionType.VIOLATION:
                if hasattr(record, 'violation_type') and record.violation_type is not None:
                    type_str = record.violation_type.name
            else:  # 非违规扣分
                if hasattr(record, 'non_violation_type') and record.non_violation_type is not None:
                    type_str = record.non_violation_type
            all_records.append({
                "type": record_type,
                "points": -record.points,  # 扣分为负数
                "reason": record.violation_behavior if record.deduction_type == DeductionType.VIOLATION else record.treatment_measures,
                "date": record.date,
                "record": record,
                "violation_type": type_str
            })
            
        # 添加加分记录
        for record in addition_records:
            all_records.append({
                "type": "加分",
                "points": record.points,
                "reason": record.reason,
                "date": record.start_date,  # 使用开始日期
                "record": record
            })
            
        # 按日期排序
        all_records.sort(key=lambda x: x["date"], reverse=True)
        
        # 更新表格
        self.records_table.setRowCount(len(all_records))
        
        for i, record in enumerate(all_records):
            # 类型
            type_item = QTableWidgetItem(record["type"])
            self.records_table.setItem(i, 0, type_item)
            
            # 姓名
            name_item = QTableWidgetItem(record["record"].student_name)
            self.records_table.setItem(i, 1, name_item)
            
            # 分数
            points_item = QTableWidgetItem(f"{record['points']:.1f}")
            points_item.setTextAlignment(Qt.AlignCenter)
            # 设置颜色：扣分为红色，加分为绿色
            if record['points'] < 0:
                points_item.setForeground(Qt.red)
            else:
                points_item.setForeground(Qt.darkGreen)
            self.records_table.setItem(i, 2, points_item)
            
            # 原因
            reason_item = QTableWidgetItem(record["reason"])
            self.records_table.setItem(i, 3, reason_item)
            
            # 日期
            date_item = QTableWidgetItem(record["date"].strftime("%Y-%m-%d"))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.records_table.setItem(i, 4, date_item)
            
            # 违规类型
            if "violation_type" in record:
                violation_item = QTableWidgetItem(record["violation_type"])
                self.records_table.setItem(i, 5, violation_item)
            
    # 对话框显示方法
    def show_violation_deduction_dialog(self):
        """显示违规扣分对话框"""
        dialog = ViolationDeductionDialog(self.db, self)
        if dialog.exec_():
            self.on_student_changed()
            
    def show_non_violation_deduction_dialog(self):
        """显示非违规扣分对话框"""
        dialog = NonViolationDeductionDialog(self.db, self)
        if dialog.exec_():
            self.on_student_changed()
            
    def show_compensation_dialog(self):
        """显示修改违规扣分对话框"""
        dialog = CompensationDialog(self.db, self)
        if dialog.exec_():
            self.on_student_changed()
            
    def show_addition_dialog(self):
        """显示加分对话框"""
        dialog = AdditionDialog(self.db, self)
        if dialog.exec_():
            self.on_student_changed()
            
    def show_delete_addition_dialog(self):
        """显示删除加分对话框"""
        dialog = DeleteAdditionDialog(self.db, self)
        if dialog.exec_():
            self.on_student_changed()
            
    def show_deduction_ranking_dialog(self):
        """显示扣分排名对话框"""
        dialog = DeductionRankingDialog(self.db, self)
        dialog.exec_()
        
    def show_addition_ranking_dialog(self):
        """显示加分排名对话框"""
        dialog = AdditionRankingDialog(self.db, self)
        dialog.exec_()
        
    def show_total_ranking_dialog(self):
        """显示总分排名对话框"""
        dialog = TotalScoreRankingDialog(self.db, self)
        dialog.exec_()
        
    def show_deduction_search_dialog(self):
        """显示扣分记录查询对话框"""
        dialog = DeductionSearchDialog(self.db, self)
        dialog.exec_()
        
    def show_addition_search_dialog(self):
        """显示加分记录查询对话框"""
        dialog = AdditionSearchDialog(self.db, self)
        dialog.exec_()
        
    def show_violation_count_dialog(self):
        """显示违规次数查询对话框"""
        dialog = ViolationCountDialog(self.db, self)
        dialog.exec_()
        
    def show_initial_score_dialog(self):
        """显示设置初始分数对话框"""
        dialog = InitialScoreDialog(self.db, self)
        if dialog.exec_():
            self.on_student_changed()
            
    def show_about_dialog(self):
        """显示关于对话框"""
        about_text = """
        <h2>学生积分管理系统</h2>
        
        <b>版本:</b> 2.0.0<br>
        <b>构建日期:</b> 2025-7-22<br>
        
        <b>开发者:</b><br>
        - 周 (https://github.com/1989649735)<br><br>
        
        <b>系统依赖:</b><br>
        - Python 3.10+<br>
        - PyQt5 5.15.7+<br>
        - SQLite 3.37+<br><br>
        
        <b>许可证:</b> MIT 开源许可证<br>
        
        <b>系统功能:</b><br>
        <b>核心功能:</b>
        - 学生积分全生命周期管理<br>
        - 支持多种积分类型(违规/非违规扣分、加分)<br>
        - 实时积分计算与更新<br>
        
        <b>记录管理:</b>
        - 详细的扣分记录管理<br>
        - 灵活的加分记录系统<br>
        - 违规记录修改与补偿<br>
        
        <b>统计分析:</b>
        - 多维度的积分排名统计<br>
        - 违规次数分析<br>
        - 历史记录查询<br>
        
        """
        
        about_box = QMessageBox(self)
        about_box.setWindowTitle("关于")
        about_box.setTextFormat(Qt.RichText)
        about_box.setText(about_text)
        about_box.setIconPixmap(QIcon(":/icons/app_icon.png").pixmap(64, 64))
        about_box.exec_()
        
    # 密码功能已删除
            
    def export_data(self):
        """导出数据"""
        # 选择保存文件
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出数据",
            "",
            "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            # 获取所有学生
            students = self.db.get_students()
            students_data = [student.to_dict() for student in students]
            
            # 获取所有扣分记录
            all_deduction_records = []
            for student in students:
                records = self.db.get_deduction_records(student.name)
                all_deduction_records.extend([record.to_dict() for record in records])
                
            # 获取所有补偿记录
            all_compensation_records = []
            for student in students:
                records = self.db.get_student_compensation_records(student.name)
                all_compensation_records.extend([record.to_dict() for record in records])
                
            # 获取所有加分记录
            all_addition_records = []
            for student in students:
                records = self.db.get_addition_records(student.name)
                all_addition_records.extend([record.to_dict() for record in records])
                
            # 获取配置
            self.db.cursor.execute('SELECT * FROM config')
            config_rows = self.db.cursor.fetchall()
            config_data = {row['key']: row['value'] for row in config_rows}
            
            # 组合数据
            export_data = {
                "students": students_data,
                "deduction_records": all_deduction_records,
                "compensation_records": all_compensation_records,
                "addition_records": all_addition_records,
                "config": config_data
            }
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            QMessageBox.information(self, "成功", "数据导出成功")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出数据失败: {str(e)}")
        
    def import_data(self):
        """导入数据"""
        # 选择导入文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入数据",
            "",
            "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
            
        # 确认导入
        reply = QMessageBox.question(
            self,
            "确认导入",
            "导入数据将覆盖当前数据库中的所有数据，确定要继续吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
                
            # 验证数据格式
            required_keys = ["students", "deduction_records", "compensation_records", "addition_records", "config"]
            for key in required_keys:
                if key not in import_data:
                    raise ValueError(f"导入文件缺少必要的数据: {key}")
                    
            # 关闭当前数据库连接
            self.db.close()
            
            # 备份当前数据库
            backup_path = self.db.db_path + ".bak"
            if os.path.exists(self.db.db_path):
                import shutil
                shutil.copy2(self.db.db_path, backup_path)
                
            # 删除当前数据库
            if os.path.exists(self.db.db_path):
                os.remove(self.db.db_path)
                
            # 重新连接数据库（会创建新的数据库文件）
            self.db.connect()
            self.db.init_db()
            
            # 导入学生数据
            for student_data in import_data["students"]:
                student = Student.from_dict(student_data)
                self.db.update_student_initial_score(student.name, student.initial_score)
                
            # 导入扣分记录
            for record_data in import_data["deduction_records"]:
                record = DeductionRecord.from_dict(record_data)
                self.db.add_deduction_record(record)
                
            # 导入补偿记录
            for record_data in import_data["compensation_records"]:
                record = CompensationRecord.from_dict(record_data)
                self.db.add_compensation_record(record)
                
            # 导入加分记录
            for record_data in import_data["addition_records"]:
                record = AdditionRecord.from_dict(record_data)
                try:
                    self.db.add_addition_record(record)
                except ValueError:
                    # 忽略时间重叠的加分记录
                    pass
                    
            # 导入配置
            for key, value in import_data["config"].items():
                self.db.cursor.execute(
                    'INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)',
                    (key, value)
                )
                
            self.db.conn.commit()
            
            QMessageBox.information(self, "成功", "数据导入成功")
            
            # 刷新界面
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入数据失败: {str(e)}")
            
            # 尝试恢复备份
            if os.path.exists(backup_path):
                try:
                    self.db.close()
                    if os.path.exists(self.db.db_path):
                        os.remove(self.db.db_path)
                    import shutil
                    shutil.copy2(backup_path, self.db.db_path)
                    self.db.connect()
                    QMessageBox.information(self, "恢复", "已恢复到导入前的数据")
                except Exception as restore_error:
                    QMessageBox.critical(self, "错误", f"恢复备份失败: {str(restore_error)}")

    def show_group_management(self):
        """显示小组管理界面"""
        from ui.group_management.group_management_ui import GroupManagementUI
        self.group_management_window = GroupManagementUI(self.db)
        self.group_management_window.show()
        
    def show_locked_time_period_dialog(self):
        """显示锁定时间段管理对话框"""
        from ui.locked_time_period_dialog import LockedTimePeriodDialog
        dialog = LockedTimePeriodDialog(self.db, self)
        dialog.exec_()

    def show_clear_data_dialog(self):
        """显示清除数据对话框"""
        from .clear_data_dialog import ClearDataDialog
        dialog = ClearDataDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted:
            # 数据已清除，刷新界面
            self.refresh_all()
            
    def refresh_all(self):
        """刷新所有数据"""
        self.on_student_changed()
        
    def delete_all_data(self):
        """删除所有数据"""
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除所有数据吗？此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 关闭当前数据库连接
                self.db.close()
                
                # 删除数据库文件
                if os.path.exists(self.db.db_path):
                    os.remove(self.db.db_path)
                
                # 重新创建数据库
                self.db.connect()
                self.db.init_db()
                
                QMessageBox.information(self, "成功", "所有数据已删除")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除数据失败: {str(e)}")