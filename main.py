from flask import Flask, request, jsonify, render_template
import os
import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from PyPDF2 import PdfReader

app = Flask(__name__)

# Directory to store uploaded PDFs
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    """Renders the homepage with upload options."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file uploads and PDF processing."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Process the PDF and extract data
    data = extract_pdf_data(filepath)
    if data.empty:
        return jsonify({"error": "Failed to extract data from PDF"}), 500

    # Save the extracted data for visualizations
    app.config['data'] = data.to_dict(orient='records')
    return jsonify({"message": "File processed successfully"}), 200

def extract_pdf_data(filepath):
    """Extracts incident data from the uploaded PDF."""
    try:
        reader = PdfReader(filepath)
        text = ''
        for page in reader.pages:
            text += page.extract_text()

        # Parse the extracted text into structured data
        lines = text.splitlines()
        data = []
        for line in lines:
            # Custom parsing logic for the PDF structure
            if "BURGLARY" in line or "LARCENY" in line or "FORGERY" in line:  # Example keywords
                parts = line.split(' ')
                data.append({
                    "Date": parts[0],
                    "Case_Number": parts[1],
                    "Location": parts[2],
                    "Offense": ' '.join(parts[3:])
                })

        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return pd.DataFrame()

@app.route('/visualizations', methods=['GET'])
def visualizations():
    """Generates visualizations based on the extracted data."""
    data = pd.DataFrame(app.config.get('data', []))
    if data.empty:
        return jsonify({"error": "No data available"}), 400

    # Visualization 1: Clustering
    cluster_img = generate_cluster_chart(data)

    # Visualization 2: Bar Chart
    bar_img = generate_bar_chart(data)

    # Visualization 3: Custom Visualization (e.g., Offense Distribution Pie Chart)
    pie_img = generate_pie_chart(data)

    return jsonify({
        "clustering": cluster_img,
        "bar_chart": bar_img,
        "pie_chart": pie_img
    })

def generate_cluster_chart(data):
    """Clusters data based on offense types and generates a scatter plot."""
    try:
        data['Cluster'] = KMeans(n_clusters=3, random_state=42).fit_predict(
            pd.get_dummies(data['Offense'])
        )
        plt.figure()
        sns.scatterplot(data=data, x="Date", y="Location", hue="Cluster", palette="viridis")
        return save_plot_to_base64()
    except Exception as e:
        print(f"Error in clustering: {e}")
        return None

def generate_bar_chart(data):
    """Generates a bar chart of offense counts."""
    try:
        offense_counts = data['Offense'].value_counts()
        plt.figure()
        offense_counts.plot(kind='bar', color='skyblue')
        return save_plot_to_base64()
    except Exception as e:
        print(f"Error in bar chart: {e}")
        return None

def generate_pie_chart(data):
    """Generates a pie chart for offense distribution."""
    try:
        offense_counts = data['Offense'].value_counts()
        plt.figure()
        offense_counts.plot(kind='pie', autopct='%1.1f%%')
        return save_plot_to_base64()
    except Exception as e:
        print(f"Error in pie chart: {e}")
        return None

def save_plot_to_base64():
    """Saves the current plot to a base64-encoded string."""
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    base64_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return f"data:image/png;base64,{base64_img}"

if __name__ == '__main__':
    app.run(debug=True)
