from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QRadioButton
)
from PyQt5.QtCore import Qt, QDate
from typing import Optional, List, Dict, Any
from database import Database
from ui.search_dialog import DeductionSearchDialog


class ViolationCountDialog(QDialog):
    """违规次数查询对话框"""
    
    def __init__(self, database: Database, parent=None):
        super().__init__(parent)
        self.database = database
        self.setWindowTitle("违规次数查询")
        self.resize(600, 400)
        
        self.init_ui()
        self.load_students()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 查询条件区域
        query_group = QGroupBox("查询条件")
        query_layout = QVBoxLayout()
        
        # 学生选择
        student_layout = QHBoxLayout()
        student_layout.addWidget(QLabel("学生:"))
        self.student_combo = QComboBox()
        self.student_combo.addItem("全部学生", None)
        student_layout.addWidget(self.student_combo)
        query_layout.addLayout(student_layout)
        
        # 日期范围选择
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("开始日期:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.start_date_edit)
        
        date_layout.addWidget(QLabel("结束日期:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date_edit)
        query_layout.addLayout(date_layout)
        
        # 查询按钮
        button_layout = QHBoxLayout()
        self.query_button = QPushButton("查询")
        self.query_button.clicked.connect(self.on_query)
        button_layout.addStretch()
        button_layout.addWidget(self.query_button)
        query_layout.addLayout(button_layout)
        
        query_group.setLayout(query_layout)
        layout.addWidget(query_group)
        
        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["学生", "时间段", "违规次数"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 设置表格为只读模式
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # 添加表格单元格点击事件
        self.result_table.cellClicked.connect(self.on_cell_clicked)
        layout.addWidget(self.result_table)
        
        self.setLayout(layout)
        
    def load_students(self):
        """加载学生列表"""
        students = self.database.get_students()
        for student in students:
            self.student_combo.addItem(student.name, student.name)
            
    def on_query(self):
        """执行查询"""
        # 获取查询参数
        student_name = self.student_combo.currentData()
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        # 执行查询
        results = self.database.count_violations_by_date_range(
            student_name=student_name,
            start_date=start_date,
            end_date=end_date
        )
        
        # 显示结果
        self.display_results(results)
        
    def on_cell_clicked(self, row: int, column: int):
        """处理表格单元格点击事件"""
        # 检查点击的是否是学生姓名单元格（第0列）
        if column == 0:
            # 获取学生姓名
            student_name = self.result_table.item(row, 0).text()
            
            # 创建并显示扣分查询对话框
            search_dialog = DeductionSearchDialog(self.database, self)
            # 设置学生姓名
            search_dialog.name_edit.setText(student_name)
            # 设置日期范围（从当前对话框获取）
            search_dialog.start_date_edit.setDate(self.start_date_edit.date())
            search_dialog.end_date_edit.setDate(self.end_date_edit.date())
            # 显示对话框
            search_dialog.exec_()
    
    def display_results(self, results: List[Dict[str, Any]]):
        """显示查询结果"""
        self.result_table.setRowCount(0)
        
        # 按违规次数降序排序
        sorted_results = sorted(results, key=lambda x: x["count"], reverse=True)
        
        for row, result in enumerate(sorted_results):
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(result["student_name"]))
            self.result_table.setItem(row, 1, QTableWidgetItem(result["period"]))
            self.result_table.setItem(row, 2, QTableWidgetItem(str(result["count"])))
            
        # 如果没有结果，显示提示信息
        if len(results) == 0:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "查询结果", "在指定日期范围内没有找到违规记录")