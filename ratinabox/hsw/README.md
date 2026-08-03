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
python arousal_mediated_model/main2.py [--percent_task_responsive_cells ...] [--percent_is_task_responsive_distribution ...]
                                [--percent_place_cells ...] [--holdovers ...] [--num_iters ...]
```

| Argument | Description | Default |
|---|---|---|
| `--percent_task_responsive_cells` | Comma-separated responsive rates, e.g. `0.4,0.6,0.8` | `0.5` |
| `--percent_is_task_responsive_distribution` | `fixed`, `binomial`, `normal`, `poisson` | `fixed` |
| `--percent_place_cells` | Fraction of cells that are place cells | `0.7` |
| `--holdovers` | `1` to reuse TEBC-responsive cells from env A in env B | `1` |
| `--num_iters` | Number of iterations | `1` |

```bash
python arousal_mediated_model/main2.py --percent_task_responsive_cells 0.4,0.6,0.8 --percent_is_task_responsive_distribution binomial --percent_place_cells .7 --holdovers 1 --num_iters 4
python arousal_mediated_model/main2.py --percent_task_responsive_cells 0.4,0.6 --percent_is_task_responsive_distribution binomial --percent_place_cells .7 --holdovers 5 --num_iters 4
python arousal_mediated_model/main2.py --percent_task_responsive_cells 0.4 --percent_is_task_responsive_distribution binomial --percent_place_cells .7 --holdovers 1 --num_iters 4
python arousal_mediated_model/main2.py --percent_task_responsive_cells 0.5 --percent_is_task_responsive_distribution fixed --percent_place_cells .7 --holdovers 1 --num_iters 4
python arousal_mediated_model/main2.py --percent_task_responsive_cells .25,.5,.75,1 --percent_is_task_responsive_distribution fixed --percent_place_cells 1,.85,.7,.55 --holdovers 2 --num_iters 4
```

---

### Independent Model (`independent_model/main2.py`)

Place and tEBC signals are combined additively, weighted by a percent-task-in-response parameter that controls how much each cell incorporates spatial vs tEBC data.

```
python independent_model/main2.py [--percent_task_in_response_values ...] [--percent_task_in_response_dist ...] [--percent_task_in_response_std ...]
                               [--percent_task_responsive_cells ...] [--percent_is_task_responsive_distribution ...]
                               [--percent_place_cells ...] [--num_iters ...]
```

| Argument | Description | Default |
|---|---|---|
| `--percent_task_in_response_values` | Comma-separated percent-task-in-response values, e.g. `0.3,0.5,0.7` | `0.5` |
| `--percent_task_in_response_dist` | `fixed`, `gaussian`, or `additive` (cumulative place+tEBC; use with percent_task_in_response=1) | `fixed` |
| `--percent_task_in_response_std` | Std dev for Gaussian percent-task-in-response distribution | `0.1` |
| `--percent_task_responsive_cells` | Comma-separated responsive rates | `0.5` |
| `--percent_is_task_responsive_distribution` | `fixed`, `binomial`, `normal`, `poisson` | `fixed` |
| `--percent_place_cells` | Fraction of cells that are place cells | `0.7` |
| `--num_iters` | Number of iterations | `1` |

```bash
python independent_model/main2.py --percent_task_in_response_values 0.3,0.5,0.7 --percent_task_in_response_dist gaussian --percent_task_in_response_std 0.1 --percent_task_responsive_cells 0.4,0.6,0.8 --percent_is_task_responsive_distribution binomial --percent_place_cells .7 --num_iters 4
python independent_model/main2.py --percent_task_in_response_values 0.3,0.5 --percent_task_in_response_dist gaussian --percent_task_in_response_std 0.5 --percent_task_responsive_cells 0.4,0.6 --percent_is_task_responsive_distribution binomial --percent_place_cells .7 --num_iters 4
python independent_model/main2.py --percent_task_in_response_values 0.5 --percent_task_in_response_dist fixed --percent_task_responsive_cells 0.5 --percent_is_task_responsive_distribution fixed --percent_place_cells .7 --num_iters 4
python independent_model/main2.py --percent_task_in_response_values 1 --percent_task_in_response_dist additive --percent_task_responsive_cells 0.5 --percent_is_task_responsive_distribution fixed --percent_place_cells .7 --num_iters 4
python independent_model/main2.py --percent_task_in_response_values 0,.25,.5,.75,1 --percent_task_in_response_dist fixed --percent_task_responsive_cells .25,.5,.75,1 --percent_is_task_responsive_distribution fixed --percent_place_cells 1,.85,.7,.55 --num_iters 4
```

---

### Place-Dependent Model (`place_dependent_model/main2.py`)

Similar to the independent model; tEBC responsiveness depends on the percent-task-in-response factor.

```
python place_dependent_model/main2.py [--percent_task_in_response_values ...] [--percent_task_in_response_dist ...] [--percent_task_in_response_std ...]
                                [--percent_task_responsive_cells ...] [--percent_is_task_responsive_distribution ...]
                                [--percent_place_cells ...] [--num_iters ...]
```

Arguments are identical to the independent model above.

```bash
python place_dependent_model/main2.py --percent_task_in_response_values 0.3,0.5,0.7 --percent_task_in_response_dist gaussian --percent_task_in_response_std 0.1 --percent_task_responsive_cells 0.4,0.6,0.8 --percent_is_task_responsive_distribution binomial --percent_place_cells .7 --num_iters 1
python place_dependent_model/main2.py --percent_task_in_response_values 0.5 --percent_task_in_response_dist fixed --percent_task_responsive_cells 0.5 --percent_is_task_responsive_distribution fixed --percent_place_cells .7 --num_iters 1
python place_dependent_model/main2.py --percent_task_in_response_values 1 --percent_task_in_response_dist additive --percent_task_responsive_cells 0.5 --percent_is_task_responsive_distribution fixed --percent_place_cells .7 --num_iters 1
python place_dependent_model/main2.py --percent_task_in_response_values 0,.25,.5,.75,1 --percent_task_in_response_dist fixed --percent_task_responsive_cells .25,.5,.75,1 --percent_is_task_responsive_distribution fixed --percent_place_cells 1,.85,.7,.55 --num_iters 1
```

---

### Separate Learning Model (`separate_learning/main.py`)

Place and tEBC learning are handled in separate passes.

```
python separate_learning/main.py [--percent_task_in_response_values ...] [--percent_task_in_response_dist ...] [--percent_task_in_response_std ...]
                                 [--percent_task_responsive_cells ...] [--percent_is_task_responsive_distribution ...]
```

| Argument | Description | Default |
|---|---|---|
| `--percent_task_in_response_values` | Comma-separated percent-task-in-response values | `0.5` |
| `--percent_task_in_response_dist` | `fixed` or `gaussian` | `fixed` |
| `--percent_task_in_response_std` | Std dev for Gaussian percent-task-in-response distribution | `0.1` |
| `--percent_task_responsive_cells` | Comma-separated responsive rates | — |
| `--percent_is_task_responsive_distribution` | `fixed`, `binomial`, `normal`, `poisson` | `fixed` |

```bash
python separate_learning/main.py --percent_task_in_response_values 0.3,0.5,0.7 --percent_task_in_response_dist gaussian --percent_task_in_response_std 0.1 --percent_task_responsive_cells 0.4,0.6,0.8 --percent_is_task_responsive_distribution binomial
python separate_learning/main.py --percent_task_in_response_values 0.3,0.5 --percent_task_in_response_dist gaussian --percent_task_in_response_std 0.5 --percent_task_responsive_cells 0.4,0.6 --percent_is_task_responsive_distribution binomial
python separate_learning/main.py --percent_task_in_response_values 0.3 --percent_task_in_response_dist gaussian --percent_task_in_response_std 0.1 --percent_task_responsive_cells 0.4 --percent_is_task_responsive_distribution binomial
python separate_learning/main.py --percent_task_in_response_values 0.5 --percent_task_in_response_dist fixed --percent_task_responsive_cells 0.5 --percent_is_task_responsive_distribution fixed
```
