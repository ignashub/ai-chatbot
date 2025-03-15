import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const { message, systemPrompt, isDocumentQuery, temperature, topP, frequencyPenalty, presencePenalty } = await request.json();
    
    console.log(`Processing ${isDocumentQuery ? 'document' : 'regular'} query: ${message.substring(0, 50)}${message.length > 50 ? '...' : ''}`);
    
    // Send request to backend chat endpoint
    const chatResponse = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/chat/message`, {
      message,
      systemPrompt: isDocumentQuery 
        ? `${systemPrompt || "You are a Health and Wellness Coach."} When answering questions about documents, provide comprehensive and detailed responses based on the information in the context. Include all relevant details, examples, tools, methods, and frameworks mentioned in the document. Pay special attention to sections marked as 'RELEVANT SECTION' as they directly relate to the user's query. Be thorough and specific, ensuring you don't omit any important information from the document.`
        : systemPrompt,
      temperature,
      topP,
      frequencyPenalty,
      presencePenalty
    }, {
      timeout: 120000 // 2 minute timeout
    });
    
    return NextResponse.json(chatResponse.data);
  } catch (error: any) {
    console.error('Error in chat API route:', error);
    
    // Log more detailed error information
    if (error.response) {
      console.error('Error response data:', error.response.data);
    }
    
    return NextResponse.json(
      { error: error.message || 'An error occurred processing your request' },
      { status: 500 }
    );
  }
} 