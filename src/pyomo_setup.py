import pyomo.environ as pyo
import pandas as pd


class EnergyFlowOptimization:
    def __init__(self, data_df: pd.DataFrame):
        self.df = data_df

        # creating the model and defining time
        self.model = pyo.ConcreteModel()
        self.model.t = pyo.RangeSet(0, len(self.df) - 1)

        self.init_params()

    def init_params(self):
        # initialize scalar parameters
        self.model.batt_cap = pyo.Param(initialize=160.0)
        self.model.batt_rate = pyo.Param(initialize=100.0)
        self.model.batt_eff_charge = pyo.Param(initialize=0.92)
        self.model.batt_eff_discharge = pyo.Param(initialize=1.0)
        self.model.grid_sell_max = pyo.Param(initialize=700.0)
        self.model.grid_buy_max = pyo.Param(initialize=700.0)
        self.model.batt_init_charge = pyo.Param(initialize=0.0)

        # initialize time-dependent parameters (given data: convert to dict for pyomo)
        pv_prod_dict = self.df["pv production, kWh"].to_dict()
        elec_cons_dict = self.df["electrical consumption, kWh"].to_dict()
        lcos_dict = self.df["lcos, c/kWh"].to_dict()
        price_sell_dict = self.df["electricity selling price, c/kWh"].to_dict()
        price_buy_dict = self.df["electricity buying price c/kWh"].to_dict()

        self.model.pv_prod = pyo.Param(self.model.t, initialize=pv_prod_dict)
        self.model.elec_cons = pyo.Param(self.model.t, initialize=elec_cons_dict)
        self.model.lcos = pyo.Param(self.model.t, initialize=lcos_dict)
        self.model.price_sell = pyo.Param(self.model.t, initialize=price_sell_dict)
        self.model.price_buy = pyo.Param(self.model.t, initialize=price_buy_dict)

    def init_purchase_and_battery_vars(self):
        # define the buy/sell and battery state variables 
        self.model.energy_bought = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.energy_sold = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.energy_charge = pyo.Var(self.model.t, domain=pyo.NonNegativeReals) 
        self.model.energy_discharge = pyo.Var(self.model.t, domain=pyo.NonNegativeReals) 
        self.model.battery_soc = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)

    def init_flow_vars(self):
        # define the flow variables (see the Figure 1: there are 7 arrows in total)
        self.model.pv_to_consumer_kwh = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.pv_to_battery_kwh = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.pv_to_grid_kwh = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.battery_to_consumer_kwh = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.battery_to_grid_kwh = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.grid_to_consumer_kwh = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.grid_to_battery_kwh = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
    
