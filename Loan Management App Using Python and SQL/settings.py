from user import db
from datetime import datetime

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @staticmethod
    def get_setting(key, default_value=None):
        """Get a setting value by key"""
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default_value

    @staticmethod
    def set_setting(key, value, description=None, updated_by=None):
        """Set a setting value"""
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value
            if description:
                setting.description = description
            if updated_by:
                setting.updated_by = updated_by
            setting.updated_at = datetime.utcnow()
        else:
            setting = SystemSetting(
                setting_key=key,
                setting_value=value,
                description=description,
                updated_by=updated_by
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting

    def __repr__(self):
        return f'<SystemSetting {self.setting_key}>'

    def to_dict(self):
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'description': self.description,
            'updated_by': self.updated_by,
            'updater_name': self.updater.full_name if self.updater else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

