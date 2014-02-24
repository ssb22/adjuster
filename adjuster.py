#!/usr/bin/env python

program_name = "Web Adjuster v0.1684 (c) 2012-13 Silas S. Brown"

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys,os

if '--html-options' in sys.argv: # for updating the website
    tornado=False
    inDL = 0
    print "<h3>Options for "+program_name[:program_name.index("(c)")].strip()+"</h3>"
    def heading(h):
        global inDL
        if inDL: print "</dl>"
        print "<h4>"+h+"</h4>"
        print "<dl>"
        inDL = 1
    def define(name,default=None,help="",multiple=False):
        if default or default==False:
            if type(default)==type(""): default=default.replace(",",", ").replace("  "," ")
            else: default=repr(default)
            default=" (default "+default+")"
        else: default=""
        def amp(h): return h.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        help = amp(help)
        for ttify in ["option=\"value\"","option='value'","\"\"\"","--"]: help=help.replace(ttify,"<nobr><tt>"+ttify+"</tt></nobr>")
        print "<dt><tt>--"+name+"</tt>"+amp(default)+"</dt><dd>"+help.replace(" - ","---")+"</dd>"
    def getfqdn(): return "is the machine's domain name" # default is ...
else:
    import tornado
    from tornado.httpclient import AsyncHTTPClient
    from tornado.ioloop import IOLoop
    from tornado import web
    from tornado.web import Application, RequestHandler, asynchronous
    import tornado.options
    from tornado.options import define,options
    from socket import getfqdn
    def heading(h): pass

heading("General options")
define("config",help="Name of the configuration file to read, if any. The process's working directory will be set to that of the configuration file so that relative pathnames can be used inside it. Any option that would otherwise have to be set on the command line may be placed in this file as an option=\"value\" or option='value' line (without any double-hyphen prefix). Multi-line values are possible if you quote them in \"\"\"...\"\"\", and you can use standard \\ escapes. You can also set config= in the configuration file itself to import another configuration file (for example if you have per-machine settings and global settings). If you want there to be a default configuration file without having to set it on the command line every time, an alternative option is to set the ADJUSTER_CFG environment variable.")

heading("Network listening and security settings")
define("port",default=28080,help="The port to listen on. Setting this to 80 will make it the main Web server on the machine (which will likely require root access on Unix).")
define("user",help="The user name to run as, instead of root. This is for Unix machines where port is less than 1024 (e.g. port=80) - you can run as root to open the privileged port, and then drop privileges. Not needed if you are running as an ordinary user.")
define("address",default="",help="The address to listen on. If unset, will listen on all IP addresses of the machine. You could for example set this to localhost if you want only connections from the local machine to be received, which might be useful in conjunction with real_proxy.")
define("password",help="The password. If this is set, nobody can connect without specifying ?p= followed by this password. It will then be sent to them as a cookie so they don't have to enter it every time. Notes: (1) If wildcard_dns is False and you have multiple domains in host_suffix, then the password cookie will have to be set on a per-domain basis. (2) On a shared server you probably don't want to specify this on the command line where it can be seen by process-viewing tools; use a configuration file instead.")
define("password_domain",help="The domain entry in host_suffix to which the password applies. For use when wildcard_dns is False and you have several domains in host_suffix, and only one of them (perhaps the one with an empty default_site) is to be password-protected, with the others public. If this option is used then prominentNotice (if set) will not apply to the passworded domain.") # on the assumption that those who know the password understand what the tool is
define("auth_error",default="Authentication error",help="What to say when password protection is in use and a correct password has not been entered. HTML markup is allowed in this message. As a special case, if this begins with http:// then it is assumed to be the address of a Web site to which the browser should be redirected; if it is set to http:// and nothing else, the request will be passed to the server specified by own_server (if set).") # TODO: basic password form? or would that encourage guessing
define("open_proxy",default=False,help="Whether or not to allow running with no password. Off by default as a safeguard against accidentally starting an open proxy.")
define("real_proxy",default=False,help="Whether or not to accept requests in real HTTP 'proxy' format with original domains.  Warning: this bypasses the password and implies open_proxy.  Off by default.")
define("via",default=True,help="Whether or not to update the Via: and X-Forwarded-For: HTTP headers when forwarding requests") # (Via is "must" in RFC 2616)
define("robots",default=False,help="Whether or not to pass on requests for /robots.txt.  If this is False then all robots will be asked not to crawl the site; if True then the original site's robots settings will be mirrored.  The default of False is recommended.")

heading("DNS and website settings")
define("host_suffix",default=getfqdn(),help="The last part of the domain name. For example, if the user wishes to change www.example.com and should do so by visiting www.example.com.adjuster.example.org, then host_suffix is adjuster.example.org. If you do not have a wildcard domain then you can still adjust one site by setting wildcard_dns to False, host_suffix to your non-wildcard domain, and default_site to the site you wish to adjust. If you have more than one non-wildcard domain, you can set wildcard_dns to False, host_suffix to all your domains separated by slash (/), and default_site to the sites these correspond to, again separated by slash (/). If wildcard_dns is False and default_site is empty (or if it's a /-separated list and one of its items is empty), then the corresponding host_suffix gives a URL box and sets its domain in a cookie (and adds a link at the bottom of pages to clear this and return to the URL box), but this should be done only as a last resort: you can browse only one domain at a time at that host_suffix (links and HTTP redirects to other domains will leave the adjuster), and the sites you visit at that host_suffix might be able to see some of each other's cookies etc (leaking privacy) although the URL box page will try to clear site cookies.")
define("default_site",help="The site to fetch from if nothing is specified before host_suffix. If this is omitted then the user is given a URL box when that happens.")
define("own_server",help="Where to find your own web server. This can be something like localhost:1234 or 192.168.0.2:1234. If it is set, then any request that does not match host_suffix will be passed to that server to deal with, unless real_proxy is in effect. You can use this option as a quick way to put your existing server on the same public port if you don't want to go via nginx or whatever. Note: the password option will NOT password-protect your own_server.")
define("ownServer_if_not_root",default=True,help="When trying to access an empty default_site, if the path requested is not / then redirect to own_server (if set) instead of providing a URL box. If this is False then the URL box will be provided no matter what path was requested.") # TODO: "ownServer even if root" option, i.e. option to make host_suffix by itself go to own_server?  Or make ownServer_if_not_root permanent?  The logic that deals with off-site Location: redirects assumes the URL box will normally be at / (TODO document this?)
define('search_sites',multiple=True,help="Comma-separated list of search sites to be made available when the URL box is displayed (if default_site is empty). Each item in the list should be a URL (which will be prepended to the search query), then a space, then a short description of the site. The first item on the list is used by default; the user can specify other items by making the first word of their query equal to the first word of the short description. Additionally, if some of the letters of that first word are in parentheses, the user may specify just those letters. So for example if you have an entry http://search.example.com?q= (e)xample, and the user types 'example test' or 'e test', it will use http://search.example.com?q=test")
define("wildcard_dns",default=True,help="Set this to False if you do NOT have a wildcard domain and want to process only default_site. Setting this to False does not actually prevent other sites from being processed (for example, a user could override their local DNS resolver to make up for your lack of wildcard domain); if you want to really prevent other sites from being processed then you could also set own_server to deal with unrecognised domains. Setting wildcard_dns to False does stop the automatic re-writing of links to sites other than default_site. Leave it set to True to have ALL sites' links rewritten on the assumption that you have a wildcard domain.") # will then say "(default True)"

heading("General adjustment options")
define("default_cookies",help="Semicolon-separated list of name=value cookies to send to all remote sites, for example to set preferences. Any cookies that the browser itself sends will take priority over cookies in this list. Note that these cookies are sent to ALL sites. You can set a cookie only on a specific browser by putting (browser-string) before the cookie name, e.g. (iPad)x=y will set x=y only if 'iPad' occurs in the browser string (to match more than one browser-string keyword, you have to specify the cookie multiple times).") # TODO: site-specific option
# TODO: sets of adjustments can be switched on and off at a /__settings URL ?  or leave it to the injected JS
define("headAppend",help="Code to append to the HEAD section of every HTML document that has a BODY. Use for example to add your own stylesheet links and scripts. Not added to documents that lack a BODY such as framesets.")
define("headAppendCSS",help="URL of a stylesheet for headAppend.  This option automatically generates the LINK REL=... markup for it, and also tries to delete the string '!important' from other stylesheets, to emulate setting this stylesheet as a user CSS.")
define("cssName",help="A name for the stylesheet specified in headAppendCSS, such as \"High Contrast\".  If cssName is set, then the headAppendCSS stylesheet will be marked as \"alternate\", with Javascript links at the bottom of the page for browsers that lack their own CSS switching options.  If cssName is not set (default) then any stylesheet specified in headAppendCSS will be always on.") # TODO: non-Javascript fallback for the switcher
define("cssNameReload",multiple=True,default="IEMobile 6,Opera Mini,rekonq",help="List of (old) browsers that require alternate code for the cssName option, which is slower as it involves reloading the page on CSS switches.  Use this if the CSS switcher provided by cssName does nothing on your browser.") # Opera Mini sometimes worked and sometimes didn't; maybe there were regressions at their proxy.  JS switcher needs network traffic anyway on Opera Mini so we almost might as well use the non-JS version
define("headAppendRuby",default=False,help="Convenience option which appends CSS and Javascript code to the HEAD that tries to ensure simple RUBY markup displays legibly across all modern browsers; this might be useful if you used Annotator Generator to make the htmlFilter program.")
define("bodyAppend",help="Code to append to the BODY section of every HTML document that has one. Use for example to add a script that needs to be run after the rest of the body has been read, or to add a footer explaining how the page has been modified. See also prominentNotice.") # TODO: note that it will go at the bottom of IFRAMEs also, and suggest using something similar to prominentNotice's iframe-detection code?
define("bodyAppendGoesAfter",help="If this is set to some text or HTML code that appears verbatim in the body section, the code in bodyAppend will be inserted after the last instance of this text (case sensitive) instead of at the end of the body. Use for example if a site styles its pages such that the end of the body is not a legible place for a footer.") # (e.g. it would overprint some position=fixed stuff)
define("bodyPrepend",help="Code to place at the start of the BODY section of every HTML document that has one.") # May be a useful place to put some scripts. For example, a script that changes a low-vision stylesheet according to screen size might be better in the BODY than in the HEAD, because some Webkit-based browsers do not make screen size available when processing the HEAD of the starting page. # but sometimes it still goes wrong on Chromium startup; probably a race condition; might be worth re-running the script at end of page load just to make sure
define("prominentNotice",help="Text to add as a brief prominent notice to processed sites (may include HTML). If the browser has sufficient Javascript support, this will float relative to the browser window and will contain an 'acknowledge' button to hide it (for the current site in the current browsing session). Use prominentNotice if you need to add important information about how the page has been modified.")
define("delete",multiple=True,help="Comma-separated list of regular expressions to delete from HTML documents. Can be used to delete selected items of Javascript and other code if it is causing trouble for your browser. Will also delete from the text of pages; use with caution.")
define("delete_doctype",default=False,help="Delete the DOCTYPE declarations from HTML pages. This option is needed to get some old Webkit browsers to apply multiple CSS files consistently.")
define("deleteOmit",multiple=True,default="iPhone,iPad,Android,Macintosh",help="A list of browsers that do not need the delete and delete-doctype options to be applied. If any of these strings occur in the user-agent then these options are disabled for that request, on the assumption that these browsers are capable enough to cope with the \"problem\" code.")
define("codeChanges",help="Several lines of text specifying changes that are to be made to all HTML and Javascript code files on certain sites; use as a last resort for fixing a site's scripts. This option is best set in the configuration file and surrounded by r\"\"\"...\"\"\". The first line is a URL prefix, the second is a string of code to search for, and the third is a string to replace it with. Further groups of URL/search/replace lines may follow; blank lines and lines starting with # are ignored.")
define("viewsource",default=False,help="Provide a \"view source\" option. If set, you can see a page's pre-adjustment source code, plus client and server headers, by adding \".viewsource\" to the end of a URL (after any query parameters etc)")
define("htmlonly_mode",default=True,help="Provide a checkbox allowing the user to see pages in \"HTML-only mode\", stripping out most images, scripts and CSS; this might be a useful fallback for very slow connections if a site's pages bring in many external files and the browser cannot pipeline its requests. The checkbox is displayed by the URL box, not at the bottom of every page.") # if no pipeline, a slow UPLINK can be a problem, especially if many cookies have to be sent with each request for a js/css/gif/etc.
# (and if wildcard_dns=False and we're domain multiplexing, our domain can accumulate a lot of cookies, causing requests to take more uplink bandwidth, TODO: do something about this?)
# Above says "most" not "all" because some stripping not finished (see TODO comments) and because some scripts/CSS added by Web Adjuster itself are not stripped

heading("External processing options")
define("htmlFilter",help="External program to run to filter every HTML document. This can be any shell command; its standard input will get the HTML (or the plain text if htmlText is set), and it should send the new version to standard output. Multiple copies of the program might be run at the same time to serve concurrent requests. UTF-8 character encoding is used.")
define("htmlFilterName",help="A name for the task performed by htmlFilter. If this is set, the user will be able to switch it on and off from the browser via a cookie and some Javascript links at the bottom of HTML pages.") # TODO: non-Javascript fallback for the switcher
define("htmlJson",default=False,help="Try to detect HTML strings in JSON responses and feed them to htmlFilter. This can help when using htmlFilter with some AJAX-driven sites. IMPORTANT: Unless you also set the 'separator' option, the external program must preserve all newline characters, because multiple HTML strings in the same JSON response will be given to it separated by newlines, and the newlines of the output determine which fragment to put back where. (If you combine htmlJson with htmlText, the external program will see text in HTML in JSON as well as text in HTML, but it won't see text in HTML in JSON in HTML.)")
define("htmlText",default=False,help="Causes the HTML to be parsed, and only the text parts (not the markup) will be sent to htmlFilter. Useful to save doing HTML parsing in the external program. The external program is still allowed to include HTML markup in its output. IMPORTANT: Unless you also set the 'separator' option, the external program must preserve all newline characters, because multiple text strings will be given to it separated by newlines, and the newlines of the output determine which modified string to put back where.")
define("separator",help="If you are using htmlFilter with htmlJson and/or htmlText, you can set separator to any text string to be used as a separator between multiple items of data when passing them to the external program. By default, newlines are used for this, but you can set it to any other character or sequence of characters that cannot be added or removed by the program. (It does not matter if a website's text happens to use the separator characters.) If you set separator, not only will it be used as a separator BETWEEN items of data but also it will be added before the first and after the last item, thus allowing you to use an external program that outputs extra text before the first and after the last item. The extra text will be discarded. If however you do not set separator then the external program should not add anything extra before/after the document.")
define("leaveTags",multiple=True,default="script,style,title,textarea,option",help="When using htmlFilter with htmlText, you can set a comma-separated list of HTML tag names whose enclosed text should NOT be sent to the external program for modification. For this to work, the website must properly close these tags and must not nest them. (This list is also used for character-set rendering.)") # not including 'option' can break pages that need character-set rendering

heading("Server control options")
define("background",default=False,help="If True, fork to the background as soon as the server has started (Unix only). You might want to enable this if you will be running it from crontab, to avoid long-running cron processes.")
define("restart",default=False,help="If True, try to terminate any other process listening on our port number before we start (Unix only). Useful if Web Adjuster is running in the background and you want to quickly restart it with new options. Note that no check is made to make sure the other process is a copy of Web Adjuster; whatever it is, if it has our port open, it is asked to stop.")
define("stop",default=False,help="Like 'restart', but don't replace the other process after stopping it. This option can be used to stop a background server (if it's configured with the same port number) without starting a new one. Unix only.")
define("install",default=False,help="Try to install the program in the current user's Unix crontab as an @reboot entry, unless it's already there.  The arguments of the cron entry will be the same as the command line, with no directory changes (so make sure you are in the home directory before doing this).  The program will continue to run normally after the installation attempt.  (If you are on Cygwin then you might need to run cron-config also.)")
define("watchdog",default=0,help="(Linux only) Ping the system's watchdog every this number of seconds. This means the watchdog can reboot the system if for any reason Web Adjuster stops functioning, provided that no other program is pinging the watchdog. The default value of 0 means do not ping the watchdog.") # This option might not be suitable for a system whose watchdog cannot be set to wait a few extra seconds for a very complex page to be parsed (the worst case is where the program is just about to ping the watchdog when it gets a high-CPU request; the allowed delay time is the difference between the ping interval and the watchdog's \"heartbeat\" timeout, and this difference can be maximised by setting the ping interval to 1 although this does mean Adjuster will wake every second).  But see watchdogWait.
define("watchdogWait",default=0,help="When the watchdog option is set, wait this number of seconds before stopping the watchdog pings. This causes the watchdog pings to be sent from a separate thread and therefore not stopped when the main thread is busy; they are stopped only when the main thread has not responded for watchdogWait seconds. This can be used to work around the limitations of a hardware watchdog that cannot be set to wait that long.") # such as the Raspberry Pi's Broadcom chip which defaults to 10 seconds and has max 15; you could say watchdog=5 and watchdogWait=60
define("browser",help="The Web browser command to run. If this is set, Web Adjuster will run the specified command (which is assumed to be a web browser), and will exit when this browser exits. This is useful in conjunction with --real_proxy to have a personal proxy run with the browser. You still need to set the browser to use the proxy; this can sometimes be done via browser command line or environment variables.")

heading("Media conversion options")
define("bitrate",default=0,help="Audio bitrate for MP3 files, or 0 to leave them unchanged. If this is set to anything other than 0 then the 'lame' program must be present. Bitrate is normally a multiple of 8. If your mobile device has a slow link, try 16 for speech.")
define("askBitrate",default=False,help="If True, instead of recoding MP3 files unconditionally, try to add links to \"lo-fi\" versions immediately after each original link so you have a choice.")
define("pdftotext",default=False,help="If True, add links to run PDF files through the 'pdftotext' program (which must be present if this is set). A text link will be added just after any PDF link that is found, so that you have a choice of downloading PDF or text; note that pdftotext does not always manage to extract all text. The htmlJson setting will also be applied to the PDF link finder, and see also the guessCMS option.")
define("epubtotext",default=False,help="If True, add links to run EPUB files through Calibre's 'ebook-convert' program (which must be present), to produce a text-only option. A text link will be added just after any EPUB link that is found, so that you have a choice of downloading EPUB or text. The htmlJson setting will also be applied to the EPUB link finder, and see also the guessCMS option.")
# pdftotext and epubtotext both use temporary files, which are created in the system default temp directory unless overridden by environment variables TMPDIR, TEMP or TMP, TODO: do we want an override for NamedTemporaryFile's dir= option ourselves?  (/dev/shm might make more sense on some Flash-based systems, although filling the RAM and writing to swap might do more damage than writing files in /tmp if it gets big; also hopefully some OS's won't actually write anything if the file has been deleted before the buffer needed to be flushed (TODO: check this))
define("epubtozip",default=False,help="If True, add links to download EPUB files renamed to ZIP, as a convenience for platforms that don't have EPUB readers but can open them as ZIP archives and display the XHTML files they contain. The htmlJson setting will also be applied to the EPUB link finder, and see also the guessCMS option.") # TODO: option to cache the epub file and serve its component files individually, so other transforms can be applied and for platforms without ZIP capabilities
define("guessCMS",default=False,help="If True, then the pdftotext, epubtotext and epubtozip options attempt to guess if a link is pointing to a PDF or EPUB file via a Content Management System (i.e. the URL does not end in .pdf or .epub, but contains something like ?format=PDF)")
define("pdfepubkeep",default=200,help="Number of seconds to keep any generated text files from PDF and EPUB.  If this is 0, the files will be deleted immediately, but that might be undesirable: if a mobile phone browser has a timeout that takes effect before ebook-convert has finished (this can sometimes be the case with Opera Mini for example), it might be best to allow the user to wait a short time and re-submit the request, this time getting a cached response.") # Opera Mini's opera:config can set the loading timeout to longer, default is 30 seconds

heading("Character rendering options")
# TODO: option to add a switch at top of page ?
define("render",default=False,help="Whether to enable the character-set renderer. This functionality requires the Python Imaging Library and suitable fonts. The settings of htmlJson and leaveTags will also be applied to the renderer. Text from computed Javascript writes might not be rendered as images.") # ("computed" as in not straight from a JSON document.  TODO: could write a piece of JS that goes through the DOM finding them? ditto any JS alterations that haven't been through htmlFilter, although you'd have to mark the ones that have and this could be filter-dependent)
define("renderFont",help="The font file to use for the character-set renderer (if enabled). This should be a font containing all the characters you want to render, and it should be in .TTF, .OTF or other Freetype-supported format (.PCF is sometimes possible if you set renderSize correctly, e.g. 16 for wenquanyi_12pt.pcf)") # TODO: different fonts for different Unicode ranges? (might be hard to auto-detect missing characters)
define("renderInvert",default=False,help="If True, the character-set renderer (if enabled) will use a black background. Useful when you are also adding a stylesheet with a dark background.")
define("renderSize",default=20,help="The height (in pixels) to use for the character-set renderer if it is enabled.")
define("renderPath",default="/@_",help="The location on every adjusted website to put the character-set renderer's images, if enabled. This must be made up of URL-safe characters starting with a / and should be a short path that is unlikely to occur on normal websites.")
define("renderFormat",default="png",help="The file format of the images to be created by the character-set renderer if it is enabled, for example 'png' or 'jpeg'.")
define("renderRange",multiple=True,help="The lowest and highest Unicode values to be given to the character-set renderer if it is enabled. For example 3000:A6FF for most Chinese characters. Multiple ranges are allowed. Any characters NOT in one of the ranges will be passed to the browser to render. If the character-set renderer is enabled without renderRange being set, then ALL text will be rendered to images.")
define("renderOmit",multiple=True,default="iPhone,iPad,Android,Macintosh",help="A list of browsers that do not need the character-set renderer. If any of these strings occur in the user-agent then the character set renderer is turned off even if it is otherwise enabled. The assumption is that these browsers can always do their own character-set rendering.")
define("renderCheck",help="If renderOmit does not apply to the browser, it might still be possible to check for native character-set support via Javascript. renderCheck can be set to the Unicode value of a character to be checked (try 802F for complete Chinese support); if the browser reports its width differently from known unprintable characters, we assume it won't need our renderer.") # 802F shouldn't create false positives in environments that support only GB2312, only Big5, only SJIS or only KSC instead of all Chinese. It does have GB+ and Big5+ codes (and also demonstrates that we want a hex number). If browser's "unprintable character" glyph happens to be the same width as renderCheck anyway then we could have a false negative, but that's better than a false positive and the user can still switch it off manually if renderName is left set.
define("renderNChar",default=1,help="The maximum number of characters per image to be given to the character-set renderer if it is enabled. Keeping this low means the browser cache is more likely to be able to re-use images, but some browsers might struggle if there are too many separate images. Don't worry about Unicode \"combining diacritic\" codes: any found after a character that is to be rendered will be included with it without counting toward the renderNChar limit and without needing to be in renderRange.")
define("renderWidth",default=0,help="The maximum pixel width of a 'word' when using the character-set renderer. If you are rendering a language that uses space to separate words, but are using only one or two characters per image, then the browser might split some words in the middle. Setting renderWidth to some value other than 0 can help to prevent this: any word narrower than renderWidth will be enclosed in a <nobr> element. (This will however be ineffective if your stylesheet overrides the behaviour of <nobr>.) You should probably not set renderWidth if you intend to render languages that do not separate words with spaces.")
define("renderDebug",default=False,help="If the character-set renderer is having problems, try to insert comments in the HTML source to indicate why.  The resulting HTML is not guaranteed to be well-formed, but it might help you debug a misbehaving htmlFilter.  This option may also insert comments in bad HTML before the htmlFilter stage even when the renderer is turned off.")
define("renderName",default="Fonts",help="A name for a switch that allows the user to toggle character set rendering on and off from the browser (via a cookie and Javascript links at the bottom of HTML pages); if set to the empty string then no switch is displayed. At any rate none is displayed when renderOmit applies.") # TODO: non-Javascript fallback for the switcher

heading("Dynamic DNS options")
define("dynamic_dns_api",help="URL (http or https) that will cause one of your dynamic DNS entries to be updated to a new IP address.  If this is set, it will be used to automatically update the domains listed in host_suffix.  The URL should contain two instances of %s; the first will be substituted with the domain name and the second with its new IP address.")
define("ddns_api_user",help="The user name to supply to the dynamic_dns_api URL (Basic authentication over HTTP or HTTPS)")
define("ddns_api_pwd",help="The password to supply to the dynamic_dns_api URL (Basic authentication over HTTP or HTTPS).  Best not placed on the command line on a shared machine where it can be seen by process-viewing tools; use a configuration file instead.")
define("ip_query_url",help="URL that will return your current public IP address, as a line of text with no markup added. Used for the dynamic_dns_api option. You can set up a URL by placing a CGI script on a server outside your network and having it do: echo Content-type: text/plain;echo;echo $REMOTE_ADDR")
define("ip_check_interval",default=8000,help="Number of seconds between checks of ip_query_url for the dynamic_dns_api option")
define("ip_force_interval",default=7*24*3600,help="Number of seconds before dynamic_dns_api (if set) is forced to update even if there was no IP change.  This is to let the Dynamic DNS system know that we are still around.  Set to 0 to disable forced updates (a forced update will occur on server startup anyway), otherwise an update will occur on the next ip_check_interval after ip_force_interval has elapsed.")
define("ip_change_command",help="An optional shell command to run (in a separate thread) whenever your IP changes. Use instead of, or in addition to, dynamic_dns_api.  The new IP address will be appended to this command.")

heading("Speedup options")
define("useLXML",default=False,help="Use the LXML library for parsing HTML documents. This is usually faster, but it can fail if your system does not have a good installation of LXML and its dependencies, or if the websites you visit are badly broken. Use of LXML libraries may also result in more changes to all HTML markup, although this should be harmless.")
define("renderBlocks",default=False,help="Treat all characters rendered by the character-set renderer as \"blocks\" that are guaranteed to have the same dimensions (true for example if you are using the renderer for Chinese characters only). This is faster than checking words individually, but it may produce incorrect HEIGHT and WIDTH attributes if given a range of characters whose dimensions do differ.") # TODO: blocksRange option for if want to render some that do and some that don't? (but profile it: PIL's getsize just might turn out to be quicker than the high-level range-check code)
define("fasterServer",help="Address:port of another instance of Web Adjuster to which we forward all traffic whenever it is available. When the other instance is not available, traffic will be handled by this one. Use for example if you have a slower always-on machine and a faster not-always-on machine and you want the slower machine to delegate to the faster machine when available. See also ipTrustReal.")
define("ipTrustReal",help="IP address of a machine that we trust, for example a machine that is using us as fasterServer. Any traffic coming from this machine with an X-Real-Ip header will be logged as though it originated at the value of its X-Real-Ip header.") # (TODO: multiple IPs option?)

# THIS MUST BE THE LAST SECTION because it continues into
# the note below about Tornado logging options.  (The order
# of define()s affects the HTML order only; --help will be
# sorted alphabetically by Tornado.)
heading("Logging options")
define("renderLog",default=False,help="Whether or not to log requests for character-set renderer images. Note that this can generate a LOT of log entries on some pages.")
define("logUnsupported",default=False,help="Whether or not to log attempts at requests using unsupported HTTP methods. Note that this can sometimes generate nearly as many log entries as renderLog if some browser (or malware) tries to do WebDAV PROPFIND requests on each of the images.")
define("ipNoLog",multiple=True,help="A comma-separated list of IP addresses which can use the adjuster without being logged. If your network has a \"friendly probing\" service then you might want to use this to stop it filling up the logs.  (Any tracebacks it causes will still be logged however.)")
define("squashLogs",default=True,help="Try to remove some duplicate information from consecutive log entries, to make logs easier to check. You might want to set this to False if you plan to use automatic search tools on the logs.") # (word 'some' is important as not all duplicate info is guaranteed to be removed)
define("whois",default=False,help="Try to log the Internet service provider for each IP address in the logs.  Requires the 'whois' program.  The extra information is written as separate log entries when it becomes available, and not for recent duplicate IPs or IPs that do not submit valid requests.")
define("errorHTML",default="Adjuster error has been logged",help="What to say when an uncaught exception (due to a misconfiguration or programming error) has been logged. HTML markup is allowed in this message.")
define("logDebug",default=False,help="Write debugging messages (to standard error if in the foreground, or to the logs if in the background). Use as an alternative to --logging=debug if you don't also want debug messages from other Tornado modules.")
# and continuing into the note below:
if not tornado:
    print "</dl>"
    print "Tornado-provided logging options are not listed above because they might vary across Tornado versions; run <tt>python adjuster.py --help</tt> to see a full list of the ones available on your setup. They typically include <tt>log_file_max_size</tt>, <tt>log_file_num_backups</tt>, <tt>log_file_prefix</tt> and <tt>log_to_stderr</tt>." # and --logging=debug but that may generate a lot of entries from curl_httpclient
    raise SystemExit

import time,os,commands,string,urllib,urlparse,re,socket,logging,subprocess,threading,json,base64
from HTMLParser import HTMLParser,HTMLParseError

try: # can we page the help text?
    import pydoc,cStringIO ; pydoc.pager # ensure present
    old_top = tornado.options.print_help
    def new_top():
        dat = cStringIO.StringIO() ; old_top(dat)
        pydoc.pager(dat.getvalue())
    tornado.options.print_help = new_top
except: pass

def hostSuffix(n=0):
    if options.host_suffix:
        return options.host_suffix.split("/")[n]
    return ""
def defaultSite(n=0):
    if options.default_site:
        return options.default_site.split("/")[n]
    return ""

def convert_to_real_host(requested_host,cookie_host=None):
    # Converts the host name requested by the user into the
    # actual host that we should request, or returns "" if
    # we should display the URL entry box etc.
    # Returns -1 if we should pass to options.own_server.
    if requested_host:
      port=":"+str(options.port)
      orig_requested_host = requested_host
      if requested_host.endswith(port): requested_host=requested_host[:-len(port)]
      n=0
      for h in options.host_suffix.split("/"):
        if requested_host.endswith("."+h): return redot(requested_host[:-len(h)-1])
        if requested_host == h:
            d = defaultSite(n)
            if d: return d
            elif cookie_host==h: return 0 # special type of (false) value to tell the code that we're handling this request ourselves but possibly via ownServer_if_not_root
            else: return cookie_host
        n += 1
      if options.real_proxy: return orig_requested_host
    if options.own_server: return -1
    else: return defaultSite()
def convert_to_via_host(requested_host):
    if requested_host:
      port=":"+str(options.port)
      orig_requested_host = requested_host
      if requested_host.endswith(port): requested_host=requested_host[:-len(port)]
      if options.port==80: port=""
      for h in options.host_suffix.split("/"):
        if (requested_host == h and options.default_site) or requested_host.endswith("."+h): return h+port
    if options.wildcard_dns and not '/' in options.host_suffix: return options.host_suffix+port
    return "somewhere" # ?
def convert_to_requested_host(real_host,cookie_host=None):
    # Converts the actual host name into the host name that
    # the user should request to get it through us
    if not real_host: return ""
    if options.port==80: port=""
    else: port=":"+str(options.port)
    if options.default_site:
      n=0
      for i in options.default_site.split("/"):
        if not i: i=cookie_host
        if real_host == i:
            return hostSuffix(n)+port
        n += 1
    if not options.wildcard_dns: return real_host # leave the proxy
    else: return dedot(real_host)+"."+hostSuffix()+port

# RFC 2109: A Set-Cookie from request-host y.x.foo.com for Domain=.foo.com would be rejected, because H is y.x and contains a dot.
# That means (especially if a password is set) we'd better make sure our domain-rewrites don't contain dots.  If requested with dot, relocate to without dot.
def dedot(domain):
    # - means . but -- is a real - (OK as 2 dots can't come together and a - can't come immediately after a dot in domain names, so --- = -., ---- = --, ----- = --. etc)
    return domain.replace("-","--").replace(".","-")
def redot(domain): return domain.replace("--","@MINUS@").replace("-",".").replace("@MINUS","-")

def changeConfigDirectory(fname):
    fdir,ffile = os.path.split(fname)
    def tryDir(d):
        d2 = d
        if d2 and not d2.endswith(os.sep): d2 += os.sep
        if os.path.isfile(d2+fname):
            if d: os.chdir(d)
            if fdir: os.chdir(fdir)
            return True # found it
    if tryDir("") or not (os.sep in sys.argv[0] or (os.sep=='\\' and '/' in sys.argv[0])): return ffile
    if os.sep=="\\" and '/' in sys.argv[0] and os.path.isfile(sys.argv[0].replace('/','\\')): sys.argv[0]=sys.argv[0].replace('/','\\') # hack for some Windows Python builds accepting slash in command line but reporting os.sep as backslash
    if tryDir(sys.argv[0][:sys.argv[0].rfind(os.sep)]):
        return ffile
    return fname

def readOptions():
    tornado.options.parse_command_line()
    configsDone = set()
    if not options.config: options.config=os.environ.get("ADJUSTER_CFG","") # must do HERE rather than setting default= above, or options.config=None below might not work
    while options.config and (options.config,os.getcwd()) not in configsDone:
        # sys.stderr.write("Reading config from "+options.config+"\n")
        config = options.config ; options.config=None # allow it to be overridden on the next file
        oldDir = os.getcwd()
        config2 = changeConfigDirectory(config)
        try: open(config2)
        except:
            sys.stderr.write("Cannot open configuration file %s (current directory is %s)\n" % (config2,os.getcwd()))
            sys.exit(1)
        tornado.options.parse_config_file(config2)
        configsDone.add((config,oldDir))
    tornado.options.parse_command_line() # need to do this again to ensure logging is set up for the *current* directory (after any chdir's while reading config files)
    if type(options.leaveTags)==type(""): options.leaveTags=options.leaveTags.split(',')
    create_inRenderRange_function(options.renderRange)
    if type(options.renderOmit)==type(""): options.renderOmit=options.renderOmit.split(',')
    if type(options.deleteOmit)==type(""): options.deleteOmit=options.deleteOmit.split(',')
    if type(options.cssName)==type(""): options.cssName=options.cssName.replace('"',"&quot;") # for embedding in JS
    if type(options.cssNameReload)==type(""): options.cssNameReload=options.cssNameReload.split(',')
    if type(options.search_sites)==type(""): options.search_sites=options.search_sites.split(',')
    if type(options.ipNoLog)==type(""): options.ipNoLog=options.ipNoLog.split(',')
    if type(options.delete)==type(""): options.delete=options.delete.split(',')
    global codeChanges ; codeChanges = []
    if options.codeChanges:
      ccLines = [x for x in options.codeChanges.split("\n") if x and not x.startswith("#")]
      while ccLines:
        if len(ccLines)<3:
            sys.stderr.write("codeChanges must be a multiple of 3 lines (see --help)\n")
            sys.exit(1)
        codeChanges.append(tuple(ccLines[:3]))
        ccLines = ccLines[3:]
    if options.real_proxy: options.open_proxy=True
    if not options.password and not options.open_proxy:
        stderr.write("Please set a password, or use --open_proxy.\n(Try --help for help)\n")
        sys.exit(1)
    if options.install:
        current_crontab = commands.getoutput("crontab -l 2>/dev/null")
        new_cmd = "@reboot python "+" ".join(sys.argv) # TODO: crontab-friendly quoting of special characters
        if not new_cmd in current_crontab.replace("\r","\n").split("\n"):
            sys.stderr.write("Adding to crontab: "+new_cmd+"\n")
            if not current_crontab.endswith("\n"): current_crontab += "\n"
            os.popen("crontab -","w").write(current_crontab+new_cmd+"\n")
    if options.restart or options.stop:
        pidFound = stopOther()
        if options.stop:
            if not pidFound: sys.stderr.write("Could not find which PID to stop (maybe nothing was running?)\n")
            sys.exit(0)
        elif pidFound: time.sleep(0.5) # give it time to stop

def main():
    readOptions()
    handlers = [
        (r"/(.*)", RequestForwarder, {})
    ]
    if options.real_proxy: handlers.append((r"(.*)", RequestForwarder, {})) # doesn't have to start with /
    application = Application(handlers,log_function=accessLog,gzip=True)
    # tornado.web.Application.__init__(self,  transforms=[ChunkedTransferEncoding], gzip=True)
    if not hasattr(application,"listen"):
        sys.stderr.write("Your version of Tornado is too old.  Please install version 2.x.\n")
        sys.exit(1)
    if options.useLXML: check_LXML()
    if fork_before_listen and options.background:
        sys.stderr.write("%s\nLicensed under the Apache License, Version 2.0\nChild will listen on port %d\n(can't report errors here as this system needs early fork)\n" % (program_name,options.port)) # (need some other way of checking it really started)
        unixfork()
    try: application.listen(options.port,options.address)
    except:
        if options.browser:
            # there's probably another adjuster instance, in which case we probably want to let the browser open a new window and let our listen() fail
            dropPrivileges()
            runBrowser()
        raise
    if options.watchdog:
        watchdog = open("/dev/watchdog", 'w')
    dropPrivileges()
    sys.stderr.write("%s\nLicensed under the Apache License, Version 2.0\nListening on port %d\n" % (program_name,options.port))
    if options.watchdog:
        sys.stderr.write("Writing /dev/watchdog every %d seconds\n" % options.watchdog)
        if options.watchdogWait: sys.stderr.write("(abort if unresponsive for %d seconds)\n" % options.watchdogWait)
    if options.background and not fork_before_listen:
        unixfork()
    if options.browser: IOLoop.instance().add_callback(runBrowser)
    if options.watchdog: WatchdogPings(watchdog)
    if options.fasterServer: IOLoop.instance().add_callback(checkServer)
    if options.ip_query_url and (options.dynamic_dns_api or options.ip_change_command): Dynamic_DNS_updater()
    try:
        import signal
        signal.signal(signal.SIGTERM, stopServer)
    except: pass # signal not supported on this platform?
    if options.background: logging.info("Server starting")
    IOLoop.instance().start()
    # gets here after stopServer (e.g. got SIGTERM from a --stop, or options.browser and the browser finished)
    if options.background: logging.info("Server shutdown")
    if options.watchdog:
        watchdog.write('V') # this MIGHT be clean exit, IF the watchdog supports it (not all of them do, so it might not be advisable to use the watchdog option if you plan to stop the server without restarting it)
        watchdog.close()
    if not options.background:
        sys.stderr.write("Adjuster shutdown\n")

def dropPrivileges():
    if options.user and not os.getuid():
        # need to drop privileges
        import pwd
        os.setuid(pwd.getpwnam(options.user)[2])

fork_before_listen = not 'linux' in sys.platform

def unixfork():
    if os.fork(): sys.exit()
    os.setsid()
    if os.fork(): sys.exit()
    devnull = os.open("/dev/null", os.O_RDWR)
    for fd in range(3): os.dup2(devnull,fd) # commenting out this line will let you see stderr after the fork (TODO debug option?)
    
def stopOther():
    import commands,signal
    out = commands.getoutput("lsof -iTCP:"+str(options.port)+" -sTCP:LISTEN")
    if out.startswith("lsof: unsupported"):
        # lsof 4.81 has -sTCP:LISTEN but lsof 4.78 does not.  However, not including -sTCP:LISTEN can cause lsof to make unnecessary hostname queries for established connections.  So fall back only if have to.
        out = commands.getoutput("lsof -iTCP:"+str(options.port)+" -Ts") # -Ts ensures will say LISTEN on the pid that's listening
        lines = filter(lambda x:"LISTEN" in x,out.split("\n")[1:])
    elif out.find("not found")>-1 and not commands.getoutput("which lsof 2>/dev/null"):
        sys.stderr.write("stopOther: no 'lsof' command on this system\n")
        return False
    else: lines = out.split("\n")[1:]
    for line in lines:
        try: pid=int(line.split()[1])
        except:
            sys.stderr.write("stopOther: Can't make sense of lsof output\n")
            break
        if not pid==os.getpid():
            if options.stop: other="the"
            else: other="other"
            try:
                os.kill(pid,signal.SIGTERM)
                sys.stderr.write("Stopped %s process at PID %d\n" % (other,pid))
            except: sys.stderr.write("Failed to stop %s process at PID %d\n" % (other,pid))
            return True # (a pid was found, whether or not the stop was successful) (don't continue - there should be only one pid, and continuing might get duplicate listings for IPv4 and IPv6)

the_supported_methods = ("GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "CONNECT")
# Don't support PROPFIND (from WebDAV) unless be careful about how to handle image requests with it
# TODO: image requests with OPTIONS ?

class BrowserLogger:
  def __init__(self):
    # Do NOT read options here - they haven't been read yet
    self.lastBrowser = self.lastDate = None
    self.lastIp = self.lastMethodStuff = None
    self.whoisLogger = WhoisLogger()
  def __call__(self,req):
    if req.request.remote_ip in options.ipNoLog: return
    try: ch = req.cookie_host()
    except: ch = None # shouldn't happen
    req=req.request
    try:
        if req.suppress_logging: return
    except: pass
    if req.method not in the_supported_methods and not options.logUnsupported: return
    if req.method=="CONNECT" or req.uri.startswith("http://"): host="" # URI will have everything
    else: host=convert_to_real_host(req.host,ch)
    if host==-1: host=req.host # for own_server (but this shouldn't happen as it was turned into a CONNECT; we don't mind not logging own_server because it should do so itself)
    elif host: host="http://"+host
    # elif host==0: host="http://"+ch # e.g. adjusting one of the ownServer_if_not_root pages (TODO: uncomment this?)
    else: host=""
    browser = req.headers.get('User-Agent',None)
    if browser:
        browser='"'+browser+'"'
        if options.squashLogs and browser==self.lastBrowser: browser = ""
        else:
            self.lastBrowser = browser
            browser=" "+browser
    else: self.lastBrowser,browser = None," -"
    if options.squashLogs:
        # Time will already be included in Tornado logging format (a format we don't want to override, especially as it has 'start of log string syntax highlighting' on some platforms), so don't add it here.  Just add the date if different.
        t = time.strftime("[%d/%b/%Y] ")
        if t==self.lastDate: t=""
        else: self.lastDate = t
        if req.remote_ip == self.lastIp:
            ip=""
        else:
            self.lastIp = req.remote_ip
            ip=req.remote_ip+" "
            self.lastMethodStuff = None # always log method/version anew when IP is different
        methodStuff = (req.method, req.version)
        if methodStuff == self.lastMethodStuff:
            r=host+req.uri
        else:
            r='"%s %s%s %s"' % (req.method, host, req.uri, req.version)
            self.lastMethodStuff = methodStuff
        msg = t+ip+r+browser
    else: msg = '%s - - [%s] "%s %s%s %s" - - - %s' % (req.remote_ip, time.strftime("%d/%b/%Y:%X"), req.method, host, req.uri, req.version, browser)
    logging.info(msg)
    if options.whois and hasattr(req,"valid_for_whois"): self.whoisLogger(req.remote_ip)

class WhoisLogger:
    def __init__(self):
        # Do NOT read options here - haven't been read yet
        # (can be constructed even if not options.whois)
        self.recent_whois = []
        self.thread_running = False
    def __call__(self,ip):
        if ip in self.recent_whois: return
        if len(self.recent_whois) > 20: # TODO: configure?
            self.recent_whois.pop()
        self.recent_whois.insert(0,ip)
        self.reCheck(ip)
    def reCheck(self,ip):
        if self.thread_running: # allow only one at once
            IOLoop.instance().add_timeout(time.time()+1,lambda *args:self.reCheck(ip))
            return
        self.thread_running = True
        threading.Thread(target=whois_thread,args=(ip,self)).start()
def getWhois(ip):
    import commands
    lines = commands.getoutput("whois '"+ip.replace("'",'')+"'").split('\n')
    if any(l and l.lower().split()[0]=="descr:" for l in lines): checkList = ["descr:"] # ,"netname:","address:"
    else: checkList = ["orgname:"]
    ret = []
    for l in lines:
        if len(l.split())<2: continue
        field,value = l.split(None,1) ; field=field.lower()
        if field in checkList or (field=="country:" and ret) and not value in ret: ret.append(value) # omit 1st country: from RIPE/APNIC/&c, and de-dup
    return ", ".join(ret)
def whois_thread(ip,logger):
    address = getWhois(ip)
    logger.thread_running = False
    if address: IOLoop.instance().add_callback(lambda *args:logging.info("whois "+ip+": "+address))

accessLog = BrowserLogger()

try:
    import pycurl # check it's there
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
except: pass # fall back to the pure-Python one

cookieExpires = "Tue Jan 19 03:14:07 2038" # TODO: S2G

def writeAndClose(stream,data):
    # This helper function is needed for CONNECT and own_server handling because, contrary to Tornado docs, some Tornado versions (e.g. 2.3) send the last data packet in the FIRST callback of IOStream's read_until_close
    if data: stream.write(data)
    if not stream.closed(): stream.close()

# Domain-setting cookie for when we have no wildcard_dns and no default_site:
adjust_domain_cookieName = "_adjusterDN_"
adjust_domain_none = "0" # not a valid top-level domain (TODO hopefully no user wants this as a local domain...)
enable_adjustDomainCookieName_URL_override = True # TODO: document this!  (Allow &_adjusterDN_=0 or &_adjusterDN_=wherever in bookmark URLs, so it doesn't matter what setting the cookie has when the bookmark is activated)

htmlmode_cookie_name = "_adjustZJCG_" # zap JS, CSS and Graphics
password_cookie_name = "_pxyAxsP_" # "proxy access password". have to pick something that's unlikely to collide with a site's cookie

class RequestForwarder(RequestHandler):
    
    def get_error_html(self,status,**kwargs): return "<html><body>"+options.errorHTML+"</body></html>"

    def cookie_host(self,checkReal=True,checkURL=True):
        # for cookies telling us what host the user wants
        if checkReal and convert_to_real_host(self.request.host,None): return # if we can get a real host without the cookie, the cookie does not apply to this host
        if enable_adjustDomainCookieName_URL_override and checkURL:
            if self.cookieViaURL: v = self.cookieViaURL
            else:
                v = self.request.arguments.get(adjust_domain_cookieName,None)
                if type(v)==type([]): v=v[-1]
                if v: self.removeArgument(adjust_domain_cookieName,urllib.quote(v))
            if v:
                self.cookieViaURL = v
                if v==adjust_domain_none: return None
                else: return v
        return self.getCookie(adjust_domain_cookieName,adjust_domain_none)
    
    def getCookie(self,cookieName,zeroValue=None):
        # zeroValue is a value that the cookie can be set to so as to "clear" it (because some browsers don't seem to understand JS that clears a cookie)
        for c in self.request.headers.get_list("Cookie"):
            for cc in c.split(';'):
                n,v = cc.strip().split('=',1)
                if n==cookieName:
                    if v==zeroValue: v=None
                    return v
    
    def clearUnrecognisedCookies(self):
        # When serving via adjust_domain_cookieName, on URL box try to save browser memory (and request time) and improve security by deleting cookies set by previous sites.  But can cover only the path=/ ones from here.
        for c in self.request.headers.get_list("Cookie"):
            for cc in c.split(';'):
                n,v = cc.strip().split('=',1)
                if n in [password_cookie_name,adjust_domain_cookieName]: continue # don't do adjust_domain_cookieName unless take into account addCookieFromURL (TODO: but would we ever GET here if that happens?)
                elif n in [htmlmode_cookie_name,"adjustCssSwitch","adjustNoFilter","adjustNoRender","_WA_warnOK"] and v=="1": continue
                for dot in ["","."]:
                    logging.info(n+"="+v+"; Domain="+dot+self.cookieHostToSet()+"; Path=/; Expires=Thu Jan 01 00:00:00 1970")
                    self.add_header("Set-Cookie",n+"="+v+"; Domain="+dot+self.cookieHostToSet()+"; Path=/; Expires=Thu Jan 01 00:00:00 1970")

    def addCookieFromURL(self):
        if self.cookieViaURL: self.add_header("Set-Cookie",adjust_domain_cookieName+"="+urllib.quote(self.cookieViaURL)+"; Path=/; Expires="+cookieExpires)

    def removeArgument(self,argName,value):
        if "&"+argName+"="+value in self.request.uri: self.request.uri=self.request.uri.replace("&"+argName+"="+value,"")
        elif self.request.uri.endswith("?"+argName+"="+value): self.request.uri=self.request.uri[:-len("?"+argName+"="+value)]
        elif "?"+argName+"="+value+"&" in self.request.uri: self.request.uri=self.request.uri.replace("?"+argName+"="+value+"&","?")

    def checkViewsource(self):
        # if URI ends with .viewsource, return True and take it out of the URI and all arguments (need to do this before further processing)
        if not options.viewsource or not self.request.uri.endswith(".viewsource"): return False
        self.request.uri = self.request.uri[:-len(".viewsource")]
        if not self.request.method.lower() in ['get','head']: return True # TODO: unless arguments are taken from both url AND body in that case
        for k,argList in self.request.arguments.items():
            if argList and argList[-1].endswith(".viewsource"):
                argList[-1]=argList[-1][:-len(".viewsource")]
                break
        return True
    
    def cookieHostToSet(self):
        # for the Domain= field of cookies
        for hs in options.host_suffix.split("/"):
            if self.request.host.endswith("."+hs):
                return hs
        return self.request.host
    
    def authenticates_ok(self,host):
        if not options.password: return True
        if options.password_domain and host and not (host==options.password_domain or host.endswith("."+options.password_domain)): return True
        if options.password_domain: self.is_password_domain=True
        # if they said ?p=(password), it's OK and we can
        # give them a cookie with it
        if "p" in self.request.arguments:
            p = self.request.arguments["p"]
            if type(p)==type([]): p=p[0]
            if p == options.password:
                for dot in ["","."]: self.add_header("Set-Cookie",password_cookie_name+"="+urllib.quote(options.password)+"; Domain="+dot+self.cookieHostToSet()+"; Path=/; Expires="+cookieExpires) # (at least in Safari, need BOTH with and without the dot to be sure of setting the domain and all subdomains.  TODO: might be able to skip the dot if not wildcard_dns, here and in the cookie-setting scripts.)
                self.removeArgument("p",options.password)
                return True
        # otherwise if they have the cookie they're OK
        for c in self.request.headers.get_list("Cookie"):
            for cc in c.split(';'):
                if cc.strip().split('=',1)==[password_cookie_name,urllib.quote(options.password)]: return True # TODO: rm this cookie b4 sending to remote server, and don't let remote server clear it
        # otherwise access denied

    SUPPORTED_METHODS = the_supported_methods
    @asynchronous
    def get(self, *args, **kwargs):     return self.doReq()
    @asynchronous
    def head(self, *args, **kwargs):    return self.doReq()
    @asynchronous
    def post(self, *args, **kwargs):    return self.doReq()
    @asynchronous
    def put(self, *args, **kwargs):     return self.doReq()
    @asynchronous
    def delete(self, *args, **kwargs):  return self.doReq()
    @asynchronous
    def patch(self, *args, **kwargs):  return self.doReq()
    @asynchronous
    def options(self, *args, **kwargs): return self.doReq()

    @asynchronous
    def connect(self, *args, **kwargs):
      if options.real_proxy: # support tunnelling (but we can't adjust anything)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        upstream = tornado.iostream.IOStream(s)
        client = self.request.connection.stream
        host, port = self.request.uri.split(':')
        # See note about Tornado versions in the own_server code (if realHost == -1) below
        upstream.connect((host, int(port)), lambda *args:(client.read_until_close(lambda data:writeAndClose(upstream,data),lambda data:upstream.write(data)), upstream.read_until_close(lambda data:writeAndClose(client,data),lambda data:client.write(data)), client.write('HTTP/1.0 200 Connection established\r\n\r\n')))
      else: self.set_status(400),self.myfinish()

    def myfinish(self):
        if hasattr(self,"_finished") and self._finished: return # try to avoid "connection closed" exceptions if browser has already gone away
        try: self.finish()
        except: pass # belt and braces (depends on Tornado version?)

    def redirect(self,redir):
        self.set_status(301)
        self.add_header("Location",redir)
        self.write('<html><body><a href="%s">Redirect</a></body></html>' % redir)
        self.myfinish()

    def addToHeader(self,header,toAdd):
        val = self.request.headers.get(header,"")
        if val: val += ", "
        self.request.headers[header] = val+toAdd

    def proxyFor(self,server):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        upstream = tornado.iostream.IOStream(s)
        client = self.request.connection.stream
        if ':' in server: host, port = server.split(':')
        else: host, port = server, 80
        upstream.connect((host, int(port)),lambda *args:(upstream.read_until_close(lambda data:writeAndClose(client,data),lambda data:client.write(data)),client.read_until_close(lambda data:writeAndClose(upstream,data),lambda data:upstream.write(data))))
        upstream.write(self.request.method+" "+self.request.uri+" "+self.request.version+"\r\n"+"\r\n".join(("%s: %s" % (k,v)) for k,v in (list(h for h in self.request.headers.get_all() if not h[0].lower()=="x-real-ip")+[("X-Real-Ip",self.request.remote_ip)]))+"\r\n\r\n"+self.request.body)

    def answerPing(self):
        # answer a "ping" request from another machine that's using us as a fasterServer
        # Need to make the response short, but still allow keepalive
        self.request.suppress_logging = True
        for h in ["Server","Content-Type"]:
            try: self.clear_header(h)
            except: pass
        self.set_header("Etag","0") # shorter than Tornado's computed one (clear_header won't work with Etag)
        self.write("1") ; self.myfinish()

    def find_real_IP(self):
        if not self.request.remote_ip == options.ipTrustReal: return
        # log (and update Via header) using X-Real-Ip if available
        try: self.request.remote_ip = self.request.connection.confirmed_ip
        except:
            self.request.remote_ip = self.request.headers.get("X-Real-Ip",self.request.remote_ip)
            try: self.request.connection.confirmed_ip = self.request.remote_ip # keep it for keepalive connections (X-Real-Ip is set only on the 1st request)
            except: pass
        try: del self.request.headers["X-Real-Ip"]
        except: pass
    
    def serveRobots(self):
        self.add_header("Content-Type","text/plain")
        self.write("User-agent: *\nDisallow: /\n")
        self.myfinish()

    def serveImage(self,img):
        if not options.renderLog:
            self.request.suppress_logging = True
        self.add_header("Content-Type","image/"+options.renderFormat)
        self.add_header("Last-Modified","Sun, 06 Jul 2008 13:20:05 GMT")
        self.add_header("Expires","Wed, 1 Dec 2036 23:59:59 GMT") # TODO: S2G
        self.write(img) ; self.myfinish()

    def set_htmlonly_cookie(self):
        # Set the cookie according to the value of "pr" entered from the URL box.
        # TODO: option to combine this and other cookie-based settings with enable_adjustDomainCookieName_URL_override so the setting can be bookmarked ?  (some users might want that off however, as an address is different from a setting; in the case of htmlOnly the q= URL can already be bookmarked if can stop it before the redirect)
        if options.htmlonly_mode:
            htmlonly_mode = "pr" in self.request.arguments
            current_setting = htmlmode_cookie_name+"=1" in ';'.join(self.request.headers.get_list("Cookie"))
            if not htmlonly_mode == current_setting:
                if htmlonly_mode: val="1"
                else: val="0"
                self.add_header("Set-Cookie",htmlmode_cookie_name+"="+val+"; Path=/; Expires="+cookieExpires)
    def htmlOnlyMode(self): return options.htmlonly_mode and htmlmode_cookie_name+"=1" in ';'.join(self.request.headers.get_list("Cookie"))
                
    def handle_URLbox_query(self,v):
        self.set_htmlonly_cookie()
        if not v.startswith("http://"):
            if ' ' in v or not '.' in v: v=getSearchURL(v)
            else: v="http://"+v
        if not options.wildcard_dns:
            i = len("http://") ; j = i
            while j<len(v) and v[j] in string.letters+string.digits+'.-': j += 1
            v2 = v[i:j]
            ch = self.cookie_host(checkURL=False)
            if convert_to_requested_host(v2,ch)==v2: # can't do it without changing cookie_host
                if enable_adjustDomainCookieName_URL_override:
                    # do it by URL so they can bookmark it (that is if it doesn't immediately redirect)
                    # (TODO: option to also include the password in this link so it can be passed it around?  and also in the 'back to URL box' link?  but it would be inconsistent because not all links can do that, unless we consistently 302-redirect everything so that they do, but that would reduce the efficiency of the browser's HTTP fetches.  Anyway under normal circumstances we probably won't want users accidentally spreading include-password URLs)
                    vv = adjust_domain_cookieName+'='+urllib.quote(v2)
                    if '?' in v: v += '&'+vv
                    else: v += '?'+vv
                else: self.add_header("Set-Cookie",adjust_domain_cookieName+"="+urllib.quote(v2)+"; Path=/; Expires="+cookieExpires) # (DON'T do this unconditionally, convert_to_requested_host above might see we already have another fixed domain for it)
                # (TODO: if convert_to_requested_host somehow returns a *different* non-default_site domain, that cookie will be lost.  Might need to enforce max 1 non-default_site domain.)
            else: v2 = ch
        else: v2=None # not needed if wildcard_dns
        self.redirect(domain_process(v,v2,True))
    
    def serve_URLbox(self):
        if not options.wildcard_dns: self.clearUnrecognisedCookies() # TODO: optional?
        self.addCookieFromURL()
        self.doResponse2(urlbox_html(self.htmlOnlyMode()),True,False) # TODO: run htmlFilter on it also? (render etc will be done by doResponse2)
    
    def doReq(self):
        debuglog("doReq "+self.request.uri)
        if self.request.uri=="/ping" and self.request.headers.get("User-Agent","")=="ping": return self.answerPing()
        if fasterServer_up:
            return self.proxyFor(options.fasterServer)
        self.find_real_IP()
        # TODO: option to restrict by self.request.remote_ip ?  Slow down heavy users?
        viewSource = self.checkViewsource()
        self.cookieViaURL = None
        realHost = convert_to_real_host(self.request.host,self.cookie_host(checkReal=False)) # don't need checkReal if return value will be passed to convert_to_real_host anyway
        if realHost == -1:
            return self.proxyFor(options.own_server)
            # (TODO: what if it's keep-alive and some browser figures out our other domains are on the same IP and tries to fetch them through the same connection?  is that supposed to be allowed?)
        elif realHost==0 and options.ownServer_if_not_root: realHost=options.own_server # asking by cookie to adjust the same host, so don't proxyFor() it but fetch it normally and adjust it
        
        self.request.valid_for_whois = 1 # (if options.whois, don't whois unless it gets this far, e.g. don't whois any that didn't even match "/(.*)" etc)

        maybeRobots = (not options.robots and self.request.uri=="/robots.txt") # don't actually serveRobots yet, because MIGHT want to pass it to own_server (see below)
        
        self.is_password_domain=False # needed by doResponse2
        if options.password and not options.real_proxy: # whether or not open_proxy, because might still have password (perhaps on password_domain), anyway the doc for open_proxy says "allow running" not "run"
          # First ensure the wildcard part of the host is de-dotted, so the authentication cookie can be shared across hosts.
          # (This is not done if options.real_proxy because we don't want to touch the hostname for that)
          host = self.request.host
          if host:
            if host.endswith(":"+str(options.port)): host=host[:-len(":"+str(options.port))]
            for hs in options.host_suffix.split("/"):
              ohs = "."+hs
              if host.endswith(ohs) and host.index(".")<len(host)-len(ohs):
                if maybeRobots: return self.serveRobots()
                if options.port==80: colPort=""
                else: colPort=":"+str(options.port)
                return self.redirect("http://"+dedot(host[:-len(ohs)])+ohs+colPort+self.request.uri)
          # Now OK to check authentication:
          if not self.authenticates_ok(host):
              if options.auth_error=="http://":
                  if options.own_server: return self.proxyFor(options.own_server)
                  elif maybeRobots: return self.serveRobots()
                  else: options.auth_error = "auth_error set incorrectly (own_server not set)" # see auth_error help (TODO: is it really a good idea to say this HERE?)
              elif maybeRobots: return self.serveRobots()
              elif options.auth_error.startswith("http://"): return self.redirect(options.auth_error)
              self.set_status(401)
              self.write("<html><body>"+options.auth_error+"</body></html>")
              self.myfinish() ; return
        # Authentication is now OK
        self.set_header("Server",program_name[:program_name.index("(c)")].strip())
        # Now check if it's an image request:
        path = self.request.uri
        if path.startswith("http://"): path=urlparse.urlunparse(("","")+urlparse.urlparse(path)[2:]) # (gets here only if options.real_proxy, otherwise we won't have added a handler for paths that don't start with '/')
        img = Renderer.getImage(path)
        if img: return self.serveImage(img)
        # Not an image:
        if not realHost: # default_site(s) not set
            if options.own_server and options.ownServer_if_not_root and len(self.request.path)>1: return self.proxyFor(options.own_server)
            elif maybeRobots: return self.serveRobots()
            # Serve URL box
            v=self.request.arguments.get("q","")
            if v and type(v)==type([]): v=v[0]
            if v: return self.handle_URLbox_query(v)
            else: return self.serve_URLbox()
        if maybeRobots: return self.serveRobots()
        self.addCookieFromURL()
        isProxyRequest = options.real_proxy and realHost == self.request.host
        def fixDNS(val):
            if isProxyRequest: return val
            if val.startswith("http://"): return "http://"+fixDNS(val[7:])
            i=0
            while i<len(val) and val[i] in string.letters+string.digits+'.-': i += 1
            if i<len(val) and val[i]==':': # port no.
                i += 1
                while i<len(val) and val[i] in string.digits: i += 1
            if not i: return val
            r=convert_to_real_host(val[:i],self.cookie_host())
            if r==-1: return val # shouldn't happen
            elif not r: r="" # ensure it's a string
            return r+val[i:]
        converterFlags = []
        for opt,suffix,ext,fmt in [
            (options.pdftotext,pdftotext_suffix,".pdf","pdf"),
            (options.epubtotext,epubtotext_suffix,".epub","epub"),
            (options.epubtozip,epubtozip_suffix,".epub","epub"),
            (options.askBitrate,mp3lofi_suffix,".mp3",None),
            ]:
            if opt and self.request.uri.endswith(suffix) and (self.request.uri.lower()[:-len(suffix)].endswith(ext) or guessCMS(self.request.uri,fmt)):
                self.request.uri = self.request.uri[:-len(suffix)]
                converterFlags.append(True)
            else: converterFlags.append(False)
        if options.default_cookies:
          for defaultCookie in options.default_cookies.split(';'):
            defaultCookie = defaultCookie.strip()
            if defaultCookie.startswith("(") and ")" in defaultCookie: # browser-specific
                if not defaultCookie[1:defaultCookie.index(")")] in self.request.headers.get("User-Agent",""): continue
                defaultCookie=defaultCookie[defaultCookie.index(")")+1:]
            # add if a cookie of that name is not already set
            dcName,dcValue=defaultCookie.strip().split('=',1)
            if not self.getCookie(dcName): self.request.headers.add("Cookie",defaultCookie)
        if self.request.headers.get_list("Cookie"):
            # some sites require them all in one header
            ck = "; ".join(self.request.headers.get_list("Cookie"))
            self.request.headers["Cookie"]=ck
        for v in self.request.headers.get_list("Referer"):
            if v: self.request.headers["Referer"] = fixDNS(v)
        if "http://" in self.request.uri[1:]: # xyz?q=http://... stuff
            u=self.request.uri.split("http://")
            for i in range(1,len(u)): u[i]=fixDNS(u[i])
            self.request.uri="http://".join(u)
        if self.request.uri.startswith("http://"): # will reach here only if options.real_proxy
            if not self.request.headers["Host"]: self.request.headers["Host"] = urlparse.urlparse(self.request.uri).netloc
            self.request.uri = urlparse.urlunparse(("","")+urlparse.urlparse(self.request.uri)[2:])
            try: del self.request.headers['Proxy-Connection']
            except: pass
        else: self.request.headers["Host"]=realHost
        try: del self.request.headers["Accept-Encoding"] # we'd better re-do that one
        except: pass
        if options.via:
            v = self.request.version
            if v.startswith("HTTP/"): v=v[5:]
            self.addToHeader("Via",v+" "+convert_to_via_host(self.request.host)+" ("+program_name[:program_name.index("(c)")].strip()+")")
            self.addToHeader("X-Forwarded-For",self.request.remote_ip)
        self.sendRequest(converterFlags,viewSource,isProxyRequest,follow_redirects=False) # (DON'T follow redirects - browser needs to know about them!)
    def sendRequest(self,converterFlags,viewSource,isProxyRequest,follow_redirects):
        http = AsyncHTTPClient()
        body = self.request.body
        if not body: body = None # required by some Tornado versions
        # TODO: basic authentication? auth_username, auth_password
        self.urlToFetch = "http://"+self.request.headers["Host"]+self.request.uri
        # TODO: try del self.request.headers['Connection'] ? but check it can't mess up Tornado (may have to put it back before write()s)
        http.fetch(self.urlToFetch,
                   use_gzip=not hasattr(self,"avoid_gzip"),
                   method=self.request.method, headers=self.request.headers, body=body,
                   callback=lambda r:self.doResponse(r,converterFlags,viewSource,isProxyRequest),follow_redirects=follow_redirects)
    def doResponse(self,response,converterFlags,viewSource,isProxyRequest):
        debuglog("doResponse "+self.request.uri)
        do_pdftotext,do_epubtotext,do_epubtozip,do_mp3 = converterFlags
        do_domain_process = do_html_process = do_js_process = True
        do_json_process = do_css_process = False
        charset = "utf-8" # by default
        if not response.code or response.code==599:
            # (some Tornado versions don't like us copying a 599 response)
            try: error = str(response.error)
            except: error = "Gateway timeout or something"
            if "incorrect data check" in error and not hasattr(self,"avoid_gzip"):
                # Some versions of the GWAN server can send NULL bytes at the end of gzip data.  Retry without requesting gzip.
                self.avoid_gzip = True
                return self.sendRequest(converterFlags,viewSource,isProxyRequest,False)
            self.set_status(504)
            return self.doResponse2(("<html><body>%s</body></html>" % error),True,False)
        if viewSource:
            def txt2html(t): return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
            def h2html(h): return "<br>".join("<b>"+txt2html(k)+"</b>: "+txt2html(v) for k,v in sorted(h.get_all()))
            return self.doResponse2("<html><body><a href=\"#1\">Headers sent</a> | <a href=\"#2\">Headers received</a> | <a href=\"#3\">Page source</a><a name=\"1\"></a><h2>Headers sent</h2>"+h2html(self.request.headers)+"<a name=\"2\"></a><h2>Headers received</h2>"+h2html(response.headers)+"<a name=\"3\"></a><h2>Page source</h2>"+txt2html(response.body),True,False)
        headers_to_add = []
        if (do_pdftotext or do_epubtotext or do_epubtozip or do_mp3) and not response.headers.get("Location","") and response.headers.get("Content-type","").startswith("text/"):
          # We thought we were going to get a PDF etc that could be converted, but it looks like they just sent more HTML (perhaps a "which version of the PDF did you want" screen)
          do_pdftotext=do_epubtotext=do_epubtozip=do_mp3=False
        cookie_host = self.cookie_host()
        for name,value in response.headers.get_all():
          if name.lower() in ["connection","content-length","content-encoding","transfer-encoding","etag","server","alternate-protocol"]: continue # we'll do our own connection type etc
          # TODO: WebSocket (and Microsoft SM) gets the client to say 'Connection: Upgrade' with a load of Sec-WebSocket-* headers, check what Tornado does with that
          if (do_pdftotext or do_epubtotext) and name.lower() in ["content-disposition","content-type"]: continue # we're re-doing these also
          elif do_epubtozip and name.lower()=="content-disposition" and value.replace('"','').endswith(".epub"):
            epub = value.rfind(".epub")
            value=value[:epub]+".zip"+value[epub+5:]
          elif "location" in name.lower():
            old_value_1 = value
            if not isProxyRequest:
                value=domain_process(value,cookie_host,True)
                offsite = (value==old_value_1 and "http://" in value)
            else: offsite = False
            old_value_2 = value
            if do_pdftotext: # is it still going to be pdf?
              if value.lower().endswith(".pdf") or guessCMS(value,"pdf"): value += pdftotext_suffix
            if do_epubtotext:
              if value.lower().endswith(".epub") or guessCMS(value,"epub"): value += epubtotext_suffix
            if do_epubtozip:
              if value.lower().endswith(".epub") or guessCMS(value,"epub"): value += epubtozip_suffix
            if do_mp3:
              if value.lower().endswith(".mp3"): value += mp3lofi_suffix
            if offsite and not old_value_2==value:
                # ouch, we're not going to be able to do it this way because it's redirecting to somewhere we can't domain-proxy for.  But we could follow the redirects ourselves to do the conversion:
                return self.sendRequest(converterFlags,viewSource,isProxyRequest,follow_redirects=True)
                # TODO: if that sendRequest results in HTML, overriding the do_... options, the browser will end up with an incorrect idea of the current address; might want to detect this and give the user the unchanged Location: header
            else: do_pdftotext=do_epubtotext=do_epubtozip=do_mp3=False # do not attempt to media-process any body that is sent with this Location: redirect (if it's just a copy of the URL then running it through ebook-convert might hold things up unnecessarily)
            if cookie_host and self.request.path=="/" and value.startswith("http") and not value.startswith("http://"+cookie_host+"/"):
                # This'll be a problem.  If the user is requesting / and the site's trying to redirect off-site, how do we know that the user isn't trying to get back to the URL box (having forgotten to clear the cookie) and now can't possibly do so because / always results in an off-site Location redirect ?
                # (The same thing can occur if offsite is False but we're redirecting to one of our other domains, hence we use the value.startswith condition instead of the 'offsite' flag; the latter is true only if NONE of our domains can do it.)
                # (DON'T just do this for ANY offsite url when in cookie_host mode - that could mess up images and things.  (Could still mess up images etc if they're served from / with query parameters; for now we're assuming path=/ is a good condition to do this.  The whole cookie_host thing is a compromise anyway; wildcard_dns is better.))
                if offsite: reason="which this adjuster is not currently set to adjust"
                else: reason="which will be adjusted at %s (not here)" % (value[len("http://"):(value+"/").index('/',len("http://"))],)
                return self.doResponse2(("<html><body>The server is redirecting you to <a href=\"%s\">%s</a> %s.</body></html>" % (value,old_value_1,reason)),True,False) # and 'Back to URL box' link will be added
          elif "set-cookie" in name.lower() and not isProxyRequest:
            value=cookie_domain_process(value,cookie_host)
          headers_to_add.append((name,value))
          if name.lower()=="content-type":
            if do_epubtozip: value="application/zip"
            value=value.lower()
            if not options.askBitrate: do_mp3 = (value=="audio/mpeg" or (value.startswith("application/") and response.headers.get("Content-Disposition","").replace('"','').endswith('.mp3'))) # else do only if was set in converterFlags
            do_domain_process = ("html" in value or "css" in value or "javascript" in value or "json" in value or self.request.path.endswith(".js") or self.request.path.endswith(".css")) # and hope the server doesn't incorrectly say text/plain or something for a CSS or JS that doesn't end with that extension
            do_js_process = ("html" in value or "javascript" in value or self.request.path.endswith(".js"))
            do_html_process = ("html" in value) # TODO: configurable?
            do_json_process = ("json" in value)
            do_css_process = ("css" in value or self.request.path.endswith(".css"))
            if "charset=" in value:
                charset=extractCharsetEquals(value)
                if do_html_process: headers_to_add[-1]=((name,value.replace(charset,"utf-8"))) # we'll be converting it
            elif do_html_process: headers_to_add[-1]=((name,value+"; charset=utf-8")) # ditto (don't leave as latin-1)
          # TODO: if there's no content-type header, send one anyway, with a charset
        self.set_status(response.code) # (not before here! as might return doResponse2 above which will need status 200.  Redirect without Location gets "unknown error 0x80072f76" on Pocket IE 6.)
        added = {}
        for name,value in headers_to_add:
          if name in added: self.add_header(name,value)
          else: self.set_header(name,value) # overriding any Tornado default
          added[name]=1
        body = response.body
        if not body:
            self.myfinish() ; return # might just be a redirect (TODO: if it's not, set type to text/html and report error?)
        if do_html_process:
            # Normalise the character set
            charset2,tagStart,tagEnd = get_httpequiv_charset(body)
            if charset2:
                charset=charset2 # override server header (TODO: is this always correct?)
                body = body[:tagStart]+body[tagEnd:] # delete that META tag because we're changing the charset
            if body.startswith('<?xml version="1.0" encoding'): body = '<?xml version="1.0"'+body[body.find("?>"):] # TODO: honour THIS 'encoding'?  anyway remove it because we've changed it to utf-8 (and if we're using LXML it would get a 'unicode strings with encoding not supported' exception)
            if charset=="gb2312": charset="gb18030" # 18030 is a superset of 2312, and some pages say 2312 for backward compatibility with old software when they're actually 18030 (most Chinese software treats both as equivalent, but not all Western software does)
            try: "".decode(charset)
            except: charset="latin-1" # ?? (unrecognised charset name)
            if not charset=="utf-8": body=body.decode(charset,'replace').encode('utf-8')
        if do_pdftotext or do_epubtotext:
            self.set_header("Content-Type","text/plain; charset=utf-8")
            self.set_header("Content-Disposition","attachment; filename=\"%s\"" % (self.request.uri[self.request.uri.rfind("/")+1:self.request.uri.rfind(".")]+".txt"))
            # (Pocket IE on Windows Mobile doesn't always obey Content-Disposition, but Opera Mini etc should do it)
            import tempfile
            if do_pdftotext: ext="pdf"
            elif do_epubtotext: ext="epub"
            else: ext="" # shouldn't get here
            def remove_blanks_add_utf8_BOM(out): return '\xef\xbb\xbf'+"\n".join([x for x in out.replace("\r","").split("\n") if x])
            # first, is the result of pdftotext etc cached?
            ktkey = (self.request.host, self.request.uri)
            if kept_tempfiles.get(ktkey,None)==1:
                # This conversion is in progress on another request (TODO: check it didn't somehow fail without updating kept_tempfiles?)
                def tryLater():
                    try: txt=open(kept_tempfiles[ktkey]).read()
                    except: txt = None
                    if txt:
                        self.write(remove_blanks_add_utf8_BOM(txt))
                        self.myfinish()
                    else: IOLoop.instance().add_timeout(time.time()+1,lambda *args:tryLater())
                return tryLater()
            if not ktkey in kept_tempfiles:
                kept_tempfiles[ktkey] = 1 # in progress
            try: txt=open(kept_tempfiles[ktkey]).read()
            except: txt = None
            if txt:
                self.write(remove_blanks_add_utf8_BOM(txt))
                self.myfinish() ; return
            # not cached - need to generate
            f=tempfile.NamedTemporaryFile(delete=False,suffix="."+ext) # Python 2.6+
            f.write(body) ; f.close()
            def tryDel(k):
                try: del kept_tempfiles[k]
                except: pass
            def unlinkLater(k,fn):
                kept_tempfiles[k] = fn # it's ready for now
                IOLoop.instance().add_timeout(time.time()+options.pdfepubkeep,lambda *args:(tryDel(k),os.unlink(fn)))
            if do_pdftotext: runFilter(("pdftotext -enc UTF-8 -nopgbrk \"%s\" -" % f.name),"",(lambda out:(unlinkLater(ktkey,f.name),self.write(remove_blanks_add_utf8_BOM(out)),self.myfinish())), False)
            elif do_epubtotext:
                def ebookCallback(self,fn):
                    try: txt = open(fn+".txt").read()
                    except: txt = "Unable to read ebook-convert's output"
                    unlinkLater(ktkey,fn+".txt")
                    unlinkLater(0,fn)
                    self.write(remove_blanks_add_utf8_BOM(txt))
                    self.myfinish()
                runFilter(("ebook-convert %s %s.txt" % (f.name,f.name)),"",(lambda out:ebookCallback(self,f.name)), False)
            return
        if do_domain_process and not isProxyRequest: body = domain_process(body,cookie_host) # first, so filters to run and scripts to add can mention new domains without these being redirected back
        # Must also do things like 'delete' BEFORE the filters, especially if lxml is in use and might change the code so the delete patterns aren't recognised
        if not self.checkBrowser(options.deleteOmit):
            for d in options.delete:
                body=re.sub(d,"",body)
            if options.delete_doctype:
                body=re.sub("^<![dD][oO][cC][tT][yY][pP][eE][^>]*>","",body,1)
        if do_js_process: body = js_process(body,self.urlToFetch)
        # OK to change the code now:
        adjustList = []
        if self.htmlOnlyMode(): adjustList.append(StripJSEtc())
        if (options.pdftotext or options.epubtotext or options.epubtozip or options.askBitrate) and (do_html_process or (do_json_process and options.htmlJson)):
            # Add PDF links BEFORE the external filter, in case the external filter is broken and we have trouble parsing the result
            if do_html_process:
                adjustList.append(AddConversionLinks())
            else:
                ctl = find_HTML_in_JSON(body)
                for i in range(1,len(ctl),2):
                    ctl[i] = json_reEscape(add_conversion_links(ctl[i]))
                body = "".join(ctl)
        if options.headAppendCSS:
          # remove !important from other stylesheets
          important = re.compile("! *important")
          if (do_html_process or (do_css_process and not self.urlToFetch == options.headAppendCSS)) and re.search(important,body):
            if do_css_process: body=re.sub(important,"",body)
            else: adjustList.append(transform_in_selected_tag("style",lambda s:re.sub(important,"",s)))
        if adjustList: body = HTML_adjust_svc(body,adjustList)
        callback = lambda out:self.doResponse2(out,do_html_process,do_json_process)
        skipFilter = options.htmlFilterName and "adjustNoFilter=1" in ';'.join(self.request.headers.get_list("Cookie"))
        if do_html_process and options.htmlFilter and not skipFilter:
            if options.htmlText: runFilterOnText(options.htmlFilter,find_text_in_HTML(body),callback)
            else: runFilter(options.htmlFilter,body,callback)
        elif do_json_process and options.htmlJson and options.htmlFilter and not skipFilter:
            if options.htmlText: htmlFunc = find_text_in_HTML
            else: htmlFunc = None
            runFilterOnText(options.htmlFilter,find_HTML_in_JSON(body,htmlFunc),callback,True)
        elif do_mp3 and options.bitrate:
            runFilter("lame --quiet --mp3input -m m --abr %d - -o -" % options.bitrate,body,callback,False) # -m m = mono (TODO: optional?)
        else: callback(body)
    def doResponse2(self,body,do_html_process,do_json_process):
        debuglog("doResponse2 "+self.request.uri)
        # 2nd stage (domain change and external filter
        # has been run) - now add scripts etc, and render
        canRender = options.render and (do_html_process or (do_json_process and options.htmlJson)) and not self.checkBrowser(options.renderOmit)
        jsCookieString = ';'.join(self.request.headers.get_list("Cookie"))
        if do_html_process: body = html_additions(body,self.checkBrowser(options.cssNameReload),self.cookieHostToSet(),jsCookieString,canRender,self.cookie_host(),self.is_password_domain)
        callback = lambda out:self.doResponse3(out)
        if canRender and not "adjustNoRender=1" in jsCookieString:
            if do_html_process: func = find_text_in_HTML
            else: func=lambda body:find_HTML_in_JSON(body,find_text_in_HTML)
            debuglog("runFilterOnText Renderer")
            runFilterOnText(lambda t:Renderer.getMarkup(t.decode('utf-8')).encode('utf-8'),func(body),callback,not do_html_process,chr(0))
        else: callback(body)
    def doResponse3(self,body):
        # 3rd stage (rendering has been done)
        debuglog("doResponse3 (len=%d)" % len(body))
        self.write(body)
        self.myfinish()
    def checkBrowser(self,blist):
        ua = self.request.headers.get("User-Agent","")
        return any(b in ua for b in blist)

kept_tempfiles = {} # TODO: delete any outstanding kept_tempfiles.values() on server interrupt

def getSearchURL(q):
    if not options.search_sites: return urllib.quote(q) # ??
    def site(s,q): return s.split()[0]+urllib.quote(q)
    splitq = q.split(None,1)
    if len(splitq)==2 and len(options.search_sites)>1:
      cmd,rest = splitq
      for s in options.search_sites:
        t = s.split()[1]
        if "(" in t and ")" in t:
            if cmd==t[t.index("(")+1:t.index(")")] or cmd==t.replace("(","").replace(")",""): return site(s,rest)
        elif cmd==t: return site(s,rest)
    return site(options.search_sites[0],q)
def searchHelp():
    if not options.search_sites: return ""
    elif len(options.search_sites)==1: return " (or enter search terms)"
    else: return " or enter search terms, first word can be "+", ".join([x.split(None,1)[1] for x in options.search_sites])
def urlbox_html(htmlonly_checked):
    r = '<html><head><title>Web Adjuster start page</title><meta name="viewport" content="width=device-width"></head><body><form action="/">Website to adjust: <input type="text" name="q"><input type="submit" value="Go">'+searchHelp()
    if htmlonly_checked: htmlonly_checked=' checked="checked"'
    else: htmlonly_checked = ""
    if options.htmlonly_mode: r += '<br><input type="checkbox" name="pr"'+htmlonly_checked+'> HTML-only mode'
    return r+'</form><script language="javascript"><!--\ndocument.forms[0].q.focus();\n//--></script></body></html>'

def runFilter(cmd,text,callback,textmode=True):
    # runs shell command 'cmd' on input 'text' in a new
    # thread, then gets Tornado to call callback(output)
    # If 'cmd' is not a string, assumes it's a function
    # to call (no new thread necessary, TODO: Jython/SMP)
    # this is for using runFilterOnText with an internal
    # callable such as the Renderer.
    if not type(cmd)==type(""):
        # return callback(cmd(text))
        # slightly more roundabout version to give watchdog ping a chance to work between cmd and callback:
        out = cmd(text)
        return IOLoop.instance().add_timeout(time.time(),lambda *args:callback(out))
    def subprocess_thread():
        sp=subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,universal_newlines=textmode) # TODO: check shell=True won't throw error on Windows
        out,err = sp.communicate(text)
        IOLoop.instance().add_callback(lambda *args:callback(out))
    threading.Thread(target=subprocess_thread,args=()).start()

def runBrowser(*args):
    def browser_thread():
        os.system(options.browser) ; stopServer()
    threading.Thread(target=browser_thread,args=()).start()

def stopServer(*args): IOLoop.instance().add_callback(lambda *args:IOLoop.instance().stop())
    
def json_reEscape(x):
    try: x=x.decode('utf-8')
    except: pass
    return json.dumps(x)[1:-1] # omit ""s (necessary as we might not have the whole string here)
    
def runFilterOnText(cmd,codeTextList,callback,escape=False,separator=None):
    # codeTextList is a list of alternate [code, text, code, text, code]. Any 'text' element can itself be a list of [code, text, code] etc.
    # Pick out all the 'text' elements, separate them, send to the filter, and re-integrate assuming separators preserved
    # If escape is True, on re-integration escape anything that comes under a top-level 'text' element so they can go into JSON strings (see find_HTML_in_JSON)
    if not separator: separator = options.separator
    if not separator: separator="\n"
    def getText(l,replacements=None,codeAlso=False,alwaysEscape=False):
        isTxt = False ; r = [] ; rLine = 0
        def maybeEsc(x):
            if escape and replacements and (isTxt or alwaysEscape): return json_reEscape(x)
            else: return x
        for i in l:
            if isTxt:
                if type(i)==type([]):
                  if i: # (skip empty lists)
                    if replacements==None: repl=None
                    else:
                        cl = countItems(i) # >= 1 (site might already use separator)
                        repl=replacements[rLine:rLine+cl]
                        rLine += cl
                    r += getText(i,repl,codeAlso,True)
                elif replacements==None: r.append(maybeEsc(i))
                else:
                    cl = countItems(["",i]) # >= 1 (site might already use separator)
                    r.append(maybeEsc(separator.join(replacements[rLine:rLine+cl])))
                    rLine += cl
            elif codeAlso: r.append(maybeEsc(i))
            isTxt = not isTxt
        return r
    def countItems(l): return len(separator.join(getText(l)).split(separator))
    text = getText(codeTextList)
    toSend = separator.join(text)
    if options.separator:
        toSend=separator+toSend+separator
        sortout = lambda out:out.split(separator)[1:-1]
    else: sortout = lambda out:out.split(separator)
    runFilter(cmd,toSend,lambda out:callback("".join(getText(codeTextList,sortout(out),True))))

def extractCharsetEquals(value):
    charset=value[value.index("charset=")+len("charset="):]
    if ';' in charset: charset=charset[:charset.index(';')]
    return charset

def get_httpequiv_charset(htmlStr):
    class Finished:
        def __init__(self,charset=None,tagStart=None,tagEnd=None):
            self.charset,self.tagStart,self.tagEnd = charset,tagStart,tagEnd
    class Parser(HTMLParser): # better not use LXML yet...
        def handle_starttag(self, tag, attrs):
            if tag=="body": raise Finished() # only interested in head
            attrs = dict(attrs)
            if tag=="meta" and attrs.get("http-equiv",attrs.get("http_equiv","")).lower()=="content-type" and "charset=" in attrs.get("content","").lower():
                charset = extractCharsetEquals(attrs['content'].lower())
                line,offset = self.getpos() ; knownLine = 1 ; knownLinePos = 0
                while line>knownLine:
                    knownLine += 1
                    knownLinePos=htmlStr.find('\n',knownLinePos)+1
                tagStart = knownLinePos + offset
                tagEnd = htmlStr.index(">",tagStart)+1
                raise Finished(charset,tagStart,tagEnd)
        def handle_endtag(self, tag):
            if tag=="head": raise Finished() # as above
    parser = Parser()
    htmlStr = fixHTML(htmlStr)
    try:
        parser.feed(htmlStr) ; parser.close()
    except UnicodeDecodeError: pass
    except HTMLParseError: pass
    except Finished,e: return e.charset,e.tagStart,e.tagEnd
    return None,None,None

pdftotext_suffix = epubtotext_suffix = ".TxT" # TODO: what if a server uses .pdf.TxT or .epub.TxT ?
mp3lofi_suffix = "-lOfI.mP3"
epubtozip_suffix = ".ZiP" # TODO: what if a server uses .epub.ZiP ?
class AddConversionLinks:
    def init(self,parser):
        self.parser = parser
        self.gotPDF=self.gotEPUB=self.gotMP3=None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag=="a" and "href" in attrs:
            l = attrs["href"].lower()
            if l.startswith("http://"):
                if not options.wildcard_dns and not options.real_proxy and not url_is_ours(l): return # "offsite" link, can't process (TODO: unless we send it to ourselves via an alternate syntax)
                # TODO: should also check isProxyRequest rather than just relying on options.real_proxy
                # TODO: (if don't implement processing the link anyway) insert explanatory text for why an alternate link wasn't provided?
            elif ":" in l and l.index(":")<l.find("/"): return # non-HTTP protocol - can't do (TODO: unless we do https, or send the link to ourselves via an alternate syntax)
            if l.endswith(".pdf") or guessCMS(l,"pdf"):
                self.gotPDF = attrs["href"]
            if l.endswith(".epub") or guessCMS(l,"epub"):
                self.gotEPUB = attrs["href"]
            if l.endswith(".mp3"):
                self.gotMP3 = attrs["href"]
    def handle_endtag(self, tag):
        if tag=="a" and ((self.gotPDF and options.pdftotext) or (self.gotEPUB and (options.epubtozip or options.epubtotext)) or (self.gotMP3 and options.bitrate and options.askBitrate)):
            linksToAdd = []
            if self.gotPDF: linksToAdd.append("<a href=\"%s%s\">text</a>" % (self.gotPDF,pdftotext_suffix))
            elif self.gotEPUB:
                if options.epubtotext: linksToAdd.append("<a href=\"%s%s\">text</a>" % (self.gotEPUB,epubtotext_suffix))
                if options.epubtozip: linksToAdd.append("<a href=\"%s%s\">zip</a>" % (self.gotEPUB,epubtozip_suffix))
            elif self.gotMP3: linksToAdd.append("<a href=\"%s%s\">lo-fi</a>" % (self.gotMP3,mp3lofi_suffix))
            if linksToAdd: self.parser.addDataFromTagHandler(" ("+", ".join(linksToAdd)+") ")
            self.gotPDF=self.gotEPUB=self.gotMP3=None
    def handle_data(self,data): pass
def add_conversion_links(h):
    # (wrapper for when we can't avoid doing a special-case HTMLParser for it)
    return HTML_adjust_svc(h,[AddConversionLinks()],can_use_LXML=False) # False because we're likely dealing with a fragment inside JSON, not a complete HTML document

class StripJSEtc:
    # TODO: HTML_adjust_svc might need to do handle_entityref and handle_charref to catch those inside scripts etc
    def init(self,parser):
        self.parser = parser
        self.suppressing = False
    def handle_starttag(self, tag, attrs):
        if tag=="img":
            self.parser.addDataFromTagHandler(dict(attrs).get("alt",""),1)
            return True
        elif tag in ['script','style']:
            self.suppressing = True ; return True
        else: return self.suppressing or tag in ['link','noscript']
        # TODO: remove style= attribute on other tags? (or only if it refers to a URL?)
        # TODO: what about event handler attributes, and javascript: URLs
    def handle_endtag(self, tag):
        if tag in ['script','style']:
            self.suppressing = False ; return True
        elif tag=='noscript': return True
        else: return self.suppressing
    def handle_data(self,data):
        if self.suppressing: return ""

def guessCMS(url,fmt):
    # (TODO: more possibilities for this?  Option to HEAD all urls and return what they resolve to? but fetch-ahead might not be a good idea on all sites)
    return fmt and options.guessCMS and "?" in url and "format="+fmt in url.lower()

def check_LXML():
    # Might not find ALL problems with lxml installations, but at least we can check some basics
    global etree, StringIO
    try:
        from lxml import etree
        from StringIO import StringIO # not cStringIO, need Unicode
        etree.HTMLParser(target=None) # works on lxml 2.3.2
    except ImportError:
        sys.stderr.write("LXML library not found - ignoring useLXML option\n")
        options.useLXML = False
    except TypeError: # no target= option in 1.x
        sys.stderr.write("LXML library too old - ignoring useLXML option\n")
        options.useLXML = False

def HTML_adjust_svc(htmlStr,adjustList,can_use_LXML=True):
    # Runs an HTMLParser on htmlStr, calling multiple adjusters on adjustList.
    # Faster than running the HTMLParser separately for each adjuster,
    # but still limited (find_text_in_HTML is still separate)
    if options.useLXML and can_use_LXML: return HTML_adjust_svc_LXML(htmlStr,adjustList)
    class Parser(HTMLParser):
        def handle_starttag(self, tag, att):
            for l in adjustList:
                if l.handle_starttag(tag,att):
                    return self.suppressTag()
        def suppressTag(self):
            pos = self.getBytePos()
            self.out.append(htmlStr[self.lastStart:pos])
            self.lastStart = htmlStr.index(">",pos)+1
            return True
        def handle_endtag(self, tag):
            for l in adjustList:
                if l.handle_endtag(tag):
                    return self.suppressTag()
        def addDataFromTagHandler(self,data,replacesTag=0):
            # (if replacesTag=1, tells us the tag will be suppressed later; does not actually do it now. C.f. the lxml version.)
            pos = self.getBytePos()
            if not replacesTag: pos = htmlStr.index(">",pos)+1 # AFTER the tag (assumes tag not suppressed)
            self.out.append(htmlStr[self.lastStart:pos])
            self.out.append(data) # (assumes none of the other handlers will want to process it)
            self.lastStart = pos
        def getBytePos(self):
            line,offset = self.getpos()
            while line>self.knownLine:
                self.knownLine += 1
                self.knownLinePos=htmlStr.find('\n',self.knownLinePos)+1
            return self.knownLinePos + offset
        def handle_data(self,data):
            if not data: return
            oldData = data
            for l in adjustList:
                data0 = data
                data = l.handle_data(data)
                if data==None: data = data0
            dataStart = self.getBytePos()
            self.out.append(htmlStr[self.lastStart:dataStart])
            self.out.append(data)
            self.lastStart = dataStart+len(oldData)
    parser = Parser()
    for l in adjustList: l.init(parser)
    parser.out = [] ; parser.lastStart = 0
    parser.knownLine = 1 ; parser.knownLinePos = 0
    htmlStr = fixHTML(htmlStr)
    numErrs = 0
    debug = False # change to True if needed
    while numErrs < 20: # TODO: customise this limit?
        try:
            parser.feed(htmlStr) ; break
        except UnicodeDecodeError: pass # see comments in find_text_in_HTML
        except HTMLParseError: pass
        # try dropping just 1 byte
        parser.out.append(htmlStr[parser.lastStart:parser.lastStart+1])
        parser2 = Parser()
        for l in adjustList: l.parser=parser2 # TODO: makes assumptions about how init() works
        if debug: parser.out.append(" (Debugger: HTML_adjust_svc skipped a character) ")
        htmlStr = htmlStr[parser.lastStart+1:]
        parser2.out = parser.out ; parser2.lastStart = 0
        parser2.knownLine = 1 ; parser2.knownLinePos = 0
        parser = parser2
        numErrs += 1
    try: parser.close()
    except UnicodeDecodeError: pass
    except HTMLParseError: pass
    if debug: parser.out.append("<!-- Debugger: HTML_adjust_svc ended here -->")
    parser.out.append(htmlStr[parser.lastStart:])
    if type(htmlStr)==type(u""):
        return latin1decode(u"".join(parser.out))
    else: return "".join(parser.out)

def lxmlEncodeTag(tag,att):
    def encAtt(a,v):
        if v:
            v=v.replace('&','&amp;').replace('"','&quot;')
            if not re.search('[^A-Za-z_]',v): return a+'='+v # no quotes needed (TODO: option to keep it valid?)
            return a+'="'+v+'"'
        else: return a
    return "<"+tag+"".join((" "+encAtt(a,v)) for a,v in att.items())+">"

html_tags_not_needing_ends = set(['area','base','basefont','br','hr','input','img','link','meta'])

def HTML_adjust_svc_LXML(htmlStr,adjustList):
    class Parser:
        def start(self, tag, att):
            att=dict((k,v.encode('utf-8')) for k,v in dict(att).items()) # so latin1decode doesn't pick up on it
            i = len(self.out)
            for l in adjustList:
                if l.handle_starttag(tag,att):
                    return # want the tag to be suppressed
            self.out.insert(i,lxmlEncodeTag(tag,att))
        def end(self, tag):
            i = len(self.out)
            for l in adjustList:
                if l.handle_endtag(tag): return
            if tag not in html_tags_not_needing_ends:
                self.out.insert(i,"</"+tag+">")
        def addDataFromTagHandler(self,data,_=0):
            self.out.append(data)
        def data(self,unidata):
            data = unidata.encode('utf-8')
            oldData = data
            for l in adjustList:
                data0 = data
                data = l.handle_data(data)
                if data==None: data = data0
            self.out.append(data)
        def comment(self,text): # TODO: option to keep these or not?  some of them could be MSIE conditionals
            self.out.append("<!--"+text+"-->")
        def close(self): pass
    parser = Parser() ; parser.out = []
    for l in adjustList: l.init(parser)
    lparser = etree.HTMLParser(target=parser)
    etree.parse(StringIO(htmlStr.decode('utf-8')), lparser)
    return "".join(parser.out)

def transform_in_selected_tag(intag,transformFunc):
    # assumes intag is closed and not nested, e.g. style
    # also assumes transformFunc doesn't need to know about entity references etc (it's called for the data between them)
    class Adjustment:
        def init(self,parser):
            self.intag = False
        def handle_starttag(self, tag, attrs):
            self.intag=(tag==intag)
        def handle_endtag(self, tag):
            self.intag = False
        def handle_data(self,data):
            if self.intag:
                return transformFunc(data)
    return Adjustment()

def fixHTML(htmlStr):
    # some versions of Python's HTMLParser can't cope with missing spaces between attributes:
    if re.search(r'<[^>]*?= *"[^"]*"[A-Za-z]',htmlStr):
        htmlStr = re.sub(r'(= *"[^"]*")([A-Za-z])',r'\1 \2',htmlStr) # (TODO: that might match cases outside of tags)
    # (TODO: don't need to do the above more than once on same HTML)
    
    # HTMLParser bug in some Python libraries: it can take UTF-8 bytes, but if both non-ASCII UTF-8 and entities (named or numeric) are used in the same attribute of a tag, we get a UnicodeDecodeError on the UTF-8 bytes.
    # HTMLParser's unescape()'s replaceEntities() is inconsistent about whether it returns string or Unicode, and the coercion goes wrong.
    # That happens for example when &quot; or &#34; is used in the attribute along with UTF-8 bytes.
    # It's OK if the entire HTML document is pre-decoded, but that means we can't "stop before" any charset errors; errors are either ignored/replaced or we give up on the whole document.
    # Moreover, if we're being called by get_httpequiv_charset then we might not have UTF-8.
    # Workaround: do a .decode using 'latin1', which maps bytes to Unicode characters in a 'dumb' way.
    # (This is reversed by latin1decode.  If left as byte string, latin1decode does nothing.)
    if re.search(r'<[^>]*?"[^"]*?&[^"]*?[^ -~]',htmlStr) or re.search(r'<[^>]*?"[^"]*[^ -~][^"]*?&',htmlStr): # looks like there are entities and non-ASCII in same attribute value
        htmlStr = htmlStr.decode('latin1')
    
    return htmlStr
def latin1decode(htmlStr):
    # back to bytes (hopefully UTF-8)
    if type(htmlStr)==type(u""):
        return htmlStr.encode('latin1')
    else: return htmlStr

def find_text_in_HTML(htmlStr): # returns a codeTextList; encodes entities in utf-8
    if options.useLXML:
        return LXML_find_text_in_HTML(htmlStr)
    import htmlentitydefs
    class Parser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag in options.leaveTags:
                self.ignoreData=True
        def handle_endtag(self, tag):
            if tag in options.leaveTags:
                self.ignoreData=False
            # doesn't check for nesting or balancing
            # (documented limitation)
        def handle_data(self,data,datalen=None):
            if self.ignoreData or not data.strip():
                return # keep treating it as code
            if datalen==None: data = latin1decode(data)
            line,offset = self.getpos()
            while line>self.knownLine:
                self.knownLine += 1
                self.knownLinePos=htmlStr.find('\n',self.knownLinePos)+1
            dataStart = self.knownLinePos + offset
            self.codeTextList.append(latin1decode(htmlStr[self.lastCodeStart:dataStart]))
            self.codeTextList.append(data)
            if datalen==None: datalen = len(data) # otherwise we're overriding it for entity refs etc
            self.lastCodeStart = dataStart+datalen
        def handle_entityref(self,name):
            if name in htmlentitydefs.name2codepoint:
                self.handle_data(unichr(htmlentitydefs.name2codepoint[name]).encode('utf-8'),len(name)+2)
            # else leave the entity ref as-is
        def handle_charref(self,name):
            if name.startswith('x'): self.handle_data(unichr(int(name[1:],16)).encode('utf-8'),len(name)+3)
            else: self.handle_data(unichr(int(name)).encode('utf-8'),len(name)+3)
    parser = Parser()
    parser.codeTextList = [] ; parser.lastCodeStart = 0
    parser.knownLine = 1 ; parser.knownLinePos = 0
    parser.ignoreData = False
    htmlStr = fixHTML(htmlStr)
    err=""
    try:
        parser.feed(htmlStr) ; parser.close()
    except UnicodeDecodeError, e:
        # sometimes happens in parsing the start of a tag in duff HTML (possibly emitted by a duff htmlFilter if we're currently picking out text for the renderer)
        try: err="UnicodeDecodeError at bytes %d-%d: %s" % (e.start,e.end,e.reason)
        except: err = "UnicodeDecodeError"
    except HTMLParseError: err="HTMLParseError" # rare?
    # If either of the above errors occur, we leave the rest of the HTML as "code" i.e. unchanged
    if len(parser.codeTextList)%2: parser.codeTextList.append("") # ensure len is even before appending the remaining code (adjustment is required only if there was an error)
    if not options.renderDebug: err=""
    elif err: err="<!-- "+err+" -->"
    parser.codeTextList.append(err+latin1decode(htmlStr[parser.lastCodeStart:]))
    return parser.codeTextList

def LXML_find_text_in_HTML(htmlStr):
    import htmlentitydefs
    class Parser:
        def start(self, tag, attrs):
            self.out.append(lxmlEncodeTag(tag,dict((k,v.encode('utf-8')) for k,v in dict(attrs).items())))
            if tag in options.leaveTags:
                self.ignoreData=True
        def end(self, tag):
            if tag not in html_tags_not_needing_ends:
                self.out.append("</"+tag+">")
            if tag in options.leaveTags:
                self.ignoreData=False
        def data(self,unidata):
            data = unidata.encode('utf-8')
            if self.ignoreData or not data.strip():
                self.out.append(data) ; return
            self.codeTextList.append("".join(self.out))
            self.codeTextList.append(data)
            self.out = []
        def comment(self,text): # TODO: same as above's def comment
            self.out.append("<!--"+text+"-->")
        def close(self): pass
    parser = Parser() ; parser.out = []
    parser.codeTextList = [] ; parser.ignoreData = False
    lparser = etree.HTMLParser(target=parser)
    etree.parse(StringIO(htmlStr.decode('utf-8')), lparser)
    if len(parser.codeTextList)%2: parser.codeTextList.append("")
    parser.codeTextList.append("".join(parser.out))
    return parser.codeTextList

def find_HTML_in_JSON(jsonStr,htmlListFunc=None):
    # makes a codeTextList from JSON, optionally calling
    # htmlListFunc to make codeTextLists from any HTML
    # parts it finds.  Unescapes the HTML parts.
    def afterQuoteEnd(i):
        while i<len(jsonStr):
            i += 1
            if jsonStr[i]=='\\': i += 2
            if jsonStr[i]=='"': return i+1
        return -1
    def looks_like_HTML(s): return "<div " in s.lower() or "<span " in s.lower() # TODO: more?
    codeTextList = [] ; i=j=0
    while True:
        j=jsonStr.find('"',j)
        if j==-1: break
        k = afterQuoteEnd(j)
        if k==-1: break
        assert type(jsonStr)==type("")
        try: html = json.loads(jsonStr[j:k]).encode('utf-8')
        except: html = None
        if html and looks_like_HTML(html):
            codeTextList.append(jsonStr[i:j+1]) # code (include opening quote, necessary as see the dumps comment)
            if htmlListFunc: html = htmlListFunc(html)
            codeTextList.append(html) # text
            i = k-1 # on the closing quote
        j = k
    codeTextList.append(jsonStr[i:])
    return codeTextList
    
def domain_process(text,cookieHost=None,stopAtOne=False):
    # Change the domains on appropriate http:// URLs.
    # Hope that there aren't any JS-computed links where
    # the domain is part of the computation.
    # TODO: https ?  (will need a different HTTPServer on a different port configured to HTTPS with cert and key files)
    # TODO: what of links to alternate ports or user:password links, currently we leave them unchanged
    # TODO: leave alone URLs in HTML text/comments and JS comments? but script overload can make it hard to judge what is and isn't text. (NB this function is also called for Location headers)
    start=0
    while True:
        i = text.find("http://",start)
        if i==-1: break
        if "<!DOCTYPE" in text:
            # don't touch URLs inside the doctype!
            dtStart = text.index("<!DOCTYPE")
            dtEnd = text.find(">",dtStart)
            if dtStart<i<dtEnd:
                start = dtEnd ; continue
        if i and text[i-1].split() and text[:i].rsplit(None,1)[-1].startswith("xmlns"):
            # don't touch this one either (xmlns="... xmlns:elementname='... etc)
            start = i+1 ; continue
        i += len("http://") ; j = i
        while j<len(text) and text[j] in string.letters+string.digits+'.-': j += 1
        if j==len(text) or text[j] in '/?"\'': # we have a normal link
            newhost = convert_to_requested_host(text[i:j],cookieHost) # "" if i==j
            text = text[:i] + newhost + text[j:]
            if stopAtOne: return text
            j=i+len(newhost)
        start = j
    return text

def cookie_domain_process(text,cookieHost=None):
    start=0
    while True:
        i = text.lower().find("; domain=",start)
        if i==-1: break
        i += len("; domain=")
        if text[i]=='.': i += 1 # leading . on the cookie (TODO: what if we're not wildcard_dns?)
        j = i
        while j<len(text) and not text[j]==';': j += 1
        newhost = convert_to_requested_host(text[i:j],cookieHost)
        if ':' in newhost: newhost=newhost[:newhost.index(':')] # apparently you don't put the port number, see comment in authenticates_ok
        text = text[:i] + newhost + text[j:]
        j=i+len(newhost)
        start = j
    return text

def url_is_ours(url):
    # check if url has been through domain_process
    if not url.startswith("http://"): return False
    url=url[len("http://"):]
    if '/' in url: url=url[:url.index('/')]
    rh = convert_to_real_host(url,"cookie-host\n")
    return rh and type(rh)==type("") and not rh==url # TODO: is the last part really necessary?

def js_process(body,url):
    for prefix, srch, rplac in codeChanges:
        if url.startswith(prefix): body=body.replace(srch,rplac)
    return body

detect_iframe = """(window.frameElement && window.frameElement.nodeName.toLowerCase()=="iframe" && function(){var i=window.location.href.indexOf("/",7); return (i>-1 && window.top.location.href.slice(0,i)==window.location.href.slice(0,i))}())""" # expression that's true if we're in an iframe that belongs to the same site, so can omit reminders etc
def reloadSwitchJS(cookieName,jsCookieString,flipLogic,readableName,cookieHostToSet,cookieExpires,extraCondition=None):
    # writes a complete <script> to switch something on/off by cookie and reload (TODO: non-JS version would be nice, but would mean intercepting more URLs)
    # if flipLogic, "cookie=1" means OFF, default ON
    # document.write includes a trailing space so another one can be added after
    isOn,setOn,setOff = (cookieName+"=1" in jsCookieString),"1","0"
    if flipLogic: isOn,setOn,setOff = (not isOn),setOff,setOn
    if extraCondition: extraCondition = "&&"+extraCondition
    else: extraCondition = ""
    if isOn: return r"""<script type="text/javascript"><!--
if(!%s%s)document.write("%s: On | "+'<a href="javascript:document.cookie=\'%s=%s;domain=%s;expires=%s;path=/\';document.cookie=\'%s=%s;domain=.%s;expires=%s;path=/\';location.reload()">Off</a> ')
//--></script>""" % (detect_iframe,extraCondition,readableName,cookieName,setOff,cookieHostToSet,cookieExpires,cookieName,setOff,cookieHostToSet,cookieExpires)
    else: return r"""<script type="text/javascript"><!--
if(!%s%s)document.write("%s: "+'<a href="javascript:document.cookie=\'%s=%s;domain=%s;expires=%s;path=/\';document.cookie=\'%s=%s;domain=.%s;expires=%s;path=/\';location.reload()">On</a> | Off ')
//--></script>""" % (detect_iframe,extraCondition,readableName,cookieName,setOn,cookieHostToSet,cookieExpires,cookieName,setOn,cookieHostToSet,cookieExpires)

def detect_renderCheck(): return r"""(document.getElementsByTagName && function(){var b=document.getElementsByTagName("BODY")[0],d=document.createElement("DIV"),s=document.createElement("SPAN"); d.appendChild(s); function wid(chr) { s.innerHTML = chr; b.appendChild(d); var width = s.offsetWidth; b.removeChild(d); return width; } var w1=wid("\u%s"),w2=wid("\uffff"),w3=wid("\ufffe"),w4=wid("\u2fdf"); return (w1!=w2 && w1!=w3 && w1!=w4)}())""" % options.renderCheck
# ffff, fffe - guaranteed invalid by Unicode, but just might be treated differently by browsers
# 2fdf unallocated character at end of Kangxi radicals block, hopefully won't be used
#  do NOT use fffd, it's sometimes displayed differently to other unrenderable characters
# Works even in Opera Mini, which must somehow communicate the client's font metrics to the proxy

def html_additions(html,slow_CSS_switch,cookieHostToSet,jsCookieString,canRender,cookie_host,is_password_domain):
    # Additions to make to HTML only (not on HTML embedded in JSON)
    if not "<body" in html.lower() and not "</body" in html.lower():
        # frameset etc (TODO: what about broken HTML that omits the body tag?  have tried to check for "</body" as well, but that might be missing also)
        return html
    bodyAppend = options.bodyAppend
    if not bodyAppend: bodyAppend = ""
    bodyPrepend = options.bodyPrepend
    if not bodyPrepend: bodyPrepend = ""
    headAppend = ""
    if options.headAppendCSS:
        # do this BEFORE headAppend, because someone might want to refer to it in a script in headAppend (although bodyPrepend is a better place to put 'change the href according to screen size' scripts, as some Webkit-based browsers don't make screen size available when processing the HEAD of the 1st document in the session)
        if options.cssName:
          if slow_CSS_switch:
              # alternate, slower code involving hard HTML coding and page reload (but still requires some JS)
              bodyAppend += reloadSwitchJS("adjustCssSwitch",jsCookieString,False,options.cssName,cookieHostToSet,cookieExpires)
              if "adjustCssSwitch=1" in jsCookieString:
                  headAppend += '<link rel="stylesheet" type="text/css" href="%s">' % (options.headAppendCSS,)
          else: # client-side only CSS switcher:
            headAppend += """<link rel="alternate stylesheet" type="text/css" id="adjustCssSwitch" title="%s" href="%s">
<script language="Javascript"><!--
if(document.getElementById) document.getElementById('adjustCssSwitch').disabled=true
//--></script>""" % (options.cssName,options.headAppendCSS,) # (on some Webkit versions, MUST set disabled to true (from JS?) before setting it to false will work)
# disabled=}
            bodyPrepend += """<script language="Javascript"><!--
if(document.getElementById && document.cookie.indexOf("adjustCssSwitch=1")>-1) document.getElementById('adjustCssSwitch').disabled=false
//--></script>"""
            bodyAppend += r"""<script type="text/javascript"><!--
if(document.getElementById && !%s) document.write("%s: "+'<a href="javascript:document.getElementById(\'adjustCssSwitch\').disabled=false;document.cookie=\'adjustCssSwitch=1;domain=%s;expires=%s;path=/\';document.cookie=\'adjustCssSwitch=1;domain=.%s;expires=%s;path=/\';window.scrollTo(0,0)">On</a> | <a href="javascript:document.getElementById(\'adjustCssSwitch\').disabled=true;document.cookie=\'adjustCssSwitch=0;domain=%s;expires=%s;path=/\';document.cookie=\'adjustCssSwitch=0;domain=.%s;expires=%s;path=/\';window.scrollTo(0,0)">Off</a> ')
//--></script>""" % (detect_iframe,options.cssName,cookieHostToSet,cookieExpires,cookieHostToSet,cookieExpires,cookieHostToSet,cookieExpires,cookieHostToSet,cookieExpires)
        else: headAppend += '<link rel="stylesheet" type="text/css" href="%s">' % (options.headAppendCSS,)
    if options.htmlFilterName and options.htmlFilter: bodyAppend += reloadSwitchJS("adjustNoFilter",jsCookieString,True,options.htmlFilterName,cookieHostToSet,cookieExpires)
    if canRender:
        # TODO: make the script below set a cookie to stop itself from being served on subsequent pages if detect_renderCheck failed? but this might be a false economy if upload bandwidth is significantly smaller than download bandwidth (and making it external could have similar issues)
        # TODO: if cookies are not supported, the script below could go into an infinite reload loop
        if options.renderCheck and not "adjustNoRender=1" in jsCookieString: bodyPrepend += r"""<script type="text/javascript"><!--
if(!%s && %s) { document.cookie='adjustNoRender=1;domain=%s;expires=%s;path=/';document.cookie='adjustNoRender=1;domain=.%s;expires=%s;path=/';location.reload()
}
//--></script>""" % (detect_iframe,detect_renderCheck(),cookieHostToSet,cookieExpires,cookieHostToSet,cookieExpires)
        if options.renderName:
            if options.renderCheck and "adjustNoRender=1" in jsCookieString: extraCondition="!"+detect_renderCheck() # don't want the adjustNoRender=0 (fonts ON) link visible if detect_renderCheck is true, because it won't work anyway (any attempt to use it will be reversed by the script, and if we work around that then legacy pre-renderCheck cookies could interfere; anyway, if implementing some kind of 'show the switch anyway' option, might also have to address showing it on renderOmit browsers)
            else: extraCondition=None
            bodyAppend += reloadSwitchJS("adjustNoRender",jsCookieString,True,options.renderName,cookieHostToSet,cookieExpires,extraCondition)
    if cookie_host:
        if enable_adjustDomainCookieName_URL_override: bodyAppend += r"""<script type="text/javascript"><!--
if(!%s)document.write('<a href="http://%s/?%s=%s">Back to URL box</a>')
//--></script><noscript><a href="http://%s/?%s=%s">Back to URL box</a></noscript>""" % (detect_iframe,cookieHostToSet,adjust_domain_cookieName,adjust_domain_none,cookieHostToSet,adjust_domain_cookieName,adjust_domain_none)
        else: bodyAppend += r"""<script type="text/javascript"><!--
if(!%s)document.write('<a href="javascript:document.cookie=\'%s=%s;expires=%s;path=/\';if(location.href==\'http://%s/\')location.reload();else location.href=\'http://%s/?nocache=\'+Math.random()">Back to URL box</a>')
//--></script>""" % (detect_iframe,adjust_domain_cookieName,adjust_domain_none,cookieExpires,cookieHostToSet,cookieHostToSet) # (we should KNOW if location.href is already that, and can write the conditional here not in that 'if', but they might bookmark the link or something)
    if options.headAppendRuby: headAppend += """
<style id="ruby">ruby { display: inline-table; vertical-align: top; }
ruby * { display: inline;
line-height:1.0; text-indent:0; text-align:center;
white-space: nowrap; }
rb { display: table-row-group; font-size: 100%; }
rt { display: table-header-group; font-size: 100%; line-height: 1.1; }</style>
<!--[if !IE]>-->
<style>rt { font-family: Gandhari, DejaVu Sans, Lucida Sans Unicode, Times New Roman, serif !important; }</style>
<!--<![endif]-->
<script language="JavaScript"><!--
var wk=navigator.userAgent.indexOf('WebKit/');
if(wk>-1){var v=document.getElementById('ruby');v.innerHTML=v.innerHTML.replace(/display[^;]*;/g,'');
v=navigator.userAgent.slice(wk+7,wk+12);if(v>=534.3&&v<535.7)document.write('<style>rt{padding-left:1ex;padding-right:1ex;}<'+'/style>')}
//--></script>
""" # (I sent the WebKit hack to Wenlin Institute as well)
    if options.headAppend: headAppend += options.headAppend
    if options.prominentNotice and not is_password_domain:
        # if JS is available, use fixed positioning (so it still works on sites that do that, in case we're not overriding it via user CSS) and a JS acknowledge button
        styleAttrib="style=\"width: 80% !important; margin: 10%; border: red solid !important; background: black !important; color: white !important; text-align: center !important; display: block !important; left:0px; top:0px; z-index:99999; -moz-opacity: 1 !important; filter: none !important; opacity: 1 !important; visibility: visible !important;\""
        if slow_CSS_switch: # use a slow version for this as well (TODO document that we do this?) (TODO the detect_iframe exclusion of the whole message)
            if not "_WA_warnOK=1" in jsCookieString: bodyPrepend += "<div id=_WA_warn0 "+styleAttrib+">"+options.prominentNotice+r"""<script language="JavaScript"><!--
document.write("<br><button style=\"color: black !important;background:#c0c0c0 !important;border: white solid !important\" onClick=\"document.cookie='_WA_warnOK=1;path=/';location.reload()\">Acknowledge</button>")
//--></script></div><script language="JavaScript"><!--
if(document.getElementById) document.getElementById('_WA_warn0').style.position="fixed"
}
//--></script>"""
        else: bodyPrepend += "<div id=_WA_warn0 "+styleAttrib+">"+options.prominentNotice+r"""</div><script language="JavaScript"><!--
if(document.getElementById) {
  var w=document.getElementById('_WA_warn0');
  if(w.innerHTML) {
  var s=w.style;
  s.position="fixed";
  var f="""+detect_iframe+r""";
  if(!f) { var c=document.cookie.split(";"); for (i=0;i<c.length;i++) if (c[i].substr(0,c[i].indexOf("=")).replace(/\s/g,"") == "_WA_warnOK") { f=1;break; } }
  if(f) document.body.removeChild(document.getElementById('_WA_warn0'));
  else w.innerHTML += "<br><button style=\"color: black !important;background:#c0c0c0 !important;border: white solid !important\" onClick=\"document.body.removeChild(document.getElementById('_WA_warn0'));document.cookie='_WA_warnOK=1;path=/'\">Acknowledge</button>";
}}
//--></script>"""
    if options.headAppendRuby: bodyAppend += """
<script language="javascript"><!--
if(navigator.userAgent.indexOf('WebKit/')>-1 && navigator.userAgent.slice(wk+7,wk+12)>534){var rbs=document.getElementsByTagName('rb');for(var i=0;i<rbs.length;i++)rbs[i].innerHTML='&#8203;'+rbs[i].innerHTML+'&#8203;'}
function treewalk(n) { var c=n.firstChild; while(c) { if (c.nodeType==1 && c.nodeName!="SCRIPT" && c.nodeName!="TEXTAREA" && !(c.nodeName=="A" && c.hasAttribute("href"))) { treewalk(c); if(c.nodeName=="RUBY" && c.hasAttribute("title") && !c.hasAttribute("onclick")) c.onclick=Function("alert(this.title)") } c=c.nextSibling; } } function tw() { treewalk(document.body); window.setTimeout(tw,5000); } treewalk(document.body); window.setTimeout(tw,1500);
//--></script>"""
    if headAppend:
        i=html.lower().find("</head")
        if i==-1: # no head section?
            headAppend = "<head>"+headAppend+"</head>"
            i=html.lower().find("<body")
            if i==-1: # broken HTML?
                i=html.lower().find(">")
                if i==-1: i=0 # ???
        html = html[:i]+headAppend+html[i:]
    if bodyPrepend:
        i=html.lower().find("<body")
        if i>-1:
            i=html.find(">",i)
            if i>-1: html=html[:i+1]+bodyPrepend+html[i+1:]
    if bodyAppend:
        if options.bodyAppendGoesAfter:
            i=html.rfind(options.bodyAppendGoesAfter)
            if i>-1: i += len(options.bodyAppendGoesAfter)
        else: i=-1
        if i==-1: i=html.lower().find("</body")
        if i==-1: i=html.lower().find("</html")
        if i==-1: i=len(html)
        html = html[:i]+bodyAppend+html[i:]
    return html

def ampEncode(unitxt): return unitxt.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;") # needed because these entities will be in cleartext to the renderer

class Renderer:
    def __init__(self):
        self.renderFont = None
        self.hanziW,self.hanziH = 0,0
    def font(self):
        if not self.renderFont: # first time
            try: import ImageFont
            except: import PIL.ImageFont as ImageFont
            if options.renderFont: self.renderFont = ImageFont.truetype(options.renderFont, options.renderSize, encoding="unic")
            else: self.renderFont = ImageFont.load_default()
        return self.renderFont
    def getMarkup(self,unitext):
        i=0 ; import unicodedata
        width = 0 ; imgStrStart = -1
        ret = [] ; copyFrom = 0
        def doImgEnd():
            if imgStrStart >= 0 and width <= options.renderWidth and len(ret) > imgStrStart + 1:
                ret.insert(imgStrStart,'<nobr>')
                ret.append('</nobr>')
        if options.renderWidth==0: doImgEnd=lambda:None
        if options.renderBlocks: combining=lambda x:False
        else: combining=unicodedata.combining
        checkAhead = (options.renderNChar>1 or not options.renderBlocks)
        while i<len(unitext):
            if inRenderRange(unitext[i]) and not combining(unitext[i]): # (don't START the render with a combining character - that belongs to the character before)
                j = i+1
                if checkAhead:
                  charsDone = 1
                  while j<len(unitext) and ((charsDone < options.renderNChar and inRenderRange(unitext[j])) or combining(unitext[j])):
                    if not combining(unitext[j]): charsDone += 1
                    j += 1
                rep,w=self.getMarkup_inner(unitext[i:j])
                width += w
                if i>copyFrom: ret.append(ampEncode(unitext[copyFrom:i]))
                if imgStrStart==-1: imgStrStart = len(ret)
                ret.append(rep)
                copyFrom = i = j
            else:
                doImgEnd() ; i += 1
                width = 0 ; imgStrStart = -1
        doImgEnd()
        if i>copyFrom: ret.append(ampEncode(unitext[copyFrom:i]))
        return u"".join(ret)
    def getMarkup_inner(self,unitext):
        if options.renderBlocks and self.hanziW:
            w,h = self.hanziW*len(unitext), self.hanziH
        else:
            w,h = self.font().getsize(unitext)
            if options.renderBlocks:
                self.hanziW = w/len(unitext)
                self.hanziH = h
        return ('<img src="%s" width=%d height=%d>' % (options.renderPath+imgEncode(unitext),w,h)), w
    def getImage(self,uri):
        if not options.render or not uri.startswith(options.renderPath): return False
        try: import ImageDraw,Image
        except:
            import PIL.ImageDraw as ImageDraw
            import PIL.Image as Image
        import cStringIO
        try: text=imgDecode(uri[len(options.renderPath):])
        except: return False # invalid base64 = fall back to fetching the remote site
        size = self.font().getsize(text) # w,h
        if options.renderInvert: bkg,fill = 0,1
        else: bkg,fill = 1,0
        img=Image.new("1",size,bkg) # "1" is 1-bit
        ImageDraw.Draw(img).text((0, 0),text,font=self.font(),fill=fill)
        dat=cStringIO.StringIO()
        img.save(dat,options.renderFormat)
        return dat.getvalue()
Renderer=Renderer()

def create_inRenderRange_function(arg):
    # create the inRenderRange function up-front (don't re-parse the options every time it's called)
    global inRenderRange
    if type(arg)==type(""): arg=arg.split(',')
    arg = [tuple(int(x,16) for x in lh.split(':')) for lh in arg] # [(l,h), (l,h)]
    if len(arg)==1: # Only one range - try to make it fast
        l,h = arg[0]
        while l==0 or not unichr(l).strip(): l += 1 # NEVER send whitespace to the renderer, it will break all hope of proper word-wrapping in languages that use spaces. And chr(0) is used as separator.  (TODO: what if there's whitespace in the MIDDLE of one of the ranges?  but don't add the check to inRenderRange itself unless we've confirmed it might be needed)
        inRenderRange=lambda uc:(l <= ord(uc) <= h)
    elif arg: # More than one range
        inRenderRange=lambda uc:(ord(uc)>0 and uc.strip() and any(l <= ord(uc) <= h for l,h in arg))
    else: inRenderRange=lambda uc:(ord(uc) and uc.strip())

def imgEncode(unitext):
    # Encode unitext to something URL-safe, try to be efficient especially in small cases
    # Normally base64-encoded UTF-8 (output will be a multiple of 4 bytes)
    # but some single characters will be OK as-is, and 2 or 3 bytes could hex a unichr under U+1000
    if len(unitext)==1:
        if unitext in string.letters+string.digits+"_.-": return unitext
        elif 0xf<ord(unitext)<0x1000: return hex(ord(unitext))[2:]
    return base64.b64encode(unitext.encode('utf-8'))
def imgDecode(code):
    if len(code)==1: return code
    elif len(code) <= 3: return unichr(int(code,16))
    else: return base64.b64decode(code).decode('utf-8')

class Dynamic_DNS_updater:
    def __init__(self):
        self.currentIP = None
        self.forceTime=0
        IOLoop.instance().add_callback(lambda *args:self.queryIP())
    def queryIP(self):
        debuglog("queryIP")
        def handleResponse(r):
            if not r.error: self.newIP(r.body.strip())
            IOLoop.instance().add_timeout(time.time()+options.ip_check_interval,lambda *args:self.queryIP())
        AsyncHTTPClient().fetch(options.ip_query_url, callback=handleResponse)
    def newIP(self,ip):
        debuglog("newIP "+ip)
        if ip==self.currentIP and (not options.ip_force_interval or time.time()<self.forceTime): return
        try: socket.inet_aton(ip) # IPv4 only
        except socket.error: # try IPv6
            try: socket.inet_pton(socket.AF_INET6,ip)
            except socket.error: return # illegal IP, maybe a temporary error from the server
        self.currentIP = ip
        if options.ip_change_command:
            cmd = options.ip_change_command+" "+ip
            logging.info("ip_change_command: "+cmd)
            threading.Thread(target=os.system,args=(cmd,)).start()
        if options.dynamic_dns_api:
          # send the API updates one domain at a time
          def upHost(hostList):
            if hostList: AsyncHTTPClient().fetch(options.dynamic_dns_api % (hostList[0],ip), callback=lambda r:(logging.info("Dynamic DNS: update %s to %s gave error %s and body %s" % (hostList[0],ip,repr(r.error),repr(r.body.strip()))),upHost(hostList[1:])), auth_username=options.ddns_api_user, auth_password=options.ddns_api_pwd)
          upHost(options.host_suffix.split("/"))
        self.forceTime=time.time()+options.ip_force_interval

class WatchdogPings:
    def __init__(self,wFile):
        self.wFile = wFile
        if options.watchdogWait:
            import thread
            thread.start_new_thread((lambda *args:self.separate_thread()),())
        self.ping()
    def separate_thread(self): # version for watchdogWait
        def respond(*args):
            global watchdog_mainServerResponded
            watchdog_mainServerResponded = time.time()
        respond() ; stopped = 0
        while True:
            if watchdog_mainServerResponded + options.watchdogWait >= time.time():
                self.ping()
                if stopped:
                    logging.info("Main thread responded, restarting watchdog ping")
                    stopped = 0
                IOLoop.instance().add_callback(respond)
            elif not stopped:
                logging.info("Main thread unresponsive, stopping watchdog ping")
                stopped = 1 # but don't give up (it might respond just in time)
            time.sleep(options.watchdog)
    def ping(self):
        debuglog("pinging watchdog",logRepeats=False)
        self.wFile.write('a') ; self.wFile.flush()
        if not options.watchdogWait: # run from main thread
            IOLoop.instance().add_timeout(time.time()+options.watchdog,lambda *args:self.ping())
        # else one ping only (see separate_thread)

fasterServer_up = False
class checkServer:
    def __init__(self): self.client=None ; self.interval=1
    def __call__(self):
      def callback(r):
        global fasterServer_up
        fsu_old = fasterServer_up
        fasterServer_up = not r.error
        if not fasterServer_up == fsu_old:
            if fasterServer_up: logging.info("fasterServer %s came up - forwarding traffic to it" % options.fasterServer)
            else: logging.info("fasterServer %s went down - handling traffic ourselves" % options.fasterServer)
        # debuglog("fasterServer_up="+repr(fasterServer_up)+" (err="+repr(r.error)+")",logRepeats=False)
        if fasterServer_up: self.interval = 1 # TODO: configurable? fallback if timeout when we try to connect to it as well?
        else:
            if self.interval < 60: # TODO: configurable?
                self.interval *= 2
            self.client = None
        IOLoop.instance().add_timeout(time.time()+self.interval,lambda *args:checkServer())
      if not self.client: self.client=AsyncHTTPClient()
      self.client.fetch("http://"+options.fasterServer+"/ping",connect_timeout=1,request_timeout=1,user_agent="ping",callback=callback,use_gzip=False)
checkServer=checkServer()

def debuglog(msg,logRepeats=True):
    global lastDebugMsg
    try: lastDebugMsg
    except: lastDebugMsg=None
    if logRepeats or not msg==lastDebugMsg:
        if not options.logDebug: logging.debug(msg)
        elif options.background: logging.info(msg)
        else: sys.stderr.write(time.strftime("%X ")+msg+"\n")
    lastDebugMsg = msg

if __name__ == "__main__": main()
