from flask import Blueprint, jsonify, request, send_file, make_response
import json
import csv
import io
from fpdf import FPDF
import os
import sys
from datetime import datetime
from io import BytesIO

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    """
    Export conversation to PDF
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Set up fonts
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Conversation Export", ln=True, align="C")
    pdf.ln(10)
    
    # Add timestamp
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(10)
    
    # Add conversation
    pdf.set_font("Arial", "", 12)
    
    for message in conversation:
        # Add role as header
        role = message.get("role", "unknown").capitalize()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"{role}:", ln=True)
        
        # Add content with word wrapping
        pdf.set_font("Arial", "", 12)
        content = message.get("content", "")
        
        # Simple word wrapping
        words = content.split()
        line = ""
        for word in words:
            test_line = line + " " + word if line else word
            if pdf.get_string_width(test_line) > pdf.w - 20:  # 20 is margin
                pdf.multi_cell(0, 10, line)
                line = word
            else:
                line = test_line
        
        if line:
            pdf.multi_cell(0, 10, line)
        
        pdf.ln(5)
    
    # Create BytesIO object
    memory_file = BytesIO()
    
    # Save PDF to BytesIO object
    pdf.output(dest='S').encode('latin-1')
    memory_file.write(pdf.output(dest='S').encode('latin-1'))
    memory_file.seek(0)
    
    # Create response
    response = make_response(memory_file.getvalue())
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', f'attachment; filename={filename}')
    
    return response 