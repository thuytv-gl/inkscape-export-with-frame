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
import math
import inkex
import logging as logger
import sys
import random, string
import time

logger.basicConfig(filename='./ext.log',
filemode='w', format='%(levelname)s: %(message)s', level=logger.DEBUG)

FRAME_NODE_ID = '1:2frame'
MAX_WIDTH = 400
def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

def clone_node(node):
    newn = node.copy()
    newn.set('id', "")
    return newn

class TaoChuKyExtension(inkex.EffectExtension, inkex.base.TempDirMixin):
    """EffectExtension to fill selected objects red"""

    def add_arguments(self, pars):
        pars.add_argument("--dpi", type=int, default=700, help="DPI")
        pars.add_argument("--filename", type=str, help="File name")
        pars.add_argument("--export-type", type=str, default="demo", help="Export type: demo|done")

    def effect(self):
        start = time.time()
        self._export()
        logger.debug(f"[Time] total: {time.time() - start }")
    
    def find_by_label(self, label):
        for node in self.svg.iter():
            node_label = node.get('inkscape:label')
            if node_label == label:
                return node
        return None

    def select_area(self):
        os.environ["SELF_CALL"] = "true"

        svg = inkex.base.SvgOutputMixin.get_template(width=0, height=0).getroot()
        g = inkex.Group(*map(clone_node, list(self.svg.selection.values())))
        groupId = randomword(10)
        g.set('id', groupId)
        svg.append(g)
        infile = os.path.join(f'{randomword(6)}.svg')
        inkex.command.write_svg(svg, infile)

        start = time.time()
        actions = [
            "active-window-start",
            f"select-by-id:{groupId}",
            'object-to-path',
            "export-overwrite",
            "export-do"
        ]
        d = inkex.command.inkscape(
                infile, 
                actions=";".join(actions),
                select=groupId,
                X=True,
                Y=True,
                W=True,
                H=True,
            )

        points = list(map(lambda n: float(n), d.splitlines()))
        logger.debug(f"[Time][MesureSize] mesuring: {time.time() - start }")

        os.remove(infile)
        return points


    def _export(self):
        os.environ["SELF_CALL"] = "true"
        layer = self.svg.get_current_layer()
        c = self.select_area()
        x, y, w0, h0 = c
        w = w0
        h = h0
        if h <= w / 2:
            h = w / 2
        else:
            w = h * 2
        new_rect = inkex.Rectangle(
            x=f'{x + w0/2 - w/2}',
            y=f'{y + h0/2 - h/2}',
            width=f'{w}',
            height=f'{h}')
        new_rect.style ={'fill' : 'none', 'stroke' : 'none'}
        new_rect.set('label', FRAME_NODE_ID)

        g = inkex.Group(new_rect, *map(clone_node, list(self.svg.selection.values())))

        if self.options.export_type == 'demo':
            bg = self.find_by_label('demo-background')
            if bg != None:
                padding = 10
                bg_copy = bg.copy()
                bg_copy.set('x', x + w0/2 - w/2 - padding)
                bg_copy.set('y', y + h0/2 - h/2 - padding)
                bg_copy.set('width', w + padding * 2)
                bg_copy.set('height', h + padding * 2)
                g.insert(0, bg_copy)
            self.export_demo(g)
        else:
            self.export_final(g)
    
    def export_demo(self, g):
        os.environ["SELF_CALL"] = "true"
        opt = self.options
        export_type = opt.export_type
        filename = os.path.join(self.svg_path(), opt.filename)
        colors = [('den-demo', '000000')]
        self.do_export(g, colors, 100, filename, False)

    def export_final(self, g):
        os.environ["SELF_CALL"] = "true"
        opt = self.options
        export_type = opt.export_type
        filename = os.path.join(self.svg_path(), opt.filename)
        colors = [('den', '000000'), ('trang', 'ffffff'), ('gold', 'ffd42aff')]
        self.do_export(g, colors, opt.dpi, filename)
    
    def gen_demo_export_action(self, filename):
        return f"export-id:{id};;export-filename:{filename}-{id}.png;export-do"
        pass
    
    def gen_export_action(self, id, filename):
        return f"export-id:{id};export-filename:{filename}-{id}.png;export-id-only;export-do"

    def do_export(self, node, colors, dpi, filename, demo=False):
        dx = MAX_WIDTH / node.bounding_box().width
        node.set('transform', f'matrix({dx},0.00,0.00,{dx},0,0)')

        svg = inkex.base.SvgOutputMixin.get_template(width=0, height=0).getroot()
        svg.append(self.svg.defs.copy())
        ids = []
        for cid, color in colors:
            gc = node.copy()
            gc.set('id', cid)
            self.set_fill(gc, f'#{color}')
            svg.append(gc)
            ids.append(cid)

        tmpfile = os.path.join(f'{randomword(4)}.svg')
        inkex.command.write_svg(svg, tmpfile)
        exports = []
        if demo:
            exports = list(map(lambda id: self.gen_demo_export_action(id, filename), ids))
        else:
            exports = list(map(lambda id: self.gen_export_action(id, filename), ids))
        actions = [ "active-window-start", f"export-dpi:{dpi}" ]
        
        actions = actions + exports
        inkex.command.inkscape(tmpfile, actions=";".join(actions))
        os.remove(tmpfile)

    def set_fill(self, node, color):
        elements = [
                element
                for element in node.iter()
                if isinstance(element, (inkex.base.IBaseElement, str))
        ]
        for child in elements:
            if child.get('label') == FRAME_NODE_ID:
                continue
            child.style["fill"] = color

if __name__ == '__main__':
    TaoChuKyExtension().run()
