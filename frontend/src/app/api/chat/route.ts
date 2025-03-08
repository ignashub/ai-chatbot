import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { 
      message, 
      systemPrompt, 
      temperature, 
      topP, 
      frequencyPenalty, 
      presencePenalty 
    } = body;

    const response = await axios.post('http://127.0.0.1:5000/chat', {
      message,
      systemPrompt,
      temperature,
      topP,
      frequencyPenalty,
      presencePenalty,
    });

    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error in chat API route:', error);
    return NextResponse.json(
      { error: error.response?.data?.error || 'Error communicating with the chatbot' },
      { status: 500 }
    );
  }
} 