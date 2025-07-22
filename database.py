#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from models import Student, DeductionRecord, CompensationRecord, AdditionRecord, DeductionType, STUDENT_LIST

class Database:
    """数据库类"""
    
    def __init__(self, db_path: str = "student_score.db"):
        """初始化数据库"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # 连接数据库
        self.connect()
        
        # 初始化数据库
        self.init_db()
        
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        self.cursor = self.conn.cursor()
        
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            
    def init_db(self):
        """初始化数据库"""
        # 创建学生表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            initial_score REAL DEFAULT 0.0
        )
        ''')
        
        # 创建扣分记录表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS deduction_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            points REAL NOT NULL,
            violation_behavior TEXT,
            treatment_measures TEXT,
            date TEXT NOT NULL,
            deduction_type INTEGER NOT NULL,
            violation_type INTEGER,
            FOREIGN KEY (student_name) REFERENCES students (name)
        )
        ''')
        
        # 创建索引
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_deduction_student_name ON deduction_records(student_name)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_deduction_date ON deduction_records(date)')
        
        # 检查deduction_records表的结构
        self.cursor.execute("PRAGMA table_info(deduction_records)")
        columns = {column[1]: column for column in self.cursor.fetchall()}
        
        # 检查并添加缺失的字段
        if 'violation_behavior' not in columns:
            self.cursor.execute('''
            ALTER TABLE deduction_records ADD COLUMN violation_behavior TEXT
            ''')
            
        if 'treatment_measures' not in columns:
            self.cursor.execute('''
            ALTER TABLE deduction_records ADD COLUMN treatment_measures TEXT
            ''')
            
        # 检查是否存在reason字段
        if 'reason' in columns:
            # 如果存在且有NOT NULL约束，则修改为可为NULL
            if columns['reason'][3] == 1:  # 第3个元素是notnull约束
                # SQLite不支持直接修改列约束，需要创建新表并复制数据
                self.cursor.execute('''
                CREATE TABLE deduction_records_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT NOT NULL,
                    points REAL NOT NULL,
                    violation_behavior TEXT,
                    treatment_measures TEXT,
                    date TEXT NOT NULL,
                    deduction_type INTEGER NOT NULL,
                    violation_type INTEGER,
                    reason TEXT,
                    non_violation_type TEXT,
                    FOREIGN KEY (student_name) REFERENCES students (name)
                )
                ''')
                
                # 获取所有列名
                self.cursor.execute("PRAGMA table_info(deduction_records)")
                column_names = [column[1] for column in self.cursor.fetchall()]
                columns_str = ", ".join(column_names)
                
                # 复制数据
                self.cursor.execute(f'''
                INSERT INTO deduction_records_new 
                SELECT {columns_str}
                FROM deduction_records
                ''')
                
                # 删除旧表并重命名新表
                self.cursor.execute('DROP TABLE deduction_records')
                self.cursor.execute('ALTER TABLE deduction_records_new RENAME TO deduction_records')
        else:
            # 如果不存在reason字段，添加它
            self.cursor.execute('''
            ALTER TABLE deduction_records ADD COLUMN reason TEXT
            ''')
            
        # 检查是否存在non_violation_type字段
        self.cursor.execute("PRAGMA table_info(deduction_records)")
        columns = {column[1]: column for column in self.cursor.fetchall()}
        if 'non_violation_type' not in columns:
            self.cursor.execute('''
            ALTER TABLE deduction_records ADD COLUMN non_violation_type TEXT
            ''')
        
        # 创建补偿记录表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS compensation_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deduction_record_id INTEGER NOT NULL,
            old_points REAL NOT NULL,
            new_points REAL NOT NULL,
            reason TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (deduction_record_id) REFERENCES deduction_records (id)
        )
        ''')
        
        # 创建加分记录表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS addition_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            points REAL NOT NULL,
            reason TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            FOREIGN KEY (student_name) REFERENCES students (name)
        )
        ''')
        
        # 创建小组表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
        )
        ''')
        
        # 创建学生分组表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            group_id INTEGER NOT NULL,
            join_date TEXT NOT NULL,
            FOREIGN KEY (student_name) REFERENCES students (name),
            FOREIGN KEY (group_id) REFERENCES groups (id)
        )
        ''')
        
        # 创建小组加分记录表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_addition_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            points REAL NOT NULL,
            reason TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (group_id) REFERENCES groups (id)
        )
        ''')
        
        # 创建配置表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        ''')
        
        # 创建锁定时间段表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS locked_time_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        ''')
        
        # 初始化学生数据
        for student_name in STUDENT_LIST:
            self.cursor.execute('SELECT * FROM students WHERE name = ?', (student_name,))
            if not self.cursor.fetchone():
                self.cursor.execute('INSERT INTO students (name) VALUES (?)', (student_name,))
                
        self.conn.commit()
        
    # 学生相关方法
    def get_students(self) -> List[Student]:
        """获取所有学生"""
        self.cursor.execute('SELECT * FROM students ORDER BY name')
        rows = self.cursor.fetchall()
        return [Student.from_dict(dict(row)) for row in rows]
        
    def get_student(self, name: str) -> Optional[Student]:
        """获取指定学生"""
        self.cursor.execute('SELECT * FROM students WHERE name = ?', (name,))
        row = self.cursor.fetchone()
        return Student.from_dict(dict(row)) if row else None
        
    def get_student_by_id(self, student_id: int) -> Optional[Student]:
        """通过ID获取学生"""
        self.cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        row = self.cursor.fetchone()
        return Student.from_dict(dict(row)) if row else None
        
    def update_student_initial_score(self, name: str, initial_score: float) -> bool:
        """更新学生初始分数"""
        try:
            self.cursor.execute(
                'UPDATE students SET initial_score = ? WHERE name = ?',
                (initial_score, name)
            )
            self.conn.commit()
            return True
        except Exception as e:
            return False
            
    # 扣分记录相关方法
    def add_deduction_record(self, record: DeductionRecord) -> bool:
        """添加扣分记录
        
        参数:
            record: DeductionRecord对象，包含:
                - student_name: 学生姓名
                - points: 扣分分值
                - violation_behavior: 违规具体行为(可选)
                - treatment_measures: 处理措施(可选)
                - date: 扣分日期
                - deduction_type: 扣分类型
                - violation_type: 违规类型(可选)
                - reason: 扣分原因(可选)
                - non_violation_type: 非违规类型(可选)
        """
        try:
            self.cursor.execute(
                '''
                INSERT INTO deduction_records 
                (student_name, points, violation_behavior, treatment_measures, date, deduction_type, violation_type, reason, non_violation_type) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    record.student_name,
                    record.points,
                    record.violation_behavior,
                    record.treatment_measures,
                    record.date.isoformat(),
                    record.deduction_type.value,
                    record.violation_type.value if record.violation_type else None,
                    record.reason,
                    record.non_violation_type
                )
            )
            record.id = self.cursor.lastrowid
            self.conn.commit()
            return True
        except Exception as e:
            print(f"添加扣分记录失败: {e}")
            return False
            
    def add_batch_deduction_records(self, records: List[DeductionRecord]) -> bool:
        """批量添加扣分记录
        
        参数:
            records: DeductionRecord对象列表，每个对象包含:
                - student_name: 学生姓名
                - points: 扣分分值
                - violation_behavior: 违规具体行为(可选)
                - treatment_measures: 处理措施(可选)
                - date: 扣分日期
                - deduction_type: 扣分类型
                - violation_type: 违规类型(可选)
                - reason: 扣分原因(可选)
                - non_violation_type: 非违规类型(可选)
        """
        try:
            for record in records:
                self.cursor.execute(
                    '''
                    INSERT INTO deduction_records 
                    (student_name, points, violation_behavior, treatment_measures, date, deduction_type, violation_type, reason, non_violation_type) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        record.student_name,
                        record.points,
                        record.violation_behavior,
                        record.treatment_measures,
                        record.date.isoformat(),
                        record.deduction_type.value,
                        record.violation_type.value if record.violation_type else None,
                        record.reason,
                        record.non_violation_type
                    )
                )
                record.id = self.cursor.lastrowid
            self.conn.commit()
            return True
        except Exception as e:
            print(f"批量添加扣分记录失败: {e}")
            return False
            
    def get_deduction_records(self, student_name: str) -> List[DeductionRecord]:
        """获取指定学生的扣分记录"""
        self.cursor.execute(
            'SELECT * FROM deduction_records WHERE student_name = ? ORDER BY date DESC',
            (student_name,)
        )
        rows = self.cursor.fetchall()
        return [DeductionRecord.from_dict(dict(row)) for row in rows]
        
    def update_deduction_record_points_and_treatment(self, record_id: int, new_points: float, treatment_measures: str, compensation_record: CompensationRecord = None) -> bool:
        """更新扣分记录的扣分值和处理措施
        
        参数:
            record_id: 扣分记录ID
            new_points: 新的扣分值
            treatment_measures: 新的处理措施
            compensation_record: 补偿记录对象(可选)，如果提供则同时添加补偿记录
            
        返回:
            bool: 操作是否成功
            如果新扣分值大于原值，将引发ValueError
        """
        try:
            # 获取原扣分值
            self.cursor.execute(
                'SELECT points FROM deduction_records WHERE id = ?',
                (record_id,)
            )
            original_points = self.cursor.fetchone()['points']
            
            # 验证新扣分值
            if new_points > original_points:
                raise ValueError("补偿后扣分不能大于原扣分值")
                
            # 开始事务
            self.conn.execute('BEGIN TRANSACTION')
            
            # 更新扣分记录
            self.cursor.execute(
                'UPDATE deduction_records SET points = ?, treatment_measures = ? WHERE id = ?',
                (new_points, treatment_measures, record_id)
            )
            
            # 如果提供了补偿记录，则添加到数据库
            if compensation_record:
                # 确保补偿记录中的值一致
                compensation_record.old_points = original_points
                compensation_record.new_points = new_points
                
                self.cursor.execute(
                    '''
                    INSERT INTO compensation_records 
                    (deduction_record_id, old_points, new_points, reason, date) 
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (
                        compensation_record.deduction_record_id,
                        compensation_record.old_points,
                        compensation_record.new_points,
                        compensation_record.reason,
                        compensation_record.date.isoformat()
                    )
                )
                compensation_record.id = self.cursor.lastrowid
            
            # 提交事务
            self.conn.commit()
            return True
        except ValueError as e:
            # 回滚事务
            if self.conn:
                self.conn.rollback()
            raise e  # 重新抛出验证错误
        except Exception as e:
            # 回滚事务
            if self.conn:
                self.conn.rollback()
            print(f"更新扣分记录失败: {e}")
            return False
        
    # 补偿记录相关方法
    def add_compensation_record(self, record: CompensationRecord) -> bool:
        """添加补偿记录"""
        try:
            self.cursor.execute(
                '''
                INSERT INTO compensation_records 
                (deduction_record_id, old_points, new_points, reason, date) 
                VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    record.deduction_record_id,
                    record.old_points,
                    record.new_points,
                    record.reason,
                    record.date.isoformat()
                )
            )
            record.id = self.cursor.lastrowid
            self.conn.commit()
            return True
        except Exception as e:
            print(f"添加补偿记录失败: {e}")
            return False
            
    def get_compensation_records(self, deduction_record_id: int) -> List[CompensationRecord]:
        """获取指定扣分记录的补偿记录"""
        self.cursor.execute(
            'SELECT * FROM compensation_records WHERE deduction_record_id = ? ORDER BY date DESC',
            (deduction_record_id,)
        )
        rows = self.cursor.fetchall()
        return [CompensationRecord.from_dict(dict(row)) for row in rows]
        
    def get_deduction_record_modifications(self, deduction_record_id: int) -> List[Dict[str, Any]]:
        """获取扣分记录的修改历史"""
        # 获取扣分记录
        self.cursor.execute(
            'SELECT * FROM deduction_records WHERE id = ?',
            (deduction_record_id,)
        )
        deduction_record = self.cursor.fetchone()
        if not deduction_record:
            return []
            
        # 获取补偿记录
        compensation_records = self.get_compensation_records(deduction_record_id)
        
        # 转换为修改历史格式
        modifications = []
        
        for record in compensation_records:
            modifications.append({
                'date': record.date,
                'old_points': record.old_points,
                'new_points': record.new_points,
                'reason': record.reason
            })
            
        return modifications
        
    def get_student_compensation_records(self, student_name: str) -> List[CompensationRecord]:
        """获取指定学生的所有补偿记录"""
        self.cursor.execute(
            '''
            SELECT c.* FROM compensation_records c
            JOIN deduction_records d ON c.deduction_record_id = d.id
            WHERE d.student_name = ?
            ORDER BY c.date DESC
            ''',
            (student_name,)
        )
        rows = self.cursor.fetchall()
        return [CompensationRecord.from_dict(dict(row)) for row in rows]
        
    # 小组相关方法
    def get_group_ranking(self) -> List[Dict[str, Any]]:
        """获取小组排名，基于小组成员个人加分的总和
        
        返回:
            按总分降序排序的小组列表，每个小组包含:
            - id: 小组ID
            - name: 小组名称
            - total_points: 小组总分(成员个人加分总和)
        """
        # 获取所有小组
        self.cursor.execute('SELECT * FROM groups')
        groups = [dict(row) for row in self.cursor.fetchall()]
        
        group_ranking = []
        
        for group in groups:
            # 获取小组成员
            self.cursor.execute(
                '''
                SELECT student_name FROM student_groups 
                WHERE group_id = ?
                ''',
                (group['id'],)
            )
            members = [row['student_name'] for row in self.cursor.fetchall()]
            
            total_points = 0.0
            
            # 计算每个成员的加分总和
            for member in members:
                self.cursor.execute(
                    '''
                    SELECT COALESCE(SUM(points), 0) as sum_points 
                    FROM addition_records 
                    WHERE student_name = ?
                    ''',
                    (member,)
                )
                result = self.cursor.fetchone()
                total_points += result['sum_points']
            
            group_ranking.append({
                'id': group['id'],
                'name': group['name'],
                'total_points': total_points
            })
        
        # 按总分降序排序
        group_ranking.sort(key=lambda x: x['total_points'], reverse=True)
        
        return group_ranking
        
    def get_group_ranking_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取指定时间段内的小组排名，基于小组成员在该时间段内的个人加分总和
        
        参数:
            start_date: 开始日期 (格式: 'YYYY-MM-DD')，包含当天
            end_date: 结束日期 (格式: 'YYYY-MM-DD')，包含当天
            
        返回:
            按总分降序排序的小组列表，每个小组包含:
            - id: 小组ID
            - name: 小组名称
            - total_points: 小组在指定时间段内的总分(成员个人加分总和)
        """
        # 获取所有小组
        self.cursor.execute('SELECT * FROM groups')
        groups = [dict(row) for row in self.cursor.fetchall()]
        
        group_ranking = []
        
        for group in groups:
            # 获取小组成员
            self.cursor.execute(
                '''
                SELECT student_name FROM student_groups 
                WHERE group_id = ?
                ''',
                (group['id'],)
            )
            members = [row['student_name'] for row in self.cursor.fetchall()]
            
            total_points = 0.0
            
            # 计算每个成员在指定时间段内的加分总和
            for member in members:
                self.cursor.execute(
                    '''
                    SELECT COALESCE(SUM(points), 0) as sum_points 
                    FROM addition_records 
                    WHERE student_name = ?
                    AND start_date <= ?
                    AND end_date >= ?
                    ''',
                    (member, end_date, start_date)
                )
                result = self.cursor.fetchone()
                total_points += result['sum_points']
            
            group_ranking.append({
                'id': group['id'],
                'name': group['name'],
                'total_points': total_points
            })
        
        # 按总分降序排序
        group_ranking.sort(key=lambda x: x['total_points'], reverse=True)
        
        return group_ranking
        
    # 加分记录相关方法
    def add_addition_record(self, record: AdditionRecord) -> bool:
        """添加加分记录"""
        try:
            # 检查是否有重叠的时间段
            self.cursor.execute(
                '''
                SELECT * FROM addition_records 
                WHERE student_name = ? AND 
                (
                    (start_date <= ? AND end_date >= ?) OR
                    (start_date <= ? AND end_date >= ?) OR
                    (start_date >= ? AND end_date <= ?)
                )
                ''',
                (
                    record.student_name,
                    record.end_date.isoformat(), record.start_date.isoformat(),
                    record.start_date.isoformat(), record.start_date.isoformat(),
                    record.start_date.isoformat(), record.end_date.isoformat()
                )
            )
            if self.cursor.fetchone():
                raise ValueError("该时间段内已存在加分记录")
                
            self.cursor.execute(
                '''
                INSERT INTO addition_records 
                (student_name, points, reason, start_date, end_date) 
                VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    record.student_name,
                    record.points,
                    record.reason,
                    record.start_date.isoformat(),
                    record.end_date.isoformat()
                )
            )
            record.id = self.cursor.lastrowid
            self.conn.commit()
            return True
        except ValueError as e:
            raise e
        except Exception as e:
            print(f"添加加分记录失败: {e}")
            return False
            
    def get_addition_records(self, student_name: str) -> List[AdditionRecord]:
        """获取指定学生的加分记录
        
        参数:
            student_name: 学生姓名
            
        返回:
            按日期降序排序的AdditionRecord对象列表
        """
        self.cursor.execute(
            '''
            SELECT * FROM addition_records 
            WHERE student_name = ? 
            ORDER BY start_date DESC
            ''',
            (student_name,)
        )
        rows = self.cursor.fetchall()
        return [AdditionRecord.from_dict(dict(row)) for row in rows]
    
    def count_violations_by_date_range(self, student_name: Optional[str], start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """统计指定日期范围内的违规次数
        
        参数:
            student_name: 学生姓名，如果为None则查询所有学生
            start_date: 开始日期，格式为'yyyy-MM-dd'
            end_date: 结束日期，格式为'yyyy-MM-dd'
            
        返回:
            包含统计结果的字典列表，每个字典包含:
            - student_name: 学生姓名
            - period: 时间段描述
            - count: 违规次数
        """
        results = []
        
        # 构建查询条件
        query = '''
            SELECT student_name, COUNT(*) as violation_count
            FROM deduction_records
            WHERE date BETWEEN ? AND ?
            AND deduction_type = 1  -- 违规扣分类型
        '''
        params = [start_date, end_date]
        
        # 如果指定了学生，添加学生筛选条件
        if student_name:
            query += ' AND student_name = ?'
            params.append(student_name)
            
        # 按学生分组
        query += ' GROUP BY student_name'
        
        # 执行查询
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        # 格式化时间段描述
        period = f"{start_date} 至 {end_date}"
        
        # 构建结果
        for row in rows:
            results.append({
                "student_name": row['student_name'],
                "period": period,
                "count": row['violation_count']
            })
            
        return results
        
    # 小组成员管理方法
    def add_student_to_group(self, student_id: int, group_id: int) -> bool:
        """将学生添加到小组
        
        参数:
            student_id: 学生ID
            group_id: 小组ID
            
        返回:
            bool: 操作是否成功
            
        说明:
            一个学生只能加入一个小组，如果学生已经在其他小组中，将返回False
        """
        try:
            # 获取学生姓名
            self.cursor.execute('SELECT name FROM students WHERE id = ?', (student_id,))
            student = self.cursor.fetchone()
            if not student:
                return False
                
            student_name = student['name']
            
            # 检查学生是否已在该小组
            self.cursor.execute(
                'SELECT * FROM student_groups WHERE student_name = ? AND group_id = ?',
                (student_name, group_id)
            )
            if self.cursor.fetchone():
                return False  # 学生已在小组中
                
            # 检查学生是否已在其他小组中
            self.cursor.execute(
                'SELECT * FROM student_groups WHERE student_name = ?',
                (student_name,)
            )
            if self.cursor.fetchone():
                return False  # 学生已在其他小组中
                
            # 添加学生到小组
            current_date = datetime.now().strftime('%Y-%m-%d')
            self.cursor.execute(
                'INSERT INTO student_groups (student_name, group_id, join_date) VALUES (?, ?, ?)',
                (student_name, group_id, current_date)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"添加学生到小组失败: {e}")
            return False
            
    def remove_student_from_group(self, group_id: int, student_id: int) -> bool:
        """从小组中移除学生
        
        参数:
            group_id: 小组ID
            student_id: 学生ID
            
        返回:
            bool: 操作是否成功
        """
        try:
            # 获取学生姓名
            self.cursor.execute('SELECT name FROM students WHERE id = ?', (student_id,))
            student = self.cursor.fetchone()
            if not student:
                return False
                
            student_name = student['name']
            
            # 从小组中移除学生
            self.cursor.execute(
                'DELETE FROM student_groups WHERE student_name = ? AND group_id = ?',
                (student_name, group_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"从小组中移除学生失败: {e}")
            return False
            
    def get_groups(self) -> List[Dict[str, Any]]:
        """获取所有小组列表
        
        返回:
            包含所有小组的列表，每个小组是一个字典，包含:
            - id: 小组ID
            - name: 小组名称
            - description: 小组描述
            - created_at: 创建时间
        """
        self.cursor.execute('SELECT * FROM groups ORDER BY name')
        return [dict(row) for row in self.cursor.fetchall()]
        
    def get_locked_time_periods(self) -> List[Dict[str, Any]]:
        """获取所有锁定时间段
        
        返回:
            包含所有锁定时间段的列表，每个时间段是一个字典，包含:
            - id: 时间段ID
            - name: 时间段名称
            - start_date: 开始日期
            - end_date: 结束日期
            - created_at: 创建时间
        """
        self.cursor.execute('SELECT * FROM locked_time_periods ORDER BY start_date DESC')
        return [dict(row) for row in self.cursor.fetchall()]
        
    def get_locked_date_ranges(self) -> List[Dict[str, Any]]:
        """获取所有锁定的日期范围
        
        返回:
            包含所有锁定日期范围的列表，每个范围是一个字典，包含:
            - start_date: 开始日期
            - end_date: 结束日期
        """
        self.cursor.execute('SELECT start_date, end_date FROM locked_time_periods ORDER BY start_date DESC')
        return [dict(row) for row in self.cursor.fetchall()]
    
    def add_locked_time_period(self, name: str, start_date: str, end_date: str) -> bool:
        """添加锁定时间段
        
        参数:
            name: 时间段名称
            start_date: 开始日期 (格式: 'YYYY-MM-DD')
            end_date: 结束日期 (格式: 'YYYY-MM-DD')
            
        返回:
            添加成功返回True，否则返回False
        """
        try:
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute(
                'INSERT INTO locked_time_periods (name, start_date, end_date, created_at) VALUES (?, ?, ?, ?)',
                (name, start_date, end_date, current_date)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"添加锁定时间段失败: {e}")
            return False
    
    def delete_locked_time_period(self, period_id: int) -> bool:
        """删除锁定时间段
        
        参数:
            period_id: 时间段ID
            
        返回:
            删除成功返回True，否则返回False
        """
        try:
            self.cursor.execute('DELETE FROM locked_time_periods WHERE id = ?', (period_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"删除锁定时间段失败: {e}")
            return False
    
    def is_date_range_in_locked_period(self, start_date: str, end_date: str) -> bool:
        """检查日期范围是否在任何锁定时间段内
        
        参数:
            start_date: 开始日期 (格式: 'YYYY-MM-DD')
            end_date: 结束日期 (格式: 'YYYY-MM-DD')
            
        返回:
            如果日期范围在任何锁定时间段内，返回True，否则返回False
        """
        locked_periods = self.get_locked_date_ranges()
        
        for period in locked_periods:
            # 检查日期范围是否与锁定时间段有重叠
            if not (end_date < period['start_date'] or start_date > period['end_date']):
                return True
                
        return False
        
    def create_group(self, name: str, description: str = None) -> bool:
        """创建新的小组
        
        参数:
            name: 小组名称
            description: 小组描述，可选
            
        返回:
            创建成功返回True，否则返回False
        """
        try:
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute(
                'INSERT INTO groups (name, description, created_at) VALUES (?, ?, ?)',
                (name, description, current_date)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"创建小组失败: {e}")
            return False
        
    def get_addition_time_periods(self) -> List[Dict[str, Any]]:
        """从加分记录中提取时间段
        
        返回:
            包含所有加分时间段的列表，每个时间段是一个字典，包含:
            - id: 时间段ID (使用加分记录ID)
            - name: 时间段名称 (使用加分原因)
            - start_date: 开始日期
            - end_date: 结束日期
        """
        self.cursor.execute('''
            SELECT 
                id,
                COALESCE(reason, '未命名时间段') as name,
                start_date,
                end_date
            FROM addition_records
            GROUP BY start_date, end_date
            ORDER BY start_date DESC
        ''')
        return [dict(row) for row in self.cursor.fetchall()]
        
    def get_group_addition_records(self, group_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取小组在指定时间段内的加分记录
        
        参数:
            group_id: 小组ID
            start_date: 开始日期 (格式: 'YYYY-MM-DD')，包含当天
            end_date: 结束日期 (格式: 'YYYY-MM-DD')，包含当天
            
        返回:
            包含加分记录的列表，每个记录是一个字典，包含:
            - id: 记录ID
            - points: 加分分值
            - reason: 加分原因
            - date: 加分日期
        """
        # 获取小组成员
        self.cursor.execute('SELECT student_name FROM student_groups WHERE group_id = ?', (group_id,))
        members = [row['student_name'] for row in self.cursor.fetchall()]
        
        if not members:
            return []
            
        # 获取小组成员的加分记录
        # 修改查询条件，确保包含开始日期和结束日期当天的记录
        self.cursor.execute('''
            SELECT 
                id,
                points,
                reason,
                start_date as date
            FROM addition_records
            WHERE student_name IN ({})
            AND start_date <= ?
            AND end_date >= ?
            ORDER BY start_date DESC
        '''.format(','.join(['?'] * len(members))), 
        members + [end_date, start_date])
        
        return [dict(row) for row in self.cursor.fetchall()]

    def get_student_addition_records(self, student_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取学生在指定时间段内的加分记录
        
        参数:
            student_id: 学生ID
            start_date: 开始日期 (格式: 'YYYY-MM-DD')，包含当天
            end_date: 结束日期 (格式: 'YYYY-MM-DD')，包含当天
            
        返回:
            包含加分记录的列表，每个记录是一个字典，包含:
            - id: 记录ID
            - points: 加分分值
            - reason: 加分原因
            - date: 加分日期
        """
        # 获取学生姓名
        self.cursor.execute('SELECT name FROM students WHERE id = ?', (student_id,))
        student = self.cursor.fetchone()
        if not student:
            return []
            
        student_name = student['name']
        
        # 获取学生的加分记录
        self.cursor.execute('''
            SELECT 
                id,
                points,
                reason,
                start_date as date
            FROM addition_records
            WHERE student_name = ?
            AND start_date <= ?
            AND end_date >= ?
            ORDER BY start_date DESC
        ''', (student_name, end_date, start_date))
        
        return [dict(row) for row in self.cursor.fetchall()]
        
    def get_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        """获取小组成员列表
        
        参数:
            group_id: 小组ID
            
        返回:
            包含小组成员信息的列表，每个成员是一个字典，包含:
            - student_name: 学生姓名
            - join_date: 加入日期
        """
        self.cursor.execute('''
            SELECT 
                sg.student_name,
                s.id as student_id,
                sg.join_date
            FROM student_groups sg
            JOIN students s ON sg.student_name = s.name
            WHERE sg.group_id = ?
            ORDER BY sg.student_name
        ''', (group_id,))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_non_violation_types(self) -> List[str]:
        """获取所有非违规类型列表
        
        返回:
            包含所有不同非违规类型的字符串列表
        """
        self.cursor.execute('''
            SELECT DISTINCT non_violation_type 
            FROM deduction_records 
            WHERE non_violation_type IS NOT NULL 
            AND non_violation_type != ''
            ORDER BY non_violation_type
        ''')
        
        # 提取结果并过滤掉None值
        types = [row['non_violation_type'] for row in self.cursor.fetchall() if row['non_violation_type']]
        return types
    
    def search_deduction_records(self, student_name: Optional[str] = None, 
                                start_date: Optional[str] = None, 
                                end_date: Optional[str] = None,
                                deduction_type: Optional[int] = None,
                                violation_type: Optional[int] = None,
                                non_violation_type: Optional[str] = None,
                                min_points: Optional[float] = None,
                                max_points: Optional[float] = None,
                                name: Optional[str] = None) -> List[DeductionRecord]:
        """搜索扣分记录
        
        参数:
            student_name: 学生姓名，如果为None则查询所有学生
            start_date: 开始日期，格式为'yyyy-MM-dd'，如果为None则不限制开始日期
            end_date: 结束日期，格式为'yyyy-MM-dd'，如果为None则不限制结束日期
            deduction_type: 扣分类型，如果为None则不限制扣分类型
            violation_type: 违规类型，如果为None则不限制违规类型
            non_violation_type: 非违规类型，如果为None则不限制非违规类型
            min_points: 最小分数，如果为None则不限制最小分数
            max_points: 最大分数，如果为None则不限制最大分数
            name: 学生姓名的别名，与student_name参数功能相同
            
        返回:
            符合条件的扣分记录列表
        """
        query = 'SELECT * FROM deduction_records WHERE 1=1'
        params = []
        
        # 处理name参数（作为student_name的别名）
        if name is not None:
            student_name = name
        
        # 添加查询条件
        if student_name:
            query += ' AND student_name = ?'
            params.append(student_name)
            
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
            
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)
            
        if deduction_type is not None:
            query += ' AND deduction_type = ?'
            params.append(deduction_type)
            
        if violation_type is not None:
            query += ' AND violation_type = ?'
            params.append(violation_type)
            
        if non_violation_type is not None:
            query += ' AND non_violation_type = ?'
            params.append(non_violation_type)
            
        if min_points is not None:
            query += ' AND points >= ?'
            params.append(min_points)
            
        if max_points is not None:
            query += ' AND points <= ?'
            params.append(max_points)
            
        # 按日期降序排序
        query += ' ORDER BY date DESC'
        
        # 执行查询
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        # 转换为DeductionRecord对象列表
        records = []
        for row in rows:
            row_dict = dict(row)
            try:
                record = DeductionRecord.from_dict(row_dict)
                records.append(record)
            except Exception as e:
                print(f"转换扣分记录时出错: {str(e)}, 记录: {row_dict}")
                
        return records
    
    def clear_deduction_records(self) -> bool:
        """清除所有扣分记录
        
        返回:
            bool: 操作是否成功
        """
        try:
            self.cursor.execute('DELETE FROM deduction_records')
            self.cursor.execute('DELETE FROM compensation_records')
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"清除扣分记录失败: {e}")
            return False
            
    def clear_addition_records(self) -> bool:
        """清除所有加分记录
        
        返回:
            bool: 操作是否成功
        """
        try:
            self.cursor.execute('DELETE FROM addition_records')
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"清除加分记录失败: {e}")
            return False
            
    def clear_group_data(self) -> bool:
        """清除所有小组相关数据
        
        返回:
            bool: 操作是否成功
        """
        try:
            # 先删除有外键约束的记录
            self.cursor.execute('DELETE FROM student_groups')
            self.cursor.execute('DELETE FROM group_addition_records')
            # 然后删除小组记录
            self.cursor.execute('DELETE FROM groups')
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"清除小组数据失败: {e}")
            return False

    def get_addition_ranking(self) -> List[Dict[str, Any]]:
        """获取学生加分排名
        
        返回:
            按加分总和降序排序的学生列表，每个学生包含:
            - name: 学生姓名
            - addition_points: 加分总和
        """
        # 获取所有学生
        self.cursor.execute('SELECT name FROM students')
        students = [row['name'] for row in self.cursor.fetchall()]
        
        ranking = []
        
        for student_name in students:
            # 获取加分总和
            self.cursor.execute(
                '''
                SELECT COALESCE(SUM(points), 0) as sum_points 
                FROM addition_records 
                WHERE student_name = ?
                ''',
                (student_name,)
            )
            addition_points = self.cursor.fetchone()['sum_points']
            
            # 只包含有加分记录的学生
            if addition_points > 0:
                ranking.append({
                    'name': student_name,
                    'addition_points': addition_points
                })
        
        # 按加分总和降序排序
        ranking.sort(key=lambda x: x['addition_points'], reverse=True)
        
        return ranking
    
    def get_deduction_ranking(self, sort_by: str = "total") -> List[Tuple[str, float, float, float]]:
        """获取学生扣分排名
        
        参数:
            sort_by: 排序方式，可选值:
                - "total": 按总扣分排序（默认）
                - "violation": 按违规扣分排序
                - "non_violation": 按非违规扣分排序
                
        返回:
            按指定方式排序的学生列表，每个元素是一个元组，包含:
            - 学生姓名
            - 违规扣分
            - 非违规扣分
            - 总扣分
        """
        # 获取所有学生
        self.cursor.execute('SELECT name FROM students')
        students = [row['name'] for row in self.cursor.fetchall()]
        
        ranking = []
        
        for student_name in students:
            # 获取违规扣分总和
            self.cursor.execute(
                '''
                SELECT COALESCE(SUM(points), 0) as sum_points 
                FROM deduction_records 
                WHERE student_name = ? AND deduction_type = 1
                ''',
                (student_name,)
            )
            violation_points = self.cursor.fetchone()['sum_points']
            
            # 获取非违规扣分总和
            self.cursor.execute(
                '''
                SELECT COALESCE(SUM(points), 0) as sum_points 
                FROM deduction_records 
                WHERE student_name = ? AND deduction_type = 2
                ''',
                (student_name,)
            )
            non_violation_points = self.cursor.fetchone()['sum_points']
            
            # 计算总扣分
            total_points = violation_points + non_violation_points
            
            # 只包含有扣分记录的学生
            if total_points > 0:
                ranking.append((student_name, violation_points, non_violation_points, total_points))
        
        # 根据sort_by参数排序
        if sort_by == "violation":
            ranking.sort(key=lambda x: x[1], reverse=True)  # 按违规扣分降序排序
        elif sort_by == "non_violation":
            ranking.sort(key=lambda x: x[2], reverse=True)  # 按非违规扣分降序排序
        else:  # "total" 或其他值
            ranking.sort(key=lambda x: x[3], reverse=True)  # 按总扣分降序排序
        
        return ranking
    
    def get_total_score_ranking(self) -> List[Dict[str, Any]]:
        """获取学生总分排名
        
        返回:
            按总分降序排序的学生列表，每个学生包含:
            - id: 学生ID
            - name: 学生姓名
            - initial_score: 初始分数
            - addition_points: 加分总和
            - deduction_points: 扣分总和
            - total_score: 总分(初始分数 + 加分总和 - 扣分总和)
        """
        # 获取所有学生
        self.cursor.execute('SELECT * FROM students')
        students = [dict(row) for row in self.cursor.fetchall()]
        
        ranking = []
        
        for student in students:
            # 获取加分总和
            self.cursor.execute(
                '''
                SELECT COALESCE(SUM(points), 0) as sum_points 
                FROM addition_records 
                WHERE student_name = ?
                ''',
                (student['name'],)
            )
            addition_points = self.cursor.fetchone()['sum_points']
            
            # 获取扣分总和
            self.cursor.execute(
                '''
                SELECT COALESCE(SUM(points), 0) as sum_points 
                FROM deduction_records 
                WHERE student_name = ?
                ''',
                (student['name'],)
            )
            deduction_points = self.cursor.fetchone()['sum_points']
            
            # 计算总分
            total_score = student['initial_score'] + addition_points - deduction_points
            
            ranking.append({
                'id': student['id'],
                'name': student['name'],
                'initial_score': student['initial_score'],
                'addition_points': addition_points,
                'deduction_points': deduction_points,
                'total_score': total_score
            })
        
        # 按总分降序排序
        ranking.sort(key=lambda x: x['total_score'], reverse=True)
        
        return ranking
    
    def search_addition_records(self, student_name: Optional[str] = None,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               min_points: Optional[float] = None,
                               max_points: Optional[float] = None) -> List[AdditionRecord]:
        """搜索加分记录
        
        参数:
            student_name: 学生姓名，如果为None则查询所有学生
            start_date: 开始日期，格式为'yyyy-MM-dd'，如果为None则不限制开始日期
            end_date: 结束日期，格式为'yyyy-MM-dd'，如果为None则不限制结束日期
            min_points: 最小分数，如果为None则不限制最小分数
            max_points: 最大分数，如果为None则不限制最大分数
            
        返回:
            符合条件的加分记录列表
        """
        query = 'SELECT * FROM addition_records WHERE 1=1'
        params = []
        
        # 添加查询条件
        if student_name:
            query += ' AND student_name = ?'
            params.append(student_name)
            
        if start_date:
            # 查找与指定时间段有重叠的记录
            query += ' AND end_date >= ?'
            params.append(start_date)
            
        if end_date:
            # 查找与指定时间段有重叠的记录
            query += ' AND start_date <= ?'
            params.append(end_date)
            
        if min_points is not None:
            query += ' AND points >= ?'
            params.append(min_points)
            
        if max_points is not None:
            query += ' AND points <= ?'
            params.append(max_points)
            
        # 按开始日期降序排序
        query += ' ORDER BY start_date DESC'
        
        # 执行查询
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        # 转换为AdditionRecord对象列表
        records = []
        for row in rows:
            row_dict = dict(row)
            try:
                record = AdditionRecord.from_dict(row_dict)
                records.append(record)
            except Exception as e:
                print(f"转换加分记录时出错: {str(e)}, 记录: {row_dict}")
                
        return records
                   