import os
from typing import List, Tuple

from src.simulation.data.deployment import Deploy
from src.resource_allocation.ds.util_type import CircularRegion, Coordinate
from src.simulation.data.util_type import HotSpot
from src.simulation.graph.util_graph import scatter_chart


def gen_graph_deployment(in_area: Tuple[CircularRegion, ...],
                         coordinates_list: List[Tuple[Coordinate, ...]]):
    c = ['b', 'g', 'm']
    assert 0 < len(in_area) <= 2

    bound = Deploy.union_bound(in_area)
    x = [i.x for i in in_area]
    y = [i.y for i in in_area]
    color = ['r'] * len(in_area)
    for i, coordinates in enumerate(coordinates_list):
        x, y, color = _ue_deployment(coordinates, x, y, color, c[i])
    scatter_chart('', x, y, color,
                  (bound['left'], bound['right']), (bound['up'], bound['down']),
                  os.path.dirname(__file__), {})


def _ue_deployment(ue_list, x, y, color, c):
    for ue in ue_list:
        x.append(ue.x)
        y.append(ue.y)
        color.append(c)
    return x, y, color


def test_random_deploy():
    a = CircularRegion(x=0.0, y=0.0, radius=0.5)
    b = CircularRegion(x=0.5, y=0.0, radius=0.5)
    in_area: Tuple[CircularRegion, ...] = (a, b)
    sc_coordinates, dc_coordinates = Deploy.random(1000, in_area)
    sc_coordinates = list(sc_coordinates)
    sc_coordinates.append(dc_coordinates)
    gen_graph_deployment(in_area, sc_coordinates)


def test_cell_edge_deploy():
    a = CircularRegion(x=0.0, y=0.0, radius=0.5)
    b = CircularRegion(x=0.5, y=0.0, radius=0.5)
    in_area: Tuple[CircularRegion, ...] = (a, b)
    sc_coordinates, dc_coordinates = Deploy.cell_edge(1000, in_area,
                                                      radius_proportion_of_cell_edge=0.1, proportion_of_ue_in_edge=0.5)
    sc_coordinates = list(sc_coordinates)
    sc_coordinates.append(dc_coordinates)
    gen_graph_deployment(in_area, sc_coordinates)


def test_hotspot_deploy():
    a = CircularRegion(x=0.0, y=0.0, radius=0.5)
    b = CircularRegion(x=0.5, y=0.0, radius=0.5)
    h1 = HotSpot(0.4, 0.0, 0.09, 0.2)
    h2 = HotSpot(0.0, 0.0, 0.09, 0.2)
    h3 = HotSpot(0.8, 0.2, 0.09, 0.2)
    in_area: Tuple[CircularRegion, ...] = (a, b)
    sc_coordinates, dc_coordinates = Deploy.hotspots(1000, in_area, (h1, h2, h3))
    sc_coordinates = list(sc_coordinates)
    sc_coordinates.append(dc_coordinates)
    gen_graph_deployment(in_area, sc_coordinates)


def test_dc_proportion_deploy():
    a = CircularRegion(x=0.0, y=0.0, radius=0.5)
    b = CircularRegion(x=0.5, y=0.0, radius=0.5)
    in_area: Tuple[CircularRegion, ...] = (a, b)
    sc_coordinates, dc_coordinates = Deploy.dc_proportion(1000, in_area, 40)
    sc_coordinates = list(sc_coordinates)
    sc_coordinates.append(dc_coordinates)
    gen_graph_deployment(in_area, sc_coordinates)
