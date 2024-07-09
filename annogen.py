#!/usr/bin/env python
# (compatible with both Python 2.7 and Python 3)

"Annotator Generator v3.383 (c) 2012-24 Silas S. Brown"

# See http://ssb22.user.srcf.net/adjuster/annogen.html

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
# and at https://gitlab.developers.cam.ac.uk/ssb22/adjuster
# and in China: https://gitee.com/ssb22/adjuster
# although some early ones are missing.

import sys,os,os.path,tempfile,time,re,subprocess,unicodedata
import json,codecs
from optparse import OptionParser
if '--html-options' in sys.argv:
  print ("Usage: annogen.py [options]<p>Options:<dl>")
  class HTMLOptions:
    def add_option(self,*args,**kwargs):
      if not 'action' in kwargs: args=[a+'=' if a.startswith('--') else a for a in args]
      print ("<dt><kbd>"+"</kbd>, <kbd>".join(args)+"</kbd></dt><dd>"+re.sub('(?<=[A-Za-z])([/=_])(?=[A-Za-z])',r'<wbr/>\1',re.sub('(--[A-Za-z-]*)',r'<kbd>\1</kbd>',kwargs.get("help","").replace("%default",str(kwargs.get("default","%default"))).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))).replace("BEFORE","<strong>before</strong>").replace("AFTER","<strong>after</strong>").replace("ALWAYS","<strong>always</strong>").replace(" ALL "," <strong>all</strong> ").replace(" LONG "," <strong>long</strong> ").replace(" NOT "," <strong>not</strong> ").replace("WITHOUT","<strong>without</strong>").replace("js:search:replace,","js:<wbr>search:<wbr>replace,<wbr>")+"</dd>")
  parser = HTMLOptions()
  parser.add_option("-h","--help",action=True,help="show this help message and exit")
elif '--markdown-options' in sys.argv:
  l = "Options for "+__doc__[:__doc__.index("(c)")].strip()
  print (l) ; print ("="*len(l)) ; print ("")
  class MarkdownOptions:
    def add_option(self,*args,**kwargs):
      if not 'action' in kwargs: args=[a+'=' if a.startswith('--') else a for a in args]
      d = str(kwargs.get("default","%default"))
      if "://" in d or "<" in d: d="`"+d+"`"
      print ("`"+"`, `".join(args)+"`\n : "+re.sub('(--[A-Za-z-]*)',r'`\1`',kwargs.get("help","").replace("%default",d)).replace("BEFORE","**before**").replace("AFTER","**after**").replace("ALWAYS","**always**").replace(" ALL "," **all** ").replace(" LONG "," **long** ").replace(" NOT "," **not** ").replace("WITHOUT","**without**")+"\n")
  parser = MarkdownOptions()
  parser.add_option("-h","--help",action=True,help="show this help message and exit")
else: parser = OptionParser()
try: from subprocess import getoutput
except: from commands import getoutput
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

parser.add_option("--end-pri",
                  help="Treat words that occur in the examples before this delimeter as having \"high priority\" for Yarowsky-like seed collocations (if these are in use).  Normally the Yarowsky-like logic tries to identify a \"default\" annotation based on what is most common in the examples, with the exceptions indicated by collocations.  If however a word is found in a high-priority section at the start, then the first annotation found there will be taken as the ideal \"default\" even if it's in a minority in the examples; everything else will be taken as an exception.")

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

parser.add_option("--suffix",
                  help="Comma-separated list of annotations that can be considered optional suffixes for normalisation") # e.g. use --suffix=r if you have Mandarin Pinyin with inconsistent -r additions
parser.add_option("--suffix-minlen",
                  default=1,
                  help="Minimum length of word (in Unicode characters) to apply suffix normalisation")

parser.add_option("--post-normalise",
                  help="Filename of an optional Python module defining a dictionary called 'table' mapping integers to integers for arbitrary single-character normalisation on the Unicode BMP.  This can reduce the size of the annotator.  It is applied in post-processing (does not affect rules generation itself).  For example this can be used to merge the recognition of Full, Simplified and Variant forms of the same Chinese character in cases where this can be done without ambiguity, if it is acceptable for the generated annotator to recognise mixed-script words should they occur.  If any word in the examples has a different annotation when normalised than not, the normalised version takes precedence.")

parser.add_option("--glossfile",
                  help="Filename of an optional text file (or compressed .gz, .bz2 or .xz file or URL) to read auxiliary \"gloss\" information.  Each line of this should be of the form: word (tab) annotation (tab) gloss.  Extra tabs in the gloss will be converted to newlines (useful if you want to quote multiple dictionaries).  When the compiled annotator generates ruby markup, it will add the gloss string as a popup title whenever that word is used with that annotation (before any reannotator option is applied).  The annotation field may be left blank to indicate that the gloss will appear for all other annotations of that word.  The entries in glossfile do NOT affect the annotation process itself, so it's not necessary to completely debug glossfile's word segmentation etc.")
parser.add_option("-C", "--gloss-closure",
                  help="If any Chinese, Japanese or Korean word is missing from glossfile, search its closure of variant characters also, using the Unihan variants file specified by this option")
cancelOpt("gloss-closure")
parser.add_option("-M","--glossmiss-omit",
                  action="store_true",
                  default=False,
                  help="Omit rules containing any word not mentioned in glossfile.  Might be useful if you want to train on a text that uses proprietary terms and don't want to accidentally 'leak' those terms (assuming they're not accidentally included in glossfile also).  Words may also be listed in glossfile with an empty gloss field to indicate that no gloss is available but rules using this word needn't be omitted.")
cancelOpt("glossmiss-omit")

parser.add_option("--words-omit",
                  help="File (or compressed .gz, .bz2 or .xz file or URL) containing words (one per line, without markup) to omit from the annotator.  Use this to make an annotator smaller if for example if you're working from a rules file that contains long lists of place names you don't need this particular annotator to recognise but you still want to keep them as rules for other annotators, but be careful because any word on such a list gets omitted even if it also has other meanings (some place names are also normal words).")

parser.add_option("--manualrules",
                  help="Filename of an optional text file (or compressed .gz, .bz2 or .xz file or URL) to read extra, manually-written rules.  Each line of this should be a marked-up phrase (in the input format) which is to be unconditionally added as a rule.  Use this sparingly, because these rules are not taken into account when generating the others and they will be applied regardless of context (although a manual rule might fail to activate if the annotator is part-way through processing a different rule); try checking messages from --diagnose-manual.") # (or if there's a longer automatic match)

#  =========== OUTPUT OPTIONS ==============

parser.add_option("--c-filename",default="",help="Where to write the C, C#, Python, Javascript, Go or Dart program. Defaults to standard output, or annotator.c in the system temporary directory if standard output seems to be the terminal (the program might be large, especially if Yarowsky-like indicators are not used, so it's best not to use a server home directory where you might have limited quota).") # because the main program might not be running on the launch node

parser.add_option("--c-compiler",default="cc -o annotator"+exe,help="The C compiler to run if generating C and standard output is not connected to a pipe. The default is to use the \"cc\" command which usually redirects to your \"normal\" compiler. You can add options (remembering to enclose this whole parameter in quotes if it contains spaces), but if the C program is large then adding optimisation options may make the compile take a LONG time. If standard output is connected to a pipe, then this option is ignored because the C code will simply be written to the pipe. You can also set this option to an empty string to skip compilation. Default: %default")

parser.add_option("--outcode",default="utf-8",
                  help="Character encoding to use in the generated parser (default %default, must be ASCII-compatible i.e. not utf-16)")

parser.add_option("--rulesFile",help="Filename of a JSON file to hold the accumulated rules. Adding .gz, .bz2 or .xz for compression is acceptable. If this is set then either --write-rules or --read-rules must be specified.")

parser.add_option("--write-rules",
                  action="store_true",default=False,
                  help="Write rulesFile instead of generating a parser.  You will then need to rerun with --read-rules later.")
cancelOpt("write-rules")

parser.add_option("--read-rules",
                  action="store_true",default=False,
                  help="Read rulesFile from a previous run, and apply the output options to it. You should still specify the input formatting options (which should not change), and any glossfile or manualrules options (which may change), but no input is required.")
cancelOpt("read-rules")

parser.add_option("-E","--newlines-reset",
                  action="store_false",
                  dest="ignoreNewlines",
                  default=True,
                  help="Have the annotator reset its state on every newline byte. By default newlines do not affect state such as whether a space is required before the next word, so that if the annotator is used with Web Adjuster's htmlText option (which defaults to using newline separators) the spacing should be handled sensibly when there is HTML markup in mid-sentence.")
cancelOpt("newlines-reset","store_true","ignoreNewlines")

parser.add_option("-z","--compress",
                  action="store_true",default=False,
                  help="Compress annotation strings in the C code.  This compression is designed for fast on-the-fly decoding, so it saves only a limited amount of space (typically 10-20%) but might help if RAM is short.")
cancelOpt("compress")

parser.add_option("-Z","--zlib",
                  action="store_true",default=False,
                  help="Compress the embedded data table using zlib (or pyzopfli if available), and include code to call zlib to decompress it on load.  Useful if the runtime machine has the zlib library and you need to save disk space but not RAM (the decompressed table is stored separately in RAM, unlike --compress which, although giving less compression, at least works 'in place').  Once --zlib is in use, specifying --compress too will typically give an additional disk space saving of less than 1% (and a runtime RAM saving that's greater but more than offset by zlib's extraction RAM).  If generating a Javascript annotator with zlib, the decompression code is inlined so there's no runtime zlib dependency, but startup can be ~50% slower so this option is not recommended in situations where the annotator is frequently reloaded from source (unless you're running on Node.js in which case loading is faster due to the use of Node's \"Buffer\" class).")
cancelOpt("zlib")

parser.add_option("-l","--library",
                  action="store_true",default=False,
                  help="Instead of generating C code that reads and writes standard input/output, generate a C library suitable for loading into Python via ctypes.  This can be used for example to preload a filter into Web Adjuster to cut process-startup delays.")
cancelOpt("library")

parser.add_option("-W","--windows-clipboard",
                  action="store_true",default=False,
                  help="Include C code to read the clipboard on Windows or Windows Mobile and to write an annotated HTML file and launch a browser, instead of using the default cross-platform command-line C wrapper.  See the start of the generated C file for instructions on how to compile for Windows or Windows Mobile.")
cancelOpt("windows-clipboard")

parser.add_option("--java",
                  help="Instead of generating C code, generate Java, and place the *.java files in the directory specified by this option.  The last part of the directory should be made up of the package name; a double slash (//) should separate the rest of the path from the package name, e.g. --java=/path/to/wherever//org/example/annotator and the main class will be called Annotator.")
parser.add_option("--android",
                  help="URL for an Android app to browse (--java must be set).  If this is set, code is generated for an Android app which starts a browser with that URL as the start page, and annotates the text on every page it loads.  Use file:///android_asset/index.html for local HTML files in the assets directory; a clipboard viewer is placed in clipboard.html, and the app will also be able to handle shared text.  If certain environment variables are set, this option can also compile and sign the app using Android SDK command-line tools (otherwise it puts a message on stderr explaining what needs to be set)")
parser.add_option("--android-template",
                  help="File to use as a template for Android start HTML.  This option implies --android=file:///android_asset/index.html and generates that index.html from the file specified (or from a built-in default if the special filename 'blank' is used).  The template file may include URL_BOX_GOES_HERE to show a URL entry box and related items (offline-clipboard link etc) in the page, in which case you can optionally define a Javascript function 'annotUrlTrans' to pre-convert some URLs from shortcuts etc; also enables better zoom controls on Android 4+, a mode selector if you use --annotation-names, a selection scope control on recent-enough WebKit, and a visible version stamp (which, if the device is in 'developer mode', you may double-tap on to show missing glosses). VERSION_GOES_HERE may also be included if you want to put it somewhere other than at the bottom of the page. If you do include URL_BOX_GOES_HERE you'll have an annotating Web browser app that allows the user to navigate to arbitrary URLs: as of 2020, this is acceptable on Google Play and Huawei AppGallery (non-China only from 2022), but NOT Amazon AppStore as they don't want 'competition' to their Silk browser.") # but some devices allow APKs to be 'side-loaded'.  annotUrlTrans returns undefined = uses original
parser.add_option("-L","--pleco-hanping",
                  action="store_true",default=False,
                  help="In the Android app, make popup definitions link to Pleco or Hanping if installed")
cancelOpt("pleco-hanping")

parser.add_option("--bookmarks",
                  help="Android bookmarks: comma-separated list of package names that share our bookmarks. If this is not specified, the browser will not be given a bookmarks function. If it is set to the same value as the package specified in --java, bookmarks are kept in just this Android app. If it is set to a comma-separated list of packages that have also been generated by annogen (presumably with different annotation types), and if each one has the same android:sharedUserId attribute in AndroidManifest.xml's 'manifest' tag (you'll need to add this manually), and if the same certificate is used to sign all of them, then bookmarks can be shared across the set of browser apps.  But beware the following two issues: (1) adding an android:sharedUserId attribute to an app that has already been released without one causes some devices to refuse the update with a 'cannot install' message (details via adb logcat; affected users would need to uninstall and reinstall instead of update, and some of them may not notice the instruction to do so); (2) this has not been tested with Google's new \"App Bundle\" arrangement, and may be broken if the Bundle results in APKs being signed by a different key.  In June 2019 Play Console started issuing warnings if you release an APK instead of a Bundle, even though the \"size savings\" they mention are under 1% for annogen-generated apps.") # (the only resource that might vary by device is the launcher icon)
parser.add_option("-e","--epub",
                  action="store_true",default=False,
                  help="When generating an Android browser, make it also respond to requests to open EPUB files. This results in an app that requests the 'read external storage' permission on Android versions below 6, so if you have already released a version without EPUB support then devices running Android 5.x or below will not auto-update past this change until the user notices the update notification and approves the extra permission.") # see comments around READ_EXTERNAL_STORAGE below
cancelOpt("epub")
parser.add_option("--android-print",
                  action="store_true",default=False,
                  help="When generating an Android browser, include code to provide a Print option (usually print to PDF) and a simple highlight-selection option. The Print option will require Android 4.4, but the app should still run without it on earlier versions of Android.")
cancelOpt("android-print")
parser.add_option("--known-characters",help="When generating an Android browser, include an option to leave the most frequent characters unannotated as 'known'.  This option should be set to the filename of a UTF-8 file of characters separated by newlines, assumed to be most frequent first, with characters on the same line being variants of each other (see --freq-count for one way to generate it). Words consisting entirely of characters found in the first N lines of this file (where N is settable by the user) will be unannotated until tapped on.")
parser.add_option("--freq-count",help="Name of a file to write that is suitable for the known-characters option, taken from the input examples (which should be representative of typical use).  Any post-normalise table provided will be used to determine which characters are equivalent.")
parser.add_option("--android-audio",help="When generating an Android browser, include an option to convert the selection to audio using this URL as a prefix, e.g. https://example.org/speak.cgi?text= (use for languages not likely to be supported by the device itself). Optionally follow the URL with a space (quote carefully) and a maximum number of words to read in each user request. Setting a limit is recommended, or somebody somewhere will likely try 'Select All' on a whole book or something and create load problems. You should set a limit server-side too of course.") # do need https if we're Android 5+ and will be viewing HTTPS pages, or Chrome will block (OK if using EPUB-etc or http-only pages)
parser.add_option("--extra-js",help="Extra Javascript to inject into sites to fix things in the Android browser app. The snippet will be run before each scan for new text to annotate. You may also specify a file to read: --extra-js=@file.js or --extra-js=@file1.js,file2.js (do not use // comments in these files, only /* ... */ because newlines will be replaced), and you can create variants of the files by adding search-replace strings: --extra-js=@file1.js:search:replace,file2.js")
parser.add_option("--tts-js",action="store_true",default=False,help="Make Android 5+ multilingual Text-To-Speech functions available to extra-js scripts (see TTSInfo code for details)")
cancelOpt("tts-js")
parser.add_option("--existing-ruby-js-fixes",help="Extra Javascript to run in the Android browser app or browser extension whenever existing RUBY elements are encountered; the DOM node above these elements will be in the variable n, which your code can manipulate or replace to fix known problems with sites' existing ruby (such as common two-syllable words being split when they shouldn't be). Use with caution. You may also specify a file to read: --existing-ruby-js-fixes=@file.js")
parser.add_option("--existing-ruby-lang-regex",help="Set the Android app or browser extension to remove existing ruby elements unless the document language matches this regular expression. If --sharp-multi is in use, you can separate multiple regexes with comma and any unset will always delete existing ruby.  If this option is not set at all then existing ruby is always kept.")
parser.add_option("--existing-ruby-shortcut-yarowsky",action="store_true",default=False,help="Set the Android browser app to 'shortcut' Yarowsky-like collocation decisions when adding glosses to existing ruby over 2 or more characters, so that words normally requiring context to be found are more likely to be found without context (this may be needed because adding glosses to existing ruby is done without regard to context)") # (an alternative approach would be to collapse the existing ruby markup to provide the context, but that could require modifying the inner functions to 'see' context outside the part they're annotating)
parser.add_option("--extra-css",help="Extra CSS to inject into sites to fix things in the Android browser app. You may also specify a file to read --extra-css=@file.css")
parser.add_option("--app-name",default="Annotating browser",
                  help="User-visible name of the Android app")

parser.add_option("--compile-only",
                  action="store_true",default=False,
                  help="Assume the code has already been generated by a previous run, and just run the compiler")
cancelOpt("compile-only")

parser.add_option("-j","--javascript",
                  action="store_true",default=False,
                  help="Instead of generating C code, generate JavaScript.  This might be useful if you want to run an annotator on a device that has a JS interpreter but doesn't let you run your own binaries.  The JS will be table-driven to make it load faster.  See comments at the start for usage.") # but it's better to use the C version if you're in an environment where 'standard input' makes sense
cancelOpt("javascript")

parser.add_option("-6","--js-6bit",
                  action="store_true",default=False,
                  help="When generating a Javascript annotator, use a 6-bit format for many addresses to reduce escape codes in the data string by making more of it ASCII") # May result in marginally slower JS, but it should be smaller and parse more quickly on initial load, which is normally the dominant factor if you have to reload it on every page.
cancelOpt("js-6bit")

parser.add_option("-8","--js-octal",
                  action="store_true",default=False,
                  help="When generating a Javascript annotator, use octal instead of hexadecimal codes in the data string when doing so would save space. This does not comply with ECMAScript 5 and may give errors in its strict mode.")
cancelOpt("js-octal")

parser.add_option("-9","--ignore-ie8",
                  action="store_true",default=False,
                  help="When generating a Javascript annotator, do not make it backward-compatible with Microsoft Internet Explorer 8 and below. This may save a few bytes.")
cancelOpt("ignore-ie8")

parser.add_option("-u","--js-utf8",
                  action="store_true",default=False,
                  help="When generating a Javascript annotator, assume the script can use UTF-8 encoding directly and not via escape sequences. In some browsers this might work only on UTF-8 websites, and/or if your annotation can be expressed without the use of Unicode combining characters.")
cancelOpt("js-utf8")

parser.add_option("--browser-extension", help="Name of a Chrome or Firefox browser extension to generate.  The extension will be placed in a directory of the same name (without spaces), which may optionally already exist and contain icons like 32.png and 48.png to be used.")
# To test the resulting extension locally:
# Firefox: about:debugging - 'this firefox' - load temporary add-on - manifest.json
# Chrome: chrome://extensions - Developer mode - Load unpacked - select the directory
# Chrome bug: browser_style true gives unreadable text in Chromium 89 with enable-force-dark set to "Enabled with selective inversion of everything" (and possibly other settings)

parser.add_option("--browser-extension-description", help="Description field to use when generating browser extensions")

parser.add_option("--manifest-v3",
                  action="store_true",default=False,
                  help="Use Manifest v3 instead of Manifest v2 when generating browser extensions (tested on Chrome only, and requires Chrome 88 or higher).  This is now required for all Chrome Web Store uploads.")

parser.add_option("--gecko-id",help="a Gecko (Firefox) ID to embed in the browser extension")

parser.add_option("--dart",
                  action="store_true",default=False,
                  help="Instead of generating C code, generate Dart.  This might be useful if you want to run an annotator in a Flutter application.")
cancelOpt("dart")

parser.add_option("--dart-datafile",
                  help="When generating Dart code, put annotator data into a separate file and open it using this pathname. Not compatible with Dart's \"Web app\" option, but might save space in a Flutter app (especially along with --zlib)")

parser.add_option("-Y","--python",
                  action="store_true",default=False,
                  help="Instead of generating C code, generate a Python module.  Similar to the Javascript option, this is for when you can't run your own binaries, and it is table-driven for fast loading.")
cancelOpt("python")

parser.add_option("--reannotator",
                  help="Shell command through which to pipe each word of the original text to obtain new annotation for that word.  This might be useful as a quick way of generating a new annotator (e.g. for a different topolect) while keeping the information about word separation and/or glosses from the previous annotator, but it is limited to commands that don't need to look beyond the boundaries of each word.  If the command is prefixed by a # character, it will be given the word's existing annotation instead of its original text, and if prefixed by ## it will be given text#annotation.  The command should treat each line of its input independently, and both its input and its output should be in the encoding specified by --outcode.") # TODO: reannotatorCode instead? (see other 'reannotatorCode' TODOs)
# (Could just get the reannotator to post-process the 1st annotator's output, but that might be slower than generating an altered annotator with it)

parser.add_option("-A","--reannotate-caps",
                  action="store_true",default=False,
                  help="When using --reannotator, make sure to capitalise any word it returns that began with a capital on input")
cancelOpt("reannotate-caps")

parser.add_option("--sharp-multi",
                  action="store_true",default=False,
                  help="Assume annotation (or reannotator output) contains multiple alternatives separated by # (e.g. pinyin#Yale) and include code to select one by number at runtime (starting from 0). This is to save on total space when shipping multiple annotators that share the same word grouping and gloss data, differing only in the transcription of each word.")
cancelOpt("sharp-multi")
parser.add_option("--annotation-names",help="Comma-separated list of annotation types supplied to sharp-multi (e.g. Pinyin,Yale), if you want the Android app etc to be able to name them.  You can also set just one annotation names here if you are not using sharp-multi.")
parser.add_option("--annotation-map",help="Comma-separated list of annotation-number overrides for sharp-multi, e.g. 7=3 to take the 3rd item if a 7th is selected") # this one starts at 1 rather than 0
parser.add_option("--annotation-postprocess",help="Extra code for post-processing specific annotNo selections after retrieving from a sharp-multi list (@file is allowed)")

#  =========== ANALYSIS OPTIONS ==============

parser.add_option("-o", "--allow-overlaps",
                  action="store_true",default=False,
                  help="Normally, the analyser avoids generating rules that could overlap with each other in a way that would leave the program not knowing which one to apply.  If a short rule would cause overlaps, the analyser will prefer to generate a longer rule that uses more context, and if even the entire phrase cannot be made into a rule without causing overlaps then the analyser will give up on trying to cover that phrase.  This option allows the analyser to generate rules that could overlap, as long as none of the overlaps would cause actual problems in the example phrases. Thus more of the examples can be covered, at the expense of a higher risk of ambiguity problems when applying the rules to other texts.  See also the -y option.")
cancelOpt("allow-overlaps")

parser.add_option("-y","--ybytes",default=0,
                  help="Look for candidate Yarowsky seed-collocations within this number of bytes of the end of a word.  If this is set then overlaps and rule conflicts will be allowed when seed collocations can be used to distinguish between them, and the analysis is likely to be faster.  Markup examples that are completely separate (e.g. sentences from different sources) must have at least this number of (non-whitespace) bytes between them.")
parser.add_option("--ybytes-max",default=0,
                  help="Extend the Yarowsky seed-collocation search to check over larger ranges up to this maximum.  If this is set then several ranges will be checked in an attempt to determine the best one for each word, but see also ymax-threshold and ymax-limitwords.")
parser.add_option("--ymax-threshold",default=1,
                  help="Limits the length of word that receives the narrower-range Yarowsky search when ybytes-max is in use. For words longer than this, the search will go directly to ybytes-max. This is for languages where the likelihood of a word's annotation being influenced by its immediate neighbours more than its distant collocations increases for shorter words, and less is to be gained by comparing different ranges when processing longer words. Setting this to 0 means no limit, i.e. the full range will be explored on ALL Yarowsky checks.") # TODO: see TODO below re temporary recommendation of --ymax-threshold=0
parser.add_option("--ymax-limitwords",
                  help="Comma-separated list of words (without annotation markup) for which the ybytes expansion loop should run at most two iterations.  This may be useful to reduce compile times for very common ambiguous words that depend only on their immediate neighbours.  Annogen may suggest words for this option if it finds they take inordinate time to process.") # two iterations rather than one increases the rate of correctly handling things like 'yi/bu sandhi before duoyinzi' in Chinese, where the next TWO characters matter because the sandhi tone depends on how the duoyinzi resolves (which is often determined by the 3rd character, although this shortcut may not catch some rare cases where it's determined by one further on)
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
parser.add_option("--yarowsky-multiword",
                  action="store_true",default=False,
                  help="Check potential multiword rules for Yarowsky seed collocations also.  Without this option (default), only single-word rules are checked.") # multiword might not work so well
cancelOpt("yarowsky-multiword")
parser.add_option("--yarowsky-thorough",
                  action="store_true",default=False,
                  help="Recheck Yarowsky seed collocations when checking if any multiword rule would be needed to reproduce the examples.  This could risk 'overfitting' the example set.") # (more likely to come up with rules that aren't really needed and end with 1st half of a sandhi etc)
cancelOpt("yarowsky-thorough")
parser.add_option("--yarowsky-half-thorough",
                  action="store_true",default=False,
                  help="Like --yarowsky-thorough but check only what collocations occur within the proposed new rule (not around it), less likely to overfit")
cancelOpt("yarowsky-half-thorough")
parser.add_option("--yarowsky-debug",default=1,
                  help="Report the details of seed-collocation false positives if there are a large number of matches and at most this number of false positives (default %default). Occasionally these might be due to typos in the corpus, so it might be worth a check.")
parser.add_option("--normalise-debug",default=1,
                  help="When --capitalisation is not in effect. report words that are usually capitalised but that have at most this number of lower-case exceptions (default %default) for investigation of possible typos in the corpus")
parser.add_option("--normalise-cache",
                  help="Optional file to use to cache the result of normalisation. Adding .gz, .bz2 or .xz for compression is acceptable.")

parser.add_option("-1","--single-words",
                  action="store_true",default=False,
                  help="Do not generate any rule longer than 1 word, although it can still have Yarowsky seed collocations if -y is set. This speeds up the search, but at the expense of thoroughness. You might want to use this in conjuction with -y to make a parser quickly.")
cancelOpt("single-words")
parser.add_option("--max-words",default=0,
                  help="Limits the number of words in a rule.  0 means no limit.  --single-words is equivalent to --max-words=1.  If you need to limit the search time, and are using -y, it should suffice to use --single-words for a quick annotator or --max-words=5 for a more thorough one (or try 3 if --yarowsky-half-thorough is in use).")  # (There was a bug in annogen versions before 0.58 that caused --max-words to additionally limit how far away from the start of its phrase a rule-example must be placed; this has now been fixed.  There was also a bug that resulted in too many extra rules being tested over already-catered-for phrases; as this has now been fixed, the additional benefit of a --max-words limit is now reduced, but you might want to put one in anyway.  That second bug also had the effect of the coverage % being far too low in the progress stats.)
parser.add_option("--multiword-end-avoid",
                  help="Comma-separated list of words (without annotation markup) that should be avoided at the end of a multiword rule (e.g. sandhi likely to depend on the following word)")

parser.add_option("-d","--diagnose",help="Output some diagnostics for the specified word. Use this option to help answer \"why doesn't it have a rule for...?\" issues. This option expects the word without markup and uses the system locale (UTF-8 if it cannot be detected).")
parser.add_option("--diagnose-limit",default=10,help="Maximum number of phrases to print diagnostics for (0 means unlimited). Default: %default")
parser.add_option("-m","--diagnose-manual",
                  action="store_true",default=False,
                  help="Check and diagnose potential failures of --manualrules")
cancelOpt("diagnose-manual")
parser.add_option("-q","--diagnose-quick",
                  action="store_true",default=False,
                  help="Ignore all phrases that do not contain the word specified by the --diagnose option, for getting a faster (but possibly less accurate) diagnostic.  The generated annotator is not likely to be useful when this option is present.")
cancelOpt("diagnose-quick")

parser.add_option("--priority-list",help="Instead of generating an annotator, use the input examples to generate a list of (non-annotated) words with priority numbers, a higher number meaning the word should have greater preferential treatment in ambiguities, and write it to this file (or compressed .gz, .bz2 or .xz file).  If the file provided already exists, it will be updated, thus you can amend an existing usage-frequency list or similar (although the final numbers are priorities and might no longer match usage-frequency exactly).  The purpose of this option is to help if you have an existing word-priority-based text segmenter and wish to update its data from the examples; this approach might not be as good as the Yarowsky-like one (especially when the same word has multiple readings to choose from), but when there are integration issues with existing code you might at least be able to improve its word-priority data.")

parser.add_option("-t","--time-estimate",
                  action="store_true",default=False,
                  help="Estimate time to completion.  The code to do this is unreliable and is prone to underestimate.  If you turn it on, its estimate is displayed at the end of the status line as days, hours or minutes.") # Unreliable because the estimate assumes 'phrases per minute' will remain constant on average, whereas actually it will decrease because the more complex phrases are processed last
cancelOpt("time-estimate")

parser.add_option("-0","--single-core",
                  action="store_true",default=False,
                  help="Use only one CPU core even when others are available on Unix")
cancelOpt("single-core")
parser.add_option("--cores-command",help="Command to run when changing the number of CPU cores in use (with new number as a parameter); this can run a script to pause/resume any lower-priority load")

parser.add_option("-p","--status-prefix",help="Label to add at the start of the status line, for use if you batch-run annogen in multiple configurations and want to know which one is currently running")

if '--html-options' in sys.argv or '--markdown-options' in sys.argv:
  if '--html-options' in sys.argv:
    print ("</dl>")
  sys.exit()
term = os.environ.get("TERM","")
is_xterm = "xterm" in term
ansi_escapes = is_xterm or term in ["screen","linux"]
def isatty(f): return hasattr(f,"isatty") and f.isatty()
if ansi_escapes and isatty(sys.stderr): clear_eol,reverse_on,reverse_off,bold_on,bold_off="\x1b[K","\x1b[7m","\x1b[0m","\x1b[1m","\x1b[0m"
else: clear_eol,reverse_on,reverse_off,bold_on,bold_off="  "," **","** ","",""
sys.stderr.write(bold_on+__doc__+bold_off+"\n") # not sys.stdout: may or may not be showing --help (and anyway might want to process the help text for website etc)
options, args = parser.parse_args()
globals().update(options.__dict__)

try: import thread
except: import _thread as thread # Python 3
import gc ; gc.disable() # should be OK if we don't create cycles (TODO: run gc.collect() manually after init, just in case?)

def warn(msg):
  sys.stderr.write("Warning: "+msg+"\n")
if "PyPy" in sys.version: warn("with annogen, PyPy is likely to run 60% slower than python") # (not to mention concurrent.futures being less likely to be available)

if ybytes: ybytes=int(ybytes)
if ybytes_max: ybytes_max=int(ybytes_max)
else: ybytes_max = ybytes
if yarowsky_debug: yarowsky_debug=int(yarowsky_debug)
else: yarowsky_debug = 0
if normalise_debug: normalise_debug=int(normalise_debug)
else: normalise_debug = 0
ybytes_step = int(ybytes_step)
ymax_threshold = int(ymax_threshold)
def errExit(msg):
  try:
    if not outfile==getBuf(sys.stdout):
      outfile.close() ; rm_f(c_filename)
  except: pass # works only if got past outfile opening
  sys.stderr.write(msg+"\n") ; sys.exit(1)
if args: errExit("Unknown argument "+repr(args[0]))
if sharp_multi and not annotation_names and (browser_extension or existing_ruby_lang_regex): errExit("--sharp-multi requires --annotation-names to be set if --browser-extension or --existing-ruby-lang-regex")
if existing_ruby_lang_regex:
    while len(existing_ruby_lang_regex.split(','))<len(annotation_names.split(',')): existing_ruby_lang_regex += r",^\b$"
if browser_extension: javascript = True
if android_template:
  android = "file:///android_asset/index.html"
if android and not java: errExit('You must set --java=/path/to/src//name/of/package when using --android')
if bookmarks and not android: errExit("--bookmarks requires --android, e.g. --android=file:///android_asset/index.html")
if known_characters and not (android or javascript): errExit("--known-characters requires --android, --javascript or --browser-extension")
if known_characters and freq_count: errExit("--known-characters and --freq-count must be on separate runs in the current implementation") # otherwise need to postpone loading known_characters
if known_characters and android and not android_template and not ("ANDROID_NO_UPLOAD" in os.environ and "GOOGLE_PLAY_TRACK" in os.environ): warn("known-characters without android-template means you call the Javascript functions yourself")
if android_print and not bookmarks: errExit("The current implementation of --android-print requires --bookmarks to be set as well")
if android_audio:
  if not android_print: errExit("The current implementation of --android-audio requires --android-print to be set as well") # for the highlighting (and TODO: I'm not sure about the HTML5-Audio support of Android 2.x devices etc, so should we check a minimum Android version before making the audio option available? as highlight option can be done pre-4.4 just no way to save the result)
  if "'" in android_audio or '"' in android_audio or '\\' in android_audio: errExit("The current implementation of --android-audio requires the URL not to contain any quotes or backslashes, please percent-encode them")
  if ' ' in android_audio:
    android_audio,android_audio_maxWords = android_audio.split()
    android_audio_maxWords = int(android_audio_maxWords)
  else: android_audio_maxWords=None
if (extra_js or extra_css or tts_js) and not android: errExit("--extra-js, --tts-js and --extra-css require --android")
if (existing_ruby_lang_regex or existing_ruby_js_fixes) and not (android or javascript): errExit("--existing-ruby-lang-regex and --existing-ruby-js-fixes require --android, --javascript or --browser-extension")
if not extra_css: extra_css = ""
if not extra_js: extra_js = ""
if not existing_ruby_js_fixes: existing_ruby_js_fixes = ""
if not annotation_postprocess: annotation_postprocess = ""
if extra_css.startswith("@"): extra_css = open(extra_css[1:],"rb").read()
if annotation_postprocess.startswith("@"): annotation_postprocess = open(annotation_postprocess[1:],"rb").read()
if annotation_postprocess and not java: errExit("--annotation-postprocess is currently implemented only for Java") # TODO could at least do JS
if type("")==type(u""): # Python 3
  def B(s):
    try: return s.encode('latin1')
    except: return s
  def S(b):
    try: return b.decode('latin1')
    except: return b
  def getBuf(f):
    try: return f.buffer
    except: return f
else: # Python 2: pass through as quickly as possible
  def B(s): return s # (and as this particular script shouldn't need to run on a Python 2 below 2.7, we also use b"" inline for literals)
  def S(s): return s
  def getBuf(f): return f
if extra_js.startswith("@"):
  f,extra_js=extra_js,b""
  can_check_syntax = not os.system("which node 2>/dev/null >/dev/null")
  for f in f[1:].split(','):
   if ':' in f: f,fSR = f.split(':',1)
   else: fSR=None
   dat = open(f,"rb").read()
   if fSR:
     fSR = fSR.split(':')
     for i in range(0,len(fSR),2):
       if not B(fSR[i]) in dat: errExit("extra-js with search and replace: unable to find "+repr(fSR[i])+" in "+f)
       dat = dat.replace(B(fSR[i]),B(fSR[i+1]))
   if can_check_syntax:
     out = err = True
     if os.path.exists("/dev/shm"):
       # node -c /dev/stdin can fail on some installations of GNU/Linux (but /dev/shm can fail on others, so try both)
       fn="/dev/shm/"+str(os.getpid())+".js"
       open(fn,"wb").write(dat)
       out,err = subprocess.Popen("node -c "+fn,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
       os.remove(fn)
     if out or err:
       out0,err0 = out,err
       out,err = subprocess.Popen("node -c /dev/stdin",shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate(dat)
       if (out or err) and not out0==True:
         out,err = out0+out,err0+err
     if out or err: errExit("Syntax check failed for extra-js file "+f+"\n"+"node stdout: "+repr(out)+"\nnode stderr: "+repr(err))
   else: warn("No syntax checker available for "+f)
   m=re.search(br"\([^)]*\)\s*=>\s*{",dat)
   if m: errExit(f+" seems to have arrow function (breaks compatibility with Android 4.x): "+repr(m.group())) # TODO: also check for ||= (but not in comments; comments would need rm 1st); ||= requires Chrome 85
   extra_js += dat ; del dat,fSR
if extra_js.rstrip() and not B(extra_js.rstrip()[-1:]) in b';}': errExit("--extra-js must end with a semicolon or a closing brace")
if existing_ruby_js_fixes.startswith("@"): existing_ruby_js_fixes = open(existing_ruby_js_fixes[1:],"rb").read()
if browser_extension and re.search("erHTML *=[^=]",existing_ruby_js_fixes): warn("Code in --existing-ruby-js-fixes that sets innerHTML or outerHTML might result in an extension that's not accepted by Firefox uploads")
jPackage = None
if java:
  if not '//' in java: errExit("--java must include a // to separate the first part of the path from the package name")
  jSrc,jRest=java.rsplit('//',1)
  if '.' in jRest: errExit("--java must be ...src//org/example/package not ...src//org.example.package") # (TODO: fix it automatically in both jRest and java? only on the right-hand side of the //)
  jPackage = jRest.replace('/','.')
  if 'NewFunc' in jPackage: errExit("Currently unable to include the string 'NewFunc' in your package due to an implementation detail in annogen's search/replace operations")
if not c_filename and isatty(sys.stdout):
  c_filename = tempfile.gettempdir()+os.sep+"annotator.c"
def shell_escape(arg):
  if re.match("^[A-Za-z0-9_=/.%+,:@-]*$",arg): return arg
  return "'"+arg.replace("'",r"'\''")+"'"
if sharp_multi:
  if python: errExit("sharp-multi not yet implemented in Python") # TODO: easy enough
  elif windows_clipboard: errExit("sharp-multi not yet implemented for windows-clipboard") # would need a way to select the annotator, probably necessitating a GUI on Windows
if java or javascript or python or dart:
    def cOnly(param): errExit(param+" not yet implemented in any language other than C, so cannot be used with --java, --javascript, --python or --dart")
    if windows_clipboard: cOnly("--windows-clipboard")
    if library: cOnly("--library")
    if not outcode=="utf-8": cOnly("Non utf-8 outcode")
    if compress: cOnly("--compress")
    if sum(1 for x in [java,javascript,python,dart] if x) > 1:
      errExit("Outputting more than one programming language on the same run is not yet implemented")
    if java:
      if android and not "/src//" in java: errExit("When using --android, the last thing before the // in --java must be 'src' e.g. --java=/workspace/MyProject/src//org/example/package")
      if not compile_only: # (delete previous files, only if we're not a subprocess)
       os.system("mkdir -p "+shell_escape(java))
       for f in os.listdir(java):
        if f.endswith(".java") and f.startswith("z"): os.remove(java+os.sep+f)
      c_filename = java+os.sep+"Annotator.java"
      if android:
        os.system("rm -rf "+shell_escape(jSrc+"/../bin")) # needed to get rid of old *.class files that might be no longer used
        for d in ["assets","bin","gen","res/layout","res/menu","res/values","res/xml"]: os.system("mkdir -p "+shell_escape(jSrc+"/../"+d))
    elif c_filename.endswith(".c"):
      if javascript: c_filename = c_filename[:-2]+".js"
      elif dart: c_filename = c_filename[:-2]+".dart"
      else: c_filename = c_filename[:-2]+".py"
elif windows_clipboard:
  if library: errExit("Support for having both --windows-clipboard and --library at the same time is not yet implemented") # ditto
  if c_compiler=="cc -o annotator": c_compiler="i386-mingw32-gcc -o annoclip.exe"
  if not outcode=="utf-8": errExit("outcode must be utf-8 when using --windows-clipboard")
elif library:
  if c_compiler=="cc -o annotator": c_compiler="gcc -shared -fPIC -Wl,-soname,annotator.so.1 -o libannotator.so.1 -lc"
if js_6bit:
  if not javascript: errExit("--js-6bit requires --javascript") # or just set js_6bit=False in these circumstances?
  import urllib
if dart:
  js_utf8 = not dart_datafile
  if dart_datafile and any(x in dart_datafile for x in "'\\$"): errExit("Current implementation cannot cope with ' or \\ or $ in dart_datafile")
elif dart_datafile: errExit("--dart-datafile requires --dart")
if zlib:
  if javascript: errExit("--zlib not supported with Javascript")
  del zlib
  try:
    from zopfli import zlib # pip install zopfli
    zlib._orig_compress = zlib.compress
    zlib.compress = lambda s,level: zlib._orig_compress(s) # delete level
    zlib_name = "zopfli"
  except:
    import zlib
    zlib_name = "zlib"
  if windows_clipboard: warn("--zlib with --windows-clipboard is inadvisable because ZLib is not typically present on Windows platforms. If you really want it, you'll need to figure out the compiler options and library setup for it.")
  if dart and not dart_datafile: warn("--zlib without --dart-datafile might not be as efficient as you'd hope (and --zlib prevents the resulting Dart code from being compiled to a \"Web app\" anyway)") # as it requires dart:io
if rulesFile:
  if not (read_rules or write_rules): errExit("rulesFile requires --read-rules or --write-rules")
  elif read_rules and write_rules: errExit("--read-rules and --write-rules are mutually exclusive")
  if priority_list: errExit("can't set both rulesFile and priority-list") # because PairPriorities uses corpus, not rules
elif read_rules or write_rules: errExit("--read-rules or --write-rules requires rulesFile")
if java or javascript or python or dart: c_compiler = None
try: xrange # Python 2
except: xrange,unichr,unicode = range,chr,str # Python 3
if post_normalise:
  if not (javascript or java or freq_count): errExit('--post-normalise currently requires --javascript or --java (or --freq-count)')
  if type("")==type(u""): # Python 3 (this requires 3.5+, TODO: support 3.3/3.4 ?)
    import importlib.util as iu
    s = iu.spec_from_file_location("post.normalise", post_normalise)
    post_normalise = iu.module_from_spec(s) ; s.loader.exec_module(post_normalise)
  else: # Python 2
    import imp
    post_normalise = imp.load_source('post.normalise', post_normalise)
  post_normalise = post_normalise.table
  for k,v in list(post_normalise.items()):
    if not (k<=0xFFFF and v<=0xFFFF and len(unichr(k).encode('utf-8'))==len(unichr(v).encode('utf-8'))): del post_normalise[k] # BMP only for now, and only mappings that don't change UTF-8 length so inBytes / origInBytes are sync'd
    elif k==v: del post_normalise[k] # don't need identity mappings
  problems = set(post_normalise.keys()).intersection(set(post_normalise.values()))
  if problems: errExit("--post-normalise table problem: both keys AND values have "+", ".join(hex(h) for h in sorted(list(problems))))
  if type(u"")==type(""): post_normalise_translate = lambda x:x.translate(post_normalise) # Python 3 can use the dictionary as-is
  else: post_normalise_translate = lambda u: u''.join(unichr(post_normalise.get(ord(i),ord(i))) for i in u) # as Python 2 .translate can take only len=256 (at least as documented; some versions can do more but not all tested), so we'd better write it out ourselves
try:
  import locale
  terminal_charset = locale.getpreferredencoding()
except: terminal_charset = None
if not terminal_charset: terminal_charset = "utf-8"
if existing_ruby_shortcut_yarowsky:
  if not (android and ybytes and glossfile): errExit("--existing-ruby-shortcut-yarowsky makes sense only when generating an Android app with both ybytes and glossfile set")
def T(s):
  if type(s)==type(u""): return s # Python 3
  return s.decode(terminal_charset)
if keep_whitespace: keep_whitespace = set(T(keep_whitespace).split(','))
if ymax_limitwords: ymax_limitwords = set(T(ymax_limitwords).split(','))
if multiword_end_avoid: multiword_end_avoid = set(T(multiword_end_avoid).split(','))
if status_prefix: status_prefix += ": "
else: status_prefix = ""
if diagnose: diagnose=T(diagnose)
diagnose_limit = int(diagnose_limit)
max_words = int(max_words)
if single_words: max_words = 1
if read_rules and diagnose_manual: errExit("--diagnose-manual is not compatible with --read-rules")
suffix_minlen=int(suffix_minlen)

if compress:
  squashStrings = set() ; squashReplacements = []
  def squashFinish():
    global squashStrings # so can set it to "done" at end
    tokens = set()
    for s in squashStrings: tokens.update(list(S(s)))
    totSaved = 0
    tokens = [chr(t) for t in range(1,256) if not chr(t) in tokens] ; orig_tokens = set(tokens)
    pairs = [chr(0)] * 512
    while tokens and squashStrings:
      t = tokens.pop()
      counts = {}
      for s in squashStrings:
        # To make decompression as fast and compact as possible, each 1-byte token represents 2 bytes exactly.  In practice allowing it to represent variable lengths of whole bytes up to 4 is not likely to improve the compression by more than 3.2% (that's 3.2% of the 10-20% it achieves, so it's around 0.5%), and not very much better for length 9, so we might as well stick with this simpler scheme unless we do real LZMA or whatever.
          for i in range(0,len(s)-1):
            k = s[i:i+2]
            if S(k[:1]) in orig_tokens or S(k[1:]) in orig_tokens: continue # to keep the decoder simple, don't set things up so it needs to recurse (being able to recurse within the 2-byte expansion is very unlikely to save anything in practice anyway - it didn't on my annotators - so not worth implementing the decoder for)
            counts[k] = counts.get(k,0) + 1
      bSaved, k = max((v,k) for k,v in counts.items())
      pairs[ord(t)] = k[:1]
      pairs[ord(t)+256] = k[1:]
      squashReplacements.append((k,B(t))) # this assumes we won't be doing things like 'if ALL instances of a byte end up in our tokens, add the byte's original value as an extra token'
      for s in squashStrings:
        s2 = s.replace(k,B(t))
        if not s2==s:
          squashStrings.remove(s) ; squashStrings.add(s2)
      totSaved += bSaved
      sys.stderr.write("Compress: %d/%d tokens, %d bytes saved%s\r" % (len(orig_tokens)-len(tokens),len(orig_tokens),totSaved,clear_eol)) ; sys.stderr.flush()
    squashStrings = "done"
    while len(pairs) > 256 and pairs[-1]==chr(0): pairs = pairs[:-1]
    sys.stderr.write("\n")
    if totSaved < len(pairs)+50: sys.stderr.write("Warning: --compress on this data made it bigger!  Consider dropping --compress\n") # 50 as rough guess for OutWriteDecompress binary (probably about 12 instructions at 4+ bytes each)
    return c_escapeRawBytes(b"".join(B(p) for p in pairs))
  decompress_func=br"""

static unsigned char pairs[]="%%PAIRS%%";
static void OutWriteDecompress(const char *s) {
while(*s) {
  int i=(unsigned char)*s;
  if (pairs[i]) { OutWriteByte(pairs[i]); OutWriteByte(pairs[i|0x100]); } else OutWriteByte(*s);
  s++;
}
}"""
  if sharp_multi: decompress_func += br"""
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
elif sharp_multi: decompress_func = br"""
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
else: decompress_func = b""

def annotMap(varName="annotNo",mayNeedParen=False):
  r = ""
  if annotation_map:
    for i in annotation_map.split(","):
      k,v = i.split('=')
      r += varName+"=="+str(int(k)-1)+"?"+str(int(v)-1)+":"
  r += varName
  if mayNeedParen and "==" in r: r="("+r+")"
  return B(r)

if c_filename and os.sep in c_filename: cfn = c_filename[c_filename.rindex(os.sep)+1:]
else: cfn = c_filename
if library:
  c_preamble = br"""
  /*
     This library is NOT thread safe.  But you can use it
     with single-threaded or multiprocess code like Web Adjuster
     (not in WSGI mode).
    
     To wrap this library in Python (2 or 3), you can do:

from ctypes import CDLL,c_char_p,c_int
alib = CDLL("./libannotator.so.1")
_annotate,_afree = alib.annotate,alib.afree
_annotate.restype = c_char_p
_annotate.argtypes = [c_char_p"""
  if sharp_multi: c_preamble += b",c_int"
  c_preamble += b",c_int]"
  if outcode=="utf-8":
    c_preamble += br"""
_annotateRL = alib.annotateRawLatinize
_annotateRL.restype = c_char_p
_annotateRL.argtypes = [c_char_p"""
    if sharp_multi: c_preamble += b",c_int"
    c_preamble += b"]\ndef annotR(txt"
    if sharp_multi: c_preamble += b",aType=0"
    c_preamble += br"""):
    if type(txt)==type(u''): txt = txt.encode('utf-8')
    r = _annotateRL(txt"""
    if sharp_multi: c_preamble += b",aType"
    c_preamble += br""")
    _afree() ; return r"""
  c_preamble += b"\ndef annotate(txt"
  if sharp_multi: c_preamble += b",aType=0"
  c_preamble += br""",aMode=1):
    "aMode: 0 = raw, 1 = ruby (default), 2 = braces"
    if type(txt)==type(u''): txt = txt.encode('"""+B(outcode)+br"""')
    r = _annotate(txt"""
  if sharp_multi: c_preamble += b",aType"
  c_preamble += br""",aMode)
    _afree() ; return r
# then for Web Adjuster you can do, for example,
# adjuster.annotFunc1 = lambda t:annotate(t"""
  if sharp_multi: c_preamble += b",1"
  c_preamble += b",1)\n"
  if outcode=="utf-8":
    if sharp_multi: c_preamble += b"# adjuster.annotFunc1R = lambda t:annotR(t,1)"
    else: c_preamble += b"# adjuster.annotFunc1R = annotR"
    c_preamble += br"""
# adjuster.options.htmlFilter = "*annotFunc1#*annotFunc1R"
# adjuster.options.htmlFilterName = "ruby#annot-only"
"""
  else: c_preamble += br"""
# adjuster.options.htmlFilter = "*annotFunc1"
"""
  if not outcode=="utf-8": c_preamble += br"""
# but BEWARE Web Adjuster assumes UTF-8; you'd better write a wrapper to re-code it
""" # (TODO: automate this?)
  c_preamble += br"""
    Compile with:
    gcc -shared -fPIC -Wl,-soname,annotator.so.1 -o libannotator.so.1 annotator.c -lc

  */
  """
  if cfn: c_preamble=c_preamble.replace(b"annotator.c",B(cfn))
  c_preamble += br"""
#include <stdlib.h>
#include <string.h>
"""
  c_defs = br"""static const unsigned char *readPtr, *writePtr, *startPtr;
static char *outBytes;
static size_t outWriteLen,outWritePtr;
#define NEXTBYTE (*readPtr++)
#define NEXT_COPY_BYTE (*writePtr++)
#define COPY_BYTE_SKIP writePtr++
#define COPY_BYTE_SKIPN(n) writePtr += (n)
#define POSTYPE const unsigned char*
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
    const unsigned char *startFrom = readPtr-nearbytes,
                     *end = readPtr+nearbytes;
    if (startFrom < startPtr) startFrom = startPtr;
    size_t l=strlen(string); end -= l;
    while (*startFrom && startFrom <= end) {
      if(!strncmp(startFrom,string,l)) return 1;
      startFrom++;
    }
    return 0;
}
void matchAll();"""
  c_defs += br"""
void afree() { if(outBytes) free(outBytes); outBytes=NULL; }
char *annotate(const char *input"""
  if sharp_multi: c_defs += b", int annotNo"
  c_defs += br""",int aMode) {
  readPtr=writePtr=startPtr=(char*)input;
  outWriteLen = strlen(startPtr)*5+1; /* initial guess (must include the +1 to ensure it's non-0 for OutWrite...'s *= code) */
  afree(); outBytes = malloc(outWriteLen);"""
  if sharp_multi: c_defs += b" numSharps="+annotMap()+b";"
  c_defs += br""" annotation_mode = aMode;
  if(outBytes) { outWritePtr = 0; matchAll(); }
  if(outBytes) OutWriteByte(0);
  return outBytes;
}
"""
  if outcode=="utf-8": # (TODO: document this feature?  non-utf8 versions ??)
    c_defs += br"""
static void latinizeMatch(); static int latCap,latSpace;
char *annotateRawLatinize(const char *input"""
    if sharp_multi: c_defs += b", int annotNo"
    c_defs += br""") {
    // "Bonus" library function, works only if annotation is Latin-like,
    // tries to improve the capitalisation when in 'raw' mode
    // (TODO: make this available in other annogen output formats?  work into ruby mode??)
    char *tmp=annotate(input"""
    if sharp_multi: c_defs += b",annotNo"
    c_defs += br""",annotations_only);
    if(tmp) { tmp=strdup(tmp); if(tmp) {
      readPtr=writePtr=startPtr=tmp;
      afree(); outBytes=malloc(outWriteLen);
      if(outBytes) {
        outWritePtr = 0; latCap=1; latSpace=0;
        while(!FINISHED) {
          POSTYPE oldPos=THEPOS;
          latinizeMatch();
          if (oldPos==THEPOS) { OutWriteByte(NEXTBYTE); COPY_BYTE_SKIP; }
        }
      }
      if(outBytes) OutWriteByte(0);
      free(tmp);
    } } return(outBytes);
}
static inline void doLatSpace() {
  if(latSpace) {
    OutWriteByte(' ');
    latSpace = 0;
  }
}
static void latinizeMatch() {
  POSTYPE oldPos=THEPOS;
  int nb = NEXTBYTE;
  if (latCap || latSpace) {
    if (nb >= '0' && nb <= '9') latSpace = 0; /* 1:1 */
    else if(nb >= 'A' && nb <= 'Z') {
      latCap = 0; doLatSpace();
    } else if(nb >= 'a' && nb <= 'z') {
      doLatSpace();
      if(latCap) {
        latCap = 0;
        OutWriteByte(nb-('a'-'A')); return;
      }
    } else switch(nb) {
      case 0xC3:
        { int nb2 = NEXTBYTE;
          switch(nb2) {
          case 0x80: case 0x81: case 0x88: case 0x89:
          case 0x8c: case 0x8d: case 0x92: case 0x93:
          case 0x99: case 0x9a:
            doLatSpace();
            latCap=0; break;
          case 0xa0: case 0xa1: case 0xa8: case 0xa9:
          case 0xac: case 0xad: case 0xb2: case 0xb3:
          case 0xb9: case 0xba:
            doLatSpace();
            if (latCap) {
              OutWriteByte(0xC3);
              OutWriteByte(nb2-0x20); latCap=0; return;
            }
          } break; }
      case 0xC4:
        { int nb2 = NEXTBYTE;
          switch(nb2) {
          case 0x80: case 0x92: case 0x9a: case 0xaa:
            doLatSpace();
            latCap=0; break;
          case 0x81: case 0x93: case 0x9b: case 0xab:
            doLatSpace();
            if (latCap) {
              OutWriteByte(0xC4);
              OutWriteByte(nb2-1); latCap=0; return;
            }
          } break; }
      case 0xC5:
        { int nb2 = NEXTBYTE;
          switch(nb2) {
          case 0x8c: case 0xaa:
            doLatSpace();
            latCap=0; break;
          case 0x8d: case 0xab:
            doLatSpace();
            if (latCap) {
              OutWriteByte(0xC5);
              OutWriteByte(nb2-1); latCap=0; return;
            }
          } break; }
      case 0xC7:
        { int nb2 = NEXTBYTE;
          switch(nb2) {
          case 0x8d: case 0x8f: case 0x91: case 0x93:
          case 0x95: case 0x97: case 0x99: case 0x9b:
            doLatSpace();
            latCap=0; break;
          case 0x8e: case 0x90: case 0x92: case 0x94:
          case 0x96: case 0x98: case 0x9a: case 0x9c:
            doLatSpace();
            if (latCap) {
              OutWriteByte(0xC7);
              OutWriteByte(nb2-1); latCap=0; return;
            }
          } break; }
      }
  }
  switch(nb) {
  case 0xE2: /* could be opening quote */
    if(NEXTBYTE==0x80) switch(NEXTBYTE) {
      case 0x98: case 0x9c:
        OutWriteByte(' '); latSpace = 0;
      }
    break;
  case 0xE3: /* could be Chinese stop or list-comma */
    if(NEXTBYTE==0x80) switch(NEXTBYTE) {
      case 0x81:
      OutWriteByte(','); latSpace = 1; return;
      case 0x82:
      OutWriteByte('.'); latSpace = 1;
      latCap=1; return;
    } break;
  case 0xEF: /* could be full-width ascii */
    switch(NEXTBYTE) {
    case 0xBC:
      {
        int b=NEXTBYTE;
        if (b >= 0x81 && b <= 0xbf) {
          int punc = b-(0x81-'!');
          switch(punc) {
          case '(': OutWriteByte(' '); latSpace = 0;
          }
          OutWriteByte(punc);
          if (punc >= 0x90 && punc <= 0x99) latSpace = 0;
          else switch(punc) {
            case '!': case '.': case '?':
              latCap = 1; /* fall through */
            case ')': case ',':
            case ':': case ';':
              latSpace = 1;
            }
          return;
        }
        break;
      }
    case 0xBD:
      {
        int b=NEXTBYTE;
        if (b >= 0x80 && b <= 0x9d) {
          /* TODO: capitalise if it's a letter (but probably not needed in most annotations) */
          OutWriteByte(b-(0x80-'`')); return;
        }
      } break;
    } break;
  }
  SETPOS(oldPos);
}
"""
  have_annotModes = library # only ruby is needed by the Android code
elif windows_clipboard:
  c_preamble = br"""/*

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
  if cfn: c_preamble=c_preamble.replace(b"annoclip.c",B(cfn))
  c_defs = br"""static int near(char* string) {
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
  have_annotModes = False # only ruby is needed by the windows_clipboard code
else:
  c_preamble = br"""
#include <stdio.h>
#include <string.h>

/* To include this code in another program,
   define the ifndef'd macros below + define Omit_main */
"""
  c_defs = br"""#ifndef NEXTBYTE
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
"""
  have_annotModes = True
if have_annotModes:
  c_defs = br"""
#ifndef Default_Annotation_Mode
#define Default_Annotation_Mode ruby_markup
#endif

enum {
  annotations_only,
  ruby_markup,
  brace_notation,
  segment_only} annotation_mode = Default_Annotation_Mode;
""" + c_defs
  c_switch1=br"""switch (annotation_mode) {
  case annotations_only: OutWriteDecompressP(annot); COPY_BYTE_SKIPN(numBytes); break;
  case ruby_markup:"""
  c_switch2=br"""break;
  case brace_notation:
    OutWriteByte('{');
    for(;numBytes;numBytes--)
      OutWriteByte(NEXT_COPY_BYTE);
    OutWriteByte('|'); OutWriteDecompressP(annot);
    OutWriteByte('}'); break;
  case segment_only:
    for(;numBytes;numBytes--)
      OutWriteByte(NEXT_COPY_BYTE); break;
  }"""
  c_switch3 = b"if (annotation_mode == ruby_markup) {"
  c_switch4 = b"} else o(numBytes,annot);"
else: c_switch1=c_switch2=c_switch3=c_switch4=b""

c_preamble += b'#include <stdlib.h>\n'
if sharp_multi: c_preamble += b'#include <ctype.h>\n'
if zlib: c_preamble += b'#include "zlib.h"\n'
if sharp_multi: c_preamble += b"static int numSharps=0;\n"

version_stamp = B(time.strftime("generated %Y-%m-%d by ")+__doc__[:__doc__.index("(c)")].strip())

c_start = b"/* -*- coding: "+B(outcode)+b" -*- */\n/* C code "+version_stamp+b" */\n"
c_start += c_preamble+br"""
enum { ybytes = %%YBYTES%% }; /* for Yarowsky-like matching, minimum readahead */
static int nearbytes = ybytes;
#define setnear(n) (nearbytes = (n))
""" + c_defs + br"""static int needSpace=0;
static void s() {
  if (needSpace) OutWriteByte("""
if have_annotModes: c_start += b"annotation_mode==segment_only?'-':' '); /* (hyphen is probably the best separator character if our binary will be used for Gradint's espeak_preprocessors option) */"
else: c_start += b"' ');"
c_start += br"""
  else needSpace=1; /* for after the word we're about to write (if no intervening bytes cause needSpace=0) */
} static void s0() {
  if (needSpace) { OutWriteByte("""
if have_annotModes: c_start += b"annotation_mode==segment_only?'-':' '"
else: c_start += b"' '"
c_start += br"""); needSpace=0; }
}""" + decompress_func + br"""

static void c(int numBytes) {
  /* copyBytes, needSpace unchanged */
  for(;numBytes;numBytes--)
    OutWriteByte(NEXT_COPY_BYTE);
}
static void o(int numBytes,const char *annot) {
  s();""" + c_switch1 + br"""
    OutWriteStr("<ruby><rb>");
    for(;numBytes;numBytes--)
      OutWriteByte(NEXT_COPY_BYTE);
    OutWriteStr("</rb><rt>"); OutWriteDecompressP(annot);
    OutWriteStr("</rt></ruby>"); """+c_switch2+br""" }
static void o2(int numBytes,const char *annot,const char *title) {"""+c_switch3+br"""
    s();
    OutWriteStr("<ruby title=\""); OutWriteDecompress(title);
    OutWriteStr("\"><rb>");
    for(;numBytes;numBytes--)
      OutWriteByte(NEXT_COPY_BYTE);
    OutWriteStr("</rb><rt>"); OutWriteDecompressP(annot);
    OutWriteStr("</rt></ruby>"); """+c_switch4+b"}"

if not sharp_multi: c_start = c_start.replace(b"OutWriteDecompressP",b"OutWriteDecompress")
if not compress: c_start = c_start.replace(b"OutWriteDecompress",b"OutWriteStr") # and hence OutWriteDecompressP to OutWriteStrP

c_end = br"""
void matchAll() {"""
if zlib: c_end += b"  if(!data) init();\n"
c_end += br"""  while(!FINISHED) {
    POSTYPE oldPos=THEPOS;
    topLevelMatch();
    if (oldPos==THEPOS) { needSpace=0; OutWriteByte(NEXTBYTE); COPY_BYTE_SKIP; }
  }
}"""

# (innerHTML support should be OK at least from Chrome 4 despite MDN compatibility tables not going back that far)
annotation_font = [b"Times New Roman"] # Android has NotoSerif but you can't select it by name, it's mapped from "Times New Roman" (tested in Android 4.4, Android 10 and Android 12, however in Android 12 it does not work for printing, so we'll override it to "sans-serif" in Android 11+ below)
# there's a more comprehensive list in the windows_clipboard code below, but those fonts are less likely found on Android
# jsAddRubyCss is Android-only.  Browser extensions instead use extension_rubycss.
jsAddRubyCss=b"all_frames_docs(function(d) { if(d.rubyScriptAdded==1 || !d.body) return; var e=d.createElement('span'); e.innerHTML='<style>ruby{display:inline-table !important;vertical-align:bottom !important;-webkit-border-vertical-spacing:1px !important;padding-top:0.5ex !important;margin:0px !important;}ruby *{display: inline !important;vertical-align:top !important;line-height:1.0 !important;text-indent:0 !important;text-align:center !important;padding-left:0px !important;padding-right:0px !important;}rb{display:table-row-group !important;font-size:100% !important;}rt{"
if android_template: jsAddRubyCss += b"-webkit-user-select:'+(ssb_local_annotator.getIncludeAll()?'text':'none')+' !important;" # because some users want to copy entire phrases to other tools where inline annotation gets in the way, but other users want the annotations (and copying one word at a time via the popup box is slow).  This (plus our JS fix) narrows things down only if Copy is in use, not extended popup options e.g. Translate. (Incidentally, user-select:all on rb doesn't work in Android 10 as of 2021-01, so better use 'text' or 'auto')
jsAddRubyCss += b"display:table-header-group !important;font-size:100% !important;line-height:1.1 !important;font-family: "+b", ".join(annotation_font)+b" !important;}"
jsAddRubyCss += b"rt:not(:last-of-type){font-style:italic;opacity:0.5;color:purple}" # for 3line mode (assumes rt/rb and rt/rt/rb)
jsAddRubyCss += b"rp{display:none!important}"+B(extra_css).replace(b"'",br"\'")+b"'"
if epub: jsAddRubyCss += br"""+((location.href.slice(0,12)=='http://epub/')?'ol{list-style-type:disc!important}li{display:list-item!important}nav[*|type="page-list"] ol li,nav[epub\\:type="page-list"] ol li{display:inline!important;margin-right:1ex}':'')""" # LI style needed to avoid completely blank toc.xhtml files that style-out the LI elements and expect the viewer to add them to menus etc instead (which hasn't been implemented here); OL style needed to avoid confusion with 2 sets of numbers (e.g. <ol><li>preface<li>1. Chapter One</ol> would get 1.preface 2.1.Chapter One unless turn off the OL numbers)
if android_print: jsAddRubyCss += b"+' @media print { .ssb_local_annotator_noprint, #ssb_local_annotator_bookmarks { visibility: hidden !important; }'+(ssb_local_annotator.printNeedsCssHack()?' rt { font-family: sans-serif !important; }':'')+' }'"
if android_template: jsAddRubyCss += br"""+(ssb_local_annotator.getDevCSS()?'ruby:not([title]){border:thin blue solid} ruby[title~="||"]{border:thin blue dashed}':'')""" # (use *= instead of ~= if the || is not separated on both sides with space)
jsAddRubyCss += b"+'</style>'"
if known_characters: jsAddRubyCss += b"""+'<style id="ssb_hide0">rt.known{display: none !important}</style>'"""
def sort20px(singleQuotedStr): # 20px is relative to zoom
  assert singleQuotedStr.startswith(b"'") and singleQuotedStr.endswith(b"'")
  if not android_template: return singleQuotedStr
  return singleQuotedStr.replace(b"20px",b"'+Math.round(20/Math.pow((ssb_local_annotator.canCustomZoom()?ssb_local_annotator.getRealZoomPercent():100)/100,0.6))+'px") # (do allow some scaling, but not by the whole zoom factor)
def bookmarkJS():
  "Returns inline JS expression (to be put in parens) that evaluates to HTML fragment to be added for bookmarks, and event-setup code to be added after (as Content-Security-Policy could be unsafe-inline + unsafe-eval)"
  assert not '"' in android, "bookmarkJS needs re-implementing if --android URL contains quotes: please %-escape it"
  should_show_bookmarks = B("(location.href=='"+android.replace("'",r"\'")+"'&&!document.noBookmarks)") # noBookmarks is used for handling ACTION_SEND, since it has the same href (TODO @lower-priority: use different href instead?)
  are_there_bookmarks = b"ssb_local_annotator.getBMs().replace(/,/g,'')"
  show_bookmarks_string = br"""'<div style="border: green solid">'+(function(){var c='<h3>Bookmarks you added</h3><ul>',a=ssb_local_annotator.getBMs().split(','),i;for(i=0;i<a.length;i++)if(a[i]){var s=a[i].indexOf(' ');var url=a[i].slice(0,s),title=a[i].slice(s+1).replace(/%2C/g,',');c+='<li>[<a style="color:red;text-decoration:none" href="javascript:if(confirm(\'Delete '+title.replace(/\'/g,"&apos;").replace(/"/g,"&quot;")+"?')){ssb_local_annotator.deleteBM(ssb_local_annotator.getBMs().split(',')["+i+']);location.reload()}">Delete</a>] <a style="color:blue;text-decoration:none" href="'+url+'">'+title+'</a>'}return c+'</ul>'})()+'</div>'""" # TODO: use of confirm() will include the line "the page at file:// says", could do without that (but reimplementing will need complex callbacks rather than a simple 'if').  The javascript: here is OK as we assume there's no Content-Security-Policy on our start page where should_show_bookmarks is true.
  show_bookmarks_string = are_there_bookmarks+b"?("+show_bookmarks_string+b"):''"
  should_suppress_toolset=[
    b"location.href.slice(0,7)=='file://'", # e.g. assets URLs
    b"document.noBookmarks",
    # "location.href=='about:blank'", # for the 'loading, please wait' on at least some Android versions (-> we set noBookmarks=1 in handleIntent instead)
  ]
  if epub: should_suppress_toolset.append(b"location.href.slice(0,12)=='http://epub/'")
  should_suppress_toolset = b"("+b"||".join(should_suppress_toolset)+b")"
  toolset_openTag = sort20px(br"""'<span id="ssb_local_annotator_bookmarks" style="display: block !important; left: 0px; right: 0px; bottom: 0px; margin: auto !important; position: fixed !important; z-index:2147483647; -moz-opacity: 0.8 !important; opacity: 0.8 !important; text-align: center !important"><span style="display: inline-block !important; vertical-align: top !important; border: #1010AF solid !important; background: #1010AF !important; color: white !important; font-size: 20px !important; overflow: auto !important">'""") # need to select a background that doesn't 'invert' too much by whatever algorithm forceDarkAllowed uses; 1010AF at opacity 0.8 = 4040BF on white
  toolset_closeTag = b"'</span></span>'"
  emoji_supported = br"(function(){var c=document.createElement('canvas');if(!c.getContext)return;c=c.getContext('2d');if(!c.fillText)return;c.textBaseline='top';c.font='32px Arial';c.fillText('\ud83d\udd16',0,0);return c.getImageData(16,16,1,1).data[0]})()" # these emoji are typically supported on Android 4.4 but not on Android 4.1
  bookmarks_emoji = br"""'>\ud83d\udd16</a> &nbsp; <a href="#" id="ssb_local_annotator_b2">\ud83d\udccb</a> &nbsp; """
  if android_print: bookmarks_emoji += br"""'+(ssb_local_annotator.canPrint()?('<a id="ssb_local_annotator_b3" href="#">'+ssb_local_annotator.canPrint()+'</a> &nbsp; '):'')+'""" # don't need bookmarks_noEmoji equivalent, because pre-4.4 devices can't print anyway
  bookmarks_emoji += br"""<span id=annogenFwdBtn style="display: none"><a href="#">\u27a1\ufe0f</a> &nbsp;</span> <a id="ssb_local_annotator_b5" href="#">\u274c'"""
  bookmarks_noEmoji = br"""' style="color: white !important">Bookmark</a> <a href="#" id="ssb_local_annotator_b2" style="color: white !important">Copy</a> <a id=annogenFwdBtn style="display: none" href="#" style="color: white !important">Fwd</a> <a id="ssb_local_annotator_b5" href="#" style="color: white !important">X'"""
  toolset_string = toolset_openTag+br"""+'<a id="ssb_local_annotator_b1" href="#"'+(ssb_local_annotator_toolE?("""+bookmarks_emoji+b"):("+bookmarks_noEmoji+br"))+'</a>'+"+toolset_closeTag # if not emoji_supported, could delete the above right: 40%, change border to border-top, and use width: 100% !important; margin: 0pt !important; padding: 0pt !important; left: 0px; text-align: justify; then add a <span style="display: inline-block; width: 100%;"></span> so the links are evenly spaced.  BUT that increases the risk of overprinting a page's own controls that might be fixed somewhere near the bottom margin (there's currently no way to get ours back after closure, other than by navigating to another page)
  # TODO: (don't know how much more room there is on smaller devices, but) U+1F504 Reload (just do window.location.reload)
  toolset_string = should_suppress_toolset+b"?'':("+toolset_string+b")"
  
  unconditional_inject = b"ssb_local_annotator_toolE="+emoji_supported
  # Highlighting function, currently depending on android_print (calls canPrint, and currently no other way to save highlights, TODO: figure out how we can save the highlights in a manner that's stable against document changes and annotation changes with newer app versions)
  if android_print:
    p = br""";ssb_local_annotator_highlightSel=function(colour){var r=window.getSelection().getRangeAt(0);var s=document.getElementsByTagName('ruby'),i,d=0;for(i=0;i < s.length && !r.intersectsNode(s[i]); i++);for(;i < s.length && r.intersectsNode(s[i]); i++){d=1;s[i].setAttribute('style','background:'+colour+'!important');if(!window.doneWarnHighl){window.doneWarnHighl=true;ssb_local_annotator.alert('','','This app cannot yet SAVE your highlights. They may be lost when you leave.'+(ssb_local_annotator.canPrint()?' Save as PDF to keep them.':''))}}if(!d)ssb_local_annotator.alert('','','This tool can highlight only annotated words. Select at least one annotated word and try again.')};if(!document.gotSelChg){document.gotSelChg=true;document.addEventListener('selectionchange',function(){var i=document.getElementById('ssb_local_annotator_HL');if(window.getSelection().isCollapsed || document.getElementsByTagName('ruby').length < 9) i.style.display='none'; else i.style.display='block'})}function doColour(c){return '<span style="background:'+c+' !important" data-c="'+c+'">'+(ssb_local_annotator_toolE?'\u270f':'M')+'</span>'}return """+sort20px(br"""'<button id="ssb_local_annotator_HL" style="display: none; position: fixed !important; background: white !important; border: red solid !important; color: black !important; right: 0px; top: 3em; font-size: 20px !important; z-index:2147483647; -moz-opacity: 1 !important; opacity: 1 !important; overflow: auto !important;">'""")+br"""+doColour('yellow')+doColour('cyan')+doColour('pink')+doColour('inherit')+'</button>'"""
    if android_audio:
      p=p.replace(b"ssb_local_annotator_highlightSel=",br"""ssb_local_annotator_playSel=function(){var r=window.getSelection().getRangeAt(0);var s=document.getElementsByTagName('ruby'),i,d=0;for(i=0;i < s.length && !r.intersectsNode(s[i]); i++);var t=new Array();for(;i < s.length && r.intersectsNode(s[i]); i++) t.push(s[i].getElementsByTagName('rb')[0].innerText); ssb_local_annotator.sendToAudio(t.join(''))};ssb_local_annotator_highlightSel=""").replace(b"+'</button>'",br"""+'<span>'+(ssb_local_annotator_toolE?'\ud83d\udd0a':'S')+'</span></button>'""")
      if android_audio_maxWords: p=p.replace(b"ssb_local_annotator.sendToAudio",b"if(t.length > %d) ssb_local_annotator.alert('','','Limit %d words!'); else ssb_local_annotator.sendToAudio" % (android_audio_maxWords,android_audio_maxWords))
    unconditional_inject += p
  unconditional_inject = b"(function(){"+unconditional_inject+b"})()"
  event_handlers = b"""
function annogenAddHandler1(id,func){var e=document.getElementById(id);if(e)e.addEventListener('click',func)} /* waits for full click (avoiding scroll-start) but more likely to have side-effects in sites' own event handlers */
function annogenAddHandler2(id,func){var e=document.getElementById(id);if(e){var f=function(e){func();if(e&&e.stopPropagation){e.stopPropagation();e.preventDefault();if(e.stopImmediatePropagation)e.stopImmediatePropagation()}};e.addEventListener('click',f,true);e.addEventListener('touchstart',f,true)}} /* tries to override sites' document-level event capture routines changing the document just before printing (e.g. de-selecting something) */
annogenAddHandler2('ssb_local_annotator_b1',function(){ssb_local_annotator.addBM((location.href+' '+(document.title?document.title:location.hostname?location.hostname:'untitled')).replace(/,/g,'%2C'))});
annogenAddHandler2('ssb_local_annotator_b2',function(){ssb_local_annotator.copy(location.href,true)});
annogenAddHandler1('annogenFwdBtn',function(){history.go(1)});
annogenAddHandler1('ssb_local_annotator_b5',function(){var e=document.getElementById('ssb_local_annotator_bookmarks');e.parentNode.removeChild(e)});
"""
  if android_print:
    event_handlers += b"annogenAddHandler2('ssb_local_annotator_b3',function(){ssb_local_annotator.print()});" # DO have to wrap the ssb_local_annotator funcs in a function() or get "ReferenceError: NPObject deleted" on Android 4.4
    event_handlers += b"var a=document.getElementById('ssb_local_annotator_HL'); if(a) for(a=a.firstChild;a;a=a.nextSibling)a.addEventListener('click',function(colour){return colour?function(){ssb_local_annotator_highlightSel(colour)}:ssb_local_annotator_playSel}(a.getAttribute('data-c')));"
    if not android_audio: event_handlers=event_handlers.replace(b"return colour?function",b"return function").replace(b":ssb_local_annotator_playSel",b"")
  return unconditional_inject+b"+("+should_show_bookmarks+b"?("+show_bookmarks_string+b"):("+toolset_string+b"))", event_handlers
if bookmarks: jsAddRubyCss += b"+("+bookmarkJS()[0]+b")"
jsAddRubyCss += b";d.body.insertBefore(e,d.body.firstChild)"
if bookmarks: jsAddRubyCss += b";"+bookmarkJS()[1]
jsAddRubyCss += b";d.rubyScriptAdded=1 })" # end of all_frames_docs call for add-ruby
jsAddRubyCss += b";if(!window.doneHash){var h=window.location.hash.slice(1);if(h&&document.getElementById(h)) window.hash0=document.getElementById(h).offsetTop}" # see below
jsAddRubyCss += b"tw0()" # perform the first annotation scan after adding the ruby (calls all_frames_docs w.annotWalk)
jsAddRubyCss += b";if(!window.doneHash && window.hash0){window.hCount=10*2;window.doneHash=function(){var e=document.getElementById(window.location.hash.slice(1)); if(e.offsetTop==window.hash0 && --window.hCount) setTimeout(window.doneHash,500); e.scrollIntoView()};window.doneHash()}" # and redo jump-to-ID if necessary (e.g. Android 4.4 Chrome 33 on EPUBs), but don't redo this every time doc length changes on Android. setTimeout loop because rendering might take a while with large documents on slow devices.

class JsBlock:
  def __init__(self,l=b"",r=b""):
    self.start,self.end = l,r
    self.mid = []
  def a(self,i): self.mid.append(i)
  def r(self):
    return self.start+b"".join(self.mid)+self.end

def jsAnnot(for_android=True,for_async=False):
  # Android or browser JS-based DOM annotator.  Return value becomes the js_common string in the Android Java: must be escaped as if in single-quoted Java string.
  # for_android True: provides AnnotIfLenChanged, annotScan, all_frames_docs etc
  # for_android False: just provides annotWalk, assumed to be called as-needed by user JS (doesn't install timers etc) and calls JS annotator instead of Java one
  # for_async (browser_extension): provides MutationObserver (assumed capable browser if running the extension)
  assert not (for_android and for_async), "options are mutually exclusive"
  if sharp_multi:
    if for_android: annotNo = b"ssb_local_annotator.getAnnotNo()"
    elif for_async: annotNo = b"document.aType" # set by the startup sendMessage callback in content.js (frontend needs it for KeepRuby logic)
    else: annotNo = b"aType" # will be in JS context
  else: annotNo = b"0" # TODO: could take out relevant code altogether
  
  r = br"""var leaveTags=['SCRIPT','STYLE','TITLE','TEXTAREA','OPTION'], /* we won't scan inside these tags ever */
  
  mergeTags=['EM','I','B','STRONG']; /* we'll merge 2 of these the same if they're leaf elements */"""

  if for_android: r += br"""
  function annotPopAll(e){
    /* click handler: alert box for glosses etc. Now we have a Copy button, it's convenient to put the click handler on ALL ruby elements, not just ones with title; beware compatibility with sites that disable unsafe-inline and/or unsafe-eval in their Content-Security-Policy headers. */
    if(e.currentTarget) e=e.currentTarget;
    function f(c){ /* scan all text under c */
      var i=0,r='',cn=c.childNodes;
      for(;i < cn.length;i++) r+=(cn[i].firstChild?f(cn[i]):(cn[i].nodeValue?cn[i].nodeValue:''));
      return r } ssb_local_annotator.alert(f(e.firstChild),' '+f(e.firstChild.nextSibling),e.title||'') };
  function all_frames_docs(c) {
    /* Call function c on all documents in the window */
    var f=function(w) {
      try{w.document}catch(E){return} /* (cross-domain issues?) */
      if(w.frames && w.frames.length) {
        var i; for(i=0; i<w.frames.length; i++)
          f(w.frames[i]) }
      c(w.document) };
    f(window) };
  function AnnotIfLenChanged() { if(window.lastScrollTime){if(new Date().getTime() < window.lastScrollTime+500) return} else { window.lastScrollTime=1; window.addEventListener('scroll',function(){window.lastScrollTime = new Date().getTime()}) } var getLen=function(w) { var r=0; try{w.document}catch(E){return r} if(w.frames && w.frames.length) { var i; for(i=0; i<w.frames.length; i++) r+=getLen(w.frames[i]) } if(w.document && w.document.body && w.document.body.innerHTML) r+=w.document.body.innerHTML.length; return r },curLen=getLen(window); if(curLen!=window.curLen) { annotScan(); window.curLen=getLen(window) } else return 'sameLen' };
  function tw0() { all_frames_docs(function(d){annotWalk(d,d,false,false)}) };
  function annotScan() {"""+B(extra_js)+jsAddRubyCss+b"};"
  
  r += br"""
function annotWalk(n"""
  if not for_async: r += b",document" # multiple frames
  if for_android: r += b",inLink,inRuby"
  elif for_async and existing_ruby_lang_regex: r += b",nfOld,nfNew" # as the callback 'need to fix [replace]' element is not necessarily at current level, see below
  r += br""") {
    /* Our main DOM-walking code */
  var c;"""
  CheckExistingRuby = None
  if for_async and (existing_ruby_lang_regex or existing_ruby_js_fixes):
    # we might delete or change existing ruby
    CheckExistingRuby = JsBlock(b"var nf=!!nfOld,nReal=n,kR=1; if(!nf){",b"}")
  elif not for_async:
    CheckExistingRuby = JsBlock(b"var nf=false,kR=1;") # nf = "need to fix" as there was already ruby on the page; kR = do we keep existing ruby (can be set to false later)
  if CheckExistingRuby:
    if for_android: SetNF=JsBlock(b"if(!inRuby) {",b"}")
    else: SetNF = JsBlock()
    SetNF.a(js_check_for_existing_ruby_and_set_nf)
    CheckExistingRuby.a(SetNF.r())
    if for_async: FixupRuby = JsBlock(b"if(nf) { nfOld=nReal;n=n.cloneNode(true);nfNew=document.createElement('span');nfNew.className='_adjust0';nfNew.appendChild(n);nfNew.oldHtml=n.outerHTML;",b"}") # and in for_async, the replaceChild for this cloneNode does not happen unless we ALSO can annotate the rb (so it shouldn't disturb ruby that's completely unrelated to the charsets we annotate)
    else: FixupRuby = JsBlock(b"var nReal = n; if(nf) { n=n.cloneNode(true);",b"}") # if messing with existing ruby, first do it offline for speed (and need to set nReal here because didn't set it above if we're not for_async)
    if existing_ruby_lang_regex: KeepRuby=JsBlock(b"kR=document.documentElement.lang.match(["+b",".join(b"/"+B(l)+b"/" for l in B(existing_ruby_lang_regex).split(b','))+b"]["+annotNo+b"]);if(kR){",b"}")
    else: KeepRuby = JsBlock() # unconditional
    if existing_ruby_js_fixes: KeepRuby.a(B(existing_ruby_js_fixes))
    FixupRuby.a(KeepRuby.r())
    if KeepRuby.start: # not unconditionally keeping ruby: need an 'else delete'
      if for_async: FixupRuby.a(br"""else {var zap=function(t){while(1){var r=n.getElementsByTagName(t);if(!r.length)break;r[0].parentNode.removeChild(r[0])}};zap('rt');zap('rp');while(1){var r=n.getElementsByTagName('ruby');if(!r.length)break;r[0].parentNode.replaceChild(document.createTextNode(r[0].innerText),r[0])}}""") # not allowed to write to innerHTML in Firefox extensions
      else: FixupRuby.a(br"""else {var n2=n.cloneNode(false);n2.innerHTML=n.innerHTML.replace(/<r[pt].*?<[/]r[pt]>/g,'').replace(/<[/]?(?:ruby|rb)[^>]*>/g,'');n=n2}""")
    CheckExistingRuby.a(FixupRuby.r())
    r += CheckExistingRuby.r()
  # else no CheckExistingRuby (and consequently no nf or kR defined): existing ruby will be double-annotated.  This happens if for_async and not existing_ruby_lang_regex.

  r += js_check_wbr_and_mergeTags
  r += br"""
    /* Recurse into nodes, or annotate new text */
    c=n.firstChild; """
  if not for_async: r += b"var cP=null;"
  r += br"""while(c){
      var cNext=c.nextSibling;
      switch(c.nodeType) {
        case 1:
          if(leaveTags.indexOf(c.nodeName)==-1 && c.className!='_adjust0') {"""
  if not for_async:
    r += b"if(!nf &&" # TODO: unless existing_ruby_lang_regex is set to always delete no matter what
    if for_android: r += b"!inRuby &&"
    r += br"""cP && c.previousSibling!=cP && c.previousSibling.lastChild.nodeType==1) n.insertBefore(document.createTextNode(' '),c); /* space between the last RUBY and the inline link or em etc (but don't do this if the span ended with unannotated punctuation like em-dash or open paren) */"""
  if existing_ruby_shortcut_yarowsky and for_android: r += br"""
            var setR=false; if(!inRuby) {setR=(c.nodeName=='RUBY');if(setR)ssb_local_annotator.setYShortcut(true)}
            annotWalk(c,document,inLink||(c.nodeName=='A'&&!!c.href)||c.nodeName=='BUTTON',inRuby||setR);
            if(setR)ssb_local_annotator.setYShortcut(false)"""
  else:
    r += b"annotWalk(c"
    if not for_async: r += b",document"
    if for_android: r += b",inLink||(c.nodeName=='A'&&!!c.href)||c.nodeName=='BUTTON',inRuby||(c.nodeName=='RUBY')"
    if for_async and CheckExistingRuby: r += b",nfOld,nfNew"
    r += b");"
  r += br"""
          } break;
        case 3: {var cnv=c.nodeValue.replace(/\u200b/g,'').replace(/\B +\B/g,'');"""
  if for_async:
    r += br"""
            if(!cnv.match(/^\s*$/)) {
                (function(n"""
    if CheckExistingRuby: r += b",nfOld,nfNew"
    r += br""",c,cnv){
                    var newNode=document.createElement('span');
                    newNode.className='_adjust0';"""
    if CheckExistingRuby: r += b"if(!nfNew)"
    r += b"newNode.oldTxt=cnv;"
    if ybytes: r += br"""
    var inline=["SPAN","STRONG","EM","B","I","U","FONT","A","RUBY","RB","RP","RT"]; function cStop(p){return !p||(p.nodeType==1&&inline.indexOf(p.nodeName)==-1)} function cNorm(p){return unescape(encodeURIComponent(p.nodeValue.replace(/\s+/g,'').replace(/^[+*0-9]*$/,'')))} /* omit simple footnote link */
    function contextLeft(p) {
      var accum=""; while(accum.length<MAX_CONTEXT) {
        while(!p.previousSibling){p=p.parentNode;if(cStop(p))return accum}
        p=p.previousSibling;if(cStop(p))return accum;
        while(p.nodeType==1&&p.lastChild){if(inline.indexOf(p.nodeName)==-1)return accum; else if(p.nodeName=="RT"||p.nodeName=="RP") break; p=p.lastChild}
        if(p.nodeType==3) accum=cNorm(p)+accum
      } return accum }
    function contextRight(p) {
      var accum=""; while(accum.length<MAX_CONTEXT) {
        while(!p.nextSibling){p=p.parentNode;if(cStop(p))return accum}
        p=p.nextSibling;if(cStop(p))return accum;
        while(p.nodeType==1&&p.firstChild){if(inline.indexOf(p.nodeName)==-1)return accum; else if(p.nodeName=="RT"||p.nodeName=="RP") break; p=p.firstChild}
        if(p.nodeType==3) accum+=cNorm(p)
      } return accum }
                    chrome.runtime.sendMessage({'t':cnv,'l':contextLeft(c),'r':contextRight(c)},(function(nv){""".replace(b"MAX_CONTEXT",(b"%d"%ybytes_max))
    else: r += br"""
                    chrome.runtime.sendMessage({'t':cnv},(function(nv){ """
    r += br"""
                        if(nv && (nv!=cnv || nv.trim()!=cnv.trim())) {
                            try {
                                for(const t of new DOMParser().parseFromString('<span> '+nv+' </span>','text/html').body.firstChild.childNodes) newNode.appendChild(t.cloneNode(true));
                                var a=newNode.getElementsByTagName('ruby'),i; for(i=0; i < a.length; i++) if(a[i].title) (function(e){e.addEventListener('click',(function(){alert(e.title)}))})(a[i])
                            } catch(err) { console.log(err.message) }
                            try{n.replaceChild(newNode, c)}catch(err){ /* already done */ }"""
    if CheckExistingRuby: r += br"""
                            if(nfOld) {
try{nfOld.parentNode.replaceChild(nfNew,nfOld)}catch(err){ /* already done */ }
    /* Fix damage we did to existing ruby, keeping new titles */
      var a=nfNew?nfNew.getElementsByTagName('ruby'): /* not sure how it gets here when nfOld is non-null */ [],i;
      for(i=0; i < a.length; i++) {
        if(i && a[i].previousSibling==a[i-1]) a[i].parentNode.insertBefore(document.createTextNode(" "),a[i]);
        var t=[],chgFmt=0;
        while(1) {
          var r=a[i].getElementsByTagName('ruby');
          if(!r.length) break; r=r[0];
          var tt=r.getAttribute('title');
          if(tt) t.push(tt);
          var rl=r.lastChild;while(rl.previousSibling&&rl.nodeName!="RB"){rl=rl.previousSibling;}
          chgFmt=r.firstChild.nodeName=="RT";
          r.parentNode.replaceChild(document.createTextNode(rl.innerText),r);
        }
        t = t.join(' || '); if(t){a[i].setAttribute('title',t);(function(e){e.addEventListener('click',(function(){alert(e.title)}))})(a[i])}
        if(chgFmt) { /* patch up 3-line */ var rt=document.createElement("rt"); rt.appendChild(document.createTextNode(t.match(/[^/(;]*/)[0])); a[i].insertBefore(rt,a[i].firstChild); var v=a[i].lastChild;if(v.nodeName=="RT"){a[i].removeChild(v);v.nodeName="RB";a[i].insertBefore(v,a[i].firstChild.nextSibling)} }
      }
}"""
    r += br"""
                        }
                    }))})(n"""
    if CheckExistingRuby: r += b",nfOld,nfNew"
    r += b",c,cnv)}" # this } matches if(!cnv.match...) {
  else: # not for_async
    if for_android: annotateFunc = b"ssb_local_annotator.annotate"
    elif not sharp_multi and not glossfile and not known_characters:
      annotateFunc = b"Annotator.annotate" # just takes str
    else:
      annotateFunc = b"function(s){return Annotator.annotate(s"
      if sharp_multi: annotateFunc += b",aType"
      if glossfile: annotateFunc += b",numLines"
      if known_characters: annotateFunc += b",numKnownGroups"
      annotateFunc += b")}"
    r += b"var nv="+annotateFunc+br"""(cnv); if(nv!=cnv) { var newNode=document.createElement('span'); newNode.className='_adjust0'; if(inLink) newNode.inLink=1; n.replaceChild(newNode, c); try { newNode.innerHTML=nv } catch(err) { alert(err.message) }"""
    if for_android: r += br"""if(!inLink){var a=newNode.getElementsByTagName('ruby'),i;for(i=0; i < a.length; i++) a[i].addEventListener('click',annotPopAll)}"""
    r += b"}" # if nv != cnv
  r += b"}}" # case 3, switch
  if not for_async: r += b"cP=c;"
  r += b"c=cNext"
  if not for_async:
    r += b";if(!nf &&"  # TODO: as above: unless existing_ruby_lang_regex is set to always delete it no matter what
    r += br"""!inRuby && c && c.previousSibling!=cP && c.previousSibling.previousSibling && c.previousSibling.firstChild.nodeType==1) n.insertBefore(document.createTextNode(' '),c.previousSibling) /* space after the inline link or em etc */"""
  r += b"}" # while c
  if not for_async:
    r += br"""
    /* Batch-fix any damage we did to existing ruby.
       Keep new titles; normalise the markup so our 3-line option still works.
       Also ensure all ruby is space-separated like ours,
       so our padding CSS overrides don't give inconsistent results */
    if(nf) {"""
    if existing_ruby_lang_regex:
      KeepRuby = JsBlock(b"if(kR){",b"} else nReal.parentNode.replaceChild(n,nReal)")
    else: KeepRuby = JsBlock() # unconditional
    KeepRuby.a(br"""
        nReal.innerHTML='<span class=_adjust0>'+n.innerHTML.replace(/<ruby[^>]*>((?:<[^>]*>)*?)<span class=.?_adjust0.?>((?:<span><[/]span>)?[^<]*)(<ruby[^>]*><rb>.*?)<[/]span>((?:<[^>]*>)*?)<rt[^>]*>(.*?)<[/]rt><[/]ruby>/ig,function(m,open,lrm,rb,close,rt){var a=rb.match(/<ruby[^>]*/g),i;for(i=1;i < a.length;i++){var b=a[i].match(/title=["]([^"]*)/i);if(b)a[i]=' || '+b[1]; else a[i]=''}var attrs=a[0].slice(5).replace(/title=["][^"]*/,'$&'+a.slice(1).join('')); return lrm+'<ruby'+attrs+'><rb>'+open.replace(/<rb>/ig,'')+rb.replace(/<ruby[^>]*><rb>/g,'').replace(/<[/]rb>.*?<[/]ruby> */g,'')+close.replace(/<[/]rb>/ig,'')+'</rb><rt""")
    if known_characters: KeepRuby.a(br"""'+(rb.indexOf('<rt>')==-1?' class=known':'')+'""") # if all the <rt> we generated are <rt class=known> then propagate this to the existing ruby
    KeepRuby.a(br""">'+rt+'</rt></ruby>'}).replace(/<[/]ruby>((<[^>]*>|\u200e)*?<ruby)/ig,'</ruby> $1').replace(/<[/]ruby> ((<[/][^>]*>)+)/ig,'</ruby>$1 ')+'</span>'""")
    if for_android: KeepRuby.a(br""";
        if(!inLink){var a=function(n){for(n=n.firstChild;n;n=n.nextSibling){if(n.nodeType==1){if(n.nodeName=='RUBY')n.addEventListener('click',annotPopAll);else if(n.nodeName!='A')a(n)}}};a(nReal)}""")
    r += KeepRuby.r()
    r += b"}" # if nf
  r += b"}" # function annotWalk
  if for_async: r += br"""
document.annotWalkOff=1;
chrome.runtime.sendMessage(true,function(r){if(r!=-1){document.aType=r;annotWalk(document)}document.annotWalkOff=(r==-1)});
new window.MutationObserver(function(mut){var i,j;if(!document.annotWalkOff){document.annotWalkOff=1;for(i=0;i<mut.length;i++)for(j=0;j<mut[i].addedNodes.length;j++){var n=mut[i].addedNodes[j],m=n,ok=1;while(ok&&m&&m!=document.body){ok=m.className!='_adjust0';m=m.parentNode}if(ok)annotWalk(n)}window.setTimeout(function(){document.annotWalkOff=0},10)}}).observe(document.body,{childList:true,subtree:true});
""" # TODO: even with annotWalkOff temporarily set to suppress the nested observer trigger, long popups on pages with their own ruby can still take 16+secs on older PCs
  elif for_android: r += br"if(!ssb_local_annotator.getIncludeAll())document.addEventListener('copy',function(e){var s=window.getSelection(),i,c=document.createElement('div');for(i=0;i < s.rangeCount;i++)c.appendChild(s.getRangeAt(i).cloneContents());e.clipboardData.setData('text/plain',c.innerHTML.replace(/<rt.*?<[/]rt>/g,'').replace(/<.*?>/g,''));e.preventDefault()});" # work around user-select:none not always working (and newlines sometimes being added anyway)
  if not for_async:
    r=re.sub(br"\s+",b" ",re.sub(b"/[*].*?[*]/",b"",r,flags=re.DOTALL)) # remove /*..*/ comments, collapse space
    r=re.sub(br'\\(?!u)',br'\\\\',r).replace(b'"',br'\"')
  return r

js_check_for_existing_ruby_and_set_nf = b"""
var rShared=false;
for(c=n.firstChild; c; c=c.nextSibling) {
  if(c.nodeType==1) {
    if(c.nodeName=='RUBY') nf=true; else rShared=true
  }
  if(nf&&rShared) { /* put ruby parts in separate span so it can be batched-changed without interfering with event handlers on other elements such as links at same level */
    nf=false; var rubySpan=false; c=n.firstChild;
    while(c) { var c2=c.nextSibling;
      if(!rubySpan && c.nodeType==1 && c.nodeName=='RUBY') {
        rubySpan=document.createElement('span');
        n.insertBefore(rubySpan,c)
      } if(rubySpan) {
        if(c.nodeType!=1 || c.nodeName=='RUBY') {
          n.removeChild(c); rubySpan.appendChild(c)
        } else rubySpan=false
      } c=c2
    }
    break
  }
}"""

js_check_wbr_and_mergeTags = br"""
    /* Check for WBR and mergeTags */
    function isTxt(n) { return n && n.nodeType==3 && n.nodeValue && !n.nodeValue.match(/^\s*$/)};
    var c=n.firstChild; while(c) {
      var ps = c.previousSibling, cNext = c.nextSibling;
      if (c.nodeType==1) { if((c.nodeName=='WBR' || (c.nodeName=='SPAN' && c.childNodes.length<=1 && (!c.firstChild || (c.firstChild.nodeValue && c.firstChild.nodeValue.match(/^\s*$/))))) && isTxt(cNext) && isTxt(ps) /* e.g. <span id="page8" class="pageNum">&#160;</span> in mid-word; rm ONLY if non-whitespace text immediately before/after: beware of messing up JS applications */ ) {
        n.removeChild(c);
        cNext.previousSibling.nodeValue+=cNext.nodeValue;
        n.removeChild(cNext); cNext=ps}
      else if(cNext && cNext.nodeType==1 && mergeTags.indexOf(c.nodeName)!=-1 && c.nodeName==cNext.nodeName && c.childNodes.length==1 && cNext.childNodes.length==1 && isTxt(c.firstChild) && isTxt(cNext.firstChild)){
        cNext.firstChild.nodeValue=c.firstChild.nodeValue+cNext.firstChild.nodeValue;
        n.removeChild(c)} }
      c=cNext}
"""

if windows_clipboard: c_end += br"""
#ifdef _WINCE
#define CMD_LINE_T LPWSTR
#else
#define CMD_LINE_T LPSTR
#endif

static void errorExit(char* text) {
  TCHAR msg[500];
  DWORD e = GetLastError();
  wsprintf(msg,TEXT("%hs: %d"),text,e);
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
  if(!hClipMemory) errorExit("GetClipboardData"); // empty clipboard?
  TCHAR*u16 = (TCHAR*)GlobalLock(hClipMemory);
  size_t u8bytes=0; while(u16[u8bytes++]); u8bytes*=3;
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
  strcat(fname,"c.html"); // c for clipboard
  outFile = fopen(fname,"w");
  #endif
  if (!outFile) {
    strcpy(fname,"\\c.html");
    outFile=fopen(fname,"w");
    if (!outFile) errorExit("Cannot write c.html");
  }
  OutWriteStr("<html><head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"><meta name=\"mobileoptimized\" content=\"0\"><meta name=\"viewport\" content=\"width=device-width\"></head><body><style>ruby { display: inline-table; vertical-align: bottom; -webkit-border-vertical-spacing: 1px; padding-top: 0.5ex; } ruby * { display: inline; vertical-align: top; line-height:1.0; text-indent:0; text-align:center; } rb { display: table-row-group; font-size: 100%; } rt { display: table-header-group; font-size: 100%; line-height: 1.1; }</style>\n<!--[if lt IE 8]><style>ruby, ruby *, ruby rb, ruby rt { display: inline !important; vertical-align: baseline !important; padding-top: 0pt !important; } ruby { border: thin grey solid; } </style><![endif]-->\n<!--[if !IE]>-->\n<style>rt { font-family: FreeSerif, Lucida Sans Unicode, Times New Roman, serif !important; }</style>\n<!--<![endif]-->\n<script><!--\nif(navigator.userAgent.match('Edge/'))document.write('<table><tr><td>')\n//--></script><h3>Clipboard</h3>");
  p=pOrig; copyP=p;
  matchAll();
  free(pOrig);
  OutWriteStr("<script><!--\nif(navigator.userAgent.match('Edge/'))document.write('</td></tr></table>')\n//--></script><script><!--\nfunction treewalk(n) { var c=n.firstChild; while(c) { if (c.nodeType==1 && c.nodeName!=\"SCRIPT\" && c.nodeName!=\"TEXTAREA\" && !(c.nodeName==\"A\" && c.href)) { treewalk(c); if(c.nodeName==\"RUBY\" && c.title && !c.onclick) c.onclick=function(){alert(this.title)} } c=c.nextSibling } } function tw() { treewalk(document.body); window.setTimeout(tw,5000); } treewalk(document.body); window.setTimeout(tw,1500);\n//--></script></body></html>");
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
elif not library:
  c_end += br"""
#ifndef Omit_main
int main(int argc,char*argv[]) {
  int i=1;"""
  if sharp_multi:
    c_end += br"""
  if(i<argc && isdigit(*argv[i])) { numSharps=atoi(argv[i++]);"""
    if annotation_map: c_end += br"numSharps="+annotMap("numSharps")+b";"
    c_end += b" }"
  c_end += br"""
  for(; i<argc; i++) {
    if(!strcmp(argv[i],"--help")) {"""
  if sharp_multi: c_end += br"""
      puts("Parameters: [annotation number] [options]");"""
  c_end += br"""
      puts("--ruby   = output ruby markup (default)");
      puts("--raw    = output just the annotations without the base text");
      puts("--seg    = output just a segmentation of the base text");
      puts("--braces = output as {base-text|annotation}");
      return 0;
    } else if(!strcmp(argv[i],"--ruby")) {
      annotation_mode = ruby_markup;
    } else if(!strcmp(argv[i],"--raw")) {
      annotation_mode = annotations_only;
    } else if(!strcmp(argv[i],"--seg")) {
      annotation_mode = segment_only;
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

# ANDROID: setDefaultTextEncodingName("utf-8") is included as it might be needed if you include file:///android_asset/ URLs in your app (files put into assets/) as well as remote URLs.  (If including ONLY file URLs then you don't need to set the INTERNET permission in Manifest, but then you might as well pre-annotate the files and use a straightforward static HTML app like http://ssb22.user.srcf.net/indexer/html2apk.html )
# Also we get shouldOverrideUrlLoading to return true for URLs that end with .apk .pdf .epub .mp3 etc so the phone's normal browser can handle those (search code below for ".apk" for the list) (TODO: API 1's shouldOverrideUrlLoading was deprecated in API 24; if they remove it, we may have to provide both to remain compatible?)
android_upload = all(x in os.environ for x in ["KEYSTORE_FILE","KEYSTORE_USER","KEYSTORE_PASS","SERVICE_ACCOUNT_KEY"]) and not os.environ.get("ANDROID_NO_UPLOAD","")
android_manifest = br"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="%%JPACKAGE%%" android:versionCode="1" android:versionName="1.0" android:sharedUserId="" android:installLocation="preferExternal" >
<uses-permission android:name="android.permission.INTERNET" />"""
# The versionCode, versionName and sharedUserId attributes in the above are also picked up on in the code below
if epub: android_manifest += br"""<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="22" />"""
# API 23 (Android 6) needs extra code to request this permission
# (which we don't do), but Send URIs should arrive as content://
# (they should be content:// on Android 5).
# Android 13 (API 33) apps shouldn't declare READ_EXTERNAL_STORAGE.
# On API 19 (Android 4.4), the external storage permission is:
# (1) needed for opening epubs from a file manager,
# (2) automatically propagated throughout sharedUserId (if one of your apps has it then they will all get it),
# (3) persists until the next reboot if you reinstall your apps without it.
# Points 2 and 3 can make developers think it's not really needed :-(
if pleco_hanping or tts_js:
  android_manifest+=b"\n<queries>"
  if pleco_hanping: android_manifest += br"""
<package android:name="com.pleco.chinesesystem" />
<package android:name="com.embermitre.hanping.cantodict.app.pro" />
<package android:name="com.embermitre.hanping.app.pro" />
<package android:name="com.embermitre.hanping.app.lite" />"""
  if tts_js: android_manifest += br"""
<intent><action android:name="android.intent.action.TTS_SERVICE" /></intent>"""
  android_manifest+=b"\n</queries>"
android_manifest += br"""
<uses-sdk android:minSdkVersion="1" android:targetSdkVersion="33" />
<supports-screens android:largeScreens="true" android:xlargeScreens="true" />
<application android:icon="@drawable/ic_launcher" android:label="@string/app_name" android:theme="@style/AppTheme" android:networkSecurityConfig="@xml/network_security_config" >
<service android:name=".BringToFront" android:exported="false"/>
<activity android:configChanges="orientation|screenSize|keyboardHidden" android:name="%%JPACKAGE%%.MainActivity" android:label="@string/app_name" android:launchMode="singleTask" android:exported="true" >
<intent-filter><action android:name="android.intent.action.MAIN" /><category android:name="android.intent.category.LAUNCHER" /></intent-filter>
<intent-filter><action android:name="android.intent.action.SEND" /><category android:name="android.intent.category.DEFAULT" /><data android:mimeType="text/plain" /></intent-filter>"""
if epub: android_manifest += br"""
<intent-filter> <action android:name="android.intent.action.VIEW" /> <category android:name="android.intent.category.DEFAULT" /> <category android:name="android.intent.category.BROWSABLE" /> <data android:scheme="file"/> <data android:scheme="content"/> <data android:host="*" /> <data android:pathPattern="/.*\\.epub"/> </intent-filter> <intent-filter> <action android:name="android.intent.action.VIEW" /> <category android:name="android.intent.category.DEFAULT" /> <data android:scheme="file"/> <data android:scheme="content"/> <data android:mimeType="application/epub+zip"/> </intent-filter>"""
android_manifest += b"\n</activity></application></manifest>\n"
android_layout = br"""<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" android:layout_height="fill_parent" android:layout_width="fill_parent" android:orientation="vertical">
  <WebView android:id="@+id/browser" android:layout_height="match_parent" android:layout_width="match_parent" />
</LinearLayout>
"""
if android_template == "blank": android_template = B(r"""<html><head><meta name="mobileoptimized" content="0"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head><body><h3>"""+app_name+r"</h3>URL_BOX_GOES_HERE</body></html>")
elif android_template:
  android_template = open(android_template,'rb').read()
  if not b"</body" in android_template: warn("--android-template has no \"</body\" so won't have a version stamp")
# android_url_box: one user saw an "Offline EPUB file" link and said "I have to give it an EPUB, that's too complicated" without noticing the URL box immediately afterwards, so we'd better put the URL box first.
# Another user still found the EPUB link distracting, so let's make it a button (to match the Go button) rather than a 'different'-looking link (if most users want the Web browser then we probably don't want EPUB to be the _first_ thing they notice).
# As we're using forceDarkAllowed to allow 'force dark mode' on Android 10, we MUST specify background and color.  Left unspecified results in input elements that always have white backgrounds even in dark mode, in which case you get white on white = invisible text.  "inherit" works; background #ededed looks more shaded and does get inverted; background-image linear-gradient does NOT get inverted (so don't use it).
# And as fewer browsers display "http" users might be less likely to recognise that as the start of the URL, so don't use "http://" for the box's placeholder.
android_url_box = br"""<div style="border: thin dotted grey">
<form style="margin:0em;padding-bottom:0.5ex" onSubmit="var v=this.url.value;if(typeof annotUrlTrans!='undefined'){var u=annotUrlTrans(v);if(typeof u!='undefined')v=u}if(v.slice(0,4)!='http')v='http://'+v;if(v.indexOf('.')==-1)ssb_local_annotator.alert('','','The text you entered is not a Web address. Please enter a Web address like www.example.org');else{this.t.parentNode.style.width='50%';this.t.value='LOADING: PLEASE WAIT';window.location.href=v}return false"><table style="width: 100%"><tr><td style="width:1em;margin:0em;padding:0em;display:none" id=displayMe align=left><button style="width:100%;background:#ededed;color:inherit" onclick="document.forms[document.forms.length-1].url.value='';document.getElementById('displayMe').style.display='none';return false">X</button></td><td style="margin: 0em; padding: 0em"><input type=text style="width:100%;background:inherit;color:inherit" placeholder="Web page" name=url></td><td style="width:1em;margin:0em;padding:0em" align=right><input type=submit name=t value=Go style="width:100%;background:#ededed;color:inherit"></td></tr></table></form>"""
# Now all other controls:
if epub: android_url_box += br"""
<button style="margin-top: 0.5ex;background:#ededed;color:inherit" onclick="ssb_local_annotator.getEPUB()">EPUB</button>"""
android_url_box += br"""
<button style="margin-top: 0.5ex;background:#ededed;color:inherit" onclick="location.href='file:///android_asset/clipboard.html'">Clipboard</button>
<script>
function viewZoomCtrls() {
   window.setTimeout(function(){
   var t=document.getElementById("zI");
   var r=t.getBoundingClientRect();
   if (r.bottom > window.innerHeight) t.scrollIntoView(false); else if (r.top < 0) t.scrollIntoView();
   },200);
}
function zoomOut() {
   var l=ssb_local_annotator.getZoomLevel();
   if (l > 0) { ssb_local_annotator.setZoomLevel(--l); document.getElementById("zL").innerHTML=""+ssb_local_annotator.getZoomPercent()+"%" }
   if (!l) document.getElementById("zO").disabled=true;
   else document.getElementById("zI").disabled=false;
   viewZoomCtrls();
}
function zoomIn() {
   var l=ssb_local_annotator.getZoomLevel(),m=ssb_local_annotator.getMaxZoomLevel();
   if (l < m) { ssb_local_annotator.setZoomLevel(++l); document.getElementById("zL").innerHTML=""+ssb_local_annotator.getZoomPercent()+"%" }
   if (l==m) document.getElementById("zI").disabled=true;
   else document.getElementById("zO").disabled=false;
   viewZoomCtrls();
}
if(ssb_local_annotator.canCustomZoom()) document.write('<div style="display:inline-block;margin-top: 0.5ex"><button id=zO onclick="zoomOut()" style="background:#ededed;color:inherit;font-size:90%">A</button><span id=zL>'+ssb_local_annotator.getZoomPercent()+'%</span><button id=zI onclick="zoomIn()" style="background:#ededed;color:inherit;font-size:110%">A</button></div> ');"""
if sharp_multi and annotation_names: android_url_box += br"""
modeNames=["""+b",".join((b'"'+B(x)+b'"') for x in annotation_names.split(','))+br"""];document.write('<select style="margin-top: 0.5ex" onChange="ssb_local_annotator.setAnnotNo(this.selectedIndex<0?0:this.selectedIndex);location.reload()">');var c=ssb_local_annotator.getAnnotNo();for(var i=0;i < modeNames.length;i++)document.write('<option'+(i==c?' selected':'')+'>'+modeNames[i]+'</option>');document.write('</select> ');"""
if known_characters:
  L = [i for i in [re.sub(br'\s+',b'',l) for l in open(known_characters,'rb').readlines()] if i]
  knownCharsGroups = [] ; s = 0
  while s < len(L):
    if s>=800: inc=100
    elif s>=300: inc=50
    elif s>=100: inc=20
    else: inc=10
    if s+inc > len(L): warn("UI code currently assumes known_characters line count will be a round number, but it isn't.  Last option will be too high.") # TODO handle this properly?
    knownCharsGroups.append(b"".join(L[s:s+inc])) ; s += inc
  knownCharsGroupsArray = b'['+b','.join(b"'"+i+b"'" for i in knownCharsGroups)+b']'
  android_url_box += br"""
var hFreq="""+knownCharsGroupsArray+br""",known=ssb_local_annotator.getKnownCharacters();
document.write('<select style="margin-top: 0.5ex" onchange="ssb_local_annotator.setKnownCharacters(hFreq.slice(0,this.selectedIndex<0?0:this.selectedIndex).join('+"''"+'));location.reload()"><option'+(known==""?' selected':'')+'>Annotate all</option>');
for(var dx=0,N=10,k='';dx<"""+B(str(len(knownCharsGroups)))+br""";dx++,N+=(N>=800?100:N>=300?50:N>=100?20:10)) document.write('<option'+(known==(k+=hFreq[dx])?' selected':'')+'>Leave '+N+' known</option>');
document.write('</select> ');""" # TODO: could add a 'custom' option that's selected if none of the others are, but will need some way of editing it (and might need to nicely handle the case of 'frequency table corrected during an app upgrade')
android_url_box += br"""
document.write('<button style="margin-top: 0.5ex;background:#ededed;color:inherit;padding-left:0px;padding-right:0.2ex" onclick="ssb_local_annotator.setIncludeAll(!ssb_local_annotator.getIncludeAll());location.reload();return false"><input type=checkbox'+(ssb_local_annotator.getIncludeAll()?' checked':'')+'>Include """
if annotation_names:
  if sharp_multi: android_url_box += br"'+modeNames[ssb_local_annotator.getAnnotNo()].replace(/^.*?([^ ]+)( [(].*)?$/g,'$1')+'" # so e.g. "Cantonese Sidney Lau (with numbers)" -> "Lau" (as we want this shorter than the buttons)
  else: android_url_box += B(annotation_names) # assume it's just one name
else: android_url_box += br"annotation"
android_url_box += br""" with Copy</button>');
var m=navigator.userAgent.match(/Android ([0-9]+)\./); if(m && m[1]<5) document.write("<div id=insecure style=\"background-color: pink; color: black\"><b>In-app browsers receive no security updates on Android&nbsp;4.4 and below, so be careful where you go.</b> It might be safer to copy/paste or Share text to it when working with an untrusted web server. <button onclick=\"document.getElementById('insecure').style.display='none'\">OK</button></div>");
var c=ssb_local_annotator.getClip(); if(c && c.match(/^https?:\/\/[-!#%&+,.0-9:;=?@A-Z\/_|~]+$/i)){document.forms[document.forms.length-1].url.value=c;document.getElementById("displayMe").style.display="table-cell"}</script>"""
# API 19 (4.4) and below has no browser updates.  API 17 (4.2) and below has known shell exploits for CVE-2012-6636 which requires only that a site (or network access point) can inject arbitrary Javascript into the HTTP stream.  Not sure what context the resulting shell runs in, but there are probably escalation attacks available.  TODO: insist on working offline-only on old versions?
android_url_box += b'</div>'
if android_template:
  android_template = android_template.replace(b"URL_BOX_GOES_HERE",android_url_box)
  if not b"VERSION_GOES_HERE" in android_template:
    android_template = android_template.replace(b"</body",b"VERSION_GOES_HERE</body")
android_version_stamp = br"""<script>document.write('<address '+(ssb_local_annotator.isDevMode()?'onclick="if(((typeof ssb_local_annotator_dblTap==\'undefined\')?null:ssb_local_annotator_dblTap)==null) window.ssb_local_annotator_dblTap=setTimeout(function(){window.ssb_local_annotator_dblTap=null},500); else { clearTimeout(ssb_local_annotator_dblTap);window.ssb_local_annotator_dblTap=null;ssb_local_annotator.setDevCSS();ssb_local_annotator.alert(\'\',\'\',\'Developer mode: words without glosses will be boxed in blue. Compile time %%TIME%%\')}" ':'')+'>%%DATE%% version</address>')</script>""" # ensure date itself is on LHS (especially if we're at the bottom), as zoom control on API levels 3 through 13 can overprint RHS of last thing on page. This date should help with "can I check your app is up-to-date" encounters + ensures there's an extra line on the document in case zoom control overprints last line.  Time available in developer mode as might have more than one alpha release per day and want to check got latest.
android_src = br"""package %%JPACKAGE%%;
import android.annotation.*;
import android.app.Activity;
import android.content.*;
import android.net.Uri;
import android.os.*;
import android.view.KeyEvent;
import android.webkit.*;"""
if android_print: android_src += br"""
import java.lang.reflect.InvocationTargetException;
import android.print.*;"""
if tts_js: android_src += br"""
import android.speech.tts.*;"""
android_src += br"""
import android.widget.Toast;
import java.io.*;
import java.util.regex.*;
import java.util.zip.ZipInputStream;
public class MainActivity extends Activity {
    %%JPACKAGE%%.Annotator annotator;
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
        try {
            setContentView(R.layout.activity_main);
        } catch (android.view.InflateException e) {
            // this can occur if "Android System Webview" on Android 5 happens to be in the process of updating, see Chromium bug 506369
            android.app.AlertDialog.Builder d = new android.app.AlertDialog.Builder(this); d.setTitle("Cannot start WebView"); d.setMessage("Your device may be updating WebView. Close this app and try again in a few minutes."); d.setPositiveButton("Bother",null);
            try { d.create().show(); }
            catch(Exception e0) {
                Toast.makeText(this, "Cannot start WebView. Close and try when system update finished.",Toast.LENGTH_LONG).show();
            }
            return; // TODO: close app after dialog dismissed? (setNegativeButton?) currently needs Back pressed
        }
        browser = (WebView)findViewById(R.id.browser);
        // ---------------------------------------------
        // Delete the following line if you DON'T want to be able to use chrome://inspect in desktop Chromium when connected via USB to Android 4.4+
        if(AndroidSDK >= 19) WebView.setWebContentsDebuggingEnabled(true);
        // ---------------------------------------------"""
if pleco_hanping: android_src += br"""
        try { getApplicationContext().getPackageManager().getPackageInfo("com.pleco.chinesesystem", 0); gotPleco = true; dictionaries++; } catch (android.content.pm.PackageManager.NameNotFoundException e) {}
        if(AndroidSDK >= 11) for(int i=0; i<3; i++) try { hanpingVersion[i]=getApplicationContext().getPackageManager().getPackageInfo(hanpingPackage[i],0).versionCode; if(hanpingVersion[i]!=0) { dictionaries++; if(i==1) break /* don't also check Lite if got Pro*/; } } catch (android.content.pm.PackageManager.NameNotFoundException e) {}
        // ---------------------------------------------"""
android_src += br"""
        if(AndroidSDK >= 7 && AndroidSDK < 33) { try { WebSettings.class.getMethod("setAppCachePath",new Class[] { String.class }).invoke(browser.getSettings(),getApplicationContext().getCacheDir().getAbsolutePath()); WebSettings.class.getMethod("setAppCacheEnabled",new Class[] { Boolean.class }).invoke(browser.getSettings(),true); } catch (NoSuchMethodException e) {} catch (IllegalAccessException e) {} catch (InvocationTargetException e) {} } // not to be confused with the normal browser cache (call methods dynamically because platform 33 can't compile this)
        if(AndroidSDK<=19 && savedInstanceState==null) browser.clearCache(true); // (Android 4.4 has Chrome 33 which has Issue 333804 XMLHttpRequest not revalidating, which breaks some sites, so clear cache when we 'cold start' on 4.4 or below.  We're now clearing cache anyway in onDestroy on Android 5 or below due to Chromium bug 245549, but do it here as well in case onDestroy wasn't called last time e.g. swipe-closed in Activity Manager)
        browser.getSettings().setJavaScriptEnabled(true);
        browser.setWebChromeClient(new WebChromeClient());"""
if android_template: android_src += br"""
        float fs = getResources().getConfiguration().fontScale; // from device accessibility settings
        if (fs < 1.0f) fs = 1.0f; // bug in at least some versions of Android 8 returns 0 for fontScale
        final float fontScale=fs*fs; // for backward compatibility with older annogen (and pre-Android 4 version that still sets setDefaultFontSize) : unconfirmed reports say the OS scales the size units anyway, so we've been squaring fontScale all along, which is probably just as well because old Android versions don't offer much range in their settings"""
android_src += br"""
        @TargetApi(1)
        class A {
            public A(MainActivity act) {
                this.act = act;"""
if sharp_multi or known_characters or android_template: android_src += br"""
                SharedPreferences sp=getSharedPreferences("ssb_local_annotator",0);"""
if sharp_multi: android_src += br"""
                annotNo = Integer.valueOf(sp.getString("annotNo", "0")); setSharpMultiPattern();"""
if known_characters: android_src += br"""
                knownChars = sp.getString("knownChars", ""); setKnownCharsPattern();"""
if android_template: android_src += br"""
                if(canCustomZoom()) setZoomLevel(Integer.valueOf(sp.getString("zoom", "4")));
                setIncludeAll(sp.getString("includeAll", "f").equals("t"));"""
android_src += br"""
            }
            MainActivity act; String copiedText="";"""
if existing_ruby_shortcut_yarowsky: android_src += br"""
            @JavascriptInterface public void setYShortcut(boolean v) { if(annotator!=null) annotator.shortcut_nearTest=v; }"""
if sharp_multi: android_src += br""" int annotNo;
            @JavascriptInterface public void setAnnotNo(int no) { annotNo = no;
                android.content.SharedPreferences.Editor e;
                do {
                e = getSharedPreferences("ssb_local_annotator",0).edit();
                e.putString("annotNo",String.valueOf(annotNo));
                } while(!e.commit()); setSharpMultiPattern();
            }
            void setSharpMultiPattern() {
                smPat=Pattern.compile("<rt>"+new String(new char["""+annotMap()+br"""]).replace("\0","[^#]*#")+"([^#]*?)(#.*?)?</rt>"); // don't need to deal with <rt class=known> here, as we're working before that's applied
            }
            Pattern smPat=Pattern.compile("<rt>([^#]*?)(#.*?)?</rt>");
            @JavascriptInterface public int getAnnotNo() { return annotNo; }"""
if known_characters: android_src += br"""
            @JavascriptInterface public String getKnownCharacters() { return knownChars; }
            @JavascriptInterface public void setKnownCharacters(String known) {
                knownChars = known;
                android.content.SharedPreferences.Editor e;
                do {
                e = getSharedPreferences("ssb_local_annotator",0).edit();
                e.putString("knownChars",known);
                } while(!e.commit());
                setKnownCharsPattern();
            }
            String knownChars = "";
            Pattern kcPat;
            void setKnownCharsPattern() {
                if (knownChars.isEmpty()) kcPat=null;
                else kcPat=Pattern.compile("(<rb>["+knownChars+"]+</rb><rt)(>.*?</rt>)");
            }
"""
if android_template: android_src += br"""
            int zoomLevel; boolean includeAllSetting;
            @JavascriptInterface public int getZoomLevel() { return zoomLevel; }
            final int[] zoomPercents = new int[] {"""+B(','.join(str(x) for x in (list(reversed([int((0.9**x)*100) for x in range(5)][1:]))+[int((1.1**x)*100) for x in range(15)])))+br"""};
            @JavascriptInterface public int getZoomPercent() { return zoomPercents[zoomLevel]; }
            @JavascriptInterface public int getRealZoomPercent() { return Math.round(zoomPercents[zoomLevel]*fontScale); }
            @JavascriptInterface public int getMaxZoomLevel() { return zoomPercents.length-1; }
            @JavascriptInterface @TargetApi(14) public void setZoomLevel(final int level) {
                act.runOnUiThread(new Runnable(){
                    @Override public void run() {
                        browser.getSettings().setTextZoom(Math.round(zoomPercents[level]*fontScale));
                    }
                });
                android.content.SharedPreferences.Editor e;
                do { e = getSharedPreferences("ssb_local_annotator",0).edit();
                     e.putString("zoom",String.valueOf(level));
                } while(!e.commit());
                zoomLevel = level;
            }
            @JavascriptInterface public boolean getIncludeAll() { return includeAllSetting; }
            @JavascriptInterface public void setIncludeAll(boolean i) {
                android.content.SharedPreferences.Editor e;
                do { e = getSharedPreferences("ssb_local_annotator",0).edit();
                     e.putString("includeAll",i?"t":"f");
                } while(!e.commit());
                includeAllSetting = i;
            }"""
android_src += br"""
            @JavascriptInterface public String annotate(String t) throws java.util.zip.DataFormatException { if(annotator==null) return t; String r=annotator.annotate(t);"""
if sharp_multi: android_src += br"""
                Matcher m = smPat.matcher(r);
                StringBuffer sb=new StringBuffer();
                while(m.find()) m.appendReplacement(sb, "<rt>"+m.group(1)+"</rt>");
                m.appendTail(sb); r=sb.toString();"""+B(annotation_postprocess)
if known_characters: android_src += br"""
                if(kcPat!=null) {
                    Matcher k = kcPat.matcher(r);
                    StringBuffer s2=new StringBuffer();
                    while(k.find()) k.appendReplacement(s2, k.group(1)+" class=known"+k.group(2));
                    k.appendTail(s2); r=s2.toString();
                }"""
if epub: android_src += br"""if(loadingEpub && r.contains("<ruby")) r=(r.startsWith("<ruby")?"<span></span>":"")+"\u200e"+r;""" # &lrm; needed due to &rlm; in the back-navigation links of some footnotes etc; empty span is to help annotWalk space-repair.  Fix in v0.6899: use Unicode rather than &lrm; as the latter is not recognised as "valid XML" by Android 10, leading to innerHTML assignment throwing an exception, which in previous versions went uncaught and led to unexplained disappearance of text instead of annotation, usually at 1 chunk per second due to runTimerLoop.  (This issue was not manifest on Android 9 and below.)
android_src += br"""return r; }
            @JavascriptInterface public void alert(String text,String annot,String gloss) {
                class DialogTask implements Runnable {
                    String tt,aa,gg;
                    DialogTask(String t,String a,String g) { tt=t; aa=a; gg=g; }
                    @Override public void run() {
                        android.app.AlertDialog.Builder d = new android.app.AlertDialog.Builder(act);
                        if(tt.length()>0) d.setTitle(tt+aa);"""
if pleco_hanping:
  if android_audio: maxDicts,xtraItems=0,2
  else: maxDicts,xtraItems=1,1
  android_src += br"""
                        if(tt.length()>0 && dictionaries>%d) {
                            int nItems=dictionaries+%d; if(gg.length()==0) --nItems;
                            String[] items=new String[nItems]; int i=0;
                            if(gg.length()>0) items[i++]=gg;
                            if(hanpingVersion[0]!=0) items[i++]="\u25b6CantoDict";
                            if(hanpingVersion[1]!=0) items[i++]="\u25b6Hanping Pro";
                            if(hanpingVersion[2]!=0) items[i++]="\u25b6Hanping Lite";
                            if(gotPleco) items[i++]="\u25b6Pleco";""" % (maxDicts,xtraItems)
  if android_audio: android_src += br"""
                            items[i++]="\ud83d\udd0aAudio";
  """
  android_src += br"""
                            // TODO: (if gloss exists) to prevent popup disappearing if items[0] is tapped, use d.setAdapter instead of d.setItems?  items must then implement android.widget.ListAdapter with: boolean isEnabled(int position) { return position!=0; } boolean areAllItemsEnabled() { return false; } int getCount(); Object getItem(int position); long getItemId(int position) { return position; } int getItemViewType(int position) { return -1; } boolean hasStableIds() { return true; } boolean isEmpty() { return false; } void registerDataSetObserver(android.database.DataSetObserver observer) {} void unregisterDataSetObserver(android.database.DataSetObserver observer) {}  but still need to implement android.view.View getView(int position, android.view.View convertView, android.view.ViewGroup parent) (init convertView or get a new one) and int getViewTypeCount()
                            d.setItems(items,new android.content.DialogInterface.OnClickListener() {
                                @TargetApi(11) public void onClick(android.content.DialogInterface dialog,int id) {
                                    int test=0,i;
                                    if(gg.length()==0) --test;
                                    for(i=0; i<3; i++) if(hanpingVersion[i]!=0 && ++test==id) { Intent h = new Intent(Intent.ACTION_VIEW); h.setData(new android.net.Uri.Builder().scheme(hanpingVersion[i]<906030000?"dictroid":"hanping").appendEncodedPath((hanpingPackage[i].indexOf("canto")!=-1)?"yue":"cmn").appendEncodedPath("word").appendPath(tt).build()); h.setPackage(hanpingPackage[i]); h.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK | Intent.FLAG_ACTIVITY_NEW_TASK); try { startActivity(h); } catch (ActivityNotFoundException e) { Toast.makeText(act, "Failed. Hanping uninstalled?",Toast.LENGTH_LONG).show(); } }
                                    if(gotPleco && ++test==id) { Intent p = new Intent(Intent.ACTION_MAIN); p.setComponent(new android.content.ComponentName("com.pleco.chinesesystem","com.pleco.chinesesystem.PlecoDroidMainActivity")); p.addCategory(Intent.CATEGORY_LAUNCHER); p.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP); p.putExtra("launch_section", "dictSearch"); p.putExtra("replacesearchtext", tt+aa); try { startActivity(p); } catch (ActivityNotFoundException e) { Toast.makeText(act, "Failed. Pleco uninstalled?",Toast.LENGTH_LONG).show(); } }"""
  if android_audio: android_src += br"""
                                    if(++test==id) { sendToAudio(tt); act.runOnUiThread(new DialogTask(tt,aa,gg)); }"""
  android_src += br"""
                        } });
                        } else"""
android_src += br"""
                        if(gg.length()>0) d.setMessage(gg);
                        d.setNegativeButton("Copy",new android.content.DialogInterface.OnClickListener() {
                                public void onClick(android.content.DialogInterface dialog,int id) { copy(tt+aa+" "+gg,false); }
                        });"""
if pleco_hanping:
  if android_audio: android_src += br"""
                        if(dictionaries==0 && tt.length()>0) d.setNeutralButton("Audio", new android.content.DialogInterface.OnClickListener() {public void onClick(android.content.DialogInterface dialog,int id) {sendToAudio(tt); act.runOnUiThread(new DialogTask(tt,aa,gg));}});"""
  else: android_src += br"""
                        if(dictionaries==1) { /* for consistency with old versions, have a 'middle button' if there's only one recognised dictionary app installed */
                        if(tt.length()==0) { /* Pleco or Hanping button not added if empty title i.e. error/info box */ }
                        else if(gotPleco) d.setNeutralButton("Pleco", new android.content.DialogInterface.OnClickListener() {
                            public void onClick(android.content.DialogInterface dialog,int id) {
                                Intent i = new Intent(Intent.ACTION_MAIN);
                                i.setComponent(new android.content.ComponentName("com.pleco.chinesesystem","com.pleco.chinesesystem.PlecoDroidMainActivity"));
                                i.addCategory(Intent.CATEGORY_LAUNCHER);
                                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                                i.putExtra("launch_section", "dictSearch");
                                i.putExtra("replacesearchtext", tt+aa);
                                try { startActivity(i); } catch (ActivityNotFoundException e) { Toast.makeText(act, "Failed. Pleco uninstalled?",Toast.LENGTH_LONG).show(); }
                            }
                        }); else d.setNeutralButton("Hanping", new android.content.DialogInterface.OnClickListener() {
                            @TargetApi(11)
                            public void onClick(android.content.DialogInterface dialog,int id) {
                                int v; for(v=0; hanpingVersion[v]==0; v++);
                                Intent i = new Intent(Intent.ACTION_VIEW);
                                i.setData(new android.net.Uri.Builder().scheme(hanpingVersion[v]<906030000?"dictroid":"hanping").appendEncodedPath((hanpingPackage[v].indexOf("canto")!=-1)?"yue":"cmn").appendEncodedPath("word").appendPath(tt).build());
                                i.setPackage(hanpingPackage[v]);
                                i.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK | Intent.FLAG_ACTIVITY_NEW_TASK);
                                try { startActivity(i); } catch (ActivityNotFoundException e) { Toast.makeText(act, "Failed. Hanping uninstalled?",Toast.LENGTH_LONG).show(); }
                            }
                        }); }"""
if glossfile: android_src += br"""
                        if (tt.length()>0) {
                        // TODO: 3-line persist to pop-ups (re-scan the DOM)?
                        // TODO: 3-line persist to other pages? (might be counterproductive to encouraging people not to rely on it)
                        d.setPositiveButton("1/2/3L", // not 1L/2L/3L: on some zoomed-in Android 13 phones it wraps and leaves the "3L" occluded
new android.content.DialogInterface.OnClickListener() { public void onClick(android.content.DialogInterface dialog,int id) { act.runOnUiThread(new Runnable() { @Override public void run() {
                            android.app.AlertDialog.Builder d = new android.app.AlertDialog.Builder(act);"""
if known_characters and glossfile: # TODO: might want a way of getting this choice if known_characters and not glossfile, probably by providing some alternative to the 1/2/3L button in this case
  android_src += br"""
                            if(!knownChars.isEmpty()) {
                                String[] items=new String[2];
                                items[0]=new String("Show all"); items[1]=new String("Hide known");
                                d.setItems(items,new android.content.DialogInterface.OnClickListener() { public void onClick(android.content.DialogInterface dialog,int hideOrNot) {
                                    if(hideOrNot==0) act.runOnUiThread(new Runnable() { @Override public void run() { browser.loadUrl(
"javascript:var h=document.getElementById('ssb_hide0');if(h)h.parentNode.removeChild(h)"
); } }); else act.runOnUiThread(new Runnable() { @Override public void run() { browser.loadUrl(
"javascript:var h=document.getElementById('ssb_hide0');if(!h){h=document.createElement('span');h.setAttribute('id','ssb_hide0');h.innerHTML='<style>rt.known{display:none!important}</style>';document.body.insertBefore(h,document.body.firstChild.nextSibling)}"
); } }); } }); } else"""
if glossfile: android_src += br"""
                            d.setTitle("Choose a format:");
                            d.setPositiveButton("1 line",new android.content.DialogInterface.OnClickListener() { public void onClick(android.content.DialogInterface dialog,int id) { act.runOnUiThread(new Runnable() { @Override public void run() { browser.loadUrl(
"javascript:var l1=document.getElementById('ssb_1Line'),l2=document.getElementById('ssb_2Line');if(l2)l2.parentNode.removeChild(l2);if(!l1){var e=document.createElement('span');e.setAttribute('id','ssb_1Line');e.innerHTML='<style>rt{display:none!important}</style>';document.body.insertBefore(e,document.body.firstChild.nextSibling)}"
); } }); } });
                            d.setNeutralButton("2 lines",new android.content.DialogInterface.OnClickListener() { public void onClick(android.content.DialogInterface dialog,int id) { act.runOnUiThread(new Runnable() { @Override public void run() { browser.loadUrl(
"javascript:var l1=document.getElementById('ssb_1Line'),l2=document.getElementById('ssb_2Line');if(l1)l1.parentNode.removeChild(l1);if(!l2){var e=document.createElement('span');e.setAttribute('id','ssb_2Line');e.innerHTML='<style>rt:not(:last-of-type){display:none!important}</style>';document.body.insertBefore(e,document.body.firstChild.nextSibling)}"
); } }); } });
                            d.setNegativeButton("3 lines",new android.content.DialogInterface.OnClickListener() { public void onClick(android.content.DialogInterface dialog,int id) { act.runOnUiThread(new Runnable() { @Override public void run() { browser.loadUrl(
"javascript:var l1=document.getElementById('ssb_1Line'),l2=document.getElementById('ssb_2Line');if(l1)l1.parentNode.removeChild(l1);if(l2)l2.parentNode.removeChild(l2);var ad0=document.getElementsByClassName('_adjust0');for(i=0;i<ad0.length;i++){ad0[i].innerHTML=ad0[i].innerHTML.replace(/<ruby[^>]*title=\"([^\"]*)\"[^>]*><rb>(.*?)<[/]rb><rt(.*?)>(.*?)<[/]rt><[/]ruby>/g,function(m,title,rb,known,rt){return '<ruby title=\"'+title+'\"><rp>'+rb+'</rp><rp>'+rt+'</rp><rt'+known+'>'+title.split(' || ').map(function(m){return m.replace(/^([(]?[^/(;]*).*/,'$1')}).join(' ')+'</rt><rt'+known+'>'+rt+'</rt><rb>'+rb+'</rb></ruby>'});if(!ad0[i].inLink){var a=ad0[i].getElementsByTagName('ruby'),j;for(j=0;j < a.length; j++)a[j].addEventListener('click',annotPopAll)}} ad0=document.body.innerHTML;ssb_local_annotator.alert('','','3-line definitions tend to be incomplete!')"
/* Above rp elements are to make firstChild etc work in
   dialogue.  Don't do whole document.body.innerHTML, or
   scripts like document.write may execute a second time,
   but DO read innerHTML afterwards to work around bug in
   Chrome 33, otherwise whole document replaced by last
   ad0 found.  Also need the alert box, or document.write
   scripts in the page run twice.  (This 'tend to be
   incomplete' message seems as good as any.  NB the
   glosses are being trimmed.)  onclick= is removed in the
   postprocessing loop due to sites that put unsafe-inline
   in their Content-Security-Policy headers. */
); } }); } });
                            try { d.create().show(); } catch(Exception e) { Toast.makeText(act, "Unable to create popup box",Toast.LENGTH_LONG).show(); }
                        } }); } });
                        } else """
android_src += br"""
                        d.setPositiveButton("OK", null); // or can just click outside the dialog to clear. (TODO: would be nice if it could pop up somewhere near the word that was touched)
                        try { d.create().show(); }
                        catch(Exception e) {
                            Toast.makeText(act, "Unable to create popup box",Toast.LENGTH_LONG).show(); // some reports of WindowManager$BadTokenException crash, maybe users are popping up too many boxes at a time?? catching like this for now
                        }
                    }
                }
                act.runOnUiThread(new DialogTask(text,annot,gloss));
            }
            @JavascriptInterface public String getClip() {
                String r=readClipboard(); if(r.equals(copiedText)) return ""; else return r;
            }
            @JavascriptInterface public boolean isFocused() {
                return _isFocused;
            }"""
if android_template: android_src += br"""
            @JavascriptInterface public boolean canCustomZoom() {
                return AndroidSDK >= 14;
            }"""
if android_print: android_src += br"""
            @JavascriptInterface public String canPrint() {
                if(AndroidSDK >= 24) return "\ud83d\udda8";
                else if(AndroidSDK >= 19) return "<span style=color:black;background:white;padding:0.3ex>P</span>";
                else return "";
            }
            @JavascriptInterface public boolean printNeedsCssHack() {
                return AndroidSDK >= 30; // known good on 29, known bad on 31 (as of 2022-06, at least on Samsung phones; fault not reproduced on Pixel 2 simulated in AVD, with or without updates, but not sure if we can read the device manufacturer from here)
            }
            boolean printing_in_progress = false;
            @TargetApi(19)
            @JavascriptInterface public void print() {
                act.runOnUiThread(new Runnable(){
                    @Override public void run() {
                        if(printing_in_progress) return;
                        printing_in_progress = true;
                        try {
                            ((PrintManager) act.getSystemService(android.content.Context.PRINT_SERVICE)).print("annotated",new PrintDocumentAdapter(){
                                PrintDocumentAdapter delegate=(AndroidSDK >= 21) ? (PrintDocumentAdapter)(WebView.class.getMethod("createPrintDocumentAdapter",new Class[] { String.class }).invoke(browser,"Annotated document")) : browser.createPrintDocumentAdapter(); // (createPrintDocumentAdapter w/out string deprecated in API 21; using introspection so this still compiles with API 19 SDKs e.g. old Eclipse)
                                @Override @SuppressLint("WrongCall") public void onLayout(PrintAttributes a, PrintAttributes b, CancellationSignal c, LayoutResultCallback d, Bundle e) { delegate.onLayout(a, b, c, d, e); }
                                @Override public void onWrite(PageRange[] a, ParcelFileDescriptor b, CancellationSignal c, WriteResultCallback d) { try { delegate.onWrite(a,b,c,d); } catch(IllegalStateException e){Toast.makeText(act, "Print glitch. Press Back and try again.",Toast.LENGTH_LONG).show();} }
                                @Override public void onStart() { browser.setVisibility(android.view.View.INVISIBLE); delegate.onStart(); }
                                @Override public void onFinish() { delegate.onFinish(); browser.setVisibility(android.view.View.VISIBLE); printing_in_progress=false; }
                            },new PrintAttributes.Builder().build());
                        } catch (NoSuchMethodException e) {} catch (IllegalAccessException e) {} catch (InvocationTargetException e) {}
                    }
                });
            }"""
if tts_js: android_src += br"""
            @JavascriptInterface public boolean TTS(String s) { return doTTS(s); }
            @JavascriptInterface public boolean TTSIsSet() { return tts_keep!=null; }
            @JavascriptInterface public String TTSInfo(String voices_to_set) {
                // Optionally init a voice; return voice list.
                // You might need to call this twice, with
                // a delay to let it initialise, to get
                // the list.  Call with "" just to list.
                // 
                // List is likely to be useful in Google's
                // version of Android, but might not be so
                // useful in AOSP (Huawei etc): not tested
                // on their non-Google devices.
                // 
                // Must init a voice before TTSIsSet()==true and TTS() works.
                // (Will be checked for in clipboard.html; you can also check in extra-js)
                // voices_to_set: comma-separated in order of preference (TODO: what if the 'better' one doesn't work due to network or firewall issues?) or "" to find none
                // 
                // Limitation: only one voice may be selected by TTSInfo; subsequent calls just return in-progress or cached list (if changing this, beware of race conditions in the async init)
                // Known bug: after a device is upgraded from Android 11 to Android 12, the first time this app is launched it might select the wrong voice (and e.g. get a UK English voice to read out Google's Pinyin conversion of hanzi), could not reproduce this a second time, suspect race condition with the upgrade scripts finishing off
                // 
                return TTSTest(1,","+voices_to_set+",");
            }"""
if android_template: android_src += br"""
            @TargetApi(17)
            @JavascriptInterface public boolean isDevMode() {
                return ((AndroidSDK==16)?android.provider.Settings.Secure.getInt(getApplicationContext().getContentResolver(),android.provider.Settings.Secure.DEVELOPMENT_SETTINGS_ENABLED,0):((AndroidSDK>=17)?android.provider.Settings.Secure.getInt(getApplicationContext().getContentResolver(),android.provider.Settings.Global.DEVELOPMENT_SETTINGS_ENABLED,0):0)) != 0;
            }
            boolean devCSS = false;
            @JavascriptInterface public void setDevCSS() {
                devCSS = true;
            }
            @JavascriptInterface public boolean getDevCSS() {
                return devCSS;
            }"""
android_src += br"""
            @JavascriptInterface public void bringToFront() {
                if(AndroidSDK >= 3) {
                    startService(new Intent(MainActivity.this, BringToFront.class));
                    nextBackHides = true;
                }
            }
            @JavascriptInterface public boolean canGoForward() { return browser.canGoForward(); }
            @JavascriptInterface public String getSentText() { return sentText; }
            @JavascriptInterface public String getLanguage() { return java.util.Locale.getDefault().getLanguage(); } /* ssb_local_annotator.getLanguage() returns "en", "fr", "de", "es", "it", "ja", "ko" etc */"""
if android_upload: android_src += br"""
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
            }"""
android_src += br"""
            @JavascriptInterface @TargetApi(11) public void copy(String copiedText,boolean toast) {
                this.copiedText = copiedText;
                if(AndroidSDK < Build.VERSION_CODES.HONEYCOMB)
                    ((android.text.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).setText(copiedText);
                else ((android.content.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).setPrimaryClip(android.content.ClipData.newPlainText(copiedText,copiedText));
                if(toast && AndroidSDK<33) Toast.makeText(act, "Copied \""+copiedText+"\"",Toast.LENGTH_LONG).show();
            }"""
if android_audio: android_src += br"""
            @JavascriptInterface public void sendToAudio(final String s) {
                class InjectorTask implements Runnable { InjectorTask() {} @Override public void run() { try { browser.loadUrl("javascript:var src='"""+B(android_audio)+br""""+java.net.URLEncoder.encode(s,"utf-8")+"';if(!window.audioElement || window.audioElement.getAttribute('src')!=src){window.audioElement=document.createElement('audio');window.audioElement.setAttribute('src',src)}window.audioElement.play()"); } catch(java.io.UnsupportedEncodingException e) {} Toast.makeText(act, "Sent \""+s+"\" to audio server",Toast.LENGTH_LONG).show(); } };
                act.runOnUiThread(new InjectorTask());
            }"""
if epub: android_src += br"""
            @JavascriptInterface public void getEPUB() { Intent i = new Intent(Intent.ACTION_GET_CONTENT); i.setType("*/*"); /* application/epub+zip leaves all files unselectable on Android 4.4 */ try { startActivityForResult(i, 8778); } catch (ActivityNotFoundException e) { Toast.makeText(act,"Please install a file manager",Toast.LENGTH_LONG).show(); } }"""
if bookmarks: android_src += br"""
            @SuppressLint("DefaultLocale")
            @JavascriptInterface public void addBM(String p) {
                android.content.SharedPreferences.Editor e;
                do {
                   SharedPreferences sp=getSharedPreferences("ssb_local_annotator",0);
                   String s=sp.getString("prefs", ",");
                   if((","+s).contains(","+p+",")) { // we have to give it a number
                       int count=1; String p2; while(true) {
                           p2=String.format("%s (%d)", p, ++count);
                           if(!(","+s).contains(","+p2+",")) break;
                       } p=p2;
                   }
                   s += p+",";
                   e = sp.edit();
                   e.putString("prefs",s);
                } while(!e.commit());
                Toast.makeText(act, "Added bookmark", Toast.LENGTH_LONG).show();
            }
            @JavascriptInterface public void deleteBM(String p) {
                android.content.SharedPreferences.Editor e; boolean done=false; String s,p2;"""+B("".join(r"""
                try {
                    do {
                        SharedPreferences sp=createPackageContext("%s", 0).getSharedPreferences("ssb_local_annotator",0);
                        p2=","+sp.getString("prefs", ",");
                        s=p2.replaceFirst(Pattern.quote(","+p+","), ",");
                        if(s.equals(p2)) break;
                        e = sp.edit(); done=true;
                        e.putString("prefs",s.substring(1));
                     } while(!e.commit());
                } catch(Exception x) {} if(done) return;""" % p for p in bookmarks.split(",") if not p==jPackage))+br"""
                do {
                   SharedPreferences sp=getSharedPreferences("ssb_local_annotator",0);
                   p2=","+sp.getString("prefs", ",");
                   s=p2.replaceFirst(Pattern.quote(","+p+","), ",");
                   if(s.equals(p2)) break;
                e = sp.edit();
                e.putString("prefs",s.substring(1));
                } while(!e.commit());
            }
            @JavascriptInterface public String getBMs() {
                String s="";"""+B("".join(r"""
                try { s = createPackageContext("%s", 0).getSharedPreferences("ssb_local_annotator",0).getString("prefs", "")+","+s; } catch(Exception e) {}""" % p for p in bookmarks.split(",") if not p==jPackage))+br"""
                return s+getSharedPreferences("ssb_local_annotator",0).getString("prefs", "");
            }""" # and even if not bookmarks:
android_src += b"\n}\n" + b"try { annotator=new %%JPACKAGE%%.Annotator(getApplicationContext()); } catch(Exception e) { Toast.makeText(this,\"Cannot load annotator data!\",Toast.LENGTH_LONG).show(); String m=e.getMessage(); if(m!=null) Toast.makeText(this,m,Toast.LENGTH_LONG).show(); }" # TODO: should we keep a static synchronized annotator instance, in case some version of Android gives us multiple Activity instances and we start taking up more RAM than necessary?
android_src += br"""
        browser.addJavascriptInterface(new A(this),"ssb_local_annotator"); // hope no conflict with web JS
        final MainActivity act = this;
        browser.setWebViewClient(new WebViewClient() {
                @TargetApi(8) @Override public void onReceivedSslError(WebView view, android.webkit.SslErrorHandler handler, android.net.http.SslError error) { Toast.makeText(act,"Cannot check encryption! Carrier redirect? Old phone?",Toast.LENGTH_LONG).show(); if(AndroidSDK<0) handler.cancel(); else handler.proceed(); } // must include both cancel() and proceed() for Play Store, although Toast warning should be enough in our context
                @TargetApi(4) public boolean shouldOverrideUrlLoading(WebView view,String url) {
                    if(url.endsWith(".apk") || url.endsWith(".pdf") || url.endsWith(".epub") || url.endsWith(".mp3") || url.endsWith(".zip")) {
                        // Let the default browser download this file, but prefer not to let EPUB-reader apps intercept the URL: we want it _downloaded_ so we can annotate it, but some users might get confused, so give preference to Chrome or Kindle Silk, starting the Chooser only if neither is installed
                        Intent i=new Intent(Intent.ACTION_VIEW,android.net.Uri.parse(url));
                        if(AndroidSDK < 4) startActivity(i); // no way to specify package preference
                        else { i.setPackage("com.android.chrome"); try { startActivity(i); } catch (ActivityNotFoundException e1) { i.setPackage("com.amazon.cloud9"); try { startActivity(i); } catch (ActivityNotFoundException e2) { i.setPackage(null); startActivity(i); } } }
                        return true;
                    } else {
                        needJsCommon=3; return false;
                    }
                }"""
if epub: android_src += br"""
                @TargetApi(11) public WebResourceResponse shouldInterceptRequest (WebView view, String url) {
                    String epubPrefix = "http://epub/"; // also in handleIntent, and in annogen.py should_suppress_toolset
                    loadingEpub = url.startsWith(epubPrefix); // TODO: what if an epub includes off-site prerequisites? (should we be blocking that?) : setting loadingEpub false would suppress the lrm marks (could make them unconditional but more overhead; could make loadingEpub 'stay on' for rest of session)
                    if (!loadingEpub) return null;
                    SharedPreferences sp=getPreferences(0);
                    String epubUrl=sp.getString("epub","");
                    if(epubUrl.length()==0) return new WebResourceResponse("text/html","utf-8",new ByteArrayInputStream(("epubUrl setting not found").getBytes()));
                    Uri epubUri=Uri.parse(epubUrl);
                    String part=null; // for directory listing
                    boolean getNextPage = false;
                    if(url.contains("#")) url=url.substring(0,url.indexOf("#"));
                    if(url.length() > epubPrefix.length()) {
                        part=url.substring(epubPrefix.length());
                        if(part.startsWith("N=")) {
                            part=part.substring(2);
                            getNextPage = true;
                        }
                    }
                    ZipInputStream zin = null;
                    try {
                        zin = new ZipInputStream(getContentResolver().openInputStream(epubUri));
                    } catch (FileNotFoundException e) {
                        return new WebResourceResponse("text/html","utf-8",new ByteArrayInputStream(("Unable to open "+epubUrl+"<p>"+e.toString()+"<p>Could this be a permissions problem?").getBytes()));
                    } catch (SecurityException e) {
                        return new WebResourceResponse("text/html","utf-8",new ByteArrayInputStream(("Insufficient permissions to open "+epubUrl+"<p>"+e.toString()).getBytes()));
                    }
                    java.util.zip.ZipEntry ze;
                    try {
                        ByteArrayOutputStream f=null;
                        if(part==null) {
                            f=new ByteArrayOutputStream();
                            String fName=epubUrl;
                            int slash=fName.lastIndexOf("/"),slash2=fName.lastIndexOf("%2F"); if(slash2>slash) slash=slash2+2; if(slash>-1) fName=fName.substring(slash+1);
                            f.write(("<h2>"+fName+"</h2>Until I write a <em>real</em> table-of-contents handler, you have to make do with <em>this</em>:").getBytes());
                        }
                        boolean foundHTML = false; // doubles as 'foundPart' if getNextPage
                        while ((ze = zin.getNextEntry()) != null) {
                            if (part==null) {
                                if(ze.getName().contains("toc.xhtml")) return new WebResourceResponse("text/html","utf-8",new ByteArrayInputStream(("Loading... <script>window.location='"+epubPrefix+ze.getName()+"'</script>").getBytes())); // TODO: we should really be getting this via content.opf which is ref'd in META-INF/container.xml <rootfile full-path= (but most epub files call it toc.xhtml and we do have a 'list all' fallback)
                                if(ze.getName().contains("htm")) { foundHTML = true; f.write(("<p><a href=\""+epubPrefix+ze.getName()+"\">"+ze.getName()+"</a>").getBytes()); }
                            } else if (ze.getName().equalsIgnoreCase(part)) {
                                if(getNextPage) {
                                    foundHTML = true;
                                } else {
                                    int bufSize=2048;
                                    if(ze.getSize()==-1) {
                                        f=new ByteArrayOutputStream();
                                    } else {
                                        bufSize=(int)ze.getSize();
                                        f=new ByteArrayOutputStream(bufSize);
                                    }
                                    byte[] buf=new byte[bufSize];
                                    int r; while ((r=zin.read(buf))!=-1) f.write(buf,0,r);
                                    String mimeType=android.webkit.MimeTypeMap.getSingleton().getMimeTypeFromExtension(android.webkit.MimeTypeMap.getFileExtensionFromUrl(ze.getName()));
                                    if(mimeType==null || mimeType.equals("application/xhtml+xml")) mimeType="text/html"; // needed for annogen style modifications
                                    if(mimeType.equals("text/html")) {
                                        // TODO: if ((epubUrl.startsWith("file:") || epubUrl.contains("com.android.externalstorage")) && part!="toc.xhtml") then getSharedPreferences putString("eR"+epubUrl,part) ?  To avoid unbounded buildup, need to store only the most recent few (use one pref with separators?  or other mechanism e.g. 0=url 1=url ... nxtWrite=2 w. wraparound?)  Then add "jump to last seen page" link from both directory and toc.xhtml (latter will need manipulation as below)
                                        return new WebResourceResponse(mimeType,"utf-8",new ByteArrayInputStream(f.toString().replaceFirst("</[bB][oO][dD][yY]>","<p><script>document.write("""+sort20px(br"""'<a class=ssb_local_annotator_noprint style=\"border: #1010AF solid !important; background: #1010AF !important; color: white !important; display: block !important; position: fixed !important; font-size: 20px !important; right: 0px; bottom: 0px;z-index:2147483647; -moz-opacity: 0.8 !important; opacity: 0.8 !important;\" href=\""+epubPrefix+"N="+part+"\">'""")+br""")</script>Next</a></body>").getBytes())); // TODO: will f.toString() work if f is utf-16 ?
                                    } else return new WebResourceResponse(mimeType,"utf-8",new ByteArrayInputStream(f.toByteArray()));
                                }
                            } else if(foundHTML && ze.getName().contains("htm")) return new WebResourceResponse("text/html","utf-8",new ByteArrayInputStream(("Loading... <script>window.location='"+epubPrefix+ze.getName()+"'</script>").getBytes()));
                        }
                        if(part==null) { if(!foundHTML) f.write(("<p>Error: No HTML files were found in this EPUB").getBytes()); return new WebResourceResponse("text/html","utf-8",new ByteArrayInputStream(f.toByteArray())); }
                        else if(foundHTML) return new WebResourceResponse("text/html","utf-8",new ByteArrayInputStream(("No more pages").getBytes()));
                        else return new WebResourceResponse("text/html","utf-8",new ByteArrayInputStream(("No zip entry for "+part+" in "+epubUrl).getBytes()));
                    } catch (IOException e) {
                        return new WebResourceResponse("text/html","utf-8",new ByteArrayInputStream("IOException".getBytes()));
                    } finally { try { zin.close(); } catch(IOException e) {} }
                }"""
if android_print: android_print_script = br"""if(ssb_local_annotator.canPrint())document.write("""+sort20px(br"""'<a class=ssb_local_annotator_noprint style=\"border: #1010AF solid !important; background: #1010AF !important; display: block !important; position: fixed !important; font-size: 20px !important; left: 0px; bottom: 0px;z-index:2147483647; -moz-opacity: 0.8 !important; opacity: 0.8 !important;\" href=\"javascript:ssb_local_annotator.print()\">'""")+br"""+ssb_local_annotator.canPrint().replace('0.3ex','0.3ex;display:inline-block')+'</a>')"""
else: android_print_script = b""
if epub and android_print: android_src = android_src.replace(b"Next</a>",b"Next</a><script>"+android_print_script+b"</script>")
if not android_template: android_src += br"""
                float scale = 0; boolean scaling = false;
                public void onScaleChanged(final WebView view,float from,final float to) {
                    if (AndroidSDK < 19 || !view.isShown() || scaling || Math.abs(scale-to)<0.01) return;
                    scaling=view.postDelayed(new Runnable() { public void run() {
                        view.evaluateJavascript("document.body.style.width=((window.visualViewport!=undefined?window.visualViewport.width:window.innerWidth)-getComputedStyle(document.body).marginLeft.replace(/px/,'')*1-getComputedStyle(document.body).marginRight.replace(/px/,'')*1)+'px';window.setTimeout(function(){document.body.scrollLeft=0},400)",null); // window.outerWidth will still be excessive on 4.4; not sure there's much we can do about that
                        scale=to; scaling=false;
                    } }, 100);
                }"""
android_src += br"""
                public void onPageFinished(WebView view,String url) {
                    if(AndroidSDK < 19) // Pre-Android 4.4, so below runTimer() alternative won't work.  This version has to wait for the page to load entirely (including all images) before annotating.  Also handles displaying the forward button when needed (4.4+ uses different logic for this in onKeyDown, because API19+ reduces frequency of scans when same length, due to it being only a backup to MutationObserver)
                    browser.loadUrl("javascript:"+js_common+"function AnnotMonitor() { AnnotIfLenChanged();if(!document.doneFwd && ssb_local_annotator.canGoForward()){var e=document.getElementById('annogenFwdBtn');if(e){e.style.display='inline';document.doneFwd=1}}window.setTimeout(AnnotMonitor,1000)} AnnotMonitor()");
                    else browser.evaluateJavascript(js_common+"AnnotIfLenChanged(); var m=window.MutationObserver;if(m)new m(function(mut){var j;if(mut.length==1)for(j=0;j<mut[i].addedNodes.length;j++){var n=mut[0].addedNodes[j],inLink=0,m=n,ok=1;while(ok&&m&&m!=document.body){inLink=inLink||(m.nodeName=='A'&&!!m.href)||m.nodeName=='BUTTON';ok=m.className!='_adjust0';m=m.parentNode}if(ok)annotWalk(n,document,inLink,false)}else window.setTimeout(AnnotIfLenChanged,500)}).observe(document.body,{childList:true,subtree:true})",null); // run only if 1 set of changed nodes, otherwise can run too long (especially if iterating on own changes) so use a setTimeout (or wait for runTimerLoop fallback, but that might be on a 5sec wait).  The setTimeout needs to be AnnotIfLenChanged not just annotScan, because multiple ones might get batched up and tie up the browser, especially on Android 10 (not so bad on Android 13).
                } });"""
if android_template: android_src += br"""
        if(AndroidSDK >= 3 && AndroidSDK < 14) { /* (we have our own zoom functionality on API 14+ which works better on 19+) */
            browser.getSettings().setBuiltInZoomControls(true);
        } if (AndroidSDK < 14) {
            final int size=Math.round(16*fs);
            browser.getSettings().setDefaultFontSize(size);
            browser.getSettings().setDefaultFixedFontSize(size);
        }"""
else: android_src += br"""
        if(AndroidSDK >= 3) browser.getSettings().setBuiltInZoomControls(true);
        float fs = getResources().getConfiguration().fontScale; // from device accessibility settings
        if (fs < 1.0f) fs = 1.0f; // bug in at least some versions of Android 8 returns 0 for fontScale
        final int size=Math.round(16*fs); // from device accessibility settings (might be squared if OS does it too, but that's OK because the settings don't give enough of a range)
        browser.getSettings().setDefaultFontSize(size);
        browser.getSettings().setDefaultFixedFontSize(size);"""
android_src += br"""
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
        if(browser==null) return false;
        if (Intent.ACTION_SEND.equals(intent.getAction()) && "text/plain".equals(intent.getType())) {
            sentText = intent.getStringExtra(Intent.EXTRA_TEXT);
            if (sentText == null) return false;
            browser.loadUrl("javascript:document.close();document.noBookmarks=1;document.rubyScriptAdded=0;document.write('<html><head><meta name=\"mobileoptimized\" content=\"0\"><meta name=\"viewport\" content=\"width=device-width\"></head><body>'+ssb_local_annotator.getSentText().replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/(https?:\\/\\/[-!#%&+,.0-9:;=?@A-Z\\/_|~]+)/gi,function r(m,p1) { return '<a href=\"'+p1.replace('&amp;','&')+'\">'+p1+'</a>'}).replace('\\n','<br>'));"""+android_print_script+br"""");
        }
        else if (Intent.ACTION_VIEW.equals(intent.getAction())) {
            String url=intent.getData().toString();"""
if epub: android_src += br"""
            if (((url.startsWith("file:") || url.startsWith("content:")) && url.endsWith(".epub")) || "application/epub+zip".equals(intent.getType())) openEpub(url); else"""
android_src += br""" loadingWait(url);
        }
        else return false; return true;
    }
    void loadingWait(String url) {
        browser.loadUrl("javascript:document.close();document.noBookmarks=1;document.write('<html><head><meta name=\"mobileoptimized\" content=\"0\"><meta name=\"viewport\" content=\"width=device-width\"></head><body>Loading, please wait...</body>')");
        browser.loadUrl(url);
    }
    String sentText = null;"""
if epub: android_src += br"""
    void openEpub(String url) {
        if(AndroidSDK<11 && url.endsWith(".epub")) { browser.loadUrl("javascript:document.close();document.noBookmarks=1;document.rubyScriptAdded=0;document.write('<html><head><meta name=\"mobileoptimized\" content=\"0\"><meta name=\"viewport\" content=\"width=device-width\"></head><body>This app'+\"'s EPUB handling requires Android 3 or above :-(</body>\")"); return; } // (Support for Android 2 would require using data URIs for images etc, and using shouldOverrideUrlLoading on all links)
        // Android 5+ content:// URIs expire when the receiving Activity finishes, so we won't be able to add them to bookmarks (unless copy the entire epub, which is not good on a space-limited device)
        SharedPreferences sp=getPreferences(0);
        android.content.SharedPreferences.Editor e; do { e=sp.edit(); e.putString("epub",url); } while(!e.commit());
        loadingWait("http://epub/"); // links will be absolute; browser doesn't have to change
    }
    @Override protected void onActivityResult(int request, int result, Intent intent) { if(request!=8778 || intent==null || result!=-1) return; boolean isEpub=false; try{byte[] buf=new byte[58]; getContentResolver().openInputStream(Uri.parse(intent.getData().toString())).read(buf,0,58); isEpub=buf[0]=='P' && buf[1]=='K' && buf[2]==3 && buf[3]==4 && new String(buf,30,28).equals("mimetypeapplication/epub+zip"); }catch(Exception e){} if(isEpub) openEpub(intent.getData().toString()); else {Toast.makeText(this, "That wasn't an EPUB file :-(",Toast.LENGTH_LONG).show();} }"""
if pleco_hanping: android_src += br"""
    int dictionaries = 0;
    boolean gotPleco = false;
    String[] hanpingPackage = new String[]{"com.embermitre.hanping.cantodict.app.pro","com.embermitre.hanping.app.pro","com.embermitre.hanping.app.lite"};
    int[] hanpingVersion = new int[]{0,0,0};"""
if tts_js: android_src += br"""
    String ttsList = "";
    TextToSpeech tts=null,tts2=null,
        tts_keep=null; int found_dx=-1;
    int nextID=0; @TargetApi(21)
    boolean doTTS(String text) {
        if(tts_keep==null) return false;
        int maxLen=TextToSpeech.getMaxSpeechInputLength();
        int queueMode = TextToSpeech.QUEUE_FLUSH;
        while(text.length() > 0) {
            String t2;
            if (text.length() > maxLen) {
                t2=text.substring(0,maxLen);
                if(t2.indexOf("\u3002")>0) t2=t2.substring(0,t2.lastIndexOf("\u3002")+1);
                else if(t2.indexOf(". ")>0) t2=t2.substring(0,t2.lastIndexOf(". ")+2);
            } else t2 = text;
            if(tts_keep.speak(t2,queueMode,null,String.valueOf(nextID++))!=TextToSpeech.SUCCESS) return false;
            text = text.substring(t2.length());
            queueMode = TextToSpeech.QUEUE_ADD;
        } return true;
    }
    java.util.List<TextToSpeech.EngineInfo> eiList = null;
    @TargetApi(21)
    String TTSTest(int batchNo,String voices_to_set) {
        final android.content.Context context = this;
        if (batchNo==1) {
            if (ttsList != "") return ttsList;
            if(AndroidSDK < 21) return "Android 5+ required for multilingual TTS";
            if(eiList==null) {
                tts = new TextToSpeech(context,new TextToSpeech.OnInitListener(){
                        public void onInit(int status) {
                            if(tts == null) {
                                ttsList += "race-condition fail";
                                return;
                            }
                            if (status != 0) {
                                ttsList += "init fail";
                                return;
                            }
                            eiList = tts.getEngines();
                            try { tts.shutdown(); } catch(Exception e) {} tts = null;
                            TTSTest(1,voices_to_set);
                        }
                    });
                return "Fetching engine list";
            }
            ttsList="TTS voice list:\n";
        }
        int i=0; boolean found=false;
        for(TextToSpeech.EngineInfo ei : eiList) {
            if (++i < batchNo) continue;
            found = true;
            tts2 = new TextToSpeech(context,new TextToSpeech.OnInitListener(){
                    public void onInit(int status) {
                        if (tts2 == null) {
                            ttsList += "(engine race-condition fail)";
                            return;
                        }
                        if (status != 0) {
                            ttsList += "(engine init fail)";
                            return;
                        }
                        boolean do_shutdown = true;
                        java.util.Set<Voice> voices; try { voices=tts2.getVoices(); } catch(Exception e) { voices=null; } if(voices==null /* (either by exception or otherwise, e.g. on somebody's Android 11 getVoices() simply returned null) */) { ttsList += "(getVoices fail)"; return; }
                        for(Voice v: voices) {
                            ttsList += v.getName()+"(lang="+v.getLocale().getLanguage()+" variant="+v.getLocale().getVariant()+" quality="+String.valueOf(v.getQuality())+" connection="+(v.isNetworkConnectionRequired()?"t":"f")+" latency="+String.valueOf(v.getLatency())+")\n";
                            int dx=voices_to_set.indexOf(","+v.getName()+",");
                            if (dx>-1 && (found_dx==-1 || dx < found_dx) && tts2.setVoice(v)==TextToSpeech.SUCCESS) {
                                if(tts_keep!=null && do_shutdown) try { tts_keep.shutdown(); } catch(Exception e) {} // != tts2
                                tts_keep = tts2; do_shutdown=false;
                                found_dx = dx;
                            }
                        }
                        if (do_shutdown) try { tts2.shutdown(); } catch(Exception e) {}
                        TTSTest(batchNo+1,voices_to_set);
                    }
                },ei.name);
            break; // we have to wait for 1st tts2 to be processed before starting next, hence batchNo
        }
        if(!found) {
            ttsList += "scan complete";
            return ttsList;
        } else return "Scanning engines";
    }"""
android_src += br"""
    static final String js_common="""+b'"'+jsAnnot()+br"""";
    @SuppressWarnings("deprecation")
    @TargetApi(19)
    void runTimerLoop() {
        if(AndroidSDK >= 19) { // on Android 4.4+ we can do evaluateJavascript while page is still loading (useful for slow-network days) - but setTimeout won't usually work so we need an Android OS timer
            final Handler theTimer = new Handler(Looper.getMainLooper());
            theTimer.postDelayed(new Runnable() {
                @Override public void run() {
                    final Runnable r = this;
                    runOnUiThread(new Runnable() { @Override public void run() {
                      browser.evaluateJavascript(((needJsCommon>0)?js_common:"")+"AnnotIfLenChanged()",new android.webkit.ValueCallback<String>() {
                        @Override
                        public void onReceiveValue(String s) {
                            theTimer.postDelayed(r,(s!=null && s.contains("sameLen"))?5000:1000); // s.equals("\"sameLen\"", is this true in all versions of the API?)
                        }
                      });
                      if(needJsCommon>0) --needJsCommon;
                    } });
                }
            },0);
        }
    }
    boolean nextBackHides = false, _isFocused = true;
    int needJsCommon=3;
    @Override public void onPause() { super.onPause(); nextBackHides = _isFocused = false; } // but may still be visible on Android 7+, so don't pause the browser yet
    @Override public void onResume() { _isFocused = true; super.onResume(); }
    @TargetApi(11) @Override public void onStop() { super.onStop(); if(browser!=null && AndroidSDK >= 11) browser.onPause(); } // NOW pause the browser (screen off or app not visible)
    @TargetApi(11) @Override public void onStart() { super.onStart(); if(browser!=null && AndroidSDK >= 11) browser.onResume(); }
    @Override public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            if (nextBackHides) {
                nextBackHides = false;
                if(moveTaskToBack(true)) return true;
            }
            if (browser!=null && browser.canGoBack()) {
                final String fwdUrl=browser.getUrl();
                browser.goBack();
                if(AndroidSDK<19) return true; // before Android 4.4 we can't evaluateJavascript, and unclear if we can loadUrl javascript: when we don't have onPageFinished on back, but AnnotMonitor runs at a higher frequency so we let that do it instead of this
                needJsCommon=3;
                final Handler theTimer=new Handler(Looper.getMainLooper());
                theTimer.postDelayed(new Runnable() {
                  int tried=0;
                  @Override public void run() {
                    if(++tried==9) return;
                    runOnUiThread(new Runnable() {
                    @Override public void run() {
                        if(browser.getUrl().equals(fwdUrl)) {
                            // not yet finished going back
                            theTimer.postDelayed(this,500);
                        } else browser.evaluateJavascript("function annogenMakeFwd(){var e=document.getElementById('annogenFwdBtn'); if(e) e.style.display='inline'; else window.setTimeout(annogenMakeFwd,1000)}annogenMakeFwd()",null);
                    }});
                  }
                },500);
                return true;
            }
        } return super.onKeyDown(keyCode, event);
    }
    @SuppressWarnings("deprecation") // using getText so works on API 1 (TODO consider adding a version check and the more-modern alternative android.content.ClipData c=((android.content.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).getPrimaryClip(); if (c != null && c.getItemCount()>0) return c.getItemAt(0).coerceToText(this).toString(); return ""; )
    @TargetApi(11)
    public String readClipboard() {
        if(AndroidSDK < Build.VERSION_CODES.HONEYCOMB) // SDK_INT requires API 4 but this works on API 1
            return ((android.text.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).getText().toString();
        android.content.ClipData c=((android.content.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).getPrimaryClip();
        if (c != null && c.getItemCount()>0) {
            return c.getItemAt(0).coerceToText(this).toString();
        }
        return "";
    }
    @Override protected void onSaveInstanceState(Bundle outState) { if(browser!=null) browser.saveState(outState); }
    @Override protected void onDestroy() {"""
if tts_js: android_src += br"if(tts_keep!=null) try { tts_keep.shutdown(); } catch(Exception e) {}"
android_src += br"""
if(isFinishing() && AndroidSDK<23 && browser!=null) browser.clearCache(true); super.onDestroy(); } // (Chromium bug 245549 needed this workaround to stop taking up too much 'data' (not counted as cache) on old phones; it MIGHT be OK in API 22, or even API 20 with updates, but let's set the threshold at 23 just to be sure.  This works only if the user exits via Back button, not via swipe in Activity Manager: no way to catch that.)
    @SuppressWarnings("deprecation") // we use Build.VERSION.SDK only if we're on an Android so old that SDK_INT is not available:
    int AndroidSDK = (android.os.Build.VERSION.RELEASE.startsWith("1.") ? Integer.valueOf(Build.VERSION.SDK) : Build.VERSION.SDK_INT);
    WebView browser;"""
if epub: android_src += b" boolean loadingEpub = false;"
android_src += b"}\n"
android_bringToFront=br"""package %%JPACKAGE%%;
import android.annotation.TargetApi;
import android.content.Intent;
import android.os.Build;
@TargetApi(3)
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
android_clipboard = br"""<html><head><meta name="mobileoptimized" content="0"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head><body>
    <h3 class="ssb_local_annotator_noprint">Clipboard</h3>
    <div id="clip">waiting for clipboard contents</div>
    <script>
var curClip="",isFocused=true,lastTime=new Date();
function update() {
var newClip = ssb_local_annotator.getClip();
var isF2 = ssb_local_annotator.isFocused();
var thisTime = new Date();
if (newClip && newClip != curClip) {
  if(curClip && isFocused && isF2 && thisTime-lastTime < 2000) {
    // looks like they copied from clipboard view itself
    // - no need to replace the whole thing with this part
    curClip=newClip;
  } else {
  document.getElementById('clip').innerHTML = """
if tts_js: android_clipboard += br"""'<span class="ssb_local_annotator_noprint" id="read" onclick="ssb_local_annotator.TTS(curClip.replace(/:/g,\'; \'))"'+(ssb_local_annotator.TTSIsSet()?'':' style="visibility:hidden"')+'>\ud83d\udd0a</span>'+""" # (digit:digit read as hours:minutes by some voices, but shouldn't always be; TTSIsSet might be false if clipboard view selected before TTS has finished starting on application launch, in which case we want the control to appear later)
android_clipboard += br"""newClip.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/(https?:\/\/[-!#%&+,.0-9:;=?@A-Z\/_|~]+)/gi,function r(m,p1) { return '<a href="'+p1.replace('&amp;','&')+'">'+p1+'</a>' });
  if(typeof annotScan!='undefined') annotScan();
  curClip = newClip; if(ssb_local_annotator.annotate(newClip)!=newClip) ssb_local_annotator.bringToFront(); // should work on Android 9 or below; Android Q (API 29) takes away background clipboard access and we'll just get newClip="" until we're brought to foreground manually
  }
}"""
if tts_js: android_clipboard += br"""if(ssb_local_annotator.TTSIsSet()){var e=document.getElementById('read');if(e)e.style.visibility='visible'}"""
android_clipboard += br"""isFocused = isF2; lastTime = thisTime;
window.setTimeout(update,1000) } update()"""
if android_print: android_clipboard += b';'+android_print_script.replace(br'\"',b'"')
android_clipboard += br"""</script>
</body></html>"""
java_src = br"""package %%JPACKAGE%%;
import java.io.*;
public class Annotator {
public Annotator("""
if android:
  # will need a context param to read from assets
  java_src += b"android.content.Context context"
java_src += b") throws IOException"
if zlib: java_src += b",java.util.zip.DataFormatException"
java_src += b""" { try { data=new byte[%%DLEN%%]; } catch (OutOfMemoryError e) { throw new IOException("Out of memory! Can't load annotator!"); }"""
if android: java_src += b'context.getAssets().open("annotate.dat").read(data);'
else: java_src += b'this.getClass().getResourceAsStream("/annotate.dat").read(data);'
if zlib: java_src += br"""
java.util.zip.Inflater i=new java.util.zip.Inflater();
i.setInput(data);
byte[] decompressed; try { decompressed=new byte[%%ULEN%%]; } catch (OutOfMemoryError e) { throw new IOException("Out of memory! Can't unpack annotator!"); }
i.inflate(decompressed); i.end(); data = decompressed;"""
java_src += br"addrLen = data[0] & 0xFF;"
if post_normalise: java_src += b"""
    dPtr = 1; char[] rleDat;
    try {
        rleDat = new String(java.util.Arrays.copyOfRange(data,readAddr(),data.length), "UTF-16LE").toCharArray();
    } catch (UnsupportedEncodingException e) {
        // should never happen with UTF-16LE
        return;
    }
    normalisationTable = new char[65536];
    int maxRLE = rleDat[0]; char w=0; // Java char is unsigned short
    for(int cF=0; cF < rleDat.length; cF++) {
        if(rleDat[cF] <= maxRLE) for(int j=0; j<rleDat[cF]; j++) { normalisationTable[w]=w; w++; }
        else normalisationTable[w++] = rleDat[cF];
    } while(w!=0) { normalisationTable[w]=w; w++; /* overflows to 0 */ }
}
char[] normalisationTable; byte[] origInBytes;"""
else: java_src += b"}" # end c'tor w/out adding extra private data
java_src += br"""
int nearbytes;
byte[] inBytes;
public int inPtr,writePtr; boolean needSpace;
ByteArrayOutputStream outBuf;
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
public void s0() {
  if (needSpace) { o((byte)' '); needSpace=false; }
}
byte[] s2b(String s) {
  // Convert string to bytes - version that works before Android API level 9 i.e. in Java 5 not 6.  (Some versions of Android Lint sometimes miss the fact that s.getBytes(UTF8) where UTF8==java.nio.charset.Charset.forName("UTF-8") won't always work.)  We could do an API9+ version and use @android.annotation.TargetApi(9) around the class, but anyway we'd rather not have to generate a special Android-specific version of Annotator as well as putting Android stuff in a separate class.)
  try { return s.getBytes("UTF-8"); }
  catch(UnsupportedEncodingException e) {
    // should never happen for UTF-8
    return null;
  }
}"""
if existing_ruby_shortcut_yarowsky: java_src += b"\npublic boolean shortcut_nearTest=false;"
java_src += br"""
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
                case 70: s0(); break;
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
                    int fPtr = readAddr();"""
if existing_ruby_shortcut_yarowsky: java_src += br"""
                    if (shortcut_nearTest) {
                        dPtr = (tPtr<fPtr) ? tPtr : fPtr; // relying on BytecodeAssembler addActionDictSwitch behaviour: the higher pointer will be the one that skips past the 'if', so we want the lower one if we want to always take it
                        break;
                    }"""
java_src += br"""
                    sn(data[dPtr++] & 0xFF);
                    boolean found = false;
                    while (dPtr < tPtr && dPtr < fPtr) if (n(readRefStr())) { found = true; break; }
                    dPtr = found ? tPtr : fPtr; break; }
                default: throw new java.util.zip.DataFormatException("corrupt data table");
                }
        }
    }
public String annotate(String txt) throws java.util.zip.DataFormatException {"""
if existing_ruby_shortcut_yarowsky: java_src += br"""
  boolean old_snt = shortcut_nearTest;
  if(txt.length() < 2) shortcut_nearTest=false;
"""
if post_normalise: java_src += br"""
  origInBytes=s2b(txt); char[] tmp=txt.toCharArray(); for(int i=0; i<tmp.length; i++) tmp[i]=normalisationTable[tmp[i]]; txt=new String(tmp);
"""
java_src += br"""
  nearbytes=%%YBYTES%%;inBytes=s2b(txt);writePtr=0;needSpace=false;outBuf=new ByteArrayOutputStream();inPtr=0;
  while(inPtr < inBytes.length) {
    int oldPos=inPtr; """
if post_normalise: java_src += b"dPtr=1+addrLen;" # after byte nBytes, we'll have address of normalisation table, and then the bytecode itself
else: java_src += b"dPtr=1;" # just byte nBytes needs to be skipped
java_src += br"""readData();
    if (oldPos==inPtr) { needSpace=false; o(nB()); writePtr++; }
  }
  String ret=null; try { ret=new String(outBuf.toByteArray(), "UTF-8"); } catch(UnsupportedEncodingException e) {}"""
if post_normalise: java_src = java_src.replace(b"inBytes[writePtr",b"origInBytes[writePtr").replace(b"o(nB()); writePtr++;",b"inPtr++; o(origInBytes[writePtr++]);")
if existing_ruby_shortcut_yarowsky: java_src += b"shortcut_nearTest=old_snt;"
java_src += br"""
  inBytes=null; outBuf=null; return ret;
}"""
if not android: java_src += b"""
public static void main(String[] args) {
  try {
    BufferedReader r=new BufferedReader(new InputStreamReader(System.in)); String s; Annotator a=new Annotator();
    while((s=r.readLine()) != null) System.out.println(a.annotate(s));
  } catch(Exception e) { e.printStackTrace(); System.exit(1); }
}
"""
java_src += b"}"

if js_6bit: js_6bit_offset = 35 # any offset between 32 and 63 makes all printable, but 35+ avoids escaping of " at 34 (can't avoid escaping of \ though, unless have a more complex decoder), and low offsets increase the range of compact-switchbyte addressing also.
else: js_6bit_offset = 0

class BytecodeAssembler:
  # Bytecode for a virtual machine run by the Javascript version etc
  opcodes = {
    # 0-19    RESERVED for short switchbyte (C,Java,Py)
    'jump': 50, # '2' params: address
    'call': 51, # '3' params: function address
    'return': 52, # '4' (or 'end program' if top level)
    'switchbyte': 60, # '<' switch(NEXTBYTE) (params: numBytes-1, bytes (sorted, TODO take advantage of this), addresses, default address)
    's0':70, # 'F'
    'copyBytes':71,'o':72,'o2':73, # 'G','H','I' (don't change these numbers, they're hard-coded below)
    # 74-76 ('J','K','L') reserved for 'above + return'
    'savepos':80, # 'P', local to the function
    'restorepos':81, # 'Q'
    'neartest':90, # 'Z' params: true-label, false-label, byte nbytes, addresses of conds strings until first of the 2 labels is reached (normally true-label, unless the whole neartest is negated)
    # 91-107 RESERVED for short switchbyte (JS, UTF-8 printability optimisation for 6bit)
    # 108-127 RESERVED for short switchbyte (JS,Dart, more in the printable range to reduce escaping a bit)
    # 128-255 RESERVED for short jumps
  }
  def __init__(self):
    self.l = [] # code list
    self.d2l = {} # definition to label
    self.lastLabelNo = 0
    self.addingPosStack = []
  def addOpcode(self,opcode): self.l.append((opcode,))
  def addBytes(self,bStr):
      if type(bStr)==int: self.l.append(B(chr(bStr)))
      elif type(bStr)==bytes: self.l.append(bStr)
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
      self.addBytes(b"".join(byteArray))
      for i in labelArray: self.addRef(i)
  def addActions(self,actionList):
    # assert type(actionList) in [list,tuple], repr(actionList)
    for a in actionList:
      if a==b's0':
        self.addOpcode('s0') ; continue
      assert 1 <= len(a) <= 3 and type(a[0])==int and all(type(b)==bytes for b in a[1:]), repr(a)
      assert 1 <= a[0] <= 255, "bytecode currently supports markup or copy between 1 and 255 bytes only, not %d (but 0 is reserved for expansion)" % a[0]
      self.addOpcode(['copyBytes','o','o2'][len(a)-1])
      if js_6bit:
        self.addBytes((a[0]+(js_6bit_offset-1))&0xFF)
      else: self.addBytes(a[0]) # num i/p bytes to copy
      for i in a[1:]: self.addRefToString(i)
  def addActionDictSwitch(self,byteSeq_to_action_dict,isFunc=True,labelToJump=None):
    # Actions aren't strings: they list tuples of either
    # 1, 2 or 3 items for copyBytes, o(), o2()
    # labelToJump is a jump to insert afterwards if not isFunc and if we don't emit an unconditional 'return'.  Otherwise, will ALWAYS end up with a 'return' (even if not isFunc i.e. the main program)
    allBytes = set(b[:1] for b in iterkeys(byteSeq_to_action_dict) if b)
    if isFunc:
        self.startAddingFunction()
        savePos = len(self.l)
        self.addOpcode('savepos')
    elif (b"" in byteSeq_to_action_dict and len(byteSeq_to_action_dict) > 1) or not labelToJump: # ('not labelToJump' and 'not isFunc' == main program)
        savePos = len(self.l)
        self.addOpcode('savepos')
    else: savePos = None
    if b"" in byteSeq_to_action_dict and len(byteSeq_to_action_dict) > 1 and len(byteSeq_to_action_dict[b""])==1 and not byteSeq_to_action_dict[b""][0][1] and all((len(a)==1 and a[0][0][:len(byteSeq_to_action_dict[b""][0][0])]==byteSeq_to_action_dict[b""][0][0] and not a[0][1]) for a in itervalues(byteSeq_to_action_dict)):
        self.addActions(byteSeq_to_action_dict[b""][0][0])
        l = len(byteSeq_to_action_dict[b""][0][0])
        byteSeq_to_action_dict = dict((x,[(y[l:],z)]) for x,[(y,z)] in iteritems(byteSeq_to_action_dict))
        del self.l[savePos] ; savePos = None
        del byteSeq_to_action_dict[b""]
        self.addActionDictSwitch(byteSeq_to_action_dict) # as a subfunction (ends up adding the call to it, which should be replaced by a jump during compaction; TODO: auto-inline if it turns out there's only this one call to it?  other calls might happen if it's merged with an identical one)
        byteSeq_to_action_dict[b""] = [(b"",[])] # for the end of this func
        self.addOpcode('return')
    elif allBytes:
      allBytes = sorted(list(allBytes))
      labels = [self.makeLabel() for b in allBytes+[0]]
      self.addByteswitch(allBytes,labels)
      for case in allBytes:
        self.addLabelHere(labels[0]) ; del labels[0]
        self.addActionDictSwitch(dict([(k[1:],v) for k,v in iteritems(byteSeq_to_action_dict) if k[:1]==case]),False,labels[-1])
      self.addLabelHere(labels[0])
    if not savePos==None: self.addOpcode('restorepos')
    if isFunc:
        self.addOpcode('return')
        if self.l[-1]==self.l[-2]: del self.l[-1] # double return
        return self.finishFunctionAndAddCall()
    elif b"" in byteSeq_to_action_dict:
        default_action = b""
        for action,conds in byteSeq_to_action_dict[b""]:
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
        if default_action or not byteSeq_to_action_dict[b""]:
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
    assert type(string)==bytes, repr(string)
    l = len(string)
    if python or java or javascript or dart:
      # prepends with a length hint if possible (or if not
      # prepends with 0 and null-terminates it)
      if js_utf8:
        string = unicodedata.normalize("NFC",string.decode('utf-8')) # NFC very important for browser_extension: some browsers seem to do it anyway, throwing off data addresses if we haven't accounted for that
        l = len(string) # we count in UCS-2 characters
        assert all((ord(c) < 0xD800 or 0xE000 < ord(c) <= 0xFFFF) for c in string), "js_utf8 addressing will be confused by non UCS-2: "+repr(string) # Surrogate pairs would cause invalid UTF-8, don't know which if any Javascript or Dart implementations would take them
        # Have checked browsers + Node count combining characters separately, so len(string) should be correct (e.g. u'Moc\u0306nik')
        if 1 <= l < 0x02B0: # can use length-first unichr (avoid combining and modifier marks just in case; also avoid 0xD800+ surrogates)
          string = unichr(l) + string
        else: string = unichr(0)+string+unichr(0)
      elif js_6bit:
        string = re.sub(b"%(?=[0-9A-Fa-f])|[\x7f-\xff]",lambda m:urllib.quote(m.group()),string) # for JS 'unescape' in readRefStr, which is applied (without encodeURIComponent) if js_6bit and not js_utf8 so we can use %-encoding
        l = len(string) # length is needed BEFORE %-decode
        if 1 <= l <= 91: # use 32-122 inclusive
          string = B(chr(l+31))+string
        else: # try to avoid using \x00 for termination
          for termChar in '{|}~\x00': # 123-126 + nul
            termChar=B(termChar)
            if not termChar in string:
              string = termChar + string + termChar
              break
      elif 1 <= l < 256: # length byte + string
        string = B(chr(l))+string
      else: string = B(chr(0))+string+B(chr(0))
    else: string += b'\x00' # just null-termination for C
    if not string in self.d2l:
      self.d2l[string] = (-len(self.d2l)-1,)
    self.l.append(self.d2l[string])
  def link(self): # returns resulting bytes
    # (add an 'end program' instruction before calling)
    def f(*args): raise Exception("Must call link() only once")
    self.link = f
    sys.stderr.write("Linking... ") ; sys.stderr.flush()
    def dl(t):
      r = [(x,y) for x,y in iteritems(self.d2l) if type(x)==t]
      if not t==tuple: r.sort() # so we can optimise for overlaps (but don't let Python 3 try to compare across types, it's more fussy than Python 2)
      return r
    d2l = dl(bytes)+dl(unicode)+dl(tuple) # the functions and data to add to the end of self.l
    assert len(d2l)==len(self.d2l), "missed out a key type"
    for dat,ref in d2l:
        assert type(ref)==tuple and type(ref[0])==int
        self.l.append((-ref[0],)) # the label
        if type(dat) in [bytes,unicode]:
            if type(self.l[-2])==type(dat) and self.l[-2][-1]==dat[0]: # overlap of termination-byte indicators (TODO: look for longer overlaps? unlikely to occur)
              self.l[-2] = self.l[-2][:-1]
            self.l.append(dat) ; continue
        # otherwise it's a function, and non-reserved labels are local, so we need to rename them
        l2l = {} # local label to renamed label
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
    if post_normalise and not javascript: # must be AFTER d2l, as EOF is used to end it
      normLabel = self.makeLabel()
      self.l.insert(0,-normLabel)
      self.l.append(normLabel)
      bmp = [(k,v) for k,v in sorted(post_normalise.items())]
      maxRLE = min(bmp[0][0],min(v for k,v in bmp))-1
      assert maxRLE >= 0, "can't have a mapping to 0"
      curPtr = 0
      def lsbmsb(i):
        assert type(i)==int and 0<=i<=0xFFFF
        return B(chr(i&0xFF)+chr(i>>8))
      for i in xrange(len(bmp)):
        delta = bmp[i][0]-curPtr
        while delta:
          skip = min(delta,maxRLE)
          self.l.append(lsbmsb(skip))
          delta -= skip ; curPtr += skip
        self.l.append(lsbmsb(bmp[i][1]))
        curPtr += 1
    # elements of self.l are now:
    # - (byte) strings (just copied in)
    # - positive integers (labels for code)
    # - negative integers (references to labels)
    # - +ve or -ve integers in tuples (labels for functions and text strings: different 'namespace')
    # strings in tuples: opcodes
    # 1st byte of o/p is num bytes needed per address
    class TooNarrow(Exception): pass
    if js_6bit: aBits,aMask = 6,0x3F
    else: aBits,aMask = 8,0xFF
    for addrSize in xrange(1,256):
        sys.stderr.write("(%d-bit) " % (aBits*addrSize))
        sys.stderr.flush()
        src = self.l[:] # must start with fresh copy, because compaction modifies src and we don't want a false start with wrong addrSize to affect us
        try:
          compacted = 0 ; compaction_types = set()
          # The compact opcodes all rely on relative addressing (relative to AFTER the compact instruction) that goes only forward.  Easiest way to deal with that is to work backwards from the end, inlining the compactions, before running a conventional 2-pass assembly.
          # TODO: Could move the below loop into this one in its entirety, and just assemble backwards.  Most within-function label references point forwards anyway.  (Would still need some backward refs for functions though)
          bytesFromEnd = 0
          lDic = {} # labelNo -> bytesFromEnd
          def LGet(lRef,origOperandsLen):
            # Return the number of bytes between the end of the proposed compact instruction and the label, to see if it's small enough to fit inside the compact instruction.  Since bytesFromEnd includes origOperandsLen, we need to subtract that out, which would then leave bytes from end of code to end of proposed new instruction (whatever its length will be), and then subtracting the bytesFromEnd of the label will give the number of forward bytes we want.
            if not -lRef in lDic: return -1
            return bytesFromEnd-origOperandsLen-lDic[-lRef]
          counts_to_del = set()
          for count in xrange(len(src)-1,-1,-1):
              i = src[count]
              if type(i)==tuple and type(i[0])==str:
                  opcode = i[0]
                  i = "-" # for len() at end of block
                  if opcode in ['copyBytes','o','o2'] and src[count+['copyBytes','o','o2'].index(opcode)+2]==('return',):
                    # 74 to 76 = 71 to 73 + return
                    src[count] = B(chr(['copyBytes','o','o2'].index(opcode)+74))
                    counts_to_del.add(count+['copyBytes','o','o2'].index(opcode)+2)
                    compacted += 1 ; bytesFromEnd -= 1
                    compaction_types.add('return')
                  elif opcode=='call' and src[count+2]==('return',):
                    src[count] = ('jump',)
                    counts_to_del.add(count+2)
                    compacted += 1 ; bytesFromEnd -= 1
                    compaction_types.add(opcode)
                    # can't fall through by setting opcode='jump', as the address will be in the function namespace (integer in tuple, LGet would need adjusting) and is highly unlikely to be within range (TODO: unless we try to arrange the functions to make it so for some cross-calls)
                  elif opcode=='jump' and 0 <= LGet(src[count+1],addrSize) < 0x80: # we can use a 1-byte relative forward jump (up to 128 bytes), useful for 'break;' in a small switch
                    offset = LGet(src[count+1],addrSize)
                    if offset == 0:
                      # can remove this jump completely
                      i = "" # for len() at end of block
                      compacted += 1
                      counts_to_del.add(count) # zap jmp
                    else: src[count] = i = B(chr(0x80 | offset)) # new instr: 0x80|offset
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
                      if javascript or dart: # use printable range
                        if js_6bit and numItems<=17 and all(0x80<=ord(x)<=0xBF or 0xD4<=ord(x)<=0xEF for x in S(src[count+2])): # if bytes being switched on are all from UTF-8 representations of U+0500 through U+FFFF, move to printable range (in one test this saved 780k for the continuation bytes and another 200k for the rest)
                          def mv(x):
                            if x>=0xD4: x -= 20 # or, equivalently, if (x-93)>118, which is done to the input byte in JS before searching on these
                            return B(chr(x-93))
                          src[count+2]=b''.join(mv(ord(x)) for x in S(src[count+2]))
                          i = B(chr(ord(src[count+1])+91)) # and a printable opcode
                        else: i = B(chr(ord(src[count+1])+108)) # can't make the match bytes printable, but at least we can have a printable opcode 108-127 for short switchbyte in Javascript or Dart
                      else: i = B(src[count+1]) # 0-19 for short switchbyte in C,Java,Python
                      src[count] = i = i+src[count+2]+b''.join(B(chr(LGet(src[count+N],origOperandsLen)+js_6bit_offset)) for N in xrange(4,3+numLabels)) # opcode_including_nItems, string of bytes, offsets (assume 1st offset at count+3 is 0 so not listed)
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
          # End of opcode compaction
          lDic = {} # label dictionary: labelNo -> address
          for P in [1,2]:
            r = [B(chr(addrSize))] # List to hold the output bytecode, initialised with a byte indicating how long our addresses will be.
            ll = 1 # cumulative length of output list, normally in bytes, but if js_utf8 then we count in Javascript (UCS-2) characters
            count = 0 # reading through src opcodes etc
            while count < len(src):
                i = src[count] ; count += 1
                if type(i)==tuple and type(i[0])==str: i = B(chr(BytecodeAssembler.opcodes[i[0]]))
                elif type(i) in [int,tuple]: # labels
                    if type(i)==int: i2,iKey = i,-i # +ve integers are labels, -ve integers are references to them
                    else: i2,iKey = i[0],(-i[0],) # reserved labels (a different counter, handled here by putting the key in a tuple)
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
                            j.append(B(chr(((i>>shift)&aMask)+js_6bit_offset)))
                        i = b"".join(j)
                        assert len(i)==addrSize
                    else: # ref to as-yet unknown label
                        assert P==1, "undefined label %d" % -i
                        i = B("-"*addrSize) # placeholder (well we could just advance ll, but setting this makes things easier if you ever want to inspect partial results)
                if len(i): # bytes or Unicode
                  r.append(i) ; ll += len(i)
            sys.stderr.write(".") ; sys.stderr.flush()
          if js_utf8: # normalise all before join
            for i in xrange(len(r)):
              if type(r[i])==bytes:
                r[i]=unicode(r[i],'latin1')
            r = u"".join(r)
          else: r = b"".join(r)
          if zlib:
            self.origLen = ll # needed for efficient malloc in the C code later
            oR,r = r,zlib.compress(r,9)
            sys.stderr.write("%d bytes (%s compressed from %d after opcode compaction saved %d on %s)\n" % (len(r),zlib_name,ll,compacted,','.join(sorted(list(compaction_types)))))
          else: sys.stderr.write("%d bytes (opcode compaction saved %d on %s)\n" % (ll,compacted,','.join(sorted(list(compaction_types)))))
          return r
        except TooNarrow: pass
    assert 0, "can't even assemble it with 255-byte addressing !?!"

def js_escapeRawBytes(s):
  if js_utf8: # type(s)==type(u"")
    s = s.replace("\\",r"\\").replace('"',r'\"').replace(chr(8),r"\b").replace(chr(9),r"\t").replace(chr(10),r"\n").replace(chr(12),r"\f").replace(chr(13),r"\r")
    if ignore_ie8: s = s.replace(chr(11),r"\v")
    if js_octal: s = re.sub("[\x00-\x1f](?![0-9])",lambda m:r"\%o"%ord(m.group()),s)
    else: s = re.sub(chr(0)+r"(?![0-9])",r"\\0",s) # \0 is allowed even if not js_octal (and we need \\ because we're in a regexp replacement)
    return re.sub(b"[\x00-\x1f\x7f]",lambda m:br"\x%02x"%ord(m.group()),s.encode('utf-8'))
  elif type(s)==type(u""): # if we're being passed a Unicode string when not js_utf8, then we must be being called from post_normalise and we want \uNNNN output
    return re.sub("[^\x20-\x7e]",lambda m:r"\u%04x"%ord(m.group()),s).encode('latin1')
  # otherwise typeof(s)==typeof(b"")
  s = s.replace(b"\\",br"\\").replace(b'"',br'\"').replace(B(chr(8)),br"\b").replace(B(chr(9)),br"\t").replace(B(chr(10)),br"\n").replace(B(chr(12)),br"\f").replace(B(chr(13)),br"\r")
  if ignore_ie8: s = s.replace(B(chr(11)),br"\v")
  if js_octal: s = re.sub(b"[\x00-\x1f](?![0-9])",lambda m:br"\%o"%ord(m.group()),s)
  else: s = re.sub(b'\x00'+br"(?![0-9])",br"\\0",s) # \0 is allowed even if not js_octal (and we need \\ because we're in a regexp replacement)
  return re.sub(b"[\x00-\x1f\x7f-\xff]",lambda m:br"\x%02x"%ord(m.group()),s)

if not browser_extension:
  js_start = b'/* Javascript '+version_stamp+br"""

Usage:

 - You could just include this code and then call the
   annotate() function i.e. var result = annotate(input"""
  if sharp_multi: js_start += b", annotation_type_number"
  if glossfile: js_start += b", lines=2"
  js_start += b")"
  if not os.environ.get("JS_OMIT_DOM",""):
    js_start += br"""

   or, if you're in a browser and have loaded a page,
   annotate_page("""
    if sharp_multi:
      js_start += b"annotation_type_number"
      if glossfile: js_start += b","
    if glossfile: js_start += b"lines=2"
    js_start += br""")
   (run annogen with JS_OMIT_DOM environment variable set
   if you want to omit the annotate_page code)"""
  js_start += br"""

 - Or you could use (and perhaps extend) the Annotator
   object, and call its annotate() method.  If you have
   Backbone.JS, Annotator will instead be a generator
   (extending Backbone.Model) which you will have to
   instantiate yourself (possibly after extending it).
   The Annotator object/class is also what will be
   exported by this module if you're using Common.JS.

 - On Unix systems with Node.JS, you can run this file in
   "node" to annotate standard input as a simple test. */
"""
else: js_start = b"" # browser_extension
js_start += b"var Annotator={\n"
if not browser_extension:
  js_start += b" version: '"+version_stamp+b"',\n"
  if glossfile: js_start += b"numLines: 2 /* override to 1 or 3 if you must, but not recommended for learning */,\n"
  if known_characters: js_start += b"numKnownGroups: 0 /* override to number of \"known\" groups of characters (words composed entirely of these will be annotated with CSS class 'known') */,\n"
if sharp_multi: js_start += b"annotate: function(input,aType) { if(aType==undefined) aType=0;"
else: js_start += b"annotate: function(input) {"
if removeSpace: js_start += br" input=input.replace(/\B +\B/g,'');" # TODO: document that we do this (currently only in JS annotator here, and Android app via jsAnnot, although Web Adjuster does it separately in Python before calling the filter).  It deals with software that adds ASCII spaces between Chinese characters of the same word, without deleting spaces between embedded English words (TODO: this 'JS + app' version may still delete spaces between punctuation characters, which may be an issue for consecutive quoted words e.g. 'so-called "word1" "word2"').  If doing it at the nextbyte level, we'd have to update prevbyte; if this or doing it at switchbyte level (e.g. recurse) we'd have to do something about the copy pointer (skip the spaces?) and the near-call distance (and associated buffer sizes in C) so they're best pre-removed, but only from between characters we annotate.
if post_normalise: js_start += br"""
var nChars = this.nChars;
var origInBytes = unescape(encodeURIComponent(input));
input = input.replace(/./g,function(m){return nChars[m]||m});
if(this.contextL_u8) { this.contextL_u8=unescape(encodeURIComponent(decodeURIComponent(escape(this.contextL_u8)).replace(/./g,function(m){return nChars[m]||m}))); origInBytes = this.contextL_u8 + origInBytes }
if(this.contextR_u8) this.contextR_u8=unescape(encodeURIComponent(decodeURIComponent(escape(this.contextR_u8)).replace(/./g,function(m){return nChars[m]||m})));"""
js_start += br"""
input = unescape(encodeURIComponent(input)); // to UTF-8
var data = this.data""" # TODO: if input is a whole html doc, insert css in head (e.g. from annoclip and/or adjuster), and hope there's no stuff that's not to be annotated (form fields etc).  But really want them to be using browser_extension or annotate_page if doing this (TODO add css to annotate_page, already there in browser_extension)
if glossfile: js_start += b", numLines = this.numLines"
if known_characters: js_start += b", numKnownGroups = this.numKnownGroups, hFreq = this.hFreq"
js_start += br""";
var addrLen = data.charCodeAt(0), dPtr;
var p = 0; // read-ahead pointer
if(this.contextL_u8) { var cL=this.contextL_u8; input = cL+input; p=cL.length }
var inputLength = input.length;
if(this.contextR_u8) input += this.contextR_u8;
var copyP = p; // copy pointer
var output = new Array(), needSpace = 0;

function readAddr() {
  var i,addr=0;
  for (i=addrLen; i; i--) addr=(addr << """
if js_6bit: js_start += b"6) | (data.charCodeAt(dPtr++)-"+B(str(js_6bit_offset))+b");"
else: js_start += b"8) | data.charCodeAt(dPtr++);"
js_start += br"""
  
  return addr;
}

function readRefStr() {
  var a = readAddr(); var l=data.charCodeAt(a);"""
if js_6bit and not js_utf8:
  js_start += br"""
  if(l && l<123) a = data.slice(a+1,a+l-30);
  else a = data.slice(a+1,data.indexOf(data.charAt(a),a+1));"""
else: js_start += br"""
  if (l != 0) a = data.slice(a+1,a+l+1);
  else a = data.slice(a+1,data.indexOf('\x00',a+1));"""
if js_utf8: js_start += b"return unescape(encodeURIComponent(a))" # Unicode to UTF-8 (TODO: or keep as Unicode? but copyP things will be in UTF-8, as will the near tests)
elif js_6bit: js_start += b"return unescape(a)" # %-encoding
else: js_start += b"return a"
js_start += br"""}
function s() {
  if (needSpace) output.push(" ");
  else needSpace=1; // for after the word we're about to write (if no intervening bytes cause needSpace=0)
}

function readData() {
    var sPos = new Array(), c;
    while(1) {
        c = data.charCodeAt(dPtr++);
        if (c & 0x80) dPtr += (c&0x7F);"""
if js_6bit: js_start += br"""
        else if (c > 90) { c-=90; 
            var i=-1;if(p<inputLength){var cc=input.charCodeAt(p++)-93; if(cc>118)cc-=20; i=data.slice(dPtr,dPtr+c).indexOf(String.fromCharCode(cc))}
            if (i==-1) i = c;
            if(i) dPtr += data.charCodeAt(dPtr+c+i-1)-"""+B(str(js_6bit_offset))+br""";
            dPtr += c+c }"""
else: js_start += br"""
        else if (c > 107) { c-=107;
            var i = ((p>=inputLength)?-1:data.slice(dPtr,dPtr+c).indexOf(input.charAt(p++)));
            if (i==-1) i = c;
            if(i) dPtr += data.charCodeAt(dPtr+c+i-1);
            dPtr += c+c;
        }"""
js_start += br""" else switch(c) {
            case 50: dPtr = readAddr(); break;
            case 51: {
              var f = readAddr(); var dO=dPtr;
              dPtr = f; readData() ; dPtr = dO;
              break; }
            case 52: return;
            case 60: {
              var nBytes = data.charCodeAt(dPtr++)+1;
              var i = ((p>=inputLength)?-1:data.slice(dPtr,dPtr+nBytes).indexOf(input.charAt(p++)));
              if (i==-1) i = nBytes;
              dPtr += (nBytes + i * addrLen);
              dPtr = readAddr(); break; }
            case 70: if(needSpace) { output.push(' '); needSpace=0; } break;
            case 71: case 74: {
              var numBytes = (data.charCodeAt(dPtr++)-34)&0xFF;
              var base = input.slice(copyP, copyP + numBytes);
              output.push(base);
              copyP += numBytes;
              if(c==74) return; break; }
            case 72: case 75: {
              var numBytes = (data.charCodeAt(dPtr++)-34)&0xFF;
              var annot = readRefStr();
              var base = input.slice(copyP, copyP + numBytes); copyP += numBytes;
              s();"""
if glossfile: js_start += br"""
              switch (numLines) {
                case 1:
                  output.push("<ruby><rb>");
                  output.push(base);
                  output.push("</rb></ruby>");
                  break;
                case 3:
                  output.push("<ruby><rt>&nbsp;</rt><rb>");
                  output.push(annot); output.push("</rb><rb>");
                  output.push(base);
                  output.push("</rb></ruby>");
                  break;
                default:"""
js_start += br"""
                  output.push("<ruby><rb>");
                  output.push(base);
                  output.push("</rb><rt>");
                  output.push(annot);
                  output.push("</rt></ruby>")"""
if glossfile: js_start += b"}"
else: js_start += b";"
js_start += br"""
              if(c==75) return; break; }"""
if glossfile: js_start += br"""
            case 73: case 76: {
              var numBytes = (data.charCodeAt(dPtr++)-34)&0xFF;
              var annot = readRefStr();
              var title = readRefStr();
              var base = input.slice(copyP, copyP + numBytes); copyP += numBytes;
              s();
              switch (numLines) {
                case 1:
                  output.push("<ruby title=\"");
                  output.push(title);
                  output.push("\"><rb>");
                  output.push(base);
                  output.push("</rb>");
                  output.push("</ruby>");
                  break;
                case 3:
                  output.push("<ruby title=\"");
                  output.push(title);
                  output.push("\"><rt>");
                  output.push(title.match(/[^/(;]*/)[0]);
                  output.push("</rt><rb>");
                  output.push(annot);
                  output.push("</rb><rb>");
                  output.push(base);
                  output.push("</rb></ruby>");
                  break;
                default:
                  output.push("<ruby title=\"");
                  output.push(title);
                  output.push("\"><rb>");
                  output.push(base);
                  output.push("</rb><rt>");
                  output.push(annot);
                  output.push("</rt></ruby>") }
              if(c==76) return; break; }"""
if not js_6bit: js_start = js_start.replace(b"(data.charCodeAt(dPtr++)-34)&0xFF",b"data.charCodeAt(dPtr++)")
js_start += br"""
            case 80: sPos.push(p); break;
            case 81: p=sPos.pop(); break;
            case 90: {
                var tPtr = readAddr();
                var fPtr = readAddr();
                var nearbytes = data.charCodeAt(dPtr++);
  var o=p;
  if (o > nearbytes) o -= nearbytes; else o = 0;
  var max = p + nearbytes;
  if (max > input.length) max = input.length; // not inputLength: we include contextR_u8
  var tStr = input.slice(o,max);
                var found = 0;
                while (dPtr < tPtr && dPtr < fPtr) if (tStr.indexOf(readRefStr()) != -1) { found = 1; break; }
                dPtr = found ? tPtr : fPtr; break;
                }
        default: throw("corrupt data table at "+(dPtr-1)+"/"+data.length+" ("+c+")");
            }
        }
    }

while(p < inputLength) {
var oldPos=p;
dPtr=1;readData();
if (oldPos==p) { needSpace=0; output.push(input.charAt(p++)); copyP++; }
}
output=decodeURIComponent(escape(output.join("")));"""
if known_characters: js_start += br"""
if(numKnownGroups) output=output.replace(new RegExp("(<rb>["+hFreq.slice(0,numKnownGroups).join('')+"]+</rb><rt)(>.*?</rt>)",'g'),"$1 class=known$2");
""" # TODO: pre-cache hFreq regex on select (like in Android)?
js_start += br"""
return output"""
if js_6bit: js_start = js_start.replace(b"var numBytes = data.charCodeAt(dPtr++);",b"var numBytes = (data.charCodeAt(dPtr++)-"+B(str(js_6bit_offset-1))+b")&0xFF;")
if sharp_multi: js_start += br""".replace(new RegExp("(</r[bt]><r[bt]>)"+"[^#]*#".repeat("""+annotMap("aType")+br""")+"(.*?)(#.*?)?</r","g"),"$1$2</r")""" # normally <rt>, but this regexp will also work if someone changes the generated code to put annotation into second <rb> and title into <rt> as long as annotation is not given first.  Cannot put [^#<] as there might be <sup> etc in the annotation, and .*?# still matches across ...</rb><rt>... :-(
js_start += br"""; // from UTF-8 back to Unicode
}""" # end of annotate method
if post_normalise: js_start += b',\nnChars:(Object.fromEntries?Object.fromEntries:function(e){o={};Object.keys(e).forEach(function(k){[k,v]=e[k];o[k]=v});return o})(function(){var t="'+js_escapeRawBytes(u''.join(unichr(c) for c in post_normalise.values()))+b'".split("");return "'+js_escapeRawBytes(u''.join(unichr(c) for c in post_normalise.keys()))+b'".split("").map(function(e,i){return [e,t[i]]})}())'
if known_characters: js_start += b",\nhFreq: "+knownCharsGroupsArray
if not browser_extension: js_start += b",\n" # data: ... \n goes here (browser_extension reads it from annotate-dat.txt instead)
if post_normalise: js_start = js_start.replace(b"input.slice(copyP",b"origInBytes.slice(copyP").replace(b"push(input.charAt",b"push(origInBytes.charAt")
js_end = br"""};
function annotate(input"""
if sharp_multi: js_end += b",aType"
if glossfile: js_end += b",numLines"
if known_characters: js_end += b",numKnownGroups"
js_end += b""",contextL_u8,contextR_u8) {
Annotator.contextL_u8=contextL_u8; Annotator.contextR_u8=contextR_u8;
"""
if glossfile: js_end += b"if(numLines==undefined) numLines=2; Annotator.numLines=numLines; "
if known_characters: js_end += b"Annotator.numKnownGroups=numKnownGroups; "
js_end += b"return Annotator.annotate(input"
if sharp_multi: js_end += b",aType"
js_end += b")}"
if browser_extension:
  if gecko_id:
    if not gecko_id.startswith("{") or not gecko_id.endswith("}"): gecko_id = "{" + gecko_id + "}"
  else: gecko_id = ""
  if manifest_v3: js_end += br"""
function restoreOld(numLines,aType) {
    for(let c of Array.prototype.slice.call(document.getElementsByClassName("_adjust0")))
        if(c.oldTxt) c.parentNode.replaceChild(document.createTextNode(c.oldTxt),c); else if(c.oldHtml)c.parentNode.replaceChild(new DOMParser().parseFromString(c.oldHtml,"text/html").body.firstChild.cloneNode(true),c);
    document.annotWalkOff=(numLines==1);document.aType=aType;annotWalk(document,document) }"""
  else: js_end += br"""
if(localStorage.aType===undefined) localStorage.aType=0;
if(localStorage.numLines===undefined) localStorage.numLines=2;
var aType=localStorage.aType,numLines=localStorage.numLines,numKnownGroups=localStorage.numKnownGroups;""" # TODO: some of this can be omitted if not sharp_multi, not glossfile or not known_characters, and similarly above and below.  Low priority because this part is for browser extension and all three of these will likely be on.
  js_end += br"""function handleMessage(request, sender, sendResponse) {"""
  if manifest_v3: js_end += br"""
    chrome.storage.local.get(["aType"],(aType)=>{
    chrome.storage.local.get(["numLines"],(numLines)=>{
    chrome.storage.local.get(["numKnownGroups"],(numKnownGroups)=>{
        aType=aType["aType"];numLines=numLines["numLines"];numKnownGroups=numKnownGroups["numKnownGroups"];
        if(aType===undefined) aType=0;
        if(numLines===undefined) numLines=2;
        if(numKnownGroups===undefined) numKnownGroups=0;
        if(typeof request=='number') {
            if(request<0) numLines=-request;
            else if(request-Math.floor(request)>=.9) numKnownGroups=Math.floor(request);
            else {
                aType=request;
                if(numLines==1)numLines=2
            }
        }
        chrome.storage.local.set({["aType"]: aType, ["numLines"]: numLines, ["numKnownGroups"]: numKnownGroups},()=>{
"""
  js_end += b"if(typeof request=='number') {"
  if manifest_v3: js_end += br"""
      (chrome.tabs && chrome.tabs.query?chrome.tabs.query:browser.tabs.query)({},function(T){for (let t of T)(chrome.scripting && chrome.scripting.executeScript?chrome.scripting.executeScript:browser.scripting.executeScript)({target:{tabId:t.id,allFrames:true},func: restoreOld, args:[numLines,aType]},()=>{chrome.runtime.lastError})}); // ignore lastError as it's likely to be "cannot access chrome:// URL" if one of the tabs in the extension manager
      sendResponse(true);"""
  else: js_end += br"""
    if(request<0) localStorage.numLines=numLines=-request; else if(request-Math.floor(request)>=.9) localStorage.numKnownGroups=numKnownGroups=Math.floor(request); else {localStorage.aType=aType=request;if(numLines==1)localStorage.numLines=numLines=2}
    (chrome.tabs && chrome.tabs.query?chrome.tabs.query:browser.tabs.query)({},function(T){for (let t of T)(chrome.tabs && chrome.tabs.executeScript?chrome.tabs.executeScript:browser.tabs.executeScript)(t.id,{allFrames: true, code: 'for(let c of Array.prototype.slice.call(document.getElementsByClassName("_adjust0")))if(c.oldTxt)c.parentNode.replaceChild(document.createTextNode(c.oldTxt),c);else if(c.oldHtml)c.parentNode.replaceChild(new DOMParser().parseFromString(c.oldHtml,"text/html").body.firstChild.cloneNode(true),c);'+(numLines==1?'document.annotWalkOff=1':'document.annotWalkOff=0;document.aType='+aType+';annotWalk(document,document)')})})"""
  js_end += br"""
  } else if(typeof request=='boolean') sendResponse(request?(numLines==1?-1:aType):numLines); // status query (used by popup and by initial off/on)
  else if(request=='g') sendResponse(numKnownGroups);
  else {"""
  if not manifest_v3: js_end += br"""
      if(request==null) request={'t':getClip()};"""
  js_end += b"sendResponse(numLines>1?annotate(request['t']"
  if sharp_multi: js_end += b",aType"
  if glossfile: js_end += b",numLines"
  if known_characters: js_end += b",numKnownGroups"
  js_end += b",request['l'],request['r']):request['t'])}}"
  if manifest_v3: js_end += br""")})})}); return true}"""
  else: js_end += br"""
function getClip(){var area=document.createElement("textarea"); document.body.appendChild(area); area.focus();area.value='';document.execCommand("Paste");var txt=area.value; document.body.removeChild(area); return txt?txt:"Failed to read clipboard"}"""
  js_end += br"""fetch((typeof browser!='undefined'&&browser.runtime&&browser.runtime.getURL?browser.runtime.getURL:chrome."""+(b"runtime" if manifest_v3 else b"extension")+br""".getURL)("annotate-dat.txt")).then(function(r){r.text().then(function(r){Annotator.data=r;chrome.runtime.onMessage.addListener(handleMessage)})})""" # if not js_utf8, having to encode latin1 as utf8 adds about 25% to the file size, but text() supports only utf8; could use arrayBuffer() instead, but inefficient to read w. DataView(buf,offset,1), or could reinstate zlib (probably using base64 read in from file: would probably need to include a versioned unzip library instead of inline-minified subset)
elif not os.environ.get("JS_OMIT_DOM",""):
  js_end += br"""
function annotate_page("""
  if sharp_multi: js_end += b"aType"
  if glossfile: js_end += (b"" if js_end.endswith(b"(") else b",") + b"numLines"
  if known_characters: js_end += (b"" if js_end.endswith(b"(") else b",") + b"numKnownGroups"
  js_end += b") { "
  if glossfile: js_end += b"if(numLines==undefined) numLines=2; Annotator.numLines=numLines; "
  if known_characters: js_end += b"Annotator.numKnownGroups=numKnownGroups; "
  js_end += jsAnnot(False) + br"""return annotWalk(document,document)
}"""
if not browser_extension:
  js_end += br"""

if (typeof Backbone != "undefined" && Backbone.Model) {
  Annotator = Backbone.Model.extend(Annotator);"""
  if sharp_multi: js_end += br"""
  annotate=function(input,aType) { return new Annotator().annotate(input,aType) }"""
  else: js_end += br"""
  annotate=function(input) { return new Annotator().annotate(input) }"""
  js_end += br"""
}
if (typeof require != "undefined" && typeof module != "undefined" && require.main === module) {
  // Node.js command-line test
  fs=require('fs');
  process.stdout.write(annotate(fs.readFileSync('/dev/stdin').toString()));
} else if (typeof module != "undefined" && module.exports) { // Common.js
  module.exports = Annotator;
}
"""

extension_rubycss = b"span._adjust0 ruby{display:inline-table !important;vertical-align:bottom !important;-webkit-border-vertical-spacing:1px !important;padding-top:0.5ex !important;margin:0px !important} span._adjust0 ruby *{display: inline !important;vertical-align:top !important;line-height:1.0 !important;text-indent:0 !important;text-align:center !important;padding-left:0px !important;padding-right:0px !important} span._adjust0 rb{display:table-row-group !important;font-size:100% !important; opacity: 1.0 !important} span._adjust0 rt{display:table-header-group !important;font-size:100% !important;line-height:1.1 !important; opacity: 1.0 !important;font-family: FreeSerif, Lucida Sans Unicode, Times New Roman, serif !important}"
if known_characters: extension_rubycss += b"span._adjust0 ruby rt.known{display: none !important}"
extension_config=br"""<html><head><meta charset="utf-8">
<style>#cr{width:100%;border:thin dotted grey;max-width:15em;max-height:10em;overflow:auto;user-select:text} #cr:empty{padding:0.5ex}
button{background:#ededed;color:inherit}
button:disabled{border:thin red solid}
"""+extension_rubycss.replace(b"span._adjust0 ",b"")+br"""</style>
</head><body>
<nobr><button id="-1">Off</button> <button id="-2">2-line</button>"""
# -ve = num lines (if glossfile), +ve = annotNo (if sharp-multi)
if glossfile:
  extension_config += b' <button id="-3">3-line</button>'
  rangeStart = -3
else:
  rangeStart = -2
  extension_config=extension_config.replace(b'2-line',b'On')
extension_config += b'</nobr>'
if sharp_multi and annotation_names and ',' in annotation_names:
  extension_config += b"".join((b'<br><button id="%d">%s</button>' % (num,B(name))) for num,name in enumerate(annotation_names.split(',')))
  rangeEnd = len(annotation_names.split(','))
else: rangeEnd = 0
if known_characters:
  extension_config += b'<select id="kc"><option>Annotate all</option>' ; s = 0
  for _ in knownCharsGroups:
    if s>=800: s+=100
    elif s>=300: s+=50
    elif s>=100: s+=20
    else: s+=10
    extension_config += b'<option>Leave %d known</option>' % (s,)
  extension_config += b"</select>"
extension_config += b'<div id="cr"></div><button id="c">Clipboard</button><script src="config.js"></script></body></html>'
# Don't want Clipboard button to auto-refresh (and hide the button) in the desktop extension version, since would need to stop the refresh when view is no longer visible + is it really a good idea to timer-paste the clipboard on a desktop when conversion to text could be costly etc + many desktops would dismiss the extension box before letting you switch to another window to change the clipboard (unless it's in a VM)
if manifest_v3: extension_confjs = br"""function getClip(){var area=document.createElement("textarea"); document.body.appendChild(area); area.focus();area.value='';document.execCommand("Paste");var txt=area.value; document.body.removeChild(area); return txt?txt:"Failed to read clipboard"}"""
else: extension_confjs = b""
extension_confjs += b"function updateClip() {"
if manifest_v3: extension_confjs += b"chrome.runtime.sendMessage({'t':getClip()},(function(cr){"
else: extension_confjs += b"chrome.runtime.sendMessage(null,(function(cr){" # 'null' gets changed to getClib background-side in v2
extension_confjs += br"""
        var v=document.getElementById("cr");
        v.textContent = ''; // clear
        if(cr) {
            try {
                for(const t of new DOMParser().parseFromString('<span> '+cr+' </span>','text/html').body.firstChild.childNodes) v.appendChild(t.cloneNode(true));
                var a=v.getElementsByTagName('ruby'),i; for(i=0; i < a.length; i++) if(a[i].title) (function(e){e.addEventListener('click',(function(){alert(e.title)}))})(a[i])
            } catch(err) { console.log(err.message) }
        }
    }))}
function update() {
chrome.runtime.sendMessage(false,function(r) {var i;for(i=%d;i;i++){var e=document.getElementById(""+i);if(i==-r)e.setAttribute('disabled','disabled');else e.removeAttribute('disabled')}})"""  % rangeStart
if rangeEnd: extension_confjs += br""";
chrome.runtime.sendMessage(true,function(r) {for(var i=0;i<%d;i++){var e=document.getElementById(""+i);if(i==r)e.setAttribute('disabled','disabled');else e.removeAttribute('disabled')}})"""  % rangeEnd
if known_characters: extension_confjs += br""";
chrome.runtime.sendMessage('g',function(r) {document.getElementById("kc").options.selectedIndex=r});document.getElementById("kc").addEventListener("change",function(){chrome.runtime.sendMessage(document.getElementById("kc").options.selectedIndex+.91,function(){})})""" # 'g' = report numKnownGroups, used as selection index (did have 'undefined' for this but not all Chrome versions support that apparently)
extension_confjs += b';\nif(document.getElementById("cr").firstChild) updateClip()\n'
extension_confjs += b"} update();\n"
extension_confjs += b';'.join((b'document.getElementById("%d").addEventListener("click",function(){chrome.runtime.sendMessage(%d,update)})' % (n,n)) for n in xrange(rangeStart,rangeEnd))
extension_confjs += b';document.getElementById("c").addEventListener("click",updateClip)'

dart_src = br"""

/* Usage
   -----
   If this file is saved as annotator.dart,
   you can import 'annotator.dart';
   and then call the annotate() function."""
if dart_datafile: dart_src += br"""
   E.g. String result = await annotate(...);
   (make your function async.)  Will read """+B(dart_datafile)
dart_src += br"""
*/

import 'dart:convert';"""
if zlib: dart_src += b"import 'dart:io';"
dart_src += br"""
class _Annotator {
  static const version="""+b'"'+version_stamp+br"""";
  int numLines = 2;  // override to 1 or 3 if you must, but not recommended for learning"""
if dart_datafile: dart_src+=b"\n  static String data=null;"
else: dart_src+=b"\n  static final String data=%%DATA_INIT%%;"
dart_src += br"""
  int addrLen=data.codeUnitAt(0),dPtr;
  bool needSpace; StringBuffer output;
  int p, copyP; List<int> inBytes; int inputLength;
  String annotate(String input"""
if sharp_multi: dart_src += br""",[int aType=0]"""
dart_src += br""") {
    inBytes=utf8.encode(input); dPtr=0;
    inputLength=input.length;
    p=0; copyP=0;
    output = StringBuffer(); needSpace = false;
    while(p < inputLength) {
      int oldPos=p;
      dPtr=1;_readData();
      if (oldPos==p) { needSpace=false; output.write(String.fromCharCode(inBytes[p++])); copyP++; }
    }
    return Utf8Decoder().convert(output.toString().codeUnits)"""
if sharp_multi: dart_src += br""".replaceAllMapped(new RegExp("(</r[bt]><r[bt]>)"+"[^#]*#"*"""+annotMap("aType",True)+br"""+"(.*?)(#.*?)?</r"),(Match m)=>"${m[1]}${m[2]}</r")"""
dart_src += br""";
  }
  int _readAddr() { int addr=0; for (int i=addrLen; i>0; i--) addr=(addr << 8) | data.codeUnitAt(dPtr++); return addr; }
  String _readRefStr() {
    int a=_readAddr();
    int l=data.codeUnitAt(a);
    String r;
    if (l != 0) r=data.substring(a+1,a+l+1);
    else r=data.substring(a+1,data.indexOf("\u0000",a+1));"""
if js_utf8: dart_src += br"""
    return String.fromCharCodes(Utf8Encoder().convert(r));"""
else: dart_src += b"return r;"
dart_src += br"""
  }
  void _s() {
    if(needSpace) output.write(" ");
    else needSpace=true; // for after the word we're about to write (if no intervening bytes cause needSpace=false)
  }
  void _readData() {
    List<int> sPos=List<int>();
    while(true) {
      int c=data.codeUnitAt(dPtr++);
      if ((c & 0x80)!=0) dPtr += (c&0x7F); // short jump
      else if (c > 107) { // short switchbyte
        c-=107;
        var i = ((p>=inputLength)?-1:data.substring(dPtr,dPtr+c).indexOf(String.fromCharCode(inBytes[p++])));
        if (i==-1) i = c;
        if(i>0) dPtr += data.codeUnitAt(dPtr+c+i-1);
        dPtr += c+c;
      } else switch(c) {
        case 50: dPtr = _readAddr(); break;
        case 51: {
          int f = _readAddr(); int dO=dPtr;
          dPtr = f; _readData() ; dPtr = dO;
          break; }
        case 52: return;
        case 60: {
          int nBytes = data.codeUnitAt(dPtr++)+1;
          int i = ((p>=inputLength)?-1:data.substring(dPtr,dPtr+nBytes).indexOf(String.fromCharCode(inBytes[p++])));
          if (i==-1) i = nBytes;
          dPtr += (nBytes + i * addrLen);
          dPtr = _readAddr(); break; }
        case 70: if(needSpace) { output.write(" "); needSpace=false; } break;
        case 71: case 74: {
          int numBytes = data.codeUnitAt(dPtr++);
  output.write(String.fromCharCodes(inBytes.sublist(copyP,copyP+numBytes)));
  copyP += numBytes; if(c==74) return; break; }
        case 72: case 75: {
          int numBytes = data.codeUnitAt(dPtr++);
          String annot = _readRefStr();
          String base = String.fromCharCodes(inBytes.sublist(copyP,copyP+numBytes)); copyP += numBytes;
          _s();
          switch (numLines) {
            case 1:
              output.write("<ruby><rb>");
              output.write(base);
              output.write("</rb></ruby>");
              break;
            case 3:
              output.write("<ruby><rt>&nbsp;</rt><rb>");
              output.write(annot);
              output.write("</rb><rb>");
              output.write(base);
              output.write("</rb></ruby>");
              break;
            default:
              output.write("<ruby><rb>");
              output.write(base);
              output.write("</rb><rt>");
              output.write(annot);
              output.write("</rt></ruby>");
            } if(c==75) return; break; }
        case 73: case 76: {
          int numBytes = data.codeUnitAt(dPtr++);
          String annot = _readRefStr();
          String title = _readRefStr();
          String base = String.fromCharCodes(inBytes.sublist(copyP,copyP+numBytes)); copyP += numBytes;
          _s();
          switch (numLines) {
            case 1:
              output.write("<ruby title=\"");
              output.write(title);
              output.write("\"><rb>");
              output.write(base);
              output.write("</rb></ruby>");
              break;
            case 3:
              output.write("<ruby title=\"");
              output.write(title);
              output.write("\"><rt>");
              output.write(RegExp("[^/(;]*").matchAsPrefix(title).group(0));
              output.write("</rt><rb>");
              output.write(annot);
              output.write("</rb><rb>");
              output.write(base);
              output.write("</rb></ruby>");
              break;
            default:
              output.write("<ruby title=\"");
              output.write(title);
              output.write("\"><rb>");
              output.write(base);
              output.write("</rb><rt>");
              output.write(annot);
              output.write("</rt></ruby>");
          } if(c==76) return; break; }
        case 80: sPos.add(p); break;
        case 81: p=sPos.removeLast(); break;
        case 90: {
          int tPtr = _readAddr();
          int fPtr = _readAddr();
          int nearbytes = data.codeUnitAt(dPtr++);
  int o=p;
  if (o > nearbytes) o -= nearbytes; else o = 0;
  var max = p + nearbytes;
  if (max > inputLength) max = inputLength;
  String tStr = String.fromCharCodes(inBytes.sublist(o,max));
                bool found = false;
                while (dPtr < tPtr && dPtr < fPtr) if (tStr.indexOf(_readRefStr()) != -1) { found = true; break; }
                dPtr = found ? tPtr : fPtr; break;
                }
        default: throw("corrupt data table at ${dPtr-1}/${data.length} (${c})");
      }
    }
  }
}

"""
if dart_datafile: dart_src += b"Future<String> annotate(String s,["
else: dart_src += b"String annotate(String s,["
if sharp_multi: dart_src += b"int aType=0,"
dart_src += b"int numLines=2]) "
if dart_datafile: dart_src += b"async "
dart_src += b"{ "
if dart_datafile: dart_src += b"if(_Annotator.data==null) _Annotator.data=await %%DATA_INIT%%;"
dart_src += b"var a=_Annotator(); a.numLines=numLines; return a.annotate(s"
if sharp_multi: dart_src += b",aType"
dart_src += b"); }\n"
if zlib: dart_src = dart_src.replace(b"%%DATA_INIT%%",b"String.fromCharCodes(zlib.decoder.convert(%%DATA_INIT%%))")

py_start = b'# Python '+version_stamp+br"""

# You can import this module and call annotate(utf8 bytes)
# (from multiple threads if desired),
# or you can run from the command line on standard input.

# annotate has an optional second argument, which can be
# 'ruby' (default), 'raw' (annotation only) or 'braces'.

# This module is compatible with both Python 2.7 and Python 3.

"""
py_end = br"""
class Annotator:
 version="""+b'"'+version_stamp+br""""
 def __call__(self,inStr,aFormat):
  if aFormat=="ruby": self.startA,self.midA,self.endA = b"<ruby><rb>",b"</rb><rt>",b"</rt></ruby>"
  elif aFormat=="raw": self.startA=self.midA=self.endA = b""
  elif aFormat=="braces": self.startA,self.midA,self.endA = b"{",b"|",b"}"
  else: raise Exception("Unrecognised annotation format "+repr(aFormat))
  assert type(inStr)==bytes
  self.inStr = inStr
  self.addrLen = ord(data[:1])
  self.inputLength = len(inStr)
  self.p = 0 # read-ahead pointer
  self.copyP = 0 # copy pointer
  self.output = []
  self.needSpace = 0
  while self.p < self.inputLength:
    oldPos = self.p
    self.dPtr = 1 ; self.readData()
    if oldPos == self.p:
      self.needSpace=0
      self.output.append(inStr[self.p:self.p+1])
      self.p += 1 ; self.copyP += 1
  return b"".join(self.output)
 def readAddr(self):
  addr = 0
  for i in range(self.addrLen):
    addr=(addr << 8) | ord(data[self.dPtr:self.dPtr+1])
    self.dPtr += 1
  return addr
 def readRefStr(self):
  a = self.readAddr(); l=ord(data[a:a+1])
  if l: return data[a+1:a+l+1]
  else: return data[a+1:data.index(b'\x00',a+1)]
 def s(self):
  if self.needSpace: self.output.append(b" ")
  else: self.needSpace=1
 def readData(self):
  sPos = [] ; out = self.output
  while True:
    d = ord(data[self.dPtr:self.dPtr+1]) ; self.dPtr += 1
    if d==50: self.dPtr = self.readAddr()
    elif d==51:
      func = self.readAddr() ; dO = self.dPtr
      self.dPtr = func ; self.readData() ; self.dPtr = dO
    elif d==52: return
    elif d==60 or d<20:
      if d<20: nBytes=d+1
      else:
        nBytes = ord(data[self.dPtr:self.dPtr+1])+1
        self.dPtr += 1
      if self.p>=len(self.inStr): i = -1
      else: i = data[self.dPtr:self.dPtr+nBytes].find(self.inStr[self.p:self.p+1]) ; self.p += 1
      if i==-1: i = nBytes
      if d<20:
        if i>0: self.dPtr += ord(data[self.dPtr+nBytes+i-1:self.dPtr+nBytes+i])
        self.dPtr += nBytes * 2
      else:
        self.dPtr += (nBytes + i * self.addrLen)
        self.dPtr = self.readAddr()
    elif d==70:
      if self.needSpace:
        out.append(b' ') ; self.needSpace=0
    elif d==71 or d==74:
      numBytes = ord(data[self.dPtr:self.dPtr+1])
      self.dPtr += 1
      out.append(self.inStr[self.copyP:self.copyP+numBytes])
      self.copyP += numBytes
      if d==74: return
    elif d==72 or d==75:
      numBytes = ord(data[self.dPtr:self.dPtr+1])
      self.dPtr += 1
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
      numBytes = ord(data[self.dPtr:self.dPtr+1])
      self.dPtr += 1
      annot = self.readRefStr()
      title = self.readRefStr()
      self.s()
      if self.startA==b"{": # omit title in braces mode
        out.append(self.startA)
        out.append(self.inStr[self.copyP:self.copyP+numBytes])
      elif self.startA:
        out.append(b"<ruby title=\"");out.append(title)
        out.append(b"\"><rb>");
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
      nearbytes = ord(data[self.dPtr:self.dPtr+1])
      self.dPtr += 1
      o = max(self.p-nearbytes,0)
      maxx = min(self.p+nearbytes,self.inputLength)
      tStr = self.inStr[o:maxx]
      found = False
      while self.dPtr < tPtr and self.dPtr < fPtr:
        if self.readRefStr() in tStr:
          found = True ; break
      if found: self.dPtr = tPtr
      else: self.dPtr = fPtr
    elif d>0x80: self.dPtr += d-0x80
    else: raise Exception("corrupt data table at "+str(self.dPtr-1)+" ("+str(ord(data[self.dPtr-1:self.dPtr]))+")")

def annotate(inStr,p="ruby"): return Annotator()(inStr,p)
def main():
  import sys ; aFormat = 'ruby'
  for a in sys.argv[1:]:
    if a.startswith("--"): aFormat=a[2:]
  if type("")==type(u""): sys.stdout.buffer.write(annotate(sys.stdin.buffer.read(),aFormat)) # Python 3
  else: sys.stdout.write(annotate(sys.stdin.read(),aFormat)) # Python 2
if __name__=="__main__": main()
""" # TODO: annotation-type option from command line in py

c_zlib = br"""static unsigned char *data=NULL;
static void init() {
  z_stream s; memset(&s,0,sizeof(s));
  s.next_in=origData; s.avail_in=%%ZLIBLEN%%;
  data=malloc(%%ORIGLEN%%); // TODO: check non-NULL
  s.next_out=data; s.avail_out=%%ORIGLEN%%;
  inflateInit(&s); inflate(&s, Z_NO_FLUSH); // TODO: check for memory and data-corruption errors
  inflateEnd(&s);
}
"""
c_datadrive = br"""
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
    case 70: s0(); break;
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
    warnPhrases = phrases
    if phrases: it=re.finditer(phrasePattern,text)
    else: it=re.finditer(wordPattern,text)
    for i in it:
      y = i.group()
      if len(y) > 1000000 and warnPhrases:
        sys.stderr.write("WARNING: Your corpus needs more phrase delimiters!\nVery long phrases can take a LONG time to process.\n")
        warnPhrases = False
      yield y

markupPattern = re.compile(re.escape(markupStart)+"(.*?)"+re.escape(markupMid)+"(.*?)"+re.escape(markupEnd),flags=re.DOTALL)
wordPattern = re.escape(markupStart)+'.*?'+re.escape(markupEnd)
if suffix: suffix = re.compile('(?:'+'|'.join('(?:'+re.escape(i)+')' for i in T(suffix).split(','))+')(?='+re.escape(markupEnd)+r'|\s)')
multiWordPattern = re.escape(markupEnd)+".*?"+re.escape(markupStart) # indicates there could be more than one word
phrasePattern = re.compile(wordPattern+r'(\s*'+wordPattern+r')*',flags=re.DOTALL+re.UNICODE)
wordPattern = re.compile(wordPattern,flags=re.DOTALL)
wspPattern = re.compile(r"\s+",flags=re.UNICODE)

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
    
def status_update(phraseNo,numPhrases,wordsThisPhrase,nRules,phraseLastUpdate,lastUpdate,startTime,coverP,nRej):
  phraseSec = (phraseNo-phraseLastUpdate)*1.0/(time.time()-lastUpdate)
  if phraseSec < 100:
    phraseSecS = "%.1f" % phraseSec
  else: phraseSecS = "%d" % int(phraseSec)
  progress = status_prefix + "%s phrase/sec (%d%%/#w=%d) rules=%d cover=%d%%" % (phraseSecS,int(100.0*phraseNo/numPhrases),wordsThisPhrase,nRules,coverP)
  if warn_yarowsky: progress += (" rej=%d" % nRej)
  if time_estimate:
    if phraseNo < 10: phraseMin = phraseSec*60 # current 'instantaneous' speed
    else: phraseMin = phraseNo*60/(time.time()-startTime) # longer-term average
    minsLeft = (numPhrases-phraseNo)/phraseMin
    if minsLeft>60*24: progress += " %dd+" % int(minsLeft/60/24)
    elif minsLeft>60: progress += " %dh+" % int(minsLeft/60)
    elif minsLeft: progress += " %dmin+" % minsLeft
    # (including the + because this is liable to be an underestimate; see comment after the --time-estimate option)
    if len(progress) + 14 < screenWidth:
     progress += " (at %02d:%02d:%02d" % time.localtime()[3:6] # clock time: might be useful for checking if it seems stuck
     if len(progress) + 20 < screenWidth and not clear_eol == "  ": # (being able to fit this in can be intermittent)
      elapsed = time.time() - startTime
      progress += ", analyse=%d:%02d:%02d" % (elapsed/3600,(elapsed%3600)/60,elapsed%60)
     progress += ")"
  sys.stderr.write(progress+clear_eol+"\r")
  sys.stderr.flush()

def read_and_normalise():
  global infile, corpus_unistr
  if infile: infile=openfile(infile)
  else:
    infile = sys.stdin
    if isatty(infile): sys.stderr.write("Reading from standard input\n(If that's not what you wanted, press Ctrl-C and run again with --help)\n")
  corpus_unistr = getBuf(infile).read().decode(incode)
  if diagnose and not diagnose in corpus_unistr:
    diagnose_write(diagnose+" is not present in the corpus, even before normalisation")
    suppress = True
  else: suppress = False
  loaded_from_cache = normalise() # will change corpus_unistr
  if diagnose and not suppress and not diagnose in corpus_unistr:
    diagnose_write(diagnose+" was in the corpus before normalisation, but not after")
    if loaded_from_cache: diagnose_write("You might want to remove "+normalise_cache+' and redo the diagnose')

collapsed_separators = ['',"'",u"\u2019"] # TODO: customise
def addHyphenReplacements(hTry,w):
  for r in collapsed_separators:
    hTry.add(w.replace('-',r))
def normWord(w,allWords):
  hTry,typo = set(),None
  if '-' in w: addHyphenReplacements(hTry,w) # if not annot_whitespace, we'll replace any non-hyphenated 'run together' version by the version with the hyphen; that's often the sensible thing to do with pinyin etc (TODO more customisation??)
  md = markDown(w)
  if suffix and len(md)>=suffix_minlen:
    wN = re.sub(suffix,'',w)
    if not w==wN: hTry.add(wN) # normalise on having the suffix in
  if not capitalisation:
    wl = w.lower() # (as long as it's all Unicode strings, .lower() and .upper() work with accents etc)
    if not w==wl and wl in allWords:
      # This word is NOT always capitalised.
      # Could be 'caps if at start of sentence'
      # (or title-case etc), but might also be
      # a corpus error, so check numbers.
      if allWords[wl]*5 < allWords[w] and allWords[wl] <= normalise_debug: typo = (wl,(u"%s (%d instances) overrides %s (%d instances)" % (wl,allWords[wl],w,allWords[w])))
      # To simplify rules, make it always lower.
      w = wl
      if '-' in w: addHyphenReplacements(hTry,w)
      wN = re.sub(suffix,'',w)
      if not w==wN: hTry.add(wN)
  if annot_whitespace or (keep_whitespace and markDown(w) in keep_whitespace): return w,None,typo
  r = trySplit(wspPattern,w,md)
  if r: return r,hTry,typo
  elif r==False: # no space found in w
    r = trySplit("-",w,md) # hTry will normalise to putting the hyphen in if there's a without-hyphen version, but if there's a version that splits at the hyphen into separate words, we normalise to that instead as if the hyphen were a space (TODO: optionally?)
    if r: return r,hTry,typo
  return w,hTry,typo
def trySplit(splitPattern,w,md):
  if not re.search(splitPattern,w): return False
  if not splitPattern=="-": # (don't try runTogether on hyphens: that's hTry, as we want to normalise it to keeping the hyphen)
   for r in collapsed_separators:
    runTogether = re.sub(splitPattern,r,w)
    if not capitalisation and not runTogether.lower()==runTogether and runTogether.lower() in allWords: return runTogether.lower()
    if runTogether in allWords: return runTogether # varying whitespace in the annotation of a SINGLE word: probably simplest if we say the version without whitespace, if it exists, is 'canonical' (there might be more than one with-whitespace variant), at least until we can set relative normalisation authority (TODO)
    # TODO: do we check for annot[0]+annot[1:].lower() version too
  ao = annotationOnly(w)
  if splitPattern=="-": annotList = ao.split("-")
  else: annotList = ao.split()
  if len(md.split())==1 and len(annotList) <= len(md):
    # Try different ways of
    # assigning each word to chars, and see if any
    # of these exist in the corpus; if any does,
    # assume we have "ABC|a bc" <= "A|a BC|bc" type
    # situations - the latter shouldn't necessarily be
    # converted into the former, but the former might
    # be convertible into the latter to simplify rules
    if capitalisation: annotListLower = annotList
    else: annotListLower = [w0.lower() for w0 in annotList]
    for charBunches in different_ways_of_splitting(md,len(annotList)):
      mwLowerList = [markUp(c,w0) for c,w0 in zip(charBunches,annotListLower)]
      if "".join(mwLowerList) in cu_lower_nospaces:
        if not capitalisation:
          for i in range(len(annotList)):
            wu = markUp(charBunches[i],annotList[i])
            wl = mwLowerList[i]
            if not wu==wl and not wl in allWords:
              mwLowerList[i] = wu # restore original caps
        return "".join(mwLowerList)
      # TODO: is there ANY time where we want multiword to take priority over the runTogether version above?  or even REPLACE multiword occurrences in the corpus with the runTogether version?? (must be VERY CAREFUL doing that)
def normBatch(words):
  r,typoR = [],[]
  for w in words:
    w2,hTry,typo = normWord(w,allWords)
    if hTry:
      hTry.add(w2.replace('-','')) # in case not already there
      for h in hTry:
        if not h==w2 and h in allWords:
          r.append((h,w2))
    if not w==w2: r.append((w,w2))
    if typo: typoR.append(typo)
  return r,typoR

def normalise():
    global capitalisation # might want to temp change it
    global corpus_unistr,allWords,cu_lower_nospaces
    if normalise_cache:
      try:
        corpus_unistr = openfile(normalise_cache).read().decode('utf-8')
        sys.stderr.write("Normalised copy loaded\n")
        return True # loaded from cache
      except: pass
    if (capitalisation and annot_whitespace) or priority_list: return # TODO: might want to normalise at least the word breaks if priority_list (but it loads it anyway if cached)
    sys.stderr.write("Normalising...");sys.stderr.flush()
    old_caps = capitalisation
    if priority_list: capitalisation = True # no point keeping it at False
    allWords = getAllWords()
    if removeSpace:
     corpus_unistr = re.sub(re.escape(markupEnd)+r'\s+'+re.escape(markupStart),(markupEnd+markupStart).replace('\\',r'\\'),corpus_unistr,flags=re.UNICODE) # so getOkStarts works consistently if corpus has some space-separated and some not
     corpus_unistr = re.sub(re.escape(markupStart)+r'\s+',markupStart.replace('\\',r'\\'),re.sub(r'\s+'+re.escape(markupMid),markupMid.replace('\\',r'\\'),re.sub(re.escape(markupMid)+r'\s+',markupMid.replace('\\',r'\\'),re.sub(r'\s+'+re.escape(markupEnd),markupEnd.replace('\\',r'\\'),corpus_unistr,flags=re.UNICODE),flags=re.UNICODE),flags=re.UNICODE),flags=re.UNICODE) # so we're tolerant of spurious whitespace between delimeters and markup (TODO: do this even if not removeSpace?)
     if not annot_whitespace:
      # normalise trailing hyphens e.g. from OCR'd scans:
      cu0 = corpus_unistr ; ff = 0
      for hTry in [1,2]:
        for w in allWords.keys():
          if '-'+aoEnd in w:
            idx = w.index('-'+aoEnd)
            if w[:idx].endswith(aoStart) or w[:idx].endswith("-"): continue # ignore this one (a mess of some kind)
            if hTry==2: # ouch, this doesn't look good
              getBuf(sys.stderr).write((u" (can't normalise hyphens due to '%s') " % w).encode(terminal_charset,'replace')) ; sys.stderr.flush()
              corpus_unistr = cu0 ; break
            if mreverse: grp,mdG=r"-\1",r"\2"
            else: grp,mdG=r"-\2",r"\1"
            # TODO: batch up the following replacements by using something similar to Replacer but with a common destination regexp that takes groups from the 'w' entries as well.  (Low priority because don't typically get TOO many of these dangling hyphens in most corpuses.)
            corpus_unistr = re.sub(re.escape(w)+r"\s*"+re.escape(markupStart)+"(.*?)"+re.escape(markupMid)+"(.*?)"+re.escape(markupEnd),w.replace('\\',r'\\').replace('-'+aoEnd.replace('\\',r'\\'),grp+aoEnd.replace('\\',r'\\')).replace(mdEnd.replace('\\',r'\\'),mdG+mdEnd.replace('\\',r'\\')),corpus_unistr,flags=re.DOTALL+re.UNICODE)
            ff = 1
        if ff: allWords = getAllWords() # re-generate
      del cu0
    cu_lower_nospaces = re.sub(wspPattern,"",corpus_unistr) # doesn't matter that spaces inside annotation are also taken out by this, since it's used only for searching for words that don't have spaces in their annotation in the split logic
    if not capitalisation: cu_lower_nospaces = cu_lower_nospaces.lower()
    sys.stderr.write(":") ; sys.stderr.flush()
    tmp = corpus_unistr ; del corpus_unistr
    numCores = setup_parallelism()
    corpus_unistr = tmp
    perCore = int(len(allWords)/numCores)+1
    allWL = list(allWords.keys()) ; jobs = []
    for c in xrange(numCores-1): jobs.append(executor.submit(normBatch,allWL[c*perCore:(c+1)*perCore]))
    if numCores>1: allWL=allWL[(numCores-1)*perCore:]
    results = [normBatch(allWL)]
    del allWords,cu_lower_nospaces
    for j in jobs: results.append(j.result())
    if cores_command: os.system(cores_command+" 1")
    sys.stderr.write(".") ; sys.stderr.flush()
    dic = {}
    for SR,typos in results:
      for x,y in SR:
        if diagnose and diagnose in x: diagnose_write("Changing %s to %s" % (x,y))
        dic[x] = y
      for wl,msg in typos: typo_report("normalise-debug.txt","allow-caps-exceptions.txt",wl,msg)
    for k in list(dic.keys()):
      seen = set()
      while dic[k] in dic:
        v = dic[dic[k]]
        assert not v in seen, "normalisation loop!"
        if v in seen: break
        seen.add(v)
        dic[k] = v
    sys.stderr.write(":") ; sys.stderr.flush()
    for exp in orRegexes(re.escape(k) for k in iterkeys(dic)):
      corpus_unistr = re.sub(exp,lambda k:dic[k.group(0)],corpus_unistr)
    sys.stderr.write(" done\n")
    if normalise_cache and capitalisation==old_caps: openfile(normalise_cache,'w').write(corpus_unistr.encode('utf-8'))
    capitalisation = old_caps
def getAllWords():
  allWords = {}
  for phrase in splitWords(corpus_unistr,phrases=True):
    for w in splitWords(phrase): allWords[w]=allWords.setdefault(w,0)+1
  return allWords # do NOT cache (call = regenerate)
def orRegexes(escaped_keys):
  escaped_keys = list(escaped_keys) # don't just iterate
  if not escaped_keys: return # don't yield ""
  try: yield re.compile('|'.join(escaped_keys))
  except OverflowError: # regex too big (e.g. default Python on Mac OS 10.7 i.e. Python 2.7.1 (r271:86832, Jul 31 2011, 19:30:53); probably some Windows versions also; does not affect Mac HomeBrew's Python 2.7.12)
    ek = escaped_keys[:int(len(escaped_keys)/2)]
    for r in orRegexes(ek): yield r
    ek = escaped_keys[len(ek):]
    for r in orRegexes(ek): yield r

def PairPriorities(markedDown_Phrases,existingPris={}):
    markedDown_Phrases = list(markedDown_Phrases)
    assert all(type(p)==list for p in markedDown_Phrases)
    mdwSet = set(existingPris.keys())
    for p in markedDown_Phrases: mdwSet.update(p)
    assert all(type(w)==unicode for w in mdwSet)
    votes = {} ; lastT = time.time()
    for pi in xrange(len(markedDown_Phrases)):
      if time.time() > lastT+2:
        sys.stderr.write("PairPriorities: %d%%%s\r" % (pi*100/len(markedDown_Phrases),clear_eol)) ; sys.stderr.flush()
        lastT = time.time()
      p=markedDown_Phrases[pi]
      for x in xrange(len(p)-1):
        a,b = p[x:x+2]
        combined = a+b
        for i in xrange(1,len(combined)):
            if i==len(a): continue
            elif i<len(a): prefer,over = a,combined[i:]
            else: prefer,over = b,combined[:i]
            if not (prefer in mdwSet and over in mdwSet and not prefer==over): continue
            k = tuple(sorted([prefer,over]))
            if k[0]==prefer: direction = 1
            else: direction = -1
            votes[k]=votes.get(k,0)+direction
            if diagnose in k: diagnose_write("Prefer %s over %s: %d vote from %s | %s" % (k+(direction,a,b)))
    sys.stderr.write("PairPriorities: done (%d relationships)\n" % len(votes))
    del markedDown_Phrases
    global closure,gtThan,lessThan
    closure,gtThan, lessThan = set(),{},{}
    def addToClosure(a,b):
        # If a>b, then a>c for any b>c (c<b)
        # (actually b>=c but we don't have equality),
        # and c>b for any c>a.
        candidate = set([(a,b)]+[(a,c) for c in lessThan.get(b,[])]+[(c,b) for c in gtThan.get(a,[])])
        if closure==None: # no longer tracking closure
          if any(y in gtThan.get(x,{}) for (x,y) in candidate): return # contradiction
        else:
          if any((y,x) in closure for (x,y) in candidate):
            return # contradiction, use higher abs votes
          closure.update(candidate)
        for x,y in candidate:
            # x>y y<x, so y should be in lessThan[x]
            lessThan.setdefault(x,set()).add(y)
            gtThan.setdefault(y,set()).add(x)
        return True
    for _,v,a,b in reversed(sorted([(abs(v),v,a,b) for (a,b),v in votes.items()])):
        if v < 0: a,b = b,a
        r=addToClosure(a,b)
        if diagnose in (a,b):
          if r==None: r = False
          diagnose_write("addToClosure(%s,%s) [v=%d] returned %s" % (a,b,abs(v),repr(r)))
    trueClosure,closure = closure,None
    lastW,lastP,lastPriorW = set(),None,set()
    if existingPris: sys.stderr.write("Processing %d existing priorities...\n" % len(existingPris.items()))
    for _,w in reversed(sorted((p,w) for w,p in existingPris.items())): # highest priority first
      if lastP and existingPris[w] < lastP:
        lastPriorW,lastW = lastW,set()
        lastP = existingPris[w]
      for W in lastPriorW: addToClosure(W,w)
      lastW.add(w)
    sys.stderr.write("%d words\n" % len(mdwSet))
    # Kahn 1962 - topological sort:
    no_incoming = set(w for w in mdwSet if not w in lessThan)
    del mdwSet ; mdwList = []
    while no_incoming:
      n = no_incoming.pop()
      mdwList.append(n)
      if not n in gtThan: continue
      for m in gtThan[n]:
        lessThan[m].remove(n)
        if not lessThan[m]:
          del lessThan[m] ; no_incoming.add(m)
      del gtThan[n]
    assert not lessThan and not gtThan, "graph has cycle(s), (%d,%d) edges remain" % (len(lessThan),len(gtThan))
    tcA = set(w for w,_ in trueClosure)
    if diagnose: diagnose_write("%s in tcA %s" % (diagnose,diagnose in tcA))
    r = [] ; _cmpT,_cmpW=time.time(),False
    for w in mdwList: # lower priorities first
        if time.time() > _cmpT + 2:
          sys.stderr.write("Finalising: %d/%d%s\r" % (len(r),len(mdwList),clear_eol)) ; sys.stderr.flush()
          _cmpT=time.time()
          _cmpW=True
        if w in tcA:
          if w==diagnose:
            f0 = existingPris.get(w,0)
            found = False
            for i in xrange(len(r)):
              W,f = r[i]
              if (w,W) in trueClosure:
                found = True
                if 1+f > f0:
                  diagnose_write("Increasing f(%s) from %d to %d to outweigh %s (f=%d)" % (w,f0,1+f,W,f))
                  f0 = 1+f
                else: diagnose_write("f(%s)=%d already outweighs %d for %s" % (w,f0,f,W))
              elif (W,w) in trueClosure:
                found = True
                diagnose_write("Problem? %s (f=%d) before %s (f=%d)" % (W,f,w,f0))
            if not found: diagnose_write("No interactions with %s found among %d lower-priority words" % (w,len(r)))
            l = [f0-1]
          else: l = [r[i][1] for i in xrange(len(r)) if (w,r[i][0]) in trueClosure]
        else: l = []
        r.append((w,1+max([existingPris.get(w,0)-1]+l)))
    if _cmpW: sys.stderr.write("Finalising: done%s\n" % clear_eol)
    return sorted(r)

def skipToNext(thing): return "(?:(?!"+re.escape(thing)+").)*"+re.escape(thing) # not ".*?"+re.escape(thing) as it may absorb one 'thing' to match the rest of the regex later
if mreverse: mdStart,mdEnd,mdSplitR,aoStart,aoEnd = markupMid,markupEnd,re.escape(markupEnd)+r'\s*'+re.escape(markupStart)+skipToNext(markupMid),markupStart,markupMid
else: mdStart,mdEnd,mdSplitR,aoStart,aoEnd = markupStart,markupMid,re.escape(markupMid)+skipToNext(markupEnd)+r'\s*'+re.escape(markupStart),markupMid,markupEnd
mdSplitR="(?:"+mdSplitR+")?" # so can use it in .join(chars) to say "maybe word-break between these chars"

def different_ways_of_splitting(chars,numWords):
  if numWords > len(chars): return
  elif numWords == len(chars):
    yield list(chars) ; return
  elif numWords == 1:
    yield [chars] ; return
  spAt_try1 = int(len(chars) / numWords) + 1
  for spAt in list(range(spAt_try1,0,-1)) + list(range(spAt_try1+1, len(chars)-numWords+1)):
    for r in different_ways_of_splitting(chars[spAt:],numWords-1): yield [chars[:spAt]]+r

if type(u"")==type(""): # Python 3
  getNext = lambda gen: gen.__next__()
  iterkeys = lambda d: d.keys()
  itervalues = lambda d: d.values()
  iteritems = lambda d: d.items()
else: # Python 2
  getNext = lambda gen: gen.next()
  iterkeys = lambda d: d.iterkeys()
  itervalues = lambda d: d.itervalues()
  iteritems = lambda d: d.iteritems()

def yarowsky_indicators(withAnnot_unistr,canBackground):
    # yields True if rule always works (or in majority of cases with ymajority), or lists enough indicators to cover example instances and yields (negate, list, nbytes), or just list if empty.
    # (If too few indicators can be found, will list the ones it can, or empty if no clearly-distinguishable indicators can be found within ybytes of end of match.)
    # yield "backgrounded" = task has been backgrounded; getNext collects result
    nonAnnot=markDown(withAnnot_unistr)
    def unconditional_looks_ok(explain):
        # could we have this as an unconditional rule, with the other cases as exceptions that will be found first?  (NB this is not the same thing as a 'default-yes rule with exceptions', this is a rule with NO qualifying indicators either way)
        if len(nonAnnot)==1:
          if nonAnnot==diagnose: diagnose_write("%s is default by %s len=1 rule after removing irrelevant badStarts" % (withAnnot_unistr,explain))
          return True # should be safe, and should cover most "common short Chinese word with thousands of contexts" cases
        # If len 2 or more, it's risky because the correct solution could be to process just a fraction of the word now and the rest will become the start of a longer word, so we probably don't want it matching the whole lot by default: we'll want positive or negative indicators instead.
        # e.g. looking at rule AB, text ABC and correct segmentation is A BC, don't want it to 'greedily' match AB by default without indicators it should do so
        # Check for no "A BC" situations, i.e. can't find any possible SEQUENCE of rules that STARTS with ALL the characters in nonAnnot and that involves having them SPLIT across multiple words:
        # (The below might under-match if there's the appearance of a split rule but it actually has extra non-marked-up text in between, but it shouldn't over-match.)
        # TODO: if we can find the actual "A BC" sequences (instead of simply checking for their possibility as here), and if we can guarantee to make 'phrase'-length rules for all of them, then AB can still be the default.  This might be useful if okStarts is very much greater than badStarts.  It would require checkCoverage to mark "A" as False if there exists a (no-indicators) "AB" rule.
        # (TODO: until the above is implemented, consider recommending --ymax-threshold=0 so all ybytes ranges are tried, because, now that Yarowsky-like collocations can be negative, the 'following word' could just go in as a collocation with low ybytes)
        # TODO: also, if the exceptions to rule AB are always of the form "Z A B", and we can guarantee to generate a phrase rule for "Z A B", then AB can still be default.  (We should already catch this when the exceptions are "ZA B", but not when they are "Z A B", and --ymax-threshold=0 probably won't always help here, especially if Z==B; Mandarin "mei2you3" / "you3 mei2 you3" comes to mind)
        llen = len(mdStart)+len(nonAnnot)
        regex=re.compile(re.escape(mdStart) + mdSplitR.join(re.escape(c) for c in list(nonAnnot)))
        if all(x.end()-x.start()==llen for x in re.finditer(regex,corpus_unistr)):
          if nonAnnot==diagnose: diagnose_write("%s is default by %s rule after checking for dangerous overlaps etc" % (withAnnot_unistr,explain))
          return True
        if nonAnnot==diagnose: diagnose_write("%s cannot be default by %s due to %s" % (withAnnot_unistr,explain,', '.join(list(set(["'"+x.group()+"'" for x in re.finditer(regex,corpus_unistr) if not x.end()-x.start()==llen]))[:5])))
    if nonAnnot in yPriorityDic: # TODO: enforce len==1 ?
        if yPriorityDic[nonAnnot] == withAnnot_unistr:
            # we want this case to be the default
            if len(withAnnot_unistr)==1:
                if nonAnnot==diagnose: diagnose_write("ref-pri forces %s" % (withAnnot_unistr,))
                yield True ; return
            else:
                if nonAnnot==diagnose: diagnose_write("ref-pri wants %s by default: finding negative indicators only" % (withAnnot_unistr,))
                can_be_default = "must"
                # might not even need to get okStarts, etc
                if unconditional_looks_ok("ref-pri"):
                  yield True ; return
        else:
          if nonAnnot==diagnose: diagnose_write("ref-pri forbids default %s" % (withAnnot_unistr,))
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
    if can_be_default==True and len(okStarts) > len(badStarts) and unconditional_looks_ok("majority-case"): # (if can_be_default=="must", we have already checked for unconditional_looks_ok() above before computing okStarts and badStarts)
        yield True ; return
    run_in_background = canBackground and len(okStarts) > 500 and executor # In a test with 300, 500, 700 and 900, the 500 threshold was fastest on concurrent.futures, but by just a few seconds.
    may_take_time = canBackground and len(okStarts) > 1000
    if may_take_time:
      getBuf(sys.stderr).write((u"\nLarge collocation check (%s has %d matches + %s), %s....  \n" % (withAnnot_unistr,len(okStarts),badInfo(badStarts,nonAnnot),"backgrounding" if run_in_background else "could take some time")).encode(terminal_charset,'replace'))
      if len(badStarts) <= yarowsky_debug: typo_report("yarowsky-debug.txt","allow-exceptions.txt",withAnnot_unistr,(u"%s has %d matches + %s" % (withAnnot_unistr,len(okStarts),badInfo(badStarts,nonAnnot,False))))
    if run_in_background:
      job = executor.submit(yarowsky_indicators_wrapped,withAnnot_unistr) # recalculate the above on the other CPU in preference to passing, as memory might not be shared
      yield "backgrounded" ; yield job
      yield job.result() ; return
    if ybytes_max > ybytes and (not ymax_threshold or len(nonAnnot) <= ymax_threshold):
      retList = [] ; append=retList.append
      times = []
      for nbytes in range(ybytes,ybytes_max+1,ybytes_step):
        t = time.time()
        negate,ret,covered,toCover,nbytes = tryNBytes(nbytes,nonAnnot,badStarts,okStarts,withAnnot_unistr,can_be_default=="must",nbytes==ybytes_max)
        if covered==toCover and len(ret)==1:
          if may_take_time: sys.stderr.write(" - using 1 indicator, negate=%s\n" % repr(negate))
          yield (negate,ret,nbytes) ; return # a single indicator that covers everything will be better than anything else we'll find
        append((-int(covered*100/toCover),len(ret),nbytes,negate,toCover,ret)) # (1st 4 of these are the sort keys: maximum coverage to nearest 1%, THEN minimum num indicators for the same coverage, THEN minimum nbytes (TODO: problems of very large nbytes might outweigh having more indicators; break if found 100% coverage by N?), THEN avoid negate)
        # TODO: try finding an OR-combination of indicators at *different* proximity lengths ?
        if nbytes>ybytes and ymax_limitwords and nonAnnot in ymax_limitwords: break
        times.append(time.time()-t) ; t=time.time()
      if len(times)>2 and sum(times) > 20*60 and not min(i[0] for i in retList)<1.05*min(i[0] for i in retList[:2]): diagnose_write("%s took %d+mins, consider --ymax-limitwords (mins:%s, coverage:%s, indicators:%s, noexpand discards #2+)" % (withAnnot_unistr,sum(times)/60,",".join(str(int(t/60)) for t in times),",".join((str(-i[0])+"%") for i in retList),",".join(str(i[1]) for i in retList)),"Suggestion")
      ret0 = min(retList,key=lambda x:x[:3]+(str(x[3]),)) # (don't let Python3 try to compare True with 'harder' in x[3] like Python2 does)
      if nonAnnot==diagnose: diagnose_write("Best coverage is %d%% of %d" % (-ret0[0],ret0[-2]))
      negate,ret = ret0[-3],ret0[-1]
      distance = ret0[2]
    else:
      negate,ret = tryNBytes(ybytes_max,nonAnnot,badStarts,okStarts,withAnnot_unistr,can_be_default=="must")[:2]
      if ybytes < ybytes_max: distance = ybytes_max
      else: distance = None # all the same anyway
    if not ret and warn_yarowsky: getBuf(sys.stderr).write((u"Couldn't find ANY Yarowsky-like indicators for %s   \n" % withAnnot_unistr).encode(terminal_charset,'replace')) # (if nonAnnot==diagnose, this'll be reported by tryNBytes below)
    # TODO: if partially but not completely covered, shouldn't entirely count the word as 'covered' in analyse()
    elif ret and may_take_time: sys.stderr.write(" - using %d indicators, negate=%s\n" % (len(ret),repr(negate)))
    if not ret or (not distance and not negate):
      yield ret
    else:
      if not distance: distance = ybytes_max
      yield negate,ret,distance
typo_data = {}
def typo_report(debugFile,exceptionFile,withAnnot_unistr,msg_unistr):
  if not exceptionFile in typo_data:
    try: typo_data[exceptionFile]=set(splitWords(openfile(exceptionFile).read().decode(terminal_charset)))
    except IOError: typo_data[exceptionFile]=set()
  if withAnnot_unistr not in typo_data[exceptionFile]:
    if not debugFile in typo_data:
      typo_data[debugFile] = openfile(debugFile,'w')
      getBuf(sys.stderr).write(B(bold_on+"Writing to "+debugFile+bold_off+"\n"))
      getBuf(typo_data[debugFile]).write(B("Put any of the following first-of-line words into %s to avoid being alerted here next time.\n\n" % exceptionFile))
    getBuf(typo_data[debugFile]).write((msg_unistr+u"\n").encode(terminal_charset,'replace'))
    typo_data[debugFile].flush() # in case interrupted
def yarowsky_indicators_wrapped(withAnnot_unistr):
    return getNext(yarowsky_indicators(withAnnot_unistr,False))
def getOkStarts(withAnnot_unistr):
    if withAnnot_unistr in precalc_sets: return precalc_sets[withAnnot_unistr]
    walen = len(withAnnot_unistr)
    return set(x for x in precalc_sets[getNext(splitWords(withAnnot_unistr))] if corpus_unistr[m2c_map[x]:m2c_map[x]+walen]==withAnnot_unistr)
def getBadStarts(nonAnnot,okStarts):
  r = [] ; append=r.append
  l=len(nonAnnot)
  k = nonAnnot[:2]
  if k in bigramCache:
    for i in bigramCache[k]:
      if not i in okStarts and corpus_markedDown[i:i+l]==nonAnnot: append(i)
    return r
  find = corpus_markedDown.find
  i = find(nonAnnot)
  while i != -1:
    if not i in okStarts: append(i)
    i = find(nonAnnot,i+l)
  return r
def getReallyBadStarts(badStarts,nonAnnot):
    # Some of the badStarts can be ignored on the grounds that they should be picked up by other rules first: any where the nonAnnot match does not start at the start of a word (the rule matching the word starting earlier should get there first), and any where it starts at the start of a word that is longer than its own first word (the longest-first ordering should take care of this).  So keep only the ones where it starts at the start of a word and that word is no longer than len(nonAnnot).
    reallyBadStarts = [] ; append=reallyBadStarts.append
    nonAnnotLen = len(mdStart+nonAnnot+mdEnd)
    theRe = re.compile(re.escape(mdStart+nonAnnot[0])+".*?"+re.escape(mdEnd),flags=re.DOTALL)
    for b in badStarts:
      try: s = m2c_map[b]
      except KeyError: continue # it wasn't the start of a word (only start positions are in that map)
      m=theRe.search(corpus_unistr, s) # will either start at s, or after it if mreverse
      assert m, "m2c_map error? "+repr(nonAnnot[0])+" "+repr(b)+"->"+repr(s)+" not found ( "+repr(corpus_markedDown[b:b+25])+"... -> "+repr(corpus_unistr[s:s+50])+"...)"
      s,e = m.start(),m.end()
      if e-s > nonAnnotLen: continue # this word is too long, should be matched by a longer rule 1st
      append(b) # to reallyBadStarts
    return reallyBadStarts
def tryNBytes(nbytes,nonAnnot,badStarts,okStarts,withAnnot_unistr,force_negate,try_harder=True):
    # try to find either positive or negative Yarowsky-like indicators, whichever gives a smaller set (or only negative ones if force_negate, used by end_pri yPriorityDic logic).  Negative indicators might be useful if there are many matches and only a few special exceptions.  (If not force_negate, then negative indicators are used only if they cover 100% of the exceptions; see below re negate==None)
    def bytesAround(start): return within_Nbytes(start+len(nonAnnot),nbytes)
    okStrs=list(set(bytesAround(s) for s in okStarts))
    badStrs=list(set(bytesAround(s) for s in badStarts))
    if nonAnnot==diagnose:
      inBoth = set(okStrs).intersection(set(badStrs))
      if inBoth: diagnose_write("tryNBytes(%d) on %s has contexts that are both OK and bad: %s" % (nbytes,withAnnot_unistr,"/".join(list(inBoth)[:10])))
    pOmit = unichr(1).join(badStrs) # omit anything that occurs in this string from +ve indicators
    nOmit = unichr(1).join(okStrs) # ditto for -ve indicators
    avoidSelf = unichr(1)+nonAnnot[max(0,len(nonAnnot)-nbytes):].encode(outcode)[-nbytes:].decode(outcode,'ignore')
    pOmit += avoidSelf ; nOmit += avoidSelf
    pCovered=[False]*len(okStrs)
    nCovered=[False]*len(badStrs)
    n2Covered=[False]*len(badStrs)
    pRet = [] ; pAppend=pRet.append
    nRet = [] ; nAppend=nRet.append
    n2Ret = [] ; nAppend2 = n2Ret.append
    negate = None # not yet set
    toCheck = [] ; diagnostics = []
    if not force_negate:
      didFind = [] # for append(True) when something found, used only by diagnostics
      diagnostics.append((didFind,"",pRet,pCovered))
      toCheck.append((didFind,okStrs,pAppend,pCovered,unique_substrings(okStrs,lambda txt:txt in pOmit,lambda txt:sum(1 for s in okStrs if txt in s)))) # a generator and associated parameters for positive indicators
    diagnose_extra = []
    if force_negate or 5*len(okStrs) > len(badStrs) or not okStrs: # and for negative indicators, if appropriate: (changed in v0.6892: still check for negative indicators if len(okStrs) is similar to len(badStrs) even if not strictly greater, but don't bother if len(okStrs) is MUCH less)
      didFind = []
      diagnostics.append((didFind,"negative",nRet,nCovered))
      toCheck.append((didFind,badStrs,nAppend,nCovered,unique_substrings(badStrs,lambda txt:txt in nOmit,lambda txt:sum(1 for s in badStrs if txt in s))))
      if try_harder and okStrs and not force_negate:
        didFind = []
        diagnostics.append((didFind,"overmatch-negative",n2Ret,n2Covered))
        toCheck.append((didFind,badStrs,nAppend2,n2Covered,unique_substrings(badStrs,lambda txt:txt in avoidSelf,lambda txt:(sum(1 for s in badStrs if txt in s),-sum(1 for s in okStrs if txt in s))))) # a harder try to find negative indicators (added in v0.6896): allow over-matching (equivalent to under-matching positive indicators) if it's the only way to get all badStrs covered (v3.264: only don't try creating an indicator from the word itself which would render the rule a no-op).  May be useful if the word can occur in isolation.
    elif nonAnnot==diagnose: diagnose_extra.append("Not checking for negative indicators as 5*%d>%d=%s." % (len(okStrs),len(badStrs),repr(5*len(okStrs)>len(badStrs))))
    while toCheck and negate==None:
      for i in range(len(toCheck)):
        didFind,strs,append,covered,generator = toCheck[i]
        try: indicator = getNext(generator) # gets a yield from the corresponding unique_substrings call
        except StopIteration:
          del toCheck[i] ; break
        found = True ; cChanged = False
        for j in xrange(len(strs)):
          if not covered[j] and indicator in strs[j]:
            covered[j]=cChanged=True
        if cChanged:
         append(indicator)
         if not didFind: didFind.append(True)
         if all(covered):
          if append==pAppend: negate=False
          elif append==nAppend: negate=True # negate with no overmatch allowed found all the exceptions, so use it (don't use it if it doesn't find ALL the exceptions, since we don't ever want an as-if 'overmatch positive' i.e. misidentifying a word/phrase in a place where the corpus explicitly DOESN'T have it, unless force_negate see comment below)
          else: # append==nAppend2 (negate with overmatch allowed): we managed to get all exceptions with overmatch-negative, but how much damage did our overmatching do to the NON-exceptions?
            fxCover = [True]*len(okStrs)
            for indicator in n2Ret:
              for i in xrange(len(okStrs)):
                if fxCover[i] and indicator in okStrs[i]:
                  # a negative indicator 'misfires' here, resulting in this okStr NOT being identified as 'ok'
                  fxCover[i] = False
            if sum(1 for x in fxCover if x) >= sum(1 for x in pCovered if x): negate="harder"
            else: diagnose_extra.append("Overmatch-negate got worse actual coverage than partial-positive.") # so don't set negate="harder", but we might still force_negate to set negate=True below
          break
    # and if negate==None AFTER this loop, didn't get all(pCovered) OR all(nCovered), in which case we fall back to negate=False (unless force_negate).  In other words, negative indicators normally have to cover ALL non-occurrences to be passed, whereas positive indicators just have to cover SOME.  This is in keeping with the idea of 'under-match is better than over-match' (because an under-matching negative indicator is like an over-matching positive one)
    if force_negate: negate = True
    if negate==True: ret,covered = nRet,nCovered
    elif negate=="harder":
      ret,covered = n2Ret,n2Covered
      if nbytes>ybytes and all(any(indicator in within_Nbytes(s+len(nonAnnot),nbytes) for indicator in ret)==any(indicator in within_Nbytes(s+len(nonAnnot),ybytes) for indicator in ret) for s in badStarts):
        # v3.242: we're using overmatch-negate on larger contexts, the smaller context might have failed to consider this compromise indicator due to there being an intersection between badStrs and okStrs when small, so when contexts are enlarged and we found it's the least-bad indicator to use anyway, check if we could then go back to the smaller context with same results (could reduce overmatch in practice even if not in the corpus, e.g. if somebody inputs 2 similar-looking words next to each other). TODO: check ybytes+ybytes_step*N for all N that yields < nbytes?
        if nonAnnot==diagnose: diagnose_write("Overriding output nbytes from %d to %d by same-result rule" % (nbytes,ybytes))
        nbytes = ybytes
    else: ret,covered = pRet,pCovered
    if nonAnnot==diagnose:
      def report(didFind,negate,ret,covered):
        if not didFind: return ""
        if negate: indicators = negate+" indicators "
        else: indicators = "indicators "
        if ret:
          if len(ret) > 30: indicators=str(len(ret))+" "+indicators # +'/'.join(ret[:30]+['...'])
          else: indicators += '/'.join(ret)
        else: indicators = "no "+indicators
        if all(covered): notCovered = ""
        else:
          if negate: strs = badStrs
          else: strs = okStrs
          notCovered = [strs[i] for i in xrange(len(covered)) if not covered[i]]
          if len(notCovered) > 10: notCovered = notCovered[:10]+["..."]
          notCovered = ", not "+'/'.join(notCovered).replace('\n',"\\n")
        if negate=="overmatch-negative":
          overmatch=[s for s in okStrs if any(i in s for i in n2Ret)]
          if len(overmatch) > 10: overmatch = overmatch[:10]+["..."]
          if overmatch: notCovered += ", overmatch "+"/".join(overmatch).replace('\n',"\\n")
        return "%s (cover=%d/%d%s)" % (indicators,sum(1 for x in covered if x),len(covered),notCovered)
      if len(pOmit) > 200: pOmit = pOmit[:200]+"..."
      diagnose_extra = " ".join(diagnose_extra)
      if diagnose_extra: diagnose_extra=" "+diagnose_extra
      rr = ", ".join(r for r in [report(*i) for i in diagnostics] if r)
      if not rr: rr = "nothing"
      diagnose_write("tryNBytes(%d) on %s (avoiding '%s') found %s%s" % (nbytes,withAnnot_unistr,pOmit.replace(unichr(1),'/').replace('\n',"\\n"),rr,diagnose_extra))
    return negate,ret,sum(1 for x in covered if x),len(covered),nbytes

def badInfo(badStarts,nonAnnot,for_tty=True):
  ret = u"%d false positive" % len(badStarts)
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
   if for_tty: ret += (u" (%s%s%s%s%s)" % (toRead[contextStart:wordStart],reverse_on,toRead[wordStart:wordEnd],reverse_off,toRead[wordEnd:contextEnd])).replace("\n","\\n").replace("\r","\\r")
   else: ret += (u" (%s <<%s>> %s)" % (toRead[contextStart:wordStart],toRead[wordStart:wordEnd],toRead[wordEnd:contextEnd])).replace("\n","\\n").replace("\r","\\r")
  return ret

def unique_substrings(texts,omitFunc,valueFunc):
    # yield unique substrings of texts, in increasing length, with equal lengths sorted by highest score returned by valueFunc, and omitting any where omitFunc is true, or that uses any character not in markedUp_unichars (unless yarowsky_all set)
    if not yarowsky_all:
        # remove non-allowed chars from texts, splitting into smaller strings as necessary
        texts2 = [] ; append=texts2.append
        for text in texts:
            start = 0
            for i in xrange(len(text)):
                if not text[i] in markedUp_unichars:
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
    # yield "backgrounded" = task has been backgrounded; getNext collects job handle, then getNext collects result (nb we default to NOT canBackground, as test_rule is called from several places of which ONE can handle backgrounding)
    if ybytes and (yarowsky_multiword or not re.search(multiWordPattern,withAnnot_unistr)):
        # Doesn't have to be always right, but put the indicators in yBytesRet
        ybrG = yarowsky_indicators(withAnnot_unistr,canBackground)
        ybr = getNext(ybrG)
        if ybr == "backgrounded":
          yield ybr ; yield getNext(ybrG)
          ybr = getNext(ybrG)
        if ybr==True or not ybr:
          yield ybr ; return
        yBytesRet.append(ybr) # (negate, list of indicators, nbytes)
        yield True
    else: # non-ybytes version: accept rule only if it exactly matches the corpus
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
          if not all(covered[wStart:wStart+ruleLen]) and (not multiword_end_avoid or ruleLen==1 or not markDown(words[wStart+ruleLen-1]) in multiword_end_avoid):
            yield words[wStart:wStart+ruleLen], wStart
            # caller join()s before adding to rules dict

if yarowsky_half_thorough: yarowsky_thorough = True # will amend it in caller of checkCoverage
def checkCoverage(ruleAsWordlist,words,coveredFlags,ybr=0):
    # Updates coveredFlags and returns True if any changes
    # (if False, the new rule is redundant)
    assert type(ruleAsWordlist)==type(words)==list
    try: start = words.index(ruleAsWordlist[0])
    except ValueError: return False
    ln = len(ruleAsWordlist)
    changedFlags = False
    while start <= len(words)-ln:
        if words[start:start+ln] == ruleAsWordlist:
            if not all(coveredFlags[start:start+ln]) and (not yarowsky_thorough or not ybr or cc_testR(ybr,markDown(wspJoin(words[:start+ln])),markDown(wspJoin(words[start+ln:])))):
                coveredFlags[start:start+ln]=[True]*ln
                changedFlags = True
            start += ln
        else: start += 1
        try: start = words.index(ruleAsWordlist[0],start)
        except ValueError: break
    return changedFlags

def cc_testR(ybr,before,after):
  # service routine for checkCoverage to also test against
  # yBytesRet (i.e. check the Yarowsky-like indicators can
  # actually enable the rule to apply in this context,
  # before we update coverage flags to say that it does)
  negate,indicators,nbytes = ybr
  context = before[-nbytes:].encode(outcode)[-nbytes:]+after[:nbytes].encode(outcode)[:nbytes]
  r=any(i.encode(outcode) in context for i in indicators)
  if negate: r = not r
  return r

if removeSpace: wspJoin = lambda l: "".join(l)
else: wspJoin = lambda l: " ".join(l)

def potentially_bad_overlap(rulesAsWordlists_By1stWord,newRuleAsWords):
    # Allow overlaps only if rule(s) being overlapped are
    # entirely included within newRule.  Otherwise could
    # get problems generating closures of overlaps.
    # (If newRule not allowed, caller to try a longer one)
    # Additionally, if allow_overlaps, allow ANY overlap as
    # long as it's not found in the marked-down text.
    if len(newRuleAsWords)==1 or ybytes: return False
    for v in rulesAsWordlists_By1stWord.values():
      for ruleAsWordlist in v:
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
    self.rules = {} # wspJoin(ruleAsWordlist) -> (negate-type, indicator-list, nbytes) or just indicator-list (if empty or negate,nbytes is default)
    self.rulesAsWordlists_By1stWord = {} # starting word -> list (order unimportant) of possible rules (as wordlists) that might apply, used internally by addRulesForPhrase for faster checks
    self.rejectedRules = set()
    self.seenPhrases = set() # de-duplicate, might speed up
  def addRulesForPhrase(self,phrase,canBackground=False):
    if phrase in self.seenPhrases or (diagnose_quick and diagnose):
      # if diagnose and diagnose_quick and mdStart+diagnose+mdEnd in phrase: pass # look at it again for diagnostics.  But do we accept a diagnose that spans multiple words?  should be pointed out by --diagnose-quick below if uncommented
      if diagnose and diagnose_quick and diagnose in markDown(phrase): pass # this version accepts diagnose of multiple words (and might also let some phrases through where it matches on an overlap)
      else:
        yield 0,0 ; return # TODO: document that this means the total 'covered' figure in the progress status is AFTER phrase de-duplication (otherwise we'd have to look up what the previous values were last time we saw it - no point doing that just for a quick statistic)
    self.seenPhrases.add(phrase)
    words = list(filter(lambda x:markDown(x).strip(),splitWords(phrase))) # filter out any that don't have base text (these will be input glitches, TODO: verify the annotation text is also just whitespace, warn if not)
    if not words:
      yield 0,0 ; return
    covered = [False]*len(words)
    # first see how much is covered by existing rules
    # (don't have to worry about the order, as we've been
    # careful about overlaps)
    for w in set(words):
      for ruleAsWordlist in self.rulesAsWordlists_By1stWord.get(w,[]):
        k = wspJoin(ruleAsWordlist)
        if yarowsky_half_thorough and self.rules[k]:
          pass # need to make worst-case assumption of context-sensitive rules NEVER matching here, because we need separately to evaluate them depending on each proposed rule from all_possible_rules
        elif checkCoverage(ruleAsWordlist,words,covered,self.rules[k]) and all(covered):
          yield len(covered),len(covered) ; return # no new rules needed
    for ruleAsWordlist, wStart in all_possible_rules(words,covered):
        rule = wspJoin(ruleAsWordlist) ; yBytesRet = []
        if rule in self.rejectedRules: continue
        if rule in self.rules: continue # this can still happen even now all_possible_rules takes 'covered' into account, because the above checkCoverage assumes the rule won't be applied in a self-overlapping fashion, whereas all_possible_rules makes no such assumption (TODO: fix this inconsistency?)
        if yarowsky_half_thorough and len(ruleAsWordlist) > 1:
          c2 = covered[wStart:wStart+len(ruleAsWordlist)]
          def f():
           for w in set(ruleAsWordlist):
            for r2 in self.rulesAsWordlists_By1stWord.get(w,[]):
              # if len(r2) >= len(c2): continue # as an optimisation, but this shouldn't be necessary if we're doing phrases in increasing length
              # if not yarowsky_multiword and len(r2)>1: continue # but self.rules[k] will be False below anyway, so this won't be much of a speedup, just saves one wspJoin
              k = wspJoin(r2)
              if self.rules[k] and checkCoverage(r2,ruleAsWordlist,c2,self.rules[k]) and all(c2): return
          f()
          if all(c2): continue
        rGen = test_rule(rule,yBytesRet,canBackground)
        r = getNext(rGen)
        if r=="backgrounded":
          yield r ; yield getNext(rGen)
          r = getNext(rGen)
        del rGen
        if not r or potentially_bad_overlap(self.rulesAsWordlists_By1stWord,ruleAsWordlist):
            self.rejectedRules.add(rule) # so we don't waste time evaluating it again (TODO: make sure rejectedRules doesn't get too big?)
            continue
        if len(yBytesRet): self.rules[rule] = yBytesRet[0]
        else: self.rules[rule] = [] # unconditional
        if yarowsky_half_thorough: k = []
        else: k = self.rules[rule]
        checkCoverage(ruleAsWordlist,words,covered,k) # changes 'covered'
        if not ruleAsWordlist[0] in self.rulesAsWordlists_By1stWord: self.rulesAsWordlists_By1stWord[ruleAsWordlist[0]] = []
        self.rulesAsWordlists_By1stWord[ruleAsWordlist[0]].append(ruleAsWordlist)
        handle_diagnose_limit(rule)
        if all(covered):
          yield len(covered),len(covered) ; return
    # If get here, failed to completely cover the phrase.
    # ruleAsWordlist should be set to the whole-phrase rule.
    yield sum(1 for x in covered if x),len(covered)

def saveRules(rulesAndConds):
  sys.stderr.write("\nSaving rules to %s... " % rulesFile) ; sys.stderr.flush()
  f = openfile(rulesFile,'w')
  d = [] # rulesAndConds is already a sorted list
  for k,v in rulesAndConds:
    if not v: d.append(k)
    elif type(v)==tuple: d.append((k,(v[0],sorted(v[1]),v[2])))
    else: d.append((k,sorted(v)))
  json.dump(d,codecs.getwriter("utf-8")(f),indent=4,ensure_ascii=False)
  f.close() ; sys.stderr.write("done")
  sys.stderr.flush()
def loadRules():
  sys.stderr.write("Loading rules from %s... " % rulesFile) ; sys.stderr.flush()
  f = openfile(rulesFile)
  rulesAndConds = []
  for item in json.load(codecs.getreader("utf-8")(f)):
    if type(item)==list:
      k,v = item
      if len(v)==3 and type(v[1])==list: v=tuple(v)
      rulesAndConds.append((k,v))
    else: rulesAndConds.append((item,[]))
  sys.stderr.write("done\n")
  return rulesAndConds

def handle_diagnose_limit(rule):
  global diagnose,diagnose_limit
  if diagnose and diagnose_limit and diagnose==markDown(rule):
    diagnose_limit -= 1
    if not diagnose_limit:
      diagnose = False
      diagnose_write("limit reached, suppressing further diagnostics")

def generate_map():
    global m2c_map, precalc_sets, yPriorityDic
    sys.stderr.write("Generating corpus map... ")
    m2c_map = {} ; precalc_sets = {}
    muStart = downLenSoFar = 0
    for s in re.finditer(re.escape(markupStart), corpus_unistr):
      s=s.start()
      md = markDown(corpus_unistr[muStart:s])
      if markupStart in md: errExit("examples have nested markup! "+repr(md))
      downLenSoFar += len(md)
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
    if end_pri and ybytes:
      sys.stderr.write("yPriorityDic ... ")
      for w in splitWords(corpus_unistr[:corpus_unistr.index(end_pri)]): # (throws error if --end-pri is not in the corpus)
          wd = markDown(w)
          if wd in yPriorityDic: continue
          if diagnose==wd: diagnose_write("yPriorityDic[%s] = %s" % (wd,w))
          yPriorityDic[wd] = w
    sys.stderr.write("done\n")

executor = None
def setup_parallelism(): # returns number of cores
    global executor
    if single_core: return 1
    elif not hasattr(os,'fork'): return 1 # e.g. Windows, would need to write to filesystem like versions of annogen before 3.183 and distinguish main/non-main like versions of annogen before 3.38 (may get muddled up if running from __main__.py under python -m)
    elif executor: executor.shutdown(True) # MUST wait for the shutdown to finish before creating a new instance: some implementations seem to have a race condition
    try:
      import multiprocessing
      params = [multiprocessing.cpu_count()-1]
      if params[0] <= 0: return 1
      if hasattr(multiprocessing,"get_context"): params.append(multiprocessing.get_context('fork')) # Python 3.4+: if this raises ValueError, we can't fork so won't multiprocess
      import concurrent.futures # Python 3.  On Python 2, you can try the backport via 'pip install futures' but deadlock is possible.  And seems to occur when annogen __name__ is not "__main__" after first normBatch returns, not sure why:
      if not (type("")==type(u"") or __name__=="__main__"): raise Exception("Python 2 as submodule is known to deadlock unless multicore disabled")
      executor = concurrent.futures.ProcessPoolExecutor(*params)
      # Do not reduce Python 2's sys.setcheckinterval() (or Python 3's setswitchinterval) if using ProcessPoolExecutor, or job starts can be delayed.
      cores = multiprocessing.cpu_count()
      if cores_command: os.system("%s %d" % (cores_command,cores))
      return cores
    except: return 1 # can't fork for some reason

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
    global corpus_markedDown, bigramCache
    corpus_markedDown = markDown(corpus_unistr)
    if not ybytes: return
    bigramCache=dict((i,[]) for i in set(corpus_markedDown[i:i+2] for i in xrange(len(corpus_markedDown)-1)))
    for i in xrange(len(corpus_markedDown)-1):
      k=corpus_markedDown[i:i+2]
      if k in bigramCache:
        bigramCache[k].append(i)
        if len(bigramCache[k]) > 100: del bigramCache[k]
    if freq_count or not yarowsky_all:
      global markedUp_unichars
      markedUp_unichars = set(list(u"".join(markDown(p) for p in get_phrases() if not type(p)==int)))

def analyse():
    accum = RulesAccumulator()
    covered = 0 # number of phrases we managed to 'cover' with our rules
    toCover = 0 # number of phrases we TRIED to cover (==covered if 100%)
    phraseNo = 0 ; wordLen = None
    phraseLastUpdate = phraseNo
    lastUpdate = startTime = time.time()
    backgrounded = [] ; phrases = get_phrases()
    while phraseNo < len(phrases):
        if type(phrases[phraseNo])==int:
          oldWL,wordLen = wordLen,phrases[phraseNo]
          if wordLen > 1 and oldWL == 1:
            # we currently use background jobs only for wordLen=1; other workers won't be needed after these jobs finish
            try: executor.shutdown(False)
            except: pass
          covered,toCover = flush_background(backgrounded," for #w change",covered,toCover)
          if wordLen > 1 and oldWL == 1 and cores_command: os.system(cores_command+" 1")
          phraseNo += 1 ; continue
        if time.time() >= lastUpdate + 2:
          if toCover: cov=int(100.0*covered/toCover)
          else: cov = 0
          status_update(phraseNo,len(phrases),wordLen,len(accum.rules),phraseLastUpdate,lastUpdate,startTime,cov,len(accum.rejectedRules))
          lastUpdate = time.time() ; phraseLastUpdate = phraseNo
        aRules = accum.addRulesForPhrase(phrases[phraseNo],wordLen==1) # We're saying canBackground only if wordLen==1 because longer phrases can be backgrounded only if they're guaranteed not to have mutual effects.  Could look into when we can do that (or a separate pass through adding all len-1 rules 1st) and remove the executor.shutdown above, but test corpus is showing NO large collocation checks needed at #w=2+ anyway, so this work would not actually save generation time.
        arr = getNext(aRules)
        if arr=="backgrounded": backgrounded.append(aRules)
        else:
          coveredA,toCoverA = arr
          covered += coveredA ; toCover += toCoverA
        phraseNo += 1
    flush_background(backgrounded)
    if wordLen==1:
      if cores_command: os.system(cores_command+" 1")
      try: executor.shutdown(False) # if wordLen never exceeded 1 so it didn't get shut down above, might as well free up other processes now
      except: pass
    if diagnose_manual: test_manual_rules()
    rules = sorted(accum.rules.items()) # sorting it makes the order stable across Python implementations and insertion histories: useful for diff when using concurrency etc (can affect order of otherwise-equal Yarowsky-like comparisons in the generated code)
    if write_rules: saveRules(rules), sys.exit(0)
    else: return rules
try: import Queue as queue # Python 2
except: import queue # Python 3
def flush_background(backgrounded,why="",covered=0,toCover=0):
  q = queue.Queue()
  origLen = len(backgrounded)
  if origLen: sys.stderr.write("Collecting backgrounded results%s: 0/%d%s" % (why,origLen,clear_eol))
  while backgrounded:
    b = backgrounded.pop()
    getNext(b).add_done_callback(lambda _,b=b:q.put(b))
  for count in xrange(origLen):
    coveredA,toCoverA = getNext(q.get())
    covered += coveredA ; toCover += toCoverA
    sys.stderr.write("\rCollecting backgrounded results%s: %d/%d" % (why,count+1,origLen))
  if origLen: sys.stderr.write("\n")
  return covered,toCover

def read_manual_rules():
  if not manualrules: return
  for l in openfile(manualrules):
    if not l.strip(): continue
    l=l.decode(incode).strip() # TODO: manualrulescode ?
    if removeSpace: l=re.sub(re.escape(markupEnd)+r'\s+'+re.escape(markupStart),(markupEnd+markupStart).replace('\\',r'\\'),l,flags=re.UNICODE)
    yield l

def test_manual_rules():
    for l in read_manual_rules():
      words = list(splitWords(l))
      # Prevent KeyError in getOkStarts:
      for w in words:
        if w not in precalc_sets: precalc_sets[w]=set()
      # Call test_rule:
      yb = []
      if not getNext(test_rule(l,yb)) or len(yb):
        getBuf(sys.stderr).write(("\nWARNING: Manual rule '%s' may contradict the examples. " % l).encode(terminal_charset))
        if len(words)==1:
          global diagnose,diagnose_limit,ybytes
          od,odl,oy,diagnose,diagnose_limit,ybytes = diagnose,diagnose_limit,ybytes,markDown(l),0,ybytes_max
          getNext(test_rule(l,[]))
          diagnose,diagnose_limit,ybytes = od,odl,oy

def zapTrigraphs(x): return re.sub(br"\?\?([=/'()<>!-])",br'?""?\1',x) # to get rid of trigraph warnings, TODO might get a marginal efficiency increase if do it to the entire C file at once instead)

def c_escapeRawBytes(s): # as it won't be valid outcode; don't want to crash any editors/viewers of the C file
  if s.endswith(b'\x00'): s=s[:-1] # as the C compiler will add a terminating 0 anyway
  return re.sub(br"(?<!\\)((?:\\\\)*\\x..)([0-9a-fA-F])",br'\1""\2',zapTrigraphs(s.replace(b'\\',b'\\\\').decode('unicode_escape').encode('unicode_escape').replace(b'"',b'\\"')))

def txt_escapeRawBytes(s): # for browser_extension
  if js_utf8: return s.encode('utf-8')
  else: return s.decode('latin1').encode('utf-8')

def dart_escapeRawBytes(s):
  if js_utf8: return re.sub(b"[\x00-\x1f\"\\\\$\x7f]",lambda m:br"\u{%x}"%ord(m.group()),s.encode('utf-8'))
  else: return re.sub(b"[\x00-\x1f\"\\\\$\x7f-\xff]",lambda m:br"\u{%x}"%ord(m.group()),s)

def c_length(unistr): return len(unistr.encode(outcode))

if java:
  outLang_bool = b"boolean"
  outLang_true = b"true"
  outLang_false = b"false"
else:
  outLang_bool = b"int"
  outLang_true = b"1"
  outLang_false = b"0"

stderr_newline = True
def allVars(u):
  global cjkVars
  try: cjkVars
  except NameError:
    global stderr_newline
    if stderr_newline: sys.stderr.write("Checking CJK closures for missing glosses\n")
    else: sys.stderr.write("checking CJK closures for missing glosses... "),sys.stderr.flush()
    stderr_newline = True
    cjkVars = {}
    abbr = {"kSemanticVariant":"M","kSimplifiedVariant":"f","kTraditionalVariant":"f","kZVariant":"v"} # TODO: if any F900..FAD9, consider reading kCompatibilityVariant from Unihan_IRGSources.txt (need to open a different file)
    for l in open(gloss_closure):
      if l.strip() and not l.startswith("#"):
        l=l.split()
        cjkVars.setdefault((int(l[0][2:],16),abbr.get(l[1],"O")),set()).update(int(i.split('<')[0][2:],16) for i in l[2:])
  done = set([u])
  for t in "fMv":
    for var in cjkVars.get((u,t),[]):
      if not var in done: yield var
      done.add(var)
      # In at least some versions of the data, U+63B3 needs to go via T (U+64C4) and M (U+865C) and S to get to U+864F (instead of having a direct M variant to 864F), so we need to take f/M/f variants also:
      if t=="f": # fanti / jianti
        for var in cjkVars.get((var,'M'),[]):
          if var in done: continue
          yield var ; done.add(var)
          for var in cjkVars.get((var,"f"),[]):
            if var in done: continue
            yield var ; done.add(var)

def allVarsW(unistr):
  vRest = []
  for i in xrange(len(unistr)):
    got_vRest = False
    for v in allVars(ord(unistr[i])):
      try: v=unichr(v)
      except: continue # narrow Python build non-BMP: ignore (TODO)
      yield unistr[:i]+v+unistr[i+1:]
      if got_vRest:
        for vr in vRest: yield unistr[:i]+v+vr
      else:
        vRest = [] ; got_vRest = True
        for vr in allVarsW(unistr[i+1:]):
          yield unistr[:i]+v+vr ; vRest.append(vr)

def matchingAction(rule,glossDic,glossMiss,glosslist,omitlist):
  # called by addRule in outputParser, returns (actionList, did-we-actually-annotate).  Also applies reannotator and compression (both of which will require 2 passes if present)
  action = []
  gotAnnot = False
  for w in splitWords(rule):
    wStart = w.index(markupStart)+len(markupStart)
    wEnd = w.index(markupMid,wStart)
    text_unistr = w[wStart:wEnd]
    mStart = wEnd+len(markupMid)
    annotation_unistr = w[mStart:w.index(markupEnd,mStart)]
    if mreverse: text_unistr,annotation_unistr = annotation_unistr,text_unistr
    if glosslist and not text_unistr in glosslist:
      return text_unistr+" not glosslisted",None
    elif text_unistr in omitlist:
      return text_unistr+" omitlisted",None
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
      if toAdd in reannotateDict:
        au = reannotateDict[toAdd]
        if au and reannotate_caps and annotation_unistr and any(a and not a[0]==a[0].lower() for a in re.split('[ -]',annotation_unistr)):
          if sharp_multi: au='#'.join(fixCaps(w,annotation_unistr) for w in au.split('#'))
          else: au=fixCaps(au,annotation_unistr)
        annotation_unistr = au
      else: toReannotateSet.add(toAdd)
    if compress:
      annotation_bytes = squash(annotation_unistr.encode(outcode))
      if gloss: gloss_bytes = squash(gloss.encode(outcode))
      else: gloss_bytes = None
    else: # no compression:
      annotation_bytes = annotation_unistr.encode(outcode)
      if gloss: gloss_bytes = gloss.encode(outcode)
      else: gloss_bytes = None
    bytesToCopy = c_length(text_unistr)
    if gloss: action.append((bytesToCopy,annotation_bytes,gloss_bytes))
    else:
        glossMiss.add(w)
        action.append((bytesToCopy,annotation_bytes))
    if annotation_unistr or gloss: gotAnnot = True
  return action,gotAnnot

def fixCaps(s,ref,splitOn=(' ','-')):
  if not s: return s # (e.g. annotation omitted for a word in reannotate)
  for tryS in splitOn:
    if tryS in ref and tryS in s:
      s2,ref2 = s.split(tryS),ref.split(tryS)
      if len(s2)==len(ref2): return tryS.join(fixCaps(s,r,splitOn[splitOn.index(tryS)+1:]) for s,r in zip(s2,ref2))
  if ref[0]==ref[0].lower(): return s
  return s[0].upper()+s[1:]

def readGlossfile():
    glossDic = {} ; glosslist = set()
    if glossfile:
        for l in openfile(glossfile):
            if not l.strip(): continue
            l=l.decode(incode,errors='replace') # TODO: glosscode ? (errors=replace because we said it's not necessary to completely debug glossfile; we don't want this to be brought down by one bad UTF8 sequence or whatever)
            try: word,annot,gloss = l.split("\t",2)
            except: # not enough tabs
              word = l.split("\t",1)[0] ; annot = gloss = ""
              if glossmiss_omit: pass # they can list words without glosses; no error if missing \t
              else: getBuf(sys.stderr).write(("Gloss: Ignoring incorrectly-formatted line "+l.strip()+"\n").encode(terminal_charset))
            word,annot,gloss = word.strip(),annot.strip(),gloss.strip().replace("\t","\n")
            if glossmiss_omit and word: glosslist.add(word)
            if not word or not gloss: continue
            if annot: glossDic[(word,annot)] = gloss
            else: glossDic[word] = gloss
    return glossDic,glosslist

def copyBytes(n,checkNeedspace=False): # needSpace unchanged for ignoreNewlines etc; checkNeedspace for open quotes
    if checkNeedspace:
      return [b's0',(n,)] # copyBytes(n)
    else: return [(n,)] # copyBytes(n)

def outputParser(rulesAndConds):
    glossDic, glosslist = readGlossfile()
    glossMiss = set() # helps gloss_closure avoid repeated lookups
    if words_omit:
      omitlist=set(w.strip() for w in openfile(words_omit).read().decode(incode).split('\n')) # TODO: glosscode?
      if diagnose and diagnose in omitlist: diagnose_write(diagnose+" is in words_omit file")
    else: omitlist = []
    sys.stderr.write("Generating byte cases...\n")
    byteSeq_to_action_dict = {}
    if ignoreNewlines: # \n shouldn't affect needSpace
      byteSeq_to_action_dict[b'\n'] = [(copyBytes(1),[])]
    for closeQuote in u'\u2019\u201d\u300b\u300d)\u3015\uff09\u3017\u3011]\uff3d':
      # close quotes should not affect needSpace
      try: closeQuote = closeQuote.encode(outcode)
      except: continue # can't do this one
      byteSeq_to_action_dict[closeQuote] = [(copyBytes(len(closeQuote)),[])]
    for openQuote in u'\u2018\u201c\u300a\u300c(\u3014\uff08\u3016\u3010[\uff3b':
      # open quotes should activate needSpace first
      try: openQuote = openQuote.encode(outcode)
      except: continue # can't do this one
      byteSeq_to_action_dict[openQuote] = [(copyBytes(len(openQuote),checkNeedspace=True),[])]
    def addRule(rule,conds,byteSeq_to_action_dict,manualOverride=False):
      md = md2 = markDown(rule)
      if post_normalise and (javascript or java):
        md2 = post_normalise_translate(md)
        byteSeq = md2.encode(outcode)
        if type(conds)==tuple: conds=(conds[0],list(map(post_normalise_translate,conds[1])),conds[2])
        else: conds=list(map(post_normalise_translate,conds))
      else: byteSeq = md.encode(outcode)
      action,gotAnnot = matchingAction(rule,glossDic,glossMiss,glosslist,omitlist)
      if not gotAnnot: return # not glosslisted, or some spurious o("{","") rule that got in due to markup corruption
      if manualOverride or not byteSeq in byteSeq_to_action_dict:
        byteSeq_to_action_dict[byteSeq] = []
      elif post_normalise:
        if (action,conds) in byteSeq_to_action_dict[byteSeq]: return # exact duplicate after post-normalisation
        elif any((x[0]==action or x[1]==conds) for x in byteSeq_to_action_dict[byteSeq]): # near-duplicate: same conds, different action (will definitely need to prioritise one, can't do both), or same action, different conds (will probably need to prioritise one, especially if one of the conds of the non-normalised action is IN the normalised action, which could short-circuit the conds)
          if md==md2: # this is the rule that DIDN'T have to be post-normalised, so its action should take priority
            byteSeq_to_action_dict[byteSeq] = [x for x in byteSeq_to_action_dict[byteSeq] if not x[1]==conds]
          else: return # other one probably has priority
      byteSeq_to_action_dict[byteSeq].append((action,conds))
    def dryRun(clearReannotator=True): # to prime the reannotator or compressor
      global toReannotateSet, reannotateDict
      toReannotateSet = set()
      if clearReannotator: reannotateDict = {} # so set gets completely repopulated (don't do this if we've run the reannotator and this dryRun is for the compressor)
      # To call squash() and populate toReannotateSet,
      # we don't need the whole of addRule, just matchingAction
      for rule,conds in rulesAndConds:
        matchingAction(rule,glossDic,glossMiss,glosslist,omitlist)
      for l in read_manual_rules():
        matchingAction(l,glossDic,glossMiss,glosslist,omitlist)
    if reannotator:
      global stderr_newline ; stderr_newline = False
      sys.stderr.write("Preparing reannotate... ")
      sys.stderr.flush()
      dryRun()
      # Setting buffer size is not enough on all systems.
      # To ensure the pipe does not fill its output while
      # we are still writing its input, we use threads and
      # don't start writing its input until we've already
      # started reading from its output.
      global toReannotateSet, reannotateDict
      l = [ll for ll in toReannotateSet if ll and not "\n" in ll] # TODO: handle the case where "\n" is in ll?  (shouldn't happen in 'sensible' annotators)
      def reader_thread(comms):
        comms[0] = True
        c = cout.read()
        try: comms[1] = c.decode(outcode).splitlines() # TODO: reannotatorCode instead of outcode?
        except:
          sys.stderr.write("Writing invalid reannotator output to reannot-ERR.txt\n")
          open("reannot-ERR.txt","wb").write(c)
          comms[1] = None
      if reannotator.startswith('##'): cmd=reannotator[2:]
      elif reannotator[0]=='#': cmd=reannotator[1:]
      else: cmd = reannotator
      sys.stderr.write("reannotating... ")
      sys.stderr.flush()
      sp=subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,close_fds=True)
      global cout ; cin,cout = sp.stdin,sp.stdout
      comms = [False,False]
      thread.start_new_thread(reader_thread,(comms,))
      while comms[0] == False: time.sleep(0.1)
      # NOW ready to start writing:
      cin.write("\n".join(l).encode(outcode)+b"\n") ; cin.close() # TODO: reannotatorCode instead of outcode?
      while comms[1] == False: time.sleep(1)
      l2 = comms[1]
      if l2==None: raise ("Exception in reader thread, probably UnicodeDecodeError in reannotator output")
      del cin,cout,cmd,comms,sp
      while len(l2)>len(l) and not l2[-1]: del l2[-1] # don't mind extra blank line(s) at end of output
      if not len(l)==len(l2):
        open('reannotator-debug-in.txt','wb').write(os.linesep.join(l).encode(outcode)+B(os.linesep))
        open('reannotator-debug-out.txt','wb').write(os.linesep.join(l2).encode(outcode)+B(os.linesep))
        errExit("Reannotator command didn't output the same number of lines as we gave it (gave %d, got %d).  Input and output have been written to reannotator-debug-in.txt and reannotator-debug-out.txt for inspection.  Bailing out." % (len(l),len(l2)))
      if stderr_newline: sys.stderr.write("reannotated %d items\n" % len(l))
      else: sys.stderr.write("(%d items)\n" % len(l))
      toReannotateSet = set() ; reannotateDict = dict(zip(l,l2)) ; del l,l2
    if compress:
      global squashStrings ; squashStrings = set() # discard any that were made in any reannotator dry-run
      dryRun(False) # redo with the new annotation strings (or do for the first time if no reannotator)
      pairs = squashFinish()
    else: pairs = b""
    for rule,conds in rulesAndConds: addRule(rule,conds,byteSeq_to_action_dict)
    for l in read_manual_rules():
      if diagnose_manual and l in rulesAndConds: getBuf(sys.stderr).write(("\nINFO: Possible unnecessary manual rule '%s'\n" % l).encode(terminal_charset))
      addRule(l,[],byteSeq_to_action_dict,True)
    longest_rule_len = max(len(b) for b in iterkeys(byteSeq_to_action_dict))
    longest_rule_len += ybytes_max # because buffer len is 2*longest_rule_len, we shift half of it when (readPtr-bufStart +ybytes >= bufLen) and we don't want this shift to happen when writePtr-bufStart = Half_Bufsize-1 and readPtr = writePtr + Half_Bufsize-1 (TODO: could we get away with max(0,ybytes_max-1) instead? but check how this interacts with the line below; things should be safe as they are now).  This line's correction was missing in Annogen v0.599 and below, which could therefore occasionally emit code that, when running from stdin, occasionally replaced one of the document's bytes with an undefined byte (usually 0) while emitting correct annotation for the original byte.  (This could result in bad UTF-8 that crashed the bookmarklet feature of Web Adjuster v0.21 and below.)
    longest_rule_len = max(ybytes_max*2, longest_rule_len) # make sure the half-bufsize is at least ybytes_max*2, so that a read-ahead when pos is ybytes_max from the end, resulting in a shift back to the 1st half of the buffer, will still leave ybytes_max from the beginning, so yar() can look ybytes_max-wide in both directions
    b = BytecodeAssembler()
    b.addActionDictSwitch(byteSeq_to_action_dict,False)
    ddrivn = b.link()
    if zlib: origLen = b.origLen
    del b
    if javascript:
      if browser_extension: return outfile.write(txt_escapeRawBytes(ddrivn))
      else: return outfile.write(js_start+b"data: \""+js_escapeRawBytes(ddrivn)+b"\",\n"+js_end+b"\n") # not Uint8Array (even if browser compatibility is known): besides taking more source space, it's typically ~25% slower to load than string, even from RAM
    elif dart:
      if dart_datafile:
        if os.sep in c_filename: d=c_filename[:c_filename.rindex(os.sep)]+os.sep
        else: d = ""
        if os.sep in dart_datafile: d += dart_datafile[dart_datafile.rindex(os.sep)+1:]
        else: d += dart_datafile
        open(d,'wb').write(ddrivn)
        sys.stderr.write("Wrote "+d+" (ensure this ships as "+dart_datafile+")\n")
      if dart_datafile and zlib: return outfile.write(dart_src.replace(b"%%DATA_INIT%%",b"await(File('"+B(dart_datafile)+b"').readAsBytes())"))
      elif zlib: return outfile.write(dart_src.replace(b"%%DATA_INIT%%",b"\""+dart_escapeRawBytes(ddrivn)+b"\".codeUnits"))
      elif dart_datafile: return outfile.write(dart_src.replace(b"%%DATA_INIT%%",b"String.fromCharCodes(await(File('"+B(dart_datafile)+b"').readAsBytes()))"))
      else: return outfile.write(dart_src.replace(b"%%DATA_INIT%%",b"\""+B(dart_escapeRawBytes(ddrivn))+b"\""))
    elif python:
      dd2 = repr(ddrivn)
      if not dd2.startswith('b'): dd2='b'+dd2 # (if we're generating in Python 2, we still want 2+3 compatibility)
      outfile.write(py_start+b"\ndata="+B(dd2)+b"\n")
      if zlib: outfile.write(b"import zlib; data=zlib.decompress(data)\n")
      return outfile.write(py_end+b"\n")
    elif java:
      start = java_src.replace(b"%%JPACKAGE%%",B(jPackage))
      start = start.replace(b"%%DLEN%%",B(str(len(ddrivn))))
      if zlib: start = start.replace(b"%%ULEN%%",B(str(origLen)))
    else: start = c_start
    outfile.write(start.replace(b'%%LONGEST_RULE_LEN%%',B(str(longest_rule_len))).replace(b"%%YBYTES%%",B(str(ybytes_max))).replace(b"%%PAIRS%%",pairs)+b"\n")
    if zlib: dataName = "origData"
    else: dataName = "data"
    if java: open(jSrc+("/../assets/annotate.dat" if android else "/annotate.dat"),"wb").write(ddrivn)
    else:
      outfile.write(b"static unsigned char "+B(dataName)+b"[]=\""+c_escapeRawBytes(ddrivn)+b'\";\n')
      if zlib: outfile.write(c_zlib.replace(b'%%ORIGLEN%%',B(str(origLen))).replace(b'%%ZLIBLEN%%',B(str(len(ddrivn))))+b"\n") # rather than using sizeof() because we might or might not want to include the compiler's terminating nul byte
      outfile.write(c_datadrive+b"\n")
    del ddrivn
    if android:
      open(java+os.sep+"MainActivity.java","wb").write(android_src.replace(b"%%JPACKAGE%%",B(jPackage)).replace(b'%%ANDROID-URL%%',B(android)))
      open(java+os.sep+"BringToFront.java","wb").write(android_bringToFront.replace(b"%%JPACKAGE%%",B(jPackage)))
      open(jSrc+"/../assets/clipboard.html",'wb').write(android_clipboard)
      if android_template:
        aStamp = android_version_stamp
        try: versionName = re.findall(B(re.escape("versionName")+r'\s*=\s*"([^"]*)"'),open(jSrc+"/../AndroidManifest.xml",'rb').read())[0]
        except: versionName = None
        if versionName: aStamp = aStamp.replace(b"%%DATE%% version",b"%%DATE%% version "+versionName)
        open(jSrc+"/../assets/index.html",'wb').write(android_template.replace(b"VERSION_GOES_HERE",aStamp.replace(b"%%DATE%%",b"%d-%02d-%02d" % time.localtime()[:3]).replace(b"%%TIME%%",b"%d:%02d" % time.localtime()[3:5])))
      update_android_manifest()
      open(jSrc+"/../res/layout/activity_main.xml","wb").write(android_layout)
      open(jSrc+"/../res/menu/main.xml","wb").write(b'<menu xmlns:android="http://schemas.android.com/apk/res/android" ></menu>\n') # TODO: is this file even needed at all?
      open(jSrc+"/../res/values/dimens.xml","wb").write(b'<resources><dimen name="activity_horizontal_margin">16dp</dimen><dimen name="activity_vertical_margin">16dp</dimen></resources>\n')
      open(jSrc+"/../res/values/styles.xml","wb").write(b'<resources><style name="AppBaseTheme" parent="android:Theme.Light"></style><style name="AppTheme" parent="AppBaseTheme"><item name="android:forceDarkAllowed">true</item></style></resources>\n') # won't compile on SDKs that don't know about API 29, e.g. Ubuntu 22.04's packages: could try using introspection to call setForceDarkAllowed() (but need to solve the 'missing d8' problem first if want to upload the resulting APK)
      open(jSrc+"/../res/values/strings.xml","wb").write(B('<?xml version="1.0" encoding="utf-8"?>\n<resources><string name="app_name">'+app_name.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')+'</string></resources>\n'))
      open(jSrc+"/../res/xml/network_security_config.xml","wb").write(b'<?xml version="1.0" encoding="utf-8"?>\n<network-security-config><base-config cleartextTrafficPermitted="true" /></network-security-config>\n')
    elif not java: outfile.write(c_end)
    outfile.write(b"\n")
    del byteSeq_to_action_dict

def update_android_manifest():
  try: manifest = old_manifest = open(jSrc+"/../AndroidManifest.xml",'rb').read()
  except IOError: manifest,old_manifest = android_manifest,None
  def readAttr(aName):
    allVals = re.findall(B(re.escape(aName)+r'\s*=\s*"([^"]*)"'),manifest)
    assert len(allVals)==1, "AndroidManifest.xml has %d instances of %s, should be 1" % (len(allVals),aName)
    return allVals[0]
  versionCode,versionName = readAttr("android:versionCode"),readAttr("android:versionName")
  if b"android:sharedUserId" in manifest: sharedUID = readAttr("android:sharedUserId")
  else: sharedUID = b""
  if android_upload:
    sys.stderr.write("AndroidManifest.xml: bumping versionCode for upload\n (assuming you've taken care of versionName separately, if needed)\n") # (might not be needed if the previous upload wasn't actually released for example)
    versionCode = B(str(int(versionCode)+1))
  manifest = android_manifest.replace(b'%%JPACKAGE%%',B(jPackage)).replace(b'android:versionCode="1"',b'android:versionCode="'+versionCode+b'"').replace(b'android:versionName="1.0"',b'android:versionName="'+versionName+b'"').replace(b'android:sharedUserId=""',b'android:sharedUserId="'+sharedUID+b'"').replace(b'android:sharedUserId="" ',b'')
  if not manifest==old_manifest:
    open(jSrc+"/../AndroidManifest.xml","wb").write(manifest)
  else: assert not android_upload, "Couldn't bump version code in "+repr(manifest)

def setup_browser_extension():
  dirToUse = browser_extension.replace(' ','')
  sys.stderr.write("Writing to "+dirToUse+"\n")
  try: os.mkdir(dirToUse)
  except: pass
  def icons(key,sizes):
    if any(os.path.isfile(dirToUse+os.sep+s+".png") for s in sizes):
      return b',"'+B(key)+b'":{'+b",".join(B('"%s":"%s.png"' % (s,s)) for s in sizes if os.path.isfile(dirToUse+os.sep+s+".png"))+b"}"
    else: return b""
  try: # increment existing version if present
    versionName = re.search(b'"version": *"([^"]*)"',open(dirToUse+"/manifest.json","rb").read()).group(1)
    versionName = versionName.split(b'.')
    versionName[-1] = B(str(int(versionName[-1])+1))
    versionName = b'.'.join(versionName)
  except: versionName = b"0.1"
  open(dirToUse+"/manifest.json","wb").write((br"""{
  "manifest_version": """+(b"3" if manifest_v3 else b"2")+br""",
  "name": "%s",%s
  "version": "%s",
  "browser_specific_settings": { "id" :"%s", "gecko_android": {}},
  "background": { """+(b'"service_worker": "background.js"' if manifest_v3 else b'"scripts": ["background.js"]')+br""" },
  "content_scripts": [{"matches": ["<all_urls>"], "js": ["content.js"], "css": ["ruby.css"]}],
  """+(b'"action"' if manifest_v3 else b'"browser_action"')+br""":{"default_title":"Annotate","default_popup":"config.html","browser_style": true%s},
  """+(b'"host_permissions": ["<all_urls>"], "permissions": ["clipboardRead","storage","scripting"]' if manifest_v3 else b'"permissions": ["<all_urls>","clipboardRead"]')+b"%s}") % (B(browser_extension),B((('" description": "%s",'%browser_extension_description) if browser_extension_description else "")),versionName,B(gecko_id),icons("default_icon",["16","32"]),icons("icons",["16","32","48","96"])))
  open(dirToUse+"/background.js","wb").write(js_start+js_end)
  open(dirToUse+"/content.js","wb").write(jsAnnot(False,True))
  open(dirToUse+"/config.html","wb").write(extension_config)
  open(dirToUse+"/config.js","wb").write(extension_confjs)
  open(dirToUse+"/ruby.css","wb").write(extension_rubycss)
  global c_filename
  c_filename = dirToUse+"/annotate-dat.txt"

if isatty(sys.stdout) and not java and not priority_list and not browser_extension and not write_rules: sys.stderr.write("Will write to "+c_filename+"\n") # will open it later (avoid having a 0-length file sitting around during the analyse() run so you don't rm it by mistake)

def openfile(fname,mode='r'):
    lzma = bz2 = None
    mode += 'b' # Python 2+3 compatibility: always binary
    if fname.endswith(".xz"): import lzma # 'pip install lzma' or 'apt-get install python2.7-lzma' may be required for .xz files
    elif fname.endswith(".bz2"): import bz2
    if re.match("https?://",fname) or fname.startswith("ftp://"):
        assert mode=='rb', "cannot write to "+fname
        try: from urllib2 import urlopen # Python 2
        except: from urllib.request import urlopen # Py3
        sys.stderr.write("Fetching "+fname+"\n")
        fileobj = urlopen(fname)
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
def rm_f(fname):
  try: os.remove(fname)
  except OSError: pass

import atexit
def set_title(t):
  if t:
    try:
      from setproctitle import setproctitle ; setproctitle(t)
    except: pass # TODO: could also try others from adjuster
  if not isatty(sys.stderr): return
  if t: atexit.register(set_title,"")
  is_screen = (term=="screen" and os.environ.get("STY",""))
  is_tmux = (term=="screen" and os.environ.get("TMUX",""))
  if is_xterm or is_tmux: sys.stderr.write("\033]0;%s\007" % (t,)) # ("0;" sets both title and minimised title, "1;" sets minimised title, "2;" sets title.  Tmux takes its pane title from title (but doesn't display it in the titlebar))
  elif is_screen: os.system("screen -X title \"%s\"" % (t,))
def diagnose_write(s,label="Diagnose"):
  getBuf(sys.stderr).write(B(bold_on+label+": "+bold_off)+s.encode(terminal_charset,'replace')+B(clear_eol+'\n'))
try: screenWidth = int(os.environ['COLUMNS'])
except:
  import struct, fcntl, termios
  try: screenWidth = struct.unpack('hh',fcntl.ioctl(sys.stderr,termios.TIOCGWINSZ,'xxxx'))[1]
  except: screenWidth = 45 # conservative

if not compile_only:
 set_title("annogen")
 if read_rules: rulesAndConds = loadRules()
 else:
  read_and_normalise()
  if priority_list:
    if os.path.exists(priority_list):
      sys.stderr.write("Reading "+priority_list+"\n")
      def getPri(line):
        word,pri = line.decode(outcode).rstrip().rsplit(None,1)
        try: return word,int(pri)
        except: return word,float(pri)
      existingPris=dict(getPri(l) for l in openfile(priority_list) if len(l.strip().split())>=2)
    else: existingPris = {}
    sys.stderr.write("Parsing...") ; sys.stderr.flush()
    i=[[markDown(w) for w in splitWords(phrase)] for phrase in splitWords(corpus_unistr,phrases=True)]
    del corpus_unistr
    sys.stderr.write(" calling PairPriorities...\n")
    out="".join(w+"\t"+str(f)+os.linesep for w,f in PairPriorities(i,existingPris) if f).encode(outcode)
    # (don't open the output before here, in case exception)
    if existingPris: sys.stderr.write("Updating "+priority_list+"...")
    else: sys.stderr.write("Writing "+priority_list+"...")
    sys.stderr.flush()
    openfile(priority_list,'w').write(out)
    sys.stderr.write(" done\n")
    sys.exit()
  generate_map() ; setup_other_globals()
  if freq_count:
    sys.stderr.write("Writing "+freq_count+"...") ; sys.stderr.flush()
    counts = {}
    for c in post_normalise_translate(corpus_unistr):
      if c in markedUp_unichars and c.strip():
        if not c in counts: counts[c] = 0
        counts[c] += 1
    cSets = {}
    for k,v in iteritems(post_normalise):
      if not unichr(v) in cSets: cSets[unichr(v)]=unichr(v)
      cSets[unichr(v)] += unichr(k)
    openfile(freq_count,'w').write((u"\n".join(cSets.get(c,c) for _,c in list(reversed(sorted((n,c) for c,n in iteritems(counts))))[:1000])+u"\n").encode('utf-8')) # TODO: customise the 1000 (maybe greater increment after 1000)
    sys.stderr.write(" done\n")
  setup_parallelism() # re-copy globals to cores
  try: rulesAndConds = analyse()
  finally: sys.stderr.write("\n") # so status line is not overwritten by 1st part of traceback on interrupt etc
  del _gp_cache

def cmd_or_exit(cmd):
  sys.stderr.write(cmd+"\n")
  r = os.system(cmd)
  if not r: return
  if r&0xFF == 0: r >>= 8 # POSIX
  sys.exit(r)

if not compile_only:
 if browser_extension: setup_browser_extension()
 if c_filename: outfile = openfile(c_filename,'w')
 else: outfile = getBuf(sys.stdout)
 outputParser(rulesAndConds) ; del rulesAndConds
 outfile.close() ; sys.stderr.write("Output complete\n")
if android:
   can_compile_android = all(x in os.environ for x in ["SDK","PLATFORM","BUILD_TOOLS"])
   can_track_android = (can_compile_android and android_upload) or ("GOOGLE_PLAY_TRACK" in os.environ and "SERVICE_ACCOUNT_KEY" in os.environ and not os.environ.get("ANDROID_NO_RETRACK",""))
   if can_compile_android and compile_only and android_upload: update_android_manifest() # AndroidManifest.xml will not have been updated, so we'd better do it now
   if can_compile_android or can_track_android:
     os.chdir(jSrc+"/..")
     dirName0 = S(getoutput("pwd|sed -e s,.*./,,"))
     dirName = shell_escape(dirName0)
   if can_compile_android: # TODO: use aapt2 and figure out how to make a 'bundle' with it so Play Store can accept new apps after August 2021 ?  (which requires giving them your signing keys, and I don't see the point in enforcing the 'bundle' format for a less than 1k saving due to not having to package multiple launcher icons on each device, and you'd probably have to compile non-Store apks separately.)  Don't know if/when updates to pre-Aug2021 apps will be required to be in Bundle format.
     cmd_or_exit("$BUILD_TOOLS/aapt package -0 '' -v -f -I $PLATFORM/android.jar -M AndroidManifest.xml -A assets -S res -m -J gen -F bin/resources.ap_") # (the -0 '' (no compression) is required if targetSdkVersion=30 or above, and shouldn't make much size difference on earlier versions as annotate.dat is itself compressed)
     cmd_or_exit("find src/"+jRest+" -type f -name '*.java' > argfile && javac -Xlint:deprecation -classpath $PLATFORM/android.jar -sourcepath 'src;gen' -d bin gen/"+jRest+"/R.java @argfile && rm argfile") # as *.java likely too long (-type f needed though, in case any *.java files are locked for editing in emacs)
     if os.path.exists(os.environ["BUILD_TOOLS"]+"/dx"): # older SDK
      a = " -JXmx4g --force-jumbo" # -J option must go first
      if "min-sdk-version" in getoutput("$BUILD_TOOLS/dx --help"):
       a += " --min-sdk-version=1" # older versions of dx don't have that flag, but will be min-sdk=1 anyway
      cmd_or_exit("$BUILD_TOOLS/dx"+a+" --dex --output=bin/classes.dex bin/")
     else: cmd_or_exit("$BUILD_TOOLS/d8 --min-api 1 --output bin $(find bin -type f -name '*.class')")
     cmd_or_exit("cp bin/resources.ap_ bin/"+dirName+".ap_")
     cmd_or_exit("cd bin && $BUILD_TOOLS/aapt add -0 '' "+dirName+".ap_ classes.dex")
     cmd_or_exit("rm -f bin/"+dirName0+".apk && $BUILD_TOOLS/zipalign 4 bin/"+dirName+".ap_ bin/"+dirName+".apk && rm -f ../"+dirName0+".apk")
     if all(x in os.environ for x in ["KEYSTORE_FILE","KEYSTORE_USER","KEYSTORE_PASS"]): cmd_or_exit("$BUILD_TOOLS/apksigner sign --ks $KEYSTORE_FILE --v1-signer-name $KEYSTORE_USER --ks-pass env:KEYSTORE_PASS --key-pass env:KEYSTORE_PASS --out ../"+dirName+".apk bin/"+dirName+".apk")
     cmd_or_exit("rm -f bin/"+dirName0+".ap_ bin/"+dirName0+".apk")
     if not can_track_android: cmd_or_exit("du -h ../"+dirName+".apk")
   if can_track_android:
     import httplib2,googleapiclient.discovery,oauth2client.service_account # pip install google-api-python-client (or pip install --upgrade google-api-python-client if yours is too old).  Might need pip install oauth2client also.
     trackToUse = os.environ.get("GOOGLE_PLAY_TRACK","").strip()
     if not trackToUse: trackToUse='beta'
     for tryNo in xrange(10):
      try:
       if tryNo:
         sys.stderr.write("\nRetrying in 1 minute... ")
         sys.stderr.flush() ; time.sleep(60)
         sys.stderr.write("now\n")
       sys.stderr.write("Logging in... ")
       sys.stderr.flush()
       service = googleapiclient.discovery.build('androidpublisher', 'v3', http=oauth2client.service_account.ServiceAccountCredentials.from_json_keyfile_name(os.environ['SERVICE_ACCOUNT_KEY'],'https://www.googleapis.com/auth/androidpublisher').authorize(httplib2.Http()))
       eId = service.edits().insert(body={},packageName=jPackage).execute()['id']
       if android_upload:
         sys.stderr.write("uploading... ")
         sys.stderr.flush()
         v = service.edits().apks().upload(editId=eId,packageName=jPackage,media_body="../"+dirName+".apk").execute()['versionCode']
         sys.stderr.write("\rUploaded "+dirName+".apk (version code "+str(v)+")\n")
         open(jSrc+"/../.last-versionCode","w").write(str(v))
       else: v = int(open(jSrc+"/../.last-versionCode").read().strip()) # if this fails, you probably didn't run annogen v0.691+ to compile the APK before trying to change track (see instructions printed when GOOGLE_PLAY_TRACK environment variable is not set)
       if os.environ.get("GOOGLE_PLAY_CHANGELOG",""): service.edits().tracks().update(editId=eId,track=trackToUse,packageName=jPackage,body={u'releases':[{u'versionCodes':[v],u"releaseNotes":[{u"language":u"en-US",u"text":T(os.environ["GOOGLE_PLAY_CHANGELOG"])}],u'status':u'completed'}],u'track':trackToUse}).execute() # needs to be "en-US" as just "en" is dropped by the Store, although it does say you can "add as supported language in your app's Store Listing"
       else:
         service.edits().tracks().update(editId=eId,track=trackToUse,packageName=jPackage,body={u'releases':[{u'versionCodes':[v],u'status':u'completed'}],u'track':trackToUse}).execute()
         if not android_upload: sys.stderr.write("Warning: GOOGLE_PLAY_CHANGELOG not set, any release notes will be deleted\n")
       sys.stderr.write("Committing... ")
       sys.stderr.flush()
       sys.stderr.write("\rCommitted edit %s: %s.apk v%s to %s\n" % (service.edits().commit(editId=eId,packageName=jPackage).execute()['id'],dirName,v,trackToUse))
       break
      except httplib2.HttpLib2Error: pass
   if not can_compile_android and not can_track_android: sys.stderr.write("Android source has been written to "+jSrc[:-3]+"""
To have Annogen build it for you, set these environment variables
before the Annogen run (change the examples obviously) :
   export SDK=/home/example/Android/Sdk
   export PLATFORM=$SDK/platforms/android-33
   export BUILD_TOOLS=$SDK/build-tools/33.0.1
   # To sign the build (required for release), additionally set:
   export KEYSTORE_FILE=/path/to/keystore
   export KEYSTORE_USER='your user name'
   export KEYSTORE_PASS='your password'

   # The app will be compatible with Android 1.0+
   # but SDK 24+ is required on the build machine.
   # SDK 24 was released mid-2016.  If you have an older Intel-based machine whose main OS cannot be upgraded, you may be able to install a newer SDK on a virtual machine, e.g. on a 2011 Mac stuck on MacOS 10.7, I used VirtualBox 4.3.4, Vagrant 1.9.5, Debian 8 Jessie and SSH with X11 forwarding to install Android Studio 3.5 from 2019, although for apksigner to work I also had to add 'deb http://archive.debian.org/debian/ jessie-backports main' to /etc/apt/sources.list and do 'sudo apt-get -o Acquire::Check-Valid-Until=false update' and 'sudo apt-get install -t jessie-backports openjdk-8-jdk openjdk-8-jre openjdk-8-jre-headless ca-certificates-java' and 'sudo apt-get --purge remove openjdk-7-jre-headless'
   # On non-Intel architectures, I suggest installing box64 (and box86 is also useful for 32-bit binaries), and installing the x86 Android SDK (you'll need an X11 connection to it to download and install Android Studio).  Ubuntu 22.04's multi-architecture android-sdk-build-tools package is not suitable (even together with google-android-platform-24-installer) because it doesn't provide the necessary update to app signing in SDK 24.

   # You can upload the apk to Google Play to update an existing app.
   # Since August 2021, Google Play enforces a different 'bundle' format
   # for new apps, which I don't yet know how to make.
   # To upload the update release to Google Play, additionally set:
   export SERVICE_ACCOUNT_KEY=/path/to/api-*.json
   # (must be an absolute path)
   # and optionally:
   export GOOGLE_PLAY_CHANGELOG="Updated annotator"
   export GOOGLE_PLAY_TRACK=alpha # default beta (please don't put production); however sending yourself the APK file is usually faster than using the alpha track if it's just to test on your own devices
   # If the above variables including SERVICE_ACCOUNT_KEY are set (and you haven't set ANDROID_NO_UPLOAD, below), then you'll also get an openPlayStore() function added to the Javascript interface for use in 'check for updates' links.
   # After testing, you can change the track of an existing APK by setting ANDROID_NO_UPLOAD=1 but still setting SERVICE_ACCOUNT_KEY and GOOGLE_PLAY_TRACK (and not ANDROID_NO_RETRACK), and run with --compile-only.  You will need to set GOOGLE_PLAY_CHANGELOG again when doing this, as the Google API now discards changelogs on track-changes unless they are re-specified.

You may also wish to create some icons in res/drawable*
   (using Android Studio or the earlier ADT tools).

On Google Play you may wish to set Release management -
   Pre-launch report - Settings - Enable pre-launch
   reports to OFF, or it'll report issues on the websites
   you link to (and maybe crashes due to Firebase issues),
   which (if you don't want them) is wasting resources.
""") # TODO: try if("true".equals(android.provider.Settings.System.getString(getContentResolver(),"firebase.test.lab"))) browser.loadUrl("about:blank"); (but turning off unwanted reports is better)
elif c_filename and c_compiler:
    cmd = c_compiler # should include any -o option
    if zlib: cmd += " -lz" # TODO: is this always correct on all platforms? (although user can always simply redirect the C to a file and compile separately)
    cmd_or_exit(cmd + " " + shell_escape(c_filename))
elif compile_only: errExit("Don't know what compiler to run for this set of options")
