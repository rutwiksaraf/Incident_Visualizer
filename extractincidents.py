import pypdf
from pypdf import PdfReader
from io import BytesIO
import re

def extractIncidents(incident_data):
    # Create a file-like object from the binary data
    file_object = BytesIO(incident_data)
    
    # Initialize a PDF reader object using PyPDF
    reader = PdfReader(file_object)
    
    # Prepare an empty list to store incident records
    incident_records = []
    
    # Iterate through each page in the PDF document
    for page in reader.pages:
        # Extract text from the current page using the layout mode
        text = page.extract_text(extraction_mode="layout")
        
        # Split the text into rows by new lines
        rows = text.split('\n')
        
        # Iterate over each row in the current page
        for info in rows:
            # Strip any leading or trailing whitespace from the row
            info = info.strip()
            
            # Skip headers or irrelevant rows
            if info.startswith('Date / Time') or info.startswith('NORMAN POLICE DEPARTMENT') or info.startswith('Daily Incident Summary'):
                continue
            
            # Check if the row starts with a date in the specified format
            if re.match(r'^\d{1,2}/\d{1,2}/\d{4}', info):
                # Split the row into parts based on two or more consecutive spaces
                parts = re.split(r'\s{2,}', info)
                
                if len(parts) >= 5:  
                    incident = {
                        'Date_Time': parts[0],
                        'Incident Number': parts[1],
                        'Location': parts[2],
                        'Nature': parts[3],
                        'ORI': parts[4]
                    }
                    # Append the incident dictionary to the records list
                    incident_records.append(incident)
    
    # Return the list of incident records
    return incident_records