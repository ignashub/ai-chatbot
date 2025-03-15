// This file is being deleted as we're removing the reindexing feature.
// The user will delete and re-upload documents instead of reindexing them. 

import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST() {
  try {
    const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/documents/reindex`);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error reindexing documents:', error);
    return NextResponse.json(
      { error: error.response?.data?.error || 'Failed to reindex documents' },
      { status: error.response?.status || 500 }
    );
  }
} 