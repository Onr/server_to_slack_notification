import logging
import os
import traceback
import json
import urllib3
import argparse


# Send Slack notification based on the given message
def slack_notification(message):

    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    try:
        slack_message = {'text': message}

        http = urllib3.PoolManager()
        response = http.request('POST',
                                webhook_url,
                                body = json.dumps(slack_message),
                                headers = {'Content-Type': 'application/json'},
                                retries = False)
        logging.info("Slack notification sent")
        
    except:
        traceback.print_exc()
        logging.info("Slack notification failed")

    return True


def main(args):
    slack_notification(message=args.m)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Send messages on slack channel')
    parser.add_argument('-m', type=str, help='message to send')
    args = parser.parse_args()
    main(args)

