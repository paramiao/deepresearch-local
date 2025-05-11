import React, { useState, useEffect } from 'react';
import { FaSearch, FaChartBar, FaFileAlt, FaSatelliteDish, FaExclamationTriangle, FaCheckCircle } from 'react-icons/fa';
import ResearchStepDetail from './ResearchStepDetail';
import '../styles/ResearchProgress.css';
import '../styles/ResearchHistory.css';
import ReactMarkdown from 'react-markdown';

const ResearchProgress = ({ researchData, researchConfirmed, onConfirm, onCancel }) => {
  // 使用状态管理展开的步骤和历史内容 - Hook必须在组件顶层调用
  const [expandedSteps, setExpandedSteps] = useState({});
  const [loading, setLoading] = useState(false);
  const [historyData, setHistoryData] = useState({});
  
  // 使用useEffect跟踪研究数据变化，保留历史内容
  useEffect(() => {
    if (!researchData) return;

    // 保存研究计划阶段的数据
    if (researchData.plan) {
      setHistoryData(prev => ({
        ...prev,
        plan: prev.plan || researchData.plan
      }));
    }

    // 保存研究步骤数据，合并而不是替换
    if (researchData.research_steps && researchData.research_steps.length > 0) {
      setHistoryData(prev => ({
        ...prev,
        research_steps: researchData.research_steps
      }));
    }

    // 保存最终报告数据
    if (researchData.report) {
      setHistoryData(prev => ({
        ...prev,
        report: prev.report || researchData.report
      }));
    }
    
  }, [researchData]);
  
  if (!researchData) {
    return null;
  }
  
  // 用户确认研究计划
  const handleConfirm = async () => {
    if (onConfirm) {
      setLoading(true);
      try {
        await onConfirm();
      } finally {
        setLoading(false);
      }
    }
  };
  
  // 用户取消研究
  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
  };

  const { 
    status, 
    progress, 
    current_step, 
    current_step_index,
    research_steps,
    research_sites, 
    research_findings, 
    analysis_results, 
    error 
  } = researchData;

  // 切换步骤的展开/折叠状态
  const toggleStep = (index) => {
    setExpandedSteps(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // 根据状态选择图标
  const getStatusIcon = () => {
    switch (status) {
      case 'researching':
        return <FaSearch className="status-icon researching" />;
      case 'analyzing':
        return <FaChartBar className="status-icon analyzing" />;
      case 'reporting':
        return <FaFileAlt className="status-icon reporting" />;
      case 'completed':
        return <FaFileAlt className="status-icon completed" />;
      case 'error':
        return <FaExclamationTriangle className="status-icon error" />;
      default:
        return <FaSatelliteDish className="status-icon" />;
    }
  };

  // 获取状态文本
  const getStatusText = () => {
    switch (status) {
      case 'planning':
        return '正在规划研究方案...';
      case 'waiting_confirmation':
        return '等待确认研究计划';
      case 'researching':
        return '正在收集研究数据...';
      case 'analyzing':
        return '正在分析研究数据...';
      case 'reporting':
        return '正在生成研究报告...';
      case 'completed':
        return '研究已完成';
      case 'error':
        return '研究过程出错';
      case 'cancelled':
        return '研究已取消';
      default:
        return '正在处理...';
    }
  };

  return (
    <div className="research-progress">
      <div className="research-progress-header">
        <div className="status-indicator">
          {getStatusIcon()}
          <span className="status-text">{getStatusText()}</span>
        </div>
        <div className="progress-bar-container">
          <div 
            className="progress-bar" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <div className="progress-percentage">{progress}%</div>
      </div>
      
      {/* 如果是等待确认状态且有按钮处理函数，显示确认/取消按钮 */}
      {status === 'waiting_confirmation' && onConfirm && !researchConfirmed && (
        <div className="research-plan-actions">
          <p className="confirmation-message">
            请确认以上研究计划，我们将按照这些步骤进行深入研究。
          </p>
          <div className="action-buttons">
            <button 
              className="confirm-button"
              onClick={handleConfirm}
              disabled={loading}
            >
              {loading ? '正在处理...' : '确认并开始研究'}
            </button>
            
            <button 
              className="cancel-button"
              onClick={handleCancel}
              disabled={loading}
            >
              取消研究
            </button>
          </div>
        </div>
      )}

      <div className="research-progress-content">
        {/* 显示研究计划历史内容 */}
        {historyData.plan && status !== 'waiting_confirmation' && (
          <div className="research-history-section">
            <h3>研究计划</h3>
            <div className="history-content plan-history">
              <ReactMarkdown>{historyData.plan}</ReactMarkdown>
            </div>
          </div>
        )}
        
        {current_step && (
          <div className="current-step">
            <h4>当前步骤</h4>
            <p>{current_step}</p>
          </div>
        )}

        {/* 研究步骤列表 - 使用升级的组件显示，即使在研究完成后也保持显示 */}
        {research_steps && research_steps.length > 0 && (
          <div className="research-steps">
            <h3>研究步骤</h3>
            <div className="steps-container">
              {/* 步骤列表导航 */}
              <div className="steps-navigation">
                {research_steps.map((step, idx) => (
                  <div 
                    key={idx} 
                    className={`step-nav-item ${current_step_index === idx ? 'active' : ''} ${step.completed ? 'completed' : ''}`}
                    onClick={() => toggleStep(idx)}
                  >
                    <div className="step-nav-number">{idx + 1}</div>
                    <div className="step-nav-title">{step.title}</div>
                    {step.completed && <FaCheckCircle className="step-nav-completed" />}
                  </div>
                ))}
              </div>

              {/* 当前步骤详情 */}
              <div className="step-details-container">
                {research_steps.map((step, idx) => (
                  <div key={idx} className={`step-detail-wrapper ${expandedSteps[idx] ? 'expanded' : 'collapsed'}`}>
                    {expandedSteps[idx] && (
                      <ResearchStepDetail 
                        step={step} 
                        index={idx} 
                        isActive={current_step_index === idx}
                        isCompleted={step.completed}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 保留原有的整体研究数据展示，以便兼容旧版实现 */}
        {research_sites && research_sites.length > 0 && !research_steps && (
          <div className="research-sites">
            <h4>研究网站</h4>
            <div className="site-list">
              {research_sites.map((site, index) => (
                <div key={index} className="site-item">
                  <span className="site-icon">{site.icon}</span>
                  <span className="site-name">{site.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 确保研究发现在有研究步骤的情况下仍然显示 */}
        {research_findings && research_findings.length > 0 && (
          <div className="research-findings">
            <h4>主要研究发现</h4>
            <ul>
              {research_findings.map((finding, index) => (
                <li key={index}>{finding}</li>
              ))}
            </ul>
          </div>
        )}

        {/* 确保分析结果在有研究步骤的情况下仍然显示 */}
        {analysis_results && analysis_results.length > 0 && (
          <div className="analysis-results">
            <h4>分析结果</h4>
            <ul>
              {analysis_results.map((result, index) => (
                <li key={index}>{result}</li>
              ))}
            </ul>
          </div>
        )}

        {/* 显示最终研究报告历史内容 */}
        {historyData.report && status === 'completed' && (
          <div className="research-history-section report-section">
            <h3>研究报告</h3>
            <div className="history-content report-history">
              <ReactMarkdown>{historyData.report}</ReactMarkdown>
            </div>
          </div>
        )}

        {error && (
          <div className="research-error">
            <h4>错误信息</h4>
            <p className="error-message">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResearchProgress;
