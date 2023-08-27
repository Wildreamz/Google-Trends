"""
Google_Trends_2.1.0.0

This script provides functions to fetch and visualize Google Trends data for specified keywords over a given timeframe.
It allows users to compare the popularity of different keywords and visualize their trends over time.

Key Updates:
    - Added granularity control. Dynamically adjust segmentation to achieve target granularity.
    - Warning: potential scaling issues.

Future Updates:
    - Add ability to add suffix to search terms before comparing.
        - User-defined list of suffix    
    - Add Categories
    - Add native pytrends granularity control.
    

"""

## Import Modules -----------------------------------------------------------##

# Standard library imports
from time import sleep
from datetime import datetime, timedelta  # For date manipulations

# Third-party imports
import pandas as pd  # Data manipulation and analysis
import matplotlib.pyplot as plt  # Plotting library
import matplotlib.dates as mdates  # Date formatting for plots
import mplcursors  # Interactive data selection cursors for Matplotlib
import seaborn as sns  # Data visualization library based on Matplotlib
from pytrends.request import TrendReq  # Google Trends API

# Setting up the plotting style
sns.set()

# Close previously opened figures
plt.close('all')

## Define Functions ---------------------------------------------------------##

def divide_timeframe_range(start_date: str, end_date: str, granularity: str, num_segments: int = None):
    """
    Function to divide the timeframe based on the chosen granularity. 

    Args:
    - start_date (str): The start date in the format 'YYYY-MM-DD'
    - end_date (str): The end date in the format 'YYYY-MM-DD'
    - granularity (str): The granularity ("d" = "daily", "w" = "weekly").
    - num_segments (int, optional): The number of segments to divide the timeframe into.

    Returns:
    - list: A list of tuples, each containing the start and end dates for a segment.
    """
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    segments = []
    current_start = start_date_obj
    
    total_days = (end_date_obj - start_date_obj).days
    
    if num_segments:
        delta = timedelta(days=total_days // num_segments)
    elif granularity == "d":
        delta = timedelta(days=269)  # Divide into segments of up to 269 days for daily granularity
    elif granularity == "w":
        delta = timedelta(days=1889)  # Divide into segments of up to 1889 days for weekly granularity
    else:  # For any other granularity, return the entire date range as one segment
        return [(start_date, end_date)]
    
    while current_start < end_date_obj:
        current_end = min(current_start + delta, end_date_obj)
        segments.append((current_start.strftime('%Y-%m-%d'), current_end.strftime('%Y-%m-%d')))
        current_start = current_end + timedelta(days=1)  # Start the next segment the day after the current segment ends
        
    return segments


def determine_overall_granularity_from_data(data: pd.DataFrame):
    """Determine the granularity (gap between each datapoint) based on the actual data intervals."""
    
    # Calculate the differences between consecutive dates in the data
    date_diffs = data.index.to_series().diff().dropna().dt.days
    
    # Find the most common difference
    common_diff = date_diffs.mode().iloc[0]
    
    if common_diff == 1:
        return "daily"
    elif common_diff <= 7:
        return "weekly"
    else:
        return "monthly"

def get_data(keywords: list, timeframe_range: tuple, geo: str, youtube: bool, granularity: str):
    """
    Function to build a payload and return the trends for each keyword over time. 

    Args:
    - keywords (list): List of keywords for which to get the trends.
    - timeframe_range (tuple): Tuple containing the start and end dates as strings in 'YYYY-MM-DD' format.
    - geo (str): The geolocation for which to get the trends.
    - youtube (bool): A flag indicating whether to get trends from YouTube (True) or Google Search (False).

    Returns:
    - pandas.DataFrame: A DataFrame containing the combined trends for all keywords over time.
    """
    pytrends = TrendReq(hl='en-US', tz=360)
    segments = divide_timeframe_range(*timeframe_range, granularity)
    trends_data = []
    
    print("Number of segments:", len(segments))
    
    # granularity = determine_overall_granularity(timeframe_range, len(segments))
    # print(f"Overall granularity: {granularity}")
    
    for time_range in segments:
        pytrends.build_payload(kw_list=keywords, timeframe=' '.join(time_range), geo=geo, cat="29" if youtube else "0")
        segment_data = pytrends.interest_over_time()
        
        # Ensure all keywords are present in the segment data
        for keyword in keywords:
            if keyword not in segment_data.columns:
                segment_data[keyword] = 0  # Add missing keyword column filled with zeros
        
        trends_data.append(segment_data)
        
        # If the number of segments is greater than 20, add a 1s delay
        if len(segments) > 20:
            sleep(0.1)
    
    # Adjusting the scaling factor for each segment
    for i in range(1, len(segments)):
        for keyword in keywords:
            # Check if the DataFrame is not empty
            if not trends_data[i].empty:
                mean_current_start = trends_data[i][keyword].iloc[0]
            else:
                mean_current_start = 0  # or some default value
    
            # Check if the previous DataFrame is not empty
            if not trends_data[i-1].empty:
                mean_previous_end = trends_data[i-1][keyword].iloc[-1]
            else:
                mean_previous_end = 0  # or some default value
    
            scale_factor = mean_current_start / mean_previous_end if mean_previous_end != 0 else 1
            trends_data[i-1][keyword] *= scale_factor

    combined_data = pd.concat(trends_data)
    
    overall_granularity = determine_overall_granularity_from_data(combined_data)
    print(f"Overall granularity: {overall_granularity}")
    
    return combined_data

def plot_keyword_trends(trends_data, dpi=80, save_figure=False, figure_path='plot.png'):
    """
    Function to plot the trends for each keyword over time.

    Args:
    - trends_data (dataframe): Dataframe of Google Trends data.
    - dpi (int): The DPI for the plot.
    - save_figure (bool): A flag indicating whether to save the figure or not.
    - figure_path (str): The path to save the figure if save_figure is True.
    """

    # combined_data = pd.concat(trends_data)
    fig, ax = plt.subplots(figsize=(10, 6), dpi=dpi)
    fig.patch.set_facecolor('#19232d')
    ax.set_facecolor('#19232d')

    colors = ['#00FFFF', '#FF69B4', '#00ff99', '#ffff99', '#B2DF8A', '#32AA15']
    marker_size = 2  
    for i, keyword in enumerate(keywords):
        ax.plot(trends_data.index, trends_data[keyword], label=keyword, linewidth=2, alpha=0.9, color=colors[i % len(colors)], marker='s', markersize=marker_size)

    title = f'Google Trends - Keyword Trends\nTimeframe: {timeframe_range[0]} to {timeframe_range[1]}'
    title += '' if geo == '' else f'  Geolocation: {geo}'
    title += '  Source: YouTube Trends' if youtube else '  Source: Google Search Trends'

    ax.set_title(title, color='white')
    ax.set_ylabel('Interest over Time', color='white')
    ax.legend()
    ax.tick_params(colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    plt.xticks(rotation=45, color='white')
    plt.yticks(color='white')

    years = mdates.YearLocator()   
    years_fmt = mdates.DateFormatter('%Y')
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(years_fmt)

    # Enable cursor functionality
    cursor = mplcursors.cursor(ax)
    cursor.connect("add", lambda sel: sel.annotation.set_text(
        'Date: {}\nInterest: {:.2f}'.format(mdates.num2date(sel.target[0]).strftime('%Y-%m-%d'), sel.target[1])
    ))

    plt.tight_layout()
    if save_figure:
        plt.savefig(figure_path, dpi=dpi, facecolor='#19232d', edgecolor='#19232d')
    else:
        plt.show()

def plot_interest_ratio(trends_data, dpi=80, save_figure=False, figure_path='plot.png'):
    """
    Function to plot the ratio of search interest of Keyword 1 over Keyword 2 over time.

    Args:
    - trends_data (pandas.DataFrame): Dataframe of Google Trends data.
    - dpi (int): The DPI for the plot.
    - save_figure (bool): A flag indicating whether to save the figure or not.
    - figure_path (str): The path to save the figure if save_figure is True.
    """

    keyword1 = trends_data.columns[0]
    keyword2 = trends_data.columns[1]

    # Calculate ratio
    ratio_data = trends_data[keyword1] / trends_data[keyword2]

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6), dpi=dpi)
    fig.patch.set_facecolor('#19232d')
    ax.set_facecolor('#19232d')

    legend_label = f'{keyword1}\n/{keyword2}'
    
    ax.plot(ratio_data.index, ratio_data.values, label=legend_label, color='#FFA07A')

    title_line_1 = f'Interest Ratio Over Time ({timeframe_range[0]} - {timeframe_range[1]})'
    title_line_2 = f'Keyword 1: {keyword1}\nKeyword 2: {keyword2}'
    ax.set_title(title_line_1 + '\n' + title_line_2, color='white')
    ax.set_ylabel('Interest Ratio', color='white')
    ax.legend()
    ax.tick_params(colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    plt.xticks(rotation=45, color='white')
    plt.yticks(color='white')

    years = mdates.YearLocator()   
    years_fmt = mdates.DateFormatter('%Y')
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(years_fmt)

    # Enable cursor functionality
    cursor = mplcursors.cursor(ax)
    cursor.connect("add", lambda sel: sel.annotation.set_text(
        'Date: {}\nRatio: {:.2f}'.format(mdates.num2date(sel.target[0]).strftime('%Y-%m-%d'), sel.target[1])
    ))

    plt.tight_layout()
    if save_figure:
        plt.savefig(figure_path)
    plt.show()

def export_data_as_csv(df,csv_name):
    """
    Function to export a given pandas DataFrame to a CSV file.

    Args:
    - df (pandas.DataFrame): The DataFrame to be exported.
    - csv_name (str): The name (including path, if necessary) of the CSV file to which the data will be written.
    """
    df.to_csv(csv_name)
    return

## Main ---------------------------------------------------------------------##
        
# Set your desired parameters here
keywords = [
    "(PyTorch+PyTorch regression+PyTorch deep learning)",
    "(TensorFlow+TensorFlow regression+TensorFlow deep learning)"
]

# Get today's date
today = str(datetime.today().date())

timeframe_range = '2015-01-01', today
geo = ''
youtube = False
granularity = 'w' # 'w' for weekly, 'd' = daily, else = default

# Call the function with the defined parameters
trends_data = get_data(keywords, timeframe_range, geo, youtube, granularity)
plot_keyword_trends(trends_data, dpi=120, save_figure=False, figure_path='plot.png')
plot_interest_ratio(trends_data, dpi=120, save_figure=False, figure_path='plot.png')
# export_data_as_csv(trends_data,"Google_Trends_Data.csv")

start_date = datetime.strptime(timeframe_range[0], '%Y-%m-%d').date()
days_between = (datetime.today().date() - start_date).days
print("Days in Timeframe: " + str(days_between) + " days")
print("trends_data Start Date: " + str(trends_data.index[0].date()))
print("trends_data End Date: " + str(trends_data.index[-1].date()))
print("Run completed.")