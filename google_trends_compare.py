import argparse
import warnings
from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import time
from flask import Flask, request, render_template, send_file, redirect, url_for
from flask_cors import CORS
import os

# Suppress FutureWarnings related to fillna downcasting behavior
warnings.simplefilter(action='ignore', category=FutureWarning)

# Use 'Agg' backend for headless environments
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving plots as images

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Function to compare Google Trends of 2 or 3 keywords
def compare_google_trends(keywords, timeframe='today 12-m'):
    # Initialize pytrends
    pytrends = TrendReq(hl='en-US', tz=360)

    # Add a small delay to prevent rate limiting
    time.sleep(5)

    # Build the payload for the keywords
    pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo='', gprop='')

    # Retrieve interest over time
    trends_data = pytrends.interest_over_time()

    # Check if any data is available
    if trends_data.empty:
        return None

    # Drop the 'isPartial' column if it exists
    trends_data = trends_data.drop(labels=['isPartial'], axis='columns', errors='ignore')

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot each keyword with a label and different colors
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Color list for each line
    for i, keyword in enumerate(keywords):
        ax.plot(trends_data.index, trends_data[keyword], label=keyword, linewidth=2, color=colors[i % len(colors)])

    # Set title and labels
    ax.set_title('Google Trends Comparison', fontsize=16, weight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Interest Over Time', fontsize=12)

    # Format x-axis for dates (daily ticks)
    ax.xaxis.set_major_locator(mdates.DayLocator())  # Set locator to days
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # Show date format as Year-Month-Day

    # Rotate the x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')

    # Add a grid for better readability
    ax.grid(True, which='both', linestyle='--', linewidth=0.7)

    # Add a legend to identify the keywords
    ax.legend(title="Keywords", loc='upper right', fontsize=10)

    # Adjust layout for better spacing
    plt.tight_layout()

    # Save the plot to an image file
    plot_filename = "static/google_trends_comparison.png"
    plt.savefig(plot_filename)
    plt.close()

    return plot_filename

# Route for the web interface
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle form submission and show the comparison
@app.route('/compare', methods=['POST'])
def compare():
    # Get the form data
    keyword1 = request.form.get('keyword1')
    keyword2 = request.form.get('keyword2')
    keyword3 = request.form.get('keyword3')
    timeframe = request.form.get('timeframe', 'today 12-m')

    # Prepare the keywords list
    keywords = [keyword1, keyword2]
    if keyword3:
        keywords.append(keyword3)

    # Generate the comparison plot
    plot_filename = compare_google_trends(keywords, timeframe)
    if not plot_filename:
        return "No data available for the given keywords."

    # Redirect to the display page
    return redirect(url_for('display_image'))

# Route to display the generated image
@app.route('/image')
def display_image():
    return render_template('image.html')

# Run the Flask server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
