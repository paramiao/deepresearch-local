import React, { useState } from 'react';
import { FaSearch, FaLink, FaFileAlt, FaChartBar, FaCheckCircle, FaInfoCircle, FaAngleDown, FaAngleUp } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import '../styles/ResearchStepDetail.css';
import '../styles/OriginalPlanContent.css';

/**
 * 研究步骤详情组件 - 显示单个研究步骤的详细信息，包括搜索结果、发现和分析
 */
const ResearchStepDetail = ({ step, index, isActive, isCompleted }) => {
  const [showOriginalContent, setShowOriginalContent] = useState(false);
  
  if (!step) return null;

  const hasOriginalContent = step.original_content && step.original_content !== step.description;

  return (
    <div className={`research-step-detail ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
      <div className="step-header">
        <div className="step-number-container">
          <div className="step-number">{index + 1}</div>
          {isCompleted && <FaCheckCircle className="step-completed-icon" />}
        </div>
        <div className="step-title-container">
          <h3 className="step-title">{step.title}</h3>
          <p className="step-description">{step.description}</p>
          
          {/* 查看原始研究计划内容的切换按钮 */}
          {hasOriginalContent && (
            <button 
              className="original-content-toggle" 
              onClick={() => setShowOriginalContent(!showOriginalContent)}
            >
              {showOriginalContent ? (
                <>
                  <FaAngleUp /> 隐藏研究计划详情
                </>
              ) : (
                <>
                  <FaAngleDown /> 查看研究计划详情
                </>
              )}
            </button>
          )}
        </div>
      </div>
      
      {/* 展示研究计划原始内容 */}
      {showOriginalContent && hasOriginalContent && (
        <div className="original-plan-content">
          <div className="original-content-header">
            <FaInfoCircle /> <span>研究计划中的原始内容：</span>
          </div>
          <div className="original-content-body">
            <ReactMarkdown>{step.original_content}</ReactMarkdown>
          </div>
        </div>
      )}
      
      <div className="step-content">
        {/* 搜索结果区域 */}
        {step.search_results && step.search_results.length > 0 && (
          <div className="step-section search-results-section">
            <h4 className="section-title">
              <FaSearch />
              <span>搜索结果</span>
              <span className="result-count">({step.search_results.length})</span>
            </h4>
            <div className="search-results-list">
              {step.search_results.map((result, idx) => (
                <div key={idx} className="search-result-item">
                  <div className="result-title">{result.title}</div>
                  <div className="result-source">{result.name}</div>
                  {result.snippet && (
                    <div className="result-snippet">{result.snippet}</div>
                  )}
                  <a 
                    href={result.url} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="result-link"
                  >
                    <FaLink /> 查看来源
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* 研究发现区域 */}
        {step.findings && step.findings.length > 0 && (
          <div className="step-section findings-section">
            <h4 className="section-title">
              <FaFileAlt />
              <span>研究发现</span>
              <span className="result-count">({step.findings.length})</span>
            </h4>
            <ul className="findings-list">
              {step.findings.map((finding, idx) => (
                <li key={idx} className="finding-item">{finding}</li>
              ))}
            </ul>
          </div>
        )}
        
        {/* 分析结果区域 */}
        {step.analysis && (
          <div className="step-section analysis-section">
            <h4 className="section-title">
              <FaChartBar />
              <span>分析结论</span>
            </h4>
            <div className="analysis-content">
              {step.analysis}
            </div>
          </div>
        )}
        
        {/* 如果步骤尚未完成，显示进行中状态 */}
        {!isCompleted && (
          <div className="step-in-progress">
            <div className="loading-spinner"></div>
            <p>{isActive ? '正在处理这个步骤...' : '等待处理...'}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResearchStepDetail;
