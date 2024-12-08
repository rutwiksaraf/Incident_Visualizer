import pandas as pd
import traceback
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.layouts import column

def create_visualizations(incidents):

    try:
        df = pd.DataFrame(incidents)

        print("Incidents DataFrame:")
        print(df.head())
        print("\nDataFrame Columns:", df.columns.tolist())

        df['Date_Time'] = pd.to_datetime(df['Date_Time'], format='%m/%d/%Y %H:%M', errors='coerce')
        df = df.dropna(subset=['Date_Time'])

        if df.empty:
            raise ValueError("No valid incident data to display after parsing.")

        if 'Nature' not in df.columns:
            raise ValueError("'Nature' column is missing from the data.")
        
        df['Nature'] = df['Nature'].fillna('Unknown').str.strip().str.lower()

        unique_natures = df['Nature'].unique()
        print("Unique Incident Types:", unique_natures)

        if len(unique_natures) < 2:
            return _create_fallback_visualization(df)

        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(df['Nature'])
        
        
        n_clusters = min(4, len(unique_natures))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(X)

        
        pca = PCA(n_components=2)
        coords = pca.fit_transform(X.toarray())
        df['cluster'] = labels
        df['x'] = coords[:, 0]
        df['y'] = coords[:, 1]

        
        palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"][:n_clusters]  # Custom color palette
        df['color'] = [palette[i] for i in df['cluster']]

        
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
            color='#8A2BE2',  
            legend_label="Incidents"
        )
        time_plot.circle(
            x='Date',
            y='Count',
            source=source_date,
            fill_color="white",
            size=8,
            color='#8A2BE2' 
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

        layout = column(cluster_plot, bar_plot, time_plot, sizing_mode='stretch_width')
        script, div = components(layout)

        return script, div

    except Exception as e:
        print("Full Error Traceback:")
        traceback.print_exc()
        
        raise ValueError(f"Visualization generation failed: {str(e)}")

def _create_fallback_visualization(df):

    df['Date'] = df['Date_Time'].dt.date
    date_counts = df.groupby('Date').size().reset_index(name='Count')
    date_counts = date_counts.sort_values('Date')
    date_counts['Date'] = pd.to_datetime(date_counts['Date'])
    source_date = ColumnDataSource(date_counts)
    
    time_plot = figure(
        x_axis_type="datetime",
        title="Incidents Over Time (Single Type)",
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
        color='#8A2BE2',  
        legend_label="Incidents"
    )
    time_plot.circle(
        x='Date',
        y='Count',
        source=source_date,
        fill_color="white",
        size=8,
        color='#8A2BE2'  
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

    nature_counts = df['Nature'].value_counts().reset_index()
    nature_counts.columns = ['Nature', 'Count']
    source_nature = ColumnDataSource(nature_counts)
    
    bar_plot = figure(
        x_range=nature_counts['Nature'],
        title="Incident Count by Nature (Limited Types)",
        sizing_mode='stretch_width',
        height=400,
        tools="pan,wheel_zoom,box_zoom,reset,hover,save",
        margin=(50, 50, 50, 50)
    )
    bar_plot.vbar(
        x='Nature',
        top='Count',
        width=0.9,
        source=source_nature,
        line_color='white',
        fill_color='#FF6347'  # Tomato color
    )
    bar_plot.xaxis.major_label_orientation = 1.2
    bar_plot.y_range.start = 0
    bar_plot.add_tools(HoverTool(tooltips=[("Nature", "@Nature"), ("Count", "@Count")]))

    # Combine plots
    layout = column(time_plot, bar_plot, sizing_mode='stretch_width')
    script, div = components(layout)

    return script, div