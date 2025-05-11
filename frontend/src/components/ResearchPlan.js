import React, { useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { FaClipboardCheck, FaTimes, FaSearch, FaQuestionCircle } from 'react-icons/fa';
import '../styles/ResearchPlan.css';

const ResearchPlan = ({ plan, onConfirm, onCancel, loading }) => {
  useEffect(() => {
    console.log('ResearchPlan组件被渲染', { plan, loading });
  }, [plan, loading]);
  
  if (!plan) {
    console.log('ResearchPlan组件没有计划数据，返回null');
    return null;
  }

  // 提取研究问题列表
  const extractResearchQuestions = (markdownText) => {
    try {
      // 寻找核心研究问题部分
      const coreQuestionsMatch = markdownText.match(/## 核心研究问题[\s\S]*?(?=##|$)/i);
      if (!coreQuestionsMatch) return [];
      
      const coreQuestionsText = coreQuestionsMatch[0];
      
      // 提取所有问题（使用数字列表匹配）
      const questions = [];
      const questionRegex = /\d+\.\s*([^\n]+)/g;
      let match;
      
      while ((match = questionRegex.exec(coreQuestionsText)) !== null) {
        if (match[1] && match[1].trim()) {
          questions.push(match[1].trim());
        }
      }
      
      return questions;
    } catch (error) {
      console.error('提取研究问题时出错:', error);
      return [];
    }
  };

  const researchQuestions = extractResearchQuestions(plan);

  return (
    <div className="research-plan">
      <div className="research-plan-header">
        <h3>研究计划</h3>
        <p className="research-plan-subtitle">以下是核心研究问题，我们将针对每个问题进行专门检索和分析</p>
      </div>
      
      <div className="research-plan-content">
        {/* 研究目标摘要部分 */}
        <div className="plan-summary">
          <ReactMarkdown>
            {plan.match(/## 研究目标[\s\S]*?(?=##|$)/i)?.[0] || ''}  
          </ReactMarkdown>
        </div>
        
        {/* 突出显示核心研究问题 */}
        <div className="core-questions-section">
          <h3><FaQuestionCircle /> 核心研究问题</h3>
          
          {researchQuestions.length > 0 ? (
            <ul className="research-questions-list">
              {researchQuestions.map((question, index) => (
                <li key={index} className="research-question-item">
                  <div className="question-number">{index + 1}</div>
                  <div className="question-content">
                    <strong>{question}</strong>
                    <div className="question-search-icon">
                      <FaSearch title="将针对此问题进行专门检索" />
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <ReactMarkdown>{plan.match(/## 核心研究问题[\s\S]*?(?=##|$)/i)?.[0] || ''}</ReactMarkdown>
          )}
        </div>
      </div>
      
      <div className="research-plan-actions">
        <button 
          className="confirm-button"
          onClick={onConfirm}
          disabled={loading}
        >
          <FaClipboardCheck /> 确认并开始研究
        </button>
        
        <button 
          className="cancel-button"
          onClick={onCancel}
          disabled={loading}
        >
          <FaTimes /> 取消
        </button>
      </div>
    </div>
  );
};

export default ResearchPlan;
