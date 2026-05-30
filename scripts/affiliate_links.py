import os
import json
from logger import logger

def process(input_p: str, output_p: str):
    if not os.path.exists(input_p):
        products = []
    else:
        with open(input_p, "r", encoding="utf-8") as f:
            products = json.load(f)
    
    os.makedirs(os.path.dirname(output_p), exist_ok=True)
    with open(output_p, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    process("data/scored_products.json", "data/affiliate_products.json")
