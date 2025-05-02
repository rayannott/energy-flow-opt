# energy-flow-opt

## Quick Start Guide

### 1. The repository
Clone the repo with your preferred method. E.g.:
```shell
git clone https://github.com/rayannott/energy-flow-opt.git
```

### 2. Virtual environment
Instead of `pip`, I much prefer using `uv` — a faster, cleaner and better package manager for Python! Install it globally using `pip`: 
```shell
pip install uv
```

I am currently running the latest release python 3.13, so to be on the safe side, (pull and) use its binaries to initialize and activate the environment:
```shell
uv -p 3.13 venv venv
source venv/bin/activate
```
or `venv\Scripts\activate` if on Windows.

Install the dependencies
```shell
uv pip install -r requirements.txt
```

### 3. Other
Install `glpsolve` to enable the `glpk` pyomo solver.

Ensure that it is installed correctly by running 
```shell
glpsol --version
```


## My Approach
First of all, I read the data using `pandas` to let it infer the types (datetime objects, floats, etc.).

I plot the data to take an insight into it (twin axes seems like the right choice here).

Then, I define the problem class in `src/pyomo_setup.py` and define the model, parameters and variables (hopefully following pyomo best practices).

### The model
So, the model optimizes energy flows between PV, battery and grid to satisfy hourly demand.

There are a few constraints which I formulate in python functions:
- _energy balance_: demand must be met exactly (pv + battery + grid == demand)
- _efficient PV allocation_: all PV energy is used (no waste)
- _battery state dynamics_: tracks state of charge (soc) with 92% charging efficiency
- _max rates_: battery charge/discharge <= 100 kw; grid buy/sell <= 700 kw
- _battery capacity: SOC stays within [0, 160] kWh.

And the objective is
> minimize total cost (grid purchases − sales + battery discharge costs).

### Results
I run the solver, and plot the energy flow results and display the costs table.

NOTE: Interestingly enough, in the solution, the battery-to-grid flow is at a constant 0 kWh...


## Optional Sections

### Part B
Here if one can either sell or buy, we should introduce binary flags for (dis)allowing respective operations and set them to be different at all times, which means `sell ^ buy == 1` (xor operation on the boolean flags). In other words, if both `sell` and `buy` $\in \{0, 1\}$, then `sell + buy = 1`.

This would convert the problem to a Mixed-Integer Linear Program (MILP), which are much harder to solve (literally, NP hard).

### Part C
If one could only sell/buy in 100kWh packages, again, effectively dealing with integer values: `energy_packages_bought := energy_bought * 100`, with `energy_packages_bought` $\in \mathbb{N}$ (same with "sold"), which would transform the problem into MILP as well.

If battery expansion is a one-time deal (say, double the capacity, but _only once_), then it's equivalent to adding a binary flag `expand_battery` and recalculating `battery_soc` and the total cost, too.


# Some References
- [1] https://pyomo.readthedocs.io/en/stable/howto/solver_recipes.html
- [2] https://pyomo.readthedocs.io/en/6.8.0/tutorial_examples.html
- [3] https://jckantor.github.io/CBE30338/06.05-Linear-Programming-in-Pyomo.html
