import { NextResponse } from 'next/server';
import axios from 'axios';

export async function GET() {
  try {
    const response = await axios.get('http://127.0.0.1:5000/documents/logs');
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error fetching document logs:', error);
    return NextResponse.json(
      { error: error.response?.data?.error || 'Failed to fetch document logs' },
      { status: error.response?.status || 500 }
    );
  }
} 