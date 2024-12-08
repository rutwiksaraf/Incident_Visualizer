from flask import Flask, request, render_template, redirect, url_for, session
import pandas as pd
import traceback
from urllib.error import HTTPError, URLError

from fetch_incidents import fetchIncidents
from extract_incidents import extractIncidents
from data_visualizer import create_visualizations

app = Flask(__name__)
app.secret_key = "rutwiksaraf3"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        urls = request.form.get('urls', '').strip()
        files = request.files.getlist('files')

        incidents = []
        errors = []

        if urls:
            for url in urls.split():
                try:
                    data = fetchIncidents(url)
                    inc = extractIncidents(data)
                    incidents.extend(inc)
                except (HTTPError, URLError) as e:
                    errors.append(f"Error fetching URL {url}: {e}")
                except Exception as e:
                    errors.append(f"General error fetching URL {url}: {e}")

        for f in files:
            if f and f.filename.lower().endswith('.pdf'):
                pdf_data = f.read()
                try:
                    inc = extractIncidents(pdf_data)
                    incidents.extend(inc)
                except Exception as e:
                    errors.append(f"Error processing file {f.filename}: {e}")

        if not incidents:
            error_message = "No incidents found or invalid input."
            if errors:
                error_message += f" Errors: {'; '.join(errors)}"
            return render_template('index.html', error=error_message)

        session['incidents_data'] = incidents
        return redirect(url_for('visuals'))

    return render_template('index.html')


@app.route('/visuals', methods=['GET', 'POST'])
def visuals():
    incidents = session.get('incidents_data', [])
    if not incidents:
        return redirect(url_for('index'))

    try:
        script, div = create_visualizations(incidents)
        if not script or not div:
            raise ValueError("Failed to generate visualizations.")
    except Exception as e:
        print("Visualization Error Traceback:")
        traceback.print_exc()
        return render_template('visuals.html', error=str(e))

    return render_template('visuals.html', script=script, div=div)


if __name__ == '__main__':
    app.run(debug=True)
