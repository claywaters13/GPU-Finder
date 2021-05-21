from twilio.rest import Client
import time


class TwilioClient:
    def __init__(self, account_sid, auth_token, phone_numbers):
        self.client = Client(account_sid, auth_token)
        self.phone_numbers = phone_numbers

    def send_initial_text(self):
        remaining_attempts = 1
        print("\nSending test text message on initialization\n")

        while remaining_attempts > 0:
            try:
                self.client.api.account.messages.create(
                    body='This message confirms that your script has initialized properly',
                    from_='+12244343786',
                    to=self.phone_numbers[0]
                )
                remaining_attempts = 0
            except:
                remaining_attempts = remaining_attempts - 1
                print(f"Tried to send message and failed, will retry {remaining_attempts} more times")
                time.sleep(3-remaining_attempts)

    def send_success_text(self, model, url):
        for number in self.phone_numbers:
            self.client.api.account.messages.create(
                body=f'{model} in Stock! {url}',
                from_='+12244343786',
                to=number
            )

    def send_script_fail_text(self):
        self.client.api.account.messages.create(
            body='Your Stock Checker Script Broke... might wanna fix it',
            from_='+12244343786',
            to=self.phone_numbers[0]
        )
        print('****     Your Script Broke... might wanna fix it     ****')