import threading
import json
import requests
import time
import traceback
from datetime import datetime
from coincrawler.blocks.downloaders import SerialDownloader
from coincrawler.network.server import NetworkServer


class BlockCollectionServer(NetworkServer):

	def __init__(self, port, dataSources, dataSourcesSleepBetweenRequests):
		super(BlockCollectionServer, self).__init__(port, BlockCollectionJobExecutor(dataSources, dataSourcesSleepBetweenRequests))


class BlockCollectionJobExecutor(object):

	def __init__(self, dataSources, dataSourcesSleepBetweenRequests):
		self.jobCounter = 0
		self.jobs = {}
		self.jobsLastAccess = {}
		self.jobsLock = threading.Lock()

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
			with self.jobsLock:
				for key, value in self.jobsLastAccess.iteritems():
					print "gc thread: testing job %d, last access %d second(s) ago" % (key, (now - value).total_seconds())
					if (now - value).total_seconds() > 30 * 60:
						toRemove.append(key)

				for jobId in toRemove:
					print "gc thread: removing job %d due to timeout" % jobId
					self.removeJobNoLock(jobId)

			time.sleep(20)

	def removeJob(self, jobId):
		with self.jobsLock:
			self.removeJobNoLock(jobId)

	def removeJobNoLock(self, jobId):
		if jobId in self.jobs:
			print "removing job %d" % jobId
			self.jobs[jobId].stop()
			del self.jobs[jobId]
			del self.jobsLastAccess[jobId]
		else:
			print "failed to remove non-existent job %s" % jobId

	def tryExecuteCommand(self, commandName, params):
		if not commandName in self.commandsRegistry:
			return None, "Unknown command"
		return self.commandsRegistry[commandName](*params)

	def startBlockCollectionJobCommand(self, currency='none', fromHeight=1, toHeight=1, *args):
		if not currency in self.dataSources:
			return None, "Unknown currency"

		if fromHeight < 1 or toHeight < 1 or toHeight < fromHeight:
			return None, "Bad params"

		with self.jobsLock:
			self.jobCounter += 1
			sleepBetweenRequests = 0
			if currency in self.dataSourcesSleepBetweenRequests:
				sleepBetweenRequests = self.dataSourcesSleepBetweenRequests[currency]
			self.jobs[self.jobCounter] = BlockCollectionJob(self.dataSources[currency], sleepBetweenRequests, fromHeight, toHeight)
			self.jobs[self.jobCounter].start()
			self.jobsLastAccess[self.jobCounter] = datetime.now()
		return self.jobCounter, None

	def stopJobCommand(self, jobId=0, *args):
		with self.jobsLock:
			jobId = int(jobId)
			if not jobId in self.jobs:
				return None, "No job with provided id"
			self.removeJobNoLock(jobId)
		return True, None

	def stopAllJobsCommand(self, *args):
		with self.jobsLock:
			for job in self.jobs.values():
				job.stop()
			for jobId in self.jobs.keys():
				self.removeJobNoLock(jobId)
			self.jobs = {}
		return True, None

	def getJobStatusCommand(self, jobId=0, *args):
		with self.jobsLock:
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
		with self.jobsLock:
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

	def __init__(self, source, sleepBetweenRequests, fromHeight, toHeight):
		self.source = source
		self.sleepBetweenRequests = sleepBetweenRequests
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

	def stop(self):
		self.stopping = True

	def threadFunc(self):
		try:
			downloader = SerialDownloader(self.source(), sleepBetweenRequests=self.sleepBetweenRequests)
			steps = 0
			for block in downloader.loadBlocks(range(self.fromHeight, self.toHeight + 1)):
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
			self.setFailed(traceback.format_exc())
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
