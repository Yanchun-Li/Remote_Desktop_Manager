import os
import subprocess
from datetime import datetime
from config import Config

def backup_database():
    """备份数据库"""
    # 创建备份目录
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 生成备份文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'remote_desktop_{timestamp}.sql')
    
    # 构建mysqldump命令
    command = [
        'mysqldump',
        f'--host={Config.MYSQL_HOST}',
        f'--port={Config.MYSQL_PORT}',
        f'--user={Config.MYSQL_USER}',
        f'--password={Config.MYSQL_PASSWORD}',
        '--databases',
        Config.MYSQL_DB,
        '--single-transaction',
        '--quick',
        '--lock-tables=false',
        f'--result-file={backup_file}'
    ]
    
    try:
        # 执行备份
        subprocess.run(command, check=True)
        print(f"数据库备份成功！备份文件: {backup_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"备份过程中出现错误: {str(e)}")
        return False

if __name__ == '__main__':
    backup_database() 