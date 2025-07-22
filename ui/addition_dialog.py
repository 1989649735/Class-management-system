#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QTextEdit, QPushButton, QMessageBox,
    QGroupBox, QFormLayout, QDialogButtonBox, QCheckBox,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtCore import Qt, QDate

from database import Database
from models import AdditionRecord, STUDENT_LIST


class AdditionDialog(QDialog):
    """添加加分对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        
        self.setWindowTitle("添加加分")
        self.setMinimumWidth(400)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建表单
        form_layout = QFormLayout()
        
        # 学生选择
        self.student_combo = QComboBox()
        self.student_combo.addItems(STUDENT_LIST)
        form_layout.addRow("学生:", self.student_combo)
        
        # 加分分数
        self.points_edit = QLineEdit()
        self.points_edit.setPlaceholderText("请输入加分分数")
        form_layout.addRow("加分分数:", self.points_edit)
        
        # 加分原因
        self.reason_edit = QTextEdit()
        self.reason_edit.setPlaceholderText("请输入加分原因")
        form_layout.addRow("加分原因:", self.reason_edit)
        
        # 开始日期
        self.start_date_edit = QDateEdit(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        form_layout.addRow("开始日期:", self.start_date_edit)
        
        # 结束日期
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        form_layout.addRow("结束日期:", self.end_date_edit)
        
        # 批量加分选项
        batch_options_layout = QHBoxLayout()
        
        # 相同分数批量加分
        self.batch_checkbox = QCheckBox("相同分数批量加分")
        self.batch_checkbox.stateChanged.connect(self.on_batch_checkbox_changed)
        batch_options_layout.addWidget(self.batch_checkbox)
        
        # 不同分数批量加分
        self.diff_points_checkbox = QCheckBox("不同分数批量加分")
        self.diff_points_checkbox.stateChanged.connect(self.on_diff_points_checkbox_changed)
        batch_options_layout.addWidget(self.diff_points_checkbox)
        
        form_layout.addRow("批量操作:", batch_options_layout)
        
        # 相同分数批量加分学生选择
        self.batch_students_group = QGroupBox("选择学生")
        self.batch_students_group.setVisible(False)
        batch_layout = QVBoxLayout(self.batch_students_group)
        
        # 创建学生复选框
        self.student_checkboxes = {}
        for student_name in STUDENT_LIST:
            checkbox = QCheckBox(student_name)
            batch_layout.addWidget(checkbox)
            self.student_checkboxes[student_name] = checkbox
            
        # 全选/取消全选按钮
        select_buttons_layout = QHBoxLayout()
        select_all_button = QPushButton("全选")
        select_all_button.clicked.connect(self.select_all_students)
        select_buttons_layout.addWidget(select_all_button)
        
        deselect_all_button = QPushButton("取消全选")
        deselect_all_button.clicked.connect(self.deselect_all_students)
        select_buttons_layout.addWidget(deselect_all_button)
        
        batch_layout.addLayout(select_buttons_layout)
        
        # 不同分数批量加分表格
        self.diff_points_group = QGroupBox("为每个学生设置不同分数")
        self.diff_points_group.setVisible(False)
        diff_points_layout = QVBoxLayout(self.diff_points_group)
        
        # 创建表格
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(2)
        self.students_table.setHorizontalHeaderLabels(["学生", "加分分数"])
        self.students_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.students_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.students_table.setRowCount(len(STUDENT_LIST))
        
        # 填充表格
        for i, student_name in enumerate(STUDENT_LIST):
            # 学生姓名
            name_item = QTableWidgetItem(student_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # 设置为不可编辑
            self.students_table.setItem(i, 0, name_item)
            
            # 分数输入
            points_item = QTableWidgetItem("0")
            self.students_table.setItem(i, 1, points_item)
        
        diff_points_layout.addWidget(self.students_table)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.batch_students_group)
        layout.addWidget(self.diff_points_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def on_batch_checkbox_changed(self, state):
        """相同分数批量加分复选框状态变化"""
        is_batch = state == Qt.Checked
        self.student_combo.setEnabled(not is_batch)
        self.batch_students_group.setVisible(is_batch)
        
        # 如果启用了相同分数批量加分，禁用不同分数批量加分
        if is_batch:
            self.diff_points_checkbox.setChecked(False)
            
    def on_diff_points_checkbox_changed(self, state):
        """不同分数批量加分复选框状态变化"""
        is_diff_points = state == Qt.Checked
        self.student_combo.setEnabled(not is_diff_points)
        self.diff_points_group.setVisible(is_diff_points)
        
        # 如果启用了不同分数批量加分，禁用相同分数批量加分和分数输入框
        if is_diff_points:
            self.batch_checkbox.setChecked(False)
            self.points_edit.setEnabled(not is_diff_points)
        else:
            self.points_edit.setEnabled(True)
        
    def select_all_students(self):
        """全选学生"""
        for checkbox in self.student_checkboxes.values():
            checkbox.setChecked(True)
            
    def deselect_all_students(self):
        """取消全选学生"""
        for checkbox in self.student_checkboxes.values():
            checkbox.setChecked(False)
            
    def reject(self):
        """取消按钮点击"""
        # 重置批量操作状态
        if self.batch_checkbox.isChecked():
            self.batch_checkbox.setChecked(False)
            self.on_batch_checkbox_changed(Qt.Unchecked)
        super().reject()

    def accept(self):
        """确认按钮点击"""
        # 获取公共输入
        reason = self.reason_edit.toPlainText().strip()
        if not reason:
            QMessageBox.warning(self, "错误", "请输入加分原因")
            return
            
        start_date = self.start_date_edit.date().toPyDate()
        start_date = datetime.combine(start_date, datetime.min.time())
        
        end_date = self.end_date_edit.date().toPyDate()
        end_date = datetime.combine(end_date, datetime.min.time())
        
        if start_date > end_date:
            QMessageBox.warning(self, "错误", "开始日期不能晚于结束日期")
            return
        
        # 不同分数批量加分
        if self.diff_points_checkbox.isChecked():
            success_count = 0
            fail_count = 0
            processed_count = 0
            
            # 从表格中获取每个学生的分数
            for row in range(self.students_table.rowCount()):
                student_name = self.students_table.item(row, 0).text()
                points_text = self.students_table.item(row, 1).text()
                
                try:
                    points = float(points_text)
                    if points <= 0:  # 跳过零分或负分
                        continue
                        
                    processed_count += 1
                    
                    record = AdditionRecord(
                        student_name=student_name,
                        points=points,
                        reason=reason,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if self.db.add_addition_record(record):
                        success_count += 1
                    else:
                        fail_count += 1
                except ValueError as e:
                    QMessageBox.warning(
                        self,
                        "错误",
                        f"学生 {student_name} 加分记录添加失败: {str(e)}"
                    )
                    fail_count += 1
            
            if processed_count == 0:
                QMessageBox.warning(self, "错误", "请至少为一名学生设置大于0的分数")
                return
                
            if success_count > 0:
                QMessageBox.information(
                    self,
                    "成功",
                    f"成功添加 {success_count} 条不同分数加分记录，失败 {fail_count} 条"
                )
                super().accept()
            else:
                QMessageBox.warning(self, "错误", "所有加分记录添加失败")
                
        # 相同分数批量加分
        elif self.batch_checkbox.isChecked():
            # 获取分数
            try:
                points = float(self.points_edit.text())
                if points <= 0:
                    raise ValueError("加分分数必须大于0")
            except ValueError as e:
                QMessageBox.warning(self, "错误", str(e))
                return
                
            selected_students = [
                name for name, checkbox in self.student_checkboxes.items()
                if checkbox.isChecked()
            ]
            
            if not selected_students:
                QMessageBox.warning(self, "错误", "请至少选择一个学生")
                return
                
            success_count = 0
            fail_count = 0
            
            for student_name in selected_students:
                record = AdditionRecord(
                    student_name=student_name,
                    points=points,
                    reason=reason,
                    start_date=start_date,
                    end_date=end_date
                )
                
                try:
                    if self.db.add_addition_record(record):
                        success_count += 1
                    else:
                        fail_count += 1
                except ValueError as e:
                    QMessageBox.warning(
                        self,
                        "错误",
                        f"学生 {student_name} 加分记录添加失败: {str(e)}"
                    )
                    fail_count += 1
                    
            if success_count > 0:
                QMessageBox.information(
                    self,
                    "成功",
                    f"成功添加 {success_count} 条相同分数加分记录，失败 {fail_count} 条"
                )
                super().accept()
            else:
                QMessageBox.warning(self, "错误", "所有加分记录添加失败")
        else:
            # 单个学生加分
            student_name = self.student_combo.currentText()
            
            # 获取分数
            try:
                points = float(self.points_edit.text())
                if points <= 0:
                    raise ValueError("加分分数必须大于0")
            except ValueError as e:
                QMessageBox.warning(self, "错误", str(e))
                return
            
            record = AdditionRecord(
                student_name=student_name,
                points=points,
                reason=reason,
                start_date=start_date,
                end_date=end_date
            )
            
            try:
                if self.db.add_addition_record(record):
                    QMessageBox.information(self, "成功", "加分记录添加成功")
                    super().accept()
                else:
                    QMessageBox.warning(self, "错误", "加分记录添加失败")
            except ValueError as e:
                QMessageBox.warning(self, "错误", str(e))


class DeleteAdditionDialog(QDialog):
    """删除加分对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        
        self.setWindowTitle("删除加分")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 学生选择
        student_layout = QHBoxLayout()
        student_label = QLabel("选择学生:")
        self.student_combo = QComboBox()
        self.student_combo.addItems(STUDENT_LIST)
        self.student_combo.currentIndexChanged.connect(self.on_student_changed)
        student_layout.addWidget(student_label)
        student_layout.addWidget(self.student_combo)
        student_layout.addStretch()
        layout.addLayout(student_layout)
        
        # 加分记录列表
        self.records_list = QListWidget()
        self.records_list.setAlternatingRowColors(True)
        layout.addWidget(self.records_list)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self.delete_record)
        button_layout.addWidget(delete_button)
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # 存储加分记录
        self.addition_records = []
        
    def load_data(self):
        """加载数据"""
        self.on_student_changed()
        
    def on_student_changed(self):
        """学生选择变化"""
        student_name = self.student_combo.currentText()
        if not student_name:
            return
            
        # 获取加分记录
        self.addition_records = self.db.get_addition_records(student_name)
        
        # 更新加分记录列表
        self.records_list.clear()
        if not self.addition_records:
            self.records_list.addItem("无加分记录")
            return
            
        for record in self.addition_records:
            start_date_str = record.start_date.strftime("%Y-%m-%d")
            end_date_str = record.end_date.strftime("%Y-%m-%d")
            item_text = f"{start_date_str} 至 {end_date_str}: {record.points} 分 - {record.reason}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, record.id)
            self.records_list.addItem(item)
            
    def delete_record(self):
        """删除加分记录"""
        current_item = self.records_list.currentItem()
        if not current_item or not current_item.data(Qt.UserRole):
            QMessageBox.warning(self, "错误", "请选择一条加分记录")
            return
            
        record_id = current_item.data(Qt.UserRole)
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除选中的加分记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # 删除加分记录
        if self.db.delete_addition_record(record_id):
            QMessageBox.information(self, "成功", "加分记录删除成功")
            self.on_student_changed()
        else:
            QMessageBox.warning(self, "错误", "加分记录删除失败")