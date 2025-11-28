import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objs as go
import plotly.subplots as sp
from statsmodels.tsa.seasonal import seasonal_decompose
import ta

st.set_page_config(page_title="Stock Analysis", page_icon="🧐", layout="wide")

defaultDate = datetime.today().date()
ticker = st.sidebar.text_input("Enter a ticker", "AAPL")
startDate = st.sidebar.date_input(
    "Select a Start Date",
    value=defaultDate - timedelta(days=365),
    min_value=datetime(2000, 1, 1),
    max_value=defaultDate,
)
endDate = st.sidebar.date_input(
    "Select a End Date",
    value=defaultDate,
    min_value=datetime(2000, 1, 1),
    max_value=defaultDate,
)


@st.cache_data
def getData(ticker):
    data = yf.download(ticker, period="max")
    data.columns = data.columns.droplevel('Ticker')
    return data


if not ticker.strip():
    st.warning("Ticker is required. Please enter a Ticker.")
else:
    try:
        totalData = getData(ticker)
        if not totalData.empty:
            data = totalData[
                (totalData.index.date >= startDate) & (totalData.index.date <= endDate)
            ]
            name = yf.Ticker(ticker).info.get("longName", "Company name not found")

            tab1, tab2, tab3 = st.tabs(
                ["Candle Stick Plot", "Decomposition", "Indicators"]
            )
            with tab1:
                adjcloseprice = totalData["Close"].iloc[-1]
                prevadjcloseprice = totalData["Close"].iloc[-2]
                change = adjcloseprice - prevadjcloseprice
                pctchange = (change / prevadjcloseprice) * 100

                st.subheader(f"{name} Stock Data Performance")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    tile = col1.container(border=True, height=125)
                    tile.metric(
                        label=f"{name}",
                        value=f"{adjcloseprice:.2f} USD",
                        delta=f"{change:.2f}({pctchange:.2f}%)",
                    )
                with col2:
                    tile = col2.container(border=True, height=125)
                    tile.metric(
                        label="High", value=f"{totalData['High'].iloc[-1]:.2f} USD"
                    )
                with col3:
                    tile = col3.container(border=True, height=125)
                    tile.metric(
                        label="Low", value=f"{totalData['Low'].iloc[-1]:.2f} USD"
                    )
                with col4:
                    tile = col4.container(border=True, height=125)
                    volume = totalData["Volume"].iloc[-1]
                    volume = (
                        f"{round(volume / 1_000_000, 2)}M"
                        if volume > 1_000_000
                        else str(volume)
                    )
                    tile.metric(label="Volume", value=f"{volume}")

                Data = data.copy()
                fig = sp.make_subplots(
                    rows=2,
                    cols=1,
                    shared_xaxes=True,
                    row_heights=[0.8, 0.2],
                    vertical_spacing=0.05,
                )
                fig.add_trace(
                    go.Candlestick(
                        x=Data.index,
                        open=Data["Open"],
                        high=Data["High"],
                        low=Data["Low"],
                        close=Data["Close"],
                        name="Dollars($)",
                        increasing_line_color="rgba(4, 219, 54, 0.78)",
                        decreasing_line_color="rgba(233, 21, 21, 0.78)",
                        increasing_fillcolor="rgba(14, 183, 90, 0.25)",
                        decreasing_fillcolor="rgba(255, 0, 0, 0.33)",
                    ),
                    row=1,
                    col=1,
                )
                fig.add_trace(
                    go.Bar(x=Data.index, y=Data["Volume"], name="Volume"), row=2, col=1
                )
                fig.update_xaxes(title_text="Date", row=4, col=1)
                fig.update_layout(
                    title=f"{name} Candlestick Chart",
                    showlegend=True,
                    yaxis1=dict(title="OHLC", showgrid=False),
                    yaxis2=dict(title="Volume", showgrid=False),
                    xaxis_rangeslider_visible=False,
                    hovermode="x",
                    plot_bgcolor="rgba(16, 19, 87, 1)",
                    # legend=dict(x=-1,y=1),
                    # paper_bgcolor='rgba(255, 255, 255, 1)',
                    height=600,
                )
                fig.add_hline(
                    y=Data["High"].max(),
                    line_dash="dot",
                    line_color="green",
                    annotation_text=f"Highest High({Data['High'].max():.2f}$)",
                    annotation_position="top right",
                    row=1,
                    col=1,
                )
                fig.add_hline(
                    y=Data["Close"].iloc[-2],
                    line_dash="dot",
                    line_color="yellow",
                    annotation_text=f"Previous CLose({Data['Close'].iloc[-2]:.2f}$)",
                    annotation_position="top right",
                    row=1,
                    col=1,
                )
                fig.add_hline(
                    y=Data["Low"].min(),
                    line_dash="dot",
                    line_color="red",
                    annotation_text=f"Lowest Low({Data['Low'].min():.2f}$)",
                    annotation_position="bottom right",
                    row=1,
                    col=1,
                )
                fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
                plot = st.container(border=True)
                plot.plotly_chart(fig)
                st.session_state.active_tab = "Candle Stick Plot"

            with tab2:
                st.subheader(f"{name} Stock Data Decomposition")
                if len(data) < 60:
                    st.warning(
                        f"We need atleast 60 observations to decompose. Your date range has {len(data)} observations."
                    )
                else:
                    ModelType = {
                        "Additive": "additive",
                        "Multiplicative": "multiplicative",
                    }
                    model_type = st.selectbox(
                        "Select Decomposition Model",
                        options=["Additive", "Multiplicative"],
                    )
                    # dataclose = data['Close'].asfreq('D').ffill()
                    dataclose = data["Close"]
                    decomposition = seasonal_decompose(
                        dataclose, model=ModelType[model_type], period=30
                    )
                    fig = sp.make_subplots(
                        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=dataclose.index,
                            y=decomposition.observed,
                            mode="lines",
                            name="Observed",
                        ),
                        row=1,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=dataclose.index,
                            y=decomposition.trend,
                            mode="lines",
                            name="Trend",
                        ),
                        row=2,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=dataclose.index,
                            y=decomposition.seasonal,
                            mode="lines",
                            name="Seasonal",
                        ),
                        row=3,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=dataclose.index,
                            y=decomposition.resid,
                            mode="lines",
                            name="Residual",
                        ),
                        row=4,
                        col=1,
                    )
                    fig.update_layout(
                        title=f"{name} Stock Price Decomposition",
                        template="plotly_dark",
                        plot_bgcolor="rgba(16, 19, 87, 1)",
                        height=1000,
                    )
                    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
                    fig.update_yaxes(showgrid=False)
                    fig.update_yaxes(title_text="Observed", row=1, col=1)
                    fig.update_yaxes(title_text="Trend", row=2, col=1)
                    fig.update_yaxes(title_text="Seasonal", row=3, col=1)
                    fig.update_yaxes(title_text="Residual", row=4, col=1)
                    fig.update_xaxes(title_text="Date", row=4, col=1)
                    plot = st.container(border=True)
                    plot.plotly_chart(fig)

            with tab3:
                st.subheader(f"{name} Stock Data Indicators")
                indicator_df = data.copy()
                indicator_df = indicator_df.drop("Volume", axis=1)
                # Calculate technical indicators
                # Simple Moving Average (SMA)
                indicator_df["SMA_20"] = ta.trend.sma_indicator(
                    indicator_df["Close"], window=20
                )
                indicator_df["SMA_50"] = ta.trend.sma_indicator(
                    indicator_df["Close"], window=50
                )

                # Exponential Moving Average (EMA)
                indicator_df["EMA_20"] = ta.trend.ema_indicator(
                    indicator_df["Close"], window=20
                )
                indicator_df["EMA_50"] = ta.trend.ema_indicator(
                    indicator_df["Close"], window=50
                )

                # Bollinger Bands
                bollinger = ta.volatility.BollingerBands(
                    indicator_df["Close"], window=20, window_dev=2
                )
                indicator_df["Bollinger_High"] = bollinger.bollinger_hband()
                indicator_df["Bollinger_Low"] = bollinger.bollinger_lband()

                # Moving Average Convergence Divergence (MACD)
                macd = ta.trend.MACD(indicator_df["Close"])
                indicator_df["MACD"] = macd.macd()
                indicator_df["MACD_Signal"] = macd.macd_signal()

                # Relative Strength Index (RSI)
                indicator_df["RSI"] = ta.momentum.rsi(
                    indicator_df["Close"], window=14
                )
                indicator_df = indicator_df.dropna()
                features = st.multiselect(
                    "Select Indicators",
                    [
                        "Close",
                        "Close",
                        "Open",
                        "High",
                        "Low",
                        "SMA_20",
                        "SMA_50",
                        "EMA_20",
                        "EMA_50",
                        "Bollinger_High",
                        "Bollinger_Low",
                    ],
                    default="Close",
                )

                fig = sp.make_subplots(
                    rows=3,
                    cols=1,
                    shared_xaxes=True,
                    row_heights=[0.5, 0.25, 0.25],
                    vertical_spacing=0.05,
                )

                for feature in features:
                    fig.add_trace(
                        go.Scatter(
                            x=indicator_df.index,
                            y=indicator_df[feature],
                            mode="lines",
                            name=feature,
                        ),
                        row=1,
                        col=1,
                    )
                fig.add_trace(
                    go.Scatter(
                        x=indicator_df.index,
                        y=indicator_df["RSI"],
                        mode="lines",
                        name="RSI",
                    ),
                    row=2,
                    col=1,
                )
                fig.add_trace(
                    go.Scatter(
                        x=indicator_df.index,
                        y=indicator_df["MACD"],
                        mode="lines",
                        name="MACD",
                    ),
                    row=3,
                    col=1,
                )
                fig.add_trace(
                    go.Scatter(
                        x=indicator_df.index,
                        y=indicator_df["MACD_Signal"],
                        mode="lines",
                        line_dash="dot",
                        name="MACD Signal",
                    ),
                    row=3,
                    col=1,
                )
                fig.add_hline(
                    y=70,
                    line_dash="dot",
                    line_color="green",
                    row=2,
                    col=1,
                )
                fig.add_hline(
                    y=30,
                    line_dash="dot",
                    line_color="red",
                    row=2,
                    col=1,
                )
                fig.update_layout(
                    title=f"{name} Stock Price Analysis",
                    template="plotly_dark",
                    plot_bgcolor="rgba(16, 19, 87, 1)",
                    height=700,
                )
                fig.update_yaxes(title_text="Indicators", row=1, col=1)
                fig.update_yaxes(title_text="RSI", row=2, col=1)
                fig.update_yaxes(title_text="MACD", row=3, col=1)
                fig.update_xaxes(title_text="Date", row=3, col=1)
                fig.update_yaxes(showgrid=False)
                fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
                plot = st.container(border=True)
                plot.plotly_chart(fig)
        else:
            st.warning("The ticker didn't return any data because of rate limits.")
            st.warning("Try again after a while.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

