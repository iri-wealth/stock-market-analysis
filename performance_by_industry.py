from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Load environment variables from.env file
load_dotenv()

# Get API key and endpoint
API_KEY = os.getenv('FMP_API_KEY')
INDUSTRY_PERFORMANCE_URL = os.getenv('INDUSTRY_PERFORMANCE_URL')

# Define industries dictionary:
AVAILABLE_INDUSTRIES_URL = os.getenv('AVAILABLE_INDUSTRIES')

if not AVAILABLE_INDUSTRIES_URL:
    print('No industries URL available in environment variables.')
    exit()

# 1. Load the target industries list
try:
    print("Loading available industries...")
    industries_data = requests.get(AVAILABLE_INDUSTRIES_URL).json()
    # Create a set for O(1) lookup speed
    target_industries = {industry['industry'] for industry in industries_data}
    print(f"✓ Loaded {len(target_industries)} target industries.")
except Exception as e:
    print(f"Error loading industries: {e}")
    exit()


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


def get_industry_performance():
    """
    Fetches industry performance data for the past 5 trading days and calculates cumulative performance.
    """
    print(f"\nFetching industry performance data for the past 5 trading days...")
    print("=" * 40)

    # Get the past 5 trading days
    trading_days = get_trading_days(5)
    print(f"Trading days to fetch: {', '.join(trading_days)}")
    print("=" * 40)

    all_data = []

    # Fetch data for each trading day
    for date in trading_days:
        try:
            # Construct URL with date and API key
            url = f"{INDUSTRY_PERFORMANCE_URL}?date={date}&apikey={API_KEY}"
            
            print(f"Fetching data for {date}...", end=" ")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data:
                # Add date to each record for tracking
                for record in data:
                    record['fetch_date'] = date
                all_data.extend(data)
                print(f"✓ ({len(data)} records)")
            else:
                print("⚠ No data")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Error: {e}")
        except ValueError as e:
            print(f"✗ JSON Error: {e}")

    if not all_data:
        print("\n⚠ No data fetched for any trading day.")
        return None

    print(f"\n✓ Total records fetched: {len(all_data)}")

    # Convert to DataFrame
    full_df = pd.DataFrame(all_data)

    # Check if required columns exist
    if 'industry' not in full_df.columns:
        print("Error: API response does not contain 'industry' column.")
        return None

    # Filter for target industries
    df = full_df[full_df['industry'].isin(target_industries)].copy()

    if df.empty:
        print("⚠ No matching data found for the target industries.")
        return None

    print(f"✓ Filtered down to {len(df)} records matching your industry list.")

    # --- Calculate Cumulative 5-Day Performance ---
    if 'averageChange' not in df.columns:
        print(f"\nError: 'averageChange' column not found.")
        print(f"Available columns: {df.columns.tolist()}")
        return df

    # Group by industry and sum the performance across all 5 days
    cumulative_performance = df.groupby('industry')['averageChange'].sum().sort_values(ascending=False)

    # Get top 5 and worst 5
    top_5 = cumulative_performance.head(5)
    worst_5 = cumulative_performance.tail(5)

    # Print results
    print("\n" + "=" * 80)
    print("TOP 5 PERFORMING INDUSTRIES (CUMULATIVE 5-DAY PERFORMANCE)")
    print("=" * 80)
    for i, (industry, change) in enumerate(top_5.items(), 1):
        print(f"{i}. {industry:50s} {change:+.2f}%")

    print("\n" + "=" * 80)
    print("WORST 5 PERFORMING INDUSTRIES (CUMULATIVE 5-DAY PERFORMANCE)")
    print("=" * 80)
    for i, (industry, change) in enumerate(worst_5.items(), 1):
        print(f"{i}. {industry:50s} {change:+.2f}%")
    print("=" * 80 + "\n")

    # Return DataFrame with cumulative performance for charting
    result_df = pd.DataFrame({
        'industry': cumulative_performance.index,
        'cumulative_performance': cumulative_performance.values
    })

    return result_df


def create_industry_performance_chart(df):
    """
    Creates a horizontal bar chart showing top 5 and worst 5 performing industries
    sorted from maximum to minimum.
    """
    if df is None or df.empty:
        print("No data available to create chart.")
        return

    # Sort by cumulative performance descending
    df_sorted = df.sort_values('cumulative_performance', ascending=False)
    
    # Get top 5 and worst 5
    top_5 = df_sorted.head(5)
    worst_5 = df_sorted.tail(5)

    # Combine and sort from maximum to minimum
    combined = pd.concat([top_5, worst_5]).sort_values('cumulative_performance', ascending=False)

    # Create figure
    fig, ax = plt.subplots(figsize=(18, 14))

    # Colors: Top 5 (Blue), Worst 5 (Purple)
    colors = ['#5A06F5' if perf in top_5['cumulative_performance'].values else '#632E62' 
              for perf in combined['cumulative_performance']]

    # Create horizontal bar chart
    bars = ax.barh(range(len(combined)), combined['cumulative_performance'].values, 
                   color=colors, edgecolor='black', linewidth=0.5, height=0.7)

    # Customize axis
    ax.set_yticks(range(len(combined)))
    ax.set_yticklabels(combined['industry'].values, fontsize=11)
    ax.set_xlabel('Cumulative 5-Day Performance (%)', fontsize=13, fontweight='bold', labelpad=15)
    ax.set_title('Industry Performance: Top 5 vs Worst 5 (5-Day Cumulative)',
                 fontsize=16, fontweight='bold', pad=25)

    # Add value labels
    for i, (bar, value) in enumerate(zip(bars, combined['cumulative_performance'].values)):
        offset = 0.3 if value > 0 else -0.3
        ha_align = 'left' if value > 0 else 'right'
        ax.text(value + offset, i, f'{value:+.2f}%',
                va='center', ha=ha_align,
                fontsize=12, fontweight='bold')

    # Aesthetics
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.7)
    ax.set_axisbelow(True)
    ax.margins(x=0.15, y=0.02)

    # Legend
    legend_elements = [
        Patch(facecolor='#5A06F5', edgecolor='black', label='Top 5 Performers'),
        Patch(facecolor='#632E62', edgecolor='black', label='Worst 5 Performers')
    ]
    legend = ax.legend(handles=legend_elements, loc='upper right',
                       fontsize=11, frameon=True, fancybox=True, shadow=True)

    # Add source text at the bottom
    fig.text(0.5, 0.02, 'Source: Ki-Wealth | 5-Day Cumulative Performance', 
             ha='center', fontsize=10, style='italic', color='gray')

    # Adjust layout
    plt.tight_layout(rect=[0.02, 0.04, 0.98, 0.97])

    # Save and show
    output_path = 'performance_by_industry_chart_5day.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
    print(f"\n✓ Chart saved as '{output_path}'")
    plt.show()


if __name__ == "__main__":
    industry_df = get_industry_performance()
    if industry_df is not None:
        create_industry_performance_chart(industry_df)