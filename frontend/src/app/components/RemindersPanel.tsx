"use client";

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { ProgressSpinner } from 'primereact/progressspinner';

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
      const response = await axios.get('http://localhost:5000/reminders');
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
    
    // Set up polling to refresh reminders every 30 seconds
    const intervalId = setInterval(fetchReminders, 30000);
    
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  return (
    <Card title="Your Reminders" className="shadow-lg mb-4">
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