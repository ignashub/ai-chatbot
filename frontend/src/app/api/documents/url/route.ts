import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { url } = body;
    
    if (!url) {
      return NextResponse.json(
        { error: 'URL is required' },
        { status: 400 }
      );
    }
    
    const response = await axios.post('http://127.0.0.1:5000/documents/url', { url });
    return NextResponse.json(response.data, { status: 201 });
  } catch (error: any) {
    console.error('Error adding document from URL:', error);
    return NextResponse.json(
      { error: error.response?.data?.error || 'Failed to add document from URL' },
      { status: error.response?.status || 500 }
    );
  }
} 