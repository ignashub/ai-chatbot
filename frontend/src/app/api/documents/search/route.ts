import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

interface DocumentItem {
  title?: string;
  document_name?: string;
  content?: string;
  text?: string;
  snippet?: string;
  source?: string;
  page?: number | string;
  score?: number;
  [key: string]: any;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const query = body.query;

    if (!query) {
      return NextResponse.json({ error: 'Query is required' }, { status: 400 });
    }

    console.log('Searching documents with query:', query);
    console.log('Sending to:', `${process.env.NEXT_PUBLIC_API_URL}/api/documents/search`);

    const response = await axios.post(
      `${process.env.NEXT_PUBLIC_API_URL}/api/documents/search`,
      { query }
    );

    // Validate and structure the response
    const responseData = response.data;
    
    // Ensure we have a properly structured response
    const formattedResponse = {
      query: query,
      results: Array.isArray(responseData) 
        ? responseData.map((item: DocumentItem) => ({
            title: item.title || item.document_name || 'Untitled',
            content: item.content || item.text || item.snippet || '',
            source: item.source || item.document_name || '',
            page: item.page || '',
            score: item.score || 0
          }))
        : Array.isArray(responseData.results)
          ? responseData.results.map((item: DocumentItem) => ({
              title: item.title || item.document_name || 'Untitled',
              content: item.content || item.text || item.snippet || '',
              source: item.source || item.document_name || '',
              page: item.page || '',
              score: item.score || 0
            }))
          : []
    };

    console.log('Formatted search response:', formattedResponse);
    return NextResponse.json(formattedResponse);
  } catch (error: any) {
    const requestBody = request.body ? await request.clone().json().catch(() => ({})) : {};
    console.error('Error searching documents:', error);
    return NextResponse.json(
      { 
        query: requestBody.query || '',
        results: [],
        error: error.message || 'Failed to search documents' 
      },
      { status: error.response?.status || 500 }
    );
  }
} 