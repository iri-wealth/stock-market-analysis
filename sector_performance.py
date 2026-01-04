"""Fetches sector performance data for the past 5 trading days and creates a cumulative performance bar chart."""
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

# Get API key and endpoint
API_KEY = os.getenv('FMP_API_KEY')
SECTOR_PERFORMANCE_URL = os.getenv('SECTOR_PERFORMANCE_URL')

# Define sectors dictionary
sectors = {
    'Technology': 'Technology',
    'Healthcare': 'Healthcare',
    'Financial Services': 'Financial Services',
    'Consumer Cyclical': 'Consumer Cyclical',
    'Industrials': 'Industrials',
    'Consumer Defensive': 'Consumer Defensive',
    'Energy': 'Energy',
    'Real Estate': 'Real Estate',
    'Utilities': 'Utilities',
    'Communication Services': 'Communication Services',
    'Basic Materials': 'Basic Materials'
}


def get_trading_days(num_days=5):
    """
    Generate a list of the past N trading days (excluding weekends).
    Returns dates in YYYY-MM-DD format.
    """
    trading_days = []
    current_date = datetime.now()
    days_checked = 0
    
    while len(trading_days) < num_days and days_checked < num_days * 2:
        # Check if it's a weekday (Monday=0, Sunday=6)
        if current_date.weekday() < 5:  # Monday to Friday
            trading_days.append(current_date.strftime('%Y-%m-%d'))
        current_date -= timedelta(days=1)
        days_checked += 1
    
    return trading_days


def get_sector_performance():
    """
    Fetches sector performance data for the past 5 trading days and calculates cumulative performance.
    
    Returns:
        pd.DataFrame: DataFrame containing cumulative sector performance metrics
    """
    print("\nFetching sector performance data for the past 5 trading days...")
    print("=" * 80)
    
    # Get the past 5 trading days
    trading_days = get_trading_days(5)
    print(f"Trading days to fetch: {', '.join(trading_days)}")
    print("=" * 80)
    
    all_sector_data = []
    
    # Fetch data for each trading day
    for date in trading_days:
        try:
            # Construct URL with date and API key
            url = f"{SECTOR_PERFORMANCE_URL}?date={date}&apikey={API_KEY}"
            
            print(f"Fetching data for {date}...", end=" ")
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse the response data into JSON object
            data = response.json()
            
            if data:
                # Add date to each record for tracking
                for record in data:
                    record['fetch_date'] = date
                all_sector_data.extend(data)
                print(f"✓ ({len(data)} records)")
            else:
                print("⚠ No data")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Error: {e}")
        except ValueError as e:
            print(f"✗ JSON Error: {e}")
    
    # Convert to DataFrame
    if not all_sector_data:
        print("\n⚠ No sector performance data available.")
        return None
    
    df = pd.DataFrame(all_sector_data)
    
    print(f"\n✓ Total records fetched: {len(df)}")
    
    # Check if we have the necessary columns
    if 'sector' not in df.columns:
        print("Error: 'sector' column not found in data")
        print(f"Available columns: {df.columns.tolist()}")
        return None
    
    # Determine which performance column to use
    perf_column = None
    if 'changesPercentage' in df.columns:
        perf_column = 'changesPercentage'
    elif 'averageChange' in df.columns:
        perf_column = 'averageChange'
    else:
        print("Error: No performance column found (changesPercentage or averageChange)")
        print(f"Available columns: {df.columns.tolist()}")
        return None
    
    print(f"Using performance column: {perf_column}")
    
    # Calculate cumulative 5-day performance by sector
    cumulative_performance = df.groupby('sector')[perf_column].sum().sort_values(ascending=False)
    
    # Print results
    print("\n" + "=" * 40)
    print("CUMULATIVE 5-DAY SECTOR PERFORMANCE")
    print("=" * 40)
    for i, (sector, change) in enumerate(cumulative_performance.items(), 1):
        print(f"{i:2d}. {sector:30s} {change:+.2f}%")
    print("=" * 40 + "\n")
    
    # Create DataFrame for charting
    result_df = pd.DataFrame({
        'sector': cumulative_performance.index,
        'cumulative_performance': cumulative_performance.values
    })
    
    # Create visual Sector Performance Bar Chart
    create_sector_bar_chart(result_df)
    
    return result_df


def create_sector_bar_chart(df):
    """
    Creates a horizontal bar chart visualization of cumulative 5-day sector performance,
    sorted from maximum to minimum.
    
    Args:
        df (pd.DataFrame): DataFrame containing sector and cumulative_performance columns
    """
    if df is None or df.empty:
        print("No data available to create chart.")
        return
    
    # Sort by cumulative performance descending (maximum to minimum)
    df_sorted = df.sort_values('cumulative_performance', ascending=False)
    
    # Create figure and axis with better spacing
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Create color list based on cumulative_performance values
    colors = ['#632E62' if value < 0 else '#5A06F5' for value in df_sorted['cumulative_performance']]
    
    # Create horizontal bar chart (reversed y-axis for top-to-bottom display)
    bars = ax.barh(
        range(len(df_sorted)),
        df_sorted['cumulative_performance'],
        color=colors,
        edgecolor='black',
        linewidth=0.5,
        height=0.7
    )
    
    # Set y-axis labels
    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels(df_sorted['sector'].values, fontsize=12, fontfamily='Segoe UI')
    
    # Add value labels on the bars
    for i, value in enumerate(df_sorted['cumulative_performance'].values):
        offset = 0.3 if value > 0 else -0.3
        ha_align = 'left' if value > 0 else 'right'
        ax.text(
            value + offset,
            i,
            f'{value:+.2f}%',
            va='center',
            ha=ha_align,
            fontsize=12,
            fontfamily='Segoe UI',
            color='black',
            fontweight='bold'
        )
    
    # Customize plot with 20px margin on top and bottom of title
    ax.set_title(
        'Sector Performance - Cumulative 5-Day Change (%)',
        fontsize=16,
        fontweight='bold',
        fontfamily='Segoe UI',
        color='black',
        pad=20
    )
    
    ax.set_xlabel(
        'Cumulative 5-Day Performance (%)',
        fontsize=12,
        fontfamily='Segoe UI',
        color='black',
        fontweight='bold',
        labelpad=10
    )
    
    ax.set_ylabel(
        'Sector',
        fontsize=12,
        fontfamily='Segoe UI',
        color='black',
        fontweight='bold',
        labelpad=10
    )
    
    # Customize tick labels
    ax.tick_params(axis='both', labelsize=12)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily('Segoe UI')
        label.set_color('black')
    
    # Add grid for better readability
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    
    # Add a vertical line at x=0 for reference
    ax.axvline(x=0, color='black', linestyle='-', linewidth=1, zorder=1)
    
    # Add margins
    ax.margins(x=0.15, y=0.02)
    
    # Add source attribution below the x-axis
    fig.text(
        0.5, 0.02,
        'Source: prepared by Ki-Wealth | 5-Day Cumulative Performance',
        ha='center',
        fontsize=10,
        fontfamily='Segoe UI',
        color='black',
        style='italic'
    )
    
    # Adjust layout with better spacing
    plt.tight_layout(rect=[0.02, 0.04, 0.98, 0.97])
    
    # Save and show the plot
    output_path = 'sector_performance_bar_chart_5day.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
    print(f"\n✓ Bar chart saved as '{output_path}'")
    plt.show()


if __name__ == "__main__":
    # Execute the function
    sector_df = get_sector_performance()
    
    if sector_df is not None:
        print("\n✓ Data fetching and visualization completed successfully!")
    else:
        print("\n✗ Failed to fetch sector performance data.")