import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas


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

    file_name: str = f'{x_label}_{y_label}_{datetime.today().strftime("%m%d-%H%M")}'
    plt.savefig(f'{output_folder}/{file_name}.png')
    plt.show()
    dump_json(f'{output_folder}/{file_name}', [title, x_label, scale_x, y_label, scale_y, output_folder, parameter])


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
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_xticks(x)
    ax.set_xticklabels(x_tick_labels)
    ax.legend()

    for i in rects:
        bar_chart_auto_label(i, ax)

    fig.tight_layout()

    plt.savefig(f'{output_file_path}.png')
    plt.show()
    dump_json(f'{output_file_path}',
              [title, x_label, x_tick_labels, y_label, data, output_file_path, parameter])


def bar_chart_auto_label(rects, ax):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')


def bar_chart_grouped_stacked(title: str, x_label: str, y_label: str, output_file_path: str, parameter: Dict,
                              data: Dict[str, List[List[float]]], x_index: List[str], stack_label: List[str],
                              labels=None, H="/", color_gradient: bool = False):
    # https://stackoverflow.com/questions/22787209/how-to-have-clusters-of-stacked-bars-with-python-pandas
    # Colormap: https://matplotlib.org/stable/tutorials/colors/colormaps.html
    dfall: List[pandas.DataFrame] = []
    for algo in labels:
        dfall.append(pandas.DataFrame(data[algo],
                                      index=[i for i in x_index],
                                      columns=[i for i in stack_label]))

    n_df = len(dfall)
    n_col = len(dfall[0].columns)
    n_ind = len(dfall[0].index)
    axe = plt.subplot(111)

    for df in dfall:  # for each data frame
        axe = df.plot(kind="bar", linewidth=0, stacked=True, ax=axe, legend=False, grid=False,
                      colormap='Blues' if color_gradient else None)  # make bar plots

    h, l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, n_df * n_col, n_col):  # len(h) = n_col * n_df
        for j, pa in enumerate(h[i:i + n_col]):
            for rect in pa.patches:  # for each index
                rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                rect.set_hatch(H * int(i / n_col))  # edited part
                rect.set_width(1 / float(n_df + 1))

    axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(n_df + 1)) / 2.)
    axe.set_xticklabels(df.index, rotation=0)
    axe.set_xlabel(x_label)
    axe.set_ylabel(y_label)
    axe.set_title(title)

    # Add invisible data to add another legend
    n = []
    for i in range(n_df):
        n.append(axe.bar(0, 0, color="gray", hatch=H * i))

    l1 = axe.legend(h[:n_col], l[:n_col], loc=[1.01, 0.25])
    if labels is not None:
        l2 = plt.legend(n, labels, loc=[1.01, 0.0])
    axe.add_artist(l1)

    plt.tight_layout()
    plt.savefig(f'{output_file_path}.png', bbox_inches='tight')
    plt.show()
    dump_json(output_file_path,
              [title, x_label, y_label, output_file_path, parameter, data, x_index, stack_label, labels, H])


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
    dump_json(output_file, [title, x, y, color, x_lim, y_lim, output_file, parameter])


def dump_json(path: str, data: Any):
    with open(f'{path}.json', 'w') as file:
        json.dump(data, file)


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
    # labels = ['G1', 'G2', 'G3', 'G4', 'G5']
    # raw_data = {'men': [20, 34, 30, 35, 27], 'women': [25, 32, 34, 20, 25], 'child': [1, 2, 3, 4, 5]}
    # bar_chart(title='Scores by group and gender', x_tick_labels=labels, y_label='Scores', data=raw_data)

    # bar chart grouped and stacked
    # import pandas as pd
    # import numpy as np
    # import matplotlib.pyplot as plt
    # df1 = pd.DataFrame(np.random.rand(4, 5),
    #                    index=["A", "B", "C", "D"],
    #                    columns=["I", "J", "K", "L", "M"])
    # df2 = pd.DataFrame(np.random.rand(4, 5),
    #                    index=["A", "B", "C", "D"],
    #                    columns=["I", "J", "K", "L", "M"])
    # df3 = pd.DataFrame(np.random.rand(4, 5),
    #                    index=["A", "B", "C", "D"],
    #                    columns=["I", "J", "K", "L", "M"])
    # bar_chart_grouped_stacked([df1, df2, df3], ["df1", "df2", "df3"])

    ##########################################
    file_path: str = '0410-094738high_qos_700ue/gNBCQI1CQI7_eNBCQI1CQI7/num_of_allocated_ue_0410-1417.json'
    with open(file_path, 'r') as f:
        d = json.load(f)
        bar_chart_grouped_stacked(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8])
