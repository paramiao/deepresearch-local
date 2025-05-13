import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api';
console.log('研究服务使用API基础URL:', API_BASE_URL); // 添加调试日志

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 开始一个新的研究过程
export const startResearch = async (topic, requirements = '') => {
  try {
    const { data } = await apiClient.post('/research/start', {
      topic,
      requirements
    });
    return data;
  } catch (error) {
    console.error('启动研究过程失败:', error);
    throw error;
  }
};

// 获取研究过程状态
export const getResearchStatus = async (processId) => {
  try {
    const { data } = await apiClient.get(`/research/status/${processId}`);
    return data;
  } catch (error) {
    console.error('获取研究状态失败:', error);
    throw error;
  }
};

// 确认研究计划，开始执行研究
export const confirmResearchPlan = async (processId) => {
  try {
    const { data } = await apiClient.post(`/research/confirm/${processId}`);
    return data;
  } catch (error) {
    console.error('确认研究计划失败:', error);
    throw error;
  }
};

// 取消研究过程
export const cancelResearch = async (processId) => {
  try {
    const { data } = await apiClient.post(`/research/cancel/${processId}`);
    return data;
  } catch (error) {
    console.error('取消研究失败:', error);
    throw error;
  }
};
