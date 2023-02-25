import logging
import random

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')

def process(force_process=False):
    # Randomize with high chance it will succeed.
    return True if random.random() > 0.1 else False

def handler(event, context):
    data = {}
    data["logistic_state"] = "done"
    data["logistic_result"] = process()        
    return data