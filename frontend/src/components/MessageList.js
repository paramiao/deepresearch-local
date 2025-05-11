import React from 'react';
import ReactMarkdown from 'react-markdown';
import { FaUser, FaRobot } from 'react-icons/fa';
import '../styles/MessageList.css';

const MessageList = ({ messages }) => {
  return (
    <div className="message-list">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
        >
          <div className="message-avatar">
            {message.role === 'user' ? (
              <FaUser className="user-avatar" />
            ) : (
              <FaRobot className="assistant-avatar" />
            )}
          </div>
          <div className="message-content">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MessageList;
