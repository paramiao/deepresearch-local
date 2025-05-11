import React from 'react';
import ReactMarkdown from 'react-markdown';
import { FaFileAlt, FaDownload, FaFileAlt as FaFileText } from 'react-icons/fa';
import '../styles/ResearchReport.css';

const ResearchReport = ({ report, title = "研究报告" }) => {
  // 导出报告为文本文件
  const exportAsText = () => {
    const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // 导出报告为Markdown文件
  const exportAsMarkdown = () => {
    const blob = new Blob([report], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  if (!report) {
    return (
      <div className="research-report-empty">
        <FaFileAlt className="report-icon" />
        <p>研究报告尚未生成</p>
      </div>
    );
  }

  return (
    <div className="research-report-container">
      <div className="research-report-header">
        <div className="report-title-section">
          <FaFileAlt className="report-icon" />
          <h2>{title}</h2>
        </div>
        <div className="report-actions">
          <div className="report-export-dropdown">
            <button className="report-action-button" title="导出报告">
              <FaDownload /> 导出
            </button>
            <div className="export-options">
              <button onClick={exportAsText} className="export-option">
                <FaFileText /> 纯文本 (.txt)
              </button>
              <button onClick={exportAsMarkdown} className="export-option">
                <FaFileAlt /> Markdown (.md)
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="research-report-content">
        <div className="report-body">
          <ReactMarkdown>{report}</ReactMarkdown>
        </div>
      </div>

      <div className="research-report-footer">
        <p className="report-timestamp">生成时间: {new Date().toLocaleString()}</p>
      </div>
    </div>
  );
};

export default ResearchReport;
