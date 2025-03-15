import { NextResponse } from 'next/server';
import axios from 'axios';

export async function GET() {
  try {
    const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/documents/logs`);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error fetching document processing logs:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to fetch document processing logs' },
      { status: 500 }
    );
  }
} 