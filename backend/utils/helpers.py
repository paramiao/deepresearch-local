import json
import logging
from datetime import datetime

def setup_logger():
    """设置日志记录器"""
    logger = logging.getLogger('deepresearch')
    logger.setLevel(logging.INFO)
    
    # 创建处理器
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    
    # 创建格式器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(handler)
    
    return logger

def parse_research_query(query):
    """
    解析研究查询，提取主题和要求
    格式可以是 "主题，要求1，要求2..." 或纯主题
    """
    parts = query.split(',')
    topic = parts[0].strip()
    requirements = ', '.join([part.strip() for part in parts[1:]]) if len(parts) > 1 else '详细全面'
    
    return {
        'topic': topic,
        'requirements': requirements
    }

def format_timestamp():
    """返回格式化的时间戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_json_loads(data, default=None):
    """安全地加载JSON数据"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default or {}
