from typing import List

from src.resource_allocation.ds.ngran import GNodeB


def setup_noma(nb_list: List[GNodeB]):
    for nb in nb_list:
        for layer in nb.frame.layer:
            for i in range(layer.FREQ):
                for j in range(layer.TIME):
                    layer.bu[i][j].set_noma_bu()
