from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

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
    return datetime.utcnow()

def format_time(dt):
    """格式化时间为ISO格式，确保包含时区信息"""
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

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
                'id': 1,
                'name': 'Remote Desktop 1',
                'status': 'available',
                'user': None,
                'loginTime': None
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
        if desktop['loginTime']:
            try:
                login_time = datetime.strptime(desktop['loginTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
                if (current_time - login_time) > timedelta(hours=TIMEOUT_HOURS):
                    desktop['status'] = 'available'
                    desktop['user'] = None
                    desktop['loginTime'] = None
            except (ValueError, TypeError):
                # 如果时间格式不正确，重置状态
                desktop['status'] = 'available'
                desktop['user'] = None
                desktop['loginTime'] = None
    save_desktops(data)
    return jsonify(data)

@app.route('/api/desktops', methods=['POST'])
def add_desktop():
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'success': False, 'message': 'Name is required'}), 400
    
    desktops = init_desktops()
    # 检查名称是否重复
    if any(d.get('name', '').lower() == name.lower() for d in desktops['desktops']):
        return jsonify({'success': False, 'message': 'A desktop with this name already exists'}), 400
    
    new_id = max([d.get('id', 0) for d in desktops['desktops']], default=0) + 1
    
    new_desktop = {
        'id': new_id,
        'name': name,
        'status': 'available',
        'user': None,
        'loginTime': None
    }
    
    desktops['desktops'].append(new_desktop)
    save_desktops(desktops)
    
    return jsonify({'success': True, 'desktop': new_desktop})

@app.route('/api/desktops/<int:desktop_id>/login', methods=['POST'])
def login_desktop(desktop_id):
    data = init_desktops()
    desktop = next((d for d in data['desktops'] if d['id'] == desktop_id), None)
    
    if desktop and desktop['status'] == 'available':
        username = request.json.get('username', 'Anonymous')
        desktop['status'] = 'in-use'
        desktop['user'] = username
        desktop['loginTime'] = format_time(get_current_time())
        save_desktops(data)
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Desktop not available'})

@app.route('/api/desktops/<int:desktop_id>/logout', methods=['POST'])
def logout_desktop(desktop_id):
    data = init_desktops()
    desktop = next((d for d in data['desktops'] if d['id'] == desktop_id), None)
    
    if not desktop:
        return jsonify({'success': False, 'message': 'Desktop not found'}), 404
    
    desktop['status'] = 'available'
    desktop['user'] = None
    desktop['loginTime'] = None
    
    save_desktops(data)
    return jsonify({'success': True, 'desktop': desktop})

@app.route('/api/desktops/<int:desktop_id>', methods=['DELETE'])
def delete_desktop(desktop_id):
    data = init_desktops()
    desktop = next((d for d in data['desktops'] if d['id'] == desktop_id), None)
    
    if not desktop:
        return jsonify({'success': False, 'message': 'Desktop not found'}), 404
    
    if desktop['status'] == 'in-use':
        return jsonify({'success': False, 'message': 'Cannot delete desktop in use'}), 400
    
    data['desktops'] = [d for d in data['desktops'] if d['id'] != desktop_id]
    save_desktops(data)
    
    return jsonify({'success': True})

@app.route('/api/desktops/<int:desktop_id>/rename', methods=['POST'])
def rename_desktop(desktop_id):
    data = request.get_json()
    new_name = data.get('newName')
    
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

if __name__ == '__main__':
    app.run(host=HOST, port=PORT) 