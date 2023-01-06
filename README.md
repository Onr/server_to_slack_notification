# server_to_slack_notification
Send notification to a slack channel when conditions are met

## Setup
### 1. Install using pip:

``` python -m venv env_notification```

```source env_notification/bin/activate```

```pip install -r requirements.txt```

### 2. Create a slack app and get the webhook url using the following link:

* [Official slack tutorial](https://api.slack.com/messaging/webhooks)

* Export the webhook url as an environment variable:

```export SLACK_WEBHOOK_URL=<your_webhook_url>```


## Run
```sh run_command.sh```


