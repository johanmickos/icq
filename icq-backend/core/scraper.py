"""
Main website scraping logic.
"""
import time
import urllib.parse
import urllib.request
from io import BytesIO
from typing import List, Optional
from urllib.parse import urlparse

import cairosvg
import numpy as np
import requests
import selenium.common.exceptions
from core.colors import RGB, distance_rgb, rgb2lab
from core.hash import md5
from core.models import (ColorDataResult, ColorDataResultType, DataSource,
                         ScrapeJob, Site, SiteColor, SitePageType)
from django.conf import settings
from django.db import transaction
from PIL import Image
from selenium import webdriver
from selenium.webdriver import Remote as WebDriver
from selenium.webdriver.common.by import By
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.metrics import silhouette_score
from webdriver_manager.chrome import ChromeDriverManager


class Scraper():
    """
    Website scraper which extracts dominant colors from a website and
    persists the results in the database.
    """

    def __init__(self, url: str, page_type_name='General', window_size=(1200, 800), load_sleep_secs:float=5.0):
        # XXX TODO: Be even more stringent with URL parsing (don't allow IP addresses, no local paths, etc.)
        if not url.startswith('https://') and not url.startswith('http://'):
            url = f'https://{url}'
        url = url.rstrip('/')
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        parts = domain.split('.')
        name = domain
        if len(parts) >= 2:
            name = parts[-2]
        self.load_sleep_secs = load_sleep_secs
        self.base_url = parsed_url.scheme + '://' + parsed_url.netloc
        self.window_size = window_size
        self.page_type, _ = SitePageType.objects.get_or_create(name=page_type_name)
        self.site, _ = Site.objects.update_or_create(
            url=url,
            defaults={
                'domain':domain,
                'name':name,
                'page_type':self.page_type,
            },
        )
        self.job = ScrapeJob.objects.create(site=self.site)

    def run(self):
        """
        Runs the website scraper against the configured site.
        """

        options = webdriver.ChromeOptions()
        options.add_argument(
            f'--window-size={self.window_size[0]},{self.window_size[1]}')
        options.add_argument('--headless')
        options.add_argument('--hide-scrollbars')
        with webdriver.Chrome(
            ChromeDriverManager().install(),
            options=options,
        ) as driver:
            # TODO: Fail if Captcha / Cloudflare verification
            # TODO Document HTTP status code
            driver.get(self.site.url)
            time.sleep(self.load_sleep_secs) # Let site's JS load
            if self.site.url.startswith('https://web.archive.org'):
                # Hide the Wayback Machine top bar (we don't want it in our screenshot)
                javascript = '''\
                    document.getElementById('wm-ipp-base').style.display='none';
                '''
                driver.execute_script(javascript)

            screenshot = driver.get_screenshot_as_png()
            screenshot_md5 = md5(screenshot)

            # TODO: Merge with favicon handling
            screenshot = Image.open(BytesIO(screenshot))
            if settings.DEBUG:
                screenshot.save('./latest.png')

            width, height = screenshot.size
            npixels = width*height
            thresh = int(npixels * 0.00004)

            visual_palette = _compute_colors(screenshot, thresh_pixel_count=thresh)

            favicon_image = favicon(driver, self.base_url)
            if favicon_image is not None:
                favicon_md5 = md5(favicon_image.tobytes())
                if settings.DEBUG:
                    favicon_image.save('./favicon.ico')
                favicon_palette = _compute_colors(favicon_image)
            # END MERGE

            results = []
            with transaction.atomic():
                # TODO: Sync. with S3 or similar
                # TODO: Clean up maybe-ness of favicon data
                if favicon_image is not None:
                    favicon_src, _ = DataSource.objects.get_or_create(
                        object_checksum=favicon_md5,
                        defaults={
                            # XXX: What if we somehow have an identical checksum but diff. site page?
                            'site': self.site,
                            'object_type': DataSource.DataSourceType.FAVICON,
                            'object_url': 's3://TODO:',
                        },
                    )
                    for rgb in favicon_palette:
                        lab = tuple(rgb2lab(rgb))
                        SiteColor.objects.update_or_create(
                            site=self.site,
                            color_lab=lab,
                        )
                        obj = ColorDataResult.objects.create(
                            site=self.site,
                            job=self.job,
                            color_lab=lab,
                            # TODO: WaybackMachine timestamp
                            result_type=ColorDataResultType.types.visual_favicon(),
                            source=favicon_src
                        )
                        results.append(obj)
                data_source, _ = DataSource.objects.get_or_create(
                    object_checksum=screenshot_md5,
                    defaults={
                        # XXX: What if we somehow have an identical checksum but diff. site page?
                        'site': self.site,
                        'object_type': DataSource.DataSourceType.SCREENSHOT,
                        'object_url': 's3://TODO:',
                    },
                )
                # TODO Refactor to share across favicon/screenshot
                for rgb in visual_palette:
                    lab = tuple(rgb2lab(rgb))
                    SiteColor.objects.update_or_create(
                        site=self.site,
                        color_lab=lab,
                    )
                    obj = ColorDataResult.objects.create(
                        site=self.site,
                        job=self.job,
                        color_lab=lab,
                        # TODO: WaybackMachine timestamp
                        result_type=ColorDataResultType.types.visual_screenshot(),
                        source=data_source,
                    )
                    results.append(obj)
            return results

def _compute_colors(image: Image.Image, thresh_pixel_count: int=15, thresh_distance: int=35)->List[RGB]:
    # XXX TODO: This is not deterministic! See 'nondeterministic.png'
    reduced = image.convert("RGBA").quantize(256)
    palette = reduced.getpalette(rawmode='RGBA')
    palette = [palette[4*n:4*n+4] for n in range(256)]
    color_count = [[n, np.array(palette[m][:3])] for n, m in reduced.getcolors() if palette[m][3] != 0]
    color_count = sorted(color_count, reverse=True, key=(lambda x: x[0]))

    color_count = filter(lambda x: x[0] > thresh_pixel_count, color_count)
    dominant = []
    for candidate in color_count:
        # (non-optimal) "Swallow" colors that are too similar to
        # already-selected dominant colors
        check = []
        for selected in dominant:
            dist = distance_rgb(candidate[1], selected[1])
            if dist < thresh_distance:
                # 'selected' subsumes 'candidate'
                selected[0] += candidate[0]
            check.append(dist < thresh_distance)
        if any(check):
            continue
        dominant.append(candidate)
        if len(dominant) == 10:
            break
    return [x[1] for x in dominant]

def _compute_kmeans(data, k=5):
    kmeans = KMeans(
        n_clusters=k,
        n_init='auto',
    )
    kmeans.fit(np.array(data))
    color_palette = kmeans.cluster_centers_
    return color_palette.astype(int)


def _compute_kmeans_predef(data):
    starting_centroids = np.array([
        [0, 0, 0, 1],  # black
        [1, 1, 1, 1],  # white
        [1, 0, 0, 1],  # red
        [0, 1, 0, 1],  # green
        [0, 0, 1, 1],  # blue
        [1, 1, 0, 1],  # yellow
    ])*255
    if data.shape[1] == 3:
        starting_centroids = starting_centroids[:, :3]
    kmeans = MiniBatchKMeans(
        n_clusters=starting_centroids.shape[0],
        n_init='auto',
        init=starting_centroids,
    )
    kmeans.fit(np.array(data))
    color_palette = kmeans.cluster_centers_
    return color_palette.astype(int)


def _compute_kmeans_sil(data, kmax=10):
    if kmax > 10:
        raise Exception("kmax larger than 10")
    sil = []
    palettes = []
    for k in range(2, kmax+1):
        kmeans = MiniBatchKMeans(
            n_init='auto',
            n_clusters=k,
        ).fit(data)
        cluster = kmeans.predict(data)
        score = silhouette_score(data, cluster)
        sil.append(score)
        palettes.append(kmeans.cluster_centers_.astype(int))
    return palettes[sil.index(max(sil))]


def _compute_meanshift(data):
    from sklearn.cluster import MeanShift, estimate_bandwidth

    # using MeanShift to get an estimate
    bandwidth = estimate_bandwidth(data,
                                quantile=0.3,
                                n_jobs=-1)
    ms = MeanShift(bandwidth=bandwidth,
                bin_seeding=False,
                n_jobs=-1,
                max_iter=500)
    ms.fit(data)
    return ms.cluster_centers_

def favicon(driver: WebDriver, base_url: str) -> Optional[Image.Image]:
    """Attempts to extract a website's favicon."""

    xpath_link_rels = [
        'icon',
        'ICON',
        'shortcut icon',
        'SHORTCUT ICON'
    ]
    xpath_link_str = ' or '.join([f'@rel="{x}"' for x in xpath_link_rels])
    xpath = f'//link[{xpath_link_str}]'
    try:
        element = driver.find_element(
            by=By.XPATH, value=xpath)
        favicon_url = element.get_attribute('href')
    except selenium.common.exceptions.NoSuchElementException:
        favicon_url = urllib.parse.urljoin(base_url, 'favicon.ico')
    try:
        headers ={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        }
        response = requests.get(favicon_url, timeout=(2,2),headers=headers)
        if response.headers['Content-Type'] == 'image/svg+xml':
            # PIL does not support SVGs, so we convert them first
            out = BytesIO()
            cairosvg.svg2png(response.content, write_to=out)
            return Image.open(out).resize((32, 32))
        return Image.open(BytesIO(response.content)).resize((32, 32))
    except Exception as ex:
        return None
