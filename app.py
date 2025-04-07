from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime, timedelta
import time
import pytz
from models import db, DesktopSession
from config import Config
import socket

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# 使用环境变量获取端口，如果没有则使用5000
PORT = int(os.environ.get('PORT', 5000))

# 使用环境变量获取主机地址，如果没有则使用0.0.0.0
HOST = os.environ.get('HOST', '0.0.0.0')

# 数据文件路径
DATA_FILE = 'desktops.json'

# 设置超时时间（小时）
TIMEOUT_HOURS = 12

def get_current_time():
    """获取当前UTC时间"""
    return datetime.now(pytz.UTC)

def format_time(dt):
    """格式化时间为ISO格式，确保包含时区信息"""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt.isoformat()

def init_desktops():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                # 确保返回的是正确的数据结构
                if isinstance(data, list):
                    return {'desktops': data}
                elif isinstance(data, dict) and 'desktops' in data:
                    return data
                return create_default_desktops()
        except (json.JSONDecodeError, FileNotFoundError):
            # 如果文件损坏或不存在，返回默认数据
            return create_default_desktops()
    # 如果文件不存在，创建默认数据并保存
    default_data = create_default_desktops()
    save_desktops(default_data)
    return default_data

def create_default_desktops():
    return {
        'desktops': [
            {
                'id': 'desktop1',
                'name': '默认桌面',
                'url': 'https://example.com/remote',
                'status': 'offline',
                'last_login': None,
                'last_logout': None
            }
        ]
    }

def save_desktops(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving desktops: {e}")
        # 如果保存失败，至少确保内存中的数据是正确的
        return data
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/desktops', methods=['GET'])
def get_desktops():
    data = init_desktops()
    # 检查是否需要自动登出
    current_time = get_current_time()
    for desktop in data['desktops']:
        # 确保desktop包含所有必要的字段
        if 'status' not in desktop:
            desktop['status'] = 'offline'
        if 'last_login' not in desktop:
            desktop['last_login'] = None
        if 'last_logout' not in desktop:
            desktop['last_logout'] = None
        
        # 检查登录状态
        if desktop['status'] == 'online' and desktop.get('last_login'):
            try:
                login_time = datetime.fromisoformat(desktop['last_login'].replace('Z', '+00:00'))
                if (current_time - login_time) > timedelta(hours=TIMEOUT_HOURS):
                    desktop['status'] = 'offline'
                    desktop['last_logout'] = format_time(current_time)
            except (ValueError, TypeError) as e:
                print(f"Error processing login time: {e}")
                desktop['status'] = 'offline'
                desktop['last_login'] = None
    
    save_desktops(data)
    return jsonify(data)

@app.route('/api/desktops', methods=['POST'])
def add_desktop():
    data = request.get_json()
    name = data.get('name')
    url = data.get('url')
    
    if not name or not url:
        return jsonify({'success': False, 'message': 'Name and URL are required'}), 400
    
    desktops = init_desktops()
    # 检查名称是否重复
    if any(d.get('name') == name for d in desktops['desktops']):
        return jsonify({'success': False, 'message': 'A desktop with this name already exists'}), 400
    
    # 生成新的desktop_id
    existing_ids = [d['id'] for d in desktops['desktops'] if isinstance(d['id'], str) and d['id'].startswith('desktop')]
    if existing_ids:
        max_num = max(int(id.replace('desktop', '')) for id in existing_ids)
        new_id = f'desktop{max_num + 1}'
    else:
        new_id = 'desktop1'
    
    new_desktop = {
        'id': new_id,
        'name': name,
        'url': url,
        'status': 'offline',
        'last_login': None,
        'last_logout': None
    }
    
    desktops['desktops'].append(new_desktop)
    save_desktops(desktops)
    
    return jsonify({'success': True, 'desktop': new_desktop})

@app.route('/api/get_local_ip', methods=['GET'])
def get_local_ip():
    """获取本地IP地址"""
    try:
        # 获取本机计算机名
        hostname = socket.gethostname()
        # 获取本机IP
        ip = socket.gethostbyname(hostname)
        return jsonify({'ip': ip})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/desktops/<desktop_id>/login', methods=['POST'])
def login_desktop(desktop_id):
    data = init_desktops()
    desktop = next((d for d in data['desktops'] if d['id'] == desktop_id), None)
    
    if not desktop:
        return jsonify({'error': 'Desktop not found'}), 404
    
    if desktop['status'] == 'online':
        return jsonify({'error': 'Desktop is already online'}), 400
    
    try:
        # 获取客户端IP地址
        client_ip = request.remote_addr
        
        # 记录登录会话
        session = DesktopSession(
            desktop_id=desktop_id,
            ip_address=client_ip  # 保存连接时的IP地址
        )
        db.session.add(session)
        db.session.commit()
        
        desktop['status'] = 'online'
        desktop['last_login'] = format_time(get_current_time())
        save_desktops(data)
        
        return jsonify({
            'message': 'Login successful',
            'session_id': session.id,
            'login_time': format_time(session.login_time),
            'ip_address': client_ip
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/desktops/<desktop_id>/logout', methods=['POST'])
def logout_desktop(desktop_id):
    data = init_desktops()
    desktop = next((d for d in data['desktops'] if d['id'] == desktop_id), None)
    
    if not desktop:
        return jsonify({'error': 'Desktop not found'}), 404
    
    if desktop['status'] == 'offline':
        return jsonify({'error': 'Desktop is already offline'}), 400
    
    try:
        # 更新最近的会话记录
        session = DesktopSession.query.filter_by(
            desktop_id=desktop_id,
            logout_time=None
        ).order_by(DesktopSession.login_time.desc()).first()
        
        if session:
            session.logout_time = get_current_time()
            db.session.commit()
        
        desktop['status'] = 'offline'
        desktop['last_logout'] = format_time(get_current_time())
        save_desktops(data)
        
        return jsonify({
            'message': 'Logout successful',
            'logout_time': format_time(get_current_time())
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

# 添加新的API端点来获取会话历史
@app.route('/api/desktops/<int:desktop_id>/sessions', methods=['GET'])
def get_desktop_sessions(desktop_id):
    sessions = DesktopSession.query.filter_by(desktop_id=desktop_id)\
        .order_by(DesktopSession.login_time.desc())\
        .all()
    return jsonify([session.to_dict() for session in sessions])

@app.route('/api/desktops/<desktop_id>', methods=['DELETE'])
def delete_desktop(desktop_id):
    data = init_desktops()
    desktop = next((d for d in data['desktops'] if d['id'] == desktop_id), None)
    
    if not desktop:
        return jsonify({'success': False, 'message': 'Desktop not found'}), 404
    
    if desktop['status'] == 'online':
        return jsonify({'success': False, 'message': 'Cannot delete desktop while it is online'}), 400
    
    data['desktops'] = [d for d in data['desktops'] if d['id'] != desktop_id]
    save_desktops(data)
    
    return jsonify({'success': True})

@app.route('/api/desktops/<int:desktop_id>/rename', methods=['POST'])
def rename_desktop(desktop_id):
    data = request.get_json()
    new_name = data.get('name')
    
    if not new_name:
        return jsonify({'success': False, 'message': 'New name is required'}), 400
    
    desktops = init_desktops()
    desktop = next((d for d in desktops['desktops'] if d['id'] == desktop_id), None)
    
    if not desktop:
        return jsonify({'success': False, 'message': 'Desktop not found'}), 404
    
    if any(d.get('name', '').lower() == new_name.lower() and d['id'] != desktop_id for d in desktops['desktops']):
        return jsonify({'success': False, 'message': 'A desktop with this name already exists'}), 400
    
    desktop['name'] = new_name
    save_desktops(desktops)
    
    return jsonify({'success': True, 'desktop': desktop})

@app.route('/api/desktops/<int:desktop_id>/window-event', methods=['POST'])
def handle_window_event(desktop_id):
    data = request.get_json()
    event_type = data.get('eventType')
    
    if event_type == 'unload':
        # 设置一个10秒的延迟登出
        def delayed_logout():
            time.sleep(10)
            data = init_desktops()
            desktop = next((d for d in data['desktops'] if d['id'] == desktop_id), None)
            if desktop and desktop['status'] == 'in-use':
                desktop['status'] = 'available'
                desktop['user'] = None
                desktop['loginTime'] = None
                save_desktops(data)
        
        # 在新线程中执行延迟登出
        import threading
        thread = threading.Thread(target=delayed_logout)
        thread.start()
        return jsonify({'success': True})
    
    elif event_type == 'load':
        # 如果收到load事件，说明是刷新，不需要登出
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid event type'}), 400

@app.route('/api/sessions', methods=['GET'])
def get_all_sessions():
    """获取所有桌面会话记录"""
    try:
        sessions = DesktopSession.query.order_by(DesktopSession.login_time.desc()).all()
        return jsonify([{
            'id': session.id,
            'desktop_id': session.desktop_id,
            'login_time': session.login_time.strftime('%Y-%m-%d %H:%M:%S'),
            'logout_time': session.logout_time.strftime('%Y-%m-%d %H:%M:%S') if session.logout_time else None,
            'ip_address': session.ip_address
        } for session in sessions])
    except Exception as e:
        return jsonify({'error': f'获取会话记录失败: {str(e)}'}), 500

@app.route('/sessions')
def sessions_page():
    """显示会话历史页面"""
    return render_template('sessions.html')

@app.route('/api/desktops/<desktop_id>/edit', methods=['POST'])
def edit_desktop(desktop_id):
    data = request.get_json()
    new_name = data.get('name')
    new_url = data.get('url')
    
    if not new_name or not new_url:
        return jsonify({'success': False, 'message': 'Name and URL are required'}), 400
    
    desktops = init_desktops()
    desktop = next((d for d in desktops['desktops'] if d['id'] == desktop_id), None)
    
    if not desktop:
        return jsonify({'success': False, 'message': 'Desktop not found'}), 404
    
    # 检查新名称是否与其他桌面重复（排除当前桌面）
    if any(d.get('name') == new_name and d['id'] != desktop_id for d in desktops['desktops']):
        return jsonify({'success': False, 'message': 'A desktop with this name already exists'}), 400
    
    desktop['name'] = new_name
    desktop['url'] = new_url
    save_desktops(desktops)
    
    return jsonify({'success': True, 'desktop': desktop})

if __name__ == '__main__':
    app.run(host=HOST, port=PORT) 