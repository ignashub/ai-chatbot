from flask import Blueprint, jsonify, request, send_file
import json
import csv
import io
from fpdf import FPDF
import os
from datetime import datetime

export_bp = Blueprint('export', __name__)

@export_bp.route('/conversation', methods=['POST'])
def export_conversation():
    """Export conversation data in the requested format (PDF, CSV, JSON)"""
    data = request.json
    conversation = data.get('conversation', [])
    format_type = data.get('format', 'json')
    
    if not conversation:
        return jsonify({"error": "No conversation data provided"}), 400
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversation_{timestamp}"
    
    if format_type == 'json':
        return export_json(conversation, filename)
    elif format_type == 'csv':
        return export_csv(conversation, filename)
    elif format_type == 'pdf':
        return export_pdf(conversation, filename)
    else:
        return jsonify({"error": "Unsupported format"}), 400

def export_json(conversation, filename):
    """Export conversation as JSON file"""
    memory_file = io.BytesIO()
    memory_file.write(json.dumps(conversation, indent=2).encode('utf-8'))
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        as_attachment=True,
        download_name=f"{filename}.json",
        mimetype='application/json'
    )

def export_csv(conversation, filename):
    """Export conversation as CSV file"""
    memory_file = io.StringIO()
    writer = csv.writer(memory_file)
    
    # Write header
    writer.writerow(['Role', 'Content', 'Timestamp'])
    
    # Write conversation data
    for message in conversation:
        writer.writerow([
            message.get('role', ''),
            message.get('content', ''),
            message.get('timestamp', '')
        ])
    
    memory_file.seek(0)
    
    return send_file(
        io.BytesIO(memory_file.getvalue().encode('utf-8')),
        as_attachment=True,
        download_name=f"{filename}.csv",
        mimetype='text/csv'
    )

def export_pdf(conversation, filename):
    """Export conversation as PDF file"""
    pdf = FPDF()
    pdf.add_page()
    
    # Set font
    pdf.set_font("Arial", size=12)
    
    # Add title
    pdf.cell(200, 10, txt="Conversation Export", ln=True, align='C')
    pdf.ln(10)
    
    # Add conversation content
    for message in conversation:
        role = message.get('role', '')
        content = message.get('content', '')
        timestamp = message.get('timestamp', '')
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"{role.capitalize()} ({timestamp})", ln=True)
        
        pdf.set_font("Arial", size=10)
        # Handle multi-line content
        pdf.multi_cell(0, 10, txt=content)
        pdf.ln(5)
    
    memory_file = io.BytesIO()
    pdf.output(memory_file)
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        as_attachment=True,
        download_name=f"{filename}.pdf",
        mimetype='application/pdf'
    ) 