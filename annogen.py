#!/usr/bin/env python

program_name = "Annotator Generator v0.371 (c) 2012 Silas S. Brown"

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
import sys,os,tempfile,time,re
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
                  help="The string that occurs in the middle of a piece of markup in the input examples, with the word on its left and the added markup on its right (or the other way around if mreverse is set); default %default")

parser.add_option("--mend",
                  dest="markupEnd",
                  default="</rt></ruby>",
                  help="The string that ends a piece of annotation markup in the input examples; default %default")

parser.add_option("--mreverse",
                  action="store_true",default=False,
                  help="Specifies that the annotation markup is reversed, so the text BEFORE mmid is the annotation and the text AFTER it is the base text")

parser.add_option("--reference-sep",
                  help="Reference separator code used in the example input.  If you want to keep example source references for each rule, you can label the input with 'references' (chapter and section numbers or whatever), and use this option to specify what keyword or other markup the input will use between each 'reference'.  The name of the next reference will be whatever text immediately follows this string.  Note that the reference separator, and the reference name that follows it, should not be part of the text itself and should therefore not be part of any annotation markup.  If this option is not set then references will not be tracked.")

parser.add_option("--ref-name-end",default=" ",
                  help="Sets what the input uses to END a reference name.  The default is a single space, so that the first space after the reference-sep string will end the reference name.")

parser.add_option("--ref-pri",
                  help="Name of a reference to be considered \"high priority\" for Yarowsky-like seed collocations (if these are in use).  Normally the Yarowsky-like logic tries to identify a \"default\" annotation based on what is most common in the examples, with the exceptions indicated by collocations.  If however a word is found in a high priority reference then the first annotation found in that reference will be considered the ideal \"default\" even if it's in a minority in the examples; everything else will be considered as an exception.  In languages without spaces, this override should normally be used only for one-character words; if used with longer words it might have unexpected effects on rule-overlap ambiguities.")

parser.add_option("-s", "--spaces",
                  action="store_false",
                  dest="removeSpace",
                  default=True,
                  help="Set this if you are working with a language that uses whitespace in its non-markedup version (not fully tested).  The default is to assume that there will not be any whitespace in the language, which is correct for Chinese and Japanese.")

parser.add_option("-c", "--capitalisation",
                  action="store_true",
                  default=False,
                  help="Don't try to normalise capitalisation in the input.  Normally, to simplify the rules, the analyser will try to remove start-of-sentence capitals in annotations, so that the only remaining words with capital letters are the ones that are ALWAYS capitalised such as names.  (That's not perfect: it's possible that some words will always be capitalised just because they happen to never occur mid-sentence in the examples.)  If this option is used, the analyser will instead try to \"learn\" how to predict the capitalisation of ALL words (including start of sentence words) from their contexts.") # TODO: make the C program put the sentence capitals back

parser.add_option("--glossfile",
                  help="Filename of a text file (or a compressed .gz or .bz2 file) to read auxiliary \"gloss\" information.  Each line of this should be of the form: word (tab) annotation (tab) gloss.  When the compiled annotator generates ruby markup, it will add the gloss string as a popup title whenever that word is used with that annotation.  The annotation field may be left blank to indicate that the gloss will appear for any annotation of that word.  The entries in glossfile do NOT affect the annotation process itself, so it's not necessary to completely debug glossfile's word segmentation etc.")

#  =========== OUTPUT OPTIONS ==============

parser.add_option("--c-filename",default=tempfile.gettempdir()+os.sep+"annotator.c",help="Where to write the C program if standard output is not connected to a pipe. Defaults to annotator.c in the system temporary directory (the program might be large, especially if Yarowsky indicators are not used, so it's best not to use a server home directory where you might have limited quota). If standard output is connected to a pipe, then this option is ignored and C code is written to the pipe instead.")

parser.add_option("--c-compiler",default="gcc -o annotator"+exe,help="The C compiler to run if standard output is not connected to a pipe. You can add options (remembering to enclose this whole parameter in quotes if it contains spaces), but if the C program is large then adding optimisation options may make the compile take a LONG time. If standard output is connected to a pipe, then this option is ignored because the C code will simply be written to the pipe. Default: %default") # -Os can take a lot longer; on 64-bit distros -m32 won't always work (and won't necessarily give a smaller program)

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
                  help="Look for candidate Yarowsky seed-collocations within this number of bytes of the end of a word.  If this is set then overlaps and rule conflicts will be allowed if the seed collocations can be used to distinguish between them.  Markup examples that are completely separate (e.g. sentences from different sources) must have at least this number of bytes between them.")
parser.add_option("--ybytes-max",default=0,
                  help="Extend the Yarowsky seed-collocation search to check over larger ranges up to this maximum.  If this is set then several ranges will be checked in an attempt to determine the best one for each word, but see also ymax-threshold.")
parser.add_option("--ymax-threshold",default=1,
                  help="Limits the length of word that receives the narrower-range Yarowsky search when ybytes-max is in use. For words longer than this, the search will go directly to ybytes-max. This is for languages where the likelihood of a word's annotation being influenced by its immediate neighbours more than its distant collocations increases for shorter words, and less is to be gained by comparing different ranges when processing longer words. Setting this to 0 means no limit, i.e. the full range will be explored on ALL Yarowsky checks.")
parser.add_option("--ybytes-step",default=3,
                  help="The increment value for the loop between ybytes and ybytes-max")
parser.add_option("--warn-yarowsky",
                  action="store_true",default=False,
                  help="Warn when absolutely no distinguishing Yarowsky seed collocations can be found for a word in the examples")
parser.add_option("--yarowsky-all",
                  action="store_true",default=False,
                  help="Accept Yarowsky seed collocations even from input characters that never occur in annotated words (this might include punctuation and example-separation markup)")

parser.add_option("--single-words",
                  action="store_true",default=False,
                  help="Do not consider any rule longer than 1 word, although it can still have Yarowsky seed collocations if -y is set. This speeds up the search, but at the expense of thoroughness. You might want to use this in conjuction with -y to make a parser quickly. It is like -P (primitive) but without removing the conflict checks.")

sys.stderr.write(program_name+"\n") # not sys.stdout, because may or may not be showing --help (and anyway might want to process the help text for website etc)
options, args = parser.parse_args()
globals().update(options.__dict__)

if primitive and ybytes: sys.stderr.write("Warning: primitive will override ybytes\n")
if ybytes: ybytes=int(ybytes)
if ybytes_max: ybytes_max=int(ybytes_max)
else: ybytes_max = ybytes
ybytes_step = int(ybytes_step)
maxrefs = int(maxrefs)
ymax_threshold = int(ymax_threshold)

def stringSwitch(byteSeq_to_action_dict,subFuncL,funcName="topLevelMatch",subFuncs={},inTopFunc=True): # ("topLevelMatch" is also mentioned in the C code)
    # make a function to switch on a large number of variable-length string cases without repeated lookahead for each case
    # (may still backtrack if no words or no suffices match)
    # byteSeq_to_action_dict is really a byte sequence to [(action, OR-list of Yarowsky-like indicators which are still in Unicode)], the latter will be c_escape()d
    # can also be byte seq to [(action,(OR-list,nbytes))] but only if OR-list is not empty, so value[1] will always be false if OR-list is empty
    allBytes = set(b[0] for b in byteSeq_to_action_dict.iterkeys() if b)
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
    if "" in byteSeq_to_action_dict and len(byteSeq_to_action_dict) > 1 and len(byteSeq_to_action_dict[""])==1 and not byteSeq_to_action_dict[""][0][1] and all((len(a)==1 and a[0][0].startswith(byteSeq_to_action_dict[""][0][0]) and not a[0][1]) for a in byteSeq_to_action_dict.itervalues()):
        # there's an action in common for this and all subsequent matches, and no Yarowsky-like indicators, so we can do the common action up-front
        if inTopFunc: ret.append("s(ns);")
        # else this will already have been done when the caller reached this part of the code
        ret.append(byteSeq_to_action_dict[""][0][0])
        l = len(byteSeq_to_action_dict[""][0][0])
        byteSeq_to_action_dict = dict((x,[(y[l:],z)]) for x,[(y,z)] in byteSeq_to_action_dict.iteritems())
        # and, since we'll be returning no matter what,
        # we can put the inner switch in a new function
        # (even if not re-used, this helps gcc speed)
        # + DON'T save/restore pos around it (it itself
        # will do any necessary save/restore pos)
        del ret[savePos] ; savePos = None
        del byteSeq_to_action_dict[""]
        newFunc = "\n".join(stringSwitch(byteSeq_to_action_dict,subFuncL,"NewFunc",subFuncs,False))
        byteSeq_to_action_dict[""] = [("",[])] # for the end of this func
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
      use_if = (len(allBytes)==1)
      if not use_if: ret.append("switch(NEXTBYTE) {")
      for case in sorted(allBytes):
        if 32<=ord(case)<127 and case!="'": cstr="'%c'" % case
        else: cstr=ord(case)
        if use_if: ret.append("if(NEXTBYTE==%s) {" % cstr)
        else: ret.append("case %s:" % cstr)
        ret += ["  "+x for x in stringSwitch(dict([(k[1:],v) for k,v in byteSeq_to_action_dict.iteritems() if k and k[0]==case]),subFuncL,None,subFuncs,inTopFunc)]
        if not use_if and not "return;" in ret[-1]: ret.append("  break;")
      ret.append("}") # end of switch or if
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
        # so execute one of the "" actions and return
        # (which one, if any, depends on the Yarowsky-like indicators; there should be at most one "default" action without indicators)
        default_action = ""
        for action,conds in byteSeq_to_action_dict[""]:
            if conds:
                assert action, "conds without action in "+repr(byteSeq_to_action_dict[""])
                if type(conds)==tuple:
                    conds,nbytes = conds
                    ret.append("setnear(%d);" % nbytes)
                ret.append("if ("+" || ".join("near(\""+c_escape(c)+"\")" for c in conds)+") {")
                if inTopFunc: ret.append("s(ns);")
                ret.append((action+" return;").strip())
                ret.append("}")
            else:
                assert not default_action, "More than one default action in "+repr(byteSeq_to_action_dict[""]) # This might indicate invalid markup in the corpus - see TODO in yarowsky_indicators
                default_action = action
        if inTopFunc and default_action: ret.append("s(ns);")
        if default_action or not byteSeq_to_action_dict[""]: ret.append((default_action+" return;").strip()) # (return only if there was a default action, OR if an empty "" was in the dict with NO conditional actions (e.g. from the common-case optimisation above).  Otherwise, if there were conditional actions but no default, we didn't "match" anything if none of the conditions were satisfied.)
    return ret # caller does '\n'.join

c_start = "/* -*- coding: "+outcode+r""" -*- */
#include <stdio.h>
#include <string.h>

/* To include this code in another program,
   define the ifndef'd macros below + define Omit_main */
#ifndef NEXTBYTE
/* Default definition of NEXTBYTE etc is to use stdin */
enum { Half_Bufsize = %%LONGEST_RULE_LEN%% };
enum { ybytes = %%YBYTES%% }; /* for Yarowsky matching, minimum readahead */
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
static int nearbytes = ybytes;
#define setnear(n) (nearbytes = (n))
static int near(char* string) {
  /* for Yarowsky-like matching */
  size_t offset = filePtr-bufStart, l=strlen(string),
         maxPos = bufLen;
  if (maxPos >= l) maxPos -= l; else return 0;
  if (offset+nearbytes>l && maxPos > offset+nearbytes-l)
    maxPos = offset+nearbytes-l;
  else maxPos = 0; // (don't let it go below 0, as size_t is usually unsigned)
  if (offset>nearbytes) offset-=nearbytes; else offset = 0;
  // can use strnstr(haystack,needle,n) if on a BSD system
  while (offset <= maxPos) {
    if(!strncmp(lookahead+offset,string,l)) return 1;
    offset++;
  }
  return 0;
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
#define OutWrite3(fmt,a,b,c) printf(fmt,a,b,c)
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
static void o2(const char *word,const char *annot,const char *title) {
  if (annotation_mode == ruby_markup)
    OutWrite3("<ruby title=\"%s\"><rb>%s</rb><rt>%s</rt></ruby>",title,word,annot);
  else o(word,annot);
}
static void s(int needed) { if(needed) OutWriteByte(' '); }
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
    text = text.replace(markupEnd+markupStart, markupEnd+' '+markupStart) # force at least one breakpoint between each marked-up phrase (otherwise get problems later - much code assumes each item returned by splitWords contains at most 1 markup)
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

markupPattern = re.compile(re.escape(markupStart)+"(.*?)"+re.escape(markupMid)+"(.*?)"+re.escape(markupEnd))
whitespacePattern = re.compile(r"\s+")

def annotationOnly(text):
    ret = []
    for w in re.finditer(markupPattern,text):
        if mreverse: ret.append(w.group(1))
        else: ret.append(w.group(2))
    return ' '.join(ret)

def markDown(text):
    # Return just the original text, without markup
    if mreverse: group=r"\2"
    else: group=r"\1"
    text = re.sub(markupPattern,group,text)
    if removeSpace: text=re.sub(whitespacePattern,"",text)
    return text

def normalise_capitalisation():
    sys.stderr.write("Normalising capitalisation... ")
    # (as long as it's all Unicode strings, .lower() and .upper() work with accents etc)
    allWords = set() ; found = False
    for phrase in splitWords(corpus_unistr,phrases=True):
        allWords.update(splitWords(phrase))
    replaceDic = {}
    def replaceBatch(r):
        global corpus_unistr
        if r: corpus_unistr = re.sub('|'.join(re.escape(k) for k in r.iterkeys()),lambda k:r[k.group(0)],corpus_unistr) # (stackoverflow suggestion)
    for w in allWords:
        wl = w.lower()
        if not w==wl and wl in allWords:
            # This word is NOT always capitalised, just
            # sometimes at the start of a sentence.
            # To simplify rules, make it always lower.
            replaceDic[w] = wl
            if len(replaceDic)==2000: # limit the size of each batch - needed on some Pythons (e.g. Mac)
                replaceBatch(replaceDic)
                replaceDic = {}
    replaceBatch(replaceDic)
    sys.stderr.write("done\n")

def yarowsky_indicators(withAnnot_unistr,markedDown):
    # returns True if rule always works (or in majority of cases with ymajority), or lists enough indicators to cover example instances and returns (list, nbytes), or just list if empty.
    # (If too few indicators can be found, will list the ones it can, or empty if no clearly-distinguishable indicators can be found within ybytes of end of match.)
    nonAnnot=markDown(withAnnot_unistr)
    if nonAnnot in yPriorityDic: # TODO: enforce len==1 ?
        if yPriorityDic[nonAnnot] == withAnnot_unistr:
            # we want this case to be the default
            return True
        else: can_be_default = False # another is default, don't make this one default even if it occurs more
    else: can_be_default = True
    # First, find positions in markedDown which match withAnnot_unistr in corpus_unistr (not markedUp as that's harder to sync with markedDown, since markedUp contains /-separated annotated phrases whereas markedDown also contains the in-between bytes)
    if withAnnot_unistr in precalc_sets: okStarts=precalc_sets[withAnnot_unistr]
    else: okStarts=set(corpus_to_markedDown_map[s.start()] for s in re.finditer(re.escape(withAnnot_unistr), corpus_unistr))
    # now check for markedDown matches that *don't* have withAnnot_unistr
    badStarts=set(x.start() for x in re.finditer(re.escape(nonAnnot),markedDown) if not x.start() in okStarts)
    if not badStarts: return True # rule always works, no Yarowsky indicators needed
    if can_be_default and len(okStarts) > len(badStarts) and len(nonAnnot)==1: return True # duplicate of code below (can test for this case early before reducing-down badStarts)
    # Some of the badStarts can be ignored on the grounds that they should be picked up by other rules first: any where the nonAnnot match does not start at the start of a word (the rule matching the word starting earlier should get there first), and any where it starts at the start of a word that is longer than itself (the longest-first ordering should take care of this).  So keep only the ones where it starts at the start of a word and that word is no longer than len(nonAnnot).
    if mreverse: mdStart,mdEnd,mdSearchBack = markupMid,markupEnd,markupStart
    else: mdStart,mdEnd,mdSearchBack = markupStart,markupMid,None
    reallyBadStarts = []
    for s in re.finditer(re.escape(mdStart+nonAnnot[0])+".*?"+re.escape(mdEnd), corpus_unistr):
        s,e = s.start(),s.end()
        if e-s > len(mdStart+nonAnnot+mdEnd): continue # this word is too long, should be matched by a longer rule 1st
        if mdSearchBack: s=corpus_unistr.rfind(mdSearchBack,0,s)
        # TODO: the above assumes markupStart will never
        # be doubled, for example if it's '{{' and the
        # text contains '{{{' - if that happens, the call
        # to markDown for the whole corpus would have
        # taken out the outermost '{{'s, whereas this
        # rfind will find the innermost.  Consequently the
        # results will not be detected as the same and the
        # badStart will be thrown out unnecessarily.  If
        # undetected, this could ultimately lead to "More
        # than one default action" crashes as two or more
        # senses are both treated as majority because
        # their badStarts sets are erroneously too small;
        # however, it is now more likely to result in a
        # KeyError in corpus_to_markedDown_map, as only
        # true start positions are in that map.
        s = corpus_to_markedDown_map[s] # if KeyError, see comment above
        if s in badStarts: reallyBadStarts.append(s)
    badStarts = reallyBadStarts
    if not badStarts: return True
    # Now, if it's right more often than not:
    if can_be_default and len(okStarts) > len(badStarts):
        # could we have this as a "default" rule, with the other cases as exceptions that will be found first?
        if len(nonAnnot)==1: return True # should be safe, and should cover most "common short Chinese word with thousands of contexts" cases
        # If len 2 or more, it's risky because the correct solution could be to process just a fraction of the word now and the rest will become the start of a longer word, so we probably don't want it matching the whole lot by default unless can be sure about it
        # e.g. looking at rule AB, text ABC and correct segmentation is A BC, don't want it to 'greedily' match AB by default without positive indicators it should do so
        # Might get an exception if there is no possibility of a rule A in the examples, i.e. no markup of a word of length < nonAnnot whose marked-down version matches the start of nonAnnot in corpus_unistr:
        # if not re.search(re.escape(mdStart)+reduce(lambda x,y:re.escape(y)+"("+x+")?",reversed(list(nonAnnot[:-1])))+re.escape(mdEnd),corpus_unistr): return True
        # Might also have an exception if there is no possibility of a rule BC, i.e. no word in corpus_unistr whose marked-down version starts with any of the strings nonAnnot[1:] [2:] ... [-1:]
        # if not re.search(re.escape(mdStart)+reduce(lambda x,y:"("+x+")?"+re.escape(y),list(nonAnnot[1:])),corpus_unistr): return True
        # + might have an exception if can confirm from all badStarts that the marked-down version of the rule applied (if one starts at that badStart) is at least as long as nonAnnot
        # Or just directly check for "A BC" situations, i.e. can't find any possible SEQUENCE of rules that STARTS with ALL the characters in nonAnnot and that involves having them SPLIT across multiple words:
        if all(x.end()-x.start()==len(mdStart)+len(nonAnnot) for x in re.finditer(re.escape(mdStart)+(re.escape(mdEnd)+".*?"+re.escape(mdStart)).join(re.escape(c) for c in list(nonAnnot)),corpus_unistr)): return True
        # (This exception might under-match if there's the appearance of a split rule but it actually has extra non-marked-up text in between.  But it shouldn't over-match.)
    if len(okStarts) > 1000: sys.stderr.write("\nLarge collocation check (rule has %d matches + %d false positives), could take some time....  \n" % (len(okStarts),len(badStarts)))
    def tryNBytes(nbytes):
      def bytesAround(start): return within_Nbytes(markedDown,start+len(nonAnnot),nbytes)
      omitStr = chr(1).join(bytesAround(s) for s in badStarts)
      okStrs=[bytesAround(s) for s in okStarts]
      covered=[False]*len(okStrs)
      ret = []
      for indicatorStr in unique_substrings(okStrs,markedUp_unichars,lambda txt:txt in omitStr,lambda txt:sum(1 for s in okStrs if txt in s)):
          cChanged = False
          for i in xrange(len(okStrs)):
              if not covered[i] and indicatorStr in okStrs[i]: covered[i]=cChanged=True
          if cChanged: ret.append(indicatorStr)
          if all(covered): break
      return ret,sum(1 for x in covered if x),len(covered)

    if ybytes_max > ybytes and (not ymax_threshold or len(nonAnnot) <= ymax_threshold):
      retList = []
      for nbytes in range(ybytes,ybytes_max+1,ybytes_step):
        ret,covered,toCover = tryNBytes(nbytes)
        if covered==toCover and len(ret)==1: return (ret,nbytes) # a single indicator that covers everything will be better than anything else we'll find
        retList.append((-covered,len(ret),nbytes,toCover,ret)) # (1st 3 of these are the sort keys: maximum coverage, THEN minimum num indicators for the same coverage, THEN minimum nbytes (TODO: problems of very large nbytes might outweigh having more indicators; break if found 100% coverage by N?)  toCover should always ==len(okStarts).)
        # TODO: try finding an OR-combination of indicators at *different* proximity lengths ?
      retList.sort() ; ret = retList[0][-1]
    else: ret,retList = tryNBytes(ybytes_max)[0],None
    if not ret and warn_yarowsky: sys.stderr.write("Couldn't find ANY Yarowsky-like indicators for %s   \n" % (withAnnot_unistr.encode('utf-8')))
    # elif ybytes_max > ybytes: sys.stderr.write("Debugger: %s best coverage=%d/%d by %d indicators at nbytes=%d   \n" % (withAnnot_unistr.encode('utf-8'),-retList[0][0],retList[0][3],retList[0][1],retList[0][2]))
    # TODO: if partially but not completely covered, shouldn't entirely count the word as 'covered' in analyse()
    if not ret or not retList: return ret
    else: return ret,retList[0][2]

def unique_substrings(texts,allowedChars,omitFunc,valueFunc):
    # yield unique substrings of texts, in increasing length, with equal lengths sorted by highest score returned by valueFunc, and omitting any where omitFunc is true, or that uses any character not in allowedChars (allowedChars==None means all allowed)
    if allowedChars:
        # remove non-allowedChars from texts, splitting into smaller strings as necessary
        texts2 = []
        for text in texts:
            start = 0
            for i in xrange(len(text)):
                if not text[i] in allowedChars:
                    if i>start: texts2.append(text[start:i])
                    start=i+1
            if start<len(text): texts2.append(text[start:])
        texts=texts2
    if not texts: return
    length=1 ; maxlen = max(len(t) for t in texts)
    while length <= maxlen:
        ret=set()
        # sys.stderr.write("Finding (l=%d)... " % len(texts))
        for text in texts: ret.update(text[s:s+length] for s in xrange(len(text)-length+1))
        l=[(valueFunc(k),k) for k in ret if not omitFunc(k)]
        # if length == ybytes_max and not l: sys.stderr.write("Debugger: omitFunc was true for all %s\n" % repr(ret))
        l.sort() ; l.reverse()
        # sys.stderr.write("%d of length %d\n" % (len(l),length))
        for v,k in l: yield k
        length += 1

def within_Nbytes(markedDown,matchEndPos,nbytes):
    # return the Unicode characters within nbytes of matchEndPos, assuming the encoding will be outcode.  Used for the Yarowsky-like functions.
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
        # Doesn't have to be always right, but put the indicators in yBytesRet
        ybr = yarowsky_indicators(withAnnot_unistr,markedDown)
        if ybr==True or not ybr: return ybr
        yBytesRet.append(ybr) # (list of indicators, nbytes)
        return True
    def occurrences(haystack,needle): return len(haystack.split(needle))-1 # assumes haystack has non-needle terminators - have put these in with unichr(1)s below
    return occurrences(markedDown,markDown(withAnnot_unistr)) == occurrences(markedUp,withAnnot_unistr)

def all_possible_rules(words):
    if single_words: # (only consider 1-word rules)
        for w in words: yield [w]
        return
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
    # Don't worry about ybytes - assume the Yarowsky-like
    # indicators have been calculated correctly across the
    # whole text so we don't need to re-check them now.
    try: start = words.index(ruleAsWords[0])
    except ValueError: return False
    ln = len(ruleAsWords)
    changedFlags = False
    while start <= len(words)-ln:
        if words[start:start+ln] == ruleAsWords:
            if not all(coveredFlags[start:start+ln]):
                for i in range(start,start+ln):
                    coveredFlags[i] = True
                changedFlags = True
            start += ln
        else:
            try:
                start = words.index(ruleAsWords[0],start+1)
            except ValueError: break
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
        for overlapSize in range(1,min(len(x) for x in [newRuleAsWords,ruleAsWords])):
            if not (ruleAsWords[-overlapSize:] == newRuleAsWords[:overlapSize] or newRuleAsWords[-overlapSize:] == ruleAsWords[:overlapSize]): continue
            if not allow_overlaps: return True
            # Test to see if the examples "allow" this potentially-bad overlap
            def overlapOK(rAW): return not markDown(" ".join(rAW)) in markedDown
            if (ruleAsWords[-overlapSize:] == newRuleAsWords[:overlapSize] and not overlapOK(ruleAsWords[:-overlapSize]+newRuleAsWords)) or (newRuleAsWords[-overlapSize:] == ruleAsWords[:overlapSize] and not overlapOK(newRuleAsWords[:-overlapSize]+ruleAsWords)): return True

def longerStartsOrEndsWithTheShorter(l1,l2):
    if len(l1) > len(l2): l1,l2 = l2,l1
    return l2[:len(l1)]==l1 or l2[-len(l1):]==l1

class RulesAccumulator:
  def __init__(self):
    self.rules = {}
    self.rulesAsWords_By1stWord = {} # starting word -> list of possible rules (as wordlists) that might apply
    self.rulesAsWordsL = [] # all rules as words (used if not ybytes, TODO: integrate with rulesAsWords_By1stWord?)
    self.rejectedRules = set()
  def addRulesForPhrase(self,phrase,markedUp,markedDown):
    words = splitWords(phrase)
    words = filter(lambda x:markDown(x).strip(),words) # filter out any that don't have base text (these will be input glitches, TODO: verify the annotation text is also just whitespace, warn if not)
    if not words: return 0,0
    covered = [False]*len(words)
    # first see how much is covered by existing rules
    # (don't have to worry about the order, as we've been
    # careful about overlaps)
    for w in set(words):
     for ruleList in self.rulesAsWords_By1stWord.get(w,[]):
      for r in ruleList:
        checkCoverage(r,words,covered)
        if all(covered): return len(covered),len(covered) # no new rules needed
    for ruleAsWords in all_possible_rules(words):
        rule = " ".join(ruleAsWords) ; yBytesRet = []
        if rule in self.rules or rule in self.rejectedRules: continue
        if not test_rule(rule,markedUp,markedDown,yBytesRet) or potentially_bad_overlap(self.rulesAsWordsL,ruleAsWords,markedDown):
            self.rejectedRules.add(rule) # so we don't waste time evaluating it again (TODO: make sure rejectedRules doesn't get too big?)
            continue
        if not checkCoverage(ruleAsWords,words,covered): continue # (checkCoverage must be last as it changes the coverage state)
        if len(yBytesRet): self.rules[rule] = yBytesRet[0]
        else: self.rules[rule] = [] # unconditional
        self.rulesAsWordsL.append(ruleAsWords)
        if not ruleAsWords[0] in self.rulesAsWords_By1stWord: self.rulesAsWords_By1stWord[ruleAsWords[0]] = []
        self.rulesAsWords_By1stWord[ruleAsWords[0]].append(ruleAsWords)
        if all(covered): return len(covered),len(covered)
    # If get here, failed to completely cover the phrase.
    # ruleAsWords should be set to the whole-phrase rule.
    return sum(1 for x in covered if x),len(covered)

def analyse():
    global corpus_unistr
    if not capitalisation: normalise_capitalisation()

    if ybytes: # we'll need corpus_to_markedDown_map etc
        sys.stderr.write("Generating corpus map... ")
        global corpus_to_markedDown_map, precalc_sets
        corpus_to_markedDown_map = {} ; precalc_sets = {}
        muStart = downLenSoFar = 0
        for s in re.finditer(re.escape(markupStart), corpus_unistr):
            s=s.start()
            downLenSoFar += len(markDown(corpus_unistr[muStart:s]))
            muStart = s
            corpus_to_markedDown_map[s] = downLenSoFar+1 # +1 as there's a unichr(1) at start of markedDown
            # Added optimisation: do precalc_sets as well
            # (at least catch the 1-word cases)
            e=corpus_unistr.find(markupEnd,s)
            if e>-1:
                e += len(markupEnd)
                k = corpus_unistr[s:e]
                if k not in precalc_sets:
                    precalc_sets[k]=set()
                precalc_sets[k].add(corpus_to_markedDown_map[s])
        global yPriorityDic ; yPriorityDic = {}
        if ref_pri:
            sys.stderr.write("yPriorityDic ... ")
            for s in re.finditer(re.escape(reference_sep+ref_pri+ref_name_end), corpus_unistr):
                s = s.start()+len(reference_sep+ref_pri+ref_name_end)
                e = corpus_unistr.find(reference_sep,s)
                if e==-1: e=len(corpus_unistr)
                for w in splitWords(corpus_unistr[s:e]):
                    wd = markDown(w)
                    if wd in yPriorityDic: pass
                    else: yPriorityDic[wd] = w
        sys.stderr.write("done\n")

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
    if ybytes:
        global markedUp_unichars
        if yarowsky_all: markedUp_unichars = None
        else: markedUp_unichars = set(list((u"".join(markDown(p) for p in phrases))))
    accum = RulesAccumulator()
    phraseNo=phraseLastUpdate=0 ; lastUpdate = time.time()
    covered = toCover = 0 ; duplicates = {}
    for phraseNo in xrange(len(phrases)):
        phrase = phrases[phraseNo]
        if phrase in duplicates: continue # (not necessary but might speed things up a bit)
        if time.time() >= lastUpdate + 2:
            progress = "%.1f phrase/sec (%d%%/#w=%d) rules=%d cover=%d%%" % ((phraseNo-phraseLastUpdate)*1.0/(time.time()-lastUpdate),int(100.0*phraseNo/len(phrases)),len(splitWords(phrases[phraseNo])),len(accum.rules),int(100.0*covered/toCover))
            if warn_yarowsky: progress += (" rej=%d" % len(accum.rejectedRules))
            sys.stderr.write(progress+" \r")
            lastUpdate = time.time()
            phraseLastUpdate = phraseNo
        duplicates[phrase]=1
        coveredA,toCoverA = accum.addRulesForPhrase(phrase,markedUp,markedDown)
        covered += coveredA ; toCover += toCoverA
    sys.stderr.write("\n")
    if ybytes: return accum.rules
    else: return accum.rules.keys()

def c_escape(unistr):
    # returns unistr encoded as outcode and escaped so can be put in C in "..."s
    return unistr.encode(outcode).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')

def outputParser(rules):
    # rules is a dictionary if ybytes, otherwise a list
    sys.stderr.write("Generating byte cases...\n")
    glossDic = {}
    if glossfile:
        for l in opentxt(glossfile).xreadlines():
            if not l.strip(): continue
            l=l.decode(incode) # TODO: glosscode ?
            try: word,annot,gloss = l.split("\t",3)
            except: sys.stderr.write("Gloss: Ignoring incorrectly-formatted line "+l.strip()+"\n")
            word,annot,gloss = word.strip(),annot.strip(),gloss.strip()
            if not word or not gloss: continue
            if annot: glossDic[(word,annot)] = gloss
            else: glossDic[word] = gloss
    byteSeq_to_action_dict = {}
    if type(rules)==type([]): rulesAndConds = [(x,[]) for x in rules]
    else: rulesAndConds = rules.items()
    for rule,conds in rulesAndConds:
        byteSeq = markDown(rule).encode(outcode)
        action = []
        words = splitWords(rule)
        doneWord = gotAnnot = False
        for w in words:
            wStart = w.index(markupStart)+len(markupStart)
            wEnd = w.index(markupMid,wStart)
            text_unistr = w[wStart:wEnd]
            mStart = wEnd+len(markupMid)
            annotation_unistr = w[mStart:w.index(markupEnd,mStart)]
            if mreverse: text_unistr,annotation_unistr = annotation_unistr,text_unistr
            gloss = glossDic.get((text_unistr,annotation_unistr),glossDic.get(text_unistr,None))
            if doneWord: action.append("s(1);")
            doneWord = True
            if gloss: action.append('o2("%s","%s","%s");' % (c_escape(text_unistr),c_escape(annotation_unistr),c_escape(gloss.replace('&','&amp;').replace('"','&quot;'))))
            else: action.append('o("%s","%s");' % (c_escape(text_unistr),c_escape(annotation_unistr)))
            if annotation_unistr or gloss: gotAnnot = True
        if not gotAnnot: continue # probably some spurious o("{","") rule that got in due to markup corruption
        if not byteSeq in byteSeq_to_action_dict: byteSeq_to_action_dict[byteSeq] = []
        byteSeq_to_action_dict[byteSeq].append((' '.join(action),conds))
    longest_rule_len = max(len(b) for b in byteSeq_to_action_dict.iterkeys())
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
                    app = ref[:ref.index(ref_name_end)]
                    if not app in ret: ret.append(app)
                    if len(ret)==maxrefs: break
            if ret: return "\t"+"; ".join(ret)
            else: return ""
    else:
        def refs(r): return ""
    if type(rules)==type([]): annotOrigRuleCondList = [(annotationOnly(r),markDown(r),r,[]) for r in rules]
    else: annotOrigRuleCondList = [(annotationOnly(k),markDown(k),k,v) for k,v in rules.iteritems()]
    for annot,orig,rule,conditions in sorted(annotOrigRuleCondList):
        toPrn = orig.encode(outcode)+"\t"+annot.encode(outcode)
        if not type(rules)==type([]):
            toPrn += "\t"
            if conditions:
                if type(conditions)==tuple: toPrn += "if within "+str(conditions[1])+" bytes of "+" or ".join(conditions[0]).encode(outcode)
                else: toPrn += "if near "+" or ".join(conditions).encode(outcode)
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
    cmd = c_compiler+" \""+c_filename+"\"" # (the -o option is part of c_compiler)
    sys.stderr.write(cmd+"\n")
    os.system(cmd)
