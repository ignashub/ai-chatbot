import { NextResponse } from 'next/server';
import axios from 'axios';

/**
 * This endpoint is deprecated and no longer used in the application.
 * It was previously used for debugging purposes to show document chunks in the vector store.
 * Kept for reference but can be safely removed.
 */
export async function GET() {
  try {
    const response = await axios.get('http://127.0.0.1:5000/documents/debug');
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error fetching debug info:', error);
    return NextResponse.json(
      { error: 'Failed to fetch debug information' },
      { status: error.response?.status || 500 }
    );
  }
} 