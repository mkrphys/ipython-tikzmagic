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

## Example

[IPython example notebook](tikzmagic_test.ipynb)
