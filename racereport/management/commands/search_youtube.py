# -*- coding: utf-8 -*-

# Sample Python code for youtube.search.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os
import logging
import re

from datetime import datetime, timedelta
from django.utils import timezone

import googleapiclient.discovery
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from racereport.models import Video, Race, RaceCat, RaceResult, Team, ScrapeReport, Streamer

logger = logging.getLogger('main')

class Command(BaseCommand):
    help = 'pulls youtube search results that include zwiftpower links'

    def add_arguments(self, parser):
        parser.add_argument('--event_id', nargs='?', type=int, default=3137962, help='zwiftpower event ID to search youtube for')
        parser.add_argument('--hours', nargs='?', type=int, default=24, help='pull videos published in last X hours')

    def handle(self, *args, **options):
        
        twenty_four_hours_ago = timezone.now() - timedelta(hours = options['hours'])
        start_time = twenty_four_hours_ago
        items = self.get_videos_to_process(start_time.isoformat())
        detailed_items = []

        for item in items:
            detailed_response =  self.get_google_video_response(item['id']['videoId'])
            # logger.debug(detailed_response)
            detailed_items.append(detailed_response['items'][0])
        
        for item in detailed_items:
            x = re.search('zid=',item['snippet']['description'])
            if x == None:
                logger.info(f"-- Error finding zpurl in {item['description']}")
                break

            zp_url = item['snippet']['description'][x.span()[0]-26:x.span()[0]+11]
            self.save_video(item, zp_url)

        ''' OLD RACE-BASED SEARCHING
        
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
        '''

    '''=== Helper processing methods ==='''

    def get_videos_to_process(self, start_time):
        # returns youtube API list of videos published after start_time with zwiftpower link
        # requires paging through results, should be ~20 videos, 5 per page
        logger.info(f"-- searching youtube for zwiftpower links in since {start_time}")
        initial_response = self.get_google_search_response("zwiftpower.com/events.php?zid=", start_time)
        total_videos = initial_response['pageInfo']['totalResults']
        items = initial_response['items']
        
        # add next pages to results
        prev_page = initial_response
        while(len(items) < total_videos):
            if 'nextPageToken' in prev_page:
                next_page = self.get_google_search_response("zwiftpower.com/events.php?zid=", start_time, prev_page['nextPageToken'])
                items += next_page['items']
                prev_page = next_page
            else:
                logger.info(f"--- Error, no more pages, but have only found {len(items)} out of {total_videos} total")
                logger.info(prev_page)
                break
        
        logger.info(f"-- {len(items)} total videos found")
        return items

    # I think this needs to be a detailed item[] response from the video.list function
    def save_video(self, item, zp_url):
        try:
            stream_url = f"https://www.youtube.com/watch?v={item['id']}"
            logger.debug(f"--attempting to create video: {stream_url}")
            streamer_name = item['snippet']['channelTitle']

            streamer = Streamer.objects.get_or_create(streamer_name=streamer_name,
                defaults={'youtube_channel_id':item['snippet']['channelId']}
            )[0]

            commentary = False
            description = item['snippet']['description']
            title = item['snippet']['title']
            thumbnail = item['snippet']['thumbnails']['default']['url']
            status = "auto_created"
            Video.objects.create_video(zp_url, stream_url, streamer, commentary, description, title, thumbnail, status)
        except Exception as e:
            logger.debug(f"--error creating video: {item} -- {e}")
            pass

    '''=== Google API methods ==='''

    def get_google_search_response(self, query, published_after, page_token=''):
        # logger.debug(f"--Querying google for: {query}")

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
            q=query,
            publishedAfter=published_after,
            pageToken = page_token
        )

        response = request.execute()
        logger.debug(f"--{response['pageInfo']['totalResults']} results found")
        logger.debug(response)

        return response
    
    def get_google_video_response(self, video_id):
        logger.debug(f"--Querying google for: {video_id}")

        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0"

        api_service_name = "youtube"
        api_version = "v3"
        DEVELOPER_KEY = settings.GOOGLE_API_KEY

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey = DEVELOPER_KEY)

        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()
        # logger.debug(f"--{response['pageInfo']['totalResults']} results found")
        # logger.debug(response)

        return response
