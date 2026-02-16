from ratinabox.Neurons import PlaceCells

N = 80

class CellBuilder:
    @staticmethod
    def build_place_cells(agent):
        return PlaceCells(
            agent,
            params={
                "n": N,
                "description": "gaussian",
                "widths": 0.20,
                "place_cell_centres": None,
                "wall_geometry": "geodesic",
                "min_fr": 0,
                "max_fr": 1, #treating this as a percent
                "save_history": True
                #"noise_std":0.15
            }
        )
