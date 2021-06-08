import json
from tokenize import String
from typing import Dict, List, Optional

from utils.frame_visualizer.frame_visualizer import FrameRenderer


class FrameRendererJson(FrameRenderer):
    def __init__(self):
        super().__init__()

    def gen_layer(self, layer: Dict, layer_info: str, float_left: bool = False):
        base_unit: Dict = layer['bu']
        height, width = len(base_unit), len(base_unit[0])

        table_header = '<th></th>' + ''.join([f'<th>j:{i}</th>' for i in range(width)])

        self.body.append(f'<table style="float: left">') if float_left else self.body.append('<table>')
        self.body.append(f'\n<tr>{table_header}</tr>')
        for i in range(height):
            tr = f'<tr><th>i:{i}</th>\n'
            for j in range(width):
                rb: Dict = base_unit[i][j]['within_rb']
                cochannel = "co-channel" if base_unit[i][j]['is_cochannel'] else None
                if rb is not None:
                    numerology = 'Numerology_' + rb['numerology']
                    tr += f'<td class="{numerology} {cochannel}">0000</td>'
                else:
                    tr += f'<td class="{cochannel}">____</td>'
            tr += '\n</tr>'
            self.body.append(tr)
        self.body.append(f'\n<tr><td colspan="{width + 1}" style="text-align:left;">')
        self.body.append(f'{layer_info}</td></tr>')
        self.body.append('</table>')

    def gen_phase(self, g_frame, e_frame):
        tab_title_id: List[String] = []
        tab_div: String = '<div class="tab-demo">'
        div_end: String = '</div>'

        self.body.append(tab_div)
        title_id: String = "whole"
        self.body.append(f'<ul id="{title_id}" class="tab-title">')
        tab_title_id.append(title_id)
        self.body.extend([f'<li><a href="#nan">nan</a></li>' for s in range(1)])
        self.body.append('</ul>')

        self.body.append(f'<div id="nan" class="tab-inner">')

        # gFrame
        for l in range(g_frame['max_layer']):
            self.gen_layer(g_frame['layer'][l], f'GNodeB Layer {l + 1}', float_left=True)

        # eFrame
        if e_frame['frame_freq'] > 0:
            self.gen_layer(e_frame['layer'][0], f'ENodeB')

        # ue
        # self.body.append(
        #     f'<div>system throughput: {round(bpframe_to_mbps(system_throughput[_s], g_frame[_s].frame_time), 5)} Mbps</div>')
        # self.gen_ue_list(g_ue_list[_s]['allocated'], "allocated", g_frame[_s].frame_time)
        # self.gen_ue_list(d_ue_list[_s]['allocated'], "allocated", g_frame[_s].frame_time)
        # self.gen_ue_list(e_ue_list[_s]['allocated'], "allocated", g_frame[_s].frame_time)
        # self.gen_ue_list(g_ue_list[_s]['unallocated'], "unallocated", g_frame[_s].frame_time)
        # self.gen_ue_list(d_ue_list[_s]['unallocated'], "unallocated", g_frame[_s].frame_time)
        # self.gen_ue_list(e_ue_list[_s]['unallocated'], "unallocated", g_frame[_s].frame_time)

        self.body.append(div_end)
        self.body.append(div_end)
        return tab_title_id


def visualize(file_name_visualized: Optional[str], g_nb, e_nb):
    frame_renderer = FrameRendererJson()
    tab_title = frame_renderer.gen_phase(g_nb['frame'], e_nb['frame'])
    frame_renderer.tab_script(tab_title)
    frame_renderer.render(file_name_visualized.replace('json', 'html'))


def open_file(file: str, t: str, a: str):
    with open(file, "r") as f:
        data: Dict[str, Dict] = json.load(f)  # {'1layer': {'DC-RA': [gNB, eNB, dUE, gUE, eUE]}
        visualize(file, data[t][a][0], data[t][a][1])


if __name__ == '__main__':
    file_path: str = '../../src/simulation/graph/0527-184500L_40mhz_qos100-500/gNBCQI1CQI7_eNBCQI1CQI7/result'
    file_name: str = 'topic3layer_iter21_algoDC-RA'
    topic: str = '3layer'
    algo: str = 'DC-RA'
    open_file(f'{file_path}/{file_name}.json', topic, algo)
