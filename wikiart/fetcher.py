"""WikiArt Retriever.

Author: Lucas David -- <ld492@drexel.edu>
License: MIT License (c) 2016

"""
import json
import os
import shutil
import time
import urllib.error
import urllib.request

import requests

from . import settings, base
from .base import Logger


class WikiArtFetcher:
    """WikiArt Fetcher.

    Fetcher for data in WikiArt.org.
    """

    def __init__(self, commit=True, override=False,
                 padder=None):
        self.commit = commit
        self.override = override

        self.padder = padder or base.RequestPadder()

        self.artists = None
        self.painting_groups = None

    def prepare(self):
        """Prepare for data extraction."""
        instance = os.path.join(settings.BASE_FOLDER,
                                settings.INSTANCE_IDENTIFIER)
        if not os.path.exists(instance):
            os.mkdir(instance)

        meta = os.path.join(instance, 'meta')
        if not os.path.exists(meta):
            os.mkdir(meta)

        images = os.path.join(instance, 'images')
        if not os.path.exists(images):
            os.mkdir(images)

        return self

    def check(self, only='all'):
        """Check if fetched data is intact."""
        Logger.info('Checking downloaded data...')

        base_dir = os.path.join(settings.BASE_FOLDER,
                                settings.INSTANCE_IDENTIFIER)
        meta_dir = os.path.join(base_dir, 'meta')
        imgs_dir = os.path.join(base_dir, 'images')

        if only in ('artists', 'all'):
            # Check for artists file.
            if not os.path.exists(os.path.join(meta_dir, 'artists.json')):
                Logger.error('artists.json is missing.')

        if only in ('paintings', 'all'):
            for artist in self.artists:
                file = os.path.join(meta_dir, artist['url'] + '.json')
                if os.path.exists(file):
                    Logger.write('.', end='')
                else:
                    Logger.error('%s\'s paintings file is missing.'
                                 % artist['url'])

            # Check for paintings copies.
            for group in self.painting_groups:
                for painting in group:
                    file = os.path.join(imgs_dir,
                                        str(painting['contentId']) +
                                        settings.SAVE_IMAGES_IN_FORMAT)
                    if not os.path.exists(file):
                        Logger.error('painting %i is missing.'
                                     % painting['contentId'])

        return self

    def fetch_all(self):
        """Fetch Everything from WikiArt."""
        return self.fetch_artists().fetch_all_paintings().copy_everything()

    def fetch_artists(self):
        """Retrieve Artists from WikiArt."""
        Logger.info('Fetching artists...', end=' ', flush=True)

        path = os.path.join(settings.BASE_FOLDER, settings.INSTANCE_IDENTIFIER,
                            'meta', 'artists.json')
        if os.path.exists(path) and not self.override:
            with open(path, encoding='utf-8') as f:
                self.artists = json.load(f)

            Logger.info('Skipped.')
            return self

        elapsed = time.time()

        try:
            url = '/'.join((settings.BASE_URL, 'Artist/AlphabetJson'))
            response = requests.get(url,
                                    timeout=settings.METADATA_REQUEST_TIMEOUT)
            response.raise_for_status()
            self.artists = response.json()

            if self.commit:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.artists, f, indent=4, ensure_ascii=False)

            Logger.write('Done (%.2f sec)' % (time.time() - elapsed))

        except Exception as error:
            Logger.write('Error %s' % str(error))

        return self

    def fetch_all_paintings(self):
        """Fetch Paintings Metadata for Every Artist"""
        Logger.write('\nFetching paintings for every artist:')
        if not self.artists:
            raise RuntimeError('No artists defined. Cannot continue.')

        self.painting_groups = []
        show_progress_at = int(.1 * len(self.artists))

        # Retrieve paintings' metadata for every artist.
        for i, artist in enumerate(self.artists):
            self.painting_groups.append(self.fetch_paintings(artist))

            if i % show_progress_at == 0:
                Logger.info('|-%i%% completed\n|--------------'
                            % (100 * (i + 1) // len(self.artists)))

        return self

    def fetch_paintings(self, artist):
        """Retrieve and Save Paintings Info from WikiArt.

        :param artist: dict, artist who should have their paintings retrieved.
        """
        Logger.write('|-fetching %s\'s paintings'
                     % artist['artistName'], end='', flush=True)
        elapsed = time.time()

        meta_folder = os.path.join(settings.BASE_FOLDER,
                                   settings.INSTANCE_IDENTIFIER, 'meta')
        url = '/'.join((settings.BASE_URL, 'Painting', 'PaintingsByArtist'))
        params = {'artistUrl': artist['url'], 'json': 2}
        file = os.path.join(meta_folder, artist['url'] + '.json')

        if os.path.exists(file) and not self.override:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            Logger.write(' Skipped')
            return data

        try:
            response = requests.get(
                url, params=params,
                timeout=settings.METADATA_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            for painting in data:
                # We have some info about the images,
                # but we're also after their details.
                url = '/'.join((settings.BASE_URL, 'Painting', 'ImageJson',
                                str(painting['contentId'])))

                self.padder.request_start()
                response = requests.get(
                    url, timeout=settings.METADATA_REQUEST_TIMEOUT)
                self.padder.request_finished()

                if response.ok:
                    # Update paintings with its details.
                    painting.update(response.json())

                Logger.write('.', end='', flush=True)

            if self.commit:
                # Save the json file with images details.
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

            Logger.write(' Done (%.2f sec)' % (time.time() - elapsed))
            return data

        except (IOError, urllib.error.HTTPError) as e:
            Logger.write(' Failed (%s)' % str(e))
            return []

    def copy_everything(self):
        """Download A Copy of Every Single Painting."""
        Logger.write('\nCopying paintings:')
        if not self.painting_groups:
            raise RuntimeError('Painting groups not found. Cannot continue.')

        progress_interval = int(.1 * len(self.painting_groups))

        # Retrieve copies of every artist's painting.
        for i, group in enumerate(self.painting_groups):
            for painting in group:
                self.download_hard_copy(painting)

            if i % progress_interval == 0:
                Logger.info('%i%% completed\n|--------------'
                            % (100 * (i + 1) // len(self.painting_groups)))

        return self

    def download_hard_copy(self, painting):
        """Download A Copy of A Painting."""
        Logger.write('|-downloading "%s"...'
                     % painting['url'], end=' ', flush=True)
        elapsed = time.time()
        url = painting['image']
        # Remove label "!Large.jpg".
        url = ''.join(url.split('!')[:-1])
        file = os.path.join(settings.BASE_FOLDER, settings.INSTANCE_IDENTIFIER,
                            'images', str(painting['contentId']) +
                            settings.SAVE_IMAGES_IN_FORMAT)

        if os.path.exists(file) and not self.override:
            Logger.write('Skipped')
            return self

        try:
            # Save image.
            self.padder.request_start()
            response = requests.get(url, stream=True,
                                    timeout=settings.PAINTINGS_REQUEST_TIMEOUT)
            self.padder.request_finished()

            response.raise_for_status()

            with open(file, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)

            Logger.write('Done (%.2f sec)' % (time.time() - elapsed))

        except Exception as error:
            Logger.write('%s' % str(error))
            if os.path.exists(file): os.remove(file)

        return self
