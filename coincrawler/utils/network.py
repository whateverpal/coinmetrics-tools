import requests
import time

def hardenedRequestsGet(url, timeout=10, maxRetries=5, sleepBetweenRetries=10, jsonResponse=False, verify=True):
	result = None
	retries = 0
	while result is None:
		try:
			result = requests.get(url, timeout=timeout, verify=verify)
		except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
			if retries < maxRetries:
				retries += 1
				time.sleep(sleepBetweenRetries)
			else:
				break

		if jsonResponse:
			if result is not None:
				try:
					json = result.json()
				except ValueError:
					print "Malformed json, response status code is %d" % result.status_code
					result = None
					if retries < maxRetries:
						retries += 1
						time.sleep(sleepBetweenRetries)
					else:
						break

	return result


			