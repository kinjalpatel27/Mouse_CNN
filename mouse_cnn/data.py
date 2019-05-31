import csv
import numpy as np
from scipy.optimize import curve_fit

"""
Interface to mouse data sources. 
"""

data_folder = 'data_files'


class Data:
    def __init__(self):
        self.e18 = Ero2018()
        self.p11 = Perin11()

    def get_areas(self):
        """
        :return: list of names of visual areas included in the model
        """
        return ['LGNd', 'VISp', 'VISl', 'VISrl', 'VISli', 'VISpl', 'VISal', 'VISpor']

    def get_layers(self):
        """
        :return: list of cortical layers included in model
        """
        return ['2/3', '4', '5']

    def get_hierarchical_level(self, area):
        """
        :param area: Name of visual area
        :return: Hierarchical level number, from 0 (LGN) to 3 (VISpor) from Stefan's
            analysis
        """
        hierarchy = {
            'LGNd': 0,
            'VISp': 1,
            'VISl': 2, 'VISrl': 2, 'VISli': 2, 'VISpl': 2, 'VISal': 2,
            'VISpor': 3
        }
        return hierarchy[area]

    def get_num_neurons(self, area, layer):
        """
        :param area: visual area name (e.g. 'VISp')
        :param layer: layer name (e.g. '2/3')
        :return: estimate of number of excitatory neurons in given area/layer
        """
        #TODO: compare with other estimates
        self.e18.get_n_excitatory(area, layer)

    def get_extrinsic_in_degree(self, area, layer):
        """
        :param area: visual area name (e.g. 'VISp')
        :param layer: layer name (e.g. '2/3')
        :return: estimate of mean number of neurons from OTHER AREAS that synapse onto a
            single excitatory neuron in given area / layer
        """
        #TODO: replace with real estimate
        return 1000

    def get_hit_rate_peak(self, source_layer, target_layer):
        """
        :param source_layer: name of presynaptic layer
        :param target_layer: name of postsynaptic layer
        :return: fraction of excitatory neuron pairs with functional connection in this
            direction, at zero horizontal offset
        """
        #TODO: replace with real estimate
        return .1

    def get_hit_rate_width(self, source_layer, target_layer):
        """
        :param source_layer: name of presynaptic layer
        :param target_layer: name of postsynaptic layer
        :return: width of Gaussian approximation of fraction of excitatory neuron pairs with
            functional connection in this direction
        """
        return self.p11.width_micrometers


class Ero2018:
    """
    Data from supplementary material of [1]. We load names of regions and numbers of
    excitatory neurons.
    """

    def __init__(self):
        self.regions = []
        self.excitatory = []
        with open(data_folder + '/Data_Sheet_1_A Cell Atlas for the Mouse Brain.CSV') as csvfile:
            r = csv.reader(csvfile)
            header_line = True
            for row in r:
                if header_line:
                    header_line = False
                else:
                    self.regions.append(row[0])
                    self.excitatory.append(row[4])

    def get_n_excitatory(self, area, layer=None):
        area_map = {
            'LGNd': 'Dorsal part of the lateral geniculate complex',
            'LGNv': 'Ventral part of the lateral geniculate complex',
            'VISal': 'Anterolateral visual area',
            'VISam': 'Anteromedial visual area',
            'VISl': 'Lateral visual area',
            'VISp': 'Primary visual area',
            'VISpl': 'Posterolateral visual area',
            'VISpm': 'posteromedial visual area'
        }

        if layer is None:
            index = self.regions.index(area_map[area])
            result = np.int(self.excitatory[index])
        elif layer == '6':
            index_a = self.regions.index('{} layer 6a'.format(area_map[area]))
            index_b = self.regions.index('{} layer 6a'.format(area_map[area]))
            result = np.int(self.excitatory[index_a]) + np.int(self.excitatory[index_b])
        else:
            index = self.regions.index('{} layer {}'.format(area_map[area], layer))
            result = np.int(self.excitatory[index])

        return result


class Perin11:
    """
    This class fits a Gaussian function to the connection probability vs. inter-somatic
    distance among pairs of thick-tufted L5 pyramids in P14-16 Wistar rats, from Fig. 1 of [1].

    In the source figure, I would expect "overall" to be the sum of reciprical
    and non-reciprocal, but it isn't. It doesn't look like this much affects the spatial
    profile though, just the peak (which we don't use).

    [1] R. Perin, T. K. Berger, and H. Markram, “A synaptic organizing principle for cortical neuronal
    groups.,” Proc. Natl. Acad. Sci. U. S. A., vol. 108, no. 13, pp. 5419–24, Mar. 2011.
    """

    def __init__(self):
        connection_probability_vs_distance = [
                [17.441860465116307, 0.21723833429098494],
                [52.79069767441864, 0.1676015362748359],
                [87.44186046511628, 0.14761544742492516],
                [122.5581395348837, 0.12294674448846282],
                [157.67441860465118, 0.09515710527111632],
                [192.55813953488376, 0.10208848701121961],
                [227.44186046511635, 0.06337617564339071],
                [262.5581395348837, 0.03480630235582299],
                [297.44186046511635, 0.07021622765899538]]

        def gaussian(x, peak, sigma):
            return peak * np.exp(-x ** 2 / 2 / sigma ** 2)

        cp = np.array(connection_probability_vs_distance)
        popt, pcov = curve_fit(gaussian, cp[:,0], cp[:,1], p0=(.2, 150))
        self.width_micrometers = popt[1]