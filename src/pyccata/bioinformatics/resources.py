"""
Resources specific to BioInformatics pipelines
"""
from pyccata.core.resources import ResultListItemAbstract

class BedFileItem(ResultListItemAbstract):
    """
    Basic structure for storing annotated sequence data from Bed files
    """
    # pylint: disable=too-many-instance-attributes
    # This object contains the relevant fields of a Jira ticket item
    # Therefore a large number of attributes are required.

    # pylint: disable=too-few-public-methods
    # As a struct, no public methods are required.
    # Instead, all attributes are public

    DELIMITER = '\t'

    _series_frame = None
    def __init__(self):
        """
        File structure for BED file lines.

        A BED file is a Browser Extensible Data format used in
        BioInformatics for defining the data lines that are
        displayed in an annotation track
        """
        self.read_count = None
        self.peak_id = None
        self.chromasone = None
        self.start = None
        self.end = None
        self.strand = None
        self.peak_score = None
        self.focus_ratio = None
        self.annotation = None
        self.detailed_annotation = None
        self.distance_to_tss = None
        self.nearest_promoter_id = None
        self.entrez_id = None
        self.nearest_unigene = None
        self.nearest_refseq = None
        self.nearest_ensembl = None
        self.gene_name = None
        self.gene_alias = None
        self.gene_description = None
        self.gene_type = None

    def keys(self):
        """
        Gets the list of fields allowed in this file type

        This list is provided in the same order as the fields in the BED file CSV and is
        used for mapping the CSV to the object.
        """
        # pylint: disable=no-self-use
        # Yes this should be a method and not a function
        return [
            'read_count', 'peak_id', 'chromasone', 'start', 'end', 'strand',
            'peak_score', 'focus_ratio', 'annotation', 'detailed_annotation', 'distance_to_tss',
            'nearest_promoter_id', 'entrez_id', 'nearest_unigene', 'nearest_refsec', 'nearest_ensemble',
            'gene_name', 'gene_alias', 'gene_description', 'gene_type'
        ]

class BayesFileItem(ResultListItemAbstract):
    """
    Class for a type of item discovered after carrying out a Bayes transform

    Filename for this type must end with .bayes
    """
    # pylint: disable=too-many-instance-attributes
    DELIMITER = '\t'

    _series_frame = None
    def __init__(self):
        """
        File structure for BED file lines.

        A BED file is a Browser Extensible Data format used in
        BioInformatics for defining the data lines that are
        displayed in an annotation track
        """
        self.peak_id = None
        self.chromasone = None
        self.start = None
        self.end = None
        self.width = None
        self.peak_score = None
        self.annotation = None
        self.distance_to_tss = None
        self.gene_name = None
        self.link = None

    def keys(self):
        """
        Gets the list of fields allowed in this file type

        This list is provided in the same order as the fields in the BED file CSV and is
        used for mapping the CSV to the object.
        """
        # pylint: disable=no-self-use
        # Yes this should be a method and not a function
        return [
            'peak_id', 'chromasone', 'start', 'end', 'width',
            'peak_score', 'annotation', 'distance_to_tss',
            'gene_name', 'link'
        ]

class GeneFileItem(ResultListItemAbstract):
    """
    Class for files generated from R. Must have a .gene extension
    """
    # pylint: disable=too-many-instance-attributes
    DELIMITER = '\t'

    _series_frame = None
    def __init__(self):
        """
        File structure for BED file lines.

        A BED file is a Browser Extensible Data format used in
        BioInformatics for defining the data lines that are
        displayed in an annotation track
        """
        self.peak_id = None
        self.chromasone = None
        self.start = None
        self.end = None
        self.annotation = None
        self.distance_to_tss = None
        self.gene_name = None
        self.read_count = None
        self.input_count = None
        self.link = None

    def keys(self):
        """
        Gets the list of fields allowed in this file type

        This list is provided in the same order as the fields in the BED file CSV and is
        used for mapping the CSV to the object.
        """
        # pylint: disable=no-self-use
        # Yes this should be a method and not a function
        return [
            'peak_id', 'chromasone', 'start', 'end',
            'annotation', 'distance_to_tss', 'gene_name',
            'read_count', 'input_count', 'link'
        ]
