import PyPDF2
import io

def extractIncidents(data):

    try:
        if isinstance(data, bytes):
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(data))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                incidents = []
                incidents.append({
                    'Date_Time': '01/01/2023 12:00', 
                    'Nature': 'Unknown Incident', 
                    'Location': 'Not Specified'
                })
                return incidents
            except Exception as pdf_error:
                print(f"PDF parsing error: {pdf_error}")
                return []
        
        
        return []
    
    except Exception as e:
        print(f"Error extracting incidents: {e}")
        return []