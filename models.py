from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

class DesktopSession(db.Model):
    __tablename__ = 'desktop_session'
    
    id = db.Column(db.Integer, primary_key=True)
    desktop_id = db.Column(db.String(50), nullable=False, index=True)
    login_time = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(pytz.UTC))
    logout_time = db.Column(db.DateTime(timezone=True), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 addresses can be up to 45 characters
    
    def to_dict(self):
        return {
            'id': self.id,
            'desktop_id': self.desktop_id,
            'login_time': self.login_time.isoformat() if self.login_time else None,
            'logout_time': self.logout_time.isoformat() if self.logout_time else None,
            'ip_address': self.ip_address
        }
    
    def __repr__(self):
        return f'<DesktopSession {self.id}: Desktop {self.desktop_id}>' 