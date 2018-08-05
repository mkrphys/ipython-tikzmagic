# ipython-tikzmagic

IPython magics for generating figures with TikZ. You can select the output format as svg, png or jpg, define the image size, specify a scale factor, load TikZ packages, and save to external files. The accompanying IPython notebooks shows some examples demonstrating how to use these features.

The package requires a working LaTeX installation, ImageMagick and pdf2svg.

## Installation

```pip install git+git://github.com/mkrphys/ipython-tikzmagic.git```

## Usage

Load package by writing
```
%load_ext tikzmagic
```
in a notebook cell.
Call tikz by prepending `%tikz` to a single command, e.g.,
```
%tikz \draw (0,0) rectangle (1,1);
```
or by starting a cell with `%%tikz`, e.g.,
```
%%tikz
\draw (0,0) rectangle (1,1);
\filldraw (0.5,0.5) circle (.1);
```

## Optional Arguments

- `-sc` or `--scale`: scaling factor of plots, default=1
- `-s` or `--size`: pixel size of plots, e.g., `-s width,height`, default=400,240
- `-f` or `--format`: plot format (png, svg or jpg), default=png
- `-e` or `--encoding`: text encoding, default=utf-8
- `-x` or `--preamble`: LaTeX preamble to insert before tikz figure, default=None
- `-p` or `--package`: LaTeX packages to load, separated by comma, e.g., `-p pgfplots,textcomp`, default=None
- `-l` or `--library`: TikZ libraries to load, separated by comma, e.g., `-l matrix,arrows`, default=None
- `-S` or `--save`: save a copy to file, e.g., -S filename, default=None

## Example

[IPython example notebook](tikzmagic_test.ipynb)
