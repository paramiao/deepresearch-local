import React from 'react';
import { FaSearch, FaLink, FaFileAlt, FaChartBar, FaCheckCircle } from 'react-icons/fa';
import '../styles/ResearchStepDetail.css';

/**
 * 研究步骤详情组件 - 显示单个研究步骤的详细信息，包括搜索结果、发现和分析
 */
const ResearchStepDetail = ({ step, index, isActive, isCompleted }) => {
  if (!step) return null;

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
        </div>
      </div>
      
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
