import os
import time
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API密钥未设置。请设置环境变量GEMINI_API_KEY或直接提供api_key参数。")
        
        # 配置Gemini API
        genai.configure(api_key=self.api_key)
        
        # 获取默认模型
        self.model = genai.GenerativeModel('gemini-pro')
        
    def generate_research_plan(self, topic, requirements):
        """根据主题和要求生成研究计划，包含重试机制"""
        prompt = f"""
        请为以下研究主题制定详细的研究计划:
        
        研究主题: {topic}
        
        研究要求: {requirements}
        
        请按照以下结构组织研究计划:
        1. 研究背景和意义
        2. 研究目标
        3. 研究方法和步骤
        4. 数据收集方案
        5. 分析方法
        6. 预期成果
        7. 时间线
        8. 资源需求
        
        请用中文回复，并确保研究计划具体、可行、全面。
        """
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试生成研究计划 (尝试 {attempt+1}/{max_retries})")
                response = self.model.generate_content(
                    prompt,
                    safety_settings=safety_settings,
                    timeout=120  # 增加超时时间到120秒
                )
                logger.info("研究计划生成成功")
                return response.text
            except Exception as e:
                logger.error(f"生成研究计划失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避策略
                else:
                    logger.error(f"生成研究计划失败，已达到最大重试次数: {str(e)}")
                    raise
    
    def generate_research_report(self, research_plan, findings):
        """根据研究计划和发现生成研究报告，包含重试机制"""
        prompt = f"""
        请基于以下研究计划和研究发现，生成一份详尽的研究报告:
        
        研究计划:
        {research_plan}
        
        研究发现:
        {findings}
        
        请按照以下结构组织研究报告:
        1. 摘要
        2. 研究背景和目标
        3. 研究方法
        4. 研究发现
        5. 分析与讨论
        6. 结论与建议
        7. 参考文献
        
        请用中文回复，确保报告内容详实、逻辑清晰、有深度。
        """
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试生成研究报告 (尝试 {attempt+1}/{max_retries})")
                response = self.model.generate_content(
                    prompt,
                    safety_settings=safety_settings,
                    timeout=120  # 增加超时时间到120秒
                )
                logger.info("研究报告生成成功")
                return response.text
            except Exception as e:
                logger.error(f"生成研究报告失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避策略
                else:
                    logger.error(f"生成研究报告失败，已达到最大重试次数: {str(e)}")
                    raise
    
    def answer_question(self, conversation_history, question):
        """回答用户问题，基于对话历史，包含重试机制"""
        # 使用中文字符'用户'，避免Unicode转义问题
        formatted_history = "\n".join([f"{'用户' if i % 2 == 0 else 'AI'}: {msg}" for i, msg in enumerate(conversation_history)])
        
        prompt = f"""
        以下是用户与AI助手的对话历史:
        
        {formatted_history}
        
        用户: {question}
        
        请以一个专业的研究助手身份回答上述问题。你的回答应该专业、全面，并尽可能提供有价值的研究见解。
        请用中文回复。
        """
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试回答用户问题 (尝试 {attempt+1}/{max_retries})")
                response = self.model.generate_content(
                    prompt,
                    safety_settings=safety_settings,
                    timeout=60  # 设置超时时间为60秒，因为单个问题回答通常比较快
                )
                logger.info("回答生成成功")
                return response.text
            except Exception as e:
                logger.error(f"回答用户问题失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避策略
                else:
                    logger.error(f"回答用户问题失败，已达到最大重试次数: {str(e)}")
                    raise
