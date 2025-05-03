import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client, Client
import webbrowser

# Load Supabase credentials
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
SUPABASE_USER = st.secrets["SUPABASE_USER"]
SUPABASE_PASSWORD = st.secrets["SUPABASE_PASSWORD"]

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase.auth.sign_in_with_password({"email": SUPABASE_USER, "password": SUPABASE_PASSWORD})

def open_zillow(url):
    webbrowser.open(url)    

# Read listing ID
listing_id = st.query_params.get("listing_id", None)
listing_id = st.text_input("Listing ID", value=listing_id or "")

# Fetch and render listing
if listing_id:
    response = supabase.table("gouged_listings").select("*").eq("listing_id", listing_id).limit(1).execute()
    if response.data:
        listing = response.data[0]

        # Basic info
        street = listing.get("street_address", "N/A")
        city = listing.get("city", "N/A")
        agent_name = listing.get("agent_name", "N/A")
        agent_phone = listing.get("agent_phone_number", "N/A")
        listing_url = listing.get("listing_url", "#")
        home_type = listing.get("home_type", "N/A")
        bedrooms = listing.get("bedrooms", "N/A")
        zip_code = listing.get("zipcode", "N/A")
        gouging_rule = listing.get("gouging_rule", "N/A")
        price_ceiling = listing.get("price_ceiling")
        listed_status = listing.get("is_currently_unlisted", "N/A")
        
        # Prices & Dates
        base_price = listing.get("base_price")
        base_date = pd.to_datetime(listing.get("base_price_date")).strftime("%B %d, %Y") if listing.get("base_price_date") else "N/A"
        first_price = listing.get("first_gouged_price")
        first_date = pd.to_datetime(listing.get("first_gouged_price_date")).strftime("%B %d, %Y") if listing.get("first_gouged_price_date") else "N/A"
        peak_price = listing.get("emergency_peak_price")
        peak_date = pd.to_datetime(listing.get("emergency_peak_price_date")).strftime("%B %d, %Y") if listing.get("emergency_peak_price_date") else "N/A"
        current_price = listing.get("latest_price")
        current_date = pd.to_datetime(listing.get("latest_price_date")).strftime("%B %d, %Y") if listing.get("latest_price_date") else "N/A"
        fmr = listing.get("fair_market_rent")

        def pct_change(price):
            if price and base_price and base_price > 0:
                return f"{(price / base_price - 1) * 100:.1f}%"
            return "N/A"

        if listing_url and listing_url != "#":
            st.markdown(f"# [{street}, {city}]({listing_url})", unsafe_allow_html=True)
        else:
            st.markdown(f"# {street}, {city}", unsafe_allow_html=True)
            
        # Top row with key information
        gouging_display = "10%" if gouging_rule == "tenpercent" else "FMR"
        confidence = "High" if gouging_rule == "tenpercent" else "Low"
        
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        
        with r1c1:
            st.metric(label="Price", value=f"${current_price:,}")
        with r1c2:
            st.metric(label="Gouged Since", value=pd.to_datetime(first_date).strftime("%m/%d/%y"))
        with r1c3:
            st.metric(label="Gouging Rule", value=gouging_display)
        with r1c4:
            st.metric(label="Confidence", value=confidence)

        # Contact and Property Info in two columns
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.subheader("Contact Info")
            contact_data = {
                "Listing Agent": agent_name,
                "Phone": agent_phone
            }
            st.dataframe(pd.DataFrame([contact_data]), hide_index=True)
        
        with r2c2:
            st.subheader("Property Details")
            property_data = {
                "Type": home_type,
                "Bedrooms": bedrooms,
                "ZIP Code": zip_code,
                "Currently Listed": "No" if listed_status else "Yes"
            }
            st.dataframe(pd.DataFrame([property_data]), hide_index=True)

        # Call Goal
        st.header("Call Goal")
        if gouging_rule == "tenpercent":
            call_goal = (
                "Inform the contact that this listing violates California's price gouging law. "
                "Ask them to rectify the price."
            )
        elif gouging_rule == "fmr":
            call_goal = (
                "Was the unit rented at any time between **January 7, 2024** and **January 7, 2025**? If so, what price?"
            )
        else:
            call_goal = "Review manually to determine appropriate action."
        
        st.write(call_goal)
        
        # Gouging Information
        st.header("Gouging Information")
        if gouging_rule == "tenpercent":
            st.subheader("Price History")
            # Create price history data
            dates = [
                pd.to_datetime(listing.get("base_price_date")).strftime("%Y-%m-%d"),
                pd.to_datetime(listing.get("first_gouged_price_date")).strftime("%Y-%m-%d"),
                pd.to_datetime(listing.get("emergency_peak_price_date")).strftime("%Y-%m-%d"),
                pd.to_datetime(listing.get("latest_price_date")).strftime("%Y-%m-%d")
            ]
            prices = [base_price, first_price, peak_price, current_price]
            
            # Create the figure
            fig = go.Figure()
            
            # Add the line
            fig.add_trace(go.Scatter(
                x=dates,
                y=prices,
                mode='lines+markers',
                line=dict(color='red', width=2),
                marker=dict(size=8, color='red'),
                name='Price History'
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
                    fig.add_annotation(
                        x=date,
                        y=price,
                        text=f'${price:,.0f}',
                        showarrow=False,
                        yshift=20 if i < 2 else 10,  # First two points get more space
                        font=dict(color='white')
                    )
                    seen_dates.add(date)
            
            # Add price ceiling line
            if price_ceiling:
                fig.add_hline(
                    y=price_ceiling,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"Max Legal: ${price_ceiling:,.0f}",
                    annotation_position="top left",
                    annotation_y=price_ceiling + (max(prices) - min(prices)) * 0.02
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
                yshift=10
            )
            
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
                    tickvals=dates,
                    ticktext=[pd.to_datetime(date).strftime('%m/%d/%y') for date in dates]
                ),
                yaxis=dict(
                    gridcolor='rgba(255, 255, 255, 0.1)',
                    zerolinecolor='rgba(255, 255, 255, 0.1)',
                    range=[min(prices) * 0.8, max(prices) * 1.2]  # Increased padding to 20%
                ),
                margin=dict(l=50, r=50, t=50, b=50)  # Added margins to ensure labels are visible
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
        elif gouging_rule == "fmr":
            calculated_ceiling = round(fmr * 1.6, 2) if fmr else None
            st.markdown(f"""
            - **Maximum Legal Rent:** ${calculated_ceiling:,}
            - **Fair Market Rent:** ${fmr:,}
            - **First Gouged Price:** ${first_price:,} on {first_date}
            - **Highest Gouged Price:** ${peak_price:,} on {peak_date}
            - **Current Price:** ${current_price:,} on {current_date}
            """)
        else:
            st.markdown("- **Status:** Unknown gouging rule; unable to calculate ceiling.")

    else:
        st.warning("No listing found with that ID.")
