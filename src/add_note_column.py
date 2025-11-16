"""
데이터베이스에 note 컬럼을 추가하는 마이그레이션 스크립트
"""
import sqlite3
import os

def add_note_column():
    # 데이터베이스 파일 경로
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'boats.db')
    
    if not os.path.exists(db_path):
        print(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        print("app.py를 먼저 실행하여 데이터베이스를 생성하세요.")
        return
    
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 정보 확인
        cursor.execute("PRAGMA table_info(boats)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # note 컬럼이 이미 있는지 확인
        if 'note' in columns:
            print("note 컬럼이 이미 존재합니다.")
        else:
            # note 컬럼 추가
            cursor.execute("ALTER TABLE boats ADD COLUMN note TEXT")
            conn.commit()
            print("note 컬럼이 성공적으로 추가되었습니다.")
        
        # 업데이트된 테이블 구조 출력
        cursor.execute("PRAGMA table_info(boats)")
        print("\n현재 boats 테이블 구조:")
        for column in cursor.fetchall():
            print(f"  {column[1]} ({column[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        if conn:
            conn.close()

if __name__ == '__main__':
    add_note_column()
