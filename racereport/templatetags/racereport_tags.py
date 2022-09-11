from django import template

register = template.Library()

@register.inclusion_tag('racereport/race_table.html')
def display_racecats(racecats):
    return {'racecats': racecats}

'''
@register.filter
def team_name_link(team_name, cat):
    return '<a href=/team/{team_name}/{cat}>{team_name}</a>'
'''