import pickle
from typing import List

from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.frame import Frame
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
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
            '</style>'
        ]
        self.body = []

    def generate_rb(self, rb_list: List[ResourceBlock]):
        rb_list = sorted(rb_list, key=lambda x: x.position[0])
        rb_i: int = 0
        for rb in rb_list:
            if rb_i != rb.position[0]:
                self.body.append('<br>')
                rb_i: int = rb.position[0]
            self.body.append(f'[{rb.position[0]}, {rb.position[2]}]')

    def generate_ue_list(self, ue_list: List[UserEquipment]):
        self.body.append(f'\n<div><p>{ue_list[0].ue_type.name}UE:</p>')
        for ue in ue_list:
            self.body.append(f'\n<div><b>User ID</b>: {ue.uuid.hex[:4]}\n<div>')
            self.body.append(f'\nnumerology: {ue.numerology_in_use}')
            self.body.append(f'\nQos: {ue.request_data_rate}')
            if ue.ue_type == UEType.G or ue.ue_type == UEType.D:
                self.body.append(f'\n<br>gnb_info: MCS: {ue.gnb_info.mcs.name}')
                self.body.append(f'\nthe number of RBs: {len(ue.gnb_info.rb)}')
                self.generate_rb(ue.gnb_info.rb)
            if ue.ue_type == UEType.E or ue.ue_type == UEType.D:
                self.body.append(f'\n<br>enb_info: MCS: {ue.enb_info.mcs.name}')
                self.body.append(f'\nthe number of RBs: {len(ue.enb_info.rb)}')
                self.generate_rb(ue.enb_info.rb)
            self.body.append('\n</div>\n</div>')
        self.body.append('\n</div>')

    def gen_layer(self, frame: Frame):
        for layer in frame.layer:
            base_unit = layer.bu
            height, width = len(base_unit), len(base_unit[0])

            table_header = '<th></th>' + ''.join([f'<th>i:{i + 1}</th>' for i in range(width)])

            self.body.append('<table>')
            self.body.append(f'\n<tr>{table_header}</tr>')
            for i in range(height):
                tr = f'<tr><th>j:{i + 1}</th>\n'
                for j in range(width):
                    rb = base_unit[i][j].within_rb
                    ue = rb.ue.uuid.hex[:4] if rb is not None else ''
                    numerology = str(rb.numerology).replace('.', '_') if rb is not None else None
                    tr += f'<td class="{numerology}">{ue}</td>'
                tr += '\n</tr>'
                self.body.append(tr)
            self.body.append(f'\n<tr><td colspan="{width + 1}" style="text-align:left;">')
            self.body.append(f'{layer.nodeb.nb_type.name}NodeB Layer {layer.layer_index + 1}</td></tr>')
            self.body.append('</table>')

    def render(self, filename: str):
        with open(filename, 'w') as w:
            w.write('<html>\n<head>')
            w.writelines(self.header)
            w.write('</head>\n<body>')
            w.writelines(self.body)
            w.write('</body>\n</html>')


if __name__ == '__main__':
    file_to_visualize = "vis_20201121"
    gFrame: List[Frame] = []
    eFrame: List[Frame] = []
    g_ue_list: List[List[GUserEquipment]] = []
    d_ue_list: List[List[DUserEquipment]] = []
    e_ue_list: List[List[EUserEquipment]] = []

    with open(file_to_visualize+".P", "rb") as file_of_frame_and_ue:
        while True:
            try:
                gf, ef, gue, due, eue = pickle.load(file_of_frame_and_ue)
                gFrame.append(gf)
                eFrame.append(ef)
                g_ue_list.append(gue)
                d_ue_list.append(due)
                e_ue_list.append(eue)
            except EOFError:
                break

    frame_renderer = FrameRenderer()
    frame_renderer.gen_layer(gFrame[0])
    frame_renderer.gen_layer(eFrame[0])
    frame_renderer.generate_ue_list(g_ue_list[0])
    frame_renderer.generate_ue_list(d_ue_list[0])
    frame_renderer.generate_ue_list(e_ue_list[0])
    frame_renderer.render(file_to_visualize+'.html')
