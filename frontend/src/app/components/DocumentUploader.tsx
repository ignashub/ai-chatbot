"use client";

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { FileUpload } from 'primereact/fileupload';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Tooltip } from 'primereact/tooltip';
import { Toast } from 'primereact/toast';
import { ScrollPanel } from 'primereact/scrollpanel';
import { Panel } from 'primereact/panel';
import { useRef } from 'react';

interface Document {
  id: string;
  title: string;
  source: string;
  total_chunks: number;
}

interface LogEntry {
  timestamp: string;
  message: string;
}

const DocumentUploader = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<Array<{ id: string; title: string }>>([]);
  const toast = useRef<Toast>(null);
  const [processingLogs, setProcessingLogs] = useState<LogEntry[]>([]);
  const [showLogs, setShowLogs] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [pollingInterval, setPollingInterval] = useState<number>(1000); // Start with 1 second
  const [isPolling, setIsPolling] = useState<boolean>(false);
  const pollingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [lastLogTimestamp, setLastLogTimestamp] = useState<number>(Date.now());
  const [noActivityTimeout, setNoActivityTimeout] = useState<NodeJS.Timeout | null>(null);

  // Function to scroll to bottom of logs
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Effect to scroll to bottom when logs update
  useEffect(() => {
    if (showLogs) {
      scrollToBottom();
    }
  }, [processingLogs, showLogs]);

  // Cleanup polling on component unmount
  useEffect(() => {
    return () => {
      if (pollingTimeoutRef.current) {
        clearTimeout(pollingTimeoutRef.current);
      }
      setIsPolling(false);
    };
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get('/api/documents');
      setDocuments(response.data.documents || []);
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

  // Function to check for inactivity
  const checkInactivity = () => {
    const now = Date.now();
    const inactiveTime = now - lastLogTimestamp;
    
    // If no new logs for 30 seconds, consider the process complete or stuck
    if (inactiveTime > 30000) {
      console.log(`No activity for ${inactiveTime/1000} seconds, stopping polling`);
      
      // Add a final log entry to indicate timeout
      const timeoutLog = {
        timestamp: new Date().toISOString(),
        message: "Processing completed or timed out due to inactivity"
      };
      
      setProcessingLogs(prev => [...prev, timeoutLog]);
      stopPolling();
      
      // Refresh documents list in case the document was actually processed
      fetchDocuments();
      
      // Clear the timeout
      if (noActivityTimeout) {
        clearTimeout(noActivityTimeout);
        setNoActivityTimeout(null);
      }
    } else {
      // Check again in 5 seconds
      const timeout = setTimeout(checkInactivity, 5000);
      setNoActivityTimeout(timeout);
    }
  };

  // Start inactivity checking when polling starts
  useEffect(() => {
    if (isPolling) {
      setLastLogTimestamp(Date.now());
      const timeout = setTimeout(checkInactivity, 5000);
      setNoActivityTimeout(timeout);
      
      return () => {
        if (noActivityTimeout) {
          clearTimeout(noActivityTimeout);
        }
      };
    }
  }, [isPolling]);

  // Update the fetchLogs function to track the last log timestamp
  const fetchLogs = async () => {
    if (!isPolling) return;
    
    try {
      const response = await axios.get('/api/documents/logs');
      const newLogs = response.data.logs || [];
      
      // Only update if we have new logs
      if (JSON.stringify(newLogs) !== JSON.stringify(processingLogs)) {
        setProcessingLogs(newLogs);
        setLastLogTimestamp(Date.now()); // Update the timestamp when we get new logs
        
        // Check if processing is complete by looking at the last log message
        if (newLogs.length > 0) {
          const lastLog = newLogs[newLogs.length - 1].message;
          
          // Check for completion indicators in the last log message
          if (lastLog.includes("Successfully processed") || 
              lastLog.includes("Successfully") ||
              lastLog.includes("Document processing complete") ||
              lastLog.includes("Error processing") ||
              lastLog.includes("Failed to") ||
              lastLog.includes("Document processing failed") ||
              lastLog.includes("No documents were extracted")) {
            
            console.log("Processing complete, stopping polling");
            stopPolling();
            
            // If successful, show success notification
            if (lastLog.includes("Successfully") || lastLog.includes("complete")) {
              toast.current?.show({
                severity: 'success',
                summary: 'Success',
                detail: 'Document processed successfully',
                life: 3000
              });
              
              // Refresh documents list
              fetchDocuments();
            }
            
            return;
          }
        }
        
        // If processing is still ongoing, continue polling with slight backoff
        setPollingInterval(prev => Math.min(prev * 1.2, 3000));
      } else {
        // No new logs, increase polling interval more aggressively
        setPollingInterval(prev => Math.min(prev * 1.5, 5000));
      }
      
      // Schedule next poll
      pollingTimeoutRef.current = setTimeout(fetchLogs, pollingInterval);
      
    } catch (error: any) {
      console.error('Error fetching logs:', error);
      
      // Handle rate limiting specifically
      if (error.response?.status === 429) {
        console.log('Rate limited, backing off significantly');
        // Back off significantly on rate limit
        setPollingInterval(prev => Math.min(prev * 2, 10000));
      } else {
        // Other errors, increase interval moderately
        setPollingInterval(prev => Math.min(prev * 1.5, 5000));
      }
      
      // Continue polling with increased interval
      pollingTimeoutRef.current = setTimeout(fetchLogs, pollingInterval);
    }
  };

  // Start polling function
  const startPolling = () => {
    // Clear any existing timeout
    if (pollingTimeoutRef.current) {
      clearTimeout(pollingTimeoutRef.current);
    }
    
    setIsPolling(true);
    setPollingInterval(1000); // Reset to initial interval
    fetchLogs();
  };

  // Stop polling function
  const stopPolling = () => {
    if (pollingTimeoutRef.current) {
      clearTimeout(pollingTimeoutRef.current);
    }
    if (noActivityTimeout) {
      clearTimeout(noActivityTimeout);
      setNoActivityTimeout(null);
    }
    setIsPolling(false);
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const addDocumentFromUrl = async () => {
    if (!url) return;

    setLoading(true);
    setProcessingLogs([]);
    setShowLogs(true);
    
    try {
      toast.current?.show({
        severity: 'info',
        summary: 'Processing',
        detail: `Processing document from ${url}. This may take a minute for large documents.`,
        life: 3000
      });
      
      // Start polling for logs
      startPolling();
      
      const response = await axios.post('/api/documents/url', { url }, {
        // Add a longer timeout for large documents
        timeout: 180000 // 3 minutes
      });
      
      // Set final logs from response if available
      if (response.data.logs) {
        setProcessingLogs(response.data.logs);
      }
      
      // Stop polling - the improved polling logic should have already stopped it
      stopPolling();
      
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
      
      // Stop polling
      stopPolling();
      
      // Set final logs from error response if available
      if (error.response?.data?.logs) {
        setProcessingLogs(error.response.data.logs);
      }
      
      // Get detailed error message
      let errorMessage = 'Failed to add document from URL';
      if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.response?.data?.details) {
        errorMessage = `${error.response.data.error} - ${error.response.data.details}`;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: errorMessage,
        life: 5000
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
    
    // Check file size
    const maxSizeInMB = 10;
    const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
    
    if (file.size > maxSizeInBytes) {
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: `File size exceeds the maximum limit of ${maxSizeInMB}MB`,
        life: 5000
      });
      return;
    }
    
    // Show loading state
    setLoading(true);
    setProcessingLogs([]);
    setShowLogs(true);
    
    // Add initial log
    const initialLog = {
      timestamp: new Date().toISOString(),
      message: `Starting upload of ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`
    };
    setProcessingLogs([initialLog]);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      console.log('Uploading file:', file.name);
      
      // Start polling for logs
      startPolling();
      
      // Add upload started log
      const uploadStartedLog = {
        timestamp: new Date().toISOString(),
        message: `Uploading ${file.name} to server...`
      };
      setProcessingLogs(prev => [...prev, uploadStartedLog]);
      
      const response = await axios.post('/api/documents/file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        // Add timeout and onUploadProgress for better monitoring
        timeout: 300000, // 5 minutes
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          console.log(`Upload progress: ${percentCompleted}%`);
          
          // Add progress log every 25%
          if (percentCompleted % 25 === 0) {
            const progressLog = {
              timestamp: new Date().toISOString(),
              message: `Upload progress: ${percentCompleted}%`
            };
            setProcessingLogs(prev => {
              // Avoid duplicate progress logs
              if (prev.some(log => log.message === progressLog.message)) {
                return prev;
              }
              return [...prev, progressLog];
            });
          }
        }
      });
      
      // Stop polling
      stopPolling();
      
      // Set final logs from response if available
      if (response.data.logs) {
        setProcessingLogs(response.data.logs);
      }
      
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
      
      // Stop polling
      stopPolling();
      
      // Set final logs from error response if available
      if (error.response?.data?.logs) {
        setProcessingLogs(error.response.data.logs);
      } else {
        // Add error log if no logs from server
        const errorLog = {
          timestamp: new Date().toISOString(),
          message: `Error: ${error.message || 'Unknown error occurred during upload'}`
        };
        setProcessingLogs(prev => [...prev, errorLog]);
      }
      
      // More detailed error logging
      if (error.response) {
        console.error('Error response:', error.response.data);
        console.error('Status:', error.response.status);
      } else if (error.request) {
        console.error('No response received:', error.request);
      } else {
        console.error('Error setting up request:', error.message);
      }
      
      // Determine error message
      let errorMessage = 'Failed to upload file. Please try again.';
      
      if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.message === 'Network Error') {
        errorMessage = 'Network error. Please check your connection and try again.';
      } else if (error.message.includes('timeout')) {
        errorMessage = 'Request timed out. The file may be too large or the server is busy.';
        
        // Add timeout log
        const timeoutLog = {
          timestamp: new Date().toISOString(),
          message: 'Processing timed out. The document may still be processing in the background. Please check the documents list in a few minutes.'
        };
        setProcessingLogs(prev => [...prev, timeoutLog]);
        
        // Schedule a refresh of the documents list after a delay
        setTimeout(() => {
          fetchDocuments();
        }, 30000); // Check after 30 seconds
      }
      
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: errorMessage,
        life: 5000
      });
    } finally {
      setLoading(false);
    }
  };

  const deleteDocument = async (docId: string, title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) {
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.delete(`/api/documents/${docId}`);
      
      toast.current?.show({
        severity: 'success',
        summary: 'Success',
        detail: response.data.message,
        life: 3000
      });
      
      // Refresh documents list
      fetchDocuments();
    } catch (error: any) {
      console.error('Error deleting document:', error);
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: error.response?.data?.error || 'Failed to delete document',
        life: 3000
      });
    } finally {
      setLoading(false);
    }
  };

  const cardTitle = (
    <div className="flex items-center gap-2">
      <span>Knowledge Base Management</span>
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
      
      {showLogs && processingLogs.length > 0 && (
        <div className="mb-4">
          <Panel 
            header="Document Processing Logs" 
            toggleable 
            collapsed={false}
            className="mb-3"
            headerTemplate={(options) => {
              const toggleIcon = options.collapsed ? 'pi pi-chevron-down' : 'pi pi-chevron-up';
              return (
                <div className="flex justify-between items-center p-3">
                  <h3 className="text-lg font-semibold m-0 flex items-center">
                    <i className="pi pi-list mr-2"></i>
                    Document Processing Logs
                  </h3>
                  <div className="flex">
                    <Button 
                      icon={toggleIcon} 
                      className="p-button-rounded p-button-text p-button-sm mr-2" 
                      onClick={options.onTogglerClick}
                    />
                    <Button 
                      icon="pi pi-times" 
                      className="p-button-rounded p-button-text p-button-sm" 
                      onClick={() => setShowLogs(false)}
                      tooltip="Close Logs"
                    />
                  </div>
                </div>
              );
            }}
          >
            <ScrollPanel style={{ height: '300px' }} className="custom-scrollpanel">
              <div className="text-sm font-mono p-2">
                {processingLogs.map((log, index) => (
                  <div key={index} className="log-entry">
                    <span className="log-timestamp">
                      {new Date(log.timestamp).toLocaleTimeString()}:
                    </span>
                    <span className="log-message">{log.message}</span>
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            </ScrollPanel>
          </Panel>
        </div>
      )}
      
      {loading && (
        <div className="flex justify-center my-4">
          <ProgressSpinner style={{ width: '50px', height: '50px' }} />
        </div>
      )}
      
      {documents.length > 0 && (
        <div className="mt-4">
          <h3 className="text-lg font-semibold mb-2">Knowledge Base Documents</h3>
          <div className="flex justify-between items-center mb-2">
            <span>{documents.length} document(s) uploaded</span>
          </div>
          <ul className="list-disc pl-5">
            {documents.map((doc) => (
              <li key={doc.id} className="mb-2 flex justify-between items-center">
                <span>{doc.title}</span>
                <Button
                  icon="pi pi-trash"
                  className="p-button-sm p-button-danger p-button-text"
                  onClick={() => deleteDocument(doc.id, doc.title)}
                  tooltip="Delete document"
                />
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
};

export default DocumentUploader; 