import dash
import chardet
from pathlib import Path
from dash import Dash, html, dash_table, dcc
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.express as px

data_breaches_df = pd.read_excel(
    './data/IIB Data Breaches - Cleaned - Ver2.xlsx', engine='openpyxl')

# Ensure 'records lost' are cleaned and converted to integers
data_breaches_df['records lost'] = data_breaches_df['records lost'].replace(
    r'[^\d]', '', regex=True).astype(int)

# Ensure that there are no spaces on the end of the values for the "Method"
data_breaches_df['method'] = data_breaches_df['method'].str.rstrip()

# Ensure that there are no spaces on the end of the values for the "Sector"
data_breaches_df['sector'] = data_breaches_df['sector'].str.rstrip()

# Ensure that there are no space on the end of "year" column
data_breaches_df.rename(columns={'year   ': 'year'}, inplace=True)

# Get unique values for dropdown options
years = data_breaches_df['year'].unique()
organisations = data_breaches_df['organisation'].unique()
sectors = data_breaches_df['sector'].unique()
methods = data_breaches_df['method'].unique()

# Initialize the Dash App
external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css', './assets/styles.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([

    # Visualization for Data Breaches Analysis Dashboard
    html.H1("Data Breaches Analysis Dashboard"),

    html.Div([
        dcc.Dropdown(
            id='analysis-type',
            options=[
                {'label': 'Sector Analysis', 'value': 'sector'},
                {'label': 'Method Analysis', 'value': 'method'},
                {'label': 'Data Sensitivity Analysis', 'value': 'data_sensitivity'},
                {'label': 'Yearly Trends', 'value': 'yearly_trends'},
                {'label': 'Records Lost Analysis', 'value': 'records_lost'},
            ],
            value='sector'
        )
    ], style={'margin-bottom': '20px'}),

    html.Div([
        html.Div([
            dcc.Dropdown(
                id='year-filter',
                options=[{'label': year, 'value': year} for year in years],
                multi=True,
                placeholder='Select Year(s)'
            )
        ], style={'width': '24%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='organisation-filter',
                options=[{'label': organisation, 'value': organisation}
                         for organisation in organisations],
                multi=True,
                placeholder='Select Organisation(s)'
            )
        ], style={'width': '24%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='sector-filter',
                options=[{'label': sector, 'value': sector}
                         for sector in sectors],
                multi=True,
                placeholder='Select Sector(s)'
            )
        ], style={'width': '24%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='method-filter',
                options=[{'label': method, 'value': method}
                         for method in methods],
                multi=True,
                placeholder='Select Method(s)'
            )
        ], style={'width': '24%', 'display': 'inline-block'})
    ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-bottom': '20px'}),

    html.Div([
        dcc.Graph(id='graph-output')
    ], className='graph-container'),

    # Visualization for Top 5 Organizations
    html.H2("Top 5 Organizations with Most Records Lost"),
    html.Div([
        dcc.Dropdown(
            id='top-5-year-filter',
            options=[{'label': year, 'value': year} for year in years],
            multi=True,
            placeholder='Select Year(s)'
        ),
        dcc.Graph(id='top-5-graph-output')
    ], className='graph-container'),

    # New visualization for number of breaches by year for specific sectors
    html.H2("Number of Breaches by Year for Specific Sectors (2020-2024)"),
    html.Div([
        dcc.Graph(id='sectors-year-graph-output')
    ], className='graph-container'),

    # New visualization for percentages of most used method
    html.H2("Percentages of most used methods"),
    html.Div([
        dcc.Graph(id='methods-donut-chart-output')
    ], className='graph-container'),

])

# Define the callbacks to update the graphs based on the selected analysis type


@app.callback(
    [Output('graph-output', 'figure'), Output('top-5-graph-output', 'figure')],
    [Input('analysis-type', 'value'),
     Input('year-filter', 'value'),
     Input('organisation-filter', 'value'),
     Input('sector-filter', 'value'),
     Input('method-filter', 'value'),
     Input('top-5-year-filter', 'value')]
)
def update_graph(selected_analysis, selected_years, selected_organisations, selected_sectors, selected_methods, selected_top5_years):
    # Filter the DataFrame based on the selected filters
    df = data_breaches_df

    # Apply filters if they are not empty or None
    if selected_years:
        df = df[df['year'].isin(selected_years)]
    if selected_organisations:
        df = df[df['organisation'].isin(selected_organisations)]
    if selected_sectors:
        df = df[df['sector'].isin(selected_sectors)]
    if selected_methods:
        df = df[df['method'].isin(selected_methods)]

    # Initialize fig to an empty figure
    fig = {}

    # Data Visualization

    # Visualization for Sector
    if selected_analysis == 'sector':
        sector_counts = df['sector'].value_counts()
        if not sector_counts.empty:
            fig = px.bar(
                x=sector_counts.index,
                y=sector_counts.values,
                labels={'x': 'Sector', 'y': 'Number of Breaches'},
                title='Number of Data Breaches per Sector',
                color=sector_counts.index,  # Color bars by sector
                hover_data={'Sector': sector_counts.index,
                            'Number of Breaches': sector_counts.values}
            )
        else:
            fig = px.bar(title='No data available for the selected filters')

    # Visualization for Method
    elif selected_analysis == 'method':
        method_counts = df['method'].value_counts()

        # Aggregate sector information for each method
        sector_info = (
            df.groupby('method')['sector']
            .apply(lambda x: ', '.join(x.unique()))
            .reindex(method_counts.index)
        ).reset_index()

        if not method_counts.empty:
            fig = px.bar(
                x=method_counts.index,
                y=method_counts.values,
                labels={'x': 'Method', 'y': 'Number of Breaches'},
                title='Number of Data Breaches per Method',
                color=method_counts.index,  # Color bars by method
                hover_data={'Method': method_counts.index,
                            'Number of Breaches': method_counts.values, 'Sector': sector_info['sector']}
            )
        else:
            fig = px.bar(title='No data available for the selected filters')

    # Visualization for Data Sensitivity
    elif selected_analysis == 'data_sensitivity':
        sensitivity_counts = df['data sensitivity'].value_counts()
        if not sensitivity_counts.empty:
            fig = px.bar(
                x=sensitivity_counts.index,
                y=sensitivity_counts.values,
                labels={'x': 'Data Sensitivity', 'y': 'Number of Breaches'},
                title='Number of Data Breaches by Data Sensitivity',
                color=sensitivity_counts.index,  # Color bars by data sensitivity
                hover_data={'Data Sensitivity': sensitivity_counts.index,
                            'Number of Breaches': sensitivity_counts.values}
            )
        else:
            fig = px.bar(title='No data available for the selected filters')

    # Visualization for Yearly Trends of data breaches
    elif selected_analysis == 'yearly_trends':
        yearly_trends = df['year'].value_counts().sort_index()
        if not yearly_trends.empty:
            fig = px.line(
                x=yearly_trends.index,
                y=yearly_trends.values,
                labels={'x': 'Year', 'y': 'Number of Breaches'},
                title='Number of Data Breaches Over the Years'
            )
        else:
            fig = px.line(title='No data available for the selected filters')

    # Visualization for Record Lost
    elif selected_analysis == 'records_lost':
        if not df.empty:
            fig = px.histogram(
                df,
                x='records lost',
                nbins=20,
                labels={'x': 'Records Lost', 'y': 'Frequency'},
                title='Distribution of Records Lost in Data Breaches',
                color=df['sector']  # Color bars by sector
            )
        else:
            fig = px.histogram(
                title='No data available for the selected filters')

    # Top 5 organizations graph
    filtered_top5_df = data_breaches_df.copy()
    if selected_top5_years:
        filtered_top5_df = filtered_top5_df[filtered_top5_df['year'].isin(
            selected_top5_years)]
    top5_records_by_org = filtered_top5_df.groupby(
        'organisation')['records lost'].sum().nlargest(5).reset_index()
    if not top5_records_by_org.empty:
        fig_top5 = px.bar(
            top5_records_by_org,
            x='organisation',
            y='records lost',
            labels={'organisation': 'Organization',
                    'records lost': 'Records Lost'},
            title='Top 5 Organizations with Most Records Lost',
            color='organisation'  # Color bars by organization
        )
    else:
        fig_top5 = px.bar(title='No data available for the selected filters')

    return fig, fig_top5

# Define the callback for the new visualization


@app.callback(
    Output('sectors-year-graph-output', 'figure'),
    Input('top-5-year-filter', 'value')  # Using this input to refresh graph
)
def update_sectors_year_graph(selected_years):
    specific_years = [2020, 2021, 2022, 2023, 2024]
    sectors = ['web', 'government', 'finance', 'health']
    filtered_df = data_breaches_df[(data_breaches_df['sector'].isin(
        sectors)) & (data_breaches_df['year'].isin(specific_years))]

    fig = px.histogram(
        filtered_df,
        x='year',
        color='sector',
        barmode='group',
        labels={'year': 'Year', 'count': 'Number of Breaches', 'sector': 'Sector'},
        title='Number of Breaches by Year for Specific Sectors (2020-2024)'
    )

    return fig


# Define the callback for the new visualization
@app.callback(
    Output('methods-donut-chart-output', 'figure'),
    Input('top-5-year-filter', 'value')  # Using this input to refresh graph
)
def update_methods_donut_chart(selected_years):
    specific_methods = ['hacked', 'poor security',
                        'lost device', 'oops!', 'inside job']
    filtered_methods_df = data_breaches_df[data_breaches_df['method'].isin(
        specific_methods)]

    # Calculate the counts and percentages of each method:
    method_counts = filtered_methods_df['method'].value_counts().reset_index()
    method_counts.columns = ['method', 'count']
    method_counts['percentage'] = (
        method_counts['count'] / method_counts['count'].sum() * 100)

    fig_donut = px.pie(
        method_counts,
        names='method',
        values='count',
        hole=0.3,  # This makes it a donut chart
        labels={'method': 'Method', 'count': 'Count'},
        title='Percentages of Most Used Methods'
    )
    fig_donut.update_traces(textinfo='percent+label')

    return fig_donut


if __name__ == '__main__':
    # Turn off reloader if inside Jupyter
    app.run(debug=True, use_reloader=False, jupyter_mode="tab")
