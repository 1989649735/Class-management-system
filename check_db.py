import sqlite3

def check_deduction_records():
    conn = sqlite3.connect('student_score.db')
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deduction_records'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("deduction_records表不存在")
        return
        
    # 获取记录数
    cursor.execute("SELECT COUNT(*) FROM deduction_records")
    count = cursor.fetchone()[0]
    print(f"deduction_records表中有{count}条记录")
    
    # 获取前5条记录
    if count > 0:
        cursor.execute("SELECT * FROM deduction_records LIMIT 5")
        print("\n前5条记录:")
        for row in cursor.fetchall():
            print(row)
    
    conn.close()

if __name__ == "__main__":
    check_deduction_records()