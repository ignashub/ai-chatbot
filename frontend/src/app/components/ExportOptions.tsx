import React, { useState, useRef } from 'react';
import { Button } from 'primereact/button';
import { Menu } from 'primereact/menu';
import { Toast } from 'primereact/toast';
import { MenuItem } from 'primereact/menuitem';

interface ExportOptionsProps {
  conversation: any[];
  isDisabled?: boolean;
}

const ExportOptions: React.FC<ExportOptionsProps> = ({ conversation, isDisabled = false }) => {
  const [isExporting, setIsExporting] = useState(false);
  const menuRef = useRef<Menu>(null);
  const toast = useRef<Toast>(null);

  const handleExport = async (format: 'json' | 'csv' | 'pdf') => {
    if (conversation.length === 0) {
      toast.current?.show({
        severity: 'warn',
        summary: 'No data to export',
        detail: 'Start a conversation first before exporting.',
        life: 3000,
      });
      return;
    }

    setIsExporting(true);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/export/conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation,
          format,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to export conversation');
      }

      // Get the blob from the response
      const blob = await response.blob();
      
      // Create a URL for the blob
      const url = window.URL.createObjectURL(blob);
      
      // Create a temporary anchor element and trigger download
      const a = document.createElement('a');
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      a.href = url;
      a.download = `conversation_${timestamp}.${format}`;
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.current?.show({
        severity: 'success',
        summary: 'Export successful',
        detail: `Your conversation has been exported as ${format.toUpperCase()}.`,
        life: 3000,
      });
    } catch (error) {
      console.error('Export error:', error);
      toast.current?.show({
        severity: 'error',
        summary: 'Export failed',
        detail: 'There was an error exporting your conversation.',
        life: 3000,
      });
    } finally {
      setIsExporting(false);
    }
  };

  const items: MenuItem[] = [
    {
      label: 'Export as JSON',
      icon: 'pi pi-file',
      command: () => handleExport('json')
    },
    {
      label: 'Export as CSV',
      icon: 'pi pi-file-excel',
      command: () => handleExport('csv')
    },
    {
      label: 'Export as PDF',
      icon: 'pi pi-file-pdf',
      command: () => handleExport('pdf')
    }
  ];

  return (
    <>
      <Toast ref={toast} />
      <Menu model={items} popup ref={menuRef} />
      <Button 
        label={isExporting ? 'Exporting...' : 'Export'} 
        icon="pi pi-download" 
        disabled={isDisabled || isExporting}
        onClick={(e) => menuRef.current?.toggle(e)}
        className="p-button-outlined"
      />
    </>
  );
};

export default ExportOptions; 