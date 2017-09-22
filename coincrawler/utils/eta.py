from datetime import datetime

class ObservationsHistory(object):

	def __init__(self, maxObservations):
		self.maxObservations = maxObservations
		self.observations = []

	def addObservation(self, observation):
		self.observations.append(observation)
		if len(self.observations) > self.maxObservations:
			self.observations = self.observations[1:]

	def getAverage(self):
		return sum(self.observations) / len(self.observations)


class BlockCollectionETA(object):

	def __init__(self, totalWorkAmount, maxObservations, outputInterval, printPrefix="", silent=False):
		assert(totalWorkAmount > 0)
		self.totalWorkAmount = totalWorkAmount
		self.workDone = 0
		self.history = ObservationsHistory(maxObservations)
		self.workStartedFlag = False
		self.workStartedTime = None
		self.outputInterval = outputInterval
		self.workSteps = 0
		self.printPrefix = printPrefix
		self.silent = silent

	def workStarted(self):
		assert(not self.workStartedFlag)
		self.workStartedFlag = True
		self.workStartedTime = datetime.now()

	def workFinished(self, workDone):
		assert(self.workStartedFlag)
		self.workStartedFlag = False
		timeForUnitOfWork = (datetime.now() - self.workStartedTime).total_seconds() / workDone
		self.history.addObservation(timeForUnitOfWork)
		self.workDone += workDone
		self.workSteps += 1

		if self.workSteps % self.outputInterval == 0:
			self.output()
			return True
		else:
			return False

	def getETA(self):
		return (self.totalWorkAmount - self.workDone) * self.history.getAverage()

	def getPercentDone(self):
		return float(self.workDone) / self.totalWorkAmount

	def output(self):
		if not self.silent:
			percentDone = self.getPercentDone()
			print self.printPrefix + "{0:0.2f}% done, eta is {1}".format(100.0 * self.getPercentDone(), self.prettyStringForETA(self.getETA()))

	def prettyStringForETA(self, etaInSeconds):
		totalSeconds = int(etaInSeconds)

		daysModulo = totalSeconds % (3600 * 24)
		days = (totalSeconds - daysModulo) / (3600 * 24)
		totalSeconds -= days * (3600 * 24)

		hoursModulo = totalSeconds % 3600
		hours = (totalSeconds - hoursModulo) / 3600
		totalSeconds -= hours * 3600

		minutesModulo = totalSeconds % 60
		minutes = (totalSeconds - minutesModulo) / 60
		seconds = totalSeconds - minutes * 60

		return "%s days %s hours %s minutes %s seconds" % (days, hours, minutes, seconds)


