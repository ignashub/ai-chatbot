import { NextResponse } from 'next/server';
import axios from 'axios';

export async function DELETE(
  request: Request,
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
    
    const response = await axios.delete(`http://127.0.0.1:5000/documents/${id}`);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error deleting document:', error);
    return NextResponse.json(
      { error: error.response?.data?.error || 'Failed to delete document' },
      { status: error.response?.status || 500 }
    );
  }
} 