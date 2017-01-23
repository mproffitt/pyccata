"""
Venn class adapted from https://github.com/tctianchi/pyvenn
"""
# coding: utf-8
from itertools import chain
import matplotlib.pyplot as plt
import matplotlib.patches as patches

DEFAULT_COLOURS = [
    # r, g, b, a
    [92, 192, 98, 0.5],
    [90, 155, 212, 0.5],
    [246, 236, 86, 0.6],
    [241, 90, 96, 0.4],
    [255, 117, 0, 0.3],
    [82, 82, 190, 0.2],
]
DEFAULT_COLOURS = [
    [i[0] / 255.0, i[1] / 255.0, i[2] / 255.0, i[3]]
    for i in DEFAULT_COLOURS
]

def draw_ellipse(axes, xpos, ypos, width, height, angle, fillcolor):
    """
    Draw ellipses for 2 - 5 venn graphs

    :param: axes
    :param int: xpos
    :param int: ypos
    :param int: width
    :param int: height
    :param float: angle
    :param list: fillcolor
    """
    # pylint: disable=too-many-arguments
    ellipse = patches.Ellipse(
        xy=(xpos, ypos),
        width=width,
        height=height,
        angle=angle,
        color=fillcolor)
    axes.add_patch(ellipse)

def draw_text(axes, xpos, ypos, text, color=None):
    """
    Draw text onto the axis

    :param int: xpos
    :param int: ypos
    :param string: text
    :param list: color
    """
    # pylint: disable=too-many-arguments
    color = [0, 0, 0, 1] if color is None else color
    axes.text(
        xpos, ypos, text,
        horizontalalignment='center',
        verticalalignment='center',
        fontsize=14,
        color=color)

def draw_annotate(xpos, ypos, textx, texty, text, color=None, arrowcolor=None):
    """
    Annotate the axis at a particular point

    :param matplotlib.Axes: axes
    :param int: xpos
    :param int: ypos
    :param int: textx
    :param int: texty
    :param string: text
    :param list: color
    :param list: arrowcolor
    """
    # pylint: disable=too-many-arguments
    color = [0, 0, 0, 1] if color is None else color
    arrowcolor = [0, 0, 0, .3] if arrowcolor is None else arrowcolor
    plt.annotate(
        text,
        xy=(xpos, ypos),
        xytext=(textx, texty),
        arrowprops=dict(color=arrowcolor, shrink=0, width=0.5, headwidth=8),
        fontsize=14,
        color=color,
        xycoords="data",
        textcoords="data",
        horizontalalignment='center',
        verticalalignment='center'
    )

def get_labels(data, fill=None):
    """
    get a dict of labels for groups in data

    @type data: list[Iterable]
    @rtype: dict[str, str]

    input
      data: data to get label for
      fill: ["number"|"logic"|"percent"]

    return
      labels: a dict of labels for different sets

    example:
    In [12]: get_labels([range(10), range(5,15), range(3,8)], fill=["number"])
    Out[12]:
    {'001': '0',
     '010': '5',
     '011': '0',
     '100': '3',
     '101': '2',
     '110': '2',
     '111': '3'}
    """
    # pylint: disable=too-many-locals
    fill = ['number'] if fill is None else fill

    set_length = len(data)

    sets_data = [set(data[i]) for i in range(set_length)]  # sets for separate groups
    s_all = set(chain(*data)) # union of all sets

    # bin(3) --> '0b11', so bin(3).split('0b')[-1] will remove "0b"
    set_collections = {}
    for index in range(1, 2**set_length):
        key = bin(index).split('0b')[-1].zfill(set_length)
        value = s_all
        sets_for_intersection = [sets_data[i] for i in range(set_length) if key[i] == '1']
        sets_for_difference = [sets_data[i] for i in range(set_length) if key[i] == '0']
        for intersection in sets_for_intersection:
            value = value & intersection
        for difference in sets_for_difference:
            value = value - difference
        set_collections[key] = value

    labels = {k: "" for k in set_collections}
    if "logic" in fill:
        for current in set_collections:
            labels[current] = current + ": "
    if "number" in fill:
        for current in set_collections:
            labels[current] += str(len(set_collections[current]))
    if "percent" in fill:
        data_size = len(s_all)
        for current in set_collections:
            labels[current] += "(%.1f%%)" % (100.0 * len(set_collections[current]) / data_size)

    return labels

def venn2(labels, names=None, **options):
    """
    plots a 2-set Venn diagram

    @type labels: dict[str, str]
    @type names: list[str]
    @rtype: (Figure, AxesSubplot)

    input
      labels: a label dict where keys are identified via binary codes ('01', '10', '11'),
              hence a valid set could look like: {'01': 'text 1', '10': 'text 2', '11': 'text 3'}.
              unmentioned codes are considered as ''.
      names:  group names
      more:   colors, figsize, dpi

    return
      pyplot Figure and AxesSubplot object
    """
    names = names if names is not None else ['A', 'B']
    colors = options.get('colors', [DEFAULT_COLOURS[i] for i in range(2)])
    figsize = options.get('figsize', (9, 7))
    dpi = options.get('dpi', 96)

    fig = plt.figure(0, figsize=figsize, dpi=dpi)
    axes = fig.add_subplot(111, aspect='equal')
    axes.set_axis_off()
    axes.set_ylim(bottom=0.0, top=0.7)
    axes.set_xlim(left=0.0, right=1.0)

    # body
    draw_ellipse(axes, 0.375, 0.3, 0.5, 0.5, 0.0, colors[0])
    draw_ellipse(axes, 0.625, 0.3, 0.5, 0.5, 0.0, colors[1])
    draw_text(axes, 0.74, 0.30, labels.get('01', ''))
    draw_text(axes, 0.26, 0.30, labels.get('10', ''))
    draw_text(axes, 0.50, 0.30, labels.get('11', ''))

    # legend
    draw_text(axes, 0.20, 0.56, names[0], colors[0])
    draw_text(axes, 0.80, 0.56, names[1], colors[1])
    leg = axes.legend(names, loc='best', fancybox=True)
    leg.get_frame().set_alpha(0.5)

    return fig, axes

def venn3(labels, names=None, **options):
    """
    plots a 3-set Venn diagram

    @type labels: dict[str, str]
    @type names: list[str]
    @rtype: (Figure, AxesSubplot)

    input
      labels: a label dict where keys are identified via binary codes ('001', '010', '100', ...),
              hence a valid set could look like: {'001': 'text 1', '010': 'text 2', '100': 'text 3', ...}.
              unmentioned codes are considered as ''.
      names:  group names
      more:   colors, figsize, dpi

    return
      pyplot Figure and AxesSubplot object
    """
    names = names if names is not None else ['A', 'B', 'C']
    colors = options.get('colors', [DEFAULT_COLOURS[i] for i in range(3)])
    figsize = options.get('figsize', (9, 9))
    dpi = options.get('dpi', 96)

    fig = plt.figure(0, figsize=figsize, dpi=dpi)
    axes = fig.add_subplot(111, aspect='equal')
    axes.set_axis_off()
    axes.set_ylim(bottom=0.0, top=1.0)
    axes.set_xlim(left=0.0, right=1.0)

    # body
    draw_ellipse(axes, 0.333, 0.633, 0.5, 0.5, 0.0, colors[0])
    draw_ellipse(axes, 0.666, 0.633, 0.5, 0.5, 0.0, colors[1])
    draw_ellipse(axes, 0.500, 0.310, 0.5, 0.5, 0.0, colors[2])
    draw_text(axes, 0.50, 0.27, labels.get('001', ''))
    draw_text(axes, 0.73, 0.65, labels.get('010', ''))
    draw_text(axes, 0.61, 0.46, labels.get('011', ''))
    draw_text(axes, 0.27, 0.65, labels.get('100', ''))
    draw_text(axes, 0.39, 0.46, labels.get('101', ''))
    draw_text(axes, 0.50, 0.65, labels.get('110', ''))
    draw_text(axes, 0.50, 0.51, labels.get('111', ''))

    # legend
    draw_text(axes, 0.15, 0.87, names[0], colors[0])
    draw_text(axes, 0.85, 0.87, names[1], colors[1])
    draw_text(axes, 0.50, 0.02, names[2], colors[2])
    leg = axes.legend(names, loc='best', fancybox=True)
    leg.get_frame().set_alpha(0.5)

    return fig, axes

def venn4(labels, names=None, **options):
    """
    plots a 4-set Venn diagram

    @type labels: dict[str, str]
    @type names: list[str]
    @rtype: (Figure, AxesSubplot)

    input
      labels: a label dict where keys are identified via binary codes ('0001', '0010', '0100', ...),
              hence a valid set could look like: {'0001': 'text 1', '0010': 'text 2', '0100': 'text 3', ...}.
              unmentioned codes are considered as ''.
      names:  group names
      more:   colors, figsize, dpi

    return
      pyplot Figure and AxesSubplot object
    """
    names = names if names is not None else ['A', 'B', 'C', 'D']
    colors = options.get('colors', [DEFAULT_COLOURS[i] for i in range(4)])
    figsize = options.get('figsize', (12, 12))
    dpi = options.get('dpi', 96)

    fig = plt.figure(0, figsize=figsize, dpi=dpi)
    axes = fig.add_subplot(111, aspect='equal')
    axes.set_axis_off()
    axes.set_ylim(bottom=0.0, top=1.0)
    axes.set_xlim(left=0.0, right=1.0)

    # body
    draw_ellipse(axes, 0.350, 0.400, 0.72, 0.45, 140.0, colors[0])
    draw_ellipse(axes, 0.450, 0.500, 0.72, 0.45, 140.0, colors[1])
    draw_ellipse(axes, 0.544, 0.500, 0.72, 0.45, 40.0, colors[2])
    draw_ellipse(axes, 0.644, 0.400, 0.72, 0.45, 40.0, colors[3])
    draw_text(axes, 0.85, 0.42, labels.get('0001', ''))
    draw_text(axes, 0.68, 0.72, labels.get('0010', ''))
    draw_text(axes, 0.77, 0.59, labels.get('0011', ''))
    draw_text(axes, 0.32, 0.72, labels.get('0100', ''))
    draw_text(axes, 0.71, 0.30, labels.get('0101', ''))
    draw_text(axes, 0.50, 0.66, labels.get('0110', ''))
    draw_text(axes, 0.65, 0.50, labels.get('0111', ''))
    draw_text(axes, 0.14, 0.42, labels.get('1000', ''))
    draw_text(axes, 0.50, 0.17, labels.get('1001', ''))
    draw_text(axes, 0.29, 0.30, labels.get('1010', ''))
    draw_text(axes, 0.39, 0.24, labels.get('1011', ''))
    draw_text(axes, 0.23, 0.59, labels.get('1100', ''))
    draw_text(axes, 0.61, 0.24, labels.get('1101', ''))
    draw_text(axes, 0.35, 0.50, labels.get('1110', ''))
    draw_text(axes, 0.50, 0.38, labels.get('1111', ''))

    # legend
    draw_text(axes, 0.13, 0.18, names[0], colors[0])
    draw_text(axes, 0.18, 0.83, names[1], colors[1])
    draw_text(axes, 0.82, 0.83, names[2], colors[2])
    draw_text(axes, 0.87, 0.18, names[3], colors[3])
    leg = axes.legend(names, loc='best', fancybox=True)
    leg.get_frame().set_alpha(0.5)

    return fig, axes

def venn5(labels, names=None, **options):
    """
    plots a 5-set Venn diagram

    @type labels: dict[str, str]
    @type names: list[str]
    @rtype: (Figure, AxesSubplot)

    input
      labels: a label dict where keys are identified via binary codes ('00001', '00010', '00100', ...),
              hence a valid set could look like: {'00001': 'text 1', '00010': 'text 2', '00100': 'text 3', ...}.
              unmentioned codes are considered as ''.
      names:  group names
      more:   colors, figsize, dpi

    return
      pyplot Figure and AxesSubplot object
    """
    # pylint: disable=too-many-statements
    # This is always going to be an ugly function as we're
    # assigning into the graph

    names = names if names is not None else ['A', 'B', 'C', 'D', 'E']
    colors = options.get('colors', [DEFAULT_COLOURS[i] for i in range(5)])
    figsize = options.get('figsize', (13, 13))
    dpi = options.get('dpi', 96)

    fig = plt.figure(0, figsize=figsize, dpi=dpi)
    axes = fig.add_subplot(111, aspect='equal')
    axes.set_axis_off()
    axes.set_ylim(bottom=0.0, top=1.0)
    axes.set_xlim(left=0.0, right=1.0)

    # body
    draw_ellipse(axes, 0.428, 0.449, 0.87, 0.50, 155.0, colors[0])
    draw_ellipse(axes, 0.469, 0.543, 0.87, 0.50, 82.0, colors[1])
    draw_ellipse(axes, 0.558, 0.523, 0.87, 0.50, 10.0, colors[2])
    draw_ellipse(axes, 0.578, 0.432, 0.87, 0.50, 118.0, colors[3])
    draw_ellipse(axes, 0.489, 0.383, 0.87, 0.50, 46.0, colors[4])
    draw_text(axes, 0.27, 0.11, labels.get('00001', ''))
    draw_text(axes, 0.72, 0.11, labels.get('00010', ''))
    draw_text(axes, 0.55, 0.13, labels.get('00011', ''))
    draw_text(axes, 0.91, 0.58, labels.get('00100', ''))
    draw_text(axes, 0.78, 0.64, labels.get('00101', ''))
    draw_text(axes, 0.84, 0.41, labels.get('00110', ''))
    draw_text(axes, 0.76, 0.55, labels.get('00111', ''))
    draw_text(axes, 0.51, 0.90, labels.get('01000', ''))
    draw_text(axes, 0.39, 0.15, labels.get('01001', ''))
    draw_text(axes, 0.42, 0.78, labels.get('01010', ''))
    draw_text(axes, 0.50, 0.15, labels.get('01011', ''))
    draw_text(axes, 0.67, 0.76, labels.get('01100', ''))
    draw_text(axes, 0.70, 0.71, labels.get('01101', ''))
    draw_text(axes, 0.51, 0.74, labels.get('01110', ''))
    draw_text(axes, 0.64, 0.67, labels.get('01111', ''))
    draw_text(axes, 0.10, 0.61, labels.get('10000', ''))
    draw_text(axes, 0.20, 0.31, labels.get('10001', ''))
    draw_text(axes, 0.76, 0.25, labels.get('10010', ''))
    draw_text(axes, 0.65, 0.23, labels.get('10011', ''))
    draw_text(axes, 0.18, 0.50, labels.get('10100', ''))
    draw_text(axes, 0.21, 0.37, labels.get('10101', ''))
    draw_text(axes, 0.81, 0.37, labels.get('10110', ''))
    draw_text(axes, 0.74, 0.40, labels.get('10111', ''))
    draw_text(axes, 0.27, 0.70, labels.get('11000', ''))
    draw_text(axes, 0.34, 0.25, labels.get('11001', ''))
    draw_text(axes, 0.33, 0.72, labels.get('11010', ''))
    draw_text(axes, 0.51, 0.22, labels.get('11011', ''))
    draw_text(axes, 0.25, 0.58, labels.get('11100', ''))
    draw_text(axes, 0.28, 0.39, labels.get('11101', ''))
    draw_text(axes, 0.36, 0.66, labels.get('11110', ''))
    draw_text(axes, 0.51, 0.47, labels.get('11111', ''))

    # legend
    draw_text(axes, 0.02, 0.72, names[0], colors[0])
    draw_text(axes, 0.72, 0.94, names[1], colors[1])
    draw_text(axes, 0.97, 0.74, names[2], colors[2])
    draw_text(axes, 0.88, 0.05, names[3], colors[3])
    draw_text(axes, 0.12, 0.05, names[4], colors[4])
    leg = axes.legend(names, loc='best', fancybox=True)
    leg.get_frame().set_alpha(0.5)

    return fig, axes
