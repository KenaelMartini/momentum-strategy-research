# Momentum Strategy Research

A structured Python study project for learning how momentum-based quantitative strategies can be designed, tested and validated across multiple assets.

The repository was initially developed as a training environment for quantitative strategy research. It focuses on reproducible data pipelines, configurable strategy parameters, vectorised and event-driven backtesting, risk controls, transaction-cost stress tests and out-of-sample validation.

## Project scope

The research workflow includes:

- configurable investment universes defined in YAML;
- historical data ingestion through Interactive Brokers;
- price validation and matrix construction;
- parameterised momentum signals;
- vectorised backtesting for rapid experimentation;
- event-driven backtesting designed to avoid look-ahead bias;
- risk overlays and position constraints;
- transaction-cost stress testing;
- sensitivity analysis and out-of-sample validation;
- archiving of configurations and research runs.

## Requirements

- Python 3.10 or later
- Trader Workstation or IB Gateway for Interactive Brokers data collection

## Installation

```bash
git clone https://github.com/KenaelMartini/momentum-strategy-research.git
cd momentum-strategy-research
python -m venv .venv
```

Activate the environment:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Install the package and development dependencies:

```bash
pip install -e ".[dev]"
```

## Main commands

| Task | Command |
|---|---|
| Download stock prices from IBKR | `mstrat fetch --stocks-only` |
| Rebuild the local price matrix | `mstrat build-matrix --stocks-only` |
| Run the minimal vectorised backtest | `mstrat minimal-backtest` |
| Run the event-driven backtest | `mstrat event-backtest --skip-baseline --skip-strategy-benchmark-report` |
| Archive configurations and the latest run | `mstrat archive-run --copy-latest-results` |
| Run a transaction-cost stress grid | `mstrat cost-stress-grid --mults 1.0,1.5,2.0` |
| Run sensitivity presets | `mstrat sensitivity-batch --presets configs/sensitivity_presets.yaml` |
| Display the research-pipeline commands | `mstrat research-pipeline print-commands` |

## Repository structure

```text
configs/                 Strategy, universe, IBKR and risk configuration
src/momentum_strategy/   Installable Python package
data/raw/                Locally downloaded source data
data/processed/          Validated matrices and manifests
docs/                    Methodology and research documentation
tests/                   Automated tests
results/                 Generated research outputs, not versioned
```

## Research methodology

The intended process is:

1. define the asset universe and strategy configuration;
2. collect and validate historical data;
3. run rapid vectorised tests;
4. reproduce the strategy in an event-driven engine;
5. apply risk constraints and cost assumptions;
6. perform sensitivity and stress analysis;
7. freeze parameters before out-of-sample evaluation;
8. archive the configuration and results for reproducibility.

## Project status

Development is currently paused.

The repository remains available as a study and training project documenting work on quantitative strategy development, backtesting methodology, risk controls and research reproducibility. It may be resumed and extended in the future.

It should be treated as a learning environment rather than a production trading system.

## Limitations

- Backtest results depend heavily on data quality, assumptions and the selected sample period.
- Interactive Brokers data collection requires a correctly configured local TWS or IB Gateway session.
- Transaction costs, liquidity constraints and implementation effects may differ materially from simplified research assumptions.
- Historical performance does not predict future results.

## Disclaimer

This repository is provided for educational and independent research purposes only. Nothing published here constitutes financial advice, an investment recommendation, portfolio management or a regulated financial service.
