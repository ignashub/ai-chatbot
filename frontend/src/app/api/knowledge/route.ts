import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { query } = body;
    
    if (!query) {
      return NextResponse.json(
        { error: 'Query is required' },
        { status: 400 }
      );
    }
    
    const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/knowledge`, { query });
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error searching knowledge base:', error);
    return NextResponse.json(
      { error: error.response?.data?.error || 'Failed to search knowledge base' },
      { status: error.response?.status || 500 }
    );
  }
} 