import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基本配置类"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    PORT = int(os.environ.get('PORT', 5000))

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

# 配置映射
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 获取当前环境配置
def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name[env]
