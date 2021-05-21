import requests
from bs4 import BeautifulSoup


class BestBuyInventoryChecker:
    def __init__(self, model_urls):
        self.headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0"}
        self.model_urls = model_urls

    def _get_page_html(self, model):
        """
        Request the web page associated with the checker and return the HTML from that request

        Returns: html contents
        """
        url = self.model_urls[model]
        page = requests.get(url, headers=self.headers)
        return page.content

    def _check_item_in_stock(self, page_contents):
        """
        Look for how many items are IN STOCK based on the class of the 'add to cart' buttons

        Returns: Int
        """
        soup = BeautifulSoup(page_contents, 'html.parser')
        in_stock_divs = soup.findAll("button", {
            "class": "btn btn-primary btn-sm btn-block btn-leading-ficon add-to-cart-button"
        })
        return len(in_stock_divs)

    def _check_item_out_of_stock(self, page_contents):
        """
        Look for how many items are OUT OF STOCK based on the class of the 'add to cart' buttons

        Returns: Int
        """
        soup = BeautifulSoup(page_contents, 'html.parser')
        out_of_stock_divs = soup.findAll("button", {
            "class": "btn btn-disabled btn-sm btn-block add-to-cart-button"
        })
        return len(out_of_stock_divs)

    def get_inventory(self, model):
        """
        Grab a new copy of the webpage and get the number of items in and out of stock

        Returns: int, int
        """
        page_contents = self._get_page_html(model)
        in_stock = self._check_item_in_stock(page_contents)
        out_of_stock = self._check_item_out_of_stock(page_contents)
        total_skus = in_stock + out_of_stock
        return in_stock, total_skus
