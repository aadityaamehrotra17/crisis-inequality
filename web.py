import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import os
import pandas as pd
import base64
import io
from PyPDF2 import PdfReader

# Initialize the Dash app
app = dash.Dash(__name__)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_text = ""
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        pdf_text += page.extract_text()
    return pdf_text

# Define the app layout
app.layout = html.Div(
    id='body',
    children=[
        html.H1('African Intellectual Traditions'),
        
        html.Label('Keywords (comma-separated)'),
        dcc.Input(
            id='keywords',
            type='text',
            placeholder='Enter keywords (comma-separated)',
            style={'width': '100%'}
        ),
        
        html.Br(), html.Br(),
        
        html.Label('Upload Files'),
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            multiple=True  # Allow multiple files to be uploaded
        ),
        
        html.Br(),
        html.Label('Chart Type'),
        dcc.RadioItems(
            id='chart-type',
            options=[
                {'label': 'Stacked Bar Chart', 'value': 'stacked_bar'},
                {'label': 'Line Plot', 'value': 'line_plot'},
                {'label': 'Heatmap', 'value': 'heatmap'},
                {'label': 'Stacked Area Plot', 'value': 'stacked_area'},
                {'label': 'Individual Bar Graphs', 'value': 'individual_bar'}
            ],
            value='stacked_bar',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
        
        html.Br(),
        dcc.Graph(id='graph-output')
    ]
)

# Callback to handle file upload, text extraction, word counting, and plotting
@app.callback(
    Output('graph-output', 'figure'),
    Input('upload-data', 'contents'),
    Input('chart-type', 'value'),
    State('upload-data', 'filename'),
    State('keywords', 'value')
)
def update_output(list_of_contents, chart_type, list_of_names, keywords):
    if list_of_contents is not None and keywords:
        dfs = []  # List to hold DataFrames for each PDF

        # Split the keywords entered by the user into a list
        words_to_count = [word.strip() for word in keywords.split(',')]

        # Process each uploaded file
        for content, name in zip(list_of_contents, list_of_names):
            # Safely handle potential decoding issues
            try:
                content_type, content_string = content.split(',')
            except ValueError:
                return {
                    'data': [],
                    'layout': {
                        'title': 'Error: Uploaded file not in expected format.'
                    }
                }

            # Decode the content
            decoded = base64.b64decode(content_string)
            pdf_file = io.BytesIO(decoded)

            # Extract text from PDF
            text = extract_text_from_pdf(pdf_file).lower()

            # Extract year from filename (first 4 characters assumed to be year)
            year = name[:4] if name[:4].isdigit() else 'Unknown'

            # Count occurrences of each word
            word_counts = {word: text.count(word) for word in words_to_count}

            # Convert word counts to DataFrame
            df = pd.DataFrame(list(word_counts.items()), columns=['Word', 'Count'])
            df['File'] = name  # Add filename
            df['Year'] = year  # Add extracted year
            
            # Append DataFrame to list
            dfs.append(df)

        # Combine all DataFrames into one
        combined_df = pd.concat(dfs)
        combined_df['Year'] = combined_df['Year'].astype(str)  # Ensure Year is treated as string

        # Generate plot based on chart type
        if chart_type == 'stacked_bar':
            figure = {
                'data': [
                    {
                        'x': combined_df['Year'],
                        'y': combined_df.groupby('Year')['Count'].sum(),
                        'type': 'bar',
                        'name': 'Stacked Bar'
                    }
                ],
                'layout': {
                    'title': 'Stacked Bar Chart of Word Counts'
                }
            }
        elif chart_type == 'line_plot':
            figure = {
                'data': [
                    {
                        'x': combined_df['Year'],
                        'y': combined_df.groupby('Year')['Count'].sum(),
                        'type': 'line',
                        'name': 'Line Plot'
                    }
                ],
                'layout': {
                    'title': 'Line Plot of Word Counts'
                }
            }
        elif chart_type == 'heatmap':
            pivot_df = combined_df.pivot_table(index='Word', columns='Year', values='Count', fill_value=0)
            figure = {
                'data': [
                    {
                        'z': pivot_df.values,
                        'x': pivot_df.columns,
                        'y': pivot_df.index,
                        'type': 'heatmap',
                        'name': 'Heatmap'
                    }
                ],
                'layout': {
                    'title': 'Heatmap of Word Counts'
                }
            }
        elif chart_type == 'stacked_area':
            figure = {
                'data': [
                    {
                        'x': combined_df['Year'],
                        'y': combined_df.groupby('Year')['Count'].sum(),
                        'type': 'scatter',
                        'mode': 'lines',
                        'fill': 'tonexty',
                        'name': 'Stacked Area Plot'
                    }
                ],
                'layout': {
                    'title': 'Stacked Area Plot of Word Counts'
                }
            }
        else:  # Individual Bar Graphs
            figure = {
                'data': [
                    {
                        'x': combined_df['Word'],
                        'y': combined_df['Count'],
                        'type': 'bar',
                        'name': 'Individual Bar Graphs'
                    }
                ],
                'layout': {
                    'title': 'Individual Bar Graphs of Word Counts'
                }
            }

        return figure

    return {}

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
