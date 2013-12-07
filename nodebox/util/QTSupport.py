import os
from tempfile import mkstemp
from Foundation import NSNumber
from AppKit import NSImage, NSApplication, NSColor, NSData, NSBitmapImageRep, NSJPEGFileType
from Quartz import *
from LaunchServices import *
from QTKit import QTMovie, QTDataReference, QTMovieFileNameAttribute, QTMakeTimeRange, QTMakeTime, QTMovieEditableAttribute, QTAddImageCodecType, QTMovieFlatten

class Movie(object):
    actual_movie = None
    def __init__(self, fname, frames=60, fps=30, loop=0):
        basename, ext = fname.rsplit('.',1)
        if ext.lower() == 'mov':
            self.actual_movie = AVMovie(fname, frames=frames, fps=fps)
        elif ext.lower() == 'gif':
            self.actual_movie = GIFMovie(fname, frames=frames, fps=fps, loop=loop)
        else:
            raise 'unrecognized movie format: %s' % ext

    def add(self, canvas_or_context):
        self.actual_movie.add(canvas_or_context)

    def save(self):
        self.actual_movie.save()

class GIFMovie(object):
    def __init__(self, fname, frames, fps, loop):
        if os.path.exists(fname):
            os.remove(fname)
        self.frame = 1
        self.frames = frames
        self.fname = fname
        self.tmpfname = None
        self.firstFrame = True
        self.movie = None
        self.fps = fps
        self.loop = loop

    def add(self, canvas_or_context):
        image = canvas_or_context._nsImage
        if not self.movie:
            self.movie = AnimatedGif.alloc().initWithFile_size_fps_loop_(
               self.fname, image.size(), self.fps, self.loop
            )
        self.movie.addFrame_(image)

    def save(self):
        self.movie.closeFile()


class CGGIFMovie(object):
    def __init__(self, fname, frames, fps):
        if os.path.exists(fname):
            os.remove(fname)
        self.frame = 1
        self.fname = fname
        self.tmpfname = None
        self.firstFrame = True
        self.movie = None
        self.fps = fps
        self._delay = 1.0/fps

        self.frameProps = {kCGImagePropertyGIFDictionary:{kCGImagePropertyGIFDelayTime:self._delay}}
        # self.gifProps = {kCGImagePropertyGIFDictionary:{kCGImagePropertyGIFLoopCount:0}}
        # self.gifProps = {kCGImagePropertyGIFDictionary:{}}
        self.gifProps = {kCGImagePropertyGIFDictionary:{kCGImagePropertyGIFHasGlobalColorMap:False}}
        
        
        self.movie = CGImageDestinationCreateWithURL(
            NSURL.fileURLWithPath_(self.fname), kUTTypeGIF,
            frames, # number of images in this GIF
            None
        )

    def add(self, canvas_or_context):
        image = canvas_or_context._nsImage
        cgFrame, dims = image.CGImageForProposedRect_context_hints_(None, NSGraphicsContext.currentContext(), None)
        props = dict(self.frameProps)
        props.update({kCGImagePropertyGIFImageColorMap:clut.encodeRawColorTable()})
        CGImageDestinationAddImage(self.movie, cgFrame, props)

    def save(self):
        CGImageDestinationSetProperties(self.movie, self.gifProps)
        if CGImageDestinationFinalize(self.movie):
            NSLog("success")
        else:
            NSLog("failure")
        self.movie = None
        
class AVMovie(object):

    def __init__(self, fname, frames, fps):
        if os.path.exists(fname):
            os.remove(fname)
        self.frame = 1
        self.fname = fname
        self.tmpfname = None
        self.firstFrame = True
        self.movie = None
        self.fps = fps
        self._time = QTMakeTime(int(600/self.fps), 600)
        
    def add(self, canvas_or_context):
        if self.movie is None:
            # The first frame will be written to a temporary png file,
            # then opened as a movie file, then saved again as a movie.
            handle, self.tmpfname = mkstemp('.tiff')
            canvas_or_context.save(self.tmpfname)
            try:
                movie, err = QTMovie.movieWithFile_error_(self.tmpfname, None)
                movie.setAttribute_forKey_(NSNumber.numberWithBool_(True), QTMovieEditableAttribute)
                range = QTMakeTimeRange(QTMakeTime(0,600), movie.duration())
                movie.scaleSegment_newDuration_(range, self._time)
                if err is not None:
                    raise str(err)
                movie.writeToFile_withAttributes_(self.fname, {QTMovieFlatten:True})
                self.movie, err = QTMovie.movieWithFile_error_(self.fname, None)
                self.movie.setAttribute_forKey_(NSNumber.numberWithBool_(True), QTMovieEditableAttribute)
                if err is not None: raise str(err)
                self.imageTrack = self.movie.tracks()[0]
            finally:
                os.remove(self.tmpfname)
        else:
            try:
                canvas_or_context.save(self.tmpfname)
                img = NSImage.alloc().initByReferencingFile_(self.tmpfname)
                self.imageTrack.addImage_forDuration_withAttributes_(img, self._time, {QTAddImageCodecType:'tiff'})
            finally:
                try:
                    os.remove(self.tmpfname)
                except OSError: pass
        self.frame += 1
                
    def save(self):
        self.movie.updateMovieFile()
        
def test():
    import sys
    sys.path.insert(0, '../..')
    from nodebox.graphics import Canvas, Context
    from math import sin

    NSApplication.sharedApplication().activateIgnoringOtherApps_(0)
    w, h = 500, 300
    m = Movie("xx3.mov")
    for i in range(200):
        print "Frame", i
        ctx = Context()
        ctx.size(w, h)
        ctx.rect(100.0+sin(i/10.0)*100.0,i/2.0,100,100)
        ctx.text(i, 0, 200)
        m.add(ctx)
    m.save()
    
if __name__=='__main__':
    test()
