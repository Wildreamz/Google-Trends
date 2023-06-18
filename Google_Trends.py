# Standard library imports
from datetime import datetime, timedelta

# Third-party imports
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplcursors
import seaborn as sns
from pytrends.request import TrendReq


sns.set()
plt.close('all')

def divide_timeframe_range(start_date: str, end_date: str) -> tuple:
    """
    Function to divide the timeframe into two halves. 

    Args:
    start_date: str -> The start date in the format 'YYYY-MM-DD'
    end_date: str -> The end date in the format 'YYYY-MM-DD'

    Returns:
    tuple -> The start, midpoint, and end dates as strings in 'YYYY-MM-DD' format.
    """
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    midpoint_date_obj = start_date_obj + (end_date_obj - start_date_obj) / 2
    return start_date_obj.strftime('%Y-%m-%d'), midpoint_date_obj.strftime('%Y-%m-%d'), end_date_obj.strftime('%Y-%m-%d')

def get_trends_data(keywords: list, timeframe_range: tuple, geo: str, youtube=True):
    """
    Generator function to build a payload and yield the trends for each keyword over time. 

    Args:
    keywords: list -> List of keywords for which to get the trends.
    timeframe_range: tuple -> Tuple containing the start and end dates as strings in 'YYYY-MM-DD' format.
    geo: str -> The geolocation for which to get the trends.
    youtube: bool -> A flag indicating whether to get trends from YouTube (True) or Google Search (False).

    Yields:
    DataFrame -> A DataFrame containing the trends for each keyword over time.
    """
    pytrends = TrendReq(hl='en-US', tz=360)
    start_date, midpoint_date, end_date = divide_timeframe_range(*timeframe_range)
    for time_range in [(start_date, midpoint_date), (midpoint_date, end_date)]:
        pytrends.build_payload(kw_list=keywords, timeframe=' '.join(time_range), geo=geo, cat="29" if youtube else "0")
        yield pytrends.interest_over_time()

def plot_keyword_trends(keywords: list, timeframe_range: tuple, geo: str, youtube=True, dpi=80, save_figure=False, figure_path='plot.png'):
    """
    Function to plot the trends for each keyword over time.

    Args:
    keywords: list -> List of keywords for which to plot the trends.
    timeframe_range: tuple -> Tuple containing the start and end dates as strings in 'YYYY-MM-DD' format.
    geo: str -> The geolocation for which to plot the trends.
    youtube: bool -> A flag indicating whether to plot trends from YouTube (True) or Google Search (False).
    dpi: int -> The DPI for the plot.
    save_figure: bool -> A flag indicating whether to save the figure or not.
    figure_path: str -> The path to save the figure if save_figure is True.
    """
    trends_data = list(get_trends_data(keywords, timeframe_range, geo, youtube))
    for keyword in keywords:
        mean_second_half_start = trends_data[1][keyword].iloc[0]
        mean_first_half_end = trends_data[0][keyword].iloc[-1]
        scale_factor = mean_second_half_start / mean_first_half_end if mean_first_half_end != 0 else 1
        trends_data[0][keyword] *= scale_factor

    combined_data = pd.concat(trends_data)
    fig, ax = plt.subplots(figsize=(10, 6), dpi=dpi)
    fig.patch.set_facecolor('#19232d')
    ax.set_facecolor('#19232d')

    colors = ['#00FFFF', '#FF69B4', '#00ff99', '#ffff99', '#B2DF8A', '#32AA15']
    marker_size = 2  
    for i, keyword in enumerate(keywords):
        ax.plot(combined_data.index, combined_data[keyword], label=keyword, linewidth=2, alpha=0.9, color=colors[i % len(colors)], marker='s', markersize=marker_size)

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

def plot_interest_ratio(keywords, timeframe_range, geo=None, youtube=True, dpi=80, save_figure=False, figure_path='plot.png'):
    """
    Function to plot the ratio of search interest of Keyword 1 over Keyword 2 over time.

    Args:
    keywords: list -> List of two keywords.
    timeframe_range: tuple -> Tuple containing the start and end dates as strings in 'YYYY-MM-DD' format.
    geo: str or None -> The geolocation for which to plot the trends. If None or an empty string (''), global trends will be used.
    youtube: bool -> A flag indicating whether to use data from YouTube (True) or Google Search (False).
    dpi: int -> The DPI for the plot.
    save_figure: bool -> A flag indicating whether to save the figure or not.
    figure_path: str -> The path to save the figure if save_figure is True.
    """
    keyword1 = keywords[0]
    keyword2 = keywords[1]

    trends_data = list(get_trends_data([keyword1, keyword2], timeframe_range, geo, youtube))

    # Combine two halves
    combined_data = pd.concat(trends_data)
    
    # Calculate ratio
    ratio_data = combined_data[keyword1] / combined_data[keyword2]

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


        
# Set your desired parameters here
keywords = [
    "(PyTorch+PyTorch regression+PyTorch deep learning)",
    "(TensorFlow+TensorFlow regression+TensorFlow deep learning)"
]

timeframe_range = '2015-01-01', '2023-06-15'
geo = ''
youtube = 0

# Call the function with the defined parameters
plot_keyword_trends(keywords, timeframe_range, geo, youtube = youtube, dpi=120, save_figure=False, figure_path='plot.png')
plot_interest_ratio(keywords, timeframe_range, geo, youtube = youtube, dpi=120, save_figure=False, figure_path='plot.png')
