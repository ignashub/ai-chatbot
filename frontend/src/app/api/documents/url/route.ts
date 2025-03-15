import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/documents/url`, body);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error adding document from URL:', error);
    return NextResponse.json(
      { error: error.response?.data?.error || 'Failed to add document from URL' },
      { status: error.response?.status || 500 }
    );
  }
} 