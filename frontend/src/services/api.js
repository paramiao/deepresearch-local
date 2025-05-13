import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api';
console.log('使用API基础URL:', API_BASE_URL); // 添加日志帮助调试

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchChatResponse = async (question, conversationHistory = []) => {
  // 分析问题类型
  const lowerQuestion = question.toLowerCase();
  
  // 判断请求类型
  if (lowerQuestion.includes('研究计划') || lowerQuestion.includes('规划研究')) {
    const parts = question.split(/[,，]/);
    const topic = parts[0] || question;
    const requirements = parts.slice(1).join(', ') || '详细全面';
    
    const { data } = await apiClient.post('/chat/research_plan', {
      topic,
      requirements
    });
    return data;
  } 
  else if (lowerQuestion.includes('研究报告') || lowerQuestion.includes('生成报告')) {
    // 从聊天历史中提取研究计划和发现
    let research_plan = '';
    let findings = question;
    
    for (let i = conversationHistory.length - 1; i >= 0; i--) {
      if (i % 2 === 0 && conversationHistory[i-1] && 
          (conversationHistory[i-1].includes('研究计划') || 
           conversationHistory[i-1].includes('研究方法'))) {
        research_plan = conversationHistory[i];
        break;
      }
    }
    
    const { data } = await apiClient.post('/chat/research_report', {
      research_plan,
      findings
    });
    return data;
  }
  else {
    // 普通问题
    const { data } = await apiClient.post('/chat/question', {
      question,
      conversation_history: conversationHistory
    });
    return data;
  }
};

// 检查API连接状态
export const checkAPIStatus = async () => {
  try {
    await apiClient.get('/status');
    return true;
  } catch (error) {
    console.error('API服务不可用:', error);
    return false;
  }
};

// 研究相关API调用

// 启动新的研究流程
export const startResearch = async (topic, requirements = '详细全面') => {
  try {
    console.log('发送研究请求:', {
      url: `${apiClient.defaults.baseURL}/research/start`,
      topic,
      requirements
    });
    
    const { data } = await apiClient.post('/research/start', {
      topic,
      requirements
    });
    console.log('研究启动成功:', data);
    return data;
  } catch (error) {
    console.error('启动研究时出错:', error.response ? error.response.data : error.message);
    throw error;
  }
};

// 获取研究进度
export const getResearchStatus = async (processId) => {
  try {
    const { data } = await apiClient.get(`/research/status/${processId}`);
    console.log('获取研究状态:', data);
    return data;
  } catch (error) {
    console.error('获取研究状态失败:', error);
    throw error;
  }
};

// 确认研究计划并开始执行
export const confirmResearchPlan = async (processId) => {
  try {
    const { data } = await apiClient.post(`/research/confirm/${processId}`);
    console.log('研究计划确认成功:', data);
    return data;
  } catch (error) {
    console.error('确认研究计划失败:', error);
    throw error;
  }
};

// 取消研究
export const cancelResearch = async (processId) => {
  try {
    const { data } = await apiClient.post(`/research/cancel/${processId}`);
    console.log('研究已取消:', data);
    return data;
  } catch (error) {
    console.error('取消研究失败:', error);
    throw error;
  }
};
