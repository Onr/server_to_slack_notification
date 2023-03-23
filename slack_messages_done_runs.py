import logging
import traceback
import argparse
import slack
from slack_api import SLACK_TOKEN

# Send Slack notification based on the given message
def slack_notification(message):
    try:
        client = slack.WebClient(token=SLACK_TOKEN)
        client.chat_postMessage(channel='#done-runs-point-clouds',text=message)
        logging.info("Slack notification sent")
    except Exception as e:
        traceback.print_exc()
        logging.info("Slack notification failed")
        

def main(args):
    slack_notification(message=args.m)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send messages on slack channel')
    parser.add_argument('-m', type=str, help='message to send')
    args = parser.parse_args()
    main(args)

