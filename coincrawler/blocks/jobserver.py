import BaseHTTPServer
import threading
import json
import urllib
import requests
import time
from datetime import datetime
from coincrawler.blocks.downloaders import SerialDownloader
from coincrawler.blocks.datasources import *

class HttpServer(object):

	class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

		def do_GET(self):
			self.server.owner.processRequest(self)

	def __init__(self, port):
		self.server = BaseHTTPServer.HTTPServer(("0.0.0.0", port), HttpServer.Handler)
		self.server.owner = self

	def start(self):
		self.thread = threading.Thread(None, self.threadFunc, "", ())
		self.thread.start()
		print "Http server started"

	def stop(self):
		self.server.shutdown()
		self.thread.join()
		print "Http server stopped"

	def threadFunc(self):
		self.server.serve_forever()

	def processRequest(self, request):
		return


class JobServer(HttpServer):

	def __init__(self, port, dataSources, dataSourcesSleepBetweenRequests):
		super(JobServer, self).__init__(port)
		self.executor = BlockCollectionJobExecutor(dataSources, dataSourcesSleepBetweenRequests)

	def stop(self):
		HttpServer.stop(self)
		self.executor.stop()

	def processRequest(self, request):
		jsonCommand = None
		elements = request.path.split("/")
		if len(elements) != 2:
			return self.badRequest(request)
		try:
			jsonCommand = json.loads(urllib.unquote(elements[1]))
		except Exception as e:
			print e
			return self.badRequest(request)

		if not "method" in jsonCommand:
			return self.badRequest(request)

		params = jsonCommand["params"] if "params" in jsonCommand else []
		if type(params) != list:
			return self.badRequest(request)

		result, error = self.executor.tryExecuteCommand(jsonCommand["method"], params)
		if error is not None:
			return self.badRequest(request, error)
		else:
			return self.respondOk(request, result)

	def badRequest(self, request, error="Malformed request"):
		request.send_response(400)
		request.send_header("Content-type", "text/json")
		request.end_headers()
		request.wfile.write('{"error": "%s"}' % error)

	def respondOk(self, request, payload):
		request.send_response(200)
		request.send_header("Content-type", "text/json")
		request.end_headers()
		request.wfile.write(json.dumps(payload))

	def tryExecuteNewJobCommand(self, request, jobParams):
		jobId, error = self.executor.tryStartJob(jobParams)
		if error:
			return self.badRequest(request, error)
		else:
			return self.respondOk(request, '{"jobId": %d}' % jobId)

	def tryExecuteGetJobStatusCommand(self, request, jobId):
		result = self.executor.tryGetJobStatus(int(jobId))
		return self.respondOk(request, json.dumps(result))

	def tryGetJobResult(self, request, jobId, blockStart, blockEnd):
		result = self.executor.tryGetJobResult(int(jobId), int(blockStart), int(blockEnd))
		return self.respondOk(request, json.dumps(result))


class BlockCollectionJobExecutor(object):

	def __init__(self, dataSources, dataSourcesSleepBetweenRequests):
		self.jobCounter = 0
		self.jobs = {}
		self.jobsLastAccess = {}
		self.commandsRegistry = {
			"startJob": self.startBlockCollectionJobCommand,
			"getNetworkBlockHeight": self.getNetworkBlockHeightCommand,
			"stopJob": self.stopJobCommand,
			"stopAllJobs": self.stopAllJobsCommand,
			"getJobStatus": self.getJobStatusCommand,
			"getJobResult": self.getJobResultCommand,
			"ping": self.getPingCommand,
		}

		self.dataSources = dataSources
		self.dataSourcesSleepBetweenRequests = dataSourcesSleepBetweenRequests

		self.stopping = False
		self.gcThread = threading.Thread(None, self.gcThreadFunc, "", ())
		self.gcThread.start()

	def stop(self):
		print "stopping jobs executor"
		self.stopping = True
		self.stopAllJobsCommand()
		self.gcThread.join()

	def gcThreadFunc(self):
		while not self.stopping:
			now = datetime.now()
			toRemove = []
			for key, value in self.jobsLastAccess.iteritems():
				print "gc thread: testing job %d, last access %d second(s) ago" % (key, (now - value).total_seconds())
				if (now - value).total_seconds() > 60 * 60:
					toRemove.append(key)

			for jobId in toRemove:
				print "gc thread: emoving job %d due to timeout" % jobId
				self.removeJob(jobId)

			time.sleep(15)

	def removeJob(self, jobId):
		print "removing job %d" % jobId
		self.jobs[jobId].stop()
		del self.jobs[jobId]
		del self.jobsLastAccess[jobId]

	def tryExecuteCommand(self, commandName, params):
		if not commandName in self.commandsRegistry:
			return None, "Unknown command"
		return self.commandsRegistry[commandName](*params)

	def startBlockCollectionJobCommand(self, currency='none', fromHeight=1, toHeight=1, *args):
		if not currency in self.dataSources:
			return None, "Unknown currency"

		if fromHeight < 1 or toHeight < 1 or toHeight < fromHeight:
			return None, "Bad params"

		self.jobCounter += 1
		sleepBetweenRequests = 0
		if currency in self.dataSourcesSleepBetweenRequests:
			sleepBetweenRequests = self.dataSourcesSleepBetweenRequests[currency]
		self.jobs[self.jobCounter] = BlockCollectionJob(SerialDownloader(self.dataSources[currency](), sleepBetweenRequests=sleepBetweenRequests), fromHeight, toHeight)
		self.jobs[self.jobCounter].start()
		self.jobsLastAccess[self.jobCounter] = datetime.now()
		return self.jobCounter, None

	def stopJobCommand(self, jobId=0, *args):
		jobId = int(jobId)
		if not jobId in self.jobs:
			return None, "No job with provided id"
		self.removeJob(jobId)
		return True, None

	def stopAllJobsCommand(self, *args):
		for job in self.jobs.values():
			job.prepareToStop()
		for jobId in self.jobs.keys():
			self.removeJob(jobId)
		self.jobs = {}
		return True, None

	def getJobStatusCommand(self, jobId=0, *args):
		jobId = int(jobId)
		if not jobId in self.jobs:
			return None, "No job with provided id"

		job = self.jobs[jobId]
		self.jobsLastAccess[jobId] = datetime.now()
		result = {"progress": job.getProgress(), "failed": job.getFailed()}
		if job.getFailed():
			result["failure_message"] = job.getFailureMessage()
		return result, None

	def getJobResultCommand(self, jobId=0, fromHeight=0, toHeight=0, *args):
		jobId = int(jobId)
		if not jobId in self.jobs:
			return None, "No job with provided id"

		job = self.jobs[jobId]
		self.jobsLastAccess[jobId] = datetime.now()
		if job.getFailed():
			return None, "Job failed %s: %s" % (jobId, job.getFailureMessage())

		if fromHeight < 1 or toHeight < 1 or toHeight < fromHeight:
			return None, "Bad params"

		return job.getResult(int(fromHeight), int(toHeight)), None

	def getNetworkBlockHeightCommand(self, currency='none'):
		if not currency in self.dataSources:
			return None, "Unavailable for requested currency"

		try:
			result = self.dataSources[currency]().getBlockHeight()
			return result, None
		except Exception as e:
			print e
			return None, str(e)

	def getPingCommand(self):
		return {}, None


class BlockCollectionJob(object):

	def __init__(self, downloader, fromHeight, toHeight):
		self.downloader = downloader
		self.fromHeight = fromHeight
		self.toHeight = toHeight
		self.stopping = False
		self.storage = {}
		self.failed = False
		self.errorMessage = ""
		self.progress = 0

	def start(self):
		self.thread = threading.Thread(None, self.threadFunc, "", ())
		self.thread.start()

	def prepareToStop(self):
		self.stopping = True

	def stop(self):
		self.stopping = True
		self.thread.join()

	def threadFunc(self):
		try:
			steps = 0
			for block in self.downloader.loadBlocks(range(self.fromHeight, self.toHeight + 1)):
				steps += 1
				self.progress = float(steps) / (self.toHeight - self.fromHeight + 1)
				self.storage[block['height']] = block
				if not type(block['timestamp']) is int:
					block['timestamp'] = int((block['timestamp'] - datetime(1970, 1, 1, tzinfo=block['timestamp'].tzinfo)).total_seconds())
				if self.stopping:
					print "Stop signal received by the job"
					break
		except Exception as e:
			print e
			print "job failed!"
			self.setFailed(str(e))
			raise e

	def getFailed(self):
		return self.failed

	def getFailureMessage(self):
		return self.errorMessage

	def getProgress(self):
		return self.progress

	def getResult(self, fromHeight, toHeight):
		result = []
		for i in range(fromHeight, toHeight + 1):
			if i in self.storage:
				result.append(self.storage[i])
			else:
				result.append(None)
		return result

	def setFailed(self, errorMessage):
		self.failed = True
		self.errorMessage = errorMessage
