import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.collection import test

collection_name = input("collection name: ").strip()

if collection_name:
    test()
else:
    test()
