import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def generate_data_plot(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["pv production, kWh"],
            name="pv production (kWh)",
            line=dict(color="green"),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["electrical consumption, kWh"],
            name="demand (kWh)",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["lcos, c/kWh"],
            name="LCOS (c/kWh)",
            line=dict(dash="dot"),
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["electricity selling price, c/kWh"],
            name="Sell Price (c/kWh)",
            line=dict(dash="dot"),
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["electricity buying price c/kWh"],
            name="buy price (c/kWh)",
            line=dict(dash="dot"),
        ),
        secondary_y=True,
    )
    fig.update_layout(
        title="Energy flows and prices over time",
        hovermode="x unified",
        template="plotly_dark",
    )
    fig.update_yaxes(title_text="energy (kWh)", secondary_y=False)
    fig.update_yaxes(title_text="price (c/kWh)", secondary_y=True)
    return fig
