#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) [YEAR] [YOUR NAME], [YOUR EMAIL]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
This extension changes the fill of all selected elements to red.
"""

import os
import inkex
import logging as logger
import random, string
import time
from lxml import etree

logger.basicConfig(filename='./ext.log',
filemode='w', format='%(levelname)s: %(message)s', level=logger.DEBUG)

FRAME_NODE_ID = '1:2frame'
MAX_WIDTH = 300
DEFAULT_GROUP_ID = 'inkxport:group1'
def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

class TaoChuKyExtension(inkex.EffectExtension, inkex.base.TempDirMixin):
    """EffectExtension to fill selected objects red"""

    def add_arguments(self, pars):
        pars.add_argument("--dpi", type=int, default=700, help="DPI")
        pars.add_argument("--filename", type=str, help="File name")

    def effect(self):
        if len(self.svg.selection.values()) == 0:
            return
        start = time.time()
        self._export()
        logger.debug(f"[Time] total: {time.time() - start }")
    
    def find_by_label(self, label):
        for node in self.svg.iter():
            node_label = node.get('inkscape:label')
            if node_label == label:
                return node
        return None

    def find_all_by_prefix(self, label):
        nodes = []
        for node in self.svg.iter():
            node_label = node.get('inkscape:label')
            if isinstance(node_label, str) and node_label.startswith(label):
                nodes.append(node)
        return nodes

    def select_area(self):
        os.environ["SELF_CALL"] = "true"

        svg = inkex.base.SvgOutputMixin.get_template(width=0, height=0).getroot()
        g = inkex.Group(*map(lambda n: n.copy(), list(self.svg.selection.values())))
        g.set('id', DEFAULT_GROUP_ID)
        svg.append(g)
        infile = os.path.join(f'in-{randomword(6)}.svg')
        inkex.command.write_svg(svg, infile)

        start = time.time()
        actions = [
            'select-all:all',
            'object-to-path',
            'export-overwrite',
            'export-do'
        ]
        d = inkex.command.inkscape(
            infile, 
            actions=";".join(actions),
            select=DEFAULT_GROUP_ID,
            X=True,
            Y=True,
            W=True,
            H=True,
        )

        points = list(map(lambda n: float(n), d.splitlines()))
        logger.debug(f"[Time][MesureSize]: {time.time() - start }")
        loaded_svg = inkex.load_svg(infile).getroot()
        g = loaded_svg.getElementById(DEFAULT_GROUP_ID)
        os.remove(infile)
        return (points, g)

    def nomalize_width(self, node, padding=0):
        dx = MAX_WIDTH / node.bounding_box().width
        px = 0
        if padding != 0:
            px = padding * dx
        node.set('transform', f'matrix({dx + px},0.00,0.00,{dx + px},{px},{px})')

    def _export(self):
        os.environ["SELF_CALL"] = "true"
        c, g = self.select_area()
        x, y, w0, h0 = c
        w = w0
        h = h0
        if h <= w / 2:
            h = w / 2
        else:
            w = h * 2
        x = x + w0/2 - w/2
        y = y + h0/2 - h/2
        new_rect = inkex.Rectangle(
            x=f'{x}',
            y=f'{y}',
            width=f'{w}',
            height=f'{h}')
        new_rect.style ={'fill' : 'none', 'stroke' : 'none'}
        new_rect.set('label', FRAME_NODE_ID)
        g.append(new_rect)
        self.export_final(g)

    def export_final(self, g):
        os.environ["SELF_CALL"] = "true"
        opt = self.options
        filename = os.path.join(self.svg_path(), opt.filename)
        self.do_export(g, opt.dpi, filename)
    
    def gen_export_action(self, id, filename):
        return f"export-id:{id};export-filename:{filename}-{id}.png;export-id-only;export-do"

    def do_export(self, node, dpi, filename):
        my_colors = self.find_all_by_prefix('color:')
        start = time.time()
        self.nomalize_width(node)

        svg = inkex.base.SvgOutputMixin.get_template(width=0, height=0).getroot()
        svg.append(self.svg.defs.copy())
        ids = []
        for color in my_colors:
            label = color.get('inkscape:label').split(':').pop()
            gc = node.copy()
            gc.set('id', label)
            self.copy_style(color, gc)
            svg.append(gc)
            ids.append(label)

        tmpfile = os.path.join(f'out-{randomword(4)}.svg')
        inkex.command.write_svg(svg, tmpfile)
        exports = []
        exports = list(map(lambda id: self.gen_export_action(id, filename), ids))
        actions = [f"export-dpi:{dpi}"] + exports
        res = inkex.command.inkscape(tmpfile, actions=";".join(actions))
        os.remove(tmpfile)
        logger.debug(f"[Time][Export]: {time.time() - start }")

    def copy_style(self, from_node, to_node):
        style = from_node.get('style')
        logger.debug(style)
        elements = [
                element
                for element in to_node.iter()
                if isinstance(element, (inkex.base.IBaseElement, str))
        ]
        for child in elements:
            if child.get('label') != FRAME_NODE_ID:
                child.set('style', style)

    def set_fill(self, node, color):
        elements = [
                element
                for element in node.iter()
                if isinstance(element, (inkex.base.IBaseElement, str))
        ]
        for child in elements:
            if child.get('label') != FRAME_NODE_ID:
                child.style["fill"] = color

if __name__ == '__main__':
    TaoChuKyExtension().run()
