import os
import time
import json
import logging
import requests
from typing import List, Optional, Dict, Any, Union

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SiliconFlowService:
    """硅基流动API服务，替代Gemini API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        if not self.api_key:
            logger.warning("硅基流动API密钥未设置。请设置环境变量SILICONFLOW_API_KEY或直接提供api_key参数。")
            self.api_key = "default_api_key"  # 可以设置一个默认值便于测试
        
        self.api_base_url = os.getenv("SILICONFLOW_API_BASE_URL", "https://api.siliconflow.cn/v1")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        # 禁用SSL验证以排除证书问题（仅用于测试，生产环境不建议）
        self.session.verify = False
        # 设置更长的超时时间
        self.timeout = 60  # 增加到60秒
        # 设置连接池选项
        self.session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=10
        ))
        # 记录可用模型
        self.available_models = ["Pro/deepseek-ai/DeepSeek-V3"]
    
    def _send_request(self, url, payload, timeout=90, max_retries=4):
        """发送API请求并处理重试逻辑，增强的超时和重试机制"""
        retry_delay = 2  # 初始重试延迟2秒，随后指数增加
        
        for attempt in range(max_retries):
            try:
                logger.info(f"向硅基流动API发送请求 (尝试 {attempt+1}/{max_retries})")
                logger.info(f"请求URL: {url}")
                logger.info(f"请求头: {self.session.headers}")
                logger.info(f"请求体: {json.dumps(payload, ensure_ascii=False)[:500]}...")
                
                # 使用渐进式超时策略 - 随着重试次数增加，超时时间也增加
                dynamic_timeout = timeout * (1 + attempt * 0.5)  # 每次重试增加50%超时时间
                logger.info(f"设置请求超时: {dynamic_timeout:.1f}秒 (尝试 {attempt+1})")
                
                response = self.session.post(url, json=payload, timeout=dynamic_timeout)
                
                # 检查响应代码，处理各种错误情况
                if response.status_code == 503:
                    logger.warning(f"API服务暂时不可用(503)，正在重试...")
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        retry_delay *= 1.5  # 更平缓的指数退避策略
                        continue
                        
                # 检查响应是否为JSON格式（防止非JSON响应导致错误）
                try:
                    result = response.json()
                except ValueError:
                    logger.error(f"响应不是有效的JSON: {response.text[:200]}")
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        retry_delay *= 1.5
                        continue
                    else:
                        raise ValueError(f"API返回了非JSON响应: {response.text[:200]}")
                
                response.raise_for_status()
                logger.info("硅基流动API请求成功")
                return result
                
            except requests.exceptions.Timeout as e:
                # 单独处理超时错误
                logger.warning(f"API请求超时 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logger.info(f"超时后等待 {wait_time} 秒再重试...")
                    time.sleep(wait_time)
                    retry_delay *= 1.5
                else:
                    logger.error(f"硅基流动API请求超时，已达到最大重试次数，放弃尝试")
                    raise
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text[:200]}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    retry_delay *= 1.5
                else:
                    logger.error(f"硅基流动API请求失败，已达到最大重试次数")
                    raise
                    
            except Exception as e:
                logger.error(f"硅基流动API请求失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    retry_delay *= 1.5
                else:
                    logger.error(f"硅基流动API请求失败，已达到最大重试次数: {str(e)}")
                    raise
    
    def _make_api_request(self, endpoint, payload, max_retries=3, timeout=120):
        """发送API请求到硅基流动，包含重试机制"""
        url = f"{self.api_base_url}/{endpoint}"
        
        # 移除payload中的max_tokens参数，使用API默认值(512)
        if 'max_tokens' in payload:
            logger.info("移除max_tokens参数，使用API默认值")
            del payload['max_tokens']
        
        return self._send_request(url, payload, timeout, max_retries)
    
    def generate_research_plan(self, topic, requirements):
        """根据主题和要求生成简洁的研究计划，专注于核心问题而非具体内容"""
        prompt = f"""
        为主题"{topic}"创建一个简洁有效的研究计划。请遵循以下指导原则：

        1. 聚焦于3-5个核心研究问题，而不是提供实际内容或结论
        2. 每个问题应该清晰、短小、可搜索，可以分几个子问题
        3. 不要在计划中包含具体的结论、数据或分析（这些将在实际搜索中获取）
        4. 考虑用户的特定要求: {requirements}

        输出格式:
        # 研究计划: {topic}

        ## 研究目标
        [简要描述研究目标，1-2句话]

        ## 核心研究问题
        1. [研究问题1]
           - [子问题1.1]
           - [子问题1.2]
        2. [研究问题2]
           - [子问题2.1]
           - [子问题2.2]
        3. [研究问题3]
           - [子问题3.1]
           - [子问题3.2]

        ## 研究方法
        - [简要描述将采用的搜索和分析方法]
        """
        
        # 使用更高的温度稍错提高创造性，因为我们需要多元化的问题
        payload = {
            "model": "Pro/deepseek-ai/DeepSeek-V3",  # 使用硅基流动支持的模型
            "messages": [
                {"role": "system", "content": "你是一个专业的研究规划助手，擅长生成简洁清晰、问题导向的研究计划。你只提出问题，不提供答案。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6,  # 微调温度以平衡创造性和精确性
        }
        
        try:
            logger.info(f"使用硬相流动API生成研究计划: {topic}")
            response = self._make_api_request("chat/completions", payload)
            content = response["choices"][0]["message"]["content"]
            logger.info(f"成功生成研究计划，长度: {len(content)}")
            return content
        except Exception as e:
            logger.error(f"生成研究计划失败: {str(e)}")
            raise
    
    def analyze_step_findings(self, step_title, findings):
        """分析单个研究步骤的发现数据"""
        prompt = f"""
        请分析以下关于"{step_title}"的研究发现，并提供简明扼要的结论。
        
        研究发现:
        {findings}
        
        请根据以上研究发现提供一个简洁而全面的分析，包括以下内容：
        1. 主要数据点和关键洞察
        2. 数据之间的联系和模式
        3. 对"{step_title}"的总体结论
        
        分析应当基于事实，避免无根据的推测。请保持客观并突出数据支持的核心发现。
        """
        
        payload = {
            "model": "Pro/deepseek-ai/DeepSeek-V3",  # 可以根据实际情况选择适合的模型
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            response = self._make_api_request("chat/completions", payload)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"分析研究步骤发现时出错: {str(e)}")
            return f"分析'{step_title}'的研究发现时出错。"
    
    def generate_search_queries(self, research_plan, step_title):
        """根据研究计划和步骤标题生成搜索查询"""
        try:
            logger.info(f"为步骤 '{step_title}' 生成搜索查询")
            
            # 优化的系统提示，专注于从研究问题到1-2个有效查询的转换
            system_message = """你是一个专业的研究搜索助手。你的任务是将研究问题转换为1-2个精准、有效的搜索查询。

生成搜索查询时，请遵循以下原则：
1. 精准和简洁：使用关键词组合而非完整问句
2. 包含时效性：添加年份或时间范围（如「2023-2025」或「最新」）
3. 兼顾中英文：对于专业术语，同时提供中英文组合查询

请仅返回搜索查询，每行一个，无需解释。最多生成三个查询。"""
            
            # 从研究计划中提取相关信息，组建提示
            prompt = f"""基于以下研究计划，为研究步骤「{step_title}」生成有效的搜索查询。

研究计划:
{research_plan}

当前研究步骤: {step_title}

请为这个研究步骤生成有1-3个有效的搜索查询，这些查询应该能帮助我找到有关「{step_title}」的最新、最相关的信息。"""
            
            # 使用较低的温度提高精确度
            payload = {
                "model": "Pro/deepseek-ai/DeepSeek-V3",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,  # 降低温度增加精确性
                "max_tokens": 500   # 减少token使用，因为查询短小
            }
            
            logger.info(f"给模型的提示长度: {len(prompt)}")
            response = self._make_api_request("chat/completions", payload)
            result = response["choices"][0]["message"]["content"]
            
            # 解析响应并处理查询
            queries = [q.strip() for q in result.split('\n') if q.strip()] 
            logger.info(f"成功生成了 {len(queries)} 个搜索查询")
            
            # 确保返回至少一个查询
            if not queries:
                logger.warning("生成的搜索查询为空，使用默认查询")
                # 从提示中提取关键词作为默认查询
                step_info = self._extract_step_info_from_prompt(prompt)
                if step_info:
                    return [step_info]
                return ["缺失查询关键词"]
                
            return queries
            
        except Exception as e:
            logger.error(f"生成搜索查询时出错: {str(e)}")
            return ["无法生成搜索查询"]
            
    def _extract_step_info_from_prompt(self, prompt):
        """从提示中提取研究步骤信息作为备用查询"""
        try:
            lines = prompt.split('\n')
            for line in lines:
                if '研究步骤:' in line or '研究步骤：' in line:
                    return line.split(':', 1)[1].strip() if ':' in line else line.strip()
            return ""
        except Exception:
            return ""
    
    def create_knowledge_content(self, step_title, step_description, topic, research_plan):
        """为知识性步骤（如研究目标、研究方法等）直接生成内容，而不进行搜索
        
        知识性步骤不需要搜索外部内容，而是通过AI直接生成框架和方法论指导
        """
        try:
            logger.info(f"为知识性步骤 '{step_title}' 生成内容")
            
            # 构造提示语，根据步骤类型生成适当内容
            prompt = f"""
            你是一位资深的研究专家，请根据以下信息，为研究步骤提供专业的内容:
            
            研究主题: {topic}
            步骤标题: {step_title}
            步骤描述: {step_description}
            
            完整研究计划概述:
            {research_plan[:1000]}  # 限制长度，避免提示过长
            
            请针对此步骤提供专业、全面且结构化的内容。不要进行实际搜索，而是根据你的专业知识，提供关于{step_title}的恰当框架和方法论指导。
            内容应当学术严谨、逻辑清晰，并与整体研究计划保持一致。
            
            如果是研究目标，请提供明确的目标陈述和预期成果。
            如果是研究方法，请概述适合该主题的研究方法和数据收集策略。
            如果是研究背景，请提供对该领域的概述和研究意义。
            
            返回格式应为结构化的Markdown格式，包含适当的小标题和要点列表。
            """

            # 调用API生成内容
            response = self._make_api_request(
                model="Pro/deepseek-ai/DeepSeek-V3",
                messages=[
                    {"role": "system", "content": "你是一位专业的研究顾问，善于提供研究方法指导和框架建议。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            if response and "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            else:
                logger.warning(f"生成知识性内容失败，返回默认内容")
                return f"## {step_title}\n\n此部分内容将在研究执行过程中完善。"
                
        except Exception as e:
            logger.error(f"生成知识性内容时出错: {str(e)}")
            return f"## {step_title}\n\n生成内容时出现错误，此部分内容将在研究执行过程中补充。"
    
    def analyze_research_report(self, research_findings, topic, requirements):
        """分析研究发现并生成最终报告
        
        Args:
            research_findings: 所有的研究发现列表
            topic: 研究主题
            requirements: 用户特定需求
            
        Returns:
            str: 生成的研究报告
        """
        try:
            if not research_findings:
                return "未找到足够的研究发现来生成报告。"
                
            # 格式化研究发现用于提示中
            findings_text = "\n".join([f"- {finding}" for finding in research_findings])
            
            # 构造适合报告生成的增强提示，确保详尽的研究报告
            prompt = f"""请基于以下实际研究过程中收集的研究发现，为主题"{topic}"撰写一份非常详尽全面的研究报告。

研究发现(请完整引用这些发现作为报告支撑):
{findings_text}

{requirements if requirements else ''}

特别重要的要求:
1. **保留完整研究过程中的详细内容** - 对每个研究问题必须有深入的分析，而不是简单的一句话结论
2. **每个研究问题点必须拥有至少150-300字的详细分析**，包含多个观点、数据论证和实例
3. 必须展示业内专家级别的分析深度和广度，避免表面或浅显的分析

报告结构要求:
1. 必须包含清晰的多层结构，包括摘要、研究背景、方法论、主要发现、个问题分析、市场分析、挑战与机遇、详细建议和结论
2. 必须使用数据驱动的方法，包含实际数据、百分比、增长率等具体数字来支持分析
3. 必须使用表格、列表等结构化方式增强内容的条理性
4. 必须直接引用所提供的研究发现作为支持证据

必须按以下详细结构组织报告，表达必须深入、综合、具体，而非模糊或简化:

# {topic} 全面研究报告

## 摘要
[包含研究背景、目的和主要发现的全面概述 - 至少150字]

## 研究背景与方法
[说明研究背景、重要性和使用的研究方法 - 至少150字]

## 核心研究发现
[对每个研究问题进行详细分析，每个问题至少200字的深入分析]

### 研究问题一: [问题标题]
[详细分析包含数据支持、多个观点和具体实例 - 至少250字]

### 研究问题二: [问题标题]
[详细分析包含数据支持、多个观点和具体实例 - 至少250字]

### 研究问题三: [问题标题]
[详细分析包含数据支持、多个观点和具体实例 - 至少250字]

## 市场分析与趋势
[全面分析市场状况、行业趋势、增长预测等 - 至少300字]

## 挑战与机遇
[分析当前面临的主要挑战与潜在机遇 - 至少250字]

## 具体建议
[基于研究发现提供具体可行的建议 - 每个建议至少包含100字的详细说明]

## 结论
[总结性观点和建议 - 至少150字]

## 附录: 研究数据和来源
[列出关键数据和信息来源]
"""

            # 调用API生成报告
            logger.info(f"开始生成研究报告，主题: {topic}")
            
            # 准备请求载荷，正确使用chat/completions端点
            payload = {
                "model": "Pro/deepseek-ai/DeepSeek-V3",
                "messages": [
                    {"role": "system", "content": "你是一位资深的市场研究专家，擅长生成详尽、有洞察力、数据驱动的行业报告。你的研究报告以全面深入的分析和数据展示而闻名。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            
            # 调用API生成报告
            response = self._make_api_request("chat/completions", payload)
            
            # 处理响应
            if response and "choices" in response and len(response["choices"]) > 0:
                report = response["choices"][0]["message"]["content"]
                logger.info("研究报告生成成功")
                return report
            else:
                logger.error("生成研究报告失败，响应数据不完整")
                return "生成报告时出错。请检查系统日志。"
                
        except Exception as e:
            logger.error(f"生成研究报告时出错: {str(e)}")
            return f"生成研究报告时出错: {str(e)}"
    
    def answer_question(self, conversation_history, question):
        """回答用户问题，基于对话历史"""
        messages = []
        
        # 将对话历史转换为消息格式
        for i, msg in enumerate(conversation_history):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": msg})
        
        # 添加当前问题
        messages.append({"role": "user", "content": question})
        
        # 添加系统消息
        system_message = "你是一个专业的研究助手，提供专业、全面、有价值的研究见解。请用中文回复。"
        messages.insert(0, {"role": "system", "content": system_message})
        
        payload = {
            "model": "Pro/deepseek-ai/DeepSeek-V3",  # 可以根据实际情况选择适合的模型
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            response = self._make_api_request("chat/completions", payload, timeout=60)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"回答问题失败: {str(e)}")
            raise

# 创建全局服务实例
siliconflow_service = SiliconFlowService()
