"use client";

import { useState } from 'react';
import axios from 'axios';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { FileUpload } from 'primereact/fileupload';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Tooltip } from 'primereact/tooltip';
import { Toast } from 'primereact/toast';
import { useRef } from 'react';

interface Document {
  id: string;
  title: string;
  source: string;
  total_chunks: number;
}

const DocumentUploader = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const toast = useRef<Toast>(null);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get('/api/documents');
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to fetch documents',
        life: 3000
      });
    }
  };

  // Fetch documents on component mount
  useState(() => {
    fetchDocuments();
  });

  const addDocumentFromUrl = async () => {
    if (!url) return;

    setLoading(true);
    try {
      const response = await axios.post('/api/documents/url', { url });
      
      toast.current?.show({
        severity: 'success',
        summary: 'Success',
        detail: response.data.message,
        life: 3000
      });
      
      // Refresh documents list
      fetchDocuments();
      
      // Clear URL input
      setUrl('');
    } catch (error: any) {
      console.error('Error adding document from URL:', error);
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: error.response?.data?.error || 'Failed to add document from URL',
        life: 3000
      });
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = async (event: any) => {
    const file = event.files[0];
    
    if (!file) {
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'No file selected',
        life: 3000
      });
      return;
    }
    
    // Show loading state
    setLoading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      console.log('Uploading file:', file.name);
      
      const response = await axios.post('/api/documents/file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        // Add timeout and onUploadProgress for better monitoring
        timeout: 30000,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          console.log(`Upload progress: ${percentCompleted}%`);
        }
      });
      
      console.log('Upload response:', response.data);
      
      toast.current?.show({
        severity: 'success',
        summary: 'Success',
        detail: response.data.message,
        life: 3000
      });
      
      // Refresh documents list
      fetchDocuments();
    } catch (error: any) {
      console.error('Error uploading file:', error);
      
      // More detailed error logging
      if (error.response) {
        console.error('Error response:', error.response.data);
        console.error('Status:', error.response.status);
      } else if (error.request) {
        console.error('No response received:', error.request);
      } else {
        console.error('Error setting up request:', error.message);
      }
      
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: error.response?.data?.error || 'Failed to upload file. Please try again.',
        life: 5000
      });
    } finally {
      setLoading(false);
    }
  };

  const cardTitle = (
    <div className="flex items-center gap-2">
      <span>Knowledge Base Documents</span>
      <i 
        className="pi pi-info-circle cursor-pointer document-tooltip" 
        data-pr-tooltip="Add documents to the knowledge base to enhance the AI's responses with specific information. You can add documents from URLs or upload files (PDF, TXT)."
        data-pr-position="right"
        data-pr-at="right+5 top"
        style={{ fontSize: '0.9rem' }}
      />
    </div>
  );

  return (
    <Card title={cardTitle} className="shadow-lg mb-4">
      <Toast ref={toast} />
      <Tooltip target=".document-tooltip" />
      
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Add Document from URL</h3>
        <div className="flex gap-2">
          <InputText
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter URL (e.g., https://example.com/article)"
            className="w-full"
          />
          <Button 
            label="Add" 
            icon="pi pi-plus" 
            onClick={addDocumentFromUrl} 
            disabled={loading || !url}
          />
        </div>
      </div>
      
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Upload Document</h3>
        <FileUpload
          mode="basic"
          name="file"
          url="/api/documents/file"
          accept=".pdf,.txt"
          maxFileSize={10000000}
          customUpload
          uploadHandler={uploadFile}
          chooseLabel="Select File"
          className="w-full"
        />
        <p className="text-xs text-gray-500 mt-1">Supported formats: PDF, TXT. Max size: 10MB</p>
      </div>
      
      {loading && (
        <div className="flex justify-center my-4">
          <ProgressSpinner style={{ width: '50px', height: '50px' }} />
        </div>
      )}
      
      <div className="mt-4">
        <h3 className="text-lg font-semibold mb-2">Uploaded Documents</h3>
        {documents.length > 0 ? (
          <ul className="list-disc pl-5">
            {documents.map((doc) => (
              <li key={doc.id} className="mb-2">
                <div className="font-medium">{doc.title}</div>
                <div className="text-sm text-gray-500">
                  Source: {doc.source}
                  <span className="ml-2">({doc.total_chunks} chunks)</span>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No documents added yet.</p>
        )}
      </div>
    </Card>
  );
};

export default DocumentUploader; 