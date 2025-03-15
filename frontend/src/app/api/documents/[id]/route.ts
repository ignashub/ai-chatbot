import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const id = params.id;
    
    if (!id) {
      return NextResponse.json(
        { error: 'Document ID is required' },
        { status: 400 }
      );
    }
    
    const response = await axios.delete(`${process.env.NEXT_PUBLIC_API_URL}/api/documents/${id}`);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error(`Error deleting document ${params.id}:`, error);
    return NextResponse.json(
      { error: error.response?.data?.error || 'Failed to delete document' },
      { status: error.response?.status || 500 }
    );
  }
} 