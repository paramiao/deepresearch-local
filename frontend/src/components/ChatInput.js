import React, { useState } from 'react';
import { FaPaperPlane } from 'react-icons/fa';
import '../styles/ChatInput.css';

const ChatInput = ({ onSendMessage, disabled, placeholder }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || "输入您的研究需求或问题..."}
        disabled={disabled}
        rows={1}
        className="chat-textarea"
      />
      <button type="submit" disabled={!message.trim() || disabled} className="send-button">
        <FaPaperPlane />
      </button>
    </form>
  );
};

export default ChatInput;
