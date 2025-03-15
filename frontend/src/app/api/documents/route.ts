import { NextResponse } from 'next/server';
import axios from 'axios';

export async function GET() {
  try {
    const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/documents`);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error fetching documents:', error);
    return NextResponse.json(
      { error: error.message || 'An error occurred fetching documents' },
      { status: 500 }
    );
  }
} 