from itertools import starmap
from operator import mul

import pyomo.environ as pyo
from pyomo.environ import SolverStatus
import pandas as pd


class EnergyFlowOptimization:
    def __init__(self, data_df: pd.DataFrame):
        self.df = data_df

        # creating the model and defining time
        self.model = pyo.ConcreteModel()
        self.model.t = pyo.RangeSet(0, len(self.df) - 1)

        self.init_params()
        self.init_purchase_and_battery_vars()
        self.init_flow_vars()
        self.set_totals_constaints()
        self.set_flow_constraints()
        self.set_max_constraints()

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
        self.model.pv_to_consumer = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.pv_to_battery = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.pv_to_grid = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.battery_to_consumer = pyo.Var(
            self.model.t, domain=pyo.NonNegativeReals
        )
        self.model.battery_to_grid = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.grid_to_consumer = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)
        self.model.grid_to_battery = pyo.Var(self.model.t, domain=pyo.NonNegativeReals)

    def set_totals_constaints(self):
        def total_cost_obj(m):
            buy_cost = sum(m.price_buy[t] * m.energy_bought[t] for t in m.t)
            sell_revenue = sum(m.price_sell[t] * m.energy_sold[t] for t in m.t)
            battery_cost = sum(m.lcos[t] * m.energy_discharge[t] for t in m.t)
            return buy_cost - sell_revenue + battery_cost

        # define the objective: minimize the total cost!
        self.model.objective = pyo.Objective(rule=total_cost_obj, sense=pyo.minimize)

        def consumer_inflow_rule(m, t):
            return (
                m.pv_to_consumer[t] + m.battery_to_consumer[t] + m.grid_to_consumer[t]
                == m.elec_cons[t]
            )

        # balance of energy inflow to consumer
        self.model.consumer_inflow_constr = pyo.Constraint(
            self.model.t, rule=consumer_inflow_rule
        )

        def battery_soc_rule(m, t):
            return (
                m.battery_soc[t]
                # inital charge at t=0 or previous time step, otherwise
                == (m.batt_init_charge if t == 0 else m.battery_soc[t - 1])
                + m.energy_charge[t] * m.batt_eff_charge
                - m.energy_discharge[t] / m.batt_eff_discharge
            )

        # battery state of charge (SOC) dynamics (charge/discharge, with efficiencies)
        self.model.battery_soc_constr = pyo.Constraint(
            self.model.t, rule=battery_soc_rule
        )

    def set_flow_constraints(self):
        def pv_outflow_rule(m, t):
            return (
                m.pv_to_consumer[t] + m.pv_to_battery[t] + m.pv_to_grid[t]
                == m.pv_prod[t]
            )

        # balance of energy outflow from PV
        self.model.pv_outflow_constr = pyo.Constraint(
            self.model.t, rule=pv_outflow_rule
        )

        def grid_outflow_rule(m, t):
            return m.energy_bought[t] == m.grid_to_consumer[t] + m.grid_to_battery[t]

        # balance of energy outflow from grid (goes either to consumer or battery)
        self.model.grid_outflow_constr = pyo.Constraint(
            self.model.t, rule=grid_outflow_rule
        )

        def grid_inflow_rule(m, t):
            return m.energy_sold[t] == m.pv_to_grid[t] + m.battery_to_grid[t]

        # balance of energy inflow to grid (comes from PV or battery)
        self.model.grid_inflow_constr = pyo.Constraint(
            self.model.t, rule=grid_inflow_rule
        )

        def battery_inflow_rule(m, t):
            return m.energy_charge[t] == m.pv_to_battery[t] + m.grid_to_battery[t]

        # balance of energy inflow to battery (comes from PV or grid)
        self.model.battery_inflow_constr = pyo.Constraint(
            self.model.t, rule=battery_inflow_rule
        )

        def battery_outflow_rule(m, t):
            return (
                m.energy_discharge[t] == m.battery_to_consumer[t] + m.battery_to_grid[t]
            )

        # balance of energy outflow from battery (goes either to consumer or grid)
        self.model.battery_outflow_constr = pyo.Constraint(
            self.model.t, rule=battery_outflow_rule
        )

    def set_max_constraints(self):
        def battery_soc_max_rule(m, t):
            return m.battery_soc[t] <= m.batt_cap

        # maximum battery capacity (aka SOC)
        self.model.battery_soc_max_constr = pyo.Constraint(
            self.model.t, rule=battery_soc_max_rule
        )

        def battery_charge_rate_rule(m, t):
            return m.energy_charge[t] <= m.batt_rate

        # maximum battery charge rate
        self.model.battery_charge_rate_constr = pyo.Constraint(
            self.model.t, rule=battery_charge_rate_rule
        )

        def battery_discharge_rate_rule(m, t):
            return m.energy_discharge[t] <= m.batt_rate

        # maximum battery discharge rate
        self.model.battery_discharge_rate_constr = pyo.Constraint(
            self.model.t, rule=battery_discharge_rate_rule
        )

        def grid_buy_limit_rule(m, t):
            return m.energy_bought[t] <= m.grid_buy_max

        # maximum grid buy limit
        self.model.grid_buy_limit_constr = pyo.Constraint(
            self.model.t, rule=grid_buy_limit_rule
        )

        def grid_sell_limit_rule(m, t):
            return m.energy_sold[t] <= m.grid_sell_max

        # maximum grid sell limit
        self.model.grid_sell_limit_constr = pyo.Constraint(
            self.model.t, rule=grid_sell_limit_rule
        )

    def solve(self):
        self.solver = pyo.SolverFactory("glpk")
        self.results = self.solver.solve(self.model, tee=True)
        if (
            (self.results.solver.status == SolverStatus.ok)
            and self.results.solver.termination_condition
            == pyo.TerminationCondition.optimal
        ):
            print("Optimal solution found!")

    # --- results ---

    @property
    def energy_bought(self):
        return list(self.model.energy_bought.get_values().values())

    @property
    def energy_sold(self):
        return list(self.model.energy_sold.get_values().values())

    @property
    def energy_charge(self):
        return list(self.model.energy_charge.get_values().values())

    @property
    def energy_discharge(self):
        return list(self.model.energy_discharge.get_values().values())

    @property
    def battery_soc(self):
        return list(self.model.battery_soc.get_values().values())

    # flows
    @property
    def pv_to_consumer(self):
        return list(self.model.pv_to_consumer.get_values().values())

    @property
    def pv_to_battery(self):
        return list(self.model.pv_to_battery.get_values().values())

    @property
    def pv_to_grid(self):
        return list(self.model.pv_to_grid.get_values().values())

    @property
    def battery_to_consumer(self):
        return list(self.model.battery_to_consumer.get_values().values())

    @property
    def battery_to_grid(self):
        return list(self.model.battery_to_grid.get_values().values())

    @property
    def grid_to_consumer(self):
        return list(self.model.grid_to_consumer.get_values().values())

    @property
    def grid_to_battery(self):
        return list(self.model.grid_to_battery.get_values().values())

    def generate_costs_table(self) -> pd.DataFrame:
        # starmap with mul and zip to calculate the dot product
        total_buy_cost = sum(
            starmap(mul, zip(self.model.price_buy.values(), self.energy_bought))
        )
        total_sell_revenue = sum(
            starmap(mul, zip(self.model.price_sell.values(), self.energy_sold))
        )
        total_battery_cost = sum(
            starmap(mul, zip(self.model.lcos.values(), self.energy_discharge))
        )
        net_cost = total_buy_cost - total_sell_revenue + total_battery_cost

        return pd.DataFrame(
            {
                "Metric (cents)": [
                    "Total Cost",
                    "Total Buy Cost",
                    "Total Sell Revenue",
                    "Battery Discharge Cost",
                ],
                "Value": [
                    net_cost,
                    total_buy_cost,
                    total_sell_revenue,
                    total_battery_cost,
                ],
            }
        )
