import React, { useRef, useEffect, useState } from 'react';
import ChatInput from '../components/ChatInput';
import MessageList from '../components/MessageList';
import ResearchPlan from '../components/ResearchPlan';
import ResearchProgress from '../components/ResearchProgress';
import { fetchChatResponse } from '../services/api';
import { startResearch, getResearchStatus, confirmResearchPlan } from '../services/api';
import { useChat } from '../utils/chatContext';
import '../styles/ChatPage.css';

const ChatPage = () => {
  const { messages, loading, error, sendUserMessage, sendAssistantMessage, setLoading, setError } = useChat();
  const messagesEndRef = useRef(null);
  
  // 研究过程状态
  const [researchMode, setResearchMode] = useState(false);
  const [researchProcessId, setResearchProcessId] = useState(null);
  const [researchPlan, setResearchPlan] = useState(null);
  const [researchData, setResearchData] = useState(null);
  const [researchConfirmed, setResearchConfirmed] = useState(false);
  
  // 轮询间隔（毫秒）
  const pollingInterval = 2000;
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // 监听研究过程状态
  useEffect(() => {
    let intervalId;
    
    const pollResearchStatus = async () => {
      if (!researchProcessId) return;
      
      try {
        const data = await getResearchStatus(researchProcessId);
        console.log('研究状态更新:', data.status, '进度:', data.progress, '当前步骤:', data.current_step);
        setResearchData(data);
        
        // 如果状态是等待确认，则保存研究计划
        if (data.status === 'waiting_confirmation') {
          console.log('发现等待确认状态，研究计划:', data.plan ? '存在' : '不存在');
          if (!researchPlan && data.plan) {
            console.log('设置研究计划并等待用户确认');
            setResearchPlan(data.plan);
          }
        }
        
        // 如果研究完成、出错或取消，则停止轮询
        if (['completed', 'error', 'cancelled'].includes(data.status)) {
          clearInterval(intervalId);
          
          // 如果研究完成，并且有报告，则发送报告到聊天
          if (data.status === 'completed' && data.report) {
            sendAssistantMessage(data.report);
            setResearchMode(false);
            setResearchProcessId(null);
            setResearchPlan(null);
            setResearchData(null);
            setResearchConfirmed(false);
          }
        }
      } catch (error) {
        console.error('获取研究状态失败:', error);
        clearInterval(intervalId);
      }
    };
    
    if (researchProcessId) {
      // 首次立即获取状态
      pollResearchStatus();
      
      // 然后定期轮询
      intervalId = setInterval(pollResearchStatus, pollingInterval);
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [researchProcessId, researchPlan, sendAssistantMessage]);

  // 处理确认研究计划
  const handleConfirmResearch = async () => {
    if (!researchProcessId) {
      console.error('无法确认研究：缺少researchProcessId');
      return;
    }
    
    console.log('开始确认研究计划', { researchProcessId, researchPlan });
    setLoading(true);
    try {
      const response = await confirmResearchPlan(researchProcessId);
      console.log('研究计划确认成功', response);
      setResearchConfirmed(true);
      
      // 发送一条消息表示已确认研究计划
      sendAssistantMessage('研究计划已确认，正在执行研究...');
      
      // 立即获取最新研究状态，确保前端状态与后端同步
      try {
        const updatedStatus = await getResearchStatus(researchProcessId);
        setResearchData(updatedStatus);
      } catch (statusError) {
        console.error('获取最新研究状态失败:', statusError);
      }
    } catch (error) {
      console.error('确认研究计划失败:', error);
      setError('确认研究计划失败: ' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };
  
  // 处理取消研究
  const handleCancelResearch = () => {
    setResearchMode(false);
    setResearchProcessId(null);
    setResearchPlan(null);
    setResearchData(null);
    setResearchConfirmed(false);
    sendAssistantMessage('研究已取消。您可以开始新的对话。');
  };
  
  // 检查是否是研究请求
  const isResearchRequest = (text) => {
    const lowerText = text.toLowerCase();
    console.log('检查是否是研究请求:', lowerText);
    return (
      (lowerText.includes('研究') || 
       lowerText.includes('分析') || 
       lowerText.includes('调查') ||
       lowerText.includes('调研') ||
       lowerText.includes('报告')) &&
      text.length > 10
    );
  };

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;

    // 添加用户消息
    sendUserMessage(text);
    setLoading(true);

    try {
      // 检查是否为研究请求
      if (isResearchRequest(text) && !researchMode) {
        // 启动研究流程
        sendAssistantMessage('正在规划研究方案，这可能需要几分钟时间...');
        
        // 将topic提取为研究目标
        let topic = text;
        let requirements = '详细全面';
        
        // 如果有逗号分隔，则拆分为主题和要求
        if (text.includes('，') || text.includes(',')) {
          const parts = text.split(/[，,]/);
          topic = parts[0].trim();
          requirements = parts.slice(1).join(', ').trim() || '详细全面';
        }
        
        console.log('开始研究:', { topic, requirements });
        const response = await startResearch(topic, requirements);
        setResearchMode(true);
        setResearchProcessId(response.process_id);
        
        // 立即开始轮询状态，不等待useEffect中的轮询
        try {
          const initialStatus = await getResearchStatus(response.process_id);
          setResearchData(initialStatus);
          
          // 如果已经有研究计划，直接显示
          if (initialStatus.plan) {
            setResearchPlan(initialStatus.plan);
            sendAssistantMessage(`我已经编写好了研究计划，请查看并确认开始执行。`);
          }
        } catch (statusError) {
          console.error('获取初始研究状态失败:', statusError);
        }
      } else if (researchMode && !researchConfirmed && researchPlan) {
        // 如果已经在研究模式但用户继续发消息，提醒用户需要先确认计划
        sendAssistantMessage('请先确认当前的研究计划，点击“确认并开始研究”按钮以继续进行研究。');
      } else if (researchMode && researchConfirmed && researchData && researchData.status !== 'completed') {
        // 如果已经在执行研究且未完成，提供当前进度
        const currentStep = researchData.current_step || '正在处理';
        const progress = researchData.progress || 0;
        sendAssistantMessage(`研究正在进行中 (进度: ${progress}%)\n当前步骤: ${currentStep}\n请稍候，您可以在每个研究步骤中查看详细的结果和分析。`);
      } else {
        // 普通对话流程
        // 准备对话历史
        const conversationHistory = messages
          .filter(msg => msg.role !== 'system')
          .map(msg => msg.content);

        // 发送请求
        const response = await fetchChatResponse(text, conversationHistory);
        
        // 添加助手消息
        const content = response.answer || response.plan || response.report || '抱歉，我无法处理您的请求。';
        sendAssistantMessage(content);
      }
    } catch (error) {
      console.error('处理消息失败:', error);
      
      // 设置错误消息
      const errorContent = `抱歉，发生了错误: ${error.message || '未知错误'}`;
      sendAssistantMessage(errorContent);
      setError(error.message || '请求失败');
      
      // 如果是研究模式，重置研究状态
      if (researchMode) {
        setResearchMode(false);
        setResearchProcessId(null);
        setResearchPlan(null);
        setResearchData(null);
        setResearchConfirmed(false);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>DeepResearch 研究助手</h1>
        <p>由 Gemini AI 提供支持</p>
      </div>
      
      <div className="chat-messages">
        <MessageList messages={messages} />
        
        {/* 研究计划确认组件 */}
        {researchMode && researchPlan && !researchConfirmed && (
          <ResearchPlan 
            plan={researchPlan} 
            onConfirm={handleConfirmResearch} 
            onCancel={handleCancelResearch}
            loading={loading}
          />
        )}
        
        {/* 研究进度组件 - 展示详细研究步骤 */}
        {researchMode && researchData && (
          <ResearchProgress 
            researchData={researchData} 
            researchConfirmed={researchConfirmed}
            onConfirm={researchConfirmed ? null : handleConfirmResearch}
            onCancel={handleCancelResearch}
          />
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-container">
        <ChatInput 
          onSendMessage={handleSendMessage} 
          disabled={loading || (researchMode && researchConfirmed && researchData?.status !== 'completed')}
          placeholder={researchMode && researchConfirmed ? "研究进行中，请等待完成..." : "输入您的研究需求或问题..."}
        />
        {loading && <div className="loading-indicator">AI思考中...</div>}
        {error && <div className="error-message">{error}</div>}
      </div>
    </div>
  );
};

export default ChatPage;
