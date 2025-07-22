#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QTextEdit, QPushButton, QMessageBox,
    QGroupBox, QFormLayout, QDialogButtonBox, QCheckBox,
    QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, QDate

from database import Database
from models import DeductionRecord, CompensationRecord, DeductionType, ViolationType, STUDENT_LIST


class ViolationDeductionDialog(QDialog):
    """违规扣分对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        
        self.setWindowTitle("违规扣分")
        self.setMinimumWidth(400)
        self.setMaximumHeight(700)  # 设置最大高度防止超出屏幕
        
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
        
        # 扣分分数
        self.points_edit = QLineEdit()
        self.points_edit.setPlaceholderText("请输入扣分分数")
        form_layout.addRow("扣分分数:", self.points_edit)
        
        # 违规具体行为
        self.violation_behavior_edit = QTextEdit()
        self.violation_behavior_edit.setPlaceholderText("请输入违规具体行为（可选）")
        form_layout.addRow("违规具体行为:", self.violation_behavior_edit)
        
        # 处理措施
        self.treatment_measures_edit = QLineEdit()
        self.treatment_measures_edit.setText("扣分")
        self.treatment_measures_edit.setReadOnly(False)
        form_layout.addRow("处理措施:", self.treatment_measures_edit)
        
        # 扣分日期
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("扣分日期:", self.date_edit)
        
        # 违规类型
        self.violation_type_combo = QComboBox()
        for violation_type in ViolationType:
            self.violation_type_combo.addItem(violation_type.name, violation_type.value)
        form_layout.addRow("违规类型:", self.violation_type_combo)
        
        # 批量扣分
        self.batch_checkbox = QCheckBox("批量扣分")
        self.batch_checkbox.stateChanged.connect(self.on_batch_checkbox_changed)
        form_layout.addRow("", self.batch_checkbox)
        
        # 批量扣分学生选择
        self.batch_students_group = QGroupBox("选择学生")
        self.batch_students_group.setVisible(False)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        batch_layout = QVBoxLayout(scroll_content)
        
        # 创建学生复选框
        self.student_checkboxes = {}
        for student_name in STUDENT_LIST:
            checkbox = QCheckBox(student_name)
            batch_layout.addWidget(checkbox)
            self.student_checkboxes[student_name] = checkbox
            
        # 设置滚动区域内容
        scroll_area.setWidget(scroll_content)
        group_layout = QVBoxLayout(self.batch_students_group)
        group_layout.addWidget(scroll_area)
            
        # 全选/取消全选按钮
        select_buttons_layout = QHBoxLayout()
        select_all_button = QPushButton("全选")
        select_all_button.clicked.connect(self.select_all_students)
        select_buttons_layout.addWidget(select_all_button)
        
        deselect_all_button = QPushButton("取消全选")
        deselect_all_button.clicked.connect(self.deselect_all_students)
        select_buttons_layout.addWidget(deselect_all_button)
        
        batch_layout.addLayout(select_buttons_layout)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.batch_students_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def on_batch_checkbox_changed(self, state):
        """批量扣分复选框状态变化"""
        is_batch = state == Qt.Checked
        self.student_combo.setEnabled(not is_batch)
        self.batch_students_group.setVisible(is_batch)
        
    def select_all_students(self):
        """全选学生"""
        for checkbox in self.student_checkboxes.values():
            checkbox.setChecked(True)
            
    def deselect_all_students(self):
        """取消全选学生"""
        for checkbox in self.student_checkboxes.values():
            checkbox.setChecked(False)
            
    def on_treatment_changed(self, text):
        """处理措施选择变化"""
        # 选择"其他"时显示原因输入框，选择"福利卷"时隐藏
        self.reason_edit.setVisible(text == "其他")
            
    def reject(self):
        """取消按钮点击"""
        # 重置批量操作状态
        if hasattr(self, 'batch_checkbox') and self.batch_checkbox.isChecked():
            self.batch_checkbox.setChecked(False)
            self.on_batch_checkbox_changed(Qt.Unchecked)
        super().reject()

    def accept(self):
        """确认按钮点击"""
        # 获取输入
        try:
            points = float(self.points_edit.text())
            if points <= 0:
                raise ValueError("扣分分数必须大于0")
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))
            return
            
        violation_behavior = self.violation_behavior_edit.toPlainText().strip()
            
        date = self.date_edit.date().toPyDate()
        date = datetime.combine(date, datetime.min.time())
        
        # 批量扣分
        if self.batch_checkbox.isChecked():
            selected_students = [
                name for name, checkbox in self.student_checkboxes.items()
                if checkbox.isChecked()
            ]
            
            if not selected_students:
                QMessageBox.warning(self, "错误", "请至少选择一个学生")
                return
                
            records = []
            for student_name in selected_students:
                # 获取违规类型
                violation_type_idx = self.violation_type_combo.currentIndex()
                violation_type = ViolationType(self.violation_type_combo.itemData(violation_type_idx))
                
                record = DeductionRecord(
                    student_name=student_name,
                    points=points,
                    violation_behavior=violation_behavior,
                    treatment_measures="扣分",
                    date=date,
                    deduction_type=DeductionType.VIOLATION,
                    violation_type=violation_type
                )
                records.append(record)
                
            if self.db.add_batch_deduction_records(records):
                QMessageBox.information(self, "成功", "批量扣分记录添加成功")
                super().accept()
            else:
                QMessageBox.warning(self, "错误", "批量扣分记录添加失败")
        else:
            # 单个学生扣分
            student_name = self.student_combo.currentText()
            
            # 获取违规类型
            violation_type_idx = self.violation_type_combo.currentIndex()
            violation_type = ViolationType(self.violation_type_combo.itemData(violation_type_idx))
            
            # 获取处理措施
            treatment_measures = self.treatment_measures_edit.text().strip()
            if not treatment_measures:
                treatment_measures = "扣分"  # 如果为空，使用默认值
                
            record = DeductionRecord(
                student_name=student_name,
                points=points,
                violation_behavior=violation_behavior,
                treatment_measures=treatment_measures,
                date=date,
                deduction_type=DeductionType.VIOLATION,
                violation_type=violation_type
            )
            
            if self.db.add_deduction_record(record):
                QMessageBox.information(self, "成功", "扣分记录添加成功")
                super().accept()
            else:
                QMessageBox.warning(self, "错误", "扣分记录添加失败")


class NonViolationDeductionDialog(QDialog):
    """非违规扣分对话框"""
    def reject(self):
        """取消按钮点击"""
        # 重置批量操作状态
        if hasattr(self, 'batch_checkbox') and self.batch_checkbox.isChecked():
            self.batch_checkbox.setChecked(False)
            self.on_batch_checkbox_changed(Qt.Unchecked)
        super().reject()
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        
        self.setWindowTitle("非违规扣分")
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
        
        # 扣分分数
        self.points_edit = QLineEdit()
        self.points_edit.setPlaceholderText("请输入扣分分数")
        form_layout.addRow("扣分分数:", self.points_edit)
        
        # 处理措施（福利卷下拉选项）
        self.treatment_measures_combo = QComboBox()
        self.treatment_measures_combo.addItems(["福利卷", "其他"])
        self.treatment_measures_combo.currentTextChanged.connect(self.on_treatment_changed)
        form_layout.addRow("福利卷类型:", self.treatment_measures_combo)
        
        # 原因输入框（仅在选择"其他"时显示）
        self.reason_edit = QTextEdit()
        self.reason_edit.setPlaceholderText("请输入扣分原因")
        self.reason_edit.setVisible(False)
        form_layout.addRow("扣分原因:", self.reason_edit)
        
        # 扣分日期
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("扣分日期:", self.date_edit)
        
        # 批量扣分
        self.batch_checkbox = QCheckBox("批量扣分")
        self.batch_checkbox.stateChanged.connect(self.on_batch_checkbox_changed)
        form_layout.addRow("", self.batch_checkbox)
        
        # 批量扣分学生选择
        self.batch_students_group = QGroupBox("选择学生")
        self.batch_students_group.setVisible(False)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        batch_layout = QVBoxLayout(scroll_content)
        
        # 创建学生复选框
        self.student_checkboxes = {}
        for student_name in STUDENT_LIST:
            checkbox = QCheckBox(student_name)
            batch_layout.addWidget(checkbox)
            self.student_checkboxes[student_name] = checkbox
            
        # 设置滚动区域内容
        scroll_area.setWidget(scroll_content)
        group_layout = QVBoxLayout(self.batch_students_group)
        group_layout.addWidget(scroll_area)
            
        # 全选/取消全选按钮
        select_buttons_layout = QHBoxLayout()
        select_all_button = QPushButton("全选")
        select_all_button.clicked.connect(self.select_all_students)
        select_buttons_layout.addWidget(select_all_button)
        
        deselect_all_button = QPushButton("取消全选")
        deselect_all_button.clicked.connect(self.deselect_all_students)
        select_buttons_layout.addWidget(deselect_all_button)
        
        batch_layout.addLayout(select_buttons_layout)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.batch_students_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def on_batch_checkbox_changed(self, state):
        """批量扣分复选框状态变化"""
        is_batch = state == Qt.Checked
        self.student_combo.setEnabled(not is_batch)
        self.batch_students_group.setVisible(is_batch)
        
    def select_all_students(self):
        """全选学生"""
        for checkbox in self.student_checkboxes.values():
            checkbox.setChecked(True)
            
    def deselect_all_students(self):
        """取消全选学生"""
        for checkbox in self.student_checkboxes.values():
            checkbox.setChecked(False)
            
    def on_treatment_changed(self, text):
        """处理措施选择变化"""
        # 选择"其他"时显示原因输入框，选择"福利卷"时隐藏
        self.reason_edit.setVisible(text == "其他")
            
    def accept(self):
        """确认按钮点击"""
        # 获取输入
        try:
            points = float(self.points_edit.text())
            if points <= 0:
                raise ValueError("扣分分数必须大于0")
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))
            return
            
        treatment_measures = self.treatment_measures_combo.currentText()
        
        # 验证原因输入
        if treatment_measures == "其他":
            reason = self.reason_edit.toPlainText().strip()
            if not reason:
                QMessageBox.warning(self, "错误", "选择'其他'时必须填写扣分原因")
                return
            
        date = self.date_edit.date().toPyDate()
        date = datetime.combine(date, datetime.min.time())
        
        # 批量扣分
        if self.batch_checkbox.isChecked():
            selected_students = [
                name for name, checkbox in self.student_checkboxes.items()
                if checkbox.isChecked()
            ]
            
            if not selected_students:
                QMessageBox.warning(self, "错误", "请至少选择一个学生")
                return
                
            records = []
            for student_name in selected_students:
                record = DeductionRecord(
                    student_name=student_name,
                    points=points,
                    treatment_measures=treatment_measures,
                    date=date,
                    deduction_type=DeductionType.NON_VIOLATION,
                    non_violation_type=treatment_measures
                )
                records.append(record)
                
            if self.db.add_batch_deduction_records(records):
                QMessageBox.information(self, "成功", "批量扣分记录添加成功")
                super().accept()
            else:
                QMessageBox.warning(self, "错误", "批量扣分记录添加失败")
        else:
            # 单个学生扣分
            student_name = self.student_combo.currentText()
            
            record = DeductionRecord(
                student_name=student_name,
                points=points,
                treatment_measures=treatment_measures,
                date=date,
                deduction_type=DeductionType.NON_VIOLATION,
                non_violation_type=treatment_measures
            )
            
            if self.db.add_deduction_record(record):
                QMessageBox.information(self, "成功", "扣分记录添加成功")
                super().accept()
            else:
                QMessageBox.warning(self, "错误", "扣分记录添加失败")


class CompensationDialog(QDialog):
    """修改违规扣分对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        
        self.setWindowTitle("修改违规扣分")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        
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
        
        # 扣分记录选择
        self.deduction_group = QGroupBox("选择扣分记录")
        deduction_layout = QVBoxLayout(self.deduction_group)
        
        self.deduction_combo = QComboBox()
        self.deduction_combo.currentIndexChanged.connect(self.on_deduction_changed)
        deduction_layout.addWidget(self.deduction_combo)
        
        # 扣分详情
        self.deduction_details = QTextEdit()
        self.deduction_details.setReadOnly(True)
        deduction_layout.addWidget(self.deduction_details)
        
        layout.addWidget(self.deduction_group)
        
        # 修改扣分表单
        compensation_group = QGroupBox("修改扣分")
        compensation_layout = QFormLayout(compensation_group)
        
        # 修改后扣分
        self.points_edit = QLineEdit()
        self.points_edit.setPlaceholderText("请输入修改后扣分")
        compensation_layout.addRow("修改后扣分:", self.points_edit)
        
        # 处理措施
        self.treatment_edit = QLineEdit()
        self.treatment_edit.setPlaceholderText("请输入处理措施")
        compensation_layout.addRow("处理措施:", self.treatment_edit)
        
        # 修改原因
        self.reason_edit = QTextEdit()
        self.reason_edit.setPlaceholderText("请输入修改原因")
        compensation_layout.addRow("修改原因:", self.reason_edit)
        
        # 修改日期
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        compensation_layout.addRow("修改日期:", self.date_edit)
        
        layout.addWidget(compensation_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 存储扣分记录
        self.deduction_records = []
        self.current_deduction_record = None
        
    def load_data(self):
        """加载数据"""
        self.on_student_changed()
        
    def on_student_changed(self):
        """学生选择变化"""
        student_name = self.student_combo.currentText()
        if not student_name:
            return
            
        # 获取扣分记录
        self.deduction_records = self.db.get_deduction_records(student_name)
        
        # 过滤出违规扣分记录
        self.deduction_records = [
            record for record in self.deduction_records
            if record.deduction_type == DeductionType.VIOLATION
        ]
        
        # 更新扣分记录下拉框
        self.deduction_combo.clear()
        if not self.deduction_records:
            self.deduction_combo.addItem("无违规扣分记录")
            self.deduction_details.clear()
            self.current_deduction_record = None
            return
            
        for record in self.deduction_records:
            date_str = record.date.strftime("%Y-%m-%d")
            reason = record.violation_behavior if record.deduction_type == DeductionType.VIOLATION else record.treatment_measures
            if reason is None:
                reason = "无详细原因"
            display_text = f"{date_str} - {reason[:20]}..." if reason else f"{date_str} - 无详细原因"
            self.deduction_combo.addItem(display_text)
            
        # 选择第一条记录
        self.on_deduction_changed()
        
    def on_deduction_changed(self):
        """扣分记录选择变化"""
        index = self.deduction_combo.currentIndex()
        if index < 0 or not self.deduction_records:
            self.deduction_details.clear()
            self.current_deduction_record = None
            return
            
        # 获取选中的扣分记录
        record = self.deduction_records[index]
        self.current_deduction_record = record
        
        # 显示扣分详情
        details = f"学生: {record.student_name}\n"
        details += f"扣分分数: {record.points}\n"
        reason = record.violation_behavior if record.deduction_type == DeductionType.VIOLATION else record.treatment_measures
        details += f"扣分原因: {reason if reason else '无详细原因'}\n"
        details += f"处理措施: {record.treatment_measures if record.treatment_measures else '无处理措施'}\n"
        details += f"扣分日期: {record.date.strftime('%Y-%m-%d')}\n"
        details += f"扣分类型: 违规扣分\n\n"
        
        # 获取该扣分记录的修改历史
        modification_history = self.db.get_deduction_record_modifications(record.id)
        if modification_history:
            details += "修改历史:\n"
            for history in modification_history:
                details += f"- {history['date'].strftime('%Y-%m-%d')}: {history['old_points']} -> {history['new_points']} 分 ({history['reason']})\n"
                
        self.deduction_details.setText(details)
        
        # 设置默认修改后扣分为原扣分值
        self.points_edit.setText(str(record.points))
        
        # 设置处理措施
        self.treatment_edit.setText(record.treatment_measures if record.treatment_measures else "")
        
    def accept(self):
        """确认按钮点击"""
        if not self.current_deduction_record:
            QMessageBox.warning(self, "错误", "请选择一条扣分记录")
            return
            
        # 获取输入
        try:
            new_points = float(self.points_edit.text())
            if new_points < 0:
                raise ValueError("修改后扣分不能为负数")
            if new_points > self.current_deduction_record.points:
                raise ValueError("修改后扣分不能大于原扣分")
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))
            return
            
        reason = self.reason_edit.toPlainText().strip()
        if not reason:
            QMessageBox.warning(self, "错误", "请输入修改原因")
            return
            
        date = self.date_edit.date().toPyDate()
        date = datetime.combine(date, datetime.min.time())
        
        # 创建修改记录
        compensation_record = CompensationRecord(
            deduction_record_id=self.current_deduction_record.id,
            old_points=self.current_deduction_record.points,
            new_points=new_points,
            reason=reason,
            date=date
        )
        
        # 更新处理措施
        treatment_measures = self.treatment_edit.text().strip()
        if not treatment_measures:
            treatment_measures = "无处理措施"
            
        # 更新扣分记录并添加修改记录
        if self.db.update_deduction_record_points_and_treatment(
            self.current_deduction_record.id, 
            new_points,
            treatment_measures,
            compensation_record
        ):
            QMessageBox.information(self, "成功", "扣分记录修改成功")
            super().accept()
        else:
            QMessageBox.warning(self, "错误", "扣分记录修改失败")