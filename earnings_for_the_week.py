
"""
Fetches earnings calendar data for the next five trading days using the FMP API.
Automatically calculates trading days excluding weekends.
"""

import os
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()


def get_next_trading_days(num_days=5):
    """
    Generate a list of the next N trading days (excluding weekends).
    Returns dates in YYYY-MM-DD format.
    
    Args:
        num_days (int): Number of trading days to generate (default: 5)
    
    Returns:
        list: List of date strings in YYYY-MM-DD format
    """
    trading_days = []
    current_date = datetime.now()
    days_checked = 0
    
    while len(trading_days) < num_days and days_checked < num_days * 2:
        current_date += timedelta(days=1)
        # Check if it's a weekday (Monday=0, Sunday=6)
        if current_date.weekday() < 5:  # Monday to Friday
            trading_days.append(current_date.strftime('%Y-%m-%d'))
        days_checked += 1
    
    return trading_days


def fetch_earnings_by_date_range(from_date: str = None, to_date: str = None) -> dict:
    """
    Fetches earnings calendar data for a specific date range.
    If dates are not provided, automatically fetches data for the next 5 trading days.
    
    Args:
        from_date (str, optional): Start date in format YYYY-MM-DD
        to_date (str, optional): End date in format YYYY-MM-DD
    
    Returns:
        dict: JSON response containing earnings data
    """
    # Get environment variables
    base_url = os.getenv("EARNINGS_CALENDAR_URL")
    api_key = os.getenv("FMP_API_KEY")
    
    # Validate environment variables
    if not base_url:
        raise ValueError("EARNINGS_CALENDAR_URL not found in .env file")
    if not api_key:
        raise ValueError("FMP_API_KEY not found in .env file")
    
    # If dates not provided, calculate next 5 trading days
    if from_date is None or to_date is None:
        trading_days = get_next_trading_days(5)
        from_date = trading_days[0]
        to_date = trading_days[-1]
        print(f"📅 Automatically calculated trading days:")
        print(f"   From: {from_date} (Next trading day)")
        print(f"   To:   {to_date} (5th trading day)")
        print(f"   Trading days: {', '.join(trading_days)}\n")
    
    # Build the complete URL with date parameters
    # Remove any existing query parameters from base_url
    base_url = base_url.split('?')[0]
    url = f"{base_url}?from={from_date}&to={to_date}&apikey={api_key}"
    
    print(f"Fetching earnings data from {from_date} to {to_date}...")
    print(f"URL: {url.replace(api_key, 'API_KEY_HIDDEN')}\n")
    
    try:
        # Make the API request
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        if not data:
            print("⚠ No earnings data found for the specified date range")
            return {}
        
        print(f"✓ Successfully fetched {len(data)} earnings records\n")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching data: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing JSON response: {e}")
        return {}


def display_json(data: dict, indent: int = 2) -> None:
    """
    Displays data in formatted JSON format.
    
    Args:
        data (dict): Data to display
        indent (int): Number of spaces for indentation
    """
    if not data:
        print("No data to display")
        return
    
    print("="*80)
    print("EARNINGS CALENDAR DATA (JSON FORMAT)")
    print("="*80)
    print(json.dumps(data, indent=indent))
    print("="*80)


def save_to_json_file(data: dict, filename: str = "earnings_week_data.json") -> None:
    """
    Saves data to a JSON file.
    
    Args:
        data (dict): Data to save
        filename (str): Output filename
    """
    if not data:
        print("No data to save")
        return
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"\n✓ Data saved to {filename}")
    except Exception as e:
        print(f"✗ Error saving to file: {e}")


def read_json_to_dataframe(filename: str = "earnings_week_data.json") -> pd.DataFrame:
    """
    Reads JSON file and transforms it into a DataFrame.
    Converts 'date' column from string to datetime format.
    
    Args:
        filename (str): JSON file to read
    
    Returns:
        pd.DataFrame: DataFrame with earnings data
    """
    try:
        # Read JSON file
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            print("⚠ No data found in JSON file")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Transform 'date' column from string to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
        
        print(f"✓ Successfully loaded {len(df)} records from {filename}")
        return df
        
    except FileNotFoundError:
        print(f"✗ File not found: {filename}")
        return pd.DataFrame()
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing JSON file: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return pd.DataFrame()


def filter_and_display_by_date(df: pd.DataFrame, filter_pattern: str = r'^[a-zA-Z]{1,4}$', max_symbols: int = 10) -> None:
    """
    Filters DataFrame by date and displays maximum symbols per date.
    Only displays symbols that match the specified regex pattern.
    
    Args:
        df (pd.DataFrame): DataFrame with earnings data
        filter_pattern (str): Regex pattern to filter symbols (default: ^[a-zA-Z]{1,4}$ for 1-4 letter symbols)
        max_symbols (int): Maximum number of symbols to display per date
    """
    if df.empty:
        print("⚠ No data to display")
        return
    
    if 'date' not in df.columns or 'symbol' not in df.columns:
        print("✗ Required columns 'date' and 'symbol' not found in DataFrame")
        return
    
    # Filter symbols that match the regex pattern
    mask = df['symbol'].str.match(filter_pattern, na=False)
    filtered_df = df[mask].copy()
    
    if filtered_df.empty:
        print(f"⚠ No symbols found matching pattern: {filter_pattern}")
        return
    
    # Sort by date
    filtered_df = filtered_df.sort_values('date')
    
    # Get unique dates
    unique_dates = filtered_df['date'].dt.date.unique()
    
    print("\n" + "="*80)
    print(f"FILTERED EARNINGS DATA (Symbols matching pattern: {filter_pattern})")
    print("="*80)
    
    # Display data for each date
    for date in unique_dates:
        date_str = date.strftime('%Y-%m-%d')
        date_data = filtered_df[filtered_df['date'].dt.date == date].head(max_symbols)
        
        print(f"\n📅 Date: {date_str}")
        print("-" * 80)
        
        # Select relevant columns for display
        display_columns = ['symbol', 'date']
        optional_columns = ['epsEstimated', 'epsActual', 'revenueEstimated', 'revenueActual', 'time']
        
        for col in optional_columns:
            if col in date_data.columns:
                display_columns.append(col)
        
        # Format date for display
        display_data = date_data[display_columns].copy()
        display_data['date'] = display_data['date'].dt.strftime('%Y-%m-%d')
        
        # Display table
        print(display_data.to_string(index=False))
        print(f"\nShowing {len(date_data)} of {len(filtered_df[filtered_df['date'].dt.date == date])} symbols for this date")
    
    print("\n" + "="*80)
    print(f"Total filtered records: {len(filtered_df)}")
    print(f"Total unique dates: {len(unique_dates)}")
    print("="*80 + "\n")


def display_all_data_by_date(df: pd.DataFrame, max_symbols: int = 10) -> None:
    """
    Displays all earnings data grouped by date without filtering.
    Shows maximum symbols per date.
    
    Args:
        df (pd.DataFrame): DataFrame with earnings data
        max_symbols (int): Maximum number of symbols to display per date
    """
    if df.empty:
        print("⚠ No data to display")
        return
    
    if 'date' not in df.columns or 'symbol' not in df.columns:
        print("✗ Required columns 'date' and 'symbol' not found in DataFrame")
        return
    
    # Sort by date
    df_sorted = df.sort_values('date')
    
    # Get unique dates
    unique_dates = df_sorted['date'].dt.date.unique()
    
    print("\n" + "="*80)
    print("ALL EARNINGS DATA BY DATE")
    print("="*80)
    
    # Display data for each date
    for date in unique_dates:
        date_str = date.strftime('%Y-%m-%d')
        date_data = df_sorted[df_sorted['date'].dt.date == date].head(max_symbols)
        
        print(f"\n📅 Date: {date_str}")
        print("-" * 80)
        
        # Select relevant columns for display
        display_columns = ['symbol', 'date']
        optional_columns = ['epsEstimated', 'epsActual', 'revenueEstimated', 'revenueActual', 'time']
        
        for col in optional_columns:
            if col in date_data.columns:
                display_columns.append(col)
        
        # Format date for display
        display_data = date_data[display_columns].copy()
        display_data['date'] = display_data['date'].dt.strftime('%Y-%m-%d')
        
        # Display table
        print(display_data.to_string(index=False))
        print(f"\nShowing {len(date_data)} of {len(df_sorted[df_sorted['date'].dt.date == date])} symbols for this date")
    
    print("\n" + "="*80)
    print(f"Total records: {len(df_sorted)}")
    print(f"Total unique dates: {len(unique_dates)}")
    print("="*80 + "\n")


def create_earnings_table(df: pd.DataFrame, filter_pattern: str = r'^[a-zA-Z]{1,4}$') -> None:
    """
    Creates a professionally formatted table showing earnings data for the week.
    Groups symbols by date with maximum 10 symbols per date.
    Displays: Date (Day Name) | Symbols (comma-separated)
    
    Args:
        df (pd.DataFrame): DataFrame with earnings data
        filter_pattern (str): Regex pattern to filter symbols (default: ^[a-zA-Z]{1,4}$ for 1-4 letter symbols)
    """
    if df.empty:
        print("⚠ No data to display")
        return
    
    if 'date' not in df.columns or 'symbol' not in df.columns:
        print("✗ Required columns 'date' and 'symbol' not found in DataFrame")
        return
    
    # Filter symbols that match the regex pattern
    mask = df['symbol'].str.match(filter_pattern, na=False)
    filtered_df = df[mask].copy()
    
    if filtered_df.empty:
        print(f"⚠ No symbols found matching pattern: {filter_pattern}")
        return
    
    # Sort by date
    filtered_df = filtered_df.sort_values('date')
    
    # Group by date and aggregate symbols (max 10 per date)
    grouped_data = []
    for date, group in filtered_df.groupby(filtered_df['date'].dt.date):
        # Get up to 10 symbols for this date
        symbols = group['symbol'].head(10).tolist()
        symbols_str = ', '.join(symbols)
        
        # Format date with day name
        date_obj = pd.to_datetime(date)
        day_name = date_obj.strftime('%A')  # Full day name (Monday, Tuesday, etc.)
        date_str = date_obj.strftime('%Y-%m-%d')
        formatted_date = f"{date_str}\n({day_name}, {date_obj.strftime('%B %d')})"
        
        grouped_data.append([formatted_date, symbols_str])
    
    # Create DataFrame for display
    display_data = pd.DataFrame(grouped_data, columns=['Date', 'Symbols'])
    
    # Calculate figure height based on number of rows
    num_rows = len(display_data)
    fig_height = max(8, num_rows * 1.5 + 3)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(20, fig_height))
    ax.axis('tight')
    ax.axis('off')
    
    # Create table
    table = ax.table(
        cellText=display_data.values,
        colLabels=display_data.columns,
        cellLoc='left',
        loc='center',
        bbox=[0, 0, 1, 1]
    )
    
    # Style table
    table.auto_set_font_size(False)
    table.scale(1, 2)
    
    # Style header row
    for i in range(len(display_data.columns)):
        cell = table[(0, i)]
        cell.set_facecolor('#4304B7')
        cell.set_text_props(weight='bold', color='white', fontsize=20, ha='center')
        cell.set_height(0.08)
    
    # Style data rows
    for i in range(1, len(display_data) + 1):
        # Date column (left-aligned, centered vertically)
        date_cell = table[(i, 0)]
        date_cell.set_facecolor('#F0F0F0')
        date_cell.set_text_props(color='black', fontsize=16, ha='left', va='center', weight='bold')
        date_cell.set_edgecolor('#CCCCCC')
        date_cell.set_height(0.15)
        
        # Symbols column (left-aligned, wrapped text)
        symbol_cell = table[(i, 1)]
        symbol_cell.set_facecolor('white')
        symbol_cell.set_text_props(color='black', fontsize=16, ha='left', va='center')
        symbol_cell.set_edgecolor('#CCCCCC')
        symbol_cell.set_height(0.15)
    
    # Set column widths (Date: 20%, Symbols: 80%)
    table.auto_set_column_width([0, 1])
    for i in range(len(display_data) + 1):
        table[(i, 0)].set_width(0.2)
        table[(i, 1)].set_width(0.8)
    
    # Add title
    plt.title('Earnings to Watch This Week', fontsize=24, fontweight='bold', pad=30)
    
    # Add source attribution at the bottom
    fig.text(
        0.5, 0.02,
        'Source: Prepared by Ki-Wealth based on FMP data',
        ha='center',
        fontsize=14,
        fontfamily='Segoe UI',
        color='black',
        style='italic'
    )
    
    plt.tight_layout(rect=[0, 0.04, 1, 0.96])
    
    # Save the figure
    filename = 'earnings_to_watch_this_week.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n✓ Table saved as {filename}")
    
    # Also print to console
    print("\n" + "="*80)
    print("EARNINGS TO WATCH THIS WEEK")
    print("="*80)
    for date_info, symbols in grouped_data:
        print(f"\n{date_info}")
        print(f"  Symbols: {symbols}")
    print("\n" + "="*80 + "\n")
    
    plt.show()


def main():
    """
    Main function to fetch and display earnings calendar data.
    """
    try:
        # Fetch earnings data for next 5 trading days
        earnings_data = fetch_earnings_by_date_range()
        
        # Display in JSON format
        display_json(earnings_data)
        
        # Optionally save to file
        if earnings_data:
            save_to_json_file(earnings_data)
            
            # Display summary statistics
            print(f"\nSummary:")
            print(f"  Total records: {len(earnings_data)}")
            if earnings_data:
                # Count unique dates
                dates = set(record.get('date', '') for record in earnings_data)
                print(f"  Unique dates: {len(dates)}")
                # Get date range from data
                if dates:
                    sorted_dates = sorted(dates)
                    print(f"  Date range: {sorted_dates[0]} to {sorted_dates[-1]}")
            
            # Read JSON file and transform to DataFrame
            print("\n" + "="*80)
            print("PROCESSING DATA FROM JSON FILE")
            print("="*80)
            
            df = read_json_to_dataframe("earnings_week_data.json")
            
            if not df.empty:
                # Display all data by date (max 10 symbols per date)
                display_all_data_by_date(df, max_symbols=10)
                
                # Filter and display symbols with 1-4 letters only
                # Pattern: ^[a-zA-Z]{1,4}$ matches symbols with exactly 1 to 4 letters
                filter_pattern = r'^[a-zA-Z]{1,4}$'
                filter_and_display_by_date(df, filter_pattern=filter_pattern, max_symbols=10)
                
                # Create professional table
                create_earnings_table(df, filter_pattern=filter_pattern)
        
    except Exception as e:
        print(f"✗ Error in main execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
