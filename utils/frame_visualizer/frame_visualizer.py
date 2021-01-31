import pickle
import re
from datetime import datetime
from tokenize import String
from typing import Dict, List, Tuple, Union

from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.frame import Frame, Layer
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.util_enum import NodeBType


class FrameRenderer:
    def __init__(self):
        self.header = [
            '<style type="text/css">',
            'table {\nborder-collapse: collapse;\ntext-align: center;\nmargin-left: 10px}',
            'table, th, td {\nborder: 1px solid black;\nfont-family: monospace;\nvertical-align: center;}',
            'th {background-color: lightgray;}',
            'td {min-width: 32px;}',
            '.LTEResourceBlock_E {background-color: #01d0cc;}',
            '.Numerology_N0 {background-color: #73A7FE;}',
            '.Numerology_N1 {background-color: #B1DE8C;}',
            '.Numerology_N2 {background-color: #F5EF97;}',
            '.Numerology_N3 {background-color: #F4CD79;}',
            '.Numerology_N4 {background-color: #FA8783;}',
            '.allocated {background-color: #b1de8c}',
            '.unallocated {background-color: #fa8783}',
            '.co-channel {border-color: #8d8c8b}',
            '.tab-demo {width: fit-content; height: fit-content;}',
            '.tab-demo > ul {display: block; margin: 0; list-style: none;}',
            '.tab-title {list-style: none;}',
            '.tab-demo > ul > li {display: inline-block; vertical-align: top; margin: 0 -1px -1px 0; border: 1px solid #bcbcbc; height: 25px; line-height: 25px; background: #cdcdcd; padding: 0 15px; list-style: none; box-sizing: border-box;}',
            '.tab-demo > ul > li a { color: #000; text-decoration: none;}',
            '.tab-demo > ul > li.active {border-bottom: 1px solid #fff; background: #fff;}',
            '.tab-demo > .tab-inner {clear: both; color: #000; border: 0px #bcbcbc solid;}',
            '.tab-inner {padding: 15px; height: inherit;}',
            '</style>',
            '<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha256-4+XzXVhsDmqanXGHaHvgh1gMQKX40OUvDEBTu8JcmNs=" crossorigin="anonymous"></script>'
        ]
        self.body = []

    def tab_script(self, tab_id: String):
        self.body.append('<script>\n$(function () {\n')
        for i in tab_id:
            self.body.extend([
                f'var $li = $("ul#{i} li");\n',
                '$($li.eq(0).addClass("active").find("a").attr("href")).siblings(".tab-inner").hide();\n',

                '$li.click(function () {\n',
                '$($(this).find("a").attr("href")).show().siblings(".tab-inner").hide();\n',
                '$(this).addClass("active").siblings(".active").removeClass("active");\n',
                '});\n'])
        self.body.append('});\n</script>')

    def gen_rb(self, rb_list: List[ResourceBlock]):
        rb_list = sorted(rb_list, key=lambda x: x.layer.layer_index)
        rb_list = sorted(rb_list, key=lambda x: x.position[0])
        rb_l: int = -1
        rb_i: int = 0
        for rb in rb_list:
            if rb.layer.layer_index != rb_l:
                rb_l: int = rb.layer.layer_index
                self.body.append(f'\n<br>l: {rb_l} ')
            if rb.position[0] != rb_i:
                rb_i: int = rb.position[0]
                self.body.append('<br>')
            self.body.append(f'[{rb.position[0]}, {rb.position[2]}]')

    def gen_ue(self, ue_list: Tuple[GUserEquipment, ...], frame_time: int):
        for ue in ue_list:
            self.body.append(f'\n<div><b>User ID</b>: {ue.uuid.hex[:4]}\n<div>')
            self.body.append(f'numerology: {ue.numerology_in_use} ')
            self.body.append(f'is_to_recalc_mcs: {ue.is_to_recalculate_mcs}')
            self.body.append(f'\n<br>Qos: {(ue.request_data_rate * (1000 // (frame_time // 16))):,} bps ')
            self.body.append(f'throughput: {ue.throughput * (1000 // (frame_time // 16))} bps')
            for nb_info in ['gnb_info', 'enb_info']:
                if hasattr(ue, nb_info):
                    ue_nb_info: Union[GNBInfo, ENBInfo] = getattr(ue, nb_info)
                    self.body.append(
                        f'\n<br>{nb_info}: distance(km): {"{:.3f}".format(ue.coordinate.distance_gnb if ue_nb_info.nb_type == NodeBType.G else ue.coordinate.distance_enb)}')
                    self.body.append(f'\n<br>MCS: {ue_nb_info.mcs.name if ue_nb_info.mcs else "None"}')
                    self.body.append(f'\nSINR: {ue_nb_info.rb[-1].sinr if ue_nb_info.rb else "None"}')
                    self.body.append(f'\nthe number of RBs: {len(ue_nb_info.rb)}')
                    self.gen_rb(ue_nb_info.rb)
            self.body.append('\n</div>\n</div>')
        self.body.append('\n</div>')

    def gen_ue_list(self, ue_list: Tuple[GUserEquipment, ...], ue_status: str, frame_time: int):
        if ue_list:
            self.body.append(
                f'\n<div><span class="{ue_status}">{ue_status} {ue_list[0].ue_type.name}UE: {len(ue_list)}</span>')
            self.gen_ue(ue_list, frame_time)

    def gen_layer(self, layer: Layer, float_left: bool = False):
        base_unit = layer.bu
        height, width = len(base_unit), len(base_unit[0])

        table_header = '<th></th>' + ''.join([f'<th>j:{i}</th>' for i in range(width)])

        self.body.append(f'<table style="float: left">') if float_left else self.body.append('<table>')
        self.body.append(f'\n<tr>{table_header}</tr>')
        for i in range(height):
            tr = f'<tr><th>i:{i}</th>\n'
            for j in range(width):
                rb = base_unit[i][j].within_rb
                ue = rb.ue.uuid.hex[:4] if rb is not None else ''
                numerology = str(rb.numerology).replace('.', '_') if rb is not None else None
                cochannel = "co-channel" if base_unit[i][j].is_cochannel else None
                tr += f'<td class="{numerology} {cochannel}">{ue}</td>'
            tr += '\n</tr>'
            self.body.append(tr)
        self.body.append(f'\n<tr><td colspan="{width + 1}" style="text-align:left;">')
        self.body.append(f'{layer.nodeb.nb_type.name}NodeB Layer {layer.layer_index + 1}</td></tr>')
        self.body.append('</table>')

    def gen_phase(self, stage, g_frame, e_frame, system_throughput, g_ue_list, d_ue_list, e_ue_list):
        tab_title_id: List[String] = []
        tab_div: String = '<div class="tab-demo">'
        div_end: String = '</div>'

        self.body.append(tab_div)
        title_id: String = "whole"
        self.body.append(f'<ul id="{title_id}" class="tab-title">')
        tab_title_id.append(title_id)
        self.body.extend([f'<li><a href="#{stage[s]}">{stage[s]}</a></li>' for s in range(len(stage))])
        self.body.append('</ul>')

        for _s in range(len(stage)):
            self.body.append(f'<div id="{stage[_s]}" class="tab-inner">')

            # gFrame
            for l in range(g_frame[0].max_layer):
                self.gen_layer(g_frame[_s].layer[l], float_left=True)

            # eFrame
            self.gen_layer(e_frame[_s].layer[0])

            # ue
            self.body.append(
                f'<div>system throughput: {round((system_throughput[_s] / 1000_000) * (1000 // (g_frame[_s].frame_time // 16)), 5)} Mbps</div>')
            self.gen_ue_list(g_ue_list[_s]['allocated'], "allocated", g_frame[_s].frame_time)
            self.gen_ue_list(d_ue_list[_s]['allocated'], "allocated", g_frame[_s].frame_time)
            self.gen_ue_list(e_ue_list[_s]['allocated'], "allocated", g_frame[_s].frame_time)
            self.gen_ue_list(g_ue_list[_s]['unallocated'], "unallocated", g_frame[_s].frame_time)
            self.gen_ue_list(d_ue_list[_s]['unallocated'], "unallocated", g_frame[_s].frame_time)
            self.gen_ue_list(e_ue_list[_s]['unallocated'], "unallocated", g_frame[_s].frame_time)

            self.body.append(div_end)
        self.body.append(div_end)
        return tab_title_id

    @staticmethod
    def open_file(file_path: String):
        with open(file_path, "rb") as file_of_frame_and_ue:
            stage: List[String] = []
            g_frame: List[Frame] = []
            e_frame: List[Frame] = []
            system_throughput: List[float] = []
            g_ue_list: List[Dict[str, Tuple[GUserEquipment, ...]]] = []
            d_ue_list: List[Dict[str, Tuple[DUserEquipment, ...]]] = []
            e_ue_list: List[Dict[str, Tuple[EUserEquipment, ...]]] = []
            while True:
                try:
                    _s, _gf, _ef, _t, _gue, _due, _eue = pickle.load(file_of_frame_and_ue)
                    stage.append(re.sub("[ ]", "_", _s))
                    g_frame.append(_gf)
                    e_frame.append(_ef)
                    system_throughput.append(_t)
                    g_ue_list.append(_gue)
                    d_ue_list.append(_due)
                    e_ue_list.append(_eue)
                except EOFError:
                    g_frame: Tuple[Frame, ...] = tuple(g_frame)
                    e_frame: Tuple[Frame, ...] = tuple(e_frame)
                    system_throughput: Tuple[float] = tuple(system_throughput)
                    g_ue_list: Tuple[Dict[str, Tuple[GUserEquipment, ...]], ...] = tuple(g_ue_list)
                    d_ue_list: Tuple[Dict[str, Tuple[DUserEquipment, ...]], ...] = tuple(d_ue_list)
                    e_ue_list: Tuple[Dict[str, Tuple[EUserEquipment, ...]], ...] = tuple(e_ue_list)
                    break
        return stage, g_frame, e_frame, system_throughput, g_ue_list, d_ue_list, e_ue_list

    def render(self, filename: str):
        with open(filename, 'w') as w:
            w.write('<html>\n<head>')
            w.writelines(self.header)
            w.write('</head>\n<body>')
            w.writelines(self.body)
            w.write('</body>\n</html>')


if __name__ == '__main__':
    file_to_visualize = "vis_" + datetime.today().strftime('%Y%m%d')
    # file_to_visualize = "vis_test_calc_weight"
    # file_to_visualize = "vis_test_phase3"
    # file_to_visualize = "vis_intuitive_" + datetime.today().strftime('%Y%m%d')

    frame_renderer = FrameRenderer()
    s, gf, ef, t, gue, due, eue = frame_renderer.open_file(file_to_visualize + ".P")
    tab_title = frame_renderer.gen_phase(s, gf, ef, t, gue, due, eue)
    frame_renderer.tab_script(tab_title)
    frame_renderer.render(file_to_visualize + '.html')
