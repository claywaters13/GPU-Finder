import requests
import time
import os
from bs4 import BeautifulSoup
from twilio.rest import Client
import env_vars

# URL for all graphics cards available in this model on BestBuy
models = {
    "RTX 3090": 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=category_facet%3Dabcat0507002%5Ecurrentprice_facet%3DPrice~%241250%20-%20%241499.99%5Ecurrentprice_facet%3DPrice~%241500%20-%20%241999.99%5Ecurrentprice_facet%3DPrice~%242000%20-%20%242499.99&sc=Global&st=rtx%203090&type=page&usc=All%20Categories',
    "RTX 3080": 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=category_facet%3DGPUs%20%2F%20Video%20Graphics%20Cards~abcat0507002&sc=Global&sp=%2Bcurrentprice%20skuidsaas&st=rtx%203080&type=page&usc=All%20Categories',
    "RTX 3070": 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=category_facet%3DGPUs%20%2F%20Video%20Graphics%20Cards~abcat0507002&sc=Global&st=rtx%203070&type=page&usc=All%20Categories',
    "RTX 3060 Ti": 'https://www.bestbuy.com/site/searchpage.jsp?id=pcat17071&qp=category_facet%3DGPUs%20%2F%20Video%20Graphics%20Cards~abcat0507002&st=rtx%203060%20ti',
    # "Nintendo Switch": 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=category_facet%3DNintendo%20Switch%20Consoles~pcmcat1484077694025%5Ecurrentprice_facet%3DPrice~200%20to%20300&sc=Global&st=nintendo%20switch%20joy-con&type=page&usc=All%20Categories',
}

# Test page for laptops that has 23 in stock macbooks and should always have something "in stock"
test_url = 'https://www.bestbuy.com/site/all-laptops/macbooks/pcmcat247400050001.c?id=pcmcat247400050001'

# Enable this line to add a webpage with items in stock and test the success messages
# models["test"] = 'https://www.bestbuy.com/site/all-laptops/macbooks/pcmcat247400050001.c?id=pcmcat247400050001'

# Twilio client setup for text messages
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

# Phone Numbers for alerting
phone_numbers = [os.environ['Main_Phone_Number']]

# Test Configuration
send_initialization_text = True

# Time Configurations
stock_check_frequency = 60  # 60 seconds
broken_script_timeout = 60*60*12  # 12 hours
maximum_message_frequency = 60 * 60 * 4  # 4 hours
retry_timeout = 10  # 10 seconds
last_sent_success = time.time() - maximum_message_frequency
messaging_armed = True

# Folder Configuration
directory = f"{os.getcwd()}/Success_HTML"


class BestBuyInventoryChecker:
    def __init__(self, model):
        self.headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0"}
        self.model = model
        if model == "test":
            self.url = test_url
        else:
            self.url = models[model]
        self.html = 0

    def _get_page_html(self):
        """
        Request the web page associated with the checker and return the HTML from that request

        Returns: html contents
        """
        page = requests.get(self.url, headers=self.headers)
        self.html = page.content

    def _check_item_in_stock(self):
        """
        Look for how many items are IN STOCK based on the class of the 'add to cart' buttons

        Returns: Int
        """
        soup = BeautifulSoup(self.html, 'html.parser')
        in_stock_divs = soup.findAll("button", {
            "class": "btn btn-primary btn-sm btn-block btn-leading-ficon add-to-cart-button"
        })
        return len(in_stock_divs)

    def _check_item_out_of_stock(self):
        """
        Look for how many items are OUT OF STOCK based on the class of the 'add to cart' buttons

        Returns: Int
        """
        soup = BeautifulSoup(self.html, 'html.parser')
        out_of_stock_divs = soup.findAll("button", {
            "class": "btn btn-disabled btn-sm btn-block add-to-cart-button"
        })
        return len(out_of_stock_divs)

    def get_inventory(self):
        """
        Grab a new copy of the webpage and get the number of items in and out of stock

        Returns: int, int
        """
        self._get_page_html()
        in_stock = self._check_item_in_stock()
        out_of_stock = self._check_item_out_of_stock()
        total_SKUs = in_stock + out_of_stock
        return in_stock, total_SKUs


# Send a single text message to confirm that the text integration is working properly

if send_initialization_text:
    print("\nSending test text message on initialization\n")

    client.api.account.messages.create(
        body='This message confirms that your script has initialized properly and text notifications are working',
        from_='+12244343786',
        to=phone_numbers[0]
    )


while True:
    # Print time for tracking
    print(f"{time.ctime()}  --  Messaging Armed: {messaging_armed}")

    # Check to see if a test request gets a response, if not sleep and try again\
    try:
        Check = BestBuyInventoryChecker("test")
        Test_SKU_Count, _ = Check.get_inventory()
    except:
        print("URL Request Failed - trying again")
        time.sleep(stock_check_frequency)
        continue

    # Make sure that test gives a positive available SKU count, but only try three times
    sku_error = 0
    max_sku_error = 3

    # Successful Test - print success and move on
    if Test_SKU_Count > 0:
        print(f"    -- SKU Check Test Successful :{Test_SKU_Count} units")
        sku_error = 0

    # Failed Test - add to counter and try again
    elif sku_error < max_sku_error:
        print(f"SKU Count Error -- Trying {max_sku_error - sku_error} more times")
        sku_error += 1
        time.sleep(retry_timeout)

    # Continually Failed Test - send a text message to the main number and wait for a while
    else:
        client.api.account.messages.create(
            body='Your Stock Checker Script Broke... might wanna fix it',
            from_='+12244343786',
            to=phone_numbers[0]
        )
        print('****     Your Script Broke... might wanna fix it     ****')

        time.sleep(broken_script_timeout)
        continue

    # Check for each model and print stock count in command line
    for model, url in models.items():
        try:
            in_stock, total_SKUs = BestBuyInventoryChecker(model).get_inventory()

            print(f"    -- {in_stock} of {total_SKUs} {model}s in Stock.")

            messaging_armed = not time.time() - last_sent_success < maximum_message_frequency

            # Send text messages if something is in stock and a message hasn't been sent for a while
            if in_stock > 0 and messaging_armed:

                print(f'{model} in Stock! {url}')

                for number in phone_numbers:
                    client.api.account.messages.create(
                        body=f'{model} in Stock! {url}',
                        from_='+12244343786',
                        to=number
                    )

                # Save message sent time and change messaging armed to prevent repeated text messages
                last_sent_success = time.time()
                messaging_armed = False

        except:
            print("    -- something went wrong, starting over")
            continue

    time.sleep(stock_check_frequency)
