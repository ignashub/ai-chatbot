"use client";

import { useState, useRef } from 'react';
import axios from 'axios';
import { InputText } from 'primereact/inputtext';
import { Button } from 'primereact/button';
import { Slider } from 'primereact/slider';
import { Card } from 'primereact/card';
import { Tooltip } from 'primereact/tooltip';
import { Toast } from 'primereact/toast';
import { ProgressSpinner } from 'primereact/progressspinner';
import { log } from 'console';

const ChatInterface = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<{ user: string; bot: string }[]>([]);
  const [temperature, setTemperature] = useState(0.7);
  const [topP, setTopP] = useState(1.0);
  const [frequencyPenalty, setFrequencyPenalty] = useState(0.0);
  const [presencePenalty, setPresencePenalty] = useState(0.0);
  const [systemPrompt, setSystemPrompt] = useState('You are a Health and Wellness Coach.');
  const [loading, setLoading] = useState(false);
  const toast = useRef<Toast>(null);

  const sendMessage = async () => {
    if (!message) return;

    setChatHistory([...chatHistory, { user: message, bot: '' }]);
    setLoading(true);
    console.log(message, systemPrompt);
    try {
      const response = await axios.post('http://localhost:5000/chat', {
        message,
        systemPrompt,
        temperature,
        topP,
        frequencyPenalty,
        presencePenalty,
      });
      const botMessage = response.data.response;

      // Simulate typing animation
      let index = 0;
      const typingInterval = setInterval(() => {
        setChatHistory((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].bot = botMessage.slice(0, index);
          return updated;
        });
        index++;
        if (index > botMessage.length) {
          clearInterval(typingInterval);
          setLoading(false);
        }
      }, 15); // Adjust typing speed here
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'An error occurred';
      console.error('Error sending message:', error);

      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: errorMessage,
        life: 5000,
      });

      setChatHistory((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].bot = errorMessage;
        return updated;
      });
      setLoading(false);
    }

    setMessage('');
  };

  return (
    <Card title="Chat Interface" className="shadow-lg">
      <Toast ref={toast} />
      <div className="mb-4">
        <label htmlFor="systemPrompt">System Prompt:</label>
        <div className="flex items-center gap-2">
          <InputText
            id="systemPrompt"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            placeholder="Enter system prompt..."
            className="w-full"
          />
          <i className="pi pi-info-circle" data-pr-tooltip="This prompt sets the context for the AI's responses." />
        </div>
      </div>
      <div className="chat-history p-4 mb-4 max-h-60 overflow-y-auto">
        {chatHistory.map((chat, index) => (
          <div key={index} className="mb-2">
            <p><strong>You:</strong> {chat.user}</p>
            <p><strong>Bot:</strong> {chat.bot}</p>
          </div>
        ))}
        {loading && <ProgressSpinner style={{ width: '20px', height: '20px' }} strokeWidth="8" />}
      </div>
      <div className="flex gap-2 mb-4">
        <InputText
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          className="w-full"
        />
        <Button label="Send" icon="pi pi-send" onClick={sendMessage} disabled={loading} />
      </div>
      <div className="flex flex-col gap-4">
        <div>
          <label>Temperature: {temperature.toFixed(1)}</label>
          <i className="pi pi-info-circle" data-pr-tooltip="Controls randomness" />
          <Slider value={temperature} onChange={(e) => setTemperature(e.value)} min={0} max={1} step={0.1} />
        </div>
        <div>
          <label>Top P: {topP.toFixed(1)}</label>
          <i className="pi pi-info-circle" data-pr-tooltip="Controls diversity" />
          <Slider value={topP} onChange={(e) => setTopP(e.value)} min={0} max={1} step={0.1} />
        </div>
        <div>
          <label>Frequency Penalty: {frequencyPenalty.toFixed(1)}</label>
          <i className="pi pi-info-circle" data-pr-tooltip="Penalizes repeated words" />
          <Slider value={frequencyPenalty} onChange={(e) => setFrequencyPenalty(e.value)} min={0} max={2} step={0.1} />
        </div>
        <div>
          <label>Presence Penalty: {presencePenalty.toFixed(1)}</label>
          <i className="pi pi-info-circle" data-pr-tooltip="Encourages new topics" />
          <Slider value={presencePenalty} onChange={(e) => setPresencePenalty(e.value)} min={0} max={2} step={0.1} />
        </div>
      </div>
      <Tooltip target=".pi-info-circle" />
    </Card>
  );
};

export default ChatInterface;