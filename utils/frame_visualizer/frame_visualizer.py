import pickle
from tokenize import String
from typing import Dict, List, Tuple

from src.resource_allocation.ds.frame import Frame, Layer
from src.resource_allocation.ds.ngran import GUserEquipment
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.util_enum import UEType


class FrameRenderer:
    def __init__(self):
        self.header = [
            '<style type="text/css">',
            'table {\nborder-collapse: collapse;\ntext-align: center;}',
            'table, th, td {\nborder: 1px solid black;\nfont-family: monospace;\nvertical-align: center;}',
            'th {background-color: lightgray;}',
            'td {min-width: 32px;}',
            '.LTEPhysicalResourceBlock_E {background-color: #73A7FE;}',
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

    def gen_ue(self, ue_list: Tuple[GUserEquipment, ...]):
        for ue in ue_list:
            self.body.append(f'\n<div><b>User ID</b>: {ue.uuid.hex[:4]}\n<div>')
            self.body.append(f'\nnumerology: {ue.numerology_in_use}')
            self.body.append(f'\nQos: {ue.request_data_rate}')
            if ue.ue_type == UEType.G or ue.ue_type == UEType.D:
                self.body.append(f'\n<br>gnb_info: MCS: {ue.gnb_info.mcs.name}')
                self.body.append(f'\nthe number of RBs: {len(ue.gnb_info.rb)}')
                self.gen_rb(ue.gnb_info.rb)
            if ue.ue_type == UEType.E or ue.ue_type == UEType.D:
                self.body.append(f'\n<br>enb_info: MCS: {ue.enb_info.mcs.name}')
                self.body.append(f'\nthe number of RBs: {len(ue.enb_info.rb)}')
                self.gen_rb(ue.enb_info.rb)
            self.body.append('\n</div>\n</div>')
        self.body.append('\n</div>')

    def gen_ue_list(self, ue_list: Dict[str, Tuple[GUserEquipment, ...]]):
        if ue_list['allocated']:
            self.body.append(
                f'\n<div><span class="allocated">Allocated {ue_list["allocated"][0].ue_type.name}UE:</span>')
            self.gen_ue(ue_list['allocated'])
        if ue_list['unallocated']:
            self.body.append(
                f'\n<div><span class="unallocated">Unallocated {ue_list["unallocated"][0].ue_type.name}UE:</span>')
            self.gen_ue(ue_list['unallocated'])

    def gen_layer(self, layer: Layer):
        base_unit = layer.bu
        height, width = len(base_unit), len(base_unit[0])

        table_header = '<th></th>' + ''.join([f'<th>j:{i + 1}</th>' for i in range(width)])

        self.body.append('<table>')
        self.body.append(f'\n<tr>{table_header}</tr>')
        for i in range(height):
            tr = f'<tr><th>i:{i + 1}</th>\n'
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

    def gen_phase(self, stage, g_frame, e_frame, g_ue_list, d_ue_list, e_ue_list):
        tab_title_id: List[String] = []
        tab_div: String = '<div class="tab-demo">'
        tab_title_end: String = '</ul>'
        div_end: String = '</div>'

        # gFrame
        for l in range(g_frame[0].max_layer):
            self.body.append(tab_div)
            title_id: String = f'g_{l}'
            self.body.append(f'<ul id="{title_id}" class="tab-title">')
            tab_title_id.append(title_id)
            self.body.extend([f'<li><a href="#{stage[s]}_g_{l}">{stage[s]}</a></li>' for s in range(len(stage))])
            self.body.append(tab_title_end)
            for s in range(len(stage)):
                self.body.append(f'<div id="{stage[s]}_g_{l}" class="tab-inner">')
                self.gen_layer(g_frame[s].layer[l])
                self.body.append(div_end)
            self.body.append(div_end)

        # eFrame
        self.body.append(tab_div)
        title_id: String = f'e'
        self.body.append(f'<ul id="{title_id}" class="tab-title">')
        tab_title_id.append(title_id)
        self.body.extend([f'<li><a href="#{stage[s]}_e">{stage[s]}</a></li>' for s in range(len(stage))])
        self.body.append(tab_title_end)
        for s in range(len(stage)):
            self.body.append(f'<div id="{stage[s]}_e" class="tab-inner">')
            self.gen_layer(e_frame[s].layer[0])
            self.body.append(div_end)
        self.body.append(div_end)

        # UEs
        self.body.append(tab_div)
        title_id: String = f'ue'
        self.body.append(f'<ul id="{title_id}" class="tab-title">')
        tab_title_id.append(title_id)
        self.body.extend([f'<li><a href="#{stage[s]}_ue">{stage[s]}</a></li>' for s in range(len(stage))])
        self.body.append(tab_title_end)
        for s in range(len(stage)):
            self.body.append(f'<div id="{stage[s]}_ue" class="tab-inner">')
            self.gen_ue_list(g_ue_list[s])
            self.gen_ue_list(d_ue_list[s])
            self.gen_ue_list(e_ue_list[s])
            self.body.append(div_end)
        self.body.append(div_end)
        return tab_title_id

    @staticmethod
    def open_file(file_path: String):
        with open(file_path, "rb") as file_of_frame_and_ue:
            stage: List[String] = []
            g_frame: List[Frame] = []
            e_frame: List[Frame] = []
            g_ue_list: List[Dict[str, Tuple[GUserEquipment, ...]]] = []
            d_ue_list: List[Dict[str, Tuple[GUserEquipment, ...]]] = []
            e_ue_list: List[Dict[str, Tuple[GUserEquipment, ...]]] = []
            while True:
                try:
                    _s, _gf, _ef, _gue, _due, _eue = pickle.load(file_of_frame_and_ue)
                    stage.append(_s)
                    g_frame.append(_gf)
                    e_frame.append(_ef)
                    g_ue_list.append(_gue)
                    d_ue_list.append(_due)
                    e_ue_list.append(_eue)
                except EOFError:
                    g_frame: Tuple[Frame, ...] = tuple(g_frame)
                    e_frame: Tuple[Frame, ...] = tuple(e_frame)
                    g_ue_list: Tuple[Dict[str, Tuple[GUserEquipment, ...]], ...] = tuple(g_ue_list)
                    d_ue_list: Tuple[Dict[str, Tuple[GUserEquipment, ...]], ...] = tuple(d_ue_list)
                    e_ue_list: Tuple[Dict[str, Tuple[GUserEquipment, ...]], ...] = tuple(e_ue_list)
                    break
        return stage, g_frame, e_frame, g_ue_list, d_ue_list, e_ue_list

    def render(self, filename: str):
        with open(filename, 'w') as w:
            w.write('<html>\n<head>')
            w.writelines(self.header)
            w.write('</head>\n<body>')
            w.writelines(self.body)
            w.write('</body>\n</html>')


if __name__ == '__main__':
    file_to_visualize = "vis_20201218"

    frame_renderer = FrameRenderer()
    s, gf, ef, gue, due, eue = frame_renderer.open_file(file_to_visualize + ".P")
    tab_title = frame_renderer.gen_phase(s, gf, ef, gue, due, eue)
    frame_renderer.tab_script(tab_title)
    frame_renderer.render(file_to_visualize + '.html')
