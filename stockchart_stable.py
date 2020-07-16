# Created by Matthew McCarroll 5/16/2020

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import datetime
from dateutil.relativedelta import *

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
# import warnings
# warnings.filterwarnings("ignore", category=DeprecationWarning)
import re
import yfinance as yf
from pandas_datareader import data as pdr

from chart_studio.plotly import plot, iplot
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from tkinter import * 
from tkinter.ttk import *

# creating tkinter window 
root = Tk() 
# getting screen"s height in pixels 
height_screen = root.winfo_screenheight() 
# getting screen"s width in pixels 
width_screen = root.winfo_screenwidth() 
# print("\n width x height = %d x %d (in pixels)\n" %(width_screen, height_screen)) 

time_buttons_period_daily=["2y","1y","6mo","3mo","1mo"]
time_buttons_period_intraday=["5d","4d","3d","2d","1d",'4h']
time_buttons_interval_intraday=["60m","30m","15m","5m",'1m']

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

app_color = {"graph_bg": "#082255"}

app.layout = html.Div(
	[
		# # header

		html.Div(
			[

			html.Div(
				[
					html.H5("Stock Screener", className="app_header_title")
				],
    			style={"width": "33%","display":"inline-block"}
			),


			# stock input
			html.Div(
				[
					dcc.Input(id="input-state-1", type="text", value="WMT"
					),
				    html.Button(id="submit-button-state", n_clicks=0, children="Submit"
				    )
				],
	    		style={"width": "33%","display":"inline-block"}
			),

			html.Div(
				[
		   			html.Div( id='live-update-time'),
		   			dcc.Interval(
            		id='interval-component-time',
            		interval=1*1000, # in milliseconds
            		n_intervals=0
        			)
				],
	    		style={"width": "33%","display":"inline-block"}
	    	),
			],
	    	style={
				"backgroundColor": "rgb(250, 250, 200)",
				"padding": "0px 0px"}

		),
		# buttons 
		html.Div(
			[
				html.Div(
					[
						html.H5("Daily Candlestick Chart: Select Period Span"),    		
						dcc.RadioItems(
			    			id="daily-period-frame",
			        		options=[{"label": i, "value": i} for i in time_buttons_period_daily],
			        		value="2y", 
			        		labelStyle={"display":"inline-block"}
	        			)
	        		],
	    			style={"width": "33%","display":"inline-block"}
	    		),

				html.Div(
					[
					   	html.H5("Intraday Candlestick: Select Period Span"),
						dcc.RadioItems(
				    		id="intraday-period-frame",
				        	options=[{"label": i, "value": i} for i in time_buttons_period_intraday],
				        	value="5d", 
				        	labelStyle={"display":"inline-block"}
				        )
				    ],
	    			style={"width": "33%","display":"inline-block"}
	    		),

				html.Div(
					[

				        html.H5("Intraday Interval: Select Time Span"),
						dcc.RadioItems(
				    		id="intraday-interval-frame",
				        	options=[{"label": i, "value": i} for i in time_buttons_interval_intraday],
				        	value="60m", labelStyle={"display":"inline-block"}
				        )
				    ],
				    style={"width": "33%","display":"inline-block"}
			    )
		    ],
	    	style={
				"borderBottom": "thick black solid",
				"backgroundColor": "rgb(250, 250, 200)",
				"padding": "5px 5px"}
	    ),

		# graphs
		html.Div(
			[
			    html.Div(
			    	[   
			    		html.H5('Daily Graph'),
			   			dcc.Graph(id="daily-graph",figure=dict(layout=dict(plot_bgcolor=app_color["graph_bg"])))
			   		],
				    style={"width": "48%","display":"inline-block"},
			   		className="six columns"
			   	),

		   		html.Div(
		   			[
		   				html.H5('Intraday Graph Generated '+ str(datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S"))),
			   			dcc.Graph(id="intraday-graph",figure=dict(layout=dict(plot_bgcolor=app_color["graph_bg"])))
			   		],
				    style={"width": "48%","display":"inline-block","float":"right"},
			   		className="six columns"
			   	)
			],
			className="row",
	    	style={
				"backgroundColor": "rgb(250, 250, 200)"}

		)
	]
)


def stock_metrics(OHLCV_data):

	#########################################################################################
	##########                MOVING AVERAGES AND BOLLINGER BANDS                  ##########
	#########################################################################################

	OHLCV_data["expMA"] = OHLCV_data["close"].ewm(span=20, min_periods=0, adjust=False).mean()
	OHLCV_data["twenty_day"]= OHLCV_data["close"].rolling(window=20).mean()
	OHLCV_data["fifty_day"]= OHLCV_data["close"].rolling(window=50).mean()
	OHLCV_data["twoHundred_day"]= OHLCV_data["close"].rolling(window=200).mean()
	OHLCV_data["bolupp"]=OHLCV_data["twenty_day"]+(2*OHLCV_data["close"].rolling(window=20).std())
	OHLCV_data["bollow"]=OHLCV_data["twenty_day"]-(2*OHLCV_data["close"].rolling(window=20).std())

	#########################################################################################
	##########                RELATIVE STRENGTH INDEX                              ##########
	#########################################################################################

	period=14
	delta = OHLCV_data["close"].diff() 
	up, down = delta.copy(), delta.copy()

	up[up < 0] = 0
	down[down > 0] = 0
	# Calculate the exponential moving averages (EWMA)
	roll_up = up.ewm(com=period - 1, adjust=False).mean()
	roll_down = down.ewm(com=period - 1, adjust=False).mean().abs()
	# Calculate RS based on exponential moving average (EWMA)
	rs = roll_up / roll_down   # relative strength =  average gain/average loss
	rsi = 100-(100/(1+rs))
	OHLCV_data["RSI"] = rsi

	#########################################################################################
	##########      ASSIGN CANDLESTICK AND VOLUME GAIN LOSS DIRECTION              ##########
	#########################################################################################

	OHLCV_data["direction"] = ["increasing" if OHLCV_data.loc[i,"close"] >= OHLCV_data.loc[i,"open"] else "decreasing" for i in OHLCV_data.index]
	OHLCV_data["color"] = ["forestgreen" if OHLCV_data.loc[i,"direction"] == "increasing" else "red" for i in OHLCV_data.index]

	return OHLCV_data

@app.callback(Output("daily-graph", "figure"),
              [Input("submit-button-state","n_clicks"),
               Input("daily-period-frame","value")],
              [State("input-state-1", "value")])

def update_daily_graph(n_clicks, time_value, input_symbol_value):

	ticker=yf.Ticker(input_symbol_value)
	OHLCV_data=pd.DataFrame()
	OHLCV_data = ticker.history(period="5y")
	OHLCV_data = OHLCV_data.reset_index(drop=False)

	num_xticks=20

	present_time = datetime.datetime.now()

	columns = OHLCV_data.columns
	columns = [x.lower() for x in columns]
	OHLCV_data.columns = columns
	
	stock_metrics(OHLCV_data)
	#########################################################################################
	##########                   ASSIGN DATE WINDOW                                ##########
	#########################################################################################

	if time_value =="2y":
		mask = (OHLCV_data["date"] >= present_time + relativedelta(years=-2))
	elif time_value =="1y":
		mask = (OHLCV_data["date"] >= present_time + relativedelta(years=-1))
	elif time_value =="6mo":
		mask = (OHLCV_data["date"] >= present_time + relativedelta(months=-6))
	elif time_value =="3mo":
		mask = (OHLCV_data["date"] >= present_time + relativedelta(months=-3))
	else:
		mask = (OHLCV_data["date"] >= present_time + relativedelta(months=-1))

	OHLCV_data["date"] = OHLCV_data["date"].dt.strftime("%m-%d-%Y      ")


	#########################################################################################
	##########              SET CANDLESTICK YAXIS BOUNDS                           ##########
	#########################################################################################

	subset = OHLCV_data[["open","high","low","close","bolupp","bollow"]].columns
	candle_low = OHLCV_data.loc[mask,subset].min().min()
	candle_high = OHLCV_data.loc[mask,subset].max().max()

	#########################################################################################
	##########                   SET RSI 70 / 30 LINES                             ##########
	#########################################################################################

	rsiupL =[OHLCV_data.loc[mask,"date"].iloc[0],OHLCV_data.loc[mask,"date"].iloc[-1]]
	rsiupR =[70,70]

	rsidownL =[OHLCV_data.loc[mask,"date"].iloc[0],OHLCV_data.loc[mask,"date"].iloc[-1]]
	rsidownR =[30,30]
	rsimidL =[OHLCV_data.loc[mask,"date"].iloc[0],OHLCV_data.loc[mask,"date"].iloc[-1]]
	rsimidR =[50,50]

	fig = make_subplots(rows=3,cols=1,shared_xaxes=True,vertical_spacing=0.03, row_width=[0.2,0.6,0.2])

	# RSI
	fig.add_trace(
	    go.Scatter(
	        name="RSI "+ "{:.2f}".format(OHLCV_data["RSI"].iloc[-1]),
	        hoverlabel=dict(font=dict(size=20),align="right"),
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["RSI"].loc[mask],
	        mode="lines",	        
	        line=dict(color="black", width=2),
	        yaxis="y1",hovertemplate = "RSI: %{y:.2f}"+ "<extra></extra>"),row=1,col=1
	)
	# RSI 70
	fig.add_trace(
	    go.Scatter(
	        name="RSI 70",
	        mode="lines",showlegend=False,hoverinfo="none",
	        x=rsiupL,y=rsiupR,line=dict(color="black", width=2),
	        yaxis="y1"),row=1,col=1
	)
	# RSI 50
	fig.add_trace(
	    go.Scatter(
	        name="RSI 50",
	        mode="lines",showlegend=False,hoverinfo="none",
	        x=rsimidL,y=rsimidR,line=dict(color="black", width=2,dash="dot"),yaxis="y1"),row=1,col=1
	)
	# RSI 30
	fig.add_trace(
	    go.Scatter(
	        name="RSI 30",
	        mode="lines",showlegend=False,hoverinfo="none",
	        x=rsidownL,y=rsidownR,line=dict(color="black", width=2),yaxis="y1"),row=1,col=1
	)

	bollinecolor="rgba(0,0,20,1)"
	# Bollinger Bands - upper
	fig.add_trace(
	    go.Scatter(
	        fill=None,
	        mode="lines",
	        hoverlabel=dict(font=dict(size=20),align="right",namelength=0),
			hovertemplate = "BB(UP): %{y:$.2f}"+ "<extra></extra>",
	        line_color=bollinecolor,
	        yaxis="y21",
	        name="bollup",
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["bolupp"].loc[mask],
	        line=dict(width=2,dash="dot"),	        
	        showlegend=False),row=2,col=1
	)

	# Bollinger Bands - lower
	fig.add_trace(
	    go.Scatter(
	        # fill="tonexty",
	        mode="lines",
	        hoverlabel=dict(font=dict(size=20),align="right",namelength=0),
			hovertemplate = "BB(LOW): %{y:$.2f}"+ "<extra></extra>", 
	        line_color=bollinecolor,
	        # fillcolor=bollinecolor,
	        name="bollow",
	        yaxis="y21",
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["bollow"].loc[mask],
	        line=dict(width=2,dash="dot"),
	        showlegend=False),row=2,col=1
	)
	# Candlesticks
	fig.add_trace(
	    go.Candlestick(
	        name = str(input_symbol_value),
	        showlegend=False,
	        hoverlabel=dict(font=dict(size=20),align="left",namelength=0),
	        x=OHLCV_data["date"].loc[mask],
	        open=round(OHLCV_data["open"].loc[mask],2),
	        high=round(OHLCV_data["high"].loc[mask],2),
	        low=round(OHLCV_data["low"].loc[mask],2),
	        close=round(OHLCV_data["close"].loc[mask],2),
	        decreasing=dict(line=dict(color="red"),fillcolor="red"),
	        increasing=dict(line=dict(color="forestgreen"),fillcolor="forestgreen"),yaxis="y2"),row=2,col=1)

	# 20 day EMA
	fig.add_trace(
	    go.Scatter(
	        name="ExpMA(20) "+ "{:.2f}".format(OHLCV_data["expMA"].iloc[-1]),
	    	hoverlabel=dict(font=dict(size=20),align="right"),
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["expMA"].loc[mask],
	        mode="lines",	       
	        line=dict(color="orange", width=2),yaxis="y2",hovertemplate = "20EMA: %{y:$.2f}"+ "<extra></extra>"),row=2,col=1
	    )

	# 20 day SMA
	fig.add_trace(
	    go.Scatter(
	        name="MA(20) "+ "{:.2f}".format(OHLCV_data["twenty_day"].iloc[-1]),
	    	hoverlabel=dict(font=dict(size=20),align="right"),
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["twenty_day"].loc[mask],
	        mode="lines",	        
	        line=dict(color="yellow", width=2),yaxis="y2",hovertemplate = "20MA: %{y:$.2f}"+ "<extra></extra>"),row=2,col=1
	    )

	# 50 day SMA
	fig.add_trace(
	    go.Scatter(
	        name="MA(50) "+ "{:.2f}".format(OHLCV_data["fifty_day"].iloc[-1]),
		    hoverlabel=dict(font=dict(size=20),align="right"),
	        x=OHLCV_data["date"].loc[mask],
	        mode="lines",	        
	        y=OHLCV_data["fifty_day"].loc[mask],line=dict(color="blue", width=2),yaxis="y2",cliponaxis=True,hovertemplate = "50MA: %{y:$.2f}"+ "<extra></extra>"),row=2,col=1
	    )

	# 200 day SMA
	fig.add_trace(
	    go.Scatter(
		cliponaxis=True,
	        name="MA(200) "+ "{:.2f}".format(OHLCV_data["twoHundred_day"].iloc[-1]),
	        hoverlabel=dict(font=dict(size=20),align="right"),	        
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["twoHundred_day"].loc[mask],line=dict(color="purple", width=2),yaxis="y2",hovertemplate = "200MA: %{y:$.2f}"+ "<extra></extra>",
	        mode="lines"),row=2,col=1
	    
	    )

	# volume
	fig.add_trace(
	    go.Bar(
	        name="volume",
	        showlegend=False,
	        hoverlabel=dict(font=dict(size=20),align="left",namelength=0),

	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["volume"].loc[mask],marker_color=OHLCV_data["color"].loc[mask],yaxis="y3"), row=3,col=1
	    )

	# fig.update_layout(yaxis2=dict(overlaying="y2",layer="below traces"))

	fig.update_layout(
	    title=dict(
	        text=input_symbol_value.upper()+". "+
	        str((present_time+relativedelta(days=-1)).strftime("%Y-%m-%d"))+
	        ". Open: "+"{:.2f}".format(OHLCV_data["open"].iloc[-1])+
	        ". High: "+"{:.2f}".format(OHLCV_data["high"].iloc[-1])+
	        ". Low: "+"{:.2f}".format(OHLCV_data["low"].iloc[-1])+
	        ". Close: "+"{:.2f}".format(OHLCV_data["close"].iloc[-1])+
	        ". Volume: "+"{:.2f}".format(OHLCV_data["volume"].iloc[-1]),
	        xanchor="left",yanchor="top",
	        x=0,
	        y=.98,
	        font=dict(color="black",family="Arial",size=18)),
	    legend=dict(
	        x=0,
	        y=1.12,
	        xanchor="left",
	        traceorder="normal",
	        font=dict(
	            family="Arial",
	            size=16,
	            color="black"
	        ),
	        bgcolor="white",
	        bordercolor="Black",
	        borderwidth=2,orientation="h"
	    ),
		autosize=False,
		height=900,
		# width=700,
		margin={"l": 0, "b": 30, "t": 120},
		hovermode="x")
	



	# Update yaxis properties
	fig.update_layout(yaxis1=dict(tickangle=0,
	                 showline=True, linewidth=1.5, linecolor="black", mirror=True,
	                 showgrid=False, gridwidth=.5, gridcolor="black",
	                 tickfont=dict(family="Arial", color="black", size=18),nticks=6, range=[10,90]
	                 ))

	fig.update_layout(yaxis2=dict(tickangle=0,
	                 showline=True, linewidth=2, linecolor="black", mirror="allticks",
	                 showgrid=True, gridwidth=1, gridcolor="black",
	                 tickfont=dict(family="Arial", color="black", size=18),fixedrange=False,
	                              range =[candle_low-candle_low*0.01,candle_high+candle_high*0.01],autorange=True,
	                 nticks=20,tickformat="$.2f"
	                 ))

	fig.update_layout(yaxis3=dict(tickangle=0,
	                 showline=True, linewidth=2, linecolor="black", mirror="ticks",
	                 showgrid=True, gridwidth=1, gridcolor="black",
	                 tickfont=dict(family="Arial", color="black", size=18)
	                 ))

	# richard drew 9/11
	
	num_xticks=20
	fig.update_layout(xaxis1=dict(type="category",nticks=num_xticks,tickangle=45,fixedrange=False,
	                 showline=True, linewidth=1.5, linecolor="black", mirror=True,
	                 showgrid=True, gridwidth=.05, gridcolor="black", tickfont=dict(family="Arial", color="black", size=14)))


	fig.update_layout(xaxis2=dict(
	    type="category",nticks=num_xticks,tickangle=45, rangemode="tozero",fixedrange=False,
	    showline=True, linewidth=1.5, linecolor="black", mirror=True,
	    showgrid=True, gridwidth=.05, gridcolor="black", tickfont=dict(family="Arial", color="black", size=14),
	    rangeslider=dict(visible=True,thickness=0)))


	fig.update_layout(xaxis3=dict(type="category",nticks=num_xticks,tickangle=35, rangemode="tozero",fixedrange=False,
	                 showline=True, linewidth=1.5, linecolor="black", mirror=True,
	                 showgrid=True, gridwidth=.05, gridcolor="black", tickfont=dict(family="Arial", color="black", size=18),
	                 rangeslider=dict(visible=True,thickness=0)))

	fig.update_layout(paper_bgcolor="rgb(250, 250, 200)")
	return fig

@app.callback(Output("intraday-graph", "figure"),
              [Input("submit-button-state","n_clicks"),
               Input("intraday-interval-frame","value"),
               Input("intraday-period-frame","value")],
              [State("input-state-1", "value")])

def update_intraday_graph(n_clicks, interval_value, period_value, input_symbol_value):
	num_xticks=20
	OHLCV_data=pd.DataFrame()
	present_time = datetime.datetime.now()
	day_of_week = datetime.datetime.now().weekday()
	ticker=yf.Ticker(input_symbol_value)
	if interval_value=='1m':
		OHLCV_data=ticker.history(interval=interval_value, start=present_time+relativedelta(days=-6),end=present_time)
	else:
		OHLCV_data=ticker.history(interval=interval_value, start=present_time+relativedelta(days=-59),end=present_time)

	OHLCV_data = OHLCV_data.reset_index(drop=False)

	columns = OHLCV_data.columns
	columns = [x.lower() for x in columns]
	OHLCV_data.columns = columns
	OHLCV_data=OHLCV_data.rename(columns={"datetime":"date"})
	OHLCV_data["date"]= OHLCV_data["date"].dt.tz_localize(None)

	OHLCV_data=OHLCV_data.drop(OHLCV_data.index[0]) # first row is blank
	OHLCV_data=OHLCV_data.drop(OHLCV_data.index[-1]) # last row is blank

	stock_metrics(OHLCV_data)

	#########################################################################################
	##########                   ASSIGN DATE WINDOW                                ##########
	#########################################################################################

	if period_value =="5d":
		if day_of_week ==5:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-8))
		elif day_of_week ==6:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-9))
		else:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-7))

	elif period_value =="4d":
		if day_of_week ==5:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-7))
		elif day_of_week ==6:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-8))
		else:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-6))

	elif period_value =="3d":
		if day_of_week ==5:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-6))
		elif day_of_week ==6:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-7))
		else:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-5))

	elif period_value =="2d":
		if day_of_week ==5:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-4))
		elif day_of_week ==6:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-5))
		else:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-3))

	elif period_value =="1d":
		if day_of_week ==5:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-3))
		elif day_of_week ==6:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-4))
		else:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-2))

	else:
		if day_of_week ==5:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-3)+ relativedelta(hours=-4))
		elif day_of_week ==6:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(days=-4))
		else:
			mask = (OHLCV_data["date"] >= present_time + relativedelta(hours=-4))


	# OHLCV_data["date"] = OHLCV_data["date"].dt.strftime("%H:%M:%S %m-%d-%Y")
	OHLCV_data["date"]=pd.to_datetime(OHLCV_data["date"])
	OHLCV_data = OHLCV_data.sort_values(by="date",ascending=True)
	OHLCV_data["date"] = OHLCV_data["date"].dt.strftime("%H:%M %m-%d-%Y")

	#########################################################################################
	##########              SET CANDLESTICK YAXIS BOUNDS                           ##########
	#########################################################################################

	#########################################################################################
	##########              SET CANDLESTICK YAXIS BOUNDS                           ##########
	#########################################################################################

	subset = OHLCV_data[["open","high","low","close","bolupp","bollow"]].columns
	candle_low = OHLCV_data.loc[mask,subset].min().min()
	candle_high = OHLCV_data.loc[mask,subset].max().max()

	#########################################################################################
	##########                   SET RSI 70 / 30 LINES                             ##########
	#########################################################################################

	rsiupL =[OHLCV_data.loc[mask,"date"].iloc[0],OHLCV_data.loc[mask,"date"].iloc[-1]]
	rsiupR =[70,70]

	rsidownL =[OHLCV_data.loc[mask,"date"].iloc[0],OHLCV_data.loc[mask,"date"].iloc[-1]]
	rsidownR =[30,30]
	rsimidL =[OHLCV_data.loc[mask,"date"].iloc[0],OHLCV_data.loc[mask,"date"].iloc[-1]]
	rsimidR =[50,50]

	fig = make_subplots(rows=3,cols=1,shared_xaxes=False,vertical_spacing=0.03, row_width=[0.2,0.6,0.2])

	# RSI
	fig.add_trace(
	    go.Scatter(
	        name="RSI "+ "{:.2f}".format(OHLCV_data["RSI"].iloc[-1]),
	        hoverlabel=dict(font=dict(size=20),align="right"),
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["RSI"].loc[mask],
	        mode="lines",	        
	        line=dict(color="black", width=2),
	        yaxis="y1",hovertemplate = "RSI: %{y:.2f}"+ "<extra></extra>"),row=1,col=1
	)
	# RSI 70
	fig.add_trace(
	    go.Scatter(
	        name="RSI 70",
	        mode="lines",showlegend=False,hoverinfo="none",
	        x=rsiupL,y=rsiupR,line=dict(color="black", width=2),
	        yaxis="y1"),row=1,col=1
	)
	# RSI 50
	fig.add_trace(
	    go.Scatter(
	        name="RSI 50",
	        mode="lines",showlegend=False,hoverinfo="none",
	        x=rsimidL,y=rsimidR,line=dict(color="black", width=2,dash="dot"),yaxis="y1"),row=1,col=1
	)
	# RSI 30
	fig.add_trace(
	    go.Scatter(
	        name="RSI 30",
	        mode="lines",showlegend=False,hoverinfo="none",
	        x=rsidownL,y=rsidownR,line=dict(color="black", width=2),yaxis="y1"),row=1,col=1
	)

	bollinecolor="rgba(0,0,0,1)"
	# Bollinger Bands - upper
	fig.add_trace(
	    go.Scatter(
	        fill=None,
	        mode="lines",
	        hoverlabel=dict(font=dict(size=20),align="right",namelength=0),
			hovertemplate = "BB(UP): %{y:$.2f}"+ "<extra></extra>",
	        line_color=bollinecolor,
	        yaxis="y21",
	        name="bollup",
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["bolupp"].loc[mask],
	        line=dict(width=2,dash="dot"),
	        showlegend=False),row=2,col=1
	)

	# Bollinger Bands - lower
	fig.add_trace(
	    go.Scatter(
	        # fill="tonexty",
	        mode="lines",
	        hoverlabel=dict(font=dict(size=20),align="right",namelength=0),
			hovertemplate = "BB(LOW): %{y:$.2f}"+ "<extra></extra>", 
	        line_color=bollinecolor,
	        # fillcolor=bollinecolor,
	        name="bollow",
	        yaxis="y21",
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["bollow"].loc[mask],
	        line=dict(width=2,dash="dot"),
	        showlegend=False),row=2,col=1
	)
	# Candlesticks
	fig.add_trace(
	    go.Candlestick(
	        name = str(input_symbol_value),
	        showlegend=False,
	        hoverlabel=dict(font=dict(size=20),align="left",namelength=0),
	        x=OHLCV_data["date"].loc[mask],
	        open=round(OHLCV_data["open"].loc[mask],2),
	        high=round(OHLCV_data["high"].loc[mask],2),
	        low=round(OHLCV_data["low"].loc[mask],2),
	        close=round(OHLCV_data["close"].loc[mask],2),
	        decreasing=dict(line=dict(color="red"),fillcolor="red"),
	        increasing=dict(line=dict(color="forestgreen"),fillcolor="forestgreen"),yaxis="y2"),row=2,col=1)

	# 20 day EMA
	fig.add_trace(
	    go.Scatter(
	        name="ExpMA(20) "+ "{:.2f}".format(OHLCV_data["expMA"].iloc[-1]),
	    	hoverlabel=dict(font=dict(size=20),align="right"),
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["expMA"].loc[mask],
	        mode="lines",	       
	        line=dict(color="orange", width=2),yaxis="y2",hovertemplate = "20EMA: %{y:$.2f}"+ "<extra></extra>"),row=2,col=1
	    )

	# 20 day SMA
	fig.add_trace(
	    go.Scatter(
	        name="MA(20) "+ "{:.2f}".format(OHLCV_data["twenty_day"].iloc[-1]),
	    	hoverlabel=dict(font=dict(size=20),align="right"),
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["twenty_day"].loc[mask],
	        mode="lines",	        
	        line=dict(color="yellow", width=2),yaxis="y2",hovertemplate = "20MA: %{y:$.2f}"+ "<extra></extra>"),row=2,col=1
	    )

	# 50 day SMA
	fig.add_trace(
	    go.Scatter(
	        name="MA(50) "+ "{:.2f}".format(OHLCV_data["fifty_day"].iloc[-1]),
		    hoverlabel=dict(font=dict(size=20),align="right"),
	        x=OHLCV_data["date"].loc[mask],
	        mode="lines",	        
	        y=OHLCV_data["fifty_day"].loc[mask],line=dict(color="blue", width=2),yaxis="y2",cliponaxis=True,hovertemplate = "50MA: %{y:$.2f}"+ "<extra></extra>"),row=2,col=1
	    )

	# 200 day SMA
	fig.add_trace(
	    go.Scatter(
		cliponaxis=True,
	        name="MA(200) "+ "{:.2f}".format(OHLCV_data["twoHundred_day"].iloc[-1]),
	        hoverlabel=dict(font=dict(size=20),align="right"),	        
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["twoHundred_day"].loc[mask],line=dict(color="purple", width=2),yaxis="y2",hovertemplate = "200MA: %{y:$.2f}"+ "<extra></extra>",
	        mode="lines"),row=2,col=1
	    
	    )

	# volume
	fig.add_trace(
	    go.Bar(
	        name="volume",
	        showlegend=False,
	        hoverlabel=dict(font=dict(size=20),align="left",namelength=0),

	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["volume"].loc[mask],marker_color=OHLCV_data["color"].loc[mask],yaxis="y3"), row=3,col=1
	    )

	# fig.update_layout(yaxis2=dict(overlaying="y2",layer="below traces"))

	fig.update_layout(

	    # plot_bgcolor="rgba(255,255,255,0)",
	    # paper_bgcolor="rgba(0,0,0,0)",
	    title=dict(
	        text=input_symbol_value.upper()+". "+
	        str(present_time.strftime("%Y-%m-%d %H:%M:%S"))+
	        ". Open: "+"{:.2f}".format(OHLCV_data["open"].iloc[-1])+
	        ". High: "+"{:.2f}".format(OHLCV_data["high"].iloc[-1])+
	        ". Low: "+"{:.2f}".format(OHLCV_data["low"].iloc[-1])+
	        ". Close: "+"{:.2f}".format(OHLCV_data["close"].iloc[-1])+
	        ". Volume: "+"{:.1f}".format(OHLCV_data["volume"].iloc[-1]),
	        xanchor="left",yanchor="top",
	        x=0,
	        y=.98,

	        font=dict(color="black",family="Arial",size=18)),
	    legend=dict(
	        x=0,
	        y=1.12,
	        xanchor="left",
	        traceorder="normal",
	        font=dict(
	            family="Arial",
	            size=16,
	            color="black"
	        ),
	        bgcolor="white",
	        bordercolor="Black",
	        borderwidth=2,orientation="h"
	    ),
		autosize=True,
		height=900,
		margin={"l": 0, "b": 30, "t": 120},
		hovermode="x")
	
	# fig.update_xaxes(showspikes=True,spikecolor="black",spikethickness=2)
	# fig.update_yaxes(showspikes=True,spikecolor="black",spikethickness=2)
	# fig.update_layout(spikedistance=1000, hoverdistance=1000)


	# Update yaxis properties
	fig.update_layout(yaxis1=dict(tickangle=0,
	                 showline=True, linewidth=1.5, linecolor="black", mirror='allticks',
	                 showgrid=False, gridwidth=1, gridcolor="black",
	                 tickfont=dict(family="Arial", color="black", size=18),nticks=6, range=[10,90]
	                 ))

	fig.update_layout(yaxis2=dict(tickangle=0,
	                 showline=True, linewidth=1.5, linecolor="black", mirror="allticks",
	                 showgrid=True, gridwidth=1, gridcolor="black",
	                 tickfont=dict(family="Arial", color="black", size=18),fixedrange=False,
	                			range =[candle_low-candle_low*0.01,candle_high+candle_high*0.01],autorange=True,
	                 nticks=20,tickformat="$.2f"
	                 ))

	fig.update_layout(yaxis3=dict(tickangle=0,
	                 showline=True, linewidth= 1.5, linecolor="black", mirror="allticks",
	                 showgrid=True, gridwidth=1, gridcolor="black",
	                 tickfont=dict(family="Arial", color="black", size=18)
	                 ))


	
	fig.update_layout(xaxis1=dict(
					type="category",nticks=num_xticks,tickangle=45,fixedrange=False, showticklabels=False,
	                showline=True, linewidth=1.5, linecolor="black", mirror=True,
	                showgrid=True, gridwidth=1, gridcolor="black", tickfont=dict(family="Arial", color="black", size=14)))


	fig.update_layout(xaxis2=dict(
	    		type="category",nticks=num_xticks,tickangle=45, rangemode="tozero",fixedrange=False, showticklabels=False,
	    		showline=True, linewidth=1.5, linecolor="black", mirror=True,
	    		showgrid=True, gridwidth=1, gridcolor="black", tickfont=dict(family="Arial", color="black", size=14),
	    		rangeslider=dict(visible=True,thickness=0)))


	fig.update_layout(xaxis3=dict(
					type="category",nticks=num_xticks,tickangle=35, rangemode="tozero",fixedrange=False,
	                showline=True, linewidth=1.5, linecolor="black", mirror=True,
	                showgrid=True, gridwidth=1, gridcolor="black", tickfont=dict(family="Arial", color="black", size=18),
	                rangeslider=dict(visible=True,thickness=0)))

	fig.update_layout(paper_bgcolor="rgb(250, 250, 200)")

	return fig

@app.callback(Output('live-update-time', 'children'),
              [Input('interval-component-time', 'n_intervals')])

def update_time(n):
	present_time = datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")
	style = {'fontSize': '22px'}

	return html.Span('Current Date and Time: ' + present_time, style=style)


print('Executed')	
if __name__ == "__main__":
    app.run_server(debug=True)