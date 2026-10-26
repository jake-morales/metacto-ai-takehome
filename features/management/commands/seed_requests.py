"""
Management command to seed the database with realistic feature requests
across predefined themes for clustering demos.

Usage:
    python manage.py seed_requests          # seed all themes
    python manage.py seed_requests --clear  # delete existing requests first
"""
from django.core.management.base import BaseCommand
from features.models import FeatureRequest
from features.tasks import process_feature_request


# Each theme: (segment, title, description)
SEED_DATA = [
    # ── Theme 1: Make it cheaper (User) ──────────────────────────────
    ("user", "Lower delivery fees please",
     "The delivery fees are way too high, especially for short-distance orders. I end up paying almost as much in fees as the food itself."),
    ("user", "Too expensive compared to competitors",
     "DoorDash and UberEats have better deals. BiteFlight charges more for the same restaurants. I'm thinking about switching."),
    ("user", "Add a free delivery option",
     "I'd love a free delivery tier, even if it means a minimum order amount. Paying $7 delivery on a $12 meal doesn't make sense."),
    ("user", "Reduce service fees",
     "The service fee keeps going up. It used to be $2, now it's $4+. Can you bring it back down?"),
    ("user", "Introduce a subscription for free delivery",
     "Something like DashPass where I pay a monthly fee and get free delivery. I order 3-4 times a week so it would save me a lot."),
    ("user", "Student discount",
     "I'm a college student and can barely afford the fees. A student discount or cheaper delivery tier would be amazing."),
    ("user", "Promo codes never work",
     "Every promo code I try is expired or not valid for my area. I just want a simple way to save money on orders."),
    ("user", "Family plan pricing",
     "When I order for my whole family the fees add up fast. A family plan with reduced fees for larger orders would help."),
    ("user", "Loyalty rewards program",
     "Reward frequent customers with points or cashback. I've spent hundreds on this app and never gotten anything back."),
    ("user", "Surge pricing is ridiculous",
     "During peak hours the prices jump 30-40%. I understand supply and demand but this feels excessive."),
    ("user", "Bundle deals with restaurants",
     "Partner with restaurants to offer combo deals exclusive to BiteFlight. It would make ordering here feel like a better deal."),
    ("user", "Lower the minimum order for free delivery",
     "The minimum for free delivery is $35 which is too high for one person. Can it be $20?"),
    ("user", "Small order fee is unfair",
     "I got charged an extra $3 'small order fee' on top of delivery and service fees. Three separate fees is too many."),

    # ── Theme 2: Scheduled / advance orders (User) ───────────────────
    ("user", "Let me schedule orders in advance",
     "I want to place an order the night before so it arrives right when I get home from work. Currently I have to order in real-time."),
    ("user", "Pre-order for lunch during morning commute",
     "I'd love to order my lunch at 8am and have it arrive at noon. Scheduled delivery would be a game changer."),
    ("user", "Recurring weekly orders",
     "I order the same thing from the same place every Friday. Let me set up a recurring order so I don't have to repeat it."),
    ("user", "Schedule breakfast delivery",
     "I want fresh breakfast delivered at 7am but the app doesn't let me order that early. Scheduling would solve this."),
    ("user", "Calendar integration for meal planning",
     "Connect with Google Calendar so I can plan meals for the week and have them auto-ordered at the right times."),
    ("user", "Future date ordering for events",
     "I'm hosting a party next Saturday and want to pre-order catering. There's no way to place an order for a future date."),
    ("user", "Timed delivery windows",
     "Instead of 'ASAP' I want to pick a 30-minute window. Like 'deliver between 6:00-6:30pm'."),
    ("user", "Meal prep scheduling",
     "Let me schedule multiple orders for the week on Sunday. Batch planning would save so much time."),
    ("user", "Office lunch pre-orders",
     "Our office wants to pre-order lunch by 10am each day. A group scheduled order feature would be perfect."),
    ("user", "Remind me to reorder",
     "Send me a notification at my usual order time asking if I want to reorder my last meal. Make it one-tap."),
    ("user", "Schedule orders for when restaurant opens",
     "My favorite ramen place opens at 11:30. I want to be first in the queue with a scheduled order."),
    ("user", "Advance catering orders",
     "For large orders (10+ people), I need to order 24-48 hours ahead. The app only supports same-day."),

    # ── Theme 3: Launch in Canada (Driver) ───────────────────────────
    ("driver", "When is BiteFlight coming to Toronto?",
     "I'm a delivery driver in Toronto and would love to sign up. There's huge demand here but the app isn't available."),
    ("driver", "Expand to Vancouver",
     "Vancouver has a massive food delivery market. I'd switch from Skip the Dishes immediately if BiteFlight launched here."),
    ("driver", "Montreal availability",
     "Please launch in Montreal. The gig economy is huge here and we need more delivery platforms to choose from."),
    ("driver", "Canadian expansion timeline?",
     "Is there any plan to expand to Canada? I keep hearing rumors but nothing official. Calgary driver here."),
    ("driver", "Ottawa drivers want BiteFlight",
     "Several drivers I know in Ottawa are waiting for BiteFlight to launch. The other apps take too big a cut here."),
    ("driver", "Support for Canadian payment methods",
     "If you launch in Canada, make sure to support Interac e-Transfer and Canadian credit cards from day one."),
    ("driver", "Edmonton needs more delivery options",
     "The delivery market in Edmonton is underserved. BiteFlight could capture a lot of market share by launching here."),
    ("driver", "Bilingual app for Quebec",
     "If you come to Canada, the app needs full French support for Quebec. It's legally required and just good practice."),
    ("driver", "Winnipeg driver interested",
     "I drive for two other apps in Winnipeg and would add BiteFlight to my rotation. When can I sign up?"),
    ("driver", "Canadian tax compliance",
     "Make sure to handle GST/HST and provincial tax correctly. Also need T4A slips for driver income reporting."),
    ("driver", "KM-based pay for Canadian cities",
     "Canadian cities are more spread out. Make sure driver pay accounts for longer distances between restaurants and customers."),
    ("driver", "Winter delivery support for Canadian climate",
     "Canadian winters are brutal. If you launch here, we need weather-based bonus pay and realistic delivery time estimates for snow days."),

    # ── Theme 4: Video uploads for merchants ─────────────────────────
    ("merchant", "Let me upload videos of my dishes",
     "Photos are fine but a short video showing the food being prepared or plated would attract way more customers."),
    ("merchant", "Video menu items",
     "I want to attach a 15-second video to each menu item. Seeing the food in motion makes it way more appetizing."),
    ("merchant", "Restaurant promo videos",
     "Let me upload a promotional video for my restaurant profile. Customers want to see the vibe, the kitchen, the food."),
    ("merchant", "Behind-the-scenes kitchen videos",
     "I'd love to show customers how we make our food. A short video clip on my profile would build trust."),
    ("merchant", "Video reviews from customers",
     "Allow customers to upload video reviews of their orders. Real video testimonials are way more convincing than text."),
    ("merchant", "Reels-style food content",
     "Add a TikTok/Reels-style feed where merchants can post short food videos. It would drive discovery and orders."),
    ("merchant", "Video for daily specials",
     "I change my specials daily. A quick video announcement would be faster than updating photos every time."),
    ("merchant", "360-degree food photography",
     "Even if not full video, let me add a rotating 360 view of dishes. Flat photos don't do justice to presentation."),
    ("merchant", "Live kitchen cam",
     "A live stream option so customers can watch their food being made in real-time. It's a huge trust builder."),
    ("merchant", "Cooking tutorial clips",
     "I want to share short cooking tips alongside my menu. Like 'how we make our signature sauce'. Engages customers."),
    ("merchant", "Video testimonials on profile",
     "Let me pin video testimonials from happy customers to my restaurant profile page."),
    ("merchant", "Animated menu banners",
     "At minimum, support GIFs or animated banners on my merchant page. Static images feel outdated."),
]


class Command(BaseCommand):
    help = "Seed the database with feature requests for clustering demos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing feature requests before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            count = FeatureRequest.objects.count()
            FeatureRequest.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {count} existing feature requests"))

        created = 0
        for segment, title, description in SEED_DATA:
            fr = FeatureRequest.objects.create(
                segment=segment,
                title=title,
                description=description,
            )
            # Queue background task for embedding + AI extraction
            process_feature_request(str(fr.id))
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Created {created} feature requests across 4 themes. "
            f"Huey worker will process embeddings + extraction in the background."
        ))
