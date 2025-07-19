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
    def get_setting(key, default=None):
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default

    @staticmethod
    def set_setting(key, value, description=None, user_id=None):
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value
            if description:
                setting.description = description
            if user_id:
                setting.updated_by = user_id
            setting.updated_at = datetime.utcnow()
        else:
            setting = SystemSetting(
                setting_key=key,
                setting_value=value,
                description=description,
                updated_by=user_id
            )
            db.session.add(setting)
        db.session.commit()
