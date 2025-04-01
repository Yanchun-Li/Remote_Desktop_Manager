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
DESKTOPS_FILE = 'desktops.json'

def load_desktops():
    if os.path.exists(DESKTOPS_FILE):
        try:
            with open(DESKTOPS_FILE, 'r') as f:
                data = json.load(f)
                # 确保返回的是列表格式
                if isinstance(data, dict) and 'desktops' in data:
                    return data['desktops']
                elif isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError:
            return []
    return []

def save_desktops(desktops):
    # 确保保存的是列表格式
    with open(DESKTOPS_FILE, 'w') as f:
        json.dump(desktops, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/desktops', methods=['GET'])
def get_desktops():
    desktops = load_desktops()
    return jsonify({'desktops': desktops})

@app.route('/api/desktops', methods=['POST'])
def add_desktop():
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'success': False, 'message': 'Name is required'}), 400
    
    desktops = load_desktops()
    # 确保desktops是列表
    if not isinstance(desktops, list):
        desktops = []
    
    # 检查名称是否重复
    if any(d.get('name', '').lower() == name.lower() for d in desktops):
        return jsonify({'success': False, 'message': 'A desktop with this name already exists'}), 400
    
    new_id = max([d.get('id', 0) for d in desktops], default=0) + 1
    
    new_desktop = {
        'id': new_id,
        'name': name,
        'status': 'available',
        'user': None,
        'loginTime': None
    }
    
    desktops.append(new_desktop)
    save_desktops(desktops)
    
    return jsonify({'success': True, 'desktop': new_desktop})

@app.route('/api/desktops/<int:desktop_id>/login', methods=['POST'])
def login_desktop(desktop_id):
    data = request.get_json()
    username = data.get('username', 'Anonymous')
    
    desktops = load_desktops()
    desktop = next((d for d in desktops if d['id'] == desktop_id), None)
    
    if not desktop:
        return jsonify({'success': False, 'message': 'Desktop not found'}), 404
    
    if desktop['status'] != 'available':
        return jsonify({'success': False, 'message': 'Desktop is not available'}), 400
    
    desktop['status'] = 'in-use'
    desktop['user'] = username
    desktop['loginTime'] = datetime.now().isoformat()
    
    save_desktops(desktops)
    return jsonify({'success': True, 'desktop': desktop})

@app.route('/api/desktops/<int:desktop_id>/logout', methods=['POST'])
def logout_desktop(desktop_id):
    desktops = load_desktops()
    desktop = next((d for d in desktops if d['id'] == desktop_id), None)
    
    if not desktop:
        return jsonify({'success': False, 'message': 'Desktop not found'}), 404
    
    if desktop['status'] != 'in-use':
        return jsonify({'success': False, 'message': 'Desktop is not in use'}), 400
    
    desktop['status'] = 'available'
    desktop['user'] = None
    desktop['loginTime'] = None
    
    save_desktops(desktops)
    return jsonify({'success': True, 'desktop': desktop})

@app.route('/api/desktops/<int:desktop_id>', methods=['DELETE'])
def delete_desktop(desktop_id):
    desktops = load_desktops()
    desktop = next((d for d in desktops if d['id'] == desktop_id), None)
    
    if not desktop:
        return jsonify({'success': False, 'message': 'Desktop not found'}), 404
    
    if desktop['status'] == 'in-use':
        return jsonify({'success': False, 'message': 'Cannot delete desktop in use'}), 400
    
    desktops = [d for d in desktops if d['id'] != desktop_id]
    save_desktops(desktops)
    
    return jsonify({'success': True})

@app.route('/api/desktops/<int:desktop_id>/rename', methods=['POST'])
def rename_desktop(desktop_id):
    data = request.get_json()
    new_name = data.get('name')
    
    if not new_name:
        return jsonify({'success': False, 'message': 'New name is required'}), 400
    
    desktops = load_desktops()
    desktop = next((d for d in desktops if d['id'] == desktop_id), None)
    
    if not desktop:
        return jsonify({'success': False, 'message': 'Desktop not found'}), 404
    
    # 检查新名称是否与其他桌面重复（排除当前桌面）
    if any(d.get('name', '').lower() == new_name.lower() and d['id'] != desktop_id for d in desktops):
        return jsonify({'success': False, 'message': 'A desktop with this name already exists'}), 400
    
    desktop['name'] = new_name
    save_desktops(desktops)
    
    return jsonify({'success': True, 'desktop': desktop})

if __name__ == '__main__':
    app.run(host=HOST, port=PORT) 