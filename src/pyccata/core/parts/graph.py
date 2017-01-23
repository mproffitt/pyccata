"""
module for creating graphs
"""

import os

from memory_profiler import profile

# pylint: disable=wrong-import-position
# Matplotlib needs to be initialised before pyplot can be
# imported. Therefore the import order needs to be ignored
# within this module.
import matplotlib
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.colors as colors

import pyupset as pyu
from pyccata.libraries import venn

from pyccata.core.configuration import Configuration
from pyccata.core.parts.picture import Picture
from pyccata.core.exceptions import InvalidGraphError
from pyccata.core.filter import Filter
from pyccata.core.resources import MultiResultList
from pyccata.core.log import Logger
from pyccata.core.exceptions import ThreadFailedError

class Graph(Picture):
    """
    Graph data in different forms
    """
    # pylint: disable=too-many-instance-attributes
    # This is a fourth level extension - attributes are cumulative
    _colours = [
        'r', 'g', 'b'
    ],
    _colour_index = 0

    _filenames = []

    def setup(self, query=None, width=100, graphtype=None, structure=None):
        """
        Set up the graph object
        """
        # pylint: disable=arguments-differ
        self.configuration = self.threadmanager.configuration
        self._width = width if isinstance(width, int) and width < 100 else 100
        self._filename = Graph._get_filename(graphtype, query.query)
        self._filenames = []
        self._graph = structure
        self._path = self.configuration.csv.output_directory
        if not os.path.exists(self._path):
            os.makedirs(self._path)

        if not hasattr(self, graphtype):
            if not hasattr(self, graphtype + '_graph'):
                raise InvalidGraphError('No graph type found for graph type \'{0}\''.format(graphtype))
            graphtype = graphtype + '_graph'
        self._graph_type = graphtype

        if hasattr(query, 'fields') and hasattr(query, 'group_by') and query.group_by not in query.fields:
            query.fields.append(query.group_by)

        self._content = Filter(
            query.query,
            max_results=(query.max_results if hasattr(query, 'max_results') else False),
            fields=(query.fields if hasattr(query, 'fields') else []),
            collate=(query.collate if hasattr(query, 'collate') else None),
            distinct=(query.distinct if hasattr(query, 'distinct') else False),
            namespace=Configuration.NAMESPACE,
            group_by=(query.group_by if hasattr(query, 'group_by') else None)
        )
        self.threadmanager.append(self._content)

    @staticmethod
    def _get_filename(graphtype, query):
        """
        Gets a filename for the current graph
        """
        query = ''.join(e for e in query if e.isalnum()).lower()
        if query == '':
            query = 'no_query_{0}'.format(Configuration.IMAGE_INDEX)
            Configuration.IMAGE_INDEX += 1

        return graphtype + '_' + query

    def run(self):
        """
        Execute the current thread
        """
        while not self._complete:
            if self._content.complete:
                self.save()

        if self._content.failed:
            Logger().warning('Failed to execute \'' + self._content.query + '\'')
            Logger().warning('Reason was:')
            Logger().warning(self._content.failure)

    def render(self, report):
        """
        Render the graph onto the report
        """
        Logger().info('Adding graph {0}'.format(self.title if self.title is not None else ''))
        if not self._complete:
            raise ThreadFailedError('Failed to render document. Has thread been executed?')
        for filename in self._filenames:
            self._filename = filename
            report.add_picture(os.path.join(os.getcwd(), self.filepath), width=self.width)

    def save(self):
        """
        Saves the graph to file
        """
        datasets = self._content.results
        if isinstance(datasets, pyu.DataExtractor):
            self._save(datasets)
            self._complete = True
            return
        elif not isinstance(datasets, MultiResultList):
            results = MultiResultList()
            results.append(datasets)
            datasets = results

        for dataset in datasets:
            self._save(dataset)
        self._complete = True

    def _save(self, dataset):
        """
        Performs the actual save...
        """
        filename = ''
        try:
            filename = self._filename + '_' + dataset.name.lower() + '.png'
        except AttributeError:
            filename = self._filename + '_' + '_'.join(dataset.name) + '.png'
        Logger().info('Plotting results for graph {0}'.format(filename))
        try:
            plot = getattr(self, self._graph_type)(dataset)
            figure = plot.get_figure() if not isinstance(plot, matplotlib.figure.Figure) else plot
            if hasattr(figure, 'suptitle'):
                figure.suptitle(
                    '{name} - {query}'.format(
                        name=dataset.name,
                        query=self._content.query
                    ),
                    fontsize=12,
                    fontweight='bold'
                )
            if hasattr(self._graph, 'legend') and self._graph.legend:
                lgd = plot.legend(loc='upper left', bbox_to_anchor=(0, 4), mode="expand", borderaxespad=0.3)
                figure.savefig(
                    os.path.join(self._path, filename),
                    dpi=1200,
                    bbox_extra_artists=(lgd,),
                    bbox_inches='tight'
                )
            else:
                figure.savefig(
                    os.path.join(self._path, filename)
                )
            figure.clf()
            plt.close(figure)
            self._filenames.append(filename)
        except Exception as exception:
            Logger().warning('Failed to create graph for dataset \'{0}\''.format(filename))
            Logger().warning(exception)
            raise

    def bar_graph(self, dataset):
        """
        Plot a pandas dataset into a bar graph

        @param dataset Pandas.Dataset

        The reference value for this method is simply 'bar' however `bar` is
        a blacklisted name in python.
        """
        return self._plot_standard('bar', dataset)

    def line(self, dataset):
        """
        Plot a line graph from a pandas dataset
        """
        return self._plot_standard('line', dataset)

    def histogram(self, dataset):
        """
        Plot a histogram from a pandas dataset
        """
        pass

    @profile
    def upset(self, dataset):
        """
        Plots an Up-Set graph showing correlations between 1 or more datasets.
        """
        filter_config = pyu.FilterConfig()
        filter_config.sort_by = pyu.SortMethods.SIZE

        if isinstance(dataset, pyu.DataExtractor):
            extractor = dataset
        else:
            extractor = pyu.DataExtractor(unique_keys=[self._content.group_by], filter_config=filter_config)
            extractor.names = dataset.name
            extractor.merge = dataset.dataframe

        if extractor.primary_set_length < 4:
            return self.venn(extractor)

        upset = pyu.UpSetPlot(extractor)
        results = upset.plot()

        for result in extractor.results:
            filename = '_'.join(result.in_sets) + '.csv'
            result.results.to_csv(
                os.path.join(
                    self._path,
                    filename
                ),
                index=False
            )
        return results.intersection_matrix

    def scatter(self, dataset):
        """
        Plot a scatter graph from a pandas dataset
        """
        plot = None
        colours = list(colors.cnames.keys())
        colour_index = 0
        for group in set(dataset.dataframe[self._content.group_by]):
            data = dataset.dataframe.query('{0} == \'{1}\''.format(self._content.group_by, group))
            if plot is None:
                plot = data.plot(
                    kind='scatter',
                    x=self._graph.xdata,
                    y=self._graph.ydata,
                    color=colours[colour_index],
                    label=group
                )
            else:
                data.plot(
                    kind='scatter',
                    x=self._graph.xdata,
                    y=self._graph.ydata,
                    color=colours[colour_index],
                    label=group,
                    ax=plot
                )
            colour_index += 1
        return plot

    def venn(self, dataset):
        """
        Plot a venn diagram from a data extractor object or dataframe merge table
        """
        filter_config = pyu.FilterConfig()
        filter_config.sort_by = pyu.SortMethods.SIZE

        if isinstance(dataset, pyu.DataExtractor):
            extractor = dataset
        else:
            extractor = pyu.DataExtractor(unique_keys=[self._content.group_by], filter_config=filter_config)
            extractor.names = dataset.name
            extractor.merge = dataset.dataframe

        if extractor.primary_set_length > 5:
            return self.venn(extractor)

        for result in extractor.results:
            filename = '_'.join(result.in_sets) + '.csv'
            result.results.to_csv(
                os.path.join(
                    self._path,
                    filename
                ),
                index=False
            )

        method = 'venn{index}'.format(index=extractor.primary_set_length)
        if not hasattr(venn, method):
            raise ValueError('Invalid number of items for venn. Use \'upset\' instead')

        data = extractor.as_logic()
        names = [data[key]['name'] for key in data if data[key]['name'] is not None]
        values = {}
        for key in data:
            values[key] = data[key]['count']
        return getattr(venn, method)(values, names)[0]

    def hexbin(self, dataset):
        """
        Plot a hexbin graph from a pandas dataset
        """
        return self._plot('hexbin', dataset)

    def _plot_standard(self, method, dataset):
        """
        Standard graphs (bar, line, etc.) use this wrapper to plot
        """
        plot = None
        plot = dataset.dataframe.plot(
            kind=method,
            x=self._graph.xdata,
            y=self._graph.ydata,
            colormap=cm.jet,
            rot=0,
            fontsize=10
        )
        return plot

    def _plot(self, method, dataset):
        """
        More complex graphs (scatter, hexbin, etc.) use this wrapper to plot
        """
        plot = dataset.dataframe.plot(
            kind=method,
            x=self._graph.xdata,
            y=self._graph.ydata,
            C=self._graph.aggragate if hasattr(self._graph, 'aggragate') else None,
            colormap=cm.jet
        )
        return plot
