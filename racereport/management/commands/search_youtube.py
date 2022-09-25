# -*- coding: utf-8 -*-

# Sample Python code for youtube.search.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os
import logging


import googleapiclient.discovery
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from racereport.models import Video, Race, RaceCat, RaceResult, Team, ScrapeReport

logger = logging.getLogger('main')

class Command(BaseCommand):
    help = 'pulls youtube search results for given zwiftpower event URL'

    def add_arguments(self, parser):
        parser.add_argument('--event_id', nargs='?', type=int, default=3137962, help='zwiftpower event ID to search youtube for')
        parser.add_argument('--type', nargs='?', type=int, default=0, help='0 - specified URL, 1 = 7 day competitive races, 2 = 7 day largest races, 3 = 24hr all races')

    def handle(self, *args, **options):
        logger.info(f"Kicking off youtube search...")
        
        
        if options['type'] == 1: racecats = RaceCat.objects.most_competitive_races_last_7_days()
        if options['type'] == 2: racecats = RaceCat.objects.largest_races_last_7_days()
        if options['type'] == 3: racecats = RaceCat.objects.racecats_last24hrs()
        if options['type'] == 4: racecats = RaceCat.objects.most_competitive_races_last_24hrs()
        if options['type'] == 5: racecats = RaceCat.objects.largest_races_last_24hrs()

        if options['type'] == 0:
            races = Race.objects.filter(event_id=options['event_id'])
        elif options['type'] == 6:
            races = Race.objects.get_top_X_races_last_Y_days(40, 1)
        else: races = Race.objects.filter(racecat__in=racecats).distinct()

        logger.info(f"--Searching {len(races)} races")
        
        for race in races:
            url = f"https://zwiftpower.com/events.php?zid={race.event_id}"
            response = self.get_google_response(url)
            if response['pageInfo']['totalResults'] > 0:
                for item in response['items']:
                    self.save_video(item, url)
            
    
    def save_video(self, item, zp_url):
        try:
            stream_url = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            logger.debug(f"--attempting to create video: {stream_url}")
            streamer = item['snippet']['channelTitle']
            commentary = False
            description = item['snippet']['description']
            title = item['snippet']['title']
            thumbnail = item['snippet']['thumbnails']['default']['url']
            status = "auto_created"
            Video.objects.create_video(zp_url, stream_url, streamer, commentary, description, title, thumbnail, status)
        except Exception as e:
            logger.debug(f"--error creating video: {item} -- {e}")
            pass

    def get_google_response(self, query):
        logger.debug(f"--Querying google for: {query}")

        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0"

        api_service_name = "youtube"
        api_version = "v3"
        DEVELOPER_KEY = settings.GOOGLE_API_KEY

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey = DEVELOPER_KEY)

        request = youtube.search().list(
            part="snippet",
            q=query
        )
        response = request.execute()
        logger.debug(f"--{response['pageInfo']['totalResults']} results found")
        logger.debug(response)

        return response
