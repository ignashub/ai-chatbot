import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, systemPrompt, temperature, topP, frequencyPenalty, presencePenalty } = body;

    // Check if this is a knowledge base query
    const isKnowledgeBaseQuery = message.includes('[SEARCH_KNOWLEDGE_BASE]');
    
    // If it's a knowledge base query, first search the knowledge base
    let documentContext = '';
    if (isKnowledgeBaseQuery) {
      console.log('Knowledge base query detected, searching documents first');
      
      try {
        // Extract the actual query (remove the special tag)
        const actualQuery = message.replace('[SEARCH_KNOWLEDGE_BASE]', '').trim();
        
        // Search the knowledge base
        const searchResponse = await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL}/api/documents/search`,
          { query: actualQuery }
        );
        
        const searchResults = searchResponse.data.results || [];
        console.log(`Found ${searchResults.length} documents for query: ${actualQuery}`);
        
        if (searchResults.length > 0) {
          // Format the document context
          documentContext = "Here is information from the documents you asked about:\n\n";
          
          // Group results by document title
          const docsByTitle = {};
          for (const doc of searchResults) {
            const title = doc.title || 'Unknown';
            if (!docsByTitle[title]) {
              docsByTitle[title] = [];
            }
            docsByTitle[title].push(doc);
          }
          
          // Add content from each document
          for (const [title, docs] of Object.entries(docsByTitle)) {
            documentContext += `--- From document: ${title} ---\n\n`;
            
            // Combine content from all chunks
            let combinedContent = "";
            for (const doc of docs) {
              combinedContent += `${doc.content}\n\n`;
            }
            
            documentContext += combinedContent;
          }
          
          console.log(`Added document context (${documentContext.length} chars)`);
        }
      } catch (searchError) {
        console.error('Error searching knowledge base:', searchError);
        // Continue with the original message if search fails
      }
    }
    
    // Prepare the message for the AI
    const enhancedMessage = documentContext 
      ? `${documentContext}\n\nUser query: ${message.replace('[SEARCH_KNOWLEDGE_BASE]', '')}`
      : message;
    
    // Send the message to the backend
    const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/chat/message`, {
      message: enhancedMessage,
      systemPrompt,
      temperature,
      topP,
      frequencyPenalty,
      presencePenalty
    });

    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error in chat API:', error);
    
    return NextResponse.json(
      { error: error.response?.data?.error || error.message || 'An error occurred' },
      { status: error.response?.status || 500 }
    );
  }
} 