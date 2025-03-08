import { NextResponse } from 'next/server';
import axios from 'axios';

export async function GET() {
  try {
    const response = await axios.get('http://127.0.0.1:5000/reminders');
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error fetching reminders:', error);
    return NextResponse.json(
      { error: 'Failed to fetch reminders' },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const response = await axios.post('http://127.0.0.1:5000/reminders', body);
    return NextResponse.json(response.data, { status: 201 });
  } catch (error: any) {
    console.error('Error creating reminder:', error);
    return NextResponse.json(
      { error: error.response?.data?.error || 'Failed to create reminder' },
      { status: error.response?.status || 500 }
    );
  }
} 