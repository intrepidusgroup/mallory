from array import array
from base import TcpProtocol
from sys import py3kwarning
from urlparse import urlsplit

import socket
import select
import urlparse
import warnings
import zlib
import gzip
import time
import Image
import sys
import StringIO
import logging
import traceback
import cgi

import malloryevt

with warnings.catch_warnings():
    if py3kwarning:
        warnings.filterwarnings("ignore", ".*mimetools has been removed",
                                DeprecationWarning)
    import mimetools

#try:
#    from cStringIO import StringIO
#except ImportError:
#    from StringIO import StringIO
  
  
HTTP_PORT = 80
HTTPS_PORT = 443

_UNKNOWN = 'UNKNOWN'

# connection states
_CS_IDLE = 'Idle'
_CS_REQ_STARTED = 'Request-started'
_CS_REQ_SENT = 'Request-sent'

# status codes
# informational
CONTINUE = 100
SWITCHING_PROTOCOLS = 101
PROCESSING = 102

# successful
OK = 200
CREATED = 201
ACCEPTED = 202
NON_AUTHORITATIVE_INFORMATION = 203
NO_CONTENT = 204
RESET_CONTENT = 205
PARTIAL_CONTENT = 206
MULTI_STATUS = 207
IM_USED = 226

# redirection
MULTIPLE_CHOICES = 300
MOVED_PERMANENTLY = 301
FOUND = 302
SEE_OTHER = 303
NOT_MODIFIED = 304
USE_PROXY = 305
TEMPORARY_REDIRECT = 307

# client error
BAD_REQUEST = 400
UNAUTHORIZED = 401
PAYMENT_REQUIRED = 402
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
NOT_ACCEPTABLE = 406
PROXY_AUTHENTICATION_REQUIRED = 407
REQUEST_TIMEOUT = 408
CONFLICT = 409
GONE = 410
LENGTH_REQUIRED = 411
PRECONDITION_FAILED = 412
REQUEST_ENTITY_TOO_LARGE = 413
REQUEST_URI_TOO_LONG = 414
UNSUPPORTED_MEDIA_TYPE = 415
REQUESTED_RANGE_NOT_SATISFIABLE = 416
EXPECTATION_FAILED = 417
UNPROCESSABLE_ENTITY = 422
LOCKED = 423
FAILED_DEPENDENCY = 424
UPGRADE_REQUIRED = 426

# server error
INTERNAL_SERVER_ERROR = 500
NOT_IMPLEMENTED = 501
BAD_GATEWAY = 502
SERVICE_UNAVAILABLE = 503
GATEWAY_TIMEOUT = 504
HTTP_VERSION_NOT_SUPPORTED = 505
INSUFFICIENT_STORAGE = 507
NOT_EXTENDED = 510

MAXAMOUNT = 1024*1024

# Mapping status codes to official W3C names
responses = {
    100: 'Continue',
    101: 'Switching Protocols',

    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',

    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    306: '(Unused)',
    307: 'Temporary Redirect',

    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',

    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
}


class HTTP(TcpProtocol):
    """
    This module interprets HTTP responses and gives an object oriented
    interface to an HTTP response. There is an external dependency on
    the Python Imaging Library (PIL). However, it is wrapped in exception
    handling code that will not prevent the module from operating properly.
    If the dependency is not met it will, however, generate a lot of errors.
    """
    def __init__(self, trafficdb, source, destination):
        TcpProtocol.__init__(self, trafficdb, source, destination)
        self.friendly_name = "HTTP"
        self.serverPort = 80
        self.log = logging.getLogger("mallorymain")
        self.log.info("HTTP protocol handler initialized")
        self.supports = {malloryevt.STARTS2C:True, malloryevt.STARTC2S:True}        
        
        
                        
    def forward_c2s(self, conndata):
        try:
            self.log.debug("HTTP: starting http request")
            request = HTTPRequest(self.source)
            request.begin()
            #RAJRAJRAJ
            #This is where the first notify for plugs are... need to be able to
            #distinguish between blogking and non blocking plugsin..
            #The events will represent where in proto notify was sent
            #Each proto will have diff hooks points.
            #STill need to think about blocking and non blocking problem
            if self.plugin_manager != None:
                request = self.plugin_manager.process(event="HTTP:c2s", data=request)
            
            if self.config.debug > 1:
                self.log.debug("HTTP: c2s: Request: \r\n%s" % (repr(str(request))))
                self.log.debug("HTTP: c2s: Request: \r\n%s" % (str(request.headers)))
            
            str_request = str(request)
            self.trafficdb.qFlow.put((conndata.conncount, \
                conndata.direction, 0, time.time(), repr(str_request))) 
            self.destination.sendall(str(request))
        
        except:
            traceback.print_exc()
            
    def forward_s2c(self, conndata):
        """
        This method is intended to interpret HTTP responses from the victim's
        server. It encapsulates the HTTP response in an object and provides 
        a high level interface to manipulate HTTP content. 
        """
        self.log.debug("HTTP: starting s2c")
        response = HTTPResponse(self.destination)
        
        response.begin()        
        responsebody = response.read()
        response.dirty_body = responsebody
                
        #isimage = False
        isgzip = False
        isdeflate = False
        remove_header = []
        
        # Process headers
        for header in response.msg.headers:
                
            # Get rid of this to avoid having to do math
            if "Content-Length" in header:
                remove_header.append(header)
                
            # Clean up and deal with compression
            if "Content-Encoding" in header:
                encoding = response.msg.getheader("content-encoding")  
                
                # Content will not be compressed          
                if encoding == "gzip":
                    isgzip = True
                    remove_header.append(header)
                if encoding == "deflate":
                    isdeflate = True
                        
            # Content will not be chunked
            if "Transfer-Encoding" in header or "Transfer-encoding" in header:
                
                remove_header.append(header)
    
        # Take out headers that are not needed
        for header in remove_header:
            response.msg.headers.remove(header)
            
        remove_header = []
                
        if isgzip:
            decompress = gzip.GzipFile("", "rb", 9, \
                                       StringIO.StringIO(responsebody))
            responsebody = decompress.read()
        
        response.clean_body = responsebody
        
        if self.plugin_manager != None:
            response = self.plugin_manager.process(event="HTTP:s2c", data=response)
        
       
                
        # Push the response off to the victim
        str_status = responses[response.status]
        
        # HTTP status line
        responseline = "HTTP/1.1 %d %s\r\n" % \
            (response.status, str_status)
        self.source.sendall(responseline)
        
        # HTTP Headers
        self.source.sendall(str(response.msg) + "\r\n")
        
        # Some response types will not have a body
        if len(response.clean_body) > 0:            
            self.source.sendall(response.clean_body)
    
            
        # Make sure nothing bad has happened reading the response
        assert response.will_close != 'UNKNOWN'
        
        str_response = responseline + str(response.msg) + "\r\n" + responsebody
        
        self.trafficdb.qFlow.put((conndata.conncount, \
                conndata.direction, 0, time.time(), repr(str_response)))
           
        self.log.debug("HTTP.forward_s2c(): cc:%s dir:%s mc:%s time:%s bytes:%d" \
            " peek:%s" % (conndata.conncount, conndata.direction,
                          1, time.time(), len(str_response), repr(str_response[0:24])))
        #self.log.debug("HTTP.forward_s2c: %s" %(str_response))
        self.destination.shutdown(socket.SHUT_RD)
        self.source.shutdown(socket.SHUT_WR)

    def flip_image(self, imagein):
        outstr = ""
        outfile = StringIO.StringIO(outstr)
        img = Image.open(StringIO.StringIO(imagein))                            
        out = img.transpose(Image.ROTATE_180)                                                
        out.save(outfile, img.format)
        return outfile.getvalue()
    
class HTTPException(Exception):
    # Subclasses that define an __init__ must call Exception.__init__
    # or define self.args.  Otherwise, str() will fail.
    pass

class ImproperConnectionState(HTTPException):
    pass

class CannotSendRequest(ImproperConnectionState):
    pass

class CannotSendHeader(ImproperConnectionState):
    pass

class ResponseNotReady(ImproperConnectionState):
    pass

class BadStatusLine(HTTPException):
    def __init__(self, line):
        self.args = line,
        self.line = line


class IncompleteRead(HTTPException):
    def __init__(self, partial, expected=None):
        self.args = partial,
        self.partial = partial
        self.expected = expected
    def __repr__(self):
        if self.expected is not None:
            e = ', %i more expected' % self.expected
        else:
            e = ''
        return 'IncompleteRead(%i bytes read%s)' % (len(self.partial), e)
    def __str__(self):
        return repr(self)
    

class HTTPRequest:
    def __init__(self, sock):
        self.msg = None
        self.fp = sock.makefile('rb', 0)
        self.command = ""
        self.path = ""
        self.request_version = ""
        self.log = logging.getLogger("mallorymain")
        self.default_request_version = "HTTP/0.9"
        self.request_version = (0, 0)
        self.headers = None
        self.body = ""
        
        
       
    def __str__(self):        
        request_line = "%s %s %s\r\n" \
                    % (self.command, self.path, self.request_version)
                           
        request = request_line + str(self.headers)
        
        if self.body:
            request += "\r\n"
            request += self.body
        else:
            request += "\r\n\r\n"
            
        return request
    def toDict(self):
        return {"command" : self.command, "path":self.path, "request_version":
        self.request_version, "headers":self.headers.dict, "body": self.body}
    
    def _quote_html(self, html):
        return html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    def send_error(self, code, message=None):
        """Send and log an error reply.

        Arguments are the error code, and a detailed message.
        The detailed message defaults to the short entry matching the
        response code.

        This sends an error response (so it must be called before any
        output has been generated), logs the error, and finally sends
        a piece of HTML explaining the error to the user.

        """
        try:
            short, long = self.responses[code]
        except KeyError:
            short, long = '???', '???'
        if message is None:
            message = short
        explain = long
        self.log_error("code %d, message %s", code, message)
        # using _quote_html to prevent Cross Site Scripting attacks (see bug #1100201)
        content = (self.error_message_format %
                   {'code': code, 'message': self._quote_html(message), 'explain': explain})
        self.send_response(code, message)
        self.send_header("Content-Type", self.error_content_type)
        self.send_header('Connection', 'close')
        self.end_headers()
        if self.command != 'HEAD' and code >= 200 and code not in (204, 304):
            self.wfile.write(content)

    
    def begin(self):        
        self.raw_requestline = self.fp.readline()
        self.parse_request()
        self.log.info("HTTPRequest: %s : %s : %s" % \
                      (self.request_version, self.command, self.path))
        
    def parse_request(self):
        """Parse a request (internal).

        The request should be stored in self.raw_requestline; the results
        are in self.command, self.path, self.request_version and
        self.headers.

        Return True for success, False for failure; on failure, an
        error is sent back.

        """
        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        self.close_connection = 1
        requestline = self.raw_requestline
        if requestline[-2:] == '\r\n':
            requestline = requestline[:-2]
        elif requestline[-1:] == '\n':
            requestline = requestline[:-1]
        self.requestline = requestline
        words = requestline.split()
        if len(words) == 3:
            [command, path, version] = words
            if version[:5] != 'HTTP/':
                self.send_error(400, "Bad request version (%r)" % version)
                return False
            try:
                base_version_number = version.split('/', 1)[1]
                version_number = base_version_number.split(".")
                # RFC 2145 section 3.1 says there can be only one "." and
                #   - major and minor numbers MUST be treated as
                #      separate integers;
                #   - HTTP/2.4 is a lower version than HTTP/2.13, which in
                #      turn is lower than HTTP/12.3;
                #   - Leading zeros MUST be ignored by recipients.
                if len(version_number) != 2:
                    raise ValueError
                version_number = int(version_number[0]), int(version_number[1])
                self.request_version = version_number
            except (ValueError, IndexError):
                self.send_error(400, "Bad request version (%r)" % version)
                return False
            #
            # Mallory is a very liberal proxy and is accepting of ideals that
            # others might reject
            #
            # if version_number >= (1, 1) and self.protocol_version >= "HTTP/1.1":
            #    self.close_connection = 0
            # if version_number >= (2, 0):
            #    self.send_error(505,
            #              "Invalid HTTP Version (%s)" % base_version_number)
            #    return False
            
            
        elif len(words) == 2:
            [command, path] = words
            self.close_connection = 1
            if command != 'GET':
                self.send_error(400,
                                "Bad HTTP/0.9 request type (%r)" % command)
                return False
        elif not words:
            return False
        else:
            self.send_error(400, "Bad request syntax (%r)" % requestline)
            return False
        self.command, self.path, self.request_version = command, path, version        
        
        # Examine the headers and look for a Connection directive
        self.headers = HTTPMessage(self.fp, 0)
        
        # TODO: We need better support of the message body here. Currently
        # it is not really interpreted at all. This will be problematic for
        # multi-part form posts.  
        if self.command == "POST": 
            if self.headers["Content-Length"]:
                self.body = self.fp.read(int(self.headers["Content-Length"]))
        
class HTTPResponse:

    # strict: If true, raise BadStatusLine if the status line can't be
    # parsed as a valid HTTP/1.0 or 1.1 status line.  By default it is
    # false because it prevents clients from talking to HTTP/0.9
    # servers.  Note that a response with a sufficiently corrupted
    # status line will look like an HTTP/0.9 response.

    # See RFC 2616 sec 19.6 and RFC 1945 sec 6 for details.

    def __init__(self, sock, debuglevel=1, strict=0, method=None):
        self.fp = sock.makefile('rb', 0)
        self.debuglevel = debuglevel
        self.strict = strict
        self._method = method
        self.log = logging.getLogger("mallorymain")
        #Body
        self.dirty_body = None
        self.clean_body = None
        #Headers
        self.msg = None

        # from the Status-Line of the response
        self.version = _UNKNOWN # HTTP-Version
        self.status = _UNKNOWN  # Status-Code
        self.reason = _UNKNOWN  # Reason-Phrase

        self.chunked = _UNKNOWN         # is "chunked" being used?
        self.chunk_left = _UNKNOWN      # bytes left to read in current chunk
        self.length = _UNKNOWN          # number of bytes left in response
        self.will_close = _UNKNOWN      # conn will close at end of response

    def _read_status(self):
        # Initialize with Simple-Response defaults
        line = self.fp.readline()
        if self.debuglevel > 1:
            self.log.debug("reply: %s" % repr(line))
            
        if not line:
            # Presumably, the server closed the connection before
            # sending a valid response.
            raise BadStatusLine(line)
        try:
            [version, status, reason] = line.split(None, 2)
        except ValueError:
            try:
                [version, status] = line.split(None, 1)
                reason = ""
            except ValueError:
                # empty version will cause next test to fail and status
                # will be treated as 0.9 response.
                version = ""
        if not version.startswith('HTTP/'):
            if self.strict:
                self.close()
                raise BadStatusLine(line)
            else:
                # assume it's a Simple-Response from an 0.9 server
                self.fp = LineAndFileWrapper(line, self.fp)
                return "HTTP/0.9", 200, ""

        # The status code is a three-digit number
        try:
            status = int(status)
            if status < 100 or status > 999:
                raise BadStatusLine(line)
        except ValueError:
            raise BadStatusLine(line)
        return version, status, reason

    def begin(self):
        if self.msg is not None:
            # we've already started reading the response
            return

        # read until we get a non-100 response
        while True:
            version, status, reason = self._read_status()
            if status != CONTINUE:
                break
            # skip the header from the 100 response
            while True:
                skip = self.fp.readline().strip()
                if not skip:
                    break
                if self.debuglevel > 1:
                    print "header:", skip

        self.status = status
        self.reason = reason.strip()
        if version == 'HTTP/1.0':
            self.version = 10
        elif version.startswith('HTTP/1.'):
            self.version = 11   # use HTTP/1.1 code for HTTP/1.x where x>=1
        elif version == 'HTTP/0.9':
            self.version = 9
        else:
            #raise UnknownProtocol(version)
            print "Things are going downhill fast my dear."

        if self.version == 9:
            self.length = None
            self.chunked = 0
            self.will_close = 1
            self.msg = HTTPMessage(StringIO.StringIO())
            return

        self.msg = HTTPMessage(self.fp, 0)
        if self.debuglevel > 1:
            for hdr in self.msg.headers:
                print "header:", hdr,

        # don't let the msg keep an fp
        self.msg.fp = None

        # are we using the chunked-style of transfer encoding?
        tr_enc = self.msg.getheader('transfer-encoding')
        if tr_enc and tr_enc.lower() == "chunked":
            self.chunked = 1
            self.chunk_left = None
        else:
            self.chunked = 0

        # will the connection close at the end of the response?
        self.will_close = self._check_close()

        # do we have a Content-Length?
        # NOTE: RFC 2616, S4.4, #3 says we ignore this if tr_enc is "chunked"
        length = self.msg.getheader('content-length')
        if length and not self.chunked:
            try:
                self.length = int(length)
            except ValueError:
                self.length = None
            else:
                if self.length < 0:  # ignore nonsensical negative lengths
                    self.length = None
        else:
            self.length = None

        # does the body have a fixed length? (of zero)
        if (status == NO_CONTENT or status == NOT_MODIFIED or
            100 <= status < 200 or      # 1xx codes
            self._method == 'HEAD'):
            self.length = 0

        # if the connection remains open, and we aren't using chunked, and
        # a content-length was not provided, then assume that the connection
        # WILL close.
        if not self.will_close and \
           not self.chunked and \
           self.length is None:
            self.will_close = 1

    def _check_close(self):
        conn = self.msg.getheader('connection')
        if self.version == 11:
            # An HTTP/1.1 proxy is assumed to stay open unless
            # explicitly closed.
            conn = self.msg.getheader('connection')
            if conn and "close" in conn.lower():
                return True
            return False

        # Some HTTP/1.0 implementations have support for persistent
        # connections, using rules different than HTTP/1.1.

        # For older HTTP, Keep-Alive indicates persistent connection.
        if self.msg.getheader('keep-alive'):
            return False

        # At least Akamai returns a "Connection: Keep-Alive" header,
        # which was supposed to be sent by the client.
        if conn and "keep-alive" in conn.lower():
            return False

        # Proxy-Connection is a netscape hack.
        pconn = self.msg.getheader('proxy-connection')
        if pconn and "keep-alive" in pconn.lower():
            return False

        # otherwise, assume it will close
        return True

    def close(self):
        if self.fp:
            self.fp.close()
            self.fp = None

    def isclosed(self):
        # NOTE: it is possible that we will not ever call self.close(). This
        #       case occurs when will_close is TRUE, length is None, and we
        #       read up to the last byte, but NOT past it.
        #
        # IMPLIES: if will_close is FALSE, then self.close() will ALWAYS be
        #          called, meaning self.isclosed() is meaningful.
        return self.fp is None

    # XXX It would be nice to have readline and __iter__ for this, too.

    def read(self, amt=None):
        if self.fp is None:
            return ''

        if self.chunked:
            return self._read_chunked(amt)

        if amt is None:
            # unbounded read
            if self.length is None:
                s = self.fp.read()
            else:
                s = self._safe_read(self.length)
                self.length = 0
            self.close()        # we read everything
            return s

        if self.length is not None:
            if amt > self.length:
                # clip the read to the "end of response"
                amt = self.length

        # we do not use _safe_read() here because this may be a .will_close
        # connection, and the user is reading more bytes than will be provided
        # (for example, reading in 1k chunks)
        s = self.fp.read(amt)
        if self.length is not None:
            self.length -= len(s)
            if not self.length:
                self.close()
        return s

    def _read_chunked(self, amt):
        assert self.chunked != _UNKNOWN
        chunk_left = self.chunk_left
        value = []
        while True:
            if chunk_left is None:
                line = self.fp.readline()
                i = line.find(';')
                if i >= 0:
                    line = line[:i] # strip chunk-extensions
                try:
                    chunk_left = int(line, 16)
                except ValueError:
                    # close the connection as protocol synchronisation is
                    # probably lost
                    self.close()
                    raise IncompleteRead(''.join(value))
                if chunk_left == 0:
                    break
            if amt is None:
                value.append(self._safe_read(chunk_left))
            elif amt < chunk_left:
                value.append(self._safe_read(amt))
                self.chunk_left = chunk_left - amt
                return ''.join(value)
            elif amt == chunk_left:
                value.append(self._safe_read(amt))
                self._safe_read(2)  # toss the CRLF at the end of the chunk
                self.chunk_left = None
                return ''.join(value)
            else:
                value.append(self._safe_read(chunk_left))
                amt -= chunk_left

            # we read the whole chunk, get another
            self._safe_read(2)      # toss the CRLF at the end of the chunk
            chunk_left = None

        # read and discard trailer up to the CRLF terminator
        ### note: we shouldn't have any trailers!
        while True:
            line = self.fp.readline()
            if not line:
                # a vanishingly small number of sites EOF without
                # sending the trailer
                break
            if line == '\r\n':
                break

        # we read everything; close the "file"
        self.close()

        return ''.join(value)

    def _safe_read(self, amt):
        """Read the number of bytes requested, compensating for partial reads.

        Normally, we have a blocking socket, but a read() can be interrupted
        by a signal (resulting in a partial read).

        Note that we cannot distinguish between EOF and an interrupt when zero
        bytes have been read. IncompleteRead() will be raised in this
        situation.

        This function should be used when <amt> bytes "should" be present for
        reading. If the bytes are truly not available (due to EOF), then the
        IncompleteRead exception can be used to detect the problem.
        """
        s = []
        while amt > 0:
            chunk = self.fp.read(min(amt, MAXAMOUNT))
            if not chunk:
                raise IncompleteRead(''.join(s), amt)
            s.append(chunk)
            amt -= len(chunk)
        return ''.join(s)

    def getheader(self, name, default=None):
        if self.msg is None:
            raise ResponseNotReady()
        return self.msg.getheader(name, default)

    def getheaders(self):
        """Return list of (header, value) tuples."""
        if self.msg is None:
            raise ResponseNotReady()
        return self.msg.items()
  
    def toDict(self):
        return {"status" : self.status, "reason":self.reason, 
                "version": self.version, "msg":self.msg.dict, 
                "body":self.body, "clean_body":self.clean_body, "TEST":"TEST"}
 
class LineAndFileWrapper:
    """A limited file-like object for HTTP/0.9 responses."""

    # The status-line parsing code calls readline(), which normally
    # get the HTTP status line.  For a 0.9 response, however, this is
    # actually the first line of the body!  Clients need to get a
    # readable file object that contains that line.

    def __init__(self, line, file):
        self._line = line
        self._file = file
        self._line_consumed = 0
        self._line_offset = 0
        self._line_left = len(line)

    def __getattr__(self, attr):
        return getattr(self._file, attr)

    def _done(self):
        # called when the last byte is read from the line.  After the
        # call, all read methods are delegated to the underlying file
        # object.
        self._line_consumed = 1
        self.read = self._file.read
        self.readline = self._file.readline
        self.readlines = self._file.readlines

    def read(self, amt=None):
        if self._line_consumed:
            return self._file.read(amt)
        assert self._line_left
        if amt is None or amt > self._line_left:
            s = self._line[self._line_offset:]
            self._done()
            if amt is None:
                return s + self._file.read()
            else:
                return s + self._file.read(amt - len(s))
        else:
            assert amt <= self._line_left
            i = self._line_offset
            j = i + amt
            s = self._line[i:j]
            self._line_offset = j
            self._line_left -= amt
            if self._line_left == 0:
                self._done()
            return s

    def readline(self):
        if self._line_consumed:
            return self._file.readline()
        assert self._line_left
        s = self._line[self._line_offset:]
        self._done()
        return s

    def readlines(self, size=None):
        if self._line_consumed:
            return self._file.readlines(size)
        assert self._line_left
        L = [self._line[self._line_offset:]]
        self._done()
        if size is None:
            return L + self._file.readlines()
        else:
            return L + self._file.readlines(size)

     
class HTTPMessage(mimetools.Message):

    def addheader(self, key, value):
        """Add header for field key handling repeats."""
        prev = self.dict.get(key)
        if prev is None:
            self.dict[key] = value
        else:
            combined = ", ".join((prev, value))
            self.dict[key] = combined

    def addcontinue(self, key, more):
        """Add more field data from a continuation line."""
        prev = self.dict[key]
        self.dict[key] = prev + "\n " + more
    
    def toDict(self):
        return self.dict
    
    def readheaders(self):
        """Read header lines.

        Read header lines up to the entirely blank line that terminates them.
        The (normally blank) line that ends the headers is skipped, but not
        included in the returned list.  If a non-header line ends the headers,
        (which is an error), an attempt is made to backspace over it; it is
        never included in the returned list.

        The variable self.status is set to the empty string if all went well,
        otherwise it is an error message.  The variable self.headers is a
        completely uninterpreted list of lines contained in the header (so
        printing them will reproduce the header exactly as it appears in the
        file).

        If multiple header fields with the same name occur, they are combined
        according to the rules in RFC 2616 sec 4.2:

        Appending each subsequent field-value to the first, each separated
        by a comma. The order in which header fields with the same field-name
        are received is significant to the interpretation of the combined
        field value.
        """
        # XXX The implementation overrides the readheaders() method of
        # rfc822.Message.  The base class design isn't amenable to
        # customized behavior here so the method here is a copy of the
        # base class code with a few small changes.

        self.dict = {}
        self.unixfrom = ''
        self.headers = hlist = []
        self.status = ''
        headerseen = ""
        firstline = 1
        startofline = unread = tell = None
        if hasattr(self.fp, 'unread'):
            unread = self.fp.unread
        elif self.seekable:
            tell = self.fp.tell
        while True:
            if tell:
                try:
                    startofline = tell()
                except IOError:
                    startofline = tell = None
                    self.seekable = 0
            line = self.fp.readline()
            if not line:
                self.status = 'EOF in headers'
                break
            # Skip unix From name time lines
            if firstline and line.startswith('From '):
                self.unixfrom = self.unixfrom + line
                continue
            firstline = 0
            if headerseen and line[0] in ' \t':
                # XXX Not sure if continuation lines are handled properly
                # for http and/or for repeating headers
                # It's a continuation line.
                hlist.append(line)
                self.addcontinue(headerseen, line.strip())
                continue
            elif self.iscomment(line):
                # It's a comment.  Ignore it.
                continue
            elif self.islast(line):
                # Note! No pushback here!  The delimiter line gets eaten.
                break
            headerseen = self.isheader(line)
            if headerseen:
                # It's a legal header line, save it.
                hlist.append(line)
                self.addheader(headerseen, line[len(headerseen)+1:].strip())
                continue
            else:
                # It's not a header line; throw it back and stop here.
                if not self.dict:
                    self.status = 'No headers'
                else:
                    self.status = 'Non-header line where header expected'
                # Try to undo the read.
                if unread:
                    unread(line)
                elif tell:
                    self.fp.seek(startofline)
                else:
                    self.status = self.status + '; bad seek'
                break
