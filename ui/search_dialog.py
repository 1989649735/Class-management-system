from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QComboBox, QFormLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator
from typing import Optional
from database import Database, DeductionRecord
from models import ViolationType, AdditionRecord


class DeductionSearchDialog(QDialog):
    """扣分记录查询对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("扣分记录查询")
        self.setMinimumSize(600, 400)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 查询条件区域
        condition_layout = QHBoxLayout()
        
        # 姓名输入
        condition_layout.addWidget(QLabel("姓名:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入学生姓名(可选)")
        condition_layout.addWidget(self.name_edit)
        
        # 记录类型筛选
        condition_layout.addWidget(QLabel("记录类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("全部", None)
        self.type_combo.addItem("违规", 1)
        self.type_combo.addItem("非违规", 2)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        condition_layout.addWidget(self.type_combo)

        # 违规类型筛选
        condition_layout.addWidget(QLabel("违规类型:"))
        self.violation_type_combo = QComboBox()
        self.violation_type_combo.addItem("全部", None)
        for violation_type in ViolationType:
            self.violation_type_combo.addItem(violation_type.name, violation_type)
        condition_layout.addWidget(self.violation_type_combo)
        
        # 非违规类型筛选
        condition_layout.addWidget(QLabel("非违规类型:"))
        self.non_violation_type_combo = QComboBox()
        self.non_violation_type_combo.addItem("全部", None)
        
        # 动态获取非违规类型列表
        non_violation_types = self.db.get_non_violation_types()
        for non_type in non_violation_types:
            self.non_violation_type_combo.addItem(non_type, non_type)
            
        # 如果没有非违规类型记录，添加一些默认选项
        if not non_violation_types:
            default_types = ["福利卷", "奖励", "其他"]
            for non_type in default_types:
                self.non_violation_type_combo.addItem(non_type, non_type)
                
        condition_layout.addWidget(self.non_violation_type_combo)
        
        # 分数范围筛选
        points_layout = QHBoxLayout()
        points_layout.addWidget(QLabel("分数范围:"))
        
        self.min_points_input = QLineEdit()
        self.min_points_input.setPlaceholderText("最小值")
        self.min_points_input.setValidator(QDoubleValidator(0, 100, 1))
        self.min_points_input.setMaximumWidth(80)
        points_layout.addWidget(self.min_points_input)
        
        points_layout.addWidget(QLabel("至"))
        
        self.max_points_input = QLineEdit()
        self.max_points_input.setPlaceholderText("最大值")
        self.max_points_input.setValidator(QDoubleValidator(0, 100, 1))
        self.max_points_input.setMaximumWidth(80)
        points_layout.addWidget(self.max_points_input)
        
        points_layout.addStretch()
        condition_layout.addLayout(points_layout)
        
        # 开始日期
        condition_layout.addWidget(QLabel("开始日期:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        condition_layout.addWidget(self.start_date_edit)
        
        # 结束日期
        condition_layout.addWidget(QLabel("结束日期:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setDate(QDate.currentDate())
        condition_layout.addWidget(self.end_date_edit)
        
        # 查询按钮
        self.search_btn = QPushButton("查询")
        self.search_btn.clicked.connect(self.on_search)
        condition_layout.addWidget(self.search_btn)
        
        layout.addLayout(condition_layout)
        
        # 结果表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "日期", "姓名", "扣分类型", "违规类型", "扣分原因", "扣分值", "处理措施"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # 设置表格为只读
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 连接双击事件
        self.table.doubleClicked.connect(self.on_table_double_click)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        # 初始化界面状态
        self.on_type_changed()
        
    def on_search(self):
        """执行查询"""
        name = self.name_edit.text().strip() or None
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        # 验证日期范围
        if self.start_date_edit.date() > self.end_date_edit.date():
            QMessageBox.warning(self, "警告", "开始日期不能晚于结束日期")
            return
            
        record_type = self.type_combo.currentData()
        violation_type = self.violation_type_combo.currentData()
        
        # 处理非违规类型查询
        non_violation_type = None
        if self.type_combo.currentData() == 2:  # 非违规类型
            selected_non_type = self.non_violation_type_combo.currentData()
            if selected_non_type is not None:
                non_violation_type = selected_non_type
        
        # 处理分数范围
        min_points = None
        if self.min_points_input.text():
            try:
                min_points = float(self.min_points_input.text())
            except ValueError:
                QMessageBox.warning(self, "警告", "最小分数必须是有效的数字")
                return
                
        max_points = None
        if self.max_points_input.text():
            try:
                max_points = float(self.max_points_input.text())
            except ValueError:
                QMessageBox.warning(self, "警告", "最大分数必须是有效的数字")
                return
                
        # 验证分数范围
        if min_points is not None and max_points is not None and min_points > max_points:
            QMessageBox.warning(self, "警告", "最小分数不能大于最大分数")
            return
        
        try:
            records = self.db.search_deduction_records(
                name=name,
                start_date=start_date,
                end_date=end_date,
                deduction_type=record_type,
                violation_type=violation_type,
                non_violation_type=non_violation_type,
                min_points=min_points,
                max_points=max_points
            )
            if not records:
                QMessageBox.information(self, "提示", "没有找到匹配的记录")
            self.display_results(records)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查询失败: {str(e)}")
            
    def on_type_changed(self):
        """当扣分类型改变时，更新相关控件的状态"""
        record_type = self.type_combo.currentData()
        
        # 根据选择的扣分类型启用或禁用相应的类型下拉框
        if record_type == 1:  # 违规
            self.violation_type_combo.setEnabled(True)
            self.non_violation_type_combo.setEnabled(False)
        elif record_type == 2:  # 非违规
            self.violation_type_combo.setEnabled(False)
            self.non_violation_type_combo.setEnabled(True)
        else:  # 全部
            self.violation_type_combo.setEnabled(True)
            self.non_violation_type_combo.setEnabled(True)
    
    def on_table_double_click(self, index):
        """处理表格双击事件，显示记录详情"""
        row = index.row()
        
        # 获取完整时间戳
        full_date = self.table.item(row, 0).data(Qt.UserRole)
        
        # 准备记录数据
        record_data = {
            "date": full_date,
            "name": self.table.item(row, 1).text(),
            "deduction_type": self.table.item(row, 2).text(),
            "violation_type": self.table.item(row, 3).text(),
            "reason": self.table.item(row, 4).text(),
            "points": self.table.item(row, 5).text(),
            "treatment_measures": self.table.item(row, 6).text()
        }
        
        # 创建并显示详情对话框
        detail_dialog = DeductionDetailDialog(record_data, self)
        detail_dialog.exec_()
        
    def display_results(self, records: list[DeductionRecord]):
        """显示查询结果"""
        self.table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            # 将datetime对象转换为字符串格式（只显示年月日）
            date_str = record.date.strftime("%Y-%m-%d")
            self.table.setItem(row, 0, QTableWidgetItem(date_str))
            # 存储完整时间戳到用户角色数据中
            full_date_str = record.date.strftime("%Y-%m-%d %H:%M:%S")
            self.table.item(row, 0).setData(Qt.UserRole, full_date_str)
            self.table.setItem(row, 1, QTableWidgetItem(record.student_name))
            self.table.setItem(row, 2, QTableWidgetItem(
                "违规" if record.deduction_type.value == 1 else "非违规"
            ))
            # 根据记录类型显示违规类型或非违规类型
            type_str = ""
            if record.deduction_type.value == 1:  # 违规
                if hasattr(record, 'violation_type') and record.violation_type:
                    type_str = record.violation_type.name
            else:  # 非违规
                if hasattr(record, 'non_violation_type') and record.non_violation_type:
                    type_str = record.non_violation_type
            self.table.setItem(row, 3, QTableWidgetItem(type_str))
            self.table.setItem(row, 4, QTableWidgetItem(record.reason))
            self.table.setItem(row, 5, QTableWidgetItem(str(record.points)))
            self.table.setItem(row, 6, QTableWidgetItem(record.treatment_measures))
            
        self.table.resizeColumnsToContents()


class AdditionSearchDialog(QDialog):
    """加分记录查询对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("加分记录查询")
        self.setMinimumSize(600, 400)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 查询条件区域
        condition_layout = QHBoxLayout()
        
        # 姓名输入
        condition_layout.addWidget(QLabel("姓名:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入学生姓名(可选)")
        condition_layout.addWidget(self.name_edit)
        
        # 分数范围筛选
        points_layout = QHBoxLayout()
        points_layout.addWidget(QLabel("分数范围:"))
        
        self.min_points_input = QLineEdit()
        self.min_points_input.setPlaceholderText("最小值")
        self.min_points_input.setValidator(QDoubleValidator(0, 100, 1))
        self.min_points_input.setMaximumWidth(80)
        points_layout.addWidget(self.min_points_input)
        
        points_layout.addWidget(QLabel("至"))
        
        self.max_points_input = QLineEdit()
        self.max_points_input.setPlaceholderText("最大值")
        self.max_points_input.setValidator(QDoubleValidator(0, 100, 1))
        self.max_points_input.setMaximumWidth(80)
        points_layout.addWidget(self.max_points_input)
        
        points_layout.addStretch()
        condition_layout.addLayout(points_layout)
        
        # 开始日期
        condition_layout.addWidget(QLabel("开始日期:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        condition_layout.addWidget(self.start_date_edit)
        
        # 结束日期
        condition_layout.addWidget(QLabel("结束日期:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setDate(QDate.currentDate())
        condition_layout.addWidget(self.end_date_edit)
        
        # 查询按钮
        self.search_btn = QPushButton("查询")
        self.search_btn.clicked.connect(self.on_search)
        condition_layout.addWidget(self.search_btn)
        
        layout.addLayout(condition_layout)
        
        # 结果表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "开始日期", "结束日期", "姓名", "加分原因", "加分值"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
    def on_search(self):
        """执行查询"""
        name = self.name_edit.text().strip() or None
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd") + "T00:00:00"
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd") + "T23:59:59"
        
        # 验证日期范围
        if self.start_date_edit.date() > self.end_date_edit.date():
            QMessageBox.warning(self, "警告", "开始日期不能晚于结束日期")
            return
            
        # 处理分数范围
        min_points = None
        if self.min_points_input.text():
            try:
                min_points = float(self.min_points_input.text())
            except ValueError:
                QMessageBox.warning(self, "警告", "最小分数必须是有效的数字")
                return
                
        max_points = None
        if self.max_points_input.text():
            try:
                max_points = float(self.max_points_input.text())
            except ValueError:
                QMessageBox.warning(self, "警告", "最大分数必须是有效的数字")
                return
                
        # 验证分数范围
        if min_points is not None and max_points is not None and min_points > max_points:
            QMessageBox.warning(self, "警告", "最小分数不能大于最大分数")
            return
        
        try:
            records = self.db.search_addition_records(
                student_name=name,
                start_date=start_date,
                end_date=end_date,
                min_points=min_points,
                max_points=max_points
            )
            if not records:
                QMessageBox.information(self, "提示", "没有找到匹配的记录")
            self.display_results(records)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查询失败: {str(e)}")
            
    def display_results(self, records: list[AdditionRecord]):
        """显示查询结果"""
        self.table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            # 将datetime对象转换为字符串格式
            start_date_str = record.start_date.strftime("%Y-%m-%d")
            end_date_str = record.end_date.strftime("%Y-%m-%d")
            
            self.table.setItem(row, 0, QTableWidgetItem(start_date_str))
            self.table.setItem(row, 1, QTableWidgetItem(end_date_str))
            self.table.setItem(row, 2, QTableWidgetItem(record.student_name))
            self.table.setItem(row, 3, QTableWidgetItem(record.reason))
            self.table.setItem(row, 4, QTableWidgetItem(str(record.points)))
            
        self.table.resizeColumnsToContents()


class DeductionDetailDialog(QDialog):
    """扣分记录详情对话框"""
    
    def __init__(self, record_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("扣分记录详情")
        self.setMinimumSize(400, 300)
        
        self.init_ui(record_data)
        
    def init_ui(self, record_data: dict):
        """初始化界面"""
        layout = QFormLayout()
        
        # 添加各个字段的显示
        layout.addRow("日期:", QLabel(record_data["date"]))
        layout.addRow("姓名:", QLabel(record_data["name"]))
        layout.addRow("扣分类型:", QLabel(record_data["deduction_type"]))
        layout.addRow("违规类型:", QLabel(record_data["violation_type"]))
        layout.addRow("扣分原因:", QLabel(record_data["reason"]))
        layout.addRow("扣分值:", QLabel(record_data["points"]))
        layout.addRow("处理措施:", QLabel(record_data["treatment_measures"]))
        
        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addRow(close_btn)
        
        self.setLayout(layout)