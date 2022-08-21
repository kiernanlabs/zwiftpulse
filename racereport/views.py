import django_tables2 as tables
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import (
    ListView,
)

from .models import Race, RaceCat, RaceResult

def index(request):
    return HttpResponse("Hello, world. You're at the index.")

class RaceCatView(ListView):
    model = RaceCat
    race_cats = RaceCat.objects.all().order_by("category", "-race")

class RaceCatTop5View(RaceCatView):
    template_name = "racereport/top5races.html"
    
    def get_queryset(self):
        return RaceCat.objects.filter(box=self.kwargs["box_num"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["box_number"] = self.kwargs["box_num"]
        return context