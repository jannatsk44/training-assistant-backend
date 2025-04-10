# add_topics.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartcompiler.settings")
django.setup()

from api.models import Topic  # Adjust 'your_app' to the actual app name where Topic model is defined

topics = [
"Basic Syntax",
"Program Execution",
"Comments",
"Data Types",
"Variables",
"Type Casting",
"Strings",
"Operators",
"Escape Characters",
"Lists",
"Keywords",
"Date and Time",
"Classes and Objects",
"Functions and Methods",
"If..Else",
"Loops",
"Break, Continue, Pass",
"Arrays",
"Exception Handling",
"Sets / HashSet / Maps",
"Dictionaries / HashMap / Map /",
"init() method / Constructor / Initialization",
"Static Method / Static / Static-like Functions",
"Introduction to OOP",
"Encapsulation",
"Inheritance / Composition",
"Polymorphism",
"Abstraction / Interfaces",
"Collections / STL Collections / Slices/Maps"
]

for topic_name in topics:
    topic, created = Topic.objects.get_or_create(name=topic_name)
    if created:
        print(f'Added new topic: {topic_name}')
    else:
        print(f'Topic already exists: {topic_name}')

print("All topics have been processed.")
