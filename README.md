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

## My Approach
First of all, I read the data using `pandas` to let it infer the types (datetime objects, floats, etc.).
