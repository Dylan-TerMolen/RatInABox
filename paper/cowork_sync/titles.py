import os, yaml
def load_titles(paper=None):
    """Display titles keyed by figure id: paper/cowork_sync/titles.yaml if present, else titles.yaml beside this script."""
    for p in ([f"{paper}/cowork_sync/titles.yaml"] if paper else []) + [os.path.join(os.path.dirname(os.path.abspath(__file__)), "titles.yaml")]:
        if os.path.exists(p):
            return yaml.safe_load(open(p)) or {}
    return {}


def load_hidden(paper=None):
    """Figure ids to leave out: paper/cowork_sync/hidden.yaml if present, else hidden.yaml beside this script."""
    for p in ([f"{paper}/cowork_sync/hidden.yaml"] if paper else []) + [os.path.join(os.path.dirname(os.path.abspath(__file__)), "hidden.yaml")]:
        if os.path.exists(p):
            return set(yaml.safe_load(open(p)) or [])
    return set()
