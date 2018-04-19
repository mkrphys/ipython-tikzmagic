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
from os import chdir, getcwd, environ, pathsep
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

try:
    import pkg_resources  # part of setuptools
    __version__ = pkg_resources.require("ipython-tikzmagic")[0].version
except ImportError:
    __version__ = 'unknown'


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


    def _run_latex(self, code, encoding, dir):
        f = open(dir + '/tikz.tex', 'w', encoding=encoding)
        f.write(code)
        f.close()

        current_dir = getcwd()
        chdir(dir)

        ret_log = False
        log = None

        # Set the TEXINPUTS environment variable, which allows the tikz code
        # to refence files relative to the notebook (includes, packages, ...)
        env = environ.copy()
        if 'TEXINPUTS' in env:
            env['TEXINPUTS'] =  current_dir + pathsep + env['TEXINPUTS']
        else:
            env['TEXINPUTS'] =  '.' + pathsep + current_dir + pathsep*2
            # note that the trailing double pathsep will insert the standard
            # search path (otherwise we would lose access to all packages)

        try:
            retcode = call("pdflatex --shell-escape tikz.tex", shell=True, env=env)
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
        
 
    def _convert_png_to_jpg(self, dir, imagemagick_path):
        current_dir = getcwd()
        chdir(dir)
        
        try:
            retcode = call("%s tikz.png -quality 100 -background white -flatten tikz.jpg"
                            % imagemagick_path, shell=True)
            if retcode != 0:
                print("convert terminated with signal", -retcode, file=sys.stderr)
        except OSError as e:
            print("convert execution failed:", e, file=sys.stderr)
 
        chdir(current_dir)
        
 
    @skip_doctest
    @magic_arguments()
    @argument(
        '-sc', '--scale', action='store', type=str, default=1,
        help='Scaling factor of plots. Default is "--scale 1".'
        )
    @argument(
        '-s', '--size', action='store', type=str, default='400,240',
        help='Pixel size of plots, "width,height". Default is "--size 400,240".'
        )
    @argument(
        '-f', '--format', action='store', type=str, default='png',
        help='Plot format (png, svg or jpg).'
        )
    @argument(
        '-e', '--encoding', action='store', type=str, default='utf-8',
        help='Text encoding, e.g., -e utf-8.'
        )
    @argument(
        '-x', '--preamble', action='store', type=str, default='',
        help='LaTeX preamble to insert before tikz figure, e.g., -x "$preamble", with preamble some string variable.'
        )
    @argument(
        '-p', '--package', action='store', type=str, default='',
        help='LaTeX packages to load, separated by comma, e.g., -p pgfplots,textcomp.'
        )
    @argument(
        '-l', '--library', action='store', type=str, default='',
        help='TikZ libraries to load, separated by comma, e.g., -l matrix,arrows.'
        )
    @argument(
        '-S', '--save', action='store', type=str, default=None,
        help='Save a copy to file, e.g., -S filename. Default is None'
        )
    @argument('-i', '--imagemagick', action='store', type=str, default='convert',
        help='Name of ImageMagick executable, optionally with full path. Default is "convert"'
        )
    @argument('-po', '--pictureoptions', action='store', type=str, default='',
        help='Additional arguments to pass to the \\tikzpicture command.'
        )
        
    @argument('--showlatex', action='store_true',
        help='Show the LATeX file instead of generating image, for debugging LaTeX errors.'
        )
        
    @argument('-ct', '--circuitikz', action='store_true',
        help='Use CircuiTikZ package instead of regular TikZ.'
        )
        
    @argument('--tikzoptions', action='store', type=str, default='',
        help='Options to pass when loading TikZ or CircuiTikZ package.'
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
        
        # read arguments
        args = parse_argstring(self.tikz, line)
        scale = args.scale
        size = args.size
        width, height = size.split(',')
        plot_format = args.format
        encoding = args.encoding
        tikz_library = args.library.split(',')
        latex_package = args.package.split(',')
        imagemagick_path = args.imagemagick
        picture_options = args.pictureoptions
        tikz_options = args.tikzoptions
 
        # arguments 'code' in line are prepended to the cell lines
        if cell is None:
            code = ''
            return_output = True
        else:
            code = cell
            return_output = False
 
        code = str('').join(args.code) + code
 
        # if there is no local namespace then default to an empty dict
        if local_ns is None:
            local_ns = {}
 
        # generate plots in a temporary directory
        plot_dir = tempfile.mkdtemp().replace('\\', '/')
        
        add_params = ""
        
        if plot_format == 'png' or plot_format == 'jpg' or plot_format == 'jpeg':
            add_params += "density=300,"
        
        # choose between CircuiTikZ and regular Tikz
        if args.circuitikz:
            tikz_env = 'circuitikz'
            tikz_package = 'circuitikz'
        else:
            tikz_env = 'tikzpicture'
            tikz_package = 'tikz'
            
        tex = []
        tex.append('''
\\documentclass[convert={convertexe={%(imagemagick_path)s},%(add_params)ssize=%(width)sx%(height)s,outext=.png},border=0pt]{standalone}
        ''' % locals())

        tex.append('\\usepackage[%(tikz_options)s]{%(tikz_package)s}\n' % locals())
        
        for pkg in latex_package:
            tex.append('''
\\usepackage{%s}
            ''' % pkg)
        
        for lib in tikz_library:
            tex.append('''
\\usetikzlibrary{%s}
            ''' % lib)
        
        if args.preamble is not None:
            tex.append('''
%s
            ''' % args.preamble)
        
        tex.append('''
\\begin{document}
\\begin{%(tikz_env)s}[scale=%(scale)s,%(picture_options)s]
        ''' % locals())
        
        tex.append(code)
        
        tex.append('''
\\end{%(tikz_env)s}
\\end{document}
        ''' % locals())
        
        code = str('').join(tex)
        
        if args.showlatex:
            print(code)
            return

        latex_log = self._run_latex(code, encoding, plot_dir)
        
        key = 'TikZMagic.Tikz'
        display_data = []

        # If the latex error log exists, then image generation has failed.
        # Publish error log and return immediately
        if latex_log:
            self._publish_display_data(source=key, data={'text/plain': latex_log})
            return

        if plot_format == 'jpg' or plot_format == 'jpeg':
            self._convert_png_to_jpg(plot_dir, imagemagick_path)
        elif plot_format == 'svg':
            self._convert_pdf_to_svg(plot_dir)

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
