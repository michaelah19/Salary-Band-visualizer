import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import numpy as np
import plotly.figure_factory as ff

# Load CSV file
df = pd.read_csv('Salary_Numbers.csv')


# Data Cleaning: Remove $ and convert columns to integers
def clean_currency(column):
    return pd.to_numeric(df[column].replace({'\$': '', ',': ''}, regex = True))


df['New Base'] = clean_currency('New Base')
df['Unvested RSUs'] = clean_currency('Unvested RSUs')
df['Bonus'] = clean_currency('Bonus')

# Create the TC (Total Compensation) column
df['TC'] = df['New Base'] + df['Unvested RSUs'] / 4 + df['Bonus']

# Normalize Location and New Level names (remove caps, then title-case)
df['Location'] = df['Location'].str.lower().str.title()
df['New Level'] = df['New Level'].str.lower().str.title()

# Sort New Level and Location columns
df = df.sort_values(by = ['New Level', 'Location'])

# Round YoE to remove decimals
df['Total YoE'] = df['Total YoE'].round(0)

# Initialize the Dash app
app = dash.Dash(__name__)

# Apply full browser page CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            html, body, #root, .container { height: 100%; width: 100%; margin: 0; padding: 0; }
            #root, .container { display: flex; flex-direction: column; }
        </style>
    </head>
    <body>
        <div class="container">
            {%app_entry%}
        </div>
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Define the layout with full-height flexbox settings
app.layout = html.Div(style = {'backgroundColor': '#2d2d2d', 'color': '#f8f8f2', 'display': 'flex', 'flexGrow': '1', 'height': '100vh'},
                      children = [
    
                          # Left column for the plots
                          html.Div(style = {'flexGrow': '1', 'display': 'flex', 'flexDirection': 'column', 'height': '100vh'}, children = [
                              dcc.Graph(id = 'top-plot', style = {'flexGrow': '1'}),
                              dcc.Graph(id = 'boxplot-plot', style = {'flexGrow': '1'})
                          ]),
    
                          # Right column for the dropdowns/filters and table
                          html.Div(style = {'width': '30%', 'padding': '10px', 'overflowY': 'auto'}, children = [
                              html.H2("Filters",
                                      style = {'color': '#f8f8f2', 'textAlign': 'center', 'fontSize': '24px'}),
        
                              # Dropdown to toggle between Plot Types
                              html.Div(style = {'marginBottom': '20px'}, children = [
                                  html.Label('Select Plot Type:', style = {'color': '#f8f8f2', 'fontSize': '18px'}),
                                  dcc.Dropdown(
                                      id = 'plot-type-dropdown',
                                      options = [
                                          {'label': 'Histogram', 'value': 'histogram'},
                                          {'label': 'Bar Plot', 'value': 'barplot'},
                                          {'label': 'Normal Curve', 'value': 'normal_curve'},
                                          {'label': 'Dist Plot (Normal)', 'value': 'distplot_normal'}
                                      ],
                                      value = 'histogram',  # Default is Histogram
                                      placeholder = "Select Plot Type",
                                      style = {'backgroundColor': '#2d2d2d', 'color': '#f8f8f2',
                                               'border': '1px solid #444', 'fontSize': '16px'}
                                  ),
                              ]),
        
                              # Dropdown for filtering by New Level
                              html.Div(style = {'marginBottom': '20px'}, children = [
                                  html.Label('Select New Level:', style = {'color': '#f8f8f2', 'fontSize': '18px'}),
                                  dcc.Dropdown(
                                      id = 'new-level-dropdown',
                                      options = [{'label': level, 'value': level} for level in
                                                 df['New Level'].unique()],
                                      value = None,
                                      multi = True,
                                      placeholder = "Filter by New Level",
                                      style = {'backgroundColor': '#2d2d2d', 'color': '#f8f8f2',
                                               'border': '1px solid #444', 'fontSize': '16px'}
                                  ),
                              ]),
        
                              # Dropdown for filtering by Location
                              html.Div(style = {'marginBottom': '20px'}, children = [
                                  html.Label('Select Location:', style = {'color': '#f8f8f2', 'fontSize': '18px'}),
                                  dcc.Dropdown(
                                      id = 'location-dropdown',
                                      options = [{'label': loc, 'value': loc} for loc in df['Location'].unique()],
                                      value = None,
                                      multi = True,
                                      placeholder = "Filter by Location",
                                      style = {'backgroundColor': '#2d2d2d', 'color': '#f8f8f2',
                                               'border': '1px solid #444', 'fontSize': '16px'}
                                  ),
                              ]),
        
                              # Number scroll for filtering by Years of Experience (YoE)
                              html.Div(style = {'marginBottom': '20px'}, children = [
                                  html.Label('Filter by Years of Experience:',
                                             style = {'color': '#f8f8f2', 'fontSize': '18px', 'marginBottom': '10px'}),
                                  dcc.Slider(
                                      id = 'yoe-slider',
                                      min = int(df['Total YoE'].min()),
                                      max = int(df['Total YoE'].max()),
                                      step = 1,
                                      value = int(df['Total YoE'].max()),  # Default to max YoE
                                      marks = {i: str(i) for i in
                                               range(int(df['Total YoE'].min()), int(df['Total YoE'].max()) + 1, 5)},
                                      tooltip = {"placement": "bottom", "always_visible": True},
                                  ),
                              ]),
        
                              # Dropdown for selecting the metric
                              html.Div(style = {'marginBottom': '20px'}, children = [
                                  html.Label('Select Metric for Plots:',
                                             style = {'color': '#f8f8f2', 'fontSize': '18px'}),
                                  dcc.Dropdown(
                                      id = 'metric-dropdown',
                                      options = [
                                          {'label': 'New Base', 'value': 'New Base'},
                                          {'label': 'Unvested RSUs', 'value': 'Unvested RSUs'},
                                          {'label': 'Bonus', 'value': 'Bonus'}
                                      ],
                                      value = 'New Base',
                                      placeholder = "Select Metric",
                                      style = {'backgroundColor': '#2d2d2d', 'color': '#f8f8f2',
                                               'border': '1px solid #444', 'fontSize': '16px'}
                                  ),
                              ]),
        
                              # Dropdown for selecting the boxplot category
                              html.Div(style = {'marginBottom': '20px'}, children = [
                                  html.Label('Boxplot Category:', style = {'color': '#f8f8f2', 'fontSize': '18px'}),
                                  dcc.Dropdown(
                                      id = 'boxplot-category-dropdown',
                                      options = [
                                          {'label': 'Location', 'value': 'Location'},
                                          {'label': 'Total YoE', 'value': 'Total YoE'},
                                          {'label': 'Rating', 'value': 'Rating'}
                                      ],
                                      value = 'Location',
                                      placeholder = "Select Boxplot Category",
                                      style = {'backgroundColor': '#2d2d2d', 'color': '#f8f8f2',
                                               'border': '1px solid #444', 'fontSize': '16px'}
                                  ),
                              ]),
        
                              # Dropdown for color category with "None" option
                              html.Div(style = {'marginBottom': '20px'}, children = [
                                  html.Label('Color by Category:', style = {'color': '#f8f8f2', 'fontSize': '18px'}),
                                  dcc.Dropdown(
                                      id = 'color-category-dropdown',
                                      options = [
                                          {'label': 'None', 'value': 'None'},
                                          {'label': 'Location', 'value': 'Location'},
                                          {'label': 'Total YoE', 'value': 'Total YoE'},
                                          {'label': 'Rating', 'value': 'Rating'}
                                      ],
                                      value = 'None',
                                      placeholder = "Color by Category",
                                      style = {'backgroundColor': '#2d2d2d', 'color': '#f8f8f2',
                                               'border': '1px solid #444', 'fontSize': '16px'}
                                  ),
                              ]),
        
                              # Title for the summary table
                              html.H3("Metrics", style = {'color': '#f8f8f2', 'textAlign': 'center', 'fontSize': '20px',
                                                          'marginTop': '20px'}),
        
                              # Table for displaying summary statistics
                              html.Div(id = 'summary-table', style = {'color': '#f8f8f2', 'marginTop': '10px'})
                          ])
                      ])


# Function to compute summary statistics
def compute_summary_statistics(filtered_df):
    metrics = ['New Base', 'Unvested RSUs', 'Bonus', 'TC']
    summary_stats = {}
    
    for metric in metrics:
        summary_stats[metric] = {
            'Mean': np.round(filtered_df[metric].mean(), 2),
            'Median': np.round(filtered_df[metric].median(), 2),
            'Min': np.round(filtered_df[metric].min(), 2),
            'Max': np.round(filtered_df[metric].max(), 2),
            '75th Percentile': np.round(np.percentile(filtered_df[metric], 75), 2),
            '95th Percentile': np.round(np.percentile(filtered_df[metric], 95), 2)
        }
    return summary_stats


# Callback to update plots and summary table based on selected filters
@app.callback(
    [Output('top-plot', 'figure'),
     Output('boxplot-plot', 'figure'),
     Output('summary-table', 'children')],
    [Input('plot-type-dropdown', 'value'),
     Input('new-level-dropdown', 'value'),
     Input('location-dropdown', 'value'),
     Input('yoe-slider', 'value'),
     Input('metric-dropdown', 'value'),
     Input('boxplot-category-dropdown', 'value'),
     Input('color-category-dropdown', 'value')]
)
def update_plots(plot_type, selected_new_level, selected_location, yoe_value, selected_metric, boxplot_category,
                 color_category):
    # Filter the data based on dropdown selections and YoE slider
    filtered_df = df[df['Total YoE'] <= yoe_value].copy()
    
    if selected_new_level:
        filtered_df = filtered_df[filtered_df['New Level'].isin(selected_new_level)]
    
    if selected_location:
        filtered_df = filtered_df[filtered_df['Location'].isin(selected_location)]
    
    # Handle the "None" color category by setting color to None when selected
    color_option = None if color_category == 'None' else color_category
    
    # Create the top plot based on the selected plot type
    if plot_type == 'histogram':
        top_plot_fig = px.histogram(
            filtered_df,
            x = selected_metric,
            color = color_option,
            title = f'Distribution of {selected_metric}',
            nbins = 30,
            template = "plotly_dark",
            marginal = "box"  # Enable distribution plot along with boxplot

        )
    elif plot_type == 'barplot':
        top_plot_fig = px.bar(
            filtered_df.groupby([boxplot_category]).mean().reset_index(),
            x = boxplot_category,
            y = selected_metric,
            color = color_option,
            title = f'Average {selected_metric} by {boxplot_category}',
            template = "plotly_dark"
        )
    elif plot_type == 'normal_curve':
        top_plot_fig = ff.create_distplot([filtered_df[selected_metric]], [selected_metric], show_hist = False)
        top_plot_fig.update_layout(title = f'Normal Curve of {selected_metric}', template = "plotly_dark")
    elif plot_type == 'distplot_normal':
        top_plot_fig = ff.create_distplot([filtered_df[selected_metric]], [selected_metric], curve_type = 'normal')
        top_plot_fig.update_layout(title = f'Distribution Plot (Normal Curve) of {selected_metric}',
                                   template = "plotly_dark")
    
    top_plot_fig.update_layout(title = {'x': 0.5})  # Center the title
    
    # Create the boxplot with marginal distribution
    boxplot_fig = px.box(
        filtered_df,
        x = boxplot_category,
        y = selected_metric,
        color = color_option,
        title = f'Boxplot of {selected_metric} by {boxplot_category}',
        template = "plotly_dark",
    )
    boxplot_fig.update_layout(title = {'x': 0.5})  # Center the title
    
    # Compute summary statistics
    summary_stats = compute_summary_statistics(filtered_df)
    
    # Create the summary table with spacing between rows
    summary_table = html.Table([
                                   html.Tr([html.Th('Metric'), html.Th('Mean'), html.Th('Median'), html.Th('Min'),
                                            html.Th('Max'), html.Th('75th Percentile'), html.Th('95th Percentile')],
                                           style = {'textAlign': 'center', 'width': '14.3%', 'marginBottom': '10px'})] +
                               [html.Tr([html.Td(metric,
                                                 style = {'textAlign': 'center', 'width': '14.3%', 'padding': '8px',
                                                          'marginBottom': '10px'}),
                                         html.Td(stats['Mean'],
                                                 style = {'textAlign': 'center', 'width': '14.3%', 'padding': '8px',
                                                          'marginBottom': '10px'}),
                                         html.Td(stats['Median'],
                                                 style = {'textAlign': 'center', 'width': '14.3%', 'padding': '8px',
                                                          'marginBottom': '10px'}),
                                         html.Td(stats['Min'],
                                                 style = {'textAlign': 'center', 'width': '14.3%', 'padding': '8px',
                                                          'marginBottom': '10px'}),
                                         html.Td(stats['Max'],
                                                 style = {'textAlign': 'center', 'width': '14.3%', 'padding': '8px',
                                                          'marginBottom': '10px'}),
                                         html.Td(stats['75th Percentile'],
                                                 style = {'textAlign': 'center', 'width': '14.3%', 'padding': '8px',
                                                          'marginBottom': '10px'}),
                                         html.Td(stats['95th Percentile'],
                                                 style = {'textAlign': 'center', 'width': '14.3%', 'padding': '8px',
                                                          'marginBottom': '10px'})])
                                for metric, stats in summary_stats.items()]
                               )
    
    return top_plot_fig, boxplot_fig, summary_table


# Run the app
if __name__ == '__main__':
    app.run_server(debug = True)
