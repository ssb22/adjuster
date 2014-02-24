#!/usr/bin/env python

program_name = "Annotator Generator v0.543 (c) 2012-13 Silas S. Brown"

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
import sys,os,os.path,tempfile,time,re
if not "mac" in sys.platform and not "darwin" in sys.platform and ("win" in sys.platform or "mingw32" in sys.platform): exe=".exe" # Windows, Cygwin, etc
else: exe=""

try: import cPickle as pickle
except:
  try: import pickle
  except: pickle = None

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

parser.add_option("-w", "--annot-whitespace",
                  action="store_true",
                  default=False,
                  help="Don't try to normalise the use of whitespace and hyphenation in the example annotations.  Normally the analyser will try to do this, to reduce the risk of missing possible rules due to minor typographical variations.") # TODO: can this be extended to the point where the words 'try to' can be deleted ?  see comments

parser.add_option("--glossfile",
                  help="Filename of an optional text file (or compressed .gz or .bz2 file) to read auxiliary \"gloss\" information.  Each line of this should be of the form: word (tab) annotation (tab) gloss.  When the compiled annotator generates ruby markup, it will add the gloss string as a popup title whenever that word is used with that annotation.  The annotation field may be left blank to indicate that the gloss will appear for any annotation of that word.  The entries in glossfile do NOT affect the annotation process itself, so it's not necessary to completely debug glossfile's word segmentation etc.")

parser.add_option("--manualrules",
                  help="Filename of an optional text file (or compressed .gz or .bz2 file) to read extra, manually-written rules.  Each line of this should be a marked-up phrase (in the input format) which is to be unconditionally added as a rule.  Use this sparingly, because these rules are not taken into account when generating the others and they will be applied regardless of context (although a manual rule might fail to activate if the annotator is part-way through processing a different rule).") # (or if there's a longer automatic match)

#  =========== OUTPUT OPTIONS ==============

parser.add_option("--rulesFile",help="Filename of an optional auxiliary binary file to hold the accumulated rules. Adding .gz or .bz2 for compression is acceptable. If this is set then the rules will be written to it (in binary format) as well as to the output. Additionally, if the file already exists then rules will first of all be read from it before generating any new rules. This might be useful if you have made some small additions to the examples and would like these to be incorporated without a complete re-run. It might not work as well as a re-run but it should be faster. If using a rulesFile then you must keep the same input (you may make small additions etc, but it won't work properly if you delete many examples or change the format between runs) and you must keep the same ybytes-related options if any.") # You may however change whether or not a --single-words / --max-words option applies to the new examples (but hopefully shouldn't have to)

parser.add_option("--no-input",
                  action="store_true",default=False,
                  help="Don't actually read the input, just use the rules that were previously stored in rulesFile. This can be used to increase speed if the only changes made are to the output options. You should still specify the input formatting options (which should not change), and any glossfile or manualrules options (which may change).")

parser.add_option("--c-filename",default=tempfile.gettempdir()+os.sep+"annotator.c",help="Where to write the C program if standard output is not connected to a pipe. Defaults to annotator.c in the system temporary directory (the program might be large, especially if Yarowsky indicators are not used, so it's best not to use a server home directory where you might have limited quota). If standard output is connected to a pipe, then this option is ignored and C code is written to the pipe instead.")

parser.add_option("--c-compiler",default="cc -o annotator"+exe,help="The C compiler to run if standard output is not connected to a pipe. The default is to use the \"cc\" command which usually redirects to your \"normal\" compiler. You can add options (remembering to enclose this whole parameter in quotes if it contains spaces), but if the C program is large then adding optimisation options may make the compile take a LONG time. If standard output is connected to a pipe, then this option is ignored because the C code will simply be written to the pipe. Default: %default")
# If compiling an experimental annotator quickly, you might try tcc as it compiles fast. If tcc is not available on your system then clang might compile faster than gcc.
# (BUT tcc can have problems on Raspberry Pi see http://www.raspberrypi.org/phpBB3/viewtopic.php?t=30036&p=263213; can be best to cross-compile, e.g. from a Mac use https://github.com/UnhandledException/ARMx/wiki/Sourcery-G---Lite-for-ARM-GNU-Linux-(2009q3-67)-for-Mac-OS-X and arm-none-linux-gnueabi-gcc)
# In large rulesets with --max-or-length=0 and --nested-switch, gcc takes time and gcc -Os can take a LOT longer, and CINT, Ch and picoc run out of memory.  Without these options the overhead of gcc's -Os isn't so bad (and does save some room).
# clang with --max-or-length=100 and --nested-switch=False is not slowed much by -Os (slowed considerably by -O3). -Os and -Oz gave same size in my tests.
# on 64-bit distros -m32 won't always work and won't necessarily give a smaller program

parser.add_option("--max-or-length",default=100,help="The maximum number of items allowed in an OR-expression in the C code (used when ybytes is in effect). When an OR-expression becomes larger than this limit, it will be made into a function. 0 means unlimited, which works for tcc and gcc; many other compilers have limits. Default: %default")

parser.add_option("--nested-switch",
                  action="store_true",default=False,
                  help="Allow C switch() constructs to be nested to arbitrary depth. This can result in a smaller executable, but it does slow down most C compilers.") # tcc is still fast (although that doesn't generate the smallest executables anyway)

parser.add_option("--outcode",default="utf-8",
                  help="Character encoding to use in the generated parser and rules summary (default %default, must be ASCII-compatible i.e. not utf-16)")

parser.add_option("-S", "--summary-only",
                  action="store_true",default=False,
                  help="Don't generate a parser, just write the rules summary to standard output")

parser.add_option("--no-summary",
                  action="store_true",default=False,
                  help="Don't add a rules summary at the end of the parser")

parser.add_option("-O", "--summary-omit",
                  help="Filename of a text file (or a compressed .gz or .bz2 file) specifying what should be omitted from the rules summary.  Each line should be a word or phrase, a tab, and its annotation (without the mstart/mmid/mend markup).  If any rule in the summary exactly matches any of the lines in this text file, then that rule will be omitted from the summary (but still included in the parser).  Use for example to take out of the summary any entries that correspond to things you already have in your dictionary, so you can see what's new.")

parser.add_option("--maxrefs",default=3,
                  help="The maximum number of example references to record in each summary line, if references are being recorded.  Default is %default; 0 means unlimited.")

parser.add_option("--norefs",
                  action="store_true",default=False,
                  help="Don't write references in the rules summary.  Use this if you need to specify reference-sep and ref-name-end for the ref-pri option but you don't actually want references in the summary (omitting references makes summary generation faster).  This option is automatically turned on if --no-input is specified.")

parser.add_option("--newlines-reset",
                  action="store_false",
                  dest="ignoreNewlines",
                  default=True,
                  help="Have the C program reset its state on every newline byte. By default newlines do not affect state such as whether a space is required before the next word, so that if the C program is used with Web Adjuster's htmlText option (which defaults to using newline separators) the spacing should be handled sensibly when there is HTML markup in mid-sentence.")

parser.add_option("--obfuscate",
                  action="store_true",default=False,
                  help="Obfuscate annotation strings in C code, as a deterrent to casual snooping of the compiled binary with tools like 'strings' (does NOT stop determined reverse engineering)")

parser.add_option("--javascript",
                  action="store_true",default=False,
                  help="Instead of generating C code, generate JavaScript.  This might be useful if you want to run an annotator on a device that has a JS interpreter but doesn't let you run native code.  The JS will be table-driven to make it load faster (and --no-summary will also be set).  See comments at the start for usage.") # but it's better to use the C version if you're in an environment where 'standard input' makes sense

parser.add_option("--python",
                  action="store_true",default=False,
                  help="Instead of generating C code, generate a Python module.  Similar to the Javascript option, this is for when you can't run native code.")

parser.add_option("--reannotator",
                  help="Shell command through which to pipe each word of the original text to obtain new annotation for that word.  This might be useful as a quick way of generating a new annotator (e.g. for a different topolect) while keeping the information about word separation and/or glosses from the previous annotator, but it is limited to commands that don't need to look beyond the boundaries of each word.  (If the command is prefixed by a # character, it will be given the word's existing annotation instead of its original text.)  The command should treat each line of its input independently, and both its input and its output should be in the encoding specified by --outcode.") # TODO: reannotatorCode instead? (see other 'reannotatorCode' TODOs)
# (Could just get the reannotator to post-process the 1st annotator's output, but that might be slower than generating an altered annotator with it)

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
parser.add_option("--max-words",default=0,
                  help="Limits the number of words in a rule; rules longer than this are not considered.  0 means no limit.  --single-words is equivalent to --max-words=1.  If you need to limit the search time, and are using -y, it should suffice to use --single-words for a quick annotator or --max-words=5 for a more thorough one.")

parser.add_option("--checkpoint",help="Periodically save checkpoint files in the specified directory.  These files can save time when starting again after a reboot (and it's easier than setting up Condor etc).  As well as a protection against random reboots, this can be used for scheduled reboots: if file called ExitASAP appears in the checkpoint directory, annogen will checkpoint, remove the ExitASAP file, and exit.  After a run has completed, the checkpoint directory should be removed, unless you want to re-do the last part of the run for some reason.")
# (Condor can checkpoint an application on Win/Mac/Linux but is awkward to set up.  Various Linux and BSD application checkpoint approaches also exist; another option is virtualisation.)

parser.add_option("-d","--diagnose",help="Output some diagnostics for the specified word. Use this option to help answer \"why doesn't it have a rule for...?\" issues. This option expects the word without markup and uses the system locale (UTF-8 if it cannot be detected).")

parser.add_option("--diagnose-limit",default=10,help="Maximum number of phrases to print diagnostics for (0 means unlimited); can be useful when trying to diagnose a common word in rulesFile without re-evaluating all phrases that contain it. Default: %default")

parser.add_option("--time-estimate",
                  action="store_true",default=False,
                  help="Estimate time to completion.  The code to do this is unreliable and is prone to underestimate.  If you turn it on, its estimate is displayed at the end of the status line as days, hours or minutes.") # Unreliable because the estimate assumes 'phrases per minute' will remain constant on average, whereas actually it will decrease because the more complex phrases are processed last

sys.stderr.write(program_name+"\n") # not sys.stdout, because may or may not be showing --help (and anyway might want to process the help text for website etc)
options, args = parser.parse_args()
globals().update(options.__dict__)

sys.setcheckinterval(32767) # won't be using threads or signals, so don't have to check for them very often
import gc ; gc.disable() # should be OK if we don't create cycles (TODO: run gc.collect() manually after init, just in case?)

if primitive and ybytes: sys.stderr.write("Warning: primitive will override ybytes\n")
if ybytes: ybytes=int(ybytes)
if ybytes_max: ybytes_max=int(ybytes_max)
else: ybytes_max = ybytes
ybytes_step = int(ybytes_step)
maxrefs = int(maxrefs)
ymax_threshold = int(ymax_threshold)
def errExit(msg):
  sys.stderr.write(msg+"\n") ; sys.exit(1)
if ref_pri and not (reference_sep and ref_name_end): errExit("ref-pri option requires reference-sep and ref-name-end to be set")
if javascript or python:
    if javascript and python: errExit("Outputting both Javascript and Python on the same run is not yet implemented")
    if not outcode=="utf-8": errExit("outcode must be utf-8 when using Javascript or Python")
    if obfuscate: errExit("obfuscate not yet implemented for the Javascript or Python version") # (and it would probably slow down the JS far too much if it were)
    if c_filename.endswith(".c"):
      if javascript: c_filename = c_filename[:-2]+".js"
      else: c_filename = c_filename[:-2]+".py"
try:
  import locale
  terminal_charset = locale.getdefaultlocale()[1]
except: terminal_charset = "utf-8"
if diagnose: diagnose=diagnose.decode(terminal_charset)
diagnose_limit = int(diagnose_limit)
max_words = int(max_words)
if single_words: max_words = 1

def nearCall(conds,subFuncs,subFuncL):
  # returns what to put in the if() for ybytes near() lists
  if not max_or_length or len(conds) <= max_or_length:
    return " || ".join("near(\""+c_escape(c,0)+"\")" for c in conds)
  return subFuncCall("static int NewFunc() {\n"+"\n".join("if("+nearCall(conds[i:j],subFuncs,subFuncL)+") return 1;" for i,j in zip(range(0,len(conds),max_or_length),range(max_or_length,len(conds),max_or_length)+[len(conds)]))+"\nreturn 0;}",subFuncs,subFuncL)

def subFuncCall(newFunc,subFuncs,subFuncL):
  if newFunc in subFuncs:
    # we generated an identical one before
    subFuncName=subFuncs[newFunc]
  else:
    subFuncName="match%d" % len(subFuncs)
    subFuncs[newFunc]=subFuncName
    subFuncL.append(newFunc.replace("NewFunc",subFuncName,1))
  return subFuncName+"()" # the call (without a semicolon)

def stringSwitch(byteSeq_to_action_dict,subFuncL,funcName="topLevelMatch",subFuncs={}): # ("topLevelMatch" is also mentioned in the C code)
    # make a function to switch on a large number of variable-length string cases without repeated lookahead for each case
    # (may still backtrack if no words or no suffices match)
    # byteSeq_to_action_dict is really a byte sequence to [(action, OR-list of Yarowsky-like indicators which are still in Unicode)], the latter will be c_escape()d
    # can also be byte seq to [(action,(OR-list,nbytes))] but only if OR-list is not empty, so value[1] will always be false if OR-list is empty
    allBytes = set(b[0] for b in byteSeq_to_action_dict.iterkeys() if b)
    ret = []
    if funcName:
        ret.append("static void %s() {" % funcName)
        savePos = len(ret)
        ret.append("{ SAVEPOS;")
    elif "" in byteSeq_to_action_dict and len(byteSeq_to_action_dict) > 1:
        # no funcName, but might still want to come back here as there's a possible action at this level
        savePos = len(ret)
        ret.append("{ SAVEPOS;")
    else: savePos = None
    called_subswitch = False
    if "" in byteSeq_to_action_dict and len(byteSeq_to_action_dict) > 1 and len(byteSeq_to_action_dict[""])==1 and not byteSeq_to_action_dict[""][0][1] and all((len(a)==1 and a[0][0].startswith(byteSeq_to_action_dict[""][0][0]) and not a[0][1]) for a in byteSeq_to_action_dict.itervalues()):
        # there's an action in common for this and all subsequent matches, and no Yarowsky-like indicators, so we can do the common action up-front
        ret.append(byteSeq_to_action_dict[""][0][0])
        l = len(byteSeq_to_action_dict[""][0][0])
        byteSeq_to_action_dict = dict((x,[(y[l:],z)]) for x,[(y,z)] in byteSeq_to_action_dict.iteritems())
        # and, since we'll be returning no matter what,
        # we can put the inner switch in a new function
        # (even if not re-used, this helps compiler speed)
        # + DON'T save/restore pos around it (it itself
        # will do any necessary save/restore pos)
        del ret[savePos] ; savePos = None
        del byteSeq_to_action_dict[""]
        newFunc = "\n".join(stringSwitch(byteSeq_to_action_dict,subFuncL,"NewFunc",subFuncs))
        byteSeq_to_action_dict[""] = [("",[])] # for the end of this func
        ret.append(subFuncCall(newFunc,subFuncs,subFuncL)+"; return;")
    elif allBytes:
      # deal with all actions except "" first
      use_if = (len(allBytes)==1)
      if not use_if: ret.append("switch(NEXTBYTE) {")
      for case in sorted(allBytes):
        if 32<=ord(case)<127 and case!="'": cstr="'%c'" % case
        else: cstr=ord(case)
        if use_if: ret.append("if(NEXTBYTE==%s) {" % cstr)
        else: ret.append("case %s:" % cstr)
        inner = stringSwitch(dict([(k[1:],v) for k,v in byteSeq_to_action_dict.iteritems() if k and k[0]==case]),subFuncL,None,subFuncs)
        need_break = not (use_if or inner[-1].endswith("return;"))
        if nested_switch or not inner[0].startswith("switch"): ret += ["  "+x for x in inner]
        else:
          # Put the inner switch into a different function
          # which returns 1 if we should return.
          # (TODO: this won't catch cases where there's a SAVEPOS before the inner switch; will still nest in that case.  But it shouldn't lead to big nesting in practice.)
          myFunc=["static int NewFunc() {"]
          for x in inner:
            if x.endswith("return;"): x=x[:-len("return;")]+"return 1;"
            myFunc.append("  "+x)
          ret.append("  if("+subFuncCall("\n".join(myFunc)+"  return 0;\n}",subFuncs,subFuncL)+") return;")
          called_subswitch=True # as it'll include more NEXTBYTE calls which are invisible to the code below
        if need_break: ret.append("  break;")
      ret.append("}") # end of switch or if
    if not savePos==None:
        if len(' '.join(ret).split('NEXTBYTE'))==2 and not called_subswitch:
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
                ret.append("if ("+nearCall(conds,subFuncs,subFuncL)+") {")
                ret.append((action+" return;").strip())
                ret.append("}")
            else:
                if default_action: sys.stderr.write("WARNING! More than one default action in "+repr(byteSeq_to_action_dict[""])+" - earlier one discarded!\n(This might indicate invalid markup in the corpus)\n") # see TODO in yarowsky_indicators
                default_action = action
        if default_action or not byteSeq_to_action_dict[""]: ret.append((default_action+" return;").strip()) # (return only if there was a default action, OR if an empty "" was in the dict with NO conditional actions (e.g. from the common-case optimisation above).  Otherwise, if there were conditional actions but no default, we didn't "match" anything if none of the conditions were satisfied.)
    return ret # caller does '\n'.join

if obfuscate:
  import random ; pad=[]
  for i in xrange(32): pad.append(random.randint(128,255))
  unobfusc_func=r"""

void OutWriteDecode(const char *s) {
static const char pad[]={%s}; int i=0;
while(*s) {
int t=pad[i++]; if(i==sizeof(pad)) i=0;
if(*s==t) OutWriteByte(t); else OutWriteByte((*s)^t); s++;
}
}""" % repr(pad)[1:-1]
  def encodeOutstr(s):
    i = 0 ; r = []
    for c in s:
      t = pad[i] ; i = (i+1) % len(pad)
      if ord(c) == t: toApp = t
      else: toApp = ord(c)^t
      if toApp==ord("\\"): r.append(r'\\')
      elif toApp==ord('"'): r.append(r'\"')
      elif toApp&0x80 or toApp<32: r.append(r'\x%x" "' % toApp)
      else: r.append(chr(toApp))
    return ''.join(r)
else: unobfusc_func = ""

c_start = "/* -*- coding: "+outcode+r""" -*- */
#include <stdio.h>
#include <string.h>

/* To include this code in another program,
   define the ifndef'd macros below + define Omit_main */
enum { ybytes = %%YBYTES%% }; /* for Yarowsky matching, minimum readahead */
static int nearbytes = ybytes;
#define setnear(n) (nearbytes = (n))
#ifndef NEXTBYTE
/* Default definition of NEXTBYTE etc is to read input
   from stdin and write output to stdout.  */
enum { Half_Bufsize = %%LONGEST_RULE_LEN%% };
static unsigned char lookahead[Half_Bufsize*2];
static size_t readPtr=0,writePtr=0,bufStart=0,bufLen=0;
static int nextByte() {
  if (readPtr-bufStart +ybytes >= bufLen) {
    if (bufLen == Half_Bufsize * 2) {
      memmove(lookahead,lookahead+Half_Bufsize,Half_Bufsize);
      bufStart += Half_Bufsize; bufLen -= Half_Bufsize;
    }
    bufLen += fread(lookahead+bufLen,1,Half_Bufsize*2-bufLen,stdin);
    if (readPtr-bufStart == bufLen) return EOF;
  }
  return lookahead[(readPtr++)-bufStart];
}
static int near(char* string) {
  /* for Yarowsky-like matching */
  size_t offset = readPtr-bufStart, l=strlen(string),
         maxPos = bufLen;
  if (maxPos >= l) maxPos -= l; else return 0; // can't possibly start after maxPos-l
  if (offset+nearbytes>l) {
    if (maxPos > offset+nearbytes-l)
      maxPos = offset+nearbytes-l;
  } else maxPos = 0; // (don't let it go below 0, as size_t is usually unsigned)
  if (offset>nearbytes) offset-=nearbytes; else offset = 0;
  // can use strnstr(haystack,needle,n) if on a BSD system
  while (offset <= maxPos) {
    if(!strncmp((char*)lookahead+offset,string,l)) return 1;
    offset++;
  }
  return 0;
}
#define NEXTBYTE nextByte()
#define NEXT_COPY_BYTE lookahead[(writePtr++)-bufStart]
#define COPY_BYTE_SKIP writePtr++
#define POSTYPE size_t
#define THEPOS readPtr /* or get it via a function */
#define SAVEPOS POSTYPE oldPos=THEPOS
#define RESTOREPOS readPtr=oldPos /* or set via a func */
#define PREVBYTE readPtr--
#define FINISHED (feof(stdin) && readPtr-bufStart == bufLen)
#define OutWriteStr(s) fputs(s,stdout)
#define OutWriteByte(c) putchar(c)
#endif

#ifndef Default_Annotation_Mode
#define Default_Annotation_Mode ruby_markup
#endif

enum {
  annotations_only,
  ruby_markup,
  brace_notation} annotation_mode = Default_Annotation_Mode;

static int needSpace=0;
static void s() {
  if (needSpace) OutWriteByte(' ');
  else needSpace=1; /* for after the word we're about to write (if no intervening bytes cause needSpace=0) */
}""" + unobfusc_func + r"""

static void o(int numBytes,const char *annot) {
  s();
  switch (annotation_mode) {
  case annotations_only: OutWriteDecode(annot); break;
  case ruby_markup:
    OutWriteStr("<ruby><rb>");
    for(;numBytes;numBytes--)
      OutWriteByte(NEXT_COPY_BYTE);
    OutWriteStr("</rb><rt>"); OutWriteDecode(annot);
    OutWriteStr("</rt></ruby>"); break;
  case brace_notation:
    OutWriteByte('{');
    for(;numBytes;numBytes--)
      OutWriteByte(NEXT_COPY_BYTE);
    OutWriteByte('|'); OutWriteDecode(annot);
    OutWriteByte('}'); break;
  }
}
static void o2(int numBytes,const char *annot,const char *title) {
  if (annotation_mode == ruby_markup) {
    s();
    OutWriteStr("<ruby title=\""); OutWriteDecode(title);
    OutWriteStr("\"><rb>");
    for(;numBytes;numBytes--)
      OutWriteByte(NEXT_COPY_BYTE);
    OutWriteStr("</rb><rt>"); OutWriteDecode(annot);
    OutWriteStr("</rt></ruby>");
  } else o(numBytes,annot);
}
"""

if not obfuscate: c_start = c_start.replace("OutWriteDecode","OutWriteStr")

c_end = """
void matchAll() {
  while(!FINISHED) {
    POSTYPE oldPos=THEPOS;
    topLevelMatch();
    if (oldPos==THEPOS) { needSpace=0; OutWriteByte(NEXTBYTE); COPY_BYTE_SKIP; }
  }
}

#ifndef Omit_main
int main(int argc,char*argv[]) {
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

class BytecodeAssembler:
  # Bytecode for a virtual machine run by the Javascript version etc
  def __init__(self):
    self.l = []
    self.d2l = {}
    self.lastLabelNo = 0
    self.addingPosStack = []
  def addOpcode(self,opcode):
      self.addBytes({
        'jump': 50, # params: address
        'call': 51, # params: function address
        'return': 52, # (or 'end program' if top level)
        'switchbyte': 60, # switch(NEXTBYTE) (params: numBytes-1, bytes (sorted, TODO take advantage of this), addresses, default address)
        'copyBytes':71,'o':72,'o2':73, # (don't change these numbers, they're hard-coded below)
        'savepos':80, # local to the function
        'restorepos':81,
        'neartest':90, # params: true-label, false-label, byte nbytes, addresses of conds strings until true-label reached
        }[opcode])
  def addBytes(self,bStr):
      if type(bStr)==int: self.l.append(chr(bStr))
      elif type(bStr)==str: self.l.append(bStr)
      else: raise Exception("unspported bytes type")
  def startAddingFunction(self):
      self.addingPosStack.append((len(self.l),self.lastLabelNo))
      self.lastLabelNo = 0
  def finishFunctionAndAddCall(self):
      # make sure to add a return instruction before this!
      fPtr, self.lastLabelNo = self.addingPosStack[-1]
      del self.addingPosStack[-1]
      fBody = tuple(self.l[fPtr:]) ; self.l=self.l[:fPtr]
      if not fBody in self.d2l: # not a duplicate
          self.d2l[fBody] = (-len(self.d2l)-1,)
      self.addOpcode('call')
      self.l.append(self.d2l[fBody])
  def addByteswitch(self,byteArray,labelArray):
      assert len(byteArray) + 1 == len(labelArray)
      # labelArray has the default case added also (TODO: could re-organize code so the bytes immediately after the switch are either the default or one of the items, saving 1 address)
      if not len(byteArray): return # empty switch = no-op
      self.addOpcode('switchbyte')
      self.addBytes(len(byteArray)-1) # num of bytes in list - 1 (so all 256 values can be accounted for if needed)
      self.addBytes("".join(byteArray))
      for i in labelArray: self.addRef(i)
  def addActions(self,actionList):
    for a in actionList:
      assert 1 <= len(a) <= 3
      assert type(a[0])==int and 1 <= a[0] <= 255, "bytecode currently supports markup or copy between 1 and 255 bytes only (but 0 is reserved for expansion)"
      self.addBytes(70+len(a)) # 71=copyBytes 72=o() 73=o2
      self.addBytes(a[0])
      for i in a[1:]: self.addRefToString(i)
  def addActionDictSwitch(self,byteSeq_to_action_dict,isFunc=True,labelToJump=None):
    # a modified stringSwitch for the bytecode
    # Actions aren't strings: they list tuples of either
    # 1, 2 or 3 items for copyBytes, o(), o2()
    # labelToJump is a jump to insert afterwards if not isFunc and if we don't emit an unconditional 'return'.  Otherwise, will ALWAYS end up with a 'return' (even if not isFunc i.e. the main program)
    allBytes = set(b[0] for b in byteSeq_to_action_dict.iterkeys() if b)
    if isFunc:
        self.startAddingFunction()
        savePos = len(self.l)
        self.addOpcode('savepos')
    elif ("" in byteSeq_to_action_dict and len(byteSeq_to_action_dict) > 1) or not labelToJump: # ('not labelToJump' and 'not isFunc' == main program)
        savePos = len(self.l)
        self.addOpcode('savepos')
    else: savePos = None
    if "" in byteSeq_to_action_dict and len(byteSeq_to_action_dict) > 1 and len(byteSeq_to_action_dict[""])==1 and not byteSeq_to_action_dict[""][0][1] and all((len(a)==1 and a[0][0][:len(byteSeq_to_action_dict[""][0][0])]==byteSeq_to_action_dict[""][0][0] and not a[0][1]) for a in byteSeq_to_action_dict.itervalues()):
        self.addActions(byteSeq_to_action_dict[""][0][0])
        l = len(byteSeq_to_action_dict[""][0][0])
        byteSeq_to_action_dict = dict((x,[(y[l:],z)]) for x,[(y,z)] in byteSeq_to_action_dict.iteritems())
        del self.l[savePos] ; savePos = None
        del byteSeq_to_action_dict[""]
        self.addActionDictSwitch(byteSeq_to_action_dict) # as a subfunction (ends up adding the call to it)
        byteSeq_to_action_dict[""] = [("",[])] # for the end of this func
        self.addOpcode('return')
    elif allBytes:
      allBytes = list(allBytes)
      labels = [self.makeLabel() for b in allBytes+[0]]
      self.addByteswitch(allBytes,labels)
      for case in allBytes:
        self.addLabelHere(labels[0]) ; del labels[0]
        self.addActionDictSwitch(dict([(k[1:],v) for k,v in byteSeq_to_action_dict.iteritems() if k and k[0]==case]),False,labels[-1])
      self.addLabelHere(labels[0])
    if not savePos==None: self.addOpcode('restorepos')
    if isFunc:
        self.addOpcode('return')
        if self.l[-1]==self.l[-2]: del self.l[-1] # double return
        return self.finishFunctionAndAddCall()
    elif "" in byteSeq_to_action_dict:
        default_action = ""
        for action,conds in byteSeq_to_action_dict[""]:
            if conds:
                if type(conds)==tuple: conds,nbytes = conds
                else: nbytes = ybytes_max
                assert 1 <= nbytes <= 255, "bytecode supports only single-byte nbytes (but nbytes=0 is reserved for expansion)"
                trueLabel,falseLabel = self.makeLabel(),self.makeLabel()
                self.addOpcode('neartest')
                self.addRef(trueLabel)
                self.addRef(falseLabel)
                assert type(nbytes)==int
                self.addBytes(nbytes)
                for c in conds: self.addRefToString(c.encode(outcode))
                self.addLabelHere(trueLabel)
                self.addActions(action)
                self.addOpcode('return')
                self.addLabelHere(falseLabel)
            else: default_action = action
        if default_action or not byteSeq_to_action_dict[""]:
            self.addActions(default_action)
            self.addOpcode('return') ; return
    if labelToJump:
        self.addOpcode('jump')
        self.addRef(labelToJump)
    else: self.addOpcode('return')
  def makeLabel(self):
      self.lastLabelNo += 1
      return self.lastLabelNo
  def addLabelHere(self,labelNo):
      assert type(labelNo)==int
      assert labelNo, "label 0 not allowed"
      self.l.append(labelNo)
  def addRef(self,labelNo):
      assert type(labelNo)==int
      self.l.append(-labelNo)
  def addRefToString(self,string):
    # prepends with a length hint if possible (or if not,
    # prepends with 0 and null-terminates it)
    assert type(string)==str
    if 1 <= len(string) < 256:
        string = chr(len(string))+string
    else: string = chr(0)+string+chr(0)
    if not string in self.d2l:
      self.d2l[string] = (-len(self.d2l)-1,)
    self.l.append(self.d2l[string])
  def link(self): # returns resulting bytes
    # (add an 'end program' instruction before calling)
    def f(*args): raise Exception("Must call link() only once")
    self.link = f
    sys.stderr.write("Linking... ")
    for dat,ref in self.d2l.iteritems():
        assert type(ref)==tuple and type(ref[0])==int
        self.l.append((-ref[0],)) # the label
        if type(dat)==str:
            self.l.append(dat) ; continue
        # otherwise it's a function, and non-reserved labels are local, so we need to rename them
        l2l = {}
        for i in dat:
            if type(i)==int:
                if i>0: j=i
                else: j=-i
                if not j in l2l:
                    l2l[j] = self.makeLabel()
                if i>0: self.addLabelHere(l2l[j])
                else: self.addRef(l2l[j])
            else: self.l.append(i) # str or tuple just cp
    del self.d2l
    # elements of self.l are now:
    # - byte strings (just copied in)
    # - positive integers (labels)
    # - negative integers (references to labels)
    # - +ve or -ve integers in tuples (reserved labels)
    # 1st byte of o/p is num bytes needed per address
    class TooNarrow(Exception): pass
    for numBytes in xrange(1,256):
        sys.stderr.write("(%d-bit) " % (numBytes*8))
        try:
          lDic = {} ; r = [chr(numBytes)]
          for P in [1,2]:
            ll = 1
            for i in self.l:
                if type(i) in [int,tuple]:
                    if type(i)==int: i2,iKey = i,-i
                    else: i2,iKey = i[0],(-i[0],)
                    assert type(i2)==int
                    if i2 > 0: # label going in here
                        if i in lDic: assert lDic[i] == ll, "changing label %s from %d to %d, P=%d" % (repr(i),lDic[i],ll,P)
                        else: lDic[i] = ll
                        continue
                    elif iKey in lDic: # known label
                        i = lDic[iKey]
                        shift = 8*numBytes
                        if (i >> shift): raise TooNarrow()
                        j = []
                        for b in xrange(numBytes):
                            # MSB-LSB (easier to do in JS)
                            shift -= 8
                            j.append(chr((i>>shift)&0xFF))
                        i = "".join(j)
                        assert len(i)==numBytes
                    else: # as-yet unknown label
                        assert P==1, "undefined label %d" % -i
                        ll += numBytes ; continue
                if P==2: r.append(i)
                ll += len(i)
          sys.stderr.write("%d bytes\n" % ll)
          return "".join(r)
        except TooNarrow: pass
    assert 0, "can't even assemble it with 255-byte addressing !?!"

js_start = r"""/* Javascript generated by """+program_name[:program_name.index("(c)")].strip()+r"""

Usage:

 - You could just include this code and then call the
   annotate() function i.e. var result = annotate(input)

 - Or you could use (and perhaps extend) the Annotator
   object, and call its annotate() method.  If you have
   Backbone.JS, Annotator will instead be a generator
   (extending Backbone.Model) which you will have to
   instantiate yourself (possibly after extending it).
   The Annotator object/class is also what will be
   exported by this module if you're using Common.JS.

 - On Unix systems with Node.JS, you can run this file in
   "node" to annotate standard input as a simple test.

*/

var Annotator={
"""
js_end = r"""
annotate: function(input) {
/* TODO: if input is a whole html doc, insert css in head
   (e.g. from annoclip and/or adjuster), and hope there's
   no stuff that's not to be annotated (form fields...) */
input = unescape(encodeURIComponent(input)); // to UTF-8
var data = this.data;
var addrLen = data.charCodeAt(0);
var dPtr;
var inputLength = input.length;
var p = 0; // read-ahead pointer
var copyP = 0; // copy pointer
var output = new Array();
var needSpace = 0;

function readAddr() {
  var i,addr=0;
  for (i=addrLen; i; i--) addr=(addr << 8) | data.charCodeAt(dPtr++);
  return addr;
}

function readRefStr() {
  var a = readAddr(); var l=data.charCodeAt(a);
  if (l != 0) return data.slice(a+1,a+l+1);
  else return data.slice(a+1,data.indexOf('\x00',a+1));
}

function s() {
  if (needSpace) output.push(" ");
  else needSpace=1; // for after the word we're about to write (if no intervening bytes cause needSpace=0)
}

function readData() {
    var sPos = new Array();
    while(1) {
        switch(data.charCodeAt(dPtr++)) {
            case 50: dPtr = readAddr(); break;
            case 51: {
              var f = readAddr(); var dO=dPtr;
              dPtr = f; readData() ; dPtr = dO;
              break; }
            case 52: return;
            case 60: {
              var nBytes = data.charCodeAt(dPtr++)+1;
              var i = data.slice(dPtr,dPtr+nBytes).indexOf(input.charAt(p++));
              if (i==-1) i = nBytes;
              dPtr += (nBytes + i * addrLen);
              dPtr = readAddr(); break; }
            case 71: {
              var numBytes = data.charCodeAt(dPtr++);
  output.push(input.slice(copyP,copyP+numBytes));
  copyP += numBytes; break; }
            case 72: {
              var numBytes = data.charCodeAt(dPtr++);
              var annot = readRefStr();
  s();
  output.push("<ruby><rb>");
  output.push(input.slice(copyP,copyP+numBytes));
  copyP += numBytes;
  output.push("</rb><rt>"); output.push(annot);
  output.push("</rt></ruby>"); break; }
            case 73: {
              var numBytes = data.charCodeAt(dPtr++);
              var annot = readRefStr();
              var title = readRefStr();
  s();
  output.push("<ruby title=\""); output.push(title);
  output.push("\"><rb>");
  output.push(input.slice(copyP,copyP+numBytes));
  copyP += numBytes;
  output.push("</rb><rt>"); output.push(annot);
  output.push("</rt></ruby>"); break; }
            case 80: sPos.push(p); break;
            case 81: p=sPos.pop(); break;
            case 90: {
                var tPtr = readAddr();
                var fPtr = readAddr();
                var nearbytes = data.charCodeAt(dPtr++);
  var o=p;
  if (o > nearbytes) o -= nearbytes; else o = 0;
  var max = p + nearbytes;
  if (max > inputLength) max = inputLength;
  var tStr = input.slice(o,max);
                var found = 0;
                while (dPtr < tPtr) if (tStr.indexOf(readRefStr()) != -1) { found = 1; break; }
                dPtr = found ? tPtr : fPtr; break;
                }
        default: throw("corrupt data table at "+(dPtr-1)+" ("+data.charCodeAt(dPtr-1)+")");
            }
        }
    }

while(p < inputLength) {
var oldPos=p;
dPtr=1;readData();
if (oldPos==p) { needSpace=0; output.push(input.charAt(p++)); copyP++; }
}
return decodeURIComponent(escape(output.join(""))); // from UTF-8 back to Unicode
} // end of annotate function
};
function annotate(input) { return Annotator.annotate(input); }

if (typeof Backbone != "undefined" && Backbone.Model) { Annotator = Backbone.Model.extend(Annotator); annotate=function(input) { return new Annotator().annotate(input) } }
if (typeof require != "undefined" && typeof module != "undefined" && require.main === module) {
  // Node.js command-line test
  fs=require('fs');
  process.stdout.write(annotate(fs.readFileSync('/dev/stdin').toString()));
} else if (typeof module != "undefined" && module.exports) { // Common.js
  module.exports = Annotator;
}
"""

py_start = r"""# Python generated by """+program_name[:program_name.index("(c)")].strip()+r"""

# You can import this module and call annotate(utf8 bytes)
# (from multiple threads if desired),
# or you can run from the command line on standard input.

# annotate has an optional second argument, which can be
# 'ruby' (default), 'raw' (annotation only) or 'braces'.

"""
py_end = r"""
class Annotator:
 def __call__(self,inStr,aType):
  if aType=="ruby": self.startA,self.midA,self.endA = "<ruby><rb>","</rb><rt>","</rt></ruby>"
  elif aType=="raw": self.startA=self.midA=self.endA = ""
  elif aType=="braces": self.startA,self.midA,self.endA = "{","|","}"
  else: raise Exception("Unrecognised annotation type "+repr(aType))
  assert type(inStr)==str
  self.inStr = inStr
  self.addrLen = ord(data[0])
  self.inputLength = len(inStr)
  self.p = 0 # read-ahead pointer
  self.copyP = 0 # copy pointer
  self.output = []
  self.needSpace = 0 ; out = self.output
  while self.p < self.inputLength:
    oldPos = self.p
    self.dPtr = 1 ; self.readData()
    if oldPos == self.p:
      self.needSpace=0
      out.append(inStr[self.p])
      self.p += 1 ; self.copyP += 1
  return "".join(self.output)
 def readAddr(self):
  addr = 0
  for i in range(self.addrLen):
    addr=(addr << 8) | ord(data[self.dPtr])
    self.dPtr += 1
  return addr
 def readRefStr(self):
  a = self.readAddr(); l=ord(data[a])
  if l: return data[a+1:a+l+1]
  else: return data[a+1:data.index('\x00',a+1)]
 def s(self):
  if self.needSpace: self.output.append(" ")
  else: self.needSpace=1
 def readData(self):
  sPos = [] ; out = self.output
  while True:
    d = ord(data[self.dPtr]) ; self.dPtr += 1
    if d==50: self.dPtr = self.readAddr()
    elif d==51:
      func = self.readAddr() ; dO = self.dPtr
      self.dPtr = func ; self.readData() ; self.dPtr = dO
    elif d==52: return
    elif d==60:
      nBytes = ord(data[self.dPtr])+1 ; self.dPtr += 1
      i = data[self.dPtr:self.dPtr+nBytes].find(self.inStr[self.p]) ; self.p += 1
      if i==-1: i = nBytes
      self.dPtr += (nBytes + i * self.addrLen)
      self.dPtr = self.readAddr()
    elif d==71:
      numBytes = ord(data[self.dPtr]) ; self.dPtr += 1
      out.append(self.inStr[self.copyP:self.copyP+numBytes])
      self.copyP += numBytes
    elif d==72:
      numBytes = ord(data[self.dPtr]) ; self.dPtr += 1
      annot = self.readRefStr()
      self.s()
      if self.startA:
        out.append(self.startA)
        out.append(self.inStr[self.copyP:self.copyP+numBytes])
      self.copyP += numBytes
      out.append(self.midA) ; out.append(annot)
      out.append(self.endA)
    elif d==73:
      numBytes = ord(data[self.dPtr]) ; self.dPtr += 1
      annot = self.readRefStr()
      title = self.readRefStr()
      self.s()
      if self.startA=="{": # omit title in braces mode
        out.append(self.startA)
        out.append(self.inStr[self.copyP:self.copyP+numBytes])
      elif self.startA:
        out.append("<ruby title=\"");out.append(title)
        out.append("\"><rb>");
        out.append(self.inStr[self.copyP:self.copyP+numBytes])
      self.copyP += numBytes
      out.append(self.midA) ; out.append(annot)
      out.append(self.endA)
    elif d==80: sPos.append(self.p)
    elif d==81: self.p = sPos.pop()
    elif d==90:
      tPtr = self.readAddr()
      fPtr = self.readAddr()
      nearbytes = ord(data[self.dPtr]) ; self.dPtr += 1
      o = max(self.p-nearbytes,0)
      maxx = min(self.p+nearbytes,self.inputLength)
      tStr = self.inStr[o:maxx]
      found = 0
      while self.dPtr < tPtr:
        if self.readRefStr() in tStr:
          found = 1 ; break
      if found: self.dPtr = tPtr
      else: self.dPtr = fPtr
    else: raise Exception("corrupt data table at "+str(self.dPtr-1)+" ("+str(ord(data[self.dPtr-1]))+")")

def annotate(inStr,p="ruby"): return Annotator()(inStr,p)
def main():
  import sys
  if sys.argv[-1].startswith("--"): param=sys.argv[-1][2:]
  else: param = "ruby"
  sys.stdout.write(annotate(sys.stdin.read(),param))
if __name__=="__main__": main()
"""

def splitWords(text,phrases=False):
    # split text into words, ignoring anything between markupStart and markupEnd
    # if phrases = True, instead of words, split on any non-whitespace char outside markupStart..markupEnd
    i=start=0
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
            if i>start: yield text[start:i]
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
    if i>start: yield text[start:i]

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

def markUp(text,annotation):
  if mreverse: text,annotation = annotation,text
  return markupStart + text + markupMid + annotation + markupEnd
    
def checkpoint_exit(doIt=1):
  if not checkpoint: return
  try: open(checkpoint+os.sep+"ExitASAP")
  except: return
  if doIt:
    os.remove(checkpoint+os.sep+"ExitASAP")
    sys.stderr.write("\nExitASAP found: exit\n")
    raise SystemExit
  else: return True

def normalise():
    if capitalisation and annot_whitespace: return
    global corpus_unistr
    if checkpoint:
      try:
        f=open(checkpoint+os.sep+'normalised','rb')
        corpus_unistr = f.read().decode('utf-8')
        return
      except: pass
    sys.stderr.write("Normalising...")
    def getAllWords():
     allWords = set()
     for phrase in splitWords(corpus_unistr,phrases=True):
        allWords.update(splitWords(phrase))
     return allWords
    allWords = getAllWords()
    if removeSpace and not annot_whitespace:
      # normalise trailing hyphens e.g. from OCR'd scans:
      cu0 = corpus_unistr ; ff = 0
      for hTry in [1,2]:
        for w in allWords:
          if '-'+aoEnd in w:
            idx = w.index('-'+aoEnd)
            if w[:idx].endswith(aoStart) or w[:idx].endswith("-"): continue # ignore this one (a mess of some kind)
            if hTry==2: # ouch, this doesn't look good
              sys.stderr.write(" (can't normalise hyphens) ")
              corpus_unistr = cu0 ; break
            if mreverse: grp,mdG=r"-\1",r"\2"
            else: grp,mdG=r"-\2",r"\1"
            # TODO: batch up the following replacements by using something similar to Replacer but with a common destination regexp that takes groups from the 'w' entries as well.  (Low priority because don't typically get TOO many of these dangling hyphens in most corpuses.)
            corpus_unistr = re.sub(re.escape(w)+r"\s*"+re.escape(markupStart)+"(.*?)"+re.escape(markupMid)+"(.*?)"+re.escape(markupEnd),re.escape(w).replace(re.escape('-'+aoEnd),grp+re.escape(aoEnd)).replace(re.escape(mdEnd),mdG+re.escape(mdEnd)),corpus_unistr)
            ff = 1
        if ff: allWords = getAllWords() # re-generate
      del cu0
    class Replacer:
      def __init__(self): self.dic = {}
      def add(self,x,y):
        self.dic[x] = y
        if len(self.dic)==2000: # limit the size of each batch - needed on some Pythons (e.g. Mac)
          self.flush()
      def flush(self):
        if not self.dic: return
        global corpus_unistr
        corpus_unistr = re.sub('|'.join(re.escape(k) for k in self.dic.iterkeys()),lambda k:self.dic[k.group(0)],corpus_unistr) # (stackoverflow suggestion)
        sys.stderr.write(".")
        self.dic = {}
    rpl = Replacer() ; rpl.cu_nosp = None
    def normWord(w):
      if '-' in w: hTry=set([w.replace('-','')]) # if not annot_whitespace, we'll replace any non-hyphenated 'run together' version by the version with the hyphen; that's often the sensible thing to do with pinyin etc (TODO more customisation??)
      else: hTry=None
      if not capitalisation:
        wl = w.lower() # (as long as it's all Unicode strings, .lower() and .upper() work with accents etc)
        if not w==wl and wl in allWords:
            # This word is NOT always capitalised, just
            # sometimes at the start of a sentence.
            # To simplify rules, make it always lower.
            w = wl
            if hTry: hTry.add(w.replace('-',''))
      if annot_whitespace: return w,None
      nowsp = "".join(w.split())
      if w == nowsp: return w,hTry # no whitespace in w
      if nowsp in allWords: return nowsp,hTry # varying whitespace in the annotation of a SINGLE word: probably simplest if we say the version without whitespace, if it exists, is 'canonical' (there might be more than one with-whitespace variant), at least until we can set the relative authority of the reference (TODO)
      ao,md = annotationOnly(w),markDown(w)
      aoS = ao.split()
      if len(md.split())==1 and len(md) <= 5 and len(aoS) <= len(md): # TODO: 5 configurable?  don't want different_ways_of_splitting to take too long
        # if not too many chars, try different ways of
        # assigning each word to chars, and see if any
        # of these exist in the corpus; if any does,
        # assume we have "ABC|a bc" <= "A|a BC|bc" type
        # situations - the latter shouldn't necessarily be
        # converted into the former, but the former might
        # be convertible into the latter to simplify rules
        if rpl.cu_nosp == None: rpl.cu_nosp = re.sub(whitespacePattern,"",corpus_unistr)
        for charBunches in different_ways_of_splitting(md,len(aoS)):
          aoS_try = [aoS]
          if not capitalisation: # we have to account for the case where the above 'wl in allWords' did not happen but WOULD have happened if this substitution had been made
            aoS_try.append([w.lower() for w in aoS])
            if aoS_try[0]==aoS_try[1]: del aoS_try[1]
          for aoS2 in aoS_try:
            mw = [markUp(c,w) for c,w in zip(charBunches,aoS2)]
            multiword = "".join(mw)
            if multiword in rpl.cu_nosp:
              # we're about to return a split version of the words, but we now have to pretend it went through the initial capitalisation logic that way (otherwise could get unnecessarily large collocation checks)
              if not capitalisation:
                for i in range(len(mw)):
                  w = mw[i]
                  wl = w.lower()
                  if not w==wl and wl in allWords:
                    mw[i] = wl
              return "".join(mw),hTry
          # TODO: is there ANY time where we want multiword to take priority over the nowsp (no-whitespace) version above?  or even REPLACE multiword occurrences in the corpus with the 1-word nowsp version?? (must be VERY CAREFUL doing that)
      # TODO: anything else?
      return w,hTry
    for w in allWords:
      w2,hTry = normWord(w)
      if hTry:
        hTry.add(w2.replace('-','')) # in case not already there
        for h in hTry:
          if h in allWords: rpl.add(h,w2)
      if not w==w2: rpl.add(w,w2)
    rpl.flush()
    sys.stderr.write(" done\n")
    if checkpoint: open(checkpoint+os.sep+'normalised','wb').write(corpus_unistr.encode('utf-8'))
    checkpoint_exit()

if mreverse: mdStart,mdEnd,aoStart,aoEnd = markupMid,markupEnd,markupStart,markupMid
else: mdStart,mdEnd,aoStart,aoEnd = markupStart,markupMid,markupMid,markupEnd

def different_ways_of_splitting(chars,splitPoints):
  if splitPoints > len(chars): return
  elif splitPoints == len(chars):
    yield list(chars) ; return
  elif splitPoints == 0:
    yield [chars] ; return
  spAt_try1 = len(chars) / splitPoints + 1
  for spAt in range(spAt_try1,0,-1) + range(spAt_try1+1, len(chars)-splitPoints):
    for r in different_ways_of_splitting(chars[spAt:],splitPoints-1): yield [chars[:spAt]]+r

def yarowsky_indicators(withAnnot_unistr,markedDown):
    # returns True if rule always works (or in majority of cases with ymajority), or lists enough indicators to cover example instances and returns (list, nbytes), or just list if empty.
    # (If too few indicators can be found, will list the ones it can, or empty if no clearly-distinguishable indicators can be found within ybytes of end of match.)
    nonAnnot=markDown(withAnnot_unistr)
    if nonAnnot in yPriorityDic: # TODO: enforce len==1 ?
        if yPriorityDic[nonAnnot] == withAnnot_unistr:
            # we want this case to be the default
            if nonAnnot==diagnose: sys.stderr.write(("Diagnose: yPriorityDic forces %s\n" % (withAnnot_unistr,)).encode(terminal_charset,'replace'))
            return True
        else:
          if nonAnnot==diagnose: sys.stderr.write(("Diagnose: yPriorityDic forbids default %s\n" % (withAnnot_unistr,)).encode(terminal_charset,'replace'))
          can_be_default = False # another is default, don't make this one default even if it occurs more
    else: can_be_default = True
    # First, find positions in markedDown which match withAnnot_unistr in corpus_unistr (not markedUp as that's harder to sync with markedDown, since markedUp contains /-separated annotated phrases whereas markedDown also contains the in-between bytes)
    okStarts = getOkStarts(withAnnot_unistr)
    # now check for markedDown matches that *don't* have withAnnot_unistr
    badStarts = getBadStarts(nonAnnot,markedDown,okStarts)
    if not badStarts:
      if nonAnnot==diagnose: sys.stderr.write(("Diagnose: %s always works\n" % (withAnnot_unistr,)).encode(terminal_charset,'replace'))
      return True # rule always works, no Yarowsky indicators needed
    if can_be_default and len(okStarts) > len(badStarts) and len(nonAnnot)==1:
      if nonAnnot==diagnose: sys.stderr.write(("Diagnose: %s is default by majority-case len-1 rule\n" % (withAnnot_unistr,)).encode(terminal_charset,'replace'))
      return True # duplicate of code below (can test for this case early before reducing-down badStarts)
    badStarts = getReallyBadStarts(badStarts,nonAnnot) # see its comments (ignore some badStarts)
    if not badStarts:
      if nonAnnot==diagnose: sys.stderr.write(("Diagnose: %s always works if we ignore probably-irrelevant badStarts\n" % (withAnnot_unistr,)).encode(terminal_charset,'replace'))
      return True
    # Now, if it's right more often than not:
    if can_be_default and len(okStarts) > len(badStarts):
        # could we have this as a "default" rule, with the other cases as exceptions that will be found first?
        if len(nonAnnot)==1:
          if nonAnnot==diagnose: sys.stderr.write(("Diagnose: %s is default by majority-case len-1 rule after removing irrelevant badStarts\n" % (withAnnot_unistr,)).encode(terminal_charset,'replace'))
          return True # should be safe, and should cover most "common short Chinese word with thousands of contexts" cases
        # If len 2 or more, it's risky because the correct solution could be to process just a fraction of the word now and the rest will become the start of a longer word, so we probably don't want it matching the whole lot by default unless can be sure about it
        # e.g. looking at rule AB, text ABC and correct segmentation is A BC, don't want it to 'greedily' match AB by default without positive indicators it should do so
        # Might get an exception if there is no possibility of a rule A in the examples, i.e. no markup of a word of length < nonAnnot whose marked-down version matches the start of nonAnnot in corpus_unistr:
        # if not re.search(re.escape(mdStart)+reduce(lambda x,y:re.escape(y)+"("+x+")?",reversed(list(nonAnnot[:-1])))+re.escape(mdEnd),corpus_unistr): return True
        # Might also have an exception if there is no possibility of a rule BC, i.e. no word in corpus_unistr whose marked-down version starts with any of the strings nonAnnot[1:] [2:] ... [-1:]
        # if not re.search(re.escape(mdStart)+reduce(lambda x,y:"("+x+")?"+re.escape(y),list(nonAnnot[1:])),corpus_unistr): return True
        # + might have an exception if can confirm from all badStarts that the marked-down version of the rule applied (if one starts at that badStart) is at least as long as nonAnnot
        # Or just directly check for "A BC" situations, i.e. can't find any possible SEQUENCE of rules that STARTS with ALL the characters in nonAnnot and that involves having them SPLIT across multiple words:
        llen = len(mdStart)+len(nonAnnot)
        if all(x.end()-x.start()==llen for x in re.finditer(re.escape(mdStart)+(re.escape(mdEnd)+".*?"+re.escape(mdStart)).join(re.escape(c) for c in list(nonAnnot)),corpus_unistr)):
          if nonAnnot==diagnose: sys.stderr.write(("Diagnose: %s is default by majority-case rule after checking for dangerous overlaps etc\n" % (withAnnot_unistr,)).encode(terminal_charset,'replace'))
          return True
        # (This exception might under-match if there's the appearance of a split rule but it actually has extra non-marked-up text in between.  But it shouldn't over-match.)
    if len(okStarts) > 1000: sys.stderr.write("\nLarge collocation check (%s has %d matches + %s), could take some time....  \n" % (withAnnot_unistr.encode(terminal_charset,'replace'),len(okStarts),badInfo(badStarts,nonAnnot,markedDown)))
    if ybytes_max > ybytes and (not ymax_threshold or len(nonAnnot) <= ymax_threshold):
      retList = [] ; append=retList.append
      for nbytes in range(ybytes,ybytes_max+1,ybytes_step):
        ret,covered,toCover = tryNBytes(nbytes,markedDown,nonAnnot,badStarts,okStarts)
        if covered==toCover and len(ret)==1: return (ret,nbytes) # a single indicator that covers everything will be better than anything else we'll find
        append((-covered,len(ret),nbytes,toCover,ret)) # (1st 3 of these are the sort keys: maximum coverage, THEN minimum num indicators for the same coverage, THEN minimum nbytes (TODO: problems of very large nbytes might outweigh having more indicators; break if found 100% coverage by N?)  toCover should always ==len(okStarts).)
        # TODO: try finding an OR-combination of indicators at *different* proximity lengths ?
      retList.sort() ; ret = retList[0][-1]
      distance = retList[0][2]
    else:
      ret = tryNBytes(ybytes_max,markedDown,nonAnnot,badStarts,okStarts)[0]
      if ybytes < ybytes_max: distance = ybytes_max
      else: distance = None # all the same anyway
    if not ret and warn_yarowsky: sys.stderr.write("Couldn't find ANY Yarowsky-like indicators for %s   \n" % (withAnnot_unistr.encode(terminal_charset,'replace')))
    # elif ybytes_max > ybytes: sys.stderr.write("Debugger: %s best coverage=%d/%d by %d indicators at nbytes=%d   \n" % (withAnnot_unistr.encode(terminal_charset,'replace'),-retList[0][0],retList[0][3],retList[0][1],retList[0][2]))
    # TODO: if partially but not completely covered, shouldn't entirely count the word as 'covered' in analyse()
    if not ret or not distance: return ret
    else: return ret,distance
# keep these functions separate for cProfile clarity:
def getOkStarts(withAnnot_unistr):
    if withAnnot_unistr in precalc_sets: return precalc_sets[withAnnot_unistr]
    # else: return set(corpus_to_markedDown_map[s.start()] for s in re.finditer(re.escape(withAnnot_unistr), corpus_unistr))
    # if large corpus, the following might be faster
    # (precalc_sets has all 1-word cases; can use that)
    walen = len(withAnnot_unistr)
    return set(x for x in precalc_sets[splitWords(withAnnot_unistr).next()] if corpus_unistr[c2m_inverse[x]:c2m_inverse[x]+walen]==withAnnot_unistr)
def getBadStarts(nonAnnot,markedDown,okStarts): return set(x.start() for x in re.finditer(re.escape(nonAnnot),markedDown) if not x.start() in okStarts)
def getReallyBadStarts(badStarts,nonAnnot):
    # Some of the badStarts can be ignored on the grounds that they should be picked up by other rules first: any where the nonAnnot match does not start at the start of a word (the rule matching the word starting earlier should get there first), and any where it starts at the start of a word that is longer than itself (the longest-first ordering should take care of this).  So keep only the ones where it starts at the start of a word and that word is no longer than len(nonAnnot).
    reallyBadStarts = [] ; append=reallyBadStarts.append
    nonAnnotLen = len(mdStart+nonAnnot+mdEnd)
    theRe = re.compile(re.escape(mdStart+nonAnnot[0])+".*?"+re.escape(mdEnd))
    for b in badStarts:
      try: s = c2m_inverse[b]
      except KeyError: continue # it wasn't the start of a word (only start positions are in that map)
      m=theRe.search(corpus_unistr, s) # will either start at s, or after it if mreverse
      s,e = m.start(),m.end()
      if e-s > nonAnnotLen: continue # this word is too long, should be matched by a longer rule 1st
      append(b) # to reallyBadStarts
    return reallyBadStarts
def tryNBytes(nbytes,markedDown,nonAnnot,badStarts,okStarts):
    def bytesAround(start): return within_Nbytes(markedDown,start+len(nonAnnot),nbytes)
    omitStr = unichr(1).join(bytesAround(s) for s in badStarts)
    okStrs=[bytesAround(s) for s in okStarts]
    covered=[False]*len(okStrs)
    ret = [] ; append=ret.append
    for indicatorStr in unique_substrings(okStrs,markedUp_unichars,lambda txt:txt in omitStr,lambda txt:sum(1 for s in okStrs if txt in s)):
      cChanged = False
      for i in xrange(len(okStrs)):
        if not covered[i] and indicatorStr in okStrs[i]: covered[i]=cChanged=True
      if cChanged: append(indicatorStr)
      if all(covered): break
    if nonAnnot==diagnose:
      if ret: indicators = "indicators "+'/'.join(ret)
      else: indicators = "no indicators"
      sys.stderr.write(("Diagnose: tryNBytes(%d) on %s found %s (avoiding '%s'), covers %d/%d contexts\n" % (nbytes,withAnnot_unistr,indicators,omitStr.replace(unichr(1),'/'),sum(1 for x in covered if x),len(covered))).encode(terminal_charset,'replace'))
    return ret,sum(1 for x in covered if x),len(covered)

def badInfo(badStarts,nonAnnot,markedDown):
  if not len(badStarts)==1: return "%d false positives" % len(badStarts)
  # 1 badStart: might want to look at this
  i = list(badStarts)[0] ; i1 = i + len(nonAnnot)
  i0 = max(0,i-5) ; i2 = i1 + 5
  toRead = markedDown
  if i in c2m_inverse and i1 in c2m_inverse:
    i00,i22 = i0,i2
    while i00 not in c2m_inverse and 0<i00<i0-5: i00-=1
    while i22 not in c2m_inverse and i22<i2+5: i22+=1
    if i00 in c2m_inverse and i22 in c2m_inverse:
      toRead = corpus_unistr
      i0,i,i1,i2 = i00,c2m_inverse[i],c2m_inverse[i1],i22
  return (u"1 false positive (%s **%s** %s)" % (toRead[i0:i],toRead[i:i1],toRead[i1:i2])).encode(terminal_charset,'replace')

def unique_substrings(texts,allowedChars,omitFunc,valueFunc):
    # yield unique substrings of texts, in increasing length, with equal lengths sorted by highest score returned by valueFunc, and omitting any where omitFunc is true, or that uses any character not in allowedChars (allowedChars==None means all allowed)
    if allowedChars:
        # remove non-allowedChars from texts, splitting into smaller strings as necessary
        texts2 = [] ; append=texts2.append
        for text in texts:
            start = 0
            for i in xrange(len(text)):
                if not text[i] in allowedChars:
                    if i>start: append(text[start:i])
                    start=i+1
            if start<len(text): append(text[start:])
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
    phrase = markDown(withAnnot_unistr)
    ret = occurrences(markedDown,phrase) == occurrences(markedUp,withAnnot_unistr)
    if diagnose and diagnose==phrase:
      sys.stderr.write(("Diagnose: occurrences(%s)==occurrences(%s) = %s\n" % (phrase,withAnnot_unistr,ret)).encode(terminal_charset,'replace'))
    return ret

def all_possible_rules(words):
    # Iterate over ALL possible rules derived from the
    # word sequence (don't just "find the shortest context
    # that predicts each word" because that can have
    # trouble with overlaps; need to check them all and
    # stop when we've got enough to reproduce the example)
    if max_words: maxRuleLen = min(len(words),max_words)
    else: maxRuleLen = len(words)
    for ruleLen in range(1,maxRuleLen+1): # (sort by len)
        for wStart in range(maxRuleLen-ruleLen+1):
            yield words[wStart:wStart+ruleLen]
            # caller should do " ".join() before putting
            # it into rules dict

def checkCoverage(ruleAsWordlist,words,coveredFlags):
    # Updates coveredFlags and returns True if any changes
    # (if False, the new rule is redundant).
    # Don't worry about ybytes - assume the Yarowsky-like
    # indicators have been calculated correctly across the
    # whole text so we don't need to re-check them now.
    try: start = words.index(ruleAsWordlist[0])
    except ValueError: return False
    ln = len(ruleAsWordlist)
    changedFlags = False
    while start <= len(words)-ln:
        if words[start:start+ln] == ruleAsWordlist:
            if not all(coveredFlags[start:start+ln]):
                for i in range(start,start+ln):
                    coveredFlags[i] = True
                changedFlags = True
            start += ln
        else:
            try:
                start = words.index(ruleAsWordlist[0],start+1)
            except ValueError: break
    return changedFlags

def checkCoverage_checkOnly(ruleAsWordlist,words,coveredFlags):
    # version that just returns without changing coveredFlags (used to early-avoid calling test_rule); assume ruleAsWordlist IS a possible rule from words
    start = words.index(ruleAsWordlist[0])
    ln = len(ruleAsWordlist)
    while start <= len(words)-ln:
        if words[start:start+ln] == ruleAsWordlist:
            if not all(coveredFlags[start:start+ln]):
                return True
            start += ln
        else:
            try:
                start = words.index(ruleAsWordlist[0],start+1)
            except ValueError: break
    return False

def potentially_bad_overlap(rulesAsWordlists,newRuleAsWords,markedDown):
    # Allow overlaps only if rule(s) being overlapped are
    # entirely included within newRule.  Otherwise could
    # get problems generating closures of overlaps.
    # (If newRule not allowed, caller to try a longer one)
    # Additionally, if allow_overlaps, allow ANY overlap as
    # long as it's not found in the marked-down text.
    if len(newRuleAsWords)==1 or primitive or ybytes: return False
    for ruleAsWordlist in rulesAsWordlists:
        if len(ruleAsWordlist)==1: continue
        if not len(ruleAsWordlist)==len(newRuleAsWords) and longerStartsOrEndsWithTheShorter(ruleAsWordlist,newRuleAsWords): continue
        for overlapSize in range(1,min(len(x) for x in [newRuleAsWords,ruleAsWordlist])):
            if not (ruleAsWordlist[-overlapSize:] == newRuleAsWords[:overlapSize] or newRuleAsWords[-overlapSize:] == ruleAsWordlist[:overlapSize]): continue
            if not allow_overlaps: return True
            # Test to see if the examples "allow" this potentially-bad overlap
            def overlapOK(rAW): return not markDown(" ".join(rAW)) in markedDown
            if (ruleAsWordlist[-overlapSize:] == newRuleAsWords[:overlapSize] and not overlapOK(ruleAsWordlist[:-overlapSize]+newRuleAsWords)) or (newRuleAsWords[-overlapSize:] == ruleAsWordlist[:overlapSize] and not overlapOK(newRuleAsWords[:-overlapSize]+ruleAsWordlist)): return True

def longerStartsOrEndsWithTheShorter(l1,l2):
    if len(l1) > len(l2): l1,l2 = l2,l1
    return l2[:len(l1)]==l1 or l2[-len(l1):]==l1

class RulesAccumulator:
  def __init__(self):
    self.rules = {}
    self.rulesAsWordlists_By1stWord = {} # starting word -> list of possible rules (as wordlists) that might apply
    self.rulesAsWordlists = list() # all rules as words (list of lists) (used if not ybytes, TODO: integrate with rulesAsWordlists_By1stWord?)
    self.rejectedRules = set()
    self.seenPhrases = set() # de-duplicate, might speed up
    self.amend_rules = False
    if rulesFile: self.load()
  def save(self):
    sys.stderr.write("Pickling rules to %s... " % rulesFile)
    f = openfile(rulesFile,'wb')
    pickle.Pickler(f,-1).dump((self.rules,self.rulesAsWordlists_By1stWord,self.rulesAsWordlists,self.seenPhrases))
    # (don't save self.rejectedRules, there might be better clues next time)
    f.close() ; sys.stderr.write("done\n")
  def load(self):
    if not os.path.isfile(rulesFile):
      sys.stderr.write("%s does not exist, starting with blank rules\n" % rulesFile)
      return
    sys.stderr.write("Unpickling rules from %s... " % rulesFile)
    f = openfile(rulesFile,'rb')
    self.rules,self.rulesAsWordlists_By1stWord,self.rulesAsWordlists,self.seenPhrases = pickle.Unpickler(f).load()
    sys.stderr.write("done\n")
    self.amend_rules = True
    self.newRules = set()
  def remove_old_rules(self,words): # for incremental runs
    for w in set(words):
      rulesAsWordlists = self.rulesAsWordlists_By1stWord.get(w,[])
      i=0
      while i<len(rulesAsWordlists):
        if max_words and len(rulesAsWordlists[i])>max_words:
          i += 1 ; continue # better leave that one alone if we're not reconsidering rules that long (e.g. running again with single_words when previous run wasn't)
        rule = " ".join(rulesAsWordlists[i])
        if rule in self.newRules:
          i += 1 ; continue # we've discovered this one on THIS run, don't re-remove it
        if checkCoverage(rulesAsWordlists[i],words,[False]*len(words)):
          if not ybytes:
            try: self.rulesAsWordlists.remove(rulesAsWordlists[i])
            except: pass
          del rulesAsWordlists[i] ; del self.rules[rule]
        else: i += 1
  def addRulesForPhrase(self,phrase,markedUp,markedDown):
    global diagnose, diagnose_limit
    if phrase in self.seenPhrases:
      if diagnose and self.amend_rules and mdStart+diagnose+mdEnd in phrase: pass # look at it again for diagnostics (TODO: accept a diagnose that spans multiple words?)
      else: return 0,0
    self.seenPhrases.add(phrase)
    words = filter(lambda x:markDown(x).strip(),splitWords(phrase)) # filter out any that don't have base text (these will be input glitches, TODO: verify the annotation text is also just whitespace, warn if not)
    if not words: return 0,0
    covered = [False]*len(words)
    # first see how much is covered by existing rules
    # (don't have to worry about the order, as we've been
    # careful about overlaps)
    if self.amend_rules: self.remove_old_rules(words)
    for w in set(words):
     for rulesAsWordlists in self.rulesAsWordlists_By1stWord.get(w,[]):
      for ruleAsWordlist in rulesAsWordlists:
        checkCoverage(ruleAsWordlist,words,covered)
        if all(covered): return len(covered),len(covered) # no new rules needed
    for ruleAsWordlist in all_possible_rules(words):
        rule = " ".join(ruleAsWordlist) ; yBytesRet = []
        if rule in self.rules or rule in self.rejectedRules: continue
        if len(ruleAsWordlist)>1 and not checkCoverage_checkOnly(ruleAsWordlist,words,covered): continue # optimisation to avoid too many test_rule calls (TODO: is >1 the best threshold?)
        if not test_rule(rule,markedUp,markedDown,yBytesRet) or potentially_bad_overlap(self.rulesAsWordlists,ruleAsWordlist,markedDown):
            self.rejectedRules.add(rule) # so we don't waste time evaluating it again (TODO: make sure rejectedRules doesn't get too big?)
            continue
        if not checkCoverage(ruleAsWordlist,words,covered): continue # (checkCoverage must be last as it changes the coverage state)
        if len(yBytesRet): self.rules[rule] = yBytesRet[0]
        else: self.rules[rule] = [] # unconditional
        if not ybytes: self.rulesAsWordlists.append(ruleAsWordlist)
        if not ruleAsWordlist[0] in self.rulesAsWordlists_By1stWord: self.rulesAsWordlists_By1stWord[ruleAsWordlist[0]] = []
        self.rulesAsWordlists_By1stWord[ruleAsWordlist[0]].append(ruleAsWordlist)
        if self.amend_rules: self.newRules.add(rule)
        if diagnose and diagnose_limit and diagnose==markDown(rule):
          diagnose_limit -= 1
          if not diagnose_limit:
            diagnose = False
            sys.stderr.write("diagnose-limit reached, suppressing further diagnostics\n")
        if all(covered): return len(covered),len(covered)
    # If get here, failed to completely cover the phrase.
    # ruleAsWordlist should be set to the whole-phrase rule.
    return sum(1 for x in covered if x),len(covered)

def generate_map():
    global corpus_to_markedDown_map, c2m_inverse
    global precalc_sets, yPriorityDic
    if checkpoint:
      try:
        f=open(checkpoint+os.sep+'map','rb')
        corpus_to_markedDown_map,c2m_inverse,precalc_sets,yPriorityDic = pickle.Unpickler(f).load()
        return
      except: pass
    sys.stderr.write("Generating corpus map... ")
    corpus_to_markedDown_map = {} ; c2m_inverse = {}
    precalc_sets = {}
    muStart = downLenSoFar = 0
    for s in re.finditer(re.escape(markupStart), corpus_unistr):
      s=s.start()
      downLenSoFar += len(markDown(corpus_unistr[muStart:s]))
      muStart = s
      corpus_to_markedDown_map[s] = downLenSoFar+1 # +1 as there's a unichr(1) at start of markedDown
      c2m_inverse[downLenSoFar+1] = s
      # Added optimisation: do precalc_sets as well
      # (at least catch the 1-word cases)
      e=corpus_unistr.find(markupEnd,s)
      if e>-1:
        e += len(markupEnd)
        k = corpus_unistr[s:e]
        if k not in precalc_sets: precalc_sets[k]=set()
        precalc_sets[k].add(corpus_to_markedDown_map[s])
    yPriorityDic = {}
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
    if checkpoint: pickle.Pickler(open(checkpoint+os.sep+'map','wb'),-1).dump((corpus_to_markedDown_map,c2m_inverse,precalc_sets,yPriorityDic))
    checkpoint_exit()

def analyse():
    global corpus_unistr
    if ybytes: generate_map()

    # Due to the way we handle overlaps, it's better to process the shortest phrases first, as the longer phrases will yield more rule options and therefore more likely to be able to work around any "no-overlap" constraints imposed by already-processed examples.  Something like:
    p2 = []
    for p in splitWords(corpus_unistr,phrases=True):
      p2.append((min([len(p.split(markupStart)),len(p.split(markupMid)),len(p.split(markupEnd))]),len(p2),p))
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
    covered = toCover = 0 ; phraseNo = 0
    if checkpoint:
      try:
        phraseNo,covered,toCover,accum.__dict__ = pickle.Unpickler(open(checkpoint+os.sep+'checkpoint','rb')).load()
        sys.stderr.write("Checkpoint loaded from %d phrases\n" % phraseNo)
      except: pass
    phraseLastUpdate = phraseLastCheckpoint = phraseNo
    lastUpdate = lastCheckpoint = time.time()
    while phraseNo < len(phrases):
        if toCover:
          if checkpoint and (checkpoint_exit(0) or time.time() >= lastCheckpoint + 1000): # TODO: configurable?
            pickle.Pickler(open(checkpoint+os.sep+'checkpoint-NEW','wb'),-1).dump((phraseNo,covered,toCover,accum.__dict__)) # better write to checkpoint-NEW, in case we reboot or have an OS-level "Out of memory" condition *while* checkpointing
            try: os.rename(checkpoint+os.sep+'checkpoint-NEW',checkpoint+os.sep+'checkpoint')
            except OSError: # OS can't do it atomically?
              try: os.remove(checkpoint+os.sep+'checkpoint')
              except OSError: pass
              try: os.rename(checkpoint+os.sep+'checkpoint-NEW',checkpoint+os.sep+'checkpoint')
              except OSError: pass
            checkpoint_exit()
            lastCheckpoint = time.time()
            phraseLastCheckpoint = phraseNo
          if time.time() >= lastUpdate + 2:
            phraseSec = (phraseNo-phraseLastUpdate)*1.0/(time.time()-lastUpdate)
            if phraseSec < 100:
              phraseSecS = "%.1f" % phraseSec
            else: phraseSecS = "%d" % int(phraseSec)
            progress = "%s phrase/sec (%d%%/#w=%d) rules=%d cover=%d%%" % (phraseSecS,int(100.0*phraseNo/len(phrases)),len([w for w in splitWords(phrases[phraseNo])]),len(accum.rules),int(100.0*covered/toCover))
            if warn_yarowsky: progress += (" rej=%d" % len(accum.rejectedRules))
            if time_estimate:
              if phraseNo-phraseLastCheckpoint < 10: phraseMin = phraseSec*60 # current 'instantaneous' speed
              else: phraseMin = (phraseNo-phraseLastCheckpoint)*60/(time.time()-lastCheckpoint) # longer-term average
              minsLeft = (len(phrases)-phraseNo)/phraseMin
              if minsLeft>60*24: progress += " %dd+" % int(minsLeft/60/24)
              elif minsLeft>60: progress += " %dh+" % int(minsLeft/60)
              elif minsLeft: progress += " %dmin+" % minsLeft
              # (including the + because this is liable to be an underestimate; see comment after the --time-estimate option)
            sys.stderr.write(progress+clear_eol)
            lastUpdate = time.time()
            phraseLastUpdate = phraseNo
        coveredA,toCoverA = accum.addRulesForPhrase(phrases[phraseNo],markedUp,markedDown)
        covered += coveredA ; toCover += toCoverA
        phraseNo += 1
    sys.stderr.write("\n")
    if rulesFile: accum.save()
    if ybytes: return accum.rules
    else: return accum.rules.keys()

def c_escape(unistr,doEncode=True):
    # returns unistr encoded as outcode and escaped so can be put in C in "..."s.  Optionally calls encodeOutstr also.
    s = unistr.encode(outcode)
    if obfuscate and doEncode: s = encodeOutstr(s)
    else: s = s.replace('\\','\\\\').replace('"','\\"')
    return re.sub(r"\?\?([=/'()<>!-])",r'?""?\1',s.replace('\n','\\n')) # (the re.sub part is to get rid of trigraph warnings, TODO might get a marginal efficiency increase if do it to the entire C file at once instead)

def c_length(unistr): return len(unistr.encode(outcode))

def matchingAction(rule,glossDic):
  action = []
  gotAnnot = False
  for w in splitWords(rule):
    wStart = w.index(markupStart)+len(markupStart)
    wEnd = w.index(markupMid,wStart)
    text_unistr = w[wStart:wEnd]
    mStart = wEnd+len(markupMid)
    annotation_unistr = w[mStart:w.index(markupEnd,mStart)]
    if mreverse: text_unistr,annotation_unistr = annotation_unistr,text_unistr
    gloss = glossDic.get((text_unistr,annotation_unistr),glossDic.get(text_unistr,None))
    if reannotator:
      if reannotator[0]=='#': toAdd=annotation_unistr
      else: toAdd = text_unistr
      if toAdd in reannotateDict: annotation_unistr = reannotateDict[toAdd]
      else: toReannotateSet.add(toAdd)
    if gloss:
        if javascript or python: action.append((c_length(text_unistr),annotation_unistr.encode(outcode),gloss.replace('&','&amp;').replace('"','&quot;').encode(outcode)))
        else: action.append('o2(%d,"%s","%s");' % (c_length(text_unistr),c_escape(annotation_unistr),c_escape(gloss.replace('&','&amp;').replace('"','&quot;'))))
    else:
        if javascript or python: action.append((c_length(text_unistr),annotation_unistr.encode(outcode)))
        else: action.append('o(%d,"%s");' % (c_length(text_unistr),c_escape(annotation_unistr)))
    if annotation_unistr or gloss: gotAnnot = True
  return action,gotAnnot

def outputParser(rules):
    # rules is a dictionary if ybytes, otherwise a list
    sys.stderr.write("Generating byte cases...\n")
    glossDic = {}
    if glossfile:
        for l in openfile(glossfile).xreadlines():
            if not l.strip(): continue
            l=l.decode(incode) # TODO: glosscode ?
            try: word,annot,gloss = l.split("\t",2)
            except: sys.stderr.write("Gloss: Ignoring incorrectly-formatted line "+l.strip()+"\n")
            word,annot,gloss = word.strip(),annot.strip(),gloss.strip()
            if not word or not gloss: continue
            if annot: glossDic[(word,annot)] = gloss
            else: glossDic[word] = gloss
    byteSeq_to_action_dict = {}
    if ignoreNewlines:
        if javascript or python: newline_action = [(1,)]
        else: newline_action = r"OutWriteByte('\n'); /* needSpace unchanged */ COPY_BYTE_SKIP;"
        byteSeq_to_action_dict['\n'] = [(newline_action,[])]
    if type(rules)==type([]): rulesAndConds = [(x,[]) for x in rules]
    else: rulesAndConds = rules.items()
    def addRule(rule,conds,byteSeq_to_action_dict,manualOverride=False):
        byteSeq = markDown(rule).encode(outcode)
        action,gotAnnot = matchingAction(rule,glossDic)
        if not gotAnnot: return # probably some spurious o("{","") rule that got in due to markup corruption
        if manualOverride or not byteSeq in byteSeq_to_action_dict: byteSeq_to_action_dict[byteSeq] = []
        if not (javascript or python): action = ' '.join(action)
        byteSeq_to_action_dict[byteSeq].append((action,conds))
    if reannotator:
      # dry run to get the words to reannotate
      global toReannotateSet, reannotateDict
      toReannotateSet = set() ; reannotateDict = {}
      dummyDict = {}
      for rule,conds in rulesAndConds: addRule(rule,conds,dummyDict)
      if manualrules:
        for l in openfile(manualrules).xreadlines():
            if not l.strip(): continue
            l=l.decode(incode) # TODO: manualrulescode ?
            addRule(l,[],dummyDict)
      del dummyDict
      if reannotator[0]=='#': cmd=reannotator[1:]
      else: cmd = reannotator
      cin,cout = os.popen2(cmd)
      l = [ll for ll in toReannotateSet if not "\n" in ll]
      cin.write("\n".join(l).encode(outcode)+"\n") ; cin.close() # TODO: reannotatorCode?
      l2 = cout.read().replace("\r\n","\n").decode(outcode).split("\n") # TODO: reannotatorCode?
      if l2 and not l2[-1]: del l2[-1]
      if not len(l)==len(l2): errExit("reannotator command didn't output the same number of lines as we gave it (gave %d, got %d)" % (len(l),len(l2)))
      toReannotateSet = set() ; reannotateDict = dict(zip(l,l2)) ; del l,l2
    for rule,conds in rulesAndConds: addRule(rule,conds,byteSeq_to_action_dict)
    if manualrules:
        for l in openfile(manualrules).xreadlines():
            if not l.strip(): continue
            l=l.decode(incode) # TODO: manualrulescode ?
            addRule(l,[],byteSeq_to_action_dict,True)
    longest_rule_len = max(len(b) for b in byteSeq_to_action_dict.iterkeys())
    longest_rule_len = max(ybytes_max*2, longest_rule_len) # make sure the half-bufsize is at least ybytes_max*2, so that a read-ahead when pos is ybytes_max from the end, resulting in a shift back to the 1st half of the buffer, will still leave ybytes_max from the beginning, so yar() can look ybytes_max-wide in both directions
    if javascript:
      print js_start
      b = BytecodeAssembler()
      b.addActionDictSwitch(byteSeq_to_action_dict,False)
      print "data:",repr(b.link())+"," ; del b
      print js_end
      return
    if python:
      print py_start
      b = BytecodeAssembler()
      b.addActionDictSwitch(byteSeq_to_action_dict,False)
      print "data=",repr(b.link()) ; del b
      print py_end
      return
    print c_start.replace('%%LONGEST_RULE_LEN%%',str(longest_rule_len)).replace("%%YBYTES%%",str(ybytes_max))
    subFuncL = []
    ret = stringSwitch(byteSeq_to_action_dict,subFuncL)
    print "\n".join(subFuncL + ret) ; del subFuncL,ret
    print c_end
    print
    del byteSeq_to_action_dict
    if no_summary: return
    if reannotator:
        print "/* Tab-delimited rules summary not yet implemented with reannotator option */"
        return
    print "/* Tab-delimited summary of above rules:"
    if manualrules: print "  (not including manual rules)"
    outputRulesSummary(rules)
    print "*/"

def outputRulesSummary(rules):
    # (summary because we don't here specify which part
    # of the annotation goes with which part of the text, plus
    # we remove /* and */ so it can be placed into a C comment)
    sys.stderr.write("Writing rules summary...\n")
    if summary_omit: omit=set(openfile(summary_omit).read().split("\n"))
    else: omit=[]
    if reference_sep and not norefs and not no_input:
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
    else: sys.stderr.write("stdout is not piped, so writing to "+c_filename+"\n") # will open it later (avoid having a 0-length file sitting around during the analyse() run so you don't rm it by mistake)
else: c_filename = None

def openfile(fname,mode='r'):
    if fname.endswith(".gz"):
        import gzip ; return gzip.open(fname,mode)
    elif fname.endswith(".bz2"):
        import bz2 ; return bz2.BZ2File(fname,mode)
    else: return open(fname,mode)

import atexit
def set_title(t):
  if not isatty(sys.stderr): return
  if t: atexit.register(set_title,"")
  term = os.environ.get("TERM","")
  is_xterm = "xterm" in term
  global clear_eol # by the way:
  if is_xterm or term in ["screen","linux"]: clear_eol="\x1b[K\r" # use ANSI escape instead of overwriting with spaces
  is_screen = (term=="screen" and os.environ.get("STY",""))
  is_tmux = (term=="screen" and os.environ.get("TMUX",""))
  if is_xterm or is_tmux: sys.stderr.write("\033]0;%s\007" % (t,)) # ("0;" sets both title and minimised title, "1;" sets minimised title, "2;" sets title.  Tmux takes its pane title from title (but doesn't display it in the titlebar))
  elif is_screen: os.system("screen -X title \"%s\"" % (t,))
clear_eol = "  \r" # hope 2 spaces enough to overwrite old (don't want to risk going onto next line)

if checkpoint:
  try: os.mkdir(checkpoint)
  except: pass

set_title("annogen")
if no_input:
  rules = RulesAccumulator() # should load rulesFile
  if ybytes: rules = rules.rules
  else: rules = rules.rules.keys()
else:
  if infile: infile=openfile(infile)
  else:
    infile = sys.stdin
    if isatty(infile): sys.stderr.write("Reading from standard input\n(If that's not what you wanted, press Ctrl-C and run again with --help)\n")
  corpus_unistr = infile.read().decode(incode)
  normalise()
  rules = analyse() # dict if ybytes, otherwise list

if c_filename: sys.stdout = open(c_filename,"w")
if summary_only: outputRulesSummary(rules)
else: outputParser(rules)
del rules
sys.stderr.write("Done\n")
if c_filename and not (javascript or python):
    sys.stdout.close()
    cmd = c_compiler+" \""+c_filename+"\"" # (the -o option is part of c_compiler)
    sys.stderr.write(cmd+"\n")
    sys.exit(os.system(cmd))
