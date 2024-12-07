from flask import Flask, request, render_template, redirect, url_for, session
import os
import pandas as pd
from fetch_indcidents import fetchIncidents
from extract_incidents import extractIncidents
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Category10
from bokeh.layouts import column
from datetime import datetime
from urllib.error import HTTPError, URLError
import io

app = Flask(__name__)
app.secret_key = "rutwiksaraf3" 

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        urls = request.form.get('urls', '').strip()
        files = request.files.getlist('files')

        incidents = []
        errors = []

        # If URLs are provided
        if urls:
            for url in urls.split():
                try:
                    data = fetchIncidents(url)
                    inc = extractIncidents(data)
                    incidents.extend(inc)
                except HTTPError as e:
                    error_msg = f"HTTP Error {e.code} for URL: {url}"
                    errors.append(error_msg)
                except URLError as e:
                    error_msg = f"URL Error for URL: {url} - {e.reason}"
                    errors.append(error_msg)
                except Exception as e:
                    error_msg = f"Error fetching from URL: {url} - {str(e)}"
                    errors.append(error_msg)

        # If files are provided
        for f in files:
            if f and f.filename.lower().endswith('.pdf'):
                pdf_data = f.read()
                inc = extractIncidents(pdf_data)
                incidents.extend(inc)

        if len(incidents) == 0:
            error_message = "No incidents found or invalid input."
            if errors:
                error_message += " Errors: " + "; ".join(errors)
            return render_template('index.html', error=error_message)

        # Store incidents in session for later use
        session['incidents_data'] = incidents
        return redirect(url_for('visuals'))
    return render_template('index.html')

@app.route('/visuals', methods=['GET', 'POST'])
def visuals():
    # Retrieve incidents data from session
    incidents = session.get('incidents_data', [])
    if not incidents:
        return redirect(url_for('index'))

    df = pd.DataFrame(incidents)

    # Ensure Date_Time is parsed correctly
    df['Date_Time'] = pd.to_datetime(df['Date_Time'], format='%m/%d/%Y %H:%M', errors='coerce')
    df = df.dropna(subset=['Date_Time'])

    if df.empty:
        return render_template('visuals.html', error="No valid incident data to display.")

    try:
        # Vectorize the 'Nature' column (incident type) using TF-IDF
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(df['Nature'])
        kmeans = KMeans(n_clusters=4, random_state=42)
        labels = kmeans.fit_predict(X)

        # Use PCA to reduce to 2D for plotting
        pca = PCA(n_components=2)
        coords = pca.fit_transform(X.toarray())
        df['cluster'] = labels
        df['x'] = coords[:, 0]
        df['y'] = coords[:, 1]

        # Assign new colors based on cluster
        palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]  # Custom color palette
        df['color'] = [palette[i] for i in df['cluster']]

        # Create Bokeh clustering plot
        source_cluster = ColumnDataSource(df)
        cluster_plot = figure(
            title="Clustering of Incidents by Nature",
            sizing_mode='stretch_width',
            height=600,
            tools="pan,wheel_zoom,box_zoom,reset,hover,save",
            margin=(50, 50, 50, 50)
        )
        cluster_plot.scatter(
            'x', 'y', source=source_cluster, color='color', legend_field='cluster', size=8
        )
        cluster_plot.add_tools(HoverTool(tooltips=[("Nature", "@Nature"), ("Cluster", "@cluster")]))
        cluster_plot.legend.title = 'Cluster'
        cluster_plot.legend.location = "top_left"

        # Create Bokeh bar plot for incident types
        top_n = 10
        nature_counts = df['Nature'].value_counts().nlargest(top_n).reset_index()
        nature_counts.columns = ['Nature', 'Count']
        source_nature = ColumnDataSource(nature_counts)
        bar_plot = figure(
            x_range=nature_counts['Nature'],
            title="Incident Count by Nature",
            sizing_mode='stretch_width',
            height=600,
            tools="pan,wheel_zoom,box_zoom,reset,hover,save",
            margin=(50, 50, 50, 50)
        )
        bar_plot.vbar(
            x='Nature',
            top='Count',
            width=0.9,
            source=source_nature,
            legend_field="Nature",
            line_color='white',
            fill_color='#FF6347'  # Change to Tomato color
        )
        bar_plot.xaxis.major_label_orientation = 1.2
        bar_plot.y_range.start = 0
        bar_plot.add_tools(HoverTool(tooltips=[("Nature", "@Nature"), ("Count", "@Count")]))
        bar_plot.legend.visible = False

        # Create Bokeh time-series plot
        df['Date'] = df['Date_Time'].dt.date
        date_counts = df.groupby('Date').size().reset_index(name='Count')
        date_counts = date_counts.sort_values('Date')
        date_counts['Date'] = pd.to_datetime(date_counts['Date'])
        source_date = ColumnDataSource(date_counts)
        time_plot = figure(
            x_axis_type="datetime",
            title="Incidents Over Time",
            sizing_mode='stretch_width',
            height=600,
            tools="pan,wheel_zoom,box_zoom,reset,hover,save",
            margin=(50, 50, 50, 50)
        )
        time_plot.line(
            x='Date',
            y='Count',
            source=source_date,
            line_width=2,
            color='#8A2BE2',  # Change to BlueViolet color
            legend_label="Incidents"
        )
        time_plot.circle(
            x='Date',
            y='Count',
            source=source_date,
            fill_color="white",
            size=8,
            color='#8A2BE2'  # Change to BlueViolet color
        )
        time_plot.xaxis.axis_label = "Date"
        time_plot.yaxis.axis_label = "Number of Incidents"
        time_plot.add_tools(
            HoverTool(
                tooltips=[("Date", "@Date{%F}"), ("Count", "@Count")],
                formatters={'@Date': 'datetime'},
                mode='vline'
            )
        )
        time_plot.legend.location = "top_left"

        # Combine plots into a layout
        layout = column(cluster_plot, bar_plot, time_plot, sizing_mode='stretch_width')
        script, div = components(layout)

    except Exception as e:
        print(f"Error creating visualizations: {e}")
        return render_template('visuals.html', error="An error occurred while generating visualizations.")

    if request.method == 'POST':
        feedback = request.form.get('feedback')
        if feedback:
            print("User Feedback:", feedback)
            feedback_submitted = True
            return render_template('visuals.html', script=script, div=div, feedback_submitted=feedback_submitted)

    return render_template('visuals.html', script=script, div=div, feedback_submitted=False)

if __name__ == '__main__':
    app.run(debug=True)
