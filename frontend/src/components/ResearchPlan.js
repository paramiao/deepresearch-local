import React, { useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { FaClipboardCheck, FaTimes } from 'react-icons/fa';
import '../styles/ResearchPlan.css';

const ResearchPlan = ({ plan, onConfirm, onCancel, loading }) => {
  useEffect(() => {
    console.log('ResearchPlan组件被渲染', { plan, loading });
  }, [plan, loading]);
  
  if (!plan) {
    console.log('ResearchPlan组件没有计划数据，返回null');
    return null;
  }

  return (
    <div className="research-plan">
      <div className="research-plan-header">
        <h3>研究计划</h3>
        <p className="research-plan-subtitle">这是我们计划的研究方案，请在确认后我们将开始执行。</p>
      </div>
      
      <div className="research-plan-content">
        <ReactMarkdown>{plan}</ReactMarkdown>
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
