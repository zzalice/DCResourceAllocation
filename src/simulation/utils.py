from typing import Dict, List

UE = Dict


def fairness_index_json(ue_list: List[UE]):
    sum_square: float = 0
    square_sum: float = 0.0
    for ue in ue_list:
        sum_square += ue['throughput']
        square_sum += ue['throughput'] ** 2
    sum_square: float = sum_square ** 2
    num_ue: int = len(ue_list)
    fairness: float = sum_square / (num_ue * square_sum)
    assert 1 / num_ue <= fairness <= 1.0, 'Fairness calculation error.'
    return fairness
