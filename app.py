import streamlit as st
import pandas as pd
from supabase import create_client, Client
import webbrowser
from charts import create_price_history_chart

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
            st.markdown(f"## [{street}, {city}]({listing_url})", unsafe_allow_html=True)
        else:
            st.markdown(f"## {street}, {city}", unsafe_allow_html=True)
        
        home_info = {
            "Listing Agent": agent_name,
            "Phone": agent_phone,
            "Type": home_type,
            "Bedrooms": bedrooms,
            "ZIP Code": zip_code,
            "Currently Listed": "No" if listed_status else "Yes"
        }
        st.dataframe(pd.DataFrame([home_info]), hide_index=True)

        # Call Goal
        # st.header("Call Goal")
        # if gouging_rule == "tenpercent":
        #     call_goal = (
        #         "Inform the contact that this listing violates California's price gouging law. "
        #         "Ask them to rectify the price."
        #     )
        # elif gouging_rule == "fmr":
        #     call_goal = (
        #         "Was the unit rented at any time between **January 7, 2024** and **January 7, 2025**? If so, what price?"
        #     )
        # else:
        #     call_goal = "Review manually to determine appropriate action."        
        # st.write(call_goal)
        
        # Gouging Information
        # st.markdown("### Pricing Information")
        gouging_display = "10%" if gouging_rule == "tenpercent" else "FMR"
        confidence = "Yes" if gouging_rule == "tenpercent" else "Maybe"
        
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        
        with r1c1:
            st.metric(label="Current Rent", value=f"${current_price:,}")
        with r1c2:
            st.metric(label="Gouged Since", value=pd.to_datetime(first_date).strftime("%m/%d"))
        with r1c3:
            st.metric(label="Rule", value=gouging_display)
        with r1c4:
            st.metric(label="Rent Gouging?", value=confidence)
        # if gouging_rule == "tenpercent":
        #     with r1c4:
        #         st.metric(label="Rent Increase", value=f"{100 * (current_price - base_price) / base_price:.1f}%")
        # else:
        #     with r1c4:
        #         st.metric(label="% of FMR", value=f"{100 * (current_price - fmr) / fmr:.1f}%")
        
        # Contact and Property Info in two columns
        st.divider()
        if gouging_rule == "tenpercent":
            r3c1, r3c2, r3c3, r3c4 = st.columns(4)
            with r3c1:
                st.metric(label="Original Rent", value=f"${base_price:,}")
            with r3c2:
                st.metric(label="First Gouged Rent", value=f"${first_price:,}")
            with r3c3: 
                st.metric(label="Current Rent", value=f"${current_price:,}")
            with r3c4:
                st.metric(label="Rent Increase", value=f"{100 * (current_price - base_price) / base_price:.1f}%")
            
            st.markdown("#### Price History")
            # Create price history data
            dates = [
                pd.to_datetime(listing.get("base_price_date")).strftime("%Y-%m-%d"),
                pd.to_datetime(listing.get("first_gouged_price_date")).strftime("%Y-%m-%d"),
                pd.to_datetime(listing.get("emergency_peak_price_date")).strftime("%Y-%m-%d"),
                pd.to_datetime(listing.get("latest_price_date")).strftime("%Y-%m-%d")
            ]
            prices = [base_price, first_price, peak_price, current_price]
            
            # Create and display the chart using the new module
            fig = create_price_history_chart(dates, prices, price_ceiling)
            st.plotly_chart(fig, use_container_width=True)
            
        elif gouging_rule == "fmr":
            r3c1, r3c2, r3c3, r3c4 = st.columns(4)
            with r3c1:
                st.metric(label="Bedrooms", value=bedrooms)
            with r3c2:
                st.metric(label="ZIP Code", value=zip_code)
            with r3c3:
                st.metric(label="Fair Market Rent (FMR)", value=f"${fmr:,}")
            with r3c4: 
                st.metric(label="Legal % of FMR", value=f"160%")
            
            r4c1, r4c2, r4c3, r4c4 = st.columns(4)
            with r4c1:
                st.metric(label="Max Legal Rent", value=f"${price_ceiling:,}")
            with r4c2:
                st.metric(label="Current Rent", value=f"${current_price:,}")
            with r4c3:
                st.metric(label="Peak Rent", value=f"${peak_price:,}")
            with r4c4:
                st.metric(label="Actual % of FMR", value=f"{100 * current_price / fmr:.0f}%")
            
            st.subheader("Price History")
            # Create price history data (excluding base price)
            dates = [
                pd.to_datetime(listing.get("first_gouged_price_date")).strftime("%Y-%m-%d"),
                pd.to_datetime(listing.get("emergency_peak_price_date")).strftime("%Y-%m-%d"),
                pd.to_datetime(listing.get("latest_price_date")).strftime("%Y-%m-%d")
            ]
            prices = [first_price, peak_price, current_price]
            
            # Create and display the chart using the new module
            fig = create_price_history_chart(dates, prices, price_ceiling)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"""
            - **Maximum Legal Rent:** ${price_ceiling:,}
            - **Fair Market Rent:** ${fmr:,}
            - **First Gouged Price:** ${first_price:,} on {first_date}
            - **Highest Gouged Price:** ${peak_price:,} on {peak_date}
            - **Current Price:** ${current_price:,} on {current_date}
            """)
        else:
            st.markdown("- **Status:** Unknown gouging rule; unable to calculate ceiling.")

    else:
        st.warning("No listing found with that ID.")
