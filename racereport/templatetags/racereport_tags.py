from django import template
from racereport.models import Race, RaceCat, RaceResult, Team, ScrapeReport


register = template.Library()

@register.inclusion_tag('racereport/race_table.html')
def display_racecats(racecats):
    return {'racecats': racecats}

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

@register.filter(name='category_title')
def active_nav(category):
    if category == None: return "All Races"
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




