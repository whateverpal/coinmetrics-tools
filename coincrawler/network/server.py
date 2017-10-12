import BaseHTTPServer
import threading
import json
import urllib
import time
import os
import traceback

class ThreadedHTTPServer(BaseHTTPServer.HTTPServer):

	def process_request(self, request, client_address):
		thread = threading.Thread(target=self.__new_request, args=(self.RequestHandlerClass, request, client_address, self))
		thread.start()
		
	def __new_request(self, handlerClass, request, address, server):
		handlerClass(request, address, server)
		self.shutdown_request(request)


class NetworkServer(object):

	class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

		def do_GET(self):
			self.server.owner.processRequest(self)

	def __init__(self, port, executor, inputExecutor=None):
		self.port = port
		self.server = ThreadedHTTPServer(("0.0.0.0", port), NetworkServer.Handler)
		self.server.owner = self
		self.executor = executor
		self.inputExecutor = inputExecutor

	def runWithInput(self):
		self.start()
		try:
			while True:
				userInput = raw_input("")
				if self.inputExecutor is not None:
					self.inputExecutor.processInput(userInput)
				else:
					print "this server doesn't handle input"
		except:
			try:
				print "Received exception: ", traceback.format_exc()
			except KeyboardInterrupt:
				print "keyboard interrupt"
			os._exit(1)

	def run(self):
		self.start()
		try:
			while True:
				time.sleep(0.1)
		except KeyboardInterrupt:
			os._exit(1)

	def start(self):
		self.thread = threading.Thread(None, self.threadFunc, "", ())
		self.thread.start()
		print "Http server started, using port %s" % self.port

	def stop(self):
		self.server.shutdown()
		self.thread.join()
		self.executor.stop()
		print "Http server stopped"

	def threadFunc(self):
		self.server.serve_forever()

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