# Stock Chart Analysis
An interactive stock chart made with  Dash and Plotly. Features include
  - open high low close candlestick marks
  - 20, 50, 200 day moving average
  - 20 day exponential moving average
  - bollinger bands
  - volume (color coded via bought or sold)

The user can
  - input what stock they wish to view
  - control time windows of a daily chart
  - control time windows of a intraday chart
  - control time period of a intraday chart
User interaction made possible by using Plotly and Dash programing

Data is used via Yahoo Finance.

stockchart_stable.py launches a Dash based browser.  The required python packages required are shown in the .py file.
beep.py is a python script that be modified to return a noise based on if a variable equals a certain value.  Ideas of alerting user if stock price or indicator is met are in development.

See video demonstrating this project on my LinkedIn: https://www.linkedin.com/posts/matthewjmccarroll_getrichordietryin-python-datanalytics-activity-6674030644026335232-jXXd
