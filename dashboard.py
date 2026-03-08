
"""
QoS Dashboard - Real-time visualization of network quality metrics
Web-based dashboard showing live graphs and prediction history
"""

import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class QoSDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.history_file = 'history.csv'
        self.setup_layout()
        self.setup_callbacks()
    
    def load_data(self):
        """Load data from CSV file"""
        if not os.path.exists(self.history_file):
            # Create sample data if no history exists
            return self.create_sample_data()
        
        try:
            df = pd.read_csv(self.history_file)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            return df
        except Exception as e:
            print(f"⚠️ Error loading data: {e}")
            return self.create_sample_data()
    
    def create_sample_data(self):
        """Create sample data for demonstration"""
        timestamps = [datetime.now() - timedelta(minutes=x*5) for x in range(20, 0, -1)]
        
        data = []
        for ts in timestamps:
            # Generate realistic sample data
            base_latency = 45 + np.random.normal(0, 15)
            data.append({
                'Timestamp': ts,
                'Latency_ms': max(10, base_latency),
                'Jitter_ms': max(1, np.random.exponential(8)),
                'PacketLoss_%': max(0, np.random.exponential(1.5)),
                'Download_Mbps': max(5, 25 + np.random.normal(0, 8)),
                'Upload_Mbps': max(1, 5 + np.random.normal(0, 2)),
                'Prediction': np.random.choice(['✅ Smooth Streaming', '⚠️ May Buffer Occasionally', '❌ Poor Experience']),
            
            })
        
        return pd.DataFrame(data)
    
    def setup_layout(self):
        """Setup dashboard layout"""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("🎯 QoS Network Monitor", 
                       style={'color': '#2c3e50', 'textAlign': 'center', 'margin': '20px'}),
                html.P("Real-time network quality monitoring and streaming prediction",
                      style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '16px'})
            ]),
            
            # Auto-refresh indicator
            html.Div([
                html.Span("🔄 Auto-refresh: ", style={'fontSize': '14px', 'color': '#2c3e50'}),
                html.Span(id='refresh-indicator', children="Active", 
                         style={'fontSize': '14px', 'color': '#27ae60', 'fontWeight': 'bold'})
            ], style={'textAlign': 'center', 'margin': '10px'}),
            
            # Key metrics cards
            html.Div(id='metrics-cards', style={'margin': '20px'}),
            
            # Charts container
            html.Div([
                # Network metrics over time
                html.Div([
                    dcc.Graph(id='latency-chart')
                ], className='chart-container', style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(id='bandwidth-chart')
                ], className='chart-container', style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(id='quality-pie-chart')
                ], className='chart-container', style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(id='packet-loss-chart')
                ], className='chart-container', style={'width': '50%', 'display': 'inline-block'})
            ]),
            
            # Recent predictions table
            html.Div([
                html.H3("📋 Recent Predictions", style={'color': '#2c3e50', 'margin': '20px'}),
                html.Div(id='predictions-table')
            ], style={'margin': '20px'}),
            
            # Auto-refresh component
            dcc.Interval(
                id='interval-component',
                interval=60*1000,  # Update every 60 seconds
                n_intervals=0
            )
        ], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#ecf0f1'})
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output('metrics-cards', 'children'),
             Output('latency-chart', 'figure'),
             Output('bandwidth-chart', 'figure'), 
             Output('quality-pie-chart', 'figure'),
             Output('packet-loss-chart', 'figure'),
             Output('predictions-table', 'children'),
             Output('refresh-indicator', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            df = self.load_data()
            
            if df.empty:
                empty_fig = go.Figure()
                empty_fig.add_annotation(text="No data available - start monitoring!", 
                                       xref="paper", yref="paper", x=0.5, y=0.5)
                return [], empty_fig, empty_fig, empty_fig, empty_fig, [], f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
            
            # Get latest metrics for cards
            latest = df.iloc[-1] if not df.empty else None
            
            # Metrics cards
            cards = self.create_metrics_cards(latest) if latest is not None else []
            
            # Charts
            latency_fig = self.create_latency_chart(df)
            bandwidth_fig = self.create_bandwidth_chart(df)
            quality_fig = self.create_quality_pie_chart(df)
            packet_loss_fig = self.create_packet_loss_chart(df)
            
            # Recent predictions table
            table = self.create_predictions_table(df.tail(10))
            
            refresh_time = f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
            
            return cards, latency_fig, bandwidth_fig, quality_fig, packet_loss_fig, table, refresh_time
    
    def create_metrics_cards(self, latest_data):
        """Create metric summary cards"""
        if latest_data is None:
            return []
        
        cards = html.Div([
            # Latency card
            html.Div([
                html.H4("🌐 Latency", style={'color': '#3498db', 'margin': '10px'}),
                html.H2(f"{latest_data['Latency_ms']:.1f}ms", 
                       style={'color': '#2c3e50', 'margin': '5px'}),
                html.P("Response time", style={'color': '#7f8c8d', 'fontSize': '12px'})
            ], style={'textAlign': 'center', 'backgroundColor': 'white', 'padding': '20px', 
                     'borderRadius': '10px', 'margin': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                     'width': '22%', 'display': 'inline-block'}),
            
            # Jitter card  
            html.Div([
                html.H4("📊 Jitter", style={'color': '#e74c3c', 'margin': '10px'}),
                html.H2(f"{latest_data['Jitter_ms']:.1f}ms", 
                       style={'color': '#2c3e50', 'margin': '5px'}),
                html.P("Variation", style={'color': '#7f8c8d', 'fontSize': '12px'})
            ], style={'textAlign': 'center', 'backgroundColor': 'white', 'padding': '20px', 
                     'borderRadius': '10px', 'margin': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                     'width': '22%', 'display': 'inline-block'}),
            
            # Download speed card
            html.Div([
                html.H4("⬇️ Download", style={'color': '#27ae60', 'margin': '10px'}),
                html.H2(f"{latest_data['Download_Mbps']:.1f} Mbps", 
                       style={'color': '#2c3e50', 'margin': '5px'}),
                html.P("Speed", style={'color': '#7f8c8d', 'fontSize': '12px'})
            ], style={'textAlign': 'center', 'backgroundColor': 'white', 'padding': '20px', 
                     'borderRadius': '10px', 'margin': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                     'width': '22%', 'display': 'inline-block'}),
            
            # Current prediction card
            html.Div([
                html.H4("🎯 Quality", style={'color': '#9b59b6', 'margin': '10px'}),
                html.H3(latest_data['Prediction'].replace('✅ ', '').replace('⚠️ ', '').replace('❌ ', ''), 
                       style={'color': '#2c3e50', 'margin': '5px', 'fontSize': '16px'}),
                html.P("Current", style={'color': '#7f8c8d', 'fontSize': '12px'})
            ], style={'textAlign': 'center', 'backgroundColor': 'white', 'padding': '20px', 
                     'borderRadius': '10px', 'margin': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                     'width': '22%', 'display': 'inline-block'})
        ])
        
        return cards
    
    def create_latency_chart(self, df):
        """Create latency and jitter time series chart"""
        fig = go.Figure()
        
        # Latency line
        fig.add_trace(go.Scatter(
            x=df['Timestamp'],
            y=df['Latency_ms'],
            mode='lines+markers',
            name='Latency (ms)',
            line=dict(color='#3498db', width=2),
            marker=dict(size=6)
        ))
        
        # Jitter line
        fig.add_trace(go.Scatter(
            x=df['Timestamp'],
            y=df['Jitter_ms'],
            mode='lines+markers',
            name='Jitter (ms)',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="🌐 Latency & Jitter Over Time",
            xaxis_title="Time",
            yaxis_title="Milliseconds (ms)",
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            legend=dict(x=0, y=1),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
    
    def create_bandwidth_chart(self, df):
        """Create bandwidth time series chart"""
        fig = go.Figure()
        
        # Download speed
        fig.add_trace(go.Scatter(
            x=df['Timestamp'],
            y=df['Download_Mbps'],
            mode='lines+markers',
            name='Download (Mbps)',
            line=dict(color='#27ae60', width=2),
            marker=dict(size=6),
            fill='tonexty'
        ))
        
        # Upload speed
        fig.add_trace(go.Scatter(
            x=df['Timestamp'],
            y=df['Upload_Mbps'],
            mode='lines+markers',
            name='Upload (Mbps)',
            line=dict(color='#f39c12', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="📶 Bandwidth Over Time",
            xaxis_title="Time",
            yaxis_title="Speed (Mbps)",
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            legend=dict(x=0, y=1),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
    
    def create_quality_pie_chart(self, df):
        """Create quality prediction distribution pie chart"""
        quality_counts = df['Prediction'].value_counts()
        
        # Clean labels and assign colors
        labels = []
        colors = []
        values = []
        
        for prediction, count in quality_counts.items():
            if '✅' in prediction:
                labels.append('Smooth Streaming')
                colors.append('#27ae60')
            elif '⚠️' in prediction:
                labels.append('May Buffer')
                colors.append('#f39c12')
            elif '❌' in prediction:
                labels.append('Poor Experience')
                colors.append('#e74c3c')
            else:
                labels.append(prediction)
                colors.append('#95a5a6')
            values.append(count)
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.4,
            marker_colors=colors,
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            title="🎯 Quality Distribution",
            font=dict(size=12),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
    
    def create_packet_loss_chart(self, df):
        """Create packet loss chart"""
        fig = go.Figure()
        
        # Packet loss bar chart
        fig.add_trace(go.Bar(
            x=df['Timestamp'],
            y=df['PacketLoss_%'],
            name='Packet Loss (%)',
            marker_color='#e74c3c',
            opacity=0.7
        ))
        
        # Add threshold line at 1%
        fig.add_hline(y=1, line_dash="dash", line_color="orange", 
                      annotation_text="Acceptable Threshold (1%)")
        
        fig.update_layout(
            title="📦 Packet Loss Over Time",
            xaxis_title="Time",
            yaxis_title="Packet Loss (%)",
            hovermode='x',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
    
    def create_predictions_table(self, df):
        """Create recent predictions table"""
        if df.empty:
            return html.P("No predictions yet - start monitoring!", 
                         style={'textAlign': 'center', 'color': '#7f8c8d'})
        
        # Prepare table data
        table_df = df[['Timestamp', 'Prediction', 'Latency_ms', 'Download_Mbps']].copy()
        table_df['Timestamp'] = table_df['Timestamp'].dt.strftime('%H:%M:%S')
        table_df['Latency_ms'] = table_df['Latency_ms'].round(1)
        table_df['Download_Mbps'] = table_df['Download_Mbps'].round(1)
        
        # Rename columns for display
        table_df.columns = ['Time', 'Quality Prediction', 'Latency (ms)', 'Speed (Mbps)',]
        
        return dash_table.DataTable(
            data=table_df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in table_df.columns],
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Arial, sans-serif',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': '#3498db',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'filter_query': '{Quality Prediction} contains "✅"'},
                    'backgroundColor': '#d5f4e6',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{Quality Prediction} contains "⚠️"'},
                    'backgroundColor': '#fef5e7',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{Quality Prediction} contains "❌"'},
                    'backgroundColor': '#fadbd8',
                    'color': 'black',
                }
            ],
            page_size=10,
            sort_action="native"
        )
    
    def run(self, debug=False, port=8050):
        """Run the dashboard server"""
        print(f"🚀 Starting QoS Dashboard on http://127.0.0.1:{port}")
        print("📊 Dashboard features:")
        print("  • Real-time network metrics")
        print("  • Quality prediction history") 
        print("  • Auto-refresh every 60 seconds")
        print("  • Interactive charts and tables")
        print(f"\n🔗 Open in browser: http://127.0.0.1:{port}")
        
        self.app.run(debug=debug, port=port, host='127.0.0.1')

def main():
    """Main entry point for dashboard"""
    dashboard = QoSDashboard()
    dashboard.run(debug=False)

if __name__ == "__main__":
    main()
