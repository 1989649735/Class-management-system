import sqlite3
from pathlib import Path

db_path = Path('student_score.db')
if not db_path.exists():
    print("数据库文件不存在")
    exit()

conn = sqlite3.connect('student_score.db')
cursor = conn.cursor()

# 检查students表
print("Students表前5条记录:")
cursor.execute("SELECT * FROM students LIMIT 5")
for row in cursor.fetchall():
    print(row)

# 检查student_groups表
print("\nStudent_groups表前5条记录:")
cursor.execute("SELECT DISTINCT student_name FROM student_groups LIMIT 5")
for row in cursor.fetchall():
    print(row)

conn.close()