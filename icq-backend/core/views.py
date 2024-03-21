import logging

from core.forms import ScrapeRequestForm
from core.functions import CubeDistance, CubeEnlargeFunc
from core.scraper import Scraper
from core.types import Cube
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.template import loader

from .colors import hex2lab, rgb2hex
from .models import ScrapeJob, Site, SiteColor

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'core/index.html', {
        "colors": [],
        "form": ScrapeRequestForm(),
    })


def colors(request):
    return scrape(request)

def latest(request):
    latest_job = ScrapeJob.objects.order_by('-created_at')[0]
    return render(request, 'core/job.html', {'job': latest_job})


def job(request, job_id):
    return _job(request, get_object_or_404(ScrapeJob, pk=job_id))


def _job(request, j: ScrapeJob):
    return render(request, 'core/job.html', {'job': j})


def site(request, site_id: None):
    if site_id is not None:
        params = {'pk': site_id}
    elif site_url := request.GET.get('site_url', None):
        params = {'site_url': site_url}
    else:
        return HttpResponseBadRequest()
    obj = get_object_or_404(Site, **params)
    return render(request, 'core/site.html', {
        'site': obj,
        'form': ScrapeRequestForm({'site_url': obj.url}),
    })


def scrape(request):
    # TODO: Trim whitespace on both frontend and backend
    site_url: str = request.GET.get('site_url', None)
    if site_url is None:
        return HttpResponseBadRequest()
    scraper = Scraper(site_url)

    # TODO Make it return a job?
    results = scraper.run()
    colors = []
    for r in results:
        colors.append(r.rgb())
    template = loader.get_template("core/index.html")
    context = {
        "site_url": site_url,
        "colors": [rgb2hex(r, g, b) for r, g, b in colors]
    }
    return HttpResponse(template.render(context, request))

def similar(request, hexcolor):
    distance = float(request.GET.get('distance', 20))
    if hexcolor is None:
        return HttpResponseBadRequest()
    lab = hex2lab(hexcolor)
    results = SiteColor.objects. \
        filter(color_lab__contained_by=CubeEnlargeFunc(Cube(lab), distance, 0)). \
        annotate(distance=CubeDistance('color_lab', Cube(lab))). \
        order_by('distance'). \
        all()[0:20]
    template = loader.get_template("core/similar.html")
    context = {
        "color": hexcolor,
        "colors": results,
    }
    return HttpResponse(template.render(context, request))
