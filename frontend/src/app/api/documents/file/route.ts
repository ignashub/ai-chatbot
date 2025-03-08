import { NextResponse } from 'next/server';
import axios from 'axios';
import { writeFile } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';

export async function POST(request: Request) {
  try {
    console.log('Received file upload request');
    
    const formData = await request.formData();
    const file = formData.get('file') as File;
    
    if (!file) {
      console.error('No file in request');
      return NextResponse.json(
        { error: 'File is required' },
        { status: 400 }
      );
    }
    
    console.log(`Processing file: ${file.name}, size: ${file.size} bytes, type: ${file.type}`);
    
    // Save file to temp directory
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    
    // Create a temporary file
    const tempFilePath = join(tmpdir(), file.name);
    await writeFile(tempFilePath, buffer);
    console.log(`File saved to temporary location: ${tempFilePath}`);
    
    // Create form data for the backend request
    const backendFormData = new FormData();
    backendFormData.append('file', new Blob([buffer], { type: file.type }), file.name);
    
    console.log('Sending file to backend');
    
    // Send to backend with timeout
    const response = await axios.post('http://127.0.0.1:5000/documents/file', backendFormData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000 // 60 second timeout
    });
    
    console.log('Backend response:', response.data);
    
    return NextResponse.json(response.data, { status: 201 });
  } catch (error: any) {
    console.error('Error in file upload API route:', error);
    
    // More detailed error logging
    if (error.response) {
      console.error('Error response from backend:', error.response.data);
      console.error('Status:', error.response.status);
    } else if (error.request) {
      console.error('No response received from backend:', error.request);
    } else {
      console.error('Error setting up request:', error.message);
    }
    
    return NextResponse.json(
      { 
        error: error.response?.data?.error || 'Failed to upload file',
        details: error.message
      },
      { status: error.response?.status || 500 }
    );
  }
} 