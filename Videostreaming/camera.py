#camera.py# import the necessary packages
import cv2# defining face detector

ds_factor=1

class VideoCamera(object):
    def __init__(self, port, focus=110):
        self.startfocus = 50
        #capturing video
        self.video = cv2.VideoCapture(port)

        #self.video.set(3, 2592)
        #self.video.set(4, 1944)

        self.video.set(cv2.CAP_PROP_FOCUS, focus)

        self.video.set(3, 720)
        self.video.set(4, 480)

        
        #self.video.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)

        #self.video.set(cv2.CAP_MODE_GRAY)
        
        #self.video.set(cv2.CAP_PROP_EXPOSURE, 2000)
        #self.video.set(cv2.CAP_PROP_CONTRAST, 10) 

        #self.video.set(cv2.CAP_PROP_AUTOFOCUS , 0)
        
        #self.video.set(cv2.CAP_PROP_AUTO_WB, 0)
        
        #self.video.set(cv2.CAP_PROP_WB_TEMPERATURE, 4200)
        #self.video.set(cv2.CAP_PROP_BRIGHTNESS, 10)
        #self.video.set(cv2.CAP_PROP_AUTO_WB, 30)

        #self.video.set(cv2.CAP_PROP_FPS, 15)
        #print(self.video.get(cv2.CAP_PROP_EXPOSURE))
    
    def __del__(self):
        #releasing camera
        self.video.release()
        
    def get_frame(self):
        #self.video.set(cv2.CAP_PROP_FOCUS, self.startfocus)
        #self.video.set(cv2.CAP_PROP_CONTRAST, self.startfocus)
        #print(self.video.get(cv2.CAP_PROP_FOCUS))


       #extracting frames
        ret, frame = self.video.read()
        frame=cv2.resize(frame,None,fx=ds_factor,fy=ds_factor,interpolation=cv2.INTER_AREA)                    
        #gray=cv2.cvtColor(image ,cv2.COLOR_BGR2GRAY)
        ret, jpeg = cv2.imencode('.png', frame)

        self.startfocus += 1
        return jpeg.tobytes()