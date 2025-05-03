import plotly.graph_objects as go
import pandas as pd

def create_price_history_chart(dates, prices, price_ceiling):
    """
    Creates a price history chart with annotations and reference lines.
    
    Args:
        dates (list): List of dates in string format
        prices (list): List of prices
        price_ceiling (float): The maximum legal price
        
    Returns:
        plotly.graph_objects.Figure: The configured figure
    """
    # Create the figure
    fig = go.Figure()
    
    # Add the line
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines+markers',
        line=dict(color='white', width=2, shape='spline'),
        marker=dict(size=8, color='white'),
        name='Price History'
    ))
    
    # Add shaded area above price ceiling if it exists
    if price_ceiling:
        # Find the first point after the emergency date
        emergency_date = pd.to_datetime("2025-01-07")
        post_emergency_dates = [date for date in dates if pd.to_datetime(date) > emergency_date]
        if post_emergency_dates:
            first_post_emergency_date = post_emergency_dates[0]
            # Get the index of this date
            start_idx = dates.index(first_post_emergency_date)
            # Create the polygon using only dates from the first post-emergency point
            shaded_dates = dates[start_idx:]
            # Add a trace for the shaded area
            fig.add_trace(go.Scatter(
                x=shaded_dates + shaded_dates[::-1],  # Create a closed polygon
                y=[price_ceiling] * len(shaded_dates) + [max(prices) * 1.2] * len(shaded_dates),  # Top and bottom of the shaded area
                fill='toself',
                fillcolor='rgba(255, 0, 0, 0.2)',  # Semi-transparent red
                line=dict(width=0),  # No border
                showlegend=False,
                hoverinfo='skip',
                mode='none'  # Disable any points or lines
            ))
    
    # Add dotted lines from x-axis to points
    for date, price in zip(dates, prices):
        fig.add_shape(
            type="line",
            x0=date,
            x1=date,
            y0=0,
            y1=price,
            line=dict(color="white", width=1, dash="dot"),
            layer="below"
        )
    
    # Add annotations for key points
    seen_dates = set()
    for i, (date, price, label) in enumerate(zip(dates, prices, ['Base', 'First Gouge', 'Peak', 'Current'])):
        if date not in seen_dates:
            # Calculate vertical offset based on position
            if i == 0:  # First point
                yshift = 20
            elif i == len(dates) - 1:  # Last point
                yshift = -20
            else:  # Middle points
                yshift = 20 if i % 2 == 0 else -20
            
            fig.add_annotation(
                x=date,
                y=price,
                text=f'${price:,.0f}',
                showarrow=False,
                yshift=yshift,
                font=dict(color='white')
            )
            seen_dates.add(date)
    
    # Add price ceiling line
    if price_ceiling:
        fig.add_hline(
            y=price_ceiling,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Max Legal: ${price_ceiling:,.0f}",
            annotation_position="top left",
            annotation_y=price_ceiling + (max(prices) - min(prices)) * 0.05  # Increased spacing
        )
    
    # Add emergency date line
    fig.add_shape(
        type="line",
        x0="2025-01-07",
        x1="2025-01-07",
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="blue", width=2, dash="dash")
    )
    
    # Add emergency declaration annotation
    fig.add_annotation(
        x="2025-01-07",
        y=1,
        yref="paper",
        text="Emergency Date",
        showarrow=False,
        xshift=-15,
        yshift=-10,
        font=dict(color='white')
    )
    
    # Calculate y-axis range with extra space for labels
    y_min = min(min(prices) * 0.7, price_ceiling * 0.8 if price_ceiling else min(prices) * 0.7)
    y_max = max(max(prices) * 1.3, price_ceiling * 1.2 if price_ceiling else max(prices) * 1.3)
    y_range = y_max - y_min
    y_min -= y_range * 0.1  # Add extra space at bottom
    y_max += y_range * 0.1  # Add extra space at top
    
    # Update layout
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Price ($)',
        showlegend=False,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='white'),
        xaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            zerolinecolor='rgba(255, 255, 255, 0.1)',
            tickmode='array',
            tickvals=dates + ["2025-01-07"],  # Add emergency date to ticks
            ticktext=[pd.to_datetime(date).strftime('%m/%d/%y') for date in dates] + ["01/07/25"],  # Add emergency date label
            tickangle=45  # Rotate labels for better readability
        ),
        yaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            zerolinecolor='rgba(255, 255, 255, 0.1)',
            range=[y_min, y_max]
        ),
        margin=dict(l=50, r=50, t=50, b=80)  # Increased bottom margin to accommodate rotated labels
    )
    
    return fig 