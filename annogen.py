#!/usr/bin/env python

program_name = "Annotator Generator v0.647 (c) 2012-18 Silas S. Brown"

# See http://people.ds.cam.ac.uk/ssb22/adjuster/annogen.html

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# If you want to compare this code to old versions, the old
# versions are being kept in the E-GuideDog SVN repository on
# http://svn.code.sf.net/p/e-guidedog/code/ssb22/adjuster
# and on GitHub at https://github.com/ssb22/adjuster
# and on GitLab at https://gitlab.com/ssb22/adjuster
# and on BitBucket https://bitbucket.org/ssb22/adjuster
# although some early ones are missing.

from optparse import OptionParser
parser = OptionParser()
import sys,os,os.path,tempfile,time,re,commands
if not "mac" in sys.platform and not "darwin" in sys.platform and ("win" in sys.platform or "mingw32" in sys.platform): exe=".exe" # Windows, Cygwin, etc
else: exe=""

#  =========== INPUT OPTIONS ==============

parser.add_option("--infile",
                  help="Filename of a text file (or a compressed .gz, .bz2 or .xz file or URL) to read the input examples from. If this is not specified, standard input is used.")

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

parser.add_option("-r","--mreverse",
                  action="store_true",default=False,
                  help="Specifies that the annotation markup is reversed, so the text BEFORE mmid is the annotation and the text AFTER it is the base text")
def cancelOpt(opt,act="store_false",dst=None):
  if not dst: dst=opt.replace("-","_")
  parser.add_option("--no-"+opt,action=act,dest=dst,help="Cancels any earlier --"+opt+" option in Makefile variables etc")
cancelOpt("mreverse")

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
cancelOpt("spaces","store_true","removeSpace")

parser.add_option("-c", "--capitalisation",
                  action="store_true",
                  default=False,
                  help="Don't try to normalise capitalisation in the input.  Normally, to simplify the rules, the analyser will try to remove start-of-sentence capitals in annotations, so that the only remaining words with capital letters are the ones that are ALWAYS capitalised such as names.  (That's not perfect: some words might always be capitalised just because they never occur mid-sentence in the examples.)  If this option is used, the analyser will instead try to \"learn\" how to predict the capitalisation of ALL words (including start of sentence words) from their contexts.") # TODO: make the C program put the sentence capitals back
cancelOpt("capitalisation")

parser.add_option("-w", "--annot-whitespace",
                  action="store_true",
                  default=False,
                  help="Don't try to normalise the use of whitespace and hyphenation in the example annotations.  Normally the analyser will try to do this, to reduce the risk of missing possible rules due to minor typographical variations.") # TODO: can this be extended to the point where the words 'try to' can be deleted ?  see comments
cancelOpt("annot-whitespace")
parser.add_option("--keep-whitespace",
                  help="Comma-separated list of words (without annotation markup) for which whitespace and hyphenation should always be kept even without the --annot-whitespace option.  Use when you know the variation is legitimate. This option expects words to be encoded using the system locale (UTF-8 if it cannot be detected).")

parser.add_option("--glossfile",
                  help="Filename of an optional text file (or compressed .gz, .bz2 or .xz file or URL) to read auxiliary \"gloss\" information.  Each line of this should be of the form: word (tab) annotation (tab) gloss.  Extra tabs in the gloss will be converted to newlines (useful if you want to quote multiple dictionaries).  When the compiled annotator generates ruby markup, it will add the gloss string as a popup title whenever that word is used with that annotation.  The annotation field may be left blank to indicate that the gloss will appear for any annotation of that word.  The entries in glossfile do NOT affect the annotation process itself, so it's not necessary to completely debug glossfile's word segmentation etc.")
parser.add_option("-C", "--gloss-closure",
                  action="store_true",
                  default=False,
                  help="If any Chinese, Japanese or Korean word is missing from glossfile, search its closure of variant characters also. This option requires the cjklib package.") # TODO: option to put variant closures into the annotator itself? (generate new rules if not already exist + closure the 'near' tests) but that could unnecessarily increase the annotator size (with --data-driven the increase could be significant unless we implement shared-substringVariants optimisations, and even then it's unclear how this would interact with the space-saving of common-prefix multibyte sequences), + it might not be correct in all cases, e.g. U+91CC in jianti SHOULDN'T be translated to U+88E1/U+88CF in fanti if it's part of a name, although recognising a 'messed-up' name with that substitution might be acceptable. Anyway, using these closures to fill in a missing gloss should be tolerable.
cancelOpt("gloss-closure")
parser.add_option("--glossmiss",
                  help="Name of an optional file to which to write information about words recognised by the annotator that are missing in glossfile (along with frequency counts and references, if available)") # (default sorted alphabetically, but you can pipe through sort -rn to get most freq 1st)
parser.add_option("--glossmiss-hide",
                  help="Comma-separated list of references to hide from the glossmiss file (does not affect the glossmiss-omit option)")
parser.add_option("-M","--glossmiss-omit",
                  action="store_true",
                  default=False,
                  help="Omit rules containing any word not mentioned in glossfile.  Might be useful if you want to train on a text that uses proprietary terms and don't want to accidentally 'leak' those terms (assuming they're not accidentally included in glossfile also).  Words may also be listed in glossfile with an empty gloss field to indicate that no gloss is available but rules using this word needn't be omitted.")
cancelOpt("glossmiss-omit")

parser.add_option("--manualrules",
                  help="Filename of an optional text file (or compressed .gz, .bz2 or .xz file or URL) to read extra, manually-written rules.  Each line of this should be a marked-up phrase (in the input format) which is to be unconditionally added as a rule.  Use this sparingly, because these rules are not taken into account when generating the others and they will be applied regardless of context (although a manual rule might fail to activate if the annotator is part-way through processing a different rule); try checking messages from --diagnose-manual.") # (or if there's a longer automatic match)

#  =========== OUTPUT OPTIONS ==============

parser.add_option("--rulesFile",help="Filename of an optional auxiliary binary file to hold the accumulated rules. Adding .gz, .bz2 or .xz for compression is acceptable. If this is set then the rules will be written to it (in binary format) as well as to the output. Additionally, if the file already exists then rules will be read from it and incrementally updated. This might be useful if you have made some small additions to the examples and would like these to be incorporated without a complete re-run. It might not work as well as a re-run but it should be faster. If using a rulesFile then you must keep the same input (you may make small additions etc, but it won't work properly if you delete many examples or change the format between runs) and you must keep the same ybytes-related options if any.") # You may however change whether or not a --single-words / --max-words option applies to the new examples (but hopefully shouldn't have to)

parser.add_option("-n","--no-input",
                  action="store_true",default=False,
                  help="Don't process new input, just use the rules that were previously stored in rulesFile. This can be used to increase speed if the only changes made are to the output options. You should still specify the input formatting options (which should not change), and any glossfile or manualrules options (which may change). For the glossmiss and summary options to work correctly, unchanged input should be provided.")
cancelOpt("no-input")

parser.add_option("--c-filename",default="",help="Where to write the C, C#, Python, Javascript or Go program. Defaults to standard output, or annotator.c in the system temporary directory if standard output seems to be the terminal (the program might be large, especially if Yarowsky-like indicators are not used, so it's best not to use a server home directory where you might have limited quota). If MPI is in use then the default will always be standard output.") # because the main program might not be running on the launch node

parser.add_option("--c-compiler",default="cc -o annotator"+exe,help="The C compiler to run if generating C and standard output is not connected to a pipe. The default is to use the \"cc\" command which usually redirects to your \"normal\" compiler. You can add options (remembering to enclose this whole parameter in quotes if it contains spaces), but if the C program is large then adding optimisation options may make the compile take a LONG time. If standard output is connected to a pipe, then this option is ignored because the C code will simply be written to the pipe. You can also set this option to an empty string to skip compilation. Default: %default")
# If compiling an experimental annotator quickly, you might try tcc as it compiles fast. If tcc is not available on your system then clang might compile faster than gcc.
# (BUT tcc can have problems on Raspberry Pi see http://www.raspberrypi.org/phpBB3/viewtopic.php?t=30036&p=263213; can be best to cross-compile, e.g. from a Mac use https://github.com/UnhandledException/ARMx/wiki/Sourcery-G---Lite-for-ARM-GNU-Linux-(2009q3-67)-for-Mac-OS-X and arm-none-linux-gnueabi-gcc)
# In large rulesets with --max-or-length=0 and --nested-switch, gcc takes time and gcc -Os can take a LOT longer, and CINT, Ch and picoc run out of memory.  Without these options the overhead of gcc's -Os isn't so bad (and does save some room).
# clang with --max-or-length=100 and --nested-switch=0 is not slowed much by -Os (slowed considerably by -O3). -Os and -Oz gave same size in my tests.
# on 64-bit distros -m32 won't always work and won't necessarily give a smaller program

parser.add_option("--max-or-length",default=100,help="The maximum number of items allowed in an OR-expression in non table-driven code (used when ybytes is in effect). When an OR-expression becomes larger than this limit, it will be made into a function. 0 means unlimited, which works for tcc and gcc; many other compilers have limits. Default: %default")

parser.add_option("--nested-if",
                  action="store_true",default=False,
                  help="Allow C/C#/Java/Go if() blocks (but not switch() constructs) to be nested to unlimited depth.  This probably increases the workload of the compiler's optimiser when reducing size, but may help when optimising for speed.")
cancelOpt("nested-if")
parser.add_option("--nested-switch",default=0,
                  help="Allow C/C#/Java/Go switch() constructs to be nested to about this depth.  Default 0 tries to avoid nesting, as it slows down most C compilers for small savings in executable size.  Setting 1 nests 1 level deeper which can occasionally help get around memory problems with Java compilers.  -1 means nest to unlimited depth, which is not recommended.  Setting this to anything other than 0 implies --nested-if also.") # tcc is still fast (although that doesn't generate the smallest executables anyway)

parser.add_option("--outcode",default="utf-8",
                  help="Character encoding to use in the generated parser and rules summary (default %default, must be ASCII-compatible i.e. not utf-16)")

parser.add_option("-S", "--summary-only",
                  action="store_true",default=False,
                  help="Don't generate a parser, just write the rules summary to standard output")
cancelOpt("summary-only")

parser.add_option("-N","--no-summary",
                  action="store_true",default=False,
                  help="Don't add a large rules-summary comment at the end of the parser code")
cancelOpt("no-summary")

parser.add_option("-O", "--summary-omit",
                  help="Filename of a text file (or a compressed .gz, .bz2 or .xz file or URL) specifying what should be omitted from the rules summary.  Each line should be a word or phrase, a tab, and its annotation (without the mstart/mmid/mend markup).  If any rule in the summary exactly matches any of the lines in this text file, then that rule will be omitted from the summary (but still included in the parser).  Use for example to take out of the summary any entries that correspond to things you already have in your dictionary, so you can see what's new.")

parser.add_option("--maxrefs",default=3,
                  help="The maximum number of example references to record in each summary line, if references are being recorded (0 means unlimited).  Default is %default.")

parser.add_option("-R","--norefs",
                  action="store_true",default=False,
                  help="Don't write references in the rules summary (or the glossmiss file).  Use this if you need to specify reference-sep and ref-name-end for the ref-pri option but you don't actually want references in the summary (which speeds up summary generation slightly).  This option is automatically turned on if --no-input is specified.") # the speed difference is not so great as of v0.593, but needed anyway if --no-input is set
cancelOpt("norefs")

parser.add_option("-E","--newlines-reset",
                  action="store_false",
                  dest="ignoreNewlines",
                  default=True,
                  help="Have the annotator reset its state on every newline byte. By default newlines do not affect state such as whether a space is required before the next word, so that if the annotator is used with Web Adjuster's htmlText option (which defaults to using newline separators) the spacing should be handled sensibly when there is HTML markup in mid-sentence.")
cancelOpt("newlines-reset","store_true","ignoreNewlines")

parser.add_option("-z","--compress",
                  action="store_true",default=False,
                  help="Compress annotation strings in the C code.  This compression is designed for fast on-the-fly decoding, so it saves only a limited amount of space (typically 10-20%) but might help if RAM is short; see also --data-driven.")
cancelOpt("compress")

parser.add_option("--ios",
                  help="Include Objective-C code for an iOS app that opens a web-browser component and annotates the text on every page it loads.  The initial page is specified by this option: it can be a URL, or a markup fragment starting with < to hard-code the contents of the page. Also provided is a custom URL scheme to annotate the local clipboard. You will need Xcode to compile the app; see the start of the generated C file for instructions. If Xcode runs out of space, try using --data-driven")

parser.add_option("-D","--data-driven",
                  action="store_true",default=False,
                  help="Generate a program that works by interpreting embedded data tables for comparisons, instead of writing these as code.  This can take some load off the compiler (so try it if you get errors like clang's \"section too large\"), as well as compiling faster and reducing the resulting binary's RAM size (by 35-40% is typical), at the expense of a small reduction in execution speed.  Javascript and Python output is always data-driven anyway.") # If the resulting binary is compressed (e.g. in an APK), its compressed size will likely not change much (same information content), so I'm specifically saying "RAM size" i.e. when decompressed
cancelOpt("data-driven")
parser.add_option("-F","--fast-assemble",
                  action="store_true",default=False,
                  help="Skip opcode compaction when using data-driven (slightly speeds up compilation, at the expense of larger code size)") # TODO: consider removing this option now it's no longer very slow anyway
cancelOpt("fast-assemble")

parser.add_option("-Z","--zlib",
                  action="store_true",default=False,
                  help="Enable --data-driven and compress the embedded data table using zlib, and include code to call zlib to decompress it on load.  Useful if the runtime machine has the zlib library and you need to save disk space but not RAM (the decompressed table is stored separately in RAM, unlike --compress which, although giving less compression, at least works 'in place').  Once --zlib is in use, specifying --compress too will typically give an additional disk space saving of less than 1% (and a runtime RAM saving that's greater but more than offset by zlib's extraction RAM).  If generating a Javascript annotator, the decompression code is inlined so there's no runtime zlib dependency, but startup is ~50% slower so this option is not recommended in situations where the annotator is frequently reloaded from source.") # compact_opcodes typically still helps no matter what the other options are
cancelOpt("zlib")

parser.add_option("-W","--windows-clipboard",
                  action="store_true",default=False,
                  help="Include C code to read the clipboard on Windows or Windows Mobile and to write an annotated HTML file and launch a browser, instead of using the default cross-platform command-line C wrapper.  See the start of the generated C file for instructions on how to compile for Windows or Windows Mobile.")
cancelOpt("windows-clipboard")

parser.add_option("-#","--c-sharp",
                  action="store_true",default=False,
                  help="Instead of generating C code, generate C# (not quite as efficient as the C code but close; might be useful for adding an annotator to a C# project; see comments at the start for usage)")
cancelOpt("c-sharp")

parser.add_option("--java",
                  help="Instead of generating C code, generate Java, and place the *.java files in the directory specified by this option.  See --android for example use.  The last part of the directory should be made up of the package name; a double slash (//) should separate the rest of the path from the package name, e.g. --java=/path/to/wherever//org/example/package and the main class will be called Annotator.")
parser.add_option("--android",
                  help="URL for an Android app to browse.  If this is set, code is generated for an Android app which starts a browser with that URL as the start page, and annotates the text on every page it loads.  Use file:///android_asset/index.html for local HTML files in the assets directory; a clipboard viewer is placed in clipboard.html.  If certain environment variables are set, this option can also compile and sign the app using Android SDK command-line tools; if the necessary environment variables are not set, this option will just write the files and print a message on stderr explaining what needs to be set for automated command-line building.")
parser.add_option("--ndk",
                  action="store_true",default=False,
                  help="Android NDK: make a C annotator and use ndk-build to compile it into a 32-bit Android JNI library.  This is no longer recommended: it's a more complex setup than a Java-based annotator, it restricts which Android versions can be supported if you are compiling on newer toolsets (see --ndk-pre-* options), and it's unsuitable for environments where dual 32-/64-bit binaries are required, such as \"Play Store\" in 2019+.  The speed bonus of NDK is increasingly negligible now that --data-driven and --zlib are also available in the Java version.") # 'increasingly' due to Android's own improvements to JIT etc.  Could add support for dual 32/64-bit, but that would double the binary size (unless shared data is passed in from the Java, but if the JIT works well anyway then what's the point)
cancelOpt("ndk")
parser.add_option("--ndk-pre-2017",
                  action="store_true",default=False,
                  help="When building with ndk-build, assume it's older than the July 2017 release (r15c) and therefore supports Android versions below 4.0")
cancelOpt("ndk-pre-2017")
parser.add_option("--ndk-pre-2016",
                  action="store_true",default=False,
                  help="When building with ndk-build, assume it's older than the June 2016 release (r12) and therefore supports Android versions below 2.3")
cancelOpt("ndk-pre-2016")

parser.add_option("--bookmarks",
                  help="Android bookmarks: comma-separated list of package names that share our bookmarks. If this is not specified, the browser will not be given a bookmarks function. If it is set to the same value as the package specified in --java, bookmarks are kept in just this Android app. If it is set to a comma-separated list of packages that have also been generated by annogen (presumably with different annotation types), and if each one has the same android:sharedUserId attribute in AndroidManifest.xml's 'manifest' tag and is signed by the same certificate, then bookmarks can be shared across the set of browser apps, but beware that adding an android:sharedUserId attribute to an app that has already been released without one causes some devices to refuse the update.")
parser.add_option("--bookmarks-developer",
                  action="store_true",default=False,
                  help="When Android bookmarks are enabled, include extra code so that, if the device is in 'developer mode' and the Add Bookmark tool is double-tapped, all words lacking glosses are marked with a blue border. This might give you an idea of how good your glossfile coverage is in practice.")
cancelOpt("bookmarks-developer")
parser.add_option("--android-urls",
                  help="Whitespace-separated list of URL prefixes to offer to be a browser for, when a matching URL is opened by another Android application")
parser.add_option("--extra-js",help="Extra Javascript to inject into sites to fix things in the Android or iOS browser app. The snippet will be run before each scan for new text to annotate.")
parser.add_option("--extra-css",help="Extra CSS to inject into sites to fix things in the Android or iOS browser app")
parser.add_option("--app-name",default="Annotating browser",
                  help="User-visible name of the Android app")

parser.add_option("--compile-only",
                  action="store_true",default=False,
                  help="Assume the code has already been generated by a previous run, and just run the compiler")
cancelOpt("compile-only")

parser.add_option("-j","--javascript",
                  action="store_true",default=False,
                  help="Instead of generating C code, generate JavaScript.  This might be useful if you want to run an annotator on a device that has a JS interpreter but doesn't let you run native code.  The JS will be table-driven to make it load faster (and --no-summary will also be set).  See comments at the start for usage.") # but it's better to use the C version if you're in an environment where 'standard input' makes sense
cancelOpt("javascript")

parser.add_option("-6","--js-6bit",
                  action="store_true",default=False,
                  help="When generating a Javascript annotator, use a 6-bit format for many addresses to reduce escape codes in the data string by making more of it ASCII. Not relevant if using zlib.") # May result in marginally slower JS, but it should be smaller and parse more quickly on initial load, which is normally the dominant factor if you have to reload it on every page.
cancelOpt("js-6bit")

parser.add_option("-8","--js-octal",
                  action="store_true",default=False,
                  help="When generating a Javascript annotator, use octal instead of hexadecimal codes in the data string when doing so would save space. This does not comply with ECMAScript 5 and may give errors in its strict mode. Not relevant if using zlib.")
cancelOpt("js-octal")

parser.add_option("-9","--ignore-ie8",
                  action="store_true",default=False,
                  help="When generating a Javascript annotator, do not make it backward-compatible with Microsoft Internet Explorer 8 and below. This may save a few bytes. Not relevant if using zlib.")
cancelOpt("ignore-ie8")

parser.add_option("-u","--js-utf8",
                  action="store_true",default=False,
                  help="When generating a Javascript annotator, assume the script can use UTF-8 encoding directly and not via escape sequences. In some browsers this might work only on UTF-8 websites.")
cancelOpt("js-utf8")

parser.add_option("-Y","--python",
                  action="store_true",default=False,
                  help="Instead of generating C code, generate a Python module.  Similar to the Javascript option, this is for when you can't run native code, and it is table-driven for fast loading.")
cancelOpt("python")

parser.add_option("--golang",
                  help="Package name for a Go library to generate instead of C code.  See comments in the generated file for how to run this on AppEngine.")

parser.add_option("--reannotator",
                  help="Shell command through which to pipe each word of the original text to obtain new annotation for that word.  This might be useful as a quick way of generating a new annotator (e.g. for a different topolect) while keeping the information about word separation and/or glosses from the previous annotator, but it is limited to commands that don't need to look beyond the boundaries of each word.  If the command is prefixed by a # character, it will be given the word's existing annotation instead of its original text, and if prefixed by ## it will be given text#annotation.  The command should treat each line of its input independently, and both its input and its output should be in the encoding specified by --outcode.") # TODO: reannotatorCode instead? (see other 'reannotatorCode' TODOs)
# (Could just get the reannotator to post-process the 1st annotator's output, but that might be slower than generating an altered annotator with it)

parser.add_option("--sharp-multi",
                  action="store_true",default=False,
                  help="Assume annotation (or reannotator output) contains multiple alternatives separated by # (e.g. pinyin#Yale) and include code to select one by number at runtime (starting from 0). This is to save on total space when shipping multiple annotators that share the same word grouping and gloss data, differing only in the transcription of each word.")
cancelOpt("sharp-multi")

#  =========== ANALYSIS OPTIONS ==============

parser.add_option("-o", "--allow-overlaps",
                  action="store_true",default=False,
                  help="Normally, the analyser avoids generating rules that could overlap with each other in a way that would leave the program not knowing which one to apply.  If a short rule would cause overlaps, the analyser will prefer to generate a longer rule that uses more context, and if even the entire phrase cannot be made into a rule without causing overlaps then the analyser will give up on trying to cover that phrase.  This option allows the analyser to generate rules that could overlap, as long as none of the overlaps would cause actual problems in the example phrases. Thus more of the examples can be covered, at the expense of a higher risk of ambiguity problems when applying the rules to other texts.  See also the -y option.")
cancelOpt("allow-overlaps")

parser.add_option("-P", "--primitive",
                  action="store_true",default=False,
                  help="Don't bother with any overlap or conflict checks at all, just make a rule for each word. The resulting parser is not likely to be useful, but the summary might be.")
cancelOpt("primitive")

parser.add_option("-y","--ybytes",default=0,
                  help="Look for candidate Yarowsky seed-collocations within this number of bytes of the end of a word.  If this is set then overlaps and rule conflicts will be allowed if the seed collocations can be used to distinguish between them.  Markup examples that are completely separate (e.g. sentences from different sources) must have at least this number of (non-whitespace) bytes between them.")
parser.add_option("--ybytes-max",default=0,
                  help="Extend the Yarowsky seed-collocation search to check over larger ranges up to this maximum.  If this is set then several ranges will be checked in an attempt to determine the best one for each word, but see also ymax-threshold.")
parser.add_option("--ymax-threshold",default=1,
                  help="Limits the length of word that receives the narrower-range Yarowsky search when ybytes-max is in use. For words longer than this, the search will go directly to ybytes-max. This is for languages where the likelihood of a word's annotation being influenced by its immediate neighbours more than its distant collocations increases for shorter words, and less is to be gained by comparing different ranges when processing longer words. Setting this to 0 means no limit, i.e. the full range will be explored on ALL Yarowsky checks.") # TODO: see TODO below re temporary recommendation of --ymax-threshold=0
parser.add_option("--ybytes-step",default=3,
                  help="The increment value for the loop between ybytes and ybytes-max")
parser.add_option("-k","--warn-yarowsky",
                  action="store_true",default=False,
                  help="Warn when absolutely no distinguishing Yarowsky seed collocations can be found for a word in the examples")
cancelOpt("warn-yarowsky")
parser.add_option("-K","--yarowsky-all",
                  action="store_true",default=False,
                  help="Accept Yarowsky seed collocations even from input characters that never occur in annotated words (this might include punctuation and example-separation markup)")
cancelOpt("yarowsky-all")
parser.add_option("--yarowsky-debug",default=1,
                  help="Report the details of seed-collocation false positives if there are a large number of matches and at most this number of false positives (default %default). Occasionally these might be due to typos in the corpus, so it might be worth a check.")

parser.add_option("-1","--single-words",
                  action="store_true",default=False,
                  help="Do not consider any rule longer than 1 word, although it can still have Yarowsky seed collocations if -y is set. This speeds up the search, but at the expense of thoroughness. You might want to use this in conjuction with -y to make a parser quickly. It is like -P (primitive) but without removing the conflict checks.")
cancelOpt("single-words")
parser.add_option("--max-words",default=0,
                  help="Limits the number of words in a rule; rules longer than this are not considered.  0 means no limit.  --single-words is equivalent to --max-words=1.  If you need to limit the search time, and are using -y, it should suffice to use --single-words for a quick annotator or --max-words=5 for a more thorough one.")  # (There was a bug in annogen versions before 0.58 that caused --max-words to additionally limit how far away from the start of its phrase a rule-example must be placed; this has now been fixed.  There was also a bug that resulted in too many extra rules being tested over already-catered-for phrases; as this has now been fixed, the additional benefit of a --max-words limit is now reduced, but you might want to put one in anyway.  That second bug also had the effect of the coverage % being far too low in the progress stats.)

# TODO: optionally (especially if NOT using Yarowsky) do an additional pass (after discovering all other rules) and turn whole phrases that are not completely covered by other rules into whole-phrase rules, if it doesn't conflict 1 phrase w. anothr of equal priority; shld be ok if no overlap, overlaps wld *sometimes* be ok suggest a len threshold

parser.add_option("--checkpoint",help="Periodically save checkpoint files in the specified directory.  These files can save time when starting again after a reboot (and it's easier than setting up Condor etc).  As well as a protection against random reboots, this can be used for scheduled reboots: if file called ExitASAP appears in the checkpoint directory, annogen will checkpoint, remove the ExitASAP file, and exit.  After a run has completed, the checkpoint directory should be removed, unless you want to re-do the last part of the run for some reason.")
# (Condor can checkpoint an application on Win/Mac/Linux but is awkward to set up.  Various Linux and BSD application checkpoint approaches also exist, and virtual machines can have their state saved.  On the other hand the physical machine might have a 'hibernate' option which is easier.)

parser.add_option("-d","--diagnose",help="Output some diagnostics for the specified word. Use this option to help answer \"why doesn't it have a rule for...?\" issues. This option expects the word without markup and uses the system locale (UTF-8 if it cannot be detected).")
parser.add_option("--diagnose-limit",default=10,help="Maximum number of phrases to print diagnostics for (0 means unlimited); can be useful when trying to diagnose a common word in rulesFile without re-evaluating all phrases that contain it. Default: %default")
parser.add_option("-m","--diagnose-manual",
                  action="store_true",default=False,
                  help="Check and diagnose potential failures of --manualrules")
cancelOpt("diagnose-manual")
parser.add_option("-q","--diagnose-quick",
                  action="store_true",default=False,
                  help="Ignore all phrases that do not contain the word specified by the --diagnose option, for getting a faster (but possibly less accurate) diagnostic.  The generated annotator is not likely to be useful when this option is present.  You may get quick diagnostics WITHOUT these disadvantages by loading a --rulesFile instead.")
cancelOpt("diagnose-quick")

parser.add_option("-t","--time-estimate",
                  action="store_true",default=False,
                  help="Estimate time to completion.  The code to do this is unreliable and is prone to underestimate.  If you turn it on, its estimate is displayed at the end of the status line as days, hours or minutes.") # Unreliable because the estimate assumes 'phrases per minute' will remain constant on average, whereas actually it will decrease because the more complex phrases are processed last
cancelOpt("time-estimate")

parser.add_option("-0","--single-core",
                  action="store_true",default=False,
                  help="Use only one CPU core even when others are available. If this option is not set, multiple cores are used if a 'futures' package is installed or if run under MPI or SCOOP; this currently requires --checkpoint + shared filespace, and is currently used only for large collocation checks in limited circumstances.") # namely, words that occur in length-1 phrases
cancelOpt("single-core")

parser.add_option("-p","--status-prefix",help="Label to add at the start of the status line, for use if you batch-run annogen in multiple configurations and want to know which one is currently running")

main = (__name__ == "__main__" and not os.environ.get("OMPI_COMM_WORLD_RANK","0").replace("0",""))
term = os.environ.get("TERM","")
is_xterm = "xterm" in term
ansi_escapes = is_xterm or term in ["screen","linux"]
def isatty(f): return hasattr(f,"isatty") and f.isatty()
if ansi_escapes and isatty(sys.stderr): clear_eol,reverse_on,reverse_off,bold_on,bold_off="\x1b[K\r","\x1b[7m","\x1b[0m","\x1b[1m","\x1b[0m"
else: clear_eol,reverse_on,reverse_off,bold_on,bold_off="  \r"," **","** ","",""
if main: sys.stderr.write(bold_on+program_name+bold_off+"\n") # not sys.stdout: may or may not be showing --help (and anyway might want to process the help text for website etc)
# else (if not main), STILL parse options (if we're being imported for parallel processing)
options, args = parser.parse_args()
globals().update(options.__dict__)

sys.setcheckinterval(32767) # won't be using threads or signals, so don't have to check for them very often
import gc ; gc.disable() # should be OK if we don't create cycles (TODO: run gc.collect() manually after init, just in case?)

def warn(msg):
  if main: sys.stderr.write("Warning: "+msg+"\n")
  # else it should have already been written
if "PyPy" in sys.version: warn("with annogen, PyPy is likely to run 60% slower than python") # (not to mention concurrent.futures being less likely to be available)

if primitive and ybytes: warn("primitive will override ybytes")
if ybytes: ybytes=int(ybytes)
if ybytes_max: ybytes_max=int(ybytes_max)
else: ybytes_max = ybytes
if yarowsky_debug: yarowsky_debug=int(yarowsky_debug)
else: yarowsky_debug = 0
ybytes_step = int(ybytes_step)
maxrefs = int(maxrefs)
ymax_threshold = int(ymax_threshold)
if not golang: golang = ""
if nested_switch: nested_if = True
def errExit(msg):
  assert main # bad news if this happens in non-main module
  try:
    if not outfile==sys.stdout:
      outfile.close() ; rm_f(c_filename)
  except: pass # works only if got past outfile opening
  sys.stderr.write(msg+"\n") ; sys.exit(1)
if args: errExit("Unknown argument "+repr(args[0]))
if ref_pri and not (reference_sep and ref_name_end): errExit("ref-pri option requires reference-sep and ref-name-end to be set")
if android and not java: errExit('You must set --java=/path/to/src//name/of/package when using --android')
if ndk and not android: errExit("You must set --android=URL when using --ndk. E.g. --android=file:///android_asset/index.html")
if (ndk_pre_2016 or ndk_pre_2017) and not ndk: errExit("--ndk-pre-* options don't make sense when not using --ndk")
if bookmarks and not android: errExit("--bookmarks requires --android, e.g. --android=file:///android_asset/index.html")
if (extra_js or extra_css) and not (android or ios): errExit("--extra-js and --extra-css require either --android or --ios")
if not extra_js: extra_js = ""
if extra_js.rstrip() and not extra_js.rstrip()[-1] in ';}': errExit("--extra-js must end with a semicolon or a closing brace")
if not extra_css: extra_css = ""
jPackage = None
if nested_switch: nested_switch=int(nested_switch) # TODO: if java, override it?  or just rely on the help text for --nested-switch (TODO cross-reference it from --java?)
if java:
  if not '//' in java: errExit("--java must include a // to separate the first part of the path from the package name")
  jSrc,jRest=java.rsplit('//',1)
  if '.' in jRest: errExit("--java must be ...src//org/example/package not ...src//org.example.package") # (TODO: fix it automatically in both jRest and java? only on the right-hand side of the //)
  jPackage = jRest.replace('/','.')
  if 'NewFunc' in jPackage: errExit("Currently unable to include the string 'NewFunc' in your package due to an implementation detail in annogen's search/replace operations")
if not c_filename and isatty(sys.stdout): # assumed false when run under MPI
  c_filename = tempfile.gettempdir()+os.sep+"annotator.c"
def shell_escape(arg):
  if re.match("^[A-Za-z0-9_=/.%+,:@-]*$",arg): return arg
  return "'"+arg.replace("'",r"'\''")+"'"
if sharp_multi:
  if c_sharp or python or golang: errExit("sharp-multi not yet implemented in C#, Python or Go")
  elif ios or windows_clipboard: errExit("sharp-multi not yet implemented for ios or windows-clipboard") # would need a way to select the annotator, probably necessitating a GUI on Windows (and extra callbacks on iOS)
if java or javascript or python or c_sharp or golang:
    if ios: errExit("--ios not yet implemented in C#, Java, JS, Python or Go; please use C (it becomes Objective-C)")
    if windows_clipboard: errExit("--windows-clipboard not yet implemented in C#, Java, JS, Python or Go; please use C")
    if sum(1 for x in [java,javascript,python,c_sharp,golang] if x) > 1:
      errExit("Outputting more than one programming language on the same run is not yet implemented")
    if not outcode=="utf-8": errExit("outcode must be utf-8 when using Java, Javascript, Python, C# or Go")
    if compress and not ndk:
      if android: errExit("--compress without --ndk not yet implemented for Android, but --zlib typically gives results within 1% of --zlib --compress")
      else: errExit("--compress not yet implemented for the Java, Javascript, Python, C# or Go versions") # (and it would probably slow down JS/Python too much if it were implemented in that)
    if java:
      if android and not "/src//" in java: errExit("When using --android, the last thing before the // in --java must be 'src' e.g. --java=/workspace/MyProject/src//org/example/package")
      if main and not compile_only: # (delete previous files, only if we're not an MPI-etc subprocess)
       os.system("mkdir -p "+shell_escape(java))
       for f in os.listdir(java):
        if f.endswith(".java") and (f.startswith("z") or f in ["topLevelMatch.java","Annotator.java"]): os.remove(java+os.sep+f) # (may want to remove topLevelMatch & Annotator if moving from non-ndk to ndk)
      if ndk:
        c_filename = jSrc+"/../jni/annotator.c"
        if main: os.system("mkdir -p "+shell_escape(c_filename[:c_filename.rindex('/')]))
      else: c_filename = java+os.sep+"Annotator.java"
      if main and android:
        os.system("rm -rf "+shell_escape(jSrc+"/../bin")) # needed to get rid of old *.class files that might be no longer used
        for d in ["assets","bin","gen","res/layout","res/menu","res/values"]: os.system("mkdir -p "+shell_escape(jSrc+"/../"+d))
    elif c_filename.endswith(".c"):
      if javascript: c_filename = c_filename[:-2]+".js"
      elif c_sharp: c_filename = c_filename[:-2]+".cs"
      elif golang: c_filename = c_filename[:-2]+".go"
      else: c_filename = c_filename[:-2]+".py"
elif windows_clipboard:
  if ios: errExit("Support for having both --ios and --windows-clipboard at the same time is not yet implemented") # (I suppose you could make a single output file that will compile as either C+MS-stuff or Objective-C depending on preprocessor tests)
  if ndk: errExit("Support for having both --ndk and --windows-clipboard at the same time is not yet implemented")
  if c_compiler=="cc -o annotator": c_compiler="i386-mingw32-gcc -o annoclip.exe"
  if not outcode=="utf-8": errExit("outcode must be utf-8 when using --windows-clipboard")
elif ios:
  if ndk: errExit("Support for having both --ios and --ndk at the same time is not yet implemented")
  if not outcode=="utf-8": errExit("outcode must be utf-8 when using --ios")
  if c_filename.endswith(".c"): c_filename = c_filename[:-2]+".m" # (if the instructions are followed, it'll be ViewController.m, but no need to enforce that here)
if js_6bit:
  if not javascript: errExit("--js-6bit requires --javascript") # or just set js_6bit=False in these circumstances?
  import urllib
if zlib:
  js_6bit = js_utf8 = False
  del zlib ; import zlib ; data_driven = True
  if windows_clipboard: warn("--zlib with --windows-clipboard is inadvisable because ZLib is not typically present on Windows platforms. If you really want it, you'll need to figure out the compiler options and library setup for it.")
  if ios: warn("--zlib with --ios will require -lz to be added to the linker options in XCode, and I don't have instructions for that (it probably differs across XCode versions)")
if data_driven:
  if c_sharp or golang: errExit("--data-driven and --zlib are not yet implemented in C# or Go")
  elif java and not android: errExit("In Java, --data-driven and --zlib currently require --android as we need to know where to store the data file") # TODO: option to specify path in 'pure' Java? (in which case also update the 'compress' errExit above so it doesn't check for android before suggesting zlib)
elif javascript or python: data_driven = True
compact_opcodes = data_driven and not fast_assemble and not python # currently implemented only in the C, Java and Javascript versions of the data-driven runtime
if java or javascript or python or c_sharp or ios or ndk or golang:
  c_compiler = None
try:
  import locale
  terminal_charset = locale.getdefaultlocale()[1]
except: terminal_charset = None
if not terminal_charset: terminal_charset = "utf-8"
if android_urls:
  if not android: errExit("--android-urls requires --android (you need to set a default URL for direct launch)")
  try: import urlparse
  except: errExit("--android-urls requires urlparse module") # unless we re-implement
else: android_urls = "" # so it can still be .split()
if keep_whitespace: keep_whitespace = set(keep_whitespace.decode(terminal_charset).split(','))
if glossmiss_hide: glossmiss_hide = set(glossmiss_hide.decode(terminal_charset).split(','))
if status_prefix: status_prefix += ": "
else: status_prefix = ""
if diagnose: diagnose=diagnose.decode(terminal_charset)
diagnose_limit = int(diagnose_limit)
max_words = int(max_words)
if single_words: max_words = 1
read_input = not no_input
if not reference_sep: norefs=True
if diagnose_manual or (not norefs and (not no_summary or glossmiss)): read_input = True

def nearCall(negate,conds,subFuncs,subFuncL):
  # returns what to put in the if() for ybytes near() lists
  if not max_or_length or len(conds) <= max_or_length:
    if java and not ndk: f="a.n"
    else: f="near"
    ret = " || ".join(f+"(\""+outLang_escape(c)+"\")" for c in conds)
    if negate:
      if " || " in ret: ret = " ! ("+ret+")"
      else: ret = "!"+ret
    return ret
  if java and not ndk: fStart,fEnd = "package "+jPackage+";\npublic class NewFunc { public static boolean f("+jPackage+".Annotator a) {","} }" # put functions in separate classes to try to save the constants table of the main class
  elif golang: fStart,fEnd = "func NewFunc() bool {","}"
  else: fStart,fEnd = outLang_bool+" NewFunc() {","}"
  if negate: rTrue,rFalse = outLang_false,outLang_true
  else: rTrue,rFalse = outLang_true,outLang_false
  return subFuncCall(fStart+"\n".join(outLang_shortIf(nearCall(False,conds[i:j],subFuncs,subFuncL),"return "+rTrue+";") for i,j in zip(range(0,len(conds),max_or_length),range(max_or_length,len(conds),max_or_length)+[len(conds)]))+"\nreturn "+rFalse+";"+fEnd,subFuncs,subFuncL)

def outLang_shortIf(cond,statement):
  if golang: return "if "+cond+" {\n  "+statement+"\n}"
  else: return "if("+cond+") "+statement

def subFuncCall(newFunc,subFuncs,subFuncL):
  if newFunc in subFuncs:
    # we generated an identical one before
    subFuncName=subFuncs[newFunc]
  else:
    if java and not ndk: subFuncName="z%X" % len(subFuncs) # (try to save as many bytes as possible because it won't be compiled out and we also have to watch the compiler's footprint; start with z so MainActivity.java etc appear before rather than among this lot in IDE listings)
    else: subFuncName="match%d" % len(subFuncs)
    subFuncs[newFunc]=subFuncName
    if java or c_sharp or golang: static=""
    else: static="static "
    subFuncL.append(static+newFunc.replace("NewFunc",subFuncName,1))
  if java and not ndk: return jPackage+"."+subFuncName+".f(a)"
  return subFuncName+"()" # the call (without a semicolon)

def stringSwitch(byteSeq_to_action_dict,subFuncL,funcName="topLevelMatch",subFuncs={},java_localvar_counter=None,nestingsLeft=None): # ("topLevelMatch" is also mentioned in the C code)
    # make a function to switch on a large number of variable-length string cases without repeated lookahead for each case
    # (may still backtrack if no words or no suffices match)
    # byteSeq_to_action_dict is really a byte sequence to [(action, OR-list of Yarowsky-like indicators which are still in Unicode)], the latter will be c_escape()d
    # can also be byte seq to [(action,(OR-list,nbytes))] but only if OR-list is not empty, so value[1] will always be false if OR-list is empty
    if nestingsLeft==None: nestingsLeft=nested_switch
    canNestNow = not nestingsLeft==0 # (-1 = unlimited)
    if java and not ndk: adot = "a."
    else: adot = ""
    if java or c_sharp or golang: NEXTBYTE = adot + 'nB()'
    else: NEXTBYTE = 'NEXTBYTE'
    allBytes = set(b[0] for b in byteSeq_to_action_dict.iterkeys() if b)
    ret = []
    if not java_localvar_counter: # Java and C# don't allow shadowing of local variable names, so we'll need to uniquify them
      java_localvar_counter=[0]
    olvc = "%X" % java_localvar_counter[0] # old localvar counter
    if funcName:
        if java and not ndk: ret.append("package "+jPackage+";\npublic class "+funcName+" { public static void f("+jPackage+".Annotator a) {")
        else:
          if funcName=="topLevelMatch" and not c_sharp: stat="static " # because we won't call subFuncCall on our result
          else: stat=""
          if golang: ret.append("func %s() {" % funcName)
          else: ret.append(stat+"void %s() {" % funcName)
        savePos = len(ret)
        if java or c_sharp: ret.append("{ int oldPos="+adot+"inPtr;")
        elif golang: ret.append("{ oldPos := inPtr;")
        else: ret.append("{ POSTYPE oldPos=THEPOS;")
    elif "" in byteSeq_to_action_dict and len(byteSeq_to_action_dict) > 1:
        # no funcName, but might still want to come back here as there's a possible action at this level
        savePos = len(ret)
        if java or c_sharp:
          ret.append("{ int oP"+olvc+"="+adot+"inPtr;")
          java_localvar_counter[0] += 1
        elif golang: ret.append("{ oldPos := inPtr;")
        else: ret.append("{ POSTYPE oldPos=THEPOS;")
    else: savePos = None
    def restorePos():
      if not savePos==None:
        if len(' '.join(ret).split(NEXTBYTE))==2 and not called_subswitch:
            # only 1 NEXTBYTE after the savePos - just
            # do a PREVBYTE instead
            # (note however that splitting on NEXTBYTE
            # does not necessarily give a reliable value
            # for max amount of lookahead required if
            # there's more than 1.  We use max rule len
            # as an upper bound for that instead.)
            del ret[savePos]
            if java and not ndk: ret.append("a.inPtr--;")
            elif c_sharp or golang: ret.append("inPtr--;")
            else: ret.append("PREVBYTE;")
        elif java or c_sharp:
          if funcName: ret.append(adot+"inPtr=oldPos; }")
          else: ret.append(adot+"inPtr=oP"+olvc+"; }")
        elif golang: ret.append("inPtr=oldPos; }")
        else: ret.append("SETPOS(oldPos); }") # restore
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
        del byteSeq_to_action_dict[""]
        if java and (canNestNow or len(byteSeq_to_action_dict)==1): # hang on - better nest (might be using --nested-switch to get around a Java compiler-memory problem; the len condition allows us to always nest a single 'if' rather than creating a new function+class for it)
          ret += ["  "+x for x in stringSwitch(byteSeq_to_action_dict,subFuncL,None,subFuncs,java_localvar_counter,nestingsLeft)]
          restorePos()
          ret.append("return;")
        else: # ok, new function
          newFunc = "\n".join(stringSwitch(byteSeq_to_action_dict,subFuncL,"NewFunc",subFuncs))
          ret.append(subFuncCall(newFunc,subFuncs,subFuncL)+"; return;")
          del ret[savePos] # will be set to None below
        byteSeq_to_action_dict[""] = [("",[])] # for the end of this func
        savePos = None # as setting funcName on stringSwitch implies it'll give us a savePos, and if we didn't set funcName then we called restorePos already above
    elif allBytes:
      # deal with all actions except "" first
      use_if = (len(allBytes)==1)
      if not use_if:
        if nestingsLeft > 0: nestingsLeft -= 1
        ret.append("switch("+NEXTBYTE+") {")
      for case in sorted(allBytes):
        if not c_sharp and 32<=ord(case)<127 and case!="'": cstr="'%c'" % case
        elif ios and ord(case)>127: cstr=str(ord(case)-256)
        else:
          cstr=str(ord(case))
          if java and not ndk: cstr = "(byte)"+cstr
        if use_if: ret.append("if("+NEXTBYTE+"=="+cstr+") {")
        else: ret.append("case %s:" % cstr)
        subDict = dict([(k[1:],v) for k,v in byteSeq_to_action_dict.iteritems() if k and k[0]==case])
        inner = stringSwitch(subDict,subFuncL,None,subFuncs,java_localvar_counter,nestingsLeft)
        if canNestNow or not (inner[0].startswith("switch") or (inner[0].startswith("if(") and not nested_if)): ret += ["  "+x for x in inner]
        else:
          # Put the inner switch into a different function
          # which returns 1 if we should return.
          # (TODO: this won't catch cases where there's a savePos before the inner switch; will still nest in that case.  But it shouldn't lead to big nesting in practice.)
          if nested_switch: inner = stringSwitch(subDict,subFuncL,None,subFuncs,None,None) # re-do it with full nesting counter
          if java and not ndk: myFunc,funcEnd = ["package "+jPackage+";\npublic class NewFunc { public static boolean f("+jPackage+".Annotator a) {"], "}}"
          elif golang: myFunc,funcEnd=["func NewFunc() bool {"],"}"
          else: myFunc,funcEnd=[outLang_bool+" NewFunc() {"],"}"
          for x in inner:
            if x.endswith("return;"): x=x[:-len("return;")]+"return "+outLang_true+";"
            myFunc.append("  "+x)
          ret += ("  "+outLang_shortIf(subFuncCall("\n".join(myFunc)+"\n  return "+outLang_false+";\n"+funcEnd,subFuncs,subFuncL),"return;")).split('\n') # if golang, MUST have the \n before the 1st return there (optional for other languages); also must split outLang_shortIf o/p into \n for the above 'for x in inner' rewrite to work
          called_subswitch=True # as it'll include more NEXTBYTE calls which are invisible to the code below
        if not (use_if or inner[-1].endswith("return;")): ret.append("  break;")
      ret.append("}") # end of switch or if
    restorePos()
    if funcName:
      if java and not ndk: ret.append("} }")
      else: ret.append("}")
    elif "" in byteSeq_to_action_dict:
        # if the C code gets to this point, no return; happened - no suffices
        # so execute one of the "" actions and return
        # (which one, if any, depends on the Yarowsky-like indicators; there should be at most one "default" action without indicators)
        default_action = ""
        for action,conds in byteSeq_to_action_dict[""]:
            if conds:
                assert action, "conds without action in "+repr(byteSeq_to_action_dict[""])
                if type(conds)==tuple:
                    negate,conds,nbytes = conds
                    if java and not ndk: ret.append("a.sn(%d);" % nbytes)
                    elif c_sharp or golang: ret.append("nearbytes=%d;" % nbytes)
                    else: ret.append("setnear(%d);" % nbytes)
                else: negate = False
                ret.append("if ("+nearCall(negate,conds,subFuncs,subFuncL)+") {")
                ret.append((action+" return;").strip())
                ret.append("}")
            else: # no conds
                if default_action:
                  sys.stderr.write("WARNING! More than one default action in "+repr(byteSeq_to_action_dict[""])+" - earlier one discarded!\n")
                  if rulesFile: sys.stderr.write("(This might indicate invalid markup in the corpus, but it might just be due to a small change or capitalisation update during an incremental run, which can be ignored.)\n") # TODO: don't write this warning at all if accum.amend_rules was set at the end of analyse() ?
                  else: sys.stderr.write("(This might indicate invalid markup in the corpus)\n")
                default_action = action
        if default_action or not byteSeq_to_action_dict[""]: ret.append((default_action+" return;").strip()) # (return only if there was a default action, OR if an empty "" was in the dict with NO conditional actions (e.g. from the common-case optimisation above).  Otherwise, if there were conditional actions but no default, we didn't "match" anything if none of the conditions were satisfied.)
    return ret # caller does '\n'.join

if compress:
  squashStrings = set() ; squashReplacements = []
  def squashFinish():
    assert main, "squashFinish sets globals"
    global squashStrings # so can set it to "done" at end
    tokens = set()
    for s in squashStrings: tokens.update(list(s))
    totSaved = 0
    tokens = [chr(t) for t in range(1,256) if not chr(t) in tokens] ; orig_tokens = set(tokens)
    pairs = [chr(0)] * 512
    while tokens:
      t = tokens.pop()
      counts = {}
      for s in squashStrings:
        # To make decompression as fast and compact as possible, each 1-byte token represents 2 bytes exactly.  In practice allowing it to represent variable lengths of whole bytes up to 4 is not likely to improve the compression by more than 3.2% (that's 3.2% of the 10-20% it achieves, so it's around 0.5%), and not very much better for length 9, so we might as well stick with this simpler scheme unless we do real LZMA or whatever.
          for i in range(0,len(s)-1):
            k = s[i:i+2]
            if k[0] in orig_tokens or k[1] in orig_tokens: continue # to keep the decoder simple, don't set things up so it needs to recurse (being able to recurse within the 2-byte expansion is very unlikely to save anything in practice anyway - it didn't on my annotators - so not worth implementing the decoder for)
            counts[k] = counts.get(k,0) + 1
      bSaved, k = max((v,k) for k,v in counts.items())
      pairs[ord(t)] = k[0]
      pairs[ord(t)+256] = k[1]
      squashReplacements.append((k,t)) # this assumes we won't be doing things like 'if ALL instances of a byte end up in our tokens, add the byte's original value as an extra token'
      for s in squashStrings:
        s2 = s.replace(k,t)
        if not s2==s:
          squashStrings.remove(s) ; squashStrings.add(s2)
      totSaved += bSaved
      sys.stderr.write("Compress: %d/%d tokens, %d bytes saved%s" % (len(orig_tokens)-len(tokens),len(orig_tokens),totSaved,clear_eol))
    squashStrings = "done"
    while len(pairs) > 256 and pairs[-1]==chr(0): pairs = pairs[:-1]
    sys.stderr.write("\n")
    if totSaved < len(pairs)+50: sys.stderr.write("Warning: --compress on this data made it bigger!  Consider dropping --compress\n") # 50 as rough guess for OutWriteDecompress binary (probably about 12 instructions at 4+ bytes each)
    return c_escapeRawBytes("".join(pairs))
  decompress_func=r"""

static unsigned char pairs[]="%%PAIRS%%";
static void OutWriteDecompress(const char *s) {
while(*s) {
  int i=(unsigned char)*s;
  if (pairs[i]) { OutWriteByte(pairs[i]); OutWriteByte(pairs[i|0x100]); } else OutWriteByte(*s);
  s++;
}
}"""
  if sharp_multi: decompress_func += r"""
static int ns; static void OutWriteNSB(int b) {
  if(b=='#') ns++; else if(ns==numSharps) OutWriteByte(b);
}
static void OutWriteDecompressP(const char *s) {
ns=0; while(*s && ns<=numSharps) {
  int i=(unsigned char)*s;
  if (pairs[i]) { OutWriteNSB(pairs[i]); OutWriteNSB(pairs[i|0x100]); } else OutWriteNSB(*s);
  s++;
}
}"""
  def squash(byteStr):
    if squashStrings == "done":
      for k,v in squashReplacements:
        byteStr = byteStr.replace(k,v)
    else: squashStrings.add(byteStr) # for the dry run
    return byteStr
elif sharp_multi: decompress_func = r"""
static void OutWriteStrP(const char *annot) {
    int ns = numSharps;
    while(ns--) {
        annot = strchr(annot,'#');
        if (!annot) return; else annot++;
    }
    char* m = strchr(annot,'#');
    if(m) OutWriteStrN(annot,m-annot); else OutWriteStr(annot);
}
"""
else: decompress_func = ""

if ios:
  c_preamble = r"""/*

To compile this, go into Xcode and do File > New > Project
and under iOS / Application choose Single View Application.
Fill in the dialogue box as you like, then use this file
to replace the generated ViewController.m file.  You should
then be able to press the Run button on the toolbar.
Tested on an iOS 6.1 simulator in Xcode 4.6 on Mac OS 10.7
(hopefully compatible with later versions too)

Swipe left to go back (as in Safari).
If your pages refer to clip://anything then that
link will show and annotate the local clipboard.
*/

#import <UIKit/UIKit.h>
#include <string.h>
"""
  c_defs = r"""static const char *readPtr, *writePtr, *startPtr;
static NSMutableData *outBytes;
#define NEXTBYTE (*readPtr++)
#define NEXT_COPY_BYTE (*writePtr++)
#define COPY_BYTE_SKIP writePtr++
#define COPY_BYTE_SKIPN(n) writePtr += (n)
#define POSTYPE const char*
#define THEPOS readPtr
#define SETPOS(p) (readPtr=(p))
#define PREVBYTE readPtr--
#define FINISHED (!(*readPtr))
#define OutWriteStrN(s,n) [outBytes appendBytes:(s) length:(n)]
static void OutWriteStr(const char *s) { OutWriteStrN(s,strlen(s)); }
static void OutWriteByte(char c) { [outBytes appendBytes:(&(c)) length:1]; }
static int near(char* string) {
    const char *startFrom = readPtr-nearbytes;
    size_t n=2*nearbytes;
    if (startFrom < startPtr) {
        n -= startPtr-startFrom;
        startFrom = startPtr; }
    return strnstr(startFrom,string,n) != NULL;
}
""" # (strnstr is BSD-specific, but that's OK on iOS.  TODO: might be nice if all loops over outWriteByte could be reduced to direct calls of appendBytes with appropriate lengths, but it wouldn't be a major speedup)
  c_switch1=c_switch2=c_switch3=c_switch4="" # only ruby is needed by the iOS code
elif ndk:
  c_preamble = r"""
#include <stdlib.h>
#include <string.h>
#include <jni.h>
"""
  c_defs = r"""static const char *readPtr, *writePtr, *startPtr;
static char *outBytes;
static size_t outWriteLen,outWritePtr;
#define NEXTBYTE (*readPtr++)
#define NEXT_COPY_BYTE (*writePtr++)
#define COPY_BYTE_SKIP writePtr++
#define COPY_BYTE_SKIPN(n) writePtr += (n)
#define POSTYPE const char*
#define THEPOS readPtr
#define SETPOS(p) (readPtr=(p))
#define PREVBYTE readPtr--
#define FINISHED (!(*readPtr))

static void OutWriteStrN(const char *s,size_t l) {
  size_t newLen = outWriteLen;
  while (outWritePtr+l > newLen) newLen *= 2;
  if (newLen > outWriteLen) {
    char *ob2 = realloc(outBytes,newLen);
    if (!ob2) return; /* This check is meaningless if the kernel overcommits, but I don't know if that's true on (all versions of) Android. */
    outBytes = ob2; outWriteLen = newLen;
  }
  memcpy(outBytes+outWritePtr, s, l);
  outWritePtr += l;
}
static void OutWriteStr(const char *s) {
  OutWriteStrN(s,strlen(s));
}
static void OutWriteByte(char c) {
  if (outWritePtr >= outWriteLen) {
    size_t newLen = outWriteLen * 2;
    char *ob2 = realloc(outBytes,newLen);
    if (!ob2) return; /* This check is meaningless if the kernel overcommits, but I don't know if that's true on (all versions of) Android. */
    outBytes = ob2; outWriteLen = newLen;
  }
  outBytes[outWritePtr++] = c;
}
int near(char* string) {
    const char *startFrom = readPtr-nearbytes,
                     *end = readPtr+nearbytes;
    if (startFrom < startPtr) startFrom = startPtr;
    size_t l=strlen(string); end -= l;
    while (*startFrom && startFrom <= end) {
      if(!strncmp(startFrom,string,l)) return 1;
      startFrom++;
    }
    return 0;
}
void matchAll();
JNIEXPORT jstring JNICALL Java_"""+jPackage.replace('.','_')+r"""_MainActivity_jniAnnotate(JNIEnv *env, jclass theClass, jstring jIn"""
  if sharp_multi: c_defs += ", jint jAnnotNo"
  c_defs += r""") {
  startPtr=(char*)(*env)->GetStringUTFChars(env,jIn,NULL);
  readPtr = startPtr; writePtr = startPtr;
  outWriteLen = strlen(startPtr)*5+1; /* initial guess (must include the +1 to ensure it's non-0 for OutWrite...'s *= code) */
  outBytes = malloc(outWriteLen);"""
  if sharp_multi: c_defs += " numSharps=jAnnotNo;"
  c_defs += r"""
  if(outBytes) { outWritePtr = 0; matchAll(); }
  (*env)->ReleaseStringUTFChars(env,jIn,startPtr);
  if(outBytes) OutWriteByte(0);
  else return (*env)->NewStringUTF(env,"out of memory"); /* which it might or might not be able to do.  This check is meaningless if the kernel overcommits, but I don't know if that's true on (all versions of) Android. */
  jstring ret=(*env)->NewStringUTF(env,outBytes);
  free(outBytes); return ret;
}
"""
  c_switch1=c_switch2=c_switch3=c_switch4="" # only ruby is needed by the Android code
elif windows_clipboard:
  c_preamble = r"""/*

For running on Windows desktop or WINE, compile with:

  i386-mingw32-gcc annoclip.c -o annoclip.exe

For running on Windows Mobile 2003SE, 5, 6, 6.1 or 6.5,
compile with:

  arm-cegcc-gcc annoclip.c -D_WINCE -Os -o annoclip-WM.exe

or (if you have MSVC 2008 on a Windows machine),

set PATH=%VCINSTALLDIR%\ce\bin\x86_arm;%PATH%
set lib=%VCINSTALLDIR%\ce\lib\armv4
set include=%VSINSTALLDIR%\SmartDevices\SDK\Smartphone2003\Include;%VCINSTALLDIR%\ce\include;%VCINSTALLDIR%\include
set CL=/TP /EHsc /D "_WIN32_WCE=0x420" /D UNDER_CE /D WIN32_PLATFORM_PSPC /D _WINCE /D _WINDOWS /D ARM /D _ARM_ /D _UNICODE /D UNICODE /D POCKETPC2003_UI_MODEL
set LINK=/force:multiple /NODEFAULTLIB:oldnames.lib /SUBSYSTEM:WINDOWSCE /LIBPATH:"C:\Program Files\Windows Mobile 5.0 SDK R2\PocketPC\Lib\ARMV4I" /OUT:annoclip-WM.exe /MANIFEST:NO /STACK:65536,4096 /DYNAMICBASE:NO aygshell.lib coredll.lib corelibc.lib ole32.lib oleaut32.lib uuid.lib commctrl.lib
cl /D_WIN32_IE=0x0400 /D_WIN32_WCE=0x0400 /Os /Og annoclip.c

(you could try omitting /Os /Og for faster compilation,
but RAM is likely important on the Windows Mobile device)

*/

#include <stdio.h>
#include <string.h>
#define UNICODE 1 /* for TCHAR to be defined correctly */
#include <windows.h>
#ifdef near
#undef near
#endif
FILE* outFile = NULL;
unsigned char *p, *copyP, *pOrig;
#define OutWriteStr(s) fputs((s),outFile)
#define OutWriteStrN(s,n) fwrite((s),(n),1,outFile)
#define OutWriteByte(c) fputc((c),outFile)
#define NEXTBYTE (*p++)
#define NEXT_COPY_BYTE (*copyP++)
#define COPY_BYTE_SKIP copyP++
#define COPY_BYTE_SKIPN(n) copyP += (n)
#define POSTYPE unsigned char*
#define THEPOS p
#define SETPOS(sp) (p=(sp))
#define PREVBYTE p--
#define FINISHED (!*p && !p[1])
"""
  if c_filename and os.sep in c_filename: cfn = c_filename[c_filename.rindex(os.sep)+1:]
  else: cfn = c_filename
  if cfn: c_preamble=c_preamble.replace("annoclip.c",cfn)
  c_defs = r"""static int near(char* string) {
  POSTYPE o=p; if(p>pOrig+nearbytes) o-=nearbytes; else o=pOrig;
  size_t l=strlen(string);
  POSTYPE max=p+nearbytes-l;
  while (*o && o <= max) {
    if(!strncmp((char*)o,(char*)string,l)) return 1;
    o++;
  }
  return 0;
}
"""
  c_switch1=c_switch2=c_switch3=c_switch4="" # only ruby is needed by the windows_clipboard code
else:
  c_preamble = r"""
#include <stdio.h>
#include <string.h>

/* To include this code in another program,
   define the ifndef'd macros below + define Omit_main */
"""
  c_defs = r"""#ifndef NEXTBYTE
/* Default definition of NEXTBYTE etc is to read input
   from stdin and write output to stdout.  */
enum { Half_Bufsize = %%LONGEST_RULE_LEN%% };
static unsigned char lookahead[Half_Bufsize*2];
static size_t readPtr=0,writePtr=0,bufStart=0,bufLen=0;
static int nextByte() {
  if (readPtr-bufStart +ybytes >= bufLen && !feof(stdin)) {
    if (bufLen == Half_Bufsize * 2) {
      memmove(lookahead,lookahead+Half_Bufsize,Half_Bufsize);
      bufStart += Half_Bufsize; bufLen -= Half_Bufsize;
    }
    bufLen += fread(lookahead+bufLen,1,Half_Bufsize*2-bufLen,stdin);
  }
  if (readPtr-bufStart == bufLen) return EOF;
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
  while (offset <= maxPos) {
    if(!strncmp((char*)lookahead+offset,string,l)) return 1;
    offset++;
  }
  return 0;
}
#define NEXTBYTE nextByte()
#define NEXT_COPY_BYTE lookahead[(writePtr++)-bufStart]
#define COPY_BYTE_SKIP writePtr++
#define COPY_BYTE_SKIPN(n) writePtr += (n)
#define POSTYPE size_t
#define THEPOS readPtr /* or get it via a function */
#define SETPOS(p) (readPtr=(p)) /* or set via a func */
#define PREVBYTE readPtr--
#define FINISHED (feof(stdin) && readPtr-bufStart == bufLen)
#define OutWriteStr(s) fputs((s),stdout)
#define OutWriteStrN(s,n) fwrite((s),(n),1,stdout)
#define OutWriteByte(c) putchar(c)
#endif

#ifndef Default_Annotation_Mode
#define Default_Annotation_Mode ruby_markup
#endif

enum {
  annotations_only,
  ruby_markup,
  brace_notation} annotation_mode = Default_Annotation_Mode;
"""
  c_switch1=r"""switch (annotation_mode) {
  case annotations_only: OutWriteDecompressP(annot); COPY_BYTE_SKIPN(numBytes); break;
  case ruby_markup:"""
  c_switch2=r"""break;
  case brace_notation:
    OutWriteByte('{');
    for(;numBytes;numBytes--)
      OutWriteByte(NEXT_COPY_BYTE);
    OutWriteByte('|'); OutWriteDecompressP(annot);
    OutWriteByte('}'); break;
  }"""
  c_switch3 = "if (annotation_mode == ruby_markup) {"
  c_switch4 = "} else o(numBytes,annot);"

if (data_driven or sharp_multi) and not ndk: c_preamble += '#include <stdlib.h>\n' # for malloc or atoi (ndk includes it anyway, above)
if sharp_multi: c_preamble += '#include <ctype.h>\n'
if zlib: c_preamble += '#include "zlib.h"\n'
if sharp_multi: c_preamble += "static int numSharps=0;\n"

version_stamp = time.strftime("generated %Y-%m-%d by ")+program_name[:program_name.index("(c)")].strip()

if ios: c_name = "Objective-C"
else: c_name = "C"
c_start = "/* -*- coding: "+outcode+" -*- */\n/* "+c_name+" code "+version_stamp+" */\n"
c_start += c_preamble+r"""
enum { ybytes = %%YBYTES%% }; /* for Yarowsky-like matching, minimum readahead */
static int nearbytes = ybytes;
#define setnear(n) (nearbytes = (n))
""" + c_defs + r"""static int needSpace=0;
static void s() {
  if (needSpace) OutWriteByte(' ');
  else needSpace=1; /* for after the word we're about to write (if no intervening bytes cause needSpace=0) */
}""" + decompress_func + r"""

static void o(int numBytes,const char *annot) {
  s();""" + c_switch1 + r"""
    OutWriteStr("<ruby><rb>");
    for(;numBytes;numBytes--)
      OutWriteByte(NEXT_COPY_BYTE);
    OutWriteStr("</rb><rt>"); OutWriteDecompressP(annot);
    OutWriteStr("</rt></ruby>"); """+c_switch2+r""" }
static void o2(int numBytes,const char *annot,const char *title) {"""+c_switch3+r"""
    s();
    OutWriteStr("<ruby title=\""); OutWriteDecompress(title);
    OutWriteStr("\"><rb>");
    for(;numBytes;numBytes--)
      OutWriteByte(NEXT_COPY_BYTE);
    OutWriteStr("</rb><rt>"); OutWriteDecompressP(annot);
    OutWriteStr("</rt></ruby>"); """+c_switch4+"}"

if not sharp_multi: c_start = c_start.replace("OutWriteDecompressP","OutWriteDecompress")
if not compress: c_start = c_start.replace("OutWriteDecompress","OutWriteStr") # and hence OutWriteDecompressP to OutWriteStrP

c_end = r"""
void matchAll() {"""
if zlib: c_end += "  if(!data) init();\n"
c_end += r"""  while(!FINISHED) {
    POSTYPE oldPos=THEPOS;
    topLevelMatch();
    if (oldPos==THEPOS) { needSpace=0; OutWriteByte(NEXTBYTE); COPY_BYTE_SKIP; }
  }
}"""

# jsAddRubyCss will be in a quoted string in ObjC / Java source, so all " and \ must be escaped:
jsAddRubyCss="all_frames_docs(function(d) { if(d.rubyScriptAdded==1 || !d.body) return; var e=d.createElement('span'); e.innerHTML='<style id=\\\"ssb_local_annotator_css\\\">ruby{display:inline-table !important;vertical-align:bottom !important;-webkit-border-vertical-spacing:1px !important;padding-top:0.5ex !important;}ruby *{display: inline !important;vertical-align:top !important;line-height:1.0 !important;text-indent:0 !important;text-align:center !important;white-space:nowrap !important;}rb{display:table-row-group !important;font-size:100% !important;}rt{display:table-header-group !important;font-size:100% !important;line-height:1.1 !important;font-family: Gandhari, DejaVu Sans, Lucida Sans Unicode, Times New Roman, serif !important; }"+extra_css.replace('\\',r'\\').replace('"',r'\"').replace("'",r"\\'")+"</style>'"
if bookmarks:
 def bookmarkJS():
  assert not '"' in android
  should_show_bookmarks = "(location.href=='"+android.replace("'",r"\\'")+"'&&!document.noBookmarks)" # noBookmarks is used for handling ACTION_SEND, since it has the same href (TODO @lower-priority: use different href instead?)
  are_there_bookmarks = "ssb_local_annotator.getBMs().replace(/,/g,'')"
  show_bookmarks_string = r"""'<div style=\"border: red solid; background: black; color: white;\">'+(function(){var c='<h3>Bookmarks you added</h3><ul>',a=ssb_local_annotator.getBMs().split(','),i;for(i=0;i<a.length;i++)if(a[i]){var s=a[i].indexOf(' ');var url=a[i].slice(0,s),title=a[i].slice(s+1).replace(/%2C/g,',');c+='<li>[<a style=\"color:#ff0000;text-decoration:none\" href=\"javascript:if(confirm(\\'Delete '+title.replace(/\\'/g,\"&apos;\").replace(/\"/g,\"&quot;\")+\"?')){ssb_local_annotator.deleteBM(ssb_local_annotator.getBMs().split(',')[\"+i+']);location.reload()}\">Delete</a>] <a style=\"color:#00ff00;text-decoration:none\" href=\"'+url+'\">'+title+'</a>'}return c+'</ul>'})()+'</div>'""" # TODO: use of confirm() will include the line "the page at file:// says", could do without that (but reimplementing will need complex callbacks rather than a simple 'if')
  show_bookmarks_string = are_there_bookmarks+"?("+show_bookmarks_string+"):''"
  should_suppress_toolset = "(location.href.slice(0,7)=='file://'||document.noBookmarks)"
  toolset_openTag = r"""'<span id=\"ssb_local_annotator_bookmarks\" style=\"border: red solid !important; background: black !important; color: white !important; display: block !important; position: fixed !important; font-size: 20px !important; right: 40%; bottom: 0px; z-index:2147483647; -moz-opacity: 1 !important; filter: none !important; opacity: 1 !important; visibility: visible !important; overflow: auto !important;\">'"""
  toolset_closeTag = "'</span>'"
  emoji_supported = "function(){var c=document.createElement('canvas');if(!c.getContext)return;c=c.getContext('2d');if(!c.fillText)return;c.textBaseline='top';c.font='32px Arial';c.fillText('\ud83d\udd16',0,0);return c.getImageData(16,16,1,1).data[0]})()" # these emoji are typically supported on Android 4.4 but not on Android 4.1
  bookmarkLink0 = "ssb_local_annotator.addBM((location.href+' '+document.title).replace(/,/g,'%2C'))"
  bookmarkLink = r'\"'+"javascript:"+bookmarkLink0+r'\"'
  copyLink = "'javascript:ssb_local_annotator.copy(location.href,true)'"
  closeLink = r'\"'+"javascript:var e=document.getElementById('ssb_local_annotator_bookmarks');e.parentNode.removeChild(e)"+r'\"'
  if bookmarks_developer: devModeStr = r"'+(ssb_local_annotator.isDevMode()?'onclick=\"if(((typeof ssb_local_annotator_dblTap==\\'undefined\\')?null:ssb_local_annotator_dblTap)==null) ssb_local_annotator_dblTap=setTimeout(function(){"+bookmarkLink0.replace("'",r"\\'")+r";ssb_local_annotator_dblTap=null},500); else { clearTimeout(ssb_local_annotator_dblTap);document.getElementById(\\'ssb_local_annotator_css\\').innerHTML+=\\'ruby:not([title]){border:thin blue solid}\\';ssb_local_annotator.alert(\\'\\',\\'Developer mode: words without glosses boxed in blue\\');ssb_local_annotator_dblTap=null}return false\" ':'')+'" # (ondblclick won't work on phones, so we have to do it ourselves)
  else: devModeStr = ""
  toolset_string = toolset_openTag + "+(function(bookmarkLink,copyLink,closeLink){return '<a "+devModeStr+r"""href=\"'+bookmarkLink+'\"'+(("""+emoji_supported+r"""?('>\ud83d\udd16</a> &nbsp; <a href=\"'+copyLink+'\">\ud83d\udccb</a> &nbsp; <a href=\"'+closeLink+'\">\u274c'):(' style=\"color: white !important\">Bookmark</a> <a href=\"'+copyLink+'\" style=\"color: white !important\">Copy</a> <a href=\"'+closeLink+'\" style=\"color: white !important\">X'))+'</a>'})("""+bookmarkLink+","+copyLink+","+closeLink+")+"+toolset_closeTag # if not emoji_supported, could delete the above right: 40%, change border to border-top, and use width: 100% !important; margin: 0pt !important; padding: 0pt !important; left: 0px; text-align: justify; then add a <span style="display: inline-block; width: 100%;"></span> so the links are evenly spaced.  BUT that increases the risk of overprinting a page's own controls that might be fixed somewhere near the bottom margin (there's currently no way to get ours back after closure, other than by navigating to another page)
  # TODO: (don't know how much more room there is on smaller devices, but) U+1F504 Reload (just do window.location.reload); U+27A1 U+FE0F Forward (can use history.go(1) but @android.webkit.JavascriptInterface public boolean canGoForward() { return browser.canGoForward(); } to set its visibility (by id ?)  or do a browser.evaluateJavascript after browser.goBack() UNLESS goBack is async (doc doesn't say))
  toolset_string = should_suppress_toolset+"?'':("+toolset_string+")"
  return should_show_bookmarks+"?("+show_bookmarks_string+"):("+toolset_string+")"
 jsAddRubyCss += "+("+bookmarkJS()+")"
jsAddRubyCss += ";d.body.insertBefore(e,d.body.firstChild); d.rubyScriptAdded=1 })"

def jsAnnot(alertStr,xtra1,xtra2,annotScan,case3):
  r = "var leaveTags=['SCRIPT', 'STYLE', 'TITLE', 'TEXTAREA', 'OPTION'];function annotPopAll(e) { function f(c) { var i=0,r='',cn=c.childNodes; for(;i < cn.length;i++) r+=(cn[i].firstChild?f(cn[i]):(cn[i].nodeValue?cn[i].nodeValue:'')); return r; } " + alertStr + " }; "+xtra1+" function all_frames_docs(c) { var f=function(w){if(w.frames && w.frames.length) { var i; for(i=0; i<w.frames.length; i++) f(w.frames[i]) } c(w.document) }; f(window) }; function tw0() { "+xtra2+"all_frames_docs(function(d){walk(d,d,false)}) }; function annotScan() {"+extra_js+annotScan+"}; function walk(n,document,inLink) { var c=n.firstChild; while(c) { var ps = c.previousSibling, cNext = c.nextSibling; function isTxt(n) {return n && n.nodeType==3 && n.nodeValue && !n.nodeValue.match(/^"+r"\\"+"s*$/)}; if (c.nodeType==1 && (c.nodeName=='WBR' || (c.nodeName=='SPAN' && c.childNodes.length<=1 && (!c.firstChild || (c.firstChild.nodeValue && c.firstChild.nodeValue.match(/^"+r"\\"+"s*$/))))) && isTxt(cNext) && isTxt(ps)) { n.removeChild(c); cNext.previousSibling.nodeValue += cNext.nodeValue; n.removeChild(cNext); cNext = ps } c=cNext; } c=n.firstChild; while(c) { var cNext = c.nextSibling; switch (c.nodeType) { case 1: if (leaveTags.indexOf(c.nodeName)==-1 && c.className!='_adjust0') walk(c,document,inLink||(c.nodeName=='A'&&!!c.href)); break; case 3: {var cnv=c.nodeValue.replace(/\u200b/g,'');"+case3+"} } c=cNext } }"
  assert not '"' in r.replace(r'\"',''), "Unescaped \" character in jsAnnot param"
  return r

if ios:
  c_end += r"""
@interface ViewController : UIViewController <UIWebViewDelegate>
@property (nonatomic,retain) UIWebView *myWebView;
@end
@implementation ViewController
- (void)viewDidLoad {
    [super viewDidLoad];
    self.myWebView = [[UIWebView alloc] initWithFrame:CGRectMake(10, 20, 300,500)];
    self.myWebView.backgroundColor = [UIColor whiteColor];
    self.myWebView.scalesPageToFit = YES;
    self.myWebView.autoresizingMask = (UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight);
    self.myWebView.delegate = self;
    [self.view addGestureRecognizer:[[UISwipeGestureRecognizer alloc] initWithTarget:self action:@selector(swipeBack:)]];
    [self.view addSubview:self.myWebView];
    [self loadInitialPage];
}
- (void)loadInitialPage {
"""
  ios=ios.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')
  if ios.startswith('<'): c_end += '[self.myWebView loadHTMLString:@"'+ios+'" baseURL:nil];'
  # TODO: 'file from local project' option?  for now, anything that doesn't start with < is taken as URL
  else:
    if not "://" in ios: errExit("--ios value doesn't look like an HTML fragment or a URL")
    c_end += '[self.myWebView loadRequest:[[NSURLRequest alloc] initWithURL:[[NSURL alloc] initWithString:@"'+ios+'"]]];'
  c_end += r"""
}
-(void)swipeBack:(UISwipeGestureRecognizer *)recognizer {
    if (recognizer.state == UIGestureRecognizerStateEnded) {
        if ([self.myWebView canGoBack]) [self.myWebView goBack];
        else [self loadInitialPage];
    }
}
- (void)webViewDidFinishLoad:(UIWebView *)webView
{
    [webView stringByEvaluatingJavaScriptFromString:@" """+jsAnnot(alertStr="window.alertTitle=f(e.firstChild)+' '+f(e.firstChild.nextSibling); window.alertMessage=e.title; window.location='alert:a'",xtra1="var texts,tLen,oldTexts,otPtr,replacements; ",xtra2="texts = new Array(); tLen=0; otPtr=0; ",annotScan="oldTexts = new Array(); replacements = new Array(); tw0(); window.location='scan:a'",case3=r"""var i=otPtr;while (i<oldTexts.length && oldTexts[i]!=cnv) i++;if(i<replacements.length) {var newNode=document.createElement('span');newNode.className='_adjust0';n.replaceChild(newNode, c);var r=replacements[i]; if(!inLink) r=r.replace(/<ruby title=/g,'<ruby onclick=\"annotPopAll(this)\" title=');newNode.innerHTML=r; otPtr=i;} else if (tLen < 1024) { texts[texts.length]=cnv;tLen += cnv.length;} else return""")+r"""annotScan()"];
}
- (BOOL)webView:(UIWebView*)webView shouldStartLoadWithRequest:(NSURLRequest*)request navigationType:(UIWebViewNavigationType)navigationType {
    NSURL *URL = [request URL];
    if ([[URL scheme] isEqualToString:@"alert"]) {
        [[[UIAlertView alloc] initWithTitle:[self.myWebView stringByEvaluatingJavaScriptFromString:@"window.alertTitle"] message:[self.myWebView stringByEvaluatingJavaScriptFromString:@"window.alertMessage"] delegate: self cancelButtonTitle: nil otherButtonTitles: @"OK",nil, nil] show];
        return NO;
    } else if ([[URL scheme] isEqualToString:@"clip"]) {
        [self.myWebView loadHTMLString:[@"<html><head><meta name=\"mobileoptimized\" content=\"0\"><meta name=\"viewport\" content=\"width=device-width\"></head><body>" stringByAppendingString:[UIPasteboard generalPasteboard].string] baseURL:nil]; // TODO: make the string HTML-safe and refresh it if clipboard changes, like the Android version does via JS
    } else if ([[URL scheme] isEqualToString:@"scan"]) {
        NSString *texts=[self.myWebView stringByEvaluatingJavaScriptFromString:@"texts.join('/@@---------@@/')"];
        startPtr = [texts UTF8String]; readPtr = startPtr; writePtr = startPtr;
        outBytes = [NSMutableData alloc]; matchAll(); OutWriteByte(0);
        if([texts length]>0) [self.myWebView stringByEvaluatingJavaScriptFromString:[@"replacements=\"" stringByAppendingString:[[[[[[NSString alloc] initWithUTF8String:[outBytes bytes]] stringByReplacingOccurrencesOfString:@"\\" withString:@"\\\\"] stringByReplacingOccurrencesOfString:@"\"" withString:@"\\\""] stringByReplacingOccurrencesOfString:@"\n" withString:@"\\n"] stringByAppendingString:@"\".split('/@@---------@@/');oldTexts=texts;"""+jsAddRubyCss+r""";tw0()"]]];
        [self.myWebView stringByEvaluatingJavaScriptFromString:@"if(typeof window.sizeChangedLoop=='undefined') window.sizeChangedLoop=0; var me=++window.sizeChangedLoop; var getLen = function(w) { var r=0; if(w.frames && w.frames.length) { var i; for(i=0; i<w.frames.length; i++) r+=getLen(w.frames[i]) } if(w.document && w.document.body && w.document.body.innerHTML) r+=w.document.body.innerHTML.length; return r }; var curLen=getLen(window), stFunc=function(){window.setTimeout(tFunc,1000)}, tFunc=function(){if(window.sizeChangedLoop==me){if(getLen(window)==curLen) stFunc(); else annotScan()}}; stFunc(); var m=window.MutationObserver||window.WebKitMutationObserver; if(m) new m(function(mut,obs){if(mut[0].type=="childList"){obs.disconnect();if(window.sizeChangedLoop==me)annotScan()}}).observe(document.body,{childList:true,subtree:true})"]; // HTMLSizeChanged(annotScan)
        return NO;
    }
    return YES;
}
@end
"""
elif windows_clipboard: c_end += r"""
#ifdef _WINCE
#define CMD_LINE_T LPWSTR
#else
#define CMD_LINE_T LPSTR
#endif

static void errorExit(char* text) {
  TCHAR msg[500];
  DWORD e = GetLastError();
  wsprintf(msg,TEXT("%s: %d"),text,e);
  MessageBox(NULL, msg, TEXT("Error"), 0);
  exit(1);
}

int APIENTRY WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, CMD_LINE_T cmdLinePSTR, int iCmdShow)
{
  TCHAR *className = TEXT("annogen");

  WNDCLASS wndclass;
  memset(&wndclass, 0, sizeof(wndclass));
  wndclass.hInstance = hInstance;
  wndclass.lpfnWndProc = DefWindowProc;
  wndclass.lpszClassName = className;
  if (!RegisterClass(&wndclass)) errorExit("RegisterClass");

#ifndef WS_OVERLAPPEDWINDOW
#define WS_OVERLAPPEDWINDOW (WS_OVERLAPPED     | \
                             WS_CAPTION        | \
                             WS_SYSMENU        | \
                             WS_THICKFRAME     | \
                             WS_MINIMIZEBOX    | \
                             WS_MAXIMIZEBOX)
#endif
  
  HWND win = CreateWindow(className,className, WS_OVERLAPPEDWINDOW,CW_USEDEFAULT, CW_USEDEFAULT,CW_USEDEFAULT,CW_USEDEFAULT, NULL,NULL,hInstance, NULL);
  if (!win) errorExit("CreateWindow");
  // ShowWindow(win, SW_SHOW); // not needed
  HANDLE hClipMemory;
  if (!OpenClipboard(win)) errorExit("OpenClipboard");
  hClipMemory = GetClipboardData(CF_UNICODETEXT);
  if(!hClipMemory) errorExit("GetClipboardData");
  TCHAR*u16 = (TCHAR*)GlobalLock(hClipMemory);
  int u8bytes=0; while(u16[u8bytes++]); u8bytes*=3;
  p=(POSTYPE)malloc(++u8bytes);
  pOrig=p;
  do {
    if(!(*u16&~0x7f)) *p++=*u16;
    else {
      if(!(*u16&~0x7ff)) {
        *p++=0xC0|((*u16)>>6);
      } else {
        *p++=0xE0|(((*u16)>>12)&15);
        *p++=0x80|(((*u16)>>6)&0x3F);
      }
      *p++=0x80|((*u16)&0x3F);
    }
  } while(*u16++);
  GlobalUnlock(hClipMemory);
  CloseClipboard();
  char fname[MAX_PATH];
  #ifndef _WINCE
  GetTempPathA(sizeof(fname) - 7, fname);
  strcat(fname,"c.html"); /* c for clipboard */
  outFile = fopen(fname,"w");
  #endif
  if (!outFile) {
    strcpy(fname,"\\c.html");
    outFile=fopen(fname,"w");
  }
  OutWriteStr("<html><head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"><meta name=\"mobileoptimized\" content=\"0\"><meta name=\"viewport\" content=\"width=device-width\"></head><body><style id=\"ruby\">ruby { display: inline-table; vertical-align: bottom; -webkit-border-vertical-spacing: 1px; padding-top: 0.5ex; } ruby * { display: inline; vertical-align: top; line-height:1.0; text-indent:0; text-align:center; white-space: nowrap; } rb { display: table-row-group; font-size: 100%; } rt { display: table-header-group; font-size: 100%; line-height: 1.1; }</style>\n<!--[if IE 6]><style>ruby, ruby *, ruby rb, ruby rt { display: inline !important; vertical-align: baseline !important; padding-top: 0pt !important; } ruby { border: thin grey solid; } </style><![endif]-->\n<!--[if !IE]>-->\n<style>rt { font-family: Gandhari, DejaVu Sans, Lucida Sans Unicode, Times New Roman, serif !important; }</style>\n<!--<![endif]-->\n");
  p=pOrig; copyP=p;
  matchAll();
  free(pOrig);
  OutWriteStr("<script><!--\nfunction treewalk(n) { var c=n.firstChild; while(c) { if (c.nodeType==1 && c.nodeName!=\"SCRIPT\" && c.nodeName!=\"TEXTAREA\" && !(c.nodeName==\"A\" && c.href)) { treewalk(c); if(c.nodeName==\"RUBY\" && c.title && !c.onclick) c.onclick=Function(\"alert(this.title)\") } c=c.nextSibling; } } function tw() { treewalk(document.body); window.setTimeout(tw,5000); } treewalk(document.body); window.setTimeout(tw,1500);\n//--></script></body></html>");
  fclose(outFile);
  TCHAR fn2[sizeof(fname)]; int i;
  for(i=0; fname[i]; i++) fn2[i]=fname[i]; fn2[i]=(TCHAR)0;
  SHELLEXECUTEINFO sei;
  memset(&sei, 0, sizeof(sei));
  sei.cbSize = sizeof(sei);
  sei.lpVerb = TEXT("open");
  sei.lpFile = fn2;
  sei.nShow = SW_SHOWNORMAL;
  if (!ShellExecuteEx(&sei)) errorExit("ShellExecuteEx");

  // TODO: sleep(); remove{fname); ?
  // (although it will probably be the same on each run)

  DestroyWindow(win); // TODO: needed?
}
"""
elif not ndk:
  c_end += r"""
#ifndef Omit_main
int main(int argc,char*argv[]) {
  int i=1;"""
  if sharp_multi: c_end += r"""
  if(i<argc && isdigit(*argv[i])) numSharps=atoi(argv[i++]);"""
  c_end += r"""
  for(; i<argc; i++) {
    if(!strcmp(argv[i],"--help")) {"""
  if sharp_multi: c_end += r"""
      puts("Params are [annotation number] [options]");"""
  c_end += r"""
      puts("--ruby   = output ruby markup (default)");
      puts("--raw    = output just the annotations without the base text");
      puts("--braces = output as {base-text|annotation}");
      return 0;
    } else if(!strcmp(argv[i],"--ruby")) {
      annotation_mode = ruby_markup;
    } else if(!strcmp(argv[i],"--raw")) {
      annotation_mode = annotations_only;
    } else if(!strcmp(argv[i],"--braces")) {
      annotation_mode = brace_notation;
    } else {
      fprintf(stderr,"Unknown argument '%s'\n(Text should be on standard input)\n",argv[i]); return 1;
    }
  }
  matchAll();
}
#endif
"""

# ANDROID: setDefaultTextEncodingName("utf-8") is included as it might be needed if you include file:///android_asset/ URLs in your app (files put into assets/) as well as remote URLs.  (If including ONLY file URLs then you don't need to set the INTERNET permission in Manifest, but then you might as well pre-annotate the files and use a straightforward static HTML app like http://people.ds.cam.ac.uk/ssb22/gradint/html2apk.html )
# Also we get shouldOverrideUrlLoading to return true for URLs that end with .apk .pdf .epub .mp3 etc so the phone's normal browser can handle those (search code below for ".apk" for the list) (TODO: API 1's shouldOverrideUrlLoading was deprecated in API 24; if they remove it, we may have to provide both to remain compatible?)
if ndk_pre_2016 or not ndk: android_minSdkVersion,armabi = "1","armeabi"
elif ndk_pre_2017: android_minSdkVersion,armabi = "9","armeabi" # Android 2.3
else: android_minSdkVersion,armabi = "14","armeabi-v7a" # Android 4.0
android_manifest = r"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="%%JPACKAGE%%" android:versionCode="1" android:versionName="1.0" >
<uses-permission android:name="android.permission.INTERNET" />
<uses-sdk android:minSdkVersion="""+'"'+android_minSdkVersion+r"""" android:targetSdkVersion="26" />
<supports-screens android:largeScreens="true" android:xlargeScreens="true" />
<application android:icon="@drawable/ic_launcher" android:label="@string/app_name" android:theme="@style/AppTheme" >
<service android:name=".BringToFront" android:exported="false"/>
<activity android:configChanges="orientation|screenSize|keyboardHidden" android:name="%%JPACKAGE%%.MainActivity" android:label="@string/app_name" android:launchMode="singleInstance" >
<intent-filter><action android:name="android.intent.action.MAIN" /><category android:name="android.intent.category.LAUNCHER" /></intent-filter>
<intent-filter><action android:name="android.intent.action.SEND" /><category android:name="android.intent.category.DEFAULT" /><data android:mimeType="text/plain" /></intent-filter>"""
android_layout = r"""<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" android:layout_height="fill_parent" android:layout_width="fill_parent" android:orientation="vertical">
  <WebView android:id="@+id/browser" android:layout_height="match_parent" android:layout_width="match_parent" />
</LinearLayout>
"""
android_src = r"""package %%JPACKAGE%%;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.KeyEvent;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.annotation.TargetApi;
import android.os.Build;
public class MainActivity extends Activity {"""
if ndk:
  android_src += r"""
    static { System.loadLibrary("Annotator"); }"""
  if sharp_multi: android_src += r"""
    static synchronized native String jniAnnotate(String in,int annotNo);"""
  else: android_src += r"""
    static synchronized native String jniAnnotate(String in);"""
else: android_src += "%%JPACKAGE%%.Annotator annotator;"
android_src += r"""
    @SuppressLint("SetJavaScriptEnabled")
    @TargetApi(19) // 19 for setWebContentsDebuggingEnabled; 7 for setAppCachePath; 3 for setBuiltInZoomControls (but only API 1 is required)
    @SuppressWarnings("deprecation") // for conditional SDK below
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // ---------------------------------------------
        // Delete the following line if you DON'T want full screen:
        requestWindowFeature(android.view.Window.FEATURE_NO_TITLE); getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN);
        // ---------------------------------------------
        setContentView(R.layout.activity_main);
        browser = (WebView)findViewById(R.id.browser);
        // ---------------------------------------------
        // Delete the following line if you DON'T want to be able to use chrome://inspect in desktop Chromium when connected via USB to Android 4.4+
        if(Integer.valueOf(Build.VERSION.SDK) >= 19) WebView.setWebContentsDebuggingEnabled(true);
        // ---------------------------------------------
        // Delete the following long line if you DON'T want to link pop-ups to Pleco (when installed):
        try { getApplicationContext().getPackageManager().getPackageInfo("com.pleco.chinesesystem", 0); gotPleco = true; } catch (android.content.pm.PackageManager.NameNotFoundException e) {}
        // Delete the following long line if you DON'T want to link pop-ups to Hanping (when installed) if not linking to Pleco (there's room for only one of the two in the AlertDialog)
        if(!gotPleco && Integer.valueOf(Build.VERSION.SDK) >= 11) for(int i=0; i<3; i++) try { hanpingPackage="com.embermitre.hanping.cantodict.app.pro com.embermitre.hanping.app.pro com.embermitre.hanping.app.lite".split(" ")[i]; hanpingVersion=getApplicationContext().getPackageManager().getPackageInfo(hanpingPackage, 0).versionCode; break; } catch (android.content.pm.PackageManager.NameNotFoundException e) {}
        // ---------------------------------------------
        if(Integer.valueOf(Build.VERSION.SDK) >= 7) { browser.getSettings().setAppCachePath(getApplicationContext().getCacheDir().getAbsolutePath()); browser.getSettings().setAppCacheMaxSize(10*1048576) /* if API==7 i.e. exactly Android 2.1 (deprecated in API 8) */ ; browser.getSettings().setAppCacheEnabled(true); } // not to be confused with the normal browser cache
        if(Integer.valueOf(Build.VERSION.SDK)<=19 && savedInstanceState==null) browser.clearCache(true); // (Android 4.4 has Chrome 33 which has Issue 333804 XMLHttpRequest not revalidating, which breaks some sites, so clear cache when we 'cold start' on 4.4 or below.  We're now clearing cache anyway in onDestroy on Android 5 or below due to Chromium bug 245549, but do it here as well in case onDestroy wasn't called last time e.g. swipe-closed in Activity Manager)
        browser.getSettings().setJavaScriptEnabled(true);
        browser.setWebChromeClient(new WebChromeClient());
        @TargetApi(1)
        class A {
            public A(MainActivity act) { this.act = act; }
            MainActivity act; String copiedText="";"""
if sharp_multi: android_src += r"""
            int annotNo = 0;
            @JavascriptInterface public void setAnnotNo(int no) { annotNo = no; }
            @JavascriptInterface public int getAnnotNo() { return annotNo; }"""
android_src += r"""
            @JavascriptInterface public String annotate(String t,boolean inLink) """
if data_driven: android_src += "throws java.util.zip.DataFormatException "
android_src += "{ String r="
if ndk and sharp_multi: android_src += 'jniAnnotate(t,annotNo)'
elif ndk: android_src += 'jniAnnotate(t)'
else: android_src += 'annotator.annotate(t)'
if sharp_multi and not ndk: android_src += r""";
                java.util.regex.Pattern p=java.util.regex.Pattern.compile("<rt>([^#]*)#(.*?)</rt>");
                java.util.regex.Matcher m = p.matcher(r);
                StringBuffer sb=new StringBuffer();
                while(m.find()) m.appendReplacement(sb, "<rt>"+m.group(annotNo+1)+"</rt>");
                m.appendTail(sb); r=sb.toString();"""
android_src += r"""; if(!inLink) r=r.replaceAll("<ruby","<ruby onclick=\"annotPopAll(this)\""); return r; } // now we have a Copy button, it's convenient to put this on ALL ruby elements, not just ones with title
            @JavascriptInterface public void alert(String t,String a) {
                class DialogTask implements Runnable {
                    String tt,aa;
                    DialogTask(String t,String a) { tt=t; aa=a; }
                    public void run() {
                        android.app.AlertDialog.Builder d = new android.app.AlertDialog.Builder(act);
                        if(tt.length()>0) d.setTitle(tt);
                        d.setMessage(aa);
                        d.setNegativeButton("Copy",new android.content.DialogInterface.OnClickListener() {
                                public void onClick(android.content.DialogInterface dialog,int id) { copy(tt+" "+aa,false); }
                        });
                        if(tt.length()==0) { /* Pleco or Hanping button not added if empty title i.e. error/info box */ }
                        else if(gotPleco) d.setNeutralButton("Pleco", new android.content.DialogInterface.OnClickListener() {
                            public void onClick(android.content.DialogInterface dialog,int id) {
                                Intent i = new Intent(Intent.ACTION_MAIN);
                                i.setComponent(new android.content.ComponentName("com.pleco.chinesesystem","com.pleco.chinesesystem.PlecoDroidMainActivity"));
                                i.addCategory(Intent.CATEGORY_LAUNCHER);
                                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                                i.putExtra("launch_section", "dictSearch");
                                i.putExtra("replacesearchtext", tt);
                                startActivity(i);
                            }
                        }); else if(hanpingVersion!=0) d.setNeutralButton("Hanping", new android.content.DialogInterface.OnClickListener() {
                            @TargetApi(11)
                            public void onClick(android.content.DialogInterface dialog,int id) {
                                Intent i = new Intent(Intent.ACTION_VIEW);
                                i.setData(new android.net.Uri.Builder().scheme(hanpingVersion<906030000?"dictroid":"hanping").appendEncodedPath((hanpingPackage.indexOf("canto")!=-1)?"yue":"cmn").appendEncodedPath("word").appendPath(tt.split(" ",2)[0]).build());
                                i.setPackage(hanpingPackage);
                                i.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK | Intent.FLAG_ACTIVITY_NEW_TASK);
                                startActivity(i);
                            }
                        });
                        d.setPositiveButton("OK", null); // or can just click outside the dialog to clear. (TODO: would be nice if it could pop up somewhere near the word that was touched)
                        d.create().show();
                    }
                }
                act.runOnUiThread(new DialogTask(t,a));
            }
            @JavascriptInterface public String getClip() {
                String r=readClipboard(); if(r.equals(copiedText)) return ""; else return r;
            }"""
if bookmarks_developer: android_src += r"""
            // isDevMode for --bookmarks-developer: (I shared this bit with StackOverflow by the way)
            @TargetApi(17)
            @JavascriptInterface public boolean isDevMode() {
                if(Integer.valueOf(Build.VERSION.SDK) == 16) {
                    return android.provider.Settings.Secure.getInt(getApplicationContext().getContentResolver(),
                            android.provider.Settings.Secure.DEVELOPMENT_SETTINGS_ENABLED , 0) != 0;
                } else if (Integer.valueOf(Build.VERSION.SDK) >= 17) {
                    return android.provider.Settings.Secure.getInt(getApplicationContext().getContentResolver(),
                            android.provider.Settings.Global.DEVELOPMENT_SETTINGS_ENABLED, 0) != 0;
                } else return false;
            }"""
android_src += r"""
            @JavascriptInterface public void bringToFront() {
                if(Integer.valueOf(Build.VERSION.SDK) >= Build.VERSION_CODES.CUPCAKE) {
                    startService(new Intent(MainActivity.this, BringToFront.class));
                    nextBackHides = true;
                }
            }
            @JavascriptInterface public String getSentText() { return sentText; }
            @JavascriptInterface public String getLanguage() { return java.util.Locale.getDefault().getLanguage(); } /* ssb_local_annotator.getLanguage() returns "en", "fr", "de", "es", "it", "ja", "ko" etc */
            @JavascriptInterface public void openPlayStore() {
                /* ssb_local_annotator.openPlayStore() opens the Google "Play Store" page
                   for the app (if you've deployed it there), for use in encouraging
                   users to update to a more recent annotator etc (please don't use it
                   to ask for ratings: that is very annoying).  Limited to only the
                   current app just in case a site being browsed tries to hijack it. */
                String id=getApplicationContext().getPackageName();
                Intent i=new Intent(Intent.ACTION_VIEW,android.net.Uri.parse("market://details?id="+id));
                for(android.content.pm.ResolveInfo playApp: getApplicationContext().getPackageManager().queryIntentActivities(i,0)) {
                    if (playApp.activityInfo.applicationInfo.packageName.equals("com.android.vending")) {
                        i.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
                        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        i.addFlags(Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
                        i.setComponent(new android.content.ComponentName(playApp.activityInfo.applicationInfo.packageName,playApp.activityInfo.name));
                        getApplicationContext().startActivity(i);
                        return;
                    }
                }
                getApplicationContext().startActivity(new Intent(Intent.ACTION_VIEW,android.net.Uri.parse("https://play.google.com/store/apps/details?id="+id))); // fallback
            }
            @JavascriptInterface @TargetApi(11) public void copy(String copiedText,boolean toast) {
                this.copiedText = copiedText;
                if(Integer.valueOf(Build.VERSION.SDK) < Build.VERSION_CODES.HONEYCOMB) // SDK_INT requires API 4 but this works on API 1
                    ((android.text.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).setText(copiedText);
                else ((android.content.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).setPrimaryClip(android.content.ClipData.newPlainText(copiedText,copiedText));
                if(toast) android.widget.Toast.makeText(act, "Copied \""+copiedText+"\"",android.widget.Toast.LENGTH_LONG).show();
            }"""
if bookmarks: android_src += r"""
            @SuppressLint("DefaultLocale")
            @JavascriptInterface public void addBM(String p) {
                android.content.SharedPreferences.Editor e;
                do {
                   android.content.SharedPreferences sp=getSharedPreferences("ssb_local_annotator",0);
                   String s=sp.getString("prefs", ",");
                   if((","+s).contains(","+p+",")) {
                       int count=1; String p2; while(true) {
                           p2=String.format("%s (%d)", p, ++count);
                           if(!(","+s).contains(","+p2+",")) break;
                       } p=p2;
                   }
                   s += p+",";
                e = sp.edit();
                e.putString("prefs",s);
                } while(!e.commit());
                android.widget.Toast.makeText(act, "Added bookmark", android.widget.Toast.LENGTH_LONG).show();
            }
            @JavascriptInterface public void deleteBM(String p) {
                android.content.SharedPreferences.Editor e; boolean done=false; String s,p2;"""+"".join(r"""
                try {
                    do {
                        android.content.SharedPreferences sp=createPackageContext("%s", 0).getSharedPreferences("ssb_local_annotator",0);
                        p2=","+sp.getString("prefs", ",");
                        s=p2.replaceFirst(java.util.regex.Pattern.quote(","+p+","), ",");
                        if(s.equals(p2)) break;
                        e = sp.edit(); done=true;
                        e.putString("prefs",s.substring(1));
                     } while(!e.commit());
                } catch(Exception x) {} if(done) return;""" % p for p in bookmarks.split(",") if not p==jPackage)+r"""
                do {
                   android.content.SharedPreferences sp=getSharedPreferences("ssb_local_annotator",0);
                   p2=","+sp.getString("prefs", ",");
                   s=p2.replaceFirst(java.util.regex.Pattern.quote(","+p+","), ",");
                   if(s.equals(p2)) break;
                e = sp.edit();
                e.putString("prefs",s.substring(1));
                } while(!e.commit());
            }
            @JavascriptInterface public String getBMs() {
                String s="";"""+"".join(r"""
                try { s = createPackageContext("%s", 0).getSharedPreferences("ssb_local_annotator",0).getString("prefs", "")+","+s; } catch(Exception e) {}""" % p for p in bookmarks.split(",") if not p==jPackage)+r"""
                return s+getSharedPreferences("ssb_local_annotator",0).getString("prefs", "");
            }""" # and even if not bookmarks:
android_src += "\n}\n"
if not ndk:
  if data_driven: android_src += "try { annotator=new %%JPACKAGE%%.Annotator(getApplicationContext()); } catch(Exception e) { android.widget.Toast.makeText(this, \"Cannot load annotator data!\", android.widget.Toast.LENGTH_LONG).show(); }" # TODO: should we keep one of these static and synchronized, in case some version of Android gives us multiple instances and we start taking up more RAM than necessary?
  else: android_src += "annotator=new %%JPACKAGE%%.Annotator();"
android_src += r"""
        browser.addJavascriptInterface(new A(this),"ssb_local_annotator"); // hope no conflict with web JS
        browser.setWebViewClient(new WebViewClient() {
                public boolean shouldOverrideUrlLoading(WebView view,String url) { if(url.endsWith(".apk") || url.endsWith(".pdf") || url.endsWith(".epub") || url.endsWith(".mp3") || url.endsWith(".zip")) { startActivity(new Intent(Intent.ACTION_VIEW,android.net.Uri.parse(url))); return true; } else return false; }
                public void onPageFinished(WebView view,String url) {
                    if(Integer.valueOf(Build.VERSION.SDK) < 19) // Pre-Android 4.4, so below runTimer() alternative won't work.  This version has to wait for the page to load entirely (including all images) before annotating.
                    browser.loadUrl("javascript:"+js_common+"function AnnotMonitor() { AnnotIfLenChanged();window.setTimeout(AnnotMonitor,1000)} AnnotMonitor()");
                    else browser.loadUrl("javascript:"+js_common+"AnnotIfLenChanged();var m=window.MutationObserver;if(m)new m(function(mut,obs){if(mut[0].type=='childList'){AnnotIfLenChanged()}}).observe(document.body,{childList:true,subtree:true})"); // (no point waiting the rest of the second for runTimer() to run, especially if this is the initial assets page; also Android 4.4+ has MutationObserver for even faster response to changes, so set that up as well) (and yes we do need to include js_common on this line because we don't know if runTimer has yet happened on this new page)
                } });
        if(Integer.valueOf(Build.VERSION.SDK) >= 3) {
            browser.getSettings().setBuiltInZoomControls(true);
        }
        int size=Math.round(16*getResources().getConfiguration().fontScale); // from device accessibility settings
        browser.getSettings().setDefaultFontSize(size);
        browser.getSettings().setDefaultFixedFontSize(size);
        browser.getSettings().setDefaultTextEncodingName("utf-8");
        runTimerLoop();
        if (savedInstanceState!=null) browser.restoreState(savedInstanceState); else
        if (!handleIntent(getIntent())) browser.loadUrl("%%ANDROID-URL%%");
    }
    @Override
    public void onNewIntent(Intent intent) {
        super.onNewIntent(intent); handleIntent(intent);
    }
    boolean handleIntent(Intent intent) {
        if (Intent.ACTION_SEND.equals(intent.getAction()) && "text/plain".equals(intent.getType())) {
            sentText = intent.getStringExtra(Intent.EXTRA_TEXT);
            if (sentText == null) return false;
            browser.loadUrl("javascript:document.close();document.noBookmarks=1;document.rubyScriptAdded=0;document.write('<html><head><meta name=\"mobileoptimized\" content=\"0\"><meta name=\"viewport\" content=\"width=device-width\"></head><body>'+ssb_local_annotator.getSentText().replace(/&/g,'&amp;').replace(/</g,'&lt;').replace('\\n','<br>')+'</body>')");
        }
        else if (Intent.ACTION_VIEW.equals(intent.getAction())) {
            browser.loadUrl("javascript:document.close();document.write('<html><head><meta name=\"mobileoptimized\" content=\"0\"><meta name=\"viewport\" content=\"width=device-width\"></head><body>Loading, please wait...</body>')");
            browser.loadUrl(intent.getData().toString());
        }
        else return false; return true;
    }
    String sentText = null;
    boolean gotPleco = false; int hanpingVersion = 0; String hanpingPackage = null;
    static final String js_common="""+'"'+jsAnnot(alertStr="ssb_local_annotator.alert(f(e.firstChild)+' '+f(e.firstChild.nextSibling),e.title||'')",xtra1="function AnnotIfLenChanged() { var getLen=function(w) { var r=0; if(w.frames && w.frames.length) { var i; for(i=0; i<w.frames.length; i++) r+=getLen(w.frames[i]) } if(w.document && w.document.body && w.document.body.innerHTML) r+=w.document.body.innerHTML.length; return r },curLen=getLen(window); if(curLen!=window.curLen) { annotScan(); window.curLen=getLen(window) } };",xtra2="",annotScan=jsAddRubyCss+";tw0()",case3="var nv=ssb_local_annotator.annotate(cnv,inLink); if(nv!=cnv) { var newNode=document.createElement('span'); newNode.className='_adjust0'; n.replaceChild(newNode, c); newNode.innerHTML=nv }")+r"""";
    android.os.Handler theTimer;
    @SuppressWarnings("deprecation")
    @TargetApi(19)
    void runTimerLoop() {
        if(Integer.valueOf(Build.VERSION.SDK) >= 19) { // on Android 4.4+ we can do evaluateJavascript while page is still loading (useful for slow-network days) - but setTimeout won't usually work so we need an Android OS timer
           theTimer = new android.os.Handler();
            theTimer.postDelayed(new Runnable() {
                @Override
                public void run() {
                    browser.evaluateJavascript(js_common+"AnnotIfLenChanged()",null);
                    theTimer.postDelayed(this,1000);
                }
            },0);
        }
    }
    boolean nextBackHides = false;
    @Override public void onPause() { super.onPause(); nextBackHides = false; } // but may still be visible on Android 7+, so don't pause the browser yet
    @Override public void onStop() { super.onStop(); if(browser!=null && Integer.valueOf(Build.VERSION.SDK) >= 11) browser.onPause(); } // NOW pause the browser (screen off or app not visible)
    @Override public void onStart() { super.onStart(); if(browser!=null && Integer.valueOf(Build.VERSION.SDK) >= 11) browser.onResume(); }
    @Override public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            if (nextBackHides) { nextBackHides = false; if(moveTaskToBack(true)) return true; }
            if (browser.canGoBack()) { browser.goBack(); return true; }
        } return super.onKeyDown(keyCode, event);
    }
    @SuppressWarnings("deprecation") // using getText so works on API 1 (TODO consider adding a version check and the more-modern alternative android.content.ClipData c=((android.content.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).getPrimaryClip(); if (c != null && c.getItemCount()>0) return c.getItemAt(0).coerceToText(this).toString(); return ""; )
    @TargetApi(11)
    public String readClipboard() {
        if(Integer.valueOf(Build.VERSION.SDK) < Build.VERSION_CODES.HONEYCOMB) // SDK_INT requires API 4 but this works on API 1
            return ((android.text.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).getText().toString();
        android.content.ClipData c=((android.content.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).getPrimaryClip();
        if (c != null && c.getItemCount()>0) {
            return c.getItemAt(0).coerceToText(this).toString();
        }
        return "";
    }
    @Override protected void onSaveInstanceState(Bundle outState) { browser.saveState(outState); }
    @Override protected void onDestroy() { if(isFinishing() && Integer.valueOf(Build.VERSION.SDK)<23 && browser!=null) browser.clearCache(true); super.onDestroy(); } // (Chromium bug 245549 needed this workaround to stop taking up too much 'data' (not counted as cache) on old phones; it MIGHT be OK in API 22, or even API 20 with updates, but let's set the threshold at 23 just to be sure.  This works only if the user exits via Back button, not via swipe in Activity Manager: no way to catch that.)
    WebView browser;
}
"""
android_bringToFront=r"""package %%JPACKAGE%%;
import android.annotation.TargetApi;
import android.content.Intent;
import android.os.Build;
@TargetApi(Build.VERSION_CODES.CUPCAKE)
public class BringToFront extends android.app.IntentService {
    public BringToFront() { super(""); }
    public BringToFront(String name) { super(name); }
    @Override
    protected void onHandleIntent(Intent workIntent) {
        Intent i = getPackageManager().getLaunchIntentForPackage(getApplicationContext().getPackageName());
        i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(i);
    }
}
"""
android_clipboard = r"""<html><head><meta name="mobileoptimized" content="0"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head><body>
<script>window.onerror=function(msg,url,line){ssb_local_annotator.alert('',''+msg+' line '+line); return true}</script>
    <h3>Clipboard</h3>
    <div id="clip">waiting for clipboard contents</div>
    <script>
var curClip="";
function update() {
var newClip = ssb_local_annotator.getClip();
if (newClip && newClip != curClip) {
  document.getElementById('clip').innerHTML = newClip.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\u200b/g,'');
  curClip = newClip; if(ssb_local_annotator.annotate(newClip,false)!=newClip) ssb_local_annotator.bringToFront();
} window.setTimeout(update,1000) } update(); </script>
</body></html>"""
java_src = r"""package %%JPACKAGE%%;
public class Annotator {
public Annotator() { %%JDATA%% }
int nearbytes;
byte[] inBytes;
public int inPtr,writePtr; boolean needSpace;
java.io.ByteArrayOutputStream outBuf;
public void sn(int n) { nearbytes = n; }
static final byte EOF = (byte)0; // TODO: a bit hacky
public byte nB() {
  if (inPtr==inBytes.length) return EOF;
  return inBytes[inPtr++];
}
public boolean n(String s) {
  // for Yarowsky-like matching (use Strings rather than byte arrays or Java compiler can get overloaded)
  return n(s2b(s));
}
public boolean n(byte[] bytes) {
  int offset=inPtr, maxPos=inPtr+nearbytes;
  if (maxPos > inBytes.length) maxPos = inBytes.length;
  maxPos -= bytes.length;
  if(offset>nearbytes) offset-=nearbytes; else offset = 0;
  while(offset <= maxPos) {
    boolean ok=true;
    for(int i=0; i<bytes.length; i++) {
      if(bytes[i]!=inBytes[offset+i]) { ok=false; break; }
    }
    if(ok) return true;
    offset++;
  }
  return false;
}
public void o(byte c) { outBuf.write(c); }
public void o(byte[] a) { outBuf.write(a,0,a.length); }
public void o(String s) { o(s2b(s)); }
public void s() {
  if (needSpace) o((byte)' ');
  else needSpace=true;
}
public void o(int numBytes,String annot) {
  s();
  o("<ruby><rb>");
  for(;numBytes>0;numBytes--)
    o(inBytes[writePtr++]);
  o("</rb><rt>"); o(annot);
  o("</rt></ruby>");
}
public void o2(int numBytes,String annot,String title) {
  s();
  o("<ruby title=\""); o(title);
  o("\"><rb>");
  for(;numBytes>0;numBytes--)
    o(inBytes[writePtr++]);
  o("</rb><rt>"); o(annot);
  o("</rt></ruby>");
}
byte[] s2b(String s) {
  // Convert string to bytes - version that works before Android API level 9 i.e. in Java 5 not 6.  (Some versions of Android Lint sometimes miss the fact that s.getBytes(UTF8) where UTF8==java.nio.charset.Charset.forName("UTF-8") won't always work.)  We could do an API9+ version and use @android.annotation.TargetApi(9) around the class (android.os.Build.VERSION.SDK_INT won't work on API less than 4 but Integer.valueOf(android.os.Build.VERSION.SDK) works), but anyway we'd rather not have to generate a special Android-specific version of Annotator as well as putting Android stuff in a separate class.)
  try { return s.getBytes("UTF-8"); }
  catch(java.io.UnsupportedEncodingException e) {
    // should never happen for UTF-8
    return null;
  }
}"""
if data_driven: java_src += r"""
    byte[] data; int addrLen, dPtr;
    int readAddr() {
        int i,addr=0;
        for (i=addrLen; i!=0; i--) addr=(addr << 8) | (int)(data[dPtr++]&0xFF); // &0xFF converts to unsigned
        return addr;
    }
    byte[] readRefStr() {
        int a = readAddr(); int l = data[a] & 0xFF;
        if (l != 0) return java.util.Arrays.copyOfRange(data, a+1, a+l+1);
        else {
            int m = a+1; while(data[m]!=0) m++;
            return java.util.Arrays.copyOfRange(data,a+1,m);
        }
    }
    int switchByte_inner(int nBytes) {
        if (inPtr < inBytes.length) {
            byte b=nB();
            int dP=dPtr, end = dPtr+nBytes;
            while(dP < end) {
                if(b==data[dP]) return dP-dPtr;
                dP++;
            }
        }
        return nBytes;
    }
    void readData() throws java.util.zip.DataFormatException{
        java.util.LinkedList<Integer> sPos=new java.util.LinkedList<Integer>();
        int c;
        while(true) {
            c = data[dPtr++] & 0xFF;
            if ((c & 0x80)!=0) dPtr += (c&0x7F);
            else if (c < 20) {
                int i = switchByte_inner(++c);
                if(i!=0) dPtr += (int)(data[dPtr+c+i-1]&0xFF);
                dPtr += c+c;
            } else switch(c) {
                case 50: dPtr = readAddr(); break;
                case 51: {
                    int f = readAddr(), dO=dPtr;
                    dPtr = f; readData() ; dPtr = dO;
                    break; }
                case 52: return;
                case 60: {
                    int nBytes = (int)(data[dPtr++]&0xFF) + 1;
                    int i = switchByte_inner(nBytes);
                    dPtr += (nBytes + i * addrLen);
                    dPtr = readAddr(); break; }
                case 71: case 74: {
                    int numBytes = data[dPtr++] & 0xFF;
                    while((numBytes--)!=0) o(inBytes[writePtr++]);
                    if(c==74) return; else break; }
                case 72: case 75: {
                    int numBytes = data[dPtr++] & 0xFF;
                    byte[] annot = readRefStr();
                    s();
                    o("<ruby><rb>");
                    while((numBytes--)!=0) o(inBytes[writePtr++]);
                    o("</rb><rt>"); o(annot);
                    o("</rt></ruby>");
                    if(c==75) return; else break; }
                case 73: case 76: {
                    int numBytes = data[dPtr++] & 0xFF;
                    byte[] annot = readRefStr();
                    byte[] title = readRefStr();
                    s();
                    o("<ruby title=\""); o(title);
                    o("\"><rb>");
                    while((numBytes--)!=0) o(inBytes[writePtr++]);
                    o("</rb><rt>"); o(annot);
                    o("</rt></ruby>");
                    if(c==76) return; else break; }
                case 80: sPos.addFirst(inPtr); break;
                case 81: inPtr=sPos.removeFirst(); break;
                case 90: {
                    int tPtr = readAddr();
                    int fPtr = readAddr();
                    sn(data[dPtr++] & 0xFF);
                    boolean found = false;
                    while (dPtr < tPtr && dPtr < fPtr) if (n(readRefStr())) { found = true; break; }
                    dPtr = found ? tPtr : fPtr; break; }
                default: throw new java.util.zip.DataFormatException("corrupt data table");
                }
        }
    }
"""
java_src += r"""
public String annotate(String txt) {
  nearbytes=%%YBYTES%%;inBytes=s2b(txt);writePtr=0;needSpace=false;outBuf=new java.io.ByteArrayOutputStream();inPtr=0;
  while(inPtr < inBytes.length) {
    int oldPos=inPtr; """
if data_driven: java_src = java_src.replace("annotate(String txt)","annotate(String txt) throws java.util.zip.DataFormatException")+"dPtr=1; readData();"
else: java_src += "%%JPACKAGE%%.topLevelMatch.f(this);"
java_src += r"""
    if (oldPos==inPtr) { needSpace=false; o(nB()); writePtr++; }
  }
  String ret=null; try { ret=new String(outBuf.toByteArray(), "UTF-8"); } catch(java.io.UnsupportedEncodingException e) {}
  inBytes=null; outBuf=null; return ret;
}
}
"""
android_loadData = r"""data=new byte[%%DLEN%%];
context.getAssets().open("annotate.dat").read(data);"""
if zlib: android_loadData += r"""
java.util.zip.Inflater i=new java.util.zip.Inflater();
i.setInput(data);
byte[] decompressed=new byte[%%ULEN%%];
i.inflate(decompressed); i.end(); data = decompressed;
"""
android_loadData += "addrLen = data[0] & 0xFF;"

if os.environ.get("ANNOGEN_CSHARP_NO_MAIN",""):
  cSharp_mainNote = ""
else: cSharp_mainNote = r"""
// or just use the Main() at end (compile with csc, and
// see --help for usage)
//   (to omit this Main() from the generated file, set
//    the environment variable ANNOGEN_CSHARP_NO_MAIN before
//    running Annotator Generator)"""

cSharp_start = "// C# code "+version_stamp+r"""
// use: new Annotator(txt).result()
// (can also set annotation_mode on the Annotator)"""+cSharp_mainNote+r"""

enum Annotation_Mode { ruby_markup, annotations_only, brace_notation };

class Annotator {
public const string version="""+'"'+version_stamp+r"""";
public Annotator(string txt) { nearbytes=%%YBYTES%%; inBytes=System.Text.Encoding.UTF8.GetBytes(txt); inPtr=0; writePtr=0; needSpace=false; outBuf=new System.IO.MemoryStream(); annotation_mode = Annotation_Mode.ruby_markup; }
int nearbytes;
public Annotation_Mode annotation_mode;
byte[] inBytes;
int inPtr,writePtr; bool needSpace;
System.IO.MemoryStream outBuf;
const byte EOF = (byte)0; // TODO: a bit hacky
byte nB() {
  if (inPtr==inBytes.Length) return EOF;
  return inBytes[inPtr++];
}
bool near(string s) {
  byte[] bytes=System.Text.Encoding.UTF8.GetBytes(s);
  int offset=inPtr, maxPos=inPtr+nearbytes;
  if (maxPos > inBytes.Length) maxPos = inBytes.Length;
  maxPos -= bytes.Length;
  if(offset>nearbytes) offset-=nearbytes; else offset = 0;
  while(offset <= maxPos) {
    bool ok=true;
    for(int i=0; i<bytes.Length; i++) {
      if(bytes[i]!=inBytes[offset+i]) { ok=false; break; }
    }
    if(ok) return true;
    offset++;
  }
  return false;
}
void o(byte c) { outBuf.WriteByte(c); }
void o(string s) { byte[] b=System.Text.Encoding.UTF8.GetBytes(s); outBuf.Write(b,0,b.Length); }
void s() {
  if (needSpace) o((byte)' ');
  else needSpace=true;
}
void o(int numBytes,string annot) {
  s();
  switch (annotation_mode) {
  case Annotation_Mode.annotations_only:
    o(annot); break;
  case Annotation_Mode.ruby_markup:
    o("<ruby><rb>");
    outBuf.Write(inBytes,writePtr,numBytes);
    o("</rb><rt>"); o(annot);
    o("</rt></ruby>"); break;
  case Annotation_Mode.brace_notation:
    o("{");
    outBuf.Write(inBytes,writePtr,numBytes);
    o("|"); o(annot);
    o("}"); break;
  }
  writePtr += numBytes;
}
void o2(int numBytes,string annot,string title) {
  if (annotation_mode == Annotation_Mode.ruby_markup) {
    s();
    o("<ruby title=\""); o(title);
    o("\"><rb>");
    outBuf.Write(inBytes,writePtr,numBytes);
    writePtr += numBytes;
    o("</rb><rt>"); o(annot);
    o("</rt></ruby>");
  } else o(numBytes,annot);
}
public string result() {
  while(inPtr < inBytes.Length) {
    int oldPos=inPtr;
    topLevelMatch();
    if (oldPos==inPtr) { needSpace=false; o(nB()); writePtr++; }
  }
  return System.Text.Encoding.UTF8.GetString(outBuf.ToArray());
}
"""
cSharp_end = "}\n"
if cSharp_mainNote: cSharp_end += r"""
class Test {
  static void Main(string[] args) {
    Annotation_Mode annotation_mode = Annotation_Mode.ruby_markup;
    for(int i=0; i<args.Length; i++) {
      if (args[i]=="--help") {
        System.Console.WriteLine("Use --ruby to output ruby markup (default)");
        System.Console.WriteLine("Use --raw to output just the annotations without the base text");
        System.Console.WriteLine("Use --braces to output as {base-text|annotation}");
        return;
      } else if(args[i]=="--ruby") {
        annotation_mode = Annotation_Mode.ruby_markup;
      } else if(args[i]=="--raw") {
        annotation_mode = Annotation_Mode.annotations_only;
      } else if(args[i]=="--braces") {
        annotation_mode = Annotation_Mode.brace_notation;
      }
    }
    System.Console.InputEncoding=System.Text.Encoding.UTF8;
    System.Console.OutputEncoding=System.Text.Encoding.UTF8;
    Annotator a=new Annotator(System.Console.In.ReadToEnd());
    a.annotation_mode = annotation_mode;
    System.Console.Write(a.result());
  }
}
"""

golang_start = '/* "Go" code '+version_stamp+r"""

To set up a Web service on GAE, put this file in a
subdirectory of your project, and create a top-level .go
file with something like:

package server
import (
  "net/http"
  "%%PKG%%"
)
func init() {
    http.HandleFunc("/", %%PKG%%_handler)
    // add other handlers as appropriate
}
func %%PKG%%_handler(w http.ResponseWriter, r *http.Request) {
    %%PKG%%.Annotate(r.Body,w)
}

Then in app.yaml:
application: whatever
version: 1
runtime: go
api_version: go1
handlers:
- url: /.*
  script: _go_app

Then test with: goapp serve
(and POST to localhost:8080, e.g. via Web Adjuster --htmlFilter="http://localhost:8080")

(To deploy with Web Adjuster also on GAE, you'll need 2 different GAE instances, because
although you could add Web Adjuster on the SAME one - put adjuster's app.yaml into a
python-api.yaml with "module: pythonapi" - there will be the issue of how to set the
URL handlers while making sure that Golang's has priority if it's an exception to .*
- unless you want to port the whole of Web Adjuster to Golang and integrate it into your
annotator that way.)

 */

package %%PKG%%

import (
  "sync"
  "bytes"
  "io"
)
// We have a Mutex for thread safety.  TODO: option to put
// the global variables into a per-instance struct instead
var mutex sync.Mutex

var inBytes []byte = nil
var outBuf bytes.Buffer
var inPtr int
var writePtr int
var needSpace bool
var nearbytes int = 15

func nB() byte {
   if (inPtr == len(inBytes)) {
      return 0
   }
   tmp := inBytes[inPtr]
   inPtr++
   return tmp
}

func near(s0 string) bool {
   s := make([]byte, len(s0))
   copy (s,s0)
   offset := inPtr
   maxPos := inPtr + nearbytes
   if maxPos > len(inBytes) {
      maxPos = len(inBytes)
   }
   maxPos -= len(s)
   if (offset > nearbytes) {
      offset -= nearbytes
   } else {
      offset = 0
   }
   for(offset <= maxPos) {
      ok := true ; i := 0
      for (i < len(s)) {
         if s[i] != inBytes[offset+i] {
            ok = false ; break
         }
         i++
      }
      if (ok) {
         return true
      }
      offset++
   }
   return false
}

func oB(c byte) {
   outBuf.WriteByte(c)
}
func oS(s string) {
   outBuf.WriteString(s)
}
func s() {
   if(needSpace) {
      oB(' ')
   } else {
      needSpace = true
   }
}
func o(numBytes int,annot string) {
  s()
  oS("<ruby><rb>")
  for (numBytes > 0) {
    // TODO: does Go have a way to do this in 1 operation?
    oB(inBytes[writePtr])
    numBytes--
    writePtr++
  }
  oS("</rb><rt>")
  oS(annot)
  oS("</rt></ruby>")
}
func o2(numBytes int,annot string,title string) {
  s()
  oS("<ruby title=\"")
  oS(title)
  oS("\"><rb>")
  for (numBytes > 0) {
    // TODO: as above
    oB(inBytes[writePtr])
    numBytes--
    writePtr++
  }
  oS("</rb><rt>")
  oS(annot)
  oS("</rt></ruby>")
}
""".replace("%%PKG%%",golang)
golang_end=r"""
func Annotate(src io.Reader, dest io.Writer) {
   inBuf := new(bytes.Buffer)
   io.Copy(inBuf, src)
   mutex.Lock()
   inBytes = inBuf.Bytes()
   inBuf.Reset() ; outBuf.Reset()
   needSpace = false
   inPtr = 0 ; writePtr = 0
   for(inPtr < len(inBytes)) {
      oldPos := inPtr
      topLevelMatch()
      if oldPos==inPtr {
         needSpace = false
         oB(nB())
         writePtr++
      }
   }
   // outBuf.WriteTo(dest) // may hold up if still locked, try this instead:
   outBytes := outBuf.Bytes()
   mutex.Unlock()
   dest.Write(outBytes)
}
"""

if js_6bit: js_6bit_offset = 35 # any offset between 32 and 63 makes all printable, but 35+ avoids escaping of " at 34 (can't avoid escaping of \ though, unless have a more complex decoder), and low offsets increase the range of compact-switchbyte addressing also.
else: js_6bit_offset = 0

class BytecodeAssembler:
  # Bytecode for a virtual machine run by the Javascript version etc
  opcodes = {
    # 0-19    RESERVED for short switchbyte (C,Java,Py)
    # 108-127 RESERVED for short switchbyte (JS, more in the printable range to reduce escaping a bit)
    # 91-107 RESERVED for short switchbyte (JS, UTF-8 printability optimisation for 6bit)
    # 128-255 RESERVED for short jumps
    'jump': 50, # '2' params: address
    'call': 51, # '3' params: function address
    'return': 52, # '4' (or 'end program' if top level)
    'switchbyte': 60, # '<' switch(NEXTBYTE) (params: numBytes-1, bytes (sorted, TODO take advantage of this), addresses, default address)
    'copyBytes':71,'o':72,'o2':73, # 'G','H','I' (don't change these numbers, they're hard-coded below)
    # 74-76 ('J','K','L') reserved for 'above + return'
    'savepos':80, # 'P', local to the function
    'restorepos':81, # 'Q'
    'neartest':90, # 'Z' params: true-label, false-label, byte nbytes, addresses of conds strings until first of the 2 labels is reached (normally true-label, unless the whole neartest is negated)
  }
  def __init__(self):
    self.l = []
    self.d2l = {}
    self.lastLabelNo = 0
    self.addingPosStack = []
  def addOpcode(self,opcode): self.l.append((opcode,))
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
    # assert type(actionList) in [list,tuple], repr(actionList)
    for a in actionList:
      assert 1 <= len(a) <= 3 and type(a[0])==int, repr(a)
      assert 1 <= a[0] <= 255, "bytecode currently supports markup or copy between 1 and 255 bytes only, not %d (but 0 is reserved for expansion)" % a[0]
      self.addBytes(70+len(a)) # 71=copyBytes 72=o() 73=o2
      if js_6bit:
        self.addBytes((a[0]+(js_6bit_offset-1))&0xFF)
      else: self.addBytes(a[0])
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
        self.addActionDictSwitch(byteSeq_to_action_dict) # as a subfunction (ends up adding the call to it, which should be replaced by a jump during compaction; TODO: auto-inline if it turns out there's only this one call to it?  other calls might happen if it's merged with an identical one)
        byteSeq_to_action_dict[""] = [("",[])] # for the end of this func
        self.addOpcode('return')
    elif allBytes:
      allBytes = sorted(list(allBytes))
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
                if type(conds)==tuple: negate,conds,nbytes = conds
                else: negate,nbytes = False,ybytes_max
                assert 1 <= nbytes <= 255, "bytecode supports only single-byte nbytes (but nbytes=0 is reserved for expansion)"
                trueLabel,falseLabel = self.makeLabel(),self.makeLabel()
                self.addOpcode('neartest')
                self.addRef(trueLabel)
                self.addRef(falseLabel)
                assert type(nbytes)==int
                self.addBytes(nbytes)
                for c in conds: self.addRefToString(c.encode(outcode)) # TODO: how much bytecode could we save by globally merging equivalent lists of string-list references ?  (zlib helps anyway but...)
                if negate: trueLabel,falseLabel = falseLabel,trueLabel
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
    assert type(string)==str
    if python or java or javascript:
      # prepends with a length hint if possible (or if not
      # prepends with 0 and null-terminates it)
      if js_6bit and not js_utf8: string = re.sub("%(?=[0-9A-Fa-f])|[\x7f-\xff]",lambda m:urllib.quote(m.group()),string) # for JS 'unescape'
      elif js_utf8: string = unicode(string,'utf-8')
      if js_6bit:
        if 1 <= len(string) <= 91:
          string = chr(len(string)+31)+string # 32-122 inc
        else:
          for termChar in '{|}~\x00': # 123-126 + nul
            if not termChar in string:
              string = termChar + string + termChar
              break
      elif 1 <= len(string) < 256:
        string = chr(len(string))+string
      else: string = chr(0)+string+chr(0)
    else: string += chr(0) # just null-termination for C
    if not string in self.d2l:
      self.d2l[string] = (-len(self.d2l)-1,)
    self.l.append(self.d2l[string])
  def link(self): # returns resulting bytes
    # (add an 'end program' instruction before calling)
    def f(*args): raise Exception("Must call link() only once")
    self.link = f
    sys.stderr.write("Linking... ")
    for dat,ref in sorted(self.d2l.iteritems()): # the functions and data to add to the end of self.l, sorted so we can optimise for overlaps
        assert type(ref)==tuple and type(ref[0])==int
        self.l.append((-ref[0],)) # the label
        if type(dat) in [str,unicode]:
            if type(self.l[-2])==type(dat) and self.l[-2][-1]==dat[0]: # overlap of termination-byte indicators (TODO: look for longer overlaps? unlikely to occur)
              self.l[-2] = self.l[-2][:-1]
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
    # - strings (just copied in)
    # - positive integers (labels for code)
    # - negative integers (references to labels)
    # - +ve or -ve integers in tuples (labels for functions and text strings: different 'namespace')
    # strings in tuples: opcodes
    # 1st byte of o/p is num bytes needed per address
    if 'ANNOGEN_DEBUG_BYTECODE' in os.environ:
      for l in self.debugDisassemble():
        sys.stderr.write(l+"\n")
    class TooNarrow(Exception): pass
    if js_6bit: aBits,aMask = 6,0x3F
    else: aBits,aMask = 8,0xFF
    for addrSize in xrange(1,256):
        sys.stderr.write("(%d-bit) " % (aBits*addrSize))
        src = self.l[:] # must start with fresh copy, because compaction modifies src and we don't want a false start with wrong addrSize to affect us
        try:
          compacted = 0 ; compaction_types = set()
          if compact_opcodes:
            # The compact opcodes all rely on relative addressing (relative to AFTER the compact instruction) that goes only forward.  Easiest way to deal with that is to work backwards from the end, inlining the compactions, before running a conventional 2-pass assembly.
            # TODO: Could move the below loop into this one in its entirety, and just assemble backwards.  Most within-function label references point forwards anyway.  (Would still need some backward refs for functions though)
            bytesFromEnd = 0
            lDic = {} # labelNo -> bytesFromEnd
            def LGet(lRef,origOperandsLen):
              # return the number of bytes between the end of the new instruction and the label.  Since bytesFromEnd includes origOperandsLen, we need to subtract that out, which would then leave bytes from end of code to end of new instruction (no matter what the length of the new instruction will be)
              if not -lRef in lDic: return -1
              return bytesFromEnd-origOperandsLen-lDic[-lRef]
            counts_to_del = set()
            for count in xrange(len(src)-1,-1,-1):
                i = src[count]
                if type(i) in [str,unicode] and len(i)==1 and 71<=ord(i)<=73 and src[count+ord(i)-70+1]==('return',):
                  # (74 to 76 = 71 to 73 + return)
                  src[count] = chr(ord(i)+3)
                  counts_to_del.add(count+ord(i)-70+1)
                  compacted += 1 ; bytesFromEnd -= 1
                  compaction_types.add('return')
                elif type(i)==tuple and type(i[0])==str:
                    opcode = i[0] ; i = "-"
                    if opcode=='call' and src[count+2]==('return',):
                      src[count] = ('jump',)
                      counts_to_del.add(count+2)
                      compacted += 1 ; bytesFromEnd -= 1
                      compaction_types.add(opcode)
                      # can't fall through by setting opcode='jump', as the address will be in the function namespace (integer in tuple, LGet would need adjusting) and is highly unlikely to be within range (TODO: unless we try to arrange the functions to make it so for some cross-calls)
                    if opcode=='jump' and 0 <= LGet(src[count+1],addrSize) < 0x80: # we can use a 1-byte relative forward jump (up to 128 bytes), useful for 'break;' in a small switch
                      offset = LGet(src[count+1],addrSize)
                      if offset == 0:
                        # can remove this jump completely
                        i = "" # for bytesFromEnd count
                        compacted += 1
                        counts_to_del.add(count) # zap jmp
                      else: src[count] = i = chr(0x80 | offset) # new instr: 0x80|offset
                      counts_to_del.add(count+1) # zap the label
                      compacted += addrSize # as we're having a single byte instead of byte + address
                      bytesFromEnd -= addrSize
                      compaction_types.add(opcode)
                    elif opcode=='switchbyte':
                      numItems = len(src[count+2]) # = ord(src[count+1]) + 1
                      if 1 <= numItems <= 20:
                       numLabels = numItems+1 # there's an extra default label at the end
                       origOperandsLen = 1+numItems+numLabels*addrSize # number + N bytes + the labels
                       if LGet(src[count+3],origOperandsLen)==0 and all(0 <= LGet(src[count+N],origOperandsLen) <= 0xFF-js_6bit_offset for N in xrange(4,3+numLabels)): # 1st label is immediately after the switchbyte, and all others are in range
                        if javascript: # use printable range
                          if js_6bit and numItems<=17 and all(0x80<=ord(x)<=0xBF or 0xD4<=ord(x)<=0xEF for x in src[count+2]): # move UTF-8 representations of U+0500 through U+FFFF to printable range (in one test this saved 780k for the continuation bytes and another 200k for the rest)
                            def mv(x):
                              if x>=0xD4: x -= 20 # or, equivalently, if (x-93)>118, which is done to the input byte in JS before searching on these
                              return chr(x-93)
                            src[count+2]=''.join(mv(ord(x)) for x in src[count+2])
                            i = chr(ord(src[count+1])+91) # and a printable opcode
                          else: i = chr(ord(src[count+1])+108) # can't make the match bytes printable, but at least we can have a printable opcode
                        else: i = src[count+1]
                        src[count] = i = i+src[count+2]+''.join(chr(LGet(src[count+N],origOperandsLen)+js_6bit_offset) for N in xrange(4,3+numLabels)) # opcode_including_nItems, string of bytes, offsets (assume 1st offset at count+3 is 0 so not listed)
                        for ctd in xrange(count+1,count+3+numLabels): counts_to_del.add(ctd)
                        newOperandsLen = numItems*2 # for each byte, the byte itself and an offset, + 1 more offset as default, - 1 because first is not given
                        compacted += origOperandsLen-newOperandsLen
                        bytesFromEnd -= origOperandsLen # will add new opCode + operands below
                        compaction_types.add(opcode)
                elif type(i) in [int,tuple]: # labels
                    if type(i)==int: i2 = i
                    else: i2 = i[0]
                    assert type(i2)==int
                    if i2 > 0:
                        lDic[i] = bytesFromEnd ; i = ""
                        if bytesFromEnd >> (aBits*addrSize+1): raise TooNarrow() # fair assumption (but do this every label, not every instruction)
                    else: i = "-"*addrSize # a reference
                bytesFromEnd += len(i)
            src=[s for s,i in zip(src,xrange(len(src))) if not i in counts_to_del] # batched up because del is O(n)
          # End of compact_opcodes
          lDic = {} # label dictionary: labelNo -> address
          for P in [1,2]:
            r = [chr(addrSize)] # List to hold the output bytecode, initialised with a byte indicating how long our addresses will be.
            ll = 1 # cumulative length of output list
            count = 0 # reading through src opcodes etc
            while count < len(src):
                i = src[count] ; count += 1
                if type(i)==tuple and type(i[0])==str: i = chr(BytecodeAssembler.opcodes[i[0]])
                elif type(i) in [int,tuple]: # labels
                    if type(i)==int: i2,iKey = i,-i # +ve integers are labels, -ve integers are references to them
                    else: i2,iKey = i[0],(-i[0],) # reserved labels (a different counter)
                    assert type(i2)==int
                    # At this point, if i2<0 then iKey will be the lDic key for looking up the label.
                    if i2 > 0: # label going in here: set lDic etc (without outputting any bytes of course)
                        if (ll >> (aBits*addrSize)): raise TooNarrow() # on the assumption that somebody will reference this label, figure out early that we need more bits
                        if i in lDic:
                          assert lDic[i] == ll, "%s moved %d->%d" % (repr(i),lDic[i],ll)
                        lDic[i] = ll ; i = ""
                    elif iKey in lDic: # known label
                        i = lDic[iKey] # the address to convert to MSB-LSB bytes and output:
                        shift = aBits*addrSize
                        if (i >> shift): raise TooNarrow()
                        j = []
                        for b in xrange(addrSize):
                            # MSB-LSB (easier to do in JS)
                            shift -= aBits
                            j.append(chr(((i>>shift)&aMask)+js_6bit_offset))
                        i = "".join(j)
                        assert len(i)==addrSize
                    else: # ref to as-yet unknown label
                        assert P==1, "undefined label %d" % -i
                        i = "-"*addrSize # placeholder (well we could just advance ll, but setting this makes things easier if you ever want to inspect partial results)
                if len(i):
                  r.append(i) ; ll += len(i)
            sys.stderr.write(".")
          if js_utf8: # some "bytes" will actually be Unicode characters, so normalise all before join
            for i in xrange(len(r)):
              if type(r[i])==str:
                r[i]=unicode(r[i],'latin1')
          r = "".join(r)
          if zlib:
            self.origLen = ll # needed for efficient malloc in the C code later
            oR,r = r,zlib.compress(r,9)
            if compact_opcodes: sys.stderr.write("%d bytes (zlib compressed from %d after opcode compaction saved %d on %s)\n" % (len(r),ll,compacted,','.join(sorted(list(compaction_types)))))
            else: sys.stderr.write("%d bytes (zlib compressed from %d)\n" % (len(r),ll))
          elif compact_opcodes: sys.stderr.write("%d bytes (opcode compaction saved %d on %s)\n" % (ll,compacted,','.join(sorted(list(compaction_types)))))
          else: sys.stderr.write("%d bytes\n" % ll)
          return r
        except TooNarrow: pass
    assert 0, "can't even assemble it with 255-byte addressing !?!"
  def debugDisassemble(self):
    i = 0
    while i < len(self.l):
      op = self.l[i]
      if type(op) in [str,unicode] and op in 'GHI': op=(op,)
      if op==('jump',):
        params = (-self.l[i+1],)
      elif op==[('call',)]:
        params = ("Lib"+repr(-self.l[i+1][0]),)
      elif op==('switchbyte',):
        params = (1+ord(self.l[i+1]),)+tuple(self.l[i+2:i+5+ord(self.l[i+1])])
      elif op in [('G',),('H',),('I',)]:
        params = (ord(self.l[i+1]),)+tuple(self.l[i+2:i+2+ord(op[0])-ord('G')])
        op=(['copyBytes','o','o2'][ord(op[0])-ord('G')],)
      elif op==('neartest',): # until +ve label reached
        j = i+3
        while not (type(self.l[j])==int and self.l[j]>0):
          j += 1
        params = ('t='+repr(self.l[i+1]),'f='+repr(self.l[i+2]),'nB='+str(ord(self.l[i+3])))+tuple(self.l[i+4:j])
      else: params = None
      if type(op)==tuple and type(op[0])==str:
        if params==None: yield "  "+op[0]
        else:
          yield "  "+op[0]+" "+" ".join(repr(x) for x in params)
          if type(params)==tuple: i += len(params)
          else: i += 1
      elif type(op) in [str,unicode]: yield "  EQUS "+repr(op)
      elif type(op)==int:
        if op>0: yield "."+str(op)+":"
        else: yield "  RefTo("+str(op)+")" # shouldn't happen outside a parameter
      elif type(op)==tuple and type(op[0])==int:
        if op>0: yield ".Lib"+str(op)+":"
        else: yield "  RefTo(Lib"+str(op)+")" # shouldn't happen outside a parameter
      i += 1

js_start = '/* Javascript '+version_stamp+r"""

Usage:

 - You could just include this code and then call the
   annotate() function i.e. var result = annotate(input"""
if sharp_multi: js_start += ", annotation_type_number"
js_start += r""")

 - Or you could use (and perhaps extend) the Annotator
   object, and call its annotate() method.  If you have
   Backbone.JS, Annotator will instead be a generator
   (extending Backbone.Model) which you will have to
   instantiate yourself (possibly after extending it).
   The Annotator object/class is also what will be
   exported by this module if you're using Common.JS.

 - On Unix systems with Node.JS, you can run this file in
   "node" to annotate standard input as a simple test.
"""
if zlib:
  js_start += r"""
   zlib'd version uses Uint8Array so has minimum browser requirements
   (Chrome 7, Ffx 4, IE10, Op11.6, Safari5.1, 4.2 on iOS)
   - generate without --zlib to support older browsers.

  Inflate code taken from UZip.js (c) 2018 "Photopea" (MIT-licensed),
  cut down with small modifications and JSCompress'd:
*/
function inflate(r,e){var t,n=new Uint8Array(e);t="undefined"!=typeof window&&window.atob?function(r){for(var e=new Uint8Array(r.length),t=0,n=e.length;t<n;t++)e[t]=r.charCodeAt(t);return e}(atob(r)):"undefined"!=typeof Buffer?new Buffer(r,"base64"):function(r){var e,t,n={},f=65,a=0,o=0,i=new Uint8Array(r.length),d=0,l=String.fromCharCode,v=r.length;for(e="";f<91;)e+=l(f++);for(e+=e.toLowerCase()+"0123456789+/",f=0;f<64;f++)n[e.charAt(f)]=f;for(e=0;e<v;e++)for(a=(a<<6)+(f=n[r.charAt(e)]),o+=6;8<=o;)((t=a>>>(o-=8)&255)||e<v-2)&&(i[d++]=t);return i}(r);var f=new Uint8Array(t.buffer,t.byteOffset+2,t.length-6),h={_decodeTiny:function(r,e,t,n,f,a){for(var o=f,i=h._bitsE,d=h._get17,l=t<<1,v=0,s=0;v<l;){var u=r[d(n,f)&e];f+=15&u;var p=u>>>4;if(p<=15)a[v]=0,s<(a[v+1]=p)&&(s=p),v+=2;else{var w=0,y=0;16==p?(y=3+i(n,f,2)<<1,f+=2,w=a[v-1]):17==p?(y=3+i(n,f,3)<<1,f+=3):18==p&&(y=11+i(n,f,7)<<1,f+=7);for(var U=v+y;v<U;)a[v]=0,a[v+1]=w,v+=2}}for(var c=a.length;v<c;)a[v+1]=0,v+=2;return s<<24|f-o},makeCodes:function(r,e){for(var t,n,f,a,o=h.U,i=r.length,d=o.bl_count,l=0;l<=e;l++)d[l]=0;for(l=1;l<i;l+=2)d[r[l]]++;var v=o.next_code;for(d[t=0]=0,n=1;n<=e;n++)t=t+d[n-1]<<1,v[n]=t;for(f=0;f<i;f+=2)0!=(a=r[f+1])&&(r[f]=v[a],v[a]++)},codes2map:function(r,e,t){var n=r.length,f=h.U.rev15;for(C=0;C<n;C+=2)if(0!=r[C+1])for(var a=C>>1,o=r[C+1],i=a<<4|o,d=e-o,l=r[C]<<d,v=l+(1<<d);l!=v;){t[f[l]>>>15-e]=i,l++}},revCodes:function(r,e){for(var t=h.U.rev15,n=15-e,f=0;f<r.length;f+=2){var a=r[f]<<e-r[f+1];r[f]=t[a]>>>n}},_bitsE:function(r,e,t){return(r[e>>>3]|r[1+(e>>>3)]<<8)>>>(7&e)&(1<<t)-1},_get17:function(r,e){return(r[e>>>3]|r[1+(e>>>3)]<<8|r[2+(e>>>3)]<<16)>>>(7&e)}};h.U={next_code:new Uint16Array(16),bl_count:new Uint16Array(16),ordr:[16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15],of0:[3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258,999,999,999],exb:[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0,0,0,0],ldef:new Uint16Array(32),df0:[1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577,65535,65535],dxb:[0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,0,0],ddef:new Uint32Array(32),flmap:new Uint16Array(512),fltree:[],fdmap:new Uint16Array(32),fdtree:[],lmap:new Uint16Array(32768),ltree:[],dmap:new Uint16Array(32768),dtree:[],imap:new Uint16Array(512),itree:[],rev15:new Uint16Array(32768),lhst:new Uint32Array(286),dhst:new Uint32Array(30),ihst:new Uint32Array(19),lits:new Uint32Array(15e3),strt:new Uint16Array(65536),prev:new Uint16Array(32768)},function(){for(var r=h.U,e=0;e<32768;e++){var t=e;t=(4278255360&(t=(4042322160&(t=(3435973836&(t=(2863311530&t)>>>1|(1431655765&t)<<1))>>>2|(858993459&t)<<2))>>>4|(252645135&t)<<4))>>>8|(16711935&t)<<8,r.rev15[e]=(t>>>16|t<<16)>>>17}for(e=0;e<32;e++)r.ldef[e]=r.of0[e]<<3|r.exb[e],r.ddef[e]=r.df0[e]<<4|r.dxb[e];for(e=0;e<=143;e++)r.fltree.push(0,8);for(;e<=255;e++)r.fltree.push(0,9);for(;e<=279;e++)r.fltree.push(0,7);for(;e<=287;e++)r.fltree.push(0,8);for(h.makeCodes(r.fltree,9),h.codes2map(r.fltree,9,r.flmap),h.revCodes(r.fltree,9),e=0;e<32;e++)r.fdtree.push(0,5);h.makeCodes(r.fdtree,5),h.codes2map(r.fdtree,5,r.fdmap),h.revCodes(r.fdtree,5);for(e=0;e<19;e++)r.itree.push(0,0);for(e=0;e<286;e++)r.ltree.push(0,0);for(e=0;e<30;e++)r.dtree.push(0,0)}();for(var a,o,i=function(r,e,t){return(r[e>>>3]|r[1+(e>>>3)]<<8|r[2+(e>>>3)]<<16)>>>(7&e)&(1<<t)-1},d=h._bitsE,l=h._decodeTiny,v=h.makeCodes,s=h.codes2map,u=h._get17,p=h.U,w=0,y=0,U=0,c=0,A=0,m=0,b=0,g=0,_=0;0==w;)if(w=i(f,_,1),y=i(f,_+1,2),_+=3,0!=y){if(1==y&&(a=p.flmap,o=p.fdmap,m=511,b=31),2==y){U=d(f,_,5)+257,c=d(f,_+5,5)+1,A=d(f,_+10,4)+4;_+=14;for(var C=0;C<38;C+=2)p.itree[C]=0,p.itree[C+1]=0;var x=1;for(C=0;C<A;C++){var k=d(f,_+3*C,3);x<(p.itree[1+(p.ordr[C]<<1)]=k)&&(x=k)}_+=3*A,v(p.itree,x),s(p.itree,x,p.imap),a=p.lmap,o=p.dmap;var E=l(p.imap,(1<<x)-1,U,f,_,p.ltree);m=(1<<(E>>>24))-1,_+=16777215&E,v(p.ltree,E>>>24),s(p.ltree,E>>>24,a);var B=l(p.imap,(1<<x)-1,c,f,_,p.dtree);b=(1<<(B>>>24))-1,_+=16777215&B,v(p.dtree,B>>>24),s(p.dtree,B>>>24,o)}for(;;){var O=a[u(f,_)&m];_+=15&O;var T=O>>>4;if(T>>>8==0)n[g++]=T;else{if(256==T)break;var L=g+T-254;if(264<T){var S=p.ldef[T-257];L=g+(S>>>3)+d(f,_,7&S),_+=7&S}var j=o[u(f,_)&b];_+=15&j;var q=j>>>4,z=p.ddef[q],D=(z>>>4)+i(f,_,15&z);for(_+=15&z;g<L;)n[g]=n[g++-D],n[g]=n[g++-D],n[g]=n[g++-D],n[g]=n[g++-D];g=L}}}else{0!=(7&_)&&(_+=8-(7&_));var F=4+(_>>>3),G=f[F-4]|f[F-3]<<8;n.set(new Uint8Array(f.buffer,f.byteOffset+F,G),g),_=F+G<<3,g+=G}return n.length==g?n:n.slice(0,g)}
"""
else: js_start += "*/"
js_start += r"""

var Annotator={
version: '"""+version_stamp+"',\n"
if sharp_multi: js_end = "annotate: function(input,aType) { if(aType==undefined) aType=0;"
else: js_end = "annotate: function(input) {"
js_end += r"""
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
  for (i=addrLen; i; i--) addr=(addr << """
if js_6bit: js_end += "6) | (data.charCodeAt(dPtr++)-"+str(js_6bit_offset)+");"
else: js_end += "8) | data.charCodeAt(dPtr++);"
js_end += r"""
  
  return addr;
}

function readRefStr() {
  var a = readAddr(); var l=data.charCodeAt(a);"""
if js_6bit:
  js_end += r"""
  if(l && l<123) a = data.slice(a+1,a+l-30);
  else a = data.slice(a+1,data.indexOf(data.charAt(a),a+1));"""
elif zlib: js_end += r"""
  if (l != 0) a = data.slice(a+1,a+l+1);
  else a = data.slice(a+1,data.indexOf(0,a+1));"""
else: js_end += r"""
  if (l != 0) a = data.slice(a+1,a+l+1);
  else a = data.slice(a+1,data.indexOf('\x00',a+1));"""
if zlib: js_end += "return String.fromCharCode.apply(null,a)"
elif js_utf8: js_end += "return unescape(encodeURIComponent(a))" # Unicode to UTF-8 (TODO: or keep as Unicode? but copyP things will be in UTF-8, as will the near tests)
elif js_6bit: js_end += "return unescape(a)" # %-encoding
else: js_end += "return a"
js_end += r"""}
function s() {
  if (needSpace) output.push(" ");
  else needSpace=1; // for after the word we're about to write (if no intervening bytes cause needSpace=0)
}

function readData() {
    var sPos = new Array(), c;
    while(1) {
        c = data.charCodeAt(dPtr++);
        if (c & 0x80) dPtr += (c&0x7F);"""
if js_6bit: js_end += r"""
        else if (c > 90) { c-=90; 
            var i=-1;if(p<input.length){var cc=input.charCodeAt(p++)-93; if(cc>118)cc-=20; i=data.slice(dPtr,dPtr+c).indexOf(String.fromCharCode(cc))}
            if (i==-1) i = c;
            if(i) dPtr += data.charCodeAt(dPtr+c+i-1)-"""+str(js_6bit_offset)+r""";
            dPtr += c+c }"""
js_end += r"""
        else if (c > 107) { c-=107;
            var i = ((p>=input.length)?-1:data.slice(dPtr,dPtr+c).indexOf(input.charAt(p++)));
            if (i==-1) i = c;
            if(i) dPtr += data.charCodeAt(dPtr+c+i-1);
            dPtr += c+c;
        } else switch(c) {
            case 50: dPtr = readAddr(); break;
            case 51: {
              var f = readAddr(); var dO=dPtr;
              dPtr = f; readData() ; dPtr = dO;
              break; }
            case 52: return;
            case 60: {
              var nBytes = data.charCodeAt(dPtr++)+1;
              var i = ((p>=input.length)?-1:data.slice(dPtr,dPtr+nBytes).indexOf(input.charAt(p++)));
              if (i==-1) i = nBytes;
              dPtr += (nBytes + i * addrLen);
              dPtr = readAddr(); break; }
            case 71: case 74: {
              var numBytes = data.charCodeAt(dPtr++);
  output.push(input.slice(copyP,copyP+numBytes));
  copyP += numBytes; if(c==74) return; break; }
            case 72: case 75: {
              var numBytes = data.charCodeAt(dPtr++);
              var annot = readRefStr();
  s();
  output.push("<ruby><rb>");
  output.push(input.slice(copyP,copyP+numBytes));
  copyP += numBytes;
  output.push("</rb><rt>"); output.push(annot);
  output.push("</rt></ruby>"); if(c==75) return; break; }
            case 73: case 76: {
              var numBytes = data.charCodeAt(dPtr++);
              var annot = readRefStr();
              var title = readRefStr();
  s();
  output.push("<ruby title=\""); output.push(title);
  output.push("\"><rb>");
  output.push(input.slice(copyP,copyP+numBytes));
  copyP += numBytes;
  output.push("</rb><rt>"); output.push(annot);
  output.push("</rt></ruby>"); if(c==76) return; break; }
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
                while (dPtr < tPtr && dPtr < fPtr) if (tStr.indexOf(readRefStr()) != -1) { found = 1; break; }
                dPtr = found ? tPtr : fPtr; break;
                }
        default: throw("corrupt data table at "+(dPtr-1)+"/"+data.length+" ("+data.charCodeAt(dPtr-1)+")");
            }
        }
    }

while(p < inputLength) {
var oldPos=p;
dPtr=1;readData();
if (oldPos==p) { needSpace=0; output.push(input.charAt(p++)); copyP++; }
}
return decodeURIComponent(escape(output.join("")))"""
if js_6bit: js_end = js_end.replace("var numBytes = data.charCodeAt(dPtr++);","var numBytes = (data.charCodeAt(dPtr++)-"+str(js_6bit_offset-1)+")&0xFF;")
if sharp_multi: js_end += r""".replace(new RegExp(">"+"[^#]*#".repeat(aType)+"(.*?)(#.*?)?</r","g"),">$1</r")""" # normally <rt>, but this regexp will also work if someone changes the generated code to put annotation into second <rb> and title into <rt>
js_end += r"""; // from UTF-8 back to Unicode
} // end of annotate function
};
"""
if sharp_multi: js_end += "function annotate(input,aType) { return Annotator.annotate(input,aType) }"
else: js_end += "function annotate(input) { return Annotator.annotate(input) }"
js_end += r"""

if (typeof Backbone != "undefined" && Backbone.Model) {
  Annotator = Backbone.Model.extend(Annotator);"""
if sharp_multi: js_end += r"""
  annotate=function(input,aType) { return new Annotator().annotate(input,aType) }"""
else: js_end += r"""
  annotate=function(input) { return new Annotator().annotate(input) }"""
js_end += r"""
}
if (typeof require != "undefined" && typeof module != "undefined" && require.main === module) {
  // Node.js command-line test
  fs=require('fs');
  process.stdout.write(annotate(fs.readFileSync('/dev/stdin').toString()));
} else if (typeof module != "undefined" && module.exports) { // Common.js
  module.exports = Annotator;
}
"""

py_start = '# Python '+version_stamp+r"""

# You can import this module and call annotate(utf8 bytes)
# (from multiple threads if desired),
# or you can run from the command line on standard input.

# annotate has an optional second argument, which can be
# 'ruby' (default), 'raw' (annotation only) or 'braces'.

"""
py_end = r"""
class Annotator:
 version="""+'"'+version_stamp+r""""
 def __call__(self,inStr,aFormat):
  if aFormat=="ruby": self.startA,self.midA,self.endA = "<ruby><rb>","</rb><rt>","</rt></ruby>"
  elif aFormat=="raw": self.startA=self.midA=self.endA = ""
  elif aFormat=="braces": self.startA,self.midA,self.endA = "{","|","}"
  else: raise Exception("Unrecognised annotation format "+repr(aFormat))
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
      if self.p>=len(self.inStr): i = -1
      else: i = data[self.dPtr:self.dPtr+nBytes].find(self.inStr[self.p]) ; self.p += 1
      if i==-1: i = nBytes
      self.dPtr += (nBytes + i * self.addrLen)
      self.dPtr = self.readAddr()
    elif d==71 or d==74:
      numBytes = ord(data[self.dPtr]) ; self.dPtr += 1
      out.append(self.inStr[self.copyP:self.copyP+numBytes])
      self.copyP += numBytes
      if d==74: return
    elif d==72 or d==75:
      numBytes = ord(data[self.dPtr]) ; self.dPtr += 1
      annot = self.readRefStr()
      self.s()
      if self.startA:
        out.append(self.startA)
        out.append(self.inStr[self.copyP:self.copyP+numBytes])
      self.copyP += numBytes
      out.append(self.midA) ; out.append(annot)
      out.append(self.endA)
      if d==75: return
    elif d==73 or d==76:
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
      if d==76: return
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
      while self.dPtr < tPtr and self.dPtr < fPtr:
        if self.readRefStr() in tStr:
          found = 1 ; break
      if found: self.dPtr = tPtr
      else: self.dPtr = fPtr
    else: raise Exception("corrupt data table at "+str(self.dPtr-1)+" ("+str(ord(data[self.dPtr-1]))+")")

def annotate(inStr,p="ruby"): return Annotator()(inStr,p)
def main():
  import sys ; aFormat = 'ruby'
  for a in sys.argv[1:]:
    if a.startswith("--"): aFormat=a[2:]
  sys.stdout.write(annotate(sys.stdin.read(),aFormat))
if __name__=="__main__": main()
""" # TODO: annotation-type option from command line in py

c_zlib = r"""static unsigned char *data=NULL;
static void init() {
  z_stream s; memset(&s,0,sizeof(s));
  s.next_in=origData; s.avail_in=%%ZLIBLEN%%;
  data=malloc(%%ORIGLEN%%); // TODO: check non-NULL
  s.next_out=data; s.avail_out=%%ORIGLEN%%;
  inflateInit(&s); inflate(&s, Z_NO_FLUSH); // TODO: check for memory and data-corruption errors
  inflateEnd(&s);
}
"""
c_datadrive = r"""
static unsigned char *dPtr; static int addrLen;

#include <stdlib.h>

static unsigned char * readAddr() {
  size_t i,addr=0;
  for (i=addrLen; i; i--) addr=(addr << 8) | *dPtr++;
  return data + addr;
}
static void readData() {
  POSTYPE *savedPositions = NULL;
  size_t numSavedPositions = 0;
  while(1) {
    unsigned char c = *dPtr++;
    if (c & 0x80) dPtr += (c&0x7F); // short relative forward jump (up to 128 bytes from addr after instruction)
    else if(c < 20) { // switchbyte with short jumps
      c++; // now c == nBytes
      unsigned char byte=(unsigned char)NEXTBYTE;
      int i;
      for (i=0; i<c; i++) if(byte==dPtr[i]) break;
      if(i) dPtr += dPtr[c+i-1]; dPtr += c+c; // relative from end of switch (after all bytes, 1-byte addresses (except 1st) and the 1-byte default address)
    } else switch(c) {
    case 50: /* jump */ dPtr = readAddr(); break;
    case 51: /* call */ {
      unsigned char *funcToCall=readAddr();
      unsigned char *retAddr = dPtr;
      dPtr = funcToCall; readData(); dPtr = retAddr;
      break; }
    case 52: /* return */
      if (savedPositions) free(savedPositions);
      return;
    case 60: /* switchbyte */ {
      int nBytes=(*dPtr++)+1, i;
      unsigned char byte=(unsigned char)NEXTBYTE;
      for (i=0; i<nBytes; i++) if(byte==dPtr[i]) break;
      dPtr += (nBytes + i * addrLen);
      dPtr = readAddr(); break; }
    case 71: case 74: /* copyBytes */ {
      int numBytes=*dPtr++;
      for(;numBytes;numBytes--)
        OutWriteByte(NEXT_COPY_BYTE);
      if(c==74) return; else break; }
    case 72: case 75: /* o */ {
      int numBytes=*dPtr++;
      char *annot = (char*)readAddr();
      o(numBytes,annot); if(c==75) return; else break; }
    case 73: case 76: /* o2 */ {
      int numBytes=*dPtr++;
      char *annot = (char*)readAddr();
      char *title = (char*)readAddr();
      o2(numBytes,annot,title);
      if(c==76) return; else break; }
    case 80: /* savepos */
      savedPositions=realloc(savedPositions,++numSavedPositions*sizeof(POSTYPE)); // TODO: check non-NULL?
      savedPositions[numSavedPositions-1]=THEPOS;
      break;
    case 81: /* restorepos */
      SETPOS(savedPositions[--numSavedPositions]);
      break;
    case 90: /* neartest */ {
      unsigned char *truePtr = readAddr();
      unsigned char *falsePtr = readAddr();
      setnear(*dPtr++); int found=0;
      while(dPtr < truePtr && dPtr < falsePtr) if(near((char*)readAddr())) { found = 1; break; }
      dPtr = found ? truePtr : falsePtr; break; }
      // default: TODO: error about corrupt data?
    }
  }
}
static void topLevelMatch() {
  addrLen = data[0];
  dPtr=data+1; readData();
}
"""

def splitWords(text,phrases=False):
    # split text into words, ignoring anything between markupStart and markupEnd
    # if phrases = True, instead of words, split on any non-whitespace char outside markupStart..markupEnd
    if phrases: it=re.finditer(phrasePattern,text)
    else: it=re.finditer(wordPattern,text)
    for i in it: yield i.group()

markupPattern = re.compile(re.escape(markupStart)+"(.*?)"+re.escape(markupMid)+"(.*?)"+re.escape(markupEnd),flags=re.DOTALL)
wordPattern = re.escape(markupStart)+'.*?'+re.escape(markupEnd)
phrasePattern = re.compile(wordPattern+r'(\s*'+wordPattern+r')*',flags=re.DOTALL)
wordPattern = re.compile(wordPattern,flags=re.DOTALL)
wspPattern = re.compile(r"\s+")

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
    return re.sub(markupPattern,group,text)

def markUp(text,annotation):
  if mreverse: text,annotation = annotation,text
  return markupStart + text + markupMid + annotation + markupEnd
    
def checkpoint_exit(doIt=1):
  if not checkpoint: return
  try: open(checkpoint+os.sep+"ExitASAP")
  except: return
  if doIt:
    assert main, "Only annogen's main module should call checkpoint_exit with doIt=1"
    os.remove(checkpoint+os.sep+"ExitASAP")
    sys.stderr.write("\nExitASAP found: exit\n")
    raise SystemExit
  else: return True
try: import cPickle as pickle
except:
  try: import pickle
  except: pickle = None
def read_checkpoint():
  t = pickle.Unpickler(open(checkpoint+os.sep+'checkpoint','rb')).load()
  sys.stderr.write("Checkpoint loaded from %d phrases\n" % t[0])
  return t
def write_checkpoint(t):
  pickle.Pickler(open(checkpoint+os.sep+'checkpoint-NEW','wb'),-1).dump(t) # better write to checkpoint-NEW, in case we reboot or have an OS-level "Out of memory" condition *while* checkpointing
  try: os.rename(checkpoint+os.sep+'checkpoint-NEW',checkpoint+os.sep+'checkpoint')
  except OSError: # OS can't do it atomically?
    rm_f(checkpoint+os.sep+'checkpoint')
    try: os.rename(checkpoint+os.sep+'checkpoint-NEW',checkpoint+os.sep+'checkpoint')
    except OSError: pass
  checkpoint_exit()

def status_update(phraseNo,numPhrases,wordsThisPhrase,nRules,phraseLastUpdate,lastUpdate,phraseLastCheckpoint,lastCheckpoint,coverP,nRej,startTime):
  phraseSec = (phraseNo-phraseLastUpdate)*1.0/(time.time()-lastUpdate)
  if phraseSec < 100:
    phraseSecS = "%.1f" % phraseSec
  else: phraseSecS = "%d" % int(phraseSec)
  progress = status_prefix + "%s phrase/sec (%d%%/#w=%d) rules=%d cover=%d%%" % (phraseSecS,int(100.0*phraseNo/numPhrases),wordsThisPhrase,nRules,coverP)
  if warn_yarowsky: progress += (" rej=%d" % nRej)
  if time_estimate:
    if phraseNo-phraseLastCheckpoint < 10: phraseMin = phraseSec*60 # current 'instantaneous' speed
    else: phraseMin = (phraseNo-phraseLastCheckpoint)*60/(time.time()-lastCheckpoint) # longer-term average
    minsLeft = (numPhrases-phraseNo)/phraseMin
    if minsLeft>60*24: progress += " %dd+" % int(minsLeft/60/24)
    elif minsLeft>60: progress += " %dh+" % int(minsLeft/60)
    elif minsLeft: progress += " %dmin+" % minsLeft
    # (including the + because this is liable to be an underestimate; see comment after the --time-estimate option)
    if len(progress) + 14 < screenWidth:
     progress += " (at %02d:%02d:%02d" % time.localtime()[3:6] # clock time: might be useful for checking if it seems stuck
     if len(progress) + 20 < screenWidth and not clear_eol == "  \r": # (being able to fit this in can be intermittent)
      elapsed = time.time() - startTime
      progress += ", analyse=%d:%02d:%02d" % (elapsed/3600,(elapsed%3600)/60,elapsed%60)
     progress += ")"
  sys.stderr.write(progress+clear_eol)

def normalise():
    if capitalisation and annot_whitespace: return
    global corpus_unistr
    if checkpoint:
      try:
        f=open_try_bz2(checkpoint+os.sep+'normalised','rb')
        corpus_unistr = f.read().decode('utf-8')
        return
      except: # if re-generating 'normalised', will also need to regenerate 'map' and 'checkpoint' if present
        assert main, "normalise checkpoint not readable in non-main module"
        rm_f(checkpoint+os.sep+'map.bz2') ; rm_f(checkpoint+os.sep+'map')
        rm_f(checkpoint+os.sep+'checkpoint')
    else: assert main, "normalise called in non-main module and checkpoint isn't even set"
    sys.stderr.write("Normalising...")
    allWords = getAllWords()
    if removeSpace:
     corpus_unistr = re.sub(re.escape(markupEnd)+r'\s+'+re.escape(markupStart),(markupEnd+markupStart).replace('\\',r'\\'),corpus_unistr) # so getOkStarts works consistently if corpus has some space-separated and some not
     corpus_unistr = re.sub(re.escape(markupStart)+'\s+',markupStart.replace('\\',r'\\'),re.sub(r'\s+'+re.escape(markupMid),markupMid.replace('\\',r'\\'),re.sub(re.escape(markupMid)+'\s+',markupMid.replace('\\',r'\\'),re.sub(r'\s+'+re.escape(markupEnd),markupEnd.replace('\\',r'\\'),corpus_unistr)))) # so we're tolerant of spurious whitespace between delimeters and markup (TODO: do this even if not removeSpace?)
     if not annot_whitespace:
      # normalise trailing hyphens e.g. from OCR'd scans:
      cu0 = corpus_unistr ; ff = 0
      for hTry in [1,2]:
        for w in allWords:
          if '-'+aoEnd in w:
            idx = w.index('-'+aoEnd)
            if w[:idx].endswith(aoStart) or w[:idx].endswith("-"): continue # ignore this one (a mess of some kind)
            if hTry==2: # ouch, this doesn't look good
              sys.stderr.write(" (can't normalise hyphens due to '%s') " % w.encode(terminal_charset,'replace'))
              corpus_unistr = cu0 ; break
            if mreverse: grp,mdG=r"-\1",r"\2"
            else: grp,mdG=r"-\2",r"\1"
            # TODO: batch up the following replacements by using something similar to Replacer but with a common destination regexp that takes groups from the 'w' entries as well.  (Low priority because don't typically get TOO many of these dangling hyphens in most corpuses.)
            corpus_unistr = re.sub(re.escape(w)+r"\s*"+re.escape(markupStart)+"(.*?)"+re.escape(markupMid)+"(.*?)"+re.escape(markupEnd),w.replace('\\',r'\\').replace('-'+aoEnd.replace('\\',r'\\'),grp+aoEnd.replace('\\',r'\\')).replace(mdEnd.replace('\\',r'\\'),mdG+mdEnd.replace('\\',r'\\')),corpus_unistr,flags=re.DOTALL)
            ff = 1
        if ff: allWords = getAllWords() # re-generate
      del cu0
    sys.stderr.write(":")
    class Replacer:
      def __init__(self): self.dic = {}
      def add(self,x,y):
        if diagnose and diagnose in x: diagnose_write("Replacer.add(%s,%s)" % (x,y))
        self.dic[x] = y
        if not (len(self.dic)%1500): sys.stderr.write('.') # try this instead
      def flush(self):
        if not self.dic: return
        global corpus_unistr
        for exp in orRegexes(re.escape(k) for k in self.dic.iterkeys()):
          sys.stderr.write(';')
          corpus_unistr = re.sub(exp,lambda k:self.dic[k.group(0)],corpus_unistr)
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
      if annot_whitespace or (keep_whitespace and markDown(w) in keep_whitespace): return w,None
      if not re.search(wspPattern,w): return w,hTry
      nowsp = re.sub(wspPattern,"",w)
      if not capitalisation and not nowsp.lower()==nowsp and nowsp.lower() in allWords: nowsp = nowsp.lower()
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
        if rpl.cu_nosp == None:
          rpl.cu_nosp = re.sub(wspPattern,"",corpus_unistr)
          if not capitalisation: rpl.cu_nosp = rpl.cu_nosp.lower() # ignore capitalisation when searching for this
        if capitalisation: aoS2 = aoS
        else: aoS2 = [w0.lower() for w0 in aoS]
        for charBunches in different_ways_of_splitting(md,len(aoS)):
            mw = [markUp(c,w0) for c,w0 in zip(charBunches,aoS2)]
            multiword = "".join(mw)
            if multiword in rpl.cu_nosp:
              # we're about to return a split version of the words, but we now have to pretend it went through the initial capitalisation logic that way (otherwise could get unnecessarily large collocation checks)
              if not capitalisation:
                mw = [markUp(c,w0) for c,w0 in zip(charBunches,aoS)] # the original capitalisation. for selective .lower()
                for i in range(len(mw)):
                  w0 = mw[i]
                  wl = w0.lower()
                  if not w0==wl and wl in allWords:
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
    if checkpoint: open_try_bz2(checkpoint+os.sep+'normalised','wb').write(corpus_unistr.encode('utf-8'))
    checkpoint_exit()
def getAllWords():
  allWords = set()
  for phrase in splitWords(corpus_unistr,phrases=True):
    allWords.update(splitWords(phrase))
  return allWords # do NOT cache (is called either side of the normaliser)
def orRegexes(escaped_keys):
  escaped_keys = list(escaped_keys) # don't just iterate
  try: yield re.compile('|'.join(escaped_keys))
  except OverflowError: # regex too big (e.g. default Python on Mac OS 10.7 i.e. Python 2.7.1 (r271:86832, Jul 31 2011, 19:30:53); probably some Windows versions also; does not affect Mac HomeBrew's Python 2.7.12)
    ek = escaped_keys[:len(escaped_keys)/2]
    for r in orRegexes(ek): yield r
    ek = escaped_keys[len(ek):]
    for r in orRegexes(ek): yield r

if mreverse: mdStart,mdEnd,aoStart,aoEnd = markupMid,markupEnd,markupStart,markupMid
else: mdStart,mdEnd,aoStart,aoEnd = markupStart,markupMid,markupMid,markupEnd

def different_ways_of_splitting(chars,numWords):
  if numWords > len(chars): return
  elif numWords == len(chars):
    yield list(chars) ; return
  elif numWords == 1:
    yield [chars] ; return
  spAt_try1 = len(chars) / numWords + 1
  for spAt in range(spAt_try1,0,-1) + range(spAt_try1+1, len(chars)-numWords+1):
    for r in different_ways_of_splitting(chars[spAt:],numWords-1): yield [chars[:spAt]]+r

def yarowsky_indicators(withAnnot_unistr,canBackground):
    # yields True if rule always works (or in majority of cases with ymajority), or lists enough indicators to cover example instances and yields (negate, list, nbytes), or just list if empty.
    # (If too few indicators can be found, will list the ones it can, or empty if no clearly-distinguishable indicators can be found within ybytes of end of match.)
    # yield "backgrounded" = task has been backgrounded; .next() collects result
    nonAnnot=markDown(withAnnot_unistr)
    if nonAnnot in yPriorityDic: # TODO: enforce len==1 ?
        if yPriorityDic[nonAnnot] == withAnnot_unistr:
            # we want this case to be the default (TODO: can't we just put it straight into the rules when making yPriorityDic, and skip this?  although I'm not sure if that would give much of a speedup, as the phrase/sec count tends to go into the thousands anyway when it's processing a yPriorityDic section)
            if nonAnnot==diagnose: diagnose_write("yPriorityDic forces %s" % (withAnnot_unistr,))
            yield True ; return
        else:
          if nonAnnot==diagnose: diagnose_write("yPriorityDic forbids default %s" % (withAnnot_unistr,))
          can_be_default = False # another is default, don't make this one default even if it occurs more
    else: can_be_default = True
    # First, find positions in corpus_markedDown which match withAnnot_unistr in corpus_unistr
    okStarts = getOkStarts(withAnnot_unistr)
    # now check for corpus_markedDown matches that *don't* have withAnnot_unistr
    badStarts = getBadStarts(nonAnnot,okStarts)
    if not badStarts:
      if nonAnnot==diagnose: diagnose_write("%s has no badStarts" % (withAnnot_unistr,))
      yield True ; return # rule always works, no Yarowsky-like indicators needed
    if can_be_default and len(okStarts) > len(badStarts) and len(nonAnnot)==1:
      if nonAnnot==diagnose: diagnose_write("%s is default by majority-case len=1 rule" % (withAnnot_unistr,))
      yield True ; return # duplicate of code below (can test for this case early before reducing-down badStarts)
    badStarts = getReallyBadStarts(badStarts,nonAnnot) # see its comments (ignore some badStarts)
    if not badStarts:
      if nonAnnot==diagnose: diagnose_write("%s has only probably-irrelevant badStarts" % (withAnnot_unistr,))
      yield True ; return
    # Now, if it's right more often than not:
    if can_be_default and len(okStarts) > len(badStarts):
        # could we have this as a "default" rule, with the other cases as exceptions that will be found first?
        if len(nonAnnot)==1:
          if nonAnnot==diagnose: diagnose_write("%s is default by majority-case len=1 rule after removing irrelevant badStarts" % (withAnnot_unistr,))
          yield True ; return # should be safe, and should cover most "common short Chinese word with thousands of contexts" cases
        # If len 2 or more, it's risky because the correct solution could be to process just a fraction of the word now and the rest will become the start of a longer word, so we probably don't want it matching the whole lot by default unless can be sure about it
        # e.g. looking at rule AB, text ABC and correct segmentation is A BC, don't want it to 'greedily' match AB by default without positive indicators it should do so
        # Check for no "A BC" situations, i.e. can't find any possible SEQUENCE of rules that STARTS with ALL the characters in nonAnnot and that involves having them SPLIT across multiple words:
        # (The below might under-match if there's the appearance of a split rule but it actually has extra non-marked-up text in between, but it shouldn't over-match.)
        # TODO: if we can find the actual "A BC" sequences (instead of simply checking for their possibility as here), and if we can guarantee to make 'phrase'-length rules for all of them, then AB can still be the default.  This might be useful if okStarts is very much greater than badStarts.
        # (TODO: until the above is implemented, consider recommending --ymax-threshold=0, because, now that Yarowsky-like collocations can be negative, the 'following word' could just go in as a collocation with low ybytes)
        # TODO: also, if the exceptions to rule AB are always of the form "Z A B", and we can guarantee to generate a phrase rule for "Z A B", then AB can still be default.  (We should already catch this when the exceptions are "ZA B", but not when they are "Z A B", and --ymax-threshold=0 probably won't always help here, especially if Z==B; Mandarin "mei2you3" / "you3 mei2 you3" comes to mind)
        llen = len(mdStart)+len(nonAnnot)
        if all(x.end()-x.start()==llen for x in re.finditer(re.escape(mdStart)+("("+re.escape(mdEnd)+"((?!"+re.escape(mdStart)+").)*.?"+re.escape(mdStart)+")?").join(re.escape(c) for c in list(nonAnnot)),corpus_unistr)):
          if nonAnnot==diagnose: diagnose_write("%s is default by majority-case rule after checking for dangerous overlaps etc" % (withAnnot_unistr,))
          yield True ; return
    run_in_background = canBackground and len(okStarts) > 500 and executor # In a test with 300, 500, 700 and 900, the 500 threshold was fastest on concurrent.futures, but by just a few seconds.  TODO: does mpi4py.futures have a different 'sweet spot' here? (low priority unless we can get MPI to outdo concurrent.futures in this application)
    may_take_time = canBackground and len(okStarts) > 1000
    if may_take_time: sys.stderr.write("\nLarge collocation check (%s has %d matches + %s), %s....  \n" % (withAnnot_unistr.encode(terminal_charset,'replace'),len(okStarts),badInfo(badStarts,nonAnnot),cond(run_in_background,"backgrounding","could take some time")))
    if run_in_background:
      job = executor.submit(yarowsky_indicators_wrapped,withAnnot_unistr) # recalculate the above on the other CPU in preference to passing, as memory might not be shared
      yield "backgrounded" ; yield job.result() ; return
    if ybytes_max > ybytes and (not ymax_threshold or len(nonAnnot) <= ymax_threshold):
      retList = [] ; append=retList.append
      for nbytes in range(ybytes,ybytes_max+1,ybytes_step):
        negate,ret,covered,toCover = tryNBytes(nbytes,nonAnnot,badStarts,okStarts,withAnnot_unistr)
        if covered==toCover and len(ret)==1:
          if may_take_time: sys.stderr.write(" - using 1 indicator, negate=%s\n" % repr(negate))
          yield (negate,ret,nbytes) ; return # a single indicator that covers everything will be better than anything else we'll find
        append((-int(covered*100/toCover),len(ret),nbytes,negate,toCover,ret)) # (1st 4 of these are the sort keys: maximum coverage to nearest 1%, THEN minimum num indicators for the same coverage, THEN minimum nbytes (TODO: problems of very large nbytes might outweigh having more indicators; break if found 100% coverage by N?), THEN avoid negate)
        # TODO: try finding an OR-combination of indicators at *different* proximity lengths ?
      retList.sort()
      if nonAnnot==diagnose: diagnose_write("Best coverage is %d%% of %d" % (-retList[0][0],retList[0][-2]))
      negate,ret = retList[0][-3],retList[0][-1]
      distance = retList[0][2]
    else:
      negate,ret = tryNBytes(ybytes_max,nonAnnot,badStarts,okStarts,withAnnot_unistr)[:2]
      if ybytes < ybytes_max: distance = ybytes_max
      else: distance = None # all the same anyway
    if not ret and warn_yarowsky: sys.stderr.write("Couldn't find ANY Yarowsky-like indicators for %s   \n" % (withAnnot_unistr.encode(terminal_charset,'replace'))) # (if nonAnnot==diagnose, this'll be reported by tryNBytes below)
    # elif ybytes_max > ybytes: sys.stderr.write("Debugger: %s best coverage=%d/%d by %d indicators at nbytes=%d   \n" % (withAnnot_unistr.encode(terminal_charset,'replace'),-retList[0][0],retList[0][3],retList[0][1],retList[0][2]))
    # TODO: if partially but not completely covered, shouldn't entirely count the word as 'covered' in analyse()
    elif ret and may_take_time: sys.stderr.write(" - using %d indicators, negate=%s\n" % (len(ret),repr(negate)))
    if not ret or (not distance and not negate):
      yield ret
    else:
      if not distance: distance = ybytes_max
      yield negate,ret,distance
def yarowsky_indicators_wrapped(withAnnot_unistr):
    check_globals_are_set_up()
    return yarowsky_indicators(withAnnot_unistr,False).next()
def getOkStarts(withAnnot_unistr):
    if withAnnot_unistr in precalc_sets: return precalc_sets[withAnnot_unistr]
    walen = len(withAnnot_unistr)
    return set(x for x in precalc_sets[splitWords(withAnnot_unistr).next()] if corpus_unistr[m2c_map[x]:m2c_map[x]+walen]==withAnnot_unistr)
def getBadStarts(nonAnnot,okStarts): return set(x.start() for x in re.finditer(re.escape(nonAnnot),corpus_markedDown) if not x.start() in okStarts)
def getReallyBadStarts(badStarts,nonAnnot):
    # Some of the badStarts can be ignored on the grounds that they should be picked up by other rules first: any where the nonAnnot match does not start at the start of a word (the rule matching the word starting earlier should get there first), and any where it starts at the start of a word that is longer than its own first word (the longest-first ordering should take care of this).  So keep only the ones where it starts at the start of a word and that word is no longer than len(nonAnnot).
    reallyBadStarts = [] ; append=reallyBadStarts.append
    nonAnnotLen = len(mdStart+nonAnnot+mdEnd)
    theRe = re.compile(re.escape(mdStart+nonAnnot[0])+".*?"+re.escape(mdEnd),flags=re.DOTALL)
    for b in badStarts:
      try: s = m2c_map[b]
      except KeyError: continue # it wasn't the start of a word (only start positions are in that map)
      m=theRe.search(corpus_unistr, s) # will either start at s, or after it if mreverse
      s,e = m.start(),m.end()
      if e-s > nonAnnotLen: continue # this word is too long, should be matched by a longer rule 1st
      append(b) # to reallyBadStarts
    return reallyBadStarts
def tryNBytes(nbytes,nonAnnot,badStarts,okStarts,withAnnot_unistr):
    # try to find either positive or negative Yarowsky-like indicators, whichever gives a smaller set.  Negative indicators might be useful if there are many matches and only a few special exceptions (TODO: but put in an option to avoid checking for them as per v0.57 and below? although I'm not sure what application would have to be that careful but still use Yarowsky-like indicators)
    # (Negative indicators are used only if they cover 100% of the exceptions - see below re negate==None)
    def bytesAround(start): return within_Nbytes(start+len(nonAnnot),nbytes)
    okStrs=list(set(bytesAround(s) for s in okStarts))
    badStrs=list(set(bytesAround(s) for s in badStarts))
    pOmit = unichr(1).join(badStrs) # omit anything that occurs in this string from +ve indicators
    nOmit = unichr(1).join(okStrs) # ditto for -ve indicators
    pCovered=[False]*len(okStrs)
    nCovered=[False]*len(badStrs)
    pRet = [] ; pAppend=pRet.append
    nRet = [] ; nAppend=nRet.append
    negate = None # not yet set
    stuffToCheck = [(okStrs,pAppend,pCovered,unique_substrings(okStrs,markedUp_unichars,lambda txt:txt in pOmit,lambda txt:sum(1 for s in okStrs if txt in s)))] # a generator and associated parameters for positive indicators
    if len(okStrs) > len(badStrs) or not okStrs: stuffToCheck.append((badStrs,nAppend,nCovered,unique_substrings(badStrs,markedUp_unichars,lambda txt:txt in nOmit,lambda txt:sum(1 for s in badStrs if txt in s)))) # and for negative indicators, if it seems badStrs are in the minority (or if not okStrs, which is for test_manual_rules) (TODO: smaller minority?  we'll try a string from each generator in turn, stopping if we find one that covers everything; that way we're hopefully more likely to finish early if one of the two is going to quickly give a string that matches everything, but TODO is this always so optimal in other cases?  especially if there are far more negative indicators than positive ones, in which case it's unlikely to end up being a "many matches and only a few special exceptions" situation, and checking through ALL the negative indicators is a lot of work for comparatively little benefit; TODO: also have 'if len(nAppend) > SOME_THRESHOLD and len(stuffToCheck)==2: del stuffToCheck[1] # give up on negative indicators if too many' ? )
    while stuffToCheck and negate==None:
      for i in range(len(stuffToCheck)):
        strs,append,covered,generator = stuffToCheck[i]
        try: indicator = generator.next()
        except StopIteration:
          del stuffToCheck[i] ; break
        found = True ; cChanged = False
        for i in xrange(len(strs)):
          if not covered[i] and indicator in strs[i]:
            covered[i]=cChanged=True
        if cChanged: append(indicator)
        if all(covered):
          if append==pAppend: negate=False
          else: negate=True
          break
    # and if negate==None AFTER this loop, didn't get all(pCovered) OR all(nCovered), in which case we fall back to negate=False.  In other words, negative indicators have to cover ALL non-occurrences to be passed, wheras positive indicators just have to cover SOME.  This is in keeping with the idea of 'under-match is better than over-match' (because an under-matching negative indicator is like an over-matching positive one)
    if negate: ret,covered = nRet,nCovered
    else: ret,covered = pRet,pCovered
    if nonAnnot==diagnose:
      if ret:
        if negate: indicators = "negative indicators "
        else: indicators = "indicators "
        if len(ret) > 30: indicators=str(len(ret))+" "+indicators # +'/'.join(ret[:30]+['...'])
        else: indicators += '/'.join(ret)
      else: indicators = "no indicators"
      if len(pOmit) > 200: pOmit = pOmit[:200]+"..."
      if all(covered): notCovered = ""
      else:
        if negate: strs = badStrs
        else: strs = okStrs
        notCovered = [strs[i] for i in xrange(len(covered)) if not covered[i]]
        if len(notCovered) > 10: notCovered = notCovered[:10]+["..."]
        notCovered = " (not "+'/'.join(notCovered).replace('\n',"\\n")+")"
      diagnose_write("tryNBytes(%d) on %s found %s (avoiding '%s'), covers %d/%d contexts%s" % (nbytes,withAnnot_unistr,indicators,pOmit.replace(unichr(1),'/').replace('\n',"\\n"),sum(1 for x in covered if x),len(covered),notCovered))
    return negate,ret,sum(1 for x in covered if x),len(covered)

def cond(a,b,c):
  if a: return b
  else: return c

def badInfo(badStarts,nonAnnot):
  ret = "%d false positive" % len(badStarts)
  if not len(badStarts)==1: ret += "s"
  if len(badStarts) > yarowsky_debug: return ret
  for wordStart in badStarts:
   wordEnd = wordStart + len(nonAnnot)
   contextStart,contextEnd=max(0,wordStart-5),wordEnd+5
   toRead = corpus_markedDown
   # but can we report it from the original corpus_unistr?
   if wordStart in m2c_map and wordEnd in m2c_map:
    toRead = corpus_unistr
    wordStart,wordEnd = m2c_map[wordStart],m2c_map[wordEnd]
    newCStart,newCEnd = contextStart,contextEnd
    while newCStart not in m2c_map and newCStart >= contextStart-5: newCStart-=1
    while newCEnd not in m2c_map and newCEnd<contextEnd+5: newCEnd+=1
    if newCStart in m2c_map: contextStart = m2c_map[newCStart]
    else: contextStart = max(0,wordStart - 15) # This might cut across markup, but better that than failing to report the original corpus and making it look like the words might not have "lined up" when actually they did.  Might also just cut into surrounding non-markup text (if the above loop simply couldn't find anything near enough because such text was in the way).
    if newCEnd in m2c_map: contextEnd = m2c_map[newCEnd]
    else: contextEnd = wordEnd + 15 # ditto
   ret += (u" (%s%s%s%s%s)" % (toRead[contextStart:wordStart],reverse_on,toRead[wordStart:wordEnd],reverse_off,toRead[wordEnd:contextEnd])).replace("\n","\\n").replace("\r","\\r").encode(terminal_charset,'replace')
  return ret

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

def within_Nbytes(matchEndPos,nbytes):
    # return the Unicode characters within nbytes of matchEndPos, assuming the encoding will be outcode.  Used for the Yarowsky-like functions.
    # Assumes multibyte codes are self-synchronizing, i.e. if you start in the middle of a multibyte sequence, the first valid character will be the start of the next sequence, ok for utf-8 but TODO might not be the case for some codes
    return corpus_markedDown[max(0,matchEndPos-nbytes):matchEndPos].encode(outcode)[-nbytes:].decode(outcode,'ignore')+corpus_markedDown[matchEndPos:matchEndPos+nbytes].encode(outcode)[:nbytes].decode(outcode,'ignore')

def test_rule(withAnnot_unistr,yBytesRet,canBackground=None):
    # Tests to see if the rule withAnnot_unistr is
    # ALWAYS right in the examples, i.e.
    # the number of occurrences of its marked-down text
    # in the continuous marked-down string should be
    # EXACTLY equal to the number of occurrences of the
    # marked-up version.
    # (If we deal only in rules that ALWAYS work, we can
    # build them up incrementally without "cross-talk")
    # yield "backgrounded" = task has been backgrounded; .next() collects result (nb we default to NOT canBackground, as test_rule is called from several places of which ONE can handle backgrounding)
    if primitive:
      yield True ; return
    if ybytes:
        # Doesn't have to be always right, but put the indicators in yBytesRet
        ybrG = yarowsky_indicators(withAnnot_unistr,canBackground)
        ybr = ybrG.next()
        if ybr == "backgrounded":
          yield ybr ; ybr = ybrG.next()
        if ybr==True or not ybr:
          yield ybr ; return
        yBytesRet.append(ybr) # (negate, list of indicators, nbytes)
        yield True ; return
    phrase = markDown(withAnnot_unistr)
    ret = corpus_markedDown.count(phrase) == len(getOkStarts(withAnnot_unistr))
    if diagnose and diagnose==phrase:
      diagnose_write("occurrences(%s)==occurrences(%s) = %s" % (phrase,withAnnot_unistr,ret))
    yield ret

def all_possible_rules(words,covered):
    # Iterate over ALL possible rules derived from the
    # word sequence (don't just "find the shortest context
    # that predicts each word" because that can have
    # trouble with overlaps; need to check them all and
    # stop when we've got enough to reproduce the example)
    # As optimisation, avoids returning rules for which
    # all(covered) over that rule's range
    if max_words: maxRuleLen = min(len(words),max_words)
    else: maxRuleLen = len(words)
    for ruleLen in range(1,maxRuleLen+1): # (sort by len)
        for wStart in range(len(words)-ruleLen+1):
          if not all(covered[wStart:wStart+ruleLen]):
            yield words[wStart:wStart+ruleLen]
            # caller join()s before adding to rules dict

def checkCoverage(ruleAsWordlist,words,coveredFlags):
    # Updates coveredFlags and returns True if any changes
    # (if False, the new rule is redundant).
    # Don't worry about ybytes - assume the Yarowsky-like
    # indicators have been calculated correctly across the
    # whole text so we don't need to re-check them now.
    assert type(ruleAsWordlist)==type(words)==list
    try: start = words.index(ruleAsWordlist[0])
    except ValueError: return False
    ln = len(ruleAsWordlist)
    changedFlags = False
    while start <= len(words)-ln:
        if words[start:start+ln] == ruleAsWordlist:
            if not all(coveredFlags[start:start+ln]):
                coveredFlags[start:start+ln]=[True]*ln
                changedFlags = True
            start += ln
        else:
            try: start = words.index(ruleAsWordlist[0],start+1)
            except ValueError: break
    return changedFlags

def wspJoin(l):
  if removeSpace: return "".join(l)
  else: return " ".join(l)

def potentially_bad_overlap(rulesAsWordlists,newRuleAsWords):
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
            def overlapOK(rAW): return not markDown(wspJoin(rAW)) in corpus_markedDown
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
    sys.stderr.write("\nPickling rules to %s... " % rulesFile)
    f = openfile(rulesFile,'wb')
    pickle.Pickler(f,-1).dump((self.rules,self.rulesAsWordlists_By1stWord,self.rulesAsWordlists,self.seenPhrases))
    # (don't save self.rejectedRules, there might be better clues next time)
    f.close() ; sys.stderr.write("done")
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
  def remove_old_rules(self,words): # for incremental runs - removes previously-discovered rules that would have been suggested by this new phrase but that no longer 'work' with the rest of the corpus due to alterations elsewhere.  DOES NOT remove old rules that are not suggested by any phrase in the corpus because the phrases that suggested them have been removed or changed (TODO: might want an option for that, although fundamentally you shouldn't be relying on incremental runs if you're making a lot of changes to the corpus)
    for w in set(words):
      rulesAsWordlists = self.rulesAsWordlists_By1stWord.get(w,[])
      i=0
      while i<len(rulesAsWordlists):
        if max_words and len(rulesAsWordlists[i])>max_words:
          i += 1 ; continue # better leave that one alone if we're not reconsidering rules that long (e.g. running again with single_words when previous run wasn't)
        rule = wspJoin(rulesAsWordlists[i])
        if rule not in self.newRules and checkCoverage(rulesAsWordlists[i],words,[False]*len(words)): # rule would apply to the new phrase
          yBytesRet = []
          if not test_rule(rule,yBytesRet).next() or potentially_bad_overlap(self.rulesAsWordlists,rulesAsWordlists[i]): # re-test fails.  In versions v0.543 and below, we just removed ALL rules that would apply to the new phrase, to see if they would be re-generated.  But that caused problems because addRulesForPhrase can return early if all(covered) due to other (longer) rules and we might be removing a perfectly good short rule that's needed elsewhere.  So we now re-test before removal.
            self.rejectedRules.add(rule)
            if not ybytes: self.rulesAsWordlists.discard(rulesAsWordlists[i])
            del rulesAsWordlists[i] ; del self.rules[rule]
            continue
          self.newRules.add(rule) # still current - add to newRules now to save calling test_rule again
          if len(yBytesRet): self.rules[rule] = yBytesRet[0] # overriding what it was before (since we've re-done test_rule for it, which might have returned a new set of Yarowsky-like indicators for the new version of the corpus)
        i += 1
  def addRulesForPhrase(self,phrase,canBackground=False):
    if phrase in self.seenPhrases or (diagnose_quick and diagnose):
      # if diagnose and (diagnose_quick or self.amend_rules) and mdStart+diagnose+mdEnd in phrase: pass # look at it again for diagnostics.  But do we accept a diagnose that spans multiple words?  should be pointed out by --diagnose-quick below if uncommented
      if diagnose and (diagnose_quick or self.amend_rules) and diagnose in markDown(phrase): pass # this version accepts diagnose of multiple words (and might also let some phrases through where it matches on an overlap)
      else:
        yield 0,0 ; return # TODO: document that this means the total 'covered' figure in the progress status is AFTER phrase de-duplication (otherwise we'd have to look up what the previous values were last time we saw it - no point doing that just for a quick statistic)
    self.seenPhrases.add(phrase)
    words = filter(lambda x:markDown(x).strip(),splitWords(phrase)) # filter out any that don't have base text (these will be input glitches, TODO: verify the annotation text is also just whitespace, warn if not)
    if not words:
      yield 0,0 ; return
    covered = [False]*len(words)
    # first see how much is covered by existing rules
    # (don't have to worry about the order, as we've been
    # careful about overlaps)
    if self.amend_rules: self.remove_old_rules(words) # NB if yignore this might not remove all, but still removes all that affect checkCoverage below
    for w in set(words):
      for ruleAsWordlist in self.rulesAsWordlists_By1stWord.get(w,[]):
        if checkCoverage(ruleAsWordlist,words,covered) and all(covered):
          yield len(covered),len(covered) ; return # no new rules needed
    for ruleAsWordlist in all_possible_rules(words,covered):
        rule = wspJoin(ruleAsWordlist) ; yBytesRet = []
        if rule in self.rejectedRules: continue
        if rule in self.rules: continue # this can still happen even now all_possible_rules takes 'covered' into account, because the above checkCoverage assumes the rule won't be applied in a self-overlapping fashion, whereas all_possible_rules makes no such assumption (TODO: fix this inconsistency?)
        rGen = test_rule(rule,yBytesRet,canBackground)
        r = rGen.next()
        if r=="backgrounded":
          yield r ; r = rGen.next()
        del rGen
        if not r or potentially_bad_overlap(self.rulesAsWordlists,ruleAsWordlist):
            self.rejectedRules.add(rule) # so we don't waste time evaluating it again (TODO: make sure rejectedRules doesn't get too big?)
            continue
        cc = checkCoverage(ruleAsWordlist,words,covered) # changes 'covered'
        assert cc, "this call to checkCoverage should never return False now that all_possible_rules takes 'covered' into account" # and it's a generator which is always working from the CURRENT copy of 'covered'
        if len(yBytesRet): self.rules[rule] = yBytesRet[0]
        else: self.rules[rule] = [] # unconditional
        if not ybytes: self.rulesAsWordlists.append(ruleAsWordlist)
        if not ruleAsWordlist[0] in self.rulesAsWordlists_By1stWord: self.rulesAsWordlists_By1stWord[ruleAsWordlist[0]] = []
        self.rulesAsWordlists_By1stWord[ruleAsWordlist[0]].append(ruleAsWordlist)
        if self.amend_rules: self.newRules.add(rule)
        handle_diagnose_limit(rule)
        if all(covered):
          yield len(covered),len(covered) ; return
    # If get here, failed to completely cover the phrase.
    # ruleAsWordlist should be set to the whole-phrase rule.
    yield sum(1 for x in covered if x),len(covered)
  def rulesAndConds(self):
    if self.amend_rules: return [(k,v) for k,v in self.rules.items() if not k in self.newRules] + [(k,v) for k,v in self.rules.items() if k in self.newRules] # new rules must come last for incremental runs, so they will override existing actions in byteSeq_to_action_dict when small changes have been made to the annotation of the same word (e.g. capitalisation-normalisation has been changed by the presence of new material)
    else: return self.rules.items()

def handle_diagnose_limit(rule):
  global diagnose,diagnose_limit
  if diagnose and diagnose_limit and diagnose==markDown(rule):
    diagnose_limit -= 1
    if not diagnose_limit:
      diagnose = False
      diagnose_write("limit reached, suppressing further diagnostics")

def generate_map():
    global m2c_map, precalc_sets, yPriorityDic
    if checkpoint:
      try:
        f=open_try_bz2(checkpoint+os.sep+'map','rb')
        m2c_map,precalc_sets,yPriorityDic = pickle.Unpickler(f).load()
        return
      except: pass
    assert main, "Only main should generate corpus map"
    sys.stderr.write("Generating corpus map... ")
    m2c_map = {} ; precalc_sets = {}
    muStart = downLenSoFar = 0
    for s in re.finditer(re.escape(markupStart), corpus_unistr):
      s=s.start()
      downLenSoFar += len(markDown(corpus_unistr[muStart:s]))
      muStart = s
      m2c_map[downLenSoFar] = s
      # Added optimisation: do precalc_sets as well
      # (at least catch the 1-word cases)
      # -> this is now needed even if not ybytes
      e=corpus_unistr.find(markupEnd,s)
      if e>-1:
        e += len(markupEnd)
        k = corpus_unistr[s:e]
        if k not in precalc_sets: precalc_sets[k]=set()
        precalc_sets[k].add(downLenSoFar)
    yPriorityDic = {}
    if ref_pri and ybytes:
      sys.stderr.write("yPriorityDic ... ")
      for s in re.finditer(re.escape(reference_sep+ref_pri+ref_name_end), corpus_unistr):
        s = s.start()+len(reference_sep+ref_pri+ref_name_end)
        e = corpus_unistr.find(reference_sep,s)
        if e==-1: e=len(corpus_unistr)
        for w in splitWords(corpus_unistr[s:e]):
          wd = markDown(w)
          if wd in yPriorityDic: continue
          if diagnose==wd: diagnose_write("yPriorityDic[%s] = %s" % (wd,w))
          yPriorityDic[wd] = w
    sys.stderr.write("done\n")
    if checkpoint: pickle.Pickler(open_try_bz2(checkpoint+os.sep+'map','wb'),-1).dump((m2c_map,precalc_sets,yPriorityDic))
    checkpoint_exit()

def setup_parallelism():
    if single_core or not checkpoint: return # parallelise only if checkpoint (otherwise could have trouble sharing the normalised corpus and map etc)
    args = commands.getoutput("ps -p " + str(os.getpid()) + " -o args")
    try:
      args.index("-m mpi4py.futures") # ValueError if not found
      import mpi4py.futures # mpi4py v2.1+
      import mpi4py.MPI, mpi4py ; assert mpi4py.MPI.COMM_WORLD.size > 1, "mpi4py says world size is 1: likely a symptom of incorrectly-configured MPI.  Did you compile mpi4py using the same setup (e.g. MPICH or OpenMPI) as you are running?  mpi4py's config is: "+repr(mpi4py.get_config())
      return mpi4py.futures.MPIPoolExecutor()
    except ValueError: pass # but raise all other exceptions: if we're being run within mpi4py.futures then we want to know about MPI problems
    try:
      args.index("-m scoop") # ValueError if not found
      import scoop.futures
      return scoop.futures # submit() is at module level
    except ValueError: pass
    try:
      import concurrent.futures # sudo pip install futures (2.7 backport of 3.2 standard library)
      import multiprocessing
      num_cpus = multiprocessing.cpu_count()
      if num_cpus > 1: return concurrent.futures.ProcessPoolExecutor(num_cpus-1) # leave one for the CPU-heavy control task
    except: pass

def get_phrases():
    # Returns a list of phrases in processing order, with length-numbers inserted in the list.  Caches its result.
    global _gp_cache
    try: return _gp_cache
    except: pass
    # Due to the way we handle overlaps, it's better to process the shortest phrases first, as the longer phrases will yield more rule options and therefore more likely to be able to work around any "no-overlap" constraints imposed by already-processed examples.  Something like:
    p2 = []
    for p in splitWords(corpus_unistr,phrases=True):
      p2.append((min([len(p.split(markupStart)),len(p.split(markupMid)),len(p.split(markupEnd))]),len(p2),p)) # no need for splitWords(phrase) just to get len, but we do need the min-of-3 for robustness against the occasional markup error
    p2.sort() # by length, then by original position (note: if removing this sort, remove wordsThisPhrase from status_update)
    phrases = [] ; wordLen = None
    for p in p2:
      if not wordLen == p[0]:
        wordLen = p[0]
        phrases.append(wordLen-1) # because it's a .split length (really want an actual count, but it only has to be roughly right in this instance and splitLen-1 will do for speed)
      phrases.append(p[-1])
    _gp_cache = phrases ; return phrases

def setup_other_globals():
    global corpus_markedDown
    corpus_markedDown = markDown(corpus_unistr)
    if ybytes:
        global markedUp_unichars
        if yarowsky_all: markedUp_unichars = None
        else: markedUp_unichars = set(list(u"".join(markDown(p) for p in get_phrases() if not type(p)==int)))
def check_globals_are_set_up(): # for use during parallelism
  global corpus_unistr
  try: corpus_unistr # if we fork()d, we may already have it
  except NameError:
    normalise() # should get corpus_unistr from checkpoint,
    try: corpus_unistr # unless we're NOT normalising,
    except: corpus_unistr = openfile(infile).read().decode(incode) # in which case we have to load the corpus from scratch (it won't be stdin)
    generate_map() # similarly this should just be a read
    setup_other_globals() # might do a bit more work, but probably faster than copying if we're not on the same machine

def analyse():
    accum = RulesAccumulator()
    covered = 0 # number of phrases we managed to 'cover' with our rules
    toCover = 0 # number of phrases we TRIED to cover (==covered if 100%)
    phraseNo = 0 ; wordLen = None
    if checkpoint:
      try: phraseNo,wordLen,covered,toCover,accum.__dict__ = read_checkpoint()
      except: pass
    phraseLastUpdate = phraseLastCheckpoint = phraseNo
    lastUpdate = lastCheckpoint = startTime = time.time()
    backgrounded = [] ; phrases = get_phrases()
    while phraseNo < len(phrases):
        if type(phrases[phraseNo])==int:
          wordLen = phrases[phraseNo]
          for b in backgrounded: # flush (TODO: duplicate code)
            coveredA,toCoverA = b.next()
            covered += coveredA ; toCover += toCoverA
          backgrounded = []
          phraseNo += 1 ; continue
        if toCover:
          if checkpoint and (checkpoint_exit(0) or time.time() >= lastCheckpoint + 1000): # TODO: configurable?
            sys.stderr.write("Checkpointing..."+clear_eol)
            for b in backgrounded: # flush (TODO: duplicate code)
              coveredA,toCoverA = b.next()
              covered += coveredA ; toCover += toCoverA
            backgrounded = []
            write_checkpoint((phraseNo,wordLen,covered,toCover,accum.__dict__))
            lastCheckpoint = time.time() ; phraseLastCheckpoint = phraseNo
          if time.time() >= lastUpdate + 2:
            status_update(phraseNo,len(phrases),wordLen,len(accum.rules),phraseLastUpdate,lastUpdate,phraseLastCheckpoint,lastCheckpoint,int(100.0*covered/toCover),len(accum.rejectedRules),startTime)
            lastUpdate = time.time() ; phraseLastUpdate = phraseNo
        aRules = accum.addRulesForPhrase(phrases[phraseNo],wordLen==1) # TODO: we're saying canBackground only if wordLen==1 because longer phrases can be backgrounded only if they're guaranteed not to have mutual effects; do we want to look into when we can do that?  (and update the help text for --single-core if changing)
        arr = aRules.next()
        if arr=="backgrounded": backgrounded.append(aRules)
        else:
          coveredA,toCoverA = arr
          covered += coveredA ; toCover += toCoverA
        phraseNo += 1
    for b in backgrounded: b.next() # flush
    del backgrounded
    if rulesFile: accum.save()
    if diagnose_manual: test_manual_rules()
    return sorted(accum.rulesAndConds()) # sorting it makes the order stable across Python implementations and insertion histories: useful for diff when using concurrency etc (can affect order of otherwise-equal Yarowsky-like comparisons in the generated code)

def read_manual_rules():
  if not manualrules: return
  for l in openfile(manualrules).xreadlines():
    if not l.strip(): continue
    l=l.decode(incode).strip() # TODO: manualrulescode ?
    if removeSpace: l=re.sub(re.escape(markupEnd)+r'\s+'+re.escape(markupStart),(markupEnd+markupStart).replace('\\',r'\\'),l)
    yield l

def test_manual_rules():
    for l in read_manual_rules():
      for s in re.finditer(re.escape(markupStart), l):
        # this loop is to prevent KeyError in getOkStarts
        s=s.start()
        e=l.find(markupEnd,s)
        if e>-1:
          e += len(markupEnd)
          k = l[s:e]
          if k not in precalc_sets: precalc_sets[k]=set()
      yb = []
      if not test_rule(l,yb).next() or len(yb):
        sys.stderr.write("\nWARNING: Manual rule '%s' may contradict the examples. " % (l.encode(terminal_charset),))
        global diagnose,diagnose_limit,ybytes
        od,odl,oy,diagnose,diagnose_limit,ybytes = diagnose,diagnose_limit,ybytes,markDown(l),0,ybytes_max
        test_rule(l,[]).next()
        diagnose,diagnose_limit,ybytes = od,odl,oy

def java_escape(unistr):
  ret = []
  for c in unistr:
    if c=='"': ret.append(r'\"')
    elif c=='\\': ret.append(r'\\')
    elif ord(' ') <= ord(c) <= 127: ret.append(c)
    elif c=='\n': ret.append(r'\n')
    else: ret.append('\u%04x' % ord(c))
  return ''.join(ret)

def golang_escape(unistr):
  return unistr.replace('\\','\\\\').replace('"','\\"').replace('\n',r'\n').encode(outcode)

def c_escape(unistr):
    # returns unistr encoded as outcode and escaped so can be put in C in "..."s
    return zapTrigraphs(unistr.encode(outcode).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','\\r')) # TODO: \r shouldn't occur, error if it does?
def zapTrigraphs(x): return re.sub(r"\?\?([=/'()<>!-])",r'?""?\1',x) # to get rid of trigraph warnings, TODO might get a marginal efficiency increase if do it to the entire C file at once instead)

def c_escapeRawBytes(s): # as it won't be valid outcode; don't want to crash any editors/viewers of the C file
  if s.endswith(chr(0)): s=s[:-1] # as the C compiler will add a terminating 0 anyway
  return re.sub(r"(?<!\\)((?:\\\\)*\\x..)([0-9a-fA-F])",r'\1""\2',zapTrigraphs(s.replace('\\','\\\\').decode('unicode_escape').encode('unicode_escape').replace('"','\\"')))

def js_escapeRawBytes(s):
  assert not zlib # js_utf8 etc not relevant if base64
  s = s.replace("\\",r"\\").replace('"',r'\"').replace(chr(8),r"\b").replace(chr(9),r"\t").replace(chr(10),r"\n").replace(chr(12),r"\f").replace(chr(13),r"\r")
  if ignore_ie8: s = s.replace(chr(11),r"\v")
  if js_octal: s = re.sub("[\x00-\x1f](?![0-9])",lambda m:r"\%o"%ord(m.group()),s)
  else: s = re.sub(chr(0)+r"(?![0-9])",r"\\0",s) # \0 is allowed even if not js_octal (and we need \\ because we're in a regexp replacement)
  if js_utf8: return re.sub("[\x00-\x1f\x7f]",lambda m:r"\x%02x"%ord(m.group()),s.encode('utf-8'))
  else: return re.sub("[\x00-\x1f\x7f-\xff]",lambda m:r"\x%02x"%ord(m.group()),s)

def c_length(unistr): return len(unistr.encode(outcode))

if (java and not ndk) or c_sharp or golang:
  if golang: outLang_escape = golang_escape
  else: outLang_escape = java_escape
  if java: outLang_bool = "boolean"
  else: outLang_bool = "bool"
  outLang_true = "true"
  outLang_false = "false"
else:
  outLang_escape = c_escape
  outLang_bool = "int"
  outLang_true = "1"
  outLang_false = "0"

def allVars(u):
  global cjk_cLookup
  try: cjk_cLookup
  except NameError:
    sys.stderr.write("(checking CJK closures for missing glosses)\n")
    from cjklib.characterlookup import CharacterLookup
    cjk_cLookup = CharacterLookup("C") # param doesn't matter for getCharacterVariants, so just put "C" for now
    cjk_cLookup.varCache = {} # because getCharacterVariants can be slow if it uses SQL queries
  def lookupVar(u,t):
    if (u,t) not in cjk_cLookup.varCache: cjk_cLookup.varCache[(u,t)] = cjk_cLookup.getCharacterVariants(u,t)
    return cjk_cLookup.varCache[(u,t)]
  done = set([u])
  for t in "STCMZ":
    for var in lookupVar(u,t):
      if not var in done: yield var
      done.add(var)
      # In at least some versions of the data, U+63B3 needs to go via T (U+64C4) and M (U+865C) and S to get to U+864F (instead of having a direct M variant to 864F), so we need to take (S/T)/M/(S/T) variants also:
      if t in "ST":
        for var in lookupVar(var,'M'):
          if var in done: continue
          yield var ; done.add(var)
          for t2 in "ST":
            for var in lookupVar(var,t2):
              if var in done: continue
              yield var ; done.add(var)

def allVarsW(unistr):
  vRest = []
  for i in xrange(len(unistr)):
    got_vRest = False
    for v in allVars(unistr[i]):
      yield unistr[:i]+v+unistr[i+1:]
      if got_vRest:
        for vr in vRest: yield unistr[:i]+v+vr
      else:
        vRest = [] ; got_vRest = True
        for vr in allVarsW(unistr[i+1:]):
          yield unistr[:i]+v+vr ; vRest.append(vr)

def matchingAction(rule,glossDic,glossMiss,whitelist):
  # called by addRule, returns (actionList, did-we-actually-annotate).  Also applies reannotator and compression (both of which will require 2 passes if present)
  action = []
  gotAnnot = False
  for w in splitWords(rule):
    wStart = w.index(markupStart)+len(markupStart)
    wEnd = w.index(markupMid,wStart)
    text_unistr = w[wStart:wEnd]
    mStart = wEnd+len(markupMid)
    annotation_unistr = w[mStart:w.index(markupEnd,mStart)]
    if mreverse: text_unistr,annotation_unistr = annotation_unistr,text_unistr
    if whitelist and not text_unistr in whitelist:
      return text_unistr+" not whitelisted",None
    gloss = glossDic.get((text_unistr,annotation_unistr),glossDic.get(text_unistr,None))
    if gloss_closure and not gloss and not w in glossMiss:
      for t2 in allVarsW(text_unistr):
        gloss = glossDic.get((t2,annotation_unistr),glossDic.get(t2,None))
        if gloss:
          glossDic[text_unistr] = gloss ; break
    if gloss: gloss = gloss.replace('&','&amp;').replace('"','&quot;').replace('\n','&#10;') # because it'll be in a title= attribute
    if reannotator:
      if reannotator.startswith('##'): toAdd = text_unistr + '#' + annotation_unistr
      elif reannotator[0]=='#': toAdd=annotation_unistr
      else: toAdd = text_unistr
      if toAdd in reannotateDict: annotation_unistr = reannotateDict[toAdd]
      else: toReannotateSet.add(toAdd)
    if compress:
      annotation_bytes0=annotation_unistr.encode(outcode)
      annotation_bytes = squash(annotation_bytes0)
      if gloss:
        gloss_bytes0 = gloss.encode(outcode)
        gloss_bytes = squash(gloss_bytes0)
      else: gloss_bytes0 = gloss_bytes = None
      if not data_driven:
        if annotation_bytes == annotation_bytes0: annotation_bytes = outLang_escape(annotation_unistr) # (if compress didn't do anything, might as well write a readable string to the C)
        else: annotation_bytes = c_escapeRawBytes(annotation_bytes)
        if gloss and gloss_bytes == gloss_bytes0: gloss_bytes = outLang_escape(gloss)
        elif gloss_bytes: gloss_bytes = c_escapeRawBytes(gloss_bytes)
    elif data_driven: # data-driven w. no compression:
      annotation_bytes = annotation_unistr.encode(outcode)
      if gloss: gloss_bytes = gloss.encode(outcode)
      else: gloss_bytes = None
    else: # non data-driven, no compression:
      annotation_bytes = outLang_escape(annotation_unistr)
      if gloss: gloss_bytes = outLang_escape(gloss)
      else: gloss_bytes = None
    if java: adot = "a." # not used if data_driven
    else: adot = ""
    bytesToCopy = c_length(text_unistr)
    if gloss:
        if data_driven: action.append((bytesToCopy,annotation_bytes,gloss_bytes))
        else: action.append(adot+'o2(%d,"%s","%s");' % (bytesToCopy,annotation_bytes,gloss_bytes))
    else:
        glossMiss.add(w)
        if data_driven: action.append((bytesToCopy,annotation_bytes))
        else: action.append(adot+'o(%d,"%s");' % (bytesToCopy,annotation_bytes))
    if annotation_unistr or gloss: gotAnnot = True
  return action,gotAnnot

def outputParser(rulesAndConds):
    sys.stderr.write("Generating byte cases...\n")
    glossDic = {} ; glossMiss = set() ; whitelist = set()
    if glossfile:
        for l in openfile(glossfile).xreadlines():
            if not l.strip(): continue
            l=l.decode(incode,errors='replace') # TODO: glosscode ? (errors=replace because we said it's not necessary to completely debug glossfile; we don't want this to be brought down by one bad UTF8 sequence or whatever)
            try: word,annot,gloss = l.split("\t",2)
            except: # not enough tabs
              word = l.split("\t",1)[0] ; annot = gloss = ""
              if glossmiss_omit: pass # they can list words without glosses; no error if missing \t
              else: sys.stderr.write("Gloss: Ignoring incorrectly-formatted line "+l.strip()+"\n")
            word,annot,gloss = word.strip(),annot.strip(),gloss.strip().replace("\t","\n")
            if glossmiss_omit and word: whitelist.add(word)
            if not word or not gloss: continue
            if annot: glossDic[(word,annot)] = gloss
            else: glossDic[word] = gloss
    byteSeq_to_action_dict = {}
    if ignoreNewlines:
        if data_driven: newline_action = [(1,)]
        elif java and not ndk: newline_action = r"a.o((byte)'\n'); /* needSpace unchanged */ a.writePtr++;"
        elif c_sharp: newline_action = r"o((byte)'\n'); writePtr++;"
        elif golang: newline_action = r"oB('\n'); writePtr++;"
        else: newline_action = r"OutWriteByte('\n'); /* needSpace unchanged */ COPY_BYTE_SKIP;"
        byteSeq_to_action_dict['\n'] = [(newline_action,[])]
    def addRule(rule,conds,byteSeq_to_action_dict,manualOverride=False):
        byteSeq = markDown(rule).encode(outcode)
        action,gotAnnot = matchingAction(rule,glossDic,glossMiss,whitelist)
        if not gotAnnot: return # not whitelisted, or some spurious o("{","") rule that got in due to markup corruption
        if manualOverride or not byteSeq in byteSeq_to_action_dict: byteSeq_to_action_dict[byteSeq] = []
        if not data_driven: action = ' '.join(action)
        byteSeq_to_action_dict[byteSeq].append((action,conds))
    def dryRun(clearReannotator=True): # to prime the reannotator or compressor
      global toReannotateSet, reannotateDict
      toReannotateSet = set()
      if clearReannotator: reannotateDict = {} # (not if we've run the reannotator and are just doing it for the compressor)
      dummyDict = {}
      for rule,conds in rulesAndConds: addRule(rule,conds,dummyDict)
      for l in read_manual_rules(): addRule(l,[],dummyDict)
    if reannotator:
      sys.stderr.write("Reannotating... ")
      dryRun()
      # Setting buffer size is not enough on all systems.
      # To ensure the pipe does not fill its output while
      # we are still writing its input, we use threads and
      # don't start writing its input until we've already
      # started reading from its output.
      global toReannotateSet, reannotateDict
      l = [ll for ll in toReannotateSet if ll and not "\n" in ll] # TODO: handle the case where "\n" is in ll?  (shouldn't happen in 'sensible' annotators)
      def reader_thread():
        global threadReading,threadRead
        threadReading = True
        threadRead = cout.read().decode(outcode).splitlines() # TODO: reannotatorCode instead of outcode?
      if reannotator.startswith('##'): cmd=reannotator[2:]
      elif reannotator[0]=='#': cmd=reannotator[1:]
      else: cmd = reannotator
      import thread ; sys.setcheckinterval(100)
      global cout ; cin,cout = os.popen2(cmd)
      global threadReading,threadRead ; threadReading=threadRead=False
      thread.start_new_thread(reader_thread,())
      while threadReading == False: time.sleep(0.1)
      # NOW ready to start writing:
      cin.write("\n".join(l).encode(outcode)+"\n") ; cin.close() # TODO: reannotatorCode instead of outcode?
      while threadRead == False: time.sleep(1)
      l2 = threadRead
      sys.setcheckinterval(32767)
      del cin,cout,cmd,threadRead
      while len(l2)>len(l) and not l2[-1]: del l2[-1] # don't mind extra blank line(s) at end of output
      if not len(l)==len(l2):
        open('reannotator-debug-in.txt','w').write("\n".join(l).encode(outcode)+"\n")
        open('reannotator-debug-out.txt','w').write("\n".join(l2).encode(outcode)+"\n")
        errExit("Reannotator command didn't output the same number of lines as we gave it (gave %d, got %d).  Input and output have been written to reannotator-debug-in.txt and reannotator-debug-out.txt for inspection.  Bailing out." % (len(l),len(l2)))
      sys.stderr.write("(%d items)\n" % len(l))
      toReannotateSet = set() ; reannotateDict = dict(zip(l,l2)) ; del l,l2
    if compress:
      global squashStrings ; squashStrings = set() # discard any that were made in any reannotator dry-run
      dryRun(False) # redo with the new annotation strings (or do for the first time if no reannotator)
      pairs = squashFinish()
    else: pairs = ""
    for rule,conds in rulesAndConds: addRule(rule,conds,byteSeq_to_action_dict)
    for l in read_manual_rules(): addRule(l,[],byteSeq_to_action_dict,True)
    write_glossMiss(glossMiss)
    longest_rule_len = max(len(b) for b in byteSeq_to_action_dict.iterkeys())
    longest_rule_len += ybytes_max # because buffer len is 2*longest_rule_len, we shift half of it when (readPtr-bufStart +ybytes >= bufLen) and we don't want this shift to happen when writePtr-bufStart = Half_Bufsize-1 and readPtr = writePtr + Half_Bufsize-1 (TODO: could we get away with max(0,ybytes_max-1) instead? but check how this interacts with the line below; things should be safe as they are now).  This line's correction was missing in Annogen v0.599 and below, which could therefore occasionally emit code that, when running from stdin, occasionally replaced one of the document's bytes with an undefined byte (usually 0) while emitting correct annotation for the original byte.  (This could result in bad UTF-8 that crashed the bookmarklet feature of Web Adjuster v0.21 and below.)
    longest_rule_len = max(ybytes_max*2, longest_rule_len) # make sure the half-bufsize is at least ybytes_max*2, so that a read-ahead when pos is ybytes_max from the end, resulting in a shift back to the 1st half of the buffer, will still leave ybytes_max from the beginning, so yar() can look ybytes_max-wide in both directions
    if data_driven:
      b = BytecodeAssembler()
      b.addActionDictSwitch(byteSeq_to_action_dict,False)
      ddrivn = b.link()
      if zlib: origLen = b.origLen
      del b
    else: ddrivn = None
    if javascript:
      if zlib:
        import base64
        return outfile.write(js_start+"data: inflate(\""+base64.b64encode(ddrivn)+"\","+str(origLen)+"),\n"+re.sub(r"data\.charCodeAt\(([^)]*)\)",r"data[\1]",js_end).replace("indexOf(input.charAt","indexOf(input.charCodeAt")+"\n")
      else: return outfile.write(js_start+"data: \""+js_escapeRawBytes(ddrivn)+"\",\n"+js_end+"\n") # not Uint8Array (even if browser compatibility is known): besides taking more source space, it's typically ~25% slower to load than string, even from RAM
    elif python:
      outfile.write(py_start+"\ndata="+repr(ddrivn)+"\n")
      if zlib: outfile.write("import zlib; data=zlib.decompress(data)\n")
      return outfile.write(py_end+"\n")
    elif java and not ndk:
      start = java_src.replace("%%JPACKAGE%%",jPackage)
      if data_driven:
        a = android_loadData.replace("%%DLEN%%",str(len(ddrivn)))
        if zlib: a = a.replace("%%ULEN%%",str(origLen))
        start = start.replace("() { %%JDATA%% }","(android.content.Context context) throws java.io.IOException { "+a+" }") # Annotator c'tor needs a context argument if it's data-driven, to load annotate.dat
        if zlib: start = start.replace("context) throws java.io.IOException {","context) throws java.io.IOException,java.util.zip.DataFormatException {")
      else: start = start.replace("%%JDATA%%","")
    elif c_sharp: start = cSharp_start
    elif golang: start = golang_start
    else: start = c_start
    outfile.write(start.replace('%%LONGEST_RULE_LEN%%',str(longest_rule_len)).replace("%%YBYTES%%",str(ybytes_max)).replace("%%PAIRS%%",pairs)+"\n")
    if data_driven:
      if zlib: dataName = "origData"
      else: dataName = "data"
      if java: open(jSrc+"/../assets/annotate.dat","wb").write(ddrivn)
      else:
        outfile.write("static unsigned char "+dataName+"[]=\""+c_escapeRawBytes(ddrivn)+'\";\n')
        if zlib: outfile.write(c_zlib.replace('%%ORIGLEN%%',str(origLen)).replace('%%ZLIBLEN%%',str(len(ddrivn)))+"\n") # rather than using sizeof() because we might or might not want to include the compiler's terminating nul byte
        outfile.write(c_datadrive+"\n")
      del ddrivn
    else: # not data_driven
      subFuncL = []
      ret = stringSwitch(byteSeq_to_action_dict,subFuncL)
      if java and not ndk:
        for f in subFuncL: open(java+os.sep+f[f.index("class ")+6:].split(None,1)[0]+".java","w").write(f)
        open(java+os.sep+"topLevelMatch.java","w").write("\n".join(ret))
      elif golang: outfile.write("\n".join(subFuncL + ret).replace(';\n','\n')+"\n") # (this 'elif' line is not really necessary but it might save someone getting worried about too many semicolons)
      else: outfile.write("\n".join(subFuncL+ret)+"\n")
      del subFuncL,ret
    if android:
      open(java+os.sep+"MainActivity.java","w").write(android_src.replace("%%JPACKAGE%%",jPackage).replace('%%ANDROID-URL%%',android))
      open(java+os.sep+"BringToFront.java","w").write(android_bringToFront.replace("%%JPACKAGE%%",jPackage))
      open(jSrc+"/../assets/clipboard.html",'w').write(android_clipboard)
      try: manifest = open(jSrc+"/../AndroidManifest.xml").read() # keep existing version codes (don't replace with 1 and 1.0) and existing targetSdkVersion, but do update android_urls (below)
      except IOError: manifest = android_manifest # first AndroidManifest.xml
      def pathQ(x):
        x = urlparse.urlparse(x)
        if x.query: return x.path+"?"+x.query
        else: return x.path
      new_manifest = "\n".join(l for l in manifest.split("\n") if l and not '<intent-filter><action android:name="android.intent.action.VIEW" /><category android:name="android.intent.category.DEFAULT" /><category android:name="android.intent.category.BROWSABLE" /><data android:scheme="' in l and not l=="</activity></application></manifest>") + ''.join(('\n<intent-filter><action android:name="android.intent.action.VIEW" /><category android:name="android.intent.category.DEFAULT" /><category android:name="android.intent.category.BROWSABLE" /><data android:scheme="%s" android:host="%s" android:pathPrefix="%s" /></intent-filter>'%(urlparse.urlparse(x).scheme,urlparse.urlparse(x).netloc,pathQ(x))) for x in android_urls.split()) + "\n</activity></application></manifest>\n"
      if not manifest==new_manifest:
        open(jSrc+"/../AndroidManifest.xml","w").write(new_manifest)
      if ndk:
        outfile.write(c_end)
        o=open(jSrc+"/../jni/Android.mk",'w')
        if zlib: o.write("LOCAL_LDLIBS := -lz\n")
        o.write("""LOCAL_PATH:= $(call my-dir)
LOCAL_SRC_FILES := annotator.c
LOCAL_MODULE := Annotator
LOCAL_MODULE_FILENAME := Annotator
include $(BUILD_SHARED_LIBRARY)
""")
        o.close()
        open(jSrc+"/../jni/Application.mk",'w').write("APP_PLATFORM := android-"+android_minSdkVersion+"\nAPP_ABI := "+armabi+"\n")
      open(jSrc+"/../res/layout/activity_main.xml","w").write(android_layout)
      open(jSrc+"/../res/menu/main.xml","w").write('<menu xmlns:android="http://schemas.android.com/apk/res/android" ></menu>\n') # TODO: is this file even needed at all?
      open(jSrc+"/../res/values/dimens.xml","w").write('<resources><dimen name="activity_horizontal_margin">16dp</dimen><dimen name="activity_vertical_margin">16dp</dimen></resources>\n')
      open(jSrc+"/../res/values/styles.xml","w").write('<resources><style name="AppBaseTheme" parent="android:Theme.Light"></style><style name="AppTheme" parent="AppBaseTheme"></style></resources>\n')
      open(jSrc+"/../res/values/strings.xml","w").write('<?xml version="1.0" encoding="utf-8"?>\n<resources><string name="app_name">'+app_name+'</string></resources>\n')
    elif c_sharp: outfile.write(cSharp_end)
    elif golang: outfile.write(golang_end)
    elif not java: outfile.write(c_end)
    outfile.write("\n")
    del byteSeq_to_action_dict
    if no_summary or not rulesAndConds: return
    if reannotator:
        outfile.write("\n/* Tab-delimited rules summary not yet implemented with reannotator option */\n")
        return
    outfile.write("\n/* Tab-delimited summary of the rules: (total %d)\n" % len(rulesAndConds))
    outputRulesSummary(rulesAndConds)
    outfile.write("*/\n")

def write_glossMiss(glossMiss):
  if not glossmiss: return
  sys.stderr.write("Writing glossmiss (norefs=%s) to %s...\n" % (repr(norefs),glossmiss))
  gm = openfile(glossmiss,'wb')
  count = 1 ; t = time.time() ; prndProg=False
  for w in sorted(list(glossMiss)):
    try: num = str(len(getOkStarts(w)))+'\t'
    except: num = '?\t' # num occurrences in e.g.s
    a,b,r = markDown(w),annotationOnly(w),refs(w,glossmiss_hide)
    if a and b and not r=="\t": gm.write((num+a+"\t"+b+r+'\n').encode(incode)) # TODO: glosscode ? glossMissCode ??
    if time.time() >= t + 2:
      sys.stderr.write(("(%d of %d)" % (count,len(glossMiss)))+clear_eol)
      t = time.time() ; prndProg = True
    count += 1
  if prndProg: sys.stderr.write("done"+clear_eol+"\n")

if norefs:
  def refs(rule,omit={}): return ""
else:
  def refs(rule,omit={}):
    global refMap
    try: refMap
    except:
      refMap = [(m.end(),m.group(1)) for m in re.finditer(re.escape(reference_sep)+"(.*?)"+re.escape(ref_name_end), corpus_unistr, flags=re.DOTALL)]
      i = 0
      while True:
        if i+1 >= len(refMap): break
        if refMap[i][1] == refMap[i+1][1]: del refMap[i+1]
        else: i += 1
    rmPos = 0 ; ret = []
    try: okStarts = getOkStarts(rule)
    except: return "" # KeyError can happen in some incremental-run glossMiss situations: just omit that reference in the debug file
    while len(ret) < maxrefs and rmPos < len(refMap):
      s = refMap[rmPos][0] ; i = -1
      while i < s and okStarts:
        i = min(okStarts) ; okStarts.remove(i)
        i = m2c_map[i]
      if i < s: break
      rmE = len(refMap)-1
      while refMap[rmE][0] > i:
        mid = int((rmPos+rmE)/2)
        if mid==rmPos or refMap[mid][0] > i: rmE = mid
        else: rmPos = mid
      rmPos = rmE
      app=refMap[rmPos][1]
      if not app in ret: ret.append(app)
      rmPos += 1
    if ret: return "\t"+"; ".join(r for r in ret if not r in omit) # (if all in omit, still return the \t to indicate we did find some)
    else: return ""

def outputRulesSummary(rulesAndConds):
    # (summary because we don't here specify which part
    # of the annotation goes with which part of the text, plus
    # we remove /* and */ so it can be placed into a C comment)
    sys.stderr.write("Writing rules summary...\n")
    if summary_omit: omit=set(openfile(summary_omit).read().splitlines())
    else: omit=[]
    count = 1 ; t = time.time()
    # If incremental or manualrules, some rules might now have been overridden by newer ones.  Rules listed later take priority in byteSeq_to_action_dict.  This should remove earlier duplicate (markedDown,conds) combinations from the summary:
    d = {}
    for r,c in rulesAndConds:
      d[(markDown(r),repr(c))] = (r,c)
    # Now sort so diff is possible between 2 summaries:
    d = sorted((annotationOnly(r),markDown(r),r,c) for r,c in d.values())
    # Can now do the summary:
    for annot,orig,rule,conditions in d:
        if time.time() >= t + 2:
          sys.stderr.write(("(%d of %d)" % (count,len(rulesAndConds)))+clear_eol)
          t = time.time()
        count += 1
        def code(x):
          if not x.strip(): return repr(x)
          else: return x.encode(outcode).replace('\n',r'\n').replace('\t',r'\t')
        toPrn = code(orig)+"\t"+code(annot)
        if ybytes:
            toPrn += "\t"
            if conditions:
                if type(conditions)==tuple:
                  negate,conds,nbytes = conditions[:3]
                  if negate: negate=" not"
                  else: negate=""
                  toPrn += "if"+negate+" within "+str(nbytes)+" bytes of "+" or ".join(code(c) for c in conds)
                else: toPrn += "if near "+" or ".join(code(c) for c in conditions)
        if not toPrn in omit: outfile.write((toPrn+refs(rule).encode(outcode)).replace('/*','').replace('*/','')+"\n")
    if ybytes: extraTab='\t'
    else: extraTab = ''
    for l in read_manual_rules(): outfile.write((markDown(l)+'\t'+annotationOnly(l)+extraTab+'\t--manualrules '+manualrules).encode(outcode)+"\n")
    sys.stderr.write("done"+clear_eol+"\n")

if isatty(sys.stdout):
    if summary_only:
        warn("Rules summary will be written to STANDARD OUTPUT\nYou might want to redirect it to a file or a pager such as 'less'")
        c_filename = None
    elif not java and main: sys.stderr.write("Writing to "+c_filename+"\n") # will open it later (avoid having a 0-length file sitting around during the analyse() run so you don't rm it by mistake)

def openfile(fname,mode='r'):
    lzma = bz2 = None
    if fname.endswith(".xz"): import lzma # 'pip install lzma' or 'apt-get install python2.7-lzma' may be required for .xz files
    elif fname.endswith(".bz2"): import bz2
    if re.match("https?://",fname):
        assert mode=='r', "cannot write to "+fname
        import urllib2
        sys.stderr.write("Fetching "+fname+"\n")
        fileobj = urllib2.urlopen(fname)
        # If it's bz2 or xz, we'd better decompress in one operation.  (gz library can stream)
        if fname.endswith(".bz2"):
            from cStringIO import StringIO
            return StringIO(bz2.decompress(fileobj.read()))
        elif fname.endswith(".xz"):
            from cStringIO import StringIO
            return StringIO(lzma.decompress(fileobj.read()))
    elif fname.endswith(".bz2"):
        return bz2.BZ2File(fname,mode)
    elif fname.endswith(".xz"):
        return lzma.LZMAFile(fname,mode)
    else: fileobj = open(fname,mode)
    # if get this far, we can use fileobj
    if fname.endswith(".gz"):
        import gzip ; return gzip.GzipFile(fileobj=fileobj,mode=mode)
    else: return fileobj
def open_try_bz2(fname,mode='r'): # use .bz2 iff available (for checkpoints)
  try: return openfile(fname+".bz2",mode)
  except: return openfile(fname,mode)
def rm_f(fname):
  try: os.remove(fname)
  except OSError: pass

import atexit
def set_title(t):
  if not isatty(sys.stderr): return
  if t: atexit.register(set_title,"")
  is_screen = (term=="screen" and os.environ.get("STY",""))
  is_tmux = (term=="screen" and os.environ.get("TMUX",""))
  if is_xterm or is_tmux: sys.stderr.write("\033]0;%s\007" % (t,)) # ("0;" sets both title and minimised title, "1;" sets minimised title, "2;" sets title.  Tmux takes its pane title from title (but doesn't display it in the titlebar))
  elif is_screen: os.system("screen -X title \"%s\"" % (t,))
def diagnose_write(s): sys.stderr.write(bold_on+"Diagnose: "+bold_off+s.encode(terminal_charset,'replace')+'\n')
try: screenWidth = int(os.environ['COLUMNS'])
except:
  import struct, fcntl, termios
  try: screenWidth = struct.unpack('hh',fcntl.ioctl(sys.stderr,termios.TIOCGWINSZ,'xxxx'))[1]
  except: screenWidth = 45 # conservative

if main and not compile_only:
 set_title("annogen")
 if checkpoint:
  try: os.mkdir(checkpoint)
  except: pass
 if no_input:
   rulesAndConds = RulesAccumulator().rulesAndConds() # should load rulesFile
 if read_input:
  if infile: infile=openfile(infile)
  else:
    infile = sys.stdin
    if isatty(infile): sys.stderr.write("Reading from standard input\n(If that's not what you wanted, press Ctrl-C and run again with --help)\n")
  corpus_unistr = infile.read().decode(incode)
  if diagnose and not diagnose in corpus_unistr:
    diagnose_write(diagnose+" is not present in the corpus, even before normalisation")
    suppress = True
  else: suppress = False
  normalise()
  if diagnose and not suppress and not diagnose in corpus_unistr: diagnose_write(diagnose+" was in the corpus before normalisation, but not after") # (if running from a checkpoint, might want to rm normalised and redo the diagnose)
  generate_map() ; setup_other_globals()
  if not no_input:
    executor = setup_parallelism()
    if executor and capitalisation and annot_whitespace and infile==sys.stdin: open_try_bz2(checkpoint+os.sep+'normalised','wb').write(corpus_unistr.encode('utf-8')) # normalise won't have done it and the other nodes will need it (TODO: unless we're doing concurrent.futures with fork)
    try: rulesAndConds = analyse()
    finally: sys.stderr.write("\n") # so status line is not overwritten by 1st part of traceback on interrupt etc
  del _gp_cache

def cmd_or_exit(cmd):
  sys.stderr.write(cmd+"\n")
  r = os.system(cmd)
  if not r: return
  if r&0xFF == 0: r >>= 8 # POSIX
  sys.exit(r)

if main and not compile_only:
 if c_filename: outfile = openfile(c_filename,"w")
 else: outfile = sys.stdout
 if summary_only: outputRulesSummary(rulesAndConds)
 else: outputParser(rulesAndConds)
 del rulesAndConds
 outfile.close() ; sys.stderr.write("Output complete\n")
if main:
 if android:
   if all(x in os.environ for x in ["SDK","PLATFORM","BUILD_TOOLS"]):
     os.chdir(jSrc+"/..")
     if ndk:
       if "NDK" in os.environ:
         cmd_or_exit("$NDK/ndk-build")
       elif os.path.exists(os.environ["SDK"]+"ndk-bundle"): cmd_or_exit("$SDK/ndk-bundle/ndk-build")
       else: cmd_or_exit("ndk-build") # need it on PATH
       os.system("mv -f libs/"+armabi+"/Annotator.so libs/"+armabi+"/libAnnotator.so >/dev/null 2>/dev/null")
     cmd_or_exit("$BUILD_TOOLS/aapt package -v -f -I $PLATFORM/android.jar -M AndroidManifest.xml -A assets -S res -m -J gen -F bin/resources.ap_")
     if ndk: cmd_or_exit("javac -classpath $PLATFORM/android.jar -sourcepath 'src;gen' -d bin src/"+jRest+"/*.java gen/"+jRest+"/R.java")
     else: cmd_or_exit("find src/"+jRest+" -name '*.java' > argfile && javac -classpath $PLATFORM/android.jar -sourcepath 'src;gen' -d bin gen/"+jRest+"/R.java @argfile && rm argfile") # as *.java likely too long
     if "min-sdk-version" in commands.getoutput("$BUILD_TOOLS/dx --help"): a=" --min-sdk-version=1"
     else: a = "" # older versions of dx don't have that flag
     if not ndk: a = " -JXmx4g --force-jumbo" + a # -J option must go first
     cmd_or_exit("$BUILD_TOOLS/dx"+a+" --dex --output=bin/classes.dex bin/")
     dirName0 = commands.getoutput("pwd|sed -e s,.*./,,")
     dirName = shell_escape(dirName0)
     cmd_or_exit("cp bin/resources.ap_ bin/"+dirName+".ap_")
     if ndk: a,b = "rsync -trv ../libs/"+armabi+" lib/ && "," lib/"+armabi+"/*.so"
     else: a,b = "",""
     cmd_or_exit("cd bin && "+a+"$BUILD_TOOLS/aapt add "+dirName+".ap_ classes.dex"+b)
     if all(x in os.environ for x in ["KEYSTORE_FILE","KEYSTORE_USER","KEYSTORE_PASS"]): cmd_or_exit("jarsigner -sigalg SHA1withRSA -digestalg SHA1 -keystore \"$KEYSTORE_FILE\" -storepass \"$KEYSTORE_PASS\" -keypass \"$KEYSTORE_PASS\" -signedjar bin/"+dirName+".apk bin/"+dirName+".ap_ \"$KEYSTORE_USER\" -tsa http://timestamp.digicert.com") # TODO: -tsa option requires an Internet connection; option to omit it if the key expiry date is far enough in the future?
     else: cmd_or_exit("mv bin/"+dirName+".ap_ bin/"+dirName+".apk") # just use the .ap_ if debug build
     rm_f("../"+dirName0+".apk") ; cmd_or_exit("$BUILD_TOOLS/zipalign 4 bin/"+dirName+".apk ../"+dirName+".apk")
     rm_f("bin/"+dirName0+".ap_")
     rm_f("bin/"+dirName0+".apk")
     cmd_or_exit("du -h ../"+dirName+".apk")
   else: sys.stderr.write("Android source has been written to "+jSrc[:-3]+"""
(You might need to change targetSdkVersion in AndroidManifest.xml if
   your SDK insists on a different target version)
To have Annogen build it for you, set these environment variables
before the Annogen run (change the examples obviously) :
   export SDK=/home/example/Android/Sdk
   export NDK=/usr/local/android-ndk-r10c # if using --ndk and it's not in $SDK/ndk-bundle or on PATH
   export PLATFORM=$SDK/platforms/android-19
   export BUILD_TOOLS=$SDK/build-tools/21.0.2
   export KEYSTORE_FILE=/path/to/keystore
   export KEYSTORE_USER='your user name'
   export KEYSTORE_PASS='your password'
   # (if the KEYSTORE variables are unset, you'll get a 'debug' build)

You may also wish to create some icons in res/drawable*
   (using Android Studio or the earlier ADT tools)
""")
 elif c_filename and c_compiler:
    cmd = c_compiler # should include any -o option
    if zlib: cmd += " -lz" # TODO: is this always correct on all platforms? (although user can always simply redirect the C to a file and compile separately)
    cmd_or_exit(cmd + " " + shell_escape(c_filename))
 elif compile_only: errExit("Don't know what compiler to run for this set of options")
