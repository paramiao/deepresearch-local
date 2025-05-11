import os
import requests
import json
import time
import re
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
        """执行搜索并返回结果"""
        if self.serpapi_key:
            return self._search_with_serpapi(query, num_results)
        else:
            # 如果没有SerpAPI密钥，使用备用的搜索方法
            return self._search_fallback(query, num_results)
    
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
        """获取网页内容"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
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
        """从文本中提取与查询相关的关键信息"""
        try:
            # 如果文本为空或过短，直接返回none，避免处理空内容
            if not text or len(text) < 50:
                logger.warning(f"提取内容过短或为空: {len(text) if text else 0} 字符")
                return None
                
            # 将文本分割成句子
            try:
                sentences = sent_tokenize(text)
            except Exception as e:
                logger.warning(f"NLTK分句失败，使用基本分割: {str(e)}")
                # 如果NLTK分句失败，使用基本的分隔符
                sentences = [s.strip() for s in re.split(r'[.!?\n]', text) if s.strip()]
            
            # 如果仍然没有句子，返回none
            if not sentences:
                logger.warning("无法提取有效的句子")
                return None
            
            # 为查询创建关键词列表，添加分词处理
            query_parts = query.lower().replace('-', ' ').replace('_', ' ')
            query_keywords = [word for word in query_parts.split() if len(word) > 1]
            
            # 寻找包含查询关键词的句子，添加相关性评分
            relevant_sentences = []
            for sentence in sentences:
                sentence_lower = sentence.lower()
                # 计算相关性分数
                relevance = sum(1 for keyword in query_keywords if keyword in sentence_lower)
                if relevance > 0:
                    relevant_sentences.append((sentence, relevance))
            
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
