import json
from typing import Any, Dict, List

import matplotlib.pyplot as plt


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


if __name__ == '__main__':
    line_chart("Line chart",
               "month", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
               "price", {"TSMC": [255, 246, 247.5, 227, 224, 216.5, 246, 256, 262.5, 234, 225.5, 225.5],
                         "FOX": [92.2, 88.1, 88.5, 82.9, 85.7, 83.2, 83.8, 80.5, 79.2, 78.8, 71.9, 70.8]}, 'line_chart')

    with open('line_chart.json') as fp:
        data = json.load(fp)
        line_chart(data[0], data[1], data[2], data[3], data[4], data[5])
