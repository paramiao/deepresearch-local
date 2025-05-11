import os
import requests
import json
import time
import re
import html
import os
from bs4 import BeautifulSoup
from serpapi.google_search import GoogleSearch
from datetime import datetime
import nltk
from nltk.tokenize import sent_tokenize
from urllib.parse import urlparse
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 尝试下载NLTK数据
nltk_data_downloaded = False

def ensure_nltk_data():
    """
    确保NLTK数据已下载，设置下载路径为当前目录
    """
    global nltk_data_downloaded
    
    if nltk_data_downloaded:
        return
        
    try:
        # 设置下载目录
        import os
        nltk_data_path = os.path.join(os.getcwd(), 'nltk_data')
        os.makedirs(nltk_data_path, exist_ok=True)
        nltk.data.path.append(nltk_data_path)
        
        # 下载数据
        logger.info(f"正在下载NLTK punkt数据到 {nltk_data_path}")
        nltk.download('punkt', download_dir=nltk_data_path, quiet=False)
        nltk_data_downloaded = True
        logger.info("NLTK数据下载成功")
    except Exception as e:
        logger.warning(f"无法下载NLTK数据: {str(e)}")

# 初始化时尝试下载
try:
    ensure_nltk_data()
except Exception as e:
    logger.warning(f"初始化NLTK数据时出错: {str(e)}")

class SearchService:
    """真实搜索服务，使用SerpAPI和网页爬取来获取真实数据"""
    
    def __init__(self, api_key=None):
        self.serpapi_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.serpapi_key:
            logger.warning("未设置SERPAPI_API_KEY，搜索功能将受限")
            self.serpapi_key = None
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search(self, query, num_results=30):
        """执行搜索并返回结果，处理可能的编码问题"""
        logger.info(f"执行搜索查询: {query}")
        try:
            # 确保查询文本编码正确
            normalized_query = self._normalize_text(query) if hasattr(self, '_normalize_text') else query
            logger.info(f"规范化后的查询: {normalized_query}")
            
            # 执行搜索
            if self.serpapi_key:
                results = self._search_with_serpapi(normalized_query, num_results)
            else:
                # 如果没有SerpAPI密钥，使用备用的搜索方法
                results = self._search_fallback(normalized_query, num_results)
            
            # 对结果进行编码处理
            for result in results:
                if 'title' in result and hasattr(self, '_normalize_text'):
                    result['title'] = self._normalize_text(result['title'])
                if 'snippet' in result and hasattr(self, '_normalize_text'):
                    result['snippet'] = self._normalize_text(result['snippet'])
            
            return results
        except Exception as e:
            logger.error(f"搜索过程中出错: {str(e)}")
            return []
    
    def _search_with_serpapi(self, query, num_results=30):
        """使用SerpAPI执行Google搜索"""
        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.serpapi_key,
                "num": num_results,
                "hl": "zh-cn"  # 设置语言为中文
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "error" in results:
                logger.error(f"SerpAPI错误: {results['error']}")
                return []
            
            organic_results = results.get("organic_results", [])
            
            search_results = []
            for result in organic_results[:num_results]:
                search_results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "source": self._get_domain_name(result.get("link", "")),
                    "source_icon": self._get_favicon(result.get("link", ""))
                })
            
            return search_results
        except Exception as e:
            logger.error(f"SerpAPI搜索错误: {str(e)}")
            return []
    
    def _search_fallback(self, query, num_results=30):
        """备用搜索方法（如果没有SerpAPI密钥）"""
        try:
            # 使用DuckDuckGo API（不需要API密钥）
            url = f"https://api.duckduckgo.com/?q={query}&format=json"
            response = requests.get(url)
            data = response.json()
            
            search_results = []
            for result in data.get("RelatedTopics", [])[:num_results]:
                if "Text" in result and "FirstURL" in result:
                    search_results.append({
                        "title": result["Text"].split(" - ")[0] if " - " in result["Text"] else result["Text"],
                        "link": result["FirstURL"],
                        "snippet": result["Text"],
                        "source": self._get_domain_name(result["FirstURL"]),
                        "source_icon": self._get_favicon(result["FirstURL"])
                    })
            
            return search_results
        except Exception as e:
            logger.error(f"备用搜索错误: {str(e)}")
            return []
    
    def fetch_content(self, url):
        """获取网页内容，并处理编码问题"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br'
            }
            response = self.session.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            
            # 尝试检测内容编码
            if response.encoding.lower() == 'iso-8859-1':
                # 可能是误判，尝试用更可能的编码
                encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
                for enc in encodings:
                    try:
                        text = response.content.decode(enc)
                        response.encoding = enc
                        logger.info(f"成功使用 {enc} 编码解析网页内容")
                        break
                    except UnicodeDecodeError:
                        continue
            
            # 使用正确的编码和HTML解析器
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding=response.encoding)
            
            # 尝试提取主要内容
            main_content = ""
            
            # 尝试查找文章主体
            for tag in ["article", "main", ".content", "#content", ".post", ".article"]:
                content = soup.select(tag)
                if content:
                    main_content = content[0].get_text(separator=' ', strip=True)
                    break
            
            # 如果未找到主要内容，则使用所有段落
            if not main_content:
                paragraphs = soup.find_all('p')
                main_content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # 如果依然没有内容，则使用整个页面文本
            if not main_content:
                main_content = soup.get_text(separator=' ', strip=True)
            
            # 截断过长的内容
            if len(main_content) > 10000:
                main_content = main_content[:10000] + "..."
            
            return main_content
        except Exception as e:
            logger.error(f"获取网页内容失败 {url}: {str(e)}")
            return ""
    
    def extract_key_information(self, text, query):
        """从文本中提取与查询相关的关键信息 - 改进版本"""
        try:
            # 如果文本为空或过短，直接返回none，避免处理空内容
            if not text or len(text) < 50:
                logger.warning(f"提取内容过短或为空: {len(text) if text else 0} 字符")
                return None
            
            # 预清理文本，去除多余空格和几个常见的无用文本模式
            text = re.sub(r'\s+', ' ', text)  # 将多个空白字符替换为单个空格
            text = re.sub(r'(\d+)\s*?[.:]\s*', r'\1. ', text)  # 修复数字列表格式
            text = re.sub(r'\.(\w)', r'. \1', text)  # 修复句点后缺少空格的问题
                
            # 将文本分割成句子 - 使用多种策略
            sentences = []
            
            # 先尝试使用NLTK
            try:
                ensure_nltk_data()  # 确保数据已下载
                sentences = sent_tokenize(text)
            except Exception as e:
                logger.warning(f"NLTK分句失败: {str(e)}")
            
            # 如果NLTK失败，使用基于规则的方法
            if not sentences:
                logger.info("使用自定义分句规则")
                # 第一阶段：先分割段落
                paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', text)
                
                # 第二阶段：对每个段落分割句子
                for paragraph in paragraphs:
                    # 使用多种分割符号分割句子
                    para_sentences = re.split(r'(?<=[.!?])\s+|(?<=[.!?])(?=[A-Z])|\.\s|\!\s|\?\s|\;\s|\n\s*\-|\n\s*\*|\n\s*\d+\.', paragraph)
                    # 清理并添加有效句子
                    for s in para_sentences:
                        s = s.strip()
                        if s and len(s) > 15:  # 只加入足够长度的有效句子
                            sentences.append(s)
            
            # 如果仍然没有成功提取句子，使用最原始的分隔符
            if not sentences and text:
                logger.warning("使用基本分隔符分句")
                sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip() and len(s.strip()) > 15]
            
            # 最后手段：如果还是无法分句，就按固定长度分割
            if not sentences and len(text) > 100:
                logger.warning("按固定长度分割文本")
                chunk_size = 150
                sentences = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            
            # 如果仍然没有句子，返回原始文本的一部分
            if not sentences and text:
                return text[:500] + "..." if len(text) > 500 else text
            elif not sentences:
                logger.warning("无法提取有效的句子")
                return None
            
            # 拆分查询关键词和短语 - 改进版算法
            query_parts = query.lower()
            # 处理多种分隔符
            query_parts = re.sub(r'[-_\s]', ' ', query_parts)
            
            # 优化关键词提取算法
            # 1. 按空格划分
            space_split_keywords = [word for word in query_parts.split() if len(word) > 2]
            
            # 2. 尝试提取短语(连续2-3个词)
            phrases = []
            words = query_parts.split()
            if len(words) >= 2:
                for i in range(len(words)-1):
                    if len(words[i]) > 1 and len(words[i+1]) > 1:  # 确保不是单个字符
                        phrases.append(f"{words[i]} {words[i+1]}")
                        
            # 3. 特殊处理中文查询
            chinese_keywords = []
            if re.search(r'[\u4e00-\u9fa5]', query_parts):
                # 中文文本处理：提取连续2-4个字符
                for i in range(len(query_parts)):
                    if i+2 <= len(query_parts):
                        chunk2 = query_parts[i:i+2]
                        if re.search(r'[\u4e00-\u9fa5]', chunk2) and len(chunk2.strip()) > 1:
                            chinese_keywords.append(chunk2)
                    if i+3 <= len(query_parts):
                        chunk3 = query_parts[i:i+3]
                        if re.search(r'[\u4e00-\u9fa5]', chunk3) and len(chunk3.strip()) > 2:
                            chinese_keywords.append(chunk3)
                    if i+4 <= len(query_parts):
                        chunk4 = query_parts[i:i+4]
                        if re.search(r'[\u4e00-\u9fa5]', chunk4) and len(chunk4.strip()) > 3:
                            chinese_keywords.append(chunk4)
            
            # 组合所有提取的关键词
            query_keywords = space_split_keywords + phrases + chinese_keywords
            
            # 去除重复并过滤常见的无意义词
            stopwords = ['研究', '问题', '什么', '怎么', '为什么', '如何', '分析']
            query_keywords = [k for k in query_keywords if k.strip() and k.strip().lower() not in stopwords]
            query_keywords = list(set(query_keywords))  # 去除重复
            
            # 如果终究没有有效关键词，使用原始查询
            if not query_keywords:
                query_keywords = [query_parts]
            
            # 寻找相关句子并打分 - 全新增强版匹配算法
            relevant_sentences = []
            
            # 记录已处理的句子以避免重复
            processed_sentences = set()
            
            for sentence in sentences:
                # 跳过过短或重复的句子
                if len(sentence) < 20 or sentence in processed_sentences:
                    continue
                    
                processed_sentences.add(sentence)
                sentence_lower = sentence.lower()
                
                # 定义不同类型的匹配得分
                exact_match_score = 0     # 精确匹配得分
                partial_match_score = 0    # 部分匹配得分
                semantic_match_score = 0    # 语义相关得分
                data_value_score = 0       # 数据价值得分
                
                # 1. 精确关键词匹配
                for keyword in query_keywords:
                    # 完全匹配：关键词出现在句子中
                    if keyword in sentence_lower:
                        exact_match_score += 3
                        # 给中文短语更高权重
                        if re.search(r'[\u4e00-\u9fa5]', keyword) and len(keyword) >= 3:
                            exact_match_score += 1
                    # 部分匹配：句子包含关键词的一部分
                    elif len(keyword) > 4 and any(part in sentence_lower for part in keyword.split() if len(part) > 3):
                        partial_match_score += 1
                    # 语义相关匹配：检测句子中是否有相关词汇
                    elif any(related in sentence_lower for related in self._get_related_terms(keyword)):
                        semantic_match_score += 0.5
                
                # 2. 数据质量权重
                # 检测百分比数据
                percentage_matches = re.findall(r'\d+(?:\.\d+)?\s*(?:%|百分之|百分比)', sentence_lower)
                if percentage_matches:
                    data_value_score += len(percentage_matches) * 2
                
                # 检测年份和日期信息
                date_matches = re.findall(r'\d{4}(?:\s*[年-]\s*\d{1,2}\s*[月日]?)', sentence_lower)
                if date_matches:
                    data_value_score += len(date_matches)
                
                # 检测数字列表和表格数据
                if re.search(r'\d+\.\s*\w+|\([1-9]\)|[1-9]\)\s*\w+|\u7b2c[\u4e00-\u4e94六七八九十]|\u8868\s*\d+', sentence_lower):
                    data_value_score += 1
                
                # 重要信息标记
                info_markers = ['\u91cd要', '\u7279别', '\u503c得\u6ce8意', '\u503c得关注', '\u4e3b要', '\u5173键', 'important', 'critical', 'significant']
                if any(marker in sentence_lower for marker in info_markers):
                    data_value_score += 1
                
                # 3. 计算加权总分
                total_score = exact_match_score * 1.5 + partial_match_score + semantic_match_score + data_value_score * 1.2
                
                # 只收集超过阈值的句子
                if total_score > 0.5:  # 降低阈值增加可能的匹配数量
                    relevant_sentences.append((sentence, total_score))
            
            # 按相关性排序
            relevant_sentences.sort(key=lambda x: x[1], reverse=True)
            
            # 如果找到了相关句子，只保留句子内容
            relevant_sentences = [s[0] for s in relevant_sentences]
            
            # 如果没有找到相关句子，使用前几个句子
            if not relevant_sentences and sentences:
                relevant_sentences = sentences[:5]
                logger.info("未找到精确匹配，使用首句摘要")
            
            # 将相关句子组合成段落
            if relevant_sentences:
                # 限制返回的句子数量，避免过多
                if len(relevant_sentences) > 8:
                    relevant_sentences = relevant_sentences[:8]
                    
                key_info = " ".join(relevant_sentences)
                # 限制长度
                if len(key_info) > 1000:
                    key_info = key_info[:1000] + "..."
                return key_info
            else:
                logger.warning("未找到任何相关信息")
                return None
        except Exception as e:
            logger.error(f"提取关键信息失败: {str(e)}")
            return None  # 返回None而不是错误消息
    
    def _get_related_terms(self, keyword):
        """生成与给定关键词语义相关的词汇
        
        Args:
            keyword: 输入关键词
        
        Returns:
            列表: 语义相关词汇
        """
        # 通用关键词映射表
        common_term_map = {
            # 中文常见语义相关映射
            '研究': ['分析', '调查', '考察', '实验', '探索', '测试'],
            '市场': ['销售', '行业', '商业', '销量', '客户', '消费', '商品', '产品'],
            '分析': ['评估', '解析', '比较', '评价', '考量', '研判'],
            '数据': ['统计', '信息', '资料', '表格', '指标', '百分比', '占比'],
            '趋势': ['发展', '走势', '变化', '潮流', '未来', '增长', '上涨', '下降'],
            '竞争': ['对手', '对比', '比较', '竞争者', '竞争格局', '竞争对手'],
            '问题': ['困难', '障碍', '挑战', '瓶颈', '矛盾'],
            '发展': ['增长', '扩大', '提升', '改进', '进步'],
            '成本': ['支出', '费用', '价格', '花费', '投入'],
            '效益': ['回报', '利润', '收益', '效益率', '效益率', '投资回报'],
            # 英文常见语义相关映射
            'market': ['industry', 'business', 'commercial', 'customers', 'consumers', 'sales'],
            'analysis': ['evaluation', 'assessment', 'research', 'study', 'investigation', 'examination'],
            'data': ['statistics', 'figures', 'information', 'metrics', 'indicators', 'percentage'],
            'trend': ['development', 'movement', 'change', 'growth', 'future', 'evolution'],
            'cost': ['expense', 'expenditure', 'payment', 'investment', 'price'],
            'benefit': ['profit', 'return', 'gain', 'advantage', 'roi', 'return on investment']
        }

        # 首先检查关键词是否直接在映射表中
        if keyword.lower() in common_term_map:
            return common_term_map[keyword.lower()]
            
        # 检查关键词是否是召回映射表中某个词的一部分
        related_terms = []
        for base_word, terms in common_term_map.items():
            # 检查关键词是否包含在任何基础词中
            if base_word in keyword or keyword in base_word:
                related_terms.extend(terms)
            # 如果关键词在任何相关词中
            for term in terms:
                if term in keyword or keyword in term:
                    # 添加基础词及其他相关词
                    related_terms.append(base_word)
                    related_terms.extend([t for t in terms if t != term])
        
        # 返回去重后的结果
        return list(set(related_terms))
    
    def _normalize_text(self, text):
        """清理和规范化文本，修复编码问题和特殊字符"""
        if not text:
            return ""
            
        # 替换常见的HTML编码字符
        text = html.unescape(text)
        
        # 替换常见的无效UTF-8序列
        text = re.sub(r'\\u[0-9a-fA-F]{4}', ' ', text)
        text = re.sub(r'\\x[0-9a-fA-F]{2}', ' ', text)
        
        # 删除控制字符
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # 规范化空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze_data(self, findings):
        """分析收集到的研究发现（纯Python实现）"""
        try:
            # 如果没有足够的发现，则无法分析
            if len(findings) < 2:
                return "数据不足，无法进行详细分析"
            
            # 提取可能的数字数据
            numeric_data = []
            for finding in findings:
                # 尝试提取百分比
                if "%" in finding:
                    parts = finding.split("%")
                    for i, part in enumerate(parts[:-1]):  # 不包括最后一部分（%符号后面）
                        words = part.split()
                        if words:
                            try:
                                value = float(words[-1])
                                numeric_data.append({
                                    "value": value,
                                    "type": "percentage",
                                    "context": finding
                                })
                            except:
                                pass
            
            # 如果有数值数据，生成简单的统计分析
            if numeric_data:
                values = [item["value"] for item in numeric_data]
                analysis = f"数据分析：从收集的{len(findings)}条信息中，我们提取了{len(numeric_data)}个数值数据点。"
                
                if len(values) >= 2:
                    avg_value = sum(values) / len(values)
                    max_value = max(values)
                    min_value = min(values)
                    analysis += f" 这些数值的平均值为{avg_value:.2f}%，最大值为{max_value:.2f}%，最小值为{min_value:.2f}%。"
                
                # 添加一些发现的上下文
                if numeric_data:
                    analysis += f" 重要数据点包括：{numeric_data[0]['context']}"
                
                return analysis
            else:
                # 如果没有提取到数字，返回文本分析
                total_text = " ".join(findings)
                common_phrases = self._extract_common_phrases(total_text)
                
                if common_phrases:
                    return f"文本分析：基于收集的{len(findings)}条信息，我们发现最常出现的主题是{', '.join(common_phrases[:3])}。"
                else:
                    return f"文本分析：基于收集的{len(findings)}条信息，未能提取出明确的主题模式。"
        except Exception as e:
            logger.error(f"分析数据失败: {str(e)}")
            return "分析数据时出错"
    
    def _extract_common_phrases(self, text, num_phrases=3):
        """从文本中提取常见短语"""
        try:
            # 简单实现，实际应用中可能需要更复杂的NLP处理
            words = text.lower().split()
            word_counts = {}
            
            for word in words:
                if len(word) > 2:  # 忽略短词
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # 获取最常见的词
            sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
            return [word for word, count in sorted_words[:num_phrases]]
        except Exception as e:
            logger.error(f"提取常见短语失败: {str(e)}")
            return ["未能提取常见短语"]
    
    def _get_domain_name(self, url):
        """从URL中提取域名"""
        try:
            domain = urlparse(url).netloc
            # 移除"www."前缀
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return url
    
    def _get_favicon(self, url):
        """生成网站图标信息"""
        domain = self._get_domain_name(url).lower()
        
        # 根据域名返回合适的图标Emoji
        if 'gov.cn' in domain:
            return '🏛️'
        elif 'edu.cn' in domain or 'edu' in domain:
            return '🎓'
        elif 'org' in domain:
            return '🌐'
        elif 'news' in domain or 'sina' in domain or 'sohu' in domain:
            return '📰'
        elif 'stats' in domain:
            return '📊'
        elif 'byd' in domain or 'tesla' in domain or 'nio' in domain:
            return '🚗'
        elif 'ev' in domain or 'electric' in domain:
            return '⚡'
        elif 'caam' in domain:
            return '🏢'
        else:
            return '🔍'

# 创建全局服务实例
search_service = SearchService()
