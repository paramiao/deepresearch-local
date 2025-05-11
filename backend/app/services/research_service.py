import os
import re
import time
import threading
import uuid
import random
import logging
from urllib.parse import urlparse
from flask import current_app
from app.services.siliconflow_service import SiliconFlowService
from app.services.search_service import search_service

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResearchProcess:
    """研究过程类，用于管理和跟踪研究过程"""
    
    def __init__(self, topic, requirements):
        self.topic = topic
        self.requirements = requirements
        self.status = "planning"  # planning, researching, analyzing, completed, error
        self.progress = 0
        self.plan = None
        self.current_step = None
        self.research_sites = []
        self.research_findings = []
        self.analysis_results = []
        self.source_contents = {}  # 存储抓取的网页内容
        self.search_queries = []  # 存储搜索查询
        self.research_steps = []  # 存储详细的研究步骤及其进度和结果
        self.current_step_index = 0  # 当前执行到的步骤索引
        self.report = None
        self.error = None
        self.process_id = str(int(time.time() * 1000))
        self.start_time = time.time()
        self.ai_service = SiliconFlowService()
        logger.info(f"初始化硅基流动API服务用于研究过程: {self.process_id}")
        
    def to_dict(self):
        """将研究过程转换为字典"""
        return {
            "process_id": self.process_id,
            "topic": self.topic,
            "requirements": self.requirements,
            "status": self.status,
            "progress": self.progress,
            "plan": self.plan,
            "current_step": self.current_step,
            "current_step_index": self.current_step_index,
            "research_steps": self.research_steps,  # 添加详细的研究步骤列表
            "research_sites": self.research_sites,
            "research_findings": self.research_findings[:15],  # 增加返回的发现数量
            "analysis_results": self.analysis_results,
            "search_queries": self.search_queries[:5],  # 返回的查询数量
            "report": self.report,
            "error": self.error,
            "elapsed_time": round(time.time() - self.start_time, 2)
        }

class ResearchService:
    """研究服务，用于管理所有研究过程"""
    
    def __init__(self):
        self.research_processes = {}
        # 不再预定义网站列表，而是使用搜索服务来获取真实数据
        logger.info("初始化研究服务，使用真实数据模式")
        
    def create_research_process(self, topic, requirements):
        """创建新的研究过程"""
        research_process = ResearchProcess(topic, requirements)
        self.research_processes[research_process.process_id] = research_process
        self._start_research_thread(research_process)
        return research_process.process_id
        
    def get_research_process(self, process_id):
        """获取研究过程"""
        return self.research_processes.get(process_id)
        
    def _start_research_thread(self, research_process):
        """启动研究计划生成线程，只负责生成计划，不执行完整研究"""
        thread = threading.Thread(target=self._generate_research_plan, args=(research_process,))
        thread.daemon = True
        thread.start()
        
    def _generate_research_plan(self, process):
        """只生成研究计划，不执行完整研究过程"""
        try:
            # 1. 生成研究计划
            process.status = "planning"
            process.current_step = "生成研究计划"
            
            try:
                process.plan = process.ai_service.generate_research_plan(
                    process.topic, process.requirements
                )
                logger.info("研究计划生成成功")
                process.progress = 20
            except Exception as e:
                logger.error(f"生成研究计划时出错: {str(e)}")
                process.error = f"生成研究计划时出错: {str(e)}"
                process.status = "error"
                return
                
            # 2. 等待用户确认研究计划
            process.status = "waiting_confirmation"
            process.current_step = "等待用户确认研究计划"
            
            # 后续的研究执行步骤将在用户确认后通过start_research_execution触发
            
        except Exception as e:
            process.error = f"生成研究计划过程中出错: {str(e)}"
            process.status = "error"
        
    def _conduct_research(self, process):
        """按照研究计划的每个步骤执行研究（仅在用户确认计划后进行）
        优化版流程：专注于核心研究问题的专门检索和分析
        """
        try:
            # 确保当前状态正确 - 允许confirmed或waiting_confirmation状态
            if process.status != "confirmed" and process.status != "waiting_confirmation":
                logger.error(f"状态错误，无法执行研究: {process.status}")
                return
                
            logger.info(f"用户已确认研究计划，开始执行研究: {process.process_id}")
            
            # 1. 解析研究计划中的步骤，优化版本专注于研究问题
            research_steps = self._parse_research_plan(process.plan, prioritize_questions=True)
            total_steps = len(research_steps)
            
            # 初始化研究步骤数据结构
            process.research_steps = [
                {
                    "title": step["title"],
                    "description": step["description"],
                    "is_core_question": step.get("is_core_question", False),  # 新增属性，标记是否为核心研究问题
                    "completed": False,
                    "search_results": [],
                    "findings": [],
                    "analysis": None
                }
                for step in research_steps
            ]
            
            # 更新状态为研究中
            process.status = "researching"
            process.progress = 30
            
            # 2. 区分核心研究问题和其他步骤
            core_research_steps = []
            knowledge_steps = []  # 研究目标和研究方法等知识性步骤
            
            for i, step in enumerate(research_steps):
                step_title = step["title"]
                step_description = step["description"]
                is_core_question = False
                
                # 使用更精确的检测方法判断步骤类型
                if step.get("is_core_question", False) or \
                   ("核心" in step_title and "问题" in step_title) or \
                   ("研究问题" in step_title) or \
                   ("关键问题" in step_title) or \
                   any(q in step_title.lower() for q in ["问题", "question", "inquiry", "探究"]):
                    is_core_question = True
                    step["is_core_question"] = True  # 更新步骤属性
                    process.research_steps[i]["is_core_question"] = True  # 保持同步
                    core_research_steps.append(i)
                elif ("研究目标" in step_title) or ("研究方法" in step_title) or \
                     ("研究背景" in step_title) or ("研究范围" in step_title):
                    knowledge_steps.append(i)
                    # 将这些步骤标记为知识性步骤
                    step["is_knowledge_step"] = True
                    process.research_steps[i]["is_knowledge_step"] = True
                else:
                    # 其他实质性分析步骤也视为核心
                    core_research_steps.append(i)
                
                logger.info(f"步骤 {i+1}: {step_title} - {'核心研究问题' if is_core_question else '知识性步骤' if i in knowledge_steps else '分析步骤'} (优先级: {len(core_research_steps)})")
                
                # 初始化步骤数据中的原始内容
                process.research_steps[i]["original_content"] = step.get("original_content", "")  # 保存原始内容
            
            # 优化研究流程 - 按不同类型处理步骤并保留完整过程
            
            # 先处理知识性步骤(研究目标等)
            for i in knowledge_steps:
                step = research_steps[i]
                step_title = step["title"]
                step_description = step["description"]
                
                process.current_step = f"生成知识性内容: {step_title} ({i+1}/{total_steps})"
                logger.info(f"开始处理知识性步骤 {i+1}/{total_steps}: {step_title}")
                
                # 更新当前步骤索引
                process.current_step_index = i
                current_step_data = process.research_steps[i]
                
                # 使用AI直接生成概述，而非执行搜索
                from app.services.siliconflow_service import siliconflow_service
                
                analysis = siliconflow_service.create_knowledge_content(
                    step_title,
                    step_description,
                    process.topic,
                    process.plan
                )
                
                current_step_data["analysis"] = analysis
                logger.info(f"生成了知识性步骤 '{step_title}' 的内容")
                current_step_data["completed"] = True
                
                # 更新进度
                progress_increment = 10 / len(knowledge_steps) if len(knowledge_steps) > 0 else 0
                process.progress = 30 + progress_increment
            
            # 处理核心研究问题 - 每个问题单独搜索并生成分析
            logger.info(f"开始处理核心研究问题，共 {len(core_research_steps)} 个问题")
            
            for idx, i in enumerate(core_research_steps):
                step = research_steps[i]
                step_title = step["title"]
                step_description = step["description"]
                
                process.current_step = f"研究问题: {step_title} ({idx+1}/{len(core_research_steps)})"
                logger.info(f"开始执行核心研究问题 {idx+1}/{len(core_research_steps)}: {step_title}")
                
                # 更新当前步骤索引
                process.current_step_index = i
                current_step_data = process.research_steps[i]
                current_step_data["step_number"] = i+1  # 保存步骤编号
                current_step_data["search_queries"] = []  # 初始化步骤的搜索查询列表
                step_findings = []
                
                # 生成当前研究问题的搜索查询
                search_queries = self._generate_step_search_queries(step_title, step_description, process.topic)
                logger.info(f"为核心研究问题 '{step_title}' 生成了 {len(search_queries)} 个搜索查询")
                
                # 存储步骤的搜索查询，便于前端展示
                current_step_data["search_queries"] = search_queries
                
                # 添加到总查询列表中
                process.search_queries.extend(search_queries)
                
                # 对每个查询执行搜索
                for query_idx, query in enumerate(search_queries):
                    process.current_step = f"搜索: '{query}' (问题 {idx+1}/{len(core_research_steps)}, 查询 {query_idx+1}/{len(search_queries)})"
                    logger.info(f"执行搜索查询 {query_idx+1}/{len(search_queries)}: {query}")
                    
                    # 调用搜索服务
                    search_results = search_service.search(query)
                    logger.info(f"查询 '{query}' 返回了 {len(search_results)} 个结果")
                    
                    # 为查询创建结果结构
                    query_result = {
                        "query": query,
                        "results": [],
                        "findings": []
                    }
                    
                    # 处理搜索结果
                    for result in search_results:
                        site_info = {
                            "name": result["source"],
                            "url": result["link"],
                            "title": result["title"],
                            "snippet": result["snippet"],
                            "icon": result.get("source_icon", "🔍")
                        }
                        
                        # 添加到当前查询的结果中
                        query_result["results"].append(site_info)
                        
                        # 添加到步骤的总搜索结果中
                        if site_info not in current_step_data["search_results"]:
                            current_step_data["search_results"].append(site_info)
                        
                        # 同时添加到总的研究网站列表中
                        if site_info not in process.research_sites:
                            process.research_sites.append(site_info)
                    
                    # 从搜索结果提取内容
                    extracted_findings = []
                    for result_idx, result in enumerate(search_results[:3]):  # 每个查询选择3个结果深入分析
                        try:
                            url = result["link"]
                            process.current_step = f"提取内容: {result['source']} (问题 {idx+1}, 查询 {query_idx+1})"
                            
                            # 获取网页内容
                            content = search_service.fetch_content(url)
                            if not content:
                                continue
                                
                            # 存储网页内容
                            process.source_contents[url] = content
                            
                            # 提取相关信息
                            key_info = search_service.extract_key_information(content, query)
                        
                            # 只有当key_info有效且不为None时才创建发现
                            if key_info:
                                # 格式化发现内容，增强可读性
                                domain = urlparse(result['link']).netloc
                                finding = f"根据{result['source']}({domain})的数据，{key_info}"
                                
                                # 添加到当前查询的发现中
                                query_result["findings"].append(finding)
                                extracted_findings.append(finding)
                                
                                # 添加到步骤的发现中
                                if finding not in current_step_data["findings"]:
                                    current_step_data["findings"].append(finding)
                                    logger.info(f"添加新的研究发现: {finding[:100]}...")
                                    
                                # 同时添加到总的研究发现中
                                if finding not in process.research_findings:
                                    process.research_findings.append(finding)
                                    step_findings.append(finding)
                            else:
                                logger.warning(f"无法从 {result['source']} 提取有效信息")
                        except Exception as e:
                            logger.error(f"获取网页内容时出错: {str(e)}")
                    
                    # 将当前查询的结果存储到步骤中
                    if not hasattr(current_step_data, "query_results"):
                        current_step_data["query_results"] = []
                    current_step_data["query_results"].append(query_result)
                    
                    # 为当前查询生成小结
                    if extracted_findings:
                        query_summary = self._generate_query_summary(query, extracted_findings, step_title)
                        query_result["summary"] = query_summary
                        logger.info(f"为查询 '{query}' 生成了小结")

                
                # 使用LLM分析该步骤的结果
                if step_findings:
                    process.current_step = f"分析步骤 {i+1} 的发现: {step_title}"
                    step_analysis = process.ai_service.analyze_step_findings(
                        step_title, 
                        "\n".join(step_findings)
                    )
                    
                    # 保存分析结果
                    current_step_data["analysis"] = step_analysis
                    process.analysis_results.append(f"**{step_title}**\n{step_analysis}")
                else:
                    # 如果没有发现，也需要添加一个空的分析结果
                    current_step_data["analysis"] = "未收集到足够的数据进行分析。"
                    process.analysis_results.append(f"**{step_title}**\n未收集到足够的数据进行分析。")
                
                # 标记步骤完成
                current_step_data["completed"] = True
                
                # 更新进度
                process.progress = 30 + (i+1) * (50 / total_steps)
            
            # 3. 生成报告阶段
            process.status = "reporting"
            process.current_step = "生成研究报告"
            process.progress = 90
            
            try:
                # 收集所有步骤的研究发现和分析结果 - 全面增强版
                findings_text = ""
                
                # 收集所有核心研究问题的详细发现和分析
                core_questions = []
                for step_data in process.research_steps:
                    if step_data.get("is_core_question", False):
                        core_questions.append(step_data)
                
                logger.info(f"为研究报告收集了 {len(core_questions)} 个核心研究问题的详细分析")
                
                # 为每个核心研究问题生成深度分析文本
                detailed_analyses = {}
                
                # 生成每个核心问题的详细分析
                for question_data in core_questions:
                    question_title = question_data['title']
                    question_id = question_data.get('step_number', 0)
                    
                    # 收集该问题的所有发现
                    all_findings = question_data.get('findings', [])
                    
                    # 收集该问题的所有查询结果
                    query_results = question_data.get('query_results', [])
                    
                    # 创建每个问题的详细分析
                    detailed_analysis = f"## 研究问题{question_id}: {question_title}\n\n"
                    detailed_analysis += f"**问题描述**: {question_data['description']}\n\n"
                    
                    # 添加搜索过程
                    if query_results:
                        detailed_analysis += f"### 搜索过程\n\n"
                        detailed_analysis += f"为回答该问题，我们执行了以下{len(question_data.get('search_queries', []))}个搜索查询：\n\n"
                        
                        # 添加每个查询的结果和小结
                        for idx, query_result in enumerate(query_results):
                            query = query_result.get('query', '')
                            findings = query_result.get('findings', [])
                            summary = query_result.get('summary', '')
                            
                            detailed_analysis += f"#### 查询 {idx+1}: `{query}`\n\n"
                            
                            # 添加该查询的小结
                            if summary:
                                detailed_analysis += f"**小结**: {summary}\n\n"
                            
                            # 添加关键发现
                            if findings:
                                detailed_analysis += f"**关键发现**:\n\n"
                                for finding in findings[:3]:  # 限制每个查询显示前3个发现
                                    detailed_analysis += f"- {finding}\n"
                                detailed_analysis += "\n"
                    
                    # 添加该问题的最终分析
                    if question_data.get('analysis'):
                        detailed_analysis += f"### 问题分析\n\n{question_data['analysis']}\n\n"
                    
                    # 存储该问题的详细分析
                    detailed_analyses[question_title] = detailed_analysis
                    
                # 准备研究报告的数据
                findings_text += f"# 研究分析报告: {process.topic}\n\n"
                findings_text += f"*本报告深入研究了主题: {process.topic}*\n\n"
                
                if process.requirements:
                    findings_text += f"**研究要求**: {process.requirements}\n\n"
                
                # 添加数据收集统计
                total_search_queries = sum(len(step.get('search_queries', [])) for step in process.research_steps)
                total_search_results = sum(len(step.get('search_results', [])) for step in process.research_steps)
                total_findings = sum(len(step.get('findings', [])) for step in process.research_steps)
                
                findings_text += f"## 研究方法与数据\n\n"
                findings_text += f"- 研究深度: 执行了 {len(core_questions)} 个核心研究问题的详细分析\n"
                findings_text += f"- 搜索范围: 执行了 {total_search_queries} 个精心设计的搜索查询\n"
                findings_text += f"- 数据量: 分析了 {total_search_results} 个搜索结果，提取了 {total_findings} 条相关发现\n\n"
                
                # 添加详细的每个研究问题分析
                findings_text += "## 研究问题列表\n\n"
                
                # 添加问题列表
                for idx, question_data in enumerate(core_questions):
                    findings_text += f"{idx+1}. **{question_data['title']}**\n"
                
                findings_text += "\n## 详细分析\n\n"
                
                # 添加每个问题的详细分析
                for question_data in core_questions:
                    findings_text += detailed_analyses[question_data['title']]
                    if step_data.get('search_results'):
                        findings_text += "#### 数据来源\n\n"
                        
                        # 添加数据来源汇总表格
                        findings_text += "| 来源 | 标题 | 类型 |\n"
                        findings_text += "|-------|------|---------|\n"
                        
                        # 增加显示数量，确保不丢失信息
                        for result in step_data['search_results'][:10]:  # 显示前10个结果
                            result_type = result.get('type', '网页')
                            findings_text += f"| {result['name']} | {result['title']} | {result_type} |\n"
                        
                        # 如果还有更多结果，添加汇总信息
                        if len(step_data['search_results']) > 10:
                            remaining = len(step_data['search_results']) - 10
                            findings_text += f"\n*及其他 {remaining} 个数据来源*\n"
                            
                        findings_text += "\n"
                    
                    # 添加研究发现 - 对发现进行分类和标注
                    if step_data.get('findings'):
                        findings_text += "#### 详细发现\n\n"
                        
                        # 尝试检测发现中的数据类型，加以标记
                        statistical_findings = []
                        trend_findings = []
                        comparison_findings = []
                        general_findings = []
                        
                        for finding in step_data['findings']:
                            # 检测包含数字统计信息的发现
                            if re.search(r'\d+(\.\d+)?\s*(%|百分比|亿|万|千|元)', finding):
                                statistical_findings.append(finding)
                            # 检测趋势相关的发现
                            elif re.search(r'(增长|下降|趋势|变化|发展|未来|\d{4}年)', finding):
                                trend_findings.append(finding)
                            # 检测比较信息
                            elif re.search(r'(比|相对|与|对比|不同|类似|差异)', finding):
                                comparison_findings.append(finding)
                            # 其他通用发现
                            else:
                                general_findings.append(finding)
                                
                        # 按类别添加发现
                        if statistical_findings:
                            findings_text += "**统计数据:**\n\n"
                            for finding in statistical_findings:
                                findings_text += f"- {finding}\n"
                            findings_text += "\n"
                            
                        if trend_findings:
                            findings_text += "**趋势分析:**\n\n"
                            for finding in trend_findings:
                                findings_text += f"- {finding}\n"
                            findings_text += "\n"
                            
                        if comparison_findings:
                            findings_text += "**比较分析:**\n\n"
                            for finding in comparison_findings:
                                findings_text += f"- {finding}\n"
                            findings_text += "\n"
                            
                        if general_findings:
                            findings_text += "**其他发现:**\n\n"
                            for finding in general_findings:
                                findings_text += f"- {finding}\n"
                            findings_text += "\n"
                    
                    # 添加分析结果 - 使用引用格式增强可读性
                    if step_data.get('analysis'):
                        findings_text += "#### 专家分析\n\n"
                        # 使用引用格式美化分析显示
                        analysis_lines = step_data['analysis'].strip().split('\n')
                        for line in analysis_lines:
                            if line.strip():
                                # 对标题行使用加粗
                                if re.match(r'^[\s]*\d+\.\s+', line) or line.strip().endswith(':'):
                                    findings_text += f"**{line.strip()}**\n\n"
                                else:
                                    findings_text += f"> {line.strip()}\n\n"
                    
                    findings_text += "---\n\n"
                
                # 生成最终研究报告
                logger.info("开始生成研究报告")
                try:
                    # 提取所有研究发现用于生成报告
                    all_findings = []
                    for step in process.research_steps:
                        if step.get('findings'):
                            all_findings.extend(step.get('findings', []))
                    
                    # 如果没有足够的研究发现，添加备用内容
                    if len(all_findings) < 3:
                        # 添加从findings_text中提取的内容
                        extracted_findings = [line.strip('- ') for line in findings_text.split('\n') 
                                            if line.strip().startswith('- ') and len(line) > 5]
                        all_findings.extend(extracted_findings)
                    
                    # 确保研究发现不重复
                    unique_findings = list(dict.fromkeys(all_findings))
                    
                    # 记录研究发现数量
                    logger.info(f"为研究报告准备了 {len(unique_findings)} 条研究发现")
                    
                    # 尝试通过AI服务生成研究报告，使用正确的方法和参数
                    process.report = process.ai_service.analyze_research_report(
                        unique_findings,
                        process.topic,
                        process.requirements
                    )
                    logger.info("研究报告生成成功")
                except Exception as e:
                    # 如果AI服务失败，使用备用方案生成报告
                    logger.warning(f"使用AI服务生成报告失败: {str(e)}，切换到备用方案")
                    
                    # 创建一个结构化的报告，使用已经提取的研究发现
                    process.report = self._generate_fallback_report(
                        process.topic, 
                        process.requirements,
                        unique_findings, 
                        process.research_steps
                    )
                    logger.info("使用备用方案生成报告成功")
                
                # 完成研究
                process.progress = 100
                process.status = "completed"
                process.current_step = "研究完成"
            except Exception as e:
                logger.error(f"生成研究报告时出错: {str(e)}")
                process.error = f"生成研究报告时出错: {str(e)}"
                process.status = "error"
            
        except Exception as e:
            process.error = f"研究过程中出错: {str(e)}"
            process.status = "error"
    
    def _generate_fallback_report(self, topic, requirements, findings, research_steps):
        """生成备用研究报告，当AI服务无法生成报告时使用
        
        Args:
            topic: 研究主题
            requirements: 用户的特定需求
            findings: 已经提取的研究发现列表
            research_steps: 研究步骤数据
        """
        from datetime import datetime
        import re
        
        logger.info(f"使用备用方案为主题 '{topic}' 生成研究报告")
        
        # 按类型分类研究发现
        statistical_findings = []
        trend_findings = []
        comparison_findings = []
        general_findings = []
        
        for finding in findings:
            # 检测包含数字统计信息的发现
            if re.search(r'\d+(\.\d+)?\s*(%|百分比|亿|万|千|元)', finding):
                statistical_findings.append(finding)
            # 检测趋势相关的发现
            elif re.search(r'(增长|下降|趋势|变化|发展|未来|\d{4}年)', finding):
                trend_findings.append(finding)
            # 检测比较信息
            elif re.search(r'(比|相对|与|对比|不同|类似|差异)', finding):
                comparison_findings.append(finding)
            # 其他通用发现
            else:
                general_findings.append(finding)
        
        # 提取完成的研究步骤标题
        completed_steps = [step.get('title', '') for step in research_steps if step.get('completed', False)]
        
        # 生成当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建报告标题
        report = f"""# {topic} 研究报告

## 摘要

本报告汇总了关于"{topic}"的综合研究发现，并提供了相关市场分析和建议。研究通过多个数据源和网络资源进行，涵盖了多个相关方面。
"""
        
        # 添加用户需求部分（如果有）
        if requirements:
            report += f"""
## 研究目标与范围

当前研究是应用户要求进行的，具体需求如下：

"{requirements}"

研究内容涵盖了以下主要方面：

{', '.join(completed_steps)}
"""
        
        # 添加统计数据发现
        if statistical_findings:
            report += """
## 关键数据与统计

以下是研究中发现的重要数据和统计信息：

"""
            for finding in statistical_findings:
                report += f"- {finding}\n"
        
        # 添加趋势相关发现
        if trend_findings:
            report += """
## 市场趋势分析

研究发现了以下市场和行业趋势：

"""
            for finding in trend_findings:
                report += f"- {finding}\n"
        
        # 添加比较分析发现
        if comparison_findings:
            report += """
## 比较分析

以下是不同方面的比较分析：

"""
            for finding in comparison_findings:
                report += f"- {finding}\n"
        
        # 添加一般发现
        if general_findings:
            report += """
## 其他重要发现

研究过程中收集的其他重要发现包括：

"""
            for finding in general_findings:
                report += f"- {finding}\n"
        
        # 添加结论和建议
        report += f"""
## 结论与建议

基于以上研究发现，我们对"{topic}"提出以下结论和建议：

1. 本研究提供了多角度的观点和数据，应根据具体应用场景进行选择应用。
2. 建议进一步深入分析特定领域的数据，以获得更精确的洞察。
3. 市场与技术环境持续变化，定期进行类似研究可以跟踪最新趋势。

---
报告生成时间: {current_time}
"""
        
        logger.info("高质量备用报告生成成功")
        return report
        
    def start_research_execution(self, process_id):
        """开始执行研究（在用户确认计划后）"""
        process = self.get_research_process(process_id)
        if not process:
            logger.error(f"无法找到研究进程: {process_id}")
            return False
            
        if process.status != "waiting_confirmation":
            logger.error(f"研究进程状态不正确，无法执行: {process.status}")
            return False
            
        # 更新状态，表明用户已确认研究计划
        process.status = "confirmed"
        logger.info(f"研究计划已被用户确认: {process_id}")
        
        # 启动一个新线程来执行研究
        logger.info(f"开始执行研究过程: {process_id}")
        thread = threading.Thread(target=self._conduct_research, args=(process,))
        thread.daemon = True
        thread.start()
        return True
    
    def _parse_research_plan(self, plan, prioritize_questions=False):
        """从研究计划中解析出各个研究步骤 - 增强版本
        
        Args:
            plan: 研究计划文本
            prioritize_questions: 是否优先处理研究问题（比如将研究问题放在前面处理）
            
        Returns:
            解析出的研究步骤列表
        """
        try:
            # 如果计划为空或不合法，返回默认的研究步骤
            if not plan:
                logger.warning("研究计划为空，使用默认步骤")
                return self._get_default_research_steps()
            
            logger.info("-------- 开始解析研究计划 --------")
            logger.info(f"原始计划\n{plan}")
            
            # 方法1：使用标题模式识别步骤
            steps = self._parse_steps_by_headers(plan)
            
            # 方法2：如果标题解析失败，尝试使用编号列表匹配
            if not steps:
                logger.info("标题解析失败，尝试使用编号列表匹配")
                steps = self._parse_steps_by_numbered_list(plan)
            
            # 方法3：如果上述方法失败，尝试使用空行分隔段落
            if not steps:
                logger.info("编号解析失败，尝试使用段落分析")
                steps = self._parse_steps_by_paragraphs(plan)
            
            # 标记研究问题和知识性步骤
            research_questions = []
            knowledge_steps = []
            analysis_steps = []
            
            # 分类每个步骤
            for i, step in enumerate(steps):
                step_title = step["title"]
                
                # 标记是否为核心研究问题
                if ("核心" in step_title and "问题" in step_title) or \
                   ("研究问题" in step_title) or \
                   ("关键问题" in step_title) or \
                   any(q in step_title.lower() for q in ["问题", "question", "inquiry", "探究"]):
                    step["is_core_question"] = True
                    research_questions.append(step)
                # 标记知识性步骤
                elif ("研究目标" in step_title) or ("研究方法" in step_title) or \
                     ("研究背景" in step_title) or ("研究范围" in step_title):
                    step["is_knowledge_step"] = True
                    knowledge_steps.append(step)
                # 其他为分析步骤
                else:
                    analysis_steps.append(step)
                    
                # 保存原始文本片段，用于前端显示
                step["original_content"] = step["description"]
                
                # 确保步骤标题合理
                if len(step["title"]) > 50:
                    step["title"] = step["title"][:47] + "..."
                    
                # 确保步骤描述合适
                if len(step["description"]) > 500:
                    step["description"] = step["description"][:150] + "..." + step["description"][-150:]
            
            # 确保至少有一个研究步骤
            if not steps:
                logger.warning("所有解析方法均失败，使用默认步骤")
                return self._get_default_research_steps()
            
            # 如果需要优先处理研究问题，调整步骤顺序
            if prioritize_questions and research_questions:
                logger.info(f"启用优先处理研究问题模式，找到 {len(research_questions)} 个研究问题")
                # 按筛选归类重排步骤：先知识性步骤、然后核心研究问题、最后是分析步骤
                reordered_steps = knowledge_steps + research_questions + analysis_steps
                steps = reordered_steps
                logger.info(f"重排完成，新的步骤顺序: 知识性步骤({len(knowledge_steps)}) -> 研究问题({len(research_questions)}) -> 分析步骤({len(analysis_steps)})")
            
            # 记录提取的步骤
            logger.info(f"成功提取了 {len(steps)} 个研究步骤:")
            for i, step in enumerate(steps):
                step_type = '核心研究问题' if step.get('is_core_question', False) else '知识性步骤' if step.get('is_knowledge_step', False) else '分析步骤'
                logger.info(f"  步骤 {i+1}: {step['title']} ({step_type})")
                logger.info(f"  描述: {step['description'][:100]}...")
            
            return steps
        
        except Exception as e:
            logger.error(f"解析研究计划时出错: {str(e)}")
            logger.exception(e)  # 打印完整堆栈跟踪
            # 出错时返回默认步骤
            return self._get_default_research_steps()
    
    def _get_default_research_steps(self):
        """获取默认的研究步骤"""
        return [
            {"title": "市场概览", "description": "分析市场规模和增长趋势", "original_content": "分析市场规模和增长趋势"}, 
            {"title": "竞争分析", "description": "评估主要竞争对手和竞争态势", "original_content": "评估主要竞争对手和竞争态势"}, 
            {"title": "关键驱动因素", "description": "评估市场成长的主要驱动因素", "original_content": "评估市场成长的主要驱动因素"},
            {"title": "趋势展望", "description": "分析未来发展趋势和机会", "original_content": "分析未来发展趋势和机会"}
        ]
        
    def _parse_steps_by_headers(self, plan):
        """根据标题标记(#、##等)解析研究步骤"""
        steps = []
        current_step = None
        
        for line in plan.split('\n'):
            line = line.strip()
            
            # 检测标题行
            header_match = re.match(r'^(#+)\s+(.+)$', line)
            if header_match:
                header_level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                # 如果标题级别为1或30上的字符，则可能是主标题，不是研究步骤
                if (header_level > 1 or len(title) <= 30) and not title.lower().startswith(('overview', '概述', '简介', '介绍', '关于')):
                    # 保存当前步骤（如果有）
                    if current_step and current_step["title"] and current_step["description"].strip():
                        steps.append(current_step)
                    
                    # 创建新步骤
                    current_step = {"title": title, "description": ""}
                elif current_step:  # 如果为子标题或其他标题类型，并且已有当前步骤
                    current_step["description"] += line + "\n"
            
            # 收集非标题行
            elif current_step and line:
                current_step["description"] += line + "\n"
        
        # 添加最后一个步骤
        if current_step and current_step["title"] and current_step["description"].strip():
            steps.append(current_step)
            
        return steps
    
    def _parse_steps_by_numbered_list(self, plan):
        """根据编号列表(1. 2. 等)解析研究步骤"""
        steps = []
        lines = plan.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 匹配编号形式：1. 2. 或 1) 2) 等
            num_match = re.match(r'^(\d+)[.)]\s+(.+)$', line)
            if num_match:
                number = int(num_match.group(1))
                title = num_match.group(2).strip()
                
                # 如果是编号为1的新列表或编号按顺序的条目
                if number == 1 or len(steps) > 0:
                    description = ""
                    j = i + 1
                    
                    # 查找当前条目关联的所有文本
                    while j < len(lines) and not re.match(r'^\d+[.)]\s+', lines[j].strip()):
                        if lines[j].strip():  # 只添加非空行
                            description += lines[j].strip() + "\n"
                        j += 1
                        if j >= len(lines) or lines[j].strip() == "":
                            break
                    
                    steps.append({"title": title, "description": description})
                    i = j - 1  # 调整索引位置
            i += 1
            
        return steps
    
    def _parse_steps_by_paragraphs(self, plan):
        """根据段落结构解析研究步骤"""
        steps = []
        paragraphs = re.split(r'\n\s*\n', plan)  # 按空行分隔段落
        
        # 过滤掉可能的引言段落
        filtered_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            # 跳过空段落和可能是标题的段落
            if not p or len(p.split('\n')) == 1 and len(p) < 40:
                continue
            filtered_paragraphs.append(p)
        
        # 如果只有一个段落，再进一步尝试分割
        if len(filtered_paragraphs) == 1:
            text = filtered_paragraphs[0]
            # 尝试按可能的分隔符分割
            split_paragraphs = re.split(r'\n\s*[-*]\s+|\n\s*\d+\.\s+', text)
            if len(split_paragraphs) > 1:
                filtered_paragraphs = split_paragraphs
        
        # 限制最多6个步骤
        max_steps = min(len(filtered_paragraphs), 6)
        
        for i in range(max_steps):
            p = filtered_paragraphs[i].strip()
            lines = p.split('\n')
            
            # 取第一行作为标题，如果它足够短
            if len(lines) > 0 and len(lines[0]) < 100:
                title = lines[0].strip()
                description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
            else:
                # 如果第一行太长，生成一个合适的标题
                words = re.findall(r'\w+', p[:200])  # 取前200个字符分析
                title = f"研究步骤 {i+1}: " + (' '.join(words[:5]) + "..." if len(words) > 5 else ' '.join(words))
                description = p
            
            steps.append({"title": title, "description": description})
            
        return steps
            
    def _generate_query_summary(self, query, findings, question_title):
        """为单个查询生成小结，便于用户理解该查询的研究成果
        
        Args:
            query: 搜索查询
            findings: 从该查询中提取的发现列表
            question_title: 研究问题标题
            
        Returns:
            str: 该查询的小结分析
        """
        try:
            if not findings:
                return f"未从查询'{query}'中获取到有效信息"
                
            # 使用AI服务生成小结
            from app.services.siliconflow_service import siliconflow_service
            
            # 构建提示
            prompt = f"""请根据以下从搜索查询'{query}'中提取的信息，为研究问题"{question_title}"生成一个简短但有信息量的小结。
            
提取的信息如下：
{chr(10).join([f'- {finding}' for finding in findings])}

请总结上述信息的关键点，确保小结：
1. 直接回答与查询'{query}'相关的部分
2. 提供具体的数据点和洞见（如果有）
3. 不超过150字
4. 不要添加任何未在提供的信息中出现的内容

小结："""
            
            # 调用API生成小结
            payload = {
                "model": "Pro/deepseek-ai/DeepSeek-V3",
                "messages": [
                    {"role": "system", "content": "你是一位专业的研究助手，擅长简明扼要地总结查询结果。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 300
            }
            
            response = siliconflow_service._make_api_request("chat/completions", payload)
            
            if response and "choices" in response and len(response["choices"]) > 0:
                summary = response["choices"][0]["message"]["content"].strip()
                logger.info(f"为查询'{query}'生成了小结：{summary[:50]}...")
                return summary
            else:
                # 如果AI服务失败，生成一个简单的小结
                return self._generate_simple_summary(findings)
                
        except Exception as e:
            logger.error(f"为查询生成小结时出错: {str(e)}")
            return self._generate_simple_summary(findings)
    
    def _generate_simple_summary(self, findings):
        """生成一个简单的小结，当AI服务失败时使用"""
        if not findings:
            return "未找到相关信息"
            
        # 简单地合并前两个发现
        summary = findings[0]
        if len(findings) > 1:
            summary += "\n此外，" + findings[1]
            
        return summary
    
    def _generate_step_search_queries(self, step_title, step_description, topic):
        """为研究步骤生成搜索查询 - 改进版本，确保查询中包含主题相关的具体关键词"""
        try:
            # 如果是默认步骤，使用预设查询
            if any(default in step_title.lower() for default in ["市场概览", "竞争分析", "关键驱动因素", "趋势展望"]):
                return self._get_default_queries_for_step(step_title, topic)
            
            # 使用AI生成查询
            logger.info(f"为步骤 '{step_title}' 生成搜索查询，主题: {topic}")
            from app.services.siliconflow_service import siliconflow_service
            
            # 使用更严格的提示，强调必须包含具体研究主题
            prompt = f"""请为主题"{topic}"的研究步骤"{step_title}"生成 3 个搜索查询。

需求:
1. 每个查询必须包含"{topic}"这个具体主题词
2. 不要使用抽象术语例如“研究问题”“市场分析”等宽泛词汇
3. 每个查询应该包含具体、直接相关的关键词
4. 查询长度不超过5个关键词
5. 只输出查询词，不要加入数字编号或其他格式化文本

步骤描述: {step_description}

返回格式示例：
{topic} 市场规模 2025
{topic} 最新数据 分析
{topic} 行业领先企业
"""

            # 尝试调用AI生成查询
            queries = []
            try:
                search_queries_text = siliconflow_service.generate_search_queries(prompt, step_title)
                
                # 分行并过滤空行
                raw_queries = [q.strip() for q in search_queries_text.split('\n') if q.strip()]
                
                # 过滤替换提示中的示例查询
                example_pattern = f"{topic} \u5e02\u573a\u89c4\u6a21 2025"
                queries = [q for q in raw_queries if q != example_pattern and len(q) < 100 and not q.startswith('#')]
                
                # 处理每个查询，确保包含研究主题
                for i in range(len(queries)):
                    if topic.lower() not in queries[i].lower():
                        queries[i] = f"{topic} {queries[i]}"
                
                logger.info(f"AI生成了 {len(queries)} 个搜索查询")
                
            except Exception as query_error:
                logger.warning(f"调用查询生成服务出错: {str(query_error)}")
            
            # 如果AI生成的查询不足三个，补充默认查询
            if len(queries) < 3:
                # 计算需要添加的默认查询数量
                needed = 3 - len(queries)
                queries.extend(default_queries[:needed])
                logger.info(f"添加了 {needed} 个默认查询")
            
            # 去除重复查询
            unique_queries = []
            for q in queries:
                normalized_q = q.lower().strip()
                if normalized_q not in [uq.lower().strip() for uq in unique_queries]:
                    unique_queries.append(q)
            
            # 确保所有查询都包含研究主题
            final_queries = []
            for q in unique_queries:
                if topic.lower() in q.lower():
                    final_queries.append(q)
                else:
                    final_queries.append(f"{topic} {q}")
            
            logger.info(f"最终生成了 {len(final_queries)} 个搜索查询: {final_queries[:3]}")
            
            # 只返回前三个查询
            return final_queries[:3]
            
        except Exception as e:
            logger.error(f"生成搜索查询时出错: {str(e)}")
            
            # 如果出错，返回必定包含主题的基本查询
            return [
                f"{topic} {step_title}", 
                f"{topic} 最新数据 分析", 
                f"{topic} 研究报告 2025"
            ]

            
    def _generate_search_queries(self, topic, requirements):

        """基于主题和要求生成搜索查询"""

        # 初始化查询列表
        queries = []
        
        # 基础查询 - 主题本身
        queries.append(topic)
        
        # 特定领域查询
        if "汽车" in topic or "电动汽车" in topic or "新能源" in topic:
            queries.extend([
                f"{topic} 市场规模 数据",
                f"{topic} 行业趋势分析",
                f"{topic} 销量排名"
            ])
            
            # 如果是电动汽车，添加一些特定查询
            if "电动汽车" in topic:
                queries.extend([
                    f"中国电动汽车 补贴政策",
                    f"中国电动汽车 充电基础设施"
                ])
        elif "市场" in topic or "分析" in topic:
            queries.extend([
                f"{topic} 行业报告",
                f"{topic} 数据统计",
                f"{topic} 发展前景"
            ])
        elif "技术" in topic or "创新" in topic:
            queries.extend([
                f"{topic} 最新进展",
                f"{topic} 研究进展",
                f"{topic} 案例分析"
            ])
        else:
            # 通用的查询
            queries.extend([
                f"{topic} 数据分析",
                f"{topic} 行业趋势",
                f"{topic} 发展现状"
            ])
        
        # 如果有特定要求，添加相关查询
        if requirements:
            # 检查是否有特定时间范围
            time_patterns = ["近五年", "近三年", "近十年", "2023", "2022", "2021", "2020"]
            for pattern in time_patterns:
                if pattern in requirements:
                    queries.append(f"{topic} {pattern} 数据")
                    break
            
            # 如果有具体的分析需求
            if "预测" in requirements or "展望" in requirements:
                queries.append(f"{topic} 未来预测")
            
            if "企业" in requirements or "公司" in requirements or "品牌" in requirements:
                queries.append(f"{topic} 主要企业 市场份额")
        
        # 去除重复的查询
        unique_queries = list(set(queries))
        
        # 限制查询数量，避免过多
        return unique_queries[:5]


# 创建全局服务实例
research_service = ResearchService()
