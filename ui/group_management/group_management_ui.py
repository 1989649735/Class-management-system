from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QInputDialog, QComboBox, QSpinBox, QFormLayout, QGroupBox,
    QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from ui.group_management.group_score_stats_dialog import GroupScoreStatsDialog

class GroupManagementUI(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("小组管理")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        
        # 功能栏
        function_bar = QHBoxLayout()
        
        # 添加功能按钮
        refresh_btn = QPushButton("刷新数据")
        refresh_btn.clicked.connect(self.refresh_all)
        
        export_btn = QPushButton("导出小组信息")
        export_btn.clicked.connect(self.export_group_info)
        
        score_stats_btn = QPushButton("小组分数统计")
        score_stats_btn.clicked.connect(self.show_group_score_stats)
        
        help_btn = QPushButton("帮助")
        help_btn.clicked.connect(self.show_help)
        
        function_bar.addWidget(refresh_btn)
        function_bar.addWidget(export_btn)
        function_bar.addWidget(score_stats_btn)
        function_bar.addWidget(help_btn)
        function_bar.addStretch()  # 添加弹性空间，使按钮靠左对齐
        
        # 将功能栏添加到主布局
        main_layout.addLayout(function_bar)
        
        # 顶部控制区域
        control_layout = QHBoxLayout()
        
        # 创建小组区域
        create_group_box = QGroupBox("创建小组")
        create_layout = QFormLayout()
        
        self.group_name_input = QLineEdit()
        self.group_desc_input = QLineEdit()
        create_btn = QPushButton("创建")
        create_btn.clicked.connect(self.create_group)
        
        create_layout.addRow("小组名称:", self.group_name_input)
        create_layout.addRow("小组描述:", self.group_desc_input)
        create_layout.addRow(create_btn)
        create_group_box.setLayout(create_layout)
        
        # 删除小组区域
        delete_group_box = QGroupBox("删除小组")
        delete_layout = QVBoxLayout()
        
        self.group_selector = QComboBox()
        self.refresh_group_selector()
        self.group_selector.currentIndexChanged.connect(self.on_group_changed)
        delete_btn = QPushButton("删除选中小组")
        delete_btn.clicked.connect(self.delete_group)
        
        delete_layout.addWidget(self.group_selector)
        delete_layout.addWidget(delete_btn)
        delete_group_box.setLayout(delete_layout)
        
        control_layout.addWidget(create_group_box)
        control_layout.addWidget(delete_group_box)
        
        # 成员管理区域
        member_management_box = QGroupBox("成员管理")
        member_layout = QVBoxLayout()
        
        # 成员表格
        self.member_table = QTableWidget()
        self.member_table.setColumnCount(3)
        self.member_table.setHorizontalHeaderLabels(["学号", "姓名", "操作"])
        self.member_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 添加成员区域
        add_member_layout = QHBoxLayout()
        self.student_selector = QComboBox()
        self.refresh_student_selector()
        add_btn = QPushButton("添加成员")
        add_btn.clicked.connect(self.add_member)
        
        add_member_layout.addWidget(self.student_selector)
        add_member_layout.addWidget(add_btn)
        
        member_layout.addWidget(self.member_table)
        member_layout.addLayout(add_member_layout)
        member_management_box.setLayout(member_layout)
        
        # 排名显示区域
        ranking_box = QGroupBox("小组排名")
        ranking_layout = QVBoxLayout()
        
        # 添加日期选择区域
        date_selection_layout = QHBoxLayout()
        
        date_selection_layout.addWidget(QLabel("开始日期:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))  # 默认显示最近30天
        date_selection_layout.addWidget(self.start_date_edit)
        
        date_selection_layout.addWidget(QLabel("结束日期:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())  # 默认显示到今天
        date_selection_layout.addWidget(self.end_date_edit)
        
        self.date_range_query_btn = QPushButton("按时间段查询")
        self.date_range_query_btn.clicked.connect(self.query_ranking_by_date_range)
        date_selection_layout.addWidget(self.date_range_query_btn)
        
        self.show_all_ranking_btn = QPushButton("显示全部排名")
        self.show_all_ranking_btn.clicked.connect(self.show_all_ranking)
        date_selection_layout.addWidget(self.show_all_ranking_btn)
        
        ranking_layout.addLayout(date_selection_layout)
        
        self.ranking_table = QTableWidget()
        self.ranking_table.setColumnCount(4)
        self.ranking_table.setHorizontalHeaderLabels(["排名", "小组名称", "成员数", "总分"])
        self.ranking_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        ranking_layout.addWidget(self.ranking_table)
        ranking_box.setLayout(ranking_layout)
        
        # 添加到主布局
        main_layout.addLayout(control_layout)
        main_layout.addWidget(member_management_box)
        main_layout.addWidget(ranking_box)
        
        self.setLayout(main_layout)
        
        # 初始加载数据
        self.refresh_all()

    def on_group_changed(self, index):
        """处理小组选择变化事件"""
        if index >= 0:
            self.refresh_member_table()
            self.refresh_student_selector()

    def refresh_all(self):
        self.refresh_group_selector()
        self.refresh_member_table()
        self.refresh_ranking_table()
        self.refresh_student_selector()

    def refresh_group_selector(self):
        self.group_selector.clear()
        groups = self.db.get_group_ranking()
        for group in groups:
            self.group_selector.addItem(f"{group['name']} (ID: {group['id']})", group['id'])

    def refresh_student_selector(self):
        self.student_selector.clear()
        current_group_id = self.group_selector.currentData()
        if current_group_id:
            # 查询当前小组成员
            self.db.cursor.execute(
                'SELECT student_name FROM student_groups WHERE group_id = ?',
                (current_group_id,)
            )
            current_member_names = [row['student_name'] for row in self.db.cursor.fetchall()]
            
            # 获取学生ID
            current_member_ids = []
            for name in current_member_names:
                self.db.cursor.execute('SELECT id FROM students WHERE name = ?', (name,))
                result = self.db.cursor.fetchone()
                if result:
                    current_member_ids.append(result['id'])
            
            all_students = self.db.get_students()
            available_students = [
                s for s in all_students 
                if s.id not in current_member_ids
            ]
            for student in available_students:
                # 确保存储的是学生ID，而不是学生对象
                self.student_selector.addItem(f"{student.name} (ID: {student.id})", student.id)

    def refresh_member_table(self):
        current_group_id = self.group_selector.currentData()
        if current_group_id:
            # 清空表格
            self.member_table.setRowCount(0)
            
            # 获取成员名称列表
            self.db.cursor.execute(
                'SELECT student_name FROM student_groups WHERE group_id = ?',
                (current_group_id,)
            )
            member_names = [row['student_name'] for row in self.db.cursor.fetchall()]
            
            # 获取学生ID
            member_ids = []
            for name in member_names:
                self.db.cursor.execute('SELECT id FROM students WHERE name = ?', (name,))
                result = self.db.cursor.fetchone()
                if result:
                    member_ids.append(result['id'])
            
            # 设置表格行数
            self.member_table.setRowCount(len(member_ids))
            
            # 填充表格
            for i, student_id in enumerate(member_ids):
                # 通过ID获取学生信息
                student = self.db.get_student_by_id(int(student_id))
                if not student:
                    print(f"警告: 找不到ID为{student_id}的学生")
                    continue
                
                # 学号
                id_item = QTableWidgetItem(str(student.id))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.member_table.setItem(i, 0, id_item)
                
                # 姓名
                name_item = QTableWidgetItem(student.name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.member_table.setItem(i, 1, name_item)
                
                # 删除按钮
                remove_btn = QPushButton("移除")
                remove_btn.clicked.connect(lambda _, row=i: self.remove_member(row))
                self.member_table.setCellWidget(i, 2, remove_btn)

    def refresh_ranking_table(self, ranking_data=None):
        """刷新排名表格，可以接受自定义排名数据"""
        if ranking_data is None:
            ranking = self.db.get_group_ranking()
        else:
            ranking = ranking_data
            
        self.ranking_table.setRowCount(len(ranking))
        
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
            rank_item = QTableWidgetItem(str(i + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ranking_table.setItem(i, 0, rank_item)
            
            # 小组名称
            name_item = QTableWidgetItem(group['name'])
            self.ranking_table.setItem(i, 1, name_item)
            
            # 成员数
            count_item = QTableWidgetItem(str(member_count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ranking_table.setItem(i, 2, count_item)
            
            # 总分
            score_item = QTableWidgetItem(f"{group['total_points']:.1f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ranking_table.setItem(i, 3, score_item)
            
    def query_ranking_by_date_range(self):
        """按时间段查询小组排名"""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        # 检查输入的日期与已有锁定段时间是否不同
        locked_ranges = self.db.get_locked_date_ranges()
        date_in_locked_range = False
        matching_range = None
        
        for locked_range in locked_ranges:
            locked_start = locked_range['start_date']
            locked_end = locked_range['end_date']
            
            # 检查输入的日期是否与某个锁定段完全匹配
            if start_date == locked_start and end_date == locked_end:
                date_in_locked_range = True
                matching_range = locked_range
                break
        
        # 如果日期与已有锁定段不同，提示用户
        if not date_in_locked_range and locked_ranges:
            msg = "输入的日期与已有锁定段时间不同，是否继续排名？\n\n"
            msg += "已有锁定段时间:\n"
            
            for i, locked_range in enumerate(locked_ranges):
                msg += f"{i+1}. {locked_range['start_date']} 至 {locked_range['end_date']}\n"
            
            msg += "\n您可以选择继续使用当前日期，或者自动校准到最近的锁定段时间。"
            
            reply = QMessageBox.question(
                self, 
                "日期不匹配", 
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.No:
                # 自动校准到最近的锁定段时间
                if locked_ranges:
                    # 默认使用第一个锁定段
                    auto_range = locked_ranges[0]
                    
                    # 如果有多个锁定段，让用户选择
                    if len(locked_ranges) > 1:
                        items = [f"{r['start_date']} 至 {r['end_date']}" for r in locked_ranges]
                        selected, ok = QInputDialog.getItem(
                            self, 
                            "选择锁定段", 
                            "请选择要使用的锁定段时间:", 
                            items, 
                            0, 
                            False
                        )
                        
                        if ok and selected:
                            index = items.index(selected)
                            auto_range = locked_ranges[index]
                    
                    # 更新日期选择器
                    start_date = auto_range['start_date']
                    end_date = auto_range['end_date']
                    
                    # 更新UI上的日期选择器
                    self.start_date_edit.setDate(QDate.fromString(start_date, "yyyy-MM-dd"))
                    self.end_date_edit.setDate(QDate.fromString(end_date, "yyyy-MM-dd"))
                    
                    QMessageBox.information(
                        self, 
                        "日期已校准", 
                        f"日期已自动校准为: {start_date} 至 {end_date}"
                    )
        
        try:
            ranking_data = self.db.get_group_ranking_by_date_range(start_date, end_date)
            self.refresh_ranking_table(ranking_data)
            
            # 更新标题显示时间范围
            self.ranking_table.setHorizontalHeaderLabels([
                "排名", 
                "小组名称", 
                "成员数", 
                f"总分 ({start_date} 至 {end_date})"
            ])
            
            # 打开详细排名对话框
            from ui.group_management.group_ranking_dialog import GroupRankingByDateRangeDialog
            dialog = GroupRankingByDateRangeDialog(self.db, self)
            # 设置日期范围
            dialog.start_date_edit.setDate(QDate.fromString(start_date, "yyyy-MM-dd"))
            dialog.end_date_edit.setDate(QDate.fromString(end_date, "yyyy-MM-dd"))
            # 加载数据
            dialog.load_data()
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "查询失败", f"按时间段查询小组排名失败: {str(e)}")
    
    def show_all_ranking(self):
        """显示全部排名"""
        self.refresh_ranking_table()
        # 恢复原始标题
        self.ranking_table.setHorizontalHeaderLabels(["排名", "小组名称", "成员数", "总分"])

    def create_group(self):
        name = self.group_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "错误", "小组名称不能为空")
            return
            
        desc = self.group_desc_input.text().strip()
        if self.db.create_group(name, desc if desc else None):
            QMessageBox.information(self, "成功", "小组创建成功")
            self.group_name_input.clear()
            self.group_desc_input.clear()
            self.refresh_all()
        else:
            QMessageBox.warning(self, "错误", "小组创建失败")

    def delete_group(self):
        current_group_id = self.group_selector.currentData()
        if not current_group_id:
            return
            
        group_name = self.group_selector.currentText()
        if QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除小组 {group_name} 吗？这将删除该小组的所有成员和加分记录！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            if self.db.delete_group(current_group_id):
                QMessageBox.information(self, "成功", "小组删除成功")
                self.refresh_all()
            else:
                QMessageBox.warning(self, "错误", "小组删除失败")

    def add_member(self):
        current_group_id = self.group_selector.currentData()
        if not current_group_id:
            return
            
        # 检查小组成员数量是否已达到上限
        self.db.cursor.execute(
            'SELECT student_name FROM student_groups WHERE group_id = ?',
            (current_group_id,)
        )
        member_names = [row['student_name'] for row in self.db.cursor.fetchall()]
        if len(member_names) >= 7:
            QMessageBox.warning(self, "错误", "小组成员已达到上限（最多7人）")
            return
            
        student_id = self.student_selector.currentData()
        if not student_id:
            return
            
        try:
            # 获取学生姓名
            student = None
            for s in self.db.get_students():
                if s.id == student_id:
                    student = s
                    break
                    
            if not student:
                QMessageBox.warning(self, "错误", "找不到选中的学生")
                return
                
            if self.db.add_student_to_group(student_id, current_group_id):
                QMessageBox.information(self, "成功", "成员添加成功")
                # 先刷新成员表格，确保新成员显示
                self.refresh_member_table()
                # 然后刷新学生选择器，移除已添加的学生
                self.refresh_student_selector()
                # 最后刷新排名表格
                self.refresh_ranking_table()
            else:
                # 检查学生是否已经在其他小组中
                self.db.cursor.execute(
                    'SELECT sg.group_id, g.name FROM student_groups sg '
                    'JOIN groups g ON sg.group_id = g.id '
                    'WHERE sg.student_name = (SELECT name FROM students WHERE id = ?)',
                    (student_id,)
                )
                existing_group = self.db.cursor.fetchone()
                
                if existing_group:
                    QMessageBox.warning(self, "错误", f"成员添加失败：该学生已经在小组 '{existing_group['name']}' 中。一个学生只能加入一个小组。")
                else:
                    QMessageBox.warning(self, "错误", "成员添加失败")
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))

    def remove_member(self, row):
        current_group_id = self.group_selector.currentData()
        if not current_group_id:
            return
            
        # 获取学生ID和姓名
        student_id = int(self.member_table.item(row, 0).text())
        student_name = self.member_table.item(row, 1).text()
        
        print(f"尝试移除学生 - ID:{student_id}, 姓名:{student_name}, 小组ID:{current_group_id}")
        
        if QMessageBox.question(
            self,
            "确认移除",
            f"确定要从小组中移除 {student_name} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            # 先检查学生是否存在
            student = self.db.get_student_by_id(student_id)
            if not student:
                QMessageBox.warning(self, "错误", f"找不到ID为{student_id}的学生")
                return
                
            print(f"找到学生 - ID:{student.id}, 姓名:{student.name}")
            
            if self.db.remove_student_from_group(current_group_id, student_id):
                QMessageBox.information(self, "成功", "成员移除成功")
                # 先刷新成员表格，确保成员被移除
                self.refresh_member_table()
                # 然后刷新学生选择器，添加被移除的学生
                self.refresh_student_selector()
                # 最后刷新排名表格
                self.refresh_ranking_table()
            else:
                QMessageBox.warning(self, "错误", "成员移除失败，请确保该学生在小组中")
            
    def show_group_score_stats(self):
        """显示小组分数统计对话框"""
        current_group_id = self.group_selector.currentData()
        if not current_group_id:
            QMessageBox.warning(self, "错误", "请先选择一个小组")
            return
            
        dialog = GroupScoreStatsDialog(self, self.db, current_group_id)
        dialog.exec_()

    def show_help(self):
        """显示帮助信息"""
        help_text = """
        <p><b>创建小组</b>：输入小组名称和描述后点击创建按钮</p>
        <p><b>删除小组</b>：从下拉框选择小组后点击删除按钮</p>
        <p><b>添加成员</b>：从学生列表选择学生后点击添加按钮</p>
        <p><b>移除成员</b>：点击成员表格中的移除按钮</p>
        <p><b>小组分数统计</b>：查看小组的详细分数分布</p>
        <p><b>导出小组信息</b>：将所有小组信息导出到文本文件</p>
        <p><b>按时间段查询</b>：选择开始和结束日期，查询特定时间段内的小组排名</p>
        """
        QMessageBox.information(self, "帮助", help_text)

    def export_group_info(self):
        """导出小组信息到文本文件"""
        import os
        from datetime import datetime
        
        try:
            # 创建导出目录
            export_dir = os.path.join(os.getcwd(), "exports")
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
                
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"group_export_{timestamp}.txt"
            filepath = os.path.join(export_dir, filename)
            
            # 获取所有小组信息
            groups = self.db.get_group_ranking()
            
            # 写入文件
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("小组信息导出\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for group in groups:
                    f.write(f"小组名称: {group['name']}\n")
                    f.write(f"小组ID: {group['id']}\n")
                    if group['description']:
                        f.write(f"描述: {group['description']}\n")
                    
                    # 获取小组成员
                    self.db.cursor.execute(
                        'SELECT student_name FROM student_groups WHERE group_id = ?',
                        (group['id'],)
                    )
                    member_names = [row['student_name'] for row in self.db.cursor.fetchall()]
                    f.write(f"成员数: {len(member_names)}\n")
                    f.write("成员列表:\n")
                    
                    for member_name in member_names:
                        self.db.cursor.execute('SELECT * FROM students WHERE name = ?', (member_name,))
                        student_row = self.db.cursor.fetchone()
                        if student_row:
                            student_id = student_row['id']
                            student = self.db.get_student_by_id(student_id)
                        if student:
                            f.write(f"  - {student.name} (ID: {student.id})\n")
                    
                    f.write("\n")  # 小组间空行
            
            QMessageBox.information(self, "导出成功", f"小组信息已导出到:\n{filepath}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出过程中发生错误:\n{str(e)}")