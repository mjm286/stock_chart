# Created by Matthew McCarroll 5/16/2020

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import datetime
from dateutil.relativedelta import *

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr

from chart_studio.plotly import plot, iplot
import plotly.graph_objects as go
from plotly.subplots import make_subplots

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
time_buttons=["2y","1y","6mo","3mo","1mo","5d"]
app.layout = html.Div([


    dcc.Input(id="input-symbol", type="text", value="AAPL"),
    html.Button(id="submit-button-state", n_clicks=0, children="Submit"),
    html.Div([
    	dcc.RadioItems(
    		id="time-frame",
        options=[{"label": i, "value": i} for i in time_buttons],
        value="2y", labelStyle={"display":"inline-block"}),
    	],style={"width": "75%"}),
   	
   	dcc.Graph(id="main-graph")


])


@app.callback(Output("main-graph", "figure"),
              [Input("submit-button-state", "n_clicks"),
               Input("time-frame","value")],
              [State("input-symbol", "value")])



def update_graph(n_clicks, time_value, input_symbol_value):

	# symbol="PTON"
	ticker=yf.Ticker(input_symbol_value)
	OHLCV_data=pd.DataFrame()

	OHLCV_data = ticker.history(period="5y")
	OHLCV_data = OHLCV_data.reset_index(drop=False)


	present_time = datetime.datetime.now()
	timestamp = present_time.strftime("%m-%d-%Y")
	# timestamp = present_time.strftime("%Y-%m-%d %H:%M:%S")

	# OHLCV_data.head()
	columns = OHLCV_data.columns
	columns = [x.lower() for x in columns]
	OHLCV_data.columns = columns
	# OHLCV_data["date"]= OHLCV_data.sort_values(by="date")#key=lambda date: datetime.strptime(date, "%d-%b-%y"))

#########################################################################################
#########################################################################################
##########                MOVING AVERAGES AND BOLLINGER BANDS                  ##########
#########################################################################################
#########################################################################################

	OHLCV_data["twenty_day"]= OHLCV_data["close"].rolling(window=20).mean()
	OHLCV_data["fifty_day"]= OHLCV_data["close"].rolling(window=50).mean()
	OHLCV_data["twoHundred_day"]= OHLCV_data["close"].rolling(window=200).mean()
	OHLCV_data["bolupp"]=OHLCV_data["twenty_day"]+(2*OHLCV_data["close"].rolling(window=20).std())
	OHLCV_data["bollow"]=OHLCV_data["twenty_day"]-(2*OHLCV_data["close"].rolling(window=20).std())

	#########################################################################################
	#########################################################################################
	##########                RELATIVE STRENGTH INDEX                              ##########
	#########################################################################################
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
	#########################################################################################
	##########      ASSIGN CANDLESTICK AND VOLUME GAIN LOSS DIRECTION              ##########
	#########################################################################################
	#########################################################################################

	OHLCV_data["direction"] = ["increasing" if OHLCV_data.loc[i,"close"] >= OHLCV_data.loc[i,"open"] else "decreasing" for i in OHLCV_data.index]
	OHLCV_data["color"] = ["forestgreen" if OHLCV_data.loc[i,"direction"] == "increasing" else "red" for i in OHLCV_data.index]

	#########################################################################################
	#########################################################################################
	##########                   ASSIGN DATE WINDOW                                ##########
	#########################################################################################
	#########################################################################################

	y=OHLCV_data["date"].iloc[-1].year
	m=OHLCV_data["date"].iloc[-1].month
	d=OHLCV_data["date"].iloc[-1].day
	# mask = (OHLCV_data["date"] <= timestamp)
	# print(type(timestamp))
	# print(OHLCV_data["date"].iloc[0])
	# print(type(OHLCV_data["date"].iloc[0]))
	# OHLCV_data["date"] = OHLCV_data["date"].dt.strftime("%m-%d-%Y")
	# print(OHLCV_data["date"].iloc[0])
	twoyr = datetime.date.today() + relativedelta(years=-2)
	oneyr = datetime.date.today() + relativedelta(years=-1)
	six_months = datetime.date.today() + relativedelta(months=-6)
	three_months = datetime.date.today() + relativedelta(months=-3)
	one_months = datetime.date.today() + relativedelta(months=-1)
	fivedays = datetime.date.today() + relativedelta(days=-6)
	if time_value =="2y":
		mask = (OHLCV_data["date"] >= str(twoyr)) & (OHLCV_data["date"]<=timestamp)
		OHLCV_data["date"] = OHLCV_data["date"].dt.strftime("%m-%d-%Y")
	elif time_value =="1y":
		mask = (OHLCV_data["date"] >= str(oneyr)) & (OHLCV_data["date"]<=timestamp)
		OHLCV_data["date"] = OHLCV_data["date"].dt.strftime("%m-%d-%Y")
	elif time_value =="6mo":
		mask = (OHLCV_data["date"] >= str(six_months)) & (OHLCV_data["date"]<=timestamp)
		OHLCV_data["date"] = OHLCV_data["date"].dt.strftime("%m-%d-%Y")
	elif time_value =="3mo":
		mask = (OHLCV_data["date"] >= str(three_months)) & (OHLCV_data["date"]<=timestamp)
		OHLCV_data["date"] = OHLCV_data["date"].dt.strftime("%m-%d-%Y")	
	elif time_value =="1mo":
		mask = (OHLCV_data["date"] >= str(one_months)) & (OHLCV_data["date"]<=timestamp)
		OHLCV_data["date"] = OHLCV_data["date"].dt.strftime("%m-%d-%Y")
	else:
		mask = (OHLCV_data["date"] >= str(fivedays)) & (OHLCV_data["date"]<=timestamp)
		OHLCV_data["date"] = OHLCV_data["date"].dt.strftime("%m-%d-%Y")



	#########################################################################################
	#########################################################################################
	##########              SET CANDLESTICK YAXIS BOUNDS                           ##########
	#########################################################################################
	#########################################################################################

	subset = OHLCV_data[["open","high","low","close","bolupp","bollow"]].columns
	candle_low = OHLCV_data.loc[mask,subset].min().min()
	candle_high = OHLCV_data.loc[mask,subset].max().max()

	#########################################################################################
	#########################################################################################
	##########                   SET RSI 70 / 30 LINES                             ##########
	#########################################################################################
	#########################################################################################

	rsiupL =[OHLCV_data.loc[mask,"date"].iloc[0],OHLCV_data.loc[mask,"date"].iloc[-1]]
	rsiupR =[70,70]

	rsidownL =[OHLCV_data.loc[mask,"date"].iloc[0],OHLCV_data.loc[mask,"date"].iloc[-1]]
	rsidownR =[30,30]
	rsimidL =[OHLCV_data.loc[mask,"date"].iloc[0],OHLCV_data.loc[mask,"date"].iloc[-1]]
	rsimidR =[50,50]
	# fillxyUP=OHLCV_data.loc[OHLCV_data["RSI"]>=70]]

	fig = make_subplots(rows=3,cols=1,shared_xaxes=True,vertical_spacing=0.02, row_width=[0.2,0.6,0.2])

	# RSI
	fig.add_trace(
	    go.Scatter(
	        name="RSI "+ "{:.2f}".format(OHLCV_data["RSI"].iloc[-1]),
	        hoverlabel=dict(font=dict(size=20),align="right"),
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["RSI"].loc[mask],
			# marker_color=OHLCV_data["color"].loc[mask]
	        line=dict(color="black", width=3),
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

	bollinecolor="rgba(220,220,220,0.31)"
	# Bollinger Bands - upper
	fig.add_trace(
	    go.Scatter(
	        fill=None,
	        mode="lines",
	        line_color=bollinecolor,
	        yaxis="y21",
	        name="bollup",
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["bolupp"].loc[mask],hoverinfo="none",
	        showlegend=False),row=2,col=1
	)

	# Bollinger Bands - lower
	fig.add_trace(
	    go.Scatter(
	        fill="tonexty",
	        mode="lines",
	        line_color=bollinecolor,
	        fillcolor=bollinecolor,
	        name="bollow",
	        yaxis="y21",
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["bollow"].loc[mask], hoverinfo="none",
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

	# 20 day SMA
	fig.add_trace(
	    go.Scatter(
	        name="MA(20) "+ "{:.2f}".format(OHLCV_data["twenty_day"].iloc[-1]),
	    	hoverlabel=dict(font=dict(size=20),align="right"),
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["twenty_day"].loc[mask],
	        line=dict(color="yellow", width=2),yaxis="y2",hovertemplate = "20MA: %{y:$.2f}"+ "<extra></extra>"),row=2,col=1
	    )

	# 50 day SMA
	fig.add_trace(
	    go.Scatter(
	        name="MA(50) "+ "{:.2f}".format(OHLCV_data["fifty_day"].iloc[-1]),
		    hoverlabel=dict(font=dict(size=20),align="right"),
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["fifty_day"].loc[mask],line=dict(color="blue", width=2),yaxis="y2",cliponaxis=True,hovertemplate = "50MA: %{y:$.2f}"+ "<extra></extra>"),row=2,col=1
	    )

	# 200 day SMA
	fig.add_trace(
	    go.Scatter(
	        name="MA(200) "+ "{:.2f}".format(OHLCV_data["twoHundred_day"].iloc[-1]),
	        hoverlabel=dict(font=dict(size=20),align="right"),	        
	        x=OHLCV_data["date"].loc[mask],
	        y=OHLCV_data["twoHundred_day"].loc[mask],line=dict(color="purple", width=2),yaxis="y2",hovertemplate = "200MA: %{y:$.2f}"+ "<extra></extra>"),row=2,col=1
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

	fig.update_layout(yaxis2=dict(overlaying="y2",layer="below traces"))

	fig.update_layout(
	    height=825,
	    width=825,
	    plot_bgcolor="rgba(254,254,254,0)",
	    paper_bgcolor="rgba(0,0,0,0)",
	    title=dict(
	        text=input_symbol_value.upper()+". "+
	        str(present_time.strftime("%Y-%m-%d %H:%M:%S"))+
	        ". Open: "+"{:.2f}".format(OHLCV_data["open"].iloc[-1])+
	        ". High: "+"{:.2f}".format(OHLCV_data["high"].iloc[-1])+
	        ". Low: "+"{:.2f}".format(OHLCV_data["low"].iloc[-1])+
	        ". Close: "+"{:.2f}".format(OHLCV_data["close"].iloc[-1])+
	        ". Volume: "+"{:.2f}".format(OHLCV_data["volume"].iloc[-1]),
	        font=dict(color="black",family="Arial",size=16))
	)

	# Update yaxis properties
	fig.update_layout(yaxis1=dict(tickangle=0,
	                 showline=True, linewidth=1.5, linecolor="black", mirror=True,
	                 showgrid=False, gridwidth=.5, gridcolor="black",
	                 tickfont=dict(family="Arial", color="black", size=14),nticks=6, range=[10,90]
	                 ))

	fig.update_layout(yaxis2=dict(tickangle=0,
	                 showline=True, linewidth=2, linecolor="black", mirror="allticks",
	                 showgrid=True, gridwidth=1, gridcolor="black",
	                 tickfont=dict(family="Arial", color="black", size=14),fixedrange=False,
	                              range =[candle_low-candle_low*0.01,candle_high+candle_high*0.01],autorange=True,
	                 nticks=20,tickformat="$"
	                 ))

	fig.update_layout(yaxis3=dict(tickangle=0,
	                 showline=True, linewidth=2, linecolor="black", mirror="ticks",
	                 showgrid=True, gridwidth=1, gridcolor="black",
	                 tickfont=dict(family="Arial", color="black", size=14)
	                 ))


	# fig.update_xaxes(type="category",nticks=25,tickangle=45,
	#                  showline=True, linewidth=2, linecolor="black", mirror=True,
	#                  showgrid=True, gridwidth=.5, gridcolor="black", tickfont=dict(family="Arial", color="black", size=14))

	fig.update_layout(
	    legend=dict(
	        x=0,
	        y=1.08,
	        traceorder="normal",
	        font=dict(
	            family="Arial",
	            size=14,
	            color="black"
	        ),
	        bgcolor="white",
	        bordercolor="Black",
	        borderwidth=2,orientation="h"
	    )
	)
	x_numticks=20
	fig.update_layout(xaxis1=dict(type="category",nticks=x_numticks,tickangle=45,fixedrange=False,
	                 showline=True, linewidth=1.5, linecolor="black", mirror=True,
	                 showgrid=True, gridwidth=.05, gridcolor="black", tickfont=dict(family="Arial", color="black", size=14)))


	fig.update_layout(xaxis2=dict(
	    type="category",nticks=x_numticks,tickangle=45, rangemode="tozero",fixedrange=False,
	    showline=True, linewidth=1.5, linecolor="black", mirror=True,
	    showgrid=True, gridwidth=.05, gridcolor="black", tickfont=dict(family="Arial", color="black", size=14),
	    rangeslider=dict(visible=True,thickness=0)))


	fig.update_layout(xaxis3=dict(type="category",nticks=x_numticks,tickangle=35, rangemode="tozero",fixedrange=False,
	                 showline=True, linewidth=1.5, linecolor="black", mirror=True,
	                 showgrid=True, gridwidth=.05, gridcolor="black", tickfont=dict(family="Arial", color="black", size=14),
	                 rangeslider=dict(visible=True,thickness=0)))

	               
	  

	fig.update_layout(hovermode="x")

	# fig.show()
# fig.write_html(str(input1)+".html")

	return fig


if __name__ == "__main__":
    app.run_server(debug=True)