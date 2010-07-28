import config
import Image
import StringIO
from base import Base

class ImageFlip (Base):
    def __init__(self, rules = [], config = config.Config()):
        Base.__init__(self)
        self.persistent = 0

    def do (self, **kwargs):
        #Check to see if this came of the dameon we expected
        if kwargs['event'] == "HTTP:s2c":
            response = kwargs['data']
            for header in response.msg.headers:
                if "Content-Type" in header and "image" in header:
                    try:
                        response.clean_body = self.flip_image(response.clean_body)
                    except:
                        pass
            kwargs['data'] = response
        return kwargs
    
    def flip_image(self, imagein):
        outstr = ""
        outfile = StringIO.StringIO(outstr)
        img = Image.open(StringIO.StringIO(imagein))                            
        out = img.transpose(Image.ROTATE_180)                                                
        out.save(outfile, img.format)
        return outfile.getvalue()