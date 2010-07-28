 # Experimental handling of HTTP protocol. THIS IS A PROTOTYPE
    if connData['direction'] == "s2c" and connData['serverPort'] == 80:
        print "[*] forward(): interceptor:" + str(connData)
        
        accumulator = ""
        httpheader = ""
        httpheader_arr = []
        httpbody = ""
        httpheader_len = 0
        content_length = 0
        content_encoding = ""
        is_image = False
        
        while string:
            print "[*] forward(): http interceptor: source.recv()"
            string = source.recv(8192)
            accumulator = accumulator + string
                           
            if string:              
                print "[*] forward(): http interceptor: finished source.recv()"
                
                
                #destination.sendall(string)
                
                # BEGIN EVIL HACK
                
                # Look for the HTTP header
                headerpos = accumulator.find("\r\n\r\n")
                
                if headerpos > -1 and len(httpheader) == 0:                    
                    httpheader = accumulator[0:headerpos]
                    print httpheader
                    httpheader_arr = httpheader.split("\r\n")                                
                    for header in httpheader_arr:
                        if header.find("Content-Length") > -1:
                            (name, value) = header.split(" ")
                            content_length = int(value)
                        if header.find("Content-Encoding") > -1:
                            print "[*] forward(): http interceptor: content_" \
                                "encoding: %s" % (header)
                            (name, value) = header.split(" ")
                            content_encoding = value 
                            
                        if header.find("Content-Type") > -1 and header.find("image") > 1:
                            print "FOUND IMAGE!!!!\r\n"
                            is_image = True
                            
                                         
                    print "[*] forward(): http interceptor: found end of HTTP" \
                        " header. Content length is: %d" % (content_length)
                    httpheader_len = headerpos              

                # hack. track actual bytes in the future. avoid len per recv
                # sub four for \r\n
                if httpheader_len > 0:
                    contentbytes = len(accumulator) - 4 - httpheader_len 
                    print "[*] forward(): http interceptor: content so far " \
                         "%d" % (contentbytes)
                         
                    # we have the data!!!
                    if contentbytes == content_length:
                        print"[*] forward(): http interceptor: GOOD TO GO!"
                        
                        httpbody = accumulator[headerpos+4:len(accumulator)]
                        
                        if content_encoding == "gzip":
                            
                            httpbody_gzip = gzip.GzipFile("", "rb", 9, 
                                                    StringIO.StringIO(httpbody))
                            httpbody_decompress = httpbody_gzip.read()
                            httpbody =  httpbody_decompress
                        
                        httpresponse = accumulator
                        
                        # Lets roll it    
                        if is_image:
                            outstr = ""
                            outfile = StringIO.StringIO(outstr)
                            img = Image.open(StringIO.StringIO(httpbody))                            
                            out = img.transpose(Image.ROTATE_180)                                                
                            out.save(outfile, img.format)
                            imagebytes = outfile.getvalue()
                            httpresponse = httpheader + "\r\n\r\n" + imagebytes
                            print "\r\n\r\nGOT IMAGE. FORMAT:\r\n\r\n" + img.format
                        
                        print "[*] forward(): http_interceptor: SENDING CONTENT"
                        destination.sendall(httpresponse)    
                        source.shutdown(socket.SHUT_RD)
                        destination.shutdown(socket.SHUT_WR)                            
                        break
                        #print data
                        
                        #print accumulator
                        #print repr(httpbody)
                        
                          
                        #destination.sendall("HTTP/1.1 200 OK\r\n\r\n<html><body><div><bold>In your data.</bold></body></html>\r\n\r\n")
                        
                        # we know when we are finished
                    
                        #httpbody_unzip = zlib.decompress(httpbody,-15)
                        #print httpbody_unzip
                
                    #for header in httpheader_arr:
                        #if header.find("Content-Length"):
                            #foo = 1
                            #print header
                            
                        
                        
                # END EVIL HACK               
                
                   
                dbConn.qFlow.put((connData['connCount'], connData['direction'],\
                                msgCnt, time.time(), repr(string)))
    
                print "[*] forward(): http interceptor: " \
                    "reading server response: cc:%s dir:%s mc:%s time:%s" \
                    " bytes:%d peek:%s" % \
                    (connData['connCount'], connData['direction'], msgCnt, \
                      time.time(), len(string), string[0:24])
            else:
                print "[*] forward(): interceptor: no more data. shutting down"
                
                if debug == 1:
                    print "[*] forward(): interceptor: [%s] CLOSE" % connData['direction']
                    print connData
            
                try:
                    source.shutdown(socket.SHUT_RD)
                    print "[*] forward(): interceptor package: sending \"response\""      
                    #destination.sendall("HTTP/1.1 200 OK\r\n\r\n<html><body><div><bold>In your data.</bold></body></html>\r\n\r\n")
                    #destination.sendall(accumulator)
                    destination.shutdown(socket.SHUT_WR)                    
                    return
                except:
                    return
            
            
            
                    # Destination in this case is the client. Send them the hacked up msg.                    
                    # End Experimental PROTOTYPE
                else:                         