"""WikiArt Retriever Base Settings.

Author: Lucas David -- <ld492@drexel.edu>
License: MIT License (c) 2016

"""

# Base Settings
# Identifies the retrieving instance currently executing.
INSTANCE_IDENTIFIER = '1'

# WikiArt base url.
BASE_URL = 'http://www.wikiart.org/en/App'

# Base folder in which the files will be saved.
BASE_FOLDER = '/media/ldavid/hdd/data/wikiart'

# Format in which the images will be saved.
SAVE_IMAGES_IN_FORMAT = '.jpg'

# Request Settings

# WikiArt supposedly blocks users that make more than 10 requests within 5
# seconds. The following parameters are used to control the frequency of
# these same requests.
# Number of requests made before checking if the process should slow down.
REQUEST_STRIDE = 10
# Minimum delta time between two consecutive request strides.
REQUEST_PADDING_IN_SECS = 5

# Maximum time (in secs) before canceling a download.
METADATA_REQUEST_TIMEOUT = 2 * 60
PAINTINGS_REQUEST_TIMEOUT = 5 * 60

# Data Set Conversion Settings

# Set which attributes are considered when converting the paintings json files
# to a more common data set format.
PAINTING_ATTRIBUTES = (
    'contentId', 'image', 'url', 'title', 'description', 'serie', 'style',
    'period', 'genre', 'technique', 'material', 'height', 'width', 'sizeX',
    'sizeY', 'diameter', 'auction', 'location', 'artistContentId',
    'artistUrl', 'artistName', 'completitionYear', 'yearAsString',
    'yearOfTrade', 'galleryName', 'lastPrice')

PAINTINGS_HEADER = """
=======================
WikiArt Data Set Images
=======================

This data set was created from paintings extracted from WikiArt.org.

Please refer to https://github.com/lucasdavid/wikiart for more information
or to report a bug.

Attributes are:
%s

""" % ', '.join(())

# Set which attributes are considered when converting the artists' attributes
# to a more common data set format.
ARTIST_ATTRIBUTES = (
    'contentId', 'url', 'artistName', 'lastNameFirst', 'image', 'wikipediaUrl',
    'birthDay', 'deathDay', 'birthDayAsString', 'deathDayAsString',
)

# Header of generated file labels.data.
LABELS_HEADER = """
=======================
WikiArt Data Set Labels
=======================

This data set was created from paintings extracted from WikiArt.org.

Please refer to https://github.com/lucasdavid/wikiart for more information
or to report a bug.

Attributes are:
%s

""" % ', '.join(ARTIST_ATTRIBUTES)
