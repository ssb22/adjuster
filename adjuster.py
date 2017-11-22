#!/usr/bin/env python

program_name = "Web Adjuster v0.262 (c) 2012-17 Silas S. Brown"

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
# although some early ones are missing.

import sys,os
twoline_program_name = program_name+"\nLicensed under the Apache License, Version 2.0"

if '--version' in sys.argv:
    print twoline_program_name ; raise SystemExit # no imports needed
elif '--html-options' in sys.argv: # for updating the website (this option is not included in the help text)
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
    try: from tornado.httpserver import HTTPServer
    except: HTTPServer = None # may happen in WSGI mode (e.g. AppEngine can have trouble importing this)
    from tornado.ioloop import IOLoop
    from tornado.web import Application, RequestHandler, StaticFileHandler, asynchronous
    import tornado.options, tornado.iostream
    from tornado.options import define,options
    def heading(h): pass
    if 'port' in options:
        # we may be being imported by an extension, and some Tornado versions don't compile if 'define' is run twice
        def define(*args,**kwargs): pass
getfqdn_default = "is the machine's domain name" # default is ... (avoid calling getfqdn unnecessarily, as the server might be offline/experimental and we don't want to block on an nslookup with every adjuster start)

heading("General options")
define("config",help="Name of the configuration file to read, if any. The process's working directory will be set to that of the configuration file so that relative pathnames can be used inside it. Any option that would otherwise have to be set on the command line may be placed in this file as an option=\"value\" or option='value' line (without any double-hyphen prefix). Multi-line values are possible if you quote them in \"\"\"...\"\"\", and you can use standard \\ escapes. You can also set config= in the configuration file itself to import another configuration file (for example if you have per-machine settings and global settings). If you want there to be a default configuration file without having to set it on the command line every time, an alternative option is to set the ADJUSTER_CFG environment variable.")
define("version",help="Just print program version and exit")

heading("Network listening and security settings")
define("port",default=28080,help="The port to listen on. Setting this to 80 will make it the main Web server on the machine (which will likely require root access on Unix); setting it to 0 disables request-processing entirely (if you want to use only the Dynamic DNS and watchdog options). For --real_proxy and related options, additional unused ports are needed immediately above this number: they listen only on localhost and are used for SSL helpers etc.") # when not in WSGI mode ('CONNECT' is not supported in WSGI mode, neither is js_reproxy).  If running on Openshift in non-WSGI mode, you'd better not use real_proxy or js_reproxy because Openshift won't let you open ports other than OPENSHIFT_PYTHON_PORT (TODO: find some way to multiplex everything on one port? how to authenticate our JS-interpreter connections if the load-balancer makes remote connections to that port also seem to come from our IP?)
define("publicPort",default=0,help="The port to advertise in URLs etc, if different from 'port' (the default of 0 means no difference). Used for example if a firewall prevents direct access to our port but some other server has been configured to forward incoming connections.")
define("user",help="The user name to run as, instead of root. This is for Unix machines where port is less than 1024 (e.g. port=80) - you can run as root to open the privileged port, and then drop privileges. Not needed if you are running as an ordinary user.")
define("address",default="",help="The address to listen on. If unset, will listen on all IP addresses of the machine. You could for example set this to localhost if you want only connections from the local machine to be received, which might be useful in conjunction with --real_proxy.")
define("password",help="The password. If this is set, nobody can connect without specifying ?p= followed by this password. It will then be sent to them as a cookie so they don't have to enter it every time. Notes: (1) If wildcard_dns is False and you have multiple domains in host_suffix, then the password cookie will have to be set on a per-domain basis. (2) On a shared server you probably don't want to specify this on the command line where it can be seen by process-viewing tools; use a configuration file instead.")
define("password_domain",help="The domain entry in host_suffix to which the password applies. For use when wildcard_dns is False and you have several domains in host_suffix, and only one of them (perhaps the one with an empty default_site) is to be password-protected, with the others public. If this option is used then prominentNotice (if set) will not apply to the passworded domain. You may put the password on two or more domains by separating them with slash (/).") # prominentNotice not apply: on the assumption that those who know the password understand what the tool is.  DOES apply anyway if =="htmlFilter".
define("auth_error",default="Authentication error",help="What to say when password protection is in use and a correct password has not been entered. HTML markup is allowed in this message. As a special case, if this begins with http:// or https:// then it is assumed to be the address of a Web site to which the browser should be redirected; if it is set to http:// and nothing else, the request will be passed to the server specified by own_server (if set). If the markup begins with a * when this is ignored and the page is returned with code 200 (OK) instead of 401 (authorisation required).") # TODO: basic password form? or would that encourage guessing
define("open_proxy",default=False,help="Whether or not to allow running with no password. Off by default as a safeguard against accidentally starting an open proxy.")
define("prohibit",multiple=True,default="wiki.*action=edit",help="Comma-separated list of regular expressions specifying URLs that are not allowed to be fetched unless --real_proxy is in effect. Browsers requesting a URL that contains any of these will be redirected to the original site. Use for example if you want people to go direct when posting their own content to a particular site (this is of only limited use if your server also offers access to any other site on the Web, but it might be useful when that's not the case). Include ^https in the list to prevent Web Adjuster from fetching HTTPS pages for adjustment and return over normal HTTP. This access is enabled by default now that many sites use HTTPS for public pages that don't really need to be secure, just to get better placement on some search engines, but if sending confidential information to the site then beware you are trusting the Web Adjuster machine and your connection to it, plus its certificate verification might not be as thorough as your browser's.")
define("real_proxy",default=False,help="Whether or not to accept requests with original domains like a \"real\" HTTP proxy.  Warning: this bypasses the password and implies open_proxy.  Off by default.")
define("via",default=True,help="Whether or not to update the Via: and X-Forwarded-For: HTTP headers when forwarding requests") # (Via is "must" in RFC 2616)
define("uavia",default=True,help="Whether or not to add to the User-Agent HTTP header when forwarding requests, as a courtesy to site administrators who wonder what's happening in their logs (and don't log Via: etc)")
define("robots",default=False,help="Whether or not to pass on requests for /robots.txt.  If this is False then all robots will be asked not to crawl the site; if True then the original site's robots settings will be mirrored.  The default of False is recommended.") # TODO: do something about badly-behaved robots ignoring robots.txt? (they're usually operated by email harvesters etc, and start crawling the web via the proxy if anyone "deep links" to a page through it, see comments in request_no_external_referer)

define("upstream_proxy",help="address:port of a proxy to send our requests through. This can be used to adapt existing proxy-only mediators to domain rewriting, or for a caching proxy. Not used for ip_query_url options, own_server or fasterServer. If address is left blank (just :port) then localhost is assumed and https URLs will be rewritten into http with altered domains; you'll then need to set the upstream proxy to send its requests back through the adjuster (which will listen on localhost:port+1 for this purpose) to undo that rewrite. This can be used to make an existing HTTP-only proxy process HTTPS pages.") # The upstream_proxy option requires pycurl (will refuse to start if not present). Does not set X-Real-Ip because Via should be enough for upstream proxies. The ":port"-only option rewrites URLs in requests but NOT ones referred to in documents: we assume the proxy can cope with that.

define("ip_messages",help="Messages or blocks for specific IP address ranges (IPv4 only).  Format is ranges|message|ranges|message etc, where ranges are separated by commas; can be individual IPs, or ranges in either 'network/mask' or 'min-max' format; the first matching range-set is selected.  If a message starts with * then its ranges are blocked completely (rest of message, if any, is sent as the only reply to any request), otherwise message is shown on a 'click-through' page (requires Javascript and cookies).  If the message starts with a hyphen (-) then it is considered a minor edit of earlier messages and is not shown to people who selected `do not show again' even if they did this on a different version of the message.  Messages may include HTML.")

heading("DNS and website settings")
define("host_suffix",default=getfqdn_default,help="The last part of the domain name. For example, if the user wishes to change www.example.com and should do so by visiting www.example.com.adjuster.example.org, then host_suffix is adjuster.example.org. If you do not have a wildcard domain then you can still adjust one site by setting wildcard_dns to False, host_suffix to your non-wildcard domain, and default_site to the site you wish to adjust. If you have more than one non-wildcard domain, you can set wildcard_dns to False, host_suffix to all your domains separated by slash (/), and default_site to the sites these correspond to, again separated by slash (/); if two or more domains share the same default_site then the first is preferred in links and the others are assumed to be for backward compatibility. If wildcard_dns is False and default_site is empty (or if it's a /-separated list and one of its items is empty), then the corresponding host_suffix gives a URL box and sets its domain in a cookie (and adds a link at the bottom of pages to clear this and return to the URL box), but this should be done only as a last resort: you can browse only one domain at a time at that host_suffix; most links and HTTP redirects to other domains will leave the adjuster when not in HTML-only mode, which can negatively affect sites that use auxiliary domains for scripts etc and check Referer (unless you ensure these auxiliary domains are listed elsewhere in default_site). Also, the sites you visit at that host_suffix might be able to see some of each other's cookies etc (leaking privacy) although the URL box page will try to clear site cookies.")
# ("preferred" / "backward compatibility" thing: can be useful if old domain has become unreliable, or if "preferred" domain is actually a URL-path-forwarding service with a memorable name which redirects browsers to an actual domain that's less memorable, and you want the memorable domain to be used in links etc, although in this case you might still get the less-memorable domain in the address bar)
# TODO: (two or more domains pointing to the same default_site) "preferred" / "backward compatibility" thing above: or, add an option to periodically check which of our domains are actually 'up' and move them to the front of the host_suffix / default_site list; that way we don't have to guess ahead of time which one is more reliable and should be preferred.
# Could also do 'use the currently-requested host if it's appropriate', but what if there's a *set* of sites we adjust and we need to try to rewrite cross-site links to be in the same set of domains as the one the browser is requesting - maybe it's best to leave the "preferred" DNS to the config or the periodic check.
# TODO at lower priority: empty (item in) host_suffix to match ALL (unknown) hosts, including IP hosts and no Host: header.  Fetch the corresponding default_site (empty means use cookies), and adjust it USING THE HOST SPECIFIED BY THE BROWSER to rewrite the links.  This could be useful if setting up an adjuster with NO domain name (IP only).  Could periodically upload our public IP to a separate static website via FTP/SSH/etc in case dynamic DNS is not reliable.  But if IP address has to change then all cookies would be 'lost'.  Also, if no password is set then IP-based "webserver probes" could cause us to send malicious-looking traffic to default_site.
# TODO: Could do different hosts on different ports, which might also be useful if you have a domain name but only one.  Would have to check for cookie sharing (or just say "do this only if you don't mind it"); fasterServer would have to forward to same as incoming port.  Might be a problem if some users' firewalls disallow outgoing Web traffic to non-standard ports.
# (In the current code, setting host_suffix to a public IP address should work: most browsers set Host: to the IP if requesting a URL by IP, and then the IP will be used in rewrites if it's the first thing specified for its corresponding default_site.  But adjuster will need to be reconfigured and restarted on every change of the public IP.)
define("default_site",help="The site to fetch from if nothing is specified before host_suffix, e.g. example.org (add .0 at the end to specify an HTTPS connection, but see the 'prohibit' option). If default_site is omitted then the user is given a URL box when no site is specified; if it is 'error' then an error is shown in place of the URL box (the text of the error depends on the settings of wildcard_dns and real_proxy).") # using .0 here rather than https:// prefix because / is a separator: see the host_suffix help text (TODO: change the separator? but don't break existing installations)
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
define('search_sites',multiple=True,help="Comma-separated list of search sites to be made available when the URL box is displayed (if default_site is empty). Each item in the list should be a URL (which will be prepended to the search query), then a space, then a short description of the site. The first item on the list is used by default; the user can specify other items by making the first word of their query equal to the first word of the short description. Additionally, if some of the letters of that first word are in parentheses, the user may specify just those letters. So for example if you have an entry http://search.example.com/?q= (e)xample, and the user types 'example test' or 'e test', it will use http://search.example.com/?q=test")
define("urlbox_extra_html",help="Any extra HTML you want to place after the URL box (when shown), such as a paragraph explaining what your filters do etc.")
define("wildcard_dns",default=True,help="Set this to False if you do NOT have a wildcard domain and want to process only default_site. Setting this to False does not actually prevent other sites from being processed (for example, a user could override their local DNS resolver to make up for your lack of wildcard domain); if you want to really prevent other sites from being processed then you could also set own_server to deal with unrecognised domains. Setting wildcard_dns to False does stop the automatic re-writing of links to sites other than default_site. Leave it set to True to have ALL sites' links rewritten on the assumption that you have a wildcard domain.") # will then say "(default True)"

heading("General adjustment options")
define("default_cookies",help="Semicolon-separated list of name=value cookies to send to all remote sites, for example to set preferences. Any cookies that the browser itself sends will take priority over cookies in this list. Note that these cookies are sent to ALL sites. You can set a cookie only on a specific browser by putting (browser-string) before the cookie name, e.g. (iPad)x=y will set x=y only if 'iPad' occurs in the browser string (to match more than one browser-string keyword, you have to specify the cookie multiple times).") # TODO: site-specific option
# TODO: sets of adjustments can be switched on and off at a /__settings URL ?  or leave it to the injected JS
define("headAppend",help="Code to append to the HEAD section of every HTML document that has a BODY. Use for example to add your own stylesheet links and scripts. Not added to documents that lack a BODY such as framesets.")
define("headAppendCSS",help="URL of a stylesheet for headAppend.  This option automatically generates the LINK REL=... markup for it, and also tries to delete the string '!important' from other stylesheets, to emulate setting this stylesheet as a user CSS.  You can also include one or more 'fields' in the URL, by marking them with %s and following the URL with options e.g. http://example.org/style%s-%s.css;1,2,3;A,B will allow combinations like style1-A.css or style3-B.css; in this case appropriate selectors are provided with the URL box (values may optionally be followed by = and a description), and any visitors who have not set their options will be redirected to the URL box to do so.")
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
define("prominentNotice",help="Text to add as a prominent notice to processed sites (may include HTML). If the browser has sufficient Javascript support, this will float relative to the browser window and will contain an 'acknowledge' button to hide it (for the current site in the current browsing session). Use prominentNotice if you need to add important information about how the page has been modified. If you set prominentNotice to the special value \"htmlFilter\", then the output of the htmlFilter option (if any) will be placed as a prominent notice; this can be used if you want to provide extra information or links derived from the content of the page. Note: if you include Javascript document.write() code in prominentNotice, check that document.readyState is not 'complete' or you might find the document is erased on some website/browser combinations when a site script somehow causes your script to be re-run after the document stream is closed. In some rare cases you might also need to verify that document.cookie does not contain _WA_warnOK=1") # e.g. if the site does funny things with the browser cache.  Rewriting the innerHTML manipulation to appendChild doesn't fix the need to check document.readyState
define("staticDocs",help="url#path of static documents to add to every website, e.g. /_myStatic/#/var/www (make sure the first part is something not likely to be used by the websites you visit). This can be used to supply extra Javascript (e.g. for bodyPrepend to load) if it needs to be served from the same domain. Note: staticDocs currently overrides the password and own_server options.")
define("delete",multiple=True,help="Comma-separated list of regular expressions to delete from HTML documents. Can be used to delete selected items of Javascript and other code if it is causing trouble for your browser. Will also delete from the text of pages; use with caution.")
define("delete_css",multiple=True,help="Comma-separated list of regular expressions to delete from CSS documents (but not inline CSS in HTML); can be used to remove, for example, dimension limits that conflict with annotations you add, as an alternative to inserting CSS overrides.  In rare cases you might want to replace the deleted regexp with another, in which case you can use @@ to separate the two, and a second @@ can be used to specify a string in the CSS URL that must be present for the operation to take effect (this could be combined with a codeChanges to add query parameters to the URL if you want the change to occur only when the CSS is loaded from specific HTML pages).")
define("delete_doctype",default=False,help="Delete the DOCTYPE declarations from HTML pages. This option is needed to get some old Webkit browsers to apply multiple CSS files consistently.")
define("deleteOmit",multiple=True,default="iPhone,iPad,Android,Macintosh",help="A list of browsers that do not need the delete and delete-doctype options to be applied. If any of these strings occur in the user-agent then these options are disabled for that request, on the assumption that these browsers are capable enough to cope with the \"problem\" code. Any delete-css option is still applied however.")
define("codeChanges",help="Several lines of text specifying changes that are to be made to all HTML and Javascript code files on certain sites; use as a last resort for fixing a site's scripts. This option is best set in the configuration file and surrounded by r\"\"\"...\"\"\". The first line is a URL prefix (just \"http\" matches all); append a # to match an exact URL instead of a prefix, and #+number (e.g. #1 or #2) to match an exact URL and perform the change only that number of times in the page.  The second line is a string of code to search for, and the third is a string to replace it with. Further groups of URL/search/replace lines may follow; blank lines and lines starting with # are ignored. If the 'URL prefix' starts with a * then it is instead a string to search for within the code of the document body; any documents containing this code will match; thus it's possible to write rules of the form 'if the code contains A, then replace B with C'. This processing takes place before any 'delete' option takes effect so it's possible to pick up on things that will be deleted, and it occurs after the domain rewriting so it's possible to change rewritten domains in the search/replace strings (but the URL prefix above should use the non-adjusted version).")
define("boxPrompt",default="Website to adjust",help="What to say before the URL box (when shown); may include HTML; for example if you've configured Web Adjuster to perform a single specialist change that can be described more precisely with some word other than 'adjust', you might want to set this.")
define("viewsource",default=False,help="Provide a \"view source\" option. If set, you can see a page's pre-adjustment source code, plus client and server headers, by adding \".viewsource\" to the end of a URL (after any query parameters etc)")
define("htmlonly_mode",default=True,help="Provide a checkbox allowing the user to see pages in \"HTML-only mode\", stripping out images, scripts and CSS; this might be a useful fallback for very slow connections if a site's pages bring in many external files and the browser cannot pipeline its requests. The checkbox is displayed by the URL box, not at the bottom of every page.") # if no pipeline, a slow UPLINK can be a problem, especially if many cookies have to be sent with each request for a js/css/gif/etc.
# (and if wildcard_dns=False and we're domain multiplexing, our domain can accumulate a lot of cookies, causing requests to take more uplink bandwidth, TODO: do something about this?)
define("htmlonly_css",default=False,help="Leave images and CSS in the page when in \"HTML-only mode\", removing only scripts")
define("mailtoPath",default="/@mail@to@__",help="A location on every adjusted website to put a special redirection page to handle mailto: links, showing the user the contents of the link first (in case a mail client is not set up). This must be made up of URL-safe characters starting with a / and should be a path that is unlikely to occur on normal websites and that does not conflict with renderPath. If this option is empty, mailto: links are not changed. (Currently, only plain HTML mailto: links are changed by this function; Javascript-computed ones are not.)")
define("mailtoSMS",multiple=True,default="Opera Mini,Opera Mobi,Android,Phone,Mobile",help="When using mailtoPath, you can set a comma-separated list of platforms that understand sms: links. If any of these strings occur in the user-agent then an SMS link will be provided on the mailto redirection page, to place the suggested subject and/or body into a draft SMS message instead of an email.")

heading("External processing options")
define("htmlFilter",help="External program(s) to run to filter every HTML document. If more than one program is specified separated by # then the user will be given a choice (see htmlFilterName option). Any shell command can be used; its standard input will get the HTML (or the plain text if htmlText is set), and it should send the new version to standard output. Multiple copies of each program might be run at the same time to serve concurrent requests. UTF-8 character encoding is used. If you are not able to run external programs then you could use a back-end server (specify an http:// or https:// URL and input is POSTed in the request body; if this back-end server is another Web Adjuster with submitPath and submitBookmarklet set then give its submitPath plus uA for its 1st filter, uB for its 2nd, etc), or use a Python function: specify * followed by the function name, and inject the function into the adjuster module from a wrapper script (which imports adjuster, sets adjuster.options.htmlFilter etc, injects the function and calls adjuster.main). The function is run in the serving thread.") # (so try to make it fast, although this is not quite so essential in WSGI mode; if you're in WSGI mode then I suggest getting the function to import any large required modules on-demand)
define("htmlFilterName",help="A name for the task performed by htmlFilter. If this is set, the user will be able to switch it on and off from the browser via a cookie and some Javascript links at the bottom of HTML pages. If htmlFilter lists two or more options, htmlFilterName should list the same number plus one (again separated by #); the first is the name of the entire category (for example \"filters\"), and the user can choose between any one of them or none at all (hence the number of options is one more than the number of filters); if this yields more than 3 options then all but the first two are hidden behind a \"More\" option on some browsers.") # TODO: non-Javascript fallback for the switcher
define("htmlJson",default=False,help="Try to detect HTML strings in JSON responses and feed them to htmlFilter. This can help when using htmlFilter with some AJAX-driven sites. IMPORTANT: Unless you also set the 'separator' option, the external program must preserve all newline characters, because multiple HTML strings in the same JSON response will be given to it separated by newlines, and the newlines of the output determine which fragment to put back where. (If you combine htmlJson with htmlText, the external program will see text in HTML in JSON as well as text in HTML, but it won't see text in HTML in JSON in HTML.)")
define("htmlText",default=False,help="Causes the HTML to be parsed, and only the text parts (not the markup) will be sent to htmlFilter. Useful to save doing HTML parsing in the external program. The external program is still allowed to include HTML markup in its output. IMPORTANT: Unless you also set the 'separator' option, the external program must preserve all newline characters, because multiple text strings will be given to it separated by newlines, and the newlines of the output determine which modified string to put back where.")
define("separator",help="If you are using htmlFilter with htmlJson and/or htmlText, you can set separator to any text string to be used as a separator between multiple items of data when passing them to the external program. By default, newlines are used for this, but you can set it to any other character or sequence of characters that cannot be added or removed by the program. (It does not matter if a website's text happens to use the separator characters.) If separator is set, not only will it be used as a separator BETWEEN items of data but also it will be added before the first and after the last item, thus allowing you to use an external program that outputs extra text before the first and after the last item. The extra text will be discarded. If however you do not set separator then the external program should not add anything extra before/after the document.")
define("leaveTags",multiple=True,default="script,style,title,textarea,option",help="When using htmlFilter with htmlText, you can set a comma-separated list of HTML tag names whose enclosed text should NOT be sent to the external program for modification. For this to work, the website must properly close these tags and must not nest them. (This list is also used for character-set rendering.)") # not including 'option' can break pages that need character-set rendering
define("stripTags",multiple=True,default="wbr",help="When using htmlFilter with htmlText, you can set a comma-separated list of HTML tag names which should be deleted if they occur in any section of running text. For example, \"wbr\" (word-break opportunity) tags (listed by default) might cause problems with phrase-based annotators.") # TODO: <span class="whatever">&nbsp;</span> (c.f. annogen's JS) ?  have already added to the bookmarklet JS (undocumented! see 'awkwardSpan') but not to the proxy version (the two find_text_in_HTML functions)

define("submitPath",help="If set, accessing this path (on any domain) will give a form allowing the user to enter their own text for processing with htmlFilter. The path should be one that websites are not likely to use (even as a prefix), and must begin with a slash (/). If you prefix this with a * then the * is ignored and any password set in the 'password' option does not apply to submitPath. Details of the text entered on this form is not logged by Web Adjuster, but short texts are converted to compressed GET requests which might be logged by proxies etc.") # (see comments in serve_submitPage; "with htmlFilter" TODO: do we add "(or --render)" to this? but charset submit not entirely tested with all old browsers; TODO: consider use of chardet.detect(buf) in python-chardet)
define("submitPrompt",default="Type or paste in some text to adjust",help="What to say before the form allowing users to enter their own text when submitPath is set (compare boxPrompt)")
define("submitBookmarklet",default=True,help="If submitPath and htmlFilter is set, and if browser Javascript support seems sufficient, then add one or more 'bookmarklets' to the 'Upload Text' page (named after htmlFilterName if provided), allowing the user to quickly upload text from other sites. This might be useful if for some reason those sites cannot be made to go through Web Adjuster directly. The bookmarklets should work on modern desktop browsers and on iOS and Android; they should cope with frames and with Javascript-driven changes to a page, and on some browsers an option is provided to additionally place the page into a frameset so that links to other pages on the same site can be followed without explicitly reactivating the bookmarklet (but this does have disadvantages - page must be reloaded + URL display gets 'stuck' - so it's left to the user to choose).") # (and if the other pages check their top.location, things could break there as well)
define("submitBookmarkletFilterJS",default=r"!c.nodeValue.match(/^[ -~\s]*$/)",help="A Javascript expression that evaluates true if a DOM text node 'c' should be processed by the 'bookmarklet' Javascript when submitPath and submitBookmarklet are set. To process ALL text, set this option to c.nodeValue.length, but if your htmlFilter will not change certain kinds of text then you can make the Javascript run more efficiently by not processing these (quote the expression carefully). The default setting will not process text that is all ASCII.") # + whitespace.  TODO: add non-ascii 'smart punctuation'? entered as Unicode escapes, or rely on serving the script as utf-8. (Previously said "To process ALL text, simply set this option to 'true'", but that can have odd effects on some sites' empty nodes. Saying c.nodeValue.length for now; c.nodeValue.match(/[^\s]/) might be better but needs more quoting explanation. Could change bookmarkletMainScript so it alters the DOM only if replacements[i] != oldTexts[i], c.f. annogen's android code, but that would mean future passes would re-send all the unchanged nodes cluttering the XMLHttpRequests especially if they fill a chunk - annogen version has the advantage of immediate local processing)
define("submitBookmarkletChunkSize",default=1024,help="Specifies the approximate number of characters at a time that the 'bookmarklet' Javascript will send to the server if submitPath and submitBookmarklet are set. Setting this too high could impair browser responsiveness, but too low will be inefficient with bandwidth and pages will take longer to finish.")
define("submitBookmarkletDomain",help="If set, specifies a domain to which the 'bookmarklet' Javascript should send its XMLHttpRequests, and ensures that they are sent over HTTPS if the 'bookmarklet' is activated from an HTTPS page (this is needed by some browsers to prevent blocking the XMLHttpRequest).  submitBookmarkletDomain should be a domain for which the adjuster can receive requests on both HTTP and HTTPS, and which has a correctly-configured HTTPS front-end with valid certificate.") # e.g. example.rhcloud.com (although that does introduce the disadvantage of tying bookmarklet installations to the current URLs of the OpenShift service rather than your own domain)

heading("Javascript execution options")
define("js_interpreter",default="",help="Execute Javascript on the server for users who choose \"HTML-only mode\". You can set js_interpreter to PhantomJS, HeadlessChrome or HeadlessFirefox, and must have the appropriate one installed along with Selenium (and ChromeDriver if you're using HeadlessChrome, and the exact right version of Selenium etc if you're using HeadlessFirefox, which is notorious for breaking at the slightest version mismatch).  If you have multiple users, beware logins etc may be shared!  Only the remote site's script is executed: scripts in --headAppend etc are still sent to the client.   If a URL box cannot be displayed (no wildcard_dns and default_site is full, or processing a \"real\" proxy request) then htmlonly_mode auto-activates when js_interpreter is set, thus providing a way to partially Javascript-enable browsers like Lynx.  If --viewsource is enabled then js_interpreter URLs may also be followed by .screenshot")
define("js_instances",default=1,help="The number of virtual browsers to load when js_interpreter is in use. Increasing it will take more RAM but may aid responsiveness if you're loading multiple sites at once.")
define("js_429",default=True,help="Return HTTP error 429 (too many requests) if js_interpreter queue is too long") # RFC 6585, April 2012 ('too long' = 'longer than 2*js_instances', but in the case of --js_reproxy this is inspected before the prefetch: once we decide to prefetch a page, we'll queue it no matter what (unless the client goes away or the prefetch fails), so the queue can get longer than 2*js_instances if more items are in prefetch)
define("js_restartAfter",default=10,help="When js_interpreter is in use, restart each virtual browser after it has been used this many times (0=unlimited); might help work around excessive RAM usage in PhantomJS v2.1.1. If you have many --js-instances (and hardware to match) you could also try --js-restartAfter=1 (restart after every request) to work around runaway or unresponsive js_interpreter processes.") # (although that would preclude a faster response when a js_interpreter instance is already loaded with the page requested, although TODO faster response is checked for only AFTER selecting an instance and is therefore less likely to work with multiple instances under load); RAM usage is a regression from 2.0.1 ?
define("js_restartMins",default=10,help="Restart an idle js_interpreter instance after about this number of minutes (0=unlimited); use this to stop the last-loaded page from consuming CPU etc indefinitely if no more requests arrive at that instance.  Not applicable when --js-restartAfter=1.") # Setting it low does have the disadvantage of not being able to use an already-loaded page, see above
define("js_retry",default=True,help="If a js_interpreter fails, restart it and try the same fetch again while the remote client is still waiting")
define("js_fallback",default=True,help="If a js_interpreter fails (even after js_retry if set), serve the page without Javascript processing instead of serving an error")
define("js_reproxy",default=True,help="When js_interpreter is in use, have it send its upstream requests back through the adjuster on a different port. This allows js_interpreter to be used for POST forms, fixes its Referer headers when not using real_proxy, monitors AJAX for early completion, prevents problems with file downloads, and prefetches main pages to avoid holding up a js_interpreter instance if the remote server is down.") # and works around issue #13114 in PhantomJS 2.x.  Only real reason to turn it off is if we're running in WSGI mode (which isn't recommended with js_interpreter) as we haven't yet implemented 'find spare port and run separate IO loop behind the WSGI process' logic
define("js_UA",help="Custom user-agent string for js_interpreter requests, if for some reason you don't want to use the JS browser's default. If you prefix this with a * then the * is ignored and the user-agent string is set by the upstream proxy (--js_reproxy) so scripts running in the JS browser itself will see its original user-agent.")
define("js_images",default=True,help="When js_interpreter is in use, instruct it to fetch images just for the benefit of Javascript execution. Setting this to False saves bandwidth but misses out image onload events.") # plus some versions of Webkit leak memory (PhantomJS issue 12903), TODO: return a fake image if js_reproxy? (will need to send a HEAD request first to verify it is indeed an image, as PhantomJS's Accept header is probably */*) but height/width will be wrong
define("js_size",default="1024x768",help="The virtual screen dimensions of the browser when js_interpreter is in use (changing it might be useful for screenshots)")
define("js_links",default=True,help="When js_interpreter is in use, handle some Javascript links via special suffixes on href URLs. Turn this off if you don't mind such links not working and you want to ensure URLs are unchanged modulo domain-rewriting.")
define("js_multiprocess",default=True,help="When js_interpreter is in use, handle the webdriver instances in completely separate processes (not just separate threads) when the multiprocessing module is available. This might be more robust.")
define("ssl_fork",default=False,help="Run SSL-helper proxies as separate processes (Unix only) to stop the main event loop from being stalled by buggy SSL libraries. This costs RAM, but adding --multicore too will limit the number of helpers to one per core instead of one per port, so --ssl-fork --multicore is recommended if you want more js_interpreter instances than cores.")

heading("Server control options")
define("background",default=False,help="If True, fork to the background as soon as the server has started (Unix only). You might want to enable this if you will be running it from crontab, to avoid long-running cron processes.")
define("restart",default=False,help="If True, try to terminate any other process listening on our port number before we start (Unix only). Useful if Web Adjuster is running in the background and you want to quickly restart it with new options. Note that no check is made to make sure the other process is a copy of Web Adjuster; whatever it is, if it has our port open, it is asked to stop.")
define("stop",default=False,help="Like 'restart', but don't replace the other process after stopping it. This option can be used to stop a background server (if it's configured with the same port number) without starting a new one. Unix only.") # "stop" overrides "restart", so if "restart" is set in a configuration file then you can still use "stop" on the command line
define("install",default=False,help="Try to install the program in the current user's Unix crontab as an @reboot entry, unless it's already there.  The arguments of the cron entry will be the same as the command line, with no directory changes, so make sure you are in the home directory before doing this.  The program will continue to run normally after the installation attempt.  (If you are on Cygwin then you might need to run cron-config also.)")
define("watchdog",default=0,help="(Linux only) Ping the system's watchdog every this number of seconds, so the watchdog can reboot the system if for any reason Web Adjuster stops functioning. The default value of 0 means do not ping the watchdog. If your machine's unattended boot is no longer reliable, beware of unnecessary reboot if you remotely stop the adjuster and are unable to restart it.") # e.g. some old Raspberry Pis no longer boot 100% of the time and have watchdogs that cannot be cleanly closed with 'V'
define("watchdogWait",default=0,help="When the watchdog option is set, wait this number of seconds before stopping the watchdog pings. This causes the watchdog pings to be sent from a separate thread and therefore not stopped when the main thread is busy; they are stopped only when the main thread has not responded for watchdogWait seconds. This can be used to work around the limitations of a hardware watchdog that cannot be set to wait that long.") # such as the Raspberry Pi's Broadcom chip which defaults to 10 seconds and has max 15; you could say watchdog=5 and watchdogWait=60 (if you have an RPi which actually reboots when the watchdog goes off, see above)
define("watchdogDevice",default="/dev/watchdog",help="The watchdog device to use (set this to /dev/null to check main-thread responsiveness without actually pinging the watchdog)")
define("browser",help="The Web browser command to run. If this is set, Web Adjuster will run the specified command (which is assumed to be a web browser), and will exit when this browser exits. This is useful in conjunction with --real_proxy to have a personal proxy run with the browser. You still need to set the browser to use the proxy; this can sometimes be done via browser command line or environment variables.")
define("run",help="A command to run that is not a browser. If set, Web Adjuster will run the specified command and will restart it if it stops. The command will be stopped when Web Adjuster is shut down. This could be useful, for example, to run an upstream proxy.")
define("runWait",default=1,help="The number of seconds to wait before restarting the 'run' command if it fails")
define("ssh_proxy",help="host[:port][,URL] which, if set, can help to proxy SSH connections over HTTP if you need to perform server administration from a place with port restrictions.  See comments in adjuster.py for details.")
# - If set host (and optional port, defaults to 22), then CONNECT requests for that server are accepted even without real_proxy.  Use (e.g.) ssh -o ProxyCommand "nc -X connect -x adjuster.example.org:80 %h %p" ssh-host
# - This however won't work if the adjuster is running on a virtual hosting provider (like OpenShift) which doesn't support CONNECT (and many of them don't even support streaming 1-way connections like proxy2ssh, even if we modify Tornado to do that).  But you can set ,URL and write a ProxyCommand like this:
"""# ---------- cut here ----------
#!/usr/bin/env python
host_name = host_name_or_IP = "you need to set this"
path_part_of_URL = "/you need to set this too"
import sys,socket,select,time,os ; lastPostTime = 0
def connect():
  global s ; s=socket.socket() ; s.connect((host_name_or_IP,80))
connect()
def post(dat):
  global lastPostTime
  if not lastPostTime: dat="new connection"
  s.sendall('POST %s HTTP/1.1\r\nHost: %s\r\nConnection: keep-alive\r\nContent-Length: %d\r\n\r\n%s' % (path_part_of_URL,host_name,len(dat),dat)) ; r="" ; rx = True
  while rx and not "\r\n\r\n" in r:
    try: rx = s.recv(1024)
    except socket.error: break
    r += rx
  if not "\r\n\r\n" in r: # probably keep-alive interrupted by virtualiser
    connect() ; return post(dat)
  cl=r[r.index(':',r.index("\nContent-Length:"))+1:].lstrip() ; cl=cl[:cl.index('\r')] ; cl=int(cl) ; r=r[r.index("\r\n\r\n")+4:]
  while len(r) < cl:
    rx = s.recv(1024) ; assert rx ; r += rx
  r = r[:cl] ; sys.stdout.write(r) ; sys.stdout.flush()
  lastPostTime = time.time()
interval = 1
while True:
  read = []
  while 0 in select.select([0], [], [], 0)[0]:
    rx = os.read(0,1) ; assert rx ; read.append(rx)
  if read or time.time() > lastPostTime+interval: post("".join(read))
  if read: interval = 1
  elif interval < 30: interval *= 2
  time.sleep(0.1)
# ---------- cut here ---------- """
# and if you then need to forward to the adjuster from a CGI
# script (for example because the adjuster itself can't be
# run on port 80) then try something like this:
"""# ---------- cut here ----------
#!/bin/bash
export URL=http://localhost:28080/LetMeIn # or whatever
export T=$(mktemp /dev/shm/XXXXXX) ; cat > $T
export T2=$(mktemp /dev/shm/XXXXXX)
wget --post-file $T -q -O - "$URL" > $T2
echo "Content-Length: $(wc -c < $T2)" # please don't "chunk" it
echo ; cat $T2 ; rm $T $T2
# ---------- cut here ---------- """

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
define("renderOmit",multiple=True,default="iPhone,iPad,Android,Macintosh,Windows NT 6,Windows NT 10,Windows Phone OS,Lynx/2",help="A list of platforms that do not need the character-set renderer. If any of these strings occur in the user-agent then the character set renderer is turned off even if it is otherwise enabled, on the assumption that these platforms either have enough fonts already, or wouldn't show the rendered images anyway.") # (Win: Vista=6.0 7=6.1 8=6.2 reportedly don't need language packs for display) (Lynx: being careful by specifying /2 to try to avoid false positives; don't list w3m as some versions can do graphics; not sure about Links/ELinks etc)
define("renderOmitGoAway",default=False,help="If set, any browsers that match renderOmit will not be allowed to use the adjuster. This is for servers that are set to do character rendering only and do not have enough bandwidth for people who don't need this function and just want a proxy.") # (See also the extended syntax of the headAppendCSS option, which forces all users to choose a stylesheet, especially if cssName is not set; that might be useful if the server's sole purpose is to add stylesheets and you don't want to provide a straight-through service for non-stylesheet users.)
define("renderCheck",help="If renderOmit does not apply to the browser, it might still be possible to check for native character-set support via Javascript. renderCheck can be set to the Unicode value of a character to be checked (try 802F for complete Chinese support); if the browser reports its width differently from known unprintable characters, we assume it won't need our renderer.") # 802F shouldn't create false positives in environments that support only GB2312, only Big5, only SJIS or only KSC instead of all Chinese. It does have GB+ and Big5+ codes (and also demonstrates that we want a hex number). If browser's "unprintable character" glyph happens to be the same width as renderCheck anyway then we could have a false negative, but that's better than a false positive and the user can still switch it off manually if renderName is left set.
define("renderNChar",default=1,help="The maximum number of characters per image to be given to the character-set renderer if it is enabled. Keeping this low means the browser cache is more likely to be able to re-use images, but some browsers might struggle if there are too many separate images. Don't worry about Unicode \"combining diacritic\" codes: any found after a character that is to be rendered will be included with it without counting toward the renderNChar limit and without needing to be in renderRange.")
define("renderWidth",default=0,help="The maximum pixel width of a 'word' when using the character-set renderer. If you are rendering a language that uses space to separate words, but are using only one or two characters per image, then the browser might split some words in the middle. Setting renderWidth to some value other than 0 can help to prevent this: any word narrower than renderWidth will be enclosed in a <nobr> element. (This will however be ineffective if your stylesheet overrides the behaviour of <nobr>.) You should probably not set renderWidth if you intend to render languages that do not separate words with spaces.")
define("renderDebug",default=False,help="If the character-set renderer is having problems, try to insert comments in the HTML source to indicate why.  The resulting HTML is not guaranteed to be well-formed, but it might help you debug a misbehaving htmlFilter.  This option may also insert comments in bad HTML before the htmlFilter stage even when the renderer is turned off.")
define("renderName",default="Fonts",help="A name for a switch that allows the user to toggle character set rendering on and off from the browser (via a cookie and Javascript links at the bottom of HTML pages); if set to the empty string then no switch is displayed. At any rate none is displayed when renderOmit applies.") # TODO: non-Javascript fallback for the switcher

heading("Dynamic DNS options")
define("ip_change_command",help="An optional script or other shell command to launch whenever the public IP address changes. The new IP address will be added as a parameter; ip_query_url must be set to make this work. The script can for example update any Dynamic DNS services that point to the server.")
define("ip_query_url",help="URL that will return your current public IP address, as a line of text with no markup added. Used for the ip_change_command option. You can set up a URL by placing a CGI script on a server outside your network and having it do: echo Content-type: text/plain;echo;echo $REMOTE_ADDR (but if you want your IPv4 address, ensure the adjuster machine and the outside server are not both configured for IPv6)")
define("ip_query_url2",help="Optional additional URL that might sometimes return your public IP address along with other information. This can for example be a status page served by a local router (http://user:password@192.168... is accepted, and if the password is the name of an existing file then its contents are read instead). If set, the following behaviour occurs: Once ip_query_interval has passed since the last ip_query_url check, ip_query_url2 will be queried at an interval of ip_query_interval2 (which can be short), to check that the known IP is still present in its response. Once the known IP is no longer present, ip_query_url will be queried again. This arrangement can reduce the load on ip_query_url as well as providing a faster response to IP changes, while not completely trusting the local router to report the correct IP at all times. See also ip_query_aggressive if the router might report an IP change before connectivity is restored. You may also set ip_query_url2 to the special value 'upnp' if you want it to query a router via UPnP (miniupnpc package required).") # (If using filename then its contents will be re-read every time the URL is used; this might be useful for example if the router password can change)
define("ip_check_interval",default=8000,help="Number of seconds between checks of ip_query_url for the ip_change_command option")
define("ip_check_interval2",default=60,help="Number of seconds between checks of ip_query_url2 (if set), for the ip_change_command option")
define("ip_query_aggressive",default=False,help="If a query to ip_query_url fails with a connection error or similar, keep trying again until we get a response. This is useful if the most likely reason for the error is that our ISP is down: we want to get the new IP just as soon as we're back online. However, if the error is caused by a problem with ip_query_url itself then this option can lead to excessive traffic, so use with caution. (Log entries are written when this option takes effect, and checking the logs is advisable.)")
define("ip_force_interval",default=7*24*3600,help="Number of seconds before ip_change_command (if set) is run even if there was no IP change.  This is to let Dynamic DNS services know that we are still around.  Set to 0 to disable forced updates (a forced update will occur on server startup anyway), otherwise an update will occur on the next IP check after ip_force_interval has elapsed.")

heading("Speedup options")
define("useLXML",default=False,help="Use the LXML library for parsing HTML documents. This is usually faster, but it can fail if your system does not have a good installation of LXML and its dependencies. Use of LXML libraries may also result in more changes to all HTML markup: this should be harmless for browsers, but beware when using options like bodyAppendGoesAfter then you might or might not be dealing with the original HTML depending on which filters are switched on.") # (hence bodyAppendGoesAfter now takes regexps as of adjuster 0.1836) / dependencies: did have ", or if the websites you visit are badly broken" but it turns out some breakages are actually better handled by LXML than by HTMLParser, e.g. <div id=something">
define("usepycurl",default=True,help="Use the pycurl library if available (setting this to False might save a little RAM at the expense of remote-server tolerance)")
define("renderBlocks",default=False,help="Treat all characters rendered by the character-set renderer as \"blocks\" that are guaranteed to have the same dimensions (true for example if you are using the renderer for Chinese characters only). This is faster than checking words individually, but it may produce incorrect HEIGHT and WIDTH attributes if given a range of characters whose dimensions do differ.") # TODO: blocksRange option for if want to render some that do and some that don't? (but profile it: PIL's getsize just might turn out to be quicker than the high-level range-check code)
define("fasterServer",help="Address:port of another instance of Web Adjuster to which we forward all traffic whenever it is available. When the other instance is not available, traffic will be handled by this one. Use for example if you have a slower always-on machine and a faster not-always-on machine and you want the slower machine to delegate to the faster machine when available. See also ipTrustReal.")
define("ipTrustReal",help="IP address of a machine that we trust, for example a machine that is using us as fasterServer. Any traffic coming from this machine with an X-Real-Ip header will be logged as though it originated at the value of its X-Real-Ip header. Setting this to * will cause X-Real-Ip to be trusted from ANY connection.") # , which might be useful in an environment where you know the adjuster can be reached only via a proxy but the proxy's address can change; see also trust_XForwardedFor. (TODO: multiple IPs option like ip_messages?  but might need to make it ipv6 ready)
define("trust_XForwardedFor",default=False,help="Like ipTrustReal but trusts X-Forwarded-For header from any IP if set to True (use this in an environment where the adjuster can be reached only via a load balancer etc)")
define("fasterServerNew",default=True,help="If fasterServer is set, assume it is running Web Adjuster v0.17 or later and use a more lightweight method of checking its availability. You might need to set this to False if for some reason you can't upgrade the fasterServer first.") # (don't do auto-fallback as that creates unnecessary extra traffic, plus sending an unrecognized ping2 could clutter logs)
define("machineName",help="A name for the current machine to insert into the \"Server\" HTTP header for adjusted requests, for example to let users know if it's your faster or your slower machine that's currently serving them (although they'd need to inspect the headers to find out)")
define("redirectFiles",default=False,help="If, when not functioning as a \"real\" HTTP proxy, a URL is received that looks like it requires no processing on our part (e.g. an image or downloadable file that the user does not want converted), and if this is confirmed via a HEAD request to the remote server, then redirect the browser to fetch it directly and not via Web Adjuster. This takes bandwidth off the adjuster server, and should mean faster downloads, especially from sites that are better connected than the adjuster machine. However it might not work with sites that restrict \"deep linking\". (As a precaution, the confirmatory HEAD request is sent with a non-adjusted Referer header to simulate what the browser would send if fetching directly. If this results in an HTML \"Referer denied\" message then Web Adjuster will proxy the request in the normal way. This precaution might not detect ALL means of deep-linking denial though.)") # e.g. cookie-based, or serving an image but not the real one.  But it works with Akamai-based assets servers as of 2013-09 (but in some cases you might be able to use codeChanges to point these requests back to the site's original server instead of the Akamai one, if the latter just mirrors the former which is still available, and therefore save having to proxy the images.  TODO: what if you can't do that but you can run another service on a higher bandwidth machine that can cache them, but can't run the adjuster on the higher-bandwidth machine; can we redirect?)
# If adjuster machine is running on a home broadband connection, don't forget the "uplink" speed of that broadband is likely to be lower than the "downlink" speed; the same should not be the case of a site running at a well-connected server farm.  There's also extra delay if Web Adjuster has to download files first (which might be reduced by implementing streaming).  Weighed against this is the extra overhead the browser has of repeating its request elsewhere, which could be an issue if the file is small and the browser's uplink is slow; in that case fetching it ourselves might be quicker than having the browser repeat the request; see TODO comment elsewhere about minimum content length before redirectFiles.
# TODO: for Referer problems in redirectFiles, if we're not on HTTPS, could redirect to an HTTPS page (on a separate private https server, or https://www.google.com/url/?q= but they might add checks) which then redirs to the target HTTP page, but that might not strip Referer on MSIE 7 etc, may have to whitelist browsers+versions for it, or test per-request but that wld lead to 4 redirects per img instead of 2 although cld cache (non-empty) ok-browser-strings (and hold up other requests from same browser until we know or have timed out ??); do this only if sendHead returns false but sendHead with proper referer returns ok (and cache a few sites where this is the case so don't have to re-test) ??  also it might not work in places where HTTPS is forbidden
# TODO: redirectFiles could call request_no_external_referer and test with blank Referer instead of non-adjusted Referer, but we'd have to figure out some way of verifying that the browser actually supports 'Referrer-Policy: same-origin' before doing this

define("upstream_guard",default=True,help="Modify scripts and cookies sent by upstream sites so they do not refer to the cookie names that our own scripts use. This is useful if you chain together multiple instances of Web Adjuster, such as for testing another installation without coming out of your usual proxy. If however you know that this instance will not be pointed to another, you can set upstream_guard to False to save some processing.")
define("skipLinkCheck",multiple=True,help="Comma-separated list of regular expressions specifying URLs to which we won't try to add or modify links for the pdftotext, epubtotext, epubtozip, askBitrate or mailtoPath options.  This processing can take some time on large index pages with thousands of links; if you know that none of them are PDF, EPUB, MP3 or email links, or if you don't mind not processing any that are, then it saves time to skip this step for those pages.") # TODO: it would be nice to have a 'max links on the page' limit as an alternative to a list of URL patterns

define("extensions",help="Name of a custom Python module to load to handle certain requests; this might be more efficient than setting up a separate Tornado-based server. The module's handle() function will be called with the URL and RequestHandler instance as arguments, and should return True if it processed the request, but anyway it should return as fast as possible. This module does NOT take priority over forwarding the request to fasterServer.")

define("loadBalancer",default=False,help="Set this to True if you have a default_site set and you are behind any kind of \"load balancer\" that works by issuing a GET / with no browser string. This option will detect such requests and avoid passing them to the remote site.")
define("multicore",default=False,help="(Linux only) On multi-core CPUs, fork enough processes for all cores to participate in handling incoming requests. This increases RAM usage, but can help with high-load situations. Disabled on BSD/Mac due to unreliability (other cores can still be used for htmlFilter etc)") # and --ssl-fork if there's not TOO many instances taking up the RAM; if you really want multiple cores to handle incoming requests on Mac/BSD you could run GNU/Linux in a virtual machine (or use a WSGI server)
# Note: start_multicore() does NOT use SO_REUSEPORT multiplexing: it forks AFTER we've started listening to the port, and processes share the SAME socket (SO_REUSEPORT is for different sockets).
# If rewriting for SO_REUSEPORT multiplexing (open socket after fork): Linux 3.9+ uses a hash (including remote IP + source port) to decide which process gets it; contrary to some articles, it does not account for which of the port-sharing processes are currently blocking on accept() (which is not relevant to Tornado anyway): that approach would require processes to share the SAME socket with a bunch of threads calling accept().  With so_reuseport a process would have to close and reopen its port if it wants to temporarily shut itself off (and this is NOT recommended because changing the number of open ports mid-flight can cause ACKs to get lost in some kernel versions).
# Linux 4.6+ adds a BPF bytecode option (see SO_ATTACH_REUSEPORT_ options in man 7 socket): if using this for js_interpreter balancing, would need cores to open their sockets in a known order so the index numbers make sense; the more basic CBPF option would be:
# # From linux/include/uapi/linux/bpf_common.h :
# BPF_LD,BPF_LDX,BPF_ST,BPF_STX,BPF_ALU,BPF_JMP,BPF_RET,BPF_MISC=range(8) # instruction classes
# BPF_W,BPF_H,BPF_B = 0,8,16 # ld/ldx fields
# BPF_IMM,BPF_ABS,BPF_IND,BPF_MEM,BPF_LEN,BPF_MSH = 0,32,64,96,128,160 # ld/ldx modes
# BPF_ADD,BPF_SUB,BPF_MUL,BPF_DIV,BPF_OR,BPF_AND,BPF_LSH,BPF_RSH,BPF_NEG,BPF_MOD,BPF_XOR = range(0,161,16) # ALU fields
# BPF_JA,BPF_JEQ,BPF_JGT,BPF_JGE,BPF_JSET = range(0,65,16) # JMP fields
# BPF_K,BPF_X = 0,8
# def bpf_instruction(code,k,jumpTrue=0,jumpFalse=0): return struct.pack('HBBI', code, jumpTrue, jumpFalse, k)
# def bpf_random(): return bpf_instruction(32,0xfffff038) # = ld rand (loads a random uint32 into A), from bpf_asm -c
# def bpf_jumpIfGreater(k,toSkip): return bpf_instruction(JGT,k,toSkip)
# # etc
# filterProg = [ ] # list of bpf_random() bpf_jumpIfGreater() etc calls
# b = ctypes.create_string_buffer(''.join(filterProg))
# socket.setsockopt(socket.SOL_SOCKET, 51, struct.pack('HL', len(filterProg), ctypes.addressof(b)))
# but would then need periodically to update the program to use a different random distribution depending on the current values of len(webdriver_queue)+len(webdriver_runner) or similar (would probably need to forward all metrics to coreNo 0, as must be handled by one of the listening processes not by an extra process)
# eBPF can pass data to/from the BPF program via "maps", which might be more efficient than reloading the program.  Would need to do socket.setsockopt(socket.SOL_SOCKET, 52, fd) but need a C module to call the bpf() syscall to get that fd.  Would probably need something like https://github.com/iovisor/bcc/ (recent distro required).
define("compress_responses",default=True,help="Use gzip to compress responses for clients that indicate they are compatible with it. You may want to turn this off if your server's CPU is more important than your network bandwidth (e.g. browser on same machine).")

# THIS MUST BE THE LAST SECTION because it continues into
# the note below about Tornado logging options.  (The order
# of define()s affects the HTML order only; --help will be
# sorted alphabetically by Tornado.)
heading("Logging options")
define("profile",default=0,help="Log timing statistics every N seconds (only when not idle)")
define("profile_lines",default=5,help="Number of lines to log when profile option is in use (not applicable if using --multicore)")
define("renderLog",default=False,help="Whether or not to log requests for character-set renderer images. Note that this can generate a LOT of log entries on some pages.")
define("logUnsupported",default=False,help="Whether or not to log attempts at requests using unsupported HTTP methods. Note that this can sometimes generate nearly as many log entries as renderLog if some browser (or malware) tries to do WebDAV PROPFIND requests on each of the images.")
define("logRedirectFiles",default=True,help="Whether or not to log requests that result in the browser being simply redirected to the original site when the redirectFiles option is on.") # (Since this still results in a HEAD request being sent to the remote site, this option defaults to True in case you need it to diagnose "fair use of remote site" problems)
define("ownServer_useragent_ip",default=False,help="If own_server is set, and that server cannot be configured to log the X-Real-Ip header we set when we proxy for it, you can if you wish turn on this option, which will prepend the real IP to the User-Agent header on the first request of each connection (most servers can log User-Agent). This is slightly dangerous: fake IPs can be inserted into the log if keep-alive is used.") # (and it might break some user-agent detection)
define("ipNoLog",multiple=True,help="A comma-separated list of IP addresses which can use the adjuster without being logged. If your network has a \"friendly probing\" service then you might want to use this to stop it filling up the logs.  (Any tracebacks it causes will still be logged however.)")
define("squashLogs",default=True,help="Try to remove some duplicate information from consecutive log entries, to make logs easier to check. You might want to set this to False if you plan to use automatic search tools on the logs.") # (word 'some' is important as not all duplicate info is guaranteed to be removed)
define("whois",default=False,help="Try to log the Internet service provider for each IP address in the logs.  Requires the 'whois' program.  The extra information is written as separate log entries when it becomes available, and not for recent duplicate IPs or IPs that do not submit valid requests.")
define("errorHTML",default="Adjuster error has been logged",help="What to say when an uncaught exception (due to a misconfiguration or programming error) has been logged. HTML markup is allowed in this message. If for some reason you have trouble accessing the log files, the traceback can usually be included in the page itself by placing {traceback} in the message.") # TODO: this currently requires Tornado 2.1+ (document this? see TODO in write_error)
define("logDebug",default=False,help="Write debugging messages (to standard error if in the foreground, or to the logs if in the background). Use as an alternative to --logging=debug if you don't also want debug messages from other Tornado modules.") # see debuglog()
# and continuing into the note below:
if not tornado:
    print "</dl>"
    print "Tornado-provided logging options are not listed above because they might vary across Tornado versions; run <tt>python adjuster.py --help</tt> to see a full list of the ones available on your setup. They typically include <tt>log_file_max_size</tt>, <tt>log_file_num_backups</tt>, <tt>log_file_prefix</tt> and <tt>log_to_stderr</tt>." # and --logging=debug but that may generate a lot of entries from curl_httpclient
    raise SystemExit

import time,os,commands,string,urllib,urlparse,re,socket,logging,subprocess,threading,base64,htmlentitydefs,signal,traceback
try: import simplejson as json # Python 2.5, and faster?
except: import json # Python 2.6
from HTMLParser import HTMLParser,HTMLParseError

try: # can we page the help text?
    # (Tornado 2 just calls the module-level print_help, but Tornado 3 includes some direct calls to the object's method, so we have to override the latter.  Have to use __dict__ because they override __setattr__.)
    import pydoc,cStringIO ; pydoc.pager # ensure present
    def new_top(*args):
        dat = cStringIO.StringIO()
        dat.write(twoline_program_name+"\n")
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
    return options.default_site.split("/")[n]

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
    if not requested_host: requested_host = "" # ?
    port=":"+str(options.publicPort) # the port to advertise
    orig_requested_host = requested_host
    if requested_host.endswith(port): requested_host=requested_host[:-len(port)]
    if options.publicPort==80: port=""
    for h in options.host_suffix.split("/"):
      if (requested_host == h and options.default_site) or requested_host.endswith("."+h): return h+port
    return options.host_suffix+port
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
    elif not options.wildcard_dns and real_host == cookie_host:
        return hostSuffix(0)+port # no default_site, cookie_host everywhere
    if not options.wildcard_dns: return real_host # leave the proxy
    else: return dedot(real_host)+"."+hostSuffix()+port

# RFC 2109: A Set-Cookie from request-host y.x.example.com for Domain=.example.com would be rejected, because H is y.x and contains a dot.
# That means (especially if a password is set) we'd better make sure our domain-rewrites don't contain dots.  If requested with dot, relocate to without dot.  (But see below re RFC 1035 limitation.)
def dedot(domain):
    # - means . but -- is a real - (OK as 2 dots can't come together and a - can't come immediately after a dot in domain names, so --- = -., ---- = --, ----- = --. etc)
    d2 = domain.replace("-","--").replace(".","-")
    if len(d2) > 63: return domain # because RFC 1035 puts a 63-byte limit on each label (so our cross-domain preferences cookies can't work on very long domains, TODO document this?)
    else: return d2
def redot(domain): return domain.replace("--","@MINUS@").replace("-",".").replace("@MINUS@","-")

def protocolAndHost(realHost):
    # HTTPS hack: host ends with .0 = use HTTPS instead of HTTP
    # (the dot will be represented as a hyphen by dedot/redot,
    # but some servers e.g. GAE can't cope with any part of the
    # wildcard domain ending with a hyphen, so add the 0;
    # TODO: what about fetching from IP addresses, although it's rare to get a server with IP ending .0 because it used to represent "the network")
    if realHost.endswith(".0"): return "https://",realHost[:-2]
    else: return "http://",realHost
def protocolWithHost(realHost):
    x,y = protocolAndHost(realHost) ; return x+y

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
        if not istty(): logging.error(msg)
        # in case run from crontab w/out output (and e.g. PATH not set properly)
        # (but don't do this if not options.background, as log_to_stderr is likely True and it'll be more cluttered than the simple sys.stderr.write below)
    except: pass # options or logging not configured yet
    sys.stderr.write(msg+"\n")
    sys.exit(1)

def parse_command_line(final):
    if len(tornado.options.parse_command_line.func_defaults)==1: # Tornado 2.x
        rest = tornado.options.parse_command_line()
    else:
        rest=tornado.options.parse_command_line(final=final)
    if rest: errExit("Unrecognised command-line argument '%s'" % rest[0]) # maybe they missed a '--' at the start of an option: don't want result to be ignored without anyone noticing
def parse_config_file(cfg, final):
    check_config_file(cfg)
    if not tornado.options.parse_config_file.func_defaults: # Tornado 2.x
        tornado.options.parse_config_file(cfg)
    else: tornado.options.parse_config_file(cfg,final=final)
def check_config_file(cfg):
    # (why doesn't Tornado do this by default?  catch
    # capitalisation and spelling errors etc)
    try:
        options = tornado.options.options._options
        from tornado.util import exec_in
    except: return
    d = {} ; exec_in(open(cfg,'rb').read(),d,d)
    for k in d.keys():
        if not k in options and not k.replace('_','-') in options and type(d[k]) in [str,unicode,list,bool,int]: # (allow functions etc)
            errExit("Unrecognised global '%s' in configuration file '%s'" % (k,cfg))

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
        except: errExit("Cannot open configuration file %s (current directory is %s)" % (config2,os.getcwd()))
        parse_config_file(config2,False)
        configsDone.add((config,oldDir))
    parse_command_line(True) # need to do this again to ensure logging is set up for the *current* directory (after any chdir's while reading config files)

class CrossProcessLogging(logging.Handler):
    def needed(self): return (options.multicore or options.ssl_fork or (options.js_interpreter and options.js_multiprocess)) and options.log_file_prefix # (not needed if stderr-only or if won't fork)
    def init(self):
        self.multiprocessing = False
        if not self.needed(): return
        try: logging.getLogger().handlers
        except: errExit("The logging module on this system is not suitable for --log-file-prefix with --ssl-fork or --js-multiprocess") # because we won't know how to clear its handlers and start again in the child processes
        try: import multiprocessing
        except ImportError: multiprocessing = None
        self.multiprocessing = multiprocessing
        if not self.multiprocessing: return # we'll have to open multiple files in initChild instead
        self.loggingQ=multiprocessing.Queue()
        def logListener():
          try:
            while True: logging.getLogger().handle(self.loggingQ.get())
          except KeyboardInterrupt: pass
        self.p = multiprocessing.Process(target=logListener) ; self.p.start()
        logging.getLogger().handlers = [] # clear what Tornado has already put in place when it read the configuration
        logging.getLogger().addHandler(self)
    def initChild(self,toAppend=""):
        if not options.log_file_prefix: return # stderr is OK
        if self.multiprocessing:
            try: self.multiprocessing.process.current_process()._children.clear() # so it doesn't try to join() to children it doesn't have (multiprocessing wasn't really designed for the parent to fork() outside of multiprocessing later on)
            except: pass # probably wrong version
            return # should be OK now
        logging.getLogger().handlers = [] # clear Tornado's
        if toAppend: options.log_file_prefix += "-"+toAppend
        else: options.log_file_prefix += "-"+str(os.getpid())
        # and get Tornado to (re-)initialise logging with these parameters:
        if hasattr(tornado.options,"enable_pretty_logging"): tornado.options.enable_pretty_logging() # Tornado 2
        else: # Tornado 4
            import tornado.log
            tornado.log.enable_pretty_logging()
    def shutdown(self):
        try: self.p.terminate() # in case KeyboardInterrupt hasn't already stopped it
        except: pass
    def emit(self, record): # simplified from Python 3.2:
        try:
            ei = record.exc_info
            if ei:
                dummy = self.format(record) # record.exc_text
                record.exc_info = None
            self.loggingQ.put(record)
        except (KeyboardInterrupt, SystemExit): raise
        except: self.handleError(record)

def initLogging(): # MUST be after unixfork() if background
    global CrossProcessLogging
    CrossProcessLogging = CrossProcessLogging()
    CrossProcessLogging.init()

def preprocessOptions():
    if options.version: errExit("--version is for the command line only, not for config files") # to save confusion.  (If it were on the command line, we wouldn't get here: we process it before loading Tornado.  TODO: if they DO try to put it in a config file, they might set some type other than string and get a less clear error message from tornado.options.)
    if options.restart and options.watchdog and options.watchdogDevice=="/dev/watchdog" and options.user and os.getuid(): errExit("This configuration looks like it should be run as root.") # if the process we're restarting has the watchdog open, and the watchdog is writable only by root (which is probably at least one of the reasons why options.user is set), there's no guarantee that stopping that other process will properly terminate the watchdog, and we won't be able to take over, = sudden reboot
    if options.host_suffix==getfqdn_default: options.host_suffix = socket.getfqdn()
    if type(options.mailtoSMS)==type(""): options.mailtoSMS=options.mailtoSMS.split(',')
    if type(options.leaveTags)==type(""): options.leaveTags=options.leaveTags.split(',')
    if type(options.stripTags)==type(""): options.stripTags=options.stripTags.split(',')
    if options.render:
        try: import PIL
        except ImportError: errExit("render requires PIL")
    if options.js_interpreter:
      global webdriver
      try: from selenium import webdriver
      except: errExit("js_interpreter requires selenium")
      check_jsInterpreter_valid()
      if options.js_multiprocess:
        try: import multiprocessing # Python 2.6
        except ImportError: # can't do it then
            options.js_multiprocess = False
    create_inRenderRange_function(options.renderRange)
    if type(options.renderOmit)==type(""): options.renderOmit=options.renderOmit.split(',')
    if options.renderOmitGoAway:
        if options.renderCheck: errExit("Setting both renderOmitGoAway and renderCheck is not yet implemented (renderOmitGoAway assumes all testing is done by renderOmit only).  Please unset either renderOmitGoAway or renderCheck.")
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
    global upstream_rewrite_ssl ; upstream_rewrite_ssl=False
    global cores ; cores = 1
    if options.multicore:
        if not 'linux' in sys.platform: errExit("multicore option not supported on this platform") # it does work on BSD/Mac, but some incoming connections get 'lost' so it's not a good idea
        # Not needed unless we're rewriting multicore to use SO_REUSEPORT:
        # if tuple(int(x) for x in open("/proc/version").readline().split()[2].split('.',2)[:2]) < (3,9): errExit("Linux kernel version must be at least 3.9 for multicore to work (SO_REUSEPORT)")
        import tornado.process
        cores = tornado.process.cpu_count()
        if cores==1: options.multicore = False
        elif options.js_interpreter and options.js_instances % cores:
            old = options.js_instances
            options.js_instances += (cores - (options.js_instances % cores))
            sys.stderr.write("multicore: changing js_instances %d -> %d (%d per core x %d cores)\n" % (old,options.js_instances,options.js_instances/cores,cores))
    global js_per_core
    js_per_core = options.js_instances/cores
    if options.upstream_proxy:
        maxCurls = 30*js_per_core
        if options.ssl_fork: maxCurls /= 2
        if not options.usepycurl: errExit("upstream_proxy is not compatible with --usepycurl=False")
        setupCurl(maxCurls,"upstream_proxy requires pycurl (try sudo pip install pycurl)")
        if not ':' in options.upstream_proxy: options.upstream_proxy += ":80"
        upstream_proxy_host,upstream_proxy_port = options.upstream_proxy.split(':') # TODO: IPv6 ?
        if not upstream_proxy_host:
            upstream_proxy_host = "127.0.0.1"
            if wsgi_mode: sys.stderr.write("Can't do SSL-rewrite for upstream proxy when in WSGI mode\n")
            else: upstream_rewrite_ssl = True
        upstream_proxy_port = int(upstream_proxy_port)
    elif options.usepycurl and not options.submitPath=='/': setupCurl(3*js_per_core) # and no error if not there
    global codeChanges ; codeChanges = []
    if options.codeChanges:
      ccLines = [x for x in [x.strip() for x in options.codeChanges.split("\n")] if x and not x.startswith("#")]
      while ccLines:
        if len(ccLines)<3: errExit("codeChanges must be a multiple of 3 lines (see --help)")
        codeChanges.append(tuple(ccLines[:3]))
        ccLines = ccLines[3:]
    if options.real_proxy:
        options.open_proxy=True
        if options.browser and "lynx" in options.browser and not "I_PROMISE_NOT_TO_LYNX_DUMP_SSL" in os.environ and not "-stdin" in options.browser and ("-dump" in options.browser or "-source" in options.browser or "-mime_header" in options.browser): errExit("Don't do that.  If Lynx wants to ask you about our self-signed certificates, it'll assume the answer is No when running non-interactively, and this will cause it to fetch the page directly (not via our proxy) which could confuse you into thinking the adjuster's not working.  If you know what you're doing, put I_PROMISE_NOT_TO_LYNX_DUMP_SSL in the environment to suppress this message (but if using js_interpreter beware of redirect to SSL).  Or you can use wget --no-check-certificate -O - | lynx -dump -stdin") # TODO: could we configure Lynx to always accept when running non-interactively?
    if options.htmlFilter and '#' in options.htmlFilter and not len(options.htmlFilter.split('#'))+1 == len(options.htmlFilterName.split('#')): errExit("Wrong number of #s in htmlFilterName for this htmlFilter setting")
    if not options.port:
        if wsgi_mode:
            sys.stderr.write("Warning: port=0 won't work in WSGI mode, assuming 80\n")
            options.port = 80
        else:
            options.real_proxy=options.js_reproxy=False ; options.fasterServer=""
            options.open_proxy = True # bypass the check
    if not options.publicPort:
        options.publicPort = options.port
    if not options.password and not options.open_proxy and not options.submitPath=='/' and not options.stop: errExit("Please set a password, or use --open_proxy.\n(Try --help for help; did you forget a --config=file?)") # (as a special case, if submitPath=/ then we're serving nothing but submit-your-own-text and bookmarklets, which means we won't be proxying anything anyway and don't need this check)
    if options.submitBookmarkletDomain and not options.publicPort==80: errExit("submitBookmarkletDomain option requires public port to be 80 (and HTTPS-capable on port 443)")
    if options.pdftotext and not "pdftotext version" in os.popen4("pdftotext -h")[1].read(): errExit("pdftotext command does not seem to be usable\nPlease install it, or unset the pdftotext option")
    if options.epubtotext and not "calibre" in os.popen4("ebook-convert -h")[1].read(): errExit("ebook-convert command does not seem to be usable\nPlease install calibre, or unset the epubtotext option")
    global extensions
    if options.extensions:
        extensions = __import__(options.extensions)
    else:
        class E:
            def handle(*args): return False
        extensions = E()
    global ownServer_regexp
    if options.ownServer_regexp:
        if not options.own_server: errExit("Cannot set ownServer_regexp if own_sever is not set")
        ownServer_regexp = re.compile(options.ownServer_regexp)
    else: ownServer_regexp = None
    global ipMatchingFunc
    if options.ip_messages: ipMatchingFunc=ipv4ranges_func(options.ip_messages)
    else: ipMatchingFunc = None
    global submitPathIgnorePassword, submitPathForTest
    if options.submitPath and options.submitPath.startswith('*'):
        submitPathIgnorePassword = True
        options.submitPath = options.submitPath[1:]
    else: submitPathIgnorePassword = False
    submitPathForTest = options.submitPath
    if submitPathForTest and submitPathForTest[-1]=="?": submitPathForTest = submitPathForTest[:-1] # for CGI mode: putting the ? in tells adjuster to ADD a ? before any parameters, but does not require it to be there for the base submit URL (but don't do this if not submitPathForTest because it might not be a string)
    if options.submitPath and not options.htmlText: errExit("submitPath only really makes sense if htmlText is set (or do you want users to submit actual HTML?)") # TODO: allow this? also with submitBookmarklet ??
    if options.prominentNotice=="htmlFilter":
        if not options.htmlFilter: errExit("prominentNotice=\"htmlFilter\" requires htmlFilter to be set")
        if options.htmlJson or options.htmlText: errExit("prominentNotice=\"htmlFilter\" does not work with the htmlJson or htmlText options")
    if not (options.submitPath and options.htmlFilter): options.submitBookmarklet = False # TODO: bookmarklet for character rendering? (as an additional bookmarklet if there are filters as well, and update submitBookmarklet help text) although it's rare to find a machine that lacks fonts but has a bookmarklet-capable browser
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
    global allowConnectHost,allowConnectPort,allowConnectURL
    allowConnectHost=allowConnectPort=allowConnectURL=None
    if options.ssh_proxy:
        if ',' in options.ssh_proxy: sp,allowConnectURL = options.ssh_proxy.split(',',1)
        else: sp = options.ssh_proxy
        if ':' in sp: allowConnectHost,allowConnectPort=sp.rsplit(':',1)
        else: allowConnectHost,allowConnectPort = sp,"22"
    if not options.default_site: options.default_site = ""
    # (so we can .split it even if it's None or something)
    if not options.js_interpreter: options.js_reproxy=False
    elif not options.htmlonly_mode: errExit("js_interpreter requires htmlonly_mode")
def open_upnp():
    if options.ip_query_url2=="upnp":
        global miniupnpc ; import miniupnpc # sudo pip install miniupnpc or apt-get install python-miniupnpc
        miniupnpc = miniupnpc.UPnP()
        miniupnpc.discoverdelay=200

profile_forks_too = False # TODO: configurable
def open_profile():
    if options.profile:
        global cProfile,pstats,cStringIO,profileIdle,psutil
        import cProfile, pstats, cStringIO
        try: import psutil
        except ImportError: psutil = None
        setProfile() ; profileIdle = False
        global reqsInFlight,origReqInFlight
        reqsInFlight = set() ; origReqInFlight = set()
def open_profile_pjsOnly(): # TODO: combine with above
    if options.profile:
        global profileIdle,psutil
        try: import psutil
        except ImportError: psutil = None
        setProfile_pjsOnly() ; profileIdle = False
        global reqsInFlight,origReqInFlight
        reqsInFlight = set() ; origReqInFlight = set()
def setProfile():
    global theProfiler, profileIdle
    theProfiler = cProfile.Profile()
    IOLoop.instance().add_timeout(time.time()+options.profile,lambda *args:pollProfile())
    profileIdle = True ; theProfiler.enable()
def setProfile_pjsOnly():
    IOLoop.instance().add_timeout(time.time()+options.profile,lambda *args:pollProfile_pjsOnly())
    global profileIdle ; profileIdle = True
def pollProfile():
    theProfiler.disable()
    if not profileIdle: showProfile()
    setProfile()
def pollProfile_pjsOnly():
    if not profileIdle: showProfile(pjsOnly=True)
    setProfile_pjsOnly()
def showProfile(pjsOnly=False):
    if pjsOnly: pr = ""
    else:
        s = cStringIO.StringIO()
        pstats.Stats(theProfiler,stream=s).sort_stats('cumulative').print_stats()
        pr = "\n".join([x for x in s.getvalue().split("\n") if x and not "Ordered by" in x][:options.profile_lines])
    if options.js_interpreter and len(webdriver_runner):
        global webdriver_lambda,webdriver_mu,webdriver_maxBusy,webdriver_oops
        stillUsed = sum(1 for i in webdriver_runner if i.thread_running)
        maybeStuck = sum(1 for i in webdriver_runner if i.maybe_stuck)
        for i in webdriver_runner: i.maybe_stuck = i.thread_running
        webdriver_maxBusy = max(webdriver_maxBusy,stillUsed)
        if pr: pr += "\n"
        elif not options.background: pr += ": "
        if options.multicore: offset = "js_interpreter(%d-%d)" % (webdriver_runner[0].start,webdriver_runner[0].start+js_per_core-1)
        else: offset = "js_interpreter"
        if not webdriver_maxBusy: pr += offset+" idle"
        else:
            if webdriver_oops: served = "%d successes + %d failures = %d served" % (webdriver_mu-webdriver_oops,webdriver_oops,webdriver_mu)
            else: served = "%d served" % webdriver_mu
            if maybeStuck: stuck = "%d may be" % maybeStuck
            else: stuck = "none"
            pr += offset+" %d/%d used (%d still in use, %s stuck); queue %d (%d arrived, %s)" % (webdriver_maxBusy,len(webdriver_runner),stillUsed,stuck,len(webdriver_queue),webdriver_lambda,served)
        webdriver_lambda = webdriver_mu = 0
        webdriver_oops = 0
        webdriver_maxBusy = stillUsed
        # TODO: also measure lambda/mu of other threads e.g. htmlFilter ?
        if psutil: pr += "; system RAM %.1f%% used" % (psutil.virtual_memory().percent)
    if pr: pr += "\n"
    elif not options.background: pr += ": "
    pr += "%d requests in flight (%d from clients)" % (len(reqsInFlight),len(origReqInFlight))
    if options.background: logging.info(pr)
    elif can_do_ansi_colour: sys.stderr.write("\033[35m"+(time.strftime("%X")+pr).replace("\n","\n\033[35m")+"\033[0m\n")
    else: sys.stderr.write(time.strftime("%X")+pr+"\n")

def setProcName(name="adjuster"):
    "Try to set the process name for top/ps"
    try: # works on both Linux and BSD/Mac if installed (although doesn't affect Mac OS 10.7 "Activity Monitor")
        import setproctitle # sudo pip install setproctitle or apt-get install python-setproctitle (requires gcc)
        return setproctitle.setproctitle(name) # (TODO: this also stops 'ps axwww' from displaying command-line arguments; make it optional?)
    except: pass
    try: # ditto but non-Mac BSD not checked:
        import procname # sudo pip install procname (requires gcc)
        return procname.setprocname(name)
    except: pass
    try: # this works in GNU/Linux for 'top', 'pstree -p' and 'killall', but not 'ps' or 'pidof' (which need argv[0] to be changed in C) :
        import ctypes
        b = ctypes.create_string_buffer(len(name)+1)
        b.value = name
        ctypes.cdll.LoadLibrary('libc.so.6').prctl(15,ctypes.byref(b),0,0,0)
    except: pass # oh well

def serverControl():
    if options.install:
        current_crontab = commands.getoutput("crontab -l 2>/dev/null")
        def shell_escape(arg):
            if re.match("^[A-Za-z0-9_=/.%+,:@-]*$",arg): return arg # no need to quote if it's entirely safe-characters (including colon: auto-complete escapes : in pathnames but that's probably in case it's used at the START of a command, where it's a built-in alias for 'true')
            return "'"+arg.replace("'",r"'\''")+"'"
        def cron_escape(arg): return shell_escape(arg).replace('%',r'\%')
        new_cmd = "@reboot python "+" ".join(cron_escape(a) for a in sys.argv)
        if not new_cmd in current_crontab.replace("\r","\n").split("\n") and not new_cmd in current_crontab.replace("$HOME",os.environ.get("HOME")).replace("\r","\n").split("\n"):
            sys.stderr.write("Adding to crontab: "+new_cmd+"\n")
            if not current_crontab.endswith("\n"): current_crontab += "\n"
            os.popen("crontab -","w").write(current_crontab+new_cmd+"\n")
    if options.restart or options.stop:
        pidFound = stopOther()
        if options.stop:
            if not pidFound: sys.stderr.write("Could not find which PID to stop (maybe nothing was running?)\n")
            try: CrossProcessLogging.shutdown()
            except: pass
            sys.exit(0)

def make_WSGI_application():
    global errExit, wsgi_mode, runFilter, sync_runFilter
    wsgi_mode = True ; runFilter = sync_runFilter
    def errExit(m): raise Exception(m)
    global main
    def main(): raise Exception("Cannot run main() after running make_WSGI_application()")
    preprocessOptions()
    for opt in 'config user address background restart stop install watchdog browser ip_change_command fasterServer ipTrustReal renderLog logUnsupported ipNoLog whois own_server ownServer_regexp ssh_proxy js_reproxy ssl_fork'.split(): # also 'port' 'logRedirectFiles' 'squashLogs' but these have default settings so don't warn about them
        # (js_interpreter itself should work in WSGI mode, but would be inefficient as the browser will be started/quit every time the WSGI process is.  But js_reproxy requires additional dedicated ports being opened on the proxy: we *could* do that in WSGI mode by setting up a temporary separate service, but we haven't done it.)
        if eval('options.'+opt):
            sys.stderr.write("Warning: '%s' option may not work in WSGI mode\n" % opt)
    options.js_reproxy = False # for now (see above)
    if (options.pdftotext or options.epubtotext or options.epubtozip) and (options.pdfepubkeep or options.waitpage):
        options.pdfepubkeep=0 ; options.waitpage = False
        sys.stderr.write("Warning: pdfepubkeep and waitpage may not work in WSGI mode; clearing them\n") # both rely on one process doing all requests (not guaranteed in WSGI mode), and both rely on ioloop's add_timeout being FULLY functional
    options.own_server = "" # for now, until we get forwardFor to work (TODO, and update the above list of ignored options accordingly)
    import tornado.wsgi
    handlers = [("(.*)",SynchronousRequestForwarder)]
    if options.staticDocs: handlers.insert(0,static_handler()) # (the staticDocs option is probably not really needed in a WSGI environment if we're behind a wrapper that can also list static URIs, but keeping it anyway might be a convenience for configuration-porting; TODO: warn that this won't work with htaccess redirect and SCRIPT_URL thing)
    return tornado.wsgi.WSGIApplication(handlers)

sslforks_to_monitor = [] # list of [pid,callback1,callback2,port,last response time]
sslfork_monitor_pid = None
def sslSetup(callback1, port2):
    if options.ssl_fork: # queue it to be started by monitor
        callback2 = lambda *_:listen_on_port(Application([(r"(.*)",AliveResponder,{})],log_function=nullLog),port2,"127.0.0.1",False) # the "I'm still alive" responder is non-SSL
        if options.multicore and sslforks_to_monitor: sslforks_to_monitor[0][1] = lambda c1=callback1,c2=sslforks_to_monitor[0][1]:(c1(),c2()) # in multicore mode we'll have {N cores} * {single process handling all SSL ports}, rather than cores * processes (TODO: if one gets stuck but others on the port can still handle requests, do we want to somehow detect the individual stuck one and restart it to reduce wasted CPU load?)
        else:
            sslforks_to_monitor.append([None,callback1,callback2,port2,None])
            return port2 + 1 # where to put the next listener
    else: callback1() # just run it on the current process
    return port2 # next listener can use what would have been the monitor port
sslFork_pingInterval = 1 # TODO: configurable?  (ping every interval, restart if down for 2*interval)  (if setting this larger, might want to track the helper threads for early termination)
def maybe_sslfork_monitor():
    "Returns SIGTERM callback if we're now a child process"
    global sslforks_to_monitor
    if not sslforks_to_monitor: return
    global sslfork_monitor_pid
    import urllib2 # don't use IOLoop for this monitoring: too confusing if we have to restart it on fork
    pid = os.fork()
    if pid:
        sslfork_monitor_pid = pid ; return
    # If background, can't double-fork (our PID is known)
    # (TODO: if profile_forks_too, there's no profile loop in this monitor (it starts only when we fork a new helper); unlikely to be useful here though)
    try: os.setpgrp() # for stop_threads0 later
    except: pass
    signal.signal(signal.SIGTERM, terminateSslForks)
    signal.signal(signal.SIGINT, terminateSslForks)
    setProcName("adjusterSSLmon") # 15 chars is max for some "top" implementations
    CrossProcessLogging.initChild("SSL") # not SSLmon because helper IDs will be appended to it also
    for i in xrange(len(sslforks_to_monitor)):
      if i==len(sslforks_to_monitor)-1: pid = 0 # don't bother to fork for the last one
      else: pid = os.fork()
      if pid: sslforks_to_monitor[i][0] = pid # for SIGTERM
      else: # child
        oldI = i
        if i < len(sslforks_to_monitor)-1:
            sslforks_to_monitor = [sslforks_to_monitor[i]]
            i = 0 # we'll monitor only one in the child
        try: urlopen = urllib2.build_opener(urllib2.ProxyHandler({})).open # don't use the system proxy if set
        except: urlopen = urllib2.urlopen # wrong version?
        while True:
            t = time.time()
            try:
                urlopen("http://localhost:%d/" % sslforks_to_monitor[i][3],timeout=sslFork_pingInterval)
                sslforks_to_monitor[i][4]=time.time()
            except: # URLError etc
              t2 = sslforks_to_monitor[i][4]
              if sslforks_to_monitor[i][0]==None or (t2 and t2 + 2*sslFork_pingInterval < time.time()):
                if restart_sslfork(i,oldI): # child
                    return lambda *args:stopServer("SIG*")
              elif not t2: sslforks_to_monitor[i][4] = time.time()
            time.sleep(max(0,t+sslFork_pingInterval-time.time()))
def restart_sslfork(n,oldN):
    global sslforks_to_monitor
    if not sslforks_to_monitor[n][0]==None: # not first time
        logging.error("Restarting SSL helper %d (old pid %d; not heard from its port %d for %d seconds)" % (oldN,sslforks_to_monitor[n][0],sslforks_to_monitor[n][3],time.time()-sslforks_to_monitor[n][4]))
        try: os.kill(sslforks_to_monitor[n][0],9)
        except OSError: logging.info("Unable to kill pid %d (already gone?)" % sslforks_to_monitor[n][0])
        try: os.waitpid(sslforks_to_monitor[n][0], os.WNOHANG) # clear it from the process table
        except OSError: pass
    # TODO: if profile_forks_too, do things with profile?
    pid = os.fork()
    if pid:
        sslforks_to_monitor[n][0] = pid
        sslforks_to_monitor[n][4] = None
    else: # child
        setProcName("adjusterSSLhelp")
        CrossProcessLogging.initChild(str(n)) # TODO: or port number?
        sslforks_to_monitor[n][1]() # main listener
        sslforks_to_monitor[n][2]() # 'still alive' listener
        sslforks_to_monitor = [] # nothing for us to check
        return True
def terminateSslForks(*args):
    "sslfork_monitor's SIGTERM handler"
    global sslforks_to_monitor
    for p,_,_,_,_ in sslforks_to_monitor:
        if p==None: continue
        try: os.kill(p,signal.SIGTERM)
        except OSError: pass # somebody might have 'killall'd them
        try: os.waitpid(p, os.WNOHANG)
        except OSError: pass
    stop_threads0()

def open_extra_ports():
    "Returns the stop function if we're now a child process that shouldn't run anything else"
    nextPort = options.port + 1
    # don't add any other ports here: NormalRequestForwarder assumes the real_proxy SSL helper will be at port+1
    # banner() must be kept in sync with these port numbers
    # All calls to sslSetup and maybe_sslfork_monitor must be made before ANY other calls to listen_on_port (as we don't yet want there to be an IOLoop instance when maybe_sslfork_monitor is called)
    if options.real_proxy: nextPort = sslSetup(lambda port=nextPort:listen_on_port(Application([(r"(.*)",SSLRequestForwarder(),{})],log_function=accessLog,gzip=False),port,"127.0.0.1",False,ssl_options={"certfile":duff_certfile()}),nextPort+1) # gzip=False because little point if we know the final client is on localhost.  A modified Application that's 'aware' it's the SSL-helper version (use SSLRequestForwarder & no need for staticDocs listener) - this will respond to SSL requests that have been CONNECT'd via the first port.
    if options.js_reproxy:
        # ditto for js_interpreter (saves having to override its user-agent, or add custom headers requiring PhantomJS 1.5+, for us to detect its connections back to us)
        global js_proxy_port
        js_proxy_port = []
        for c in xrange(cores):
          for i in xrange(js_per_core):
            # PjsRequestForwarder to be done later
            js_proxy_port.append(nextPort)
            nextPort = sslSetup(lambda port=nextPort:listen_on_port(Application([(r"(.*)",PjsSslRequestForwarder(c*js_per_core,i),{})],log_function=nullLog,gzip=False),port+1,"127.0.0.1",False,ssl_options={"certfile":duff_certfile()}),nextPort+2)
        js_proxy_port.append(nextPort-1) # highest port in use, for banner()
    if upstream_rewrite_ssl:
        # This one does NOT listen on SSL: it listens on unencrypted HTTP and rewrites .0 into outgoing SSL.  But we can still run it in a different process if ssl_fork is enabled, and this will save encountering the curl_max_clients issue as well as possibly offloading *client*-side SSL to a different CPU core (TODO: could also use Tornado's multiprocessing to multi-core the client-side SSL)
        sslSetup(lambda port=upstream_proxy_port+1:listen_on_port(Application([(r"(.*)",UpSslRequestForwarder,{})],log_function=nullLog,gzip=False),port,"127.0.0.1",False),upstream_proxy_port+2) # TODO: document upstream_proxy_port+2 needs to be reserved if options.ssl_fork and not options.upstream_proxy_host
    r = maybe_sslfork_monitor()
    if r: return r
    # NOW we can start non-sslSetup listen_on_port:
    if options.js_reproxy:
        for c in xrange(cores):
          for i in xrange(js_per_core):
            listen_on_port(Application([(r"(.*)",PjsRequestForwarder(c*js_per_core,i),{})],log_function=nullLog,gzip=False),js_proxy_port[c*js_per_core+i],"127.0.0.1",False,core=c)

def makeMainApplication():
    handlers = [(r"(.*)",NormalRequestForwarder(),{})]
    if options.staticDocs: handlers.insert(0,static_handler())
    return Application(handlers,log_function=accessLog,gzip=options.compress_responses) # TODO: gzip= deprecated in Tornado 4.x (if they remove it, we may have to check Tornado version and send either gzip= or compress_response= as appropriate, in all calls to Application)

def start_multicore(isChild=False):
    "Fork child processes, set coreNo unless isChild; parent waits and exits.  Call to this must come after unixfork if want to run in the background."
    global coreNo
    if not options.multicore:
        if not isChild: coreNo = 0
        return
    # Simplified version of Tornado fork_processes with
    # added setupRunAndBrowser (must have the terminal)
    children = set()
    for i in range(cores):
        pid = os.fork()
        if not pid:
            if not isChild: coreNo = i
            return CrossProcessLogging.initChild()
        children.add(pid)
    if not isChild:
        # Do the equivalent of setupRunAndBrowser() but without the IOLoop.  This can start threads, so must be afster the above fork() calls.
        if options.browser: runBrowser()
        if options.run: runRun()
    # Now wait for the browser or the children to exit
    # (and monitor for SIGTERM: we might be an SSLhelp)
    gotTerm = False
    def handleTerm(*_):
        global interruptReason, gotTerm
        interruptReason = "SIGTERM received by multicore helper"
        for pid in children: os.kill(pid,signal.SIGTERM)
    signal.signal(signal.SIGTERM,handleTerm)
    try:
      while children:
        try: pid, status = os.wait()
        except KeyboardInterrupt: raise # see below
        except: continue # interrupted system call OK
        if pid in children: children.remove(pid)
    except KeyboardInterrupt: pass
    try: reason = interruptReason
    except: reason = "Keyboard interrupt"
    if reason and not isChild:
        reason += ", stopping child processes"
        if options.background: logging.info(reason)
        else: sys.stderr.write(reason+"\n")
    for pid in children: os.kill(pid,signal.SIGTERM)
    while children:
        try: pid, status = os.wait()
        except KeyboardInterrupt: raise
        except: continue
        if pid in children: children.remove(pid)
    if not isChild: announceShutdown0()
    sys.exit()

def openPortsEtc():
    workaround_raspbian_IPv6_bug()
    workaround_timeWait_problem()
    early_fork = (options.ssl_fork and options.background)
    if early_fork: banner(True),unixfork()
    if options.ssl_fork: initLogging() # even if not early_fork (i.e. not background)
    stopFunc = open_extra_ports()
    if stopFunc: # we're a child process (--ssl-fork)
        assert not options.background or early_fork
        dropPrivileges()
        # can't double-fork (our PID is known), hence early_fork above
        start_multicore(True)
        if profile_forks_too: open_profile()
    else: # we're not a child process
      try:
        if options.port: listen_on_port(makeMainApplication(),options.port,options.address,options.browser)
        openWatchdog() ; dropPrivileges()
        open_upnp() # make sure package avail if needed
        if not early_fork: banner()
        if options.background and not early_fork:
            if options.js_interpreter: test_init_webdriver()
            unixfork() # MUST be before init_webdrivers (js_interpreter does NOT work if you start them before forking)
        if not options.ssl_fork: initLogging() # as we hadn't done it before (must be after unixfork)
        start_multicore()
        if not options.multicore or profile_forks_too: open_profile()
        else: open_profile_pjsOnly()
        if options.js_interpreter: init_webdrivers(coreNo*js_per_core,js_per_core)
        if not options.multicore: setupRunAndBrowser()
        watchdog.start() # ALL cores if multicore (since only one needs to be up for us to be still working) although TODO: do we want this only if not coreNo so as to ensure Dynamic_DNS_updater is still up?
        checkServer.setup() # (TODO: if we're multicore, can we propagate to other processes ourselves instead of having each core check the fasterServer?  Low priority because how often will a multicore box need a fasterServer)
        if not coreNo: Dynamic_DNS_updater()
        if options.multicore: stopFunc = lambda *_:stopServer("SIG*")
        else: stopFunc = lambda *_:stopServer("SIGTERM received")
      except SystemExit: raise # from the unixfork, OK
      except: # oops, error during startup, stop forks if any
        if not sslfork_monitor_pid == None:
          time.sleep(0.5) # (it may have only just started: give it a chance to install its signal handler)
          try: os.kill(sslfork_monitor_pid,signal.SIGTERM)
          except OSError: pass
        raise
    signal.signal(signal.SIGTERM, stopFunc)
    try: os.setpgrp() # for stop_threads0 later
    except: pass

def banner(delayed=False):
    ret = [twoline_program_name]
    if options.port:
        ret.append("Listening on port %d" % options.port)
        if (options.real_proxy or options.js_reproxy or upstream_rewrite_ssl): ret.append("with these helpers (don't connect to them yourself):")
        if options.real_proxy:
            if options.ssl_fork: ret.append("--real_proxy SSL helper on localhost:%d-%d" % (options.port+1,options.port+2))
            else: ret.append("--real_proxy SSL helper on localhost:%d" % (options.port+1))
        if options.js_reproxy:
            try: ret.append("--js_reproxy helpers on localhost:%d-%d" % (js_proxy_port[0],js_proxy_port[-1]))
            except NameError: ret.append("--js_reproxy helpers (ports to be determined)") # early_fork
        if upstream_rewrite_ssl:
            if options.ssl_fork and not (options.multicore and (options.real_proxy or options.js_reproxy)): ret.append("--upstream-proxy back-connection helper on localhost:%d-%d" % (upstream_proxy_port+1,upstream_proxy_port+2))
            else: ret.append("--upstream-proxy back-connection helper on localhost:%d" % (upstream_proxy_port+1,))
    else: ret.append("Not listening (--port=0 set)")
    if options.watchdog:
        ret.append("Writing "+options.watchdogDevice+" every %d seconds" % options.watchdog)
        if options.watchdogWait: ret.append("(abort if unresponsive for %d seconds)" % options.watchdogWait)
    if options.ssl_fork and not options.background: ret.append("To inspect processes, use: pstree "+str(os.getpid()))
    ret = "\n".join(ret)+"\n"
    if delayed: ret=ret.replace("Listening","Will listen").replace("Writing","Will write") # for --ssl-fork --background (need early fork, TODO: unless write a PID somewhere)
    sys.stderr.write(ret)
    if not options.background:
        # set window title for foreground running
        t = "adjuster"
        if "SSH_CONNECTION" in os.environ: t += "@"+hostSuffix() # TODO: might want to use socket.getfqdn() to save confusion if several servers are configured with the same host_suffix and/or host_suffix specifies multiple hosts?
        set_title(t)
coreNo = "unknown" # want it to be non-False to begin with
def announceInterrupt():
    if coreNo or options.multicore: return # silent helper process (coreNo=="unknown"), or we announce interrupts differently in multicore (see start_multicore)
    if options.background: logging.info("SIGINT received"+find_adjuster_in_traceback())
    else: sys.stderr.write("\nKeyboard interrupt"+find_adjuster_in_traceback()+"\n")
def announceShutdown():
    if coreNo or options.multicore: return # as above
    announceShutdown0()
def announceShutdown0():
    if options.background: logging.info("Server shutdown")
    else: sys.stderr.write("Adjuster shutdown\n")

def main():
    setProcName() ; readOptions() ; preprocessOptions()
    serverControl() ; openPortsEtc()
    workaround_tornado_fd_issue() ; startServers()
    try: IOLoop.instance().start()
# "There seemed a strangeness in the air,
#  Vermilion light on the land's lean face;
#  I heard a Voice from I knew not where:
#   'The Great Adjustment is taking place!'" - Thomas Hardy
    except KeyboardInterrupt: announceInterrupt()
    announceShutdown()
    for v in kept_tempfiles.values(): unlink(v)
    if watchdog: watchdog.stop()
    stop_threads() # must be last thing

def plural(number):
    if number == 1: return ""
    else: return "s"
def stop_threads():
    if not sslfork_monitor_pid == None:
        try: os.kill(sslfork_monitor_pid,signal.SIGTERM) # this should cause it to propagate that signal to the monitored PIDs
        except OSError: pass # somebody might have killall'd it
    CrossProcessLogging.shutdown()
    if not helper_thread_count: return
    msg = "Terminating %d helper thread%s" % (helper_thread_count,plural(helper_thread_count))
    # in case someone needs our port quickly.
    # Most likely "runaway" thread is ip_change_command if you did a --restart shortly after the server started.
    # TODO it would be nice if the port can be released at the IOLoop.instance.stop, and make sure os.system doesn't dup any /dev/watchdog handle we might need to release, so that it's not necessary to stop the threads
    if not options.background and not coreNo: sys.stderr.write(msg+"\n")
    stop_threads0()
def stop_threads0():
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    if options.run:
        global exitting ; exitting = True # so not restarted if options.runWait == 0
        try: os.kill(runningPid,signal.SIGTERM)
        except NameError: pass # runningPid not set
        except OSError: pass # already exitted
    os.killpg(os.getpgrp(),signal.SIGTERM)
    os.abort() # if the above didn't work, this should

def static_handler():
    url,path = options.staticDocs.split('#')
    if not url.startswith("/"): url="/"+url
    if not url.endswith("/"): url += "/"
    class OurStaticFileHandler(StaticFileHandler):
        def set_extra_headers(self,path): fixServerHeader(self)
    return (url+"(.*)",OurStaticFileHandler,{"path":path,"default_filename":"index.html"})

theServers = {}
def listen_on_port(application,port,address,browser,core="all",**kwargs):
    if not core in theServers: theServers[core] = []
    theServers[core].append(HTTPServer(application,**kwargs))
    for portTry in [5,4,3,2,1,0]:
      try: return theServers[core][-1].bind(port,address)
      except socket.error, e:
        if not "already in use" in e.strerror: raise
        # Maybe the previous server is taking a while to stop
        if portTry:
            time.sleep(0.5) ; continue
        # tried 6 times over 3 seconds, can't open the port
        if browser:
            # there's probably another adjuster instance, in which case we probably want to let the browser open a new window and let our listen() fail
            dropPrivileges()
            runBrowser()
        raise Exception("Can't open port "+repr(port)+" (tried for 3 seconds, "+e.strerror+")")

def startServers():
    for core,sList in theServers.items():
        if core == "all" or core == coreNo:
            for s in sList: s.start()

def workaround_raspbian_IPv6_bug():
    """Some versions of Raspbian apparently boot with IPv6 enabled but later don't configure it, hence tornado/netutil.py's AI_ADDRCONFIG flag is ineffective and socket.socket raises "Address family not supported by protocol" when it tries to listen on IPv6.  If that happens, we'll need to set address="0.0.0.0" for IPv4 only.  However, if we tried IPv6 and got the error, then at that point Tornado's bind_sockets will likely have ALREADY bound an IPv4 socket but not returned it; the socket does NOT get closed on dealloc, so a retry would get "Address already in use" unless we quit and re-run the application (or somehow try to figure out the socket number so it can be closed).  Instead of that, let's try to detect the situation in advance so we can set options.address to IPv4-only the first time."""
    if options.address: return # don't need to do this if we're listening on a specific address
    flags = socket.AI_PASSIVE
    if hasattr(socket, "AI_ADDRCONFIG"): flags |= socket.AI_ADDRCONFIG
    for af,socktype,proto,r1,r2 in socket.getaddrinfo(None,options.port,socket.AF_UNSPEC,socket.SOCK_STREAM,0,flags):
        try: socket.socket(af,socktype,proto)
        except socket.error, e:
            if "family not supported" in e.strerror:
                options.address = "0.0.0.0" # use IPv4 only
                return

def workaround_timeWait_problem():
    """Work around listen-port failing to bind when there are still TIME_WAIT connections from the previous run.  This at least seems to work around the problem MOST of the time."""
    if "win" in sys.platform and not sys.platform=="darwin":
        # Don't do this on MS-Windows.  It can result in
        # 'stealing' a port from another server even while
        # that other server is still running.
        return
    if not hasattr(socket, "SO_REUSEPORT"): return
    try: import tornado.netutil, inspect
    except ImportError: return
    if not 'reuse_port' in inspect.getargspec(tornado.netutil.bind_sockets).args: return # Tornado version too old
    obs = tornado.netutil.bind_sockets
    def newBind(*args,**kwargs):
        if len(args) < 6: kwargs['reuse_port'] = True
        return obs(*args,**kwargs)
    debuglog("Adding reuse_port to tornado.netutil.bind_sockets")
    tornado.netutil.bind_sockets = newBind
    # but tornado.tcpserver may have already imported it:
    try: import tornado.tcpserver
    except ImportError: pass # Tornado version too old (TODO: as above)
    debuglog("Adding reuse_port to tornado.tcpserver.bind_sockets")
    tornado.tcpserver.bind_sockets = newBind

def workaround_tornado_fd_issue():
    cxFunc = IOLoop.instance().handle_callback_exception
    def newCx(callback):
        if callback: return cxFunc(callback)
        # self._handlers[fd] raised KeyError.  This means
        # we don't want to keep being told about the fd.
        fr = sys.exc_info()[2]
        while fr.tb_next: fr = fr.tb_next
        fd = fr.tb_frame.f_locals.get("fd",None)
        if not fd: return cxFunc("callback="+repr(callback)+" and newCx couldn't get fd from stack")
        logging.info("IOLoop has no handler left for fd "+repr(fd)+" but is still getting events from it.  Attempting low-level close to avoid loop.")
        try: IOLoop.instance().remove_handler(fd)
        except: pass
        try: os.close(fd)
        except: pass
    IOLoop.instance().handle_callback_exception = newCx

def istty(): return hasattr(sys.stderr,"isatty") and sys.stderr.isatty()
def set_title(t):
  if not istty(): return
  term = os.environ.get("TERM","")
  is_xterm = "xterm" in term
  is_screen = (term=="screen" and os.environ.get("STY",""))
  is_tmux = (term=="screen" and os.environ.get("TMUX",""))
  if is_xterm or is_tmux: sys.stderr.write("\033]0;%s\007" % (t,)) # ("0;" sets both title and minimised title, "1;" sets minimised title, "2;" sets title.  Tmux takes its pane title from title (but doesn't display it in the titlebar))
  elif is_screen: os.system("screen -X title \"%s\"" % (t,))
  else: return
  if not t: return
  import atexit
  atexit.register(set_title,"")
  global can_do_ansi_colour
  can_do_ansi_colour = is_xterm or (is_screen and "VT 100/ANSI" in os.environ.get("TERMCAP","")) # used by showProfile (TODO: if profile_forks_too, we'd need to set this earlier than the call to banner / set_title in order to make it available to SSL forks etc, otherwise only the main one has purple profile output. Multicore is already OK (but does only counts per core).)
can_do_ansi_colour=False

def dropPrivileges():
    if options.user and not os.getuid():
        # need to drop privileges
        import pwd ; pwd=pwd.getpwnam(options.user)
        os.setuid(pwd[2])
        # and help our external programs:
        os.environ['HOME'] = pwd[5] # (so they don't try to load root's preferences etc)
        os.environ['USER']=os.environ['LOGNAME']=options.user

def unixfork():
    if os.fork(): sys.exit()
    os.setsid()
    if os.fork(): sys.exit()
    devnull = os.open("/dev/null", os.O_RDWR)
    for fd in range(3): os.dup2(devnull,fd) # commenting out this line will let you see stderr after the fork (TODO debug option?)
    
def stopOther():
    if not options.port: errExit("Cannot use --restart or --stop with --port=0") # because the listening port is used to identify the other process (TODO: can we have a pid file or something for the case when there are no listening ports)
    import commands,signal
    out = commands.getoutput("lsof -iTCP:"+str(options.port)+" -sTCP:LISTEN 2>/dev/null") # >/dev/null because it sometimes prints warnings, e.g. if something's wrong with Mac FUSE mounts, that won't affect the output we want. TODO: lsof can hang if ANY programs have files open on stuck remote mounts etc, even if this is nothing to do with TCP connections.  -S 2 might help a BIT but it's not a solution.  Linux's netstat -tlp needs root, and BSD's can't show PIDs.  Might be better to write files or set something in the process name.
    if out.startswith("lsof: unsupported"):
        # lsof 4.81 has -sTCP:LISTEN but lsof 4.78 does not.  However, not including -sTCP:LISTEN can cause lsof to make unnecessary hostname queries for established connections.  So fall back only if have to.
        out = commands.getoutput("lsof -iTCP:"+str(options.port)+" -Ts 2>/dev/null") # -Ts ensures will say LISTEN on the pid that's listening
        lines = filter(lambda x:"LISTEN" in x,out.split("\n")[1:])
    elif not out.strip() and not commands.getoutput("which lsof 2>/dev/null"):
        sys.stderr.write("stopOther: no 'lsof' command on this system\n")
        return False
    else: lines = out.split("\n")[1:]
    for line in lines:
        try: pid=int(line.split()[1])
        except:
            sys.stderr.write("stopOther: Can't make sense of lsof output %s\n" % repr(line))
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
            self.recent_whois.pop(0)
        self.recent_whois.append(ip)
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
    if address: logging.info("whois "+ip+": "+address)
    helper_thread_count -= 1

class NullLogger:
  def __call__(self,req): pass
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
    if req.method=="CONNECT" or req.uri.startswith("http://") or req.uri.startswith("https://"): host="" # URI will have everything
    elif hasattr(req,"suppress_logger_host_convert"): host = req.host
    else: host=convert_to_real_host(req.host,ch)
    if host in [-1,"error"]: host=req.host # -1 for own_server (but this shouldn't happen as it was turned into a CONNECT; we don't mind not logging own_server because it should do so itself)
    elif host: host=protocolWithHost(host)
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

nullLog = NullLogger()
accessLog = BrowserLogger()

def MyAsyncHTTPClient(): return AsyncHTTPClient()
def curlFinished(): pass
def setupCurl(maxCurls,error=None):
  global pycurl
  try:
    import pycurl # check it's there
    if not ('c-ares' in pycurl.version or 'threaded' in pycurl.version):
        if error: sys.stderr.write("WARNING: The libcurl on this system might hold up our main thread while it resolves DNS (try building curl with ./configure --enable-ares)\n")
        else:
            del pycurl ; return # TODO: and say 'not using'?
    if float('.'.join(pycurl.version.split()[0].split('/')[1].rsplit('.')[:2])) < 7.5:
        if error: sys.stderr.write("WARNING: The curl on this system is old and might hang when fetching certain SSL sites\n") # strace -p (myPID) shows busy looping on poll (TODO: option to not use it if we're not using upstream_proxy)
        else:
            del pycurl ; return # TODO: as above
    _oldCurl = pycurl.Curl
    def _newCurl(*args,**kwargs):
        c = _oldCurl(*args,**kwargs)
        so = c.setopt
        def mySetopt(k,v):
            so(k,v)
            if k==pycurl.PROXY: so(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_0) # workaround 599 "transfer closed with outstanding read data remaining" in Curl 7.55.1 with polipo2 as upstream proxy (TODO: curl-version dependent? 7.43.0 seemed OK in this aspect, although it had the above problem)
        c.setopt = mySetopt
        return c
    pycurl.Curl = _newCurl
    curl_max_clients = min(max(maxCurls,10),1000) # to work around Tornado issue 2127, and we'll warn about the issue ourselves if we go over:
    curl_inUse_clients = 0
    try: AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient",max_clients=curl_max_clients)
    except: AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient") # will try in MyAsyncHTTPClient too (different versions of Tornado and all that...)
    try: HTTPClient.configure("tornado.curl_httpclient.CurlHTTPClient") # for WSGI
    except: pass # not all Tornado versions support configure on HTTPClient, and we still want to define the following if AsyncHTTPClient.configure worked
    def MyAsyncHTTPClient():
        try: problem = not len(AsyncHTTPClient()._free_list)
        except:
            global curl_inUse_clients
            curl_inUse_clients += 1
            problem = curl_inUse_clients >= curl_max_clients
        if problem:
            if upstream_rewrite_ssl and not options.ssl_fork: logging.error("curl_max_clients too low; AsyncHTTPClient will queue requests and COULD DEADLOCK due to upstream_rewrite_ssl (try --ssl-fork if you can't increase curl_max_clients)")
            else: logging.info("curl_max_clients too low; AsyncHTTPClient will queue requests")
        try: return AsyncHTTPClient(max_clients=curl_max_clients)
        except: return AsyncHTTPClient()
    def curlFinished(): # for callbacks to call
        global curl_inUse_clients
        curl_inUse_clients -= 1
        if curl_inUse_clients < 0:
            # This shouldn't happen.  But if it does, don't let the effect 'run away'.
            curl_inUse_clients = 0
  except: # fall back to the pure-Python one
      if error: errExit(error) # (unless it won't do)

try:
    import zlib
    enable_gzip = True # for fetching remote sites
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

debug_connections = False
def myRepr(d):
    if re.search("[\x00-\x09\x0e-\x1f]",d): return "%d bytes" % len(d)
    elif len(d) >= 512: return repr(d[:500]+"...")
    else: return repr(d)
def peerName(socket):
    try: return socket.getpeername()
    except: return "(no socket??)"
def writeAndClose(stream,data):
    # This helper function is needed for CONNECT and own_server handling because, contrary to Tornado docs, some Tornado versions (e.g. 2.3) send the last data packet in the FIRST callback of IOStream's read_until_close
    if data:
        if debug_connections: print "Writing",myRepr(data),"to",peerName(stream.socket),"and closing it"
        try: stream.write(data,lambda *args:True)
        except: pass # ignore errors like client disconnected
    if not stream.closed():
        try: stream.close()
        except: pass
def writeOrError(name,stream,data):
    if debug_connections: print "Writing",myRepr(data),"to",peerName(stream.socket)
    try: stream.write(data)
    except:
        if name: logging.error("Error writing data to "+name)

# Domain-setting cookie for when we have no wildcard_dns and no default_site:
adjust_domain_cookieName = "_adjusterDN_"
adjust_domain_none = "0" # not a valid top-level domain (TODO hopefully no user wants this as a local domain...)
enable_adjustDomainCookieName_URL_override = True # TODO: document this!  (Allow &_adjusterDN_=0 or &_adjusterDN_=wherever in bookmark URLs, so it doesn't matter what setting the cookie has when the bookmark is activated)

seen_ipMessage_cookieName = "_adjusterIPM_"

htmlmode_cookie_name = "_adjustZJCG_" # zap JS, CSS and Graphics
password_cookie_name = "_pxyAxsP_" # "proxy access password". have to pick something that's unlikely to collide with a site's cookie
webdriver_click_code = "._adjustPJSC_"

redirectFiles_Extensions=set("pdf epub mp3 aac zip gif png jpeg jpg exe tar tgz tbz ttf woff swf txt doc rtf midi mid wav ly c h py".split()) # TODO: make this list configurable + maybe add a "minimum content length before it's worth re-directing" option

class HTTPClient_Fixed(HTTPClient):
    def __init__(self,*args):
        self._closed = True # so don't get error in 'del' if have to catch an exception in the constructor
        HTTPClient.__init__(self,*args)
wsgi_mode = False
def httpfetch(url,**kwargs):
    url = re.sub("[^ -~]+",lambda m:urllib.quote(m.group()),url) # sometimes needed to get out of redirect loops
    if not wsgi_mode:
        return MyAsyncHTTPClient().fetch(url,**kwargs)
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
        r = None
        try: resp = urllib2.urlopen(req,timeout=60)
        except urllib2.HTTPError, e: resp = e
        except Exception, e: resp = r = wrapResponse(e) # could be anything, especially if urllib2 has been overridden by a 'cloud' provider
        if r==None: r = wrapResponse(resp.read(),resp.info(),resp.getcode())
    callback(r)
def wrapResponse(body,info={},code=500):
    "Makes a urllib2 response or an error message look like an HTTPClient response.  info can be a headers dict or a resp.info() object."
    class Empty: pass
    r = Empty()
    r.code = code
    class H:
        def __init__(self,info): self.info = info
        def get(self,h,d): return self.info.get(h,d)
        def get_all(self):
            if type(self.info)==dict:
                return self.info.items()
            if hasattr(self.info,"headers"):
                return [h.replace('\n','').split(': ',1) for h in self.info.headers]
            else: return self.info.get_all()
    r.headers = H(info) ; r.body = body ; return r

class WebdriverWrapper:
    "Wrapper for webdriver that might or might not be in a separate process without shared memory"
    def __init__(self): self.theWebDriver = None
    def new(self,*args):
        self.theWebDriver = get_new_webdriver(*args)
    def quit(self,*args):
        if not self.theWebDriver: return
        try: pid = self.theWebDriver.service.process.pid
        except: pid = None # TODO: log?
        try: self.theWebDriver.quit()
        except: pass # e.g. sometimes get 'bad fd' in selenium's send_remote_shutdown_command _cookie_temp_file_handle
        # Try zapping the process ourselves anyway (even if theWebDriver.quit DIDN'T return error: seems it's sometimes still left around.  TODO: this could have unexpected consequences if the system's pid-reuse rate is excessively high.)
        self.theWebDriver = None
        if not pid: return
        try: os.killpg(pid,9)
        except OSError: pass # maybe it's not a process group
        try: import psutil
        except ImportError: pass
        try:
            for c in psutil.Process(pid).children(recursive=True):
                try: c.kill(9)
                except: pass
        except: pass
        try: os.kill(pid,9)
        except OSError: pass
        try: os.waitpid(pid, os.WNOHANG) # clear it from the process table
        except OSError: pass
    def current_url(self):
        try: return self.theWebDriver.current_url
        except: return "" # PhantomJS Issue #13114: unconditional reload for now
    def get(self,url):
        self.theWebDriver.get(url)
        if options.logDebug:
          try:
            for e in self.theWebDriver.get_log('browser'):
                print "webdriver log:",e['message']
          except: print "webdriver log exception"
    def execute_script(self,script): self.theWebDriver.execute_script(script)
    def click_id(self,clickElementID): self.theWebDriver.find_element_by_id(clickElementID).click()
    def click_xpath(self,xpath): self.theWebDriver.find_element_by_xpath(xpath).click()
    def click_linkText(self,clickLinkText): self.theWebDriver.find_element_by_link_text(clickLinkText).click()
    def getu8(self): return self.theWebDriver.find_element_by_xpath("//*").get_attribute("outerHTML").encode('utf-8')
    def getpng(self): return self.theWebDriver.get_screenshot_as_png()
try: from selenium.common.exceptions import TimeoutException
except: # no Selenium or wrong version
    class TimeoutException: pass # placeholder
def webdriverWrapper_receiver(pipe):
    "Command receiver for WebdriverWrapper for when it's running over IPC.  Receives (command,args) and sends (return,exception)."
    setProcName("adjusterWDhelp")
    CrossProcessLogging.initChild()
    try: w = WebdriverWrapper()
    except KeyboardInterrupt: return
    def raiseTimeout(*args): raise TimeoutException()
    try: signal.signal(signal.SIGALRM, raiseTimeout)
    except: pass # SIGALRM may be Unix-only
    while True:
        try: cmd,args = pipe.recv()
        except KeyboardInterrupt:
            try: w.quit()
            except: pass
            pipe.send(("INT","INT"))
            return pipe.close()
        if cmd=="EOF": return pipe.close()
        try:
          try: signal.alarm(100) # as a backup: if Selenium timeout somehow fails, don't let this process get stuck forever (can do this only when js_multiprocess or we won't know what thread gets it)
          except: pass # alarm() is Unix-only
          try: ret,exc = getattr(w,cmd)(*args), None
          except Exception, e:
              p = find_adjuster_in_traceback()
              if p: # see if we can add it to the message:
                try:
                    if type(e.args[0])==str: e.args=(repr(e.args[0])+p,) + tuple(e.args[1:]) # should work with things like httplib.BadStatusLine that are fussy about the number of arguments they get
                    else: e.args += (p,) # works with things like KeyError (although so should the above)
                except: e.message += p # works with base Exception
              ret,exc = None,e
          try: signal.alarm(0)
          except: pass # Unix-only
        except Exception, e: ret,exc = None,e # e.g. if 1st 'except' block catches a non-sigalarm exception but then the alarm goes off while it's being handled
        try: pipe.send((ret,exc))
        except: pass # if they closed it, we'll get EOFError on next iteration
def webdriverWrapper_send(pipe,cmd,args=()):
    "Send a command to a Webdriverwrapper over IPC, and either return its result or raise its exception in this process."
    try: pipe.send((cmd,args))
    except IOError: return # already closed
    if cmd=="EOF": return pipe.close() # no return code
    ret,exc = pipe.recv()
    if ret==exc=="INT": return pipe.close()
    if exc: raise exc
    else: return ret
class WebdriverWrapperController:
    "Proxy for WebdriverWrapper if it's running over IPC"
    def __init__(self):
        self.pipe, cPipe = multiprocessing.Pipe()
        multiprocessing.Process(target=webdriverWrapper_receiver,args=(cPipe,)).start()
    def send(self,cmd,args=()): return webdriverWrapper_send(self.pipe,cmd,args)
    def new(self,*args): self.send("new",args)
    def quit(self,final=False):
        self.send("quit")
        if final: self.send("EOF")
    def current_url(self): return self.send("current_url")
    def get(self,url): return self.send("get",(url,))
    def execute_script(self,script): self.send("execute_script",(script,))
    def click_id(self,clickElementID): self.send("click_id",(clickElementID,))
    def click_xpath(self,xpath): self.send("click_xpath",(xpath),)
    def click_linkText(self,clickLinkText): self.send("click_linkText",(clickLinkText,))
    def getu8(self): return self.send("getu8")
    def getpng(self): return self.send("getpng")
try: import multiprocessing # Python 2.6
except: multiprocessing = None
class WebdriverRunner:
    "Manage a WebdriverWrapperController (or a WebdriverWrapper if we're not using IPC) from a thread of the main process"
    def __init__(self,start=0,index=0):
        self.start,self.index = start,index
        self.thread_running = False
        if options.js_multiprocess:
            self.wrapper = WebdriverWrapperController()
        else: self.wrapper = WebdriverWrapper()
        self.renew_webdriver(True)
    def renew_webdriver(self,firstTime=False):
        "Async if called from main thread; sync if called from our thread (i.e. inside fetch)"
        if not self.thread_running:
            self.thread_running = True
            threading.Thread(target=_renew_wd,args=(self,firstTime)).start() ; return
        self.wrapper.quit()
        self.wrapper.new(self.start+self.index,not firstTime)
        self.usageCount = 0 ; self.maybe_stuck = False
    def quit_webdriver(self): self.wrapper.quit(final=True)
    def fetch(self,url,prefetched,clickElementID,clickLinkText,asScreenshot,callback):
        assert not self.thread_running, "webdriver_checkServe did WHAT?"
        self.thread_running = True ; self.maybe_stuck = False
        threading.Thread(target=wd_fetch,args=(url,prefetched,clickElementID,clickLinkText,asScreenshot,callback,self)).start()
    def current_url(self): return self.wrapper.current_url()
    def get(self,url): self.wrapper.get(url)
    def execute_script(self,script): self.wrapper.execute_script(script)
    def click_id(self,clickElementID): self.wrapper.click_id(clickElementID)
    def click_xpath(self,xpath): self.wrapper.click_xpath(xpath)
    def click_linkText(self,clickLinkText): self.wrapper.click_linkText(clickLinkText)
    def getu8(self): return self.wrapper.getu8()
    def getpng(self): return self.wrapper.getpng()
def _renew_wd(wd,firstTime):
    wd.renew_webdriver(firstTime)
    wd.thread_running = False
    IOLoop.instance().add_callback(webdriver_checkServe)
def find_adjuster_in_traceback():
    l = traceback.extract_tb(sys.exc_info()[2]) # must do this BEFORE the following try: (it'll overwrite it even when except: block has finished)
    try: p = sys.exc_info()[1].args[-1]
    except: p = ""
    if "adjuster line" in p: return p # for webdriverWrapper_receiver
    for i in xrange(len(l)-1,-1,-1):
        if "adjuster.py" in l[i][0]: return ", adjuster line "+str(l[i][1])
    return ""
def wd_fetch(url,prefetched,clickElementID,clickLinkText,asScreenshot,callback,manager):
    global helper_thread_count
    helper_thread_count += 1
    need_restart = False
    def errHandle(error,extraMsg,prefetched):
        if not options.js_fallback: prefetched=None
        if prefetched: toRet = "non-webdriver page"
        else: toRet = "error"
        logging.error(extraMsg+" returning "+toRet)
        global webdriver_oops
        webdriver_oops += 1
        if prefetched: return prefetched
        else: return wrapResponse("webdriver "+error)
    try: r = _wd_fetch(manager,url,prefetched,clickElementID,clickLinkText,asScreenshot)
    except TimeoutException: r = errHandle("timeout","webdriver "+str(manager.index)+" timeout fetching "+url+find_adjuster_in_traceback()+"; no partial result, so",prefetched)
    except:
        if options.js_retry:
            logging.info("webdriver error fetching "+url+" ("+repr(sys.exc_info()[:2])+find_adjuster_in_traceback()+"); restarting webdriver "+str(manager.index)+" for retry") # usually a BadStatusLine
            manager.renew_webdriver()
            try: r = _wd_fetch(manager,url,prefetched,clickElementID,clickLinkText,asScreenshot)
            except:
                r = errHandle("error","webdriver error on "+url+" even after restart, so re-restarting and",prefetched)
                need_restart = True
        else: # no retry
            r = errHandle("error","webdriver error on "+url+", so restarting and",prefetched)
            need_restart = True
    IOLoop.instance().add_callback(lambda *args:callback(r))
    manager.usageCount += 1
    if need_restart or (options.js_restartAfter and manager.usageCount >= options.js_restartAfter): manager.renew_webdriver()
    else: manager.finishTime = time.time()
    manager.thread_running = manager.maybe_stuck = False
    IOLoop.instance().add_callback(webdriver_checkServe)
    helper_thread_count -= 1
def _wd_fetch(manager,url,prefetched,clickElementID,clickLinkText,asScreenshot): # single-user only! (and relies on being called only in htmlOnlyMode so leftover Javascript is removed and doesn't double-execute on JS-enabled browsers)
    import tornado.httputil
    currentUrl = manager.current_url()
    if prefetched or not re.sub('#.*','',currentUrl) == url:
        if prefetched:
            debuglog("webdriver %d get about:blank" % manager.index)
            manager.get("about:blank") # ensure no race condition with current page's XMLHttpRequests
            webdriver_prefetched[manager.index] = prefetched
        webdriver_inProgress[manager.index].clear() # race condition with start of next 'get' if we haven't done about:blank, but worst case is we'll wait a bit too long for page to finish
        debuglog(("webdriver %d get " % manager.index)+url)
        try: manager.get(url) # waits for onload
        except: # possibly a timeout; did we get some of it?
            currentUrl = manager.current_url()
            if not currentUrl==url: # didn't get any
                debuglog("webdriver %d .get exception; currentUrl=%s so re-raising" % (manager.index,repr(currentUrl)))
                raise
            debuglog("Ignoring webdriver exception because it seems we did get something")
        # + we want to double-check XMLHttpRequests have gone through (TODO: low-value setTimeout as well?)
        debuglog("webdriver %d loaded" % manager.index)
        if options.js_reproxy:
          wasActive = True
          for _ in xrange(40): # up to 8+ seconds in steps of 0.2 (on top of the inital load)
            time.sleep(0.2) # unconditional first-wait hopefully long enough to catch XMLHttpRequest delayed-send, very-low-value setTimeout etc, but we don't want to wait a whole second if the page isn't GOING to make any requests (TODO: monitor the js going through the upstream proxy to see if it contains any calls to this? but we'll have to deal with js_interpreter's cache, unless set it to not cache and we cache upstream)
            active = webdriver_inProgress[manager.index]
            if not active and not wasActive: break # TODO: wait longer than 0.2-0.4 to see if it restarts another request?
            wasActive = active
        else: time.sleep(1) # can't do much if we're not reproxying, so just sleep 1sec and hope for the best
        currentUrl = None
    if clickElementID or clickLinkText:
      try:
        manager.execute_script("window.open = window.confirm = function(){return true;}") # in case any link has a "Do you really want to follow this link?" confirmation (webdriver default is usually Cancel), or has 'pop-under' window (TODO: switch to pop-up?)
        if clickElementID: manager.click_id(clickElementID)
        if clickLinkText:
            if not '"' in clickLinkText: manager.click_xpath(u'//a[text()="'+clickLinkText+'"]')
            elif not "'" in clickLinkText: manager.click_xpath(u"//a[text()='"+clickLinkText+"']")
            else: manager.click_linkText(clickLinkText) # least reliable
        time.sleep(0.2) # TODO: more? what if the click results in fetching a new URL, had we better wait for XMLHttpRequests to finish?  (loop as above but how do we know when they've started?)  currentUrl code below should at least show us the new URL even if it hasn't finished loading, and then there's a delay while the client browser is told to fetch it, but that might not be enough
      except: debuglog("js_links find_element exception ignored",False)
      currentUrl = None
    if currentUrl == None: # we need to ask for it again
        currentUrl = manager.current_url()
        if not currentUrl: currentUrl = url # PhantomJS Issue #13114: relative links after a redirect are not likely to work now
    if currentUrl == "about:blank":
        debuglog("got about:blank instead of "+url)
        return wrapResponse("webdriver failed to load") # rather than an actual redirect to about:blank, which breaks some versions of Lynx
    debuglog("Getting data from webdriver %d (current_url=%s)" % (manager.index,currentUrl))
    if not re.sub('#.*','',currentUrl) == url and not asScreenshot: # redirected (but no need to update local browser URL if all they want is a screenshot, TODO: or view source; we have to ignore anything after a # in this comparison because we have no way of knowing (here) whether the user's browser already includes the # or not: might send it into a redirect loop)
        return wrapResponse('<html lang="en"><body><a href="%s">Redirect</a></body></html>' % manager.current_url().replace('&','&amp;').replace('"','&quot;'),tornado.httputil.HTTPHeaders.parse("Location: "+manager.current_url()),302)
    if asScreenshot: return wrapResponse(manager.getpng(),tornado.httputil.HTTPHeaders.parse("Content-type: image/png"),200)
    else: return wrapResponse(get_and_remove_httpequiv_charset(manager.getu8())[1],tornado.httputil.HTTPHeaders.parse("Content-type: text/html; charset=utf-8"),200)
def check_jsInterpreter_valid():
    if options.js_interpreter and not options.js_interpreter in ["PhantomJS","HeadlessChrome","HeadlessFirefox"]: errExit("js_interpreter (if set) must be PhantomJS, HeadlessChrome or HeadlessFirefox")
    if options.js_reproxy and options.js_interpreter in ["HeadlessChrome","HeadlessFirefox"]: errExit("HeadlessChrome and HeadlessFirefox currently require --js_reproxy=False due to Chromium bug 721739 and a similar issue with Firefox; you'll still need to use PhantomJS for production") # (unless you don't ever want to fetch any SSL, or TODO: upstream-proxy rewrite SSL to non-SSL w/out changing domain (http://domain:443 or sthg??) but it could go wrong if miss some rewrites)
def get_new_webdriver(index,renewing=False):
    if options.js_interpreter == "HeadlessChrome":
        return get_new_HeadlessChrome(index,renewing)
    elif options.js_interpreter == "HeadlessFirefox":
        return get_new_HeadlessFirefox(index,renewing)
    else: return get_new_PhantomJS(index,renewing)
def get_new_HeadlessChrome(index,renewing):
    log_complaints = (index==0 and not renewing)
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    if options.js_reproxy:
        opts.add_argument("--proxy-server=127.0.0.1:%d" % js_proxy_port[index])
        opts.add_argument("--allow-insecure-localhost") # TODO: does this work for proxies, not just localhost as a domain? and requires Chrome 62+ (not 59)
        # opts.add_argument("--ignore-certificate-errors") # dropped before headless started in Chrome 59?
    elif options.upstream_proxy: opts.add_argument('--proxy-server='+options.upstream_proxy)
    if options.logDebug: opts.add_argument("--verbose")
    if options.js_UA and not options.js_UA.startswith("*"): opts.add_argument("--user-agent="+options.js_UA)
    if not options.js_images: opts.add_experimental_option("prefs",{"profile.managed_default_content_settings.images":2})
    # TODO: do we need to disable Javascript's ability to open new windows and tabs, plus target="_blank" etc, especially if using clickElementID?
    if options.via and not options.js_reproxy and log_complaints: sys.stderr.write("Warning: --via ignored when running HeadlessChrome without --js-reproxy\n") # unless you want to implement a Chrome extension to do it
    if "x" in options.js_size:
        w,h = options.js_size.split("x",1)
    else: w,h = options.js_size,768
    try: w,h = int(w),int(h)
    except: w,h = 0,0
    if not (w and h):
        if log_complaints: sys.stderr.write("Unrecognised size '%s', using 1024x768\n" % options.js_size)
        w,h = 1024,768
    opts.add_argument("--window-size=%d,%d" % (w,h))
    debuglog("Instantiating webdriver.Chrome")
    while True:
        try: p = webdriver.Chrome(chrome_options=opts)
        except:
            if log_complaints: raise
            logging.error("Unhandled exception when instantiating webdriver %d, retrying in 5sec" % index)
            time.sleep(5) ; p = None
        if p: break
    debuglog("webdriver.Chrome instantiated")
    try: p.set_page_load_timeout(30) # TODO: configurable?
    except: logging.info("Couldn't set HeadlessChrome page load timeout")
    return p
def get_new_HeadlessFirefox(index,renewing):
    os.environ['MOZ_HEADLESS'] = '1' # in case -headless not yet working
    from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
    profile = FirefoxProfile()
    log_complaints = (index==0 and not renewing) ; op = None
    if options.js_reproxy: profile.set_proxy("127.0.0.1:%d" % js_proxy_port[index]) # TODO: any way to ignore certs ?
    elif options.upstream_proxy: profile.set_proxy(options.upstream_proxy)
    if options.js_UA and not options.js_UA.startswith("*"): profile.set_preference("general.useragent.override",options.js_UA)
    if not options.js_images: profile.set_preference("permissions.default.image", 2)
    if options.via and not options.js_reproxy and log_complaints: sys.stderr.write("Warning: --via ignored when running HeadlessFirefox without --js-reproxy\n") # unless you want to implement a Firefox extension to do it
    # TODO: do any other options need to be set?  disable plugins, Firefox-update prompts, new windows/tabs with JS, etc?  or does Selenium do that?
    if options.logDebug: binary=FirefoxBinary(log_file=sys.stderr) # TODO: support logDebug to a file as well
    else: binary=FirefoxBinary()
    binary.add_command_line_options('-headless')
    binary.add_command_line_options('-no-remote')
    if "x" in options.js_size: binary.add_command_line_options("-width",options.js_size.split("x")[0],"-height",options.js_size.split("x")[1])
    elif options.js_size: binary.add_command_line_options("-width",options.js_size)
    debuglog("Instantiating webdriver.Firefox")
    while True:
        import selenium.webdriver.firefox.firefox_profile
        try: p = webdriver.Firefox(firefox_profile=profile,firefox_binary=binary)
        except:
            if log_complaints: raise
            logging.error("Unhandled exception when instantiating webdriver %d, retrying in 5sec" % index)
            time.sleep(5) ; p = None
        if p: break
    debuglog("webdriver.Firefox instantiated")
    try: p.set_page_load_timeout(30) # TODO: configurable?
    except: logging.info("Couldn't set HeadlessFirefox page load timeout")
    return p
def _get_new_PhantomJS(index,renewing):
    log_complaints = (index==0 and not renewing)
    sa = ['--ssl-protocol=any']
    # if options.logDebug: sa.append("--debug=true") # doesn't work: we don't see the debug output on stdout or stderr
    if options.js_reproxy:
        sa.append('--ignore-ssl-errors=true')
        sa.append('--proxy=127.0.0.1:%d' % js_proxy_port[index])
    elif options.upstream_proxy: sa.append('--proxy='+options.upstream_proxy)
    try: from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    except:
        if log_complaints:
            sys.stderr.write("Your Selenium installation is too old to set PhantomJS custom options.\n")
            if options.js_reproxy: sys.stderr.write("This means --js_reproxy won't work.") # because we can't set the UA string or custom headers
        if options.js_reproxy:
            sa.pop()
            if options.upstream_proxy: sa.append('--proxy='+options.upstream_proxy)
        return webdriver.PhantomJS(service_args=sa)
    dc = dict(DesiredCapabilities.PHANTOMJS)
    if options.js_UA and not options.js_UA.startswith("*"): dc["phantomjs.page.settings.userAgent"]=options.js_UA
    if not options.js_images: dc["phantomjs.page.settings.loadImages"]=False
    dc["phantomjs.page.settings.javascriptCanOpenWindows"]=dc["phantomjs.page.settings.javascriptCanCloseWindows"]=False # TODO: does this cover target="_blank" in clickElementID etc (which could have originated via DOM manipulation, so stripping them on the upstream proxy is insufficient; close/restart the driver every so often?)
    if options.via and not options.js_reproxy: dc["phantomjs.page.customHeaders.Via"]="1.0 "+convert_to_via_host("")+" ("+viaName+")" # customHeaders works in PhantomJS 1.5+ (TODO: make it per-request so can include old Via headers & update protocol version, via_host + X-Forwarded-For; will webdriver.DesiredCapabilities.PHANTOMJS[k]=v work before a request?) (don't have to worry about this if js_reproxy)
    debuglog("Instantiating webdriver.PhantomJS "+' '.join(sa))
    while True:
        try: p = webdriver.PhantomJS(desired_capabilities=dc,service_args=sa)
        except:
            if log_complaints: raise
            logging.error("Unhandled exception when instantiating webdriver %d, retrying in 5sec" % index)
            time.sleep(5) ; p = None
        if p: break
    debuglog("webdriver.PhantomJS instantiated")
    return p
def get_new_PhantomJS(index,renewing=False):
    wd = _get_new_PhantomJS(index,renewing)
    log_complaints = (index==0 and not renewing)
    if log_complaints and not options.js_reproxy:
     try: is_v2 = wd.capabilities['version'].startswith("2.")
     except: is_v2 = False
     if is_v2: sys.stderr.write("\nWARNING: You may be affected by PhantomJS issue #13114.\nRelative links may be wrong after a redirect if the site sets Content-Security-Policy.\nTry --js_reproxy, or downgrade your PhantomJS to version 1.9.8\n\n")
    if "x" in options.js_size:
        w,h = options.js_size.split("x",1)
    else: w,h = options.js_size,768
    try: w,h = int(w),int(h)
    except: w,h = 0,0
    if not (w and h):
        if log_complaints: sys.stderr.write("Unrecognised size '%s', using 1024x768\n" % options.js_size)
        w,h = 1024,768
    try: wd.set_window_size(w, h)
    except: logging.info("Couldn't set PhantomJS window size")
    try: wd.set_page_load_timeout(30) # TODO: configurable?
    except: logging.info("Couldn't set PhantomJS page load timeout")
    return wd
webdriver_runner = [] ; webdriver_prefetched = []
webdriver_via = []
webdriver_inProgress = [] ; webdriver_queue = []
webdriver_lambda = webdriver_mu = webdriver_oops = 0
def test_init_webdriver():
    "Check that we CAN start a webdriver, before forking to background and starting all of them"
    sys.stderr.write("Checking webdriver configuration... ")
    get_new_webdriver(0).quit()
    sys.stderr.write("OK\n")
def init_webdrivers(start,N):
    informing = not options.background and not start and not (options.multicore and options.ssl_fork) # (if ssl_fork, we don't want the background 'starting N processes' messages to be interleaved with this)
    if informing:
        sys.stderr.write("Starting %d webdriver%s... " % (options.js_instances,plural(options.js_instances)))
    for i in xrange(N):
        webdriver_runner.append(WebdriverRunner(start,len(webdriver_runner)))
        webdriver_prefetched.append(None)
        webdriver_inProgress.append(set())
        webdriver_via.append(None)
    def quit_wd(*args):
      if informing: sys.stderr.write("Quitting %d webdriver%s... " % (options.js_instances,plural(options.js_instances)))
      try:
        for i in webdriver_runner:
            try: i.quit_webdriver()
            except: pass
      except: pass
      if informing: sys.stderr.write("done\n")
    import atexit ; atexit.register(quit_wd)
    if options.js_restartMins and not options.js_restartAfter==1: IOLoop.instance().add_timeout(time.time()+60,webdriver_checkRenew)
    if informing: sys.stderr.write("done\n")
webdriver_maxBusy = 0
def webdriver_checkServe(*args):
    # how many queue items can be served right now?
    global webdriver_maxBusy
    webdriver_maxBusy = max(webdriver_maxBusy,sum(1 for i in webdriver_runner if i.thread_running))
    for i in xrange(len(webdriver_runner)):
        if not webdriver_runner[i].thread_running:
            if not webdriver_queue: return
            while True:
                url,prefetched,clickElementID,clickLinkText,via,asScreenshot,callback,tooLate = webdriver_queue.pop(0)
                if not tooLate(): break
                if not webdriver_queue: return
            debuglog("Starting fetch of "+url+" on webdriver instance "+str(i+webdriver_runner[i].start))
            webdriver_via[i]=via
            webdriver_runner[i].fetch(url,prefetched,clickElementID,clickLinkText,asScreenshot,callback)
            global webdriver_mu ; webdriver_mu += 1
    if webdriver_queue: debuglog("All of this core's js_instances are busy; %d items still in queue" % len(webdriver_queue))
def webdriver_checkRenew(*args):
    for i in webdriver_runner:
        if not i.thread_running and i.usageCount and i.finishTime + options.js_restartMins < time.time(): i.renew_webdriver()
    IOLoop.instance().add_timeout(time.time()+60,webdriver_checkRenew)
def webdriver_fetch(url,prefetched,clickElementID,clickLinkText,via,asScreenshot,callback,tooLate):
    if tooLate(): return # probably webdriver_queue overload (which will also be logged)
    elif prefetched and prefetched.code >= 500: return callback(prefetched) # don't bother allocating a webdriver if we got a timeout or DNS error or something
    elif wsgi_mode: return callback(_wd_fetch(webdriver_runner[0],url,prefetched,clickElementID,clickLinkText,asScreenshot)) # TODO: if *threaded* wsgi, index 0 might already be in use (we said threadsafe:true in AppEngine instructions but AppEngine can't do js_interpreter anyway; where else might we have threaded wsgi?  js_interpreter really is better run in non-wsgi mode anyway, so can js_reproxy)
    webdriver_queue.append((url,prefetched,clickElementID,clickLinkText,via,asScreenshot,callback,tooLate))
    global webdriver_lambda ; webdriver_lambda += 1
    debuglog("webdriver_queue len=%d after adding %s" % (len(webdriver_queue),url))
    webdriver_checkServe()

def fixServerHeader(i):
    i.set_header("Server",serverName) # TODO: in "real" proxy mode, "Server" might not be the most appropriate header to set for this
    try: i.clear_header("Date") # Date is added by Tornado 3; HTTP 1.1 says it's mandatory but then says don't put it if you're a clockless server (which we might be I suppose) so it seems leaving it out is OK especially if not specifying Age etc, and leaving it out saves bytes.  But if the REMOTE server specifies a Date then we should probably pass it on (see comments in doResponse below)
    except: pass # (ok if "Date" wasn't there)

rmServerHeaders = set([
    # server headers to remove.  We'll do our own connection type etc (but don't include "Date" in this list: if the remote server includes a Date it would be useful to propagate that as a reference for its Age headers etc, TODO: unless remote server is broken? see also comment in fixServerHeader re having no Date by default).  Many servers' Content-Location is faulty; it DOESN'T necessarily provide the new base href; it might be relative; it might be identical to the actual URL fetched; many browsers ignore it anyway
    "connection","content-length","content-encoding","transfer-encoding","etag","content-md5","server","alternate-protocol","strict-transport-security","content-location",
    "x-associated-content", # should NOT be sent to browser (should be interpreted by a server's SPDY/push module) but somebody might misread the specs (at least one Wikipedia editor did)
    "x-host","x-http-reason", # won't necessarily be the same
    "content-security-policy","x-webkit-csp","x-content-security-policy", # sorry but if we're adjusting the site by adding our own scripts/styles we are likely to be broken by a CSP that restricts which of these we're allowed to do. (Even if we adjust the domains listed on those headers, what if our scripts rely on injecting inline code?)  Sites shouldn't *depend* on CSP to prevent XSS: it's just a belt-and-braces that works only in recent browsers.  Hopefully our added styles etc will break the XSS-introduced ones if we hit a lazy site.
    "vary", # we modify this (see code)
    "alt-svc",
])
# TODO: WebSocket (and Microsoft SM) gets the client to say 'Connection: Upgrade' with a load of Sec-WebSocket-* headers, check what Tornado does with that
rmClientHeaders = ['Connection','Proxy-Connection','Accept-Charset','Accept-Encoding','X-Forwarded-Host','X-Forwarded-Port','X-Forwarded-Server','X-Forwarded-Proto','X-Request-Start','TE','Upgrade',
                   'Upgrade-Insecure-Requests', # we'd better remove this from the client headers if we're removing Content-Security-Policy etc from the server's
                   'Range', # TODO: we can pass Range to remote server if and only if we guarantee not to need to change anything  (could also add If-Range and If-None-Match to the list, but these should be harmless to pass to the remote server and If-None-Match might actually help a bit in the case where the document doesn't change)
]

dryrun_upstream_rewrite_ssl = False # for debugging

class RequestForwarder(RequestHandler):
    
    def get_error_html(self,status,**kwargs): return htmlhead("Web Adjuster error")+options.errorHTML+"</body></html>"
    def write_error(self,status,**kwargs):
        msg = self.get_error_html(status,**kwargs)
        if "{traceback}" in msg and 'exc_info' in kwargs:
            msg = msg.replace("{traceback}","<pre>"+ampEncode("".join(traceback.format_exception(*kwargs["exc_info"])))+"</pre>")
            # TODO: what about substituting for {traceback} on pre-2.1 versions of Tornado that relied on get_error_html and put the error into sys.exc_info()?  (need to check their source to see how reliable the traceback is in this case; post-2.1 versions re-raise it from write_error itself)
        if self.canWriteBody(): self.write(msg)
        self.finish()

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
        # - and in js_interpreter mode, recognise .screenshot too and return "screenshot", also (webdriver_click_code + .*)
        toRemove = ret = None
        if options.js_interpreter and options.js_links and webdriver_click_code in self.request.uri:
            toRemove = self.request.uri[self.request.uri.index(webdriver_click_code):]
            ret2 = urllib.unquote(toRemove[len(webdriver_click_code):])
        elif not options.viewsource: return False
        else: ret2 = None
        if self.request.uri.endswith(".viewsource"):
            if toRemove: ret2 = ret2[:-len(".viewsource")]
            else: toRemove = ".viewsource"
            ret = True
        elif options.js_interpreter and self.request.uri.endswith(".screenshot"):
            if toRemove: ret2 = ret2[:-len(".screenshot")]
            else: toRemove = ".screenshot",
            ret = "screenshot"
        elif not toRemove: return False
        if ret2: ret = (ret2,ret)
        self.request.uri = self.request.uri[:-len(toRemove)]
        if not self.request.method.lower() in ['get','head']: return ret # TODO: unless arguments are taken from both url AND body in that case
        for k,argList in self.request.arguments.items():
            if argList and argList[-1].endswith(toRemove):
                argList[-1]=argList[-1][:-len(toRemove)]
                break
        return ret
    
    def cookieHostToSet(self):
        # for the Domain= field of cookies
        for hs in options.host_suffix.split("/"):
            if self.request.host.endswith("."+hs):
                return hs
        pp = ':'+str(options.publicPort)
        if self.request.host.endswith(pp): return self.request.host[:-len(pp)]
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
    def patch(self, *args, **kwargs):   return self.doReq()
    @asynchronous
    def options(self, *args, **kwargs): return self.doReq()

    @asynchronous
    def connect(self, *args, **kwargs):
      try: host, port = self.request.uri.split(':')
      except: host,port = None,None
      is_sshProxy = (host,port)==(allowConnectHost,allowConnectPort)
      if host and (options.real_proxy or self.isPjsUpstream or self.isSslUpstream or is_sshProxy): # support tunnelling if real_proxy (but we might not be able to adjust anything, see below), but at any rate support ssh_proxy if set
        upstream = tornado.iostream.IOStream(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0))
        client = self.request.connection.stream
        # See note about Tornado versions in writeAndClose
        if not is_sshProxy and not self.isSslUpstream and int(port)==443:
            # We can change the host/port to ourselves
            # and adjust the SSL site (assuming this CONNECT
            # is for an SSL site)
            # This should result in a huge "no cert" warning
            host,port = "127.0.0.1",self.WA_connectPort
            debuglog("Rerouting CONNECT to "+host+":"+str(port))
        def callback(*args):
          client.read_until_close(lambda data:writeAndClose(upstream,data),lambda data:writeOrError("upstream "+host+":"+str(port)+self.debugExtras(),upstream,data)) # (DO say 'upstream', as if host==localhost it can be confusing (TODO: say 'upstream' only if it's 127.0.0.1?))
          if self.isPjsUpstream: clientErr=None # we won't mind if our js_interpreter client gives up on an upstream fetch
          else: clientErr = "client "+self.request.remote_ip+self.debugExtras()
          upstream.read_until_close(lambda data:writeAndClose(client,data),lambda data:writeOrError(clientErr,client,data))
          try: client.write('HTTP/1.0 200 Connection established\r\n\r\n')
          except tornado.iostream.StreamClosedError:
              if not self.isPjsUpstream: logging.error("client "+self.request.remote_ip+" closed before we said Established"+self.debugExtras())
        upstream.connect((host, int(port)), callback)
        # Tornado _log is not called until finish(); it would be useful to log the in-process connection at this point
        try: self._log()
        except: pass # not all Tornado versions support this?
      else: self.set_status(400),self.myfinish()
    def myfinish(self):
        debuglog("myfinish"+self.debugExtras())
        if hasattr(self,"_finished") and self._finished: pass # try to avoid "connection closed" exceptions if browser has already gone away
        else:
          try:
            self.finish()
            self._finished = 1 # (just in case)
          except: pass # belt and braces (depends on Tornado version?)
        if self.isPjsUpstream:
            try:
                webdriver_inProgress[self.WA_PjsIndex].remove(self.request.uri)
            except: pass
        try: reqsInFlight.remove(id(self))
        except: pass
        try: origReqInFlight.remove(id(self))
        except: pass

    def redirect(self,redir,status=301):
        debuglog("Serving redirect ("+repr(status)+" to "+repr(redir)+")"+self.debugExtras())
        self.set_status(status)
        for h in ["Location","Content-Type","Content-Language"]: self.clear_header(h) # so redirect() can be called AFTER a site's headers are copied in
        self.add_header("Location",redir)
        self.add_header("Content-Type","text/html")
        if self.canWriteBody(): self.write('<html lang="en"><body><a href="%s">Redirect</a></body></html>' % redir.replace('&','&amp;').replace('"','&quot;'))
        self.myfinish()

    def request_no_external_referer(self):
        # Not all browsers implement this, but we can ask.
        # Some sites publically log their Referer headers,
        # so if an adjusted page needs to link directly to a
        # non-adjusted page then we could end up with a
        # 'deep link' in a public log, which bad robots (that
        # ignore our robots.txt) might try to crawl.  Try to
        # stop this from happening by politely asking the
        # browser to suppress Referer in this case.
        # (For --renderOmitGoAway, we could redirect to an
        # 'air lock' URL before providing the link out to the
        # site, but that wouldn't help with --redirectFiles)
        self.add_header("Referrer-Policy","same-origin")
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
        warn=self.checkBrowser(["IEMobile 6","IEMobile 7","Opera Mobi"],"<h3>WARNING: Your browser might not save this file</h3>You are using {B}, which has been known to try to display text attachments in its own window using very small print, giving no option to save to a file. You might get better results in IEMobile 8+ or Opera Mini (although the latter may have a more limited range of font sizes in the browser itself).") # TODO: make this warning configurable?  See comment after set_header("Content-Disposition",...) below for details
        self.doResponse2(("""%s<h1>File conversion in progress</h1>The result should start downloading soon. If it does not, try <script><!--
document.write('<a href="javascript:location.reload(true)">refreshing this page</a>')
//--></script><noscript>refreshing this page</noscript>.%s%s<hr>This is %s</body></html>""" % (htmlhead("File conversion in progress"),backScript,warn,serverName_html)),True,False)
        # TODO: if (and only if) refreshing from this page, might then need a final 'conversion finished' page before serving the attachment, so as not to leave an 'in progress' page up afterwards
        return True
    def inProgress_run(self): return hasattr(self,"inProgress_has_run") and self.inProgress_has_run

    def addToHeader(self,header,toAdd):
        val = self.request.headers.get(header,"")
        if (", "+val).endswith(", "+toAdd): return # seems we're running inside a software stack that already added it
        if val: val += ", "
        self.request.headers[header] = val+toAdd

    def forwardFor(self,server,serverType="ownServer"):
        debuglog("forwardFor "+server)
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
        upstream.connect((host, int(port)),lambda *args:(upstream.read_until_close(lambda data:writeAndClose(client,data),lambda data:writeOrError(serverType+" client",client,data)),client.read_until_close(lambda data:writeAndClose(upstream,data),lambda data:writeOrError(serverType+" upstream",upstream,data))))
        try: self.request.uri = self.request.original_uri
        except: pass
        upstream.write(self.request.method+" "+self.request.uri+" "+self.request.version+"\r\n"+"\r\n".join(("%s: %s" % (k,v)) for k,v in (list(h for h in self.request.headers.get_all() if not h[0].lower()=="x-real-ip")+[("X-Real-Ip",self.request.remote_ip)]))+"\r\n\r\n"+self.request.body)

    def thin_down_headers(self):
        # For ping, and for SSH tunnel.  Need to make the response short, but still allow keepalive
        self.request.suppress_logging = True
        for h in ["Server","Content-Type","Date"]:
            try: self.clear_header(h)
            except: pass
        # (Date is added by Tornado 3, which can also add "Vary: Accept-Encoding" but that's done after we get here, TODO: option to ping via a connect and low-level TCP keepalive bytes?)
        self.set_header("Etag","0") # shorter than Tornado's computed one (clear_header won't work with Etag; TODO: could override RequestHandler's compute_etag and make it return None if we've set somewhere that we don't want Etag on this request)

    def answerPing(self,newVersion):
        # answer a "ping" request from another machine that's using us as a fasterServer
        self.thin_down_headers()
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
        if self.canWriteBody(): self.write(htmlhead()+"<h1>Web Adjuster load-balancer page</h1>This page should not be shown to normal browsers, only to load balancers and uptime checkers. If you are a human reading this message, <b>it probably means your browser is \"cloaked\"</b> (hidden User-Agent string); please un-hide this to see the top-level page.</body></html>")
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
        try: self.request.remote_ip = self.request.connection.stream.confirmed_ip
        except:
            self.request.remote_ip = self.request.headers.get("X-Real-Ip",self.request.remote_ip)
            try: self.request.connection.stream.confirmed_ip = self.request.remote_ip # keep it for keepalive connections (X-Real-Ip is set only on the 1st request)
            except: pass
        try: del self.request.headers["X-Real-Ip"]
        except: pass
    
    def serveRobots(self):
        self.add_header("Content-Type","text/plain")
        if self.canWriteBody(): self.write("User-agent: *\nDisallow: /\n")
        self.request.suppress_logger_host_convert = True
        self.myfinish()

    def serveImage(self,img):
        if not options.renderLog:
            self.request.suppress_logging = True
        self.add_header("Content-Type","image/"+options.renderFormat)
        self.add_header("Last-Modified","Sun, 06 Jul 2008 13:20:05 GMT")
        self.add_header("Expires","Wed, 1 Dec 2036 23:59:59 GMT") # TODO: S2G
        # self.clear_header("Server") # save bytes if possible as we could be serving a LOT of these images .. but is this really needed? (TODO)
        if self.canWriteBody(): self.write(img)
        self.myfinish()

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
    def htmlOnlyMode(self,isProxyRequest=False):
        if not options.htmlonly_mode: return False
        if hasattr(self.request,"old_cookie"): ck = self.request.old_cookie # so this can be called between change_request_headers and restore_request_headers, e.g. at the start of send_request for js_interpreter mode
        else: ck = ';'.join(self.request.headers.get_list("Cookie"))
        return htmlmode_cookie_name+"=1" in ck or self.auto_htmlOnlyMode(isProxyRequest)
    def auto_htmlOnlyMode(self,isProxyRequest): return options.js_interpreter and (isProxyRequest or (not options.wildcard_dns and not "" in options.default_site.split("/")))
    
    def handle_URLbox_query(self,v):
        self.set_htmlonly_cookie()
        if not (v.startswith("http://") or v.startswith("https://")):
            if ' ' in v or not '.' in v: v=getSearchURL(v)
            else: v="http://"+v
        if not options.wildcard_dns: # need to use cookie_host
            j = i = v.index('/')+2 # after the http:// or https://
            while j<len(v) and v[j] in string.letters+string.digits+'.-': j += 1
            wanted_host = v[i:j]
            if v[i-4]=='s': wanted_host += ".0" # HTTPS hack (see protocolAndHost)
            ch = self.cookie_host(checkURL=False) # current cookie hostname
            if convert_to_requested_host(wanted_host,ch)==wanted_host: # can't do it without changing cookie_host
                if enable_adjustDomainCookieName_URL_override:
                    # do it by URL so they can bookmark it (that is if it doesn't immediately redirect)
                    # (TODO: option to also include the password in this link so it can be passed it around?  and also in the 'back to URL box' link?  but it would be inconsistent because not all links can do that, unless we consistently 302-redirect everything so that they do, but that would reduce the efficiency of the browser's HTTP fetches.  Anyway under normal circumstances we probably won't want users accidentally spreading include-password URLs)
                    v = addArgument(v,adjust_domain_cookieName+'='+urllib.quote(wanted_host))
                else: self.add_header("Set-Cookie",adjust_domain_cookieName+"="+urllib.quote(wanted_host)+"; Path=/; Expires="+cookieExpires) # (DON'T do this unconditionally, convert_to_requested_host above might see we already have another fixed domain for it)
                # (TODO: if convert_to_requested_host somehow returns a *different* non-default_site domain, that cookie will be lost.  Might need to enforce max 1 non-default_site domain.)
            else: wanted_host = ch
        else: wanted_host=None # not needed if wildcard_dns
        self.redirect(domain_process(v,wanted_host,True))

    def forwardToOtherPid(self):
        if not (options.ssl_fork and self.WA_UseSSL): return
        # We're handling SSL in a separate PID, so we have to
        # forward the request back to the original PID in
        # case it needs to do things with webdrivers etc.
        self.request.headers["X-WA-FromSSLHelper"] = "1"
        self.forwardFor("127.0.0.1:%d" % (self.WA_connectPort-1),"SSL helper")
        return True
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
        if options.ssl_fork and self.request.headers.get("X-WA-FromSSLHelper",""):
            self.request.connection.stream.isFromSslHelper = True # (it doesn't matter if some browser spoofs that header: it'll mean they'll get .0 asked for; however we could check the remote IP is localhost if doing anything more complex with it)
            del self.request.headers["X-WA-FromSSLHelper"] # (don't pass it to upstream servers)
        if self.WA_UseSSL or (hasattr(self.request,"connection") and hasattr(self.request.connection.stream,"isFromSslHelper")): # we're the SSL helper on port+1 and we've been CONNECT'd to, or we're on port+0 and forked SSL helper has forwarded it to us, so the host asked for must be a .0 host for https
            if self.request.host and not self.request.host.endswith(".0"): self.request.host += ".0"
            
    def handleSSHTunnel(self):
        if not allowConnectURL=="http://"+self.request.host+self.request.uri: return
        self.thin_down_headers() ; self.add_header("Pragma","no-cache") # hopefully enough and don't need all of self.add_nocache_headers
        global the_ssh_tunnel # TODO: support more than one? (but will need to use session IDs etc; GNU httptunnel does just 1 tunnel as of 3.x so maybe we're OK)
        try:
            if self.request.body=="new connection":
                self.request.body = ""
                the_ssh_tunnel[1].append(None) # if exists
            if None in the_ssh_tunnel[1]:
                try: the_ssh_tunnel[0].close()
                except: pass
                raise NameError # as though the_ssh_tunnel didn't yet exist
        except NameError: # not yet established
            sessionID = time.time() # for now
            the_ssh_tunnel = [tornado.iostream.IOStream(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)),[],sessionID] # upstream connection, data waiting for client, id
            def add(data):
                if sessionID==the_ssh_tunnel[2]:
                    the_ssh_tunnel[1].append(data)
            the_ssh_tunnel[0].connect((allowConnectHost, int(allowConnectPort)), lambda *args:the_ssh_tunnel[0].read_until_close(lambda data:(add(data),add(None)),add))
            # TODO: log the fact we're starting a tunnel?
        if self.request.body: the_ssh_tunnel[0].write(self.request.body) # TODO: will this work even when it's not yet established? (not a big problem on SSH because server always speaks first)
        def check_ssh_response(startTime,sessionID):
            if not the_ssh_tunnel[2]==sessionID: return self.myfinish()
            if the_ssh_tunnel[1]==[] and not time.time()>startTime+3: return IOLoop.instance().add_timeout(time.time()+0.2,lambda *args:check_ssh_response(startTime,sessionID)) # keep waiting (up to max 3sec - not too long because if client issues a 'read on timeout' while the SSH layer above is waiting for user input then we still want it to be reasonably responsive to that input; it's the client side that should wait longer between polls)
            if None in the_ssh_tunnel[1]:
                self.write(''.join(the_ssh_tunnel[1][:-1]))
                the_ssh_tunnel[1] = [None]
            else:
                self.write(''.join(the_ssh_tunnel[1]))
                the_ssh_tunnel[1] = []
            self.myfinish()
        IOLoop.instance().add_timeout(time.time()+0.2,lambda *args:check_ssh_response(time.time(),the_ssh_tunnel[2]))
        return True

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
        if self.canWriteBody(): self.write("%s%s<p><form><label><input type=\"checkbox\" name=\"gotit\">Don't show this message again</label><br><input type=\"submit\" value=\"Continue\" onClick=\"var a='%s=%s;domain=',b=(document.forms[0].gotit.checked?'expires=%s;':'')+'path=/',h='%s;';document.cookie=a+'.'+h+b;document.cookie=a+h+b;location.reload(true);return false\"></body></html>" % (htmlhead("Message"),msg,seen_ipMessage_cookieName,val,cookieExpires,hs))
        logging.info("ip_messages: done "+self.request.remote_ip)
        self.myfinish() ; return True

    def handleGoAway(self,realHost,maybeRobots):
        if not options.renderOmitGoAway: return False
        browser = self.checkBrowser(options.renderOmit)
        if not browser: return False
        if maybeRobots:
            self.serveRobots() # regardless of which browser header it presents
            return True # do NOT shorten this by making serveRobots return True: it must return None due to other uses
        # TODO: option to redirect immediately without this message?  (but then we'd be supplying a general redirection service, which might have issues of its own)
        if realHost:
            msg = ' and <a rel="noreferrer" href="%s%s">go directly to the original site</a>' % (protocolWithHost(realHost),self.request.uri)
            self.request_no_external_referer()
        else: msg = ''
        self.add_nocache_headers()
        if self.canWriteBody(): self.write("%s<h1>You don't need this!</h1>This installation of Web Adjuster has been set up to change certain characters into pictures, for people using old computers that don't know how to display them themselves. However, <em>you</em> seem to be using %s, which is <noscript>either </noscript>definitely capable of showing these characters by itself<noscript>, or else wouldn't be able to show the pictures anyway<!-- like Lynx --></noscript>. Please save our bandwidth for those who really need it%s. Thank you.</body></html>" % (htmlhead(),browser,msg))
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
        self.doResponse2(urlbox_html(self.htmlOnlyMode(),self.cssOptionsHtml(),self.getArg("q") or self.getArg("d")),True,False) # TODO: run htmlFilter on it also? (render etc will be done by doResponse2)

    def serve_hostError(self):
        l = []
        if options.wildcard_dns: l.append("prefixing its domain with the one you want to adjust")
        if options.real_proxy: l.append("setting it as a <b>proxy</b>")
        if l: err="This adjuster can be used only by "+", or ".join(l)+"."
        else: err="This adjuster cannot be used. Check the configuration."
        self.doResponse2(htmlhead()+err+'</body></html>',True,False) # TODO: run htmlFilter on it also? (render etc will be done by doResponse2)

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
                if self.checkBrowser(["iPhone OS 4","iPhone OS 5","iPhone OS 6","iPhone OS 7"]): sep = ';'
                elif self.checkBrowser(["iPhone OS 8","iPhone OS 9"]): sep = '&'
                else: sep = '?'
                smsLink = '<br><a href="sms:'+sep+'body=%s">Send as SMS (text message)</a>' % urllib.quote(rm_u8punc(smsLink))
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
            self.set_status(400) ; self.myfinish() ; return
        if len(self.request.uri) > len(options.submitPath):
            txt = self.request.uri[len(options.submitPath):]
            if len(txt)==2 and options.submitBookmarklet:
                filterNo = ord(txt[1])-ord('A')
                if txt[0] in 'bB': return self.serve_bookmarklet_code(txt[1],txt[0]=='B')
                elif txt[0]=='j': return self.serve_bookmarklet_json(filterNo)
                elif txt[0]=='u': return self.serve_backend_post(filterNo)
                elif txt[0] in 'iap':
                    # Android or iOS instructions
                    # (a=Android i=iPhone p=iPad)
                    # (Similar technique does NOT work in Opera Mini 5.1.21594 or Opera Mobile 10.00 (both 2010) on Windows Mobile 6.1: can end up with a javascript: bookmark but it has no effect when selected)
                    theSys = {"i":"iPhone","p":"iPad","a":"Android"}[txt[0]]
                    title = None
                    if '#' in options.htmlFilter:
                        fNames=options.htmlFilterName.split('#')
                        if filterNo+1 < len(fNames):
                            title=fNames[filterNo+1]
                    elif options.htmlFilterName:
                        title=options.htmlFilterName
                    if title: title += " on current page" # because page won't be visible while choosing bookmarks, unlike on desktops
                    else: title=theSys+" bookmarklet - Web Adjuster" # will be the default name of the bookmark
                    # TODO: we say txt[0]+'z' in the instructions to display on another device below, but if there are enough filters to get up to 'z' then the title on the other device will be whatever THAT filter is; might be better to just use txt in that situation
                    i0 = "<h3>%s bookmarklet</h3>To install this bookmarklet on %s, follow the instructions below. You might want to take some notes first, because this page will <em>not</em> be displayed throughout the process! If you have another device, you can show another copy of these instructions on it by going to <tt>http://%sz</tt>" % (theSys, theSys, self.request.host+options.submitPath+txt[0])
                    if "Firefox/" in self.request.headers.get("User-Agent",""): i0 += "<h4>Not Yet Working On Mobile Firefox!</h4>Please use Chrome/Safari.<p>TODO: extension for mobile Firefox?"
                    i0 += "<h4>Instructions</h4><ol><li>"
                    sharp = "<li>You should see a sharp sign (#). If you don't, you might have to scroll a little to the right to get it into view. When you see the sharp sign, press immediately to the right of it. (This can be difficult, depending on your eyesight and the size of your fingers. You must put the text cursor <em>immediately</em> to the right of that sharp. Keep trying until you get it in <em>exactly</em> the right place.)<li>Use the backspace key to delete everything up to and including the sharp. The code should now start with the word <tt>javascript</tt>.<li>"
                    if txt[0] in 'ip':
                        if txt[0]=='i': # iPhone
                            menu="centre square button below"
                            bookmarkOpt="Bookmark"
                            bDone = "Done"
                            bookmarks = "(one to the right of menu button below)"
                        else: # iPad
                            menu="look near the top right of the iPad's screen for a square button with an arrow going up"
                            bookmarkOpt="Add Bookmark"
                            bDone = "Save"
                            bookmarks = "(look near the top left of the iPad's screen for an open book) if the bookmarks are not already showing"
                        i0 += "Press Menu (%s) and choose %s, to bookmark <b>this</b> page<li>Change the name if you want, and press %s<li>Press Bookmarks %s<li>Press Edit (bottom left or bottom right)<li>Find the bookmark you made and press it<li>Long-press the <em>second</em> line to get the selection menu on it<li>Press Select<li>Gently drag the left-most marker over to the left so that it scrolls to the extreme left of the address%sPress \"Done\" three times to come back here." % (menu,bookmarkOpt,bDone,bookmarks,sharp)
                    else: # Android
                        i0 += "Press Menu and Save to Bookmarks, to bookmark <b>this</b> page (on some phones that option is just a drawing of a star)<li>Change the label if you want, but <b>do not</b> press OK<li>Long-press the <em>second</em> line to get the selection on it<li>Gently drag the marker over to the left so that it scrolls to the extreme left of the address"+sharp+"Press \"OK\" to come back here."
                    i0 += "<li>The bookmarklet is now ready for use. Go to whatever page you want to use it on, and select it from the bookmarks to use it."
                    if txt[0]=='a': i0 += " <b>On later versions of Android, it doesn't work to choose the bookmark directly</b>: you have to start typing <tt>javascript:</tt> in the URL box and select it that way."
                    return self.doResponse2(htmlhead(title)+i0+"</ol></body></html>","noFilterOptions",False)
            txt = zlib.decompressobj().decompress(base64.b64decode(txt),16834) # limit to 16k to avoid zip bombs (limit is also in the compress below)
            self.request.uri = "%s (input not logged, len=%d)" % (options.submitPath,len(txt))
        else: txt = self.request.arguments.get("i",None)
        if not txt:
            self.is_password_domain=True # no prominentNotice needed
            # In the markup below, body's height=100% is needed to ensure we can set a percentage height on the textarea consistently across many browsers (otherwise e.g. Safari 6 without user CSS might start making the textarea larger as soon as it contains input, overprinting the rest of the document)
            local_submit_url = "http://"+self.request.host+options.submitPath
            if options.submitBookmarkletDomain: submit_url = "//"+options.submitBookmarkletDomain+options.submitPath
            else: submit_url = local_submit_url
            if (options.password and submitPathIgnorePassword) or options.submitPath=='/': urlbox_footer = "" # not much point linking them back to the URL box under these circumstances
            else: urlbox_footer = '<p><a href="http://'+hostSuffix()+publicPortStr()+'">Process a website</a></p>'
            # TODO: what if their browser doesn't submit in the correct charset?  for example some versions of Lynx need -display_charset=UTF-8 otherwise they might double-encode pasted-in UTF-8 and remove A0 bytes even though it appears to display correctly (and no, adding accept-charset won't help: that's for if the one to be accepted differs from the document's)
            return self.doResponse2(("""%s<body style="height:100%%;overflow:auto"><form method="post" action="%s"><h3>Upload Text</h3>%s:<p><span style="float:right"><input type="submit"><script><!--
document.write(' (Ctrl-Enter) | <a href="javascript:history.go(-1)">Back</a>')
//--></script></span><br><textarea name="i" style="width:100%%;clear:both;height:60%%" rows="5" cols="20" placeholder="Type or paste your text here"
onKeyDown="if((event.ctrlKey||event.metaKey) && (event.keyCode==13 || event.which==13)) document.forms[0].submit(); else return true;">
</textarea></form>%s<script><!--
document.forms[0].i.focus()
//--></script></body></html>""" % (htmlhead("Upload Text - Web Adjuster").replace("<body>",""),options.submitPath,options.submitPrompt,bookmarklet(submit_url,local_submit_url)+urlbox_footer)),"noFilterOptions",False)
        if type(txt) == list: # came from the POST form
            txt = txt[0].strip()
            # On at least some browsers (e.g. some Safari versions), clicking one of our JS reload links after the POST text has been shown will reload the form (instead of re-submitting the POST text) and can scroll to an awkward position whether the code below calls focus() or not.  Could at least translate to GET if it's short enough (don't want to start storing things on the adjuster machine - that would require a shared database if load-balancing)
            if len(txt) <= 16384: # (else we wouldn't decompress all; see comment above)
                enc = base64.b64encode(zlib.compress(txt,9))
                if 0 < len(enc) < 2000: return self.redirect("http://"+hostSuffix()+publicPortStr()+options.submitPath+enc,303) # POST to GET

        # pretend it was served by a remote site; go through everything including filters (TODO: could bypass most of doResponse instead of rigging it up like this; alternatively keep this as it shows how to feed data to doResponse)
        self.connection_header = None
        self.urlToFetch = "" # for js_process
        class H:
            def get(self,h,d):
                if h=="Content-Type": return "text/html; charset=utf-8"
                else: return d
            def get_all(self): return [("Content-Type","text/html; charset=utf-8")]
        runFilterOnText(self.getHtmlFilter(),find_text_in_HTML("""%s<h3>Your text</h3>%s<hr>This is %s. %s</body></html>""" % (htmlhead("Uploaded Text - Web Adjuster"),txt2html(txt),serverName_html,backScriptNoBr)),lambda out,err:self.doResponse2(out,True,False)) # backScriptNoBr AFTER the server notice to save vertical space
    def serve_bookmarklet_code(self,xtra,forceSameWindow):
        self.add_header("Content-Type","application/javascript")
        self.add_header("Access-Control-Allow-Origin","*")
        if options.submitBookmarkletDomain: submit = "//"+options.submitBookmarkletDomain
        else: submit = "http://"+self.request.host
        if self.canWriteBody(): self.write(bookmarkletMainScript(submit+options.submitPath+'j'+xtra,forceSameWindow))
        self.myfinish()
    def serve_err(self,err):
        self.set_status(500)
        self.add_header("Content-Type","text/plain")
        logging.error("Bookmarklet error: "+err) # +' '+repr(self.request.body)
        if self.canWriteBody(): self.write(err)
        self.myfinish()
    def serve_bookmarklet_json(self,filterNo):
        self.add_header("Access-Control-Allow-Origin","*")
        self.add_header("Access-Control-Allow-Headers","Content-Type")
        if not self.request.body:
            self.add_header("Content-Type","text/plain")
            self.add_header("Allow","POST") # some browsers send OPTIONS first before POSTing via XMLHttpRequest (TODO: check if OPTIONS really is the request method before sending this?)
            if self.canWriteBody(): self.write("OK")
            return self.myfinish()
        try: l = json.loads(self.request.body)
        except: return self.serve_err("Bad JSON")
        for i in xrange(len(l)):
            if l[i]=='': l[i] = u'' # shouldn't get this (TODO: fix in bookmarkletMainScript? e.g. if submitBookmarkletFilterJS can match empty strings, or conversion to 'cnv' makes it empty, anything else?), but if we do, don't let it trip up the 'wrong data structue' below
        if not (type(l)==list and all((type(i)==type(u"") and not chr(0) in i) for i in l)): return self.serve_err("Wrong data structure")
        codeTextList = []
        for i in l:
            codeTextList.append(chr(0))
            codeTextList.append(i.encode('utf-8'))
        def callback(out,err):
            self.add_header("Content-Type","application/json")
            if self.canWriteBody(): self.write(json.dumps([i.decode('utf-8','replace') for i in out[1:].split(chr(0))])) # 'replace' here because we don't want utf-8 errors to time-out the entire request (although hopefully the filter WON'T produce utf-8 errors...)
            self.finish()
        runFilterOnText(self.getHtmlFilter(filterNo),codeTextList,callback)
    def serve_backend_post(self,filterNo):
        l = self.request.body
        runFilter(self.getHtmlFilter(filterNo),self.request.body,lambda out,err: (self.write(out),self.finish()))

    def checkTextCache(self,newext):
        # check for PDF/EPUB conversion on other threads or cached
        if not options.pdfepubkeep: return False # we don'tguarantee to update kept_tempfiles properly if it's 0 (e.g. pdf can just pipe, so don't need unlinkOutputLater)
        ktkey = (self.request.host, self.request.uri)
        if ktkey in kept_tempfiles:
            def tryRead():
                try: txt=open(kept_tempfiles[ktkey]).read()
                except: txt = None
                if txt:
                    if self.canWriteBody():
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

    def debugExtras(self):
        r = " for "+self.request.method+" "+self.request.uri
        if not self.request.uri.startswith("http"): r += " host="+str(self.request.host)
        if self.WA_UseSSL or (hasattr(self.request,"connection") and hasattr(self.request.connection.stream,"isFromSslHelper")): r += " WA_UseSSL"
        if self.isPjsUpstream: r += " isPjsUpstream instance "+str(self.WA_PjsIndex+self.WA_PjsStart)
        if self.isSslUpstream: r += " isSslUpstream"
        return r

    def canWriteBody(self): return not self.request.method in ["HEAD","OPTIONS"]
    
    def doReq(self):
        debuglog("doReq"+self.debugExtras()) # MUST keep this here: it also sets profileIdle=False
        try: reqsInFlight.add(id(self)) # for profile
        except: pass
        if not self.isPjsUpstream and not self.isSslUpstream:
            try: origReqInFlight.add(id(self))
            except: pass
        if wsgi_mode and self.request.path==urllib.quote(os.environ.get("SCRIPT_NAME","")+os.environ.get("PATH_INFO","")) and 'SCRIPT_URL' in os.environ:
            # workaround for Tornado 2.x limitation when used with CGI and htaccess redirects
            self.request.uri = os.environ['SCRIPT_URL']
            qs = os.environ.get("QUERY_STRING","")
            if not qs: qs = os.environ.get("REDIRECT_QUERY_STRING","")
            if qs:
                self.request.uri += "?"+qs
                self.request.arguments = urlparse.parse_qs(qs)
            self.request.path = self.request.uri
        else:
            # HTTP/1.x headers are officially Latin-1 (but usually ASCII), and Tornado (at least versions 2 through 4) decodes the Latin-1 and re-encodes it as UTF-8.  This can cause confusion, so let's emulate modern browsers and %-encode any non-ASCII URIs:
            try: uri2 = self.request.uri.decode('utf-8').encode('latin1')
            except: uri2 = self.request.uri
            if not self.request.uri == uri2: self.request.uri = urllib.quote(uri2)
        if self.request.method=="HEAD": self.set_header("Content-Length","-1") # we don't know yet: Tornado please don't add it!  (NB this is for HEAD only, not OPTIONS, which should have Content-Length 0 or some browsers time out) (TODO: in non-WSGI mode could call .flush() after writing headers (with callback param), then Content-Length won't be added on .finish())
        if self.request.headers.get("User-Agent","")=="ping":
            if self.request.uri=="/ping2": return self.answerPing(True)
            elif self.request.uri=="/ping": return self.answerPing(False)
        elif options.loadBalancer and self.request.headers.get("User-Agent","")=="" and self.request.uri=="/": return self.answer_load_balancer()
        self.find_real_IP() # must do this BEFORE forwarding to fasterServer, because might also be behind nginx etc
        if fasterServer_up:
            return self.forwardFor(options.fasterServer,"fasterServer")
        if self.forwardToOtherPid(): return
        if self.handleFullLocation(): return # if returns here, URL is invalid; if not, handleFullLocation has 'normalised' self.request.host and self.request.uri
        if self.isPjsUpstream:
            if options.js_UA and options.js_UA.startswith("*"): self.request.headers["User-Agent"] = options.js_UA[1:]
            webdriver_inProgress[self.WA_PjsIndex].add(self.request.uri)
        elif not self.isSslUpstream:
            if self.handleSSHTunnel(): return
            if self.handleSpecificIPs(): return
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
            if (self.request.host=="localhost" or self.request.host.startswith("localhost:")) and not "localhost" in options.host_suffix: return self.redirect("http://"+hostSuffix(0)+publicPortStr()+self.request.uri) # save confusion later (e.g. set 'HTML-only mode' cookie on 'localhost' but then redirect to host_suffix and cookie is lost)
        viewSource = (not self.isPjsUpstream and not self.isSslUpstream) and self.checkViewsource()
        self.cookieViaURL = None
        if self.isPjsUpstream or self.isSslUpstream: realHost = self.request.host
        else: realHost = convert_to_real_host(self.request.host,self.cookie_host(checkReal=False)) # don't need checkReal if return value will be passed to convert_to_real_host anyway
        if realHost == -1:
            return self.forwardFor(options.own_server)
            # (TODO: what if it's keep-alive and some browser figures out our other domains are on the same IP and tries to fetch them through the same connection?  is that supposed to be allowed?)
        elif realHost==0 and options.ownServer_if_not_root: realHost=options.own_server # asking by cookie to adjust the same host, so don't forwardFor() it but fetch it normally and adjust it
        isProxyRequest = self.isPjsUpstream or self.isSslUpstream or (options.real_proxy and realHost == self.request.host)
        self.request.valid_for_whois = True # (if options.whois, don't whois unless it gets this far, e.g. don't whois any that didn't even match "/(.*)" etc)
        maybeRobots = (not self.isPjsUpstream and not self.isSslUpstream and not options.robots and self.request.uri=="/robots.txt") # don't actually serveRobots yet, because MIGHT want to pass it to own_server (see below)
        
        self.is_password_domain=False # needed by doResponse2
        if options.password and not options.real_proxy and not self.isPjsUpstream and not self.isSslUpstream: # whether or not open_proxy, because might still have password (perhaps on password_domain), anyway the doc for open_proxy says "allow running" not "run"
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
          if not self.authenticates_ok(host) and not (submitPathIgnorePassword and self.request.uri.startswith(submitPathForTest)):
              self.request.suppress_logger_host_convert = True
              if options.auth_error=="http://":
                  if options.own_server: return self.forwardFor(options.own_server)
                  elif maybeRobots: return self.serveRobots()
                  else: options.auth_error = "auth_error set incorrectly (own_server not set)" # see auth_error help (TODO: is it really a good idea to say this HERE?)
              elif maybeRobots: return self.serveRobots()
              self.add_nocache_headers() # in case they try the exact same request again after authenticating (unlikely if they add &p=..., but they might come back to the other URL later, and refresh is particularly awkward if we redirect)
              if options.auth_error.startswith("http://") or options.auth_error.startswith("https://"): return self.redirect(options.auth_error)
              if options.auth_error.startswith("*"): auth_error = options.auth_error[1:]
              else:
                  self.set_status(401)
                  auth_error = options.auth_error
              if self.canWriteBody(): self.write(htmlhead("")+auth_error+"</body></html>")
              return self.myfinish()
        # Authentication is now OK
        fixServerHeader(self)
        if not self.isPjsUpstream and not self.isSslUpstream:
          if self.handleGoAway(realHost,maybeRobots): return
          # Now check if it's an image request:
          _olduri = self.request.uri
          self.request.uri=urllib.unquote(self.request.uri)
          img = Renderer.getImage(self.request.uri)
          if img: return self.serveImage(img)
          # Not an image:
          if options.mailtoPath and self.request.uri.startswith(options.mailtoPath): return self.serve_mailtoPage()
          if options.submitPath and self.request.uri.startswith(submitPathForTest): return self.serve_submitPage()
          self.request.uri = _olduri
        if realHost=="error" and not maybeRobots:
            return self.serve_hostError()
        if not realHost: # default_site(s) not set
            if options.own_server and options.ownServer_if_not_root and len(self.request.path)>1: return self.forwardFor(options.own_server)
            elif maybeRobots: return self.serveRobots()
            # Serve URL box
            self.set_css_from_urlbox()
            if self.getArg("try"): return self.serve_URLbox() # we just set the stylesheet (TODO: preserve any already-typed URL?)
            if options.submitPath and self.getArg("sPath"): return self.redirect("http://"+hostSuffix()+publicPortStr()+options.submitPath)
            v=self.getArg("q")
            if v: return self.handle_URLbox_query(v)
            else: return self.serve_URLbox()
        if maybeRobots: return self.serveRobots()
        if not self.isPjsUpstream and not self.isSslUpstream and self.needCssCookies():
            self.add_nocache_headers() # please don't cache this redirect!  otherwise user might not be able to leave the URL box after:
            return self.redirect("http://"+hostSuffix()+publicPortStr()+"/?d="+urllib.quote(protocolWithHost(realHost)+self.request.uri),302) # go to the URL box - need to set more options (and 302 not 301, or some browsers could cache it despite the above)
        if not self.isPjsUpstream and not self.isSslUpstream: self.addCookieFromURL() # for cookie_host
        converterFlags = []
        for opt,suffix,ext,fmt in [
            (options.pdftotext,pdftotext_suffix,".pdf","pdf"),
            (options.epubtotext,epubtotext_suffix,".epub","epub"),
            (options.epubtozip,epubtozip_suffix,".epub","epub"),
            (options.askBitrate,mp3lofi_suffix,".mp3",None),
            ]:
            if opt and not self.isPjsUpstream and not self.isSslUpstream and self.request.uri.endswith(suffix) and (self.request.uri.lower()[:-len(suffix)].endswith(ext) or guessCMS(self.request.uri,fmt)):
                self.request.uri = self.request.uri[:-len(suffix)]
                converterFlags.append(True)
            else: converterFlags.append(False)
        if upstream_rewrite_ssl and not self.isSslUpstream and not (options.js_interpreter and not self.isPjsUpstream): protocol = "http://" # keep the .0 in and call protocolAndHost again on the isSslUpstream pass
        else: protocol,realHost = protocolAndHost(realHost)
        self.change_request_headers(realHost,isProxyRequest)
        self.urlToFetch = protocol+self.request.headers["Host"]+self.request.uri
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
        elif self.isPjsUpstream and "text/html" in self.request.headers.get("Accept","") and not (any(converterFlags) or viewSource): self.sendHead(forPjs=True)
        else: self.sendRequest(converterFlags,viewSource,isProxyRequest,follow_redirects=False) # (DON'T follow redirects - browser needs to know about them!)
    
    def change_request_headers(self,realHost,isProxyRequest):
        def fixDNS(val):
            # undo our domain rewrites (for Referer and for the path part of the URL); change http://X-0 to https://X (HTTPS hack)
            if isProxyRequest: return val
            start = 0
            for http in ["http://", "http%3A%2F%2F",
                         "https://", "https%3A%2F%2F"]:
                if val.startswith(http):
                    start = len(http) ; break
            i = start ; proto = val[:start]
            while i<len(val) and val[i] in string.letters+string.digits+'.-': i += 1
            if i<len(val) and val[i]==':': # port no.
                i += 1
                while i<len(val) and val[i] in string.digits: i += 1
            if i==start: return val
            r=convert_to_real_host(val[start:i],self.cookie_host())
            if r in [-1,"error"]: # shouldn't happen
                return val # (leave unchanged if it does)
            elif not r: r="" # ensure it's a string
            elif r.endswith(".0"): # undo HTTPS hack
                r = r[:-2]
                if proto and not proto.startswith("https"): proto=proto[:4]+'s'+proto[5:] # (TODO: what if not proto here?)
            return proto+r+val[i:]
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
                if v in ["","http://","http:///"]:
                    # it must have come from the URL box
                    del self.request.headers["Referer"]
                else: self.request.headers["Referer"] = v
        for http in ["http://","http%3A%2F%2F"]: # xyz?q=http://... stuff
          if http in self.request.uri[1:]:
            u=self.request.uri.split(http)
            for i in range(1,len(u)): u[i]=fixDNS(http+u[i])
            self.request.uri="".join(u)
        self.accept_stuff = []
        for h in rmClientHeaders:
            l = self.request.headers.get_list(h)
            if l:
                del self.request.headers[h]
                self.accept_stuff.append((h,l[0]))
        self.request.headers["Host"]=realHost
        if options.via and not self.isSslUpstream:
            v = self.request.version
            if v.startswith("HTTP/"): v=v[5:]
            self.addToHeader("Via",v+" "+convert_to_via_host(self.request.host)+" ("+viaName+")")
            self.addToHeader("X-Forwarded-For",self.request.remote_ip)
        if options.uavia and not self.isSslUpstream: self.addToHeader("User-Agent","via "+convert_to_via_host(self.request.host)+" ("+viaName+")")
    def restore_request_headers(self): # restore the ones Tornado might use (Connection etc)
        if not hasattr(self,"accept_stuff"): return # haven't called change_request_headers (probably means this is user input)
        for k,v in self.accept_stuff: self.request.headers[k]=v
        if hasattr(self.request,"old_cookie"): self.request.headers["Cookie"] = self.request.old_cookie # + put this back so we can refer to our own cookies
    
    def sendRequest(self,converterFlags,viewSource,isProxyRequest,follow_redirects):
        if self.isPjsUpstream and webdriver_prefetched[self.WA_PjsIndex]:
            r = webdriver_prefetched[self.WA_PjsIndex]
            webdriver_prefetched[self.WA_PjsIndex] = None
            return self.doResponse(r,converterFlags,viewSource,isProxyRequest)
        body = self.request.body
        if not body: body = None # required by some Tornado versions
        if self.isSslUpstream: ph,pp = None,None
        else: ph,pp = upstream_proxy_host,upstream_proxy_port
        if dryrun_upstream_rewrite_ssl and pp and upstream_rewrite_ssl: pp += 1
        if options.js_interpreter and not self.isPjsUpstream and not self.isSslUpstream and self.htmlOnlyMode(isProxyRequest) and not follow_redirects and not self.request.uri in ["/favicon.ico","/robots.txt"] and not self.request.method.lower()=="head":
            if options.via: via = self.request.headers["Via"],self.request.headers["X-Forwarded-For"]
            else: via = None # they might not be defined
            if body or self.request.method.lower()=="post":
                body = self.request.method, body
            clickElementID = clickLinkText = None
            if type(viewSource)==tuple:
                idEtc,viewSource = viewSource
                if idEtc.startswith(';'):
                    clickElementID = idEtc[1:]
                elif idEtc.startswith('-'):
                    clickLinkText = idEtc[1:]
            def tooLate():
              r=hasattr(self,"_finished") and self._finished
              if r:
                  logging.error("Client gave up on "+self.urlToFetch+" while queued")
                  try: reqsInFlight.remove(id(self))
                  except: pass
                  try: origReqInFlight.remove(id(self))
                  except: pass
              return r
            if options.js_429 and len(webdriver_queue) >= 2*options.js_instances: # TODO: do we want to allow for 'number of requests currently in prefetch stage' as well?  (but what if we're about to get a large number of prefetch-failures anyway?)  + update comment by define("js_429") above
                try: self.set_status(429,"Too many requests")
                except: self.set_status(429)
                self.add_header("Retry-After",str(10*len(webdriver_queue)/options.js_instances)) # TODO: increase this if multiple clients?
                if self.canWriteBody(): self.write("Too many requests (HTTP 429)")
                if not self.request.remote_ip in options.ipNoLog: logging.error("Returning HTTP 429 (too many requests) for "+self.urlToFetch+" to "+self.request.remote_ip)
                self.request.suppress_logging = True
                self.myfinish() ; return
            if options.js_reproxy:
              def prefetch():
                # prefetch the page, don't tie up a PJS until
                # we have the page in hand
                httpfetch(self.urlToFetch,
                  connect_timeout=60,request_timeout=120,
                  proxy_host=ph, proxy_port=pp,
                  # TODO: use_gzip=enable_gzip, # but will need to retry without it if it fails
                  method=self.request.method,
                  allow_nonstandard_methods=True,
                  headers=self.request.headers, body=body,
                  validate_cert=False,
                  callback=lambda prefetched_response:
                    webdriver_fetch(self.urlToFetch,
                                    prefetched_response,
                        clickElementID, clickLinkText,
                        via,viewSource=="screenshot",
                        lambda r:self.doResponse(r,converterFlags,viewSource==True,isProxyRequest,js=True),tooLate),
                  follow_redirects=False)
              def prefetch_when_ready(t0):
                if len(webdriver_queue) < 2*options.js_instances: return prefetch()
                # If too many PJS instances already tied up,
                # don't start the prefetch yet
                again = time.time()+1 # TODO: in extreme cases this can result in hundreds or thousands of calls to prefetch_when_ready per second; need a second queue? (tooLate() should mitigate it if client goes away, + won't get here unless --js_429=False)
                global last_Qoverload_time, Qoverload_max
                try: last_Qoverload_time
                except: last_Qoverload_time=Qoverload_max=0
                Qoverload_max = max(Qoverload_max,again-t0)
                if time.time() > last_Qoverload_time + 5:
                    logging.error("webdriver_queue overload (max prefetch delay %d secs)" % Qoverload_max)
                    last_Qoverload_time = time.time()
                if not tooLate(): IOLoop.instance().add_timeout(again,lambda *args:prefetch_when_ready(t0))
              prefetch_when_ready(time.time())
            else: # no reproxy: can't prefetch
                webdriver_fetch(self.urlToFetch,None,
                        clickElementID, clickLinkText,
                        via,viewSource=="screenshot",
                        lambda r:self.doResponse(r,converterFlags,viewSource==True,isProxyRequest,js=True),tooLate)
        else:
            if options.js_interpreter and self.isPjsUpstream and webdriver_via[self.WA_PjsIndex]: self.request.headers["Via"],self.request.headers["X-Forwarded-For"] = webdriver_via[self.WA_PjsIndex]
            httpfetch(self.urlToFetch,
                  connect_timeout=60,request_timeout=120, # Tornado's default is usually something like 20 seconds each; be more generous to slow servers (TODO: customise?)
                  proxy_host=ph, proxy_port=pp,
                  use_gzip=enable_gzip and not hasattr(self,"avoid_gzip"),
                  method=self.request.method, headers=self.request.headers, body=body,
                  allow_nonstandard_methods=True, # (e.g. POST with empty body)
                  validate_cert=False, # TODO: options.validate_certs ? but (1) there's little point unless you also secure your connection to the adjuster (or run it on localhost), (2) we haven't sorted out how to gracefully return if the validation fails, (3) True will cause failure if we're on a VM/container without a decent root-certs configuration
                  callback=lambda r:self.doResponse(r,converterFlags,viewSource,isProxyRequest),follow_redirects=follow_redirects)
        # (Don't have to worry about auth_username/auth_password: should just work by passing on the headers)
        # TODO: header_callback (run with each header line as it is received, and headers will be empty in the final response); streaming_callback (run with each chunk of data as it is received, and body and buffer will be empty in the final response), but how to abort a partial transfer if we realise we don't want it (e.g. large file we don't want to modify on site that doesn't mind client being redirected there directly)

    def doResponse(self,response,converterFlags,viewSource,isProxyRequest,js=False):
        curlFinished()
        debuglog("doResponse"+self.debugExtras()+" isProxyRequest="+repr(isProxyRequest))
        self.restore_request_headers()
        do_pdftotext,do_epubtotext,do_epubtozip,do_mp3 = converterFlags
        do_domain_process = do_html_process = do_js_process = True
        do_json_process = do_css_process = False
        charset = "utf-8" # by default
        if response==None or not response.code or response.code==599:
            # (some Tornado versions don't like us copying a 599 response without adding our own Reason code; just making it a 504 for now)
            try: error = str(response.error)
            except: error = "Gateway timeout or something"
            if "incorrect data check" in error and not hasattr(self,"avoid_gzip") and enable_gzip:
                # Some versions of the GWAN server can send NUL bytes at the end of gzip data.  Retry without requesting gzip.
                self.avoid_gzip = True
                return self.sendRequest(converterFlags,viewSource,isProxyRequest,False)
            tryFetch = self.urlToFetch
            if self.isSslUpstream: tryFetch += " (upstream of "+options.upstream_proxy+")"
            elif options.upstream_proxy: tryFetch += " via "+options.upstream_proxy
            logging.error(error+" when fetching "+tryFetch) # better log it for the admin, especially if options.upstream_proxy, because it might be an upstream proxy malfunction
            error = """%s<h1>Error</h1>%s<br>Was trying to fetch %s<hr>This is %s</body></html>""" % (htmlhead("Error"),error,ampEncode(tryFetch),serverName_html)
            self.set_status(504)
            return self.doResponse2(error,True,False)
        if response.headers.get("Content-Encoding","")=="gzip": # sometimes Tornado's client doesn't decompress it for us, for some reason
            try: response.body = zlib.decompressobj().decompress(response.body,1048576*32) # 32M limit to avoid zip bombs (TODO adjust? what if exceeded?)
            except: pass
        if viewSource:
            def h2html(h): return "<br>".join("<b>"+txt2html(k)+"</b>: "+txt2html(v) for k,v in sorted(h.get_all()))
            r = "<html><head><title>Source of "+ampEncode(self.urlToFetch)+" - Web Adjuster</title></head><body>"
            if not js: r += "<a href=\"#1\">Headers sent</a> | <a href=\"#2\">Headers received</a> | <a href=\"#3\">Page source</a> | <a href=\"#4\">Bottom</a>"
            r += "<br>Fetched "+ampEncode(self.urlToFetch)
            if js: r += " <ul><li>using js_interpreter (see <a href=\"%s.screenshot\">screenshot</a>)</ul>" % self.urlToFetch
            else: r += "<h2><a name=\"1\"></a>Headers sent</h2>"+h2html(self.request.headers)+"<a name=\"2\"></a><h2>Headers received</h2>"+h2html(response.headers)+"<a name=\"3\"></a>"
            return self.doResponse2(r+"<h2>Page source</h2>"+txt2html(response.body)+"<hr><a name=\"4\"></a>This is "+serverName_html,True,False)
        headers_to_add = []
        if (do_pdftotext or do_epubtotext or do_epubtozip or do_mp3) and not response.headers.get("Location","") and response.headers.get("Content-type","").startswith("text/"):
          # We thought we were going to get a PDF etc that could be converted, but it looks like they just sent more HTML (perhaps a "which version of the PDF did you want" screen)
          do_pdftotext=do_epubtotext=do_epubtozip=do_mp3=False
        vary = response.headers.get("Vary","")
        cookie_host = self.cookie_host()
        doRedirect = ""
        for name,value in response.headers.get_all():
          if name.lower() in rmServerHeaders: continue
          elif (do_pdftotext or do_epubtotext) and name.lower() in ["content-disposition","content-type"]: continue # we're re-doing these also
          elif do_epubtozip and name.lower()=="content-disposition" and value.replace('"','').endswith(".epub"):
            epub = value.rfind(".epub")
            value=value[:epub]+".zip"+value[epub+5:]
          elif name.lower() in [
                  # Remote-server headers that need URLs rewriting (except Set-Cookie and Location which are handled separately below).
                  # (DON'T just say "all headers except some whitelist": somebody might put DTD URIs (or server/proxy documentation references) into headers and we want to leave those alone)
                  "access-control-allow-origin", # better rewrite this for JSON responses to scripts that are used on a site's other domains
                  "link", # RFC 5988 equivalent to link elements in body; includes preloads; might want to adjust the resulting CSS or scripts (especially if the server won't support a fetch from a browser that supplies us as Referer)
                  # "x-associated-content" # see comment in rmServerHeaders
                  ]: value=domain_process(value,cookie_host,True,https=self.urlToFetch.startswith("https"),isProxyRequest=isProxyRequest,isSslUpstream=self.isSslUpstream)
          elif name.lower()=="location": # TODO: do we need to delete this header if response.code not in [301,302,303,307] ?
            old_value_1 = value # before domain_process
            value=domain_process(value,cookie_host,True,https=self.urlToFetch.startswith("https"),isProxyRequest=isProxyRequest,isSslUpstream=self.isSslUpstream)
            offsite = (not isProxyRequest and value==old_value_1 and (value.startswith("http://") or value.startswith("https://"))) # i.e. domain_process didn't change it, and it's not relative
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
                # redirecting to somewhere we can't domain-proxy for, but we could follow the redirects ourselves to do the conversion (TODO: check options.prohibit against the redirects?) :
                return self.sendRequest(converterFlags,viewSource,isProxyRequest,follow_redirects=True)
                # TODO: if that sendRequest results in HTML, overriding the do_... options, the browser will end up with an incorrect idea of the current address; might want to detect this and give the user the unchanged Location: header
            else: doRedirect = value
            if cookie_host and (self.request.path=="/" or self.request.arguments.get(adjust_domain_cookieName,None)) and old_value_1.startswith("http") and not (old_value_1.startswith("http://"+cookie_host+"/") or (cookie_host.endswith(".0") and old_value_1.startswith("https://"+cookie_host[:-2]+"/"))):
                # This'll be a problem.  If the user is requesting / and the site's trying to redirect off-site, how do we know that the user isn't trying to get back to the URL box (having forgotten to clear the cookie) and now can't possibly do so because '/' always results in an off-site Location redirect ?
                # (DON'T just do this for just ANY offsite url when in cookie_host mode (except when also in htmlOnlyMode, see below) - it could mess up images and things.  (Could still mess up images etc if they're served from / with query parameters; for now we're assuming path=/ is a good condition to do this.  The whole cookie_host thing is a compromise anyway; wildcard_dns is better.)  Can however do it if adjust_domain_cookieName is in the arguments, since this should mean a URL has just been typed in.)
                if offsite:
                    # as cookie_host has been set, we know we CAN do this request if it were typed in directly....
                    value = "http://" + convert_to_requested_host(cookie_host,cookie_host) + "/?q=" + urllib.quote(old_value_1) + "&" + adjust_domain_cookieName + "=0" # go back to URL box and act as though this had been typed in
                    if self.htmlOnlyMode(): value += "&pr=on"
                    reason = "" # "which will be adjusted here, but you have to read the code to understand why it's necessary to follow an extra link in this case :-("
                else: reason=" which will be adjusted at %s (not here)" % (value[value.index('//')+2:(value+"/").index('/',value.index('/')+2)],)
                return self.doResponse2(("<html lang=\"en\"><body>The server is redirecting you to <a href=\"%s\">%s</a>%s.</body></html>" % (value,old_value_1,reason)),True,False) # and 'Back to URL box' link will be added
            elif cookie_host and offsite and self.htmlOnlyMode() and not options.htmlonly_css: # in HTML-only mode, it should never be an embedded image etc, so we should be able to change the current cookie domain unconditionally
                value = "http://" + convert_to_requested_host(cookie_host,cookie_host) + "/?q=" + urllib.quote(old_value_1) + "&" + adjust_domain_cookieName + "=0&pr=on" # as above
          elif "set-cookie" in name.lower():
            if not isProxyRequest: value=cookie_domain_process(value,cookie_host) # (never doing this if isProxyRequest, therefore don't have to worry about the upstream_rewrite_ssl exception that applies to normal domain_process isProxyRequest)
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
        try: self.set_status(response.code) # (not before here! as might return doResponse2 above which will need status 200.  Redirect without Location gets "unknown error 0x80072f76" on IEMobile 6.)
        except ValueError: self.set_status(response.code,"Unknown") # some Tornado versions raise ValueError if given a code they can't look up in a 'reason' dict
        if response.code >= 400 and response.body and response.body[:5].lower()=="<html": # some content distribution networks are misconfigured to serve their permission error messages with the Content-Type and Content-Disposition headers of the original file, so the browser won't realise it's HTML to be displayed if you try to fetch the link directly.  This should work around it (but should rarely be needed now that headResponse() is also 'aware' of this problem for redirectFiles)
            for name,value in headers_to_add:
                if name=='Content-Type' and not 'text/html' in value:
                    headers_to_add.remove((name,value))
                    headers_to_add.append(('Content-Type','text/html'))
                elif name=='Content-Disposition':
                    headers_to_add.remove((name,value))
        added = {'set-cookie':1} # might have been set by authenticates_ok
        if not self.isPjsUpstream and not self.isSslUpstream:
            if vary: vary += ", "
            vary += 'Cookie, User-Agent' # can affect adjuster settings (and just saying 'Vary: *' can sometimes be ignored on Android 4.4)
        if vary: headers_to_add.append(('Vary',vary))
        for name,value in headers_to_add:
          value = value.replace("\t"," ") # needed for some servers
          try:
            if name.lower() in added: self.add_header(name,value)
            else: self.set_header(name,value) # overriding any Tornado default
            added[name.lower()]=1
          except ValueError: pass # ignore unsafe header values
        if doRedirect:
            # ignore response.body and put our own in
            return self.redirect(doRedirect,response.code)
        body = response.body
        if not body or not self.canWriteBody(): return self.myfinish() # TODO: if canWriteBody() but not body and it's not just a redirect, set type to text/html and report empty?
        if do_html_process:
            # Normalise the character set
            charset2, body = get_and_remove_httpequiv_charset(body)
            if charset2: charset=charset2 # override server header (TODO: is this always correct?)
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
                if self.canWriteBody():
                    if newext==".mobi": self.write(txt)
                    else: self.write(remove_blanks_add_utf8_BOM(txt))
                self.myfinish()
            self.inProgress() # if appropriate
            if do_pdftotext:
                if options.pdfepubkeep: runFilter(("pdftotext -enc UTF-8 -nopgbrk \"%s\" \"%s.txt\"" % (f.name,f.name)),"",(lambda out,err:txtCallback(self,f.name,"pdftotext",out+err)), False)
                elif self.canWriteBody(): runFilter(("pdftotext -enc UTF-8 -nopgbrk \"%s\" -" % f.name),"",(lambda out,err:(unlink(f.name),self.write(remove_blanks_add_utf8_BOM(out)),self.myfinish())), False) # (pipe o/p from pdftotext directly, no temp outfile needed)
                else: self.myfinish()
            elif self.isKindle(): runFilter(("ebook-convert \"%s\" \"%s.mobi\"" % (f.name,f.name)),"",(lambda out,err:txtCallback(self,f.name,"ebook-convert",out+err)), False)
            else: runFilter(("ebook-convert \"%s\" \"%s.txt\"" % (f.name,f.name)),"",(lambda out,err:txtCallback(self,f.name,"ebook-convert",out+err)), False)
            return
        if do_domain_process and not isProxyRequest: body = domain_process(body,cookie_host,https=self.urlToFetch.startswith("https")) # first, so filters to run and scripts to add can mention new domains without these being redirected back
        # Must also do things like 'delete' BEFORE the filters, especially if lxml is in use and might change the code so the delete patterns aren't recognised.  But do JS process BEFORE delete, as might want to pick up on something that was there originally.  (Must do it AFTER domain process though.)
        if self.isPjsUpstream and do_html_process: # add a CSS rule to help with js_interpreter screenshots (especially if the image-display program shows transparent as a headache-inducing chequer board) - this rule MUST go first for the cascade to work
            i = htmlFind(body,"<head")
            if i==-1: i=htmlFind(body,"<html")
            if not i==-1: i = body.find('>',i)+1
            if i: body=body[:i]+"<style>html{background:#fff}</style>"+body[i:] # setting on 'html' rather than 'body' allows body bgcolor= to override.  (body background= is not supported in HTML5 and PhantomJS will ignore it anyway.)
        if self.isPjsUpstream or self.isSslUpstream: return self.doResponse3(body) # write & finish
        if do_js_process: body = js_process(body,self.urlToFetch)
        if not self.checkBrowser(options.deleteOmit):
            body = process_delete(body)
        if do_css_process:
            body = process_delete_css(body,self.urlToFetch)
        # OK to change the code now:
        adjustList = []
        if do_html_process:
          if self.htmlOnlyMode(isProxyRequest):
              if cookie_host:
                  adjustList.append(RewriteExternalLinks("http://" + convert_to_requested_host(cookie_host,cookie_host) + "/?"+adjust_domain_cookieName+"=0&pr=on&q="))
              if options.js_links:
                  if isProxyRequest: url = self.urlToFetch
                  else: url = domain_process(self.urlToFetch,cookie_host,True,self.urlToFetch.startswith("https"))
                  adjustList.append(AddClickCodes(url))
              adjustList.append(StripJSEtc(self.urlToFetch,transparent=self.auto_htmlOnlyMode(isProxyRequest)))
              if not options.htmlonly_css: adjustList.append(transform_in_selected_tag("style",lambda s:"",True)) # strips JS events also (TODO: support this in htmlonly_css ? although htmlonly_css is mostly a 'developer' option)
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
        if options.prominentNotice=="htmlFilter": callback = lambda out,err: self.doResponse2(body,do_html_process,do_json_process,out)
        else: callback = lambda out,err:self.doResponse2(out,do_html_process,do_json_process)
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
        if not options.htmlFilterName: return options.htmlFilter # unconditional
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
    def doResponse2(self,body,do_html_process,do_json_process,htmlFilterOutput=None):
        debuglog("doResponse2"+self.debugExtras())
        # 2nd stage (domain change and external filter
        # has been run) - now add scripts etc, and render
        canRender = options.render and (do_html_process or (do_json_process and options.htmlJson)) and not self.checkBrowser(options.renderOmit)
        jsCookieString = ';'.join(self.request.headers.get_list("Cookie"))
        if do_html_process: body = html_additions(body,self.cssAndAttrsToAdd(),self.checkBrowser(options.cssNameReload),self.cookieHostToSet(),jsCookieString,canRender,self.cookie_host(),self.is_password_domain,not do_html_process=="noFilterOptions",htmlFilterOutput) # noFilterOptions is used by bookmarklet code (to avoid confusion between filter options on current screen versus bookmarklets)
        if canRender and not "adjustNoRender=1" in jsCookieString:
            if do_html_process: func = find_text_in_HTML
            else: func=lambda body:find_HTML_in_JSON(body,find_text_in_HTML)
            debuglog("runFilterOnText Renderer"+self.debugExtras())
            runFilterOnText(lambda t:Renderer.getMarkup(ampDecode(t.decode('utf-8'))).encode('utf-8'),func(body),lambda out,err:self.doResponse3(out),not do_html_process,chr(0))
        else: self.doResponse3(body)
    def doResponse3(self,body):
        # 3rd stage (rendering has been done)
        debuglog(("doResponse3 (len=%d)" % len(body))+self.debugExtras())
        if self.canWriteBody(): self.write(body)
        self.myfinish()
    def sendHead(self,forPjs=False):
        # forPjs is for options.js_reproxy: we've identified the request as coming from js_interpreter and being its main document (not images etc).  Just check it's not a download link.
        # else for options.redirectFiles: it looks like we have a "no processing necessary" request that we can tell the browser to get from the real site.  But just confirm it's not a mis-named HTML document.
        body = self.request.body
        if not body: body = None
        if hasattr(self,"original_referer"): self.request.headers["Referer"],self.original_referer = self.original_referer,self.request.headers.get("Referer","") # we'll send the request with the user's original Referer, to check it still works
        ph,pp = upstream_proxy_host, upstream_proxy_port
        if dryrun_upstream_rewrite_ssl and pp and upstream_rewrite_ssl: pp += 1
        httpfetch(self.urlToFetch,
                  connect_timeout=60,request_timeout=120, # same TODO as above
                  proxy_host=ph, proxy_port=pp,
                  method="HEAD", headers=self.request.headers, body=body,
                  callback=lambda r:self.headResponse(r,forPjs),follow_redirects=True)
    def headResponse(self,response,forPjs):
        debuglog("headResponse "+repr(response.code)+self.debugExtras())
        if response.code == 503: # might be a cache error (check for things like X-Squid-Error ERR_DNS_FAIL 0 that can be due to a missing newline before the "never_direct allow all" after the "cache_peer" setting in Squid)
            for name,value in response.headers.get_all(): debuglog(name+": "+value)
        curlFinished()
        self.restore_request_headers()
        if hasattr(self,"original_referer"): # undo the change made above, in case it goes to sendRequest below
            self.request.headers["Referer"],self.original_referer = self.original_referer,self.request.headers.get("Referer","")
            if not self.request.headers.get("Referer",""): del self.request.headers["Referer"] # This line is relevant only if change_request_headers deleted it, i.e. the original request came from the URL box.  Why would anybody type a URL that fits options.redirectFiles?  3 reasons I can think of: (1) website has odd naming for its CGI scripts; (2) person is using privacy software that doesn't remove Referer but does truncate it; (2) person is trying to (mis)use the adjuster to retrieve a file by proxy w/out realising redirectFiles is set (this would get 500 server error on v0.202 but just a redirect on v0.203)
        if forPjs:
            reason = None
            if response.code < 300:
                for name,value in response.headers.get_all():
                    if name.lower()=="content-type":
                        value=value.lower()
                        if not value.startswith("text/"):
                            reason="it is neither HTML nor text" ; break
                    elif name.lower()=="content-disposition":
                        value=value.lower()
                        if value.startswith("attachment"):
                            reason="it is a download" ; break # TODO: could we just delete content-disposition and show it in the browser (it's usually for CSS/JS/etc)
            if not reason: return self.sendRequest([False]*4,False,True,follow_redirects=False)
            self.set_status(200)
            self.add_header("Content-Type","text/html")
            if self.canWriteBody(): self.write(htmlhead()+"js_interpreter cannot load "+ampEncode(self.urlToFetch)+" as "+reason+"</body></html>") # TODO: provide a direct link if the original request wasn't a proxy request?  (or even if it was a proxy request, give webdriver a placeholder (so it can still handle cookies etc) and bypass it with the actual response body?  but don't expect to load non-HTML files via PhantomJS: its currentUrl will be unchanged, sometimes from about:blank)
            self.myfinish() ; return
        might_need_processing_after_all = True
        if response.code < 400: # this 'if' is a workaround for content-distribution networks that misconfigure their servers to serve Referrer Denied messages as HTML without changing the Content-Type from the original file: if the code is >=400 then assume might_need_processing_after_all is True no matter what the Content-Type is
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
    def checkBrowser(self,blist,warn="{B}"):
        assert type(blist)==list # (if it's a string we don't know if we should check for just that string or if we should .split() it on something)
        ua = self.request.headers.get("User-Agent","")
        for b in blist:
            if b in ua: return warn.replace("{B}",b)
        return ""

the_duff_certfile = None
def duff_certfile():
    global the_duff_certfile
    if the_duff_certfile: return the_duff_certfile # (we don't need to worry about /tmp reaping here because we're called only twice at start)
    for n in ['/dev/shm/dummy.pem','/tmp/dummy.pem','dummy.pem']:
        try:
            # Here's one I made earlier, unsigned localhost:
            open(n,'w').write("""-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCrpSY8Ei98Vx3o
mdksXcaPdstvlL2xhRpRO6RNyL7rMc/bJWIscOVdm8OlxTlnQghJ/TW4X5InE6+X
dVbxGaEC3DYRcIJHvz7oD7myRD/xXbpWjPPkol4eVe2afyKeh7qJ8JQ9ayJCfFL2
Bj/yvqjls+eBYeJ7o0txw19r8T3zuplGhTPzz0sdV66i+9vzBWT80xqgZQm0Dtrw
09gpO3ya56JRwBIRSio6K17t4u8AFYIS+jcqApGNMeapnnopHB5ZQlopF/LApTsp
7MYSYaUxahLhYnqZ5Y3P32rES3DLlB9y94FT6wJi80H/tLzyS647NHlQ8ZQR+vKm
UjE//vzDAgMBAAECggEBAIeKmm7FTYo6oPuUwdIvGyUfAfbS1hjgqq+LEWv7IghI
BYNgOe4uGHGbFxxIadQIaNNEiK9XiOoiuX44wrcRLfw8ONX8qmRNuTc3c8Q58OSA
xyyhkdbyALCj2kUuMABP3hYfTHBTsXIfCsQMm2Ls/CKntiCNU3Oet2zWgvuSPQHB
BBqFRCf793GcTcmifhnj4xSCNa7tBUQgaz1ZDZMP0av5u6L4jfrxKy9fb8doLYx/
c7CwhRdhbIat51VBSMXHtl3fEQGfQnhiRLqHhzpo46kzdR0Y+sIh58aYIb3nkAa3
Z0fkq1hPubdBejKOZquJsXHDGfqOr/0hpKZlmILdUEECgYEA5BBeXgBGZu8tVHqE
yxO8YFGwbFqwHFSyIfegt8sYWTeh9wmBDHhqYRY5v/6iIUzLI44qjUjDXLZ1Ncyo
4P6EPlumCy6PDW4V5/vlOScB1YSKtk6Z7H5PpsWbBvb5dUjDhV4BHlkFscGMYAZf
8Ykd8lqHd/VYPL7JwSzreqXp920CgYEAwKuZP7R0RsUAIWFo5mNpKrJPyJU8Xbcv
2XllaOKkSEBaAv45KQmfct4pvXOMDCnd+hS3+Fq0cWKyLJfmnBl0oljrQ00VXGaF
XeFk+XWkmWjt7tVvMv6YRHhmdfnVdJMK8WJZL25Q56W9OX2A1WnPXctxJuKKcu2j
jSpctOXgNu8CgYA2EU9d97C5HIDhoz4yKtag+xzZQ1K3FLk6Zkt65zI5jH/gYidu
/mkx5SQByWtEe8E5B6482oA+TZ9SBtgOpyhQ5EdkJUCSzYNyAPzh5MaBiS+dctr4
/yUBA53yM8EGNh7sUlHvkOlRr/IIndpHF9u6pg2xub+WfyCzpGObKxRhrQKBgGGC
dzzWh0KJ0VcThZOUHFWPiPFrFfIYFA9scPZ0PdCTQPrizusGA7yO03EeWXKOfdlj
Qvheb5Qy7xnChuPZvj2r4uVczcLF4BlzSTc3YuaBRGnreyvDzixZAwISPwWQpakk
rR5kJm4WY34FFn7r3hcKL2oOnSMtQejf16t169PhAoGBAIBR/FskuCDgrS8tcSLd
ONeipyvxLONi3eKGWeWOPiMf97szZRCgQ9cX1sQ2c3SRFASdFXV5ujij2m9MepV5
EmpHS+6okHNIrxE01mMNV+/Y6KfZiqu9zKU5Qc2tEVaY+jE/wqMLIJsDE1pzu75t
JHCPQWkiQD78FvYsV/d6Qa9Q
-----END PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIIDgTCCAmmgAwIBAgIJAKqlaBInju0KMA0GCSqGSIb3DQEBCwUAMFYxCzAJBgNV
BAYTAlVLMRUwEwYDVQQHDAxEZWZhdWx0IENpdHkxHDAaBgNVBAoME0RlZmF1bHQg
Q29tcGFueSBMdGQxEjAQBgNVBAMMCWxvY2FsaG9zdDAgFw0xNzA2MDcxNDA0NTRa
GA8yMTE3MDUxNDE0MDQ1NFowVjELMAkGA1UEBhMCVUsxFTATBgNVBAcMDERlZmF1
bHQgQ2l0eTEcMBoGA1UECgwTRGVmYXVsdCBDb21wYW55IEx0ZDESMBAGA1UEAwwJ
bG9jYWxob3N0MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAq6UmPBIv
fFcd6JnZLF3Gj3bLb5S9sYUaUTukTci+6zHP2yViLHDlXZvDpcU5Z0IISf01uF+S
JxOvl3VW8RmhAtw2EXCCR78+6A+5skQ/8V26Vozz5KJeHlXtmn8inoe6ifCUPWsi
QnxS9gY/8r6o5bPngWHie6NLccNfa/E987qZRoUz889LHVeuovvb8wVk/NMaoGUJ
tA7a8NPYKTt8mueiUcASEUoqOite7eLvABWCEvo3KgKRjTHmqZ56KRweWUJaKRfy
wKU7KezGEmGlMWoS4WJ6meWNz99qxEtwy5QfcveBU+sCYvNB/7S88kuuOzR5UPGU
EfryplIxP/78wwIDAQABo1AwTjAdBgNVHQ4EFgQULMiW+U9eS7LNQrXfCfRLt/kD
p+wwHwYDVR0jBBgwFoAULMiW+U9eS7LNQrXfCfRLt/kDp+wwDAYDVR0TBAUwAwEB
/zANBgkqhkiG9w0BAQsFAAOCAQEAgIAkEKExjnVdiYsjQ8hqCVBLaZk2+x0VoROd
1/xZn9qAT0RsnoQ8De+xnOHxwmDMYNBQj3bIUXjc8XIUd0nZb9OYhIpj1OyggHfB
3KECnnm/mfbtv3jB1rilUnRTknRCwyVJetOpLVEJONP/qWVSD7y2nfcQIcilWPka
q/wcEZA7n1nzJetW6taOT/sx+E8JO2yawnvHoY7m7Zj7NIrsLCIyQlLZ0Xm/401s
rmHjGlInkZKbj3jEsGSxU4oKRDBM5syJgm1XYi5vPRNOUu4CXUGJAXhzJtd9teqB
8FHasZQjl5aqS0j2vPREQl6fnw4i9/sOBvgZLgw03XZXtXr6Ow==
-----END CERTIFICATE-----
""")
            the_duff_certfile = n ; return n
        except: continue
    raise Exception("Can't write the duff certificate anywhere?")

def MakeRequestForwarder(useSSL,connectPort,isPJS=False,start=0,index=0):
    class MyRequestForwarder(RequestForwarder):
        WA_UseSSL = useSSL
        WA_connectPort = connectPort
        isPjsUpstream = isPJS
        WA_PjsStart = start # (for multicore)
        WA_PjsIndex = index # (relative to start)
        isSslUpstream = False
    return MyRequestForwarder # the class, not an instance
def NormalRequestForwarder(): return MakeRequestForwarder(False,options.port+1)
def SSLRequestForwarder(): return MakeRequestForwarder(True,options.port+1)
def PjsRequestForwarder(start,index): return MakeRequestForwarder(False,js_proxy_port[start+index]+1,True,start,index)
def PjsSslRequestForwarder(start,index): return MakeRequestForwarder(True,js_proxy_port[start+index]+1,True,start,index)

class UpSslRequestForwarder(RequestForwarder):
    "A RequestForwarder for running upstream of upstream_proxy, rewriting its .0 requests back into SSL requests"
    WA_UseSSL = isPjsUpstream = False
    isSslUpstream = True

class SynchronousRequestForwarder(RequestForwarder):
   "A RequestForwarder for use in WSGI mode"
   WA_UseSSL = isPjsUpstream = isSslUpstream = False
   def get(self, *args, **kwargs):     return self.doReq()
   def head(self, *args, **kwargs):    return self.doReq()
   def post(self, *args, **kwargs):    return self.doReq()
   def put(self, *args, **kwargs):     return self.doReq()
   def delete(self, *args, **kwargs):  return self.doReq()
   def patch(self, *args, **kwargs):   return self.doReq()
   def options(self, *args, **kwargs): return self.doReq()
   def connect(self, *args, **kwargs): raise Exception("CONNECT is not implemented in WSGI mode")
   def myfinish(self): pass

class AliveResponder(RequestHandler):
    SUPPORTED_METHODS = ("GET",)
    def get(self, *args, **kwargs): self.write("1")

kept_tempfiles = {}

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
def htmlhead(title="Web Adjuster"): return '<html><head><title>%s</title><meta name="mobileoptimized" content="0"><meta name="viewport" content="width=device-width"></head><body>' % title
def urlbox_html(htmlonly_checked,cssOpts_html,default_url=""):
    r = htmlhead('Web Adjuster start page')+'<form action="/"><label for="q">'+options.boxPrompt+'</label>: <input type="text" id="q" name="q"'
    if default_url: r += ' value="'+default_url+'"'
    else: r += ' placeholder="http://"' # HTML5 (Firefox 4, Opera 11, MSIE 10, etc)
    r += '><input type="submit" value="Go">'+searchHelp()+cssOpts_html # 'go' button MUST be first, before cssOpts_html, because it's the button that's hit when Enter is pressed.  (So might as well make the below focus() script unconditional even if there's cssOpts_html.  Minor problem is searchHelp() might get in the way.)
    if enable_adjustDomainCookieName_URL_override and not options.wildcard_dns and "" in options.default_site.split("/"): r += '<input type="hidden" name="%s" value="%s">' % (adjust_domain_cookieName,adjust_domain_none) # so you can get back to the URL box via the Back button as long as you don't reload
    if htmlonly_checked: htmlonly_checked=' checked="checked"'
    else: htmlonly_checked = ""
    if options.htmlonly_mode:
        if not r.endswith("</p>"): r += "<br>"
        r += '<input type="checkbox" id="pr" name="pr"'+htmlonly_checked+'> <label for="pr">HTML-only mode</label>'
    if options.submitPath: r += '<p><input type="submit" name="sPath" value="Upload your own text"></p>'
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

rubyCss1 = "ruby{display:inline-table;vertical-align:bottom;-webkit-border-vertical-spacing:1px;padding-top:0.5ex;}ruby *{display: inline;vertical-align:top;line-height:1.0;text-indent:0;text-align:center;white-space:nowrap;}rb{display:table-row-group;font-size: 100%;}rt{display:table-header-group;font-size:100%;line-height:1.1;}"
rubyScript = '<style>'+rubyCss1+'</style>'
# And the following hack is to stop the styles in the 'noscript' and the variable (and any others) from being interpreted if an HTML document with this processing is accidentally referenced as a CSS source (which can mess up ruby):
rubyScript = "<!-- { } @media(none) { -->" + rubyScript
# By the way, also try to specify some nice fonts (but IE doesn't like this) :
rubyScript_fonts = '<!--[if !IE]>--><style>rt { font-family: Gandhari, DejaVu Sans, Lucida Sans Unicode, Times New Roman, serif !important; }</style><!--<![endif]-->'
rubyScript += rubyScript_fonts
# and this goes at the END of the body:
rubyEndScript = """
<script><!--
function treewalk(n) { var c=n.firstChild; while(c) { if (c.nodeType==1 && c.nodeName!="SCRIPT" && c.nodeName!="TEXTAREA" && !(c.nodeName=="A" && c.href)) { treewalk(c); if(c.nodeName=="RUBY" && c.title && !c.onclick) c.onclick=Function("alert(this.title)") } c=c.nextSibling; } } function tw() { treewalk(document.body); window.setTimeout(tw,5000); } treewalk(document.body); window.setTimeout(tw,1500);
//--></script>"""

def bookmarklet(submit_url,local_submit_url):
    # Returns JS code to write out the bookmarklet.
    # If options.submitBookmarkletDomain is set, submit_url should NOT include the location.protocol part.
    # Get the bookmarklet to fetch more JS and eval/exec it, seeing as it'll need to talk to the server anyway (avoids cluttering bookmarks / can fix bugs later)
    # TODO: ensure server response is cached!  last-modified when adjuster started ??
    # TODO: make sure submit_url doesn't contain anything that can't be embedded in ''s within ""s (this depends on the user's setting of options.submitPath! although anything 'nasty' could run into trouble with browser URL-escaping anyway)
    if not options.submitBookmarklet: return ""
    if not options.htmlFilterName: names=['filter']
    elif '#' in options.htmlFilter: names=options.htmlFilterName.split('#')[1:]
    else: names = [options.htmlFilterName]
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
    # noIOS spans added because the "Plus" bookmarklets say no "frames loophole" on any tested version of iOS
    if options.submitBookmarkletDomain: locProto = '(location.protocol=="https:"?"https:":"http:")+' # use http if it's file: etc
    else: locProto = ""
    return '<script><!--\nif(typeof XMLHttpRequest!="undefined"&&typeof JSON!="undefined"&&JSON.parse&&document.getElementById&&document.readyState!="complete"){var n=navigator.userAgent;var i=n.match(/iPhone/),a=n.match(/Android/),p=n.match(/iPad/),c="",t=0,j="javascript:",u="var r=new XMLHttpRequest();r.open(\'GET\','+locProto.replace('"',"'")+"'"+submit_url+'",v="\',false);r.send();eval(r.responseText)"; var u2=j+"if(window.doneMasterFrame!=1){var d=document;var b=d.body;var fs=d.createElement(\'frameset\'),h=d.createElement(\'html\');fs.appendChild(d.createElement(\'frame\'));fs.firstChild.src=self.location;while(b.firstChild)h.appendChild(b.removeChild(b.firstChild));b.appendChild(fs);window.doneMasterFrame=1;window.setTimeout(function(){if(!window.frames[0].document.body.innerHTML){var d=document;var b=d.body;while(b.firstChild)b.removeChild(b.firstChild);while(h.firstChild)b.appendChild(h.removeChild(h.firstChild));alert(\'The bookmarklet cannot annotate the whole site because your browser does not seem to have the frames loophole it needs. Falling back to annotating this page only. (To avoid this message in future, install the not Plus bookmarklet.)\')}},1000)}"+u+"B";u=j+u+"b";if(i||a||p){t="'+local_submit_url+'"+(i?"i":(p?"p":"a"));u="#"+u;u2="#"+u2}else c=" onclick=_IHQ_alert(\'To use this bookmarklet, first drag it to your browser toolbar. (If your browser does not have a toolbar, you probably have to paste text manually.)\');return false_IHQ_";document.write(((i||a||p)?"On "+(i?"iPhone":(p?"iPad":"Android"))+", you can install a special kind of bookmark (called a \'bookmarklet\'), and activate":"On some browsers, you can drag a \'bookmarklet\' to the toolbar, and press")+" it later to use this service on the text of another site. '+quote_for_JS_doublequotes(r'<span id="bookmarklet"><a href="#bookmarklet" onClick="document.getElementById('+"'bookmarklet'"+r').innerHTML=&@]@+@]@quot;<span class=noIOS>Basic bookmarklet'+plural(len(names))+' (to process <b>one page</b> when activated): </span>'+(' | '.join(('<a href="@]@+(t?(t+@]@'+c.noInc()+'@]@):\'\')+u+@]@'+c()+'@]@+v+@]@"@]@+c+@]@>'+name+'</a>') for name in names)).replace(r'"','_IHQ_')+c.reset()+'<span class=noIOS>. Advanced bookmarklet'+plural(len(names))+' (to process <b>a whole site</b> when activated, but with the side-effect of resetting the current page and getting the address bar \'stuck\'): '+(' | '.join(('<a href="@]@+(t?(t+@]@'+c.noInc()+'@]@):\'\')+u2+@]@'+c()+'@]@+v+@]@"@]@+c+@]@>'+name+'+</a>') for name in names)).replace(r'"','_IHQ_')+'</span>&@]@+@]@quot;.replace(/_IHQ_/g,\'&@]@+@]@quot;\');return false">Show bookmarklet'+plural(len(names))+'</a></span>').replace('@]@','"')+'");if(i||p) document.write("<style>.noIOS{display:none;visibility:hidden}</style>")}\n//--></script>' # JSON.parse is needed (rather than just using eval) because we'll also need JSON.stringify (TODO: unless we fall back to our own slower encoding; TODO: could also have a non-getElementById fallback that doesn't hide the bookmarklets)
    # 'loophole': https://bugzilla.mozilla.org/show_bug.cgi?id=1123694 (+ 'seem to' because I don't know if the timeout value is enough; however we don't want it to hang around too long) (don't do else h=null if successful because someone else may hv used that var?)
    # 'resetting the current page': so you lose anything you typed in text boxes etc
    # (DO hide bookmarklets by default, because don't want to confuse users if they're named the same as the immediate-action filter selections at the bottom of the page)
    # TODO: maybe document that on Chrome Mobile (Android/iOS) you can tap address bar and start typing the bookmarklet name IF you've sync'd it from a desktop
    # TODO: we append '+' to the names of the 'advanced' versions of the bookmarklets, but we don't do so on the Android/iOS title pages; is that OK?
def quote_for_JS_doublequotes(s): return s.replace("\\","\\\\").replace('"',"\\\"").replace("\n","\\n").replace('</','<"+"/') # for use inside document.write("") etc
def bookmarkletMainScript(jsonPostUrl,forceSameWindow):
    if forceSameWindow: xtra = "if(c.target=='_blank') c.removeAttribute('target'); "
    else: xtra = ""
    # HTMLSizeChanged in the below calls callback the NEXT time HTML size is changed, and then stops checking.  The expectation is that HTMLSizeChanged will be called again to set up change monitoring again after the callback has made its own modifications.
    # innerHTML size will usually change if there's a JS popup etc (TODO: could periodically do a full scan anyway, on the off-chance that some JS change somehow keeps length the same); sizeChangedLoop is an ID so we can stop our checking loop if for any reason HTMLSizeChanged is called again while we're still checking (e.g. user restarts the bookmarklet, or callback is called by MutationObserver - we assume JS runs only one callback at a time).
    # MutationObserver gives faster response times when supported, but might not respond to ALL events on all browsers, so we keep the size check as well.
    if options.submitBookmarkletDomain: locProto = '(location.protocol=="https:"?"https:":"http:")+'
    else: locProto = ""
    return r"""var leaveTags=%s,stripTags=%s;
function HTMLSizeChanged(callback) {
  if(typeof window.sizeChangedLoop=="undefined") window.sizeChangedLoop=0; var me=++window.sizeChangedLoop;
  var getLen = function(w) { var r=0; if(w.frames && w.frames.length) { var i; for(i=0; i<w.frames.length; i++) r+=getLen(w.frames[i]) } if(w.document && w.document.body && w.document.body.innerHTML) r+=w.document.body.innerHTML.length; return r };
  var curLen=getLen(window),
    stFunc=function(){window.setTimeout(tFunc,1000)},
    tFunc=function(){if(window.sizeChangedLoop==me){if(getLen(window)==curLen) stFunc(); else callback()}};
  stFunc(); var m=window.MutationObserver||window.WebKitMutationObserver; if(m) new m(function(mut,obs){if(mut[0].type=="childList"){obs.disconnect();if(window.sizeChangedLoop==me)callback()}}).observe(document.body,{childList:true,subtree:true})
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
    r.open("POST",%s"%s",false);
    r.send(JSON.stringify(texts));
    replacements = JSON.parse(r.responseText);
    if (replacements.length >= texts.length) {
      oldTexts = texts; tw0();
    } else break; // TODO: handle as error?
    %s
  }
  HTMLSizeChanged(adjusterScan)
}
function walk(n,document) {
  var c=n.firstChild;
  while(c) {
    var ps = c.previousSibling, cNext = c.nextSibling;
    function isTxt(n) {return n && n.nodeType==3 && n.nodeValue && !n.nodeValue.match(/^"\s*$/)};
    if (isTxt(cNext) && isTxt(ps)) {
    var awkwardSpan = (c.nodeType==1 && c.nodeName=='SPAN' && c.childNodes.length<=1 && (!c.firstChild || (c.firstChild.nodeValue && c.firstChild.nodeValue.match(/^\s*$/))));
    if (c.nodeType==1 && stripTags.indexOf(c.nodeName)!=-1 || awkwardSpan) { // TODO: this JS code strips more stripTags than the Python shouldStripTag stuff does
      while (c.firstChild && !awkwardSpan) {
        var tmp = c.firstChild; c.removeChild(tmp);
        n.insertBefore(tmp,c);
      }
      n.removeChild(c);
      cNext.previousSibling.nodeValue += cNext.nodeValue;
      n.removeChild(cNext); cNext = ps
    }
    }
    c=cNext;
  }
  c=n.firstChild;
  while(c) {
    var cNext = c.nextSibling;
    switch (c.nodeType) {
    case 1: if (leaveTags.indexOf(c.nodeName)==-1 && c.className!="_adjust0") walk(c,document); %sbreak;
    case 3:
      if (%s) {
          var cnv = c.nodeValue.replace(/\u200b/g,''); // for some sites that use zero-width spaces between words that can upset some annotators (TODO: document, and add to Python version also)
          var i=otPtr;
          while (i<oldTexts.length && oldTexts[i]!=cnv) i++;
          if(i<replacements.length) {
            var newNode=document.createElement("span");
            newNode.className="_adjust0";
            n.replaceChild(newNode, c);
            newNode.innerHTML=replacements[i]; otPtr=i;
          } else if (tLen < %d) {
            texts[texts.length]=cnv;
            tLen += cnv.length;
          } else return; // will deal with rest next pass
      }
    }
    c=cNext;
  }
}adjusterScan();%s""" % (repr([t.upper() for t in options.leaveTags]),repr([t.upper() for t in options.stripTags]),locProto,jsonPostUrl,addRubyScript(),xtra,options.submitBookmarkletFilterJS,options.submitBookmarkletChunkSize,rubyEndScript[rubyEndScript.index("<!--")+4:rubyEndScript.rindex("//-->")]) # TODO: addRubyScript and rubyEndScript optional? (needed only if the filter is likely to use ruby); duplicate rubyEndScript added because at least some browsers don't seem to execute it when set as innerHTML by the all_frames_docs call in addRubyScript below, so at least we can do it here in the current frame
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

    # (Note: replaced by sync_runFilter when in WSGI mode)
    
    # runs shell command 'cmd' on input 'text' in a new
    # thread, then gets Tornado to call callback(out,err)
    # If 'cmd' is not a string, assumes it's a function
    # to call (no new thread necessary, TODO: Jython/SMP)
    # this is for using runFilterOnText with an internal
    # callable such as the Renderer.  Similarly if 'cmd'
    # starts with a * then we assume the rest is the name
    # of a Python function to call on the text.  And if it
    # starts with http(s?):// then we assume it's a back-end
    # server to query.
    if not cmd: return callback(text,"") # null filter, e.g. render-only submitPage
    if type(cmd)==type("") and cmd.startswith("*"):
        cmd = eval(cmd[1:]) # (normally a function name, but any Python expression that evaluates to a callable is OK, TODO: document this?  and incidentally if it evaluates to a string that's OK as well; the string will be given to an external command)
    if not type(cmd)==type(""):
        if wsgi_mode: return callback(cmd(text),"")
        # else use a slightly more roundabout version to give watchdog ping a chance to work between cmd and callback:
        out = cmd(text)
        return IOLoop.instance().add_timeout(time.time(),lambda *args:callback(out,""))
    elif cmd.startswith("http://") or cmd.startswith("https://"):
        return httpfetch(cmd,method="POST",body=text,callback=lambda r:(curlFinished(),callback(r.body,"")))
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
    if not cmd: return callback(text,"")
    if type(cmd)==type("") and cmd.startswith("*"):
        cmd = eval(cmd[1:])
    if not type(cmd)==type(""): out,err = cmd(text),""
    elif cmd.startswith("http://") or cmd.startswith("https://"):
        return httpfetch(cmd,method="POST",body=text,callback=lambda r:callback(r.body,""))
    else:
        sp=subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=textmode) # TODO: check shell=True won't throw error on Windows
        out,err = sp.communicate(text)
        if not out: out=""
        if not err: err="" # TODO: else logging.debug ? (some stderr might be harmless; don't want to fill normal logs)
    callback(out,err)

def runBrowser(*args):
    mainPid = os.getpid()
    def browser_thread():
        global helper_thread_count
        helper_thread_count += 1
        os.system(options.browser)
        helper_thread_count -= 1
        if options.multicore: # main thread will still be in start_multicore, not IOLoop
            global interruptReason
            interruptReason = "Browser command finished"
            os.kill(mainPid,signal.SIGINT)
        else: stopServer("Browser command finished")
    threading.Thread(target=browser_thread,args=()).start()
def runRun(*args):
    def runner_thread():
        global helper_thread_count
        helper_thread_count += 1
        global exitting ; exitting = 0
        while True:
            startTime = time.time()
            sp=subprocess.Popen(options.run,shell=True,stdin=subprocess.PIPE)
            global runningPid ; runningPid = sp.pid
            ret = sp.wait()
            if exitting: break
            if time.time() < startTime + 5:
                logging.info("run command exitted after only %d seconds" % (time.time() - startTime))
                logging.info("run: trying to catch errors with subprocess.communicate")
                sp=subprocess.Popen(options.run,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                stdout,stderr = sp.communicate()
                logging.info("run: stdout="+repr(stdout)+" stderr="+repr(stderr))
            time.sleep(options.runWait)
            if exitting: break
            logging.info("Restarting run command after %dsec (last exit = %d)" % (options.runWait,ret))
        helper_thread_count -= 1
    threading.Thread(target=runner_thread,args=()).start()
def setupRunAndBrowser():
    if options.browser: IOLoop.instance().add_callback(runBrowser)
    if options.run: IOLoop.instance().add_callback(runRun)

def stopServer(reason=None):
    def stop(*args):
        if reason and not reason=="SIG*" and not coreNo:
            # logging from signal handler is not safe, so we
            # defer it until this inner function is called
            if options.background: logging.info(reason)
            else: sys.stderr.write(reason+"\n")
        IOLoop.instance().stop()
    if reason.startswith("SIG") and hasattr(IOLoop.instance(),"add_callback_from_signal"): IOLoop.instance().add_callback_from_signal(stop)
    else: IOLoop.instance().add_callback(stop)

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
                    r.append(maybeEsc(separator.join(rpl.replace(chr(0),"&lt;NUL&gt;") for rpl in replacements[rLine:rLine+cl]))) # there shouldn't be any chr(0)s in the o/p, but if there are, don't let them confuse things
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

def get_and_remove_httpequiv_charset(body):
    charset,tagStart,tagEnd = get_httpequiv_charset(body)
    if charset: body = body[:tagStart]+body[tagEnd:]
    if body.startswith('<?xml version="1.0" encoding'): body = '<?xml version="1.0"'+body[body.find("?>"):] # TODO: honour THIS 'encoding'?  anyway remove it because we've changed it to utf-8 (and if we're using LXML it would get a 'unicode strings with encoding not supported' exception)
    return charset, body

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
            if l.startswith("http://") or l.startswith("https://"):
                if not self.offsite_ok and not url_is_ours(l): return # "offsite" link, can't process (TODO: unless we send it to ourselves via an alternate syntax)
                # TODO: (if don't implement processing the link anyway) insert explanatory text for why an alternate link wasn't provided?
            elif options.mailtoPath and l.startswith("mailto:"):
                newAttrs = []
                for k,v in items(attrs):
                    if k.lower()=="href": v=options.mailtoPath+v[7:].replace('%','%%+') # see comments in serve_mailtoPage
                    newAttrs.append((k,v))
                return (tag,newAttrs)
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
    # Doesn't have to strip style= and on...= attributes (we'll do that separately) but DOES have to strip javascript: links when AddClickCodes isn't doing it (when AddClickCodes is doing it, we'll just see the PLACEHOLDER which hasn't yet been patched up, so let AddClickCodes do it itself in that case)
    # TODO: change any "[if IE" at the start of comments, in case anyone using affected versions of IE wants to use this mode
    def __init__(self,url,transparent):
        self.url,self.transparent = url,transparent
    def init(self,parser):
        self.parser = parser
        self.suppressing = False
    def handle_starttag(self, tag, attrs):
        if tag=="img" and not options.htmlonly_css:
            self.parser.addDataFromTagHandler(dict(attrs).get("alt",""),1)
            return True
        elif tag=='script' or (tag=="noscript" and options.js_interpreter) or (tag=='style' and not options.htmlonly_css): # (in js_interpreter mode we want to suppress 'noscript' alternatives to document.write()s or we'll get both; anyway some versions of PhantomJS will ampersand-encode anything inside 'noscript' when we call find_element_by_xpath)
            self.suppressing = True ; return True
        elif tag=="body":
            if not self.transparent:
                self.parser.addDataFromTagHandler('HTML-only mode. <a href="%s">Settings</a> | <a rel="noreferrer" href="%s">Original site</a><p>' % ("http://"+hostSuffix()+publicPortStr()+"/?d="+urllib.quote(self.url),self.url)) # TODO: document that htmlonly_mode adds this (can save having to 'hack URLs' if using HTML-only mode with bookmarks, RSS feeds etc)
                # TODO: call request_no_external_referer() on the RequestForwarder as well? (may need a parameter for it)
            return
        elif tag=="a" and not self.suppressing:
            attrsD = dict(attrs)
            if attrsD.get("href","").startswith("javascript:"):
                attrsD["href"] = "#" ; return tag,attrsD
        return self.suppressing or tag=='noscript' or (tag=='link' and not options.htmlonly_css)
    def handle_endtag(self, tag):
        if tag=="head":
            self.parser.addDataFromTagHandler('<meta name="mobileoptimized" content="0"><meta name="viewport" content="width=device-width"></head>',True) # TODO: document that htmlonly_mode adds this; might also want to have it when CSS is on
            return True # suppress </head> because we've done it ourselves in the above (had to or addDataFromTagHandler would have added it AFTER the closing tag)
        if tag=='script' or (tag=='style' and not options.htmlonly_css) or (tag=="noscript" and options.js_interpreter):
            self.suppressing = False ; return True
        elif tag=='noscript': return True
        else: return self.suppressing
    def handle_data(self,data):
        if self.suppressing: return ""

class RewriteExternalLinks: # for use with cookie_host in htmlOnlyMode (will probably break the site's scripts in non-htmlOnly): make external links go back to URL box and act as though the link had been typed in.  TODO: rewrite ALL links so history works (and don't need a whole domain, like the old Web Access Gateway)? but if doing that, wld hv to deal w.relative links (whether or not starting with a / ) & base href.
    def __init__(self, rqPrefix): self.rqPrefix = rqPrefix
    def init(self,parser): self.parser = parser
    def handle_starttag(self, tag, attrs):
        if tag=="a":
            attrsD = dict(attrs)
            hr = attrsD.get("href","")
            if (hr.startswith("http://") and not url_is_ours(hr)) or hr.startswith("https://"):
              attrsD["href"]=self.rqPrefix + urllib.quote(hr)
              return tag,attrsD
    def handle_endtag(self, tag): pass
    def handle_data(self,data): pass

def guessCMS(url,fmt):
    # (TODO: more possibilities for this?  Option to HEAD all urls and return what they resolve to? but fetch-ahead might not be a good idea on all sites)
    return fmt and options.guessCMS and "?" in url and "format="+fmt in url.lower() and not ((not fmt=="pdf") and "pdf" in url.lower())

def check_LXML():
    # Might not find ALL problems with lxml installations, but at least we can check some basics
    global etree, StringIO
    try:
        from lxml import etree
        from StringIO import StringIO # not cStringIO, need Unicode
        return etree.HTMLParser(target=None) # works on lxml 2.3.2
    except ImportError: sys.stderr.write("LXML library not found - ignoring useLXML option\n")
    except TypeError: sys.stderr.write("LXML library too old - ignoring useLXML option\n") # no target= option in 1.x
    options.useLXML = False

def HTML_adjust_svc(htmlStr,adjustList,can_use_LXML=True):
    # Runs an HTMLParser on htmlStr, calling multiple adjusters on adjustList.
    # Faster than running the HTMLParser separately for each adjuster,
    # but still limited (find_text_in_HTML is still separate)
    if options.useLXML and can_use_LXML: return HTML_adjust_svc_LXML(htmlStr,adjustList)
    class Parser(HTMLParser):
        def handle_starttag(self, tag, att):
            changed = False
            for l in adjustList:
                r = l.handle_starttag(tag,att)
                if r==True: return self.suppressTag()
                elif r: (tag,att),changed = r,True
            if changed:
                self.addDataFromTagHandler(encodeTag(tag,att),True)
                return self.suppressTag() # original tag
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
        def handle_entityref(self,name):
            if any(l.handle_data('-')=="" for l in adjustList): # suppress entities when necessary, e.g. when suppressing noscript in js_interpreter-processed pages
                dataStart = self.getBytePos()
                self.out.append(htmlStr[self.lastStart:dataStart])
                self.lastStart = dataStart+len(name)+2
        def handle_charref(self,name):
            if any(l.handle_data('-')=="" for l in adjustList): # ditto
                dataStart = self.getBytePos()
                self.out.append(htmlStr[self.lastStart:dataStart])
                self.lastStart = dataStart+len(name)+3
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
    try: return "".join(parser.out)
    except UnicodeDecodeError: raise Exception("This should never happen: how did some of parser.out become Unicode when we were working in byte strings? repr: "+repr(parser.out))

def encodeTag(tag,att):
    def encAtt(a,v):
        if v:
            v=v.replace('&','&amp;').replace('"','&quot;')
            if not re.search('[^A-Za-z_]',v): return a+'='+v # no quotes needed (TODO: option to keep it valid?)
            return a+'="'+v+'"'
        else: return a
    return "<"+tag+"".join((" "+encAtt(a,v)) for a,v in items(att))+">"

html_tags_not_needing_ends = set(['area','base','basefont','br','hr','input','img','link','meta'])

def HTML_adjust_svc_LXML(htmlStr,adjustList):
    class Parser:
        def start(self, tag, att):
            att=dict((k,v.encode('utf-8')) for k,v in dict(att).items()) # so latin1decode doesn't pick up on it
            i = len(self.out)
            for l in adjustList:
                r = l.handle_starttag(tag,att)
                if r==True: return # suppress the tag
                elif r: tag,att = r
            self.out.insert(i,encodeTag(tag,att))
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

def transform_in_selected_tag(intag,transformFunc,events=False):
    # assumes intag is closed and not nested, e.g. style, although small tags appearing inside it MIGHT work
    # also assumes transformFunc doesn't need to know about entity references etc (it's called for the data between them)
    if intag=="script": events=True # can also set events=True for style if want to strip JS events while stripping style
    class Adjustment:
        def init(self,parser):
            self.intag = False
            self.parser = parser
        def handle_starttag(self, tag, attrs):
            if tag==intag: self.intag=True
            elif intag in ["script","style"]:
              changed = False ; r=[]
              for k,v in items(attrs):
                  if k==intag or (events and k.startswith("on")) or (intag=="script" and k=="id"):
                      v2 = transformFunc(v)
                      if not v2 and k=="id": v2 = v # don't change IDs just because we're removing scripts altogether
                      changed = changed or not v==v2
                      if v2: r.append((k,v2))
                  else: r.append((k,v))
              if changed: return (tag,r)
        def handle_endtag(self, tag):
            if tag==intag: self.intag=False
        def handle_data(self,data):
            if self.intag:
                return transformFunc(data)
    return Adjustment()

class AddClickCodes:
    # add webdriver_click_code + clickID before any #
    # don't put & or = in it due to checkViewsource's arglist processing, try ;id or -txt
    def __init__(self,url): self.url = url
    def init(self,parser):
        self.parser = parser
        self.linkStart = self.href = None
        self.linkTexts = set() ; self.inA = 0
    def handle_starttag(self, tag, attrs):
        if not tag=="a": return
        if self.inA==0: self.currentLinkText = ""
        self.inA += 1
        attrsD = dict(attrs)
        if not ("onclick" in attrsD or attrsD.get("href","").startswith("javascript:")): return # not a js link
        href = attrsD.get("href","")
        if '#' in href: href = href[href.index('#'):]
        else: href = ""
        if "id" in attrsD: # we can rewrite it straight away
            attrsD["href"] = self.url + webdriver_click_code + ';' + attrsD["id"] + href
        else: # we have to wait to see the text inside it
            self.linkStart = len(self.parser.out) # assumes further processing hasn't already appended anything
            self.href = href
            self.original_href = attrsD.get("href","#")
            if self.original_href.startswith("javascript:"): self.original_href = "#" # take it out
            attrsD["href"] = '"PLACEHOLDER"' + webdriver_click_code # make sure there's quotes in the placeholder so we always get quoted by encAtt (simplifies the back-off replace below)
        return tag, attrsD
    def handle_endtag(self, tag):
        if not tag=="a": return
        self.inA = max(self.inA-1,0)
        if not self.linkStart: return
        # DON'T try to write 'shortest unique text', because
        # that can change if another link is clicked (e.g. if
        # clicking the other link makes it disappear) and we
        # don't know what state the page will be in + could
        # end up with duplicate URLs.  Write full link text.
        if self.currentLinkText in self.linkTexts: replaceWith = self.original_href.replace('&','&amp;').replace('"','&quot;') # oops, not unique, back off
        else: replaceWith = self.url + webdriver_click_code + '-' + self.currentLinkText + self.href
        self.linkTexts.add(self.currentLinkText)
        self.parser.out[self.linkStart] = self.parser.out[self.linkStart].replace('&quot;PLACEHOLDER&quot;' + webdriver_click_code,replaceWith)
        self.linkStart = None ; self.currentLinkText = ""
    def handle_data(self,data):
        if self.inA==1: self.currentLinkText += data

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
            if name in htmlentitydefs.name2codepoint and not name in ['lt','gt','amp']: self.handle_data(unichr(htmlentitydefs.name2codepoint[name]).encode('utf-8'),len(name)+2)
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
    class Parser:
        def shouldStripTag(self,tag):
            self.ignoredLastTag = (tag.lower() in options.stripTags and (self.ignoredLastTag or not self.out))
            return self.ignoredLastTag
        def start(self, tag, attrs):
            sst = self.shouldStripTag(tag)
            self.out.append(encodeTag(tag,dict((k,v.encode('utf-8')) for k,v in dict(attrs).items())))
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

def domain_process(text,cookieHost=None,stopAtOne=False,https=None,isProxyRequest=False,isSslUpstream=False):
    if isProxyRequest: # called for Location: headers etc (not for document bodies)
        if upstream_rewrite_ssl and not isSslUpstream:
            # Although we don't need a full domain_process when the client is sending us a proxy request, we still have to beware of our UPstream proxy saying .0 in a Location: URL due to upstream_rewrite_ssl: take it out
            m = re.match(r"http(://[A-Za-z0-9.-]*)\.0(?![A-Za-z0-9.-])",text)
            if m: return "https"+m.group(1)
        return text
    # Change the domains on appropriate http:// and https:// URLs.
    # Also on // URLs using 'https' as default (if it's not None).
    # Hope that there aren't any JS-computed links where
    # the domain is part of the computation.
    # TODO: what of links to alternate ports or user:password links, currently we leave them unchanged (could use .<portNo> as an extension of the 'HTTPS hack' of .0, but allowing the public to request connects to any port could be a problem, and IP addresses would have to be handled carefully: can no longer rely on ".0 used to mean the network" sort-of saving us)
    # TODO: leave alone URLs in HTML text/comments and JS comments? but script overload can make it hard to judge what is and isn't text. (NB this function is also called for Location headers)
    if "<!DOCTYPE" in text:
        # don't touch URLs inside the doctype!
        dtStart = text.index("<!DOCTYPE")
        dtEnd = text.find(">",dtStart)
    else: dtStart = dtEnd = -1
    def mFunc(m):
        if dtStart<m.start()<dtEnd: return m.group() # avoid doctype
        i = m.start()
        if i and text[i-1].split() and text[:i].rsplit(None,1)[-1].startswith("xmlns"): return m.group() # avoid xmlns="... xmlns:elementname='... etc
        protocol,oldhost = m.groups()
        if oldhost[-1] in ".-": return m.group() # omit links ending with . or - because they're likely to be part of a domain computation; such things are tricky but might be more likely to work if we DON'T touch them if it has e.g. "'test.'+domain" where "domain" is a variable that we've previously intercepted
        if protocol=="//":
            if https: protocol = "https://"
            else: protocol = "http://"
        if protocol=="https://": oldhost += ".0" # HTTPS hack (see protocolAndHost)
        newHP = "http://" + convert_to_requested_host(oldhost,cookieHost) # TODO: unless using https to communicate with the adjuster itself, in which case would either have to run a server with certificates set up or make it a WSGI-etc script running on one, and if that's the case then might wish to check through the rest of the code (search http://) to ensure this would always work well
        if newHP.endswith(".0"): return m.group() # undo HTTPS hack if we have no wildcard_dns and convert_to_requested_host sent that URL off-site
        return newHP
    if stopAtOne: count=1
    else: count=0
    return re.sub(r"((?:https?://)|(?:(?<=['"+'"'+r"])//))([A-Za-z0-9.-]+)(?=[/?'"+'"'+r"]|$)",mFunc,text,count) # http:// https:// or "// in scripts (but TODO: it won't pick up things like host="www.example.com"; return "https://"+host, also what about embedded IPv6 addresses i.e. \[[0-9a-fA-F:]*\] in place of hostnames (and what should we rewrite them to?)  Hopefully IPv6-embedding is rare as such sites wouldn't be usable by IPv4-only users (although somebody might have IPv6-specific versions of their pages/servers); if making Web Adjuster IPv6 ready, also need to check all instances of using ':' to split host from port as this won't be the case if host is '[' + IPv6 + ']'.  Splitting off hostname from protocol is more common though, e.g. used in Google advertising iframes 2017-06)

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
        if newhost==text[i:j] and cookieHost and cookieHost.endswith(text[i:j]): newhost = convert_to_requested_host(cookieHost,cookieHost) # cookie set server.example.org instead of www.server.example.org; we can deal with that
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
        times = None
        if prefix.startswith('*'): cond = (prefix[1:] in body)
        elif '#' in prefix:
                i = prefix.index('#')
                cond = (url == prefix[:i])
                try: times = int(prefix[i+1:])
                except: pass
        else: cond = url.startswith(prefix)
        if cond:
            if times: body=body.replace(srch,rplac,times)
            else: body=body.replace(srch,rplac)
    return body

def process_delete(body):
    for d in options.delete:
        body=re.sub(d,"",body)
    if options.delete_doctype:
        body=re.sub("^<![dD][oO][cC][tT][yY][pP][eE][^>]*>","",body,1)
    return body

def process_delete_css(body,url):
    for d in options.delete_css:
        if '@@' in d: # it's a replace, not a delete
            s,r = d.split('@@',1)
            if '@@' in r: # replace only for certain URLs
                r,urlPart = r.split('@@',1)
                if not urlPart in url:
                    continue # skip this rule
            body = re.sub(s,r,body)
        else: body=re.sub(d,"",body)
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

def htmlFind(html,markup):
    # basically html.lower().find(markup), but we need to be
    # aware of things like Tencent's <!--headTrap<body></body><head></head><html></html>-->
    # preferably without running a slow full parser
    r = html.lower().find(markup)
    if r<0: return r
    c = html.find("<!--")
    if c<0 or c>r: return r
    # If gets here, we might have a headTrap situation
    def blankOut(m): return " "*(m.end()-m.start())
    return re.sub("<!--.*?-->",blankOut,html,flags=re.DOTALL).lower().find(markup) # TODO: improve efficiency of this? (blankOut doesn't need to go through the entire document)

def html_additions(html,(cssToAdd,attrsToAdd),slow_CSS_switch,cookieHostToSet,jsCookieString,canRender,cookie_host,is_password_domain,addHtmlFilterOptions,htmlFilterOutput):
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
    if options.htmlFilterName and options.htmlFilter and addHtmlFilterOptions:
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
//--></script><noscript><a href="http://%s/?%s=%s">Back to URL box</a></noscript>""" % (detect_iframe,cookieHostToSet+publicPortStr(),adjust_domain_cookieName,adjust_domain_none,cookieHostToSet+publicPortStr(),adjust_domain_cookieName,adjust_domain_none)
        else: bodyAppend += r"""<script><!--
if(!%s&&document.readyState!='complete')document.write('<a href="javascript:document.cookie=\'%s=%s;expires=%s;path=/\';if(location.href==\'http://%s/\')location.reload(true);else location.href=\'http://%s/?nocache=\'+Math.random()">Back to URL box<\/a>')
//--></script>""" % (detect_iframe,adjust_domain_cookieName,adjust_domain_none,cookieExpires,cookieHostToSet+publicPortStr(),cookieHostToSet+publicPortStr()) # (we should KNOW if location.href is already that, and can write the conditional here not in that 'if', but they might bookmark the link or something)
    if options.headAppend: headAppend += options.headAppend
    if options.headAppendRuby: bodyPrepend += rubyScript
    if options.prominentNotice=="htmlFilter": pn = htmlFilterOutput
    elif options.prominentNotice and not is_password_domain: pn = options.prominentNotice
    else: pn = None
    if pn:
        # if JS is available, use fixed positioning (so it still works on sites that do that, in case we're not overriding it via user CSS) and a JS acknowledge button
        styleAttrib="style=\"width: 80% !important; margin: 10%; border: red solid !important; background: black !important; color: white !important; text-align: center !important; display: block !important; left:0px; top:0px; z-index:2147483647; -moz-opacity: 1 !important; filter: none !important; opacity: 1 !important; visibility: visible !important; max-height: 80% !important; overflow: auto !important; \""
        if slow_CSS_switch: # use a slow version for this as well (TODO document that we do this?) (TODO the detect_iframe exclusion of the whole message)
            if not "_WA_warnOK=1" in jsCookieString: bodyPrepend += "<div id=_WA_warn0 "+styleAttrib+">"+pn+r"""<script><!--
if(document.readyState!='complete'&&document.cookie.indexOf("_WA_warnOK=1")==-1)document.write("<br><button style=\"color: black !important;background:#c0c0c0 !important;border: white solid !important\" onClick=\"document.cookie='_WA_warnOK=1;path=/';location.reload(true)\">Acknowledge<\/button>")
//--></script></div><script><!--
if(document.getElementById) document.getElementById('_WA_warn0').style.position="fixed"
}
//--></script>"""
            #" # (this comment helps XEmacs21's syntax highlighting)
        else: bodyPrepend += "<div id=_WA_warn0 "+styleAttrib+">"+pn+r"""</div><script><!--
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
        if options.prominentNotice=="htmlFilter": bodyPrepend = bodyPrepend.replace("document.cookie='_WA_warnOK=1;path=/';","") # don't set the 'seen' cookie if the notice will be different on every page and if that's the whole point of htmlFilter
    if options.headAppendRuby: bodyAppend += rubyEndScript
    if headAppend:
        i=htmlFind(html,"</head")
        if i==-1: # no head section?
            headAppend = "<head>"+headAppend+"</head>"
            i=htmlFind(html,"<body")
            if i==-1: # no body section either?
                i=htmlFind(html,"<html")
                if i > -1: i = html.find('>',i)
                if i==-1: i=html.find('>')
                i += 1 # 0 if we're still -1, else past the '>'
        html = html[:i]+headAppend+html[i:]
    if bodyPrepend:
        i=htmlFind(html,"<body")
        if i==-1: i = htmlFind(html,"</head")
        if i==-1: i = htmlFind(html,"<html")
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
   i=htmlFind(html,"<body")
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
        if not (options.ip_query_url and options.ip_change_command): return
        self.currentIP = None
        self.forceTime=0
        self.aggressive_mode = False
        # check for user:password@ in ip_query_url2
        global ip_query_url2,ip_query_url2_user,ip_query_url2_pwd,ip_url2_pwd_is_fname
        ip_query_url2 = options.ip_query_url2
        ip_query_url2_user=ip_query_url2_pwd=ip_url2_pwd_is_fname=None
        if ip_query_url2 and not ip_query_url2=="upnp":
            netloc = urlparse.urlparse(ip_query_url2).netloc
            if '@' in netloc:
                auth,rest = netloc.split('@',1)
                ip_query_url2 = ip_query_url2.replace(netloc,rest,1)
                ip_query_url2_user,ip_query_url2_pwd = auth.split(':',1)
                ip_url2_pwd_is_fname = os.path.isfile(ip_query_url2_pwd)
        # and start the updater
        IOLoop.instance().add_callback(lambda *args:self.queryIP())
    def queryLocalIP(self):
        # Queries ip_query_url2 (if set, and if we know current IP).  Depending on the response/situation, either passes control to queryIP (which sets the next timeout itself), or sets an ip_check_interval2 timeout.
        if not ip_query_url2 or not self.currentIP:
            return self.queryIP()
        debuglog("queryLocalIP")
        if ip_query_url2=="upnp":
            def run():
              try:
                miniupnpc.discover() # every time - it might have rebooted or changed
                miniupnpc.selectigd()
                addr = miniupnpc.externalipaddress()
              except: addr = ""
              if addr == self.currentIP:
                  IOLoop.instance().add_callback(lambda *args:self.newIP(addr)) # in case forceTime is up
                  IOLoop.instance().add_timeout(time.time()+options.ip_check_interval2,lambda *args:self.queryLocalIP())
              else: IOLoop.instance().add_callback(self.queryIP)
            threading.Thread(target=run,args=()).start()
            return
        def handleResponse(r):
            curlFinished()
            if r.error or not self.currentIP in r.body:
                return self.queryIP()
            # otherwise it looks like the IP is unchanged:
            self.newIP(self.currentIP) # in case forceTime is up
            IOLoop.instance().add_timeout(time.time()+options.ip_check_interval2,lambda *args:self.queryLocalIP())
        if ip_query_url2_user:
            # some routers etc insist we send the non-auth'd request first, and the credentials only when prompted (that's what Lynx does with the -auth command line), TODO do we really need to do this every 60secs? (do it only if the other way gets an error??) but low-priority as this is all local-net stuff (and probably a dedicated link to the switch at that)
            if ip_url2_pwd_is_fname: pwd=open(ip_query_url2_pwd).read().strip() # re-read each time
            else: pwd = ip_query_url2_pwd
            callback = lambda r:(curlFinished(),MyAsyncHTTPClient().fetch(ip_query_url2, callback=handleResponse, auth_username=ip_query_url2_user,auth_password=pwd))
        else: callback = handleResponse
        MyAsyncHTTPClient().fetch(ip_query_url2, callback=callback)
    def queryIP(self):
        # Queries ip_query_url, and, after receiving a response (optionally via retries if ip_query_aggressive), sets a timeout to go back to queryLocalIP after ip_check_interval (not ip_check_interval2)
        debuglog("queryIP")
        def handleResponse(r):
            curlFinished()
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
        MyAsyncHTTPClient().fetch(options.ip_query_url, callback=handleResponse)
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
        subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE)
        self.forceTime=time.time()+options.ip_force_interval

watchdog = None
def openWatchdog():
    global watchdog
    watchdog = WatchdogPings()
class WatchdogPings:
    def __init__(self):
        if options.watchdog:
            self.wFile = open(options.watchdogDevice, 'w')
        else: self.wFile = None
        # then call start() after privileges are dropped
    def start(self):
        if not self.wFile: return # no watchdog
        if options.watchdogWait: threading.Thread(target=self.separate_thread,args=()).start()
        self.ping()
    def stop(self):
        if not self.wFile: return # no watchdog
        options.watchdog = 0 # tell any separate_thread() to stop (that thread is not counted in helper_thread_count)
        self.wFile.write('V') # this MIGHT be clean exit, IF the watchdog supports it (not all of them do, so it might not be advisable to use the watchdog option if you plan to stop the server without restarting it)
        self.wFile.close()
    def separate_thread(self): # version for watchdogWait
        # (does not adjust helper_thread_count / can't be "runaway")
        global watchdog_mainServerResponded # a flag.  Do NOT timestamp with time.time() - it can go wrong if NTP comes along and re-syncs the clock by a large amount
        def respond(*args):
            global watchdog_mainServerResponded
            debuglog("watchdogWait: responding",stillIdle=True)
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
                logging.error("Main thread unresponsive, stopping watchdog ping. lastDebugMsg: "+lastDebugMsg)
                stopped = 1 # but don't give up (it might respond just in time)
            time.sleep(options.watchdog)
            sleptSinceResponse += options.watchdog # "dead reckoning" to avoid time.time()
    def ping(self):
        if not options.watchdogWait: debuglog("pinging watchdog",logRepeats=False,stillIdle=True) # ONLY if run from MAIN thread, otherwise it might overwrite the real lastDebugMsg of where we were stuck
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
    # debuglog("fasterServer_up="+repr(fasterServer_up)+" (err="+repr(r.error)+")",logRepeats=False,stillIdle=True)
    if fasterServer_up: return 1 # TODO: configurable? fallback if timeout when we try to connect to it as well?
    elif interval < 60: interval *= 2 # TODO: configurable?
    return interval
class checkServer:
    def __init__(self):
        self.client = self.pendingClient = None
        self.count = 0
        self.interval=1
    def setup(self):
        if not options.fasterServer: return
        if not ':' in options.fasterServer: options.fasterServer += ":80" # needed for the new code
        logging.getLogger("tornado.general").disabled=1 # needed to suppress socket-level 'connection refused' messages from ping2 code in Tornado 3
        class NoConErrors:
            def filter(self,record): return not record.getMessage().startswith("Connect error on fd")
        logging.getLogger().addFilter(NoConErrors()) # ditto in Tornado 2 (which uses the root logger) (don't be tempted to combine this by setting tornado.general to a filter, as the message might change in future Tornado 3 releases)
        IOLoop.instance().add_callback(self)
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
        if not self.client:
            self.client=MyAsyncHTTPClient()
            curlFinished() # we won't count it here
        self.client.fetch("http://"+options.fasterServer+"/ping",connect_timeout=1,request_timeout=1,user_agent="ping",callback=callback,use_gzip=False)
    def serverOK(self):
        # called when any chunk is available from the stream (normally once a second, but might catch up a few bytes if we've delayed for some reason)
        self.interval = FSU_set(True,0)
        self.count = 0
checkServer=checkServer()

lastDebugMsg = "None" # for 'stopping watchdog ping'
def debuglog(msg,logRepeats=True,stillIdle=False):
    global lastDebugMsg, profileIdle
    if not stillIdle: profileIdle = False
    if logRepeats or not msg==lastDebugMsg:
        if not options.logDebug: logging.debug(msg)
        elif options.background: logging.info(msg)
        else: sys.stderr.write(time.strftime("%X ")+msg+"\n")
    lastDebugMsg = msg

if __name__ == "__main__": main()
