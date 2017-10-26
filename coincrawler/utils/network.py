import requests
import time

def hardenedRequestsGet(url, timeout=10, maxRetries=5, sleepBetweenRetries=5):
	result = None
	retries = 0
	while result is None:
		try:
			result = requests.get(url, timeout=timeout)
		except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
			if retries < maxRetries:
				retries += 1
				time.sleep(sleepBetweenRetries)
			else:
				break
	return result


			