import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function GET() {
  try {
    console.log('Fetching reminders from:', `${process.env.NEXT_PUBLIC_API_URL}/api/reminders`);
    const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/reminders`);
    console.log('Reminders response data:', response.data);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error fetching reminders:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to fetch reminders' },
      { status: error.response?.status || 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    console.log('Creating reminder:', body);
    
    // Extract date and time from the date string if it's in ISO format
    let date = body.date;
    let time = body.time;
    
    if (!time && date) {
      // If we have a date in ISO format but no time, extract them
      const dateObj = new Date(date);
      date = dateObj.toISOString().split('T')[0]; // YYYY-MM-DD
      time = dateObj.toTimeString().split(' ')[0].substring(0, 5); // HH:MM
    }
    
    const reminderData = {
      title: body.title,
      description: body.description || "",
      date: date,
      time: time
    };
    
    console.log('Sending reminder data to backend:', reminderData);
    console.log('Sending to:', `${process.env.NEXT_PUBLIC_API_URL}/api/reminders`);
    
    const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/reminders`, reminderData);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error creating reminder:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to create reminder' },
      { status: error.response?.status || 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    
    if (!id) {
      return NextResponse.json({ error: 'Reminder ID is required' }, { status: 400 });
    }
    
    console.log('Deleting reminder:', id);
    const response = await axios.delete(`${process.env.NEXT_PUBLIC_API_URL}/api/reminders/${id}`);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error deleting reminder:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to delete reminder' },
      { status: error.response?.status || 500 }
    );
  }
} 