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
import { Dialog } from 'primereact/dialog';
import ExportOptions from './ExportOptions';

const ChatInterface = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<{ user: string; bot: string }[]>([]);
  const [temperature, setTemperature] = useState(0.7);
  const [topP, setTopP] = useState(1.0);
  const [frequencyPenalty, setFrequencyPenalty] = useState(0.0);
  const [presencePenalty, setPresencePenalty] = useState(0.0);
  const [systemPrompt, setSystemPrompt] = useState(`You are a Health and Wellness Coach with access to a knowledge base of health documents. 

When users ask about specific documents or topics in the knowledge base:
1. Always search the knowledge base for relevant information
2. If a user mentions a specific document (e.g., "Concept-health-Rai-2016.pdf"), search for and retrieve information from that document
3. Present information accurately, citing the source document
4. Include specific details from the documents when available, such as measurement methods, frameworks, or tools
5. If you find information in the knowledge base, include "Sources: [document name]" at the end of your response

If you cannot find information in the knowledge base, clearly state that you don't have that specific document or information, but still try to provide helpful general information on the topic.

You can also help set reminders for health activities and provide nutrition information for food items.`);
  const [loading, setLoading] = useState(false);
  const [cost, setCost] = useState<string | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const toast = useRef<Toast>(null);

  // Convert chatHistory to the format expected by ExportOptions
  const getExportableConversation = () => {
    return chatHistory.flatMap((chat, index) => [
      {
        role: 'user',
        content: chat.user,
        timestamp: new Date(Date.now() - (chatHistory.length - index) * 60000).toISOString()
      },
      {
        role: 'assistant',
        content: chat.bot,
        timestamp: new Date(Date.now() - (chatHistory.length - index) * 60000 + 30000).toISOString()
      }
    ]);
  };

  const sendMessage = async () => {
    if (!message) return;

    setChatHistory([...chatHistory, { user: message, bot: '' }]);
    setLoading(true);
    setCost(null);
    
    try {
      // Check if the message is asking about a document
      const isDocumentQuery = /knowledge\s*base|document|pdf|file|uploaded|Concept-health-Rai-2016|tell\s*me\s*about/i.test(message);
      
      // If it's a document query, add a special instruction to search the knowledge base
      const enhancedMessage = isDocumentQuery 
        ? `[SEARCH_KNOWLEDGE_BASE] ${message}` 
        : message;
      
      const response = await axios.post('/api/chat', {
        message: enhancedMessage,
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

  const formatMessage = (message: string) => {
    // Check if the message contains sources
    if (message.includes('Sources:')) {
      // Split the message into content and sources
      const [content, sources] = message.split('Sources:');
      
      return (
        <>
          {content}
          <div className="mt-1">
            <span className="font-semibold">Sources:</span>
            <span className="text-sm text-gray-600">{sources}</span>
          </div>
        </>
      );
    }
    
    return message;
  };

  return (
    <Card title="Health & Wellness AI Assistant" className="shadow-lg">
      <Toast ref={toast} />
      <div className="mb-4 flex justify-between items-center">
        <div className="flex-grow">
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
      </div>
      <div className="chat-history p-4 mb-4 max-h-96 overflow-y-auto border rounded-lg bg-gray-50">
        {chatHistory.length === 0 && (
          <div className="text-center p-4 text-gray-500">
            <p className="mb-2 font-semibold">Welcome to your Health & Wellness AI Assistant!</p>
            <p>You can ask me questions about health topics, nutrition information, or search our knowledge base.</p>
            <p className="mt-2 text-sm">Try asking:</p>
            <ul className="text-sm list-disc list-inside mt-1">
              <li>"What are the benefits of regular exercise?"</li>
              <li>"Tell me about positive health from our knowledge base"</li>
              <li>"What does the document Concept-health-Rai-2016.pdf say about health?"</li>
              <li>"Remind me to drink water every 2 hours"</li>
            </ul>
          </div>
        )}
        {chatHistory.map((chat, index) => (
          <div key={index} className="mb-4">
            <div className="bg-blue-100 p-3 rounded-lg inline-block max-w-[80%] float-right clear-both">
              <div className="font-bold text-blue-800 mb-1">You</div>
              <div className="text-blue-700">{chat.user}</div>
            </div>
            <div className="clear-both"></div>
            <div className="bg-white p-3 rounded-lg shadow-sm inline-block max-w-[80%] mt-2">
              <div className="font-bold text-gray-800 mb-1">Bot</div>
              <div className="text-gray-700">{formatMessage(chat.bot)}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-center my-2">
            <ProgressSpinner style={{ width: '30px', height: '30px' }} strokeWidth="8" />
          </div>
        )}
      </div>
      <div className="ml-4">
          <ExportOptions 
            conversation={getExportableConversation()} 
            isDisabled={chatHistory.length === 0} 
          />
        </div>
      <div className="flex gap-2 mb-4">
        <InputText
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask about health topics or search our knowledge base..."
          className="w-full"
        />
        <Button label="Send" icon="pi pi-send" onClick={sendMessage} disabled={loading || !message.trim()} />
        <Button label="Help" icon="pi pi-question-circle" onClick={() => setShowHelp(true)} />
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
          <li>Use the 'Export' button to download your conversation in JSON, CSV, or PDF format.</li>
        </ul>
        
        <h3 className="font-bold mt-4">Special Features:</h3>
        <ul>
          <li><strong>Knowledge Base Search:</strong> Ask questions about health topics in our knowledge base. For example, "What does our knowledge base say about positive health?" or "Tell me about the document Concept-health-Rai-2016.pdf"</li>
          <li><strong>Set Reminders:</strong> Ask the AI to set reminders for your health activities. For example, "Remind me to take my vitamins tomorrow at 9 AM" or "Set a reminder for my workout on Friday at 6 PM".</li>
          <li><strong>Nutrition Information:</strong> Ask about nutrition facts for different foods. For example, "What's the nutritional value of an apple?" or "How many calories are in 200g of chicken breast?"</li>
          <li><strong>Export Conversations:</strong> Download your conversations in different formats for record-keeping or sharing.</li>
        </ul>
        
        <p className="mt-4 text-sm text-gray-600">Your reminders will appear in the panel on the right side of the screen.</p>
      </Dialog>
    </Card>
  );
};

export default ChatInterface;