from django import template
from django.conf import settings

from racereport.models import Race, RaceCat, RaceResult, Team, ScrapeReport


register = template.Library()

@register.inclusion_tag('racereport/race_table.html')
def display_racecats(racecats):
    return {'racecats': racecats}

@register.inclusion_tag('racereport/race_single_detail.html')
def display_racecat_single_detail(racecat):
    return {'race_cat': racecat}

@register.inclusion_tag('racereport/video_detail.html')
def display_video(video):
    return {'video': video}

@register.inclusion_tag('racereport/video_detail_with_race.html')
def display_video_with_race(video, race):
    return {'video': video, 'race': race}

@register.inclusion_tag('racereport/narrative_card.html')
def display_narrative(narrative):
    results = narrative.why.all()
    return {'narrative': narrative, 'results': results}

@register.inclusion_tag('racereport/scrape_report.html')
def display_scrape_report():
    most_recent_scrape = ScrapeReport.objects.latest('scrape_start')
    return {'recent_scrape': most_recent_scrape}

@register.filter(name='active_nav')
def active_nav(value, category):
    if value == category: return "is-active"
    return ''

#return full url to swap between live/static in production only
@register.filter(name='production_url')
def production_url(subdomain):
    if settings.PRODUCTION == 'TRUE': return f"http://{subdomain}.zwiftpulse.com"
    return ''

@register.filter(name='active_nav2')
def active_nav(value, report):
    if value == report: return "is-active"
    return ''

@register.filter(name='report_timeframe')
def report_url(report, timeframe):
    if report == 'races' : return f'{report}/{timeframe}'
    return report

@register.filter(name='timeframe_title')
def report_url(timeframe):
    if timeframe == 'week' : return "last 7 days"
    if timeframe == 'day' : return "last 24hrs"
    return ""

@register.filter(name='category_title')
def active_nav(category):
    if category == None: return "All Categories"
    else:
        return f"{category} Cat Races"

@register.filter(name='category_color')
def category_color(category):
    if category == None: return "is-light"
    if category == 'A': return "is-danger"
    if category == 'B': return "is-success"
    if category == 'C': return "is-info"
    if category == 'D': return "is-warning"
    if category == 'E': return "is-light"
    return "is-light"




