import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/nutrition`, body);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error fetching nutrition info:', error);
    return NextResponse.json(
      { error: error.response?.data?.error || 'Failed to fetch nutrition information' },
      { status: error.response?.status || 500 }
    );
  }
} 