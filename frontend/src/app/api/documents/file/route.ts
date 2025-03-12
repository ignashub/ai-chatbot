import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';
import fs from 'fs';
import os from 'os';
import path from 'path';

export async function POST(request: NextRequest) {
  console.log('Received file upload request');
  
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    
    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }
    
    console.log(`Processing file: ${file.name}, size: ${file.size} bytes, type: ${file.type}`);
    
    // Save file to temporary location
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    
    // Create a temporary file path
    const tempFilePath = path.join(os.tmpdir(), file.name);
    fs.writeFileSync(tempFilePath, buffer);
    console.log(`File saved to temporary location: ${tempFilePath}`);
    
    // Create form data for backend
    const backendFormData = new FormData();
    const fileStream = fs.createReadStream(tempFilePath);
    
    // Add file to form data
    backendFormData.append('file', new Blob([buffer]), file.name);
    
    console.log('Sending file to backend');
    
    // Send to backend with a much longer timeout for large files
    try {
      const response = await axios.post('http://127.0.0.1:5000/documents/file', backendFormData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        // Increase timeout to 5 minutes for large files
        timeout: 300000,
        // Add progress tracking
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          console.log(`Upload progress: ${percentCompleted}%`);
        }
      });
      
      // Clean up temporary file
      try {
        fs.unlinkSync(tempFilePath);
        console.log(`Temporary file removed: ${tempFilePath}`);
      } catch (cleanupError) {
        console.error(`Error removing temporary file: ${cleanupError}`);
      }
      
      return NextResponse.json(response.data);
    } catch (error: any) {
      console.error('Error in file upload API route:', error);
      
      // Clean up temporary file
      try {
        fs.unlinkSync(tempFilePath);
        console.log(`Temporary file removed: ${tempFilePath}`);
      } catch (cleanupError) {
        console.error(`Error removing temporary file: ${cleanupError}`);
      }
      
      // Handle different error types
      if (error.code === 'ECONNABORTED') {
        console.error('Request timed out');
        return NextResponse.json(
          { 
            error: 'Request timed out. The file may be too large or the server is busy.',
            logs: [{ 
              timestamp: new Date().toISOString(),
              message: 'Processing timed out. The document may still be processing in the background. Please check the documents list in a few minutes.'
            }]
          }, 
          { status: 504 }
        );
      }
      
      if (error.response) {
        // The server responded with an error status
        console.error('Server error response:', error.response.data);
        return NextResponse.json(error.response.data, { status: error.response.status });
      } else if (error.request) {
        // No response received
        console.error('No response received from backend:', error.request);
        return NextResponse.json(
          { 
            error: 'No response received from the server. The server may be overloaded.',
            logs: [{ 
              timestamp: new Date().toISOString(),
              message: 'Server did not respond. The document may still be processing in the background. Please check the documents list in a few minutes.'
            }]
          }, 
          { status: 503 }
        );
      } else {
        // Error setting up the request
        return NextResponse.json({ error: error.message }, { status: 500 });
      }
    }
  } catch (error: any) {
    console.error('Error processing file upload:', error);
    return NextResponse.json({ error: 'Error processing file upload' }, { status: 500 });
  }
} 