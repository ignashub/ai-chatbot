import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const id = params.id;
    console.log('Deleting reminder with ID:', id);
    
    const response = await axios.delete(`${process.env.NEXT_PUBLIC_API_URL}/api/reminders/${id}`);
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error deleting reminder:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to delete reminder' },
      { status: error.response?.status || 500 }
    );
  }
} 