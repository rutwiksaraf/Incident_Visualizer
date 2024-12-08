import pandas as pd

def handle_dates(df):
    df['Date_Time'] = pd.to_datetime(df['Date_Time'], format='%m/%d/%Y %H:%M', errors='coerce')
    df = df.dropna(subset=['Date_Time'])
    return df
