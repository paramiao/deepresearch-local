from flask import Blueprint, request, jsonify
from app.services.research_service import research_service
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('research', __name__, url_prefix='/api/research')

@bp.route('/start', methods=['POST'])
def start_research():
    """开始一个新的研究过程"""
    logger.info("\n" + "-"*50)
    logger.info(f"\u63a5收到研究请求: {request.remote_addr}")
    data = request.json
    logger.info(f"\u8bf7求数据: {data}")
    
    if not data or 'topic' not in data:
        logger.error("\u7f3a少必要参数: topic")
        return jsonify({"error": "缺少必要参数: topic"}), 400
    
    topic = data.get('topic')
    requirements = data.get('requirements', '详细全面')
    logger.info(f"\u7814究主题: {topic}, \u8981求: {requirements}")
    
    try:
        process_id = research_service.create_research_process(topic, requirements)
        logger.info(f"\u7814究过程创建成功, ID: {process_id}")
        
        response_data = {
            "process_id": process_id,
            "message": "研究计划生成中，请稍后查询结果"
        }
        logger.info(f"\u8fd4回响应: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        error_msg = f"启动研究过程时出错: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({"error": error_msg}), 500

@bp.route('/status/<process_id>', methods=['GET'])
def get_research_status(process_id):
    """获取研究过程的状态"""
    logger.debug(f"\u83b7取研究状态: {process_id}")
    
    process = research_service.get_research_process(process_id)
    if not process:
        logger.warning(f"\u672a找到研究过程: {process_id}")
        return jsonify({"error": "未找到指定的研究过程"}), 404
    
    result = process.to_dict()
    # 记录关键状态变化
    logger.debug(f"\u7814究过程状态: {result['status']}, \u8fdb度: {result['progress']}%")
    
    # 特别注意等待确认状态
    if result['status'] == 'waiting_confirmation':
        logger.info(f"\u7814究计划已生成并等待确认: {process_id}")
        has_plan = bool(result.get('plan'))
        logger.info(f"\u8ba1划存在: {has_plan}, \u8ba1划长度: {len(result.get('plan', ''))}")
    
    return jsonify(result)

@bp.route('/confirm/<process_id>', methods=['POST'])
def confirm_research_plan(process_id):
    """确认研究计划，开始执行研究"""
    logger.info("\n" + "-"*50)
    logger.info(f"\u63a5收研究计划确认请求: {process_id}")
    
    process = research_service.get_research_process(process_id)
    if not process:
        logger.warning(f"\u672a找到研究过程: {process_id}")
        return jsonify({"error": "未找到指定的研究过程"}), 404
    
    logger.info(f"\u7814究过程当前状态: {process.status}")
    if process.status != "waiting_confirmation":
        logger.warning(f"\u72b6态错误，无法确认: {process.status}")
        return jsonify({"error": "该研究过程当前状态不允许确认操作"}), 400
    
    logger.info(f"\u5f00始执行研究: {process_id}")
    success = research_service.start_research_execution(process_id)
    if not success:
        logger.error(f"\u542f动研究执行失败: {process_id}")
        return jsonify({"error": "启动研究执行失败"}), 500
    
    logger.info(f"\u7814究执行已成功启动: {process_id}")
    response_data = {
        "message": "研究执行已启动，请定期查询进度",
        "process_id": process_id
    }
    return jsonify(response_data)

@bp.route('/cancel/<process_id>', methods=['POST'])
def cancel_research(process_id):
    """取消研究过程"""
    process = research_service.get_research_process(process_id)
    if not process:
        return jsonify({"error": "未找到指定的研究过程"}), 404
    
    # 将状态设置为取消
    process.status = "cancelled"
    process.current_step = "研究已取消"
    
    return jsonify({
        "message": "研究已取消",
        "process_id": process_id
    })
