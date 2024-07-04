import axios from 'axios';
import React, { useEffect, useRef, useState } from 'react';

const BASE_URL = 'http://localhost:5005/webhooks/rest'; // Adjust to your Rasa server address

const myAxios = axios.create({
    baseURL: BASE_URL,
});

const App: React.FC = () => {
    const [inputMessage, setInputMessage] = useState('');
    const [chatHistory, setChatHistory] = useState<{ sender: string, message: string }[]>([]);
    const chatEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        scrollToBottom();
    }, [chatHistory]);

    const scrollToBottom = () => {
        if (chatEndRef.current) {
            chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    };

    const sendMessage = async () => {
        if (!inputMessage.trim()) return; // Prevent sending empty messages

        // Add user message to chat history
        setChatHistory([...chatHistory, { sender: 'user', message: inputMessage }]);
        setInputMessage(''); // Clear input field

        // Send message to Rasa server
        try {
            const response = await postMessage(inputMessage);
            const botResponse = response.length > 0 ? response[0].text : 'No response from bot';
            // Add bot message to chat history
            setChatHistory([...chatHistory, { sender: 'bot', message: botResponse }]);
        } catch (error) {
            console.error('Error sending message:', error);
        }
    };

    const postMessage = async (message: string) => {
        const payload = {
            sender: 'user',
            message: message,
        };

        try {
            const response = await myAxios.post('/webhook', payload);
            return response.data;
        } catch (error) {
            console.error('Error posting message:', error);
            throw error;
        }
    };

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setInputMessage(event.target.value);
    };

    return (
      <div className="flex flex-col h-screen">
      <header className="bg-blue-500 text-white p-4">
          <h1 className="text-xl font-bold">RoboBanker</h1>
      </header>
      <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 bg-gray-100 p-4 overflow-y-auto">
              <div className="flex flex-col gap-2">
                  {chatHistory.map((message, index) => (
                      <div key={index} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`bg-gray-300 p-2 rounded-lg max-w-xs break-words ${message.sender === 'user' ? 'self-end' : 'self-start'}`}>
                              <p className="text-sm">{message.message}</p>
                          </div>
                      </div>
                  ))}
                  <div ref={chatEndRef}></div>
              </div>
          </div>
          <div className="w-1/4 p-4 bg-white">
              <div className="flex items-center mb-4">
                  <input type="text" value={inputMessage} onChange={handleInputChange} className="flex-1 p-2 border border-gray-300 rounded-l-lg" />
                  <button onClick={sendMessage} className="bg-blue-500 text-white p-2 rounded-r-lg">Send</button>
              </div>
          </div>
      </div>
  </div>
    );
};

export default App;