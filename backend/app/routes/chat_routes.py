from flask import Blueprint, request, jsonify
from app.services.siliconflow_service import SiliconFlowService
import os
import logging

# 设置日志
logger = logging.getLogger(__name__)

bp = Blueprint('chat', __name__, url_prefix='/api/chat')
ai_service = None

try:
    # 尝试初始化硅基流动服务
    ai_service = SiliconFlowService()
    logger.info("成功初始化硅基流动API服务")
except Exception as e:
    logger.error(f"初始化硅基流动API服务失败: {str(e)}")
    ai_service = None

@bp.before_request
def check_gemini_service():
    global ai_service
    if ai_service is None:
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if api_key:
            ai_service = SiliconFlowService(api_key)
            logger.info("成功初始化硅基流动API服务")
        else:
            logger.error("SILICONFLOW_API_KEY环境变量未设置")
            return jsonify({"error": "硬相流动API密钥未设置"}), 500

@bp.route('/research_plan', methods=['POST'])
def create_research_plan():
    data = request.json
    if not data or 'topic' not in data or 'requirements' not in data:
        return jsonify({"error": "缺少必要参数: topic, requirements"}), 400
    
    try:
        logger.info(f"正在生成研究计划: {data['topic']}")
        result = ai_service.generate_research_plan(data['topic'], data['requirements'])
        logger.info("研究计划生成成功")
        return jsonify({"plan": result})
    except Exception as e:
        logger.error(f"生成研究计划时出错: {str(e)}")
        return jsonify({"error": f"生成研究计划时出错: {str(e)}"}), 500

@bp.route('/research_report', methods=['POST'])
def create_research_report():
    data = request.json
    if not data or 'research_plan' not in data or 'findings' not in data:
        return jsonify({"error": "缺少必要参数: research_plan, findings"}), 400
    
    try:
        logger.info("正在生成研究报告")
        result = ai_service.generate_research_report(data['research_plan'], data['findings'])
        logger.info("研究报告生成成功")
        return jsonify({"report": result})
    except Exception as e:
        logger.error(f"生成研究报告时出错: {str(e)}")
        return jsonify({"error": f"生成研究报告时出错: {str(e)}"}), 500

@bp.route('/question', methods=['POST'])
def answer_question():
    data = request.json
    if not data or 'question' not in data:
        return jsonify({"error": "缺少必要参数: question"}), 400
    
    conversation_history = data.get('conversation_history', [])
    
    try:
        logger.info(f"正在回答问题: {data['question'][:30]}...")
        result = ai_service.answer_question(conversation_history, data['question'])
        logger.info("问题回答成功")
        return jsonify({"answer": result})
    except Exception as e:
        logger.error(f"回答问题时出错: {str(e)}")
        return jsonify({"error": f"回答问题时出错: {str(e)}"}), 500
