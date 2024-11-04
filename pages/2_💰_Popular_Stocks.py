import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd

st.set_page_config(page_title="Popular Stocks", page_icon="💰", layout="wide")


urls = {
    "Most Active": "https://finance.yahoo.com/markets/stocks/most-active/",
    "Trending Now": "https://finance.yahoo.com/markets/stocks/trending/",
    "Top Gainers": "https://finance.yahoo.com/markets/stocks/gainers/",
    "Top Losers": "https://finance.yahoo.com/markets/stocks/losers/",
}


def getTable(category):
    response = requests.get(urls[category])
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    headers = [header.text.strip() for header in table.find_all("th")]
    data = []
    for row in table.find_all("tr")[1:]:
        cells = [cell.text.strip() for cell in row.find_all("td")]
        if cells:  # Avoid empty rows
            data.append(cells)
    df = pd.DataFrame(data, columns=headers)
    df = df[["Symbol", "Name", "Price", "Change", "Change %"]].copy()
    df.columns = ["ticker", "name", "price", "change", "pctchange"]
    df["price"] = df["price"].str.split().str[0]
    return df


category = st.sidebar.selectbox(
    "Choose a category", ["Most Active", "Trending Now", "Top Gainers", "Top Losers"]
)
st.header(f"{category} :")
data = getTable(category)

mainTile = st.container(border=True)
with mainTile:
    cols = st.columns(3)
    for i, col in enumerate(cols):
        subTile = col.container(border=True)
        subTile.metric(
            label=f"{data.name[i]}",
            value=f"{data.price[i]} USD",
            delta=f"{data.change[i]}({data.pctchange[i]})",
        )
        subTile.write(data.ticker[i])
        cols = st.columns(3)
    for i, col in enumerate(cols, start=3):
        subTile = col.container(border=True)
        subTile.metric(
            label=f"{data.name[i]}",
            value=f"{data.price[i]} USD",
            delta=f"{data.change[i]}({data.pctchange[i]})",
        )
        subTile.write(data.ticker[i])
