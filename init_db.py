import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app import app, db
from models import DesktopSession
from config import Config
import sys

def create_database():
    """创建数据库"""
    try:
        print("正在连接到 PostgreSQL...")
        conn = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            port=Config.POSTGRES_PORT,
            database='postgres',
            client_encoding='utf8'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 检查数据库是否存在
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (Config.POSTGRES_DB,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"正在创建数据库 {Config.POSTGRES_DB}...")
            cursor.execute(f'''
                CREATE DATABASE {Config.POSTGRES_DB}
                WITH 
                ENCODING = 'UTF8'
                LC_COLLATE = 'C'
                LC_CTYPE = 'C'
                TEMPLATE template0
            ''')
            print(f"数据库 {Config.POSTGRES_DB} 创建成功！")
        else:
            print(f"数据库 {Config.POSTGRES_DB} 已存在！")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"创建数据库时出错: {str(e)}")
        sys.exit(1)

def init_tables():
    """初始化数据库表"""
    try:
        print("正在创建数据库表...")
        with app.app_context():
            # 删除所有现有的表（如果存在）
            db.drop_all()
            print("已删除旧表（如果存在）")
            
            # 创建所有表
            db.create_all()
            
            # 验证表是否创建成功
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"已创建的表: {tables}")
            
            if 'desktop_session' in tables:
                # 验证表结构
                columns = {col['name']: col['type'] for col in inspector.get_columns('desktop_session')}
                print("表结构:", columns)
                print("数据库表创建成功！")
            else:
                print("警告：desktop_session 表未创建！")
                raise Exception("表创建失败")
            
    except Exception as e:
        print(f"创建表时出错: {str(e)}")
        print(f"错误类型: {type(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        sys.exit(1)

def main():
    try:
        print("开始初始化数据库...")
        # 创建数据库
        create_database()
        # 创建表
        init_tables()
        print("数据库初始化完成！")
    except Exception as e:
        print(f"初始化过程中出现错误: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 