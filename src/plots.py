import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from src.pyomo_setup import EnergyFlowOptimization

def generate_data_plot(df: pd.DataFrame) -> go.Figure:
    """
    Generate a figure with the given data for this optimization task.

    Usage:
    >>> generate_data_plot(df).show()
    """
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


def generate_flows_plot(efo: EnergyFlowOptimization):
    results = {
        "PV to Consumer": efo.pv_to_consumer,
        "PV to Battery": efo.pv_to_battery,
        "PV to Grid": efo.pv_to_grid,
        "Battery to Consumer": efo.battery_to_consumer,
        "Grid to Consumer": efo.grid_to_consumer,
        "Grid to Battery": efo.grid_to_battery,
        "Battery to Grid": efo.battery_to_grid,
    }

    # Create stacked area plot
    fig = go.Figure()

    for label, data in results.items():
        fig.add_trace(
            go.Scatter(
                x=efo.df.index,
                y=data,
                mode="lines+markers",
                name=label,
            )
        )

    fig.update_layout(
        title="Energy Flow Optimization Results",
        yaxis_title="Energy flow (kWh)",
        legend_title="Flow direction",
        xaxis_title="Time step",
        hovermode="x unified",
        template="plotly_dark",
    )
    return fig
