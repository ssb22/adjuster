#!/usr/bin/env python

program_name = "Annotator Generator v0.2 (c) 2012 Silas S. Brown"

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from optparse import OptionParser
parser = OptionParser()
import sys,os,tempfile
if not "mac" in sys.platform and not "darwin" in sys.platform and ("win" in sys.platform or "mingw32" in sys.platform): exe=".exe" # Windows, Cygwin, etc
else: exe=""

#  =========== INPUT OPTIONS ==============

parser.add_option("--infile",
                  help="Filename of a text file (or a compressed .gz or .bz2 file) to read the input examples from. If this is not specified, standard input is used.")

parser.add_option("--incode",default="utf-8",
                  help="Character encoding of the input file (default %default)")

parser.add_option("--mstart",
                  dest="markupStart",
                  default="<ruby><rb>",
                  help="The string that starts a piece of text with annotation markup in the input examples; default %default")

parser.add_option("--mmid",
                  dest="markupMid",
                  default="</rb><rt>",
                  help="The string that occurs in the middle of a piece of markup in the input examples, with the word on its left and the added markup on its right; default %default")

parser.add_option("--mend",
                  dest="markupEnd",
                  default="</rt></ruby>",
                  help="The string that ends a piece of annotation markup in the input examples; default %default")

parser.add_option("--reference-sep",
                  help="Reference separator code used in the example input.  If you want to keep example source references for each rule, you can label the input with 'references' (chapter and section numbers or whatever), and use this option to specify what keyword or other markup the input will use between each 'reference'.  The name of the next reference will be whatever text immediately follows this string.  Note that the reference separator, and the reference name that follows it, should not be part of the text itself and should therefore not be part of any annotation markup.  If this option is not set then references will not be tracked.")

parser.add_option("--ref-name-end",default=" ",
                  help="Sets what the input uses to END a reference name.  The default is a single space, so that the first space after the reference-sep string will end the reference name.")

parser.add_option("-s", "--spaces",
                  action="store_false",
                  dest="removeSpace",
                  default=True,
                  help="Set this if you are working with a language that uses whitespace in its non-markedup version (not fully tested).  The default is to assume that there will not be any whitespace in the language, which is correct for Chinese and Japanese.")

parser.add_option("-c", "--capitalisation",
                  action="store_true",
                  default=False,
                  help="Don't try to normalise capitalisation in the input.  Normally, to simplify the rules, the analyser will try to remove start-of-sentence capitals in annotations, so that the only remaining words with capital letters are the ones that are ALWAYS capitalised such as names.  (That's not perfect: it's possible that some words will always be capitalised just because they happen to never occur mid-sentence in the examples.)  If this option is used, the analyser will instead try to \"learn\" how to predict the capitalisation of ALL words (including start of sentence words) from their contexts.") # TODO: make the C program put the sentence capitals back

#  =========== OUTPUT OPTIONS ==============

parser.add_option("--c-filename",default=tempfile.gettempdir()+os.sep+"annotator.c",help="Where to write the C program if standard output is not connected to a pipe. Defaults to annotator.c in the system temporary directory (the program might be large, especially if Yarrowsky indicators are not used, so it's best not to use a server home directory where you might have limited quota). If standard output is connected to a pipe, then this option is ignored and C code is written to the pipe instead.")

parser.add_option("--c-compiler",default="gcc -o annotator"+exe,help="The C compiler to run if standard output is not connected to a pipe. You can add options (remembering to enclose this whole parameter in quotes if it contains spaces), but if the C program is large then adding optimisation options may make the compile take a LONG time. If standard output is connected to a pipe, then this option is ignored because the C code will simply be written to the pipe. Default: %default") # -Os can take a lot longer; -m32 won't always work on 64-bit distros

parser.add_option("--outcode",default="utf-8",
                  help="Character encoding to use in the generated parser and rules summary (default %default, must be ASCII-compatible i.e. not utf-16)")

parser.add_option("-S", "--summary-only",
                  action="store_true",default=False,
                  help="Don't generate a parser, just write the rules summary to standard output")

parser.add_option("-O", "--summary-omit",
                  help="Filename of a text file (or a compressed .gz or .bz2 file) specifying what should be omitted from the rules summary.  Each line should be a word or phrase, a tab, and its annotation (without the mstart/mmid/mend markup).  If any rule in the summary exactly matches any of the lines in this text file, then that rule will be omitted from the summary (but still included in the parser).  Use for example to take out of the summary any entries that correspond to things you already have in your dictionary, so you can see what's new.")

parser.add_option("--maxrefs",default=3,
                  help="The maximum number of example references to record in each summary line, if references are being recorded.  Default is %default; 0 means unlimited.")

#  =========== ANALYSIS OPTIONS ==============

parser.add_option("-o", "--allow-overlaps",
                  action="store_true",default=False,
                  help="Normally, the analyser avoids generating rules that could overlap with each other in a way that would leave the program not knowing which one to apply.  If a short rule would cause overlaps, the analyser will prefer to generate a longer rule that uses more context, and if even the entire phrase cannot be made into a rule without causing overlaps then the analyser will give up on trying to cover that phrase.  This option allows the analyser to generate rules that could overlap, as long as none of the overlaps would cause actual problems in the example phrases. Thus more of the examples can be covered, at the expense of a higher risk of ambiguity problems when applying the rules to other texts.")

parser.add_option("-P", "--primitive",
                  action="store_true",default=False,
                  help="Don't bother with any overlap or conflict checks at all, just make a rule for each word. The resulting parser is not likely to be useful, but the summary might be.")
                  
parser.add_option("-y","--ybytes",default=0,
                  help="Look for candidate Yarrowsky seed-collocations within this number of bytes of the end of a word.  If this is set then overlaps and rule conflicts will be allowed if the seed collocations can be used to distinguish between them.")
# parser.add_option("--ybytes-max",default=0) # TODO: if uncommenting, need to carry the variable-ybytes through to the C code and tables
# parser.add_option("--ybytes-step",default=1)
parser.add_option("--warn-yarrowsky",
                  action="store_true",default=False,
                  help="Warn when absolutely no distinguishing Yarrowsky seed collocations can be found for a word in the examples")

sys.stderr.write(program_name+"\n") # not sys.stdout, because may or may not be showing --help (and anyway might want to process the help text for website etc)
options, args = parser.parse_args()
globals().update(options.__dict__)

if primitive and ybytes: sys.stderr.write("Warning: primitive will override ybytes\n")
if ybytes: ybytes=int(ybytes)
# if ybytes_max: ybytes_max=int(ybytes_max)
# else: ybytes_max = ybytes
# ybytes_step=int(ybytes_step)
maxrefs = int(maxrefs)

def stringSwitch(byteSeq_to_action_dict,subFuncL,funcName="topLevelMatch",subFuncs={},inTopFunc=True): # ("topLevelMatch" is also mentioned in the C code)
    # make a function to switch on a large number of variable-length string cases without repeated lookahead for each case
    # (may still backtrack if no words or no suffices match)
    # byteSeq_to_action_dict is really a byte sequence to (action, OR-list of Yarrowsky-like indicators which are still in Unicode), the latter will be c_escape()d
    allBytes = set([b[0] for b in byteSeq_to_action_dict.keys() if b])
    ret = []
    if funcName:
        if inTopFunc: ret.append("static void %s(int ns /* needSpace */) {" % funcName)
        else: ret.append("static void %s() {" % funcName)
        savePos = len(ret)
        ret.append("{ SAVEPOS;")
    elif "" in byteSeq_to_action_dict and len(byteSeq_to_action_dict) > 1:
        # no funcName, but might still want to come back here as there's a possible action at this level
        savePos = len(ret)
        ret.append("{ SAVEPOS;")
    else: savePos = None
    if "" in byteSeq_to_action_dict and len(byteSeq_to_action_dict) > 1 and not byteSeq_to_action_dict[""][1] and all([(a[0].startswith(byteSeq_to_action_dict[""][0]) and not a[1]) for a in byteSeq_to_action_dict.values()]):
        # there's an action in common for this and all subsequent matches, and no Yarrowsky-like indicators, so we can do the common action up-front
        if inTopFunc: ret.append("if(ns) s();")
        # else this will already have been done when the caller reached this part of the code
        ret.append(byteSeq_to_action_dict[""][0])
        l = len(byteSeq_to_action_dict[""][0])
        byteSeq_to_action_dict = dict([(x,(y[l:],z)) for x,(y,z) in byteSeq_to_action_dict.items()])
        # and, since we'll be returning no matter what,
        # we can put the inner switch in a new function
        # (even if not re-used, this helps gcc speed)
        # + DON'T save/restore pos around it (it itself
        # will do any necessary save/restore pos)
        del ret[savePos] ; savePos = None
        del byteSeq_to_action_dict[""]
        newFunc = "\n".join(stringSwitch(byteSeq_to_action_dict,subFuncL,"NewFunc",subFuncs,False))
        byteSeq_to_action_dict[""] = ("",[]) # for the end of this func
        if newFunc in subFuncs:
            # we generated an identical one before
            subFuncName=subFuncs[newFunc]
        else:
            subFuncName="match%d" % len(subFuncs)
            subFuncs[newFunc]=subFuncName
            subFuncL.append(newFunc.replace("NewFunc",subFuncName,1))
        ret.append(subFuncName+"();") # the call
    elif allBytes:
      # deal with all actions except "" first
      ret.append("switch(NEXTBYTE) {")
      for case in sorted(allBytes):
        if 32<=ord(case)<127 and case!="'": cstr="'%c'" % case
        else: cstr=ord(case)
        ret.append("case %s:" % cstr)
        ret += ["  "+x for x in stringSwitch(dict([(k[1:],v) for k,v in byteSeq_to_action_dict.items() if k and k[0]==case]),subFuncL,None,subFuncs,inTopFunc)]
        if not "return;" in ret[-1]: ret.append("  break;")
      ret.append("}") # end of switch(NEXTBYTE)
    if not savePos==None:
        if len(' '.join(ret).split('NEXTBYTE'))==2:
            # only 1 NEXTBYTE after the SAVEPOS - just
            # do a PREVBYTE instead
            # (note however that splitting on NEXTBYTE
            # does not necessarily give a reliable value
            # for max amount of lookahead required if
            # there's more than 1.  We use max rule len
            # as an upper bound for that instead.)
            del ret[savePos]
            ret.append("PREVBYTE;")
        else: ret.append("RESTOREPOS; }")
    if funcName: ret.append("}")
    elif "" in byteSeq_to_action_dict:
        # if the C code gets to this point, no return; happened - no suffices
        # so execute the "" action and return
        # (unless Yarrowsky-like indicators don't permit)
        conds = byteSeq_to_action_dict[""][1]
        if conds: ret.append("if ("+" || ".join(["near(\""+c_escape(c)+"\")" for c in conds])+") {")
        if inTopFunc and byteSeq_to_action_dict[""][0]: ret.append("if(ns) s();")
        ret.append((byteSeq_to_action_dict[""][0]+" return;").strip())
        if conds: ret.append("}")
    return ret # caller does '\n'.join

c_start = """/* -*- coding: """+outcode+""" -*- */
#include <stdio.h>
#include <string.h>

/* To include this code in another program,
   define the ifndef'd macros below + define Omit_main */
#ifndef NEXTBYTE
/* Default definition of NEXTBYTE etc is to use stdin */
enum { Half_Bufsize = %%LONGEST_RULE_LEN%% };
enum { ybytes = %%YBYTES%% }; /* for Yarrowsky matching, minimum readahead */
static unsigned char lookahead[Half_Bufsize*2];
static size_t filePtr=0,bufStart=0,bufLen=0;
static int nextByte() {
  if (filePtr-bufStart +ybytes >= bufLen) {
    if (bufLen == Half_Bufsize * 2) {
      memmove(lookahead,lookahead+Half_Bufsize,Half_Bufsize);
      bufStart += Half_Bufsize; bufLen -= Half_Bufsize;
    }
    bufLen += fread(lookahead+bufLen,1,Half_Bufsize*2-bufLen,stdin);
    if (filePtr-bufStart == bufLen) return EOF;
  }
  return lookahead[(filePtr++)-bufStart];
}
static int near(char* string) {
  /* for Yarrowsky-like matching */
  size_t offset = filePtr-bufStart, l=strlen(string),
         maxPos = bufLen-l;
  if (maxPos > offset+ybytes) maxPos = offset+ybytes;
  if (offset > ybytes) offset -= ybytes; else offset = 0;
  while (offset <= maxPos) {
    if(!strncmp(lookahead+offset,string,l)) return 1;
    offset++;
  }
  return 0;
  // or can use strnstr(haystack,needle,n) if on FreeBSD
}
#define NEXTBYTE nextByte()
#define POSTYPE size_t
#define THEPOS filePtr /* or get it via a function */
#define SAVEPOS POSTYPE oldPos=THEPOS
#define RESTOREPOS filePtr=oldPos /* or set via a func */
#define PREVBYTE filePtr--
#define BOGUS_BYTE OutWriteByte(NEXTBYTE)
#define FINISHED (feof(stdin) && filePtr-bufStart == bufLen)
#endif
#ifndef OutWrite
#define OutWrite(fmt,a,b) printf(fmt,a,b)
#define OutWriteStr(s) fputs(s,stdout)
#define OutWriteByte(c) putchar(c)
#endif
#ifndef OutWriteStr
#define OutWriteStr(s) OutWrite("%s",s)
#endif
#ifndef OutWriteByte
#define OutWriteByte(c) OutWrite("%c",c)
#endif

#ifndef Default_Annotation_Mode
#define Default_Annotation_Mode ruby_markup
#endif

enum {
  annotations_only,
  ruby_markup,
  brace_notation} annotation_mode = Default_Annotation_Mode;

static void o(const char *word,const char *annot) {
  switch (annotation_mode) {
  case annotations_only: OutWriteStr(annot); break;
  case ruby_markup: OutWrite("<ruby><rb>%s</rb><rt>%s</rt></ruby>",word,annot); break;
  case brace_notation: OutWrite("{%s|%s}",word,annot); break;
  }
}
static void s() { OutWriteByte(' '); }
"""

c_end = """
void matchAll() {
  int needSpace=0;
  while(!FINISHED) {
    POSTYPE oldPos=THEPOS;
    topLevelMatch(needSpace);
    if (oldPos==THEPOS) { needSpace=0; BOGUS_BYTE; }
    else needSpace=1;
  }
}

#ifndef Omit_main
main(int argc,char*argv[]) {
  int i; for(i=1; i<argc; i++) {
    if(!strcmp(argv[i],"--help")) {
      puts("Use --ruby to output ruby markup (default)");
      puts("Use --raw to output just the annotations without the base text");
      puts("Use --braces to output as {base-text|annotation}");
      return 0;
    } else if(!strcmp(argv[i],"--ruby")) {
      annotation_mode = ruby_markup;
    } else if(!strcmp(argv[i],"--raw")) {
      annotation_mode = annotations_only;
    } else if(!strcmp(argv[i],"--braces")) {
      annotation_mode = brace_notation;
    }
  }
  matchAll();
}
#endif
"""

def splitWords(text,phrases=False):
    # split text into words, ignoring anything between markupStart and markupEnd
    # if phrases = True, instead of words, split on any non-whitespace char outside markupStart..markupEnd
    i=start=0 ; ret = []
    def isSplitpoint():
        isspace = not text[i].split()
        if phrases: return not isspace
        else: return isspace
    while i<len(text):
        if text[i:i+len(markupStart)]==markupStart:
            i = text.find(markupEnd,i+len(markupStart))
            if i==-1: i=len(text)
            else: i += len(markupEnd)
        elif isSplitpoint():
            ret.append(text[start:i])
            if phrases:
                # can skip to text markupStart
                i=text.find(markupStart,i)
                if i==-1: i=len(text)
                start = i
            else:
                i += 1 # just after the 1st splitter
                while i<len(text) and isSplitpoint(): i += 1
                start = i # 1st non-splitter char
        else: i += 1
    ret.append(text[start:i])
    return filter(lambda x:x,ret)

def annotationOnly(text):
    ret = []
    for w in splitWords(text):
        i=w.find(markupMid,len(markupStart))
        if i==-1: continue
        ret.append(w[i+len(markupMid):-len(markupEnd)])
    return ' '.join(ret)

def markDown(text):
    # Return just the original text, without markup
    i=start=inMarkup=0 ; ret = []
    while i<len(text):
        i = text.find(markupStart,start)
        if i==-1: i=len(text)
        else:
            t = text[start:i] # the text BETWEEN markups
            if removeSpace: t=''.join(t.split())
            ret.append(t)
            start=i=i+len(markupStart)
            i = text.find(markupMid,start)
            if i==-1: i=len(text)
            ret.append(text[start:i])
            i = text.find(markupEnd,i+len(markupMid))
            if i==-1: i=len(text)
            else: i += len(markupEnd)
            start = i
    return ''.join(ret)

import sys,time

def normalise_capitalisation():
    global corpus_unistr
    sys.stderr.write("Normalising capitalisation... ")
    # (as long as it's all Unicode strings, .lower() and .upper() work with accents etc)
    allWords = {} ; found = False
    for phrase in splitWords(corpus_unistr,phrases=True):
        for w in splitWords(phrase):
            allWords[w] = True
    for w in allWords.keys():
        wl = w.lower()
        if not w==wl and wl in allWords:
            # This word is NOT always capitalised, just
            # sometimes at the start of a sentence.
            # To simplify rules, make it always lower.
            corpus_unistr = corpus_unistr.replace(w,wl)
    sys.stderr.write("done\n")

def yarrowsky_indicators(withAnnot_unistr,markedDown):
    # returns True if rule always works, or lists enough indicators to cover example instances.
    # (If too few indicators can be found, will list the ones it can, or empty if no clearly-distinguishable indicators can be found within ybytes of end of match.)
    # First, find positions in markedDown which match withAnnot_unistr in corpus_unistr (not markedUp as that's harder to sync with markedDown)
    muStart=downLenSoFar=0 ; okStarts = []
    for s in findAll(corpus_unistr,withAnnot_unistr):
        downLenSoFar += len(markDown(corpus_unistr[muStart:s]))
        muStart = s
        okStarts.append(downLenSoFar+1) # +1 as there's a unichr(1) at start of markedDown
    # now check for markedDown matches that *don't* have withAnnot_unistr
    okStarts=set(okStarts)
    nonAnnot=markDown(withAnnot_unistr)
    badStarts=[x for x in findAll(markedDown,nonAnnot) if not x in okStarts]
    if not badStarts: return True # rule always works, no Yarrowsky indicators needed
    def tryNBytes(nbytes):
      def bytesAround(start): return within_Nbytes(markedDown,start+len(nonAnnot),nbytes)
      omitStr = chr(1).join([bytesAround(s) for s in badStarts])
      okStrs=[bytesAround(s) for s in okStarts]
      def score(txt):
        s = 0
        for st in okStrs:
            if txt in st: s += 1
        return s
      covered=[False]*len(okStrs)
      ret = []
      for indicatorStr in unique_substrings(okStrs,lambda txt:txt in omitStr,score):
          cChanged = False
          for i in xrange(len(okStrs)):
              if not covered[i] and indicatorStr in okStrs[i]: covered[i]=cChanged=True
          if cChanged: ret.append(indicatorStr)
          if all(covered): break
      return ret,len([x for x in covered if x]),len(covered)
    
    ret = tryNBytes(ybytes)[0] # if no ybytes_max logic
    # retList = []
    # assert ybytes_max >= ybytes
    # for nbytes in range(ybytes,ybytes_max+1,ybytes_step):
    #     ret,covered,toCover = tryNBytes(nbytes)
    #     if covered==toCover and len(ret)==1: return ret # a single indicator that covers everything will be better than anything else we'll find
    #     retList.append((-covered,len(ret),nbytes,toCover,ret)) # (1st 3 of these are the sort keys: maximum coverage, THEN minimum num indicators for the same coverage, THEN minimum nbytes (TODO: problems of very large nbytes might outweigh having more indicators; break if found 100% coverage by N?)  toCover should always ==len(okStarts).)
    #     # TODO: try finding an OR-combination of indicators at *different* proximity lengths ?
    # retList.sort() ; ret = retList[0][-1]
    if not ret and warn_yarrowsky: sys.stderr.write("Couldn't find ANY Yarrowsky-like indicators for %s   \n" % (withAnnot_unistr.encode('utf-8')))
    # else: sys.stderr.write("Debugger: best coverage=%d/%d by %d indicators at nbytes=%d   \n" % (-retList[0][0],retList[0][3],retList[0][1],retList[0][2]))
    # TODO: if partially but not completely covered, shouldn't entirely count the word as 'covered' in analyse()
    return ret

def unique_substrings(texts,omitFunc,valueFunc):
    # yield unique substrings of texts, in increasing length, with equal lengths sorted by highest score returned by valueFunc, and omitting any where omitFunc is true
    length=1 ; maxlen = max([len(t) for t in texts])
    while length <= maxlen:
        ret={}
        for text in texts:
          s=0
          while s <= len(text)-length:
            ret[text[s:s+length]]=True
            s += 1
        l=[(valueFunc(k),k) for k in ret.keys() if not omitFunc(k)]
        # if length == ybytes_max and not l: sys.stderr.write("Debugger: omitFunc was true for all %s\n" % repr(ret.keys()))
        l.sort() ; l.reverse()
        for v,k in l: yield k
        length += 1

def findAll(haystack,needle):
    # yields non-overlapping match positions in order (TODO: is there a library func for this?)
    i=0
    while True:
        i=haystack.find(needle,i)
        if i<0: break
        yield i
        i += len(needle)

def within_Nbytes(markedDown,matchEndPos,nbytes):
    # return the Unicode characters within nbytes of matchEndPos, assuming the encoding will be outcode.  Used for the Yarrowsky-like functions.
    # Assumes multibyte codes are self-synchronizing, i.e. if you start in the middle of a multibyte sequence, the first valid character will be the start of the next sequence, ok for utf-8 but TODO might not be the case for some codes
    return markedDown[max(0,matchEndPos-nbytes):matchEndPos].encode(outcode)[-nbytes:].decode(outcode,'ignore')+markedDown[matchEndPos:matchEndPos+nbytes].encode(outcode)[:nbytes].decode(outcode,'ignore')

def test_rule(withAnnot_unistr,markedUp,markedDown,yBytesRet):
    # Tests to see if the rule withAnnot_unistr is
    # ALWAYS right in the examples, i.e.
    # the number of occurrences of its marked-down text
    # in the continuous marked-down string should be
    # EXACTLY equal to the number of occurrences of the
    # marked-up version.
    # (If we deal only in rules that ALWAYS work, we can
    # build them up incrementally without "cross-talk")
    if primitive: return True
    if ybytes:
        ybr = yarrowsky_indicators(withAnnot_unistr,markedDown)
        if ybr==True or not ybr: return ybr
        yBytesRet.append(ybr) # list of indicators
        return True
    def occurrences(haystack,needle): return len(haystack.split(needle))-1 # assumes haystack has non-needle terminators - have put these in with unichr(1)s below
    return occurrences(markedDown,markDown(withAnnot_unistr)) == occurrences(markedUp,withAnnot_unistr)

def all_possible_rules(words):
    # Iterate over ALL possible rules derived from the
    # word sequence (don't just "find the shortest context
    # that predicts each word" because that can have
    # trouble with overlaps; need to check them all and
    # stop when we've got enough to reproduce the example)
    for ruleLen in range(1,len(words)+1): # (sort by len)
        for wStart in range(len(words)-ruleLen+1):
            yield words[wStart:wStart+ruleLen]
            # caller should do " ".join() before putting
            # it into rules dict

def checkCoverage(ruleAsWords,words,coveredFlags):
    # Updates coveredFlags and returns True if any changes
    # (if False, the new rule is redundant).
    # Don't worry about ybytes - assume the Yarrowsky-like
    # indicators have been calculated correctly across the
    # whole text so we don't need to re-check them now.
    ln = len(ruleAsWords)
    start = 0 ; changedFlags = False
    while start <= len(words)-ln:
        if words[start:start+ln] == ruleAsWords:
            if not all(coveredFlags[start:start+ln]):
                for i in range(start,start+ln):
                    coveredFlags[i] = True
                changedFlags = True
            start += ln
        else: start += 1
    return changedFlags

def potentially_bad_overlap(rulesAsWordsL,newRuleAsWords,markedDown):
    # Allow overlaps only if rule(s) being overlapped are
    # entirely included within newRule.  Otherwise could
    # get problems generating closures of overlaps.
    # (If newRule not allowed, caller to try a longer one)
    # Additionally, if allow_overlaps, allow ANY overlap as
    # long as it's not found in the marked-down text.
    if len(newRuleAsWords)==1 or primitive or ybytes: return False
    for ruleAsWords in rulesAsWordsL:
        if len(ruleAsWords)==1: continue
        if not len(ruleAsWords)==len(newRuleAsWords) and longerStartsOrEndsWithTheShorter(ruleAsWords,newRuleAsWords): continue
        for overlapSize in range(1,min([len(x) for x in [newRuleAsWords,ruleAsWords]])):
            if not (ruleAsWords[-overlapSize:] == newRuleAsWords[:overlapSize] or newRuleAsWords[-overlapSize:] == ruleAsWords[:overlapSize]): continue
            if not allow_overlaps: return True
            # Test to see if the examples "allow" this potentially-bad overlap
            def overlapOK(rAW): return not markDown(" ".join(rAW)) in markedDown
            if (ruleAsWords[-overlapSize:] == newRuleAsWords[:overlapSize] and not overlapOK(ruleAsWords[:-overlapSize]+newRuleAsWords)) or (newRuleAsWords[-overlapSize:] == ruleAsWords[:overlapSize] and not overlapOK(newRuleAsWords[:-overlapSize]+ruleAsWords)): return True

def longerStartsOrEndsWithTheShorter(l1,l2):
    if len(l1) > len(l2): l1,l2 = l2,l1
    return l2[:len(l1)]==l1 or l2[-len(l1):]==l1

def addRulesForPhrase(phrase,rules,rulesAsWordsL,markedUp,markedDown):
    words = splitWords(phrase)
    words = filter(lambda x:markDown(x).strip(),words) # filter out any that don't have base text (these will be input glitches, TODO: verify the annotation text is also just whitespace, warn if not)
    if not words: return 0,0
    covered = [False]*len(words)
    # first see how much is covered by existing rules
    # (don't have to worry about the order, as we've been
    # careful about overlaps)
    for r in rulesAsWordsL: # TODO: make this faster by somehow avoiding this iteration
        checkCoverage(r,words,covered)
        if all(covered): return len(covered),len(covered) # no new rules needed
    for ruleAsWords in all_possible_rules(words):
        rule = " ".join(ruleAsWords) ; yBytesRet = []
        if rule in rules or not test_rule(rule,markedUp,markedDown,yBytesRet) or potentially_bad_overlap(rulesAsWordsL,ruleAsWords,markedDown) or not checkCoverage(ruleAsWords,words,covered): continue # (checkCoverage must be last as it changes the coverage state)
        if len(yBytesRet): rules[rule] = yBytesRet[0]
        else: rules[rule] = [] # unconditional
        rulesAsWordsL.append(ruleAsWords)
        if all(covered): return len(covered),len(covered)
    # If get here, failed to completely cover the phrase.
    # ruleAsWords should be set to the whole-phrase rule.
    return len(filter(lambda x:x,covered)),len(covered)

def analyse():
    global corpus_unistr
    if not capitalisation: normalise_capitalisation()
    phrases = splitWords(corpus_unistr,phrases=True)
    
    # Due to the way we handle overlaps, it's better to process the shortest phrases first, as the longer phrases will yield more rule options and therefore more likely to be able to work around any "no-overlap" constraints imposed by already-processed examples.  Something like:
    p2 = []
    for p in phrases: p2.append((min([len(p.split(markupStart)),len(p.split(markupMid)),len(p.split(markupEnd))]),len(p2),p))
    p2.sort() # by length, then by original position
    phrases = [p[-1] for p in p2] ; del p2
    # (Note: if removing this sort, remove len from stats below)
    
    markedDown = unichr(1) + markDown(corpus_unistr) + unichr(1)
    if not reference_sep and not ybytes: del corpus_unistr # (won't need it again so free up some RAM)
    markedUp = unichr(1) + "/".join(phrases) + unichr(1)
    rules = {} ; rulesAsWordsL = []
    phraseNo = 0 ; lastUpdate = time.time()
    covered = toCover = 0
    while phraseNo < len(phrases):
        if time.time() >= lastUpdate + 2:
            sys.stderr.write("Checking phrases (%d%%/len=%d) rules=%d coverage=%d%% \r" % (int(100.0*phraseNo/len(phrases)),len(splitWords(phrases[phraseNo])),len(rules),int(100.0*covered/toCover)))
            lastUpdate = time.time()
        phrase = phrases[phraseNo] ; phraseNo += 1
        coveredA,toCoverA = addRulesForPhrase(phrase,rules,rulesAsWordsL,markedUp,markedDown)
        covered += coveredA ; toCover += toCoverA
    sys.stderr.write("\n")
    if ybytes: return rules
    else: return rules.keys()

def c_escape(unistr):
    # returns unistr encoded as outcode and escaped so can be put in C in "..."s
    return unistr.encode(outcode).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')

def outputParser(rules):
    # rules is a dictionary if ybytes, otherwise a list
    # ******************* what if rules is a dictionary ?
    sys.stderr.write("Generating byte cases...\n")
    byteSeq_to_action_dict = {}
    if type(rules)==type([]): rulesAndConds = [(x,[]) for x in rules]
    else: rulesAndConds = rules.items()
    for rule,conds in rulesAndConds:
        byteSeq = markDown(rule).encode(outcode)
        action = []
        words = splitWords(rule)
        doneWord = False
        for w in words:
            wStart = w.index(markupStart)+len(markupStart)
            wEnd = w.index(markupMid,wStart)
            text_unistr = w[wStart:wEnd]
            mStart = wEnd+len(markupMid)
            annotation_unistr = w[mStart:w.index(markupEnd,mStart)]
            if doneWord: action.append("s();")
            doneWord = True
            action.append('o("%s","%s");' % (c_escape(text_unistr),c_escape(annotation_unistr)))
        byteSeq_to_action_dict[byteSeq] = (' '.join(action),conds)
    longest_rule_len = max([len(b) for b in byteSeq_to_action_dict.keys()])
    longest_rule_len = max(ybytes*2, longest_rule_len) # make sure the half-bufsize is at least ybytes*2, so that a read-ahead when pos is ybytes from the end, resulting in a shift back to the 1st half of the buffer, will still leave ybytes from the beginning, so yar() can look ybytes-wide in both directions
    print c_start.replace('%%LONGEST_RULE_LEN%%',str(longest_rule_len)).replace("%%YBYTES%%",str(ybytes))
    subFuncL = []
    ret = stringSwitch(byteSeq_to_action_dict,subFuncL)
    print "\n".join(subFuncL + ret)
    print c_end
    print
    del byteSeq_to_action_dict,subFuncL,ret
    print "/* Tab-delimited summary of above rules:"
    outputRulesSummary(rules)
    print "*/"

def outputRulesSummary(rules):
    # (summary because we don't here specify which part
    # of the annotation goes with which part of the text, plus
    # we remove /* and */ so it can be placed into a C comment)
    sys.stderr.write("Writing rules summary...\n")
    if summary_omit: omit=set(opentxt(summary_omit).read().split("\n"))
    else: omit=[]
    if reference_sep:
        references = corpus_unistr.split(reference_sep)
        def refs(r):
            ret = []
            for ref in references:
                if r in ref and ref_name_end in ref:
                    refname,ref = ref.split(ref_name_end,1)
                    ret.append(refname)
                    if len(ret)==maxrefs: break
            if ret: return "\t"+"; ".join(ret)
            else: return ""
    else:
        def refs(r): return ""
    if type(rules)==type([]): annotOrigRuleCondList = [(annotationOnly(r),markDown(r),r,[]) for r in rules]
    else: annotOrigRuleCondList = [(annotationOnly(k),markDown(k),k,v) for k,v in rules.items()]
    for annot,orig,rule,conditions in sorted(annotOrigRuleCondList):
        toPrn = orig.encode(outcode)+"\t"+annot.encode(outcode)
        if not type(rules)==type([]):
            toPrn += "\t"
            if conditions: toPrn += "if near "+" or ".join(conditions).encode(outcode)
        if not toPrn in omit: print (toPrn+refs(rule).encode(outcode)).replace('/*','').replace('*/','')

def isatty(f): return hasattr(f,"isatty") and f.isatty()
    
if isatty(sys.stdout):
    if summary_only:
        sys.stderr.write("WARNING: Rules summary will be written to STANDARD OUTPUT\nYou might want to redirect it to a file or a pager such as 'less'\n")
        c_filename = None
    else:
        sys.stdout = open(c_filename,"w")
        sys.stderr.write("stdout is not piped, so writing to "+c_filename+"\n")
else: c_filename = None
def opentxt(fname):
    if fname.endswith(".gz"):
        import gzip ; return gzip.open(fname)
    elif fname.endswith(".bz2"):
        import bz2 ; return bz2.BZ2File(fname)
    else: return open(fname)
if infile: infile=opentxt(infile)
else:
    infile = sys.stdin
    if isatty(infile):
        sys.stderr.write("Reading from standard input\n(If that's not what you wanted, press Ctrl-C and run again with --help)\n")
corpus_unistr = infile.read().decode(incode)
rules = analyse() # dict if ybytes, otherwise list
if summary_only: outputRulesSummary(rules)
else: outputParser(rules)
del rules
sys.stderr.write("Done\n")
if c_filename:
    sys.stdout.close()
    cmd = c_compiler+" \""+c_filename+"\""
    sys.stderr.write(cmd+"\n")
    os.system(cmd)
