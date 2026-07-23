# HSW Neuronal Simulation Models

## Setup

```bash
conda create -n ratinabox python=3.9
conda activate ratinabox
conda install numpy scipy matplotlib
pip install shapely
```

For CEBRA:
```bash
conda install pytorch::pytorch torchvision torchaudio -c pytorch
pip install cebra
```

Configure paths by copying `.env.example` to `.env` in this directory and filling in:
- `MATLAB_FILE_PATH` — path to the `.mat` file with position data
- `SAVE_DIRECTORY` — directory for simulation outputs
- `TRAINING_DATA_DIR` — directory for training data

---

## Models

### Arousal-Mediated Model (`arousal_mediated_model/main2.py`)

Simulates neurons whose tEBC responsiveness is assigned independently of place field structure. Responsive cells can optionally be held over from environment A to B.

```
python arousal_mediated_model/main2.py [--responsive_values ...] [--responsive_type ...]
                                [--percent_place_cells ...] [--holdovers ...] [--num_iters ...]
```

| Argument | Description | Default |
|---|---|---|
| `--responsive_values` | Comma-separated responsive rates, e.g. `0.4,0.6,0.8` | `0.5` |
| `--responsive_type` | `fixed`, `binomial`, `normal`, `poisson` | `fixed` |
| `--percent_place_cells` | Fraction of cells that are place cells | `0.7` |
| `--holdovers` | `1` to reuse TEBC-responsive cells from env A in env B | `1` |
| `--num_iters` | Number of iterations | `1` |

```bash
python arousal_mediated_model/main2.py --responsive_values 0.4,0.6,0.8 --responsive_type binomial --percent_place_cells .7 --holdovers 1 --num_iters 4
python arousal_mediated_model/main2.py --responsive_values 0.4,0.6 --responsive_type binomial --percent_place_cells .7 --holdovers 5 --num_iters 4
python arousal_mediated_model/main2.py --responsive_values 0.4 --responsive_type binomial --percent_place_cells .7 --holdovers 1 --num_iters 4
python arousal_mediated_model/main2.py --responsive_values 0.5 --responsive_type fixed --percent_place_cells .7 --holdovers 1 --num_iters 4
python arousal_mediated_model/main2.py --responsive_values .25,.5,.75,1 --responsive_type fixed --percent_place_cells 1,.85,.7,.55 --holdovers 2 --num_iters 4
```

---

### Independent Model (`independent_model/main2.py`)

Place and tEBC signals are combined additively, weighted by a balance parameter that controls how much each cell incorporates spatial vs tEBC data.

```
python independent_model/main2.py [--balance_values ...] [--balance_dist ...] [--balance_std ...]
                               [--responsive_values ...] [--responsive_type ...]
                               [--percent_place_cells ...] [--num_iters ...]
```

| Argument | Description | Default |
|---|---|---|
| `--balance_values` | Comma-separated balance values, e.g. `0.3,0.5,0.7` | `0.5` |
| `--balance_dist` | `fixed`, `gaussian`, or `additive` (cumulative place+tEBC; use with balance=1) | `fixed` |
| `--balance_std` | Std dev for Gaussian balance distribution | `0.1` |
| `--responsive_values` | Comma-separated responsive rates | `0.5` |
| `--responsive_type` | `fixed`, `binomial`, `normal`, `poisson` | `fixed` |
| `--percent_place_cells` | Fraction of cells that are place cells | `0.7` |
| `--num_iters` | Number of iterations | `1` |

```bash
python independent_model/main2.py --balance_values 0.3,0.5,0.7 --balance_dist gaussian --balance_std 0.1 --responsive_values 0.4,0.6,0.8 --responsive_type binomial --percent_place_cells .7 --num_iters 4
python independent_model/main2.py --balance_values 0.3,0.5 --balance_dist gaussian --balance_std 0.5 --responsive_values 0.4,0.6 --responsive_type binomial --percent_place_cells .7 --num_iters 4
python independent_model/main2.py --balance_values 0.5 --balance_dist fixed --responsive_values 0.5 --responsive_type fixed --percent_place_cells .7 --num_iters 4
python independent_model/main2.py --balance_values 1 --balance_dist additive --responsive_values 0.5 --responsive_type fixed --percent_place_cells .7 --num_iters 4
python independent_model/main2.py --balance_values 0,.25,.5,.75,1 --balance_dist fixed --responsive_values .25,.5,.75,1 --responsive_type fixed --percent_place_cells 1,.85,.7,.55 --num_iters 4
```

---

### Place-Dependent Model (`place_dependent_model/main2.py`)

Similar to the independent model; tEBC responsiveness depends on the balance factor.

```
python place_dependent_model/main2.py [--balance_values ...] [--balance_dist ...] [--balance_std ...]
                                [--responsive_values ...] [--responsive_type ...]
                                [--percent_place_cells ...] [--num_iters ...]
```

Arguments are identical to the independent model above.

```bash
python place_dependent_model/main2.py --balance_values 0.3,0.5,0.7 --balance_dist gaussian --balance_std 0.1 --responsive_values 0.4,0.6,0.8 --responsive_type binomial --percent_place_cells .7 --num_iters 1
python place_dependent_model/main2.py --balance_values 0.5 --balance_dist fixed --responsive_values 0.5 --responsive_type fixed --percent_place_cells .7 --num_iters 1
python place_dependent_model/main2.py --balance_values 1 --balance_dist additive --responsive_values 0.5 --responsive_type fixed --percent_place_cells .7 --num_iters 1
python place_dependent_model/main2.py --balance_values 0,.25,.5,.75,1 --balance_dist fixed --responsive_values .25,.5,.75,1 --responsive_type fixed --percent_place_cells 1,.85,.7,.55 --num_iters 1
```

---

### Separate Learning Model (`separate_learning/main.py`)

Place and tEBC learning are handled in separate passes.

```
python separate_learning/main.py [--balance_values ...] [--balance_dist ...] [--balance_std ...]
                                 [--responsive_values ...] [--responsive_type ...]
```

| Argument | Description | Default |
|---|---|---|
| `--balance_values` | Comma-separated balance values | `0.5` |
| `--balance_dist` | `fixed` or `gaussian` | `fixed` |
| `--balance_std` | Std dev for Gaussian balance distribution | `0.1` |
| `--responsive_values` | Comma-separated responsive rates | — |
| `--responsive_type` | `fixed`, `binomial`, `normal`, `poisson` | `fixed` |

```bash
python separate_learning/main.py --balance_values 0.3,0.5,0.7 --balance_dist gaussian --balance_std 0.1 --responsive_values 0.4,0.6,0.8 --responsive_type binomial
python separate_learning/main.py --balance_values 0.3,0.5 --balance_dist gaussian --balance_std 0.5 --responsive_values 0.4,0.6 --responsive_type binomial
python separate_learning/main.py --balance_values 0.3 --balance_dist gaussian --balance_std 0.1 --responsive_values 0.4 --responsive_type binomial
python separate_learning/main.py --balance_values 0.5 --balance_dist fixed --responsive_values 0.5 --responsive_type fixed
```
