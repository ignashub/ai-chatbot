import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, systemPrompt, temperature, topP, frequencyPenalty, presencePenalty } = body;

    // Check if the message is asking about a specific document
    const isDocumentQuery = message.toLowerCase().includes('.pdf') || 
                           message.toLowerCase().includes('document') || 
                           message.toLowerCase().includes('from the');
    
    console.log(`Processing ${isDocumentQuery ? 'document' : 'regular'} query: ${message}`);
    
    // Send request to backend chat endpoint
    const chatResponse = await axios.post('http://127.0.0.1:5000/chat', {
      message: message,
      systemPrompt: isDocumentQuery 
        ? `${systemPrompt || "You are a Health and Wellness Coach."} When answering questions about documents, provide comprehensive and detailed responses based on the information in the context. Include all relevant details, examples, tools, methods, and frameworks mentioned in the document. Pay special attention to sections marked as 'RELEVANT SECTION' as they directly relate to the user's query. Be thorough and specific, ensuring you don't omit any important information from the document.`
        : systemPrompt || "You are a Health and Wellness Coach. You can help set reminders for health activities and provide nutrition information for food items.",
      model: "gpt-4",
      temperature: temperature || 0.3,  // Lower temperature for more factual responses
      top_p: topP || 1.0,
      frequency_penalty: frequencyPenalty || 0.0,
      presence_penalty: presencePenalty || 0.0
    }, {
      timeout: 120000 // 120 second timeout for document processing
    });
    
    // Calculate estimated cost - handle missing usage information
    let formattedCost = 'Cost information not available';
    
    if (chatResponse.data.tokens) {
      const promptTokens = chatResponse.data.tokens.input || 0;
      const completionTokens = chatResponse.data.tokens.output || 0;
      const promptCost = (promptTokens / 1000) * 0.01; // $0.01 per 1K tokens
      const completionCost = (completionTokens / 1000) * 0.03; // $0.03 per 1K tokens
      const totalCost = promptCost + completionCost;
      formattedCost = `$${totalCost.toFixed(5)} (${promptTokens} prompt tokens, ${completionTokens} completion tokens)`;
    } else if (chatResponse.data.estimated_cost) {
      formattedCost = chatResponse.data.estimated_cost;
    }
    
    console.log(`Response received from backend, length: ${chatResponse.data.response?.length || 0} characters`);
    
    return NextResponse.json({
      response: chatResponse.data.response,
      estimated_cost: formattedCost
    });
  } catch (error: any) {
    console.error('Error in chat API route:', error);
    
    let errorMessage = 'Failed to get response from AI';
    let statusCode = 500;
    
    if (error.response) {
      console.error('Error response data:', error.response.data);
      errorMessage = error.response.data?.error || errorMessage;
      statusCode = error.response.status || statusCode;
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    return NextResponse.json({ error: errorMessage }, { status: statusCode });
  }
} 