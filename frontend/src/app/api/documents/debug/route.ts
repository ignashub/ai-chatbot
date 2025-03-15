import { NextResponse } from 'next/server';
import axios from 'axios';

/**
 * This endpoint is deprecated and no longer used in the application.
 * It was previously used for debugging purposes to show document chunks in the vector store.
 * Kept for reference but can be safely removed.
 */
export async function GET() {
  try {
    const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/documents/debug`);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error fetching document debug info:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to fetch document debug info' },
      { status: 500 }
    );
  }
} 