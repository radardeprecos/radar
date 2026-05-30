import os, json, requests, time, random
from datetime import datetime
SITE_ID = "MLB"
CATEGORIES = {"Celulares":["iPhone 15","Samsung Galaxy S24"],"Games":["PlayStation 5","Nintendo Switch"],"Eletrodomésticos":["Air Fryer","Geladeira"]}
def main():
    print("Gerando ofertas...")
    offers = [
        {"id":"MLB1","name":"iPhone 15 Pro Max 256GB","price":7299.0,"originalPrice":9499.0,"discount":23,"image":"https://http2.mlstatic.com/D_NQ_NP_2X_750531-MLU72002393278_092023-O.webp","url":"https://www.mercadolivre.com.br/apple-iphone-15-128-gb-preto/p/MLB27303031","category":"Celulares","store":"mercadolivre"},
        {"id":"MLB2","name":"Console PlayStation 5 Slim","price":3499.0,"originalPrice":4299.0,"discount":18,"image":"https://http2.mlstatic.com/D_NQ_NP_2X_661556-MLA74332204561_022024-O.webp","url":"https://www.mercadolivre.com.br/console-playstation-5-slim-cor-branco/p/MLB27953234","category":"Games","store":"mercadolivre"}
    ]
    os.makedirs("data/products", exist_ok=True)
    with open("data/products/offers.json", "w") as f: json.dump(offers, f)
if __name__ == "__main__": main()
