from django import template
from racereport.models import Race, RaceCat, RaceResult, Team, ScrapeReport


register = template.Library()

@register.inclusion_tag('racereport/race_table.html')
def display_racecats(racecats):
    return {'racecats': racecats}

@register.inclusion_tag('racereport/scrape_report.html')
def display_scrape_report():
    most_recent_scrape = ScrapeReport.objects.latest('scrape_start')
    return {'recent_scrape': most_recent_scrape}

'''
@register.filter
def team_name_link(team_name, cat):
    return '<a href=/team/{team_name}/{cat}>{team_name}</a>'
'''