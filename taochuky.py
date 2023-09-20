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
from inkex.command import to_args, call, which
import random, string

logger.basicConfig(filename='./ext.log',
filemode='w', format='%(levelname)s: %(message)s', level=logger.DEBUG)

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
        pass # We don't need arguments for this extension

    def effect(self):
        for elem in self.svg.selection:
            self._set_fill(elem)

        self._create_bounding_box()

    def select_area(self):
        os.environ["SELF_CALL"] = "true"
        svg = inkex.base.SvgOutputMixin.get_template(width=0, height=0).getroot()
        g = inkex.Group(*map(clone_node, list(self.svg.selection.values())))
        groupId = "GROUP_OBJ"
        g.set('id', groupId)
        svg.append(g)
        infile = os.path.join(f'{randomword(6)}.svg')
        inkex.command.write_svg(svg, infile)
        logger.debug(f'file: {infile}')

        actions = [
            f"select-by-id:{groupId}",
            'object-to-path',
            "export-overwrite",
            "export-do"
        ]
        inkex.command.inkscape(
                infile, 
                actions=";".join(actions),
                select=groupId,
                export_overwrite=True
            )
        d = inkex.command.inkscape(
                infile,
                X=True,
                Y=True,
                W=True,
                H=True,
                query_id=groupId
            )

        points = list(map(lambda n: float(n), d.splitlines()))
        logger.debug(points)

        return points


    def _create_bounding_box(self):
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
        new_rect.style ={'fill' : 'none', 'stroke' : '#ff33ee', 'stroke-width' : '0.1'}

        g = inkex.Group(new_rect, *map(clone_node, list(self.svg.selection.values())))
        layer.add(g)

    def _set_fill(self, node):
        pass # implement later
        # for child in node.descendants():
        #     child.style["fill"] = "#ff00ff"

if __name__ == '__main__':
    TaoChuKyExtension().run()
