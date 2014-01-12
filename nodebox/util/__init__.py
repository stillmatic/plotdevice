import re
from AppKit import NSFontManager, NSFont, NSMacOSRomanStringEncoding
from random import choice

__all__ = ('grid', 'random', 'choice', 'files', 'fonts', 'autotext', '_copy_attr', '_copy_attrs')

### Utilities ###

def grid(cols, rows, colSize=1, rowSize=1, shuffled = False):
    """Returns an iterator that contains coordinate tuples.
    
    The grid can be used to quickly create grid-like structures. A common way to use them is:
        for x, y in grid(10,10,12,12):
            rect(x,y, 10,10)
    """
    # Prefer using generators.
    rowRange = xrange(int(rows))
    colRange = xrange(int(cols))
    # Shuffled needs a real list, though.
    if (shuffled):
        rowRange = list(rowRange)
        colRange = list(colRange)
        shuffle(rowRange)
        shuffle(colRange)
    for y in rowRange:
        for x in colRange:
            yield (x*colSize,y*rowSize)

def random(v1=None, v2=None):
    """Returns a random value.
    
    This function does a lot of things depending on the parameters:
    - If one or more floats is given, the random value will be a float.
    - If all values are ints, the random value will be an integer.
    
    - If one value is given, random returns a value from 0 to the given value.
      This value is not inclusive.
    - If two values are given, random returns a value between the two; if two
      integers are given, the two boundaries are inclusive.
    """
    import random
    if v1 != None and v2 == None: # One value means 0 -> v1
        if isinstance(v1, float):
            return random.random() * v1
        else:
            return int(random.random() * v1)
    elif v1 != None and v2 != None: # v1 -> v2
        if isinstance(v1, float) or isinstance(v2, float):
            start = min(v1, v2)
            end = max(v1, v2)
            return start + random.random() * (end-start)
        else:
            start = min(v1, v2)
            end = max(v1, v2) + 1
            return int(start + random.random() * (end-start))
    else: # No values means 0.0 -> 1.0
        return random.random()

def files(path="*"):
    """Returns a list of files.
    
    You can use wildcards to specify which files to pick, e.g.
        f = files('*.gif')
    """
    from glob import glob
    if not type(path)==unicode:
        path = path.decode('utf-8')
    return glob(path)

def fonts(like=None, western=True):
    """Returns a list of all fonts installed on the system (with filtering capabilities)

    If `like` is a string, only fonts whose names contain those characters will be returned.

    If `western` is True (the default), fonts with non-western character sets will be omitted.
    If False, only non-western fonts will be returned.
    """
    def in_region(fontname):
        # always filter out the system menu fonts
        if fontname.startswith('.'):
            return False
        # filter based on region preference
        enc = NSFont.fontWithName_size_(fontname, 12).mostCompatibleStringEncoding()
        if western: return enc==NSMacOSRomanStringEncoding
        else: return enc!=NSMacOSRomanStringEncoding
    all_fonts = [f for f in NSFontManager.sharedFontManager().availableFonts() if in_region(f)]
    if like:
        return [name for name in all_fonts if like.lower() in name.lower()]
    return all_fonts

def autotext(sourceFile):
    from nodebox.util.kgp import KantGenerator
    k = KantGenerator(sourceFile)
    return k.output()

def _copy_attr(v):
    if v is None:
        return None
    elif hasattr(v, "copy"):
        return v.copy()
    elif isinstance(v, list):
        return list(v)
    elif isinstance(v, tuple):
        return tuple(v)
    elif isinstance(v, (int, str, unicode, float, bool, long)):
        return v
    else:
        raise NodeBoxError, "Don't know how to copy '%s'." % v

def _copy_attrs(source, target, attrs):
    for attr in attrs:
        setattr(target, attr, _copy_attr(getattr(source, attr)))
