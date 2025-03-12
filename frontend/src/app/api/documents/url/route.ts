import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const { url } = await request.json();
    
    if (!url) {
      return NextResponse.json({ error: 'URL is required' }, { status: 400 });
    }
    
    console.log(`Processing document from URL: ${url}`);
    
    // Increase timeout to 3 minutes (180 seconds)
    const response = await axios.post(
      'http://127.0.0.1:5000/documents/url', 
      { url },
      { 
        timeout: 180000, // 3 minutes
        maxContentLength: Infinity,
        maxBodyLength: Infinity
      }
    );
    
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error processing document from URL:', error);
    
    // Detailed error logging
    if (error.response) {
      console.error('Error response:', error.response.data);
      console.error('Status:', error.response.status);
      
      // Return the backend error message and logs if available
      return NextResponse.json({
        error: error.response.data.error || 'Failed to process document',
        logs: error.response.data.logs || [],
        details: `Status code: ${error.response.status}`
      }, { status: error.response.status });
    } else if (error.request) {
      console.error('No response received:', error.request);
      return NextResponse.json({
        error: 'No response received from server. The server might be overloaded or the document is too large.',
        details: 'Request timeout or server error'
      }, { status: 504 });
    } else {
      console.error('Error setting up request:', error.message);
      return NextResponse.json({
        error: `Error: ${error.message}`,
        details: 'Client-side error'
      }, { status: 500 });
    }
  }
} 