"use client";

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Tooltip } from 'primereact/tooltip';

interface Reminder {
  id: number;
  title: string;
  description: string;
  datetime: string;
  created_at: string;
}

const RemindersPanel = () => {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReminders = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Fetching reminders...');
      const response = await axios.get('/api/reminders');
      console.log('Reminders response:', response.data);
      setReminders(response.data);
    } catch (error) {
      console.error('Error fetching reminders:', error);
      setError('Failed to load reminders. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReminders();
    
    // Set up a refresh interval (every 60 seconds)
    const intervalId = setInterval(fetchReminders, 60000);
    
    // Listen for reminder set events
    const handleReminderSet = () => {
      console.log('Reminder set event detected, refreshing reminders');
      fetchReminders();
    };
    
    window.addEventListener('reminderSet', handleReminderSet);
    
    return () => {
      clearInterval(intervalId);
      window.removeEventListener('reminderSet', handleReminderSet);
    };
  }, []);

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  const cardTitle = (
    <div className="flex items-center gap-2">
      <span>Your Reminders</span>
      <i 
        className="pi pi-info-circle cursor-pointer reminder-tooltip" 
        data-pr-tooltip="To set a reminder, ask the AI: 'Remind me to take my vitamins tomorrow at 9 AM' or 'Set a reminder for my workout on Friday at 6 PM'"
        data-pr-position="right"
        data-pr-at="right+5 top"
        style={{ fontSize: '0.9rem' }}
      />
    </div>
  );

  return (
    <Card title={cardTitle} className="shadow-lg mb-4">
      <Tooltip target=".reminder-tooltip" />
      <Button 
        label="Refresh" 
        icon="pi pi-refresh" 
        className="mb-3" 
        onClick={fetchReminders} 
        disabled={loading}
      />
      
      {loading && (
        <div className="flex justify-center my-4">
          <ProgressSpinner style={{ width: '50px', height: '50px' }} />
        </div>
      )}
      
      {error && (
        <div className="p-message p-message-error mb-3">
          <div className="p-message-text">{error}</div>
        </div>
      )}
      
      {!loading && reminders.length === 0 && (
        <div className="text-center p-4 border rounded bg-gray-50">
          <p>No reminders yet. Ask the AI to set a reminder for you!</p>
          <p className="text-sm text-gray-500 mt-2">
            Try saying: "Remind me to drink water at 3:00 PM today"
          </p>
        </div>
      )}
      
      {reminders.map((reminder) => (
        <div key={reminder.id} className="p-3 border-bottom mb-2">
          <h3 className="text-xl font-bold">{reminder.title}</h3>
          {reminder.description && <p className="text-gray-700">{reminder.description}</p>}
          <p className="text-sm text-gray-500 mt-2">
            <i className="pi pi-calendar mr-2"></i>
            {formatDateTime(reminder.datetime)}
          </p>
        </div>
      ))}
    </Card>
  );
};

export default RemindersPanel; 