#!/usr/bin/env python

program_name = "Web Adjuster v0.194 (c) 2012-14 Silas S. Brown"

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
# versions are being kept on SourceForge's E-GuideDog SVN repository
# http://sourceforge.net/p/e-guidedog/code/HEAD/tree/ssb22/adjuster/
# although some early ones are missing.
# To check out the repository, you can do:
# svn co http://svn.code.sf.net/p/e-guidedog/code/ssb22/adjuster

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
else:
    import tornado
    from tornado.httpclient import AsyncHTTPClient,HTTPClient,HTTPError
    from tornado.ioloop import IOLoop
    from tornado import web
    from tornado.web import Application, RequestHandler, asynchronous
    import tornado.options, tornado.iostream
    from tornado.options import define,options
    def heading(h): pass
getfqdn_default = "is the machine's domain name" # default is ... (avoid calling getfqdn unnecessarily, as the server might be offline/experimental and we don't want to block on an nslookup with every adjuster start)

heading("General options")
define("config",help="Name of the configuration file to read, if any. The process's working directory will be set to that of the configuration file so that relative pathnames can be used inside it. Any option that would otherwise have to be set on the command line may be placed in this file as an option=\"value\" or option='value' line (without any double-hyphen prefix). Multi-line values are possible if you quote them in \"\"\"...\"\"\", and you can use standard \\ escapes. You can also set config= in the configuration file itself to import another configuration file (for example if you have per-machine settings and global settings). If you want there to be a default configuration file without having to set it on the command line every time, an alternative option is to set the ADJUSTER_CFG environment variable.")

heading("Network listening and security settings")
define("port",default=28080,help="The port to listen on. Setting this to 80 will make it the main Web server on the machine (which will likely require root access on Unix).")
define("publicPort",default=0,help="The port to advertise in URLs etc, if different from 'port' (the default of 0 means no difference). Used for example if a firewall prevents direct access to our port but some other server has been configured to forward incoming connections.")
define("user",help="The user name to run as, instead of root. This is for Unix machines where port is less than 1024 (e.g. port=80) - you can run as root to open the privileged port, and then drop privileges. Not needed if you are running as an ordinary user.")
define("address",default="",help="The address to listen on. If unset, will listen on all IP addresses of the machine. You could for example set this to localhost if you want only connections from the local machine to be received, which might be useful in conjunction with real_proxy.")
define("password",help="The password. If this is set, nobody can connect without specifying ?p= followed by this password. It will then be sent to them as a cookie so they don't have to enter it every time. Notes: (1) If wildcard_dns is False and you have multiple domains in host_suffix, then the password cookie will have to be set on a per-domain basis. (2) On a shared server you probably don't want to specify this on the command line where it can be seen by process-viewing tools; use a configuration file instead.")
define("password_domain",help="The domain entry in host_suffix to which the password applies. For use when wildcard_dns is False and you have several domains in host_suffix, and only one of them (perhaps the one with an empty default_site) is to be password-protected, with the others public. If this option is used then prominentNotice (if set) will not apply to the passworded domain. You may put the password on two or more domains by separating them with slash (/).") # prominentNotice not apply: on the assumption that those who know the password understand what the tool is
define("auth_error",default="Authentication error",help="What to say when password protection is in use and a correct password has not been entered. HTML markup is allowed in this message. As a special case, if this begins with http:// then it is assumed to be the address of a Web site to which the browser should be redirected; if it is set to http:// and nothing else, the request will be passed to the server specified by own_server (if set). If the markup begins with a * when this is ignored and the page is returned with code 200 (OK) instead of 401 (authorisation required).") # TODO: basic password form? or would that encourage guessing
define("open_proxy",default=False,help="Whether or not to allow running with no password. Off by default as a safeguard against accidentally starting an open proxy.")
define("prohibit",multiple=True,default="wiki.*action=edit",help="Comma-separated list of regular expressions specifying URLs that are not allowed to be fetched unless --real-proxy is in effect. Browsers requesting a URL that contains any of these will be redirected to the original site. Use for example if you want people to go direct when posting their own content to a particular site (this is of only limited use if your server also offers access to any other site on the Web, but it might be useful when that's not the case).")
define("real_proxy",default=False,help="Whether or not to accept requests with original domains like a \"real\" HTTP proxy.  Warning: this bypasses the password and implies open_proxy.  Off by default.")
define("via",default=True,help="Whether or not to update the Via: and X-Forwarded-For: HTTP headers when forwarding requests") # (Via is "must" in RFC 2616)
define("robots",default=False,help="Whether or not to pass on requests for /robots.txt.  If this is False then all robots will be asked not to crawl the site; if True then the original site's robots settings will be mirrored.  The default of False is recommended.")

define("upstream_proxy",help="address:port of a proxy to send our requests through, such as a caching proxy to reduce load on websites (putting this upstream of the adjuster should save the site from having to re-serve pages when adjuster settings are changed). This proxy (if set) is used for normal requests, but not for ip_query_url options, own_server, fasterServer or HTTPS requests.") # The upstream_proxy option requires pycurl (will refuse to start if not present). Does not set X-Real-Ip because Via should be enough for upstream proxies.

define("ip_messages",help="Messages or blocks for specific IP address ranges (IPv4 only).  Format is ranges|message|ranges|message etc, where ranges are separated by commas; can be individual IPs, or ranges in either 'network/mask' or 'min-max' format; the first matching range-set is selected.  If a message starts with * then its ranges are blocked completely (rest of message, if any, is sent as the only reply to any request), otherwise message is shown on a 'click-through' page (requires Javascript and cookies).  If the message starts with a hyphen (-) then it is considered a minor edit of earlier messages and is not shown to people who selected `do not show again' even if they did this on a different version of the message.  Messages may include HTML.")

heading("DNS and website settings")
define("host_suffix",default=getfqdn_default,help="The last part of the domain name. For example, if the user wishes to change www.example.com and should do so by visiting www.example.com.adjuster.example.org, then host_suffix is adjuster.example.org. If you do not have a wildcard domain then you can still adjust one site by setting wildcard_dns to False, host_suffix to your non-wildcard domain, and default_site to the site you wish to adjust. If you have more than one non-wildcard domain, you can set wildcard_dns to False, host_suffix to all your domains separated by slash (/), and default_site to the sites these correspond to, again separated by slash (/); if two or more domains share the same default_site then the first is preferred in links and the others are assumed to be for backward compatibility. If wildcard_dns is False and default_site is empty (or if it's a /-separated list and one of its items is empty), then the corresponding host_suffix gives a URL box and sets its domain in a cookie (and adds a link at the bottom of pages to clear this and return to the URL box), but this should be done only as a last resort: you can browse only one domain at a time at that host_suffix (links and HTTP redirects to other domains will leave the adjuster), and the sites you visit at that host_suffix might be able to see some of each other's cookies etc (leaking privacy) although the URL box page will try to clear site cookies.")
# ("preferred" / "backward compatibility" thing: can be useful if old domain has become unreliable, or if "preferred" domain is actually a URL-path-forwarding service with a memorable name which redirects browsers to an actual domain that's less memorable, and you want the memorable domain to be used in links etc, although in this case you might still get the less-memorable domain in the address bar)
# TODO: (two or more domains pointing to the same default_site) "preferred" / "backward compatibility" thing above: or, add an option to periodically check which of our domains are actually 'up' and move them to the front of the host_suffix / default_site list; that way we don't have to guess ahead of time which one is more reliable and should be preferred.
# Could also do 'use the currently-requested host if it's appropriate', but what if there's a *set* of sites we adjust and we need to try to rewrite cross-site links to be in the same set of domains as the one the browser is requesting - maybe it's best to leave the "preferred" DNS to the config or the periodic check.
# TODO at lower priority: empty (item in) host_suffix to match ALL (unknown) hosts, including IP hosts and no Host: header.  Fetch the corresponding default_site (empty means use cookies), and adjust it USING THE HOST SPECIFIED BY THE BROWSER to rewrite the links.  This could be useful if setting up an adjuster with NO domain name (IP only).  Could periodically upload our public IP to a separate static website via FTP/SSH/etc in case dynamic DNS is not reliable.  But if IP address has to change then all cookies would be 'lost'.  Also, if no password is set then IP-based "webserver probes" could cause us to send malicious-looking traffic to default_site.
# TODO: Could do different hosts on different ports, which might also be useful if you have a domain name but only one.  Would have to check for cookie sharing (or just say "do this only if you don't mind it"); fasterServer would have to forward to same as incoming port.  Might be a problem if some users' firewalls disallow outgoing Web traffic to non-standard ports.
# (In the current code, setting host_suffix to a public IP address should work: most browsers set Host: to the IP if requesting a URL by IP, and then the IP will be used in rewrites if it's the first thing specified for its corresponding default_site.  But adjuster will need to be reconfigured and restarted on every change of the public IP.)
define("default_site",help="The site to fetch from if nothing is specified before host_suffix. If this is omitted then the user is given a URL box when that happens.")
define("own_server",help="Where to find your own web server. This can be something like localhost:1234 or 192.168.0.2:1234. If it is set, then any request that does not match host_suffix will be passed to that server to deal with, unless real_proxy is in effect. You can use this option to put your existing server on the same public port without much reconfiguration. Note: the password option will NOT password-protect your own_server. (You might gain a little responsiveness if you instead set up nginx or similar to direct incoming requests appropriately; see comments in adjuster.py for example nginx settings.)")
# without much reconfiguration: might just need to change which port number it listens on.
# Alternatively you could set nginx (or similar) to reverse-proxy the host_suffix domains to the adjuster, e.g.:
# location / {
#   proxy_set_header X-Real-Ip $remote_addr;
#   proxy_set_header Host $host;
#   proxy_pass_header Server;
#   access_log off;
#   proxy_pass http://localhost:<YOUR-ADJUSTER-PORT-HERE>;
#   proxy_max_temp_file_size 0;
#   proxy_read_timeout 130s;  # or whatever; default 60s
#        # - may need to be longer, especially if using
#        #    file conversion with waitpage=False on a
#        #    low-powered server and there are big files
# }
# inside a "server" block with appropriate server_name(s)
# (and set ipTrustReal to 127.0.0.1 in Adjuster's config,
# and set publicPort to the port nginx runs on e.g. 80),
# but if you're not already using nginx then you either
# have to either port your existing server to nginx or get
# nginx to reverse-proxy for your other server, so for
# small installations it might be simpler just to set
# own_server, unless it's vitally important that
# own_server is not held up in any way when the adjuster
# is under heavy CPU load.

define("ownServer_regexp",help="If own_server is set, you can set ownServer_regexp to a regular expression to match URL prefixes which should always be handled by your own server even if they match host_suffix. This can be used for example to add extra resources to any site, or to serve additional pages from the same domain, as long as the URLs used are not likely to occur on the sites being adjusted. The regular expression is matched against the requested host and the requested URL, so for example [^/]*/xyz will match any URL starting with /xyz on any host, whereas example.org/xyz will match these on your example.org domain. You can match multiple hosts and URLs by using regular expression grouping.")
define("ownServer_if_not_root",default=True,help="When trying to access an empty default_site, if the path requested is not / then redirect to own_server (if set) instead of providing a URL box. If this is False then the URL box will be provided no matter what path was requested.") # TODO: "ownServer even if root" option, i.e. option to make host_suffix by itself go to own_server?  Or make ownServer_if_not_root permanent?  The logic that deals with off-site Location: redirects assumes the URL box will normally be at / (TODO document this?)
define('search_sites',multiple=True,help="Comma-separated list of search sites to be made available when the URL box is displayed (if default_site is empty). Each item in the list should be a URL (which will be prepended to the search query), then a space, then a short description of the site. The first item on the list is used by default; the user can specify other items by making the first word of their query equal to the first word of the short description. Additionally, if some of the letters of that first word are in parentheses, the user may specify just those letters. So for example if you have an entry http://search.example.com?q= (e)xample, and the user types 'example test' or 'e test', it will use http://search.example.com?q=test")
define("urlbox_extra_html",help="Any extra HTML you want to place after the URL box (when shown), such as a paragraph explaining what your filters do etc.")
define("wildcard_dns",default=True,help="Set this to False if you do NOT have a wildcard domain and want to process only default_site. Setting this to False does not actually prevent other sites from being processed (for example, a user could override their local DNS resolver to make up for your lack of wildcard domain); if you want to really prevent other sites from being processed then you could also set own_server to deal with unrecognised domains. Setting wildcard_dns to False does stop the automatic re-writing of links to sites other than default_site. Leave it set to True to have ALL sites' links rewritten on the assumption that you have a wildcard domain.") # will then say "(default True)"

heading("General adjustment options")
define("default_cookies",help="Semicolon-separated list of name=value cookies to send to all remote sites, for example to set preferences. Any cookies that the browser itself sends will take priority over cookies in this list. Note that these cookies are sent to ALL sites. You can set a cookie only on a specific browser by putting (browser-string) before the cookie name, e.g. (iPad)x=y will set x=y only if 'iPad' occurs in the browser string (to match more than one browser-string keyword, you have to specify the cookie multiple times).") # TODO: site-specific option
# TODO: sets of adjustments can be switched on and off at a /__settings URL ?  or leave it to the injected JS
define("headAppend",help="Code to append to the HEAD section of every HTML document that has a BODY. Use for example to add your own stylesheet links and scripts. Not added to documents that lack a BODY such as framesets.")
define("headAppendCSS",help="URL of a stylesheet for headAppend.  This option automatically generates the LINK REL=... markup for it, and also tries to delete the string '!important' from other stylesheets, to emulate setting this stylesheet as a user CSS.  You can also include one or more 'fields' in the URL, by marking them with %s and following the URL with options e.g. http://example.org/style%s-%s.css;1,2,3;A,B will allow combinations like style1-A.css or style3-B.css; in this case appropriate selectors are provided with the URL box (values may optionally be followed by = and a description), and any visitors who have not set their options will be redirected to the URL box to do so.") # TODO: fill in a default URL in the URL box when doing this ?
define("protectedCSS",help="A regular expression matching URLs of stylesheets with are \"protected\" from having their '!important' strings deleted by headAppendCSS's logic. This can be used for example if you are adding scripts to allow the user to choose alternate CSS files in place of headAppendCSS, and you wish the alternate CSS files to have the same status as the one supplied in headAppendCSS.")
define("cssName",help="A name for the stylesheet specified in headAppendCSS, such as \"High Contrast\".  If cssName is set, then the headAppendCSS stylesheet will be marked as \"alternate\", with Javascript links at the bottom of the page for browsers that lack their own CSS switching options.  If cssName begins with a * then the stylesheet is switched on by default; if cssName is not set then the stylesheet (if any) is always on.")
define("cssNameReload",multiple=True,default="IEMobile 6,IEMobile 7,IEMobile 8,Opera Mini,Opera Mobi,rekonq",help="List of (old) browsers that require alternate code for the cssName option, which is slower as it involves reloading the page on CSS switches.  Use this if the CSS switcher provided by cssName does nothing on your browser.") # Opera Mini sometimes worked and sometimes didn't; maybe there were regressions at their proxy; JS switcher needs network traffic anyway on Opera Mini so we almost might as well use the reloading version (but in Spring 2014 they started having trouble with reload() AS WELL, see cssReload_cookieSuffix below)
# Opera Mobile 10 on WM6.1 is fine with CSS switcher but it needs cssHtmlAttrs, TODO we might be able to have a list of browsers that require cssHtmlAttrs but not cssNameReload, add cssHtmlAttrs only if CSS is selected at time of page load, and make the 'off' switch remove them
# TODO: Opera/9.5 on WM6.1 document.write can corrupt the display with EITHER script; page might also display for some time before the document.writes take effect.  Suggest those users upgrade to version 10 (= Opera/9.8) ?
cssReload_cookieSuffix = "&&_adjuster_setCookie:" # enables code that works better on Opera Mini's transcoder (Spring 2014) by setting the cookie server-side. (Set to blank to use the old code. TODO: browser-dependent? make it a 'define' option?)
define("cssHtmlAttrs",help="Attributes to add to the BODY element of an HTML document when cssNameReload is in effect (or when it would be in effect if cssName were set). This is for old browsers that try to render the document first and apply CSS later. Example: 'text=\"yellow\" bgcolor=\"black\"' (not as flexible as CSS but can still make the rendering process less annoying). If headAppendCSS has \"fields\" then cssHtmlAttrs can list multiple sets of attributes separated by ; and each set corresponds with an option in the last field of headAppendCSS.") # e.g. IEMobile 7 (or Opera 10) on WM 6.1
define("headAppendRuby",default=False,help="Convenience option which adds CSS and Javascript code to the HTML body that tries to ensure simple RUBY markup displays legibly across all modern browsers; this might be useful if you used Annotator Generator to make the htmlFilter program. (The option is named 'head' because it used to add markup to the HEAD; this was moved to the BODY to work around browser bugs.)") # IEMobile 6 drops whitespace after closing tags if document HEAD contains any STYLE element, even an empty one, except via link rel=Stylesheet. Style element works OK if placed at start of body.
define("bodyAppend",help="Code to append to the BODY section of every HTML document that has one. Use for example to add a script that needs to be run after the rest of the body has been read, or to add a footer explaining how the page has been modified. See also prominentNotice.") # TODO: note that it will go at the bottom of IFRAMEs also, and suggest using something similar to prominentNotice's iframe-detection code?
define("bodyAppendGoesAfter",help="If this is set to a regular expression matching some text or HTML code that appears verbatim in the body section, the code in bodyAppend will be inserted after the last instance of this regular expression (case sensitive) instead of at the end of the body. Use for example if a site styles its pages such that the end of the body is not a legible place for a footer.") # (e.g. it would overprint some position=fixed stuff)
define("bodyPrepend",help="Code to place at the start of the BODY section of every HTML document that has one.") # May be a useful place to put some scripts. For example, a script that changes a low-vision stylesheet according to screen size might be better in the BODY than in the HEAD, because some Webkit-based browsers do not make screen size available when processing the HEAD of the starting page. # but sometimes it still goes wrong on Chromium startup; probably a race condition; might be worth re-running the script at end of page load just to make sure
define("prominentNotice",help="Text to add as a brief prominent notice to processed sites (may include HTML). If the browser has sufficient Javascript support, this will float relative to the browser window and will contain an 'acknowledge' button to hide it (for the current site in the current browsing session). Use prominentNotice if you need to add important information about how the page has been modified. Note: if you include Javascript document.write() code in prominentNotice, check that document.readyState is not 'complete' or you might find the document is erased on some website/browser combinations when a site script somehow causes your script to be re-run after the document stream is closed. In some rare cases you might also need to verify that document.cookie.indexOf('_WA_warnOK=1')==-1.") # e.g. if the site does funny things with the browser cache.  Rewriting the innerHTML manipulation to appendChild doesn't fix the need to check document.readyState
define("delete",multiple=True,help="Comma-separated list of regular expressions to delete from HTML documents. Can be used to delete selected items of Javascript and other code if it is causing trouble for your browser. Will also delete from the text of pages; use with caution.")
define("delete_css",multiple=True,help="Comma-separated list of regular expressions to delete from CSS documents (but not inline CSS in HTML); can be used to remove, for example, dimension limits that conflict with annotations you add, as an alternative to inserting CSS overrides.")
define("delete_doctype",default=False,help="Delete the DOCTYPE declarations from HTML pages. This option is needed to get some old Webkit browsers to apply multiple CSS files consistently.")
define("deleteOmit",multiple=True,default="iPhone,iPad,Android,Macintosh",help="A list of browsers that do not need the delete and delete-doctype options to be applied. If any of these strings occur in the user-agent then these options are disabled for that request, on the assumption that these browsers are capable enough to cope with the \"problem\" code. Any delete-css option is still applied however.")
define("codeChanges",help="Several lines of text specifying changes that are to be made to all HTML and Javascript code files on certain sites; use as a last resort for fixing a site's scripts. This option is best set in the configuration file and surrounded by r\"\"\"...\"\"\". The first line is a URL prefix (just \"http\" matches all), the second is a string of code to search for, and the third is a string to replace it with. Further groups of URL/search/replace lines may follow; blank lines and lines starting with # are ignored. If the 'URL prefix' starts with a * then it is instead a string to search for within the code of the document body; any documents containing this code will match; thus it's possible to write rules of the form 'if the code contains A, then replace B with C'. This processing takes place before any 'delete' option takes effect so it's possible to pick up on things that will be deleted, and it occurs after the domain rewriting so it's possible to change rewritten domains in the search/replace strings (but the URL prefix above should use the non-adjusted version).")
define("boxPrompt",default="Website to adjust",help="What to say before the URL box (when shown); may include HTML; for example if you've configured Web Adjuster to perform a single specialist change that can be described more precisely with some word other than 'adjust', you might want to set this.")
define("viewsource",default=False,help="Provide a \"view source\" option. If set, you can see a page's pre-adjustment source code, plus client and server headers, by adding \".viewsource\" to the end of a URL (after any query parameters etc)")
define("htmlonly_mode",default=True,help="Provide a checkbox allowing the user to see pages in \"HTML-only mode\", stripping out most images, scripts and CSS; this might be a useful fallback for very slow connections if a site's pages bring in many external files and the browser cannot pipeline its requests. The checkbox is displayed by the URL box, not at the bottom of every page.") # if no pipeline, a slow UPLINK can be a problem, especially if many cookies have to be sent with each request for a js/css/gif/etc.
# (and if wildcard_dns=False and we're domain multiplexing, our domain can accumulate a lot of cookies, causing requests to take more uplink bandwidth, TODO: do something about this?)
# Above says "most" not "all" because some stripping not finished (see TODO comments) and because some scripts/CSS added by Web Adjuster itself are not stripped
define("mailtoPath",default="/@mail@to@__",help="A location on every adjusted website to put a special redirection page to handle mailto: links, showing the user the contents of the link first (in case a mail client is not set up). This must be made up of URL-safe characters starting with a / and should be a path that is unlikely to occur on normal websites and that does not conflict with renderPath. If this option is empty, mailto: links are not changed. (Currently, only plain HTML mailto: links are changed by this function; Javascript-computed ones are not.)")
define("mailtoSMS",multiple=True,default="Opera Mini,Opera Mobi,Android,Phone,Mobile",help="When using mailtoPath, you can set a comma-separated list of platforms that understand sms: links. If any of these strings occur in the user-agent then an SMS link will be provided on the mailto redirection page.")

heading("External processing options")
define("htmlFilter",help="External program(s) to run to filter every HTML document. If more than one program is specified separated by # then the user will be given a choice (see htmlFilterName option). Any shell command can be used; its standard input will get the HTML (or the plain text if htmlText is set), and it should send the new version to standard output. Multiple copies of each program might be run at the same time to serve concurrent requests. UTF-8 character encoding is used. If you are not able to run external programs then you could use Python instead: in place of an external command, put a * followed by the name of a Python function that you injected into the adjuster module from a wrapper script; the function will be run in the serving thread.") # (so try to make it fast, although this is not quite so essential in WSGI mode; if you're in WSGI mode then I suggest getting the function to import any large required modules on-demand)
define("htmlFilterName",help="A name for the task performed by htmlFilter. If this is set, the user will be able to switch it on and off from the browser via a cookie and some Javascript links at the bottom of HTML pages. If htmlFilter lists two or more options, htmlFilterName should list the same number plus one (again separated by #); the first is the name of the entire category (for example \"filters\"), and the user can choose between any one of them or none at all (hence the number of options is one more than the number of filters); if this yields more than 3 options then all but the first two are hidden behind a \"More\" option on some browsers.") # TODO: non-Javascript fallback for the switcher
define("htmlJson",default=False,help="Try to detect HTML strings in JSON responses and feed them to htmlFilter. This can help when using htmlFilter with some AJAX-driven sites. IMPORTANT: Unless you also set the 'separator' option, the external program must preserve all newline characters, because multiple HTML strings in the same JSON response will be given to it separated by newlines, and the newlines of the output determine which fragment to put back where. (If you combine htmlJson with htmlText, the external program will see text in HTML in JSON as well as text in HTML, but it won't see text in HTML in JSON in HTML.)")
define("htmlText",default=False,help="Causes the HTML to be parsed, and only the text parts (not the markup) will be sent to htmlFilter. Useful to save doing HTML parsing in the external program. The external program is still allowed to include HTML markup in its output. IMPORTANT: Unless you also set the 'separator' option, the external program must preserve all newline characters, because multiple text strings will be given to it separated by newlines, and the newlines of the output determine which modified string to put back where.")
define("separator",help="If you are using htmlFilter with htmlJson and/or htmlText, you can set separator to any text string to be used as a separator between multiple items of data when passing them to the external program. By default, newlines are used for this, but you can set it to any other character or sequence of characters that cannot be added or removed by the program. (It does not matter if a website's text happens to use the separator characters.) If separator is set, not only will it be used as a separator BETWEEN items of data but also it will be added before the first and after the last item, thus allowing you to use an external program that outputs extra text before the first and after the last item. The extra text will be discarded. If however you do not set separator then the external program should not add anything extra before/after the document.")
define("leaveTags",multiple=True,default="script,style,title,textarea,option",help="When using htmlFilter with htmlText, you can set a comma-separated list of HTML tag names whose enclosed text should NOT be sent to the external program for modification. For this to work, the website must properly close these tags and must not nest them. (This list is also used for character-set rendering.)") # not including 'option' can break pages that need character-set rendering
define("stripTags",multiple=True,default="wbr",help="When using htmlFilter with htmlText, you can set a comma-separated list of HTML tag names which should be deleted if they occur in any section of running text. For example, \"wbr\" (word-break opportunity) tags (listed by default) might cause problems with phrase-based annotators.")

define("submitPath",help="If set, accessing this path (on any domain) will give a form allowing the user to enter their own text for processing with htmlFilter. The path should be one that websites are not likely to use (even as a prefix), and must begin with a slash (/). If you prefix this with a * then the * is ignored and any password set in the 'password' option does not apply to submitPath. Details of the text entered on this form is not logged by Web Adjuster, but short texts are converted to compressed GET requests which might be logged by proxies etc.") # (see comments in serve_submitPage)
define("submitBookmarklet",default=True,help="If submitPath is set, and if browser Javascript support seems sufficient, then add one or more 'bookmarklets' to the 'Upload Text' page (named after htmlFilterName if provided), allowing the user to quickly upload text from other sites. This might be useful if for some reason those sites cannot be made to go through Web Adjuster directly. The bookmarklets should work on modern desktop browsers and on iOS and Android; they should cope with frames and with Javascript-driven changes to a page, and an option is provided to additionally place the page into a frameset so that links to other pages on the same site can be followed without explicitly reactivating the bookmarklet (but this does have disadvantages - page must be reloaded + URL display gets 'stuck' - so it's left to the user to choose).") # (and if the other pages check their top.location, things could break there as well)
define("submitBookmarkletFilterJS",default=r"!c.nodeValue.match(/^[ -~\s]*$/)",help="A Javascript expression that evaluates true if a DOM text node 'c' should be processed by the 'bookmarklet' Javascript when submitPath and submitBookmarklet are set. To process ALL text, set this option to c.nodeValue.length, but if your htmlFilter will not change certain kinds of text then you can make the Javascript run more efficiently by not processing these (quote the expression carefully). The default setting will not process text that is all ASCII.") # + whitespace.  TODO: add non-ascii 'smart punctuation'? entered as Unicode escapes, or rely on serving the script as utf-8. (Previously said "To process ALL text, simply set this option to 'true'", but that can have odd effects on some sites' empty nodes. Saying c.nodeValue.length for now; c.nodeValue.match(/[^\s]/) might be better but needs more quoting explanation. Could change bookmarkletMainScript so it alters the DOM only if replacements[i] != oldTexts[i], c.f. annogen's android code, but that would mean future passes would re-send all the unchanged nodes cluttering the XMLHttpRequests especially if they fill a chunk - annogen version has the advantage of immediate local processing)
define("submitBookmarkletChunkSize",default=1024,help="Specifies the approximate number of characters at a time that the 'bookmarklet' Javascript will send to the server if submitPath and submitBookmarklet are set. Setting this too high could impair browser responsiveness, but too low will be inefficient with bandwidth and pages will take longer to finish.")

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
define("pdftotext",default=False,help="If True, add links to run PDF files through the 'pdftotext' program (which must be present if this is set). A text link will be added just after any PDF link that is found, so that you have a choice of downloading PDF or text; note that pdftotext does not always manage to extract all text (you can use --pdfomit to specify URL patterns that should not get text links). The htmlJson setting will also be applied to the PDF link finder, and see also the guessCMS option.")
define("pdfomit",help="A comma-separated list of regular expressions which, if any are found in a PDF link's URL, will result in a text link not being generated for that PDF link (although a conversion can still be attempted if a user manually enters the modified URL).  Use this to avoid confusion for PDF files you know cannot be converted.")
define("epubtotext",default=False,help="If True, add links to run EPUB files through Calibre's 'ebook-convert' program (which must be present), to produce a text-only option (or a MOBI option if a Kindle is in use). A text link will be added just after any EPUB link that is found, so that you have a choice of downloading EPUB or text. The htmlJson setting will also be applied to the EPUB link finder, and see also the guessCMS option.")
# pdftotext and epubtotext both use temporary files, which are created in the system default temp directory unless overridden by environment variables TMPDIR, TEMP or TMP, TODO: do we want an override for NamedTemporaryFile's dir= option ourselves?  (/dev/shm might make more sense on some Flash-based systems, although filling the RAM and writing to swap might do more damage than writing files in /tmp if it gets big; also hopefully some OS's won't actually write anything if the file has been deleted before the buffer needed to be flushed (TODO: check this))
define("epubtozip",default=False,help="If True, add links to download EPUB files renamed to ZIP, as a convenience for platforms that don't have EPUB readers but can open them as ZIP archives and display the XHTML files they contain. The htmlJson setting will also be applied to the EPUB link finder, and see also the guessCMS option.") # TODO: option to cache the epub file and serve its component files individually, so other transforms can be applied and for platforms without ZIP capabilities
define("guessCMS",default=False,help="If True, then the pdftotext, epubtotext and epubtozip options attempt to guess if a link is pointing to a PDF or EPUB file via a Content Management System (i.e. the URL does not end in .pdf or .epub, but contains something like ?format=PDF)") # (doesn't seem to work very well with the askBitrate option)
define("pdfepubkeep",default=200,help="Number of seconds to keep any generated text files from PDF and EPUB.  If this is 0, the files will be deleted immediately, but that might be undesirable: if a mobile phone browser has a timeout that takes effect before ebook-convert has finished (this can sometimes be the case with Opera Mini for example), it might be best to allow the user to wait a short time and re-submit the request, this time getting a cached response.") # Opera Mini's opera:config can set the loading timeout to longer, default is 30 seconds.
define("waitpage",default=True,help="If the browser seems to be an interactive one, generate a 'please wait' page while converting PDF or EPUB files to text. Not effective if pdfepubkeep is set too low.") # TODO: mp3 also? (would need to add MP3s to pdfepubkeep)

heading("Character rendering options")
# TODO: option to add a switch at top of page ?
define("render",default=False,help="Whether to enable the character-set renderer. This functionality requires the Python Imaging Library and suitable fonts. The settings of htmlJson and leaveTags will also be applied to the renderer. Text from computed Javascript writes might not be rendered as images.") # ("computed" as in not straight from a JSON document.  TODO: could write a piece of JS that goes through the DOM finding them? ditto any JS alterations that haven't been through htmlFilter, although you'd have to mark the ones that have and this could be filter-dependent)
define("renderFont",help="The font file to use for the character-set renderer (if enabled). This should be a font containing all the characters you want to render, and it should be in .TTF, .OTF or other Freetype-supported format (.PCF is sometimes possible if renderSize is set correctly, e.g. 16 for wenquanyi_12pt.pcf)") # TODO: different fonts for different Unicode ranges? (might be hard to auto-detect missing characters)
define("renderInvert",default=False,help="If True, the character-set renderer (if enabled) will use a black background. Useful when you are also adding a stylesheet with a dark background.")
define("renderSize",default=20,help="The height (in pixels) to use for the character-set renderer if it is enabled.")
define("renderPath",default="/@_",help="The location on every adjusted website to put the character-set renderer's images, if enabled. This must be made up of URL-safe characters starting with a / and should be a short path that is unlikely to occur on normal websites.")
define("renderFormat",default="png",help="The file format of the images to be created by the character-set renderer if it is enabled, for example 'png' or 'jpeg'.")
define("renderRange",multiple=True,help="The lowest and highest Unicode values to be given to the character-set renderer if it is enabled. For example 3000:A6FF for most Chinese characters. Multiple ranges are allowed. Any characters NOT in one of the ranges will be passed to the browser to render. If the character-set renderer is enabled without renderRange being set, then ALL text will be rendered to images.")
define("renderOmit",multiple=True,default="iPhone,iPad,Android,Macintosh,Windows NT 6,Windows Phone OS,Lynx/2",help="A list of platforms that do not need the character-set renderer. If any of these strings occur in the user-agent then the character set renderer is turned off even if it is otherwise enabled, on the assumption that these platforms either have enough fonts already, or wouldn't show the rendered images anyway.") # (Win: Vista=6.0 7=6.1 8=6.2 reportedly don't need language packs for display) (Lynx: being careful by specifying /2 to try to avoid false positives; don't list w3m as some versions can do graphics; not sure about Links/ELinks etc)
define("renderOmitGoAway",default=False,help="If set, any browsers that match renderOmit will not be allowed to use the adjuster. This is for servers that are set to do character rendering only and do not have enough bandwidth for people who don't need this function and just want a proxy.") # (See also the extended syntax of the headAppendCSS option, which forces all users to choose a stylesheet, especially if cssName is not set; that might be useful if the server's sole purpose is to add stylesheets and you don't want to provide a straight-through service for non-stylesheet users.)
define("renderCheck",help="If renderOmit does not apply to the browser, it might still be possible to check for native character-set support via Javascript. renderCheck can be set to the Unicode value of a character to be checked (try 802F for complete Chinese support); if the browser reports its width differently from known unprintable characters, we assume it won't need our renderer.") # 802F shouldn't create false positives in environments that support only GB2312, only Big5, only SJIS or only KSC instead of all Chinese. It does have GB+ and Big5+ codes (and also demonstrates that we want a hex number). If browser's "unprintable character" glyph happens to be the same width as renderCheck anyway then we could have a false negative, but that's better than a false positive and the user can still switch it off manually if renderName is left set.
define("renderNChar",default=1,help="The maximum number of characters per image to be given to the character-set renderer if it is enabled. Keeping this low means the browser cache is more likely to be able to re-use images, but some browsers might struggle if there are too many separate images. Don't worry about Unicode \"combining diacritic\" codes: any found after a character that is to be rendered will be included with it without counting toward the renderNChar limit and without needing to be in renderRange.")
define("renderWidth",default=0,help="The maximum pixel width of a 'word' when using the character-set renderer. If you are rendering a language that uses space to separate words, but are using only one or two characters per image, then the browser might split some words in the middle. Setting renderWidth to some value other than 0 can help to prevent this: any word narrower than renderWidth will be enclosed in a <nobr> element. (This will however be ineffective if your stylesheet overrides the behaviour of <nobr>.) You should probably not set renderWidth if you intend to render languages that do not separate words with spaces.")
define("renderDebug",default=False,help="If the character-set renderer is having problems, try to insert comments in the HTML source to indicate why.  The resulting HTML is not guaranteed to be well-formed, but it might help you debug a misbehaving htmlFilter.  This option may also insert comments in bad HTML before the htmlFilter stage even when the renderer is turned off.")
define("renderName",default="Fonts",help="A name for a switch that allows the user to toggle character set rendering on and off from the browser (via a cookie and Javascript links at the bottom of HTML pages); if set to the empty string then no switch is displayed. At any rate none is displayed when renderOmit applies.") # TODO: non-Javascript fallback for the switcher

heading("Dynamic DNS options")
define("ip_change_command",help="An optional script or other shell command to launch whenever the public IP address changes. The new IP address will be added as a parameter; ip_query_url must be set to make this work. The script can for example update any Dynamic DNS services that point to the server.")
define("ip_query_url",help="URL that will return your current public IP address, as a line of text with no markup added. Used for the ip_change_command option. You can set up a URL by placing a CGI script on a server outside your network and having it do: echo Content-type: text/plain;echo;echo $REMOTE_ADDR")
define("ip_query_url2",help="Optional additional URL that might sometimes return your public IP address along with other information. This can for example be a status page served by a local router (http://user:password@192.168... is accepted, and if the password is the name of an existing file then its contents are read instead). If set, the following behaviour occurs: Once ip_query_interval has passed since the last ip_query_url check, ip_query_url2 will be queried at an interval of ip_query_interval2 (which can be short), to check that the known IP is still present in its response. Once the known IP is no longer present, ip_query_url will be queried again. This arrangement can reduce the load on ip_query_url as well as providing a faster response to IP changes, while not completely trusting the local router to report the correct IP at all times. See also ip_query_aggressive if the router might report an IP change before connectivity is restored.") # (If using filename then its contents will be re-read every time the URL is used; this might be useful for example if the router password can change)
define("ip_check_interval",default=8000,help="Number of seconds between checks of ip_query_url for the ip_change_command option")
define("ip_check_interval2",default=60,help="Number of seconds between checks of ip_query_url2 (if set), for the ip_change_command option")
define("ip_query_aggressive",default=False,help="If a query to ip_query_url fails with a connection error or similar, keep trying again until we get a response. This is useful if the most likely reason for the error is that our ISP is down: we want to get the new IP just as soon as we're back online. However, if the error is caused by a problem with ip_query_url itself then this option can lead to excessive traffic, so use with caution. (Log entries are written when this option takes effect, and checking the logs is advisable.)")
define("ip_force_interval",default=7*24*3600,help="Number of seconds before ip_change_command (if set) is run even if there was no IP change.  This is to let Dynamic DNS services know that we are still around.  Set to 0 to disable forced updates (a forced update will occur on server startup anyway), otherwise an update will occur on the next IP check after ip_force_interval has elapsed.")

heading("Speedup options")
define("useLXML",default=False,help="Use the LXML library for parsing HTML documents. This is usually faster, but it can fail if your system does not have a good installation of LXML and its dependencies. Use of LXML libraries may also result in more changes to all HTML markup: this should be harmless for browsers, but beware when using options like bodyAppendGoesAfter then you might or might not be dealing with the original HTML depending on which filters are switched on.") # (hence bodyAppendGoesAfter now takes regexps as of adjuster 0.1836) / dependencies: did have ", or if the websites you visit are badly broken" but it turns out some breakages are actually better handled by LXML than by HTMLParser, e.g. <div id=something">
define("renderBlocks",default=False,help="Treat all characters rendered by the character-set renderer as \"blocks\" that are guaranteed to have the same dimensions (true for example if you are using the renderer for Chinese characters only). This is faster than checking words individually, but it may produce incorrect HEIGHT and WIDTH attributes if given a range of characters whose dimensions do differ.") # TODO: blocksRange option for if want to render some that do and some that don't? (but profile it: PIL's getsize just might turn out to be quicker than the high-level range-check code)
define("fasterServer",help="Address:port of another instance of Web Adjuster to which we forward all traffic whenever it is available. When the other instance is not available, traffic will be handled by this one. Use for example if you have a slower always-on machine and a faster not-always-on machine and you want the slower machine to delegate to the faster machine when available. See also ipTrustReal.")
define("ipTrustReal",help="IP address of a machine that we trust, for example a machine that is using us as fasterServer. Any traffic coming from this machine with an X-Real-Ip header will be logged as though it originated at the value of its X-Real-Ip header. Setting this to * will cause X-Real-Ip to be trusted from ANY connection.") # , which might be useful in an environment where you know the adjuster can be reached only via a proxy but the proxy's address can change; see also trust_XForwardedFor. (TODO: multiple IPs option like ip_messages?  but might need to make it ipv6 ready)
define("trust_XForwardedFor",default=False,help="Like ipTrustReal but trusts X-Forwarded-For header from any IP if set to True (use this in an environment where the adjuster can be reached only via a load balancer etc)")
define("fasterServerNew",default=True,help="If fasterServer is set, assume it is running Web Adjuster v0.17 or later and use a more lightweight method of checking its availability. You might need to set this to False if for some reason you can't upgrade the fasterServer first.") # (don't do auto-fallback as that creates unnecessary extra traffic, plus sending an unrecognized ping2 could clutter logs)
define("machineName",help="A name for the current machine to insert into the \"Server\" HTTP header for adjusted requests, for example to let users know if it's your faster or your slower machine that's currently serving them (although they'd need to inspect the headers to find out)")
define("redirectFiles",default=False,help="If, when not functioning as a \"real\" HTTP proxy, a URL is received that looks like it requires no processing on our part (e.g. an image or downloadable file that the user does not want converted), and if this is confirmed via a HEAD request to the remote server, then redirect the browser to fetch it directly and not via Web Adjuster. This takes bandwidth off the adjuster server, and should mean faster downloads, especially from sites that are better connected than the adjuster machine. However it might not work with sites that restrict \"deep linking\". (As a precaution, the confirmatory HEAD request is sent with a non-adjusted Referer header to simulate what the browser would send if fetching directly. If this results in an HTML \"Referer denied\" message then Web Adjuster will proxy the request in the normal way. This precaution might not detect ALL means of deep-linking denial though.)") # e.g. cookie-based, or serving an image but not the real one.  But it works with Akamai-based assets servers as of 2013-09 (but in some cases you might be able to use codeChanges to point these requests back to the site's original server instead of the Akamai one, if the latter just mirrors the former which is still available, and therefore save having to proxy the images.  TODO: what if you can't do that but you can run another service on a higher bandwidth machine that can cache them, but can't run the adjuster on the higher-bandwidth machine; can we redirect?)
# If adjuster machine is running on a home broadband connection, don't forget the "uplink" speed of that broadband is likely to be lower than the "downlink" speed; the same should not be the case of a site running at a well-connected server farm.  There's also extra delay if Web Adjuster has to download files first (which might be reduced by implementing streaming).  Weighed against this is the extra overhead the browser has of repeating its request elsewhere, which could be an issue if the file is small and the browser's uplink is slow; in that case fetching it ourselves might be quicker than having the browser repeat the request; see TODO comment elsewhere about minimum content length before redirectFiles.
# TODO: for Referer problems in redirectFiles, if we're not on HTTPS, could redirect to an HTTPS page (on a separate private https server, or https://www.google.com/url?q= but they might add checks) which then redirs to the target HTTP page, but that might not strip Referer on MSIE 7 etc, may have to whitelist browsers+versions for it, or test per-request but that wld lead to 4 redirects per img instead of 2 although cld cache (non-empty) ok-browser-strings (and hold up other requests from same browser until we know or have timed out ??); do this only if sendHead returns false but sendHead with proper referer returns ok (and cache a few sites where this is the case so don't have to re-test) ??  also it might not work in places where HTTPS is forbidden

define("upstream_guard",default=True,help="Modify scripts and cookies sent by upstream sites so they do not refer to the cookie names that our own scripts use. This is useful if you chain together multiple instances of Web Adjuster, such as for testing another installation without coming out of your usual proxy. If however you know that this instance will not be pointed to another, you can set upstream_guard to False to save some processing.")
define("skipLinkCheck",multiple=True,help="Comma-separated list of regular expressions specifying URLs to which we won't try to add or modify links for the pdftotext, epubtotext, epubtozip, askBitrate or mailtoPath options.  This processing can take some time on large index pages with thousands of links; if you know that none of them are PDF, EPUB, MP3 or email links, or if you don't mind not processing any that are, then it saves time to skip this step for those pages.") # TODO: it would be nice to have a 'max links on the page' limit as an alternative to a list of URL patterns

define("extensions",help="Name of a custom Python module to load to handle certain requests; this might be more efficient than setting up a separate Tornado-based server. The module's handle() function will be called with the URL and RequestHandler instance as arguments, and should return True if it processed the request, but anyway it should return as fast as possible. This module does NOT take priority over forwarding the request to fasterServer.")

define("loadBalancer",default=False,help="Set this to True if you have a default_site set and you are behind any kind of \"load balancer\" that works by issuing a GET / with no browser string. This option will detect such requests and avoid passing them to the remote site.")

# THIS MUST BE THE LAST SECTION because it continues into
# the note below about Tornado logging options.  (The order
# of define()s affects the HTML order only; --help will be
# sorted alphabetically by Tornado.)
heading("Logging options")
define("renderLog",default=False,help="Whether or not to log requests for character-set renderer images. Note that this can generate a LOT of log entries on some pages.")
define("logUnsupported",default=False,help="Whether or not to log attempts at requests using unsupported HTTP methods. Note that this can sometimes generate nearly as many log entries as renderLog if some browser (or malware) tries to do WebDAV PROPFIND requests on each of the images.")
define("logRedirectFiles",default=True,help="Whether or not to log requests that result in the browser being simply redirected to the original site when the redirectFiles option is on.") # (Since this still results in a HEAD request being sent to the remote site, this option defaults to True in case you need it to diagnose "fair use of remote site" problems)
define("ownServer_useragent_ip",default=False,help="If own_server is set, and that server cannot be configured to log the X-Real-Ip header we set when we proxy for it, you can if you wish turn on this option, which will prepend the real IP to the User-Agent header on the first request of each connection (most servers can log User-Agent). This is slightly dangerous: fake IPs can be inserted into the log if keep-alive is used.") # (and it might break some user-agent detection)
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
    # (Tornado 2 just calls the module-level print_help, but Tornado 3 includes some direct calls to the object's method, so we have to override the latter.  Have to use __dict__ because they override __setattr__.)
    import pydoc,cStringIO ; pydoc.pager # ensure present
    def new_top(*args):
        dat = cStringIO.StringIO()
        tornado.options.options.old_top(dat)
        pydoc.pager(dat.getvalue())
    tornado.options.options.__dict__['old_top'] = tornado.options.options.print_help
    tornado.options.options.__dict__['print_help'] = new_top
except: raise

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
      port=":"+str(options.publicPort) # might or might not be present in the user's request
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
      port=":"+str(options.publicPort) # the port to advertise
      orig_requested_host = requested_host
      if requested_host.endswith(port): requested_host=requested_host[:-len(port)]
      if options.publicPort==80: port=""
      for h in options.host_suffix.split("/"):
        if (requested_host == h and options.default_site) or requested_host.endswith("."+h): return h+port
    if options.wildcard_dns and not '/' in options.host_suffix: return options.host_suffix+port
    return "somewhere" # ?
def publicPortStr():
    if options.publicPort==80: return ""
    else: return ":"+str(options.publicPort)
def convert_to_requested_host(real_host,cookie_host=None):
    # Converts the actual host name into the host name that
    # the user should request to get it through us
    if not real_host: return ""
    port = publicPortStr()
    if options.default_site:
      n=0
      for i in options.default_site.split("/"):
        if not i: i=cookie_host
        if real_host == i:
            return hostSuffix(n)+port
        n += 1
    if not options.wildcard_dns: return real_host # leave the proxy
    else: return dedot(real_host)+"."+hostSuffix()+port

# RFC 2109: A Set-Cookie from request-host y.x.example.com for Domain=.example.com would be rejected, because H is y.x and contains a dot.
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

def errExit(msg):
    # Exit with an error message BEFORE server start
    try:
        if options.background: logging.error(msg)
        # in case run from crontab w/out output (and e.g. PATH not set properly)
        # (but don't do this if not options.background, as log_to_stderr is likely True and it'll be more cluttered than the simple sys.stderr.write below)
    except: pass # options or logging not configured yet
    sys.stderr.write(msg)
    sys.exit(1)

def parse_command_line(final):
    if len(tornado.options.parse_command_line.func_defaults)==1: # Tornado 2.x
        tornado.options.parse_command_line()
    else: tornado.options.parse_command_line(final=final)
def parse_config_file(cfg, final): # similarly
    if not tornado.options.parse_config_file.func_defaults: # Tornado 2.x
        tornado.options.parse_config_file(cfg)
    else: tornado.options.parse_config_file(cfg,final=final)

def readOptions():
    # Reads options from command line and/or config files
    parse_command_line(False)
    configsDone = set()
    if not options.config: options.config=os.environ.get("ADJUSTER_CFG","") # must do HERE rather than setting default= above, or options.config=None below might not work
    while options.config and (options.config,os.getcwd()) not in configsDone:
        # sys.stderr.write("Reading config from "+options.config+"\n")
        config = options.config ; options.config=None # allow it to be overridden on the next file
        oldDir = os.getcwd()
        config2 = changeConfigDirectory(config)
        try: open(config2)
        except: errExit("Cannot open configuration file %s (current directory is %s)\n" % (config2,os.getcwd()))
        parse_config_file(config2,False)
        configsDone.add((config,oldDir))
    parse_command_line(True) # need to do this again to ensure logging is set up for the *current* directory (after any chdir's while reading config files)

def preprocessOptions():
    if options.host_suffix==getfqdn_default: options.host_suffix = socket.getfqdn()
    if type(options.mailtoSMS)==type(""): options.mailtoSMS=options.mailtoSMS.split(',')
    if type(options.leaveTags)==type(""): options.leaveTags=options.leaveTags.split(',')
    if type(options.stripTags)==type(""): options.stripTags=options.stripTags.split(',')
    create_inRenderRange_function(options.renderRange)
    if type(options.renderOmit)==type(""): options.renderOmit=options.renderOmit.split(',')
    if options.renderOmitGoAway:
        if options.renderCheck: errExit("Setting both renderOmitGoAway and renderCheck is not yet implemented: if renderOmitGoAway is set then the renderOmit-matching visitors are turned away before getting as far as renderCheck.  Please unset one of them.")
        options.renderName = "" # so it can't be switched on/off (because there's not a lot of point in switching it off if we're renderOmitGoAway; TODO: document this behaviour?)
    if type(options.deleteOmit)==type(""): options.deleteOmit=options.deleteOmit.split(',')
    if type(options.cssName)==type(""): options.cssName=options.cssName.replace('"',"&quot;") # for embedding in JS
    if type(options.cssNameReload)==type(""): options.cssNameReload=options.cssNameReload.split(',')
    if type(options.search_sites)==type(""): options.search_sites=options.search_sites.split(',')
    if type(options.ipNoLog)==type(""): options.ipNoLog=options.ipNoLog.split(',')
    if type(options.delete)==type(""): options.delete=options.delete.split(',')
    if type(options.delete_css)==type(""): options.delete_css=options.delete_css.split(',')
    if type(options.prohibit)==type(""): options.prohibit=options.prohibit.split(',')
    if type(options.skipLinkCheck)==type(""): options.skipLinkCheck=options.skipLinkCheck.split(',')
    global viaName,serverName,serverName_html
    viaName = program_name[:program_name.index("(c)")].strip() # Web Adjuster vN.NN
    if options.machineName: serverName = viaName + " on "+options.machineName
    else: serverName = viaName
    serverName_html = re.sub(r"([0-9])([0-9])",r"\1<span></span>\2",serverName) # stop mobile browsers interpreting the version number as a telephone number
    global upstream_proxy_host, upstream_proxy_port
    upstream_proxy_host = upstream_proxy_port = None
    if options.upstream_proxy:
        try: import pycurl
        except ImportError: errExit("upstream_proxy requires pycurl (try sudo pip install pycurl)\n")
        if not ':' in options.upstream_proxy: options.upstream_proxy += ":80"
        upstream_proxy_host,upstream_proxy_port = options.upstream_proxy.split(':')
        upstream_proxy_port = int(upstream_proxy_port)
    global codeChanges ; codeChanges = []
    if options.codeChanges:
      ccLines = [x for x in options.codeChanges.split("\n") if x and not x.startswith("#")]
      while ccLines:
        if len(ccLines)<3: errExit("codeChanges must be a multiple of 3 lines (see --help)\n")
        codeChanges.append(tuple(ccLines[:3]))
        ccLines = ccLines[3:]
    if options.real_proxy: options.open_proxy=True
    if not options.password and not options.open_proxy: errExit("Please set a password, or use --open_proxy.\n(Try --help for help; did you forget a --config=file?)\n")
    if options.htmlFilter and '#' in options.htmlFilter and not len(options.htmlFilter.split('#'))+1 == len(options.htmlFilterName.split('#')): errExit("Wrong number of #s in htmlFilterName for this htmlFilter setting")
    if not options.publicPort:
        options.publicPort = options.port
    if options.pdftotext and not "pdftotext version" in os.popen4("pdftotext -h")[1].read(): errExit("pdftotext command does not seem to be usable\nPlease install it, or unset the pdftotext option\n")
    if options.epubtotext and not "calibre" in os.popen4("ebook-convert -h")[1].read(): errExit("ebook-convert command does not seem to be usable\nPlease install calibre, or unset the epubtotext option\n")
    global extensions
    if options.extensions:
        extensions = __import__(options.extensions)
    else:
        class E:
            def handle(*args): return False
        extensions = E()
    global ownServer_regexp
    if options.ownServer_regexp:
        if not options.own_server: errExit("Cannot set ownServer_regexp if own_sever is not set\n")
        ownServer_regexp = re.compile(options.ownServer_regexp)
    else: ownServer_regexp = None
    global ipMatchingFunc
    if options.ip_messages: ipMatchingFunc=ipv4ranges_func(options.ip_messages)
    else: ipMatchingFunc = None
    global submitPathIgnorePassword
    if options.submitPath and options.submitPath.startswith('*'):
        submitPathIgnorePassword = True
        options.submitPath = options.submitPath[1:]
    else: submitPathIgnorePassword = False
    if options.submitPath and not options.htmlText: errExit("submitPath only really makes sense if htmlText is set (or do you want users to submit actual HTML?)") # TODO: allow this? also with submitBookmarklet ??
    if not options.submitPath: options.submitBookmarklet = False
    if options.submitBookmarklet and '_IHQ_' in options.submitPath: errExit("For implementation reasons, you cannot have the string _IHQ_ in submitPath when submitBookmarklet is on.") # Sorry.  See TODO in 'def bookmarklet'
    global upstreamGuard, cRecogniseAny, cRecognise1
    upstreamGuard = set() ; cRecogniseAny = set() ; cRecognise1 = set() # cRecognise = cookies to NOT clear at url box when serving via adjust_domain_cookieName; upstreamGuard = cookies to not pass to upstream (and possibly rename if upstream sets them)
    if options.password:
        upstreamGuard.add(password_cookie_name)
        cRecogniseAny.add(password_cookie_name)
    if options.cssName:
        upstreamGuard.add("adjustCssSwitch")
        cRecognise1.add("adjustCssSwitch")
    if options.htmlFilterName:
        upstreamGuard.add("adjustNoFilter")
        cRecognise1.add("adjustNoFilter")
    if options.renderName:
        upstreamGuard.add("adjustNoRender")
        cRecognise1.add("adjustNoRender")
    if options.prominentNotice:
        upstreamGuard.add("_WA_warnOK")
        cRecognise1.add("_WA_warnOK")
    if options.htmlonly_mode:
        upstreamGuard.add(htmlmode_cookie_name)
        cRecognise1.add(htmlmode_cookie_name)
    if options.ip_messages:
        upstreamGuard.add(seen_ipMessage_cookieName)
        cRecognise1.add(seen_ipMessage_cookieName)
    h = options.headAppendCSS
    if h and '%s' in h:
        if not ';' in h: errExit("If putting %s in headAppendCSS, must also put ; with options (please read the help text)")
        if options.default_site: errExit("Cannot set default_site when headAppendCSS contains options, because we need the URL box to show those options") # TODO: unless we implement some kind of inline setting, or special options URL ?
        if options.cssHtmlAttrs and ';' in options.cssHtmlAttrs and not len(options.cssHtmlAttrs.split(';'))==len(h.rsplit(';',1)[1].split(',')): errExit("Number of choices in headAppendCSS last field does not match number of choices in cssHtmlAttrs")
        for n in range(len(h.split(';'))-1):
            upstreamGuard.add("adjustCss"+str(n)+"s")
            cRecogniseAny.add("adjustCss"+str(n)+"s")
    if options.useLXML: check_LXML()

def serverControl():
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

def make_WSGI_application():
    global errExit, wsgi_mode, runFilter, sync_runFilter
    wsgi_mode = True ; runFilter = sync_runFilter
    def errExit(m): raise Exception(m)
    global main
    def main(): raise Exception("Cannot run main() after running make_WSGI_application()")
    preprocessOptions()
    for opt in 'config user address background restart stop install watchdog browser ip_change_command fasterServer ipTrustReal renderLog logUnsupported ipNoLog whois own_server ownServer_regexp'.split(): # also 'port' 'logRedirectFiles' 'squashLogs' but these have default settings so don't warn about them
        if eval('options.'+opt):
            sys.stderr.write("Warning: '%s' option is ignored in WSGI mode\n" % opt)
    options.own_server = "" # for now, until we get forwardFor to work (TODO, and update the above list of ignored options accordingly)
    import tornado.wsgi
    return tornado.wsgi.WSGIApplication([(r"(.*)",SynchronousRequestForwarder)])

def main():
    readOptions() ; preprocessOptions() ; serverControl()
    application = Application([(r"(.*)",RequestForwarder,{})],log_function=accessLog,gzip=True)
    if not hasattr(application,"listen"): errExit("Your version of Tornado is too old.  Please install version 2.x.\n")
    if fork_before_listen and options.background:
        sys.stderr.write("%s\nLicensed under the Apache License, Version 2.0\nChild will listen on port %d\n(can't report errors here as this system needs early fork)\n" % (program_name,options.port)) # (need some other way of checking it really started)
        unixfork()
    for portTry in [5,4,3,2,1,0]:
      try:
          application.listen(options.port,options.address)
          break
      except:
        if portTry:
            time.sleep(0.5) ; continue
        # tried 6 times over 3 seconds, can't open the port (either the other process is taking a long time to stop or something)
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
    try: os.setpgrp() # for killpg later
    except: pass
    if options.browser: IOLoop.instance().add_callback(runBrowser)
    if options.watchdog: WatchdogPings(watchdog)
    if options.fasterServer:
        if not ':' in options.fasterServer: options.fasterServer += ":80" # needed for the new code
        logging.getLogger("tornado.general").disabled=1 # needed to suppress socket-level 'connection refused' messages from ping2 code in Tornado 3
        class NoConErrors:
            def filter(self,record): return not record.getMessage().startswith("Connect error on fd")
        logging.getLogger().addFilter(NoConErrors()) # ditto in Tornado 2 (which uses the root logger) (don't be tempted to combine this by setting tornado.general to a filter, as the message might change in future Tornado 3 releases)
        IOLoop.instance().add_callback(checkServer)
    if options.ip_query_url and options.ip_change_command:
        # check for user:password@ in ip_query_url2
        global ip_query_url2,ip_query_url2_user,ip_query_url2_pwd,ip_url2_pwd_is_fname
        ip_query_url2 = options.ip_query_url2
        ip_query_url2_user=ip_query_url2_pwd=ip_url2_pwd_is_fname=None
        if ip_query_url2:
            netloc = urlparse.urlparse(ip_query_url2).netloc
            if '@' in netloc:
                auth,rest = netloc.split('@',1)
                ip_query_url2 = ip_query_url2.replace(netloc,rest,1)
                ip_query_url2_user,ip_query_url2_pwd = auth.split(':',1)
                ip_url2_pwd_is_fname = os.path.isfile(ip_query_url2_pwd)
        # and start the updater
        Dynamic_DNS_updater()
    try:
        import signal
        signal.signal(signal.SIGTERM, stopServer)
    except: pass # signal not supported on this platform?
    if options.background: logging.info("Server starting")
    else: set_title("adjuster")
    try: IOLoop.instance().start()
    except KeyboardInterrupt:
        if options.background: logging.info("SIGINT received")
        else: sys.stderr.write("\nKeyboard interrupt\n")
    # gets here after stopServer (e.g. got SIGTERM from a --stop, or options.browser and the browser finished)
    if options.background: logging.info("Server shutdown")
    else: sys.stderr.write("Adjuster shutdown\n")
    if options.watchdog:
        options.watchdog = 0 # tell any separate_thread() to stop (that thread is not counted in helper_thread_count)
        watchdog.write('V') # this MIGHT be clean exit, IF the watchdog supports it (not all of them do, so it might not be advisable to use the watchdog option if you plan to stop the server without restarting it)
        watchdog.close()
    if helper_thread_count:
        msg = "Terminating %d runaway helper threads" % (helper_thread_count,)
        # in case someone needs our port quickly.
        # Most likely "runaway" thread is ip_change_command if you did a --restart shortly after the server started.
        # TODO it would be nice if the port can be released at the IOLoop.instance.stop, and make sure os.system doesn't dup any /dev/watchdog handle we might need to release, so that it's not necessary to stop the threads
        if options.background: logging.info(msg)
        else: sys.stderr.write(msg)
        try:
            import signal
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            os.killpg(os.getpgrp(),signal.SIGTERM)
        except: pass
        os.abort()

def set_title(t):
  if not (hasattr(sys.stderr,"isatty") and sys.stderr.isatty()): return
  import atexit
  if t: atexit.register(set_title,"")
  term = os.environ.get("TERM","")
  is_xterm = "xterm" in term
  is_screen = (term=="screen" and os.environ.get("STY",""))
  is_tmux = (term=="screen" and os.environ.get("TMUX",""))
  if is_xterm or is_tmux: sys.stderr.write("\033]0;%s\007" % (t,)) # ("0;" sets both title and minimised title, "1;" sets minimised title, "2;" sets title.  Tmux takes its pane title from title (but doesn't display it in the titlebar))
  elif is_screen: os.system("screen -X title \"%s\"" % (t,))

def dropPrivileges():
    if options.user and not os.getuid():
        # need to drop privileges
        import pwd ; pwd=pwd.getpwnam(options.user)
        os.setuid(pwd[2])
        # and help our external programs:
        os.environ['HOME'] = pwd[5] # (so they don't try to load root's preferences etc)
        os.environ['USER']=os.environ['LOGNAME']=options.user

fork_before_listen = not 'linux' in sys.platform

def unixfork():
    if os.fork(): sys.exit()
    os.setsid()
    if os.fork(): sys.exit()
    devnull = os.open("/dev/null", os.O_RDWR)
    for fd in range(3): os.dup2(devnull,fd) # commenting out this line will let you see stderr after the fork (TODO debug option?)
    
def stopOther():
    import commands,signal
    out = commands.getoutput("lsof -iTCP:"+str(options.port)+" -sTCP:LISTEN") # TODO: lsof can hang if ANY programs have files open on stuck remote mounts etc, even if this is nothing to do with TCP connections.  -S 2 might help a BIT but it's not a solution.  Linux's netstat -tlp needs root, and BSD's can't show PIDs.  Might be better to write files or set something in the process name.
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
    global helper_thread_count
    helper_thread_count += 1
    address = getWhois(ip)
    logger.thread_running = False
    if address: IOLoop.instance().add_callback(lambda *args:logging.info("whois "+ip+": "+address))
    helper_thread_count -= 1

class BrowserLogger:
  def __init__(self):
    # Do NOT read options here - they haven't been read yet
    self.lastBrowser = None
    self.lastIp = self.lastMethodStuff = None
    self.whoisLogger = WhoisLogger()
  def __call__(self,req):
    if req.request.remote_ip in options.ipNoLog: return
    try: ch = req.cookie_host()
    except: ch = None # shouldn't happen
    req=req.request
    if hasattr(req,"suppress_logging"): return
    if req.method not in the_supported_methods and not options.logUnsupported: return
    if req.method=="CONNECT" or req.uri.startswith("http://"): host="" # URI will have everything
    elif hasattr(req,"suppress_logger_host_convert"): host = req.host
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
        # Date (as YYMMDD) and time are already be included in Tornado logging format, a format we don't want to override, especially as it has 'start of log string syntax highlighting' on some platforms
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
        msg = ip+r+browser
    else: msg = '%s "%s %s%s %s" %s' % (req.remote_ip, req.method, host, req.uri, req.version, browser) # could add "- - [%s]" with time.strftime("%d/%b/%Y:%X") if don't like Tornado-logs date-time format (and - - - before the browser %s)
    logging.info(msg)
    if options.whois and hasattr(req,"valid_for_whois"): self.whoisLogger(req.remote_ip)

helper_thread_count = 0

accessLog = BrowserLogger()

try:
    import pycurl # check it's there
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    HTTPClient.configure("tornado.curl_httpclient.CurlHTTPClient")
except: pass # fall back to the pure-Python one

try:
    import zlib
    enable_gzip = True
except: # Windows?
    enable_gzip = False
    class zlib:
        def compress(self,s,level): return s
        def decompressobj():
            class o:
                def decompress(self,s,maxlen): return s
            return o()
    zlib = zlib()

try:
    import hashlib # Python 2.5+, platforms?
    hashlib.md5
except: hashlib = None # (TODO: does this ever happen on a platform that supports Tornado?  Cygwin has hashlib with md5)
if hashlib: cookieHash = lambda msg: base64.b64encode(hashlib.md5(msg).digest())[:10]
else: cookieHash = lambda msg: hex(hash(msg))[2:] # this fallback is not portable across different Python versions etc, so no good if you're running a fasterServer

cookieExpires = "Tue Jan 19 03:14:07 2038" # TODO: S2G

set_window_onerror = False # for debugging Javascript on some mobile browsers (TODO make this a config option? but will have to check which browsers do and don't support window.onerror)

def writeAndClose(stream,data):
    # This helper function is needed for CONNECT and own_server handling because, contrary to Tornado docs, some Tornado versions (e.g. 2.3) send the last data packet in the FIRST callback of IOStream's read_until_close
    if data:
        try: stream.write(data)
        except IOError: pass # probably client disconnected, don't fill logs with tracebacks
    if not stream.closed(): stream.close()

# Domain-setting cookie for when we have no wildcard_dns and no default_site:
adjust_domain_cookieName = "_adjusterDN_"
adjust_domain_none = "0" # not a valid top-level domain (TODO hopefully no user wants this as a local domain...)
enable_adjustDomainCookieName_URL_override = True # TODO: document this!  (Allow &_adjusterDN_=0 or &_adjusterDN_=wherever in bookmark URLs, so it doesn't matter what setting the cookie has when the bookmark is activated)

seen_ipMessage_cookieName = "_adjusterIPM_"

htmlmode_cookie_name = "_adjustZJCG_" # zap JS, CSS and Graphics
password_cookie_name = "_pxyAxsP_" # "proxy access password". have to pick something that's unlikely to collide with a site's cookie

redirectFiles_Extensions=set("pdf epub mp3 aac zip gif png jpeg jpg exe tar tgz tbz ttf woff swf txt doc rtf midi mid wav ly c h py".split()) # TODO: make this list configurable + maybe add a "minimum content length before it's worth re-directing" option

class HTTPClient_Fixed(HTTPClient):
    def __init__(self,*args):
        self._closed = True # so don't get error in 'del' if have to catch an exception in the constructor
        HTTPClient.__init__(self,*args)
wsgi_mode = False
def httpfetch(url,**kwargs):
    if not wsgi_mode:
        return AsyncHTTPClient().fetch(url,**kwargs)
    callback = kwargs['callback']
    del kwargs['callback']
    try: r = HTTPClient_Fixed().fetch(url,**kwargs)
    except HTTPError, e: r = e.response
    except:
        # Ouch.  In many Tornado versions, HTTPClient
        # is no more than a wrapper around
        # AsyncHTTPClient with an IOLoop call.  That
        # may work on some WSGI servers but not on
        # others; in particular it might include
        # system calls that are too low-level for the
        # liking of platforms like AppEngine.  Maybe
        # we have to fall back to urllib2.
        import urllib2
        data = kwargs.get('body',None)
        if not data: data = None
        headers = dict(kwargs.get('headers',{}))
        req = urllib2.Request(url, data, headers)
        if kwargs.get('proxy_host',None) and kwargs.get('proxy_port',None): req.set_proxy("http://"+kwargs['proxy_host']+':'+kwargs['proxy_port'],"http")
        try: resp = urllib2.urlopen(req,timeout=60)
        except urllib2.HTTPError, e: resp = e
        class Empty: pass
        r = Empty()
        r.code = resp.getcode()
        class H:
            def __init__(self,info): self.info = info
            def get(self,h,d): return self.info.get(h,d)
            def get_all(self): return [h.replace('\n','').split(': ',1) for h in self.info.headers]
        r.headers = H(resp.info())
        r.body = resp.read()
    callback(r)

class RequestForwarder(RequestHandler):
    
    def get_error_html(self,status,**kwargs): return htmlhead("Web Adjuster error")+options.errorHTML+"</body></html>"

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

    def readCookies(self):
        if hasattr(self,"_adjuster_cookies_"): return # already OK
        self._adjuster_cookies_ = {}
        for c in self.request.headers.get_list("Cookie"):
            for cc in c.split(';'):
                if not '=' in cc: continue # (e.g. Maxthon has been known to append a ; to the end of the cookie string)
                n,v = cc.strip().split('=',1)
                self._adjuster_cookies_[n] = v
    def getCookie(self,cookieName,zeroValue=None):
        # zeroValue is a value that the cookie can be set to so as to "clear" it (because some browsers don't seem to understand JS that clears a cookie)
        self.readCookies()
        v = self._adjuster_cookies_.get(cookieName,None)
        if v==zeroValue: v = None
        return v
    def setCookie(self,cookieName,val):
        # This is ONLY for ADJUSTER OPTIONS - does NOT propagate to the server
        self.readCookies()
        self._adjuster_cookies_[cookieName] = val
    
    def clearUnrecognisedCookies(self):
        # When serving via adjust_domain_cookieName, on URL box try to save browser memory (and request time) and improve security by deleting cookies set by previous sites.  But can cover only the path=/ ones from here.
        self.readCookies()
        for n,v in self._adjuster_cookies_.items():
            if n in cRecogniseAny or n==adjust_domain_cookieName: continue # don't do adjust_domain_cookieName unless take into account addCookieFromURL (TODO: but would we ever GET here if that happens?)
            elif n in cRecognise1 and v=="1": continue
            for dot in ["","."]: self.add_header("Set-Cookie",n+"="+v+"; Domain="+dot+self.cookieHostToSet()+"; Path=/; Expires=Thu Jan 01 00:00:00 1970") # to clear it
    def setCookie_with_dots(self,kv):
        for dot in ["","."]: self.add_header("Set-Cookie",kv+"; Domain="+dot+self.cookieHostToSet()+"; Path=/; Expires="+cookieExpires) # (at least in Safari, need BOTH with and without the dot to be sure of setting the domain and all subdomains.  TODO: might be able to skip the dot if not wildcard_dns, here and in the cookie-setting scripts.)
    def addCookieFromURL(self):
        if self.cookieViaURL: self.add_header("Set-Cookie",adjust_domain_cookieName+"="+urllib.quote(self.cookieViaURL)+"; Path=/; Expires="+cookieExpires) # don't need dots for this (non-wildcard)

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
        if options.password_domain and host and not any((host==p or host.endswith("."+p)) for p in options.password_domain.split('/')): return True
        if options.password_domain: self.is_password_domain=True
        # if they said ?p=(password), it's OK and we can
        # give them a cookie with it
        if self.getArg("p") == options.password:
            self.setCookie_with_dots(password_cookie_name+"="+urllib.quote(options.password))
            self.removeArgument("p",options.password)
            return True
        return self.getCookie(password_cookie_name)==urllib.quote(options.password)

    def decode_argument(self, value, name=None): return value # don't try to UTF8-decode; it might not be UTF8
    
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
        try:
            self.finish()
            self._finished = 1 # (just in case)
        except: pass # belt and braces (depends on Tornado version?)

    def redirect(self,redir,status=301):
        self.set_status(status)
        for h in ["Location","Content-Location","Content-Type","Content-Language"]: self.clear_header(h) # so redirect() can be called AFTER a site's headers are copied in
        self.add_header("Location",redir)
        self.add_header("Content-Type","text/html")
        self.write('<html><body><a href="%s">Redirect</a></body></html>' % redir.replace('&','&amp;').replace('"','&quot;'))
        self.myfinish()

    def add_nocache_headers(self):
        self.add_header("Pragma","no-cache")
        self.add_header("Vary","*")
        self.add_header("Expires","Thu Jan 01 00:00:00 1970")
        self.add_header("Cache-Control","no-cache, no-store, must-revalidate, max-stale=0, post-check=0, pre-check=0")
    def inProgress(self):
        # If appropriate, writes a "conversion in progress" page and returns True, and then self.inProgress_run() should return True.
        # Not on wget or curl (TODO: configurable?)
        if not options.waitpage or not options.pdfepubkeep: return False
        ua = " "+self.request.headers.get("User-Agent","")
        if " curl/" in ua or " Wget/" in ua: return False # (but don't return false for libcurl/)
        self.set_status(200)
        self.add_nocache_headers()
        self.add_header("Refresh","10") # TODO: configurable?  and make sure it does not exceed options.pdfepubkeep
        self.clear_header("Content-Disposition")
        self.clear_header("Content-Type")
        self.add_header("Content-Type","text/html")
        self.inProgress_has_run = True # doResponse2 may set a callback for render, so can't set _finished yet, but do need to set something so txtCallback knows not to write the actual text into this response (TODO could do a "first one there gets it" approach, but it's unlikely to be needed)
        if self.checkBrowser(["IEMobile 6","IEMobile 7","Opera Mobi"]): warn="<h3>WARNING: Your browser might not save this file</h3>You are using a browser which has been known to try to display text attachments in its own window using very small print, giving no option to save to a file. You might get better results in IEMobile 8+ or Opera Mini (although the latter may have a more limited range of font sizes in the browser itself)." # TODO: make this warning configurable?  See comment after set_header("Content-Disposition",...) below for details
        else: warn=""
        self.doResponse2(("""%s<h1>File conversion in progress</h1>The result should start downloading soon. If it does not, try <script><!--
document.write('<a href="javascript:location.reload(true)">refreshing this page</a>')
//--></script><noscript>refreshing this page</noscript>.%s%s<hr>This is %s</body></html>""" % (htmlhead("File conversion in progress"),backScript,warn,serverName_html)),True,False)
        # TODO: if (and only if) refreshing from this page, might then need a final 'conversion finished' page before serving the attachment, so as not to leave an 'in progress' page up afterwards
        return True
    def inProgress_run(self): return hasattr(self,"inProgress_has_run") and self.inProgress_has_run

    def addToHeader(self,header,toAdd):
        val = self.request.headers.get(header,"")
        if val: val += ", "
        self.request.headers[header] = val+toAdd

    def forwardFor(self,server):
        if wsgi_mode: raise Exception("Not yet implemented for WSGI mode") # no .connection; we'd probably have to repeat the request with HTTPClient
        if server==options.own_server and options.ownServer_useragent_ip:
            r = self.request.headers.get("User-Agent","")
            if r: r=" "+r
            r="("+self.request.remote_ip+")"+r
            self.request.headers["User-Agent"]=r
        upstream = tornado.iostream.IOStream(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0))
        client = self.request.connection.stream
        if ':' in server: host, port = server.split(':')
        else: host, port = server, 80
        upstream.connect((host, int(port)),lambda *args:(upstream.read_until_close(lambda data:writeAndClose(client,data),lambda data:client.write(data)),client.read_until_close(lambda data:writeAndClose(upstream,data),lambda data:upstream.write(data))))
        try: self.request.uri = self.request.original_uri
        except: pass
        upstream.write(self.request.method+" "+self.request.uri+" "+self.request.version+"\r\n"+"\r\n".join(("%s: %s" % (k,v)) for k,v in (list(h for h in self.request.headers.get_all() if not h[0].lower()=="x-real-ip")+[("X-Real-Ip",self.request.remote_ip)]))+"\r\n\r\n"+self.request.body)

    def answerPing(self,newVersion):
        # answer a "ping" request from another machine that's using us as a fasterServer
        # Need to make the response short, but still allow keepalive
        self.request.suppress_logging = True
        for h in ["Server","Content-Type","Date"]:
            try: self.clear_header(h)
            except: pass
        # (Date is added by Tornado 3, which can also add "Vary: Accept-Encoding" but that's done after we get here, TODO: option to ping via a connect and low-level TCP keepalive bytes?)
        self.set_header("Etag","0") # shorter than Tornado's computed one (clear_header won't work with Etag)
        if newVersion and not wsgi_mode: # TODO: document that it's a bad idea to set up a fasterServer in wsgi_mode (can't do ipTrustReal, must have fasterServerNew=False, ...)
            # Forget the headers, just write one byte per second for as long as the connection is open
            stream = self.request.connection.stream
            stream.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            def writeBytes():
                try:
                    stream.write("1")
                    IOLoop.instance().add_timeout(time.time()+1,lambda *args:writeBytes())
                except:
                    # logging.info("ping2: disconnected")
                    self.myfinish()
            if not options.background: sys.stderr.write("ping2: "+self.request.remote_ip+" connected\n") # (don't bother logging this normally, but might want to know when running in foreground)
            writeBytes()
        else:
            self.write("1") ; self.myfinish()

    def answer_load_balancer(self):
        self.request.suppress_logging = True
        self.add_header("Content-Type","text/html")
        self.write(htmlhead("Web Adjuster")+"<h1>Web Adjuster load-balancer page</h1>This page should not be shown to normal browsers, only to load balancers and uptime checkers. If you are a human reading this message, <b>it probably means your browser is \"cloaked\"</b> (hidden User-Agent string); please un-hide this to see the top-level page.</body></html>")
        self.myfinish()

    def find_real_IP(self):
        if wsgi_mode: return
        if options.trust_XForwardedFor:
            xff = self.request.headers.get_list("X-Forwarded-For")
            if xff:
                xff = xff[0].split() # TODO: is it always the first header we want?
                if xff:
                    self.request.remote_ip = xff[0]
                    return
        if not options.ipTrustReal in [self.request.remote_ip,'*']: return
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
        # self.clear_header("Server") # save bytes if possible as we could be serving a LOT of these images .. but is this really needed? (TODO)
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
                self.setCookie_with_dots(htmlmode_cookie_name+"="+val)
    def htmlOnlyMode(self): return options.htmlonly_mode and htmlmode_cookie_name+"=1" in ';'.join(self.request.headers.get_list("Cookie"))
    
    def handle_URLbox_query(self,v):
        self.set_htmlonly_cookie()
        if v.startswith("https://"): return self.redirect(v) # for now (if someone pastes an SSL URL into the box by mistake)
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
                    v = addArgument(v,adjust_domain_cookieName+'='+urllib.quote(v2))
                else: self.add_header("Set-Cookie",adjust_domain_cookieName+"="+urllib.quote(v2)+"; Path=/; Expires="+cookieExpires) # (DON'T do this unconditionally, convert_to_requested_host above might see we already have another fixed domain for it)
                # (TODO: if convert_to_requested_host somehow returns a *different* non-default_site domain, that cookie will be lost.  Might need to enforce max 1 non-default_site domain.)
            else: v2 = ch
        else: v2=None # not needed if wildcard_dns
        self.redirect(domain_process(v,v2,True))

    def handleFullLocation(self):
        # HTTP 1.1 spec says ANY request can be of form http://...., not just a proxy request.  The differentiation of proxy/not-proxy depends on what host is requested.  So rewrite all http://... requests to HTTP1.0-style host+uri requests.
        if self.request.uri.startswith("http://"):
            self.request.original_uri = self.request.uri
            parsed = urlparse.urlparse(self.request.uri)
            self.request.host = self.request.headers["Host"] = parsed.netloc
            self.request.uri = urlparse.urlunparse(("","")+parsed[2:])
            if not self.request.uri: self.request.uri="/"
        elif not self.request.uri.startswith("/"): # invalid
            self.set_status(400) ; self.myfinish() ; return True
    
    def handleSpecificIPs(self):
        if not ipMatchingFunc: return False
        msg = ipMatchingFunc(self.request.remote_ip)
        if not msg: return False
        if msg.startswith('*'): # a block
            self.write(htmlhead("Blocked")+msg[1:]+"</body></html>") ; self.myfinish() ; return True
        if self.request.uri in ["/robots.txt","/favicon.ico"]: return False
        cookies = ';'.join(self.request.headers.get_list("Cookie"))
        if msg.startswith('-'): # minor edit
            msg = msg[1:]
            if seen_ipMessage_cookieName+"=" in cookies:
                # seen ANY message before (not just this)
                return False
        val = cookieHash(msg)
        if seen_ipMessage_cookieName+"="+val in cookies:
            # seen THIS message before
            return False
        hs = self.cookieHostToSet()
        self.add_nocache_headers()
        self.write("%s%s<p><form><label><input type=\"checkbox\" name=\"gotit\">Don't show this message again</label><br><input type=\"submit\" value=\"Continue\" onClick=\"var a='%s=%s;domain=',b=(document.forms[0].gotit.checked?'expires=%s;':'')+'path=/',h='%s;';document.cookie=a+'.'+h+b;document.cookie=a+h+b;location.reload(true);return false\"></body></html>" % (htmlhead("Message"),msg,seen_ipMessage_cookieName,val,cookieExpires,hs))
        logging.info("ip_messages: done "+self.request.remote_ip)
        self.myfinish() ; return True

    def handleGoAway(self,realHost):
        if not options.renderOmitGoAway or not self.checkBrowser(options.renderOmit): return False
        # TODO: option to redirect immediately without this message?  (but then we'd be supplying a general redirection service, which might have issues of its own)
        if realHost: msg = ' and <a href="http://%s%s">go directly to the original site</a>' % (realHost,self.request.uri)
        else: msg = ''
        self.add_nocache_headers()
        self.write("%s<h1>You don't need this!</h1>This installation of Web Adjuster has been set up to change certain characters into pictures, for people using old computers that don't know how to display them themselves. However, <em>you</em> seem to be using equipment that is <noscript>either </noscript>definitely capable of showing these characters by itself<noscript>, or else wouldn't be able to show the pictures anyway<!-- like Lynx --></noscript>. Please save our bandwidth for those who really need it%s. Thank you.</body></html>" % (htmlhead("Web Adjuster"),msg))
        self.myfinish() ; return True

    def needCssCookies(self):
        h = options.headAppendCSS
        if not h or not '%s' in h: return False
        for ckCount in range(len(h.split(';'))-1):
            if not self.getCookie("adjustCss" + str(ckCount) + "s", ""): return True
        return False
    def cssAndAttrsToAdd(self):
        h = options.headAppendCSS ; cha = options.cssHtmlAttrs
        if not h or not '%s' in h: return h, cha
        h,opts = h.split(';',1)
        opts=opts.split(';')
        ckCount = N = 0
        for o in opts:
            chosen = self.getCookie("adjustCss" + str(ckCount) + "s", "")
            if not chosen: # we don't have all the necessary cookies to choose a stylesheet, so don't have one (TODO: or do we just want to go to the first listed?)
                if cha and ';' in cha: return "", ""
                else: return "", cha
            poss_vals = [re.sub('=.*','',x) for x in o.split(',')]
            if '' in poss_vals: poss_vals[poss_vals.index('')]='-'
            if not chosen in poss_vals: chosen = re.sub('=.*','',o.split(',',1)[0]) # make sure it's an existing option, to protect against cross-site-scripting injection of CSS (as some browsers accept JS in CSS)
            N = poss_vals.index(chosen)
            if chosen=="-": chosen = "" # TODO: document in headAppendCSS that we use '-' as a placeholder because we need non-empty values in cookies etc
            h=h.replace('%s',chosen,1)
            ckCount += 1
        if cha and ';' in cha: return h, options.cssHtmlAttrs.split(';')[N]
        else: return h, cha
    def cssOptionsHtml(self):
        h = options.headAppendCSS
        if not h or not '%s' in h: return ""
        h,opts = h.split(';',1)
        opts=opts.split(';')
        ckCount = 0
        r = ["<p>Style:"]
        for o in opts:
            ckName = "adjustCss" + str(ckCount) + "s"
            r.append(' <select name="%s">' % ckName)
            chosen = self.getCookie(ckName, "")
            for val in o.split(','):
                if '=' in val: val,desc = val.split('=',1)
                else: desc = val
                if val=="": val = "-" # TODO: document in headAppendCSS that we use '-' as a placeholder because we need non-empty values in cookies etc
                if val==chosen: sel = " selected"
                else: sel = ""
                r.append('<option value="%s"%s>%s</option>' % (val,sel,desc))
            ckCount += 1
            r.append('</select>')
        return ''.join(r)+' <input type="submit" name="try" value="Try"></p>'
    def set_css_from_urlbox(self):
        h = options.headAppendCSS
        if not h or not '%s' in h: return
        h,opts = h.split(';',1)
        opts=opts.split(';')
        ckCount = 0
        for o in opts:
            ckName = "adjustCss" + str(ckCount) + "s"
            ckVal = self.getArg(ckName)
            if ckVal:
                self.setCookie_with_dots(ckName+"="+ckVal) # TODO: do we ever need to urllib.quote() ckVal ?  (document to be careful when configuring?)
                self.setCookie(ckName,ckVal) # pretend it was already set on THIS request as well (for 'Try' button; URL should be OK as it redirects)
            ckCount += 1
    
    def serve_URLbox(self):
        if not options.wildcard_dns: self.clearUnrecognisedCookies() # TODO: optional?
        self.addCookieFromURL()
        self.doResponse2(urlbox_html(self.htmlOnlyMode(),self.cssOptionsHtml()),True,False) # TODO: run htmlFilter on it also? (render etc will be done by doResponse2)

    def serve_mailtoPage(self):
        uri = self.request.uri[len(options.mailtoPath):].replace('%%+','%') # we encode % as %%+ to stop browsers and transcoders from arbitrarily decoding e.g. %26 to &
        if '?' in uri:
            addr,rest = uri.split('?',1)
            self.request.arguments = urlparse.parse_qs(rest) # after the above decoding of %'s
        else: addr=uri
        addr = urllib.unquote(addr)
        body = self.getArg("body")
        subj = self.getArg("subject")
        r = [] ; smsLink = ""
        if addr: r.append("To: "+ampEncode(addr))
        if subj: r.append("Subject: "+ampEncode(subj))
        if body:
            r.append("Body: "+ampEncode(body))
            if self.checkBrowser(options.mailtoSMS):
                if subj and not body.startswith(subj): smsLink = subj+" "+body
                else: smsLink = body
                if '&' in smsLink:
                    smsLink="[Before sending this text, replace -amp- with an ampersand. This substitution has been done in case your phone isn't compliant with RFC 5724.] "+smsLink.replace('&',' -amp- ')
                    # RFC 5724 shows we ought to get away with ampersands encoded as %26, but on Windows Mobile (Opera or IE) we don't; the SMS is truncated at that point.  TODO: whitelist some other platforms? (test with <a href="sms:?body=test1%26test2">this</a>)
                smsLink = '<br><a href="sms:?body=%s">Send as SMS (text message)</a>' % urllib.quote(rm_u8punc(smsLink))
                if self.checkBrowser(["Windows Mobile"]): # TODO: others? configurable?
                    # browsers may also have this problem with EMAIL
                    uri = uri.replace("%26","%20-amp-%20")
                    if not "body=" in uri: uri += "&body="
                    uri = uri.replace("body=","body=[Before%20sending%20this%20text,%20replace%20-amp-%20with%20an%20ampersand.%20This%20substitution%20has%20been%20done%20as%20your%20phone%20isn't%20compliant%20with%20RFC%205724.]%20")
        if len(r)==1: # different format if only 1 item is specified
            if addr: r=["The email will be sent to "+ampEncode(addr)]
            elif subj: r=["The email's Subject will be: "+ampEncode(subj)]
            else: r=["The email's Body will be: "+ampEncode(body)]
        elif not r: r.append("The link does not specify any recognised email details")
        else: r.insert(0,"The following information will be sent to the email client:")
        self.doResponse2(('%s<h3>mailto: link</h3>This link is meant to open an email client.<br>%s<br><a href=\"mailto:%s\">Open in email client</a> (if set up)%s%s<hr>This is %s</body></html>' % (htmlhead("mailto: link - Web Adjuster"),"<br>".join(r),uri,smsLink,backScript,serverName_html)),True,False)

    def serve_submitPage(self):
        self.request.suppress_logger_host_convert = True
        if self.request.uri=="/favicon.ico":
            # avoid logging favicon.ico tracebacks when submitPath=="/"
            self.set_status(400) ; self.myfinish() ; return True
        if len(self.request.uri) > len(options.submitPath):
            txt = self.request.uri[len(options.submitPath):]
            if len(txt)==2 and options.submitBookmarklet:
                filterNo = ord(txt[1])-ord('A')
                if txt[0]=='b': return self.serve_bookmarklet_code(txt[1])
                elif txt[0]=='j': return self.serve_bookmarklet_json(filterNo)
                elif txt[0]=='i' or txt[0]=='a':
                    # Android or iOS instructions
                    # (Similar technique does NOT work in Opera Mini 5.1.21594 or Opera Mobile 10.00 (both 2010) on Windows Mobile 6.1: can end up with a javascript: bookmark but it has no effect when selected)
                    if txt[0]=='i': theSys = 'iOS'
                    else: theSys = 'Android'
                    title = None
                    if '#' in options.htmlFilter:
                        fNames=options.htmlFilterName.split('#')
                        if filterNo+1 < len(fNames):
                            title=fNames[filterNo+1]
                    elif options.htmlFilterName:
                        title=options.htmlFilter
                    if title: title += " on current page" # because page won't be visible while choosing bookmarks, unlike on desktops
                    else: title=theSys+" bookmarklet - Web Adjuster" # will be the default name of the bookmark
                    # TODO: we say txt[0]+'z' in the instructions to display on another device below, but if there are enough filters to get up to 'z' then the title on the other device will be whatever THAT filter is; might be better to just use txt in that situation
                    i0 = "<h3>%s bookmarklet</h3>To install this bookmarklet on %s, follow the instructions below. You might want to take some notes first, because this page will <em>not</em> be displayed throughout the process! If you have another device, you can show another copy of these instructions on it by going to <tt>http://%sz</tt><h4>Instructions</h4><ol><li>" % (theSys, theSys, self.request.host+options.submitPath+txt[0])
                    sharp = "<li>You should see a sharp sign (#). If you don't, you might have to scroll a little to the right to get it into view. When you see the sharp sign, press immediately to the right of it. (This can be difficult, depending on your eyesight and the size of your fingers. You must put the text cursor <em>immediately</em> to the right of that sharp. Keep trying until you get it in <em>exactly</em> the right place.)<li>Use the backspace key to delete everything up to and including the sharp. The code should now start with the word <tt>javascript</tt>.<li>"
                    if txt[0]=='i': i0 += "Press Menu (centre square button below) and Bookmark, to bookmark <b>this</b> page<li>Change the name if you want, and press Done<li>Press Bookmarks (one to the right of menu)<li>Press Edit (bottom left)<li>Find the bookmark you made and press it<li>Long-press the <em>second</em> line to get the selection menu on it<li>Press Select<li>Gently drag the left-most marker over to the left so that it scrolls to the extreme left of the address"+sharp+"Press \"Done\" three times to come back here."
                    else: i0 += "Press Menu and Save to Bookmarks, to bookmark <b>this</b> page<li>Change the label if you want, but <b>do not</b> press OK<li>Long-press the <em>second</em> line to get the selection on it<li>Gently drag the marker over to the left so that it scrolls to the extreme left of the address"+sharp+"Press \"OK\" to come back here."
                    return self.doResponse2(htmlhead(title)+i0+"<li>The bookmarklet is now ready for use. Go to whatever page you want to use it on, and select it from the bookmarks to use it.</ol></body></html>",False,False) # DON'T do_html_process if it puts filter selectors up - that could be confusing on a screen that's associated with a particular filter
            txt = zlib.decompressobj().decompress(base64.b64decode(txt),16834) # limit to 16k to avoid zip bombs (limit is also in the compress below)
            self.request.uri = "%s (input not logged, len=%d)" % (options.submitPath,len(txt))
        else: txt = self.request.arguments.get("i",None)
        if not txt:
            self.is_password_domain=True # no prominentNotice needed
            # In the markup below, body's height=100% is needed to ensure we can set a percentage height on the textarea consistently across many browsers (otherwise e.g. Safari 6 without user CSS might start making the textarea larger as soon as it contains input, overprinting the rest of the document)
            return self.doResponse2(("""%s<body style="height:100%%;overflow:auto"><form method="post" action="%s"><h3 style="float:left;padding:0px;margin:0px">Upload Text</h3><span style="float:right"><input type="submit"><script><!--
document.write(' (Ctrl-Enter) | <a href="javascript:history.go(-1)">Back</a>')
//--></script></span><br><textarea name="i" style="width:100%%;clear:both;height:60%%" rows="5" cols="20" placeholder="Type or paste your text here"
onKeyDown="if((event.ctrlKey||event.metaKey) && (event.keyCode==13 || event.which==13)) document.forms[0].submit(); else return true;">
</textarea></form>%s<script><!--
document.forms[0].i.focus()
//--></script></body></html>""" % (htmlhead("Upload Text - Web Adjuster").replace("<body>",""),options.submitPath,bookmarklet("http://"+self.request.host+options.submitPath))),True,False)
        if type(txt) == list: # came from the POST form
            txt = txt[0].strip()
            # On at least some browsers (e.g. some Safari versions), clicking one of our JS reload links after the POST text has been shown will reload the form (instead of re-submitting the POST text) and can scroll to an awkward position whether the code below calls focus() or not.  Could at least translate to GET if it's short enough (don't want to start storing things on the adjuster machine - that would require a shared database if load-balancing)
            if len(txt) <= 16384: # (else we wouldn't decompress all; see comment above)
                enc = base64.b64encode(zlib.compress(txt,9))
                if 0 < len(enc) < 2000: return self.redirect(options.submitPath+enc,303) # POST to GET

        # pretend it was served by a remote site; go through everything including filters (TODO: could bypass most of doResponse instead of rigging it up like this; alternatively keep this as it shows how to feed data to doResponse)
        self.connection_header = None
        self.urlToFetch = "" # for js_process
        class H:
            def get(self,h,d):
                if h=="Content-Type": return "text/html; charset=utf-8"
                else: return d
            def get_all(self): return [("Content-Type","text/html; charset=utf-8")]
        class R:
            code = 200
            headers = H()
        r=R() ; r.body="""%s<h3>Your text</h3>%s<hr>This is %s. %s</body></html>""" % (htmlhead("Uploaded Text - Web Adjuster"),txt2html(txt),serverName_html,backScriptNoBr) # backScriptNoBr AFTER the server notice to save vertical space
        self.doResponse(r,[False]*4,False,False)
    def serve_bookmarklet_code(self,xtra):
        self.add_header("Content-Type","application/javascript")
        self.add_header("Access-Control-Allow-Origin","*")
        self.write(bookmarkletMainScript("http://"+self.request.host+options.submitPath+'j'+xtra))
        self.myfinish()
    def serve_err(self,err):
        self.set_status(500)
        self.add_header("Content-Type","text/plain")
        # logging.error(err+' '+repr(self.request.body))
        self.write(err) ; self.myfinish()
    def serve_bookmarklet_json(self,filterNo):
        self.add_header("Access-Control-Allow-Origin","*")
        self.add_header("Access-Control-Allow-Headers","Content-Type")
        if not self.request.body:
            self.add_header("Content-Type","text/plain")
            self.add_header("Allow","POST") # some browsers send OPTIONS first before POSTing via XMLHttpRequest (TODO: check if OPTIONS really is the request method before sending this?)
            self.write("OK") ; return self.myfinish()
        try: l = json.loads(self.request.body)
        except: return self.serve_err("Bad JSON")
        if not (type(l)==list and all((type(i)==type(u"") and not chr(0) in i) for i in l)): return self.serve_err("Wrong data structure")
        codeTextList = []
        for i in l:
            codeTextList.append(chr(0))
            codeTextList.append(i.encode('utf-8'))
        def callback(out,err):
            self.add_header("Content-Type","application/json")
            self.write(json.dumps([i.decode('utf-8') for i in out[1:].split(chr(0))]))
            self.finish()
        runFilterOnText(self.getHtmlFilter(filterNo),codeTextList,callback)

    def checkTextCache(self,newext):
        # check for PDF/EPUB conversion on other threads or cached
        if not options.pdfepubkeep: return False # we don'tguarantee to update kept_tempfiles properly if it's 0 (e.g. pdf can just pipe, so don't need unlinkOutputLater)
        ktkey = (self.request.host, self.request.uri)
        if ktkey in kept_tempfiles:
            def tryRead():
                try: txt=open(kept_tempfiles[ktkey]).read()
                except: txt = None
                if txt:
                    if newext==".mobi": self.write(txt)
                    else: self.write(remove_blanks_add_utf8_BOM(txt))
                    self.myfinish()
                elif not self.inProgress(): IOLoop.instance().add_timeout(time.time()+1,lambda *args:tryRead())
            tryRead() ; return True
        kept_tempfiles[ktkey] = 1 # conversion in progress
        return False

    def getArg(self,arg):
        a = self.request.arguments.get(arg,None)
        if type(a)==type([]): a=a[0]
        return a

    def doReq(self):
        debuglog("doReq "+self.request.uri)
        if self.request.headers.get("User-Agent","")=="ping":
            if self.request.uri=="/ping2": return self.answerPing(True)
            elif self.request.uri=="/ping": return self.answerPing(False)
        elif options.loadBalancer and self.request.headers.get("User-Agent","")=="" and self.request.uri=="/": return self.answer_load_balancer()
        self.find_real_IP() # must do this BEFORE forwarding to fasterServer, because might also be behind nginx etc
        if fasterServer_up:
            return self.forwardFor(options.fasterServer)
        if self.handleFullLocation() or self.handleSpecificIPs(): return
        # TODO: Slow down heavy users by self.request.remote_ip ?
        if extensions.handle("http://"+self.request.host+self.request.uri,self):
            self.request.suppress_logger_host_convert = self.request.valid_for_whois = True
            return self.myfinish()
        if ownServer_regexp and ownServer_regexp.match(self.request.host+self.request.uri):
            self.request.headers["Connection"] = "close" # MUST do this (keepalive can go wrong if it subsequently fetches a URL that DOESN'T match ownServer_regexp, but comes from the same domain, and this goes to ownServer incorrectly), TODO mention it in the help text?, TODO might we occasionally need something similar for ownServer_if_not_root etc?, TODO at lower priority: if we can reasonably repeat the requests then do that insntead of using forwardFor
            return self.forwardFor(options.own_server)
        if cssReload_cookieSuffix and cssReload_cookieSuffix in self.request.uri:
            ruri,rest = self.request.uri.split(cssReload_cookieSuffix,1)
            self.setCookie_with_dots(rest)
            return self.redirect(ruri) # so can set another
        viewSource = self.checkViewsource()
        self.cookieViaURL = None
        realHost = convert_to_real_host(self.request.host,self.cookie_host(checkReal=False)) # don't need checkReal if return value will be passed to convert_to_real_host anyway
        if realHost == -1:
            return self.forwardFor(options.own_server)
            # (TODO: what if it's keep-alive and some browser figures out our other domains are on the same IP and tries to fetch them through the same connection?  is that supposed to be allowed?)
        elif realHost==0 and options.ownServer_if_not_root: realHost=options.own_server # asking by cookie to adjust the same host, so don't forwardFor() it but fetch it normally and adjust it
        isProxyRequest = options.real_proxy and realHost == self.request.host
        
        self.request.valid_for_whois = True # (if options.whois, don't whois unless it gets this far, e.g. don't whois any that didn't even match "/(.*)" etc)

        maybeRobots = (not options.robots and self.request.uri=="/robots.txt") # don't actually serveRobots yet, because MIGHT want to pass it to own_server (see below)
        
        self.is_password_domain=False # needed by doResponse2
        if options.password and not options.real_proxy: # whether or not open_proxy, because might still have password (perhaps on password_domain), anyway the doc for open_proxy says "allow running" not "run"
          # First ensure the wildcard part of the host is de-dotted, so the authentication cookie can be shared across hosts.
          # (This is not done if options.real_proxy because we don't want to touch the hostname for that)
          host = self.request.host
          if host:
            if host.endswith(":"+str(options.publicPort)): host=host[:-len(":"+str(options.publicPort))]
            for hs in options.host_suffix.split("/"):
              ohs = "."+hs
              if host.endswith(ohs) and host.index(".")<len(host)-len(ohs):
                if maybeRobots: return self.serveRobots()
                if options.publicPort==80: colPort=""
                else: colPort=":"+str(options.publicPort)
                return self.redirect("http://"+dedot(host[:-len(ohs)])+ohs+colPort+self.request.uri)
          # Now OK to check authentication:
          if not self.authenticates_ok(host) and not (submitPathIgnorePassword and self.request.uri.startswith(options.submitPath)):
              if options.auth_error=="http://":
                  if options.own_server: return self.forwardFor(options.own_server)
                  elif maybeRobots: return self.serveRobots()
                  else: options.auth_error = "auth_error set incorrectly (own_server not set)" # see auth_error help (TODO: is it really a good idea to say this HERE?)
              elif maybeRobots: return self.serveRobots()
              elif options.auth_error.startswith("http://"): return self.redirect(options.auth_error)
              if options.auth_error.startswith("*"): auth_error = options.auth_error[1:]
              else:
                  self.set_status(401)
                  auth_error = options.auth_error
              self.write(htmlhead("")+auth_error+"</body></html>")
              return self.myfinish()
        # Authentication is now OK
        self.set_header("Server",serverName) # TODO: in "real" proxy mode, "Server" might not be the most appropriate header to set for this
        try: self.clear_header("Date") # Date is added by Tornado 3; HTTP 1.1 says it's mandatory but then says don't put it if you're a clockless server (which we might be I suppose) so it seems leaving it out is OK especially if not specifying Age etc, and leaving it out saves bytes.  But if the REMOTE server specifies a Date then we should probably pass it on (see comments below)
        except: pass # (ok if "Date" wasn't there)
        if self.handleGoAway(realHost): return
        # Now check if it's an image request:
        _olduri = self.request.uri
        self.request.uri=urllib.unquote(self.request.uri)
        img = Renderer.getImage(self.request.uri)
        if img: return self.serveImage(img)
        # Not an image:
        if options.mailtoPath and self.request.uri.startswith(options.mailtoPath): return self.serve_mailtoPage()
        if options.submitPath and self.request.uri.startswith(options.submitPath): return self.serve_submitPage()
        self.request.uri = _olduri
        if not realHost: # default_site(s) not set
            if options.own_server and options.ownServer_if_not_root and len(self.request.path)>1: return self.forwardFor(options.own_server)
            elif maybeRobots: return self.serveRobots()
            # Serve URL box
            self.set_css_from_urlbox()
            if self.getArg("try"): return self.serve_URLbox() # we just set the stylesheet (TODO: preserve any already-typed URL?)
            v=self.getArg("q")
            if v: return self.handle_URLbox_query(v)
            else: return self.serve_URLbox()
        if maybeRobots: return self.serveRobots()
        if self.needCssCookies(): return self.redirect("http://"+hostSuffix()+publicPortStr()+"/") # go to the URL box - need to set more options (TODO: keep the host+URL they put as the box's default contents?)
        self.addCookieFromURL() # for cookie_host
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
        self.change_request_headers(realHost,isProxyRequest)
        self.urlToFetch = "http://"+self.request.headers["Host"]+self.request.uri
        if not isProxyRequest and any(re.search(x,self.urlToFetch) for x in options.prohibit):
            self.restore_request_headers()
            return self.redirect(self.urlToFetch)
        # TODO: consider adding "not self.request.headers.get('If-Modified-Since','')" to the below list of sendHead() conditions, in case any referer-denying servers decide it's OK to send out "not modified" replies even to the wrong referer (which they arguably shouldn't, and seem not to as of 2013-09, but if they did then adjuster might erroneously redirect the SECOND time a browser displays the image)
        def ext(u):
            if '?' in u:
                e = ext(u[:u.index('?')])
                if e: return e
            if not '.' in u: return
            e = u[u.rindex('.')+1:].lower()
            if not (e=="mp3" and options.bitrate and not options.askBitrate): return e
        if options.redirectFiles and not (isProxyRequest or any(converterFlags) or viewSource) and ext(self.request.uri) in redirectFiles_Extensions: self.sendHead()
        else: self.sendRequest(converterFlags,viewSource,isProxyRequest,follow_redirects=False) # (DON'T follow redirects - browser needs to know about them!)
    
    def change_request_headers(self,realHost,isProxyRequest):
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
            self.request.old_cookie = ck
            def ours(c): # don't forward our own cookies upstream (may confuse some sites, especially if a site uses Web Adjuster their end)
                c = c.strip()
                if not '=' in c: return 0
                c = c[:c.index('=')]
                return c in upstreamGuard or (c==adjust_domain_cookieName and self.cookie_host())
            if options.upstream_guard:
                def maketheirs(c):
                    for ck in upstreamGuard: c=c.replace(ck+"1",ck)
                    return c
                self.request.headers["Cookie"]=";".join(maketheirs(x) for x in ck.split(";") if not ours(x))
        for v in self.request.headers.get_list("Referer"):
            if v:
                self.original_referer = v
                v = fixDNS(v)
                if v in ["http://","http:///"]:
                    # it must have come from the URL box
                    del self.request.headers["Referer"]
                else: self.request.headers["Referer"] = v
        for http in ["http://","http%3A%2F%2F"]: # xyz?q=http://... stuff
          if http in self.request.uri[1:]:
            u=self.request.uri.split(http)
            for i in range(1,len(u)): u[i]=fixDNS(u[i])
            self.request.uri=http.join(u)
        self.accept_stuff = []
        for h in ['Connection','Proxy-Connection','Accept-Charset','Accept-Encoding','X-Forwarded-Host','X-Forwarded-Port','X-Forwarded-Server','X-Forwarded-Proto','X-Request-Start','Range']: # TODO: we can pass Range to remote server if and only if we guarantee not to need to change anything  (could also add If-Range and If-None-Match to the list, but these should be harmless to pass to the remote server and If-None-Match might actually help a bit in the case where the document doesn't change)
            l = self.request.headers.get_list(h)
            if l:
                del self.request.headers[h]
                self.accept_stuff.append((h,l[0]))
        self.request.headers["Host"]=realHost
        if options.via:
            v = self.request.version
            if v.startswith("HTTP/"): v=v[5:]
            self.addToHeader("Via",v+" "+convert_to_via_host(self.request.host)+" ("+viaName+")")
            self.addToHeader("X-Forwarded-For",self.request.remote_ip)
    def restore_request_headers(self): # restore the ones Tornado might use (Connection etc)
        if not hasattr(self,"accept_stuff"): return # haven't called change_request_headers (probably means this is user input)
        for k,v in self.accept_stuff: self.request.headers[k]=v
        if hasattr(self.request,"old_cookie"): self.request.headers["Cookie"] = self.request.old_cookie # + put this back so we can refer to our own cookies
    
    def sendRequest(self,converterFlags,viewSource,isProxyRequest,follow_redirects):
        body = self.request.body
        if not body: body = None # required by some Tornado versions
        ph,pp = upstream_proxy_host, upstream_proxy_port
        httpfetch(self.urlToFetch,
                  connect_timeout=60,request_timeout=120, # Tornado's default is usually something like 20 seconds each; be more generous to slow servers (TODO: customise?)
                  proxy_host=ph, proxy_port=pp,
                  use_gzip=enable_gzip and not hasattr(self,"avoid_gzip"),
                  method=self.request.method, headers=self.request.headers, body=body,
                  callback=lambda r:self.doResponse(r,converterFlags,viewSource,isProxyRequest),follow_redirects=follow_redirects)
        # (Don't have to worry about auth_username/auth_password: should just work by passing on the headers)
        # TODO: header_callback (run with each header line as it is received, and headers will be empty in the final response); streaming_callback (run with each chunk of data as it is received, and body and buffer will be empty in the final response), but how to abort a partial transfer if we realise we don't want it (e.g. large file we don't want to modify on site that doesn't mind client being redirected there directly)

    def doResponse(self,response,converterFlags,viewSource,isProxyRequest):
        debuglog("doResponse "+self.request.uri)
        self.restore_request_headers()
        do_pdftotext,do_epubtotext,do_epubtozip,do_mp3 = converterFlags
        do_domain_process = do_html_process = do_js_process = True
        do_json_process = do_css_process = False
        charset = "utf-8" # by default
        if not response.code or response.code==599:
            # (some Tornado versions don't like us copying a 599 response)
            try: error = str(response.error)
            except: error = "Gateway timeout or something"
            if "incorrect data check" in error and not hasattr(self,"avoid_gzip") and enable_gzip:
                # Some versions of the GWAN server can send NULL bytes at the end of gzip data.  Retry without requesting gzip.
                self.avoid_gzip = True
                return self.sendRequest(converterFlags,viewSource,isProxyRequest,False)
            tryFetch = self.urlToFetch
            if options.upstream_proxy: tryFetch += " via "+options.upstream_proxy
            logging.error(error+" when fetching "+tryFetch) # better log it for the admin, especially if options.upstream_proxy, because it might be an upstream proxy malfunction
            error = """%s<h1>Error</h1>%s<br>Was trying to fetch %s<hr>This is %s</body></html>""" % (htmlhead("Error"),error,ampEncode(tryFetch),serverName_html)
            self.set_status(504)
            return self.doResponse2(error,True,False)
        if response.headers.get("Content-Encoding","")=="gzip": # sometimes Tornado's client doesn't decompress it for us, for some reason
            try: response.body = zlib.decompressobj().decompress(response.body,1048576*32) # 32M limit to avoid zip bombs (TODO adjust? what if exceeded?)
            except: pass
        if viewSource:
            def h2html(h): return "<br>".join("<b>"+txt2html(k)+"</b>: "+txt2html(v) for k,v in sorted(h.get_all()))
            return self.doResponse2("<html><body><a href=\"#1\">Headers sent</a> | <a href=\"#2\">Headers received</a> | <a href=\"#3\">Page source</a> | <a href=\"#4\">Bottom</a> <a name=\"1\"></a><h2>Headers sent</h2>"+h2html(self.request.headers)+"<a name=\"2\"></a><h2>Headers received</h2>"+h2html(response.headers)+"<a name=\"3\"></a><h2>Page source</h2>"+txt2html(response.body)+"<hr><a name=\"4\"></a>This is "+serverName_html,True,False)
        headers_to_add = []
        if (do_pdftotext or do_epubtotext or do_epubtozip or do_mp3) and not response.headers.get("Location","") and response.headers.get("Content-type","").startswith("text/"):
          # We thought we were going to get a PDF etc that could be converted, but it looks like they just sent more HTML (perhaps a "which version of the PDF did you want" screen)
          do_pdftotext=do_epubtotext=do_epubtozip=do_mp3=False
        cookie_host = self.cookie_host()
        doRedirect = ""
        for name,value in response.headers.get_all():
          if name.lower() in ["connection","content-length","content-encoding","transfer-encoding","etag","server","alternate-protocol"]: continue # we'll do our own connection type etc (but don't include "Date" in this list: if the remote server includes a Date it would be useful to propagate that as a reference for its Age headers etc, TODO: unless remote server is broken? see also above comment re having no Date by default)
          # TODO: WebSocket (and Microsoft SM) gets the client to say 'Connection: Upgrade' with a load of Sec-WebSocket-* headers, check what Tornado does with that
          if (do_pdftotext or do_epubtotext) and name.lower() in ["content-disposition","content-type"]: continue # we're re-doing these also
          elif do_epubtozip and name.lower()=="content-disposition" and value.replace('"','').endswith(".epub"):
            epub = value.rfind(".epub")
            value=value[:epub]+".zip"+value[epub+5:]
          elif "access-control-allow-origin" in name.lower(): value=domain_process(value,cookie_host,True) # might need this for JSON responses to scripts that are used on a site's other domains
          elif "location" in name.lower():
            old_value_1 = value # before domain_process
            if not isProxyRequest:
                value=domain_process(value,cookie_host,True)
                offsite = (value==old_value_1 and value.startswith("http://")) # i.e. domain_process didn't change it, and it's not relative
            else: offsite = False # proxy requests are never "offsite"
            old_value_2 = value # after domain_process but before PDF/EPUB-etc rewrites
            if do_pdftotext: # is it still going to be pdf after the redirect?
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
            # else: do_pdftotext=do_epubtotext=do_epubtozip=do_mp3=False # do not attempt to media-process any body that is sent with this Location: redirect (if it's just a copy of the URL then running it through ebook-convert might hold things up unnecessarily)
            # -> actually, don't need to process the body AT ALL (doing so and adding our scripts etc is only bloat), we can do our own brief redirect.  But not yet, because we might have to set cookies first.
            else: doRedirect = value # TODO: do we need to check if response.code is in [301,302,303,307] before accepting a Location: ?
            if cookie_host and self.request.path=="/" and old_value_1.startswith("http") and not old_value_1.startswith("http://"+cookie_host+"/"):
                # This'll be a problem.  If the user is requesting / and the site's trying to redirect off-site, how do we know that the user isn't trying to get back to the URL box (having forgotten to clear the cookie) and now can't possibly do so because / always results in an off-site Location redirect ?
                # (The same thing can occur if offsite is False but we're redirecting to one of our other domains, hence we use the old_value_1.startswith condition instead of the 'offsite' flag; the latter is true only if NONE of our domains can do it.)
                # (DON'T just do this for ANY offsite url when in cookie_host mode - that could mess up images and things.  (Could still mess up images etc if they're served from / with query parameters; for now we're assuming path=/ is a good condition to do this.  The whole cookie_host thing is a compromise anyway; wildcard_dns is better.))
                if offsite: reason="which this adjuster is not currently set to adjust"
                else: reason="which will be adjusted at %s (not here)" % (value[len("http://"):(value+"/").index('/',len("http://"))],)
                return self.doResponse2(("<html><body>The server is redirecting you to <a href=\"%s\">%s</a> %s.</body></html>" % (value,old_value_1,reason)),True,False) # and 'Back to URL box' link will be added
          elif "set-cookie" in name.lower():
            if not isProxyRequest: value=cookie_domain_process(value,cookie_host)
            for ckName in upstreamGuard: value=value.replace(ckName,ckName+"1")
          headers_to_add.append((name,value))
          if name.lower()=="content-type":
            if do_epubtozip: value="application/zip"
            value=value.lower()
            if not options.askBitrate: do_mp3 = (value=="audio/mpeg" or (value.startswith("application/") and response.headers.get("Content-Disposition","").replace('"','').endswith('.mp3'))) # else do only if was set in converterFlags
            do_domain_process = ("html" in value or "css" in value or "javascript" in value or "json" in value or "rss+xml" in value or self.request.path.endswith(".js") or self.request.path.endswith(".css")) # and hope the server doesn't incorrectly say text/plain or something for a CSS or JS that doesn't end with that extension
            do_js_process = ("html" in value or "javascript" in value or self.request.path.endswith(".js"))
            do_html_process = ("html" in value) # TODO: configurable?
            do_json_process = ("json" in value)
            do_css_process = ("css" in value or self.request.path.endswith(".css"))
            if "charset=" in value:
                charset=extractCharsetEquals(value)
                if do_html_process: headers_to_add[-1]=((name,value.replace(charset,"utf-8"))) # we'll be converting it
            elif do_html_process: headers_to_add[-1]=((name,value+"; charset=utf-8")) # ditto (don't leave as latin-1)
          # TODO: if there's no content-type header, send one anyway, with a charset
        self.set_status(response.code) # (not before here! as might return doResponse2 above which will need status 200.  Redirect without Location gets "unknown error 0x80072f76" on IEMobile 6.)
        added = {'set-cookie':1} # might have been set by authenticates_ok
        for name,value in headers_to_add:
          value = value.replace("\t"," ") # needed for some servers
          if name.lower() in added: self.add_header(name,value)
          else: self.set_header(name,value) # overriding any Tornado default
          added[name.lower()]=1
        if doRedirect:
            # ignore response.body and put our own in
            return self.redirect(doRedirect,response.code)
        body = response.body
        if not body: return self.myfinish() # might just be a redirect (TODO: if it's not, set type to text/html and report error?)
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
            if do_epubtotext and self.isKindle():
                self.set_header("Content-Type","application/x-mobipocket-ebook")
                newext = ".mobi"
            else:
                self.set_header("Content-Type","text/plain; charset=utf-8")
                newext = ".txt"
            self.set_header("Content-Disposition","attachment; filename="+urllib.quote(self.request.uri[self.request.uri.rfind("/")+1:self.request.uri.rfind(".")]+newext))
            # IEMobile 6 (and 7) ignores Content-Disposition and just displays the text in the browser using fonts that can't be made much bigger, even if you set Content-Type to application/octet-stream and filename to something ending .doc (or no filename at all), and even if you change the URL extension from TxT to TxQ or something.  Even a null-or-random byte or two before the BOM doesn't stop it.  Opening a real PDF file causes "Error: This file cannot be viewed on the device" (even if a PDF viewer is installed and associated with PDF files).  Serving a text file with Content-Type application/vnd.ms-cab-compressed results in no error but no download either (real CAB files give a download question); same result for application/msword or application/rtf.
            # And Opera Mini's not much help on that platform because its fonts can't be enlarged much (registry hacks to do so don't seem to work on non-touchscreen phones), although it could be squinted at to save some text files for later.
            # Opera Mobile 10 on Windows Mobile also has trouble recognising Content-Disposition: attachment, even though Opera Mini is fine with it.
            # Could show text as HTML, but that wouldn't allow saving multiple files for later (unless they all fit in cache, but even then navigation is restrictive).
            import tempfile
            if do_pdftotext: ext="pdf"
            elif do_epubtotext: ext="epub"
            else: ext="" # shouldn't get here
            if self.checkTextCache(newext): return
            
            f=tempfile.NamedTemporaryFile(delete=False,suffix="."+ext) # Python 2.6+ (TODO: if doing pdf/epub conversion in a Python 2.5 environment, would need fd,fname = tempfile.mkstemp(suffix=), and use os.write(fd,..) and os.close(fd))
            f.write(body) ; f.close()
            def unlinkOutputLater(fn):
                k = (self.request.host, self.request.uri)
                kept_tempfiles[k] = fn # it's ready for now
                def tryDel(k):
                    try: del kept_tempfiles[k]
                    except: pass
                IOLoop.instance().add_timeout(time.time()+options.pdfepubkeep,lambda *args:(tryDel(k),unlink(fn)))
            def txtCallback(self,fn,cmdname,err):
                try: txt = open(fn+newext).read()
                except: # try to diagnose misconfiguration
                    # TODO: change Content-Type and Content-Disposition headers if newext==".mobi" ? (but what if it's served by ANOTHER request?)
                    txt = "Could not read %s's output from %s\n%s\n(This is %s)" % (cmdname,fn+newext,err,serverName)
                    try: open(fn+newext,"w").write(txt) # must unconditionally leave a .txt file as there might be other requests waiting on cache
                    except: txt += "\nCould not write to "+fn+".txt" # TODO: logging.error as well ?
                unlinkOutputLater(fn+newext)
                unlink(fn)
                if self.inProgress_run(): return
                if newext==".mobi": self.write(txt)
                else: self.write(remove_blanks_add_utf8_BOM(txt))
                self.myfinish()
            self.inProgress() # if appropriate
            if do_pdftotext:
                if options.pdfepubkeep: runFilter(("pdftotext -enc UTF-8 -nopgbrk \"%s\" \"%s.txt\"" % (f.name,f.name)),"",(lambda out,err:txtCallback(self,f.name,"pdftotext",out+err)), False)
                else: runFilter(("pdftotext -enc UTF-8 -nopgbrk \"%s\" -" % f.name),"",(lambda out,err:(unlink(f.name),self.write(remove_blanks_add_utf8_BOM(out)),self.myfinish())), False) # (pipe o/p from pdftotext directly, no temp outfile needed)
            elif self.isKindle(): runFilter(("ebook-convert \"%s\" \"%s.mobi\"" % (f.name,f.name)),"",(lambda out,err:txtCallback(self,f.name,"ebook-convert",out+err)), False)
            else: runFilter(("ebook-convert \"%s\" \"%s.txt\"" % (f.name,f.name)),"",(lambda out,err:txtCallback(self,f.name,"ebook-convert",out+err)), False)
            return
        if do_domain_process and not isProxyRequest: body = domain_process(body,cookie_host) # first, so filters to run and scripts to add can mention new domains without these being redirected back
        # Must also do things like 'delete' BEFORE the filters, especially if lxml is in use and might change the code so the delete patterns aren't recognised.  But do JS process BEFORE delete, as might want to pick up on something that was there originally.  (Must do it AFTER domain process though.)
        if do_js_process: body = js_process(body,self.urlToFetch)
        if not self.checkBrowser(options.deleteOmit):
            for d in options.delete:
                body=re.sub(d,"",body)
            if options.delete_doctype:
                body=re.sub("^<![dD][oO][cC][tT][yY][pP][eE][^>]*>","",body,1)
        if do_css_process:
            for d in options.delete_css:
                body=re.sub(d,"",body)
        # OK to change the code now:
        adjustList = []
        if do_html_process:
          if self.htmlOnlyMode(): adjustList.append(StripJSEtc())
          elif options.upstream_guard:
            # don't let upstream scripts get confused by our cookies (e.g. if the site is running Web Adjuster as well)
            # TODO: do it in script files also?
            if options.cssName: adjustList.append(transform_in_selected_tag("script",lambda s:s.replace("adjustCssSwitch","adjustCssSwitch1")))
            if options.htmlFilterName: adjustList.append(transform_in_selected_tag("script",lambda s:s.replace("adjustNoFilter","adjustNoFilter1")))
            if options.renderName: adjustList.append(transform_in_selected_tag("script",lambda s:s.replace("adjustNoRender","adjustNoRender1")))
        if (options.pdftotext or options.epubtotext or options.epubtozip or options.askBitrate or options.mailtoPath) and (do_html_process or (do_json_process and options.htmlJson)) and not any(re.search(x,self.urlToFetch) for x in options.skipLinkCheck):
            # Add PDF links BEFORE the external filter, in case the external filter is broken and we have trouble parsing the result
            if do_html_process: adjustList.append(AddConversionLinks(options.wildcard_dns or isProxyRequest,self.isKindle()))
            else:
                ctl = find_HTML_in_JSON(body)
                for i in range(1,len(ctl),2):
                    ctl[i] = json_reEscape(add_conversion_links(ctl[i],options.wildcard_dns or isProxyRequest,self.isKindle()))
                body = "".join(ctl)
        cssToAdd,attrsToAdd = self.cssAndAttrsToAdd()
        if cssToAdd:
          # remove !important from other stylesheets
          important = re.compile("! *important")
          if (do_html_process or (do_css_process and not self.urlToFetch == cssToAdd and not (options.protectedCSS and re.search(options.protectedCSS,self.urlToFetch)))) and re.search(important,body):
            if do_css_process: body=re.sub(important,"",body)
            else: adjustList.append(transform_in_selected_tag("style",lambda s:re.sub(important,"",s))) # (do_html_process must be True here)
        if adjustList: body = HTML_adjust_svc(body,adjustList)
        callback = lambda out,err:self.doResponse2(out,do_html_process,do_json_process)
        htmlFilter = self.getHtmlFilter()
        if do_html_process and htmlFilter:
            if options.htmlText: runFilterOnText(htmlFilter,find_text_in_HTML(body),callback)
            else: runFilter(htmlFilter,body,callback)
        elif do_json_process and options.htmlJson and htmlFilter:
            if options.htmlText: htmlFunc = find_text_in_HTML
            else: htmlFunc = None
            runFilterOnText(htmlFilter,find_HTML_in_JSON(body,htmlFunc),callback,True)
        elif do_mp3 and options.bitrate:
            runFilter("lame --quiet --mp3input -m m --abr %d - -o -" % options.bitrate,body,callback,False) # -m m = mono (TODO: optional?)
        else: callback(body,"")
    def getHtmlFilter(self,filterNo=None):
        if not options.htmlFilterName: return None
        if filterNo and '#' in options.htmlFilter:
            return options.htmlFilter.split('#')[filterNo]
        anf = self.getCookie("adjustNoFilter")
        if not anf: anf = "0"
        elif '-' in anf: anf = anf[anf.rindex("-")+1:]
        if anf=="1": return None
        elif '#' in options.htmlFilter:
            htmlFilter = options.htmlFilter.split('#')
            if anf=="0": return htmlFilter[0]
            else: return htmlFilter[int(anf)-1]
        else: return options.htmlFilter
    def doResponse2(self,body,do_html_process,do_json_process):
        debuglog("doResponse2 "+self.request.uri)
        # 2nd stage (domain change and external filter
        # has been run) - now add scripts etc, and render
        canRender = options.render and (do_html_process or (do_json_process and options.htmlJson)) and not self.checkBrowser(options.renderOmit)
        jsCookieString = ';'.join(self.request.headers.get_list("Cookie"))
        if do_html_process: body = html_additions(body,self.cssAndAttrsToAdd(),self.checkBrowser(options.cssNameReload),self.cookieHostToSet(),jsCookieString,canRender,self.cookie_host(),self.is_password_domain)
        callback = lambda out,err:self.doResponse3(out)
        if canRender and not "adjustNoRender=1" in jsCookieString:
            if do_html_process: func = find_text_in_HTML
            else: func=lambda body:find_HTML_in_JSON(body,find_text_in_HTML)
            debuglog("runFilterOnText Renderer")
            runFilterOnText(lambda t:Renderer.getMarkup(ampDecode(t.decode('utf-8'))).encode('utf-8'),func(body),callback,not do_html_process,chr(0))
        else: callback(body,"")
    def doResponse3(self,body):
        # 3rd stage (rendering has been done)
        debuglog("doResponse3 (len=%d)" % len(body))
        self.write(body)
        self.myfinish()
    def sendHead(self):
        # for options.redirectFiles: it looks like we have a "no processing necessary" request that we can tell the browser to get from the real site.  But just confirm it's not a mis-named HTML document.
        body = self.request.body
        if not body: body = None
        if hasattr(self,"original_referer"): self.request.headers["Referer"],self.original_referer = self.original_referer,self.request.headers["Referer"]
        ph,pp = upstream_proxy_host, upstream_proxy_port
        httpfetch(self.urlToFetch,
                  connect_timeout=60,request_timeout=120, # same TODO as above
                  proxy_host=ph, proxy_port=pp,
                  method="HEAD", headers=self.request.headers, body=body,
                  callback=lambda r:self.headResponse(r),follow_redirects=True)
    def headResponse(self,response):
        self.restore_request_headers()
        if hasattr(self,"original_referer"): self.request.headers["Referer"],self.original_referer = self.original_referer,self.request.headers["Referer"]
        might_need_processing_after_all = True
        for name,value in response.headers.get_all():
          if name.lower()=="content-type":
            value=value.lower()
            might_need_processing_after_all = ("html" in value or "css" in value or "javascript" in value or "json" in value or "rss+xml" in value) # these need at least domain processing
        # TODO: what if browser sent If-Modified-Since and it returned 304 Not Modified, which has no Content-Type?  (I suppose 200 w/out Content Type should assume HTML.)  If 304, we currently perform a fetch and log it, which seems a bit silly (although this shouldn't happen unless we previously proxied the file anyway)
        if might_need_processing_after_all: self.sendRequest([False]*4,False,False,follow_redirects=False)
        else:
            if not options.logRedirectFiles: self.request.suppress_logging = True
            self.redirect(self.urlToFetch)
    def isKindle(self): return options.epubtotext and self.checkBrowser(["Kindle"]) and self.checkBrowser(["Linux"]) # (don't do it if epubtotext is false as might want epubtozip links only; TODO: some reports say Kindle Fire in Silk mode doesn't mention "Kindle" in user-agent)
    def checkBrowser(self,blist):
        assert type(blist)==list # (if it's a string we don't know if we should check for just that string or if we should .split() it on something)
        ua = self.request.headers.get("User-Agent","")
        return any(b in ua for b in blist)

class SynchronousRequestForwarder(RequestForwarder):
   def get(self, *args, **kwargs):     return self.doReq()
   def head(self, *args, **kwargs):    return self.doReq()
   def post(self, *args, **kwargs):    return self.doReq()
   def put(self, *args, **kwargs):     return self.doReq()
   def delete(self, *args, **kwargs):  return self.doReq()
   def patch(self, *args, **kwargs):   return self.doReq()
   def options(self, *args, **kwargs): return self.doReq()
   def connect(self, *args, **kwargs): raise Exception("CONNECT is not implemented in WSGI mode")
   def myfinish(self): pass

kept_tempfiles = {} # TODO: delete any outstanding kept_tempfiles.values() on server interrupt

def addArgument(url,extraArg):
    if '#' in url: url,hashTag = url.split('#',1)
    else: hashTag=None
    if '?' in url: url += '&'+extraArg
    else: url += '?'+extraArg
    if hashTag: url += '#'+hashTag
    return url

def remove_blanks_add_utf8_BOM(out):
    # for writing text files from PDF and EPUB
    return '\xef\xbb\xbf'+"\n".join([x for x in out.replace("\r","").split("\n") if x])

def rm_u8punc(u8):
    # for SMS links, turn some Unicode punctuation into ASCII (helps with some phones)
    for k,v in u8punc_d: u8=u8.replace(k,v)
    return u8
u8punc_d=u"\u2013 -- \u2014 -- \u2018 ' \u2019 ' \u201c \" \u201d \" \u2032 ' \u00b4 ' \u00a9 (c) \u00ae (r)".encode('utf-8').split()
u8punc_d = zip(u8punc_d[::2], u8punc_d[1::2])

def getSearchURL(q):
    if not options.search_sites: return "http://"+urllib.quote(q) # ??
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
def htmlhead(title): return '<html><head><title>%s</title><meta name="mobileoptimized" content="0"><meta name="viewport" content="width=device-width"></head><body>' % title
def urlbox_html(htmlonly_checked,cssOpts_html):
    r = htmlhead('Web Adjuster start page')+'<form action="/">'+options.boxPrompt+': <input type="text" name="q"><input type="submit" value="Go">'+searchHelp()+cssOpts_html # 'go' button MUST be first, before cssOpts_html, because it's the button that's hit when Enter is pressed.  (So might as well make the below focus() script unconditional even if there's cssOpts_html.  Minor problem is searchHelp() might get in the way.)
    if htmlonly_checked: htmlonly_checked=' checked="checked"'
    else: htmlonly_checked = ""
    if options.htmlonly_mode:
        if not r.endswith("</p>"): r += "<br>"
        r += '<input type="checkbox" name="pr"'+htmlonly_checked+'> HTML-only mode'
    r += '</form><script><!--\ndocument.forms[0].q.focus();\n//--></script>'
    if options.urlbox_extra_html: r += options.urlbox_extra_html
    return r+'</body></html>'

backScript="""<script><!--
document.write('<br><a href="javascript:history.go(-1)">Back to previous page</a>')
//--></script>"""
backScriptNoBr="""<script><!--
document.write('<a href="javascript:history.go(-1)">Back to previous page</a>')
//--></script>"""
# (HTML5 defaults type to text/javascript, as do all pre-HTML5 browsers including NN2's 'script language="javascript"' thing, so we might as well save a few bytes)

rubyCss1 = "ruby{display:inline-table;}ruby *{display: inline;line-height:1.0;text-indent:0;text-align:center;white-space:nowrap;}rb{display:table-row-group;font-size: 100%;}rt{display:table-header-group;font-size:100%;line-height:1.1;}" ; assert not '"' in rubyCss1
# but that's no good on WebKit browsers.  Did have an after-the-fact innerHTML 'hack' to remove 'display' on WebKit (which is similar to what Wenlin uses because I sent it to them as well), but it might not always interact well with all JS on all sites, so we'd better double-up script/noscript:
rubyScript = '<script><!--\nif(document.readyState!="complete"){var s="'+rubyCss1+'";var wk=navigator.userAgent.indexOf("WebKit/");if(wk>-1){s=s.replace(/display[^;]*;/g,"");var v=navigator.userAgent.slice(wk+7,wk+12);if(v>=534.3&&v<535.7)s+="rt{padding-left:1ex;padding-right:1ex;}"}document.write("<style>"+s+"<\/style>")}\n//--></script><noscript><style>'+rubyCss1+'</style></noscript>'
# (and hope nobody in webkit uses noscript, or ruby will line up wrong)
# And the following hack is to stop the styles in the 'noscript' and the variable (and any others) from being interpreted if an HTML document with this processing is accidentally referenced as a CSS source (which can mess up ruby):
rubyScript = "<!-- { } @media(none) { -->" + rubyScript
# By the way, also try to specify some nice fonts (but IE doesn't like this) :
rubyScript_fonts = '<!--[if !IE]>--><style>rt { font-family: Gandhari, DejaVu Sans, Lucida Sans Unicode, Times New Roman, serif !important; }</style><!--<![endif]-->'
rubyScript += rubyScript_fonts
# and this goes at the END of the body:
rubyEndScript = """
<script><!--
var wk=navigator.userAgent.indexOf("WebKit/");if(wk>-1 && navigator.userAgent.slice(wk+7,wk+12)>534){var rbs=document.getElementsByTagName('rb');for(var i=0;i<rbs.length;i++)rbs[i].innerHTML='&#8203;'+rbs[i].innerHTML+'&#8203;'}
function treewalk(n) { var c=n.firstChild; while(c) { if (c.nodeType==1 && c.nodeName!="SCRIPT" && c.nodeName!="TEXTAREA" && !(c.nodeName=="A" && c.href)) { treewalk(c); if(c.nodeName=="RUBY" && c.title && !c.onclick) c.onclick=Function("alert(this.title)") } c=c.nextSibling; } } function tw() { treewalk(document.body); window.setTimeout(tw,5000); } treewalk(document.body); window.setTimeout(tw,1500);
//--></script>"""

def bookmarklet(submit_url):
    # get the bookmarklet to fetch more JS and eval/exec it, seeing as it'll need to talk to the server anyway (avoids cluttering bookmarks / can fix bugs later)
    # TODO: ensure server response is cached!  last-modified when adjuster started ??
    # TODO: make sure submit_url doesn't contain anything that can't be embedded in ''s within ""s (this depends on the user's setting of options.submitPath! although anything 'nasty' could run into trouble with browser URL-escaping anyway)
    if not options.submitBookmarklet: return ""
    if not options.htmlFilterName: names=['filter']
    elif '#' in options.htmlFilter: names=options.htmlFilterName.split('#')[1:]
    else: names = [options.htmlFilter]
    if len(names)>1: plural="s"
    else: plural=""
    class C:
        def __init__(self): self.reset()
        def __call__(self):
            ret = self.noInc()
            self.count += 1 ; return ret
        def reset(self):
            self.count = 0 ; return ""
        def noInc(self): return chr(self.count+ord('A')) # TODO: what if there are too many filters for this URL scheme? (and remember we're sharing the 'namespace' with Base64 encodings - don't clash with those)
    c = C()
    # TODO: The following nested quoting is horrible.
    # Is there an Obfuscated Python+Javascript contest? :)
    # (_IHQ_ = 'InnerHtmlQuote', is also checked for in preprocessOptions)
    return '<script><!--\nif(typeof XMLHttpRequest!="undefined"&&typeof JSON!="undefined"&&JSON.parse&&document.getElementById&&document.readyState!="complete"){var n=navigator.userAgent;var i=n.match(/iPad|iPhone/),a=n.match(/Android/),c="",t=0,j="javascript:",u="var r=new XMLHttpRequest();r.open(\'GET\',\''+submit_url+'b",v="\',false);r.send();eval(r.responseText)"; var u2=j+"if(window.doneMasterFrame!=1){var d=document;var fs=d.createElement(\'frameset\');fs.appendChild(d.createElement(\'frame\'));fs.firstChild.src=self.location;while(d.firstChild)d.removeChild(d.firstChild);d.appendChild(fs);window.doneMasterFrame=1}"+u;u=j+u;if(i||a){t="'+submit_url+'"+(i?"i":"a");u="#"+u}else c=" onclick=_IHQ_alert(\'To use this bookmarklet, first drag it to your browser toolbar. (If your browser does not have a toolbar, you probably have to paste text manually.)\');return false_IHQ_";document.write(((i||a)?"On "+(i?"iOS":"Android")+", you can install a special kind of bookmark (called a \'bookmarklet\'), and activate":"On some browsers, you can drag a \'bookmarklet\' to the toolbar, and press")+" it later to use this service on the text of another site. '+quote_for_JS_doublequotes(r'<span id="bookmarklet"><a href="#bookmarklet" onClick="document.getElementById('+"'bookmarklet'"+r').innerHTML=&@]@+@]@quot;Basic bookmarklet'+plural+' (to process <b>one page</b> when activated): '+(' | '.join(('<a href="@]@+(t?(t+@]@'+c.noInc()+'@]@):\'\')+u+@]@'+c()+'@]@+v+@]@"@]@+c+@]@>'+name+'</a>') for name in names)).replace(r'"','_IHQ_')+c.reset()+'. Advanced bookmarklet'+plural+' (to process <b>a whole site</b> when activated, but with the side-effect of resetting the current page and getting the address bar \'stuck\'): '+(' | '.join(('<a href="@]@+(t?(t+@]@'+c.noInc()+'@]@):\'\')+u2+@]@'+c()+'@]@+v+@]@"@]@+c+@]@>'+name+'+</a>') for name in names)).replace(r'"','_IHQ_')+'&@]@+@]@quot;.replace(/_IHQ_/g,\'&@]@+@]@quot;\');return false">Show bookmarklet'+plural+'</a></span>').replace('@]@','"')+'")}\n//--></script>' # JSON.parse is needed (rather than just using eval) because we'll also need JSON.stringify (TODO: unless we fall back to our own slower encoding; TODO: could also have a non-getElementById fallback that doesn't hide the bookmarklets)
    # 'resetting the current page': so you lose anything you typed in text boxes etc
    # (DO hide bookmarklets by default, because don't want to confuse users if they're named the same as the immediate-action filter selections at the bottom of the page)
    # TODO: maybe document that on Chrome Mobile (Android/iOS) you can tap address bar and start typing the bookmarklet name IF you've sync'd it from a desktop
    # TODO: we append '+' to the names of the 'advanced' versions of the bookmarklets, but we don't do so on the Android/iOS title pages; is that OK?
def quote_for_JS_doublequotes(s): return s.replace("\\","\\\\").replace('"',"\\\"").replace("\n","\\n").replace('</','<"+"/') # for use inside document.write("") etc
def bookmarkletMainScript(jsonPostUrl):
    return r"""var leaveTags=%s,stripTags=%s;
function HTMLSizeChanged(callback) {
  // innerHTML size will usually change if there's a JS popup etc (TODO: could periodically do a full scan anyway, on the off-chance that some JS change somehow keeps length the same)
  if(typeof window.sizeChangedLoop=="undefined") window.sizeChangedLoop=0; var me=++window.sizeChangedLoop; // (we stop our loop if user restarts the bookmarklet and it starts another)
  var getLen = function(w) { var r=0; if(w.frames && w.frames.length) { var i; for(i=0; i<w.frames.length; i++) r+=getLen(w.frames[i]) } if(w.document && w.document.body && w.document.body.innerHTML) r+=w.document.body.innerHTML.length; return r };
  var curLen=getLen(window),
    stFunc=function(){if(window.sizeChangedLoop==me) window.setTimeout(tFunc,1000)},
    tFunc=function(){if(getLen(window)==curLen) stFunc(); else callback()};
  stFunc()
}
var texts,tLen,oldTexts,otPtr,replacements;
function all_frames_docs(c) { var f=function(w){if(w.frames && w.frames.length) { var i; for(i=0; i<w.frames.length; i++) f(w.frames[i]) } c(w.document) }; f(window) }
function tw0() {
  texts = new Array(); tLen=0;
  otPtr=0; all_frames_docs(function(d){walk(d,d)}) }
function adjusterScan() {
  oldTexts = new Array(); replacements = new Array();
  tw0();
  while(texts.length>0) {
    var r=new XMLHttpRequest();
    r.open("POST","%s",false);
    r.send(JSON.stringify(texts));
    replacements = JSON.parse(r.responseText);
    if (replacements.length>=texts.length) {
      oldTexts = texts; tw0();
    } else break; // TODO: handle as error?
    %s
  }
  HTMLSizeChanged(adjusterScan)
}
function walk(n,document) {
  var c=n.firstChild;
  while(c) {
    var cNext = c.nextSibling;
    if (c.nodeType==1 && stripTags.indexOf(c.nodeName)!=-1) { // TODO: this JS code might strip more stripTags than the Python shouldStripTag stuff does
      var ps = c.previousSibling;
      while (c.firstChild) {
        var tmp = c.firstChild; c.removeChild(tmp);
        n.insertBefore(tmp,c);
      }
      n.removeChild(c);
      if (ps && ps.nodeType==3 && ps.nextSibling && ps.nextSibling.nodeType==3) { ps.nodeValue += ps.nextSibling.nodeValue; n.removeChild(ps.nextSibling) }
      if (cNext && cNext.nodeType==3 && cNext.previousSibling && cNext.previousSibling.nodeType==3) { cNext.previousSibling.nodeValue += cNext.nodeValue; var tmp=cNext; cNext = cNext.previousSibling; n.removeChild(tmp) }
    }
    c=cNext;
  }
  c=n.firstChild;
  while(c) {
    var cNext = c.nextSibling;
    switch (c.nodeType) {
    case 1: if (leaveTags.indexOf(c.nodeName)==-1 && c.className!="_adjust0") walk(c,document); break;
    case 3:
      if (%s) {
          var i=otPtr;
          while (i<oldTexts.length && oldTexts[i]!=c.nodeValue) i++;
          if(i<replacements.length) {
            var newNode=document.createElement("span");
            newNode.className="_adjust0";
            n.replaceChild(newNode, c);
            newNode.innerHTML=replacements[i]; otPtr=i;
          } else if (tLen < %d) {
            texts[texts.length]=c.nodeValue;
            tLen += c.nodeValue.length;
          } else return; // will deal with rest next pass
      }
    }
    c=cNext;
  }
}adjusterScan()""" % (repr([t.upper() for t in options.leaveTags]),repr([t.upper() for t in options.stripTags]),jsonPostUrl,addRubyScript(),options.submitBookmarkletFilterJS,options.submitBookmarkletChunkSize)
def addRubyScript():
    if not options.headAppendRuby: return ""
    # rScript = rubyScript # doesn't work, fall back on:
    rScript = '<style>'+rubyCss1+'</style>'+rubyScript_fonts
    return r"""all_frames_docs(function(d) { if(d.rubyScriptAdded==1 || !d.body) return; var e=d.createElement('span'); e.innerHTML="%s"; d.body.insertBefore(e,d.body.firstChild);
    e=d.createElement('span'); e.innerHTML="%s"; d.body.appendChild(e); d.rubyScriptAdded=1 });""" % (quote_for_JS_doublequotes(rScript),quote_for_JS_doublequotes(rubyEndScript))

def unlink(fn):
    try: os.unlink(fn)
    except: pass

def runFilter(cmd,text,callback,textmode=True):
    # runs shell command 'cmd' on input 'text' in a new
    # thread, then gets Tornado to call callback(out,err)
    # If 'cmd' is not a string, assumes it's a function
    # to call (no new thread necessary, TODO: Jython/SMP)
    # this is for using runFilterOnText with an internal
    # callable such as the Renderer.  Similarly if 'cmd'
    # starts with a * then we assume the rest is the name
    # of a Python function to call on the text.
    if type(cmd)==type("") and cmd.startswith("*"):
        cmd = eval(cmd[1:]) # (normally a function name, but any Python expression that evaluates to a callable is OK, TODO: document this?  and incidentally if it evaluates to a string that's OK as well; the string will be given to an external command)
    if not type(cmd)==type(""):
        # return callback(cmd(text),"")
        # slightly more roundabout version to give watchdog ping a chance to work between cmd and callback:
        out = cmd(text)
        return IOLoop.instance().add_timeout(time.time(),lambda *args:callback(out,""))
    def subprocess_thread():
        global helper_thread_count
        helper_thread_count += 1
        sp=subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=textmode) # TODO: check shell=True won't throw error on Windows
        out,err = sp.communicate(text)
        if not out: out=""
        if not err: err="" # TODO: else logging.debug ? (some stderr might be harmless; don't want to fill normal logs)
        IOLoop.instance().add_callback(lambda *args:callback(out,err))
        helper_thread_count -= 1
    threading.Thread(target=subprocess_thread,args=()).start()

def sync_runFilter(cmd,text,callback,textmode=True):
    if type(cmd)==type("") and cmd.startswith("*"):
        cmd = eval(cmd[1:])
    if type(cmd)==type(""):
        sp=subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=textmode) # TODO: check shell=True won't throw error on Windows
        out,err = sp.communicate(text)
        if not out: out=""
        if not err: err="" # TODO: else logging.debug ? (some stderr might be harmless; don't want to fill normal logs)
    else: out,err = cmd(text),""
    callback(out,err)

def runBrowser(*args):
    def browser_thread():
        global helper_thread_count
        helper_thread_count += 1
        os.system(options.browser)
        helper_thread_count -= 1
        stopServer()
    threading.Thread(target=browser_thread,args=()).start()

def stopServer(*args): IOLoop.instance().add_callback(lambda *args:IOLoop.instance().stop())

def json_reEscape(u8str): return json.dumps(u8str.decode('utf-8','replace'))[1:-1] # omit ""s (necessary as we might not have the whole string here)

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
    if separator == options.separator:
        toSend=separator+toSend+separator
        sortout = lambda out:out.split(separator)[1:-1]
    else: sortout = lambda out:out.split(separator)
    runFilter(cmd,toSend,lambda out,err:callback("".join(getText(codeTextList,sortout(out),True)),err))

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
    def __init__(self,offsite_ok,isKindle):
        self.offsite_ok = offsite_ok
        self.isKindle = isKindle
    def init(self,parser):
        self.parser = parser
        self.gotPDF=self.gotEPUB=self.gotMP3=None
    def handle_starttag(self, tag, attrs):
        attrsD = dict(attrs)
        if tag=="a" and attrsD.get("href",None):
            l = attrsD["href"].lower()
            if l.startswith("http://"):
                if not self.offsite_ok and not url_is_ours(l): return # "offsite" link, can't process (TODO: unless we send it to ourselves via an alternate syntax)
                # TODO: (if don't implement processing the link anyway) insert explanatory text for why an alternate link wasn't provided?
            elif options.mailtoPath and l.startswith("mailto:"):
                r=['<'+tag+" "]
                for k,v in items(attrs):
                    if k.lower()=="href": v=options.mailtoPath+v[7:]
                    r.append(k+'="'+v.replace('&','&amp;').replace('"','&quot;').replace('&amp;#','&#').replace('%','%%+')+'"') # see comments in serve_mailtoPage re the %%+
                r.append('>')
                self.parser.addDataFromTagHandler("".join(r),True)
                return True # suppress original tag
            elif ":" in l and l.index(":")<l.find("/"): return # non-HTTP protocol - can't do (TODO: unless we do https, or send the link to ourselves via an alternate syntax)
            if l.endswith(".pdf") or guessCMS(l,"pdf"):
                self.gotPDF = attrsD["href"]
                if options.pdfomit and any(re.search(x,self.gotPDF) for x in options.pdfomit.split(",")): self.gotPDF = None
            if l.endswith(".epub") or guessCMS(l,"epub"):
                self.gotEPUB = attrsD["href"]
            if l.endswith(".mp3"):
                self.gotMP3 = attrsD["href"]
    def handle_endtag(self, tag):
        if tag=="a" and ((self.gotPDF and options.pdftotext) or (self.gotEPUB and (options.epubtozip or options.epubtotext)) or (self.gotMP3 and options.bitrate and options.askBitrate)):
            linksToAdd = []
            linkStart = "<a style=\"display:inline!important;float:none!important\" href=" # adding style in case a site styles the previous link with float, which won't work with our '('...')' stuff
            if self.gotPDF: linksToAdd.append("%s\"%s%s\">text</a>" % (linkStart,self.gotPDF,pdftotext_suffix))
            elif self.gotEPUB:
                if options.epubtotext:
                    if self.isKindle: txt = "mobi"
                    else: txt = "text"
                    linksToAdd.append("%s\"%s%s\">%s</a>" % (linkStart,self.gotEPUB,epubtotext_suffix,txt))
                if options.epubtozip and not self.isKindle: linksToAdd.append("%s\"%s%s\">zip</a>" % (linkStart,self.gotEPUB,epubtozip_suffix))
            elif self.gotMP3: linksToAdd.append("%s\"%s%s\">lo-fi</a>" % (linkStart,self.gotMP3,mp3lofi_suffix))
            if linksToAdd: self.parser.addDataFromTagHandler(" ("+", ".join(linksToAdd)+") ")
            self.gotPDF=self.gotEPUB=self.gotMP3=None
    def handle_data(self,data): pass
def add_conversion_links(h,offsite_ok,isKindle):
    # (wrapper for when we can't avoid doing a special-case HTMLParser for it)
    return HTML_adjust_svc(h,[AddConversionLinks(offsite_ok,isKindle)],can_use_LXML=False) # False because we're likely dealing with a fragment inside JSON, not a complete HTML document

class StripJSEtc:
    # TODO: HTML_adjust_svc might need to do handle_entityref and handle_charref to catch those inside scripts etc
    # TODO: change any "[if IE" at the start of comments (in case anyone using affected versions of IE wants to use this mode))
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
        if tag=="head":
            self.parser.addDataFromTagHandler('<meta name="mobileoptimized" content="0"><meta name="viewport" content="width=device-width"></head>',True) # TODO: document that htmlonly_mode adds this; might also want to have it when CSS is on
            return True # suppress </head> because we've done it ourselves in the above (had to or addDataFromTagHandler would have added it AFTER the closing tag)
        if tag in ['script','style']:
            self.suppressing = False ; return True
        elif tag=='noscript': return True
        else: return self.suppressing
    def handle_data(self,data):
        if self.suppressing: return ""

def guessCMS(url,fmt):
    # (TODO: more possibilities for this?  Option to HEAD all urls and return what they resolve to? but fetch-ahead might not be a good idea on all sites)
    return fmt and options.guessCMS and "?" in url and "format="+fmt in url.lower() and not ((not fmt=="pdf") and "pdf" in url.lower())

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
            self.out.append("<!--"+text.encode('utf-8')+"-->")
        def close(self): pass
    parser = Parser() ; parser.out = []
    for l in adjustList: l.init(parser)
    lparser = etree.HTMLParser(target=parser)
    etree.parse(StringIO(htmlStr.decode('utf-8','replace')), lparser)
    return "".join(parser.out)

def items(maybeDict):
    if type(maybeDict)==dict: return maybeDict.items()
    else: return maybeDict

def transform_in_selected_tag(intag,transformFunc):
    # assumes intag is closed and not nested, e.g. style, although small tags appearing inside it MIGHT work
    # also assumes transformFunc doesn't need to know about entity references etc (it's called for the data between them)
    class Adjustment:
        def init(self,parser):
            self.intag = False
            self.parser = parser
        def handle_starttag(self, tag, attrs):
            if tag==intag: self.intag=True
            elif intag=="script":
              attrsD = dict(attrs)
              if (attrsD.get("onclick",None) and transformFunc(attrsD["onclick"]) != attrsD["onclick"]) or (attrsD.get("id",None) and transformFunc(attrsD["id"]) != attrsD["id"]): # TODO: name as well? (shouldn't be needed for our own scripts)
                # Re-write the tag ourselves, with that attribute changed
                r=['<'+tag+" "]
                for k,v in items(attrs):
                    if k in ["onclick","id"]: v = transformFunc(v)
                    r.append(k+'="'+v.replace('&','&amp;').replace('"','&quot;')+'"')
                r.append('>')
                self.parser.addDataFromTagHandler("".join(r),True)
                return True
        def handle_endtag(self, tag):
            if tag==intag: self.intag=False
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
    if type(htmlStr)==type(u""): htmlStr=htmlStr.encode('utf-8') # just in case
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
        def shouldStripTag(self,tag):
            self.ignoredLastTag = (tag.lower() in options.stripTags and (self.ignoredLastTag or self.getBytePos()==self.lastCodeStart))
            return self.ignoredLastTag
        def handle_starttag(self, tag, attrs):
            if self.shouldStripTag(tag): return
            if tag in options.leaveTags:
                self.ignoreData=True
        def handle_endtag(self, tag):
            if self.shouldStripTag(tag): return
            if tag in options.leaveTags:
                self.ignoreData=False
            # doesn't check for nesting or balancing
            # (documented limitation)
        def getBytePos(self): # TODO: duplicate code
            line,offset = self.getpos()
            while line>self.knownLine:
                self.knownLine += 1
                self.knownLinePos=htmlStr.find('\n',self.knownLinePos)+1
            return self.knownLinePos + offset
        def handle_data(self,data,datalen=None):
            if self.ignoreData or not data.strip():
                return # keep treating it as code
            if datalen==None: data = latin1decode(data)
            dataStart = self.getBytePos()
            if self.codeTextList and (self.ignoredLastTag or dataStart == self.lastCodeStart): # no intervening code, merge (TODO reduce string concatenation?)
                self.codeTextList[-1] += data
            else:
                self.codeTextList.append(latin1decode(htmlStr[self.lastCodeStart:dataStart]))
                self.codeTextList.append(data)
            if datalen==None: datalen = len(data) # otherwise we're overriding it for entity refs etc
            self.lastCodeStart = dataStart+datalen
        def handle_entityref(self,name):
            if name in htmlentitydefs.name2codepoint and not name in ['lt','gt','amp']:
                self.handle_data(unichr(htmlentitydefs.name2codepoint[name]).encode('utf-8'),len(name)+2)
            # else leave the entity ref as-is
        def handle_charref(self,name):
            if name.startswith('x'): d=unichr(int(name[1:],16))
            else: d=unichr(int(name))
            if d in u'<>&': pass # leave entity ref as-is
            else: self.handle_data(d.encode('utf-8'),len(name)+3)
    parser = Parser()
    parser.codeTextList = [] ; parser.lastCodeStart = 0
    parser.knownLine = 1 ; parser.knownLinePos = 0
    parser.ignoreData = parser.ignoredLastTag = False
    htmlStr = fixHTML(htmlStr)
    err=""
    try:
        parser.feed(htmlStr) ; parser.close()
    except UnicodeDecodeError, e:
        # sometimes happens in parsing the start of a tag in duff HTML (possibly emitted by a duff htmlFilter if we're currently picking out text for the renderer)
        try: err="UnicodeDecodeError at bytes %d-%d: %s" % (e.start,e.end,e.reason)
        except: err = "UnicodeDecodeError"
    except HTMLParseError, e: # rare?
        try: err="HTMLParseError: "+e.msg+" at "+str(e.lineno)+":"+str(e.offset) # + ' after '+repr(htmlStr[parser.lastCodeStart:])
        except: err = "HTMLParseError"
        logging.info("WARNING: find_text_in_HTML finishing early due to "+err)
    # If either of the above errors occur, we leave the rest of the HTML as "code" i.e. unchanged
    if len(parser.codeTextList)%2: parser.codeTextList.append("") # ensure len is even before appending the remaining code (adjustment is required only if there was an error)
    if not options.renderDebug: err=""
    elif err: err="<!-- "+err+" -->"
    parser.codeTextList.append(err+latin1decode(htmlStr[parser.lastCodeStart:]))
    return parser.codeTextList

def LXML_find_text_in_HTML(htmlStr):
    import htmlentitydefs
    class Parser:
        def shouldStripTag(self,tag):
            self.ignoredLastTag = (tag.lower() in options.stripTags and (self.ignoredLastTag or not self.out))
            return self.ignoredLastTag
        def start(self, tag, attrs):
            sst = self.shouldStripTag(tag)
            self.out.append(lxmlEncodeTag(tag,dict((k,v.encode('utf-8')) for k,v in dict(attrs).items())))
            if (not sst) and tag in options.leaveTags:
                self.ignoreData=True
                if tag in ['script','style']: self.ignoreData = 2 # TODO: document this hack (see below).  It relies on 'script' and 'style' being in leaveTags (as it is by default).  Needed for at least some versions of LXML.
        def end(self, tag):
            sst = self.shouldStripTag(tag)
            if tag not in html_tags_not_needing_ends:
                self.out.append("</"+tag+">")
            if (not sst) and tag in options.leaveTags:
                self.ignoreData=False
        def data(self,unidata):
            data = unidata.encode('utf-8')
            if not self.ignoreData==2: data = ampEncode(data) # we want entity refs (which we assume to have been decoded by LXML) to be left as-is.  But DON'T do this in 'script' or 'style' - it could mess everything up (at least some versions of lxml already treat these as cdata)
            if self.ignoreData or not data.strip():
                self.out.append(data) ; return
            if self.ignoredLastTag: self.out = []
            out = "".join(self.out)
            if self.codeTextList and not out:
                # merge (TODO reduce string concatenation?)
                self.codeTextList[-1] += data
            else:
                self.codeTextList.append(out)
                self.codeTextList.append(data)
            self.out = []
        def comment(self,text): # TODO: same as above's def comment
            self.out.append("<!--"+text.encode('utf-8')+"-->")
        def close(self): pass
    parser = Parser() ; parser.out = []
    parser.codeTextList = []
    parser.ignoreData = parser.ignoredLastTag = False
    lparser = etree.HTMLParser(target=parser)
    etree.parse(StringIO(htmlStr.decode('utf-8','replace')), lparser)
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
        if (j==len(text) or text[j] in '/?"\'') and not text[j-1] in '.-': # seems like a normal link (omit ones ending with . or - because they're likely to be part of a domain computation; such things are tricky but might be more likely to work if we DON'T touch them if it has e.g. "'test.'+domain" where "domain" is a variable that we've previously intercepted)
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
        if prefix.startswith('*'): cond = (prefix[1:] in body)
        else: cond = url.startswith(prefix)
        if cond: body=body.replace(srch,rplac)
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
    if cssReload_cookieSuffix and isOn: return r"""<script><!--
if(!%s%s&&document.readyState!='complete')document.write("%s: On | "+'<a href="'+location.href.replace(location.hash,"")+'%s%s=%s">Off<\/a> ')
//--></script>""" % (detect_iframe,extraCondition,readableName,cssReload_cookieSuffix,cookieName,setOff) # TODO: create a unique id for the link and # it ? (a test of this didn't always work on Opera Mini though)
    elif cssReload_cookieSuffix: return r"""<script><!--
if(!%s%s&&document.readyState!='complete')document.write("%s: "+'<a href="'+location.href.replace(location.hash,"")+'%s%s=%s">On<\/a> | Off ')
//--></script>""" % (detect_iframe,extraCondition,readableName,cssReload_cookieSuffix,cookieName,setOn)
    elif isOn: return r"""<script><!--
if(!%s%s&&document.readyState!='complete')document.write("%s: On | "+'<a href="javascript:document.cookie=\'%s=%s;domain=%s;expires=%s;path=/\';document.cookie=\'%s=%s;domain=.%s;expires=%s;path=/\';location.reload(true)">Off<\/a> ')
//--></script>""" % (detect_iframe,extraCondition,readableName,cookieName,setOff,cookieHostToSet,cookieExpires,cookieName,setOff,cookieHostToSet,cookieExpires)
    else: return r"""<script><!--
if(!%s%s&&document.readyState!='complete')document.write("%s: "+'<a href="javascript:document.cookie=\'%s=%s;domain=%s;expires=%s;path=/\';document.cookie=\'%s=%s;domain=.%s;expires=%s;path=/\';location.reload(true)">On<\/a> | Off ')
//--></script>""" % (detect_iframe,extraCondition,readableName,cookieName,setOn,cookieHostToSet,cookieExpires,cookieName,setOn,cookieHostToSet,cookieExpires)

def reloadSwitchJSMultiple(cookieName,jsCookieString,flipInitialItems,readableNames,cookieHostToSet,cookieExpires):
    # flipInitialItems: for adjustNoFilter compatibility between one and multiple items, 1 means off, 0 (default) means 1st item, 2 means 2nd etc.  (Currently, this function is only ever called with flipInitialItems==True)
    r = [r"""<script><!--
if(!%s&&document.readyState!='complete'){document.write("%s: """ % (detect_iframe,readableNames[0])]
    spanStart = 0
    for i in range(len(readableNames)):
        if i: r.append(" | ")
        if i==len(readableNames)-1:
            rN = "Off"
            if flipInitialItems: chk = "1"
            else: chk = "0"
        else:
            if i==2:
                spanStart = len(r)
                r.append('<span id=adjustNoFilter>')
                # (gets here if len(readableNames)>3; use this as ID because we already have transform_in_selected_tag on it) (NB if quoting the id, use r'\"' because we're in a document.write)
            rN = readableNames[i+1]
            if flipInitialItems:
                if i: chk=str(i+1)
                else: chk="0"
            else: chk = str(i+1)
        if i >= 9: chk="x"+str(len(chk))+"-"+chk # so we can continue to use the 'x in string' code without worrying about common prefixes 1, 10, 100 ...
        isOn = (cookieName+"="+chk) in jsCookieString
        if chk=="0" and not isOn and not cookieName+"=" in jsCookieString: isOn = 1 # default
        if isOn:
            r.append(rN)
            if 2 <= i < len(readableNames)-1:
                # want to keep it unhidden if an option is selected that's not in the first 2 and isn't the "Off"
                del r[spanStart]
                spanStart = 0
        else: r.append(r""""+'<a href="javascript:document.cookie=\'%s=%s;domain=%s;expires=%s;path=/\';document.cookie=\'%s=%s;domain=.%s;expires=%s;path=/\';location.reload(true)">'+"%s<"+"\/a>""" % (cookieName,chk,cookieHostToSet,cookieExpires,cookieName,chk,cookieHostToSet,cookieExpires,rN))
    if spanStart: r.append('<"+"/span>')
    r.append(' ")')
    if spanStart: r.append(r';if(document.getElementById){var v=document.getElementById("adjustNoFilter");if(v.innerHTML){v.OIH=v.innerHTML;if(v.OIH==v.innerHTML)v.innerHTML="<a href=\"#adjustNoFilter\" onClick=\"this.parentNode.innerHTML=this.parentNode.OIH;return false\">More<"+"/A>"; }}') # (hide the span by default, if browser has enough JS support to do it) (TODO: could do it with non-innerHTML DOM functionality if necessary, but that's more long-winded and might also need to look out for non-working 'this' functionality)
    r.append('}\n//--></script>')
    return "".join(r)

def detect_renderCheck(): return r"""(document.getElementsByTagName && function(){var b=document.getElementsByTagName("BODY")[0],d=document.createElement("DIV"),s=document.createElement("SPAN"); if(!(b.appendChild && b.removeChild && s.innerHTML))return 0; d.appendChild(s); function wid(chr) { s.innerHTML = chr; b.appendChild(d); var width = s.offsetWidth; b.removeChild(d); return width; } var w1=wid("\u%s"),w2=wid("\uffff"),w3=wid("\ufffe"),w4=wid("\u2fdf"); return (w1!=w2 && w1!=w3 && w1!=w4)}())""" % options.renderCheck
# ffff, fffe - guaranteed invalid by Unicode, but just might be treated differently by browsers
# 2fdf unallocated character at end of Kangxi radicals block, hopefully won't be used
#  do NOT use fffd, it's sometimes displayed differently to other unrenderable characters
# Works even in Opera Mini, which must somehow communicate the client's font metrics to the proxy

def html_additions(html,(cssToAdd,attrsToAdd),slow_CSS_switch,cookieHostToSet,jsCookieString,canRender,cookie_host,is_password_domain):
    # Additions to make to HTML only (not on HTML embedded in JSON)
    # called from doResponse2 if do_html_process is set
    if html.startswith("<?xml"): link_close = " /"
    else: link_close = ""
    if not "<body" in html.lower() and "<frameset" in html.lower(): return html # but allow HTML without <body if can't determine it's a frameset (TODO: what about <noframes> blocks?  although browsers that use those are unlikely to apply the kind of CSS/JS/etc things that html_additions puts in)
    bodyAppend = bodyAppend1 = ""
    bodyPrepend = options.bodyPrepend
    if not bodyPrepend: bodyPrepend = ""
    headAppend = ""
    if set_window_onerror: headAppend += r"""<script><!--
window.onerror=function(msg,url,line){alert(msg); return true}
--></script>"""
    if cssToAdd:
        # do this BEFORE options.headAppend, because someone might want to refer to it in a script in options.headAppend (although bodyPrepend is a better place to put 'change the href according to screen size' scripts, as some Webkit-based browsers don't make screen size available when processing the HEAD of the 1st document in the session)
        if options.cssName:
          if options.cssName.startswith("*"): cssName = options.cssName[1:] # omit the *
          else: cssName = options.cssName
          if slow_CSS_switch:
              # alternate, slower code involving hard HTML coding and page reload (but still requires some JS)
              bodyAppend += reloadSwitchJS("adjustCssSwitch",jsCookieString,False,cssName,cookieHostToSet,cookieExpires)
              if options.cssName.startswith("*"): useCss = not "adjustCssSwitch=0" in jsCookieString
              else: useCss = "adjustCssSwitch=1" in jsCookieString
              if useCss:
                  headAppend += '<link rel="stylesheet" type="text/css" href="%s"%s>' % (cssToAdd,link_close)
                  if attrsToAdd: html=addCssHtmlAttrs(html,attrsToAdd)
          else: # client-side only CSS switcher:
            headAppend += """<link rel="alternate stylesheet" type="text/css" id="adjustCssSwitch" title="%s" href="%s"%s>""" % (cssName,cssToAdd,link_close)
            # On some Webkit versions, MUST set disabled to true (from JS?) before setting it to false will work. And in MSIE9 it seems must do this from the BODY not the HEAD, so merge into the next script (also done the window.onload thing for MSIE; hope it doesn't interfere with any site's use of window.onload) :
            if options.cssName.startswith("*"): cond='document.cookie.indexOf("adjustCssSwitch=0")==-1'
            else: cond='document.cookie.indexOf("adjustCssSwitch=1")>-1'
            bodyPrepend += """<script><!--
if(document.getElementById) { var a=document.getElementById('adjustCssSwitch'); a.disabled=true; if(%s) {a.disabled=false;window.onload=function(e){a.disabled=true;a.disabled=false}} }
//--></script>""" % cond
            bodyAppend += r"""<script><!--
if(document.getElementById && !%s && document.readyState!='complete') document.write("%s: "+'<a href="#" onclick="document.cookie=\'adjustCssSwitch=1;domain=%s;expires=%s;path=/\';document.cookie=\'adjustCssSwitch=1;domain=.%s;expires=%s;path=/\';window.scrollTo(0,0);document.getElementById(\'adjustCssSwitch\').disabled=false;return false">On<\/a> | <a href="#" onclick="document.cookie=\'adjustCssSwitch=0;domain=%s;expires=%s;path=/\';document.cookie=\'adjustCssSwitch=0;domain=.%s;expires=%s;path=/\';window.scrollTo(0,0);document.getElementById(\'adjustCssSwitch\').disabled=true;return false">Off<\/a> ')
//--></script>""" % (detect_iframe,cssName,cookieHostToSet,cookieExpires,cookieHostToSet,cookieExpires,cookieHostToSet,cookieExpires,cookieHostToSet,cookieExpires) # (hope it helps some MSIE versions to set cookies 1st, THEN scroll, and only THEN change the document. Also using onclick= rather than javascript: URLs)
            #" # (this comment helps XEmacs21's syntax highlighting)
        else: # no cssName: stylesheet always on
          headAppend += '<link rel="stylesheet" type="text/css" href="%s"%s>' % (cssToAdd,link_close)
          if attrsToAdd and slow_CSS_switch: html=addCssHtmlAttrs(html,attrsToAdd)
    if options.htmlFilterName and options.htmlFilter:
        if '#' in options.htmlFilter: bodyAppend1 = reloadSwitchJSMultiple("adjustNoFilter",jsCookieString,True,options.htmlFilterName.split("#"),cookieHostToSet,cookieExpires) # (better put the multi-switch at the start of the options; it might be the most-used option.  Put it into bodyAppend1: we don't want the word "Off" to be misread as part of the next option string, seeing as the word before it was probably not "On", unlike normal reloadSwitchJS switches)
        else: bodyAppend += reloadSwitchJS("adjustNoFilter",jsCookieString,True,options.htmlFilterName,cookieHostToSet,cookieExpires) # (after the CSS if it's only an on/off)
    if canRender:
        # TODO: make the script below set a cookie to stop itself from being served on subsequent pages if detect_renderCheck failed? but this might be a false economy if upload bandwidth is significantly smaller than download bandwidth (and making it external could have similar issues)
        # TODO: if cookies are not supported, the script below could go into an infinite reload loop
        if options.renderCheck and not "adjustNoRender=1" in jsCookieString: bodyPrepend += r"""<script><!--
if(!%s && %s) { document.cookie='adjustNoRender=1;domain=%s;expires=%s;path=/';document.cookie='adjustNoRender=1;domain=.%s;expires=%s;path=/';location.reload(true)
}
//--></script>""" % (detect_iframe,detect_renderCheck(),cookieHostToSet,cookieExpires,cookieHostToSet,cookieExpires)
        if options.renderName:
            if options.renderCheck and "adjustNoRender=1" in jsCookieString: extraCondition="!"+detect_renderCheck() # don't want the adjustNoRender=0 (fonts ON) link visible if detect_renderCheck is true, because it won't work anyway (any attempt to use it will be reversed by the script, and if we work around that then legacy pre-renderCheck cookies could interfere; anyway, if implementing some kind of 'show the switch anyway' option, might also have to address showing it on renderOmit browsers)
            else: extraCondition=None
            bodyAppend += reloadSwitchJS("adjustNoRender",jsCookieString,True,options.renderName,cookieHostToSet,cookieExpires,extraCondition)
    if cookie_host:
        if enable_adjustDomainCookieName_URL_override: bodyAppend += r"""<script><!--
if(!%s&&document.readyState!='complete')document.write('<a href="http://%s/?%s=%s">Back to URL box<\/a>')
//--></script><noscript><a href="http://%s/?%s=%s">Back to URL box</a></noscript>""" % (detect_iframe,cookieHostToSet,adjust_domain_cookieName,adjust_domain_none,cookieHostToSet,adjust_domain_cookieName,adjust_domain_none)
        else: bodyAppend += r"""<script><!--
if(!%s&&document.readyState!='complete')document.write('<a href="javascript:document.cookie=\'%s=%s;expires=%s;path=/\';if(location.href==\'http://%s/\')location.reload(true);else location.href=\'http://%s/?nocache=\'+Math.random()">Back to URL box<\/a>')
//--></script>""" % (detect_iframe,adjust_domain_cookieName,adjust_domain_none,cookieExpires,cookieHostToSet,cookieHostToSet) # (we should KNOW if location.href is already that, and can write the conditional here not in that 'if', but they might bookmark the link or something)
    if options.headAppend: headAppend += options.headAppend
    if options.headAppendRuby: bodyPrepend += rubyScript
    if options.prominentNotice and not is_password_domain:
        # if JS is available, use fixed positioning (so it still works on sites that do that, in case we're not overriding it via user CSS) and a JS acknowledge button
        styleAttrib="style=\"width: 80% !important; margin: 10%; border: red solid !important; background: black !important; color: white !important; text-align: center !important; display: block !important; left:0px; top:0px; z-index:99999; -moz-opacity: 1 !important; filter: none !important; opacity: 1 !important; visibility: visible !important;\""
        if slow_CSS_switch: # use a slow version for this as well (TODO document that we do this?) (TODO the detect_iframe exclusion of the whole message)
            if not "_WA_warnOK=1" in jsCookieString: bodyPrepend += "<div id=_WA_warn0 "+styleAttrib+">"+options.prominentNotice+r"""<script><!--
if(document.readyState!='complete'&&document.cookie.indexOf("_WA_warnOK=1")==-1)document.write("<br><button style=\"color: black !important;background:#c0c0c0 !important;border: white solid !important\" onClick=\"document.cookie='_WA_warnOK=1;path=/';location.reload(true)\">Acknowledge<\/button>")
//--></script></div><script><!--
if(document.getElementById) document.getElementById('_WA_warn0').style.position="fixed"
}
//--></script>"""
            #" # (this comment helps XEmacs21's syntax highlighting)
        else: bodyPrepend += "<div id=_WA_warn0 "+styleAttrib+">"+options.prominentNotice+r"""</div><script><!--
if(document.getElementById) {
  var w=document.getElementById('_WA_warn0');
  if(w.innerHTML) {
  var s=w.style;
  s.position="fixed";
  var f="""+detect_iframe+r""";
  if(!f) { var c=document.cookie.split(";"); for (i=0;i<c.length;i++) if (c[i].substr(0,c[i].indexOf("=")).replace(/\s/g,"") == "_WA_warnOK") { f=1;break; } }
  if(f) document.body.removeChild(document.getElementById('_WA_warn0'));
  else w.innerHTML += "<br><button style=\"color: black !important;background:#c0c0c0 !important;border: white solid !important\" onClick=\"document.cookie='_WA_warnOK=1;path=/';document.body.removeChild(document.getElementById('_WA_warn0'))\">Acknowledge</button>";
}}
//--></script>"""
    #" # (this comment helps XEmacs21's syntax highlighting)
    # (Above code works around a bug in MSIE 9 by setting the cookie BEFORE doing the removeChild.  Otherwise the cookie does not persist.)
    if options.headAppendRuby: bodyAppend += rubyEndScript
    if headAppend:
        i=html.lower().find("</head")
        if i==-1: # no head section?
            headAppend = "<head>"+headAppend+"</head>"
            i=html.lower().find("<body")
            if i==-1: # no body section either?
                i=html.lower().find("<html")
                if i > -1: i = html.find('>',i)
                if i==-1: i=html.find('>')
                i += 1 # 0 if we're still -1, else past the '>'
        html = html[:i]+headAppend+html[i:]
    if bodyPrepend:
        i=html.lower().find("<body")
        if i==-1: i = html.lower().find("</head")
        if i==-1: i = html.lower().find("<html")
        if i>-1:
            i=html.find(">",i)
            if i>-1: html=html[:i+1]+bodyPrepend+html[i+1:]
    if bodyAppend1 and bodyAppend: bodyAppend = '<span style="float:left">' + bodyAppend1 + '</span><span style="float:left;width:1em"><br></span><span style="float: right">'+bodyAppend+'</span><span style="clear:both"></span>' # (the <br> is in case CSS is off or overrides float)
    elif bodyAppend1: bodyAppend = bodyAppend1
    if options.bodyAppend: bodyAppend = options.bodyAppend + bodyAppend
    elif bodyAppend: bodyAppend='<p>'+bodyAppend # TODO: ?
    if bodyAppend:
        i = -1
        if options.bodyAppendGoesAfter:
            it = re.finditer(options.bodyAppendGoesAfter,html)
            while True:
                try: i = it.next().end()
                except StopIteration: break
        if i==-1: i=html.lower().rfind("</body")
        if i==-1: i=html.lower().rfind("</html")
        if i==-1: i=len(html)
        html = html[:i]+bodyAppend+html[i:]
    return html

def addCssHtmlAttrs(html,attrsToAdd):
   i=html.lower().find("<body")
   if i==-1: return html # TODO: what of HTML documents that lack <body> (and frameset), do we add one somewhere? (after any /head ??)
   i += 5 # after the "<body"
   j = html.find('>', i)
   if j==-1: return html # ?!?
   attrs = html[i:j]
   for a in re.findall(r'[A-Za-z_0-9]+\=',attrsToAdd): attrs = attrs.replace(a,"old"+a) # disable corresponding existing attributes (if anyone still uses them these days)
   return html[:i] + attrs + " " + attrsToAdd + html[j:]

def ampEncode(t): return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
# (needed below because these entities will be in cleartext to the renderer; also used by serve_mailtoPage to avoid cross-site scripting)
def txt2html(t): return ampEncode(t).replace("\n","<br>")

def ampDecode(t): return t.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&")
# ampDecode is needed if passing text with entity names to Renderer below (which ampEncode's its result and we might want it to render & < > chars)
# (shouldn't need to cope with other named entities: find_text_in_HTML already processes all known ones in htmlentitydefs, and LXML also decodes all the ones it knows about)

class Renderer:
    def __init__(self):
        self.renderFont = None
        self.hanziW,self.hanziH = 0,0
    def font(self):
        if not self.renderFont: # first time
            try: import ImageFont
            except:
                try: import PIL.ImageFont as ImageFont
                except: from PIL import ImageFont
            if options.renderFont: self.renderFont = ImageFont.truetype(options.renderFont, options.renderSize, encoding="unic")
            else: self.renderFont = ImageFont.load_default()
        return self.renderFont
    def getMarkup(self,unitext):
        i=0 ; import unicodedata
        width = 0 ; imgStrStart = -1
        ret = [] ; copyFrom = 0
        if options.renderWidth==0: doImgEnd=lambda:None
        else:
          def doImgEnd():
            if imgStrStart >= 0 and width <= options.renderWidth and len(ret) > imgStrStart + 1:
                ret.insert(imgStrStart,'<nobr>')
                ret.append('</nobr>')
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
        return ('<img src="%s%s" width=%s height=%s>' % (options.renderPath,imgEncode(unitext),w,h)), w # (%s is faster than %d apparently, and format strings are faster than ''.join)
    def getImage(self,uri):
        if not options.render or not uri.startswith(options.renderPath): return False
        try: import ImageDraw,Image
        except:
            try:
                import PIL.ImageDraw as ImageDraw
                import PIL.Image as Image
            except:
                from PIL import ImageDraw,Image
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
    # This function needs to be FAST - it can be called thousands of times during a page render
    if len(unitext)==1:
        o = ord(unitext)
        if o < 0x1000:
            # TODO: create_inRenderRange_function can also re-create this function to omit the above test if we don't have any ranges under 0x1000 ?  (but it should be quite quick)
            if unitext in string.letters+string.digits+"_.-": return unitext
            elif 0xf<ord(unitext): return hex(ord(unitext))[2:]
        elif o <= 0xFFFF: # (TODO: don't need that test if true for all our render ranges)
            # TODO: make this optional?  hex(ord(u))[-4:] is nearly 5x faster than b64encode(u.encode('utf-8')) in the case of 1 BMP character (it's faster than even just the .encode('utf-8') part), but result could also decode with base64, so we have to add an extra '_' byte to disambiguate, which adds to the traffic (although only a small amount compared to IMG markup anyway)
            return '_'+hex(o)[-4:]
    return base64.b64encode(unitext.encode('utf-8'))
def imgDecode(code):
    if len(code)==1: return code
    elif len(code) <= 3: return unichr(int(code,16))
    elif code.startswith("_"): return unichr(int(code[1:],16)) # (see TODO above)
    else: return base64.b64decode(code).decode('utf-8','replace')

ipv4_regexp = re.compile(r'^([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)$')
def ipv4_to_int(ip):
    m = re.match(ipv4_regexp,ip)
    if m: return (int(m.group(1))<<24) | (int(m.group(2))<<16) | (int(m.group(3))<<8) | int(m.group(4)) # else None
def ipv4range_to_ints(ip):
    if '-' in ip: return tuple(ipv4_to_int(i) for i in ip.split('-'))
    elif '/' in ip:
        start,bits = ip.split('/')
        start = ipv4_to_int(start)
        return start, start | ~(-1 << (32-int(bits)))
    else: return ipv4_to_int(ip),ipv4_to_int(ip)
def ipv4ranges_func(ipRanges_and_results):
    isIP = True ; rangeList=None ; fList = []
    for field in ipRanges_and_results.split('|'):
        if isIP: rangeList = [ipv4range_to_ints(i) for i in field.split(',')]
        else: fList.append((rangeList,field))
        isIP = not isIP
    def f(ip):
        ipInt = ipv4_to_int(ip)
        for rl,result in fList:
            if any((l<=ipInt<=h) for l,h in rl):
                return result # else None
    return f

class Dynamic_DNS_updater:
    def __init__(self):
        self.currentIP = None
        self.forceTime=0
        self.aggressive_mode = False
        IOLoop.instance().add_callback(lambda *args:self.queryIP())
    def queryLocalIP(self):
        # Queries ip_query_url2 (if set, and if we know current IP).  Depending on the response/situation, either passes control to queryIP (which sets the next timeout itself), or sets an ip_check_interval2 timeout.
        if not ip_query_url2 or not self.currentIP:
            return self.queryIP()
        debuglog("queryLocalIP")
        def handleResponse(r):
            if r.error or not self.currentIP in r.body:
                return self.queryIP()
            # otherwise it looks like the IP is unchanged:
            self.newIP(self.currentIP) # in case forceTime is up
            IOLoop.instance().add_timeout(time.time()+options.ip_check_interval2,lambda *args:self.queryLocalIP())
        if ip_query_url2_user:
            # some routers etc insist we send the non-auth'd request first, and the credentials only when prompted (that's what Lynx does with the -auth command line), TODO do we really need to do this every 60secs? (do it only if the other way gets an error??) but low-priority as this is all local-net stuff (and probably a dedicated link to the switch at that)
            if ip_url2_pwd_is_fname: pwd=open(ip_query_url2_pwd).read().strip() # re-read each time
            else: pwd = ip_query_url2_pwd
            callback = lambda r:AsyncHTTPClient().fetch(ip_query_url2, callback=handleResponse, auth_username=ip_query_url2_user,auth_password=pwd)
        else: callback = handleResponse
        AsyncHTTPClient().fetch(ip_query_url2, callback=callback)
    def queryIP(self):
        # Queries ip_query_url, and, after receiving a response (optionally via retries if ip_query_aggressive), sets a timeout to go back to queryLocalIP after ip_check_interval (not ip_check_interval2)
        debuglog("queryIP")
        def handleResponse(r):
            if not r.error:
                self.newIP(r.body.strip())
                if self.aggressive_mode:
                    logging.info("ip_query_url got response, stopping ip_query_aggressive")
                    self.aggressive_mode = False
            elif options.ip_query_aggressive:
                if not self.aggressive_mode:
                    logging.info("ip_query_url got error, starting ip_query_aggressive")
                    self.aggressive_mode = True
                return self.queryIP()
            IOLoop.instance().add_timeout(time.time()+options.ip_check_interval,lambda *args:self.queryLocalIP())
        AsyncHTTPClient().fetch(options.ip_query_url, callback=handleResponse)
    def newIP(self,ip):
        debuglog("newIP "+ip)
        if ip==self.currentIP and (not options.ip_force_interval or time.time()<self.forceTime): return
        try: socket.inet_aton(ip) # IPv4 only
        except socket.error: # try IPv6
            try: socket.inet_pton(socket.AF_INET6,ip)
            except socket.error: return # illegal IP, maybe a temporary error from the server
        self.currentIP = ip
        cmd = options.ip_change_command+" "+ip
        if len(options.ip_change_command) < 50: logging.info("ip_change_command: "+cmd)
        else: logging.info("Running ip_change_command for "+ip)
        backgrounded_system(cmd)
        self.forceTime=time.time()+options.ip_force_interval

def backgrounded_system(cmd):
    def run(cmd):
        global helper_thread_count
        helper_thread_count += 1
        os.system(cmd)
        helper_thread_count -= 1
    threading.Thread(target=run,args=(cmd,)).start()

class WatchdogPings:
    def __init__(self,wFile):
        self.wFile = wFile
        if options.watchdogWait:
            import thread
            thread.start_new_thread((lambda *args:self.separate_thread()),())
        self.ping()
    def separate_thread(self): # version for watchdogWait
        # (does not adjust helper_thread_count / can't be "runaway")
        global watchdog_mainServerResponded # a flag.  Do NOT timestamp with time.time() - it can go wrong if NTP comes along and re-syncs the clock by a large amount
        def respond(*args):
            global watchdog_mainServerResponded
            watchdog_mainServerResponded = True
        respond() ; stopped = 0 ; sleptSinceResponse = 0
        while options.watchdog:
            if watchdog_mainServerResponded:
                self.ping()
                if stopped:
                    logging.info("Main thread responded, restarting watchdog ping")
                    stopped = 0
                watchdog_mainServerResponded = False
                sleptSinceResponse = 0
                IOLoop.instance().add_callback(respond)
            elif sleptSinceResponse < options.watchdogWait: self.ping() # keep waiting for it
            elif not stopped:
                logging.info("Main thread unresponsive, stopping watchdog ping. lastDebugMsg: "+lastDebugMsg)
                stopped = 1 # but don't give up (it might respond just in time)
            time.sleep(options.watchdog)
            sleptSinceResponse += options.watchdog # "dead reckoning" to avoid time.time()
    def ping(self):
        if not options.watchdogWait: debuglog("pinging watchdog",logRepeats=False) # ONLY if run from MAIN thread, otherwise it might overwrite the real lastDebugMsg of where we were stuck
        self.wFile.write('a') ; self.wFile.flush()
        if not options.watchdogWait: # run from main thread
            IOLoop.instance().add_timeout(time.time()+options.watchdog,lambda *args:self.ping())
        # else one ping only (see separate_thread)

fasterServer_up = False
def FSU_set(new_FSU,interval):
    # sets new fasterServer_up state, and returns interval to next check
    global fasterServer_up
    fsu_old = fasterServer_up
    fasterServer_up = new_FSU
    if not fasterServer_up == fsu_old:
        if fasterServer_up: logging.info("fasterServer %s came up - forwarding traffic to it" % options.fasterServer)
        else: logging.info("fasterServer %s went down - handling traffic ourselves" % options.fasterServer)
    # debuglog("fasterServer_up="+repr(fasterServer_up)+" (err="+repr(r.error)+")",logRepeats=False)
    if fasterServer_up: return 1 # TODO: configurable? fallback if timeout when we try to connect to it as well?
    elif interval < 60: interval *= 2 # TODO: configurable?
    return interval
class checkServer:
    def __init__(self):
        self.client = self.pendingClient = None
        self.count = 0
        self.interval=1
    def __call__(self):
     if options.fasterServerNew:
         # TODO: might be bytes in the queue if this server somehow gets held up.  Could try read_until_close(close,stream)
         if (self.client and self.count >= 2) or self.pendingClient: # it didn't call serverOK on 2 consecutive seconds (TODO: customizable?), or didn't connect within 1sec - give up
             try: self.pendingClient.close()
             except: pass
             try: self.client.close()
             except: pass
             self.pendingClient = self.client = None
             self.interval = FSU_set(False,self.interval)
             return IOLoop.instance().add_timeout(time.time()+self.interval,lambda *args:checkServer())
         elif self.client: self.count += 1
         else: # create new self.pendingClient
             server,port = options.fasterServer.rsplit(':',1)
             self.pendingClient = tornado.iostream.IOStream(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0))
             def send_request(*args):
                 try:
                     self.pendingClient.write('GET /ping2 HTTP/1.0\r\nUser-Agent: ping\r\n\r\n')
                     self.client = self.pendingClient
                     self.pendingClient = None
                     self.client.read_until_close(lambda *args:True,lambda *args:self.serverOK())
                 except: pass
             self.pendingClient.connect((server,int(port)),send_request)
         IOLoop.instance().add_timeout(time.time()+1,lambda *args:checkServer()) # check back in 1sec to see if it connected OK (should do if it's local)
     else: # old version - issue HTTP requests to /ping
        def callback(r):
            self.interval = FSU_set(not r.error,self.interval)
            if not fasterServer_up: self.client = None
            IOLoop.instance().add_timeout(time.time()+self.interval,lambda *args:checkServer())
        if not self.client: self.client=AsyncHTTPClient()
        self.client.fetch("http://"+options.fasterServer+"/ping",connect_timeout=1,request_timeout=1,user_agent="ping",callback=callback,use_gzip=False)
    def serverOK(self):
        # called when any chunk is available from the stream (normally once a second, but might catch up a few bytes if we've delayed for some reason)
        self.interval = FSU_set(True,0)
        self.count = 0
checkServer=checkServer()

lastDebugMsg = "None" # for 'stopping watchdog ping'
def debuglog(msg,logRepeats=True):
    global lastDebugMsg
    if logRepeats or not msg==lastDebugMsg:
        if not options.logDebug: logging.debug(msg)
        elif options.background: logging.info(msg)
        else: sys.stderr.write(time.strftime("%X ")+msg+"\n")
    lastDebugMsg = msg

if __name__ == "__main__": main()
