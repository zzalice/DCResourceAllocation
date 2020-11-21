import pickle
from typing import List

from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.frame import Frame
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment


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

    def gen_tables(self, frame: Frame):
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
    file_to_visualize = "vis_20201121.P"
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
    frame_renderer.gen_tables(gFrame[0])
    frame_renderer.gen_tables(eFrame[0])
    frame_renderer.render(file_to_visualize+'.html')
