#!/usr/bin/env python

# TermLayout v0.11 (c) 2014 Silas S. Brown

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re, unicodedata, os, sys

class ANSIfiedText:
    "Small piece of text with its own ANSI attributes, which is self-contained so can be moved around into other contexts as needed.  Should not change attributes mid-text though."
    def __init__(self,txt,attrList):
        "text, and ordered list of ANSI attribute sequences.  If any of the attribute sequences change colour, only the last colour is kept.  After this, colour is thrown away if it's black or white, since this is often used for terminal backgrounds." # TODO: customise which colours are thrown away?
        self.txt = txt
        self.attrList = [] ; prevColour = None
        for a in attrList:
            if any(a in ("\x1b[%dm"%i) for i in range(30,38)): # it's a colour change
                if prevColour:
                    self.attrList.remove(prevColour)
                    prevColour = None
                if a in ["\x1b[30m","\x1b[37m"]: continue # leave us as the terminal's 'normal' colour if we're supposed to be black or white
                prevColour = a
            self.attrList.append(a)
    def __repr__(self): return 'a(%s)' % repr(self.txt) # for debugging
    def printUsingState(self,curAttrList):
        "Returns the string needed to change any necessary ANSI codes and print this text, updating curAttrList in-place"
        ret = []
        if set(curAttrList) > set(self.attrList):
            # there's attributes out there we don't want
            ret.append("\x1b[0m") # reset the state
            ret += self.attrList # and print all our own
            while curAttrList: del curAttrList[0]
            for x in self.attrList: curAttrList.append(x)
        else:
            for a in self.attrList:
                if not a in curAttrList:
                    curAttrList.append(a)
                    ret.append(a)
        return "".join(ret) + self.txt
class ANSIfiedLineDrawing(ANSIfiedText):
    "Derivative of ANSIfiedText meant for simple ASCII art line drawing.  ANSI codes are substituted for the ASCII during draw, but internally the ASCII-only version is kept (so stripANSI below results in ASCII lines).  Use characters - | for lines, / \\ L J for corners, and T U ] [ + for intersections (U is upside-down T, and ] and [ are T's with the bargoing to left or right - sorry but it's only ASCII)."
    def printUsingState(self,curAttrList):
        oldTxt = self.txt
        self.txt = '\x1b(0' + str(self.txt).translate(ansiLineTable) + '\x1b(B'
        ret = ANSIfiedText.printUsingState(self,curAttrList)
        self.txt = oldTxt ; return ret
ansiLineTable = [chr(c) for c in range(256)]
for p,q in {'-':'q', '|':'x',
            '/':'l', '\\':'k', 'L':'m', 'J':'j',
            'T':'w', 'U':'v', '[':'t', ']':'u', '+':'n' }.items(): ansiLineTable[ord(p)]=q
ansiLineTable = "".join(ansiLineTable)
class ANSIfiedNewline:
    #"Since we don't have to care about ANSI attributes when outputting a newline, this will not try to change them"
    #def printUsingState(self,curAttrList): return "\n"
    "actually we'd better reset all ANSI attributes on each new line, for use with a pager like 'less'"
    def printUsingState(self,curAttrList):
        if curAttrList:
            while curAttrList: del curAttrList[0]
            return "\x1b[0m\n"
        else: return "\n"
class ANSIfiedSpacer:
    "A 'spacer' object that prints spaces without attributes, but does not bother to clear attributes that wouldn't show up on spaces anyway"
    def __init__(self,numSpaces=1): self.ns = numSpaces
    def __repr__(self): return 's(%d)' % self.ns # for debugging
    def printUsingState(self,curAttrList):
        ret = ""
        if "\x1b[4m" in curAttrList: # oops, underline is set - we don't want that for our spacer.  (TODO: check for background colours also, if adding them)
            ret = "\x1b[0m" # reset the state
            while curAttrList: del curAttrList[0]
        return ret + " "*self.ns
def ansifiedLineLen(atList):
    s = 0
    for a in atList:
        if hasattr(a,'ns'): s += a.ns
        elif hasattr(a,'txt'): s += widthOf(a.txt)
    return s
def mergeAnsifiedTexts(atList,stripANSI=False):
    "Assembles a complete list of ANSIfiedText objects for final output"
    curAttrList = [] ; ret = []
    for a in atList:
        if stripANSI and hasattr(a,'txt'):
            ret.append(a.txt)
        else: ret += a.printUsingState(curAttrList)
    if curAttrList: ret.append("\x1b[0m") # final reset
    return "".join(ret)
def mergeAnsifiedLines(atListList,stripANSI=False):
    "Assembles a complete list of lists of ANSIfiedText objects, one per line, for final output with newlines between.  Oblivious to the wrapping.  Strips trailing ANSIfiedSpacer objects at the end of each line."
    r = [] ; anl = ANSIfiedNewline() # 1 instance
    justHadBlankLine = False # collapse any mult. blanks
    for atList in atListList:
        for i in range(len(atList),-1,-1):
          if i==0 or not (atList[i-1].__class__ == ANSIfiedSpacer or not atList[i-1].txt.strip()): break
        if i:
            r += atList[:i] ; justHadBlankLine = False
        else:
            if justHadBlankLine: continue # no anl
            justHadBlankLine = True
        r.append(anl)
    return mergeAnsifiedTexts(r,stripANSI)

class Strut:
    def __init__(self,direction='x',length=0):
        self.direction = direction
        self.length = length ; self.width = 0
    def getSize(self,direction):
        if self.direction == direction: return self.length
        else: return self.width
    def padToSize(self,direction='x',desired=0,align='c',
                       absoluteMaximum = None):
        if self.direction == direction:
            self.length = max(desired,self.length)
        else: self.width = max(desired,self.width)
    def getLine(self,N):
        if self.direction=='x': numSpaces = self.length
        else: numSpaces = self.width
        if numSpaces: return [ANSIfiedSpacer(numSpaces)]
        else: return []
    def canSubstituteLineBreak(self): return True
    def isHardLineBreak(self): return False
    def __repr__(self): # for debugging
        r = 'S'+self.direction
        if self.length or self.width:
            r += "%d" % self.length
            if self.width: r += "(w%d)" % self.width
        return r
class StackingRectangle:
    def __init__(self,stackingDir='y',initItems=None,name=""):
        if not initItems: initItems = []
        self.items = initItems
        self.stackingDir = stackingDir
        self.name = name # for debugging & introspection
    def getSize(self,direction='x'):
        if direction==self.stackingDir: func = sum
        else:
            if not self.items: return 0
            func = max
        return func(i.getSize(direction)
                    for i in self.items)
    def padToSize(self,direction='x',desired=0,align='c',
                       absoluteMaximum = None):
        if direction == self.stackingDir:
            if desired:
                before,after = centreCalc(
                self.getSize(direction),desired,align)
                if before: self.items.insert(0,Strut(direction,before))
                if after: self.items.append(Strut(direction,after))
            # else we can't make it any bigger than the existing size, but anyway just check everything inside's "padded out" (so we can put 'x' and 'y' stacks together in any order without worrying about strict alternation).  E.g. a collection of cols is told "make all your rows as wide as your widest", so says "I'm cols not rows, but I can ask any collections of rows inside to make sure each of THEIR rows is as wide as the collection"
            for r in self.items:
                r.padToSize(direction,0,align,absoluteMaximum)
        else:
            if not desired: # make all the size of largest
                desired = self.getSize(direction)
                if absoluteMaximum: # if one item exceeds absoluteMaximum, don't make the others exceed it also
                    desired=min(desired, absoluteMaximum)
            for r in self.items:
                r.padToSize(direction,desired,align)
    def tabulate(self):
        "Pad the children of children as in a table.  Assumes each cell takes exactly 1 row or column and there are no borders except a gap between columns.  For more complex tables (borders, rowspan/colspan etc), please use an XYGrid instead, which automatically tabulates (although it's probably slower than the more simplistic approach used here)."
        rows = [i for i in self.items if not i.__class__ == Strut]
        numCols = max(len([c for c in r.items if not c.__class__ == Strut]) for r in rows) ; numRows = len(rows)
        if self.stackingDir=='y': colWidthDir='x'
        else: colWidthDir='y' # (and var names all wrong)
        def xy(x,y):
            its = rows[y].items ; i = 0
            while True:
                while i < len(its) and its[i].__class__ == Strut: i+=1
                if i == len(its): return Strut() # size 0
                if not x: return its[i]
                x -= 1 ; i+=1
        for colNo in xrange(numCols):
            wid = max(xy(colNo,r).getSize(colWidthDir) for r in xrange(numRows))
            if colNo < numCols-1 and colWidthDir=='x': wid += 1 # gap between cols
            for r in xrange(numRows): xy(colNo,r).padToSize(colWidthDir,wid,'top') # TODO: currently an XYGrid is used if we have align= or valign= , but we could probably get those attributes here (but would also need to make sure that any 'docs' contained in the cell have been padded using it)
        for rowNo in xrange(numRows):
            hi = max(xy(c,rowNo).getSize(self.stackingDir) for c in xrange(numCols))
            if rowNo < numRows-1 and self.stackingDir=='x': hi += 1 # gap between cols
            for c in xrange(numCols): xy(c,rowNo).padToSize(self.stackingDir,hi,'top') # TODO: alignment as above TODO (currently handled by XYGrid)
    def lineBreakAndPadLeading(self,maxSize,ourDirectionRunsFromEnd=False,orthogonalDirectionRunsFromEnd=False,baselineAlign='bottom'): # ( = 'right' for columns)
        "When processing a stack of lines (or, for vertical text, a bunch of columns), interprets hard line breaks, adds soft line breaks, and ensures all lines are consistent 'height' (or width if they are columns), using baselineAlign to align any that were out of place.  Flags: False,False for a StackingRectangle('y') containing StackingRectangle('x') lines with left-to-right top-to-bottom line wrapping; True,False for a StackingRectangle('x') containing StackingRectangle('y') columns when we want to wrap in columns from right to left (and top to bottom within each column; True,True would give bottom to top), etc.  It's assumed that all relevant immediate children are other StackingRectangles; if any of these have a direction the same as ours, we'll recurse on them."
        if ourDirectionRunsFromEnd: self.items.reverse()
        if self.stackingDir=='y': wrappingDir = 'x'
        else: wrappingDir = 'y'
        i = 0
        while i < len(self.items):
            if not self.items[i].__class__ == StackingRectangle:
                i += 1 ; continue
            if self.items[i].stackingDir == self.stackingDir:
                self.items[i].lineBreakAndPadLeading(maxSize,ourDirectionRunsFromEnd,orthogonalDirectionRunsFromEnd,baselineAlign)
                i += 1 ; continue
            if orthogonalDirectionRunsFromEnd:
                self.items[i].items.reverse()
            itemNo, breakAt, size = 0,None,0
            for ii in self.items[i].items:
                if ii.isHardLineBreak() or ii.canSubstituteLineBreak(): breakAt = itemNo
                size += ii.getSize(wrappingDir)
                if ii.isHardLineBreak() or (size > maxSize and (breakAt or itemNo)):
                    if breakAt or ii.isHardLineBreak():
                        self.items[i].items, newItems = self.items[i].items[:breakAt], self.items[i].items[breakAt+1:]
                        if not breakAt: self.items[i].items=[Strut(self.stackingDir,1)] # if a hard line-break left an empty line, make sure it has some height
                    else: self.items[i].items, newItems = self.items[i].items[:itemNo], self.items[i].items[itemNo:] # "emergency mode" for very long words - break just before the item we just looked at, even though no breakpoint
                    nsr = StackingRectangle(wrappingDir,name='continuation')
                    if orthogonalDirectionRunsFromEnd:
                        newItems.reverse() # undo damage
                    nsr.items = newItems
                    self.items.insert(i+1,nsr)
                    break
                itemNo += 1
            if orthogonalDirectionRunsFromEnd:
              self.items[i].items.reverse() # undo damage
            for ii in self.items[i].items[:]:
                if not ii.getSize(wrappingDir):
                    self.items[i].items.remove(ii) # (no point keeping 0-width spaces and things around once the line has been wrapped)
            self.items[i].padToSize(self.stackingDir,align=baselineAlign) # (if horizontal wrap, pad-Y makes sure all cols on the items[i] row are the same height; if vertical wrap, similar for width)
            for it in self.items[i].items: it.padToSize(wrappingDir) # (so any extra 'rows' we just added to those 'columns' are padded out as well)
            # note however that we DON'T pad our ROWS to size in wrappingDir (that's done separately if centering etc is desired)
            i += 1
        if ourDirectionRunsFromEnd: self.items.reverse()
    def getLines(self):
        "assumes all needed padding is already done"
        return [self.getLine(N) for N in range(self.getSize('y'))]
    def getLine(self,N):
        if self.stackingDir == 'x':
            return reduce(lambda a,b:a+b,
                       (i.getLine(N) for i in self.items))
        if N < 0: return []
        lNo = 0
        for r in self.items:
            l0,lNo = lNo,lNo+r.getSize('y')
            if lNo > N: return r.getLine(N-l0)
        return []
    def canSubstituteLineBreak(self):
        if not self.items: return False # empty container boxes are not necessarily valid line-break points
        return all(
           i.canSubstituteLineBreak() for i in self.items)
    def isHardLineBreak(self):
        items = [i for i in self.items if not i.__class__ == Strut]
        if not items: return False
        return all(i.isHardLineBreak() for i in items)
    def isConsistent(self,seenList=None): # for debugging
        if not seenList: seenList = []
        if self in seenList: return False
        seenList.append(self)
        return all(x.isConsistent(seenList) for x in self.items if x.__class__ == StackingRectangle)
    def __repr__(self): # for debugging
        if self.stackingDir=='x': r = 'cols'
        else: r = 'rows'
        if self.name: r += '('+self.name+')'
        return "%d %s %s" % (self.getSize(self.stackingDir),r,repr(self.items))
class XYGrid:
    def __init__(self,drawBorder):
        self.items = {} # (x,y) : ((colspan,rowspan),item)
        self.drawBorder = drawBorder
    def getNumRowsOrCols(self,axis):
        return max(k[axis]+v[0][axis] for k,v in self.items.iteritems())
    def getSizeOfRowOrCol(self,N,nEnd=None,direction='x'):
        "Returns the size of a particular row or column (or range of them), not including borders (except does include internal borders when returning a range)"
        # If there's a border of size 1, the amount of space a cell contributes to each of its columns is (cell size - (colspan-1)) / colspan, but taking care to ensure that surplus space is allocated if this does not result in an integer (TODO: this need be only the average and it doesn't have to contribute equally to all)
        spaceForBorder = (direction=='x') # TODO: or True if we want line borders in Y direction also
        if not nEnd: nEnd = N+1
        def contribOf(itemSize,span,makeUp):
            if spaceForBorder: itemSize += 1-span # subtract some which will be provided anyway by internal borders of other cells (and is added in below)
            each = int(itemSize/span)
            if makeUp: return itemSize-(each*(span-1))
            else: return each
        if direction=='x': axis = 0
        else: axis = 1
        if spaceForBorder: border = nEnd-N-1 # the internal borders in the range
        else: border = 0
        return border + sum(max([0]+[contribOf(v[1].getSize(direction),v[0][axis],n == k[axis]+v[0][axis]-1) for k,v in self.items.iteritems() if k[axis] <= n < k[axis]+v[0][axis]]) for n in xrange(N,nEnd))
    def getSize(self,direction='x'):
        if direction=='x': axis = 0
        else: axis = 1
        return self.getSizeOfRowOrCol(0,self.getNumRowsOrCols(axis),direction) # TODO: +2 if external borders
    def padToSize(self,direction='x',desired=0,align='c',
                       absoluteMaximum = None):
        "XYGrid itself doesn't pad - it expects to be placed in containers that deal with padding"
    def getLine(self,N):
        if N < 0: return []
        rowsSoFar = [0] # start line of table row N
        for row in xrange(self.getNumRowsOrCols(1)):
            rowsSoFar.append(self.getSizeOfRowOrCol(row,direction='y')+rowsSoFar[-1]) # TODO: if drawing borders between rows, may need another +1 somewhere (and +1 on first if top border also), plus detect when we're on a border line and draw it (except where rowspan is in effect)
            if rowsSoFar[-1] > N: # it's this row
                cells = range(self.getNumRowsOrCols(0))
                for k,v in self.items.iteritems():
                    if not k[1] <= row < k[1]+v[0][1]:
                        continue # wrong row
                    assert cells[k[0]:k[0]+v[0][0]] == range(k[0],k[0]+v[0][0]), "overlapping cells!"
                    if hasattr(v[1],'valign'):
                        valign = v[1].valign
                    else: valign='top'
                    itsLine = N-rowsSoFar[k[1]]
                    if not valign=='top':
                        itsLine -= centreCalc(v[1].getSize('y'),rowsSoFar[k[1]+v[0][1]]-rowsSoFar[k[1]],valign)[0]
                    cells[k[0]] = v[1].getLine(itsLine)
                    for o in xrange(k[0]+1,k[0]+v[0][0]):
                        cells[o] = None
                    cellWid = ansifiedLineLen(cells[k[0]])
                    needWid = self.getSizeOfRowOrCol(k[0],k[0]+v[0][0],direction='x')
                    if needWid > cellWid:
                        if hasattr(v[1],'align'):
                            align = v[1].align
                        else: align='left'
                        before,after = centreCalc(cellWid,needWid,align)
                        if before: cells[k[0]].insert(0,ANSIfiedSpacer(before))
                        if after: cells[k[0]].append(ANSIfiedSpacer(after))
                    else: assert needWid==cellWid, "getSizeOfRowOrCol(%d:%d) returned %d but actual cell width %d" % (k[0],k[0]+v[0][0],needWid,cellWid)
                for i in xrange(len(cells)):
                    if type(cells[i]) == int:
                        cells[i] = [ANSIfiedSpacer(self.getSizeOfRowOrCol(i))]
                if self.drawBorder: mid = [ANSIfiedLineDrawing('|',[])] # TODO: more complex if drawing horizontal borders also: it might need to intersect them; TODO: external borders before/after the table?
                else: mid = [ANSIfiedSpacer(1)]
                return reduce(lambda a,b:a+mid+b, [x for x in cells if not x==None]) # (None = placeholder for colspans)
        return []
    def canSubstituteLineBreak(self): return False
    def isHardLineBreak(self): return False
def ANSIfiedTextToStackingRectangle(at):
    "Make an ANSIfiedText 'know' how to run getSize etc"
    width = widthOf(at.txt)
    if width:
        def getSize(direction='x'):
            if direction=='x': return width
            else: return 1
        def getLine(N): return [at] # (can assume N==0 here, because the enclosing StackingRectangle('y') will handle any out-of-bounds requests)
    else: # zero-width space or something - don't output
        def getSize(_): return 0
        def getLine(_): return []
    at.getSize,at.getLine = getSize,getLine
    at.padToSize = lambda *args: True # no need to do anything because the surrounding objects will add struts
    if at.txt in lineBreakCharList:
        at.canSubstituteLineBreak = lambda *args: True
    else: at.canSubstituteLineBreak = lambda *args: False
    if at.txt in ['\n']: # TODO: more?
        at.isHardLineBreak = lambda *args: True
    else: at.isHardLineBreak = lambda *args: False
    return StackingRectangle('x',[StackingRectangle('y',[at])],name='obj')

lineBreakCharList = [u' ',u'\u200b']
notAllowedToBreakHanziBefore = u'.,;?!:'
notAllowedToBreakHanziBefore = u'[\u2019\u201d\u3001\u3002' + u''.join(unichr(x) for x in range(0x3009,0x3020,2)) + notAllowedToBreakHanziBefore + u''.join(unichr(ord(c)+0xfee0) for c in notAllowedToBreakHanziBefore) +u']'
def textIntoWordsAndSpaces(text):
    text = re.sub(u'([\u4e00-\ua700])(?!'+notAllowedToBreakHanziBefore+u')',r'\1'+u'\u200b',text) # TODO: + kana ?
    i = 0
    for w in re.finditer('|'.join(re.escape(w) for w in lineBreakCharList), text):
        if w.start() > i: yield text[i:w.start()]
        yield w.group()
        i = w.end()
    if i<len(text): yield text[i:]

def centreCalc(curSize,neededSize,alignType):
    extra = neededSize - curSize
    if alignType in ['top','left']: before,after = 0,extra
    elif alignType in ['bottom','right']:
        before,after = extra,0
    else:
        before = int(extra/2) ; after = extra-before
    return before,after

def matchToClosingTag(inStr):
    "Takes account of nesting, but is quite tolerant.  Returns None if it can't make sense of the input starting at this point, or (tagName, position past opening tag, postition of end of closing tag, position past end of closing tag).  Imaginary closings are added for self-closing tags."
    tagName = re.match('<([^ >]*)( [^>]*)?>',inStr)
    if not tagName: return
    tStart = tagName.end()
    tagName = tagName.group(1).lower() ; numOpen = 0
    if inStr[tStart-2]=='/' or tagName in ['br','hr']: # TODO: more self-closing tags?
        return tagName,tStart,tStart,tStart
    for t in re.finditer('(?i)</?'+re.escape(tagName)+'[ >]', inStr): # (ONLY the named tag, not any intervening ones.  This won't work with tags like <li>, which are implicitly closed if another one starts with no intervening <ul>/<ol>'s, or <p> which is closed if another starts on same level.  These tags are patched up by the caller.)
        if t.group()[1]=='/': numOpen -= 1
        else: numOpen += 1
        if numOpen==0: return tagName, tStart, t.start(), t.end()
    # if get here, we have an 'unclosed' tag (but maybe
    # not really - see above).  Pretend it's closed at the
    # end of the section of the doc we're dealing with.
    return tagName, tStart, len(inStr), len(inStr)

tagsToIgnore = [
    '/li', # we ignore </li> and start new list items on <li> (see below)
    'noscript','/noscript',
    'span','/span', # for now (TODO: css?)
    'nobr','/nobr', # for now (TODO: nbsp?)
    'meta','link', # (header stuff)
    'a','/a', # for now (TODO: do something?)
    'blink','/blink', # please don't!
    'tt','/tt','code','/code',
    'samp','/samp','kbd','/kbd',
    '!doctype','html','/html','body','/body',
    'small','/small','big','/big',
    'dl','/dl', # we just process its contents
]
tagsToIgnore = re.compile('(?i)<('+'|'.join(re.escape(t) for t in tagsToIgnore)+')( [^>]*)?>')

def parseDoc(html,width=None,attList=None,realWidth=None,
             inPre=False,isOL=False,inCentre=False,
             callback=None):
    "if callback is not None, we're reading the top-level document and callback is called to 'flush' lines from it (so don't need to build up entire doc in memory before starting to print)"
    if width==None: width = screenWidth
    if realWidth==None: realWidth = width # for lists
    if attList==None: attList = []
    theDoc = StackingRectangle('y',name='doc')
    realDoc = theDoc # if we go into <li>, THAT becomes the new theDoc (this is a 'messy-HTML' parser)
    lstrip = True ; liNum = 0
    def flush():
        if callback and theDoc.items:
            theDoc.lineBreakAndPadLeading(realWidth)
            callback(theDoc.getLines())
            theDoc.items = []
    def makeP():
        theP=StackingRectangle('x',name='p')
        flush() ; theDoc.items.append(theP)
        return theP
    def closeLI():
        if not theDoc==realDoc:
            theDoc.lineBreakAndPadLeading(width)
            realDoc.items[-1].padToSize('x',align='left',absoluteMaximum=width)
            realDoc.items[-1].padToSize('y',align='top')
    theP = makeP()
    attList_stack = [] ; gobbled = 0
    while html:
        def f(w): return ANSIfiedTextToStackingRectangle(ANSIfiedText(unicode(deAmp(w)),attList))
        beforeTag = re.match('[^<]*',html).end()
        if beforeTag:
            txt = html[:beforeTag]
            if inPre: theP.items += [f(txt)]
            else:
                txt = re.sub(r'\s+',' ',txt)
                if lstrip: txt = txt.lstrip()
                theP.items += [f(w) for w in textIntoWordsAndSpaces(txt)]
            html = html[beforeTag:] ; gobbled += beforeTag
            if not html: break
        if attList_stack and attList_stack[-1][0]==gobbled+html.find('>')+1: # we're at the closing tag of that style
            _, al2 = attList_stack.pop()
            while attList: del attList[0]
            attList += al2 # change in-place for caller
            gobbled += html.find('>')+1
            html = html[html.find('>')+1:]
            continue # may do another, and/or more words
        m = re.match(tagsToIgnore,html)
        if m:
            gobbled += m.end() ; html = html[m.end():]
            lstrip=False ; continue
        m = re.match('(?i)</?p>',html)
        if m: # treat both <p> and </p> as <p> (see below), and don't bother trying to find their closing tags
            thisTag = ('p',m.end(),len(html),len(html))
        else: thisTag = matchToClosingTag(html)
        if thisTag:
            tagName, inStart, inEnd, pastClose = thisTag
            ansiatt=ansiAttributesForTag(html[:inStart])
            if ansiatt:
                attList_stack.append((gobbled+pastClose,attList[:]))
                attList += ansiatt ; pastClose = inStart
                lstrip = False
            elif tagName=='ruby':
                stack = parseRuby(html[inStart:inEnd],width,attList)
                if stack: theP.items.append(stack)
                else: thisTag = None # invalid
                lstrip = False
            elif tagName in ['ul','ol']:
                flush()
                theDoc.items.append(parseDoc(html[inStart:inEnd],max(min(10,width),width-4),attList,width,isOL=(tagName=='ol')))
                # plus we need a new para at the end
                theP = makeP()
                lstrip = True
            elif tagName in ['p']: # careful, this is auto-closing and matchToClosingTag doesn't "get" it, so:
                if len(theP.items): # need blank space
                    theDoc.items.append(Strut('y',1))
                theP = makeP() ; pastClose = inStart
                lstrip = True
            elif tagName in ['li']: # similar
                closeLI()
                li = StackingRectangle('x',name='li')
                realDoc.items.append(li) ; liNum += 1
                if isOL:
                    if liNum < 100: fmt = u"% 2d. "
                    elif liNum < 1000: fmt = u"% 3d."
                    else: fmt = u"%d" # who has that many?
                    txt,tAttr = (fmt % liNum),ansiAttributesForTag('<b>')
                else: txt,tAttr = u"  * ",[]
                li.items.append(ANSIfiedTextToStackingRectangle(ANSIfiedText(txt,tAttr)))
                theDoc = StackingRectangle('y')
                li.items.append(theDoc)
                theP = makeP() ; pastClose = inStart
                lstrip = True
            elif tagName in ['address','blockquote','h1','h2','h3','h4','h5','h6','dd']: # TODO: leave space above/below for some of these ?
                flush()
                if tagName.startswith('h'): al2 = attList + ansiAttributesForTag('<b>')
                elif tagName.startswith('a'): al2 = attList + ansiAttributesForTag('<em>')
                else: al2 = attList
                blk = StackingRectangle('x',name='blk')
                theDoc.items.append(blk)
                w0 = max(min(10,width),width-8)
                w1 = int((width-w0)/2)
                blk.items.append(Strut('x',w1))
                blk.items.append(parseDoc(html[inStart:inEnd],w0,al2,w0))
                blk.items[-1].padToSize('x',align='left',absoluteMaximum=width)
                blk.items.append(Strut('x',width-w0-w1))
                blk.padToSize('y') # fill out the struts
                # plus we need another new para at the end
                theP = makeP() ; lstrip = True
            elif tagName in ['div','pre','dt','center']:
                # as above but without the extra margins
                flush()
                theDoc.items.append(parseDoc(html[inStart:inEnd],width,attList,inPre=(tagName=='pre'),inCentre=(tagName=='center')))
                theP = makeP() ; lstrip = True
            elif tagName in ['table']:
                flush()
                theDoc.items.append(parseTable(html[inStart:inEnd],width,attList,'border' in html[:inStart]))
                theP = makeP() ; lstrip = True
            elif tagName in ['hr']:
                theP.items += [f(u'\u200b'),ANSIfiedTextToStackingRectangle(ANSIfiedLineDrawing(u'-'*width,[])),f(u'\u200b')]
                lstrip = True
            elif tagName in ['br']:
                theP.items.append(f('\n'))
                lstrip = True
            # TODO: more tags ?
            else: thisTag = None # unrecognised
        if thisTag: html,gobbled = html[pastClose:],gobbled+pastClose
        else: # it's a tag we didn't recognise, or something that's malformed
            theP.items.append(f('<'))
            gobbled += 1 ; html = html[1:] ; lstrip=False
    closeLI() ; flush()
    if realDoc==theDoc:
        realDoc.lineBreakAndPadLeading(realWidth)
        if inCentre: realDoc.padToSize(desired=realWidth) # TODO: unless we're inside a table or something, in which case leave desired=0
    return realDoc

def parseTable(html,width,attList,hasBorder):
    rows = StackingRectangle('y',name='table')
    while html:
        thisTag = matchToClosingTag(html)
        if not thisTag:
            # TODO: this is a bit of duplicate code
            html = html[html.find('<',1):]
            if len(html)==1: break
            else: continue
        tagName, inStart, inEnd, pastClose = thisTag
        if tagName=='tr': rows.items.append(parseRow(html[inStart:inEnd],width,attList[:]))
        html = html[pastClose:]
    if hasBorder or any(any(hasattr(c,'rowspan') or hasattr(c,'colspan') or hasattr(c,'align') or hasattr(c,'valign') for c in r.items) for r in rows.items):
        # it's complex - we'd better use an XYGrid (TODO: don't really need XYGrid for just align attrs if we implement align in StackingRectangle's tabulate; see the TODOs there)
        grid = XYGrid(hasBorder)
        y = 0 ; curRowspans = [] # (start,nLeft)
        for row in rows.items:
            x = 0
            for cell in row.items:
                while any(i[0]==x for i in curRowspans):
                    x += 1 # skip that col
                if hasattr(cell,'rowspan'):
                    rowspan = cell.rowspan
                else: rowspan = 1
                if hasattr(cell,'colspan'):
                    colspan = cell.colspan
                else: colspan = 1
                grid.items[(x,y)]=((colspan,rowspan),cell)
                if rowspan > 1:
                    for c in range(x,x+colspan):
                        curRowspans.append((c,rowspan-1))
                x += colspan
            i = 0 # update curRowspans:
            while i < len(curRowspans):
                if not curRowspans[i][1]:
                    del curRowspans[i] # it's finished
                else:
                    curRowspans[i] = (curRowspans[i][0], curRowspans[i][1]-1) ; i += 1
            y += 1
        rows.items = [StackingRectangle('x',[grid])] # in case it needs any outside padding
    else: rows.tabulate() # for simpler tables
    return rows
def parseRow(html,width,attList):
    cols = StackingRectangle('x',name='tr')
    while html:
        thisTag = matchToClosingTag(html)
        if not thisTag:
            html = html[html.find('<',1):]
            if len(html)==1: break
            else: continue
        tagName, inStart, inEnd, pastClose = thisTag
        if tagName=='td':
            cols.items.append(parseDoc(html[inStart:inEnd],width,attList[:])) # TODO: reduce width?  (but only up to a limit)  might need 2+ passes to get it optimal
            rowspan=attrValue(html[:inStart],'rowspan',1)
            colspan=attrValue(html[:inStart],'colspan',1)
            if rowspan>1 or colspan>1:
                cols.items[-1].rowspan = int(rowspan)
                cols.items[-1].colspan = int(colspan)
            align = attrValue(html[:inStart],'align','left')
            valign = attrValue(html[:inStart],'valign','top')
            if not align=='left':
                cols.items[-1].align = align
            if not valign=='top':
                cols.items[-1].valign = valign
        html = html[pastClose:]
    return cols

def attrValue(tagStr,attrName,default=None):
    for m in re.finditer('(?i) '+re.escape(attrName)+' *=([^ />]*|("[^"]*"))',tagStr):
        m = m.group(1)
        if m.startswith('"'): return m[1:-1]
        else: return m
    return default

def parseRuby(html,width,attList):
    out = StackingRectangle('y',name='ruby')
    while html:
        thisTag = matchToClosingTag(html)
        if not thisTag:
            html = html[html.find('<',1):]
            if len(html)==1: break
            else: continue
        tagName, inStart, inEnd, pastClose = thisTag
        line = parseDoc(html[inStart:inEnd],width,attList[:])
        if tagName=='rb': out.items.append(line)
        elif tagName=='rt': out.items.insert(0,line)
        html = html[pastClose:]
    if not out.items: return None # malformed ruby
    out.padToSize(absoluteMaximum = screenWidth)
    return out

def ansiAttributesForTag(tag):
    "Translates a non-closing tag (including < and >) to ANSI-sequence list, if appropriate.  Return value should be added after any existing list." # (for now, the list will always have 0 or 1 items, but in future we might support more complex style tags) (TODO: if adding background colour, see the TODO in ANSIfiedSpacer)
    tagl = tag.lower() ; ttype=tagl[1:-1].split()[0]
    def f(n): return ["\x1b[%dm" % n]
    if ttype in ['b','strong']: return f(1)
    elif ttype in ['i','em']: return f(3)
    elif ttype in ['u']: return f(4)
    elif ttype in ['s','strike','del']: return f(9) # not always poss
    elif ttype=='font':
        clr = attrValue(tagl,'color')
        priSecList = ['black','red','green','yellow','blue','magenta','cyan','white'] # r*1+g*2+b*4
        if clr.startswith('#'):
            try: r,g,b = int(clr[-6:-4],16),int(clr[-4:-2],16),int(clr[-2:],16)
            except: return []
            threshold = max([r,g,b])/4
            def contrib(v):
                if v > threshold: return 1
                else: return 0
            r,g,b = [contrib(n) for n in [r,g,b]]
            clr = priSecList[r*1+g*2+b*4]
        if clr in priSecList: return f(30+priSecList.index(clr)) # TODO: check aliases like "purple" ??
    return []

def widthOf(unistr):
    "Returns the width of unistr in terminal narrow-spaces, assuming all combining characters and ANSI attributes will be honoured (and also zero-width space), and assuming all non-fullwidth/wide chars are narrow"
    wid = 0
    for c in re.sub(u'[\u0300-\u036f\u200b]+','',re.sub("\x1b\\[[0-9]*m","",unistr)):
        if unicodedata.east_asian_width(c) in ['F','W']:
            wid += 2
        else: wid += 1
    return wid

def screenDim(d):
  c = int(os.environ.get(d,0))
  if c: return c
  import struct, fcntl, termios
  if d=='COLUMNS': offset = 1
  else: offset = 0
  for N in [sys.stdout, sys.stderr, sys.stdin]:
    if N.isatty(): return struct.unpack('hh',fcntl.ioctl(N,termios.TIOCGWINSZ,'xxxx'))[offset]
  assert 0, "Could not determine dimensions: of terminal, please set "+d
  return 60 # (last resort in case asserts are off)
screenWidth = screenDim('COLUMNS')

def htmlPreprocess(h):
    hl = h.lower()
    for tag1,tag2 in [('<!--','-->'),('<script','</script>'),('<style','</style>')]:
        s = 0
        while True:
            s = hl.find(tag1,s)
            if s<0: break
            e = hl.find(tag2,s+len(tag1))
            if e<0: break
            e += len(tag2)
            h = h[:s]+h[e:]
            hl = hl[:s]+hl[e:]
    return decode_entities(h)
import htmlentitydefs
def decode_entities(unistr): return re.sub('&([^&;]+);',matchEntity,unistr)
def matchEntity(m):
  mid=m.group(1)
  if mid.startswith('#'):
    mid=mid[1:]
    if mid.startswith('x'): base,mid=16,mid[1:]
    else: base=10
    try: return unichr(int(mid,base))
    except: pass
  elif mid in htmlentitydefs.name2codepoint and not mid in ['lt','quot','amp']: # better cope with these later as these can affect the parsing
    return unichr(htmlentitydefs.name2codepoint[mid])
  return m.group()
def deAmp(h): return h.replace('&lt;','<').replace('&quot;','"').replace('&amp;','&')

try:
  import locale
  terminal_charset = locale.getdefaultlocale()[1]
except: terminal_charset = "utf-8"

term = os.environ.get("TERM","")
supports_ansi = ("xterm" in term or term in ["screen","linux"]) # TODO: others?

if __name__ == "__main__":
    if sys.stdin.isatty(): sys.stderr.write("termlayout: reading HTML from standard input\n")
    if sys.stdout.isatty() and not sys.stdin.isatty() and os.path.exists('/usr/bin/less'):
        outstream = os.popen('/usr/bin/less -FrX','w')
    else: outstream = sys.stdout
    parseDoc(htmlPreprocess(sys.stdin.read().decode(terminal_charset)),callback=lambda lines:(outstream.write(mergeAnsifiedLines(lines,not supports_ansi).encode(terminal_charset)),outstream.flush())) # TODO: although we definitely .encode(terminal_charset), the .decode might have to be something else if there's a META specifying it
