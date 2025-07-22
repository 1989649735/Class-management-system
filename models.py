#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

# 学生列表
STUDENT_LIST = []

class DeductionType(Enum):
    """扣分类型"""
    VIOLATION = 1      # 违规扣分
    NON_VIOLATION = 2  # 非违规扣分


class ViolationType(Enum):
    """违规类型枚举"""
    未交作业 = 1      # 学习类
    迟交作业 = 2      # 学习类 
    未完成作业 = 3    # 学习类
    卫生不合格 = 4    # 卫生类
    课堂违纪 = 5      # 纪律类
    自习违纪 = 6  
    抄袭作业 = 7    # 纪律类

    @classmethod
    def get_category_types(cls, category: str) -> list:
        """获取指定大类的所有违规类型
        
        参数:
            category: 大类名称("学习"、"卫生"、"纪律")
            
        返回:
            该大类下的所有违规类型枚举列表
        """
        category_map = {
            "学习": [cls.未交作业, cls.迟交作业, cls.未完成作业],
            "卫生": [cls.卫生不合格],
            "纪律": [cls.课堂违纪, cls.自习违纪]
        }
        return category_map.get(category, [])


class Student:
    """学生模型"""
    
    def __init__(self, name: str, initial_score: float = 0.0):
        self.id: Optional[int] = None  # 数据库ID
        self.name: str = name
        self.initial_score: float = initial_score
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "initial_score": self.initial_score
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Student':
        """从字典创建对象"""
        student = cls(data["name"], data["initial_score"])
        student.id = data["id"]
        return student


class DeductionRecord:
    """扣分记录模型"""
    
    def __init__(
        self, 
        student_name: str, 
        points: float, 
        date: datetime,
        deduction_type: DeductionType,
        violation_behavior: Optional[str] = None,
        treatment_measures: Optional[str] = None,
        violation_type: Optional[ViolationType] = None,
        non_violation_type: Optional[str] = None,
        reason: Optional[str] = None
    ):
        self.id: Optional[int] = None  # 数据库ID
        self.student_name: str = student_name
        self.points: float = points
        self.violation_behavior: Optional[str] = violation_behavior
        self.treatment_measures: Optional[str] = treatment_measures
        self.date: datetime = date
        self.deduction_type: DeductionType = deduction_type
        self.violation_type: Optional[ViolationType] = violation_type
        self.non_violation_type: Optional[str] = non_violation_type
        self.reason: Optional[str] = reason  # 添加reason属性
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "student_name": self.student_name,
            "points": self.points,
            "violation_behavior": self.violation_behavior,
            "treatment_measures": self.treatment_measures,
            "date": self.date.strftime("%Y-%m-%d"),  # 统一使用年月日格式
            "deduction_type": self.deduction_type.value,
            "violation_type": self.violation_type.value if self.violation_type else None,
            "non_violation_type": self.non_violation_type,
            "reason": self.reason
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeductionRecord':
        """从字典创建对象"""
        violation_type = None
        if "violation_type" in data and data["violation_type"] is not None:
            violation_type = ViolationType(int(data["violation_type"]))
        
        # 处理可能包含时间部分的ISO格式日期字符串
        try:
            date = datetime.fromisoformat(data["date"])
        except ValueError:
            # 尝试处理其他格式的日期字符串
            try:
                # 如果包含T00:00:00这样的时间部分，先分割只取日期部分
                if "T" in data["date"]:
                    date = datetime.strptime(data["date"].split("T")[0], "%Y-%m-%d")
                else:
                    date = datetime.strptime(data["date"], "%Y-%m-%d")
            except Exception as e:
                raise ValueError(f"无法解析日期格式: {data['date']}, 错误: {str(e)}")
            
        record = cls(
            data["student_name"],
            data["points"],
            date,
            DeductionType(data["deduction_type"]),
            data.get("violation_behavior"),
            data.get("treatment_measures"),
            violation_type,
            data.get("non_violation_type"),
            data.get("reason")  # 添加reason参数
        )
        record.id = data["id"]
        return record


class CompensationRecord:
    """补偿记录模型"""
    
    def __init__(
        self, 
        deduction_record_id: int, 
        old_points: float,
        new_points: float,
        reason: str, 
        date: datetime
    ):
        self.id: Optional[int] = None  # 数据库ID
        self.deduction_record_id: int = deduction_record_id
        self.old_points: float = old_points
        self.new_points: float = new_points
        self.reason: str = reason
        self.date: datetime = date
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "deduction_record_id": self.deduction_record_id,
            "old_points": self.old_points,
            "new_points": self.new_points,
            "reason": self.reason,
            "date": self.date.strftime("%Y-%m-%d")  # 统一使用年月日格式
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompensationRecord':
        """从字典创建对象"""
        # 处理可能包含时间部分的ISO格式日期字符串
        try:
            date = datetime.fromisoformat(data["date"])
        except ValueError:
            # 尝试处理其他格式的日期字符串
            try:
                # 如果包含T00:00:00这样的时间部分，先分割只取日期部分
                if "T" in data["date"]:
                    date = datetime.strptime(data["date"].split("T")[0], "%Y-%m-%d")
                else:
                    date = datetime.strptime(data["date"], "%Y-%m-%d")
            except Exception as e:
                raise ValueError(f"无法解析日期格式: {data['date']}, 错误: {str(e)}")
        
        record = cls(
            data["deduction_record_id"],
            data["old_points"],
            data["new_points"],
            data["reason"],
            date
        )
        record.id = data["id"]
        return record


class AdditionRecord:
    """加分记录模型"""
    
    def __init__(
        self, 
        student_name: str, 
        points: float, 
        reason: Optional[str] = None,  # 改为可选参数
        start_date: datetime = datetime.now(),  # 改为可选参数，默认当前时间
        end_date: datetime = datetime.now()  # 改为可选参数，默认当前时间
    ):
        self.id: Optional[int] = None  # 数据库ID
        self.student_name: str = student_name
        self.points: float = points
        self.reason: Optional[str] = reason  # 改为可选字段
        self.start_date: datetime = start_date
        self.end_date: datetime = end_date
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "student_name": self.student_name,
            "points": self.points,
            "reason": self.reason,
            "start_date": self.start_date.strftime("%Y-%m-%d"),  # 统一使用年月日格式
            "end_date": self.end_date.strftime("%Y-%m-%d")      # 统一使用年月日格式
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdditionRecord':
        """从字典创建对象"""
        # 处理可能包含时间部分的ISO格式日期字符串
        try:
            start_date = datetime.fromisoformat(data["start_date"])
            end_date = datetime.fromisoformat(data["end_date"])
        except ValueError:
            # 尝试处理其他格式的日期字符串
            try:
                # 如果包含T00:00:00这样的时间部分，先分割只取日期部分
                if "T" in data["start_date"]:
                    start_date = datetime.strptime(data["start_date"].split("T")[0], "%Y-%m-%d")
                else:
                    start_date = datetime.strptime(data["start_date"], "%Y-%m-%d")
                
                if "T" in data["end_date"]:
                    end_date = datetime.strptime(data["end_date"].split("T")[0], "%Y-%m-%d")
                else:
                    end_date = datetime.strptime(data["end_date"], "%Y-%m-%d")
            except Exception as e:
                raise ValueError(f"无法解析日期格式: {data['start_date']}或{data['end_date']}, 错误: {str(e)}")
        
        record = cls(
            data["student_name"],
            data["points"],
            data["reason"],
            start_date,
            end_date
        )
        record.id = data["id"]
        return record