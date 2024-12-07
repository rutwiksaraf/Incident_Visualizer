import pypdf
from pypdf import PdfReader
from io import BytesIO
import re

def extractIncidents(incident_data):
    file_object = BytesIO(incident_data)
    
    reader = PdfReader(file_object)
    
    incident_records = []
    
    for page in reader.pages:
        text = page.extract_text(extraction_mode="layout")
        
        rows = text.split('\n')
        
        for info in rows:
            info = info.strip()
            
            if info.startswith('Date / Time') or info.startswith('NORMAN POLICE DEPARTMENT') or info.startswith('Daily Incident Summary'):
                continue
            
            if re.match(r'^\d{1,2}/\d{1,2}/\d{4}', info):
                parts = re.split(r'\s{2,}', info)
                
                if len(parts) >= 5:  
                    incident = {
                        'Date_Time': parts[0],
                        'Incident Number': parts[1],
                        'Location': parts[2],
                        'Nature': parts[3],
                        'ORI': parts[4]
                    }
                    incident_records.append(incident)
    
    return incident_records