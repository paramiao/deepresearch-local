import React, { createContext, useContext, useReducer, useEffect } from 'react';

// 创建聊天上下文
const ChatContext = createContext();

// 初始状态
const initialState = {
  messages: [],
  loading: false,
  error: null,
};

// 聊天状态管理器
function chatReducer(state, action) {
  switch (action.type) {
    case 'INITIALIZE':
      return {
        ...state,
        messages: [
          {
            id: Date.now(),
            role: 'system',
            content: '欢迎使用 DeepResearch 研究助手。请告诉我您想研究的主题，我将帮助您规划研究方案并生成研究报告。'
          }
        ]
      };
    case 'ADD_USER_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, {
          id: action.payload.id,
          role: 'user',
          content: action.payload.content
        }]
      };
    case 'ADD_ASSISTANT_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, {
          id: action.payload.id,
          role: 'assistant',
          content: action.payload.content
        }]
      };
    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null
      };
    default:
      throw new Error(`未处理的action类型: ${action.type}`);
  }
}

// 提供聊天上下文的组件
export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  // 初始化欢迎消息
  useEffect(() => {
    dispatch({ type: 'INITIALIZE' });
  }, []);

  // 保存聊天记录到本地存储
  useEffect(() => {
    if (state.messages.length > 1) { // 忽略仅有系统消息的情况
      localStorage.setItem('chat-history', JSON.stringify(state.messages));
    }
  }, [state.messages]);

  // 处理用户消息
  const sendUserMessage = (content) => {
    const id = Date.now();
    dispatch({ 
      type: 'ADD_USER_MESSAGE', 
      payload: { id, content } 
    });
    return id;
  };

  // 处理助手消息
  const sendAssistantMessage = (content) => {
    const id = Date.now() + 1;
    dispatch({ 
      type: 'ADD_ASSISTANT_MESSAGE', 
      payload: { id, content } 
    });
    return id;
  };

  // 设置加载状态
  const setLoading = (isLoading) => {
    dispatch({ type: 'SET_LOADING', payload: isLoading });
  };

  // 设置错误
  const setError = (error) => {
    dispatch({ type: 'SET_ERROR', payload: error });
    // 3秒后自动清除错误
    setTimeout(() => {
      dispatch({ type: 'CLEAR_ERROR' });
    }, 3000);
  };

  // 准备上下文值
  const contextValue = {
    messages: state.messages,
    loading: state.loading,
    error: state.error,
    sendUserMessage,
    sendAssistantMessage,
    setLoading,
    setError
  };

  return (
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
}

// 使用聊天上下文的钩子
export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat必须在ChatProvider内部使用');
  }
  return context;
}
