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

import os
import inkex
import logging as logger
import random
import string
import time
from lxml import etree
import subprocess
import platform

logger.disable(logger.CRITICAL) #comment this line to debug

logger.basicConfig(
    filename='./ext.log',
    filemode='w',
    format='%(levelname)s: %(message)s',
    level=logger.DEBUG
)

FRAME_NODE_ID = '1:2frame'
MAX_WIDTH = 300
DEFAULT_GROUP_ID = 'inkxport:group1'


def randomword(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def run_cli_app(binary_name, args):
    """
    Executes a command-line application.
    Args:
        binary_name (str): The name of the executable.
        args (list): A list of string arguments to pass to the executable.
    """
    # Get the current working directory
    current_dir = os.getcwd()

    # Add .exe extension on Windows
    if platform.system() == "Windows":
        binary_name += ".exe"

    # Construct the full path to the executable
    executable_path = os.path.join(current_dir, binary_name)

    # Build the full command list
    command = executable_path + " " + args

    try:
        subprocess.run(command, shell=True)
    except FileNotFoundError:
        logger.debug(f"Error: The executable '{
                     executable_path}' was not found.")
    except subprocess.CalledProcessError as e:
        logger.debug(
            f"Error: The command returned a non-zero exit code {e.returncode}.")
    except Exception as e:
        logger.debug(f"An unexpected error occurred: {e}")


class TaoChuKyExtension(inkex.EffectExtension, inkex.base.TempDirMixin):
    """EffectExtension to fill selected objects red"""

    def add_arguments(self, pars):
        pars.add_argument("--dpi", type=int, default=700, help="DPI")
        pars.add_argument("--filename", type=str, help="File name")
        pars.add_argument("--export-type", type=str, help="Export type: 1 | 2")

    def effect(self):
        if len(self.svg.selection.values()) == 0:
            return
        start = time.time()
        self._export()
        logger.debug(f"[Time] total: {time.time() - start}")

    def find_all_by_prefix(self, label):
        nodes = []
        for node in self.svg.iter():
            node_label = node.get('inkscape:label')
            if isinstance(node_label, str) and node_label.startswith(label):
                nodes.append(node)
        return nodes

    def select_area(self):
        svg = inkex.base.SvgOutputMixin.get_template(
            width=0, height=0).getroot()
        g = inkex.Group(
            *map(lambda n: n.copy(), list(self.svg.selection.values())))
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
        logger.debug(f"[Time][MesureSize]: {time.time() - start}")
        loaded_svg = inkex.load_svg(infile).getroot()
        g = loaded_svg.getElementById(DEFAULT_GROUP_ID)
        os.remove(infile)
        return (points, g)

    def nomalize_width(self, node, padding=0):
        dx = MAX_WIDTH / node.bounding_box().width
        px = 0
        if padding != 0:
            px = padding * dx
        node.set('transform', f'matrix({
                 dx + px},0.00,0.00,{dx + px},{px},{px})')

    def _export(self):
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
        new_rect.style = {'fill': 'none', 'stroke': 'none'}
        new_rect.set('label', FRAME_NODE_ID)
        g.append(new_rect)
        self.export_final(g)

    def export_final(self, g):
        opt = self.options
        filename = os.path.join(self.svg_path(), opt.filename)
        self.do_export(g, opt.dpi, filename)

    def gen_export_action(self, id, filename):
        return f"export-id:{id};export-filename:{filename};export-id-only;export-do"

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

    def do_export(self, node, dpi, filename):
        start = time.time()
        self.nomalize_width(node)
        export_type = self.options.export_type

        svg = inkex.base.SvgOutputMixin.get_template(
            width=0, height=0).getroot()
        svg.append(self.svg.defs.copy())
        ids = []
        if export_type == "1":
            my_colors = self.find_all_by_prefix('color:')
            for color in my_colors:
                label = color.get('inkscape:label').split(':').pop()
                gc = node.copy()
                gc.set('id', label)
                self.copy_style(color, gc)
                svg.append(gc)
                ids.append(label)
        else:
            label = "chuky"
            gc = node.copy()
            gc.set('id', label)
            svg.append(gc)
            ids.append(label)

        tmpfile = os.path.join(f'out-{randomword(4)}.svg')
        inkex.command.write_svg(svg, tmpfile)
        exports_cmd = []
        export_files = []

        for id in ids:
            export_name = f"{filename}-{id}.png"
            basename = os.path.basename(export_name)
            tmpname = os.path.join(basename)
            export_files.append(basename);
            exports_cmd.append(self.gen_export_action(id, tmpname))

        actions = [f"export-dpi:{dpi}"] + exports_cmd

        inkex.command.inkscape(tmpfile, actions=";".join(actions))  # write svg

        logger.debug(f"[Time][Export]: {time.time() - start}")

        start = time.time()
        target_dir = os.path.dirname(os.path.join(self.svg_path(), self.options.filename))
        for file in export_files:
            cmd = ["--quality=50-60 --force --speed=2"]
            cmd.append(f"--output={os.path.join(target_dir, file)}")
            cmd.append(f"-- {os.path.join(file)}")
            run_cli_app("pngquant-bin/pngquant", " ".join(cmd))
            os.remove(file)
        logger.debug(f"[Time][compress]: {time.time() - start}")

        os.remove(tmpfile)

if __name__ == '__main__':
    TaoChuKyExtension().run()
