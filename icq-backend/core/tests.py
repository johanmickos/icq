# from unittest.mock import patch

# from core.colors import LAB
# from core.models import Site, SiteCategory
# from django.test import TestCase

# TEST_COLORS = [LAB(0.0, 0.0, 0.0)]


# class ScrapeJobTest(TestCase):
#     def setUp(self):
#         category = SiteCategory.objects.create(
#             name="General",
#             description="General catch-all category"
#         )
#         site = Site.objects.create(
#             base_url='https://example.com/',
#             name="Example Site",
#         )
#         site.categories.add(category)

#     @patch("core.scraper.SiteColorExtractor.dominant_colors", autospec=True, return_value=TEST_COLORS)
#     def test_onetime_scrape(self, mock_dominant_colors):
#         """One-time scrape jobs generate relevant data"""
#         print(mock_dominant_colors.first)
