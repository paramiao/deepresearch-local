import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ChatPage from './pages/ChatPage';
import { ChatProvider } from './utils/chatContext';
import './styles/App.css';

function App() {
  return (
    <ChatProvider>
      <Router>
        <Routes>
          <Route path="/" element={<ChatPage />} />
        </Routes>
      </Router>
    </ChatProvider>
  );
}

export default App;
