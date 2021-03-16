import json
import os
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np


def line_chart(title: str, x_label: str, scale_x: List[Any], y_label: str, scale_y: Dict[str, List[Any]],
               output_folder: str, parameter: Dict):
    # https://newaurora.pixnet.net/blog/post/227933636-python-使用matplotlib畫折線圖%28line-chart%29
    marker = ['o', 's', '^', 'd', 'x']
    color = ['r', 'b', 'g', 'c', 'm', 'y']
    line_style = ['solid', 'dotted', 'dashed', 'dashdot']
    plt.figure(linewidth=2)
    for i, data_y in enumerate(scale_y):
        plt.plot(scale_x, scale_y[data_y], label=data_y, marker=marker[i], color=color[i], linestyle=line_style[i])

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.legend(loc="best")

    file_name: str = f'{x_label}_{y_label}'
    plt.savefig(f'{output_folder}/{file_name}.png')
    plt.show()
    with open(f'{output_folder}/{file_name}.json', 'w') as file:
        json.dump([title, x_label, scale_x, y_label, scale_y, output_folder, parameter], file)


def bar_chart(title: str, x_label: str, x_tick_labels: List[Any], y_label: str, data: Dict[str, List[float]],
              output_file_path: str, parameter: Dict):
    # https://matplotlib.org/stable/gallery/lines_bars_and_markers/barchart.html
    # https://pylibraries.com/matplotlib/tutorials/grouped-bar-charts-with-matplotlib-pyplot/#Triple-grouped-bar-chart
    x = np.arange(len(x_tick_labels))  # the label locations
    width = 0.8 / len(data)  # the width of the bars
    pos = np.array(range(len(next(iter(data.values())))))

    fig, ax = plt.subplots()
    rects = []
    for i, label in enumerate(data):
        data[label] = [round(j, 3) for j in data[label]]
        rects.append(ax.bar(pos + i * width, data[label], width, label=label))

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_title(title)
    ax.set_ylabel(y_label)
    ax.set_xticks(x)
    ax.set_xticklabels(x_tick_labels)
    ax.legend()

    for i in rects:
        bar_chart_auto_label(i, ax)

    fig.tight_layout()

    file_name: str = f'{x_label}_{y_label}'
    plt.savefig(f'{output_file_path}/{file_name}.png')
    plt.show()
    with open(f'{output_file_path}/{file_name}.json', 'w') as file:
        json.dump([title, x_label, x_tick_labels, y_label, data, output_file_path, parameter], file)


def bar_chart_auto_label(rects, ax):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')


def scatter_chart(title, x, y, color, x_lim: Tuple[float, float], y_lim: Tuple[float, float],
                  output_file: str, parameter: Dict):
    # https://www.pythonpool.com/matplotlib-circle/
    # https://matplotlib.org/stable/gallery/shapes_and_collections/scatter.html
    plt.scatter(x, y, c=color)
    plt.xlim(x_lim[0], x_lim[1])
    plt.ylim(y_lim[0], y_lim[1])

    plt.title(title)
    plt.savefig(f'{output_file}.png')
    plt.show()
    with open(f'{output_file}.json', 'w') as file:
        json.dump([title, x, y, color, x_lim, y_lim, output_file, parameter], file)


if __name__ == '__main__':
    # line chart
    # line_chart("Line chart",
    #            "month", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    #            "price", {"TSMC": [255, 246, 247.5, 227, 224, 216.5, 246, 256, 262.5, 234, 225.5, 225.5],
    #                      "FOX": [92.2, 88.1, 88.5, 82.9, 85.7, 83.2, 83.8, 80.5, 79.2, 78.8, 71.9, 70.8]}, 'line_chart')
    #
    # with open('line_chart.json') as fp:
    #     data = json.load(fp)
    #     line_chart(data[0], data[1], data[2], data[3], data[4], data[5])

    # bar chart
    labels = ['G1', 'G2', 'G3', 'G4', 'G5']
    raw_data = {'men': [20, 34, 30, 35, 27], 'women': [25, 32, 34, 20, 25], 'child': [1, 2, 3, 4, 5]}
    bar_chart(title='Scores by group and gender', x_tick_labels=labels, y_label='Scores', data=raw_data)
