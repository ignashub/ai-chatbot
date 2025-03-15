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
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/documents/file`, 
        backendFormData, 
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          // Increase timeout to 5 minutes for large files
          timeout: 300000,
          // Add progress tracking
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
            console.log(`Upload progress: ${percentCompleted}%`);
          }
        }
      );
      
      // Clean up temporary file
      try {
        fs.unlinkSync(tempFilePath);
        console.log(`Temporary file deleted: ${tempFilePath}`);
      } catch (cleanupError) {
        console.error(`Error cleaning up temporary file: ${cleanupError}`);
      }
      
      return NextResponse.json(response.data);
    } catch (uploadError: any) {
      console.error('Error uploading file to backend:', uploadError);
      
      // Clean up temporary file even if upload failed
      try {
        fs.unlinkSync(tempFilePath);
        console.log(`Temporary file deleted after upload error: ${tempFilePath}`);
      } catch (cleanupError) {
        console.error(`Error cleaning up temporary file: ${cleanupError}`);
      }
      
      return NextResponse.json(
        { error: uploadError.response?.data?.error || 'Failed to upload file to backend' },
        { status: uploadError.response?.status || 500 }
      );
    }
  } catch (error: any) {
    console.error('Error processing file upload:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to process file upload' },
      { status: 500 }
    );
  }
}