# -*- coding: utf-8 -*-
"""
=========
tikzmagic
=========
 
Magics for generating figures with TikZ.
 
.. note::
 
  ``TikZ`` and ``LaTeX`` need to be installed separately.
 
Usage
=====
 
``%%tikz``
 
{TIKZ_DOC}
 
"""
 
#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------
from __future__ import print_function 
import sys
import tempfile
from glob import glob
from os import chdir, getcwd
from subprocess import call
from shutil import rmtree, copy
from xml.dom import minidom
 
from IPython.core.displaypub import publish_display_data
from IPython.core.magic import (Magics, magics_class, line_magic,
                                line_cell_magic, needs_local_scope)
from IPython.testing.skipdoctest import skip_doctest
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring
)
from IPython.utils.py3compat import unicode_to_str
 
_mimetypes = {'png' : 'image/png',
              'svg' : 'image/svg+xml',
              'jpg' : 'image/jpeg',
              'jpeg': 'image/jpeg'}
 
@magics_class
class TikzMagics(Magics):
    """A set of magics useful for creating figures with TikZ.
    """
    def __init__(self, shell):
        """
        Parameters
        ----------
        shell : IPython shell
 
        """
        super(TikzMagics, self).__init__(shell)
        self._plot_format = 'png'
 
        # Allow publish_display_data to be overridden for
        # testing purposes.
        self._publish_display_data = publish_display_data
 
 
    def _fix_gnuplot_svg_size(self, image, size=None):
        """
        GnuPlot SVGs do not have height/width attributes.  Set
        these to be the same as the viewBox, so that the browser
        scales the image correctly.
 
        Parameters
        ----------
        image : str
            SVG data.
        size : tuple of int
            Image width, height.
 
        """
        (svg,) = minidom.parseString(image).getElementsByTagName('svg')
        viewbox = svg.getAttribute('viewBox').split(' ')
 
        if size is not None:
            width, height = size
        else:
            width, height = viewbox[2:]
 
        svg.setAttribute('width', '%dpx' % width)
        svg.setAttribute('height', '%dpx' % height)
        return svg.toxml()
    
    
    def _run_latex(self, code, dir):
        f = open(dir + '/tikz.tex', 'w')
        f.write(code)
        f.close()
        
        current_dir = getcwd()
        chdir(dir)
        
        ret_log = False
        log = None
        
        try:
            retcode = call("pdflatex -shell-escape tikz.tex", shell=True)
            if retcode != 0:
                print("LaTeX terminated with signal", -retcode, file=sys.stderr)
                ret_log = True
        except OSError as e:
            print("LaTeX execution failed:", e, file=sys.stderr)
            ret_log = True
        
        # in case of error return LaTeX log
        if ret_log:
            try:
                f = open('tikz.log', 'r')
                log = f.read()
                f.close()
            except IOError:
                print("No log file generated.", file=sys.stderr)
        
        chdir(current_dir)
    
        return log
    
 
    def _convert_pdf_to_svg(self, dir):
        current_dir = getcwd()
        chdir(dir)
        
        try:
            retcode = call("pdf2svg tikz.pdf tikz.svg", shell=True)
            if retcode != 0:
                print("pdf2svg terminated with signal", -retcode, file=sys.stderr)
        except OSError as e:
            print("pdf2svg execution failed:", e, file=sys.stderr)
        
        chdir(current_dir)
        
 
    def _convert_png_to_jpg(self, dir):
        current_dir = getcwd()
        chdir(dir)
        
        try:
            retcode = call("convert tikz.png -quality 100 -background white -flatten tikz.jpg", shell=True)
            if retcode != 0:
                print("convert terminated with signal", -retcode, file=sys.stderr)
        except OSError as e:
            print("convert execution failed:", e, file=sys.stderr)
 
        chdir(current_dir)
        
 
    @skip_doctest
    @magic_arguments()
    @argument(
        '-sc', '--scale', action='store',
        help='Scaling factor of plots. Default is "--scale 1".'
        )
    @argument(
        '-s', '--size', action='store',
        help='Pixel size of plots, "width,height". Default is "-s 400,240".'
        )
    @argument(
        '-f', '--format', action='store',
        help='Plot format (png, svg or jpg).'
        )
    @argument(
        '-l', '--library', action='store',
        help='TikZ libraries to load, separated by comma, e.g., -l matrix,arrows.'
        )
    @argument(
        '-S', '--save', action='store',
        help='Save a copy to "filename".'
        )
 
    @needs_local_scope
    @argument(
        'code',
        nargs='*',
        )
    @line_cell_magic
    def tikz(self, line, cell=None, local_ns=None):
        '''
        Run TikZ code in LaTeX and plot result.
        
            In [9]: %tikz \draw (0,0) rectangle (1,1);
 
        As a cell, this will run a block of TikZ code::
 
            In [10]: %%tikz
               ....: \draw (0,0) rectangle (1,1);
 
        In the notebook, plots are published as the output of the cell.
 
        The size and format of output plots can be specified::
 
            In [18]: %%tikz -s 600,800 -f svg --scale 2
                ...: \draw (0,0) rectangle (1,1);
                ...: \filldraw (0.5,0.5) circle (.1);
 
        TikZ packages can be loaded with -l package1,package2[,...]::
 
            In [20]: %%tikz -l arrows,matrix
                ...: \matrix (m) [matrix of math nodes, row sep=3em, column sep=4em] {
                ...: A & B \\
                ...: C & D \\
                ...: };
                ...: \path[-stealth, line width=.4mm]
                ...: (m-1-1) edge node [left ] {$ac$} (m-2-1)
                ...: (m-1-1) edge node [above] {$ab$} (m-1-2)
                ...: (m-1-2) edge node [right] {$bd$} (m-2-2)
                ...: (m-2-1) edge node [below] {$cd$} (m-2-2);
        
        '''
        args = parse_argstring(self.tikz, line)
 
        # arguments 'code' in line are prepended to the cell lines
        if cell is None:
            code = ''
            return_output = True
        else:
            code = cell
            return_output = False
 
        code = ' '.join(args.code) + code
 
        # if there is no local namespace then default to an empty dict
        if local_ns is None:
            local_ns = {}
 
        # generate plots in a temporary directory
        plot_dir = tempfile.mkdtemp().replace('\\', '/')
        #print(plot_dir, file=sys.stderr)
        
        if args.scale is not None:
            scale = args.scale
        else:
            scale = '1'
 
        if args.size is not None:
            size = args.size
        else:
            size = '400,240'
 
        width, height = size.split(',')
        
        if args.format is not None:
            plot_format = args.format
        else:
            plot_format = 'png'
 
        if args.library is not None:
            tikz_library = args.library.split(',')
        else:
            tikz_library = None
 
        add_params = ""
        
        if plot_format == 'png' or plot_format == 'jpg' or plot_format == 'jpeg':
            add_params += "density=300,"
        
#\\documentclass[convert={%(add_params)ssize=%(width)sx%(height)s,outext=.%(plot_format)s},border=0pt]{standalone}
        
        tex = []
        tex.append('''
\\documentclass[convert={%(add_params)ssize=%(width)sx%(height)s,outext=.png},border=0pt]{standalone}
\\usepackage{tikz}
        ''' % locals())
        
        if tikz_library is not None:
            for lib in tikz_library:
                tex.append('''
\\usetikzlibrary{%s}
                ''' % lib)
        
        tex.append('''
\\begin{document}
\\begin{tikzpicture}[scale=%(scale)s]
        ''' % locals())
        
        tex.append(code)
        
        tex.append('''
\\end{tikzpicture}
\\end{document}
        ''')
        
        code = ' '.join(tex)
        text_output = self._run_latex(code, plot_dir)
        
        if plot_format == 'jpg' or plot_format == 'jpeg':
            self._convert_png_to_jpg(plot_dir)
        elif plot_format == 'svg':
            self._convert_pdf_to_svg(plot_dir)
        
        key = 'TikZMagic.Tikz'
        display_data = []
 
        # Publish text output
        if text_output:
            display_data.append((key, {'text/plain': text_output}))
 
        image_filename = "%s/tikz.%s" % (plot_dir, plot_format)
        
        # Publish image
        try:
            image = open(image_filename, 'rb').read()
            plot_mime_type = _mimetypes.get(plot_format, 'image/%s' % (plot_format))
            width, height = [int(s) for s in size.split(',')]
            if plot_format == 'svg':
                image = self._fix_gnuplot_svg_size(image, size=(width, height))
            display_data.append((key, {plot_mime_type: image}))
 
        except IOError:
            print("No image generated.", file=sys.stderr)
        
        # Copy output file if requested
        if args.save is not None:
            copy(image_filename, args.save)
        
        rmtree(plot_dir)
 
        for tag, disp_d in display_data:
            if plot_format == 'svg':
                # isolate data in an iframe, to prevent clashing glyph declarations in SVG 
                self._publish_display_data(source=tag, data=disp_d, metadata={'isolated' : 'true'})
            else:
                self._publish_display_data(source=tag, data=disp_d, metadata=None)
 
 
__doc__ = __doc__.format(
    TIKZ_DOC = ' '*8 + TikzMagics.tikz.__doc__,
    )
 
 
def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magics(TikzMagics)
