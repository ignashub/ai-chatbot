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
import { Dialog } from 'primereact/dialog'; // Import Dialog component

const ChatInterface = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<{ user: string; bot: string }[]>([]);
  const [temperature, setTemperature] = useState(0.7);
  const [topP, setTopP] = useState(1.0);
  const [frequencyPenalty, setFrequencyPenalty] = useState(0.0);
  const [presencePenalty, setPresencePenalty] = useState(0.0);
  const [systemPrompt, setSystemPrompt] = useState('You are a Health and Wellness Coach. You can help set reminders for health activities and provide nutrition information for food items.');
  const [loading, setLoading] = useState(false);
  const [cost, setCost] = useState<string | null>(null);
  const [showHelp, setShowHelp] = useState(false); // State to control the help dialog
  const toast = useRef<Toast>(null);

  const sendMessage = async () => {
    if (!message) return;

    setChatHistory([...chatHistory, { user: message, bot: '' }]);
    setLoading(true);
    setCost(null);
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
      const promptCost = response.data.estimated_cost;
      setCost(promptCost);

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
      }, 15);
    } catch (error: any) {
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
    <Card title="Chat" className="shadow-lg">
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
        <Button label="Help" icon="pi pi-question-circle" onClick={() => setShowHelp(true)} /> {/* Help button */}
      </div>
      {cost && (
        <div className="mb-4">
          <p><strong>Cost of this prompt:</strong> {cost}</p>
        </div>
      )}
      <div className="flex flex-col gap-4">
        <div>
          <label>Temperature: {temperature.toFixed(1)}</label>
          <i className="pi pi-info-circle" data-pr-tooltip="Controls randomness. Example: At temperature 0.2, responses are more focused and deterministic. At 0.8, responses are more creative and varied. Low values are good for factual queries, high values for creative tasks." />
          <Slider value={temperature} onChange={(e) => setTemperature(typeof e.value === 'number' ? e.value : e.value[0])} min={0} max={1} step={0.1} />
        </div>
        <div>
          <label>Top P: {topP.toFixed(1)}</label>
          <i className="pi pi-info-circle" data-pr-tooltip="Controls diversity of responses. Example: At 0.3, responses are more focused and predictable. At 0.9, responses include more variety and unexpected ideas. Works well with Temperature to balance creativity and relevance." />
          <Slider value={topP} onChange={(e) => setTopP(typeof e.value === 'number' ? e.value : e.value[0])} min={0} max={1} step={0.1} />
        </div>
        <div>
          <label>Frequency Penalty: {frequencyPenalty.toFixed(1)}</label>
          <i className="pi pi-info-circle" data-pr-tooltip="Penalizes repeated words. Example: With a high frequency penalty, instead of saying great, great, great multiple times, the model might use alternatives like excellent, wonderful, and fantastic." />
          <Slider value={frequencyPenalty} onChange={(e) => setFrequencyPenalty(typeof e.value === 'number' ? e.value : e.value[0])} min={0} max={2} step={0.1} />
        </div>
        <div>
          <label>Presence Penalty: {presencePenalty.toFixed(1)}</label>
          <i className="pi pi-info-circle" data-pr-tooltip="Encourages new topics. Example: With a high presence penalty, if you've been discussing exercise, the model is more likely to branch out to related topics like nutrition or recovery rather than continuing to elaborate on exercise." />
          <Slider value={presencePenalty} onChange={(e) => setPresencePenalty(typeof e.value === 'number' ? e.value : e.value[0])} min={0} max={2} step={0.1} />
        </div>
      </div>
      <Tooltip target=".pi-info-circle" />

      {/* Help Dialog */}
      <Dialog header="How to Use the Chatbot" visible={showHelp} style={{ width: '50vw' }} onHide={() => setShowHelp(false)}>
        <p>Welcome to your personal AI Health & Wellness Coach! Here's how you can use this application:</p>
        <ul>
          <li>Enter your message in the input field and click 'Send' to interact with the bot.</li>
          <li>Adjust the settings like Temperature, Top P, Frequency Penalty, and Presence Penalty to customize the bot's responses.</li>
          <li>The 'System Prompt' sets the context for the AI's responses. You can change it to suit your needs.</li>
          <li>Click the 'Help' button anytime to view this guide.</li>
        </ul>
        
        <h3 className="font-bold mt-4">Special Features:</h3>
        <ul>
          <li><strong>Set Reminders:</strong> Ask the AI to set reminders for your health activities. For example, "Remind me to take my vitamins tomorrow at 9 AM" or "Set a reminder for my workout on Friday at 6 PM".</li>
          <li><strong>Nutrition Information:</strong> Ask about nutrition facts for different foods. For example, "What's the nutritional value of an apple?" or "How many calories are in 200g of chicken breast?"</li>
        </ul>
        
        <p className="mt-4 text-sm text-gray-600">Your reminders will appear in the panel on the right side of the screen.</p>
      </Dialog>
    </Card>
  );
};

export default ChatInterface;