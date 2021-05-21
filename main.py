import time
import os
from BestBuyInventoryChecker import BestBuyInventoryChecker
import Twilio
import env_vars

# URL for all graphics cards available in this model on BestBuy
model_urls = {
    "RTX 3090": 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=category_facet%3Dabcat0507002%5Ecurrentprice_facet%3DPrice~%241250%20-%20%241499.99%5Ecurrentprice_facet%3DPrice~%241500%20-%20%241999.99%5Ecurrentprice_facet%3DPrice~%242000%20-%20%242499.99&sc=Global&st=rtx%203090&type=page&usc=All%20Categories',
    "RTX 3080": 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=category_facet%3DGPUs%20%2F%20Video%20Graphics%20Cards~abcat0507002&sc=Global&sp=%2Bcurrentprice%20skuidsaas&st=rtx%203080&type=page&usc=All%20Categories',
    "RTX 3070": 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=category_facet%3DGPUs%20%2F%20Video%20Graphics%20Cards~abcat0507002&sc=Global&st=rtx%203070&type=page&usc=All%20Categories',
    "RTX 3060 Ti": 'https://www.bestbuy.com/site/searchpage.jsp?id=pcat17071&qp=category_facet%3DGPUs%20%2F%20Video%20Graphics%20Cards~abcat0507002&st=rtx%203060%20ti',
    "Test": 'https://www.bestbuy.com/site/all-laptops/macbooks/pcmcat247400050001.c?id=pcmcat247400050001'
}

# Twilio client setup for text messages
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
phone_numbers = [os.environ['Main_Phone_Number']]

# Test Configuration
send_initialization_text = True

# Time Configurations
stock_check_frequency = 5  # 60 seconds
broken_script_timeout = 60*60*12  # 12 hours
maximum_message_frequency = 60 * 60 * 4  # 4 hours
retry_timeout = 10  # 10 seconds

# Folder Configuration
directory = f"{os.getcwd()}/Success_HTML"

# Initializations
Twil = Twilio.TwilioClient(account_sid, auth_token, phone_numbers)
BestBuy = BestBuyInventoryChecker(model_urls)
last_sent_success = time.time() - maximum_message_frequency
messaging_armed = True

# Send an initialization text to confirm everything started and texting is working
if send_initialization_text:
    Twil.send_initial_text()

# Main loop
while True:
    # Print time for tracking
    print(f"{time.ctime()}  --  Messaging Armed: {messaging_armed}")

    # Check to see if a test request gets a response, if not sleep and try again
    try:
        Test_SKU_Count, _ = BestBuy.get_inventory("Test")
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
        Twil.send_script_fail_text()
        time.sleep(broken_script_timeout)
        continue

    # Check for each model and print stock count in command line
    for model, url in BestBuy.model_urls.items():
        if model != "Test":
            try:
                in_stock, total_SKUs = BestBuy.get_inventory(model)

                print(f"    -- {in_stock} of {total_SKUs} {model}s in Stock.")

                messaging_armed = not time.time() - last_sent_success < maximum_message_frequency

                # Send text messages if something is in stock and a message hasn't been sent for a while
                if in_stock > 0 and messaging_armed:

                    print(f'{model} in Stock! {url}')

                    Twilio.send_success_text(model, url, phone_numbers)

                    # Save message sent time and change messaging armed to prevent repeated text messages
                    last_sent_success = time.time()
                    messaging_armed = False

            except:
                print("    -- something went wrong, starting over")
                continue

    time.sleep(stock_check_frequency)
