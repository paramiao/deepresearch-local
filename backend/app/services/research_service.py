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
        """按照研究计划的每个步骤执行研究（仅在用户确认计划后进行）"""
        try:
            # 确保当前状态正确
            if process.status != "waiting_confirmation":
                logger.error(f"状态错误，无法执行研究: {process.status}")
                return
                
            logger.info(f"用户已确认研究计划，开始执行研究: {process.process_id}")
            
            # 1. 解析研究计划中的步骤
            research_steps = self._parse_research_plan(process.plan)
            total_steps = len(research_steps)
            
            # 初始化研究步骤数据结构
            process.research_steps = [
                {
                    "title": step["title"],
                    "description": step["description"],
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
            
            # 2. 逐步执行每个研究步骤
            for i, step in enumerate(research_steps):
                # 更新当前步骤索引和状态
                process.current_step_index = i
                current_step_data = process.research_steps[i]
                step_title = step["title"]
                step_description = step["description"]
                
                process.current_step = f"步骤 {i+1}/{total_steps}: {step_title}"
                logger.info(f"执行研究步骤 {i+1}/{total_steps}: {step_title}")
                
                # 为该步骤生成搜索查询
                search_queries = self._generate_step_search_queries(step_title, step_description)
                logger.info(f"为步骤 '{step_title}' 生成了 {len(search_queries)} 个搜索查询")
                
                # 添加到文档中以便前端显示
                process.search_queries.extend(search_queries)
                
                # 执行搜索并收集数据
                step_findings = []
                
                for query in search_queries:
                    process.current_step = f"搜索: {query} (步骤 {i+1}/{total_steps})"
                    logger.info(f"执行搜索查询: {query}")
                    
                    # 调用真实搜索服务
                    search_results = search_service.search(query)
                    logger.info(f"查询 '{query}' 返回了 {len(search_results)} 个结果")
                    
                    # 将网站信息添加到研究网站列表中
                    for result in search_results:
                        site_info = {
                            "name": result["source"],
                            "url": result["link"],
                            "title": result["title"],
                            "snippet": result["snippet"],
                            "icon": result.get("source_icon", "🔍")
                        }
                        
                        # 添加到步骤的搜索结果中
                        if site_info not in current_step_data["search_results"]:
                            current_step_data["search_results"].append(site_info)
                        
                        # 同时添加到总的研究网站列表中
                        if site_info not in process.research_sites:
                            process.research_sites.append(site_info)
                    
                    # 提取网页内容
                    for result in search_results[:3]:  # 每个查询选择3个结果深入分析
                        try:
                            url = result["link"]
                            process.current_step = f"抓取网页内容: {result['source']} (步骤 {i+1})"
                            
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
                                # 记录提取失败的网站但不显示错误消息
                        except Exception as e:
                            logger.error(f"获取网页内容时出错: {str(e)}")
                
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
                # 收集所有步骤的研究发现和分析结果
                findings_text = ""
                
                for i, step_data in enumerate(process.research_steps):
                    findings_text += f"## 步骤 {i+1}: {step_data['title']}\n\n"
                    
                    # 添加步骤描述
                    findings_text += f"{step_data['description']}\n\n"
                    
                    # 添加搜索结果
                    if step_data['search_results']:
                        findings_text += "### 相关数据来源\n\n"
                        for result in step_data['search_results'][:5]:
                            findings_text += f"- {result['title']} ({result['name']})\n"
                        findings_text += "\n"
                    
                    # 添加研究发现
                    if step_data['findings']:
                        findings_text += "### 主要发现\n\n"
                        for finding in step_data['findings']:
                            findings_text += f"- {finding}\n"
                        findings_text += "\n"
                    
                    # 添加分析结果
                    if step_data['analysis']:
                        findings_text += "### 分析\n\n"
                        findings_text += f"{step_data['analysis']}\n\n"
                    
                    findings_text += "---\n\n"
                
                # 生成最终研究报告
                logger.info("开始生成研究报告")
                try:
                    # 尝试通过AI服务生成研究报告
                    process.report = process.ai_service.generate_research_report(
                        process.plan, findings_text
                    )
                    logger.info("研究报告生成成功")
                except Exception as e:
                    # 如果AI服务失败，使用备用方案生成一个简单的研究报告
                    logger.warning(f"使用AI服务生成报告失败: {str(e)}，切换到备用方案")
                    
                    # 创建一个结构化的基本报告
                    process.report = self._generate_fallback_report(process.topic, findings_text)
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
    
    def _generate_fallback_report(self, topic, findings_text):
        """生成备用研究报告，当AI服务无法生成报告时使用"""
        from datetime import datetime
        
        logger.info(f"使用备用方案为主题 '{topic}' 生成研究报告")
        
        # 生成结构化的报告
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# 研究报告: {topic}

## 概述

本报告汇总了关于“{topic}”的研究发现。由于系统负载过高，本报告使用备用生成系统创建。

## 研究方法

本研究通过多个网络数据源收集信息，并使用结构化方法汇总关键发现。

## 研究主体

{findings_text}

## 总结

上述信息提供了关于“{topic}”的多角度观点。建议进一步深入分析各项发现，以得出更全面的结论。

---
报告生成时间: {current_time}
"""
        
        logger.info("备用报告生成成功")
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
            
        # 启动一个新线程来执行研究
        logger.info(f"开始执行研究过程: {process_id}")
        thread = threading.Thread(target=self._conduct_research, args=(process,))
        thread.daemon = True
        thread.start()
        return True
    
    def _parse_research_plan(self, plan):
        """从研究计划中解析出各个研究步骤"""
        try:
            # 如果计划为空或不合法，返回默认的研究步骤
            if not plan:
                logger.warning("研究计划为空，使用默认步骤")
                return [
                    {"title": "市场概览", "description": "分析市场规模和增长趋势"}, 
                    {"title": "竞争分析", "description": "评估主要竞争对手和竞争态势"}, 
                    {"title": "关键驱动因素", "description": "评估市场成长的主要驱动因素"},
                    {"title": "趋势展望", "description": "分析未来发展趋势和机会"}
                ]
                
            steps = []
            current_step = None
            
            for line in plan.split('\n'):
                line = line.strip()
                
                # 如果是标题行，创建一个新步骤
                if line.startswith('##'):
                    title = line.replace('##', '').strip()
                    if current_step and current_step["title"] and current_step["description"]:
                        steps.append(current_step)
                    current_step = {"title": title, "description": ""}
                elif line.startswith('#'):
                    title = line.replace('#', '').strip()
                    if current_step and current_step["title"] and current_step["description"]:
                        steps.append(current_step)
                    current_step = {"title": title, "description": ""}
                # 如果有当前步骤且行不为空
                elif current_step and line:
                    current_step["description"] += line + "\n"
            
            # 添加最后一个步骤
            if current_step and current_step["title"] and current_step["description"]:
                steps.append(current_step)
            
            # 确保至少有一个研究步骤
            if not steps:
                logger.warning("无法从研究计划中解析出步骤，使用默认步骤")
                return [
                    {"title": "市场概览", "description": "分析市场规模和增长趋势"}, 
                    {"title": "竞争分析", "description": "评估主要竞争对手和竞争态势"}, 
                    {"title": "关键驱动因素", "description": "评估市场成长的主要驱动因素"},
                    {"title": "趋势展望", "description": "分析未来发展趋势和机会"}
                ]
                
            logger.info(f"从研究计划中成功提取了{len(steps)}个研究步骤")
            return steps
        except Exception as e:
            logger.error(f"解析研究计划时出错: {str(e)}")
            # 出错时返回默认步骤
            return [
                {"title": "市场概览", "description": "分析市场规模和增长趋势"}, 
                {"title": "竞争分析", "description": "评估主要竞争对手和竞争态势"},
                {"title": "关键驱动因素", "description": "评估市场成长的主要驱动因素"},
                {"title": "趋势展望", "description": "分析未来发展趋势和机会"}
            ]
            
    def _generate_step_search_queries(self, step_title, step_description):
        """为研究步骤生成优化的搜索查询"""

        try:
            # 使用研究标题和描述生成精准查询
            logger.info(f"为研究步骤 '{step_title}' 生成搜索查询")

            
            from app.services.siliconflow_service import siliconflow_service

            
            # 使用简洁的提示生成独特查询
            prompt = f"""请为以下研究步骤生成 3 个精确的搜索查询，以获取最新、最相关的信息。请仅返回搜索查询，每行一个：

研究步骤: {step_title}
描述: {step_description}

查询应该包含研究主题相关的关键词和时间范围，而不是完整的问句。"""

            
            # 调用硅基流动API生成查询
            search_queries_text = ""

            try:
                search_queries_text = siliconflow_service.generate_search_queries(prompt)

            except Exception as query_error:
                logger.warning(f"调用查询生成服务出错: {str(query_error)}")

                # 创建默认查询
                search_queries_text = f"{step_title}\n{step_title} 最新数据\n{step_title} 分析 趋势"

            
            # 分行并过滤空行
            queries = [q.strip() for q in search_queries_text.split('\n') if q.strip()]

            
            # 过滤掉可能的标题行和非查询文本
            queries = [q for q in queries if not (q.startswith('#') or q.startswith('1. ') or len(q) > 100)]

            
            # 确保查询包含关键词
            if not any(step_title.lower() in q.lower() for q in queries) and queries:

                # 在第一个查询前添加主题关键词
                queries[0] = f"{step_title} {queries[0]}"

            
            # 保证返回至少一个查询
            if not queries:

                # 创建一个符合现代搜索引擎规则的查询
                queries = [f"{step_title} 研究 最新", f"{step_title} 数据 分析"]

                
            logger.info(f"生成了 {len(queries)} 个搜索查询: {queries}")

            return queries[:3]  # 限制为3个查询，使搜索更加精准

            
        except Exception as e:

            logger.error(f"生成搜索查询时出错: {str(e)}")

            # 如果出错，返回基本查询
            return [f"{step_title} 最新研究", f"{step_title} 数据分析"]

            
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
