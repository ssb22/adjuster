#!/usr/bin/env python
# (can be run in either Python 2 or Python 3;
# has been tested with Tornado versions 2 through 6)

"Web Adjuster v3.242 (c) 2012-25 Silas S. Brown"

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ================================================
# Viewing this code in separate files
# -----------------------------------
# For ease of installation, adjuster.py is distributed
# as a single Python file.  If you want to break it
# into parts for easier code-reading, please run:
#
#   python adjuster.py --split-files
# 
# ================================================

# If you want to compare this code to old versions, the old
# versions are being kept in the E-GuideDog SVN repository on
# http://svn.code.sf.net/p/e-guidedog/code/ssb22/adjuster
# and on GitHub at https://github.com/ssb22/adjuster
# and on GitLab at https://gitlab.com/ssb22/adjuster
# and on BitBucket https://bitbucket.org/ssb22/adjuster
# and at https://gitlab.developers.cam.ac.uk/ssb22/adjuster
# and in China: https://gitee.com/ssb22/adjuster
# although some early ones are missing.

import sys,os,re
twoline_program_name = __doc__+"\nLicensed under the Apache License, Version 2.0"

#@file: split-files.py
# --------------------------------------------------
# Split into separate files for easier code-viewing
# --------------------------------------------------
if '--split-files' in sys.argv:
    if '--autopep8' in sys.argv:
        print ("autopep8 "+__file__)
        d=os.popen("autopep8 '"+__file__.replace("'","'\"'\"'")+"'").read()
        assert "\n\n" in d, "check you have autopep8 command"
    else: d=open(__file__).read()
    assert not "\n#+# " in d
    apache = "#+# \n#+# "+[x for x in d.split("\n\n") if "Apache" in x][0].replace("\n","\n#+# ")+"\n#+# \n"
    try: os.mkdir("src")
    except: pass
    os.chdir("src")
    Makefile = open("Makefile","w")
    Makefile.write("# automatically generated\n\nFiles=")
    filesDone = set()
    d = d.replace("\n# @file","\n#@file") # in case autopep8
    for f in ("\n#@file: top.py\n"+d).split("\n#@file: "):
        try: fname,contents = f.split(None,1)
        except: continue # e.g. before top.py
        assert not fname in filesDone,"Duplicate "+fname
        filesDone.add(fname)
        print ("Writing src/"+fname)
        out = open(fname,"w")
        if not fname=="top.py":
            out.write("#@file: "+fname+"\n"+apache)
        out.write(contents)
        if not fname=="end.py": out.write("\n")
        Makefile.write(fname+" ")
    print ("Writing src/Makefile")
    Makefile.write("\n\n../adjuster.py: $(Files)\n\tcat $(Files) | grep -v '^#[+]# ' > $@\n")
    raise SystemExit

#@file: import1-tornado.py
# --------------------------------------------------
# Basic Tornado import (or not if generating the website)
# --------------------------------------------------

def S(u):
    # unicode to str, Python 2 or 3
    if type(u)==str: return u # already a str
    elif str==bytes: return u.encode('utf-8') # Python 2 unicode needs encode to get to str
    else: return u.decode('utf-8') # Python 3 bytes needs decode to get to str
def B(s):
    # bytes in Python 2 or 3
    if type(s)==bytes: return s # Python 2
    elif type(s)==str: return s.encode('utf-8') # Python 3
    else: return s # boolean or whatever (so we can write B(s) around things that might not necessarily be strings)

if '--version' in sys.argv:
    # no imports needed other than "sys" ("os" for above)
    # (If this code has been run through autopep8, many
    # imports might have been moved to the very top anyway,
    # but at least it still won't depend on tornado just
    # to print the version or the options as HTML.)
    print (twoline_program_name) ; raise SystemExit
elif '--html-options' in sys.argv or '--markdown-options' in sys.argv:
    # for updating the website
    # (these options are not included in the help text)
    tornado=inDL=False ; html = '--html-options' in sys.argv
    if html: print ("<h3>Options for "+__doc__[:__doc__.index("(c)")].strip()+"</h3>")
    else: print ("Options for "+__doc__[:__doc__.index("(c)")].strip()+"\n============\n")
    def heading(h):
        global inDL
        if html:
            if inDL: print ("</dl>")
            print ("<h4>"+h+"</h4>")
            print ("<dl>")
        else: print (h+"\n"+'-'*len(h)+'\n')
        inDL = True
    def define(name,default=None,help="",multiple=False):
        if default or default==False:
            if type(default)==type(""): default=default.replace(",",", ").replace("  "," ")
            else: default=repr(default)
            default=" (default "+default+")"
        else: default=""
        def amp(h):
            if html:
                return h.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            else: return h
        def wbrify(n): # add <wbr> to try to dissuade Android Chrome from shrinking the entire page's text
            n = re.sub("([A-Za-z])([|.:@=])([A-Za-z])(?=[a-z]{4})",r"\1\2<wbr>\3",n) # ranges|message + long URLs
            n = re.sub("([a-z])([A-Z])(?=[a-z][a-z])",r"\1<wbr>\2",n) # submitBookmarkletRemoveExistingRuby etc
            return n.replace("example.org/style%","example.org<wbr>/style%").replace("#/var","#<wbr>/var").replace("_","_<wbr>").replace("password@192","password<wbr>@192").replace("URL/search/replace","URL/<wbr>search/<wbr>replace")
        help = amp(help)
        if html:
          for ttify in ["option=\"value\"","option='value'","\"\"\"","--"]:
            help=help.replace(ttify,"<nobr><kbd>"+ttify+"</kbd></nobr>")
        for w in ["lot","not","all","Important","between","any"]:
            if html: help=re.sub("(?<![A-Za-z])"+w.upper()+"(?![A-Za-z])","<strong>"+w+"</strong>",help)
            else: help=re.sub("(?<![A-Za-z])"+w.upper()+"(?![A-Za-z])","**"+w+"**",help)
        name = name.replace("_","-")
        if html: print ("<dt><kbd>--"+wbrify(name)+"</kbd>"+amp(default.replace('.','.<wbr>'))+"</dt><dd>"+wbrify(help.replace(" - ","---"))+"</dd>")
        else: print ("`--"+name+"` "+default+"\n: "+re.sub(" (www[.]example[.][^ ,]*)",r" `\1`",re.sub("(http://[^ ]*(example|192.168)[.][^ ]*)",r"`\1`",help.replace(" - ","---").replace("---",S(u'\u2014'))))+"\n")
else: # normal run: go ahead with Tornado import
    try: # patch Tornado 5 for Python 3.10+
        import collections, collections.abc
        collections.MutableMapping = collections.abc.MutableMapping
        import asyncio # for wsgi mode:
        from tornado.platform.asyncio import AnyThreadEventLoopPolicy
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
    except: pass # probably wrong Python version, patch not needed
    import tornado
    try: from tornado.httpclient import HTTPClientError as HTTPError # Tornado 5.1+
    except ImportError: from tornado.httpclient import HTTPError # older Tornado
    from tornado.httpclient import AsyncHTTPClient
    try: from tornado.httpserver import HTTPServer
    except: HTTPServer = None # may happen in WSGI mode (e.g. AppEngine can have trouble importing this)
    from tornado.ioloop import IOLoop
    from tornado.web import Application, RequestHandler, StaticFileHandler
    try:
        from tornado.web import asynchronous # decorator removed in Tornado 6, prevents .finish() until we call it explicitly
        def doCallback(req,func,callback,*args,**kwargs):
            kwargs['callback'] = callback
            func(*args,**kwargs)
        def readUntilClose(s,onLast,onChunk):
            try: s.read_until_close(onLast,onChunk)
            except: onLast("")
    except ImportError: # Tornado 6 requires us to write coroutines instead (finish() always called), so let's emulate the old behaviour
        def doCallback(req,func,callback,*args,**kwargs):
            theFuture = func(*args,**kwargs)
            def getResult(f):
                try: r = f.result()
                except Exception as e: r = e
                try: callback(r)
                except Exception as e: # exception in callback
                    if req: req.write_error(None,exc_info=sys.exc_info())
                    raise # so it's logged
            theFuture.add_done_callback(getResult)
        # read_until_close zapped callback and streaming_callback: doCallback can do the last callback but they now also want a loop with read_bytes(maxBytes,partial=true) with a Future
        def readUntilClose(s,onLast,onChunk):
            def getResult(f):
                try: r = f.result()
                except:
                    if debug_connections: print ("readUntilClose getResult exception: calling onLast")
                    onLast("") ; return
                try: onChunk(r)
                except: logging.error("readUntilClose onChunk unhandled exception")
                readUntilClose(s,onLast,onChunk)
            try: s.read_bytes(10240,True).add_done_callback(getResult)
            except tornado.iostream.StreamClosedError: # some Tornado versions can throw to here if was already closed at start ?
                if debug_connections: print ("readUntilClose was immediately closed: calling onLast")
                onLast("") ; return
        from tornado import gen
        def asynchronous(func):
            @gen.coroutine
            def newFunc(self,*args,**kwargs):
                func(self,*args,**kwargs)
                interval = 0.1
                while not self._finished:
                    yield gen.sleep(interval)
                    if interval < 60: interval *= 2
            return newFunc
    import tornado.options, tornado.iostream, tornado.netutil
    from tornado.options import define,options
    def heading(h): pass
    if 'port' in options:
        # Looks like we're being imported by an extension
        # Some Tornado versions don't compile if 'define' is run twice
        def define(*args,**kwargs): pass

#@file: options.py
# --------------------------------------------------
# Options and help text
# --------------------------------------------------

heading("General options")
define("config",help="Name of the configuration file to read, if any. The process's working directory will be set to that of the configuration file so that relative pathnames can be used inside it. Any option that would otherwise have to be set on the command line may be placed in this file as an option=\"value\" or option='value' line (without any double-hyphen prefix). Multi-line values are possible if you quote them in \"\"\"...\"\"\", and you can use standard \\ escapes. You can also set config= in the configuration file itself to import another configuration file (for example if you have per-machine settings and global settings). If you want there to be a default configuration file without having to set it on the command line every time, an alternative option is to set the ADJUSTER_CFG environment variable.")
define("version",help="Just print program version and exit")

heading("Network listening and security settings")
define("port",default=28080,help="The port to listen on. Setting this to 80 will make it the main Web server on the machine (which will likely require root access on Unix); setting it to 0 disables request-processing entirely (for if you want to use only the Dynamic DNS option); setting it to -1 selects a local port in the ephemeral port range, in which case address and port will be written in plain form to standard output if it's not a terminal and --background is set (see also --just-me).")
# e.g. to run over an SSH tunnel, where you can't reserve a port number on the remote machine but can use a known port on the local machine:
# ssh -N -L 28080:$(ssh MachineName python adjuster.py --background --port=-1 --publicPort=28080 --just-me --restart --pidfile=adjuster.pid) MachineName
# This can be combined with --one-request-only (inefficient!) if you don't want the process to hang around afterwards, e.g. from an inetd script on your local port 28080:
# ssh MachineName 'python adjuster.py --background --port=-1 --publicPort=28080 --just-me --one-request-only --seconds=60 --stdio 2>/dev/null'
# You probably want to set up a ControlPath if repeatedly SSH'ing.
# 
define("publicPort",default=0,help="The port to advertise in URLs etc, if different from 'port' (the default of 0 means no difference). Used for example if a firewall prevents direct access to our port but a server like nginx is configured to forward incoming connections.")
define("address",default="",help="The address to listen on. If unset, will listen on all IP addresses of the machine. You could for example set this to localhost if you want only connections from the local machine to be received, which might be useful in conjunction with --real_proxy.")
define("password",help="The password. If this is set, nobody can connect without specifying ?p= followed by this password. It will then be sent to them as a cookie so they don't have to enter it every time. Notes: (1) If wildcard_dns is False and you have multiple domains in host_suffix, then the password cookie will have to be set on a per-domain basis. (2) On a shared server you probably don't want to specify this on the command line where it can be seen by process-viewing tools; use a configuration file instead. (3) When not in HTML-only mode, browsers that send AJAX requests without cookies might have problems when password is set.")
define("password_domain",help="The domain entry in host_suffix to which the password applies. For use when wildcard_dns is False and you have several domains in host_suffix, and only one of them (perhaps the one with an empty default_site) is to be password-protected, with the others public. If this option is used then prominentNotice (if set) will not apply to the passworded domain. You may put the password on two or more domains by separating them with slash (/).")
# prominentNotice not apply to password_domain: this is on
# the assumption that those who know the password understand
# what the tool is.  prominentNotice DOES apply even to the
# password_domain if prominentNotice=="htmlFilter".
# 
define("auth_error",default="Authentication error",help="What to say when password protection is in use and a correct password has not been entered. HTML markup is allowed in this message. As a special case, if this begins with http:// or https:// then it is assumed to be the address of a Web site to which the browser should be redirected. If the markup begins with a * then this is removed and the page is returned with code 200 (OK) instead of 401 (authorisation required).") # TODO: basic password form? or would that encourage guessing
define("open_proxy",default=False,help="Whether or not to allow running with no password. Off by default as a safeguard against accidentally starting an open proxy.")
define("prohibit",multiple=True,default="wiki.*action=edit",help="Comma-separated list of regular expressions specifying URLs that are not allowed to be fetched unless --real_proxy is in effect. Browsers requesting a URL that contains any of these will be redirected to the original site. Use for example if you want people to go direct when posting their own content to a particular site (this is of only limited use if your server also offers access to any other site on the Web, but it might be useful when that's not the case). Include ^https in the list to prevent Web Adjuster from fetching HTTPS pages for adjustment and return over normal HTTP. This access is enabled by default now that many sites use HTTPS for public pages that don't really need to be secure, just to get better placement on some search engines, but if sending confidential information to the site then beware you are trusting the Web Adjuster machine and your connection to it, plus its certificate verification might not be as thorough as your browser's.")
define("prohibitUA",multiple=True,default="TwitterBot",help="Comma-separated list of regular expressions which, if they occur in browser strings, result in the browser being redirected to the original site. Use for example if you want certain robots that ignore robots.txt to go direct.")
define("real_proxy",default=False,help="Whether or not to accept requests with original domains like a \"real\" HTTP proxy.  Warning: this bypasses the password and implies open_proxy.  Off by default.")
define("via",default=True,help="Whether or not to update the Via: and X-Forwarded-For: HTTP headers when forwarding requests")
# (Via is "must" in RFC 2616, so this really shouldn't be set
# to False except for experimental internal-only clients)
define("uavia",default=True,help="Whether or not to add to the User-Agent HTTP header when forwarding requests, as a courtesy to site administrators who wonder what's happening in their logs (and don't log Via: etc)")
define("robots",default=False,help="Whether or not to pass on requests for /robots.txt.  If this is False then all robots will be asked not to crawl the site; if True then the original site's robots settings will be mirrored.  The default of False is recommended.")
# TODO: do something about badly-behaved robots ignoring robots.txt? (they're usually operated by email harvesters etc, and start crawling the web via the proxy if anyone "deep links" to a page through it, see comments in request_no_external_referer)
define("just_me",default=False,help="Listen on localhost only, and check incoming connections with an ident server (which must be running on port 113) to ensure they are coming from the same user.  This is for experimental setups on shared Unix machines; might be useful in conjuction with --real_proxy.  If an ident server is not available, an attempt is made to authenticate connections via Linux netstat and /proc.")
define("one_request_only",default=False,help="Shut down after handling one request.  This is for use in inefficient CGI-like environments where you cannot leave a server running permanently, but still want to start one for something that's unsupported in WSGI mode (e.g. js_reproxy): run with --one_request_only and forward the request to its port.  You may also wish to set --seconds if using this.")
define("seconds",default=0,help="The maximum number of seconds for which to run the server (0 for unlimited).  If a time limit is set, the server will shut itself down after the specified length of time.")
define("stdio",default=False,help="Forward standard input and output to our open port, in addition to being open to normal TCP connections.  This might be useful in conjuction with --one-request-only and --port=-1.")

define("upstream_proxy",help="address:port of a proxy to send our requests through. This can be used to adapt existing proxy-only mediators to domain rewriting, or for a caching proxy. Not used for ip_query_url options or fasterServer. If address is left blank (just :port) then localhost is assumed and https URLs will be rewritten into http with altered domains; you'll then need to set the upstream proxy to send its requests back through the adjuster (which will listen on localhost:port+1 for this purpose) to undo that rewrite. This can be used to make an existing HTTP-only proxy process HTTPS pages.")
# The upstream_proxy option requires pycurl (will refuse to start if not present). Does not set X-Real-Ip because Via should be enough for upstream proxies. The ":port"-only option rewrites URLs in requests but NOT ones referred to in documents: we assume the proxy can cope with that.

define("ip_messages",help="Messages or blocks for specific IP address ranges (IPv4 only).  Format is ranges|message|ranges|message etc, where ranges are separated by commas; can be individual IPs, or ranges in either 'network/mask' or 'min-max' format; the first matching range-set is selected.  If a message starts with * then its ranges are blocked completely (rest of message, if any, is sent as the only reply to any request), otherwise message is shown on a 'click-through' page (requires Javascript and cookies).  If the message starts with a hyphen (-) then it is considered a minor edit of earlier messages and is not shown to people who selected `do not show again' even if they did this on a different version of the message.  Messages may include HTML.")

heading("DNS and website settings")

getfqdn_default = "is the machine's domain name"
# getfqdn_default comes after "default" in the HTML,
# hence "default is the machine's domain name".
# Avoids calling getfqdn unnecessarily, as the server might
# be offline/experimental and we don't want to block on an
# nslookup with every adjuster start just to get the default.

define("host_suffix",default=getfqdn_default,help="The last part of the domain name. For example, if the user wishes to change www.example.com and should do so by visiting www.example.com.adjuster.example.org, then host_suffix is adjuster.example.org. If you do not have a wildcard domain then you can still adjust one site by setting wildcard_dns to False, host_suffix to your non-wildcard domain, and default_site to the site you wish to adjust. If you have more than one non-wildcard domain, you can set wildcard_dns to False, host_suffix to all your domains separated by slash (/), and default_site to the sites these correspond to, again separated by slash (/); if two or more domains share the same default_site then the first is preferred in links and the others are assumed to be for backward compatibility. If wildcard_dns is False and default_site is empty (or if it's a /-separated list and one of its items is empty), then the corresponding host_suffix gives a URL box and sets its domain in a cookie (and adds a link at the bottom of pages to clear this and return to the URL box), but this should be done only as a last resort: you can browse only one domain at a time at that host_suffix, and unless you use HTML-only mode, most links and HTTP redirects to other domains will leave the adjuster (which can negatively affect sites that use auxiliary domains for scripts etc and check Referer, unless you ensure these auxiliary domains are listed elsewhere in default_site), and browsers that don't include cookies in their AJAX requests will have problems. Also, the sites you visit at that host_suffix might be able to see some of each other's cookies etc (leaking privacy) although the URL box page will try to clear site cookies.")
# ("preferred" / "backward compatibility" thing: can be useful if old domain has become unreliable, or if "preferred" domain is actually a URL-path-forwarding service with a memorable name which redirects browsers to an actual domain that's less memorable, and you want the memorable domain to be used in links etc, although in this case you might still get the less-memorable domain in the address bar)
# TODO: (two or more domains pointing to the same default_site) "preferred" / "backward compatibility" thing above: or, add an option to periodically check which of our domains are actually 'up' and move them to the front of the host_suffix / default_site list; that way we don't have to guess ahead of time which one is more reliable and should be preferred.
# Could also do 'use the currently-requested host if it's appropriate', but what if there's a *set* of sites we adjust and we need to try to rewrite cross-site links to be in the same set of domains as the one the browser is requesting - maybe it's best to leave the "preferred" DNS to the config or the periodic check.
# TODO at lower priority: empty (item in) host_suffix to match ALL (unknown) hosts, including IP hosts and no Host: header.  Fetch the corresponding default_site (empty means use cookies), and adjust it USING THE HOST SPECIFIED BY THE BROWSER to rewrite the links.  This could be useful if setting up an adjuster with NO domain name (IP only).  Could periodically upload our public IP to a separate static website via FTP/SSH/etc in case dynamic DNS is not reliable.  But if IP address has to change then all cookies would be 'lost'.  Also, if no password is set then IP-based "webserver probes" could cause us to send malicious-looking traffic to default_site.
# TODO: Could do different hosts on different ports, which might also be useful if you have a domain name but only one.  Would have to check for cookie sharing (or just say "do this only if you don't mind it"); fasterServer would have to forward to same as incoming port.  Might be a problem if some users' firewalls disallow outgoing Web traffic to non-standard ports.
# (In the current code, setting host_suffix to a public IP address should work: most browsers set Host: to the IP if requesting a URL by IP, and then the IP will be used in rewrites if it's the first thing specified for its corresponding default_site.  But adjuster will need to be reconfigured and restarted on every change of the public IP.)
define("default_site",help="The site to fetch from if nothing is specified before host_suffix, e.g. example.org (add .0 at the end to specify an HTTPS connection, but see the 'prohibit' option). If default_site is omitted then the user is given a URL box when no site is specified; if it is 'error' then an error is shown in place of the URL box (the text of the error depends on the settings of wildcard_dns and real_proxy).")
# --- using .0 here rather than https:// prefix because / is a separator: see the host_suffix help text (TODO: change the separator? but don't break existing installations)

define('search_sites',multiple=True,help="Comma-separated list of search sites to be made available when the URL box is displayed (if default_site is empty). Each item in the list should be a URL (which will be prepended to the search query), then a space, then a short description of the site. The first item on the list is used by default; the user can specify other items by making the first word of their query equal to the first word of the short description. Additionally, if some of the letters of that first word are in parentheses, the user may specify just those letters. So for example if you have an entry http://search.example.com/?q= (e)xample, and the user types 'example test' or 'e test', it will use http://search.example.com/?q=test")
define("urlbox_extra_html",help="Any extra HTML you want to place after the URL box (when shown), such as a paragraph explaining what your filters do etc.")
define("urlboxPath",default="/",help="The path of the URL box for use in links to it. This might be useful for wrapper configurations, but a URL box can be served from any path on the default domain. If however urlboxPath is set to something other than / then efforts are made to rewrite links to use it more often when in HTML-only mode with cookie domain, which might be useful for limited-server situations. You can force HTML-only mode to always be on by prefixing urlboxPath with *")
define("wildcard_dns",default=True,help="Set this to False if you do NOT have a wildcard domain and want to process only default_site. Setting this to False does not actually prevent other sites from being processed (for example, a user could override their local DNS resolver to make up for your lack of wildcard domain); if you want to really prevent other sites from being processed then you should get nginx or similar to block incoming requests for the wrong domain. Setting wildcard_dns to False does stop the automatic re-writing of links to sites other than default_site. Leave it set to True to have ALL sites' links rewritten on the assumption that you have a wildcard domain.") # will then say "(default True)"
define("urlscheme",default="http://",help="Default URL scheme to use when referring to our other subdomains.  Setting this to // or https:// means you will need a wildcard TLS certificate (or a multi-subdomain one with wildcard-limit set), but leaving it at http:// means you may have only an unencrypted connection to at least some of the adjuster session.")
define("alt_dot",help="String to place before host_suffix if the adjuster is run behind an SSL/TLS terminator that lacks certificates for subdomains beyond host_suffix but can still route such subdomains to the adjuster if separated by this string instead of a dot.  Beware this leads to an undesirable situation with subdomain-shared cookies: either they'll be set on only one domain instead of its subdomains (default), breaking some websites (and breaking the password option if you use it), or if you add a * before the value of alt-dot they can be sent not only to all adjusted domains but also to all other domains at the same level as the adjuster i.e. other users of the provider (use this only for temporary experimental accounts if you know what you're doing, and it won't work on modern browsers if the provider has listed their upper levels in Mozilla's top-level domains on which not even Javascript can set cookies).  If possible, it's better to avoid this option and instead use a load balancer providing a shorter host_suffix, although if that doesn't have a wildcard certificate you'll be on unencrypted HTTP, unless you can set a multi-subdomain certificate with wildcard-limit set.") # e.g. AppEngine projectName.uc.r vs just projectName (and *.r.appspot.com is in the TLD list for newer browsers so can't set cookies there)
define("wildcard_limit",help="Comma separated list of domains to process via wildcard-dns, if not unlimited.  Use this if you have a wildcard DNS entry but not a wildcard TLS certificate, but your TLS certificate can cover specific subdomains of the form www-example-net-0.adjuster.example.org and you wish to adjust these domains (in this example wildcard-limit should include www.example.net).  Unlike slash-separated default-site, this allows cookie sharing between subdomains.  Any domains not listed will be sent out of the adjuster.")
# As of 2025, LetsEncrypt can't do wildcard cert w/out DNS auth, but can have a fixed set of subdomains
# But not for appspot: its CAA record prevents LetsEncrypt from signing subdomains
# If manual, will need something like:
# certbot --config-dir=/tmp/c --work-dir=/tmp/c --logs-dir=/tmp/c certonly --manual --preferred-challenges http
# (can press Enter for all N-1 challenges and set up all at once, then deploy on the final one before the final Enter)

heading("General adjustment options")
define("default_cookies",help="Semicolon-separated list of name=value cookies to send to all remote sites, for example to set preferences. Any cookies that the browser itself sends will take priority over cookies in this list. Note that these cookies are sent to ALL sites. You can set a cookie only on a specific browser by putting (browser-string) before the cookie name, e.g. (iPad)x=y will set x=y only if 'iPad' occurs in the browser string (to match more than one browser-string keyword, you have to specify the cookie multiple times).") # TODO: site-specific option
# TODO: sets of adjustments can be switched on and off at a /__settings URL ?  or leave it to the injected JS
define("headAppend",help="Code to append to the HEAD section of every HTML document that has a BODY. Use for example to add your own stylesheet links and scripts. Not added to documents that lack a BODY such as framesets.")
define("headAppendCSS",help="URL of a stylesheet to add to the HEAD section of every HTML document that has a BODY.  This option automatically generates the LINK REL=... markup for it, and also tries to delete the string '!important' from other stylesheets, to emulate setting this stylesheet as a user CSS.  Additionally, it is not affected by --js-upstream as headAppend is.  You can also include one or more 'fields' in the URL, by marking them with %s and following the URL with options e.g. http://example.org/style%s-%s.css;1,2,3;A,B will allow combinations like style1-A.css or style3-B.css; in this case appropriate selectors are provided with the URL box (values may optionally be followed by = and a description), and any visitors who have not set their options will be redirected to the URL box to do so.")
define("protectedCSS",help="A regular expression matching URLs of stylesheets with are \"protected\" from having their '!important' strings deleted by headAppendCSS's logic. This can be used for example if you are adding scripts to allow the user to choose alternate CSS files in place of headAppendCSS, and you wish the alternate CSS files to have the same status as the one supplied in headAppendCSS.")
define("cssName",help="A name for the stylesheet specified in headAppendCSS, such as \"High Contrast\".  If cssName is set, then the headAppendCSS stylesheet will be marked as \"alternate\", with Javascript links at the bottom of the page for browsers that lack their own CSS switching options.  If cssName begins with a * then the stylesheet is switched on by default; if cssName begins with a # then the stylesheet is switched on by default only if the browser reports system dark mode; if cssName is not set then the stylesheet (if any) is always on.")
define("cssNameReload",multiple=True,default="IEMobile 6,IEMobile 7,IEMobile 8,Opera Mini,Opera Mobi,rekonq,MSIE 5,MSIE 6,MSIE 7,MSIE 9,MSIE 10",help="List of (old) browsers that require alternate code for the cssName option, which is slower as it involves reloading the page on CSS switches.  Use this if the CSS switcher provided by cssName does nothing on your browser.")
# cssNameReload: Opera Mini sometimes worked and sometimes didn't; maybe there were regressions at their proxy; JS switcher needs network traffic anyway on Opera Mini so we almost might as well use the reloading version (but in Spring 2014 they started having trouble with reload() AS WELL, see cssReload_cookieSuffix below)
# Opera Mobile 10 on WM6.1 is fine with CSS switcher but it needs cssHtmlAttrs, TODO we might be able to have a list of browsers that require cssHtmlAttrs but not cssNameReload, add cssHtmlAttrs only if CSS is selected at time of page load, and make the 'off' switch remove them
# TODO: Opera/9.5 on WM6.1 document.write can corrupt the display with EITHER script; page might also display for some time before the document.writes take effect.  Suggest those users upgrade to version 10 (= Opera/9.8) ?
cssReload_cookieSuffix = "&&_adjuster_setCookie:"
# cssReload_cookieSuffix enables code that works better on Opera Mini's transcoder (Spring 2014) by setting the cookie server-side. (Set to blank to use the old code. TODO: browser-dependent? make it a 'define' option?)
define("cssHtmlAttrs",help="Attributes to add to the BODY element of an HTML document when cssNameReload is in effect (or when it would be in effect if cssName were set). This is for old browsers that try to render the document first and apply CSS later. Example: 'text=\"yellow\" bgcolor=\"black\"' (not as flexible as CSS but can still make the rendering process less annoying). If headAppendCSS has \"fields\" then cssHtmlAttrs can list multiple sets of attributes separated by ; and each set corresponds with an option in the last field of headAppendCSS.") # e.g. IEMobile 7 (or Opera 10) on WM 6.1
define("headAppendRuby",default=False,help="Convenience option which adds CSS and Javascript code to the HTML body that tries to ensure simple RUBY markup displays legibly across all modern browsers; this might be useful if you used Annotator Generator to make the htmlFilter program. (The option is named 'head' because it used to add markup to the HEAD; this was moved to the BODY to work around browser bugs.)")
# headAppendRuby: IEMobile 6 drops whitespace after closing tags if document HEAD contains any STYLE element, even an empty one, except via link rel=Stylesheet. Style element works OK if placed at start of body.
define("highlighting",multiple=True,help="Convenience option which adds CSS and Javascript code to add a text-highlighting option to some browsers. If set, this option should be set to a comma-separated list of available colours (please ensure there's at least one for each stylesheet colour scheme likely to be in use); won't work well with --render because images are not highlighted. Highlights are saved in the browser, but might load incorrectly if the page's text changes between sessions.")
define("bodyAppend",help="Code to append to the BODY section of every HTML document that has one. Use for example to add a script that needs to be run after the rest of the body has been read, or to add a footer explaining how the page has been modified. See also prominentNotice.")
# bodyAppend TODO: note that it will go at the bottom of IFRAMEs also, and suggest using something similar to prominentNotice's iframe-detection code?
define("bodyAppendGoesAfter",help="If this is set to a regular expression matching some text or HTML code that appears verbatim in the body section, the code in bodyAppend will be inserted after the last instance of this regular expression (case sensitive) instead of at the end of the body. Use for example if a site styles its pages such that the end of the body is not a legible place for a footer.") # (e.g. it would overprint some position=fixed stuff)
define("bodyPrepend",help="Code to place at the start of the BODY section of every HTML document that has one.")
# bodyPrepend may be a useful place to put some scripts. For example, a script that changes a low-vision stylesheet according to screen size might be better in the BODY than in the HEAD, because some Webkit-based browsers do not make screen size available when processing the HEAD of the starting page. # but sometimes it still goes wrong on Chromium startup; probably a race condition; might be worth re-running the script at end of page load just to make sure
define("prominentNotice",help="Text to add as a prominent notice to processed sites (may include HTML). If the browser has sufficient Javascript support, this will float relative to the browser window and will contain an 'acknowledge' button to hide it (for the current site in the current browsing session). Use prominentNotice if you need to add important information about how the page has been modified. If you set prominentNotice to the special value \"htmlFilter\", then the output of the htmlFilter option (if any) will be placed as a prominent notice; this can be used if you want to provide extra information or links derived from the content of the page. Note: if you include Javascript document.write() code in prominentNotice, check that document.readyState is not 'complete' or you might find the document is erased on some website/browser combinations when a site script somehow causes your script to be re-run after the document stream is closed. In some rare cases you might also need to verify that document.cookie does not contain _WA_warnOK=1") # e.g. if the site does funny things with the browser cache.  Rewriting the innerHTML manipulation to appendChild doesn't fix the need to check document.readyState
define("staticDocs",help="url#path of static documents to add to every website, e.g. /_myStatic/#/var/www (make sure the first part is something not likely to be used by the websites you visit). This can be used to supply extra Javascript (e.g. for bodyPrepend to load) if it needs to be served from the same domain. The password option does not apply to staticDocs.") # You could just do this with nginx, but staticDocs can also be used with js-upstream so we should probably keep this option for experiments
define("delete",multiple=True,help="Comma-separated list of regular expressions to delete from HTML documents. Can be used to delete selected items of Javascript and other code if it is causing trouble for your browser. Will also delete from the text of pages; use with caution.")
define("delete_css",multiple=True,help="Comma-separated list of regular expressions to delete from CSS documents (but not inline CSS in HTML); can be used to remove, for example, dimension limits that conflict with annotations you add, as an alternative to inserting CSS overrides.  In rare cases you might want to replace the deleted regexp with another, in which case you can use @@ to separate the two, and a second @@ can be used to specify a string in the CSS URL that must be present for the operation to take effect (this could be combined with a codeChanges to add query parameters to the URL if you want the change to occur only when the CSS is loaded from specific HTML pages).")
define("delete_doctype",default=False,help="Delete the DOCTYPE declarations from HTML pages. This option is needed to get some old Webkit browsers to apply multiple CSS files consistently.")
define("deleteOmit",multiple=True,default="iPhone,iPad,Android,Macintosh",help="A list of browsers that do not need the delete and delete-doctype options to be applied. If any of these strings occur in the user-agent then these options are disabled for that request, on the assumption that these browsers are capable enough to cope with the \"problem\" code. Any delete-css option is still applied however.")
define("cacheOmit",multiple=True,default="IEMobile",help="A list of browsers that cannot be trusted to provide correct Cache-Control headers. Use this if your browser fails to renew data when you press Reload.")
# cacheOmit: e.g. IE6 on WM6.1 sets Cache-Control to "max-age=259200" (3 days) even if you press Reload, which can result in upstream caching proxies (e.g. on AppEngine) failing to re-query the original servers on a reload (e.g. for NextBuses, frustrating if you're trying to decide whether or not you have to run!)
define("zeroWidthDelete",multiple=True,default="IEMobile,MSIE 6",help="A list of (old) browsers that cannot be relied on to process Unicode zero-width space (U+200b) correctly and need it removed from websites")
define("codeChanges",help="Several lines of text specifying changes that are to be made to all HTML and Javascript code files on certain sites; use as a last resort for fixing a site's scripts. This option is best set in the configuration file and surrounded by r\"\"\"...\"\"\". The first line is a URL prefix (just \"http\" matches all); append a # to match an exact URL instead of a prefix, and #+number (e.g. #1 or #2) to match an exact URL and perform the change only that number of times in the page.  The second line is a string of code to search for, and the third is a string to replace it with. Further groups of URL/search/replace lines may follow; blank lines and lines starting with # are ignored. If the 'URL prefix' starts with a * then it is instead a string to search for within the code of the document body; any documents containing this code will match; thus it's possible to write rules of the form 'if the code contains A, then replace B with C'. This processing takes place before any 'delete' option takes effect so it's possible to pick up on things that will be deleted, and it occurs after the domain rewriting so it's possible to change rewritten domains in the search/replace strings (but the URL prefix above should use the non-adjusted version).")
define("boxPrompt",default="Website to adjust",help="What to say before the URL box (when shown); may include HTML; for example if you've configured Web Adjuster to perform a single specialist change that can be described more precisely with some word other than 'adjust', you might want to set this.")
define("viewsource",default=False,help="Provide a \"view source\" option. If set, you can see a page's pre-adjustment source code, plus client and server headers, by adding \".viewsource\" to the end of a URL (after any query parameters etc)")
define("htmlonly_mode",default=True,help="Provide a checkbox allowing the user to see pages in \"HTML-only mode\", stripping out images, scripts and CSS; this might be a useful fallback for very slow connections if a site's pages bring in many external files and the browser cannot pipeline its requests. The checkbox is displayed by the URL box, not at the bottom of every page.")
# htmlonly_mode: if client has no pipeline, a slow UPLINK can be a problem, especially if many cookies have to be sent with each request for a js/css/gif/etc.
# (and if wildcard_dns=False and we're domain multiplexing, our domain can accumulate a lot of cookies, causing requests to take more uplink bandwidth, TODO: do something about this?)
define("htmlonly_css",default=False,help="Leave images and CSS in the page when in \"HTML-only mode\", removing only scripts")
define("mailtoPath",default="/@mail@to@__",help="A location on every adjusted website to put a special redirection page to handle mailto: links, showing the user the contents of the link first (in case a mail client is not set up). This must be made up of URL-safe characters starting with a / and should be a path that is unlikely to occur on normal websites and that does not conflict with renderPath. If this option is empty, mailto: links are not changed. (Currently, only plain HTML mailto: links are changed by this function; Javascript-computed ones are not.)")
define("mailtoSMS",multiple=True,default="Opera Mini,Opera Mobi,Android,Phone,Mobile",help="When using mailtoPath, you can set a comma-separated list of platforms that understand sms: links. If any of these strings occur in the user-agent then an SMS link will be provided on the mailto redirection page, to place the suggested subject and/or body into a draft SMS message instead of an email.")

heading("External processing options")
define("htmlFilter",help="External program(s) to run to filter every HTML document. If more than one program is specified separated by # then the user will be given a choice (see htmlFilterName option). Any shell command can be used; its standard input will get the HTML (or the plain text if htmlText is set), and it should send the new version to standard output. Multiple copies of each program might be run at the same time to serve concurrent requests. UTF-8 character encoding is used. If you are not able to run external programs then you could use a back-end server (specify an http:// or https:// URL and input is POSTed in the request body; if this back-end server is another Web Adjuster with submitPath and submitBookmarklet set then give its submitPath plus uA for its 1st filter, uB for its 2nd, etc), or use a Python function: specify * followed by the function name, and inject the function into the adjuster module from a wrapper script (which imports adjuster, sets adjuster.options.htmlFilter etc, injects the function and calls adjuster.main). The function should take a byte-string and return its modified version, and is run in the serving thread. See also htmlUrl and htmlonly_tell_filter options.") # (run in the serving thread: so try to make it fast, although this is not quite so essential in WSGI mode; if you're in WSGI mode then I suggest getting the function to import any large required modules on-demand)
define("htmlFilterName",help="A name for the task performed by htmlFilter. If this is set, the user will be able to switch it on and off from the browser via a cookie and some Javascript links at the bottom of HTML pages. If htmlFilter lists two or more options, htmlFilterName should list the same number plus one (again separated by #); the first is the name of the entire category (for example \"filters\"), and the user can choose between any one of them or none at all, hence the number of options is one more than the number of filters")
define("htmlFilterCollapse",default=3,help="The maximum number of htmlFilterName options beyond which all but the first N-1 are hidden behind a \"More\" option on some browsers.") # TODO: non-Javascript fallback for the switcher
define("htmlJson",default=False,help="Try to detect HTML strings in JSON responses and feed them to htmlFilter. This can help when using htmlFilter with some AJAX-driven sites. IMPORTANT: Unless you also set the 'separator' option, the external program must preserve all newline characters, because multiple HTML strings in the same JSON response will be given to it separated by newlines, and the newlines of the output determine which fragment to put back where. (If you combine htmlJson with htmlText, the external program will see text in HTML in JSON as well as text in HTML, but it won't see text in HTML in JSON in HTML.)")
define("htmlText",default=False,help="Causes the HTML to be parsed, and only the text parts (not the markup) will be sent to htmlFilter. Useful to save doing HTML parsing in the external program. The external program is still allowed to include HTML markup in its output. IMPORTANT: Unless you also set the 'separator' option, the external program must preserve all newline characters, because multiple text strings will be given to it separated by newlines, and the newlines of the output determine which modified string to put back where.")
define("separator",help="If you are using htmlFilter with htmlJson and/or htmlText, you can set separator to any text string to be used as a separator between multiple items of data when passing them to the external program. By default, newlines are used for this, but you can set it to any other character or sequence of characters that cannot be added or removed by the program. (It does not matter if a website's text happens to use the separator characters.) If separator is set, not only will it be used as a separator BETWEEN items of data but also it will be added before the first and after the last item, thus allowing you to use an external program that outputs extra text before the first and after the last item. The extra text will be discarded. If however you do not set separator then the external program should not add anything extra before/after the document.")
define("leaveTags",multiple=True,default="script,style,title,textarea,option",help="When using htmlFilter with htmlText, you can set a comma-separated list of HTML tag names whose enclosed text should NOT be sent to the external program for modification. For this to work, the website must properly close these tags and must not nest them. (This list is also used for character-set rendering.)")
# leaveTags: not including 'option' can break pages that need character-set rendering
define("stripTags",multiple=True,default="wbr",help="When using htmlFilter with htmlText, you can set a comma-separated list of HTML tag names which should be deleted if they occur in any section of running text. For example, \"wbr\" (word-break opportunity) tags (listed by default) might cause problems with phrase-based annotators.")
# stripTags TODO: <span class="whatever">&nbsp;</span> (c.f. annogen's JS) ?  have already added to the bookmarklet JS (undocumented! see 'awkwardSpan') but not to the proxy version (the two find_text_in_HTML functions)
define("htmlUrl",default=False,help="Add a line containing the document's URL to the start of what gets sent to htmlFilter (useful for writing filters that behave differently for some sites; not yet implemented for submitBookmarklet, which will show a generic URL). The URL line must not be included in the filter's response.")
define("htmlonly_tell_filter",default=False,help="Add a line showing the current status of \"HTML-only mode\" (see htmlonly_mode option) to the start of what gets sent to htmlFilter (before any htmlUrl if present), as \"True\" or \"False\" (must not be included in the filter's response).  This may be useful for filters that need to do extra processing if client-side scripts are removed.")

define("submitPath",help="If set, accessing this path (on any domain) will give a form allowing the user to enter their own text for processing with htmlFilter. The path should be one that websites are not likely to use (even as a prefix), and must begin with a slash (/). If you prefix this with a * then the * is removed and any password set in the 'password' option does not apply to submitPath. Details of the text entered on this form is not logged by Web Adjuster, but short texts are converted to compressed GET requests which might be logged by proxies etc.")
# (submitPath: see comments in serve_submitPage; "with htmlFilter" TODO: do we add "(or --render)" to this? but charset submit not entirely tested with all old browsers; TODO: consider use of chardet.detect(buf) in python-chardet)
define("submitPrompt",default="Type or paste in some text to adjust",help="What to say before the form allowing users to enter their own text when submitPath is set (compare boxPrompt)")
define("submitPromptTitle",default="Upload Text",help="The title of the form allowing users to enter their own text when submitPath is set")
define("submitPromptAction",default="Upload",help="The button label for the form allowing users to enter their own text when submitPath is set")
define("identifyAdjusterOnUploadedText",default=True,help="Identify the Web Adjuster version at the bottom of the Uploaded Text result (you might want to set this to False if you're publicly running only a submitPath)")
define("submitBookmarklet",default=True,help="If submitPath and htmlFilter is set, and if browser Javascript support seems sufficient, then add one or more 'bookmarklets' to the submitPath page (named after htmlFilterName if provided), allowing the user to quickly upload text from other sites. This might be useful if for some reason those sites cannot be made to go through Web Adjuster directly. The bookmarklets should work on modern desktop browsers and on iOS and Android; they should cope with frames and with Javascript-driven changes to a page, and on some browsers an option is provided to additionally place the page into a frameset so that links to other pages on the same site can be followed without explicitly reactivating the bookmarklet (but this does have disadvantages - page must be reloaded + URL display gets 'stuck' - so it's left to the user to choose).") # (and if the other pages check their top.location, things could break there as well)
define("submitBookmarkletFilterJS",default=r"!c.nodeValue.match(/^[ -~\s]*$/)",help="A Javascript expression that evaluates true if a DOM text node 'c' should be processed by the 'bookmarklet' Javascript when submitPath and submitBookmarklet are set. To process ALL text, set this option to c.nodeValue.length, but if your htmlFilter will not change certain kinds of text then you can make the Javascript run more efficiently by not processing these (quote the expression carefully). The default setting will not process text that is all ASCII.")
# well, all ASCII + whitespace.  TODO: add non-ascii 'smart punctuation'? entered as Unicode escapes, or rely on serving the script as utf-8. (Previously said "To process ALL text, simply set this option to 'true'", but that can have odd effects on some sites' empty nodes. Saying c.nodeValue.length for now; c.nodeValue.match(/[^\s]/) might be better but needs more quoting explanation. Could change bookmarkletMainScript so it alters the DOM only if replacements[i] != oldTexts[i], c.f. annogen's android code, but that would mean future passes would re-send all the unchanged nodes cluttering the XMLHttpRequests especially if they fill a chunk - annogen version has the advantage of immediate local processing)
define("submitBookmarkletChunkSize",default=1024,help="Specifies the approximate number of characters at a time that the 'bookmarklet' Javascript will send to the server if submitPath and submitBookmarklet are set. Setting this too high could impair browser responsiveness, but too low will be inefficient with bandwidth and pages will take longer to finish.")
define("submitBookmarkletDomain",help="If set, specifies a domain to which the 'bookmarklet' Javascript should send its XMLHttpRequests, and ensures that they are sent over HTTPS if the 'bookmarklet' is activated from an HTTPS page (this is needed by some browsers to prevent blocking the XMLHttpRequest).  submitBookmarkletDomain should be a domain for which the adjuster (or an identically-configured copy) can receive requests on both HTTP and HTTPS, and which has a correctly-configured HTTPS front-end with valid certificate.")
define("letsEncryptWarning",default=False,help="Indicates that submitBookmarkletDomain (if set) has an HTTPS server that uses a certificate from LetsEncrypt, and we should warn users of certain old browsers that they won't accept it by default now LetsEncrypt's X3 expired at the end of September 2021")
define("submitBookmarkletRemoveExistingRuby",default=True,help="Specifies that 'bookmarklets' added to the submitPath page should remove all existing ruby on a page before running.  Use this for example if you expect to replace the text with ruby of a different kind of annotation.")

heading("Javascript execution options")
define("js_interpreter",default="",help="Execute Javascript on the server for users who choose \"HTML-only mode\". You can set js_interpreter to PhantomJS, HeadlessChrome, HeadlessFirefox, Chrome, Firefox, or edbrowse (experimental), and must have the appropriate one installed, along with an appropriate version of Selenium (and ChromeDriver or GeckoDriver if appropriate) if not using edbrowse.  Non-headless Chrome or Firefox requires a display (and might not respond to manual window close) but may help work around bugs in some headless versions.  If you have multiple users, beware logins etc may be shared!  If a URL box cannot be displayed (no wildcard_dns and default_site is full, or processing a \"real\" proxy request) then htmlonly_mode auto-activates when js_interpreter is set, thus providing a way to partially Javascript-enable browsers like Lynx.  If --viewsource is enabled then js_interpreter URLs may also be followed by .screenshot")
define("js_upstream",default=False,help="Handle --headAppend, --bodyPrepend, --bodyAppend and --codeChanges upstream of our Javascript interpreter instead of making these changes as code is sent to the client, and make --staticDocs available to our interpreter as well as to the client.  This is for running experimental 'bookmarklets' etc with browsers like Lynx.")
# js_upstream TODO: what of delay? (or wait for XHRs to finish, call executeJavascript instead?)
define("js_frames",default=False,help="When using js_interpreter, append the content of all frames and iframes to the main document. This might help with bandwidth reduction and with sites that have complex cross-frame dependencies that can be broken by sending separate requests through the adjuster.")
define("js_instances",default=1,help="The number of virtual browsers to load when js_interpreter is in use. Increasing it will take more RAM but may aid responsiveness if you're loading multiple sites at once.")
define("js_429",default=True,help="Return HTTP error 429 (too many requests) if js_interpreter queue is too long at page-prefetch time. When used with --multicore, additionally close to new requests any core that's currently processing its full share of js_instances.")
# js_429 + multicore: closes even though some of those new requests might not immediately require js_interpreter work.  But it's better than having an excessively uneven distribution under load.  HTTP 429 is from RFC 6585, April 2012.  Without multicore, 'too long' = 'longer than 2*js_instances', but the queue can grow longer due to items already in prefetch: not all prefetches end up being queued for JS interpretation, so we can't count them prematurely. TODO: close even *before* reached full share of js_instances? as there may be other pages in prefetch, which will then have to wait for instances on this core even though there might already be spare instances on other cores.
define("js_restartAfter",default=10,help="When js_interpreter is in use, restart each virtual browser after it has been used this many times (0=unlimited); might help work around excessive RAM usage in PhantomJS v2.1.1. If you have many --js-instances (and hardware to match) you could also try --js-restartAfter=1 (restart after every request) to work around runaway or unresponsive PhantomJS processes.")
# (js-restartAfter=1 precludes a faster response when a js_interpreter instance is already loaded with the page requested, although faster response is checked for only AFTER selecting an instance and is therefore less likely to work with multiple instances under load, and is in any event unlikely to work if running multicore with many cores); TODO: check if PhantomJS 2.1.1 RAM usage is a regression from 2.0.1 ? but it's getting less relevant now there's non-PhantomJS options.
define("js_restartMins",default=10,help="Restart an idle js_interpreter instance after about this number of minutes (0=unlimited); use this to stop the last-loaded page from consuming CPU etc indefinitely if no more requests arrive at that instance.  Not applicable when --js-restartAfter=1.")
# js_restartMins: setting it low does have the disadvantage of not being able to use an already-loaded page, see above
define("js_timeout1",default=30,help="When js_interpreter is in use, tell it to allow this number of seconds for initial page load. More time is allowed for XMLHttpRequest etc to finish (unless our client cuts the connection in the meantime).")
define("js_timeout2",default=100,help="When js_interpreter is in use, this value in seconds is treated as a 'hard timeout': if a webdriver process does not respond at all within this time, it is assumed hung and emergency restarted.")
define("js_retry",default=True,help="If a js_interpreter fails, restart it and try the same fetch again while the remote client is still waiting")
define("js_fallback",default="X-Js-Fallback",help="If this is set to a non-empty string and a js_interpreter fails (even after js_retry if set), serve the page without Javascript processing instead of serving an error. The HTTP header specified by this option can tell the client whether or not Javascript was processed when a page is served.")
define("js_reproxy",default=True,help="When js_interpreter is in use, have it send its upstream requests back through the adjuster on a different port. This allows js_interpreter to be used for POST forms, fixes its Referer headers when not using real_proxy, monitors AJAX for early completion, prevents problems with file downloads, and enables the js_prefetch option.")
# js_reproxy also works around issue #13114 in PhantomJS 2.x.  Only real reason to turn it off is if we're running in WSGI mode (which isn't recommended with js_interpreter) as we haven't yet implemented 'find spare port and run separate IO loop behind the WSGI process' logic
define("js_prefetch",default=True,help="When running with js_reproxy, prefetch main pages to avoid holding up a js_interpreter instance if the remote server is down.  Turn this off if you expect most remote servers to be up and you want to detect js_429 issues earlier.") # (Doing prefetch per-core can lead to load imbalances when running multicore with more than one interpreter per core, as several new pages could be in process of fetch when only one interpreter is ready to take them.  Might want to run non-multicore and have just the interpreters using other cores if prefetch is needed.)
define("js_UA",help="Custom user-agent string for js_interpreter requests, if for some reason you don't want to use the JS browser's default (or the client's if js_reproxy is on and js_prefetch off). If you prefix js_UA with a * then the * is removed and the user-agent string is set by the upstream proxy (--js_reproxy) so scripts running in the JS browser itself will see its original user-agent.")
define("js_images",default=True,help="When js_interpreter is in use, instruct it to fetch images just for the benefit of Javascript execution. Setting this to False saves bandwidth but misses out image onload events.") # In edbrowse this will likely be treated as false anyway
# js_images=False may also cause some versions of Webkit to leak memory (PhantomJS issue 12903), TODO: return a fake image if js_reproxy? (will need to send a HEAD request first to verify it is indeed an image, as PhantomJS's Accept header is probably */*) but height/width will be wrong
define("js_size",default="1024x768",help="The virtual screen dimensions of the browser when js_interpreter is in use (changing it might be useful for screenshots)")
define("js_links",default=True,help="When js_interpreter is in use, handle some Javascript links via special suffixes on href URLs. Turn this off if you don't mind such links not working and you want to ensure URLs are unchanged modulo domain-rewriting.")
define("js_multiprocess",default=True,help="When js_interpreter is in use, handle the webdriver instances in completely separate processes (not just separate threads) when the multiprocessing module is available and working. Recommended: if a webdriver instance gets 'stuck' in a way that somehow hangs its controlling process, we can detect and restart it.")
define("ssl_fork",default=False,help="(Unix only) Run SSL-helper proxies as separate processes to stop the main event loop from being stalled by buggy SSL/TLS libraries. This costs RAM, but adding --multicore too will limit the number of helpers to one per core instead of one per port, so --ssl-fork --multicore is recommended if you want more js_interpreter instances than cores.")

heading("Server control options")
define("background",default=False,help="(Unix only) Fork to the background as soon as the server has started. You might want to enable this if you will be running it from crontab, to avoid long-running cron processes.")
define("restart",default=False,help="(Unix only) Try to terminate any other process listening on our port number before we start. Useful if Web Adjuster is running in the background and you want to quickly restart it with new options. Note that no check is made to make sure the other process is a copy of Web Adjuster; whatever it is, if it has our port open, it is asked to stop.")
define("stop",default=False,help="(Unix only) Like 'restart', but don't replace the other process after stopping it. This option can be used to stop a background server (if it's configured with the same port number) without starting a new one.")
# "stop" overrides "restart", so if "restart" is set in a configuration file then you can still use "stop" on the command line
define("install",default=False,help="Try to install the program in the current user's Unix crontab as an @reboot entry, unless it's already there.  The arguments of the cron entry will be the same as the command line, with no directory changes, so make sure you are in the home directory before doing this.  The program will continue to run normally after the installation attempt.  (If you are on Cygwin then you might need to run cron-config also.)")
define("pidfile",default="",help="Write our process ID to this file when running in the background, so you can set up a systemd service with Type=forking and PIDFile=this instead of using crontab. (Alternatively use 'pip install sdnotify' and run in the foreground with Type=notify.)")
# [Unit]
# Description=Web Adjuster
# [Install]
# Alias=adjuster.service  # ensure it's unique
# WantedBy=multi-user.target
# [Service]
# Type=notify  # or Type=forking if we have no sdnotify module
# ExecStart=/usr/bin/python adjuster.py --config=etc
# PIDFile=/path/to/pidfile (if Type=forking)
# WorkingDirectory= and User= need to be set
# can also set Environment=LD_PRELOAD=... if needed
# then do: sudo systemctl enable --now /path/to/adjuster.service
define("browser",help="The Web browser command to run. If this is set, Web Adjuster will run the specified command (which is assumed to be a web browser), and will exit when this browser exits. This is useful in conjunction with --real_proxy to have a personal proxy run with the browser. You still need to set the browser to use the proxy; this can sometimes be done via browser command line or environment variables.")
define("run",help="A command to run that is not a browser. If set, Web Adjuster will run the specified command and will restart it if it stops. The command will be stopped when Web Adjuster is shut down. This could be useful, for example, to run an upstream proxy.")
define("runWait",default=1,help="The number of seconds to wait before restarting the 'run' command if it fails")

heading("Media conversion options")
define("bitrate",default=0,help="Audio bitrate for MP3 files, or 0 to leave them unchanged. If this is set to anything other than 0 then the 'lame' program must be present. Bitrate is normally a multiple of 8. If your mobile device has a slow link, try 16 for speech.")
define("askBitrate",default=False,help="If True, instead of recoding MP3 files unconditionally, try to add links to \"lo-fi\" versions immediately after each original link so you have a choice.")
define("pdftotext",default=False,help="If True, add links to run PDF files through the 'pdftotext' program (which must be present if this is set). A text link will be added just after any PDF link that is found, so that you have a choice of downloading PDF or text; note that pdftotext does not always manage to extract all text (you can use --pdfomit to specify URL patterns that should not get text links). The htmlJson setting will also be applied to the PDF link finder, and see also the guessCMS option.")
define("pdfomit",help="A comma-separated list of regular expressions which, if any are found in a PDF link's URL, will result in a text link not being generated for that PDF link (although a conversion can still be attempted if a user manually enters the modified URL).  Use this to avoid confusion for PDF files you know cannot be converted.")
define("epubtotext",default=False,help="If True, add links to run EPUB files through Calibre's 'ebook-convert' program (which must be present), to produce a text-only option (or a MOBI option if a Kindle is in use). A text link will be added just after any EPUB link that is found, so that you have a choice of downloading EPUB or text. The htmlJson setting will also be applied to the EPUB link finder, and see also the guessCMS option.")
# pdftotext and epubtotext both use temporary files, which are created in the system default temp directory unless overridden by environment variables TMPDIR, TEMP or TMP, TODO: do we want an override for NamedTemporaryFile's dir= option ourselves?  (/dev/shm might make more sense on some Flash-based systems, although filling the RAM and writing to swap might do more damage than writing files in /tmp if it gets big; also hopefully some OS's won't actually write anything if the file has been deleted before the buffer needed to be flushed (TODO: check this))
define("epubtozip",default=False,help="If True, add links to download EPUB files renamed to ZIP, as a convenience for platforms that don't have EPUB readers but can open them as ZIP archives and display the XHTML files they contain. The htmlJson setting will also be applied to the EPUB link finder, and see also the guessCMS option.")
# epubtozip TODO: option to cache the epub file and serve its component files individually, so other transforms can be applied and for platforms without ZIP capabilities
define("guessCMS",default=False,help="If True, then the pdftotext, epubtotext and epubtozip options attempt to guess if a link is pointing to a PDF or EPUB file via a Content Management System (i.e. the URL does not end in .pdf or .epub, but contains something like ?format=PDF)")
# TODO: guessCMS doesn't seem to work very well with the askBitrate option
define("pdfepubkeep",default=200,help="Number of seconds to keep any generated text files from PDF and EPUB.  If this is 0, the files will be deleted immediately, but that might be undesirable: if a mobile phone browser has a timeout that takes effect before ebook-convert has finished (this can sometimes be the case with Opera Mini for example), it might be best to allow the user to wait a short time and re-submit the request, this time getting a cached response.")
# pdfepubkeep: note also that Opera Mini's opera:config can set the loading timeout to longer, default is 30 seconds.
define("waitpage",default=True,help="If the browser seems to be an interactive one, generate a 'please wait' page while converting PDF or EPUB files to text. Not effective if pdfepubkeep is set too low.")
# waitpage TODO: mp3 also? (would need to add MP3s to pdfepubkeep)

heading("Character rendering options")
# TODO: option to add a switch at top of page ?
define("render",default=False,help="Whether to enable the character-set renderer. This functionality requires the Python Imaging Library and suitable fonts. The settings of htmlJson and leaveTags will also be applied to the renderer. Text from computed Javascript writes might not be rendered as images.")
# ("computed" as in not straight from a JSON document.  TODO: could write a piece of JS that goes through the DOM finding them? ditto any JS alterations that haven't been through htmlFilter, although you'd have to mark the ones that have and this could be filter-dependent)
define("renderFont",help="The font file to use for the character-set renderer (if enabled). This should be a font containing all the characters you want to render, and it should be in .TTF, .OTF or other Freetype-supported format (.PCF is sometimes possible if renderSize is set correctly, e.g. 16 for wenquanyi_12pt.pcf)")
# renderFont TODO: different fonts for different Unicode ranges? (might be hard to auto-detect missing characters)
define("renderInvert",default=False,help="If True, the character-set renderer (if enabled) will use a black background. Useful when you are also adding a stylesheet with a dark background.")
define("renderSize",default=20,help="The height (in pixels) to use for the character-set renderer if it is enabled.")
define("renderPath",default="/@_",help="The location on every adjusted website to put the character-set renderer's images, if enabled. This must be made up of URL-safe characters starting with a / and should be a short path that is unlikely to occur on normal websites.")
define("renderFormat",default="png",help="The file format of the images to be created by the character-set renderer if it is enabled, for example 'png' or 'jpeg'.")
define("renderRange",multiple=True,help="The lowest and highest Unicode values to be given to the character-set renderer if it is enabled. For example 3000:A6FF for most Chinese characters. Multiple ranges are allowed. Any characters NOT in one of the ranges will be passed to the browser to render. If the character-set renderer is enabled without renderRange being set, then ALL text will be rendered to images.")
define("renderOmit",multiple=True,default="iPhone,iPad,Android,CrOS,Macintosh,Windows NT 6,Windows NT 10,Windows Phone OS,Lynx/2",help="A list of platforms that do not need the character-set renderer. If any of these strings occur in the user-agent then the character set renderer is turned off even if it is otherwise enabled, on the assumption that these platforms either have enough fonts already, or wouldn't show the rendered images anyway.")
# (Explanation for renderOmit defaults: Win Vista=6.0 7=6.1 8=6.2 reportedly don't need language packs for display; Windows 11 is still "Windows NT 10"; Lynx: being careful by specifying /2 to try to avoid false positives; don't list w3m as some versions can do graphics; not sure about Links/ELinks etc)
define("renderOmitGoAway",default=False,help="If set, any browsers that match renderOmit will not be allowed to use the adjuster. This is for servers that are set to do character rendering only and do not have enough bandwidth for people who don't need this function and just want a proxy.")
# renderOmitGoAway: see also the extended syntax of the headAppendCSS option, which forces all users to choose a stylesheet, especially if cssName is not set; that might be useful if the server's sole purpose is to add stylesheets and you don't want to provide a straight-through service for non-stylesheet users.
define("renderCheck",help="If renderOmit does not apply to the browser, it might still be possible to check for native character-set support via Javascript. renderCheck can be set to the Unicode value of a character to be checked (try 802F for complete Chinese support); if the browser reports its width differently from known unprintable characters, we assume it won't need our renderer.")
# renderCheck: 802F shouldn't create false positives in environments that support only GB2312, only Big5, only SJIS or only KSC instead of all Chinese. It does have GB+ and Big5+ codes (and also demonstrates that we want a hex number). If browser's "unprintable character" glyph happens to be the same width as renderCheck anyway then we could have a false negative, but that's better than a false positive and the user can still switch it off manually if renderName is left set.
define("renderNChar",default=1,help="The maximum number of characters per image to be given to the character-set renderer if it is enabled. Keeping this low means the browser cache is more likely to be able to re-use images, but some browsers might struggle if there are too many separate images. Don't worry about Unicode \"combining diacritic\" codes: any found after a character that is to be rendered will be included with it without counting toward the renderNChar limit and without needing to be in renderRange.")
define("renderWidth",default=0,help="The maximum pixel width of a 'word' when using the character-set renderer. If you are rendering a language that uses space to separate words, but are using only one or two characters per image, then the browser might split some words in the middle. Setting renderWidth to some value other than 0 can help to prevent this: any word narrower than renderWidth will be enclosed in a <nobr> element. (This will however be ineffective if your stylesheet overrides the behaviour of <nobr>.) You should probably not set renderWidth if you intend to render languages that do not separate words with spaces.")
define("renderDebug",default=False,help="If the character-set renderer is having problems, try to insert comments in the HTML source to indicate why.  The resulting HTML is not guaranteed to be well-formed, but it might help you debug a misbehaving htmlFilter.  This option may also insert comments in bad HTML before the htmlFilter stage even when the renderer is turned off.")
define("renderName",default="Fonts",help="A name for a switch that allows the user to toggle character set rendering on and off from the browser (via a cookie and Javascript links at the bottom of HTML pages); if set to the empty string then no switch is displayed. At any rate none is displayed when renderOmit applies.") # TODO: non-Javascript fallback for the switcher

heading("Dynamic DNS options")
define("ip_change_command",help="An optional script or other shell command to launch whenever the public IP address changes. The new IP address will be added as a parameter; ip_query_url must be set to make this work. The script can for example update any Dynamic DNS services that point to the server.")
define("ip_change_tries",default=1,help="Number of times to run ip_change_command if it returns failure (0 means unlimited, which is not recommended).  For example, you can have the script return failure if it doesn't get either an \"Updated\" or an expected \"not changed\" response from a Dynamic DNS service (but it is not advisable to expect a host lookup to reflect the change immediately)")
define("ip_change_delay",default=5,help="Number of seconds to delay between tries of ip_change_command if it fails")
define("ip_query_url",help="URL that will return your current public IP address, as a line of text with no markup added. Used for the ip_change_command option. You can set up a URL by placing a CGI script on a server outside your network and having it do: echo Content-type: text/plain ; echo ; echo $REMOTE_ADDR (but if you want your IPv4 address, ensure the adjuster machine and the outside server are not both configured for IPv6). If you have a known static IP address but still want to run an ip_change_command for it, you can set ip_query_url to the static IP address instead of a URL.") # If you want something more complex (fallback IP servers, SSH_CLIENT values for tunnels, etc) then you could use a local CGI script to do it
define("ip_query_url2",help="Optional additional URL that might sometimes return your public IP address along with other information. This can for example be a status page served by a local router (http://user:password@192.168... is accepted, and if the password is the name of an existing file then its contents are read instead). If set, the following behaviour occurs: Once ip_check_interval has passed since the last ip_query_url check, ip_query_url2 will be queried at an interval of ip_check_interval2 (which can be short), to check that the known IP is still present in its response. Once the known IP is no longer present, ip_query_url will be queried again. This arrangement can reduce the load on ip_query_url while allowing a reduced ip_check_interval for faster response to IP changes, while not completely trusting the local router to report the correct IP at all times. (If it's notoriously unleriable then it might be best NOT to reduce ip_check_interval, in which case at least you'll get a faster response once the initial ip_check_interval wait has passed after the previous IP change; this however might not be suitable if you're behind a router that is frequently rebooting.) See also ip_query_aggressive if the router might report an IP change before connectivity is restored. You may also set ip_query_url2 to the special value 'upnp' if you want it to query a router via UPnP (miniupnpc package required).") # (If using filename then its contents will be re-read every time the URL is used; this might be useful for example if the router password can change)
define("ip_check_interval",default=8000,help="Number of seconds between checks of ip_query_url for the ip_change_command option")
define("ip_check_interval2",default=60,help="Number of seconds between checks of ip_query_url2 (if set), for the ip_change_command option")
define("ip_query_aggressive",default=False,help="If a query to ip_query_url fails with a connection error or similar, keep trying again until we get a response. This is useful if the most likely reason for the error is that our ISP is down: we want to get the new IP just as soon as we're back online. However, if the error is caused by a problem with ip_query_url itself then this option can lead to excessive traffic, so use with caution. (Log entries are written when this option takes effect, and checking the logs is advisable.)")
define("ip_force_interval",default=7*24*3600,help="Number of seconds before ip_change_command (if set) is run even if there was no IP change.  This is to let Dynamic DNS services know that we are still around.  Set to 0 to disable forced updates (a forced update will occur on server startup anyway), otherwise an update will occur on the next IP check after ip_force_interval has elapsed.")
define("pimote",help="Use an Energenie Pi-mote home control system to power-cycle the router when its Internet connection appears to be stuck in a bad state.  This option works only if Web Adjuster is running on the Raspberry Pi and as a user in the \"gpio\" group.  It must be set to R,S,I,D where R is the internal IP address of your router, S is the domain of your Internet service provider (assumed to be quick to look up), I is the IP provided by your router's built-in DNS when it's having trouble (e.g. Post Office Broadband's AMG1302-derived router responds with 219.87.158.116 which is presumably Zyxel's office in Taiwan), and D is the Pi-mote device ID (1 to 4 or all) used to switch it off and on again.  Power-cycling will be initiated if two queries to the router's DNS for its ISP domain either fail or return internalResponse, and it's assumed router caching will let us check status frequently without causing traffic.")

heading("Speedup options")
define("useLXML",default=False,help="Use the LXML library for parsing HTML documents. This is usually faster, but it can fail if your system does not have a good installation of LXML and its dependencies. Use of LXML libraries may also result in more changes to all HTML markup: this should be harmless for browsers, but beware when using options like bodyAppendGoesAfter then you might or might not be dealing with the original HTML depending on which filters are switched on.")
# useLXML: (hence bodyAppendGoesAfter now takes regexps as of adjuster 0.1836) / dependencies: did have ", or if the websites you visit are badly broken" but it turns out some breakages are actually better handled by LXML than by HTMLParser, e.g. <div id=something">
define("usepycurl",default=True,help="Use the pycurl library if a suitable version is available (setting this to False might save a little RAM at the expense of remote-server tolerance)")
define("renderBlocks",default=False,help="Treat all characters rendered by the character-set renderer as \"blocks\" that are guaranteed to have the same dimensions (true for example if you are using the renderer for Chinese characters only). This is faster than checking words individually, but it may produce misprints if given a range of characters whose dimensions do differ.")
# renderBlocks TODO: blocksRange option for if want to render some that do and some that don't? (but profile it: PIL's getsize just might turn out to be quicker than the high-level range-check code)
define("fasterServer",help="Address:port of another instance of Web Adjuster to which we forward all traffic whenever it is available. When the other instance is not available, traffic will be handled by this one. Use for example if you have a slower always-on machine and a faster not-always-on machine and you want the slower machine to delegate to the faster machine when available. See also ipTrustReal.")
define("ipTrustReal",help="IP address of a machine that we trust, for example a machine that is using us as fasterServer. Any traffic coming from this machine with an X-Real-Ip header will be logged as though it originated at the value of its X-Real-Ip header. Setting this to * will cause X-Real-Ip to be trusted from ANY connection.")
# , which might be useful in an environment where you know the adjuster can be reached only via a proxy but the proxy's address can change; see also trust_XForwardedFor. (TODO: multiple IPs option like ip_messages?  but might need to make it ipv6 ready)
define("trust_XForwardedFor",default=False,help="Like ipTrustReal but trusts X-Forwarded-For header from any IP if set to True (use this in an environment where the adjuster can be reached only via a load balancer etc)")
define("fasterServerNew",default=True,help="If fasterServer is set, assume it is running Web Adjuster v0.17 or later and use a more lightweight method of checking its availability. You might need to set this to False if for some reason you can't upgrade the fasterServer first.")
# (fasterServerNew: don't do auto-fallback as that creates unnecessary extra traffic, plus sending an unrecognized ping2 could clutter logs)
define("machineName",help="A name for the current machine to insert into the \"Server\" HTTP header for adjusted requests, for example to let users know if it's your faster or your slower machine that's currently serving them (although they'd need to inspect the headers to find out)")
define("redirectFiles",default=False,help="If, when not functioning as a \"real\" HTTP proxy, a URL is received that looks like it requires no processing on our part (e.g. an image or downloadable file that the user does not want converted), and if this is confirmed via a HEAD request to the remote server, then redirect the browser to fetch it directly and not via Web Adjuster. This takes bandwidth off the adjuster server, and should mean faster downloads, especially from sites that are better connected than the adjuster machine. However it might not work with sites that restrict \"deep linking\". (As a precaution, the confirmatory HEAD request is sent with a non-adjusted Referer header to simulate what the browser would send if fetching directly. If this results in an HTML \"Referer denied\" message then Web Adjuster will proxy the request in the normal way. This precaution might not detect ALL means of deep-linking denial though.)")
# --- e.g. it won't detect cookie-based deep-linking denial, or serving an image but not the real one.  But it works with Akamai-based assets servers as of 2013-09 (but in some cases you might be able to use codeChanges to point these requests back to the site's original server instead of the Akamai one, if the latter just mirrors the former which is still available, and therefore save having to proxy the images.  TODO: what if you can't do that but you can run another service on a higher bandwidth machine that can cache them, but can't run the adjuster on the higher-bandwidth machine; can we redirect?)
# If adjuster machine is running on a home broadband connection, don't forget the "uplink" speed of that broadband is likely to be lower than the "downlink" speed; the same should not be the case of a site running at a well-connected server farm.  There's also extra delay if Web Adjuster has to download files first (which might be reduced by implementing streaming).  Weighed against this is the extra overhead the browser has of repeating its request elsewhere, which could be an issue if the file is small and the browser's uplink is slow; in that case fetching it ourselves might be quicker than having the browser repeat the request; see TODO comment elsewhere about minimum content length before redirectFiles.
# TODO: for Referer problems in redirectFiles, if we're not on HTTPS, could redirect to an HTTPS page (on a separate private https server, or https://www.google.com/url/?q= but they might add checks) which then redirs to the target HTTP page, but that might not strip Referer on MSIE 7 etc, may have to whitelist browsers+versions for it, or test per-request but that wld lead to 4 redirects per img instead of 2 although cld cache (non-empty) ok-browser-strings (and hold up other requests from same browser until we know or have timed out ??); do this only if sendHead returns false but sendHead with proper referer returns ok (and cache a few sites where this is the case so don't have to re-test) ??  also it might not work in places where HTTPS is forbidden
# TODO: redirectFiles could call request_no_external_referer and test with blank Referer instead of non-adjusted Referer, but we'd have to figure out some way of verifying that the browser actually supports 'Referrer-Policy: same-origin' before doing this

define("upstream_guard",default=True,help="Modify scripts and cookies sent by upstream sites so they do not refer to the cookie names that our own scripts use. This is useful if you chain together multiple instances of Web Adjuster, such as for testing another installation without coming out of your usual proxy. If however you know that this instance will not be pointed to another, you can set upstream_guard to False to save some processing.")
define("skipLinkCheck",multiple=True,help="Comma-separated list of regular expressions specifying URLs to which we won't try to add or modify links for the pdftotext, epubtotext, epubtozip, askBitrate or mailtoPath options.  This processing can take some time on large index pages with thousands of links; if you know that none of them are PDF, EPUB, MP3 or email links, or if you don't mind not processing any that are, then it saves time to skip this step for those pages.")
# skipLinkCheck TODO: it would be nice to have a 'max links on the page' limit as an alternative to a list of URL patterns

define("extensions",help="Name of a custom Python module to load to handle certain requests; this might be more efficient than setting up a separate Tornado-based server. The module's handle() function will be called with the URL and RequestHandler instance as arguments, and should return True if it processed the request, but anyway it should return as fast as possible. This module does NOT take priority over forwarding the request to fasterServer.")

define("loadBalancer",default=False,help="Set this to True if you have a default_site set and you are behind any kind of \"load balancer\" that works by issuing a GET / with no browser string. This option will detect such requests and avoid passing them to the remote site.")
define("multicore",default=False,help="(Linux and BSD) On multi-core CPUs, fork enough processes for all cores to participate in handling incoming requests. This increases RAM usage, but can help with high-load situations. Disabled on Mac due to unreliability (other cores can still be used for htmlFilter etc)")
# --- and --ssl-fork if there's not TOO many instances taking up the RAM; if you really want multiple cores to handle incoming requests on Mac/BSD you could run GNU/Linux in a virtual machine (or use a WSGI server)
define("num_cores",default=0,help="Set the number of CPU cores for the multicore option (0 for auto-detect)")
define("internalPort",default=0,help="The first port number to use for internal purposes when ssl_fork is in effect.  Internal ports needed by real_proxy (for SSL/TLS) and js_reproxy are normally allocated from the ephemeral port range, but if ssl_fork delegates to independent processes then some of them need to be at known numbers. The default of 0 means one higher than 'port'; several unused ports may be needed starting at this number. If your Tornado is modern enough to support reuse_port then you can have multiple Adjuster instances listening on the same port (e.g. for one_request_only) provided they have different internalPort settings when run with ssl_fork.  Note however that the --stop and --restart options will NOT distinguish between different internalPort settings, only 'port'.")
# Some environments (e.g. old OpenShift 2) can't use real_proxy or js_reproxy because the container won't let us open extra ports even for internal purposes; TODO: find some way to multiplex everything on one port? how to authenticate our JS-interpreter connections if the load-balancer makes remote connections to that port also seem to come from our IP?
define("fixed_ports",default=False,help="Do not allocate ports (even internal ports) from the ephemeral port range even when this is otherwise possible. This option might help if you are firewalling your loopback interface and want to write specific exceptions (although that still won't work if you're using js_interpreter=HeadlessChrome or similar which opens its own ephemeral ports as well: use containers if you're concerned). Fixed ports may result in failures if internal ports are already taken.")
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
define("logRedirectFiles",default=True,help="Whether or not to log requests that result in the browser being simply redirected to the original site when the redirectFiles option is on.")
# (Since redirectFiles still results in a HEAD request being sent to the remote site, the logRedirectFiles option defaults to True in case you need it to diagnose "fair use of remote site via adjuster" problems)
define("ipNoLog",multiple=True,help="A comma-separated list of IP addresses which can use the adjuster without being logged. If your network has a \"friendly probing\" service then you might want to use this to stop it filling up the logs.  (Any tracebacks it causes will still be logged however.)")
define("squashLogs",default=True,help="Try to remove some duplicate information from consecutive log entries, to make logs easier to check. You might want to set this to False if you plan to use automatic search tools on the logs. Currently not supported with multicore, and will automatically be set to False if multicore is enabled.")
# (squashLogs: word 'some' is important as not all duplicate info is guaranteed to be removed. TODO: move BrowserLogger to the collection process so can collate for multicore?)
define("errorHTML",default="Adjuster error has been logged",help="What to say when an uncaught exception (due to a misconfiguration or programming error) has been logged. HTML markup is allowed in this message. If for some reason you have trouble accessing the log files, the traceback can usually be included in the page itself by placing {traceback} in the message.")
# errorHTML TODO: this currently requires Tornado 2.1+ (document this? see TODO in write_error)
define("logDebug",default=False,help="Write debugging messages (to standard error if in the foreground, or to the logs if in the background). Use as an alternative to --logging=debug if you don't also want debug messages from other Tornado modules. On Unix you may also toggle this at runtime by sending SIGUSR1 to the process(es).") # see debuglog()
# and continuing into the note below:
if not tornado:
    if html: print ("</dl>")
    end = "Tornado-provided logging options are not listed above because they might vary across Tornado versions; run <kbd>python adjuster.py --help</kbd> to see a full list of the ones available on your setup. They typically include <kbd>log_file_max_size</kbd>, <kbd>log_file_num_backups</kbd>, <kbd>log_file_prefix</kbd> and <kbd>log_to_stderr</kbd>."
    # and --logging=debug, but that may generate a lot of entries from curl_httpclient
    if html: print (end)
    else: print (end.replace("<kbd>","`").replace("</kbd>","`"))
    raise SystemExit

#@file: import2-other.py
# --------------------------------------------------
# Further imports
# --------------------------------------------------

import time,socket,logging,subprocess,threading,base64,signal,traceback,shutil
try: from string import letters,digits # Python 2
except ImportError:
    from string import ascii_letters as letters # Python 3
    from string import digits
try: import urlparse # Python 2
except ImportError: import urllib.parse as urlparse # Python 3
try: from urllib import quote,unquote # Python 2
except ImportError: from urllib.parse import quote,unquote # Python 3
try: import htmlentitydefs # Python 2
except ImportError: import html.entities as htmlentitydefs # Python 3
try: from urllib2 import build_opener,Request,ProxyHandler,HTTPRedirectHandler,urlopen # Python 2
except ImportError: from urllib.request import build_opener,Request,ProxyHandler,HTTPRedirectHandler,urlopen # Python 3
try: from urllib2 import HTTPError as UL_HTTPError # Python 2
except ImportError: from urllib.error import HTTPError as UL_HTTPError # Python 3
try: from commands import getoutput # Python 2
except ImportError: from subprocess import getoutput # Python 3
try: import simplejson as json # Python 2.5, and faster?
except ImportError: import json # Python 2.6
try: from HTMLParser import HTMLParser,HTMLParseError # Python 2
except ImportError:
    from html.parser import HTMLParser as _HTMLParser # Python 3
    class HTMLParser(_HTMLParser):
        def __init__(self): _HTMLParser.__init__(self,convert_charrefs=False) # please behave as the old one did
    try: from html.parser import HTMLParseError # removed in Python 3.5
    except ImportError: # we use it only for recognition anyway
        class HTMLParseError(Exception): pass
try: import psutil
except ImportError: psutil = None
try: # Python 2
    from cStringIO import StringIO as BytesIO
    from StringIO import StringIO # for when need Unicode
except ImportError: from io import BytesIO,StringIO # Python 3
try: from inspect import getfullargspec as getargspec # Python 3
except ImportError:
    try: from inspect import getargspec # Python 2
    except ImportError: getargspec = None
try: xrange # Python 2
except: xrange,unicode,unichr = range,str,chr # Python 3
try: bytes
except: bytes = str

try: # can we page the help text?
    # (Tornado 2 just calls the module-level print_help, but Tornado 3 includes some direct calls to the object's method, so we have to override the latter.  Have to use __dict__ because they override __setattr__.)
    import pydoc ; pydoc.pager # ensure present
    def new_top(*args):
        dat = StringIO()
        dat.write(twoline_program_name+"\n")
        old_top(dat)
        pydoc.pager(dat.getvalue())
        raise SystemExit
    old_top = tornado.options.options.print_help
    tornado.options.options.__dict__['print_help'] = new_top
except: pass # oh well, can't page the help text

#@file: domain-rewrite.py
# --------------------------------------------------
# Domain-rewriting service routines
# --------------------------------------------------

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
    if requested_host:
      requested_host = B(requested_host)
      port=B(":"+str(options.publicPort))
      # port might or might not be present in user's request
      orig_requested_host = requested_host
      if requested_host.endswith(port): requested_host=requested_host[:-len(port)]
      n=0
      for h in options.host_suffix.split("/"):
        if (requested_host.endswith(B("."+h)) or options.alt_dot and requested_host.endswith(B(options.alt_dot+h))) and options.wildcard_dns: return redot(requested_host[:-len(h)-(1 if requested_host.endswith(B("."+h)) else len(options.alt_dot))])
        elif requested_host == B(h):
            d = defaultSite(n)
            if d: return B(d)
            elif B(cookie_host)==B(h): return 0
            else: return B(cookie_host)
        n += 1
      if options.real_proxy: return orig_requested_host
    return B(defaultSite())
def convert_to_via_host(requested_host):
    if not requested_host: requested_host = "" # ??
    else: requested_host = S(requested_host)
    port=":"+str(options.publicPort) # the port to advertise
    orig_requested_host = requested_host
    if requested_host.endswith(port): requested_host=requested_host[:-len(port)]
    if options.publicPort==80: port=""
    for h in options.host_suffix.split("/"):
      if requested_host == h and options.default_site or requested_host.endswith("."+h) or options.alt_dot and requested_host.endswith(options.alt_dot+h): return h+port
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
        if B(real_host) == B(i):
            return hostSuffix(n)+port
        n += 1
    elif not options.wildcard_dns and B(real_host) == B(cookie_host):
        return hostSuffix(0)+port # no default_site, cookie_host everywhere
    if not options.wildcard_dns or options.wildcard_limit and not real_host in [x+".0" for x in options.wildcard_limit.split(",")]: return real_host # leave the proxy
    else: return dedot(real_host)+(options.alt_dot if options.alt_dot else ".")+hostSuffix()+port

# RFC 2109: A Set-Cookie from request-host y.x.example.com for Domain=.example.com would be rejected, because H is y.x and contains a dot.
# That means (especially if a password is set) we'd better make sure our domain-rewrites don't contain dots.  If requested with dot, relocate to without dot.  (But see below re RFC 1035 limitation.)
def dedot(domain):
    # - means . but -- is a real - (OK as 2 dots can't come together and a - can't come immediately after a dot in domain names, so --- = -., ---- = --, ----- = --. etc)
    domain = S(domain)
    d2 = domain.replace("-","--").replace(".","-") # this scheme, which I invented in 2012, was adopted by Google Translate (at the domain 'translate.goog') in 2018
    if len(d2) > 63: return domain # We can't do it because RFC 1035 puts a 63-byte limit on each label (so our cross-domain preferences cookies can't work on very long domains, TODO document this?)
    else: return d2
def redot(domain): return B(domain).replace(B("--"),B("@MINUS@")).replace(B("-"),B(".")).replace(B("@MINUS@"),B("-"))

def protocolAndHost(realHost):
    # HTTPS hack: host ends with .0 = use HTTPS instead of HTTP
    # (the dot will be represented as a hyphen by dedot/redot,
    # but some servers e.g. GAE can't cope with any part of the
    # wildcard domain ending with a hyphen, so add the 0;
    # TODO: what about fetching from IP addresses, although it's rare to get a server with IP ending .0 because it used to represent "the network")
    if B(realHost).endswith(B(".0")):
        return "https://",realHost[:-2]
    else: return "http://",realHost
def protocolWithHost(realHost):
    x,y = protocolAndHost(realHost) ; return S(x)+S(y)

def domain_process(text,cookieHost=None,stopAtOne=False,https=None,isProxyRequest=False,isSslUpstream=False):
    text = B(text)
    if isProxyRequest:
        # When running as a real proxy, domain_process is
        # still called for Location: headers etc (not for
        # document bodies), and the only thing we need to
        # check is the upstream_rewrite_ssl option: if our
        # UPstream proxy says .0 in a Location: URL due to
        # upstream_rewrite_ssl, then take it out.
        if upstream_rewrite_ssl and not isSslUpstream:
            m = re.match(B(r"http(://[A-Za-z0-9.-]*)\.0(?![A-Za-z0-9.-])"),text)
            if m: return B("https")+m.group(1)
        return text
    # Change the domains on appropriate http:// and https:// URLs.
    # Also on // URLs, using 'https' as default (if it's not None) for the expected onward fetch.
    # Hope that there aren't any JS-computed links where
    # the domain is part of the computation.
    # TODO: what of links to alternate ports or user:password links, currently we leave them unchanged (could use .<portNo> as an extension of the 'HTTPS hack' of .0, but allowing the public to request connects to any port could be a problem, and IP addresses would have to be handled carefully: can no longer rely on ".0 used to mean the network" sort-of saving us)
    # TODO: leave alone URLs in HTML text/comments and JS comments? but script overload can make it hard to judge what is and isn't text. (NB this function is also called for Location headers)
    if B("<!DOCTYPE") in text:
        # don't touch URLs inside the doctype!
        dtStart = text.index(B("<!DOCTYPE"))
        dtEnd = text.find(B(">"),dtStart)
    else: dtStart = dtEnd = -1
    def mFunc(m):
        if dtStart<m.start()<dtEnd: # avoid doctype
            return m.group()
        i = m.start()
        if i and text[i-1:i].split() and text[:i].rsplit(None,1)[-1].startswith(B("xmlns")): return m.group() # avoid xmlns="... xmlns:elementname='... etc
        protocol,auth,oldhost = m.groups() # e.g. sentry.io uses username@ in its scripts 2025
        if oldhost[-1] in B(".-"): return m.group() # omit links ending with . or - because they're likely to be part of a domain computation; such things are tricky but might be more likely to work if we DON'T touch them if it has e.g. "'test.'+domain" where "domain" is a variable that we've previously intercepted
        protocol = S(protocol)
        if protocol=="//":
            if https: protocol = "https://"
            else: protocol = "http://"
        if protocol=="https://": oldhost += B(".0") # HTTPS hack (see protocolAndHost)
        newHP = B(convert_to_requested_host(oldhost,cookieHost))
        if newHP.endswith(B(".0")): return m.group() # undo HTTPS hack if we have no wildcard_dns and convert_to_requested_host sent that URL off-site
        if not auth: auth = B("")
        return B(options.urlscheme)+auth+newHP
    if stopAtOne: count=1
    else: count=0
    return re.sub(B(r"((?:https?://)|(?:(?<=['"+'"'+r"])//))([A-Za-z0-9%:_-]+@)?([A-Za-z0-9.-]+)(?=[/?'"+'"'+r"]|$)"),mFunc,text,count) # http:// https:// or "// in scripts (but TODO: it won't pick up things like host="www.example.com"; return "https://"+host, also what about embedded IPv6 addresses i.e. \[[0-9a-fA-F:]*\] in place of hostnames (and what should we rewrite them to?)  Hopefully IPv6-embedding is rare as such sites wouldn't be usable by IPv4-only users (although somebody might have IPv6-specific versions of their pages/servers); if making Web Adjuster IPv6 ready, also need to check all instances of using ':' to split host from port as this won't be the case if host is '[' + IPv6 + ']'.  Splitting off hostname from protocol is more common though, e.g. used in Google advertising iframes 2017-06)

def cookie_domain_process(text,cookieHost=None):
    def f(m):
        m = m.group()
        hasDot = m.startswith('.') # leading . on the cookie
        if hasDot: m = m[1:]
        newhost = convert_to_requested_host(m,cookieHost)
        if ':' in newhost: newhost=newhost[:newhost.index(':')] # don't put the port number, see comment in authenticates_ok
        if newhost==m and cookieHost and S(cookieHost).endswith(m): newhost = S(convert_to_requested_host(cookieHost,cookieHost)) # cookie set server.example.org instead of www.server.example.org; we can deal with that
        if hasDot and options.wildcard_dns and not options.alt_dot: return newhost[newhost.index('.'):] # best we can do is leak to all adjusted hosts (if altdot_bad_cookie_leak we can do this line as well to leak up a further level, but the result might get pruned: JS propagation probably more reliable in this case)
        return newhost
    return re.sub("(?i)(?<=; domain=)[^;]+",f,S(text))

def can_do_cookie_host():
    return "" in options.default_site.split("/")

def url_is_ours(url,cookieHost="cookie-host\n"):
    # check if url has been through domain_process,
    # if so, returns the corresponding real URL it represents
    url = B(url)
    if not re.match(B("(https?:)?//"),url): return False
    url=url[url.index(B("/"))+2:]
    if B('/') in url:
        url,rest=url.split(B('/'),1)
        rest = B('/')+rest
    else: rest = B("")
    if B('?') in url:
        url,r2=url.split(B('?'),1)
        rest = B('?')+r2+rest
    rh = B(convert_to_real_host(url,cookieHost))
    if rh and not type(rh)==int and not rh==url:
        # (exact value is used by RewriteExternalLinks)
        if rh.endswith(B(".0")): r=B("https://")+rh[:-2]
        else: r=B("http://")+rh
        return r + rest

def fixDNS(val,reqH):
    # undo our domain rewrites (for Referer and for the path part of the URL); change http://X-0 to https://X (HTTPS hack)
    start = 0 ; val = S(val)
    for http in ["http://", "http%3A%2F%2F",
                 "https://", "https%3A%2F%2F"]:
        if val.startswith(http):
            start = len(http) ; break
    i = start ; proto = val[:start]
    while i<len(val) and val[i] in letters+digits+'.-': i += 1
    if i<len(val) and val[i]==':': # port no.
        i += 1
        while i<len(val) and val[i] in digits: i += 1
    if i==start: return val
    r=B(convert_to_real_host(val[start:i],reqH.cookie_host()))
    if r in [-1,B("error")]: # shouldn't happen
        return val # (leave unchanged if it does)
    elif not r: r=B("") # ensure it's a string
    elif r.endswith(B(".0")): # undo HTTPS hack
        r = r[:-2]
        if proto and not proto.startswith("https"): proto=proto[:4]+'s'+proto[5:] # (TODO: what if not proto here?)
    return B(proto)+r+B(val[i:])

#@file: config.py
# --------------------------------------------------
# Reading configuration files etc
# --------------------------------------------------

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
    # usually due to a configuration problem
    try:
        if not istty(): logging.error(msg)
        # in case run from crontab w/out output (and e.g. PATH not set properly)
        # (but don't do this if not options.background, as log_to_stderr is likely True and it'll be more cluttered than the simple sys.stderr.write below)
    except: pass # options or logging not configured yet
    sys.stderr.write(msg+"\n")
    sys.exit(1)

def warn(msg):
    msg = "WARNING: "+msg
    try:
        if not istty(): logging.error(msg)
    except: pass
    sys.stderr.write(msg+"\n\n")

def parse_command_line(final):
  try:
    if sys.version_info[0]==2 and len(tornado.options.parse_command_line.func_defaults)==1: # Tornado 2.x (on Python 2.x)
        rest = tornado.options.parse_command_line()
    else:
        rest=tornado.options.parse_command_line(final=final)
    if rest: errExit("Unrecognised command-line argument '%s'" % rest[0]) # maybe they missed a '--' at the start of an option: don't want result to be ignored without anyone noticing
  except tornado.options.Error as e: optErr(e.message)
def optErr(m):
    if "PhantomJS" in m: m += " (try --js_interpreter=PhantomJS instead?)" # old option was --PhantomJS
    errExit(m)
def parse_config_file(cfg):
  try:
    check_config_file(cfg)
    if sys.version_info[0]==2 and not tornado.options.parse_config_file.func_defaults: # Tornado 2.x (on Python 2.x)
        tornado.options.parse_config_file(cfg)
    else: tornado.options.parse_config_file(cfg,final=False)
  except tornado.options.Error as e: optErr(e.message)
def check_config_file(cfg):
    # Tornado doesn't catch capitalisation and spelling errors etc by default
    try:
        options = tornado.options.options._options
        from tornado.util import exec_in
    except: return
    d = {} ; exec_in(open(cfg,'rb').read(),d,d)
    for k in d.keys():
        if not k in options and not k.replace('_','-') in options:
            if not type(d[k]) in [str,unicode,list,bool,int]: continue # allow functions etc in config file
            errExit("Unrecognised global '%s' in configuration file '%s'" % (k,cfg))

def readOptions():
    # Reads options from command line and/or config files
    parse_command_line(final=False)
    configsDone = [] ; cDir = []
    if not options.config: options.config=os.environ.get("ADJUSTER_CFG","") # environment check: must do HERE rather than setting default= in the define() call, or options.config=None below might not work
    while options.config and (options.config,os.getcwd()) not in configsDone:
        config = options.config ; options.config=None
        oldDir = os.getcwd()
        config2 = changeConfigDirectory(config)
        try: open(config2)
        except: errExit("Cannot open configuration file %s (current directory is %s)" % (config2,os.getcwd()))
        parse_config_file(config2)
        configsDone.append((config,oldDir))
        cDir.append(os.getcwd())
    configsDone.reverse() # we want config= within a config file to mean the outermost config overrides anything set in the innermost config, so read them in reverse order:
    for (config,_),cd in zip(configsDone,cDir):
        os.chdir(cd) ; parse_config_file(config)
    parse_command_line(True)
    # --- need to do this again to ensure logging is set up for the *current* directory (after any chdir's while reading config files) + ensure command-line options override config files

def preprocessOptions():
    initLogDebug() ; initLogging_preListen()
    if options.version:
        # If we get here, someone tried to put "version" in a config file.  Flag this as an error to save confusion.  (If it were on the command line, we wouldn't get here: we process it before loading Tornado.  TODO: if they DO try to put it in a config file, they might set some type other than string and get a less clear error message from tornado.options.)
        errExit("--version is for the command line only, not for config files")
    if options.one_request_only:
        if options.multicore or options.fasterServer: errExit("--one-request-only is not compatible with multicore or fasterServer")
        if (options.pdftotext or options.epubtotext or options.epubtozip) and (options.pdfepubkeep or options.waitpage):
            warn("pdfepubkeep and waitpage won't work with --one-request-only: clearing them")
            options.pdfepubkeep = options.waitpage = False
        if options.js_interpreter and not options.js_instances==1:
            errExit("--one-request-only doesn't make sense with a js_instances value other than 1")
            # (well we could start N instances if you like, but what's the point? - this probably indicates 'wrong config= option' or something, so flag it)
    if options.host_suffix==getfqdn_default:
        if wsgi_mode and os.environ.get("SERVER_NAME",""):
            # if we're running as a CGI, the server may have been configured to respond to more than one domain, in which case we want to prefer SERVER_NAME to getfqdn
            options.host_suffix = os.environ["SERVER_NAME"]
        else: options.host_suffix = socket.getfqdn()
    if type(options.mailtoSMS)==type(""): options.mailtoSMS=options.mailtoSMS.split(',')
    if type(options.leaveTags)==type(""): options.leaveTags=options.leaveTags.split(',')
    if type(options.stripTags)==type(""): options.stripTags=options.stripTags.split(',')
    if type(options.highlighting)==type(""): options.highlighting=options.highlighting.split(',')
    if options.render:
        try: import PIL
        except ImportError: errExit("render requires PIL")
    global force_htmlonly_mode
    if options.urlboxPath.startswith("*"):
        options.urlboxPath = options.urlboxPath[1:]
        force_htmlonly_mode = True
    else: force_htmlonly_mode = False
    if not options.urlboxPath.startswith("/"): options.urlboxPath = "/" + options.urlboxPath
    if options.stdio:
        if options.background: errExit("stdio is not compatible with background")
        if not options.port: errExit("stdio requires a port to be listening (haven't yet implemented processing a request on stdio without a port to forward it to; you could try --just-me etc in the meantime)")
    global tornado
    if options.js_interpreter:
      if options.js_instances < 1: errExit("js_interpreter requires positive js_instances")
      global webdriver
      if options.js_interpreter=="edbrowse":
        check_edbrowse()
        if options.js_frames or options.js_links:
          warn("--js_frames and --js-links not yet implemented with edbrowse, clearing them")
          options.js_frames = options.js_links = False
      else:
        try: from selenium import webdriver
        except: errExit("js_interpreter requires selenium (unless using --js-interpreter=edbrowse)")
        if not options.js_interpreter in ["PhantomJS","HeadlessChrome","HeadlessFirefox","Chrome","Firefox"]: errExit("js_interpreter (if set) must be PhantomJS, HeadlessChrome, HeadlessFirefox, Chrome, Firefox or edbrowse")
      if "x" in options.js_size:
        w,h = options.js_size.split("x",1)
      else: w,h = options.js_size,768
      w,h = intor0(w),intor0(h)
      if not (w and h) and options.js_interpreter in ["PhantomJS","HeadlessChrome","HeadlessFirefox"]:
        warn("Unrecognised size '%s', using 1024x768\n" % options.js_size)
        w,h = 1024,768
      global js_size
      if w and h: js_size = (w,h)
      else: js_size = None # for non-headless and not specified
      if not multiprocessing: options.js_multiprocess = False
      if options.js_429 and options.multicore and not multiprocessing: errExit("js_429 with multicore requires the multiprocessing module to be available (Python 2.6+)")
    elif options.js_upstream: errExit("js_upstream requires a js_interpreter to be set")
    if options.js_timeout2 <= options.js_timeout1: errExit("js_timeout2 must be greater than js_timeout1")
    assert not (options.js_upstream and set_window_onerror), "Must have set_window_onerror==False when using options.js_upstream"
    create_inRenderRange_function(options.renderRange)
    if type(options.renderOmit)==type(""): options.renderOmit=options.renderOmit.split(',')
    if type(options.cacheOmit)==type(""): options.cacheOmit=options.cacheOmit.split(',')
    if type(options.zeroWidthDelete)==type(""): options.zeroWidthDelete=options.zeroWidthDelete.split(',')
    if options.renderOmitGoAway:
        if options.renderCheck: errExit("Setting both renderOmitGoAway and renderCheck is not yet implemented (renderOmitGoAway assumes all testing is done by renderOmit only).  Please unset either renderOmitGoAway or renderCheck.")
        options.renderName = "" # override renderName to blank so it can't be switched on/off, because there's not a lot of point in switching it off if we're renderOmitGoAway (TODO: document this behaviour?)
    if type(options.deleteOmit)==type(""): options.deleteOmit=options.deleteOmit.split(',')
    if type(options.cssName)==type(""): options.cssName=options.cssName.replace('"',"&quot;") # for embedding in JS
    if type(options.cssNameReload)==type(""): options.cssNameReload=options.cssNameReload.split(',')
    if type(options.search_sites)==type(""): options.search_sites=options.search_sites.split(',')
    if type(options.ipNoLog)==type(""): options.ipNoLog=options.ipNoLog.split(',')
    if type(options.delete)==type(""): options.delete=options.delete.split(',')
    if type(options.delete_css)==type(""): options.delete_css=options.delete_css.split(',')
    if type(options.prohibit)==type(""): options.prohibit=options.prohibit.split(',')
    if type(options.prohibitUA)==type(""): options.prohibitUA=options.prohibitUA.split(',')
    if type(options.skipLinkCheck)==type(""): options.skipLinkCheck=options.skipLinkCheck.split(',')
    global viaName,serverName,serverName_html
    viaName = __doc__[:__doc__.index("(c)")].strip() # Web Adjuster vN.NN
    if options.machineName: serverName = viaName + " on "+options.machineName
    else: serverName = viaName
    serverName_html = re.sub(r"([0-9])([0-9])",r"\1<span></span>\2",serverName) # stop mobile browsers interpreting the version number as a telephone number
    global upstream_proxy_host, upstream_proxy_port
    upstream_proxy_host = upstream_proxy_port = None
    global upstream_rewrite_ssl ; upstream_rewrite_ssl=False
    global cores ; cores = 1
    if options.multicore:
        options.squashLogs = False
        if not 'linux' in sys.platform and not 'bsd' in sys.platform:
            errExit("multicore option not supported on this platform")
            # --- it does work on darwin (Mac), but as of 10.7 some incoming connections get 'lost' so it's not a good idea
        cores = options.num_cores
        if not cores:
            import tornado.process
            cores = tornado.process.cpu_count()
        if cores==1: options.multicore = False
        elif options.js_interpreter and options.js_instances % cores:
            old = options.js_instances
            options.js_instances += (cores - (options.js_instances % cores))
            sys.stderr.write("multicore: changing js_instances %d -> %d (%d per core x %d cores)\n" % (old,options.js_instances,int(options.js_instances/cores),cores))
    if options.js_interpreter in ["HeadlessChrome","Chrome"]:
        try: # check inotify limit (Linux only)
            maxI=int(open("/proc/sys/fs/inotify/max_user_instances").read())
        except: maxI = -1
        if not maxI==-1 and options.js_instances > maxI*20: warn("This system might run out of inotify instances with that number of Chrome processes.  Try:\nsudo sysctl -n -w fs.inotify.max_user_watches=%d\nsudo sysctl -n -w fs.inotify.max_user_instances=%d" % (options.js_instances*40,options.js_instances*20))
    global js_per_core
    js_per_core = int(options.js_instances/cores)
    if options.upstream_proxy:
        maxCurls = 30*js_per_core
        if options.ssl_fork: maxCurls = int(maxCurls/2)
        if not options.usepycurl: errExit("upstream_proxy is not compatible with --usepycurl=False")
        setupCurl(maxCurls,"upstream_proxy requires pycurl (try sudo pip install pycurl)")
        if not ':' in options.upstream_proxy: options.upstream_proxy += ":80"
        upstream_proxy_host,upstream_proxy_port = options.upstream_proxy.split(':') # TODO: IPv6 ?
        if not upstream_proxy_host:
            upstream_proxy_host = "127.0.0.1"
            if wsgi_mode: warn("Can't do SSL/TLS-rewrite for upstream proxy when in WSGI mode")
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
    global port_randomise
    if options.fixed_ports:
        class NullDict(dict):
            def __setitem__(*args): pass
        port_randomise = NullDict()
    if options.port == -1:
        if wsgi_mode:
            warn("port=-1 won't work in WSGI mode, assuming 80")
            options.port = 80
        elif options.ssl_fork or options.background: errExit("Can't run in background or ssl-fork with an ephemeral main port, as that requires fork-before-listen so won't be able to report the allocated port number")
        elif options.fixed_ports: errExit("fixed_ports is not compatible with port==-1")
        else:
            port_randomise[options.port] = True
            if not options.internalPort:
                # DON'T set it to -1 + 1 = 0
                options.internalPort = 1024
    elif options.port < 0 or options.port > 65535:
        errExit("port out of range")
    elif not options.port:
        if wsgi_mode:
            warn("port=0 won't work in WSGI mode, assuming 80")
            options.port = 80
        else:
            options.real_proxy=options.js_reproxy=False ; options.fasterServer=""
            options.open_proxy = True # bypass the check
    if not options.publicPort:
        options.publicPort = options.port
    if not options.internalPort:
        options.internalPort = options.port + 1
    if options.internalPort in [options.publicPort,options.port]: errExit("--internalPort cannot match --port or --publicPort")
    if options.just_me:
        options.address = "localhost"
        try: socket.socket().connect(('localhost',113))
        except:
            if not 'linux' in sys.platform or not getoutput("which netstat 2>/dev/null"): errExit("--just_me requires either an ident server to be running on port 113, or the system to be Linux with a netstat command available")
        import getpass ; global myUsername ; myUsername = S(getpass.getuser())
    elif not options.password and not options.open_proxy and not options.submitPath=='/' and not options.stop: errExit("Please set a password (or --just_me), or use --open_proxy.\n(Try --help for help; did you forget a --config=file?)") # (as a special case, if submitPath=/ then we're serving nothing but submit-your-own-text and bookmarklets, which means we won't be proxying anything anyway and don't need this check)
    if options.submitBookmarkletDomain and not options.publicPort==80: warn("You will need to run another copy on "+options.submitBookmarkletDomain+" ports 80/443 for bookmarklets to work (submitBookmarkletDomain without publicPort=80)")
    if options.pdftotext and not "pdftotext version" in getoutput("pdftotext -h"): errExit("pdftotext command does not seem to be usable\nPlease install it, or unset the pdftotext option")
    if options.epubtotext and not "calibre" in getoutput("ebook-convert -h"): errExit("ebook-convert command does not seem to be usable\nPlease install calibre, or unset the epubtotext option")
    global extensions
    if options.extensions:
        extensions = __import__(options.extensions)
    else:
        class E:
            def handle(*args): return False
        extensions = E()
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
        if options.default_site:
            errExit("Cannot set default_site when headAppendCSS contains options, because we need the URL box to show those options")
            # TODO: unless we implement some kind of inline setting, or special options URL ?
        if options.cssHtmlAttrs and ';' in options.cssHtmlAttrs and not len(options.cssHtmlAttrs.split(';'))==len(h.rsplit(';',1)[1].split(',')): errExit("Number of choices in headAppendCSS last field does not match number of choices in cssHtmlAttrs")
        for n in range(len(h.split(';'))-1):
            upstreamGuard.add("adjustCss"+str(n)+"s")
            cRecogniseAny.add("adjustCss"+str(n)+"s")
    if options.useLXML: check_LXML()
    if not options.default_site: options.default_site = ""
    # (so we can .split it even if it's None or something)
    if not options.js_interpreter:
        options.js_reproxy=options.js_frames=False
    elif not options.htmlonly_mode: errExit("js_interpreter requires htmlonly_mode")
    if options.alt_dot:
        global altdot_bad_cookie_leak
        altdot_bad_cookie_leak = options.alt_dot.startswith("*")
        if altdot_bad_cookie_leak:
            options.alt_dot = options.alt_dot[1:]

def intor0(x):
    try: return int(x)
    except: return 0

def check_injected_globals():
    # for making sure we're used correctly when imported
    # as a module by a wrapper script
    try: defined_globals
    except: return
    for s in set(globals().keys()).difference(defined_globals):
        if s in options: errExit("Error: adjuster.%s should be adjuster.options.%s" % (s,s)) # (tell them off, don't try to patch up: this could go more subtly wrong if they do it again with something we happened to have defined in our module before)
        elif type(eval(s)) in [str,bool,int]: errExit("Don't understand injected %s %s (misspelled option?)" % (repr(type(eval(s))),s))
def setup_defined_globals(): # see above
    global defined_globals
    defined_globals = True # so included in itself
    defined_globals = set(globals().keys())

#@file: log-multi.py
# --------------------------------------------------
# Logging and busy-signalling (especially multicore)
# --------------------------------------------------

class CrossProcessLogging(logging.Handler):
    def needed(self): return (options.multicore or options.ssl_fork or (options.js_interpreter and options.js_multiprocess)) and options.log_file_prefix # (not needed if stderr-only or if won't fork)
    def init(self):
        "Called by initLogging before forks.  Starts the separate logListener process."
        if not self.needed(): return
        try: logging.getLogger().handlers
        except:
            # Ouch, we won't know how to clear logging's handlers and start again in the child processes
            errExit("The logging module on this system is not suitable for --log-file-prefix with --ssl-fork or --js-multiprocess")
        if not multiprocessing: return # we'll have to open multiple files in initChild instead
        self.loggingQ=multiprocessing.Queue()
        def logListener():
          try:
            while True: logging.getLogger().handle(logging.makeLogRecord(self.loggingQ.get()))
          except KeyboardInterrupt: pass
        self.p = multiprocessing.Process(target=logListener) ; self.p.start()
        logging.getLogger().handlers = [] # clear what Tornado has already put in place when it read the configuration
        logging.getLogger().addHandler(self)
    def initChild(self,toAppend=""):
        "Called after a fork.  toAppend helps to describe the child for logfile naming when multiprocessing is not available."
        if not options.log_file_prefix: return # stderr is OK
        if multiprocessing:
            try: multiprocessing.process.current_process()._children.clear() # multiprocessing wasn't really designed for the parent to fork() later on
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
    def emit(self, record): # simplified from Python 3.2 (but put just the dictionary, not the record obj itself, to make pickling errors less likely)
        try:
            if record.exc_info:
                placeholder = self.format(record) # record.exc_text
                record.exc_info = None
            d = record.__dict__
            d['msg'],d['args'] = record.getMessage(),None
            self.loggingQ.put(d)
        except (KeyboardInterrupt, SystemExit): raise
        except: self.handleError(record)

class CrossProcess429:
    def needed(self): return options.multicore and options.js_429
    def init(self): self.q = multiprocessing.Queue()
    def startThread(self):
        if not self.needed(): return
        self.b = [False]*cores
        def listener():
            allServersBusy = False
            while True:
                coreToSet, busyStatus = self.q.get()
                if coreToSet=="quit": break
                self.b[coreToSet] = busyStatus
                newASB = all(self.b)
                if not newASB == allServersBusy:
                    allServersBusy = newASB
                    if allServersBusy: IOLoopInstance().add_callback(lambda *args:reallyPauseOrRestartMainServer(True)) # run it just to serve the 429s, but don't set mainServerPaused=False or add an event to the queue
                    else: IOLoopInstance().add_callback(lambda *args:reallyPauseOrRestartMainServer("IfNotPaused")) # stop it if and only if it hasn't been restarted by the main thread before this callback
        threading.Thread(target=listener,args=()).start()

def initLogging(): # MUST be after unixfork() if background
    try:
        import logging, tornado.log
        class NoSSLWarnings:
            def filter(self,record): return not (record.levelno==logging.WARNING and record.getMessage().startswith("SSL"))
        tornado.log.gen_log.addFilter(NoSSLWarnings()) # Tornado 6
    except: pass
    global CrossProcessLogging
    CrossProcessLogging = CrossProcessLogging()
    CrossProcessLogging.init()

def init429():
    global CrossProcess429
    CrossProcess429 = CrossProcess429()
    if CrossProcess429.needed(): CrossProcess429.init()
def shutdown429():
    try: CrossProcess429.q.put(("quit","quit"))
    except: pass

#@file: log-browser.py
# --------------------------------------------------
# browser logging
# --------------------------------------------------

helper_threads = []

class NullLogger:
  def __call__(self,req): pass
class BrowserLogger:
  def __init__(self):
    # Do NOT read options here - they haven't been read yet
    self.lastBrowser = None
    self.lastIp = self.lastMethodStuff = None
  def __call__(self,req):
    if req.request.remote_ip in options.ipNoLog: return
    try: ch = req.cookie_host()
    except: ch = None # shouldn't happen
    req=req.request
    if hasattr(req,"suppress_logging"): return
    if S(req.method) not in the_supported_methods and not options.logUnsupported: return
    if S(req.method)=="CONNECT" or re.match(B("https?://"),B(req.uri)): host="" # URI will have everything
    elif hasattr(req,"suppress_logger_host_convert"): host = req.host
    else: host=B(convert_to_real_host(req.host,ch))
    if host in [-1,B("error")]: host=req.host
    elif host: host=protocolWithHost(host)
    else: host=""
    browser = req.headers.get("User-Agent",None)
    if browser:
        browser=B('"')+B(browser)+B('"')
        if options.squashLogs and browser==self.lastBrowser: browser = ""
        else:
            self.lastBrowser = browser
            browser=B(" ")+B(browser)
    else: self.lastBrowser,browser = None," -"
    if options.squashLogs:
        # Date (as YYMMDD) and time are already be included in Tornado logging format, a format we don't want to override, especially as it has 'start of log string syntax highlighting' on some platforms
        if req.remote_ip == self.lastIp:
            ip=""
        else:
            self.lastIp = req.remote_ip
            ip=B(req.remote_ip)+B(" ")
            self.lastMethodStuff = None # always log method/version anew when IP is different
        methodStuff = (req.method, req.version)
        if methodStuff == self.lastMethodStuff:
            r=host+S(req.uri)
        else:
            r='"%s %s%s %s"' % (S(req.method), host, S(req.uri), S(req.version))
            self.lastMethodStuff = methodStuff
        msg = S(ip)+S(r)+S(browser)
    else: msg = '%s "%s %s%s %s" %s' % (S(req.remote_ip), S(req.method), host, S(req.uri), S(req.version), S(browser)) # could add "- - [%s]" with time.strftime("%d/%b/%Y:%X") if don't like Tornado-logs date-time format (and - - - before the browser %s)
    logging.info(msg.replace('\x1b','[ESC]')) # make sure we are terminal safe, in case of malformed URLs

def initLogging_preListen():
    global nullLog, accessLog
    nullLog = NullLogger()
    accessLog = BrowserLogger()

#@file: profile.py
# --------------------------------------------------
# Profiling and process naming
# --------------------------------------------------

profile_forks_too = False # TODO: configurable
def open_profile():
    if options.profile:
        global cProfile,pstats,profileIdle
        import cProfile, pstats
        setProfile() ; profileIdle = False
        global reqsInFlight,origReqInFlight
        reqsInFlight = set() ; origReqInFlight = set()
def open_profile_pjsOnly(): # TODO: combine with above
    if options.profile:
        global profileIdle
        setProfile_pjsOnly() ; profileIdle = False
        global reqsInFlight,origReqInFlight
        reqsInFlight = set() ; origReqInFlight = set()
def setProfile():
    global theProfiler, profileIdle
    theProfiler = cProfile.Profile()
    IOLoopInstance().add_timeout(time.time()+options.profile,lambda *args:pollProfile())
    profileIdle = True ; theProfiler.enable()
def setProfile_pjsOnly():
    IOLoopInstance().add_timeout(time.time()+options.profile,lambda *args:pollProfile_pjsOnly())
    global profileIdle ; profileIdle = True
def pollProfile():
    theProfiler.disable()
    if not profileIdle: showProfile()
    setProfile()
def pollProfile_pjsOnly():
    if not profileIdle: showProfile(pjsOnly=True)
    setProfile_pjsOnly()
def showProfile(pjsOnly=False):
    global _doneShowProfile
    try: _doneShowProfile
    except: _doneShowProfile = False
    if pjsOnly: pr = ""
    else:
        s = StringIO()
        pstats.Stats(theProfiler,stream=s).sort_stats('cumulative').print_stats()
        pr = "\n".join([x for x in s.getvalue().split("\n") if x and not "Ordered by" in x][:options.profile_lines])
    if options.js_interpreter and len(webdriver_runner):
        global webdriver_lambda,webdriver_mu,webdriver_maxBusy
        stillUsed = sum(1 for i in webdriver_runner if i.wd_threadStart)
        maybeStuck = set()
        for i in webdriver_runner:
            ms,tr = i.maybe_stuck,i.wd_threadStart
            if ms and ms == tr and tr+30 < time.time():
                maybeStuck.add(ms)
            i.maybe_stuck = tr
        webdriver_maxBusy = max(webdriver_maxBusy,stillUsed)
        if pr: pr += "\n"
        elif not options.background: pr += ": "
        pr += "js_interpreter"
        if options.multicore: pr += "%d" % (int(webdriver_runner[0].start/js_per_core),)
        pr += " "
        if not webdriver_maxBusy: pr += "idle"
        else:
            try: # NameError unless js_429 and multicore
                if mainServerPaused: pr += "closed, "
                else: pr += "open, "
            except NameError: pass
            served = "%d served" % webdriver_mu
            if webdriver_lambda==webdriver_mu==len(webdriver_queue)==0: queue = "" # "; queue unused"
            elif not webdriver_queue: queue="; queue empty: "+served
            else: queue = "; queue %d: %d arrived, %s" % (len(webdriver_queue),webdriver_lambda,served)
            if not _doneShowProfile:
                if pjsOnly: stuck = ", next SIGUSR2 checks stuck;"
                else: stuck = ";"
            elif maybeStuck:
                stuck = ", %d stuck for " % len(maybeStuck)
                t = time.time()
                s1=int(t-max(maybeStuck)); s2=int(t-min(maybeStuck))
                if s1==s2: stuck += str(s1)
                else: stuck += "%d-%d" % (s1,s2)
                stuck += "s?"
            else: stuck = ";" # or ", none stuck"
            pr += "%d/%d busy%s " % (stillUsed,len(webdriver_runner),stuck)
            if not webdriver_maxBusy == stillUsed:
                pr += "maxUse=%d" % (webdriver_maxBusy,)
            pr += queue
            pr = pr.rstrip().replace("; ;",";")
            if pr.endswith(";"): pr = pr[:-1]
        webdriver_lambda = webdriver_mu = 0
        webdriver_maxBusy = stillUsed
        # TODO: also measure lambda/mu of other threads e.g. htmlFilter ?
        if psutil and not webdriver_runner[0].start: pr += "; system RAM %.1f%% used" % (psutil.virtual_memory().percent)
    try: pr2 += "%d requests in flight (%d from clients)" % (len(reqsInFlight),len(origReqInFlight))
    except NameError: pr2="" # no reqsInFlight
    _doneShowProfile = True
    if not pr and not pr2: return
    if pr: pr += "\n"
    elif not options.background: pr += ": "
    pr += pr2
    if options.background: logging.info(pr)
    elif can_do_ansi_colour: sys.stderr.write("\033[35m"+(time.strftime("%X")+pr).replace("\n","\n\033[35m")+"\033[0m\n")
    else: sys.stderr.write(time.strftime("%X")+pr+"\n")

def setProcName(name="adjuster"):
    "Try to set the process name for top/ps"
    try: # setproctitle works on both Linux and BSD/Mac if installed (but doesn't affect Mac OS 10.7 "Activity Monitor")
        import setproctitle # sudo pip install setproctitle or apt-get install python-setproctitle (requires gcc)
        return setproctitle.setproctitle(name) # TODO: this also stops 'ps axwww' from displaying command-line arguments; make it optional?
    except: pass
    try: # ditto but non-Mac BSD not checked (and doesn't always work on Python 3) :
        import procname # sudo pip install procname (requires gcc)
        return procname.setprocname(name)
    except: pass
    try: # this works in GNU/Linux for 'top', 'pstree -p' and 'killall', but not 'ps' or 'pidof' (which need argv[0] to be changed in C) :
        import ctypes ; name = B(name)
        b = ctypes.create_string_buffer(len(name)+1)
        b.value = name
        ctypes.cdll.LoadLibrary('libc.so.6').prctl(15,ctypes.byref(b),0,0,0)
    except: pass # oh well

#@file: server-control.py
# --------------------------------------------------
# Start / stop / install
# --------------------------------------------------

def serverControl():
    if options.install:
        current_crontab = getoutput("crontab -l 2>/dev/null")
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

def stopOther():
    pid = triedStop = None
    if options.pidfile:
        try: pid = int(open(options.pidfile).read().strip())
        except: pass
        if not pid==None:
            if not psutil or psutil.pid_exists(pid):
                tryStop(pid,True) # tryStop will rm pidfile if had permission to send the stop signal
                triedStop = pid
            else: unlink(options.pidfile) # stale
        if not options.port: return
    elif not options.port:
        # Oops: the listening port is used to identify the other process; without it, we don't know which process to stop
        errExit("Cannot use --restart or --stop with --port=0 and no --pidfile")
    pids = run_lsof()
    if pids==False: # no lsof, or couldn't make sense of it
        # Could try "fuser -n tcp "+str(options.port), but it can be slow on a busy system.  Try netstat instead.
        pids = run_netstat()
        if pids==False:
            if not options.pidfile: sys.stderr.write("stopOther: can't find understandable 'lsof' or 'netstat' commands on this system\n")
            return False
    try: pids.remove(os.getpid())
    except: pass
    for pid in pids:
        if not pid==triedStop:
            tryStop(pid)
    return triedStop or pids
def tryStop(pid,alsoRemovePidfile=False):
    if options.stop: other="the"
    else: other="other"
    try:
        os.kill(pid,signal.SIGTERM)
        if alsoRemovePidfile: unlink(options.pidfile)
        sys.stderr.write("Stopped %s process at PID %d\n" % (other,pid))
    except: sys.stderr.write("Failed to stop %s process at PID %d\n" % (other,pid))
def run_lsof():
    # TODO: check ssl-fork ports as well as main port ? (also in run_netstat)
    out = getoutput("lsof -iTCP:"+str(options.port)+" -sTCP:LISTEN 2>/dev/null") # Redirect lsof's stderr to /dev/null because it sometimes prints warnings, e.g. if something's wrong with Mac FUSE mounts, that won't affect the output we want. TODO: lsof can hang if ANY programs have files open on stuck remote mounts etc, even if this is nothing to do with TCP connections.  -S 2 might help a BIT but it's not a solution.  Linux's netstat -tlp needs root, and BSD's can't show PIDs.  Might be better to write files or set something in the process name.
    if out.startswith("lsof: unsupported"):
        # lsof 4.81 has -sTCP:LISTEN but lsof 4.78 does not.  However, not including -sTCP:LISTEN can cause lsof to make unnecessary hostname queries for established connections.  So fall back only if have to.
        out = getoutput("lsof -iTCP:"+str(options.port)+" -Ts 2>/dev/null") # lsof -Ts ensures will say LISTEN on the pid that's listening
        lines = filter(lambda x:"LISTEN" in x,out.split("\n")[1:])
    elif not out.strip() and not getoutput("which lsof 2>/dev/null"): return False
    else: lines = out.split("\n")[1:]
    pids = set()
    for line in lines:
        try: pids.add(int(line.split()[1]))
        except:
            if not pids:
                # sys.stderr.write("stopOther: Can't make sense of lsof output %s\n" % repr(line))
                return False # lsof not working, use something else
            break
    return pids
def run_netstat():
    if not 'linux' in sys.platform or not getoutput("which netstat 2>/dev/null"): return False
    pids = set()
    for l in getoutput("netstat -tnlp").split("\n"):
        if ':'+str(options.port)+' ' in l:
            ps = l.split()[-1]
            if '/' in ps:
                pids.add(int(ps[:ps.index('/')]))
    return pids

#@file: ssl-multiprocess.py
# --------------------------------------------------
# Support for SSL termination in separate processes
# --------------------------------------------------

sslforks_to_monitor = [] # list of [pid,callback1,callback2,port]
sslfork_monitor_pid = None
def sslSetup(HelperStarter, ping_portNo, isFixed=False):
    if options.ssl_fork: # queue it to be started by monitor
        if options.multicore and sslforks_to_monitor: sslforks_to_monitor[0][1] = (lambda c1=HelperStarter,c2=sslforks_to_monitor[0][1]:(c1(),c2())) # chain it, as in multicore mode we'll have {N cores} * {single process handling all SSL ports}, rather than cores * processes (TODO: if one gets stuck but others on the port can still handle requests, do we want to somehow detect the individual stuck one and restart it to reduce wasted CPU load?)
        else:
            # no multicore, or this is the first SSL helper, so we need to associate it with a (non-SSL) ping responder
            sslforks_to_monitor.append([None,HelperStarter,(lambda *_:listen_on_port(Application([(r"(.*)",AliveResponder,{})],log_function=nullLog),ping_portNo,"127.0.0.1",False)),ping_portNo])
            return ping_portNo + 1 # where to put the next listener
    else: # just run it on the current process, and we can randomise the internal port and keep track of what it is
        if not isFixed: port_randomise[ping_portNo-1] = True
        HelperStarter()
    return ping_portNo # next listener can use what would have been the ping-responder port as we're not using it
sslFork_pingInterval = 10 # TODO: configurable?  (if setting this larger, might want to track the helper threads for early termination)
def maybe_sslfork_monitor():
    "Returns SIGTERM callback if we're now a child process"
    global sslforks_to_monitor
    if not sslforks_to_monitor: return
    global sslfork_monitor_pid
    pid = os.fork()
    if pid:
        sslfork_monitor_pid = pid ; return
    # If background, can't double-fork (our PID is known)
    # (TODO: if profile_forks_too, there's no profile loop in this monitor (it starts only when we fork a new helper); unlikely to be useful here though)
    try: os.setpgrp() # for stop_threads0 later
    except: pass
    signal.signal(signal.SIGTERM, terminateSslForks)
    signal.signal(signal.SIGINT, terminateSslForks)
    setProcName("adjusterSSLmon")
    # (15 chars is max for some "top" implementations)
    CrossProcessLogging.initChild("SSL")
    # (not SSLmon because helper IDs will be appended to it)
    global is_sslHelp ; is_sslHelp = True
    for i in xrange(len(sslforks_to_monitor)):
      if i==len(sslforks_to_monitor)-1: pid = 0 # don't bother to fork for the last one
      else: pid = os.fork()
      if pid: sslforks_to_monitor[i][0] = pid # for SIGTERM
      else: # child
        oldI = i
        if i < len(sslforks_to_monitor)-1:
            sslforks_to_monitor = [sslforks_to_monitor[i]]
            i = 0 # we'll monitor only one in the child
        # don't use IOLoop for this monitoring: too confusing if we have to restart it on fork
        try: urlopen = build_opener(ProxyHandler({})).open # don't use the system proxy if set
        except: pass # leave urlopen as default if above not supported
        while True:
            try: urlopen(("http://localhost:%d/" % sslforks_to_monitor[i][3]),timeout=sslFork_pingInterval)
            except: # URLError etc
              if restart_sslfork(i,oldI): # child
                  return lambda *args:stopServer("SIG*")
              else: time.sleep(sslFork_pingInterval) # double it after a restart
            time.sleep(sslFork_pingInterval)
def restart_sslfork(n,oldN):
    global sslforks_to_monitor
    if not sslforks_to_monitor[n][0]==None: # not first time
        if options.multicore: oldN = "s"
        else: oldN = " "+str(oldN)
        logging.error("Restarting SSL helper%s via pid %d as not heard from port %d" % (oldN,sslforks_to_monitor[n][0],sslforks_to_monitor[n][3]))
        emergency_zap_pid_and_children(sslforks_to_monitor[n][0]) # may have children if multicore
    # TODO: if profile_forks_too, do things with profile?
    pid = os.fork()
    if pid: sslforks_to_monitor[n][0] = pid
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
    for p,_,_,_ in sslforks_to_monitor:
        if p==None: continue
        try: os.kill(p,signal.SIGTERM)
        except OSError: pass # somebody might have 'killall'd them
        try: os.waitpid(p, os.WNOHANG)
        except OSError: pass
    stop_threads0()

class AliveResponder(RequestHandler):
    SUPPORTED_METHODS = ("GET",)
    def get(self, *args, **kwargs): self.write("1")

#@file: port-listen.py
# --------------------------------------------------
# Port listening - main, SSL-termination and JS-upstream
# --------------------------------------------------

def open_extra_ports():
    "Returns the stop function if we're now a child process that shouldn't run anything else"
    nextPort = options.internalPort
    # don't add any other ports here: NormalRequestForwarder assumes the real_proxy SSL helper will be at internalPort
    # All calls to sslSetup and maybe_sslfork_monitor must be made before ANY other calls to listen_on_port (as we don't yet want there to be an IOLoop instance when maybe_sslfork_monitor is called)
    if options.real_proxy: nextPort = sslSetup(lambda port=nextPort:listen_on_port(Application([(r"(.*)",SSLRequestForwarder(),{})],log_function=accessLog,gzip=False),port,"127.0.0.1",False,ssl_options={"certfile":duff_certfile()}),nextPort+1) # A modified Application that's 'aware' it's the SSL-helper version (use SSLRequestForwarder & no need for staticDocs listener) - this will respond to SSL requests that have been CONNECT'd via the first port.  We set gzip=False because little point if we know the final client is on localhost.
    if options.js_reproxy:
        # ditto for js_interpreter (saves having to override its user-agent, or add custom headers requiring PhantomJS 1.5+, for us to detect its connections back to us)
        global js_proxy_port
        js_proxy_port = []
        for c in xrange(cores):
          for i in xrange(js_per_core):
            # PjsRequestForwarder to be done later
            js_proxy_port.append(nextPort)
            nextPort = sslSetup(lambda port=nextPort,cc=c,ii=i : listen_on_port(Application([(r"(.*)",PjsSslRequestForwarder(cc*js_per_core,ii),{})],log_function=nullLog,gzip=False),port+1,"127.0.0.1",False,ssl_options={"certfile":duff_certfile()}),nextPort+2)
    if upstream_rewrite_ssl:
        # This one does NOT listen on SSL: it listens on unencrypted HTTP and rewrites .0 into outgoing SSL.  But we can still run it in a different process if ssl_fork is enabled, and this will save encountering the curl_max_clients issue as well as possibly offloading *client*-side SSL to a different CPU core (TODO: could also use Tornado's multiprocessing to multi-core the client-side SSL)
        sslSetup(lambda port=upstream_proxy_port+1:listen_on_port(Application([(r"(.*)",UpSslRequestForwarder,{})],log_function=nullLog,gzip=False),port,"127.0.0.1",False),upstream_proxy_port+2,True) # TODO: document upstream_proxy_port+2 needs to be reserved if options.ssl_fork and not options.upstream_proxy_host
    r = maybe_sslfork_monitor()
    if r: return r
    # NOW we can start non-sslSetup listen_on_port:
    if options.js_reproxy:
        for c in xrange(cores):
          for i in xrange(js_per_core):
            if options.ssl_fork: pass # do NOT port_randomise, because maybe_sslfork_monitor is called ABOVE and the fork will NOT have a copy of our updated port_randomise map for its forwardToOtherPid call
            else: port_randomise[js_proxy_port[c*js_per_core+i]]=True
            listen_on_port(makePjsApplication(c*js_per_core,i),js_proxy_port[c*js_per_core+i],"127.0.0.1",False,core=c)

def makeMainApplication():
    handlers = [(r"(.*)",NormalRequestForwarder(),{})]
    if options.staticDocs: handlers.insert(0,static_handler())
    return Application(handlers,log_function=accessLog,gzip=options.compress_responses) # TODO: gzip= deprecated in Tornado 4.x (if they remove it, we may have to check Tornado version and send either gzip= or compress_response= as appropriate, in all calls to Application)

def makePjsApplication(x,y):
    handlers = [(r"(.*)",PjsRequestForwarder(x,y),{})]
    if options.js_upstream and options.staticDocs: handlers.insert(0,static_handler())
    return Application(handlers,log_function=nullLog,gzip=False)

def start_multicore(isSSLEtcChild=False):
    "Fork child processes, set coreNo unless isSSLEtcChild; parent waits and exits.  Call to this must come after unixfork if want to run in the background."
    global coreNo
    if not options.multicore:
        if not isSSLEtcChild: coreNo = 0
        return
    # Simplified version of Tornado fork_processes with
    # added setupRunAndBrowser (must have the terminal)
    children = set()
    for i in range(cores):
        pid = os.fork()
        if not pid: # child
            if not isSSLEtcChild: coreNo = i
            return CrossProcessLogging.initChild()
        children.add(pid)
    if not isSSLEtcChild:
        # Do the equivalent of setupRunAndBrowser() but without the IOLoop.  This can start threads, so must be after the above fork() calls.
        if options.browser: runBrowser()
        if options.run: runRun()
    # Now wait for the browser or the children to exit
    # (and monitor for SIGTERM: we might be an SSLhelp)
    def handleTerm(*_):
        global interruptReason
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
    if children:
        try: reason = interruptReason # from handleTerm
        except: reason = "keyboard interrupt"
        reason = "Adjuster multicore handler: "+reason+", stopping "+str(len(children))+" child processes"
        if options.background: logging.info(reason)
        else: sys.stderr.write("\n"+reason+"\n")
    for pid in children: os.kill(pid,signal.SIGTERM)
    while children:
        try: pid, status = os.wait()
        except KeyboardInterrupt: logging.error("KeyboardInterrupt received while waiting for child-processes to terminate: "+" ".join(str(s) for s in children))
        except: continue
        if pid in children: children.remove(pid)
    if not isSSLEtcChild: announceShutdown0()
    stop_threads() # must be last thing, except
    raise SystemExit # (in case weren't any threads to stop)

def openPortsEtc():
    workaround_raspbian7_IPv6_bug()
    workaround_timeWait_problem()
    early_fork = (options.ssl_fork and options.background)
    if early_fork: banner(True),unixfork()
    if options.ssl_fork: initLogging() # even if not early_fork (i.e. not background)
    stopFunc = open_extra_ports()
    if stopFunc: # we're a child process (--ssl-fork)
        assert not options.background or early_fork
        # can't double-fork (our PID is known), hence early_fork above
        start_multicore(True) ; schedule_retries()
        if profile_forks_too: open_profile()
    else: # we're not a child process of --ssl-fork
      try:
        if options.port: listen_on_port(makeMainApplication(),options.port,options.address,options.browser)
        open_upnp() # make sure package avail if needed
        if not early_fork: banner()
        if options.background and not early_fork:
            if options.js_interpreter: test_init_webdriver()
            unixfork() # MUST be before init_webdrivers (js_interpreter does NOT work if you start them before forking)
        if not options.ssl_fork: initLogging() # as we hadn't done it before (must be after unixfork)
        init429()
        if not options.background: notifyReady()
        start_multicore() # if multicore, returns iff we're one of the cores
        if not options.multicore or profile_forks_too: open_profile()
        else: open_profile_pjsOnly()
        if options.js_interpreter: init_webdrivers(coreNo*js_per_core,js_per_core)
        if not options.multicore: setupRunAndBrowser() # (equivalent is done by start_multicore if multicore)
        checkServer.setup() # (TODO: if we're multicore, can we propagate to other processes ourselves instead of having each core check the fasterServer?  Low priority because how often will a multicore box need a fasterServer)
        if not coreNo:
            CrossProcess429.startThread()
            Dynamic_DNS_updater()
            if options.pimote: pimote_thread() # must be on same core as Dynamic_DNS_updater so it can set pimote_may_need_override
        if options.multicore: stopFunc = lambda *_:stopServer("SIG*")
        else: stopFunc = lambda *_:stopServer("SIGTERM received")
        if options.seconds: IOLoopInstance().add_timeout(time.time()+options.seconds,lambda *args:stopServer("Uptime limit reached"))
        if options.stdio and not coreNo: setup_stdio()
      except SystemExit: raise
      except: # oops, error during startup, stop forks if any
        if not sslfork_monitor_pid == None:
          time.sleep(0.5) # (it may have only just started: give it a chance to install its signal handler)
          try: os.kill(sslfork_monitor_pid,signal.SIGTERM)
          except OSError: pass
        raise
    signal.signal(signal.SIGTERM, stopFunc)
    try: os.setpgrp() # for stop_threads0 later
    except: pass

def setup_stdio():
    # Handle option for request on standard input
    # (when used in one-off mode)
    global StdinPass,StdinPending
    StdinPass,StdinPending = None,[]
    def doStdin(fd,events):
        l=os.read(fd,1024) # read 1 line or 1024 bytes (TODO: double-check this can never block)
        if not l: # EOF (but don't close stdout yet)
            IOLoopInstance().remove_handler(sys.stdin.fileno())
            return
        global StdinPass
        if StdinPending: StdinPending.append(l) # connection is still being established
        elif StdinPass: StdinPass.write(l) # open
        else: # not yet established
            StdinPending.append(l)
            StdinPass = tornado.iostream.IOStream(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0))
            def ClearPending(): del StdinPending[:]
            def WriteOut(s):
                try: sys.stdout.buffer.write(s)
                except: sys.stdout.write(s)
            doCallback(None,StdinPass.connect,lambda *args:(StdinPass.write(B('').join(StdinPending)),ClearPending(),readUntilClose(StdinPass,lambda last:(WriteOut(last),sys.stdout.close()),WriteOut)),(options.address, port_randomise.get(options.port,options.port)))
    IOLoopInstance().add_handler(sys.stdin.fileno(), doStdin, IOLoop.READ)

#@file: up-down.py
# --------------------------------------------------
# General startup and shutdown tasks
# --------------------------------------------------

def banner(delayed=False):
    ret = [twoline_program_name]
    if options.port:
        if options.port==-1:
            ret.append("Listening on 127.0.0.1:%d" % port_randomise[-1])
            if not istty(sys.stdout) and options.background: sys.stdout.write("127.0.0.1:%d" % port_randomise[-1]),sys.stdout.flush()
        else: ret.append("Listening on port %d" % options.port)
        if upstream_rewrite_ssl: ret.append("--upstream-proxy back-connection helper is listening on 127.0.0.1:%d" % (upstream_proxy_port+1,))
        if options.stdio: ret.append("Listening on standard input")
    else: ret.append("Not listening (--port=0 set)")
    if options.ssl_fork and not options.background: ret.append("To inspect processes, use: pstree "+str(os.getpid()))
    ret = "\n".join(ret)+"\n"
    if delayed: ret=ret.replace("Listening","Will listen").replace("Writing","Will write") # for --ssl-fork --background, need early fork (TODO: unless write a PID somewhere)
    sys.stderr.write(ret),sys.stderr.flush()
    if not options.background:
        # set window title for foreground running
        t = "adjuster"
        if "SSH_CONNECTION" in os.environ: t += "@"+hostSuffix() # TODO: might want to use socket.getfqdn() to save confusion if several servers are configured with the same host_suffix and/or host_suffix specifies multiple hosts?
        set_title(t)

def istty(f=sys.stderr): return hasattr(f,"isatty") and f.isatty()
def set_title(t):
  if not istty(): return
  term = os.environ.get("TERM","")
  is_xterm = "xterm" in term
  is_screen = (term=="screen" and os.environ.get("STY",""))
  is_tmux = (term=="screen" and os.environ.get("TMUX",""))
  if is_xterm or is_tmux:
      sys.stderr.write("\033]0;%s\007" % (t,)),sys.stderr.flush()
      # ("0;" sets both title and minimised title, "1;" sets minimised title, "2;" sets title.  Tmux takes its pane title from title (but doesn't display it in the titlebar))
  elif is_screen: os.system("screen -X title \"%s\"" % (t,))
  else: return
  if not t: return
  import atexit
  atexit.register(set_title,"")
  global can_do_ansi_colour
  can_do_ansi_colour = is_xterm or (is_screen and "VT 100/ANSI" in os.environ.get("TERMCAP",""))
  # can_do_ansi_colour is used by showProfile (TODO: if profile_forks_too, we'd need to set this earlier than the call to banner / set_title in order to make it available to SSL forks etc, otherwise only the main one has purple profile output. Multicore is already OK (but does only counts per core).)
can_do_ansi_colour=False

coreNo = "unknown" # want it to be non-False to begin with
def announceInterrupt():
    if coreNo or options.multicore: return # we are a silent helper process (coreNo=="unknown"), or we announce interrupts differently in multicore (see start_multicore), so nothing to do here
    if options.background: logging.info("SIGINT received"+find_adjuster_in_traceback())
    else: sys.stderr.write("\nKeyboard interrupt"+find_adjuster_in_traceback()+"\n")
def announceShutdown():
    if coreNo or options.multicore: return # silent helper process (coreNo=="unknown"), or we announce interrupts differently in multicore (see start_multicore)
    announceShutdown0()
def announceShutdown0():
    global exitting ; exitting = True # so not restarted if options.runWait == 0 and the run process was given the same signal (it can be confusing if get a restart message from the other thread AFTER shutdown has been announced)
    if options.background:
        logging.info("Server shutdown")
        if options.pidfile: unlink(options.pidfile)
    else: sys.stderr.write("Adjuster shutdown\n")

def main():
    check_injected_globals()
    setProcName() ; readOptions() ; preprocessOptions()
    serverControl() ; openPortsEtc() ; startServers()
    try: IOLoopInstance().start()
# "There seemed a strangeness in the air,
#  Vermilion light on the land's lean face;
#  I heard a Voice from I knew not where:
#   'The Great Adjustment is taking place!'" - Thomas Hardy
    except KeyboardInterrupt: announceInterrupt()
    announceShutdown()
    options.pimote = "" # so pimote_thread stops
    for v in kept_tempfiles.values(): unlink(v)
    stop_threads() # must be last thing

def plural(number): return "" if number==1 else "s"
def stop_threads():
    shutdown429()
    if quitFuncToCall: quitFuncToCall()
    if not sslfork_monitor_pid == None:
        try: os.kill(sslfork_monitor_pid,signal.SIGTERM) # this should cause it to propagate that signal to the monitored PIDs
        except OSError: pass # somebody might have killall'd it
    CrossProcessLogging.shutdown()
    writeMsg = not options.background and not coreNo
    for t in range(10): # wait for helper_threads first (especially if quitFuncToCall above, as if the terminate routine is too forceful it might prevent the EOF from being sent over the pipe (multiprocessing.Pipe has no flush method after we send the EOF, so quitFuncToCall's returning does NOT mean the eof has actually been sent) and we could get a stuck adjusterWDhelp process)
      if t: time.sleep(0.2)
      if not helper_threads:
        if t: sys.stderr.write("Helper threads have stopped\n")
        return
      if not t and writeMsg: sys.stderr.write("Waiting 2secs for helper threads to stop...\n")
    ht = [(i,1) for i in sorted(helper_threads)]
    i = 0
    while i < len(ht)-1:
        if ht[i][0] == ht[i+1][0]:
            ht[i] = (ht[i][0], ht[i][1]+1)
            del ht[i+1]
        else: i += 1
    for i in xrange(len(ht)):
        if ht[i][1]==1: ht[i] = ht[i][0]
        else: ht[i] = ht[i][0]+"*"+str(ht[i][1])
    msg = "Terminating %d helper thread%s (%s)" % (len(ht),plural(len(ht)),", ".join(ht))
    # in case someone needs our port quickly.
    # Most likely "runaway" thread is ip_change_command if you did a --restart shortly after the server started.
    # TODO it would be nice if the port can be released at the IOLoop.instance.stop, so that it's not necessary to stop the threads
    if writeMsg: sys.stderr.write(msg+"\n")
    stop_threads0()
def stop_threads0():
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    if options.run:
        try: os.kill(runningPid,signal.SIGTERM)
        except NameError: pass # runningPid not set
        except OSError: pass # already exitted
    os.killpg(os.getpgrp(),signal.SIGTERM)
    os.abort() # if the above didn't work, this should

#@file: tornado-setup.py
# --------------------------------------------------
# Basic Tornado-server setup
# --------------------------------------------------

def static_handler():
    url,path = options.staticDocs.split('#')
    if not url.startswith("/"): url="/"+url
    if not url.endswith("/"): url += "/"
    class OurStaticFileHandler(StaticFileHandler):
        def set_extra_headers(self,path): fixServerHeader(self)
    return (url+"(.*)",OurStaticFileHandler,{"path":path,"default_filename":"index.html"})

theServers = {}
port_randomise = {} # port -> _ or port -> mappedPort
def listen_on_port(application,port,address,browser,core="all",**kwargs):
    # Don't set backlog=0: it's advisory only and is often rounded up to 8; we use CrossProcess429 instead
    if port in port_randomise:
        s = bind_sockets(0,"127.0.0.1")
        # should get len(s)==1 if address=="127.0.0.1" (may get more than one socket, with different ports, if address maps to some mixed IPv4/IPv6 configuration)
        port_randomise[port] = s[0].getsockname()[1]
    else:
     for portTry in [5,4,3,2,1,0]:
      try: s = bind_sockets(port,address)
      except socket.error as e:
        if is_sslHelp:
            # We had better not time.sleep() here trying
            # to open, especially not if multicore: don't
            # want to hold up the OTHER ports being opened
            # and get into an infinite-restart loop when
            # MOST services are already running:
            f = lambda *_:IOLoopInstance().add_timeout(time.time()+1,lambda *args:listen_on_port(application,port,address,browser,core,schedRetry,**kwargs))
            if is_sslHelp=="started": f()
            else: sslRetries.append(f)
            logging.info("Can't open port "+repr(port)+", retry scheduled")
            return
        if not "already in use" in e.strerror: raise
        # Maybe the previous server is taking a while to stop
        if portTry:
            time.sleep(0.5) ; continue
        # tried 6 times over 3 seconds, can't open the port
        if browser:
            # there's probably another adjuster instance, in which case we probably want to let the browser open a new window and let our listen() fail
            runBrowser()
        raise Exception("Can't open port "+repr(port)+" (tried for 3 seconds, "+e.strerror+")")
    i = len(theServers.setdefault(core,[])) ; c = core
    class ServerStarter: # don't construct HTTPServer before fork
        def start(self):
            h = HTTPServer(application,**kwargs)
            h.add_sockets(s)
            if port==options.port:
                global mainServer ; mainServer = h
            theServers[c][i]=(port,h) ; h.start()
    theServers[core].append((port,ServerStarter()))
is_sslHelp = False ; sslRetries = []
def schedule_retries():
    global is_sslHelp,sslRetries
    is_sslHelp = "started"
    for s in sslRetries: s()
    sslRetries = []

def IOLoopInstance():
    global ioLoopInstance
    try: return ioLoopInstance
    except: # better call this from the main thread first:
        if hasattr(IOLoop,"current"): ioLoopInstance = IOLoop.current() # for Tornado 5+ to work
        else: ioLoopInstance = IOLoop.instance() # in Tornado 4 and older, this can be called on-demand from any thread, but we're putting it in a global for forward-compatibility with the above
        return ioLoopInstance

def startServers():
    workaround_tornado_fd_issue()
    for core,sList in list(theServers.items()):
        if core == "all" or core == coreNo:
            for port,s in sList: s.start()

#@file: overload.py
# --------------------------------------------------
# Multicore: pause/restart when a core is overloaded
# --------------------------------------------------

mainServerPaused = mainServerReallyPaused = False
def pauseOrRestartMainServer(shouldRun=True):
    if not (options.multicore and options.js_429): return
    global mainServerPaused
    if (not shouldRun) == mainServerPaused: return
    # if shouldRun: return # uncomment this 'once closed, stay closed' line to demonstrate the OS forwards to open cores only
    reallyPauseOrRestartMainServer(shouldRun)
    mainServerPaused = not mainServerPaused
    debuglog("Paused=%s on core %s" % (repr(mainServerPaused),repr(coreNo)))
    CrossProcess429.q.put((coreNo,mainServerPaused))
def reallyPauseOrRestartMainServer(shouldRun):
    global mainServerReallyPaused
    if shouldRun == "IfNotPaused": # called by CrossProcess429 to re-pause if and only if hasn't been reopened by the outer level in the meantime
        shouldRun = mainServerPaused
    if (not shouldRun) == mainServerReallyPaused: return
    for core,sList in theServers.items():
        if not (core == "all" or core == coreNo): continue
        for port,s in sList:
            if not port==options.port: continue
            if not hasattr(s,"_sockets"):
                logging.error("Cannot pause server: wrong Tornado version?")
                return
            if shouldRun: s.add_sockets(s._sockets.values())
            else:
                for fd, sock in s._sockets.items():
                    if hasattr(s,"io_loop"): s.io_loop.remove_handler(fd) # Tornado 4
                    else: IOLoopInstance().remove_handler(fd) # Tornado 5, not tested (TODO)
    mainServerReallyPaused = not mainServerReallyPaused
    debuglog("reallyPaused=%s on core %s" % (repr(mainServerReallyPaused),repr(coreNo)))

#@file: workarounds.py
# --------------------------------------------------
# Miscellaneous bug workarounds
# --------------------------------------------------

def workaround_raspbian7_IPv6_bug():
    """Old Debian 7 based versions of Raspbian can boot with IPv6 enabled but later fail to configure it, hence tornado/netutil.py's AI_ADDRCONFIG flag is ineffective and socket.socket raises "Address family not supported by protocol" when it tries to listen on IPv6.  If that happens, we'll need to set address="0.0.0.0" for IPv4 only.  However, if we tried IPv6 and got the error, then at that point Tornado's bind_sockets will likely have ALREADY bound an IPv4 socket but not returned it; the socket does NOT get closed on dealloc, so a retry would get "Address already in use" unless we quit and re-run the application (or somehow try to figure out the socket number so it can be closed).  Instead of that, let's try to detect the situation in advance so we can set options.address to IPv4-only the first time."""
    if options.address: return # don't need to do this if we're listening on a specific address
    flags = socket.AI_PASSIVE
    if hasattr(socket, "AI_ADDRCONFIG"): flags |= socket.AI_ADDRCONFIG
    for af,socktype,proto,r1,r2 in socket.getaddrinfo(None,options.port,socket.AF_UNSPEC,socket.SOCK_STREAM,0,flags):
        try: socket.socket(af,socktype,proto)
        except socket.error as e:
            if "family not supported" in e.strerror:
                options.address = "0.0.0.0" # use IPv4 only
                return

def workaround_timeWait_problem():
    """Work around listen-port failing to bind when there are still TIME_WAIT connections from the previous run.  This at least seems to work around the problem MOST of the time."""
    global bind_sockets
    bind_sockets = tornado.netutil.bind_sockets
    if "win" in sys.platform and not sys.platform=="darwin":
        # Don't do this on MS-Windows.  It can result in
        # 'stealing' a port from another server even while
        # that other server is still running.
        return
    if not hasattr(socket, "SO_REUSEPORT"): return
    if getargspec==None: return
    if not 'reuse_port' in getargspec(tornado.netutil.bind_sockets).args: return # Tornado version too old
    def bind_sockets(*args,**kwargs):
        if not args[0]: pass # wer're doing port_randomise
        elif len(args) < 6: kwargs['reuse_port'] = True
        else: args=tuple(args[:6])+(True,)
        return tornado.netutil.bind_sockets(*args,**kwargs)

def workaround_tornado_fd_issue(): # TODO: is this still needed post-v0.3 now we fixed start-order bug?
    if not hasattr(IOLoopInstance(),'handle_callback_exception'):
        return # Tornado 6 doesn't have this, let's hope it's not needed
    cxFunc = IOLoopInstance().handle_callback_exception
    def newCx(callback):
        if callback: return cxFunc(callback)
        # self._handlers[fd] raised KeyError.  This means
        # we don't want to keep being told about the fd.
        fr = sys.exc_info()[2]
        while fr.tb_next: fr = fr.tb_next
        fd = fr.tb_frame.f_locals.get("fd",None)
        if not fd: return cxFunc("callback="+repr(callback)+" and newCx couldn't get fd from stack")
        logging.info("IOLoop has no handler left for fd "+repr(fd)+" but is still getting events from it.  Attempting low-level close to avoid loop.")
        try: IOLoopInstance().remove_handler(fd)
        except: pass
        try: os.close(fd)
        except: pass
    IOLoopInstance().handle_callback_exception = newCx

def check_LXML():
    # Might not find ALL problems with lxml installations, but at least we can check some basics
    global etree
    try:
        from lxml import etree
        return etree.HTMLParser(target=None) # works on lxml 2.3.2
    except ImportError: sys.stderr.write("LXML library not found - ignoring useLXML option\n")
    except TypeError: sys.stderr.write("LXML library too old - ignoring useLXML option\n") # no target= option in 1.x
    options.useLXML = False

#@file: unix.py
# --------------------------------------------------
# More setup: Unix forking etc
# --------------------------------------------------

def unixfork():
    if os.fork(): sys.exit()
    os.setsid()
    if os.fork(): sys.exit()
    devnull = os.open("/dev/null", os.O_RDWR)
    for fd in range(3): os.dup2(devnull,fd) # commenting out this loop will let you see stderr after the fork (TODO debug option?)
    if options.pidfile:
        try: open(options.pidfile,"w").write(str(os.getpid()))
        except: pass

def notifyReady():
    try: import sdnotify # sudo pip install sdnotify
    except ImportError: return
    sdnotify.SystemdNotifier().notify("READY=1") # we send READY=1 so you can do an adjuster.service (w/out --background) with Type=notify and ExecStart=/usr/bin/python /path/to/adjuster.py --config=...

#@file: curl-setup.py
# --------------------------------------------------
# cURL client setup
# --------------------------------------------------

def MyAsyncHTTPClient(): return AsyncHTTPClient()
def curlFinished(): pass
def setupCurl(maxCurls,error=None):
  global pycurl
  try:
    import pycurl # check it's there
    curl_async = pycurl.version_info()[4] & (1 << 7) # CURL_VERSION_ASYNCHDNS
    if not curl_async: curl_async = ('c-ares' in pycurl.version or 'threaded' in pycurl.version) # older
    if not curl_async:
        if error: warn("The libcurl on this system might hold up our main thread while it resolves DNS (try building curl with ./configure --enable-ares)")
        else:
            del pycurl ; return # TODO: and say 'not using'?
    if float('.'.join(pycurl.version.split()[0].split('/')[1].rsplit('.')[:2])) < 7.5:
        if error: warn("The curl on this system is old and might hang when fetching certain SSL sites") # strace -p (myPID) shows busy looping on poll (TODO: option to not use it if we're not using upstream_proxy)
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
    curl_max_clients = min(max(maxCurls,10),1000) # constrain curl_max_clients to between 10 and 1000 to work around Tornado issue 2127, and we'll warn about the issue ourselves if we go over:
    curl_inUse_clients = 0
    try: AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient",max_clients=curl_max_clients)
    except: AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient") # will try in MyAsyncHTTPClient too (different versions of Tornado and all that...) (TODO: if that one also falls back to no max_clients, we might be reduced to 10 and should set curl_max_clients accordingly in order to get appropriate warning messages)
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

#@file: message-user.py
# --------------------------------------------------
# Support for showing messages to specific IP addresses
# --------------------------------------------------

try:
    import hashlib # Python 2.5+, platforms?
    hashlib.md5
except: hashlib = None # (TODO: does this ever happen on a platform that supports Tornado?  Cygwin has hashlib with md5)
if hashlib: cookieHash = lambda msg: base64.b64encode(hashlib.md5(B(msg)).digest())[:10]
else: cookieHash = lambda msg: hex(hash(msg))[2:] # this fallback is not portable across different Python versions etc, so no good if you're running a fasterServer

ipv4_regexp = re.compile(r'^([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)$')
def ipv4_to_int(ip):
    m = re.match(ipv4_regexp,S(ip))
    if m: return (int(m.group(1))<<24) | (int(m.group(2))<<16) | (int(m.group(3))<<8) | int(m.group(4))
    else: return None
def ipv4range_to_ints(ip):
    ip = S(ip)
    if '-' in ip: return tuple(ipv4_to_int(i) for i in ip.split('-'))
    elif '/' in ip:
        start,bits = ip.split('/')
        start = ipv4_to_int(start)
        return start, start | ~(-1 << (32-int(bits)))
    else: return ipv4_to_int(ip),ipv4_to_int(ip)
def ipv4ranges_func(ipRanges_and_results):
    isIP = True ; rangeList=None ; fList = []
    for field in S(ipRanges_and_results).split('|'):
        if isIP: rangeList = [ipv4range_to_ints(i) for i in field.split(',')]
        else: fList.append((rangeList,field))
        isIP = not isIP
    def f(ip):
        ipInt = ipv4_to_int(ip)
        for rl,result in fList:
            if any((l<=ipInt<=h) for l,h in rl):
                return result # else None
    return f

#@file: connect-ssl.py
# --------------------------------------------------
# Service routines for CONNECT passing to SSL terminator
# --------------------------------------------------

debug_connections = False
def myRepr(d):
    if re.search(B("[\x00-\x09\x0e-\x1f]"),B(d)): return "%d bytes" % len(d)
    elif len(d) >= 512: return repr(d[:500]+"...")
    else: return repr(d)
def peerName(socket):
    try: return socket.getpeername()
    except: return "(no socket??)"
def writeAndClose(stream,data):
    if data:
        if debug_connections: print ("Writing "+myRepr(data)+" to "+peerName(stream.socket)+" and closing it")
        try: stream.write(data,lambda *args:True)
        except: pass # ignore errors like client disconnected
    if not stream.closed():
        try: stream.close()
        except: pass
def writeOrError(opposite,name,stream,data):
    if debug_connections: print ("Writing "+myRepr(data)+" to "+peerName(stream.socket))
    try: stream.write(data)
    except:
        if name and not hasattr(stream,"writeOrError_already_complained"): logging.error("Error writing data to "+name)
        stream.writeOrError_already_complained = True
        try: stream.close()
        except: pass
        try: opposite.close() # (try to close the server stream we're reading if the client has gone away, and vice versa)
        except: pass

#@file: misc.py
# --------------------------------------------------
# Miscellaneous variables
# --------------------------------------------------

cookieExpires = "Tue Jan 19 03:14:07 2038" # TODO: S2G (may have to switch to Max-Age and drop support for ~IE8)

set_window_onerror = False # for debugging Javascript on some mobile browsers (TODO make this a config option? but will have to check which browsers do and don't support window.onerror)

# Domain-setting cookie for when we have no wildcard_dns and no default_site:
adjust_domain_cookieName = "_adjusterDN_"

adjust_domain_none = B("0") # not a valid top-level domain (TODO hopefully no user wants this as a local domain...)

enable_adjustDomainCookieName_URL_override = True # TODO: document this!  (Allow &_adjusterDN_=0 or &_adjusterDN_=wherever in bookmark URLs, so it doesn't matter what setting the cookie has when the bookmark is activated)

seen_ipMessage_cookieName = "_adjusterIPM_"

htmlmode_cookie_name = "_adjustZJCG_" # zap JS, CSS and Graphics

password_cookie_name = "_pxyAxsP_" # "proxy access password". have to pick something that's unlikely to collide with a site's cookie

webdriver_click_code = "._adjustPJSC_"

redirectFiles_Extensions=set("pdf epub mp3 aac zip gif png jpeg jpg exe tar tgz tbz ttf woff swf txt doc rtf midi mid wav ly c h py".split()) # TODO: make this list configurable + maybe add a "minimum content length before it's worth re-directing" option

#@file: js-webdriver.py
# --------------------------------------------------
# Server-side Javascript execution support
# --------------------------------------------------

class WebdriverWrapper:
    "Wrapper for webdriver that might or might not be in a separate process without shared memory"
    def __init__(self): self.theWebDriver = self.tmpDirToDelete = None
    def new(self,*args):
        try:
            # No coredump, for emergency_zap_pid_and_children
            import resource ; resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        except: pass # oh well, have coredumps then :-(
        if options.js_multiprocess:
            # we have a whole process to ourselves (not just a thread)
            # so we can set the environment here.
            # Selenium doesn't always clean up temporary files on exit
            # (especially with Firefox), so let's set TMPDIR uniquely so we
            # can clean them ourselves.
            tmp = os.environ.get("TMPDIR",None)
            self.tempDirToDelete=os.environ['TMPDIR']=os.environ.get("TMPDIR","/tmp")+"/"+str(os.getpid())+"."+str(args[0])
            try: os.mkdir(self.tempDirToDelete)
            except: pass
        else: tmp = self.tempDirToDelete = None
        self.theWebDriver = get_new_webdriver(*args)
        if tmp: os.environ["TMPDIR"] = tmp
        elif options.js_multiprocess: del os.environ["TMPDIR"]
    def getTmp(self,*args): return self.tempDirToDelete
    def quit(self,*args):
        if not self.theWebDriver: return
        try: pid = self.theWebDriver.service.process.pid
        except: pid = debuglog("WebdriverWrapper: Unable to get self.theWebDriver.service.process.pid")
        try: self.theWebDriver.quit()
        except: debuglog("WebdriverWrapper: exception on quit") # e.g. sometimes get 'bad fd' in selenium's send_remote_shutdown_command _cookie_temp_file_handle
        # Try zapping the process ourselves anyway (even if theWebDriver.quit DIDN'T return error: seems it's sometimes still left around.  TODO: this could have unexpected consequences if the system's pid-reuse rate is excessively high.)
        self.theWebDriver = None
        emergency_zap_pid_and_children(pid)
        if self.tempDirToDelete: shutil.rmtree(self.tempDirToDelete,True)
    def current_url(self):
        try: return self.theWebDriver.current_url
        except: return "" # PhantomJS Issue #13114: unconditional reload for now
    def get(self,url):
        self.theWebDriver.get(S(url))
        if options.logDebug:
          try:
            for e in self.theWebDriver.get_log('browser'):
                print ("webdriver log: "+e['message'])
          except Exception as e: print ("webdriver get_log exception: "+repr(e))
    def execute_script(self,script): self.theWebDriver.execute_script(S(script))
    def click_id(self,clickElementID): self.theWebDriver.find_element_by_id(S(clickElementID)).click()
    def click_xpath(self,xpath): self.theWebDriver.find_element_by_xpath(S(xpath)).click()
    def click_linkText(self,clickLinkText): self.theWebDriver.find_element_by_link_text(S(clickLinkText)).click()
    def getu8(self):
        def f(switchBack):
            src = self.theWebDriver.find_element_by_xpath("//*").get_attribute("outerHTML")
            if options.js_frames:
                for el in ['frame','iframe']:
                    for frame in self.theWebDriver.find_elements_by_tag_name(el):
                        self.theWebDriver.switch_to.frame(frame)
                        src += f(switchBack+[frame])
                        self.theWebDriver.switch_to.default_content()
                        for fr in switchBack: self.theWebDriver.switch_to.frame(fr)
            return src
        return B(f([]))
    def getpng(self):
        if options.js_interpreter=="HeadlessChrome": # resize not needed for PhantomJS (but PhantomJS is worse at font configuration and is no longer maintained)
            self.theWebDriver.set_window_size(js_size[0],min(16000,intor0(self.theWebDriver.execute_script("return document.body.parentNode.scrollHeight")))) # TODO: check the 16000: what is Selenium's limit? (confirmed over 8000)
            time.sleep(1)
        png = self.theWebDriver.get_screenshot_as_png()
        if options.js_interpreter=="HeadlessChrome": self.theWebDriver.set_window_size(*js_size)
        try: # can we optimise the screenshot image size?
            from PIL import Image
            s = BytesIO() ; Image.open(StringIO(png)).save(s,'png',optimize=True)
            png = s.getvalue()
        except: pass # just return non-optimized
        return png
def getWebdriverWrapper():
    if options.js_interpreter=="edbrowse": return EdbrowseWrapper()
    else: return WebdriverWrapper()
class EdbrowseWrapper:
    "Experimental wrapper for edbrowse that behaves like WebdriverWrapper"
    def __init__(self): self.tDir,self.url,self.out = None,"about:blank",b""
    def new(self,index,*args): self.tDir,self.edEnv = setup_edbrowse(index)
    def getTmp(self,*args): return self.tDir
    def quit(self,*args):
        if self.tDir: shutil.rmtree(self.tDir,True)
    def current_url(self): return self.url
    def get(self,url):
        self.url = url
        out = subprocess.Popen(["edbrowse","-e"],-1,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=self.edEnv).communicate(b"b %s\njdb\ndocument.documentElement.outerHTML\n" % B(url))[0]
        try: self.out = re.search(b"\\.browse\n(.*)EOF\\s*$",out,flags=re.DOTALL).group(1)
        except: self.out = "Error: "+repr(out)
    def execute_script(self,script): return "0" # typically used to get window dimensions etc, not needed for edbrowse
    def click_id(self,clickElementID): pass # shouldn't be called if js_links off
    def click_xpath(self,xpath): pass
    def click_linkText(self,clickLinkText): pass
    def getu8(self): return self.out
    def getpng(self): return b"" # screenshots don't make sense on edbrowse
def check_edbrowse():
    tDir,edEnv = setup_edbrowse()
    try: out,err = subprocess.Popen(["edbrowse","-v"],-1,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=edEnv).communicate(b"")
    except OSError: errExit("Could not run edbrowse")
    shutil.rmtree(tDir)
    try: a,b,c = S(out).split('.')
    except: errExit("Could not parse format of edbrowse version number "+repr(out))
    if (intor0(a),intor0(b),intor0(c)) < (3,7,5): errExit("edbrowse too old: at least 3.7.5 is required")
def setup_edbrowse(index=None):
    tDir = getoutput("(TMPDIR=/dev/shm mktemp -d -t ed || mktemp -d -t ed) 2>/dev/null")
    edEnv=os.environ.copy()
    edEnv["TMPDIR"]=edEnv["HOME"]=tDir
    ebrc = "downdir="+tDir+"\n"
    ebrc += "jar="+tDir+os.sep+"cookies\n"
    ebrc += "cachedir="+tDir+"\ncachesize=0\n" # (dir might not be needed if size=0)
    if options.js_UA and not options.js_UA.startswith("*"): ebrc += "agent="+options.js_UA+"\n"
    if options.js_reproxy and not index==None: ebrc += "proxy=* * 127.0.0.1:%d\n" % proxyPort(index)
    elif options.upstream_proxy: ebrc += "proxy=* * "+options.upstream_proxy+"\n"
    open(tDir+os.sep+".ebrc","w").write(ebrc)
    return tDir,edEnv
def emergency_zap_pid_and_children(pid):
    if not pid: return
    try:
      for c in psutil.Process(pid).children(recursive=True):
        try: c.kill(9)
        except: pass
    except: pass # no psutil, or process already gone
    try: os.kill(pid,9),os.waitpid(pid, 0) # waitpid is necessary to clear it from the process table, but we should NOT use os.WNOHANG, as if we do, there's a race condition with the os.kill taking effect (even -9 isn't instant)
    except OSError: pass # maybe pid already gone
try: from selenium.common.exceptions import TimeoutException
except: # no Selenium or wrong version
    class TimeoutException(Exception): pass # placeholder
class SeriousTimeoutException(Exception): pass
def webdriverWrapper_receiver(pipe,timeoutLock):
    "Command receiver for WebdriverWrapper for when it's running over IPC (--js-multiprocess).  Receives (command,args) and sends (return,exception), releasing the timeoutLock whenever it's ready to return."
    setProcName("adjusterWDhelp")
    CrossProcessLogging.initChild()
    try: w = getWebdriverWrapper()
    except KeyboardInterrupt: return
    while True:
        try: cmd,args = pipe.recv()
        except KeyboardInterrupt: # all shutting down
            try: w.quit()
            except: pass
            try: timeoutLock.release()
            except ValueError: pass
            pipe.send(("INT","INT"))
            return pipe.close()
        if cmd=="EOF": return pipe.close()
        try: ret,exc = getattr(w,cmd)(*args), None
        except Exception as e:
            p = find_adjuster_in_traceback()
            if p: # see if we can add it to the message (note p will start with ", " so no need to add a space before it)
              try:
                  if hasattr(e,"msg") and e.msg: e.msg += p # should work with WebDriverException
                  elif type(e.args[0])==str: e.args=(repr(e.args[0])+p,) + tuple(e.args[1:]) # should work with things like httplib.BadStatusLine that are fussy about the number of arguments they get
                  else: e.args += (p,) # works with things like KeyError (although so should the above)
              except: e.message += p # works with base Exception
            ret,exc = None,e
        try: timeoutLock.release()
        except: pass # (may fail if controller's timeoutLock is turned off during quit_wd_atexit)
        try: pipe.send((ret,exc))
        except: pass # if they closed it, we'll get EOFError on next iteration
class WebdriverWrapperController:
    "Proxy for WebdriverWrapper if it's running over IPC"
    def __init__(self):
        self.pipe, cPipe = multiprocessing.Pipe()
        self.timeoutLock = multiprocessing.Lock()
        self.process = multiprocessing.Process(target=webdriverWrapper_receiver,args=(cPipe,self.timeoutLock))
        self.process.start()
    def send(self,cmd,args=()):
        "Send a command to a WebdriverWrapper over IPC, and either return its result or raise its exception in this process.  Also handle the raising of SeriousTimeoutException if needed, in which case the WebdriverWrapper should be stopped."
        try:
          if not self.timeoutLock.acquire(timeout=0):
            logging.error("REALLY serious SeriousTimeout (should never happen). Lock unavailable before sending command.")
            raise SeriousTimeoutException()
        except AttributeError: pass # self.timeoutLock==None because quit(final=True) called from another thread
        try: self.pipe.send((cmd,args))
        except IOError: return # already closed
        if cmd=="EOF":
            return self.pipe.close() # no return code
        try:
            if not self.timeoutLock.acquire(timeout=options.js_timeout2): # fallback in case Selenium timeout doesn't catch it (signal.alarm in the child process isn't guaranteed to help, so catch it here)
                try: logging.error("SeriousTimeout: WebdriverWrapper process took over "+str(options.js_timeout2)+"s to respond to "+repr((cmd,args))+". Emergency restarting this process.")
                except: pass # absolutely do not throw anything except SeriousTimeoutException from this branch
                raise SeriousTimeoutException()
            self.timeoutLock.release()
        except AttributeError: return # self.timeoutLock==None because quit(final=True) called from another thread
        ret,exc = self.pipe.recv()
        if ret==exc=="INT": return self.pipe.close()
        if exc: raise exc
        else: return ret
    def new(self,*args):
        self.send("new",args)
        self.tempDirToDelete=self.send("getTmp")
    def quit(self,final=False):
        if final: self.timeoutLock = None # quit_wd_atexit could plausibly run while another thread's still processing its last command, so allow these commands to be queued in the pipe from another thread without worrying about timeout when that happens
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
try:
    os.fork # exception if e.g. Windows
    import multiprocessing # Python 2.6
    if hasattr(multiprocessing,'set_start_method'): multiprocessing.set_start_method('fork')
except: multiprocessing = None
class WebdriverRunner:
    "Manage a WebdriverWrapperController (or a WebdriverWrapper if we're not using IPC) from a thread of the main process"
    def __init__(self,start=0,index=0):
        self.start,self.index = start,index
        if options.js_multiprocess:
            self.wrapper = WebdriverWrapperController()
        else: self.wrapper = getWebdriverWrapper()
        self.renew_webdriver_newThread(True) # sets wd_threadStart
    def renew_controller(self): # SeriousTimeoutException
        emergency_zap_pid_and_children(self.wrapper.process.pid)
        shutil.rmtree(self.wrapper.tempDirToDelete,True)
        self.wrapper = WebdriverWrapperController()
    def renew_webdriver_sameThread(self,firstTime=False):
        self.usageCount = 0 ; self.maybe_stuck = False
        while True:
          try:
              self.wrapper.quit(),self.wrapper.new(self.start+self.index,not firstTime)
              break
          except SeriousTimeoutException: # already logged
              self.renew_controller()
          except:
              logging.error("Exception "+exc_logStr()+" while renewing webdriver, retrying")
              time.sleep(1) # just in case
        self.usageCount = 0 ; self.maybe_stuck = False
    def renew_webdriver_newThread(self,firstTime=False):
        self.wd_threadStart = time.time() # cleared in _renew_wd after renew_webdriver_sameThread returns (it loops on exception)
        threading.Thread(target=_renew_wd,args=(self,firstTime)).start() ; return
    def quit_webdriver(self): self.wrapper.quit(final=True)
    def fetch(self,url,prefetched,clickElementID,clickLinkText,asScreenshot,callback,tooLate):
        assert not self.wd_threadStart # webdriver_checkServe
        self.wd_threadStart = time.time() # cleared in wd_fetch after _wd_fetch returns or throws + possible renew-loop (TODO: if wd_fetch ITSELF somehow throws an exception, should be logged but this JS instance gets tied up until next adjuster restart)
        self.maybe_stuck = False
        threading.Thread(target=wd_fetch,args=(url,prefetched,clickElementID,clickLinkText,asScreenshot,callback,self,tooLate)).start()
    def current_url(self): return self.wrapper.current_url()
    def get(self,url): return self.wrapper.get(url)
    def execute_script(self,script): self.wrapper.execute_script(script)
    def click_id(self,clickElementID): self.wrapper.click_id(clickElementID)
    def click_xpath(self,xpath): self.wrapper.click_xpath(xpath)
    def click_linkText(self,clickLinkText): self.wrapper.click_linkText(clickLinkText)
    def getu8(self): return self.wrapper.getu8()
    def getpng(self): return self.wrapper.getpng()
def _renew_wd(wd,firstTime):
    wd.renew_webdriver_sameThread(firstTime)
    wd.wd_threadStart = False
    IOLoopInstance().add_callback(webdriver_checkServe)
def find_adjuster_in_traceback():
    ei = sys.exc_info()
    try:
        p = ei[1].args[-1]
        if "adjuster line" in p: return p # for webdriverWrapper_receiver
    except: pass
    try: __file__
    except: return "" # sometimes not defined ??
    l = traceback.extract_tb(ei[2])
    for i in xrange(len(l)-1,-1,-1):
        if __file__ in l[i][0]: return ", adjuster line "+str(l[i][1])
    return ""
def wd_fetch(url,prefetched,clickElementID,clickLinkText,asScreenshot,callback,manager,tooLate):
    url = S(url)
    helper_threads.append('wd_fetch')
    need_restart = False
    def errHandle(error,extraMsg,prefetched):
        if not options.js_fallback: prefetched=None
        if prefetched: toRet = "non-webdriver page (js_fallback set)"
        else:
            toRet = "error"
            prefetched = wrapResponse("webdriver "+error)
        logging.error(extraMsg+" returning "+toRet)
        if options.js_fallback:
            try:
                prefetched.headers.add(options.js_fallback,error)
            except: logging.error("Could not add "+repr(options.js_fallback)+" to error response")
        return prefetched
    try:
        r = _wd_fetch(manager,url,prefetched,clickElementID,clickLinkText,asScreenshot)
        try:
            if options.js_fallback: r.headers.add(options.js_fallback,"OK")
        except: pass
    except TimeoutException:
        r = errHandle("timeout","webdriver "+str(manager.start+manager.index)+" timeout fetching "+url+find_adjuster_in_traceback()+"; no partial result, so",prefetched) # "webdriver timeout" sent to browser (can't include url here: domain gets rewritten)
    except SeriousTimeoutException:
        r = errHandle("serious timeout","lost communication with webdriver "+str(manager.start+manager.index)+" when fetching "+url+"; no partial result, so",prefetched)
        need_restart = "serious"
    except:
        if options.js_retry and not tooLate():
            logging.info("webdriver error fetching "+url+" ("+exc_logStr()+"); restarting webdriver "+str(manager.start+manager.index)+" for retry") # usually a BadStatusLine
            manager.renew_webdriver_sameThread()
            if tooLate(): r = errHandle("err","too late")
            else:
              try:
                  r = _wd_fetch(manager,url,prefetched,clickElementID,clickLinkText,asScreenshot)
                  try:
                      if options.js_fallback: r.headers.add(options.js_fallback,"OK")
                  except: pass
              except SeriousTimeoutException:
                r = errHandle("serious timeout","webdriver serious timeout on "+url+" after restart, so re-restarting and",prefetched)
                need_restart = "serious"
              except:
                r = errHandle("error","webdriver error on "+url+" even after restart, so re-restarting and",prefetched)
                need_restart = True
        else: # no retry
            r = errHandle("error","webdriver error on "+url+", so restarting and",prefetched)
            need_restart = True
    IOLoopInstance().add_callback(lambda *args:callback(r))
    manager.usageCount += 1
    if need_restart or (options.js_restartAfter and manager.usageCount >= options.js_restartAfter):
        if need_restart=="serious":manager.renew_controller()
        manager.renew_webdriver_sameThread()
    else: manager.finishTime = time.time()
    manager.wd_threadStart = manager.maybe_stuck = False
    IOLoopInstance().add_callback(webdriver_checkServe)
    helper_threads.remove('wd_fetch')
def exc_logStr():
    toLog = sys.exc_info()[:2]
    if hasattr(toLog[1],"msg") and toLog[1].msg: toLog=(toLog[0],toLog[1].msg) # for WebDriverException
    return repr(toLog)+find_adjuster_in_traceback()
def _wd_fetch(manager,url,prefetched,clickElementID,clickLinkText,asScreenshot): # single-user only! (and relies on being called only in htmlOnlyMode so leftover Javascript is removed and doesn't double-execute on JS-enabled browsers)
    import tornado.httputil ; url = S(url)
    currentUrl = S(manager.current_url())
    timed_out = False
    if prefetched or not re.sub('#.*','',currentUrl) == url:
        if prefetched:
            debuglog("webdriver %d get about:blank" % (manager.start+manager.index))
            manager.get("about:blank") # ensure no race condition with current page's XMLHttpRequests
            webdriver_prefetched[manager.index] = prefetched
        webdriver_inProgress[manager.index].clear() # race condition with start of next 'get' if we haven't done about:blank, but worst case is we'll wait a bit too long for page to finish
        debuglog(("webdriver %d get " % (manager.start+manager.index))+url)
        try: manager.get(url) # waits for onload
        except TimeoutException:
            # we might have got SOMEthing (e.g. on a page bringing in hundreds of scripts from a slow server, but still running some of them before the timeout)
            # May also be "Received error page"
            if currentUrl == S(manager.current_url()):
                debuglog(("webdriver %d get() timeout " % (manager.start+manager.index))+url+" - URL unchanged at "+currentUrl)
                raise # treat as "no partial result"
            debuglog(("webdriver %d get() timeout " % (manager.start+manager.index))+url+" - extracting partial")
        if not timed_out:
         debuglog(("webdriver %d loaded " % (manager.start+manager.index))+url)
         # we want to double-check XMLHttpRequests have gone through (TODO: low-value setTimeout as well? TODO: abort this early if currentUrl has changed and we're just going to issue a redirect? but would then need to ensure it's finished if client comes back to same instance that's still running after it follows the redirect)
         if options.js_reproxy:
          wasActive = True
          for _ in xrange(40): # up to 8+ seconds in steps of 0.2 (on top of the inital load)
            time.sleep(0.2) # unconditional first-wait hopefully long enough to catch XMLHttpRequest delayed-send, very-low-value setTimeout etc, but we don't want to wait a whole second if the page isn't GOING to make any requests (TODO: monitor the js going through the upstream proxy to see if it contains any calls to this? but we'll have to deal with js_interpreter's cache, unless set it to not cache and we cache upstream)
            active = webdriver_inProgress[manager.index]
            if not active and not wasActive: break # TODO: wait longer than 0.2-0.4 to see if it restarts another request?
            wasActive = active
         else: time.sleep(1) # can't do much if we're not reproxying, so just sleep 1sec and hope for the best
        currentUrl = None
    if (clickElementID or clickLinkText) and not timed_out:
      try:
        manager.execute_script("window.open = window.confirm = function(){return true;}") # in case any link has a "Do you really want to follow this link?" confirmation (webdriver default is usually Cancel), or has 'pop-under' window (TODO: switch to pop-up?)
        if clickElementID: manager.click_id(clickElementID)
        if clickLinkText:
            if not type(clickLinkText)==type(u""): clickLinkText=clickLinkText.decode('utf-8')
            if not '"' in clickLinkText: manager.click_xpath(u'//a[text()="'+clickLinkText+'"]')
            elif not "'" in clickLinkText: manager.click_xpath(u"//a[text()='"+clickLinkText+"']")
            else: manager.click_linkText(clickLinkText) # least reliable
        time.sleep(0.2) # TODO: more? what if the click results in fetching a new URL, had we better wait for XMLHttpRequests to finish?  (loop as above but how do we know when they've started?)  currentUrl code below should at least show us the new URL even if it hasn't finished loading, and then there's a delay while the client browser is told to fetch it, but that might not be enough
      except: debuglog("js_links find_element exception ignored",False)
      currentUrl = None
    if currentUrl == None: # we need to ask for it again
        currentUrl = manager.current_url()
        if not currentUrl: currentUrl = url # PhantomJS Issue #13114: relative links after a redirect are not likely to work now
    if S(currentUrl) == "about:blank":
        debuglog("got about:blank instead of "+S(url))
        return wrapResponse("webdriver failed to load") # don't return an actual redirect to about:blank, which breaks some versions of Lynx
    debuglog("Getting data from webdriver %d (current_url=%s)" % (manager.start+manager.index,S(currentUrl)))
    if asScreenshot: return wrapResponse(manager.getpng(),tornado.httputil.HTTPHeaders.parse("Content-type: image/png"),200)
    body = get_and_remove_httpequiv_charset(manager.getu8())[1]
    if timed_out: manager.get("about:blank") # as the timeout might have been due to a hard-locked script, so interrupting it should save some CPU
    if not re.sub(B('#.*'),B(''),B(currentUrl)) == B(url): # we have to ignore anything after a # in this comparison because we have no way of knowing (here) whether the user's browser already includes the # or not: might send it into a redirect loop
        # If we redirect, and if we have more than one user session active (and especially if we're multicore) then the second request might not come back to the same webdriver instance (or even the same adjuster process, so we can't even cache it unless shared), and reload is bad, so try to avoid redirect if possible.
        # We could set 'base href' instead, seeing as 'document.location' does not have to be right on the user's side as we've already executed the site's scripts here (unless the user has any extensions that require it to be right).  Don't use Content-Location header: not all browsers support + might cause caches to tread POST requests as invariant.
        # Any in-document "#" links will cause a reload if 'base href' is set, but at least we won't have to reload UNLESS the user follows such a link.
        if htmlFind(body,"<base href=") >= 0:
            pass # if it already has a <base href> we can leave it as-is, since it won't matter from which URL it was served
        else: return wrapResponse(addToHead(body,B('<base href="')+re.sub(B('#.*'),B(''),B(currentUrl))+B('">')),tornado.httputil.HTTPHeaders.parse("Content-type: text/html; charset=utf-8"),200)
    return wrapResponse(body,tornado.httputil.HTTPHeaders.parse("Content-type: text/html; charset=utf-8"),200)
def get_new_webdriver(index,renewing=False):
    if options.js_interpreter in ["HeadlessChrome","Chrome"]:
        return get_new_Chrome(index,renewing,options.js_interpreter=="HeadlessChrome")
    elif options.js_interpreter in ["HeadlessFirefox","Firefox"]:
        return get_new_Firefox(index,renewing,options.js_interpreter=="HeadlessFirefox")
    else: return get_new_PhantomJS(index,renewing)
def get_new_Chrome(index,renewing,headless):
    log_complaints = (index==0 and not renewing)
    from selenium.webdriver.chrome.options import Options
    opts = Options() ; dc = None
    # TODO: can set opts.binary_location if needed (e.g. for chromium, if distro's linking doesn't work)
    if headless:
        opts.add_argument("--headless")
        opts.add_argument("--disable-gpu")
    # Specify user-data-dir ourselves, further to Chromium bug 795 comment 12.  Include username and port (in case others are running or have run adjuster) as well as index.
    global myUsername
    try: myUsername
    except NameError:
        try: import getpass
        except ImportError: getpass = None
        if getpass: myUsername = S(getpass.getuser())
        else: myUsername = ""
    extra = ""
    while True: # might be restarting from a corrupted user-data-dir state; in worst case might not even be able to cleanly remove it (TODO: what if some processes associated with an older instance somehow took a while to go away and still have named referenc to previous path: increment counter unconditionally?  still rm the old one)
        path = "/tmp/hChrome-"+myUsername+str(options.port)+"."+str(index)+extra # don't use writable_tmpdir() here: some versions of Chromedriver can fail if you try to put a /dev/shm path into --user-data-dir
        if not os.path.exists(path): break
        shutil.rmtree(path,True)
        if not os.path.exists(path): break
        if extra: extra="-"+str(int(extra[1:])+1)
        else: extra = "-0"
    opts.add_argument("--user-data-dir="+path)
    opts.add_argument("--incognito") # reduce space taken up by above
    if options.js_reproxy:
        opts.add_argument("--proxy-server=127.0.0.1:%d" % proxyPort(index))
        opts.add_argument("--ignore-certificate-errors") # --ignore-certificate-errors is ignored by Chrome 59 (which was the first version to support Headless) and possibly some earlier versions, but we'll put it in just in case somebody runs an ancient non-headless Chrome in an offline experiment
        opts.add_argument("--allow-insecure-localhost") # Chrome 62+ can at least do *.localhost & 127.* but we'd need to domain-rewrite for this to help (proxy-host doesn't count)
        # Chrome 65 and chromedriver 2.35/2.36? can do:
        dc = wd_DesiredCapabilities(log_complaints)
        if dc:
            dc = dc.CHROME.copy()
            dc['acceptInsecureCerts'] = True
    elif options.upstream_proxy: opts.add_argument('--proxy-server='+options.upstream_proxy)
    if options.logDebug: opts.add_argument("--verbose")
    if options.js_UA and not options.js_UA.startswith("*"): opts.add_argument("--user-agent="+options.js_UA)
    if not options.js_images: opts.add_experimental_option("prefs",{"profile.managed_default_content_settings.images":2})
    # TODO: do we need to disable Javascript's ability to open new windows and tabs, plus target="_blank" etc, especially if using clickElementID?
    if options.via and not options.js_reproxy and log_complaints:
        # Oops: how can we put in a Via: header if we don't
        # have an upstream proxy to do so?  unless you want
        # to implement a Chrome extension to do it (TODO?)
        warn("--via ignored when running Chrome without --js-reproxy")
    if js_size: opts.add_argument("--window-size=%d,%d" % js_size)
    if dc: p = wd_instantiateLoop(webdriver.Chrome,index,renewing,chrome_options=opts,desired_capabilities=dc)
    else: p = wd_instantiateLoop(webdriver.Chrome,index,renewing,chrome_options=opts)
    if options.js_reproxy:
        chromeVersion = int(p.capabilities['version'].split(".")[0])
        if 59 <= chromeVersion < 65:
            if [int(x) for x in p.capabilities['chrome']['chromedriverVersion'].split(".",2)[:2]] < [2,35]: extrawarn = " (and chromedriver 2.35+)"
            else: extrawarn = ""
            warn("This version of Chrome will hang when used with js_reproxy on https pages. Try upgrading to Chrome 65+"+extrawarn) # TODO: is 59 really the first version to drop --ignore-certificate-errors ?
        elif chromeVersion >= 65 and not p.capabilities.get('acceptInsecureCerts',False): warn("This version of chromedriver will hang when used with js_reproxy on https pages. Your Chrome is new enough, but your chromedriver is not. Try downloading chromedriver 2.35/36+")
    try: p.set_page_load_timeout(options.js_timeout1)
    except: logging.info("Couldn't set HeadlessChrome page load timeout")
    return p
def get_new_Firefox(index,renewing,headless):
    if headless:
        os.environ['MOZ_HEADLESS'] = '1' # in case -headless not yet working
    from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
    profile = FirefoxProfile() ; caps = None
    log_complaints = (index==0 and not renewing) ; op = None
    proxyToUse = None
    if options.js_reproxy:
        from selenium.webdriver.common.proxy import Proxy,ProxyType
        proxyToUse = Proxy({'proxyType':ProxyType.MANUAL,'httpProxy':"127.0.0.1:%d" % proxyPort(index),'sslProxy':"127.0.0.1:%d" % proxyPort(index),'ftpProxy':'','noProxy':''})
        if hasattr(profile,"set_proxy"):
            import warnings
            warnings.filterwarnings("ignore","This method has been deprecated. Please pass in the proxy object to the Driver Object")
            profile.set_proxy(proxyToUse) ; proxyToUse = None
        profile.accept_untrusted_certs = True # needed for some older versions?
        caps = wd_DesiredCapabilities(log_complaints)
        if caps:
            caps = caps.FIREFOX.copy()
            caps['acceptInsecureCerts'] = True
            caps['acceptSslCerts'] = True # older versions
    elif options.upstream_proxy:
        if hasattr(profile,"set_proxy"):
            import warnings
            warnings.filterwarnings("ignore","This method has been deprecated. Please pass in the proxy object to the Driver Object")
            profile.set_proxy(options.upstream_proxy)
        else: proxyToUse = options.upstream_proxy
    if options.js_UA and not options.js_UA.startswith("*"): profile.set_preference("general.useragent.override",options.js_UA)
    if not options.js_images: profile.set_preference("permissions.default.image", 2)
    if options.via and not options.js_reproxy and log_complaints:
        # Oops: how can we put in a Via: header if we don't
        # have an upstream proxy to do so?  unless you want
        # to implement a Firefox extension to do it (TODO?)
        warn("--via ignored when running Firefox without --js-reproxy")
    # TODO: do any other options need to be set?  disable plugins, Firefox-update prompts, new windows/tabs with JS, etc?  or does Selenium do that?
    if options.logDebug: binary=FirefoxBinary(log_file=sys.stderr) # TODO: support logDebug to a file as well
    else: binary=FirefoxBinary()
    if headless: cmdL = ('-headless','-no-remote')
    else: cmdL = ('-no-remote',)
    if js_size: cmdL += ("-width",str(js_size[0]),"-height",str(js_size[1]))
    cmdL += ("about:blank",) # not Firefox start page
    binary.add_command_line_options(*cmdL) # cannot call this more than once
    if caps and proxyToUse: p = wd_instantiateLoop(webdriver.Firefox,index,renewing,firefox_profile=profile,firefox_binary=binary,capabilities=caps,proxy=proxyToUse)
    elif caps: p = wd_instantiateLoop(webdriver.Firefox,index,renewing,firefox_profile=profile,firefox_binary=binary,capabilities=caps)
    elif proxyToUse: p = wd_instantiateLoop(webdriver.Firefox,index,renewing,firefox_profile=profile,firefox_binary=binary,proxy=proxyToUse)
    else: p = wd_instantiateLoop(webdriver.Firefox,index,renewing,firefox_profile=profile,firefox_binary=binary)
    try: p.set_page_load_timeout(options.js_timeout1)
    except: logging.info("Couldn't set Firefox page load timeout")
    return p
block_headless_firefox = [
    # servers that Firefox tries to CONNECT to on startup
    "push.services.mozilla.com","snippets.cdn.mozilla.net","firefox.settings.services.mozilla.com","location.services.mozilla.com","shavar.services.mozilla.com",
    "aus5.mozilla.org","ftp.mozilla.org",
    "fonts.googleapis.com", # Fedora version of Firefox connects to this
    # "start.fedoraproject.org","fedoraproject.org", # Fedora version of Firefox does this (but what if user actually wants to view one of those pages?)
]
def wd_DesiredCapabilities(log_complaints):
    try:
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        return DesiredCapabilities
    except:
        if log_complaints: warn("Your Selenium installation is too old to set DesiredCapabilities.\nThis is likely to stop some js options from working properly.")
        return None
def wd_instantiateLoop(wdClass,index,renewing,**kw):
    debuglog("Instantiating "+wdClass.__name__+" "+repr(kw))
    if 'chrome_options' in kw:
        try: newChromedriver = 'options' in getargspec(webdriver.chrome.webdriver.WebDriver.__init__).args
        except: newChromedriver = False
        if newChromedriver:
            kw['options'] = kw['chrome_options']
            del kw['chrome_options']
    if not renewing: time.sleep(min(2*(index % js_per_core),int(options.js_timeout2 / 2))) # try not to start them all at once at the beginning (may reduce chance of failure)
    while True:
        try:
            if wdClass==webdriver.Chrome: p = wdClass(getoutput("which chromedriver 2>/dev/null"),**kw) # some versions need to be told explicitly where chromedriver is, rather than looking in PATH themselves, in order to get "wrong version" errors etc (otherwise errors ignored, Selenium looks for a different chromedriver and gives a slightly confusing error about 'none found' rather than the error you should have seen about 'wrong version')
            else: p = wdClass(**kw)
            if not p.capabilities: raise Exception("Didn't seem to get a p.capabilities")
            elif 'browserVersion' in p.capabilities:
                # Selenium 2.x calls it version, but Selenium
                # 3.x calls it browserVersion.  Map this back
                # to 'version' for our other code.
                p.capabilities['version'] = p.capabilities['browserVersion']
            elif not 'version' in p.capabilities: raise Exception("capabilities has no version: "+repr(p.capabilities.items()))
        except:
            if index==0 and not renewing: raise
            logging.error("Unhandled exception "+exc_logStr()+" when instantiating webdriver %d, retrying in 2sec" % index)
            time.sleep(2) ; p = None
        if p: break
    debuglog(wdClass.__name__+" instantiated")
    return p
def _get_new_PhantomJS(index,renewing):
    log_complaints = (index==0 and not renewing)
    os.environ["QT_QPA_PLATFORM"]="offscreen"
    sa = ['--ssl-protocol=any']
    # if options.logDebug: sa.append("--debug=true") # doesn't work: we don't see the debug output on stdout or stderr
    if options.js_reproxy:
        sa.append('--ignore-ssl-errors=true')
        sa.append('--proxy=127.0.0.1:%d' % proxyPort(index))
    elif options.upstream_proxy: sa.append('--proxy='+options.upstream_proxy)
    dc = wd_DesiredCapabilities(log_complaints)
    if dc:
        dc = dict(dc.PHANTOMJS)
        if options.js_UA and not options.js_UA.startswith("*"): dc["phantomjs.page.settings.userAgent"]=options.js_UA
        if not options.js_images: dc["phantomjs.page.settings.loadImages"]=False
        dc["phantomjs.page.settings.javascriptCanOpenWindows"]=dc["phantomjs.page.settings.javascriptCanCloseWindows"]=False # TODO: does this cover target="_blank" in clickElementID etc (which could have originated via DOM manipulation, so stripping them on the upstream proxy is insufficient; close/restart the driver every so often?)
        if options.via and not options.js_reproxy: dc["phantomjs.page.customHeaders.Via"]="1.0 "+convert_to_via_host("")+" ("+viaName+")" # customHeaders works in PhantomJS 1.5+ (TODO: make it per-request so can include old Via headers & update protocol version, via_host + X-Forwarded-For; will webdriver.DesiredCapabilities.PHANTOMJS[k]=v work before a request?) (don't have to worry about this if js_reproxy)
        return wd_instantiateLoop(webdriver.PhantomJS,index,renewing,desired_capabilities=dc,service_args=sa)
    else: return wd_instantiateLoop(webdriver.PhantomJS,index,renewing,service_args=sa)
def get_new_PhantomJS(index,renewing=False):
    wd = _get_new_PhantomJS(index,renewing)
    log_complaints = (index==0 and not renewing)
    if log_complaints and not options.js_reproxy:
     try: is_v2 = wd.capabilities['version'].startswith("2.")
     except: is_v2 = False
     if is_v2: warn("You may be affected by PhantomJS issue #13114.\nRelative links may be wrong after a redirect if the site sets Content-Security-Policy.\nTry --js_reproxy, or downgrade your PhantomJS to version 1.9.8")
    try: wd.set_window_size(*js_size)
    except: logging.info("Couldn't set PhantomJS window size")
    try: wd.set_page_load_timeout(options.js_timeout1)
    except: logging.info("Couldn't set PhantomJS page load timeout")
    return wd
def proxyPort(index): return port_randomise.get(js_proxy_port[index],js_proxy_port[index])
webdriver_runner = [] ; webdriver_prefetched = []
webdriver_via = [] ; webdriver_UA = [] ; webdriver_AL = []
webdriver_inProgress = [] ; webdriver_queue = []
webdriver_lambda = webdriver_mu = 0
def test_init_webdriver():
    "Check that we CAN start a webdriver, before forking to background and starting all of them"
    if options.js_interpreter=="edbrowse": return
    sys.stderr.write("Checking webdriver configuration... "),sys.stderr.flush()
    get_new_webdriver(0).quit()
    sys.stderr.write("OK\n")
quitFuncToCall = None
def init_webdrivers(start,N):
    informing = not options.background and not start and not (options.multicore and options.ssl_fork) # (if ssl_fork, we don't want the background 'starting N processes' messages to be interleaved with this)
    if informing:
        sys.stderr.write("Starting %d webdriver%s... " % (options.js_instances,plural(options.js_instances))),sys.stderr.flush()
    for i in xrange(N):
        webdriver_runner.append(WebdriverRunner(start,len(webdriver_runner)))
        webdriver_prefetched.append(None)
        webdriver_inProgress.append(set())
        webdriver_via.append(None) ; webdriver_UA.append("") ; webdriver_AL.append("")
    def quit_wd_atexit(*args):
      if informing: sys.stderr.write("Quitting %d webdriver%s... " % (options.js_instances,plural(options.js_instances))),sys.stderr.flush()
      try:
        for i in webdriver_runner:
            try: i.quit_webdriver()
            except: pass
      except: pass
      if informing: sys.stderr.write("done\n")
    global quitFuncToCall ; quitFuncToCall = quit_wd_atexit # don't use the real atexit, as we have our own thread-stop logic which might kick in first, leaving a stuck adjusterWDhelp process if js_multiprocess==True, and additionally holding up calling process if --stdio is in use (fixed in v0.2795)
    if options.js_restartMins and not options.js_restartAfter==1: IOLoopInstance().add_timeout(time.time()+60,webdriver_checkRenew)
    if informing: sys.stderr.write("done\n")
webdriver_maxBusy = 0
def webdriver_allBusy():
    busyNow = sum(1 for i in webdriver_runner if i.wd_threadStart)
    global webdriver_maxBusy
    webdriver_maxBusy = max(webdriver_maxBusy,busyNow)
    return busyNow == len(webdriver_runner)
def webdriver_checkServe(*args):
    # how many queue items can be served right now?
    # (called on IOLoop thread when new item added, or when
    # a server is finished)
    debuglog("Entering webdriver_checkServe, runners=%d" % len(webdriver_runner))
    for i in xrange(len(webdriver_runner)):
        if not webdriver_queue: break # just to save a little
        if not webdriver_runner[i].wd_threadStart:
            while webdriver_queue:
                url,prefetched,ua,acceptLang,clickElementID,clickLinkText,via,asScreenshot,callback,tooLate = webdriver_queue.pop(0)
                if tooLate():
                    debuglog("tooLate() for "+url)
                    continue
                debuglog("Starting fetch of "+url+" on webdriver instance "+str(i+webdriver_runner[i].start))
                webdriver_via[i],webdriver_UA[i] = via,ua
                webdriver_AL[i] = acceptLang
                webdriver_runner[i].fetch(url,prefetched,clickElementID,clickLinkText,asScreenshot,callback,tooLate)
                global webdriver_mu ; webdriver_mu += 1
                break
    if webdriver_allBusy(): pauseOrRestartMainServer(0) # we're "paused" anyway when not in the poll wait, so might as well call this only at end, to depend on the final status (and make sure to call webdriver_allBusy() no matter what, as it has the side-effect of updating webdriver_maxBusy)
    else: pauseOrRestartMainServer(1)
    debuglog("Finishing webdriver_checkServe, webdriver_queue len=%d" % len(webdriver_queue))
def webdriver_checkRenew(*args):
    for i in webdriver_runner:
        if not i.wd_threadStart and i.usageCount and i.finishTime + options.js_restartMins < time.time(): i.renew_webdriver_newThread() # safe because we're running in the IOLoop thread, which therefore can't start wd_thread between our test of wd_threadStart and renew_webdriver_newThread
    IOLoopInstance().add_timeout(time.time()+60,webdriver_checkRenew)
def webdriver_fetch(url,prefetched,ua,acceptLang,clickElementID,clickLinkText,via,asScreenshot,callback,tooLate):
    if tooLate(): return # probably webdriver_queue overload (which will also be logged)
    elif prefetched and (not hasattr(prefetched,"code") or prefetched.code >= 500 or not hasattr(prefetched,"body") or not re.search(b'<script',B(prefetched.body),flags=re.I)): return callback(prefetched) # don't bother allocating a webdriver if we got a timeout or DNS error or something, or a page with no JS (TODO: what if a page has onload=... with the scripts fully embedded in the attributes?  does edbrowse enable JS for that?  may need to ensure js_fallback is switched on when using edbrowse, in case edbrowse disables JS when we thought it wouldn't)
    elif wsgi_mode: return callback(_wd_fetch(webdriver_runner[0],url,prefetched,clickElementID,clickLinkText,asScreenshot)) # (can't reproxy in wsgi_mode, so can't use via and ua) TODO: if *threaded* wsgi, index 0 might already be in use (we said threadsafe:true in AppEngine instructions but AppEngine can't do js_interpreter anyway; where else might we have threaded wsgi?  js_interpreter really is better run in non-wsgi mode anyway, so can js_reproxy)
    webdriver_queue.append((url,prefetched,ua,acceptLang,clickElementID,clickLinkText,via,asScreenshot,callback,tooLate))
    global webdriver_lambda ; webdriver_lambda += 1
    debuglog("webdriver_queue len=%d after adding %s" % (len(webdriver_queue),url))
    webdriver_checkServe() # safe as we're IOLoop thread

#@file: http-rewrite.py
# --------------------------------------------------
# Service routines for basic HTTP header rewriting
# --------------------------------------------------

def fixServerHeader(i):
    i.set_header("Server",serverName)
    # TODO: in "real" proxy mode, "Server" might not be the most appropriate header to set for this
    try: i.clear_header("Date") # Date is added by Tornado 3; HTTP 1.1 says it's mandatory but then says don't put it if you're a clockless server (which we might be I suppose) so it seems leaving it out is OK especially if not specifying Age etc, and leaving it out saves bytes.  But if the REMOTE server specifies a Date then we should probably pass it on (see comments in doResponse below)
    except: pass # (ok if "Date" wasn't there)

rmServerHeaders = set([
    # server headers to remove.  We'll do our own connection type etc (but don't include "Date" in this list: if the remote server includes a Date it would be useful to propagate that as a reference for its Age headers etc, TODO: unless remote server is broken? see also comment in fixServerHeader re having no Date by default).  Many servers' Content-Location is faulty; it DOESN'T necessarily provide the new base href; it might be relative; it might be identical to the actual URL fetched; many browsers ignore it anyway
    "connection","content-length","content-encoding","transfer-encoding","etag","content-md5","server","alternate-protocol","strict-transport-security","content-location",
    
    "x-associated-content", # should NOT be sent to browser (should be interpreted by a server's SPDY/push module) but somebody might misread the specs (at least one Wikipedia editor did)
    
    "x-host","x-http-reason", # won't necessarily be the same
    
    "content-security-policy","x-webkit-csp","x-content-security-policy","x-frame-options", # sorry but if we're adjusting the site by adding our own scripts/styles we are likely to be broken by a CSP that restricts which of these we're allowed to do. (Even if we adjust the domains listed on those headers, what if our scripts rely on injecting inline code?)  Sites shouldn't *depend* on CSP to prevent XSS: it's just a belt-and-braces that works only in recent browsers.  Hopefully our added styles etc will break the XSS-introduced ones if we hit a lazy site.
    
    "vary", # we modify this (see code)
    
    "alt-svc",
    "public-key-pins","public-key-pins-report-only",
])
# TODO: WebSocket (and Microsoft SM) gets the client to say 'Connection: Upgrade' with a load of Sec-WebSocket-* headers, check what Tornado does with that
rmClientHeaders = ['Connection','Proxy-Connection','Accept-Charset','Accept-Encoding','X-Forwarded-Host','X-Forwarded-Port','X-Forwarded-Server','X-Forwarded-Proto','X-Request-Start','TE','Upgrade',
                   'Upgrade-Insecure-Requests', # we'd better remove this from the client headers if we're removing Content-Security-Policy etc from the server's
                   'Range', # TODO: we can pass Range to remote server if and only if we guarantee not to need to change anything  (could also add If-Range and If-None-Match to the list, but these should be harmless to pass to the remote server and If-None-Match might actually help a bit in the case where the document doesn't change)
]

#@file: request-forwarder.py
# --------------------------------------------------
# Our main RequestForwarder class.  Handles incoming
# HTTP requests, generates requests to upstream servers
# and handles responses.  Sorry it's got a bit big :-(
# --------------------------------------------------

the_supported_methods = ("GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "CONNECT")
# Don't support PROPFIND (from WebDAV) unless be careful about how to handle image requests with it
# TODO: image requests with OPTIONS ?

class RequestForwarder(RequestHandler):
    
    def get_error_html(self,status,**kwargs): return htmlhead("Web Adjuster error")+options.errorHTML+"</body></html>" # Tornado 2.0
    def write_error(self,status,**kwargs): # Tornado 2.1+
        if hasattr(self,"_finished") and self._finished: return
        msg = self.get_error_html(status,**kwargs)
        if "{traceback}" in msg and 'exc_info' in kwargs:
            msg = msg.replace("{traceback}","<pre>"+ampEncode("".join(traceback.format_exception(*kwargs["exc_info"])))+"</pre>")
            # TODO: what about substituting for {traceback} on pre-2.1 versions of Tornado that relied on get_error_html and put the error into sys.exc_info()?  (need to check their source to see how reliable the traceback is in this case; post-2.1 versions re-raise it from write_error itself)
        if self.canWriteBody(): self.write(msg)
        self.finish()

    def cookie_host(self,checkReal=True,checkURL=True):
        # for cookies telling us what host the user wants
        if self.isPjsUpstream or self.isSslUpstream:
            return False
        if checkReal and convert_to_real_host(self.request.host,None): return # if we can get a real host without the cookie, the cookie does not apply to this host
        if enable_adjustDomainCookieName_URL_override and checkURL:
            if self.cookieViaURL: v = self.cookieViaURL
            else:
                v = self.request.arguments.get(adjust_domain_cookieName,None)
                if type(v)==type([]): v=v[-1]
                if v: self.removeArgument(adjust_domain_cookieName,quote(v))
            if v: # will be a B()
                self.cookieViaURL = v
                return None if v==adjust_domain_none else v
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
            for c in self.cookieDomainsToSet("; Domain="): self.add_header("Set-Cookie",n+"="+v+c+"; Path=/; Expires=Thu Jan 01 00:00:00 1970") # to clear it
    def setCookie_with_dots(self,kv):
        for c in self.cookieDomainsToSet("; Domain="): self.add_header("Set-Cookie",kv+c+"; Path=/; Expires="+cookieExpires) # (at least in Safari, need BOTH with and without the dot to be sure of setting the domain and all subdomains.  TODO: might be able to skip the dot if not wildcard_dns, here and in the cookie-setting scripts.)
    def addCookieFromURL(self):
        if self.cookieViaURL: self.add_header("Set-Cookie",adjust_domain_cookieName+"="+quote(S(self.cookieViaURL))+"; Path=/; Expires="+cookieExpires) # don't need dots for this (non-wildcard)

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
            ret2 = unquote(toRemove[len(webdriver_click_code):])
        elif not options.viewsource: return False
        else: ret2 = None
        if self.request.uri.endswith(".viewsource"):
            if toRemove: ret2 = ret2[:-len(".viewsource")]
            else: toRemove = ".viewsource"
            ret = True
        elif options.js_interpreter and self.request.uri.endswith(".screenshot"):
            if toRemove: ret2 = ret2[:-len(".screenshot")]
            else: toRemove = ".screenshot"
            ret = "screenshot"
        elif not toRemove: return False
        if ret2: ret = (ret2,ret)
        self.request.uri = self.request.uri[:-len(toRemove)]
        if not S(self.request.method).lower() in ['get','head']: return ret # TODO: unless arguments are taken from both url AND body in that case
        for k,argList in self.request.arguments.items(): # rm .viewsource or screenshot from the last argument as well, if that's where the user put it (note however that this cannot be used together with a p= password argument during initial access, since authentication happens before checkViewsource)
            if argList and B(argList[-1]).endswith(B(toRemove)):
                argList[-1]=B(argList[-1])[:-len(B(toRemove))]
                break
        return ret
    
    def cookieDomainsToSet(self,prefix):
        host = S(self.request.host)
        for hs in options.host_suffix.split("/"):
            if host.endswith("."+hs):
                return prefix+hs, prefix+"."+hs
            elif options.alt_dot and host.endswith(options.alt_dot+hs):
                if altdot_bad_cookie_leak: return "", prefix+hs[hs.index("."):] # xyz-dot-adjuster.example.net -> *.example.net (second might be blocked, unless use JS to promote for experimental purposes only)
                else: return [""] # current host only (insufficiently broad)
        # If reaches here, incoming request is not a 'subdomain'
        for p in [options.publicPort,options.port]: # port possible for local connections if publicPort set to something else
            p=':'+str(p)
            if host.endswith(p):
                if options.wildcard_dns:
                    return "", prefix+"."+host[:-len(p)]
                else: return [""]
        if options.wildcard_dns:
            return "", prefix+"."+host
        else: return [""]
    def urlBoxHost(self):
        host = S(self.request.host)
        for hs in options.host_suffix.split("/"):
            if host.endswith("."+hs) or options.alt_dot and host.endswith(options.alt_dot+hs): return hs
        for p in [options.publicPort,options.port]:
            p=':'+str(p)
            if host.endswith(p): return host[:-len(p)]
        return host
    
    def authenticates_ok(self,host):
        if not options.password: return True
        host = S(host)
        if options.password_domain and host and not any((host==p or host.endswith("."+p) or options.alt_dot and host.endswith(options.alt_dot+p)) for p in options.password_domain.split('/')): return True
        if options.password_domain: self.is_password_domain=True
        # if they said ?p=(password), it's OK and we can
        # give them a cookie with it
        if B(self.getArg("p")) == B(options.password):
            self.setCookie_with_dots(password_cookie_name+"="+quote(options.password))
            self.removeArgument("p",options.password)
            return True
        return self.getCookie(password_cookie_name)==quote(options.password)

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
      try: host, port = S(self.request.uri).split(':')
      except: host,port = None,None
      if host and (options.real_proxy or self.isPjsUpstream or self.isSslUpstream) and not (self.isPjsUpstream and options.js_interpreter in ["HeadlessFirefox","Firefox"] and host in block_headless_firefox): # support tunnelling if real_proxy (but we might not be able to adjust anything, see below)
        upstream = tornado.iostream.IOStream(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0))
        client = self.request.connection.stream
        # See note about Tornado versions in writeAndClose
        if not self.isSslUpstream and int(port)==443:
            # We can change the host/port to ourselves
            # and adjust the SSL site (assuming this CONNECT
            # is for an SSL site)
            # This should result in a huge "no cert" warning
            host,port = "127.0.0.1",port_randomise.get(self.WA_connectPort,self.WA_connectPort)
            debuglog("Rerouting CONNECT to "+host+":"+str(port))
            self.request.suppress_logging = True # no need to log the CONNECT if our other port will be logging the GET
        def callback(*args):
          readUntilClose(client,lambda data:writeAndClose(upstream,data),lambda data:writeOrError(client,"upstream "+host+":"+str(port)+self.debugExtras(),upstream,data)) # (DO say 'upstream', as if host==localhost it can be confusing (TODO: say 'upstream' only if it's 127.0.0.1?))
          if self.isPjsUpstream: clientErr=None # we won't mind if our js_interpreter client gives up on an upstream fetch
          else: clientErr = "client "+self.request.remote_ip+self.debugExtras()
          readUntilClose(upstream,lambda data:writeAndClose(client,data),lambda data:writeOrError(upstream,clientErr,client,data))
          try:
              client.write(B('HTTP/1.0 200 Connection established\r\n\r\n'))
              debuglog("Connection established")
          except tornado.iostream.StreamClosedError:
              if not self.isPjsUpstream: logging.error("client "+self.request.remote_ip+" closed before we said Established"+self.debugExtras())
        doCallback(self,upstream.connect,callback,(host, int(port)))
        # Tornado _log is not called until finish(); it would be useful to log the in-process connection at this point
        try: self._log()
        except: pass # not all Tornado versions support this?
      else: self.set_status(400),self.myfinish()
    def on_connection_close(self): self.myfinish()
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
        elif options.one_request_only and not self.isSslUpstream:
            if options.stdio: IOLoopInstance().add_timeout(time.time()+1,lambda *args:stopServer("Stopping after 1 request + 1 second")) # otherwise stdout-write sometimes doesn't happen (Tornado 6.1)
            else:
                stopServer("Stopping after one request")
        try: reqsInFlight.remove(id(self))
        except: pass
        try: origReqInFlight.remove(id(self))
        except: pass

    def redirect(self,redir,status=301):
        if self.can_serve_without_redirect(redir):
            return self.doReq0()
        debuglog("Serving redirect ("+repr(status)+" to "+repr(redir)+")"+self.debugExtras())
        try: self.set_status(status)
        except ValueError: self.set_status(status, "Redirect") # e.g. 308 (not all Tornado versions handle it)
        for h in ["Location","Content-Type","Content-Language"]: self.clear_header(h) # clear these here, so redirect() can still be called even after a site's headers were copied in
        omit_scheme = options.urlscheme=="//" and url_is_ours(redir) # (no need to send the correct cookieHost, just need to know if host was changed)
        if omit_scheme:
            # If we're behind an optional HTTPS-terminating proxy, it would be nice to tell the browser to keep whatever protocol it's currently using, IF the browser would definitely understand this.
            # RFC 7231 from 2014 allows relative redirects in updated HTTP/1.1 based on browser observations, but original 1999 HTTP/1.1 RFC didn't.  MSIE 9 from 2011 allows relative.
            if self.checkBrowser(["Lynx/2.8","Gecko/20100101","Trident/7","Trident/8","Trident/9","Edge"]): pass
            else:
                ua = S(self.request.headers.get("User-Agent",""))
                def v(b):
                    if b in ua:
                        m = re.match("[0-9]+",ua[ua.index(b)+len(b):])
                        if m: return int(m.group())
                    return 0
                if v("WebKit/") < 537: # TODO: or v("") < ... etc
                    # I haven't been able to test it works on these old versions
                    omit_scheme = False
        if omit_scheme: redir = S(redir).replace("http:","",1)
        elif options.urlscheme=="https://" and url_is_ours(redir): redir = S(redir).replace("http:","https:",1)
        self.add_header("Location",S(redir))
        if omit_scheme: pass # these browsers don't need a body
        else:
            self.add_header("Content-Type","text/html")
            if self.canWriteBody(): self.write(B('<html lang="en"><body><a href="%s">Redirect</a></body></html>' % S(redir).replace('&','&amp;').replace('"','&quot;')))
        self.myfinish()

    def can_serve_without_redirect(self,redir):
        # Try to serve without redirect if all links can be rewritten and urlboxPath might matter
        if self.isSslUpstream or self.isPjsUpstream or options.wildcard_dns or options.urlboxPath=="/" or not self.htmlOnlyMode(): return # TODO: isProxyRequest argument to htmlOnlyMode? (relevant only if someone configures an adjuster with a non-/ urlbox-path that ALSO accepts real-proxy requests)
        if not hasattr(self.request,"redirCount"):
            self.request.redirCount = 0
        if self.request.redirCount >= 10: return # loop?
        self.request.redirCount += 1
        self.cookieViaURL = None # recalculate:
        oldArgs = self.request.arguments
        (scheme, netloc, path, query, fragment) = urlparse.urlsplit(S(redir))
        self.request.arguments = urlparse.parse_qs(query)
        if not url_is_ours(redir,self.cookie_host()):
            # raise Exception(repr((redir,self.cookie_host()))) # for testing
            self.request.arguments = oldArgs
            return
        if not path.startswith("/"): path="/"+path
        if query: query = "?"+query
        self.request.uri = scheme+"://"+netloc+path+query
        self.request.path = path
        return True

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
        ua = " "+S(self.request.headers.get("User-Agent",""))
        if " curl/" in ua or " Wget/" in ua: return False # (but don't return false for libcurl/)
        self.set_status(200)
        self.add_nocache_headers()
        self.add_header("Refresh","10") # TODO: configurable refresh period?  and make sure it does not exceed options.pdfepubkeep
        self.clear_header("Content-Disposition")
        self.clear_header("Content-Type")
        self.add_header("Content-Type","text/html")
        self.inProgress_has_run = True # doResponse2 may set a callback for render, so can't set _finished yet, but do need to set something so txtCallback knows not to write the actual text into this response (TODO could do a "first one there gets it" approach, but it's unlikely to be needed)
        warn=self.checkBrowser(["IEMobile 6","IEMobile 7","Opera Mobi"],"<h3>WARNING: Your browser might not save this file</h3>You are using {B}, which has been known to try to display text attachments in its own window using very small print, giving no option to save to a file. You might get better results in IEMobile 8+ or Opera Mini (although the latter may have a more limited range of font sizes in the browser itself).") # TODO: make this warning configurable?  See comment after set_header("Content-Disposition",...) below for details
        self.doResponse2(("""%s<h1>File conversion in progress</h1>The result should start downloading soon. If it does not, try <script><!--
document.write('<a href="javascript:location.reload(true)">refreshing this page</a>')
//-->
</script><noscript>refreshing this page</noscript>.%s%s<hr>This is %s</body></html>""" % (htmlhead("File conversion in progress"),backScript,warn,serverName_html)),True,False)
        # TODO: if (and only if) refreshing from this page, might then need a final 'conversion finished' page before serving the attachment, so as not to leave an 'in progress' page up afterwards
        return True
    def inProgress_run(self): return hasattr(self,"inProgress_has_run") and self.inProgress_has_run

    def addToHeader(self,header,toAdd):
        val = S(self.request.headers.get(header,""))
        toAdd = S(toAdd)
        if (", "+val).endswith(", "+toAdd): return # seems we're running inside a software stack that already added it
        if val: val += ", "
        self.request.headers[header] = val+toAdd

    def forwardFor(self,server,logName):
        server = S(server)
        debuglog("forwardFor "+server+self.debugExtras())
        if wsgi_mode: raise Exception("Not implemented for WSGI mode") # no .connection
        upstream = tornado.iostream.IOStream(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0))
        client = self.request.connection.stream
        if ':' in server: host, port = server.split(':')
        else: host, port = server, 80
        doCallback(self,upstream.connect,lambda *args:(readUntilClose(upstream,lambda data:writeAndClose(client,data),lambda data:writeOrError(upstream,logName+" client",client,data)),readUntilClose(client,lambda data:writeAndClose(upstream,data),lambda data:writeOrError(client,logName+" upstream",upstream,data))),(host, int(port)))
        try: self.request.uri = self.request.original_uri
        except: pass
        upstream.write(B(self.request.method)+B(" ")+B(self.request.uri)+B(" ")+B(self.request.version)+B("\r\n")+B("\r\n".join(("%s: %s" % (k,v)) for k,v in (list(h for h in self.request.headers.get_all() if not h[0].lower()=="x-real-ip")+[("X-Real-Ip",self.request.remote_ip)]))+"\r\n\r\n")+B(self.request.body))

    def thin_down_headers(self):
        # For ping.  Need to make the response short, but still allow keepalive
        self.request.suppress_logging = True
        for h in ["Server","Content-Type","Date"]:
            try: self.clear_header(h)
            except: pass
        # (Date is added by Tornado 3, which can also add "Vary: Accept-Encoding" but that's done after we get here, TODO: option to ping via a connect and low-level TCP keepalive bytes?)
        self.set_header("Etag","0") # clear_header won't work with Etag, but at least we can set one that's shorter than Tornado's computed one (TODO: could override RequestHandler's compute_etag and make it return None if we've set somewhere that we don't want Etag on the current request)

    def answerPing(self,newVersion):
        # answer a "ping" request from another machine that's using us as a fasterServer
        self.thin_down_headers()
        if newVersion and not wsgi_mode:
            # Forget the headers, just write one byte per second for as long as the connection is open
            # TODO: document that it's a bad idea to set up a fasterServer in wsgi_mode (can't do ipTrustReal, must have fasterServerNew=False, ...)
            stream = self.request.connection.stream
            stream.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            def writeBytes():
                try:
                    stream.write(B("1"))
                    IOLoopInstance().add_timeout(time.time()+1,lambda *args:writeBytes())
                except:
                    # logging.info("ping2: disconnected")
                    self.myfinish()
            if not options.background: sys.stderr.write("ping2: "+S(self.request.remote_ip)+" connected\n") # (don't bother logging this normally, but might want to know when running in foreground)
            writeBytes()
        else:
            self.write(B("1")) ; self.myfinish()

    def answer_load_balancer(self):
        self.request.suppress_logging = True
        self.add_header("Content-Type","text/html")
        if self.canWriteBody(): self.write(B(htmlhead()+"<h1>Web Adjuster load-balancer page</h1>This page should not be shown to normal browsers, only to load balancers and uptime checkers. If you are a human reading this message, <b>it probably means your browser is \"cloaked\"</b> (hidden User-Agent string); please set a browser string to see the top-level page.</body></html>"))
        self.myfinish()

    def find_real_IP(self):
        if wsgi_mode: return
        if options.trust_XForwardedFor:
            xff = self.request.headers.get_list("X-Forwarded-For")
            if xff:
                xff = xff[0].split()
                # (TODO: do we always want FIRST header?)
                if xff:
                    self.request.remote_ip = xff[0]
                    return
        if not options.ipTrustReal in [S(self.request.remote_ip),'*']: return
        try: self.request.remote_ip = self.request.connection.stream.confirmed_ip
        except:
            self.request.remote_ip = self.request.headers.get("X-Real-Ip",self.request.remote_ip)
            try: self.request.connection.stream.confirmed_ip = self.request.remote_ip # keep it for keepalive connections (X-Real-Ip is set only on the 1st request)
            except: pass
        try: del self.request.headers["X-Real-Ip"]
        except: pass
    
    def serveRobots(self):
        self.add_header("Content-Type","text/plain")
        if self.canWriteBody(): self.write(B("User-agent: *\nDisallow: /\n"))
        self.request.suppress_logger_host_convert = True
        self.myfinish()

    def serveImage(self,img):
        if not options.renderLog:
            self.request.suppress_logging = True
        self.add_header("Content-Type","image/"+options.renderFormat)
        self.add_header("Last-Modified","Sun, 06 Jul 2008 13:20:05 GMT")
        self.add_header("Expires","Wed, 1 Dec 2036 23:59:59 GMT") # TODO: S2G (may need Cache-Control with max-age directive instead, drop older browsers)
        # self.clear_header("Server") # save bytes if possible as we could be serving a LOT of these images .. but is this really needed? (TODO)
        if self.canWriteBody(): self.write(img)
        self.myfinish()

    def set_htmlonly_cookie(self):
        # Set the cookie according to the value of "pr" entered from the URL box.
        # TODO: option to combine this and other cookie-based settings with enable_adjustDomainCookieName_URL_override so the setting can be bookmarked ?  (some users might want that off however, as an address is different from a setting; in the case of htmlOnly the q= URL can already be bookmarked if can stop it before the redirect)
        if options.htmlonly_mode:
            htmlonly_mode = (force_htmlonly_mode or "pr" in self.request.arguments)
            current_setting = htmlmode_cookie_name+"=1" in ';'.join(self.request.headers.get_list("Cookie"))
            if not htmlonly_mode == current_setting:
                if htmlonly_mode: val="1"
                else: val="0"
                self.setCookie_with_dots(htmlmode_cookie_name+"="+val)
                # and also add it to self.request.headers,
                # for the benefit of htmlOnlyMode below
                # which sees the same request
                # (TODO: delete old setting? but it's
                # usually used only by redir)
                self.request.headers.add("Cookie",htmlmode_cookie_name+"="+val)
    def htmlOnlyMode(self,isProxyRequest=False):
        # order is important here
        if not options.htmlonly_mode: return False
        elif self.isPjsUpstream or self.isSslUpstream:
            return False
        elif self.auto_htmlOnlyMode(isProxyRequest):
            return True
        elif isProxyRequest: return False
        elif force_htmlonly_mode: return True
        elif hasattr(self.request,"old_cookie"): ck = self.request.old_cookie # so this can be called between change_request_headers and restore_request_headers, e.g. at the start of send_request for js_interpreter mode
        else: ck = ';'.join(self.request.headers.get_list("Cookie"))
        return htmlmode_cookie_name+"=1" in ck
    def auto_htmlOnlyMode(self,isProxyRequest): return options.js_interpreter and (isProxyRequest or (not options.wildcard_dns and not can_do_cookie_host()))
    
    def handle_URLbox_query(self,v):
        self.set_htmlonly_cookie()
        v = B(v)
        if not re.match(B("https?://"),v):
            if B(' ') in v or not B('.') in v: v=getSearchURL(v)
            else: v=B("http://")+v
        if not options.wildcard_dns: # need to use cookie_host
            j = i = v.index(B('/'))+2 # after the http:// or https://
            while j<len(v) and v[j] in B(letters+digits+'.-'): j += 1
            wanted_host = v[i:j]
            if v[i-4:i-3]==B('s'): wanted_host += B(".0") # HTTPS hack (see protocolAndHost)
            ch = self.cookie_host(checkURL=False) # current cookie hostname
            if B(convert_to_requested_host(wanted_host,ch))==B(wanted_host):
                debuglog("Need to change cookie_host to get "+repr(wanted_host))
                if enable_adjustDomainCookieName_URL_override:
                    # do it by URL so they can bookmark it (that is if it doesn't immediately redirect)
                    # (TODO: option to also include the password in this link so it can be passed it around?  and also in the 'back to URL box' link?  but it would be inconsistent because not all links can do that, unless we consistently 302-redirect everything so that they do, but that would reduce the efficiency of the browser's HTTP fetches.  Anyway under normal circumstances we probably won't want users accidentally spreading include-password URLs)
                    v = addArgument(v,adjust_domain_cookieName+'='+quote(wanted_host))
                else: self.add_header("Set-Cookie",adjust_domain_cookieName+"="+quote(wanted_host)+"; Path=/; Expires="+cookieExpires) # (DON'T do this unconditionally, convert_to_requested_host above might see we already have another fixed domain for it)
                # (TODO: if convert_to_requested_host somehow returns a *different* non-default_site domain, that cookie will be lost.  Might need to enforce max 1 non-default_site domain.)
            else: wanted_host = ch
        else: wanted_host=None # not needed if wildcard_dns
        self.redirect(domain_process(v,wanted_host,True))

    def forwardToOtherPid(self):
        if not (options.ssl_fork and self.WA_UseSSL): return
        # We're handling SSL in a separate PID, so we have to
        # forward the request back to the original PID in
        # case it needs to do things with webdrivers etc.
        self.request.headers["X-From-Adjuster-Ssl-Helper"] = "1"
        self.forwardFor("127.0.0.1:%d" % (port_randomise.get(self.WA_origPort,self.WA_origPort)),"SSL helper:"+str(port_randomise.get(self.WA_connectPort,self.WA_connectPort)))
        return True
    def handleFullLocation(self):
        # HTTP 1.1 spec says ANY request can be of form http://...., not just a proxy request.  The differentiation of proxy/not-proxy depends on what host is requested.  So rewrite all http://... requests to HTTP1.0-style host+uri requests.
        if options.ssl_fork and self.request.headers.get("X-From-Adjuster-Ssl-Helper",""):
            debuglog("Setting isFromSslHelper"+self.debugExtras())
            self.request.connection.stream.isFromSslHelper = True # it doesn't matter if some browser spoofs that header: it'll mean they'll get .0 asked for; however we could check the remote IP is localhost if doing anything more complex with it
            del self.request.headers["X-From-Adjuster-Ssl-Helper"] # don't pass it to upstream servers
        if re.match(B("https?://"),B(self.request.uri)):
            self.request.original_uri = self.request.uri
            parsed = urlparse.urlparse(S(self.request.uri))
            self.request.host = self.request.headers["Host"] = parsed.netloc
            self.request.uri = urlparse.urlunparse(("","")+parsed[2:])
            if not self.request.uri: self.request.uri="/"
        elif not B(self.request.uri).startswith(B("/")): # invalid
            self.set_status(400) ; self.myfinish() ; return True
        if self.WA_UseSSL or (hasattr(self.request,"connection") and hasattr(self.request.connection,"stream") and hasattr(self.request.connection.stream,"isFromSslHelper")): # we're the SSL helper on port+1 and we've been CONNECT'd to, or we're on port+0 and forked SSL helper has forwarded it to us, so the host asked for must be a .0 host for https
            if self.request.host and not B(self.request.host).endswith(B(".0")): self.request.host = S(self.request.host)+".0"
            
    def handleSpecificIPs(self):
        if not ipMatchingFunc: return False
        msg = ipMatchingFunc(self.request.remote_ip)
        if not msg: return False
        if B(msg).startswith(B('*')): # a block
            self.write(B(htmlhead("Blocked"))+B(msg)[1:]+B("</body></html>")) ; self.myfinish() ; return True
        if B(self.request.uri) in [B("/robots.txt"),B("/favicon.ico")]: return False
        cookies = ';'.join(self.request.headers.get_list("Cookie"))
        if B(msg).startswith(B('-')): # minor edit
            msg = B(msg)[1:]
            if seen_ipMessage_cookieName+"=" in cookies:
                # seen ANY message before (not just this)
                return False
        val = cookieHash(msg)
        if seen_ipMessage_cookieName+"="+val in cookies:
            # seen THIS message before
            return False
        self.add_nocache_headers()
        if self.canWriteBody(): self.write(B(htmlhead("Message"))+B(msg)+(B("<p><form><label><input type=\"checkbox\" name=\"gotit\">Don't show this message again</label><br><input type=\"submit\" value=\"Continue\" onClick=\"var a='%s=%s;domain=',b=(document.forms[0].gotit.checked?'expires=%s;':'')+'path=/',h='%s;';document.cookie=a+'.'+h+b;document.cookie=a+h+b;location.reload(true);return false\"></body></html>" % (seen_ipMessage_cookieName,val,cookieExpires,self.urlBoxHost()))))
        logging.info("ip_messages: done "+S(self.request.remote_ip))
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
            msg = ' and <a rel="noreferrer" href="%s%s">go directly to the original site</a>' % (protocolWithHost(realHost),S(self.request.uri))
            self.request_no_external_referer()
        else: msg = ''
        self.add_nocache_headers()
        if self.canWriteBody(): self.write(B("%s<h1>You don't need this!</h1>This installation of Web Adjuster has been set up to change certain characters into pictures, for people using old computers that don't know how to display them themselves. However, <em>you</em> seem to be using %s, which is <noscript>either </noscript>definitely capable of showing these characters by itself<noscript>, or else wouldn't be able to show the pictures anyway<!-- like Lynx --></noscript>. Please save our bandwidth for those who really need it%s. Thank you.</body></html>" % (htmlhead(),S(browser),msg)))
        self.myfinish() ; return True

    def needCssCookies(self):
        h = options.headAppendCSS
        if not h or not '%s' in h: return False
        for ckCount in range(len(h.split(';'))-1):
            if not self.getCookie("adjustCss" + str(ckCount) + "s", ""):
                # Looks like we need to redirect back to the main page to get a CSS selection.  But just double-check it doesn't look like an XMLHttpRequest, which doesn't always send the cookies:
                if any(h in S(self.request.headers.get("Referer","")) for h in options.host_suffix.split("/")):
                    accept = S(self.request.headers.get("Accept",""))
                    if "application/json" in accept or len(accept.split(","))==2:
                        return False
                self.set_header("X-Missing-Cookie","adjustCss" + str(ckCount) + "s") # in case debugging with lynx -mime-header etc
                return True
        return False
    def cssAndAttrsToAdd(self):
        h = options.headAppendCSS ; cha = options.cssHtmlAttrs
        if not h or not '%s' in h: return h, cha
        h,opts = h.split(';',1)
        opts=opts.split(';')
        ckCount = N = 0
        for o in opts:
            chosen = self.getCookie("adjustCss" + str(ckCount) + "s", "")
            if not chosen:
                # we don't have all the necessary cookies to choose a stylesheet, so don't have one (TODO: or do we just want to go to the first listed?)
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
                ckVal = S(ckVal)
                self.setCookie_with_dots(ckName+"="+ckVal) # TODO: do we ever need to quote() ckVal ?  (document to be careful when configuring?)
                self.setCookie(ckName,ckVal) # pretend it was already set on THIS request as well (for 'Try' button; URL should be OK as it redirects)
            ckCount += 1
    
    def serve_URLbox(self):
        if not options.wildcard_dns: self.clearUnrecognisedCookies() # TODO: optional?
        self.addCookieFromURL()
        r = urlbox_html(self.htmlOnlyMode() or self.checkBrowser(["Lynx/"]),self.cssOptionsHtml(),self.getArg("q") or self.getArg("d"))
        self.doResponse2(r,True,False) # TODO: run htmlFilter on it also? (render etc will be done by doResponse2)

    def serve_hostError(self):
        l = []
        if options.wildcard_dns: l.append("prefixing its domain with the one you want to adjust")
        if options.real_proxy: l.append("setting it as a <b>proxy</b>")
        if l: err="This adjuster can be used only by "+", or ".join(l)+"."
        else: err="This adjuster cannot be used. Check the configuration."
        self.doResponse2(htmlhead()+err+'</body></html>',True,False) # TODO: run htmlFilter on it also? (render etc will be done by doResponse2)

    def serve_mailtoPage(self):
        ua = S(self.request.headers.get("User-Agent",""))
        if any(re.search(x,ua) for x in options.prohibitUA): return self.serveRobots()
        uri = S(self.request.uri)[len(options.mailtoPath):].replace('%%+','%') # we encode % as %%+ to stop browsers and transcoders from arbitrarily decoding e.g. %26 to &
        if '?' in uri:
            addr,rest = uri.split('?',1)
            self.request.arguments = urlparse.parse_qs(rest) # after the above decoding of %'s
        else: addr=uri
        addr = unquote(addr)
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
                smsLink = B('<br><a href="sms:'+sep+'body=')+quote(rm_u8punc(B(smsLink)))+B('">Send as SMS (text message)</a>')
                if self.checkBrowser(["Windows Mobile"]):
                    # TODO: others? configurable?
                    # browsers that may also have this problem with EMAIL
                    uri = uri.replace("%26","%20-amp-%20")
                    if not "body=" in uri: uri += "&body="
                    uri = uri.replace("body=","body=[Before%20sending%20this%20text,%20replace%20-amp-%20with%20an%20ampersand.%20This%20substitution%20has%20been%20done%20as%20your%20phone%20isn't%20compliant%20with%20RFC%205724.]%20")
        if len(r)==1: # different format if only 1 item is specified
            if addr: r=["The email will be sent to "+ampEncode(addr)]
            elif subj: r=["The email's Subject will be: "+ampEncode(subj)]
            else: r=["The email's Body will be: "+ampEncode(body)]
        elif not r: r.append("The link does not specify any recognised email details")
        else: r.insert(0,"The following information will be sent to the email client:")
        self.doResponse2(('%s<h3>mailto: link</h3>This link is meant to open an email client.<br>%s<br><a href=\"mailto:%s\">Open in email client</a> (if set up)%s%s<hr>This is %s</body></html>' % (htmlhead("mailto: link - Web Adjuster"),"<br>".join(r),uri,S(smsLink),backScript,serverName_html)),True,False)

    def serve_submitPage(self):
        self.request.suppress_logger_host_convert = True
        if B(self.request.uri)==B("/favicon.ico") or any(re.search(x,self.request.headers.get("User-Agent","")) for x in options.prohibitUA):
            # avoid logging favicon.ico tracebacks when submitPath=="/"
            self.set_status(400) ; self.myfinish() ; return
        if len(self.request.uri) > len(options.submitPath):
            txt = S(self.request.uri[len(options.submitPath):])
            if len(txt)==2 and options.submitBookmarklet:
                filterNo = ord(txt[1])-ord('A')
                if txt[0] in 'bB': return self.serve_bookmarklet_code(txt[1],txt[0]=='B')
                elif txt[0]=='j': return self.serve_bookmarklet_json(filterNo)
                elif txt[0]=='u': return self.serve_backend_post(filterNo)
                elif txt[0] in 'iap':
                    return self.doResponse2(android_ios_instructions(txt[0],self.request.host,self.request.headers.get("User-Agent",""),filterNo),"noFilterOptions",False) # on Android and iOS, 'def bookmarklet' gives instruction_url#javascript:bookmarklet_code, so serve instructions here
            txt = zlib.decompressobj().decompress(base64.b64decode(txt),16834) # limit to 16k to avoid zip bombs (limit is also in the compress below)
            self.request.uri = "%s (input not logged, len=%d)" % (options.submitPath,len(txt))
        else: txt = self.request.arguments.get("i",None)
        if not txt:
            self.is_password_domain=True # no prominentNotice needed
            # In the markup below, body's height=100% is needed to ensure we can set a percentage height on the textarea consistently across many browsers (otherwise e.g. Safari 6 without user CSS might start making the textarea larger as soon as it contains input, overprinting the rest of the document)
            local_submit_url = options.urlscheme+self.request.host+options.submitPath
            if options.submitBookmarkletDomain: submit_url = "//"+options.submitBookmarkletDomain+options.submitPath # assume submitBookmarkletDomain can take both http and https, that's the point of the option
            else: submit_url = local_submit_url
            if (options.password and submitPathIgnorePassword) or options.submitPath=='/' or defaultSite(): urlbox_footer = "" # not much point linking them back to the URL box under the first circumstance, and there isn't one for the other two
            else: urlbox_footer = '<p><a href="'+options.urlscheme+hostSuffix()+publicPortStr()+options.urlboxPath+'">Process a website</a></p>'
            # TODO: what if their browser doesn't submit in the correct charset?  for example some versions of Lynx need -display_charset=UTF-8 otherwise they might double-encode pasted-in UTF-8 and remove A0 bytes even though it appears to display correctly (and no, adding accept-charset won't help: that's for if the one to be accepted differs from the document's)
            return self.doResponse2(("""%s<body style="height:100%%;overflow:auto"><form method="post" action="%s"><h3>%s</h3>%s:<p><span style="float:right"><input type="submit" value="%s"><script><!--
document.write(' (Ctrl-Enter) | <a href="javascript:history.go(-1)">Back</a>')
//-->
</script></span><br><textarea name="i" style="width:100%%;clear:both;height:60%%" rows="5" cols="20" placeholder="Type or paste your text here"
onKeyDown="if((event.ctrlKey||event.metaKey) && (event.keyCode==13 || event.which==13)) document.forms[0].submit(); else return true;">
</textarea></form>%s<script><!--
document.forms[0].i.focus()
//-->
</script></body></html>""" % (htmlhead("%s - Web Adjuster" % options.submitPromptTitle).replace("<body>",""),options.submitPath,options.submitPromptTitle,options.submitPrompt,options.submitPromptAction,bookmarklet(submit_url,local_submit_url,options.submitBookmarkletDomain and self.willRejectLetsEncryptOct2021())+urlbox_footer)),"noFilterOptions",False)
        if type(txt) == list: # came from the POST form
            txt = txt[0].strip()
            # On at least some browsers (e.g. some Safari versions), clicking one of our JS reload links after the POST text has been shown will reload the form (instead of re-submitting the POST text) and can scroll to an awkward position whether the code below calls focus() or not.  Could at least translate to GET if it's short enough (don't want to start storing things on the adjuster machine - that would require a shared database if load-balancing)
            if len(txt) <= 16384: # (else we wouldn't decompress all; see comment above)
                enc = base64.b64encode(zlib.compress(B(txt),9))
                if 0 < len(enc) < 2000: return self.redirect(B("http://")+B(hostSuffix())+B(publicPortStr())+B(options.submitPath)+B(enc),303) # POST to GET (http:// here is rewritten to // if possible by redirect())

        # pretend it was served by a remote site; go through everything including filters (TODO: could bypass most of doResponse instead of rigging it up like this; alternatively keep this as it shows how to feed data to doResponse)
        self.connection_header = None
        self.urlToFetch = "" # for js_process
        class H:
            def get(self,h,d):
                if h=="Content-Type": return "text/html; charset=utf-8"
                else: return d
            def get_all(self): return [("Content-Type","text/html; charset=utf-8")]
        if options.htmlUrl: line1 = "about:submitted\n"
        else: line1 = ""
        if options.htmlonly_tell_filter:
            line1=str(self.htmlOnlyMode())+"\n"+line1
        runFilterOnText(self,self.getHtmlFilter(),find_text_in_HTML(B(htmlhead("Uploaded Text - Web Adjuster"))+B("<h3>Your text</h3>")+B(txt2html(txt))+B("<hr>%s%s</body></html>" % (("This is %s. " % serverName_html) if options.identifyAdjusterOnUploadedText else "",backScriptNoBr))),lambda out,err:self.doResponse2(out,True,False),prefix=line1) # backScriptNoBr AFTER the server notice to save vertical space
    def serve_bookmarklet_code(self,xtra,forceSameWindow): # (forceSameWindow is used by the "plus" bookmarklets)
        self.add_header("Content-Type","application/javascript")
        self.add_header("Access-Control-Allow-Origin","*")
        if options.submitBookmarkletDomain: submit = "//"+options.submitBookmarkletDomain
        else: submit = "//"+self.request.host
        if self.canWriteBody(): self.write(B(bookmarkletMainScript(submit+options.submitPath+'j'+xtra,forceSameWindow)))
        self.myfinish()
    def serve_err(self,err):
        self.set_status(500)
        self.add_header("Content-Type","text/plain")
        logging.error("Bookmarklet error: "+S(err))
        # +' '+repr(self.request.body)
        if self.canWriteBody(): self.write(B(err))
        self.myfinish()
    def serve429(self,retrySecs=0):
        debuglog("serve429"+self.debugExtras())
        try: self.set_status(429,"Too many requests")
        except: self.set_status(429)
        if retrySecs: self.add_header("Retry-After",str(retrySecs))
        if self.canWriteBody(): self.write(B("Too many requests (HTTP 429)"))
        if not self.request.remote_ip in options.ipNoLog:
            try: f = " for "+S(self.urlToFetch)
            except: f = ""
            logging.error("Returning HTTP 429 (too many requests)"+f+" to "+S(self.request.remote_ip))
        self.request.suppress_logging = True
        self.myfinish()
    def serve_bookmarklet_json(self,filterNo):
        self.add_header("Access-Control-Allow-Origin","*")
        self.add_header("Access-Control-Allow-Headers","Content-Type")
        if not self.request.body:
            self.add_header("Content-Type","text/plain")
            self.add_header("Allow","POST") # some browsers send OPTIONS first before POSTing via XMLHttpRequest (TODO: check if OPTIONS really is the request method before sending this?)
            if self.canWriteBody(): self.write(B("OK"))
            return self.myfinish()
        try: l = json.loads(self.request.body)
        except: return self.serve_err("Bad JSON")
        for i in xrange(len(l)):
            if l[i]=='': l[i] = u'' # shouldn't get this (TODO: fix in bookmarkletMainScript? e.g. if submitBookmarkletFilterJS can match empty strings, or conversion to 'cnv' makes it empty, anything else?), but if we do, don't let it trip up the 'wrong data structure' below on Python 2
        if not (type(l)==list and all(((type(i)==unicode or (type(i)==str and all(ord(c)<0x80 for c in i))) and not chr(0) in i) for i in l)): return self.serve_err("Wrong data structure")
        codeTextList = []
        for i in l:
            codeTextList.append(B(chr(0)))
            if type(i)==bytes: codeTextList.append(i)
            else: codeTextList.append(i.encode('utf-8'))
        def callback(out,err):
            self.add_header("Content-Type","application/json")
            if self.canWriteBody(): self.write(B(json.dumps([i.decode('utf-8','replace') for i in B(out)[1:].split(B(chr(0)))]))) # 'replace' here because we don't want utf-8 errors to time-out the entire request (although hopefully the filter WON'T produce utf-8 errors...)
            self.finish()
        if options.htmlUrl: line1 = "about:bookmarklet\n" # TODO: get the bookmarklet to report the location.href of the site (and update htmlUrl help text)
        else: line1 = ""
        if options.htmlonly_tell_filter:
            line1=str(self.htmlOnlyMode())+"\n"+line1
        runFilterOnText(self,self.getHtmlFilter(filterNo),codeTextList,callback,prefix=line1)
    def serve_backend_post(self,filterNo):
        # for another instance's htmlFilter=http://...uA etc
        runFilter(self.getHtmlFilter(filterNo),self.request.body,lambda out,err: (self.write(B(out)),self.finish()))

    def checkTextCache(self,newext):
        # check for PDF/EPUB conversion on other threads or cached
        if not options.pdfepubkeep: return False # we don't guarantee to update kept_tempfiles properly if it's 0 (e.g. pdf can just pipe, so don't need unlinkOutputLater)
        ktkey = (self.request.host, self.request.uri)
        if ktkey in kept_tempfiles:
            def tryRead():
                try: txt=open(kept_tempfiles[ktkey],'rb').read() # ('rb' makes it give you a byte-string in Python 3)
                except: txt = None
                if txt:
                    if self.canWriteBody():
                        if newext==".mobi": self.write(txt)
                        else: self.write(remove_blanks_add_utf8_BOM(txt))
                    self.myfinish()
                elif not self.inProgress(): IOLoopInstance().add_timeout(time.time()+1,lambda *args:tryRead())
            tryRead() ; return True
        kept_tempfiles[ktkey] = 1 # conversion in progress
        return False

    def getArg(self,arg):
        a = self.request.arguments.get(arg,None)
        if type(a)==type([]): a=a[0]
        return a

    def debugExtras(self):
        r = " for "+self.request.method+" "+self.request.uri
        if not self.request.uri.startswith("http"):
            r += " host="+str(self.request.host)
        if self.WA_UseSSL or (hasattr(self.request,"connection") and hasattr(self.request.connection,"stream") and hasattr(self.request.connection.stream,"isFromSslHelper")): r += " WA_UseSSL"
        if self.isPjsUpstream: r += " isPjsUpstream instance "+str(self.WA_PjsIndex+self.WA_PjsStart)
        if self.isSslUpstream: r += " isSslUpstream"
        return r

    def canWriteBody(self): return not B(self.request.method) in [B("HEAD"),B("OPTIONS")] and not (hasattr(self,"_finished") and self._finished)

    def justMeCheck(self):
        # Ideally we should do this asynchronously, but as
        # it's only for the --just-me option and we assume a
        # local ident server, we can probably get away with:
        usr = None
        try:
            s = socket.socket()
            try: s.connect(('localhost',113))
            except:
                import pwd
                for l in getoutput("netstat -tpn").split("\n"):
                    l = l.split()
                    if len(l)>6 and l[3].endswith(":"+str(self.request.connection.stream.socket.getpeername()[1])) and l[5]=="ESTABLISHED" and "/" in l[6] and S(pwd.getpwuid(os.stat("/proc/"+l[6].split("/",1)[0]).st_uid).pw_name)==myUsername: return True
                logging.error("no ident server and couldn't confirm username with netstat: rejecting this connection")
                return
            s.send(B("%d, %d\r\n" % (self.request.connection.stream.socket.getpeername()[1], port_randomise.get(self.WA_port,self.WA_port))))
            usr = s.recv(1024).strip()
            if usr.split(B(':'))[-1]==B(myUsername): return True
            else: logging.error("ident server didn't confirm username: rejecting this connection")
        except Exception as e: logging.error("Trouble connecting to ident server (%s): rejecting this connection" % repr(e))
        self.set_status(401)
        if usr: self.write(B(usr+": "))
        self.write(B("Connection from wrong account (ident check failed)\n"))
        self.myfinish()

    def doReq(self):
        if options.just_me and not self.justMeCheck(): return
        if mainServerPaused and not self.isPjsUpstream and not self.isSslUpstream: return self.serve429()
        self.doReq0()
    def doReq0(self):
        debuglog("doReq"+self.debugExtras()) # MUST keep this debuglog call: it also sets profileIdle=False
        try: reqsInFlight.add(id(self)) # for profile
        except: pass # e.g. not options.profile
        try: del self._adjuster_cookies_
        except: pass
        if not self.isPjsUpstream and not self.isSslUpstream:
            try: origReqInFlight.add(id(self))
            except: pass # e.g. not options.profile
            if options.one_request_only:
                IOLoopInstance().handle_callback_exception = lambda *args:0 # Tornado 4 raises EBADF in accept_handler if you call server.stop() from a request handler, so disable its handle_callback_exception to reduce log clutter (TODO: handle other errors using the original exception handler if present?)
                mainServer.stop()
        if wsgi_mode and B(self.request.path)==B(quote(os.environ.get("SCRIPT_NAME","")+os.environ.get("PATH_INFO",""))) and 'SCRIPT_URL' in os.environ:
            # workaround for Tornado 2.x limitation when used with CGI and htaccess redirects
            self.request.uri = os.environ['SCRIPT_URL']
            qs = os.environ.get("QUERY_STRING","")
            if not qs: qs = os.environ.get("REDIRECT_QUERY_STRING","")
            if qs:
                self.request.uri += "?"+qs
                self.request.arguments = urlparse.parse_qs(qs)
            self.request.path = self.request.uri
        elif sys.version_info[0]==2:
            # HTTP/1.x headers are officially Latin-1 (but usually ASCII), and Tornado versions 2 through 4 decodes the Latin-1 and re-encodes it as UTF-8.  This can cause confusion, so let's emulate modern browsers and %-encode any non-ASCII URIs:
            try: self.request.uri = self.request.uri.decode('utf-8').encode('latin1')
            except: pass
        self.request.uri=re.sub("[^!-~]+",lambda m:quote(m.group()),S(self.request.uri))
        self.request.method = S(self.request.method)
        if self.request.host:
            self.request.host = S(self.request.host)
        else: self.request.host = ""
        if self.request.method=="HEAD": self.set_header("Content-Length","-1") # we don't yet the content length, so Tornado please don't add it!  (NB this is for HEAD only, not OPTIONS, which should have Content-Length 0 or some browsers time out) (TODO: in non-WSGI mode could call .flush() after writing headers (with callback param), then Content-Length won't be added on .finish())
        if self.request.headers.get("User-Agent","")=="ping":
            if self.request.uri=="/ping2": return self.answerPing(True)
            elif self.request.uri=="/ping": return self.answerPing(False)
        elif options.loadBalancer and B(self.request.headers.get("User-Agent",""))==B("") and self.request.uri=="/": return self.answer_load_balancer()
        self.find_real_IP() # must find real ip BEFORE forwarding to fasterServer, because might also be behind nginx etc
        if fasterServer_up:
            return self.forwardFor(options.fasterServer,"fasterServer")
        if self.forwardToOtherPid(): return
        if self.handleFullLocation(): return # if returns here, URL is invalid; if not, handleFullLocation has 'normalised' self.request.host and self.request.uri
        if self.isPjsUpstream:
            if options.js_UA:
                if options.js_UA.startswith("*"): self.request.headers["User-Agent"] = options.js_UA[1:]
            else: self.request.headers["User-Agent"] = webdriver_UA[self.WA_PjsIndex]
            if webdriver_AL[self.WA_PjsIndex]:
                self.request.headers["Accept-Language"] = webdriver_AL[self.WA_PjsIndex]
            webdriver_inProgress[self.WA_PjsIndex].add(self.request.uri)
        elif not self.isSslUpstream:
            if self.handleSpecificIPs(): return
            # TODO: Slow down heavy users by self.request.remote_ip ?
            try: extensionHandled = extensions.handle("http://"+self.request.host+self.request.uri,self) # regardless of whether we were actually called by http:// or https:// we send http:// to the extension for backward compatibility (after all SSL termination has definitely happened by now)
            except:
                self.request.suppress_logger_host_convert = True # counted as 'sort of handled' so we get the correct log entry after the exception
                raise
            if extensionHandled:
                self.request.suppress_logger_host_convert = True
                return self.myfinish()
            if cssReload_cookieSuffix and cssReload_cookieSuffix in self.request.uri:
                ruri,rest = self.request.uri.split(cssReload_cookieSuffix,1)
                self.setCookie_with_dots(rest)
                return self.redirect(ruri) # so can set another
        self.cookieViaURL = None
        if self.isPjsUpstream or self.isSslUpstream: realHost = self.request.host
        else: realHost = convert_to_real_host(self.request.host,self.cookie_host(checkReal=False)) # don't need checkReal if return value will be passed to convert_to_real_host anyway
        if type(realHost)==bytes and not bytes==str:
            realHost = S(realHost)
        isProxyRequest = self.isPjsUpstream or self.isSslUpstream or (options.real_proxy and realHost == self.request.host)
        if not isProxyRequest and not self.isPjsUpstream and not self.isSslUpstream and (self.request.host=="localhost" or self.request.host.startswith("localhost:")) and not "localhost" in options.host_suffix: return self.redirect("http://"+hostSuffix(0)+publicPortStr()+self.request.uri) # save confusion later (e.g. set 'HTML-only mode' cookie on 'localhost' but then redirect to host_suffix and cookie is lost) (http:// here is rewritten to // if possible by redirect()).  Bugfix 0.314: do not do this redirect if we're a real proxy for another server on localhost
        maybeRobots = (not self.isPjsUpstream and not self.isSslUpstream and not options.robots and self.request.uri=="/robots.txt")
        self.is_password_domain=False # needed by doResponse2
        if options.password and not options.real_proxy and not self.isPjsUpstream and not self.isSslUpstream:
          # whether or not open_proxy, because might still have password (perhaps on password_domain), anyway the doc for open_proxy says "allow running" not "run"
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
                return self.redirect("http://"+dedot(host[:-len(ohs)])+ohs+colPort+self.request.uri) # (http:// here is rewritten to // if possible by redirect())
          # Now OK to check authentication:
          if not self.authenticates_ok(host) and not (submitPathIgnorePassword and self.request.uri.startswith(submitPathForTest)):
              self.request.suppress_logger_host_convert = True
              if maybeRobots: return self.serveRobots()
              self.add_nocache_headers() # in case they try the exact same request again after authenticating (unlikely if they add &p=..., but they might come back to the other URL later, and refresh is particularly awkward if we redirect)
              if re.match("https?://",options.auth_error): return self.redirect(options.auth_error)
              if options.auth_error.startswith("*"): auth_error = options.auth_error[1:]
              else:
                  self.set_status(401)
                  auth_error = options.auth_error
              if self.canWriteBody(): self.write(B(htmlhead("")+auth_error+"</body></html>"))
              return self.myfinish()
        # Authentication is now OK
        fixServerHeader(self)
        if not self.isPjsUpstream and not self.isSslUpstream:
          if self.handleGoAway(realHost,maybeRobots): return
          # Now check if it's an image request:
          _olduri = self.request.uri
          self.request.uri=unquote(self.request.uri)
          img = Renderer.getImage(self.request.uri)
          if img: return self.serveImage(img)
          # Not an image:
          if options.mailtoPath and self.request.uri.startswith(options.mailtoPath): return self.serve_mailtoPage()
          if options.submitPath and self.request.uri.startswith(submitPathForTest): return self.serve_submitPage()
          self.request.uri = _olduri
        if realHost=="error" and not maybeRobots:
            return self.serve_hostError()
        if not realHost: # default_site(s) not set
            if maybeRobots or any(re.search(x,self.request.headers.get("User-Agent","")) for x in options.prohibitUA): return self.serveRobots()
            # Serve URL box
            self.set_css_from_urlbox()
            if self.getArg("try"): return self.serve_URLbox() # we just set the stylesheet
            if options.submitPath and self.getArg("sPath"): return self.redirect("http://"+hostSuffix()+publicPortStr()+options.submitPath) # http:// here is rewritten to // if possible by redirect()
            v=self.getArg("q")
            if v: return self.handle_URLbox_query(v)
            else: return self.serve_URLbox()
        if maybeRobots: return self.serveRobots()
        viewSource = (not self.isPjsUpstream and not self.isSslUpstream) and self.checkViewsource()
        if not self.isPjsUpstream and not self.isSslUpstream and self.needCssCookies():
            self.add_nocache_headers() # please don't cache this redirect!  otherwise user might not be able to leave the URL box after:
            return self.redirect("http://"+hostSuffix()+publicPortStr()+options.urlboxPath+"?d="+quote(protocolWithHost(realHost)+S(self.request.uri)),302) # (http:// here is rewritten to // if possible by redirect()) go to the URL box - need to set more options (and 302 not 301, or some browsers could cache it despite the above)
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
        if not isProxyRequest and (any(re.search(x,self.urlToFetch) for x in options.prohibit) or any(re.search(x,self.request.headers.get("User-Agent","")) for x in options.prohibitUA)):
            self.restore_request_headers()
            return self.redirect(self.urlToFetch)
        # TODO: consider adding "not self.request.headers.get('If-Modified-Since','')" to the below list of sendHead() conditions, in case any referer-denying servers decide it's OK to send out "not modified" replies even to the wrong referer (which they arguably shouldn't, and seem not to as of 2013-09, but if they did then adjuster might erroneously redirect the SECOND time a browser displays the image)
        def ext(u):
            u = S(u)
            if '?' in u:
                e = ext(u[:u.index('?')])
                if e: return e
            if not '.' in u: return
            e = u[u.rindex('.')+1:].lower()
            if not (e=="mp3" and options.bitrate and not options.askBitrate): return e
        if options.redirectFiles and not (isProxyRequest or any(converterFlags) or viewSource) and ext(self.request.uri) in redirectFiles_Extensions: self.sendHead()
        elif self.isPjsUpstream and "text/html" in self.request.headers.get("Accept","") and not (any(converterFlags) or viewSource): self.sendHead(forPjs=True) # to check it's not a download link
        else: self.sendRequest(converterFlags,viewSource,isProxyRequest,follow_redirects=False) # (DON'T follow redirects - browser needs to know about them!)
    
    def change_request_headers(self,realHost,isProxyRequest):
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
                if not isProxyRequest: v = fixDNS(v,self)
                if enable_adjustDomainCookieName_URL_override: v = re.sub(B("[?&]"+re.escape(adjust_domain_cookieName)+"=[^&]*$"),B(""),B(v))
                if S(v) in ["","http://","http:///"]:
                    # it must have come from the URL box
                    del self.request.headers["Referer"]
                else: self.request.headers["Referer"] = S(v)
        for http in ["http://","http%3A%2F%2F"]: # xyz?q=http://... stuff
          if http in self.request.uri[1:]:
            u=self.request.uri.split(http)
            if not isProxyRequest:
                for i in range(1,len(u)):
                    u[i]=S(fixDNS(http+u[i],self))
            self.request.uri="".join(u)
        self.removed_headers = []
        for h in rmClientHeaders:
            l = self.request.headers.get_list(h)
            if l:
                del self.request.headers[h]
                self.removed_headers.append((h,l[0]))
        self.request.headers["Host"]=realHost
        if options.via and not self.isSslUpstream:
            v = S(self.request.version)
            if v.startswith("HTTP/"): v=v[5:]
            self.addToHeader("Via",v+" "+convert_to_via_host(self.request.host)+" ("+viaName+")")
            self.addToHeader("X-Forwarded-For",self.request.remote_ip)
        if options.uavia and not self.isSslUpstream: self.addToHeader("User-Agent","via "+convert_to_via_host(self.request.host)+" ("+viaName+")")
        if self.checkBrowser(options.cacheOmit):
            self.request.headers["Cache-Control"] = "max-age=0, must-revalidate"
            self.request.headers["Pragma"] = "no-cache"
    def restore_request_headers(self): # restore the ones Tornado might use (Connection etc)
        if not hasattr(self,"removed_headers"): return # haven't called change_request_headers (probably means this is user input)
        for k,v in self.removed_headers: self.request.headers[k]=v
        if hasattr(self.request,"old_cookie"): self.request.headers["Cookie"] = self.request.old_cookie # + put this back so we can refer to our own cookies
    
    def sendRequest(self,converterFlags,viewSource,isProxyRequest,follow_redirects):
        debuglog("sendRequest"+self.debugExtras())
        if self.isPjsUpstream and webdriver_prefetched[self.WA_PjsIndex]:
            debuglog("sendRequest returning webdriver_prefetched["+str(self.WA_PjsIndex)+"] ("+repr(webdriver_prefetched[self.WA_PjsIndex])+")"+self.debugExtras())
            r = webdriver_prefetched[self.WA_PjsIndex]
            webdriver_prefetched[self.WA_PjsIndex] = None
            return self.doResponse(r,converterFlags,viewSource,isProxyRequest)
        body = self.request.body
        if not body: body = None # required by some Tornado versions
        if self.isSslUpstream: ph,pp = None,None
        else: ph,pp = upstream_proxy_host,upstream_proxy_port
        if options.js_interpreter and self.htmlOnlyMode(isProxyRequest) and not follow_redirects and not self.request.uri in ["/favicon.ico","/robots.txt"] and self.canWriteBody():
            if options.via: via = self.request.headers["Via"],self.request.headers["X-Forwarded-For"]
            else: via = None # they might not be defined
            ua = self.request.headers.get("User-Agent","")
            acceptLang = self.request.headers.get("Accept-Language","")
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
                return self.serve429(retrySecs=10*len(webdriver_queue)/options.js_instances) # TODO: increase this if multiple clients?
            if options.js_reproxy and options.js_prefetch:
              def prefetch():
                # prefetch the page, don't tie up a browser until
                # we have the page in hand
                debuglog("prefetch "+self.urlToFetch)
                httpfetch(self,self.urlToFetch,
                  connect_timeout=60,request_timeout=120, # Tornado's default is usually something like 20 seconds each; be more generous to slow servers (TODO: customise?  TODO: Tornado 6 sometimes logs "timeout in request queue" as well as "timeout while connecting", are we exceeding max_clients? but we set maxCurls amply; is it somehow using SimpleAsyncHTTPClient instead, which contains the "in request queue" string?  but curl is set up in preprocessOptions, which runs before openPortsEtc / start_multicore)
                  proxy_host=ph, proxy_port=pp,
                  # TODO: use_gzip=enable_gzip, # but will need to retry without it if it fails
                  method=self.request.method,
                  allow_nonstandard_methods=True,
                  headers=self.request.headers, body=B(body),
                  validate_cert=False,
                  callback=lambda prefetched_response:
                    (debuglog("Calling webdriver_fetch from prefetch callback: "+self.urlToFetch),
                    webdriver_fetch(self.urlToFetch,
                                    prefetched_response,ua,
                                    acceptLang,
                        clickElementID, clickLinkText,
                        via,viewSource=="screenshot",
                        lambda r:self.doResponse(r,converterFlags,viewSource==True,isProxyRequest,js=True),tooLate)),
                  follow_redirects=False)
              def prefetch_when_ready(t0):
                if len(webdriver_queue) < 2*options.js_instances: return prefetch()
                # If too many browser instances already tied up,
                # don't start the prefetch yet
                again = time.time()+1 # TODO: in extreme cases this can result in hundreds or thousands of calls to prefetch_when_ready per second; need a second queue? (tooLate() should mitigate it if client goes away, + won't get here unless --js_429=False)
                global last_Qoverload_time, Qoverload_max
                try: last_Qoverload_time
                except: last_Qoverload_time=Qoverload_max=0
                Qoverload_max = max(Qoverload_max,again-t0)
                if time.time() > last_Qoverload_time + 5:
                    logging.error("webdriver_queue overload (max prefetch delay %d secs)" % Qoverload_max)
                    last_Qoverload_time = time.time()
                if not tooLate(): IOLoopInstance().add_timeout(again,lambda *args:prefetch_when_ready(t0))
              prefetch_when_ready(time.time())
            else: # no reproxy: can't prefetch (or it's turned off)
                webdriver_fetch(self.urlToFetch,None,ua,
                                acceptLang,
                        clickElementID, clickLinkText,
                        via,viewSource=="screenshot",
                        lambda r:self.doResponse(r,converterFlags,viewSource==True,isProxyRequest,js=True),tooLate)
        else:
            if options.js_interpreter and self.isPjsUpstream and webdriver_via[self.WA_PjsIndex]: self.request.headers["Via"],self.request.headers["X-Forwarded-For"] = webdriver_via[self.WA_PjsIndex]
            httpfetch(self,self.urlToFetch,
                  connect_timeout=60,request_timeout=120, # same TODO as above
                  proxy_host=ph, proxy_port=pp,
                  use_gzip=enable_gzip and not hasattr(self,"avoid_gzip"),
                  method=self.request.method, headers=self.request.headers, body=B(body),
                  allow_nonstandard_methods=True, # (e.g. POST with empty body)
                  validate_cert=False, # TODO: options.validate_certs ? but (1) there's little point unless you also secure your connection to the adjuster (or run it on localhost), (2) we haven't sorted out how to gracefully return if the validation fails, (3) True will cause failure if we're on a VM/container without a decent root-certs configuration
                  callback=lambda r:self.doResponse(r,converterFlags,viewSource,isProxyRequest),follow_redirects=follow_redirects)
        # (Don't have to worry about auth_username/auth_password: should just work by passing on the headers)
        # TODO: header_callback (run with each header line as it is received, and headers will be empty in the final response); streaming_callback (run with each chunk of data as it is received, and body and buffer will be empty in the final response), but how to abort a partial transfer if we realise we don't want it (e.g. large file we don't want to modify on site that doesn't mind client being redirected there directly)

    def doResponse(self,response,converterFlags,viewSource,isProxyRequest,js=False):
        curlFinished()
        debuglog("doResponse"+self.debugExtras()+" isProxyRequest="+repr(isProxyRequest))
        self.restore_request_headers()
        if hasattr(self,"_finished") and self._finished: return # client has gone away anyway: no point trying to process this (probably a timeout)
        do_pdftotext,do_epubtotext,do_epubtozip,do_mp3 = converterFlags
        do_domain_process = do_html_process = do_js_process = True
        do_json_process = do_css_process = False
        charset = "utf-8" # by default
        if not hasattr(response,"code") or not response.code or response.code==599:
            # (some Tornado versions don't like us copying a 599 response without adding our own Reason code; just making it a 504 for now)
            try: error = str(response.error)
            except: error = str(response)
            if "incorrect data check" in error and not hasattr(self,"avoid_gzip") and enable_gzip:
                # Some versions of the GWAN server can send NUL bytes at the end of gzip data.  Retry without requesting gzip.
                self.avoid_gzip = True
                return self.sendRequest(converterFlags,viewSource,isProxyRequest,False)
            tryFetch = self.urlToFetch
            if self.isSslUpstream: tryFetch += " (upstream of "+options.upstream_proxy+")"
            elif options.upstream_proxy: tryFetch += " via "+options.upstream_proxy
            if len(tryFetch) > 100: tryFetchTrunc = tryFetch[:60]+"..."
            else: tryFetchTrunc = tryFetch
            tryFetchTrunc = tryFetchTrunc.replace('\x1b','[ESC]') # terminal safe (in case of malformed URLs)
            logging.error(error+" when fetching "+tryFetchTrunc) # better log it for the admin, especially if options.upstream_proxy, because it might be an upstream proxy malfunction
            error = """%s<h1>Error</h1>%s<br>Was trying to fetch <a href="%s">%s</a><hr>This is %s</body></html>""" % (htmlhead("Error"),error,ampEncode(tryFetch),ampEncode(tryFetch),serverName_html)
            self.set_status(504)
            return self.doResponse2(error,True,False)
        if hasattr(response, "response"): # Tornado 6 errors can be wrapped
            if hasattr(response.response,"headers"):
                response.headers = response.response.headers
            if hasattr(response.response,"body"):
                response.body = response.response.body
        if not hasattr(response, "headers"): # HTTPError might not have them in Tornado 6
            debuglog("Creating blank headers on "+repr(type(response))+" "+repr(response)+" "+repr(dir(response))+self.debugExtras())
            class H(dict):
                def get_all(self): return []
            response.headers = H()
        if not hasattr(response, "body"): response.body = B("")
        if response.headers.get("Content-Encoding","")=="gzip": # sometimes Tornado's client doesn't decompress it for us, for some reason
            try: response.body = zlib.decompressobj().decompress(response.body,1048576*32) # 32M limit to avoid zip bombs (TODO adjust? what if exceeded?)
            except: pass
        if viewSource:
            def h2html(h): return "<br>".join("<b>"+txt2html(k)+"</b>: "+txt2html(v) for k,v in sorted(h.get_all()))
            r = "<html><head><title>Source of "+ampEncode(self.urlToFetch)+" - Web Adjuster</title></head><body>"
            if not js: r += "<a href=\"#1\">Headers sent</a> | <a href=\"#2\">Headers received</a> | <a href=\"#3\">Page source</a> | <a href=\"#4\">Bottom</a>"
            r += "<br>Fetched "+ampEncode(self.urlToFetch)
            if js:
                screenshot_url = self.urlToFetch + ".screenshot"
                if not options.urlboxPath=="/": screenshot_url = "//" + S(convert_to_requested_host(self.cookie_host(),self.cookie_host())) + options.urlboxPath + "?q=" + quote(screenshot_url) + "&" + adjust_domain_cookieName + "=0&pr=on"
                elif not isProxyRequest: screenshot_url = domain_process(screenshot_url,self.cookie_host(),https=self.urlToFetch.startswith("https"))
                r += " <ul><li>using %s (see <a href=\"%s\">screenshot</a>)</ul>" % (options.js_interpreter,screenshot_url)
            else: r += "<h2><a name=\"1\"></a>Headers sent</h2>"+h2html(self.request.headers)+"<a name=\"2\"></a><h2>Headers received</h2>"+h2html(response.headers)+"<a name=\"3\"></a>"
            return self.doResponse2(r+"<h2>Page source</h2>"+txt2html(S(response.body))+"<hr><a name=\"4\"></a>This is "+serverName_html,True,False)
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
                  ]: value=S(domain_process(value,cookie_host,True,https=self.urlToFetch.startswith("https"),isProxyRequest=isProxyRequest,isSslUpstream=self.isSslUpstream))
          elif name.lower()=="location": # TODO: do we need to delete this header if response.code not in [301,302,303,307] ?
            old_value_1 = value # before domain_process
            value=S(domain_process(value,cookie_host,True,https=self.urlToFetch.startswith("https"),isProxyRequest=isProxyRequest,isSslUpstream=self.isSslUpstream))
            absolute = re.match("(https?:)?//",value)
            offsite = (not isProxyRequest and value==old_value_1 and absolute) # i.e. domain_process didn't change it, and it's not relative
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
            if cookie_host and (self.request.path=="/" or self.request.arguments.get(adjust_domain_cookieName,None)) and old_value_1.startswith("http") and not (old_value_1.startswith("http://"+cookie_host+"/") or (cookie_host.endswith(".0") and old_value_1.startswith("https://"+cookie_host[:-2]+"/"))) and options.urlboxPath=="/":
                # This'll be a problem.  If the user is requesting / and the site's trying to redirect off-site, how do we know that the user isn't trying to get back to the URL box (having forgotten to clear the cookie) and now can't possibly do so because '/' always results in an off-site Location redirect ?
                # (DON'T just do this for just ANY offsite url when in cookie_host mode (except when also in htmlOnlyMode, see below) - it could mess up images and things.  (Could still mess up images etc if they're served from / with query parameters; for now we're assuming path=/ is a good condition to do this.  The whole cookie_host thing is a compromise anyway; wildcard_dns is better.)  Can however do it if adjust_domain_cookieName is in the arguments, since this should mean a URL has just been typed in.)
                if offsite:
                    # as cookie_host has been set, we know we CAN do this request if it were typed in directly....
                    value = "//" + S(convert_to_requested_host(cookie_host,cookie_host)) + options.urlboxPath + "?q=" + quote(old_value_1) + "&" + adjust_domain_cookieName + "=0" # go back to URL box and act as though this had been typed in
                    if self.htmlOnlyMode(isProxyRequest): value += "&pr=on"
                    reason = "" # "which will be adjusted here, but you have to read the code to understand why it's necessary to follow an extra link in this case :-("
                else: reason=" which will be adjusted at %s (not here)" % (value[value.index('//')+2:(value+"/").index('/',value.index('/')+2)],)
                return self.doResponse2(("<html lang=\"en\"><body>The server is redirecting you to <a href=\"%s\">%s</a>%s.</body></html>" % (value,old_value_1,reason)),True,False) # and 'Back to URL box' link will be added
            elif can_do_cookie_host() and (offsite or (absolute and not options.urlboxPath=="/")) and self.htmlOnlyMode(isProxyRequest) and not options.htmlonly_css and enable_adjustDomainCookieName_URL_override: # in HTML-only mode, it should never be an embedded image etc, so we should be able to change the current cookie domain unconditionally (TODO: can do this even if not enable_adjustDomainCookieName_URL_override, by issuing a Set-Cookie along with THIS response)
                debuglog("HTML-only mode cookie-domain redirect (isProxyRequest="+repr(isProxyRequest)+")"+self.debugExtras())
                value = "//" + S(convert_to_requested_host(cookie_host,cookie_host)) + options.urlboxPath + "?q=" + quote(old_value_1) + "&" + adjust_domain_cookieName + "=0&pr=on" # as above
            doRedirect = value
          elif "set-cookie" in name.lower():
            if not isProxyRequest: value=cookie_domain_process(value,cookie_host) # (never doing this if isProxyRequest, therefore don't have to worry about the upstream_rewrite_ssl exception that applies to normal domain_process isProxyRequest)
            for ckName in upstreamGuard: value=value.replace(ckName,ckName+"1")
            value0 = value
            if not options.urlscheme=="https://": value=re.sub("; *(Secure|SameSite[^;]*)(?=;|$)","",value) # (could also omit this if it's "//" if we can confirm we are https)
            if options.alt_dot and altdot_bad_cookie_leak and "domain=" in value0.lower(): value=re.sub("; *HttpOnly(?=;|$)","",value) # must be available to JS for altdot_bad_cookie_leak script to work
            if "samesite=none" in value0.lower() and not "domain=" in value0.lower() and options.wildcard_dns: self.setCookie_with_dots(value)
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
        if response.code >= 400 and response.body and B(response.body[:5]).lower()==B("<html"): # some content distribution networks are misconfigured to serve their permission error messages with the Content-Type and Content-Disposition headers of the original file, so the browser won't realise it's HTML to be displayed if you try to fetch the link directly.  This should work around it (but should rarely be needed now that headResponse() is also 'aware' of this problem for redirectFiles)
            for name,value in headers_to_add:
                if name=='Content-Type' and not 'text/html' in value:
                    headers_to_add.remove((name,value))
                    headers_to_add.append(('Content-Type','text/html'))
                elif name=='Content-Disposition':
                    headers_to_add.remove((name,value))
        if not self.isPjsUpstream and not self.isSslUpstream:
            if vary: vary += ", "
            vary += 'Cookie, User-Agent' # can affect adjuster settings (and just saying 'Vary: *' can sometimes be ignored on Android 4.4)
        if vary: headers_to_add.append(('Vary',vary))
        added = set(['set-cookie']) # might have been set by authenticates_ok (or samesite=none logic above etc) so use only add_header not set_header for this
        for name,value in headers_to_add:
          value = value.replace("\t"," ") # needed for some servers
          # self.add_header("X-Header-"+name,quote(value)) # for debugging if a frontend is deleting any of our HTTP headers
          try:
            if name.lower() in added:self.add_header(name,value)
            else: self.set_header(name,value) # overriding any Tornado default
            added.add(name.lower())
          except ValueError: pass # ignore unsafe header values
        if doRedirect:
            # ignore response.body and put our own in
            return self.redirect(doRedirect,response.code)
        body = B(response.body)
        if not body or not self.canWriteBody(): return self.myfinish() # TODO: if canWriteBody() but not body and it's not just a redirect, set type to text/html and report empty?
        if do_html_process:
            # Normalise the character set
            charset2, body = get_and_remove_httpequiv_charset(body)
            if charset2: charset=charset2 # override server header (TODO: is this always correct?)
            if charset=="gb2312": charset="gb18030" # 18030 is a superset of 2312, and some pages say 2312 for backward compatibility with old software when they're actually 18030 (most Chinese software treats both as equivalent, but not all Western software does)
            if not charset=="utf-8":
                try: "".decode(charset)
                except: charset="latin-1" # ?? (unrecognised charset name)
                body=body.decode(charset,'replace').encode('utf-8')
            if self.checkBrowser(options.zeroWidthDelete):
                body=body.replace(u"\u200b".encode('utf-8'),B("")) # U+200B zero-width space, sometimes used for word-wrapping purposes, but needs deleting for old browsers
                # TODO: what about &#8203; and &#x200b;
        if do_pdftotext or do_epubtotext:
            if do_epubtotext and self.isKindle():
                self.set_header("Content-Type","application/x-mobipocket-ebook")
                newext = ".mobi"
            else:
                self.set_header("Content-Type","text/plain; charset=utf-8")
                newext = ".txt"
            self.set_header("Content-Disposition","attachment; filename="+quote(self.request.uri[self.request.uri.rfind("/")+1:self.request.uri.rfind(".")]+newext))
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
                IOLoopInstance().add_timeout(time.time()+options.pdfepubkeep,lambda *args:(tryDel(k),unlink(fn)))
            def txtCallback(self,fn,cmdname,err):
                try: txt = open(fn+newext,'rb').read()
                except: # try to diagnose misconfiguration
                    # TODO: change Content-Type and Content-Disposition headers if newext==".mobi" ? (but what if it's served by ANOTHER request?)
                    txt = "Could not read %s's output from %s\n%s\n(This is %s)" % (cmdname,fn+newext,err,serverName)
                    try: open(fn+newext,"wb").write(txt) # must unconditionally leave a .txt file as there might be other requests waiting on cache
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
                if options.pdfepubkeep: runFilter(self,("pdftotext -enc UTF-8 -nopgbrk \"%s\" \"%s.txt\"" % (f.name,f.name)),"",(lambda out,err:txtCallback(self,f.name,"pdftotext",out+err)), False)
                elif self.canWriteBody(): runFilter(self,("pdftotext -enc UTF-8 -nopgbrk \"%s\" -" % f.name),"",(lambda out,err:(unlink(f.name),self.write(remove_blanks_add_utf8_BOM(out)),self.myfinish())), False) # (pipe o/p from pdftotext directly, no temp outfile needed)
                else: self.myfinish()
            elif self.isKindle(): runFilter(self,("ebook-convert \"%s\" \"%s.mobi\"" % (f.name,f.name)),"",(lambda out,err:txtCallback(self,f.name,"ebook-convert",out+err)), False)
            else: runFilter(self,("ebook-convert \"%s\" \"%s.txt\"" % (f.name,f.name)),"",(lambda out,err:txtCallback(self,f.name,"ebook-convert",out+err)), False)
            return
        if do_domain_process and not isProxyRequest: body = domain_process(body,cookie_host,https=B(self.urlToFetch).startswith(B("https"))) # first, so filters to run and scripts to add can mention new domains without these being redirected back
        # Must also do things like 'delete' BEFORE the filters, especially if lxml is in use and might change the code so the delete patterns aren't recognised.  But do JS process BEFORE delete, as might want to pick up on something that was there originally.  (Must do it AFTER domain process though.)
        if self.isPjsUpstream:
          if do_html_process:
            # add a CSS rule to help with js_interpreter screenshots (especially if the image-display program shows transparent as a headache-inducing chequer board) - this rule MUST go first for the cascade to work
            i = htmlFind(body,"<head")
            if i==-1: i=htmlFind(body,"<html")
            if not i==-1: i = body.find(B('>'),i)+1
            if i: body=body[:i]+B("<style>html{background:#fff}</style>")+body[i:] # setting on 'html' rather than 'body' allows body bgcolor= to override.  (body background= is not supported in HTML5 and PhantomJS will ignore it anyway.)
            if options.js_upstream: body = html_additions(body,(None,None),False,"","","",False,"","PjsUpstream",False,False,"") # just headAppend,bodyPrepend,bodyAppend (no css,ruby,render,UI etc, nor htmlFilter from below)
          if do_js_process and options.js_upstream: body = js_process(body,self.urlToFetch)
          return self.doResponse3(body) # write & finish
        elif self.isSslUpstream: return self.doResponse3(body)
        elif do_js_process and not options.js_upstream: body = js_process(body,self.urlToFetch)
        if not self.checkBrowser(options.deleteOmit):
            body = process_delete(body)
        if do_css_process:
            body = process_delete_css(body,self.urlToFetch)
        # OK to change the code now:
        adjustList = []
        if do_html_process:
          if self.htmlOnlyMode(isProxyRequest):
              if isProxyRequest: url = self.urlToFetch
              else: url = domain_process(self.urlToFetch,cookie_host,True,B(self.urlToFetch).startswith(B("https")))
              if cookie_host:
                  adjustList.append(RewriteExternalLinks("//" + S(convert_to_requested_host(cookie_host,cookie_host)) + options.urlboxPath + "?" + adjust_domain_cookieName+"=0&pr=on&q=",url,cookie_host))
              if options.js_links:
                  adjustList.append(AddClickCodes(url))
              adjustList.append(StripJSEtc(self.urlToFetch,transparent=self.auto_htmlOnlyMode(isProxyRequest)))
              if not options.htmlonly_css:
                  adjustList.append(transform_in_selected_tag("style",zapAllStrOrBytes,True)) # strips JS events also (TODO: support this in htmlonly_css ? although htmlonly_css is mostly a 'developer' option)
                  adjustList.append(AriaCopier())
          elif options.upstream_guard:
            # don't let upstream scripts get confused by our cookies (e.g. if the site is running Web Adjuster as well)
            # TODO: do it in script files also?
            if options.cssName: adjustList.append(transform_in_selected_tag("script",lambda s:replaceStrOrBytes(s,"adjustCssSwitch","adjustCssSwitch1")))
            if options.htmlFilterName: adjustList.append(transform_in_selected_tag("script",lambda s:replaceStrOrBytes(s,"adjustNoFilter","adjustNoFilter1")))
            if options.renderName: adjustList.append(transform_in_selected_tag("script",lambda s:replaceStrOrBytes(s,"adjustNoRender","adjustNoRender1")))
        if (options.pdftotext or options.epubtotext or options.epubtozip or options.askBitrate or options.mailtoPath) and (do_html_process or (do_json_process and options.htmlJson)) and not any(re.search(x,self.urlToFetch) for x in options.skipLinkCheck):
            # Add PDF links BEFORE the external filter, in case the external filter is broken and we have trouble parsing the result
            if do_html_process: adjustList.append(AddConversionLinks(options.wildcard_dns or isProxyRequest,self.isKindle()))
            else:
                ctl = find_HTML_in_JSON(body)
                for i in range(1,len(ctl),2):
                    ctl[i] = json_reEscape(add_conversion_links(ctl[i],options.wildcard_dns or isProxyRequest,self.isKindle()))
                body = B("").join(ctl)
        cssToAdd,attrsToAdd = self.cssAndAttrsToAdd()
        if cssToAdd:
          # remove !important from other stylesheets
          important = re.compile(B("! *important"))
          if (do_html_process or (do_css_process and not self.urlToFetch == cssToAdd and not (options.protectedCSS and re.search(options.protectedCSS,self.urlToFetch)))) and re.search(important,body):
            if do_css_process: body=re.sub(important,B(""),body)
            else: adjustList.append(transform_in_selected_tag("style",lambda s:zapStrOrBytes(s,"! *important"))) # (do_html_process must be True here)
        if adjustList: body = HTML_adjust_svc(body,adjustList)
        if options.prominentNotice=="htmlFilter": callback = lambda out,err: self.doResponse2(body,do_html_process,do_json_process,out)
        else: callback = lambda out,err:self.doResponse2(out,do_html_process,do_json_process)
        htmlFilter = self.getHtmlFilter()
        if options.htmlUrl: line1 = B(self.urlToFetch)+B("\n")
        else: line1 = B("")
        if options.htmlonly_tell_filter:
            line1=B(str(self.htmlOnlyMode())+"\n")+line1
        if do_html_process and htmlFilter:
            if options.htmlText: runFilterOnText(self,htmlFilter,find_text_in_HTML(body),callback,prefix=line1)
            else: runFilter(self,htmlFilter,line1+body,callback)
        elif do_json_process and options.htmlJson and htmlFilter:
            if options.htmlText: htmlFunc = find_text_in_HTML
            else: htmlFunc = None
            runFilterOnText(self,htmlFilter,find_HTML_in_JSON(body,htmlFunc),callback,True,prefix=line1)
        elif do_mp3 and options.bitrate:
            runFilter(self,"lame --quiet --mp3input -m m --abr %d - -o -" % options.bitrate,body,callback,False) # -m m = mono (TODO: optional?)
        else: callback(body,"")
    def getHtmlFilter(self,filterNo=None):
        return findFilter(self,filterNo)
    def doResponse2(self,body,do_html_process,do_json_process,htmlFilterOutput=None):
        debuglog("doResponse2"+self.debugExtras())
        # 2nd stage (domain change and external filter
        # has been run) - now add scripts etc, and render
        canRender = options.render and (do_html_process or (do_json_process and options.htmlJson)) and not self.checkBrowser(options.renderOmit)
        jsCookieString = ';'.join(self.request.headers.get_list("Cookie"))
        body = B(body)
        if do_html_process: body = html_additions(body,self.cssAndAttrsToAdd(),self.checkBrowser(options.cssNameReload),self.cookieDomainsToSet(";domain="),self.urlBoxHost(),jsCookieString,canRender,self.cookie_host(),self.is_password_domain,self.checkBrowser(["Edge/"]),not do_html_process=="noFilterOptions",htmlFilterOutput) # noFilterOptions is used by bookmarklet code (to avoid confusion between filter options on current screen versus bookmarklets)
        if canRender and not "adjustNoRender=1" in jsCookieString:
            if do_html_process: func = find_text_in_HTML
            else: func=lambda body:find_HTML_in_JSON(body,find_text_in_HTML)
            debuglog("runFilterOnText Renderer"+self.debugExtras())
            runFilterOnText(self,lambda t:Renderer.getMarkup(ampDecode(t.decode('utf-8'))).encode('utf-8'),func(body),lambda out,err:self.doResponse3(out),not do_html_process,chr(0))
        else: self.doResponse3(body)
    def doResponse3(self,body):
        # 3rd stage (rendering has been done)
        debuglog(("doResponse3 (len=%d)" % len(body))+self.debugExtras())
        if self.canWriteBody(): self.write(B(body))
        self.myfinish()
    def sendHead(self,forPjs=False):
        # forPjs is for options.js_reproxy: we've identified the request as coming from js_interpreter and being its main document (not images etc).  Just check it's not a download link.
        # else for options.redirectFiles: it looks like we have a "no processing necessary" request that we can tell the browser to get from the real site.  But just confirm it's not a mis-named HTML document.
        if forPjs and webdriver_prefetched[self.WA_PjsIndex]:
            # no need to send a separate HEAD request if we've already done a prefetch
            debuglog("sendHead using prefetched head"+self.debugExtras())
            return self.headResponse(webdriver_prefetched[self.WA_PjsIndex],True)
        debuglog("sendHead"+self.debugExtras())
        body = B(self.request.body)
        if not body: body = None
        if hasattr(self,"original_referer"): self.request.headers["Referer"],self.original_referer = self.original_referer,self.request.headers.get("Referer","") # we'll send the request with the user's original Referer, to check it still works
        ph,pp = upstream_proxy_host, upstream_proxy_port
        httpfetch(self,self.urlToFetch,
                  connect_timeout=60,request_timeout=120, # same TODO as above
                  proxy_host=ph, proxy_port=pp,
                  method="HEAD", headers=self.request.headers, body=body,
                  callback=lambda r:self.headResponse(r,forPjs),follow_redirects=not forPjs)
    def headResponse(self,response,forPjs):
        try: response.code
        except Exception as e: response = wrapResponse(str(response))
        debuglog("headResponse "+repr(response.code)+self.debugExtras())
        if hasattr(response, "response"): # Tornado 6 errors can be wrapped
            if hasattr(response.response,"headers"):
                response.headers = response.response.headers
            if hasattr(response.response,"body"):
                response.body = response.response.body
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
            if self.canWriteBody(): self.write(B(htmlhead()+"js_interpreter cannot load "+ampEncode(self.urlToFetch)+" as "+reason+"</body></html>")) # TODO: provide a direct link if the original request wasn't a proxy request?  (or even if it was a proxy request, give webdriver a placeholder (so it can still handle cookies etc) and bypass it with the actual response body?  but don't expect to load non-HTML files via PhantomJS: its currentUrl will be unchanged, sometimes from about:blank)
            self.myfinish() ; return
        might_need_processing_after_all = True
        if response.code < 400: # this 'if' is a workaround for content-distribution networks that misconfigure their servers to serve Referrer Denied messages as HTML without changing the Content-Type from the original file: if the code is >=400 then assume might_need_processing_after_all is True no matter what the Content-Type is
         for name,value in response.headers.get_all():
          if name.lower()=="content-type":
            value=S(value.lower())
            might_need_processing_after_all = ("html" in value or "css" in value or "javascript" in value or "json" in value or "rss+xml" in value) # these need at least domain processing
        # TODO: what if browser sent If-Modified-Since and it returned 304 Not Modified, which has no Content-Type?  (I suppose 200 w/out Content Type should assume HTML.)  If 304, we currently perform a fetch and log it, which seems a bit silly (although this shouldn't happen unless we previously proxied the file anyway)
        if might_need_processing_after_all: self.sendRequest([False]*4,False,False,follow_redirects=False)
        else:
            if not options.logRedirectFiles: self.request.suppress_logging = True
            self.redirect(self.urlToFetch)
    def isKindle(self): return options.epubtotext and self.checkBrowser(["Kindle"]) and self.checkBrowser(["Linux"]) # (don't do it if epubtotext is false as might want epubtozip links only; TODO: some reports say Kindle Fire in Silk mode doesn't mention "Kindle" in user-agent)
    def willRejectLetsEncryptOct2021(self): # https://letsencrypt.org/docs/dst-root-ca-x3-expiration-september-2021/
        # Firefox 45: SEC_ERROR_EXPIRED_ISSUER_CERTIFICATE
        # Mac OS 10.7, Chromium 49: NET::ERR_CERT_DATE_INVALID
        if not options.letsEncryptWarning: return False
        ua = S(self.request.headers.get("User-Agent",""))
        ffx = re.search("Firefox/([1-9][0-9]*)",ua)
        if ffx and int(ffx.group(1))<50: return True
        osx = re.search("Mac OS X 10[._]([0-9]+([._][0-9]+)?)",ua)
        if osx and float(osx.group(1).replace('_','.')) < 12.1: return True
        return re.search("OS [1-9]_.*like Mac OS X",ua) # iOS before 10
    def checkBrowser(self,blist,warn="{B}"):
        assert type(blist)==list # (if it's a string we don't know if we should check for just that string or if we should .split() it on something)
        ua = S(self.request.headers.get("User-Agent",""))
        for b in blist:
            if S(b) in ua: return warn.replace("{B}",S(b))
        return ""

#@file: ssl-certs.py
# --------------------------------------------------
# Self-signed SSL certificates for SSL interception
# --------------------------------------------------

def writable_tmpdir():
    "Returns a writeable temporary directory for small files. Prefers /dev/shm on systems that have it."
    global the_writable_tmpdir
    try: return the_writable_tmpdir
    except:
      for n in ['/dev/shm/','/tmp/','./']:
        try:
            open(n+".test0",'w')
            unlink(n+".test0")
            return n
        except: continue
      raise Exception("Can't find a writeable temporary directory")
def duff_certfile():
    global the_duff_certfile
    try: return the_duff_certfile # (we shouldn't need to worry about it having been deleted by /tmp reaping, because we're called only twice at start)
    except:
        # Here's one I made earlier with 'openssl req',
        # TODO: it will expire in 2038 (S2G problem) - might or might not be relevant when asking browsers to ignore self-signed anyway
        the_duff_certfile = writable_tmpdir()+"placeholder.pem"
        open(the_duff_certfile,'w').write("""-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC1XEMV7CQYkJcu
+x7TkOL5EOeIajC3Fs2PepT6X45UkEC3Z63Gx+cXIPKWENPO6ePIMXIRCodVkKid
K2bTdlAzZvJCiml1mYUqkAEg75JjZwCiIeV7Sym2++/3WVaXynnFYyLILIKawMyq
NnjkdifiJ8HbRrPDw9vBCIWtBMv2WKft5YrYYJXztI9/xVDFz/Oq2wCIwKTxx2KP
zQMBfOPLkKfsk3Qc86e/5L32cToi/YxtgSbs2W7gWXN2GUDFGHnZtNZQsr1PXI2c
TG49pUQOr4kEDbaENWkbJgBaxLyJQyDHy+X0b8+58jNPSizeFcvgwaDALIZZvr49
1EyceV+XAgMBAAECggEAQIIrvo17HV242NYr1dcQVMVFhck3wLgUr/dLLG92we95
hYMUVcNfGGP4xZYAsPWStu+XgiY7kxzcTONWNNs9lbsFatOuxUyxCD2mmR9982t8
1y61YJCQquycI2Aco+s6OxKTGZ5zajYv1k9/2suITjIUCznv0S9GaDfuzGcLYXj4
F/Ht+OL8W3vHUK5+zY4s4iOKbXSqh5nr+mQNXbvRX6p017xmx8hGY5XLHlcfy9yX
qCrsJkXEvC0HOmn1/A256JuvFLBri4HqWc8GR8aIgwSWNpqy51qYWyj0/gxtWwoC
NGj5l72BFADYoX6RGZit9xKWVpExn5vGTv7onTABSQKBgQDcNxeZkbF3nGFKx5D2
8pURqPzuwESgc6pbYLpj6m5SX1SM4/tmyAmvYPXIZb7IljWMIOropcGKbqVdh7mu
3s/8BEtd77524gVMj/u5VizaR2/SbMiwT6J9tGoHu44tUs4EQSGxA8FwDV3U5B0N
ypxZhInk1bo6GZ4EuiGl/olOwwKBgQDS1NFeqIL6u4Xi65ogTRjKQsm8VSxMwDg+
9Sz1dFMSfPvuuvW+i5TY6LuZlwq8ojPnbX5PZXszs5CTnVXj9Nkwo05N6E/lFYCR
2GN2fCr59ENE066naJ9xL5zKsgVEnkbXgswY1ytF+IgP5OA9xNAtCLGpebYFeVyA
EghK1C6GnQKBgEkS0vb3nI8XSkWZMWZwmrywebX0ARHJL+eAknkjSpZ04caaxEqX
6HbU0to7wPIovf4Q0kJ+9lksXB1MM3Zuo096UVQLgQVL/Pwp7xrSGLIZ8GZACNxQ
oJfb7S9Bsm0hxBEvV7G4kFDRbqh9RZLU/8rIq0VPEqvC4mepKA9ABmonAoGATPkE
A7I0N8R1CjcIS1i6f0XJD2htRww6vMmYg3jXx304IZ3CkLG3Q0YdD+M0OVBi8NBp
+CTNyT96vloH/LTtArPsp8b0PGgQS68cCSsmKaHDWYKLVnV9GL7QWLSL9dRvesk3
KK6ODvrA+kSOlh6f/oEZFA3qpa78VYm/20oCPoUCgYBLogwyMK6S7PBnOL/xNOM8
8ZnOusqp6OE7s+p0c9KqrqK1jwM+iDFzrfMopuMBx0trymp2aTWNF8KEujwAknZz
41dwnEjmq9+5DTLMxbT2lwV+4l/j+029zCFOD7NvgIMG13+pgwz7ajRUuaAPG6Mn
kCTaS9Upzs5peDlxywceuw==
-----END PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIIEEjCCAvqgAwIBAgIJAOK+bHc+tH1qMA0GCSqGSIb3DQEBCwUAMIGdMQswCQYD
VQQGEwJVSzEQMA4GA1UECAwHRW5nbGFuZDESMBAGA1UEBwwJQ2FtYnJpZGdlMRUw
EwYDVQQKDAxXZWIgQWRqdXN0ZXIxCjAIBgNVBAsMAS0xEjAQBgNVBAMMCWxvY2Fs
aG9zdDExMC8GCSqGSIb3DQEJARYic3BhbS1tZS1zZW5zZWxlc3NAc2l0dGluZy1k
dWNrLmNvbTAeFw0xODA4MTMxNjU0NDJaFw0zODAxMTgxNjU0NDJaMIGdMQswCQYD
VQQGEwJVSzEQMA4GA1UECAwHRW5nbGFuZDESMBAGA1UEBwwJQ2FtYnJpZGdlMRUw
EwYDVQQKDAxXZWIgQWRqdXN0ZXIxCjAIBgNVBAsMAS0xEjAQBgNVBAMMCWxvY2Fs
aG9zdDExMC8GCSqGSIb3DQEJARYic3BhbS1tZS1zZW5zZWxlc3NAc2l0dGluZy1k
dWNrLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALVcQxXsJBiQ
ly77HtOQ4vkQ54hqMLcWzY96lPpfjlSQQLdnrcbH5xcg8pYQ087p48gxchEKh1WQ
qJ0rZtN2UDNm8kKKaXWZhSqQASDvkmNnAKIh5XtLKbb77/dZVpfKecVjIsgsgprA
zKo2eOR2J+InwdtGs8PD28EIha0Ey/ZYp+3lithglfO0j3/FUMXP86rbAIjApPHH
Yo/NAwF848uQp+yTdBzzp7/kvfZxOiL9jG2BJuzZbuBZc3YZQMUYedm01lCyvU9c
jZxMbj2lRA6viQQNtoQ1aRsmAFrEvIlDIMfL5fRvz7nyM09KLN4Vy+DBoMAshlm+
vj3UTJx5X5cCAwEAAaNTMFEwHQYDVR0OBBYEFGp//Ncf/jHwbmBVOcDIu4szLVGs
MB8GA1UdIwQYMBaAFGp//Ncf/jHwbmBVOcDIu4szLVGsMA8GA1UdEwEB/wQFMAMB
Af8wDQYJKoZIhvcNAQELBQADggEBAAbl38cy9q2yWubvmGEi4GNiwAxmYDc6U9VB
qq8QxQMc7J+kpJ/UMcfIaDHY/WIBVOsvnupUfXduE3Khiio5EwSgs2hkuWYkFA3D
6LqQTcNcSs9X3r0lu26d/7wUE3eQVReXRSV/rkwvUYvGTAtvL56YvTGwcqhKCPLg
JhD4CDjkt05LyUBPS0O6sPG+R1XunHx9w8IpxQirYA91xqMC5j7klmppD82L9bAm
BRyWAwHQyrzSf4vUEiVREEjEavc11r8KmTIqHYC/4rYjZw2rFrk3KYeqzpZVoFaQ
RguOSJvGtfKm3KZzFATfea0ej/0hgXCUvOYvIQcxMEB61+WAKhE=
-----END CERTIFICATE-----
""")
        # DON'T add the_duff_certfile to kept_tempfiles for clean up on exit.
        # If you do, there is a race condition when adjuster is restarting.
        return the_duff_certfile

kept_tempfiles = {}

def unlink(fn):
    try: os.unlink(fn)
    except: pass

#@file: request-forwarder-setup.py
# --------------------------------------------------
# Configurations of RequestForwarder for basic use,
# CONNECT termination, and Javascript upstream handling
# --------------------------------------------------

def MakeRequestForwarder(useSSL,port,connectPort,origPort,isPJS=False,start=0,index=0):
    class MyRequestForwarder(RequestForwarder):
        WA_UseSSL = useSSL
        WA_port = port # the port we are listening on
        WA_connectPort = connectPort # the port to forward CONNECT requests to (if we're not useSSL and not isSslUpstream)
        WA_origPort = origPort # the port for forwardToOtherPid (if we are useSSL)
        isPjsUpstream = isPJS
        WA_PjsStart = start # (for multicore)
        WA_PjsIndex = index # (relative to start)
        isSslUpstream = False
    return MyRequestForwarder # the class, not an instance
def NormalRequestForwarder(): return MakeRequestForwarder(False,options.port,options.internalPort,options.port)
def SSLRequestForwarder(): return MakeRequestForwarder(True,options.internalPort,options.internalPort,options.port)
def PjsRequestForwarder(start,index): return MakeRequestForwarder(False,js_proxy_port[start+index],js_proxy_port[start+index]+1,js_proxy_port[start+index],True,start,index)
def PjsSslRequestForwarder(start,index): return MakeRequestForwarder(True,js_proxy_port[start+index]+1,js_proxy_port[start+index]+1,js_proxy_port[start+index],True,start,index)

class UpSslRequestForwarder(RequestForwarder):
    "A RequestForwarder for running upstream of upstream_proxy, rewriting its .0 requests back into SSL requests"
    WA_UseSSL = isPjsUpstream = False
    isSslUpstream = True # connectPort etc not needed

#@file: wsgi.py
# --------------------------------------------------
# WSGI support for when we can't run as a server process.
# Works on Tornado versions 2 through 5.  Support for this
# has been dropped in Tornado 6, so don't use Tornado 6 if
# you want WSGI support (Tornado 5.x can run in Python 3)
# --------------------------------------------------

def make_WSGI_application():
    global errExit, wsgi_mode, runFilter
    wsgi_mode = True ; runFilter = sync_runFilter
    def errExit(m): raise Exception(m)
    global main
    def main(): raise Exception("Cannot run main() after running make_WSGI_application()")
    preprocessOptions()
    for opt in 'config address background restart stop install browser run ip_change_command fasterServer ipTrustReal renderLog logUnsupported ipNoLog js_reproxy ssl_fork just_me one_request_only seconds stdio'.split(): # also 'port' 'logRedirectFiles' 'squashLogs' but these have default settings so don't warn about them
        # (js_interpreter itself should work in WSGI mode, but would be inefficient as the browser will be started/quit every time the WSGI process is.  But js_reproxy requires additional dedicated ports being opened on the proxy: we *could* do that in WSGI mode by setting up a temporary separate service, but we haven't done it.)
        if eval('options.'+opt): warn("'%s' option may not work in WSGI mode" % opt)
    options.js_reproxy = False # for now (see above)
    options.one_request_only = False
    if (options.pdftotext or options.epubtotext or options.epubtozip) and (options.pdfepubkeep or options.waitpage):
        options.pdfepubkeep=0 ; options.waitpage = False
        warn("pdfepubkeep and waitpage may not work in WSGI mode; clearing them") # both rely on one process doing all requests (not guaranteed in WSGI mode), and both rely on ioloop's add_timeout being FULLY functional
    import tornado.wsgi
    if not hasattr(tornado.wsgi,"WSGIApplication"): errExit("Tornado 6+ does not support our WSGI mode. Use Tornado 5 or below.")
    handlers = [("(.*)",SynchronousRequestForwarder)]
    if options.staticDocs: handlers.insert(0,static_handler()) # (the staticDocs option is probably not really needed in a WSGI environment if we're behind a wrapper that can also list static URIs, but keeping it anyway might be a convenience for configuration-porting; TODO: warn that this won't work with htaccess redirect and SCRIPT_URL thing)
    return tornado.wsgi.WSGIApplication(handlers)

wsgi_mode = False
def httpfetch(req,url,**kwargs):
    url = B(url)
    url = re.sub(B("[^ -~]+"),lambda m:quote(m.group()),url) # sometimes needed to get out of redirect loops
    debuglog("httpfetch "+S(url)+" "+repr(kwargs)+repr([(n,v) for n,v in kwargs['headers'].get_all()]))
    if not wsgi_mode:
        callback = kwargs['callback']
        del kwargs['callback']
        return doCallback(req,MyAsyncHTTPClient().fetch,callback,url,**kwargs)
    # ----------------------------
    # -------- wsgi_mode: --------
    # Don't use HTTPClient: it usually just wraps ASyncHTTPClient with an IOLoop,
    # not all WSGI servers will support this (and a functioning ssl module
    # is required for https URLs), platforms like AppEngine will go wrong
    # and error sometimes gets raised later so we can't reliably catch it here.
    # Go straight to urllib2 instead.
    data = kwargs.get('body',None)
    if not data: data = None
    headers = dict(kwargs.get('headers',{}))
    req = Request(S(url), data, headers)
    if kwargs.get('proxy_host',None) and kwargs.get('proxy_port',None): req.set_proxy("http://"+kwargs['proxy_host']+':'+kwargs['proxy_port'],"http")
    r = None
    try: resp = build_opener(DoNotRedirect).open(req,timeout=60)
    except UL_HTTPError as e: resp = e
    except Exception as e: resp = r = wrapResponse(str(e)) # could be anything, especially if urllib2 has been overridden by a 'cloud' provider
    if r==None: r = wrapResponse(resp.read(),resp.info(),resp.getcode())
    kwargs['callback'](r)
def wrapResponse(body,info={},code=500):
    "Makes a urllib2 response or an error message look like an HTTPClient response.  info can be a headers dict or a resp.info() object."
    class Empty: pass
    r = Empty()
    r.code = code
    class H:
        def __init__(self,info): self.info = info
        def get(self,h,d): return self.info.get(h,d)
        def add(self,h,v): # for js_fallback header
            if type(self.info)==dict:
                self.info[h] = v
            elif hasattr(self.info,"headers"):
                self.info.headers.add(h,v)
            else: self.info.add(h,v)
        def get_all(self):
            if hasattr(self.info,"items"):
                return self.info.items()
            elif hasattr(self.info,"headers"):
                return [h.replace('\n','').split(': ',1) for h in self.info.headers]
            else: return self.info.get_all()
    r.headers = H(info) ; r.body = B(body) ; return r

class DoNotRedirect(HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers): raise UL_HTTPError(req.get_full_url(), code, msg, headers, fp)
    http_error_301 = http_error_303 = http_error_307 = http_error_302

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
   def connect(self, *args, **kwargs): raise Exception("CONNECT is not implemented in WSGI mode") # so connectPort etc not needed
   def myfinish(self): pass

#@file: user.py
# --------------------------------------------------
# URL/search box & general "end-user interface" support
# --------------------------------------------------

def addArgument(url,extraArg):
    if B('#') in url: url,hashTag = url.split(B('#'),1)
    else: hashTag=None
    if B('?') in url: url += B('&')+B(extraArg)
    else: url += B('?')+B(extraArg)
    if hashTag: url += B('#')+hashTag
    return url

def remove_blanks_add_utf8_BOM(out):
    # for writing text files from PDF and EPUB
    return unichr(0xFEFF).encode('utf-8')+B("\n").join([x for x in B(out).replace(B("\r"),B("")).split(B("\n")) if x])

def rm_u8punc(u8):
    # for SMS links, turn some Unicode punctuation into ASCII (helps with some phones)
    for k,v in u8punc_d: u8=u8.replace(k,v)
    return u8
u8punc_d=u"\u2013 -- \u2014 -- \u2018 ' \u2019 ' \u201c \" \u201d \" \u2032 ' \u00b4 ' \u00a9 (c) \u00ae (r)".encode('utf-8').split()
u8punc_d = zip(u8punc_d[::2], u8punc_d[1::2])

def getSearchURL(q):
    if not options.search_sites: return B("http://")+quote(q) # ??
    def site(s,q): return B(s.split()[0])+quote(q)
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
    r = htmlhead('Web Adjuster start page')+'<form action="'+options.urlboxPath+'"><label for="q">'+options.boxPrompt+'</label>: <input type="text" id="q" name="q"' # TODO: consider heading tag for boxPrompt if browser is IEMobile 6
    if default_url: r += ' value="'+S(default_url)+'"'
    else: r += ' placeholder="http://"' # HTML5 (Firefox 4, Opera 11, MSIE 10, etc)
    r += '><input type="submit" value="Go">'+searchHelp()+cssOpts_html # 'go' button MUST be first, before cssOpts_html, because it's the button that's hit when Enter is pressed.  (So might as well make the below focus() script unconditional even if there's cssOpts_html.  Minor problem is searchHelp() might get in the way.)
    if enable_adjustDomainCookieName_URL_override and not options.wildcard_dns and "" in options.default_site.split("/"): r += '<input type="hidden" name="%s" value="%s">' % (adjust_domain_cookieName,S(adjust_domain_none)) # so you can get back to the URL box via the Back button as long as you don't reload
    if htmlonly_checked: htmlonly_checked=' checked="checked"'
    else: htmlonly_checked = ""
    if options.htmlonly_mode:
        if not r.endswith("</p>"): r += "<br>"
        if force_htmlonly_mode: r += '<input type="checkbox" id="pr" disabled="disabled" checked="checked"> <label for="pr">HTML-only mode</label>'
        else: r += '<input type="checkbox" id="pr" name="pr"'+htmlonly_checked+'> <label for="pr">HTML-only mode</label>'
    if options.submitPath: r += '<p><input type="submit" name="sPath" value="Upload your own text"></p>'
    r += '</form><script><!--\ndocument.forms[0].q.focus();\n//-->\n</script>'
    if options.urlbox_extra_html: r += options.urlbox_extra_html
    return r+'</body></html>'

backScript="""<script><!--
document.write('<br><a href="javascript:history.go(-1)">Back to previous page</a>')
//-->
</script>"""
backScriptNoBr="""<script><!--
document.write('<a href="javascript:history.go(-1)">Back to previous page</a> ')
//-->
</script>"""
# (HTML5 defaults type to text/javascript, as do all pre-HTML5 browsers including NN2's 'script language="javascript"' thing, so we might as well save a few bytes)

#@file: ruby-css.py
# --------------------------------------------------
# Ruby CSS support for Chinese/Japanese annotators etc
# --------------------------------------------------

rubyCss1 = "".join([
    "ruby{"
    "display:inline-table !important;"
    "vertical-align:bottom !important;"
    "-webkit-border-vertical-spacing:1px !important;"
    "padding-top:0.5ex !important;"
    "margin:0px !important;}"
    "ruby *{"
    "display: inline !important;"
    "vertical-align:top !important;"
    "line-height:1.0 !important;"
    "text-indent:0 !important;"
    "text-align:center !important;"
    "padding-left:0px !important;padding-right:0px !important}" # if we space-separate words
    "rb{display:table-row-group !important;"
    "font-size: 100% !important;}"
    "rt{display:table-header-group !important;"
    "font-size:100% !important;line-height:1.1 !important;}"])
rubyScript = '<style>'+rubyCss1+'</style>'
# And the following hack is to stop the styles in the 'noscript' and the variable (and any others) from being interpreted if an HTML document with this processing is accidentally referenced as a CSS source (which can mess up ruby):
rubyScript = "<!-- { } @media(none) { -->" + rubyScript
# By the way, also try to specify some nice fonts (but IE doesn't like this) :
rubyScript_fonts = '<!--[if !IE]>--><style>rt { font-family: Gandhari Unicode, FreeSerif, Lucida Sans Unicode, Times New Roman, DejaVu Sans, serif !important; }</style><!--<![endif]-->'
rubyScript_fonts = '<!--[if lt IE 8]><style>ruby, ruby *, ruby rb, ruby rt { display: inline !important; vertical-align: baseline !important; padding-top: 0pt !important; } ruby { border: thin grey solid; } </style><![endif]-->' + rubyScript_fonts # IE6/WM6 workaround
rubyScript += rubyScript_fonts
# and this goes at the END of the body:
rubyEndScript = """
<script><!--
function treewalk(n) { var c;for(c=n.firstChild;c;c=c.nextSibling) { if (c.nodeType==1 && c.nodeName!="SCRIPT" && c.nodeName!="TEXTAREA" && !(c.nodeName=="A" && c.href)) { treewalk(c); if(c.nodeName=="RUBY" && c.title && !c.clkAdded) {c.addEventListener('click',(function(c){return function(){alert(c.title)}})(c)); c.clkAdded=1 } } } } function tw() { treewalk(document.body); window.setTimeout(tw,5000); } treewalk(document.body); window.setTimeout(tw,1500);
//-->
</script>""" # don't use onclick= as our bookmarklets could be incompatible with sites that say unsafe-inline in their Content-Security-Policy headers

#@file: bookmarklet.py
# --------------------------------------------------
# Support accessing our text processing via bookmarklet
# --------------------------------------------------

def bookmarklet(submit_url,local_submit_url,warn_letsEncrypt):
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
    if options.submitBookmarkletDomain:
        locProto = '(location.protocol=="https:"?"https:":"http:")+' # use http if it's file: etc
        if warn_letsEncrypt: warn_letsEncrypt='<strong>Your old browser will no longer respond to these on "secure" sites</strong> unless you first visit <a href="https://%s">https://%s</a> and accept its "expired" or "invalid" certificate (this is due to a change made by the "Let\'s Encrypt" certificate company at the end of September&nbsp;2021). ' % (options.submitBookmarkletDomain,options.submitBookmarkletDomain)
        else: warn_letsEncrypt = ""
    else: locProto = warn_letsEncrypt = ""
    # XMLHttpRequest requires MSIE7 (or Firefox, Chrome, etc), so we should be OK to use try...catch (introduced in MSIE6) if we can use it. IE5 and 6 could use ActiveXObject("Microsoft.XMLHTTP") but I haven't checked if Windows Mobile 2003SE/5/6/6.1 implements it (or bookmarklets). Some browsers' handling of Content-Security-Policy would prevent our bookmarklet from being run at all (with no explanation given to the user), but if it DOES run and just isn't allowed to make XMLHttpRequests then we can say something.
    return '<script><!--\nif(typeof XMLHttpRequest!="undefined"&&typeof JSON!="undefined"&&JSON.parse&&document.getElementById&&document.readyState!="complete"){var n=navigator.userAgent;var i=n.match(/iPhone/),a=n.match(/Android/),p=n.match(/iPad/),c="",t=0,j="javascript:",u="{var r;try{r=new XMLHttpRequest();r.open(\'GET\','+locProto.replace('"',"'")+"'"+submit_url+'",v="\',false);r.send();r=r.responseText}catch(e){r=0;alert(\'Bookmarklet cannot contact Web Adjuster. If this is not a network or server problem, you may need to find a browser extension that disables Content Security Policy.\')}eval(r)}"; var u2=j+"if(window.doneMasterFrame!=1){var d=document;var b=d.body;var fs=d.createElement(\'frameset\'),h=d.createElement(\'html\');fs.appendChild(d.createElement(\'frame\'));fs.firstChild.src=self.location;while(b.firstChild)h.appendChild(b.removeChild(b.firstChild));b.appendChild(fs);window.doneMasterFrame=1;window.setTimeout(function(){if(!window.frames[0].document.body.innerHTML){var d=document;var b=d.body;while(b.firstChild)b.removeChild(b.firstChild);while(h.firstChild)b.appendChild(h.removeChild(h.firstChild));alert(\'The bookmarklet cannot annotate the whole site because your browser does not seem to have the frames loophole it needs. Falling back to annotating this page only. (To avoid this message in future, install the not Plus bookmarklet.)\')}},1000)}"+u+"B";u=j+u+"b";if(i||a||p){t="'+local_submit_url+'"+(i?"i":p?"p":"a");u="#"+u;u2="#"+u2}else c=" onclick=_IHQ_alert(\'To use this bookmarklet, first drag it to your browser toolbar. (If your browser does not have a toolbar, you probably have to paste text manually.)\');return false_IHQ_";document.write(((i||a||p)?"On "+(i?"iPhone":p?"iPad":"Android")+", you can install a special kind of bookmark (called a &#8216;bookmarklet&#8217;), and activate":"On some browsers, you can drag a \'bookmarklet\' to the toolbar, and press")+" it later to use this service on the text of another site. '+quote_for_JS_doublequotes(r'<span id="bookmarklet"><a href="#bookmarklet" onClick="document.getElementById('+"'bookmarklet'"+r').innerHTML=&@]@+@]@quot;'+warn_letsEncrypt.replace('"','_IHQ_')+r'<span class=noIOS>Basic bookmarklet'+plural(len(names))+' (to process <b>one page</b> when activated): </span>'+(' | '.join(('<a href="@]@+(t?(t+@]@'+c.noInc()+'@]@):\'\')+u+@]@'+c()+'@]@+v+@]@"@]@+c+@]@>'+name+'</a>') for name in names)).replace(r'"','_IHQ_')+c.reset()+'<span class=noIOS>. Advanced bookmarklet'+plural(len(names))+' (to process <b>a whole site</b> when activated, but with the side-effect of resetting the current page and getting the address bar \'stuck\'): '+(' | '.join(('<a href="@]@+(t?(t+@]@'+c.noInc()+'@]@):\'\')+u2+@]@'+c()+'@]@+v+@]@"@]@+c+@]@>'+name+'+</a>') for name in names)).replace(r'"','_IHQ_')+'</span>&@]@+@]@quot;.replace(/_IHQ_/g,\'&@]@+@]@quot;\');return false">Show bookmarklet'+plural(len(names))+'</a></span>').replace('@]@','"')+'");if(i||p) document.write("<style>.noIOS{display:none;visibility:hidden}</style>")}\n//-->\n</script>' # JSON.parse is needed (rather than just using eval) because we'll also need JSON.stringify (TODO: unless we fall back to our own slower encoding; TODO: could also have a non-getElementById fallback that doesn't hide the bookmarklets)
    # 'loophole': https://bugzilla.mozilla.org/show_bug.cgi?id=1123694 (+ 'seem to' because I don't know if the timeout value is enough; however we don't want it to hang around too long) (don't do else h=null if successful because someone else may hv used that var?)
    # 'resetting the current page': so you lose anything you typed in text boxes etc
    # (DO hide bookmarklets by default, because don't want to confuse users if they're named the same as the immediate-action filter selections at the bottom of the page)
    # TODO: we append '+' to the names of the 'advanced' versions of the bookmarklets, but we don't do so on the Android/iOS title pages; is that OK?
    # TODO: "browser toolbar" detect which browser and name it accordingly?  (Safari calls it the "Favourites" bar)
def quote_for_JS_doublequotes(s): return s.replace("\\","\\\\").replace('"',"\\\"").replace("\n","\\n").replace('</','<"+"/') # for use inside document.write("") etc
def bookmarkletMainScript(jsonPostUrl,forceSameWindow):
    if forceSameWindow: case1Extra = "if(c.target=='_blank') c.removeAttribute('target'); " # (used by the "plus" bookmarklets)
    else: case1Extra = ""
    # HTMLSizeChanged in the below calls callback the NEXT time HTML size is changed, and then stops checking.  The expectation is that HTMLSizeChanged will be called again to set up change monitoring again after the callback has made its own modifications.
    # innerHTML size will usually change if there's a JS popup etc (TODO: could periodically do a full scan anyway, on the off-chance that some JS change somehow keeps length the same); sizeChangedLoop is an ID so we can stop our checking loop if for any reason HTMLSizeChanged is called again while we're still checking (e.g. user restarts the bookmarklet, or callback is called by MutationObserver - we assume JS runs only one callback at a time).
    # MutationObserver gives faster response times when supported, but might not respond to ALL events on all browsers, so we keep the size check as well.
    if options.submitBookmarkletDomain: locProto = '(location.protocol=="https:"?"https:":"http:")+'
    else: locProto = ""
    # TODO: make mergeTags configurable, and implement it in the non-JS version (and expand it so it's not dependent on both of the consecutive EM-etc elements being leaf nodes?) (purpose is to stop problems with <em>txt1</em><em>txt2</em> resulting in an annotator receiving txt1 and txt2 separately and not adding space between them when necessary)
    # TODO: also apply annogen's "adapt existing ruby markup to gloss-only" logic? (but if they're using a bookmarklet, they might want, and should at least be able to put up with, an annotation of the whole thing, so this is low priority)
    if options.submitBookmarkletRemoveExistingRuby: rmRT="if (c.nodeType==1 && c.nodeName=='RT') n.removeChild(c); else if (c.nodeType==1 && (c.nodeName=='RUBY' || c.nodeName=='RB') && c.firstChild) { cNext=c.firstChild; while (c.firstChild) { var tmp = c.firstChild; c.removeChild(tmp); n.insertBefore(tmp,c); } n.removeChild(c); }"
    else: rmRT = ""
    return r"""var leaveTags=%s,stripTags=%s,mergeTags=['EM','I','B','STRONG'];
function HTMLSizeChanged(callback) {
  if(typeof window.sizeChangedLoop=="undefined") window.sizeChangedLoop=0; var me=++window.sizeChangedLoop;
  var getLen = function(w) { var r=0; try{w.document}catch(E){return r} if(w.frames && w.frames.length) { var i; for(i=0; i<w.frames.length; i++) r+=getLen(w.frames[i]) } if(w.document && w.document.body && w.document.body.innerHTML) r+=w.document.body.innerHTML.length; return r };
  var curLen=getLen(window),
    stFunc=function(){window.setTimeout(tFunc,1000)},
    tFunc=function(){if(window.sizeChangedLoop==me){if(getLen(window)==curLen) stFunc(); else callback()}};
  stFunc(); var m=window.MutationObserver||window.WebKitMutationObserver; if(m) new m(function(mut,obs){obs.disconnect();if(window.sizeChangedLoop==me)callback()}).observe(document.body,{childList:true,subtree:true})
}
var texts,tLen,oldTexts,otPtr,replacements;
function all_frames_docs(c) { var f=function(w){try{w.document}catch(E){return}if(w.frames && w.frames.length) { var i; for(i=0; i<w.frames.length; i++) f(w.frames[i]) } c(w.document) }; f(window) }
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
    %s if (isTxt(cNext) && isTxt(ps)) {
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
    } else if(c.nodeType==1 && cNext && cNext.nodeType==1 && mergeTags.indexOf(c.nodeName)!=-1 && c.nodeName==cNext.nodeName && c.childNodes.length==1 && cNext.childNodes.length==1 && isTxt(c.firstChild) && isTxt(cNext.firstChild)) {
      cNext.firstChild.nodeValue = c.firstChild.nodeValue+cNext.firstChild.nodeValue;
      n.removeChild(c);
    } else if(isTxt(c)) while(cNext && isTxt(cNext)) { cNext.nodeValue=c.nodeValue+cNext.nodeValue; n.removeChild(c); c=cNext; cNext=c.nextSibling; }
    c=cNext;
  }
  c=n.firstChild;
  while(c) {
    var cNext = c.nextSibling;
    switch (c.nodeType) {
    case 1: if (leaveTags.indexOf(c.nodeName)==-1 && c.className!="_adjust0") walk(c,document); %sbreak;
    case 3:
      if (%s) {
          var cnv = c.nodeValue;
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
}adjusterScan();%s undefined""" % (repr([t.upper() for t in options.leaveTags]),repr([t.upper() for t in options.stripTags]),locProto,jsonPostUrl,addRubyScript(),rmRT,case1Extra,options.submitBookmarkletFilterJS,options.submitBookmarkletChunkSize,rubyEndScript[rubyEndScript.index("<!--")+4:rubyEndScript.rindex("//-->")]) # TODO: addRubyScript and rubyEndScript optional? (needed only if the filter is likely to use ruby); duplicate rubyEndScript added because at least some browsers don't seem to execute it when set as innerHTML by the all_frames_docs call in addRubyScript below, so at least we can do it here in the current frame.  "undefined" added after the ';' on rubyEndScript to ensure the bookmarklet's "eval()" returns undefined, which is needed in at least some versions of Firefox to prevent it replacing the page.
def addRubyScript():
    if not options.headAppendRuby: return ""
    # rScript = rubyScript # doesn't work, fall back on:
    rScript = '<style>'+rubyCss1+'</style>'+rubyScript_fonts
    return r"""all_frames_docs(function(d) { if(d.rubyScriptAdded==1 || !d.body) return; var e=d.createElement('span'); e.innerHTML="%s"; d.body.insertBefore(e,d.body.firstChild);
    e=d.createElement('span'); e.innerHTML="%s"; d.body.appendChild(e); d.rubyScriptAdded=1 });""" % (quote_for_JS_doublequotes(rScript),quote_for_JS_doublequotes(rubyEndScript))

def android_ios_instructions(pType,reqHost,ua,filterNo):
    # Android or iOS instructions for adding bookmarklet
    # (pType: a=Android i=iPhone p=iPad)
    # (Similar technique does NOT work in Opera Mini 5.1.21594 or Opera Mobile 10.00 (both 2010) on Windows Mobile 6.1: can end up with a javascript: bookmark but it has no effect when selected)
    theSys = {"i":"iPhone","p":"iPad","a":"Android"}[pType]
    title = None
    if '#' in options.htmlFilter:
        fNames=options.htmlFilterName.split('#')
        if filterNo+1 < len(fNames):
            title=fNames[filterNo+1]
    elif options.htmlFilterName:
        title=options.htmlFilterName
    if title: title += " on current page" # because page won't be visible while choosing bookmarks, unlike on desktops
    else: title=theSys+" bookmarklet - Web Adjuster" # will be the default name of the bookmark
    # TODO: we say pType+'z' in the instructions to display on another device below, but if there are enough filters to get up to 'z' then the title on the other device will be whatever THAT filter is; might be better to just use txt in that situation
    i0 = htmlhead(title)+"<h3>%s bookmarklet</h3>To install this bookmarklet on %s, follow the instructions below. You might want to take some notes first, because this page will <em>not</em> be displayed throughout the process! If you have another device, you can show another copy of these instructions on it by going to <kbd>http://%sz</kbd>" % (theSys, theSys, reqHost+options.submitPath+pType)
    if "Firefox/" in ua: i0 += "<h4>Not Yet Working On Mobile Firefox!</h4>Please use Chrome/Safari." # TODO: extension for mobile Firefox?
    i0 += "<h4>Instructions</h4><ol><li>"
    sharp = "<li>You should see a sharp sign (#). If you don't, you might have to scroll a little to the right to get it into view. When you see the sharp sign, press immediately to the right of it. (This can be difficult, depending on your eyesight and the size of your fingers. You must put the text cursor <em>immediately</em> to the right of that sharp. Keep trying until you get it in <em>exactly</em> the right place.)<li>Use the backspace key to delete everything up to and including the sharp. The code should now start with the word <code>javascript</code>.<li>"
    if pType in 'ip':
        if pType=='i': # iPhone
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
        i0 += "Press Menu (&#x22ee;) and Save to Bookmarks (&#x2606;) to bookmark <b>this</b> page<li>In the pop-up, long-press the <em>second</em> line to get the selection on it<li>Gently drag the marker over to the left so that it scrolls to the extreme left of the address"+sharp+"Press \"OK\" to come back here."
    i0 += "<li>The bookmarklet is now ready for use. Go to whatever page you want to use it on, and select it from the bookmarks to use it."
    if pType=='a': i0 += " <b>On later versions of Android, it doesn't work to choose the bookmark directly</b>: you have to start typing \""+title+"\" in the URL box and select it that way." # You can also tap address bar and start typing the bookmarklet name if you've sync'd it from a desktop
    return i0+"</ol></body></html>"

#@file: run-filters.py
# --------------------------------------------------
# Text processing etc: handle running arbitrary filters
# --------------------------------------------------

def runFilter(req,cmd,text,callback,textmode=True):

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
    text = B(text)
    if not cmd: return callback(text,"") # null filter, e.g. render-only submitPage
    if type(cmd)==type("") and cmd.startswith("*"):
        cmd = eval(cmd[1:]) # (normally a function name, but any Python expression that evaluates to a callable is OK, TODO: document this?  and incidentally if it evaluates to a string that's OK as well; the string will be given to an external command)
    if not type(cmd)==type(""):
        out = B(cmd(text))
        return IOLoopInstance().add_timeout(time.time(),lambda *args:callback(out,"")) # yield
    elif re.match("https?://",cmd):
        return httpfetch(req,cmd,method="POST",body=text,callback=lambda r:(curlFinished(),callback(B(r.body),"")))
    def subprocess_thread():
        helper_threads.append('filter-subprocess')
        sp=subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=textmode) # TODO: check shell=True won't throw error on Windows
        out,err = sp.communicate(text)
        if not out: out=B("")
        if not err: err="" # TODO: else logging.debug ? (some stderr might be harmless; don't want to fill normal logs)
        IOLoopInstance().add_callback(lambda *args:callback(out,err))
        helper_threads.remove('filter-subprocess')
    threading.Thread(target=subprocess_thread,args=()).start()

def sync_runFilter(req,cmd,text,callback,textmode=True):
    text = B(text)
    if not cmd: return B(callback(text,""))
    if type(cmd)==type("") and cmd.startswith("*"):
        cmd = eval(cmd[1:])
    if not type(cmd)==type(""): out,err = B(cmd(text)),""
    elif re.match("https?://",cmd):
        return httpfetch(req,cmd,method="POST",body=text,callback=lambda r:callback(B(r.body),""))
    else:
        sp=subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=textmode) # TODO: check shell=True won't throw error on Windows
        out,err = sp.communicate(text)
        if not out: out=B("")
        if not err: err="" # TODO: else logging.debug ? (some stderr might be harmless; don't want to fill normal logs)
    callback(out,err)

def json_reEscape(u8str): return B(json.dumps(u8str.decode('utf-8','replace')))[1:-1] # omit ""s (necessary as we might not have the whole string here)

def runFilterOnText(req,cmd,codeTextList,callback,escape=False,separator=None,prefix=""):
    # codeTextList is a list of alternate [code, text, code, text, code]. Any 'text' element can itself be a list of [code, text, code] etc.
    # Pick out all the 'text' elements, separate them, send to the filter, and re-integrate assuming separators preserved
    # If escape is True, on re-integration escape anything that comes under a top-level 'text' element so they can go into JSON strings (see find_HTML_in_JSON)
    if not separator: separator = options.separator
    if not separator: separator="\n"
    separator,prefix = B(separator),B(prefix)
    def getText(l,replacements=None,codeAlso=False,alwaysEscape=False):
        isTxt = False ; r = [] ; rLine = 0
        def maybeEsc(u8str):
            if escape and replacements and (isTxt or alwaysEscape): return json_reEscape(u8str)
            else: return u8str
        for i in l:
            i = B(i)
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
                    r.append(maybeEsc(separator.join(rpl.replace(B(chr(0)),B("&lt;NUL&gt;")) for rpl in replacements[rLine:rLine+cl]))) # there shouldn't be any chr(0)s in the o/p, but if there are, don't let them confuse things
                    rLine += cl
            elif codeAlso: r.append(maybeEsc(i))
            isTxt = not isTxt
        return r
    def countItems(l): return len(separator.join(getText(l)).split(separator))
    text = getText(codeTextList)
    text = [t.replace(unichr(0x200b).encode('utf-8'),B('')) for t in text] # for some sites that use zero-width spaces between words that can upset some annotators (TODO: document that we do this)
    text = [re.sub(u'(?<=[\u2E80-\u9FFF]) +(?=[\u2E80-\u9FFF])','',t.decode('utf-8')).encode('utf-8') for t in text] # also rm normal space when it's between two consecutive CJK characters (TODO: add hangul range? add non-BMP ranges? but what if narrow Python build?)
    toSend = separator.join(text)
    if separator == B(options.separator):
        toSend=separator+toSend+separator
        sortout = lambda out:out.split(separator)[1:-1]
    else: sortout = lambda out:out.split(separator)
    runFilter(req,cmd,prefix+toSend,lambda out,err:callback(B("").join(getText(codeTextList,sortout(out),True)),err))

def find_text_in_HTML(htmlStr): # returns a codeTextList; encodes entities in utf-8
    if options.useLXML:
        return LXML_find_text_in_HTML(htmlStr)
    htmlStr = fixHTML(htmlStr) # may now be u8 or Unicode u8-values, see comments in fixHTML
    class Parser(HTMLParser):
        def shouldStripTag(self,tag):
            self.ignoredLastTag = (tag.lower() in options.stripTags and (self.ignoredLastTag or self.getBytePos()==self.lastCodeStart))
            return self.ignoredLastTag
        def handle_starttag(self, tag, attrs):
            tag = S(tag)
            if self.shouldStripTag(tag): return
            if tag in options.leaveTags:
                self.ignoreData=True
        def handle_endtag(self, tag):
            tag = S(tag)
            if self.shouldStripTag(tag): return
            if tag in options.leaveTags:
                self.ignoreData=False
            # doesn't check for nesting or balancing
            # (documented limitation)
        def getBytePos(self): # TODO: duplicate code
            line,offset = self.getpos()
            while line>self.knownLine:
                self.knownLine += 1
                self.knownLinePos=htmlStr.find(asT(htmlStr,'\n'),self.knownLinePos)+1
            return self.knownLinePos + offset
        def handle_data(self,data,datalen=None):
            if self.ignoreData or not data.strip():
                return # keep treating it as code
            if datalen==None: data = latin1decode(data) # because the document being parsed was from fixHTML's output
            # else datalen not None means data will already have been supplied as a UTF-8 byte string by handle_entityref or handle_charref below.  Either way, 'data' is now a UTF-8 byte string.
            dataStart = self.getBytePos()
            if self.codeTextList and (self.ignoredLastTag or dataStart == self.lastCodeStart): # no intervening code, merge (TODO reduce string concatenation?)
                self.codeTextList[-1] += data
            else:
                self.codeTextList.append(latin1decode(htmlStr[self.lastCodeStart:dataStart]))
                self.codeTextList.append(data)
            if datalen==None: datalen = len(data) # otherwise we're overriding it for entity refs etc
            self.lastCodeStart = dataStart+datalen
        def handle_entityref(self,name):
            name = S(name)
            if name in htmlentitydefs.name2codepoint and not name in ['lt','gt','amp']: self.handle_data(unichr(htmlentitydefs.name2codepoint[name]).encode('utf-8'),len(name)+2)
        def handle_charref(self,name):
            name = S(name)
            if name.startswith('x'): d=unichr(int(name[1:],16))
            else: d=unichr(int(name))
            if d in u'<>&': pass # leave entity ref as-is
            else: self.handle_data(d.encode('utf-8'),len(name)+3)
    parser = Parser()
    parser.codeTextList = [] ; parser.lastCodeStart = 0
    parser.knownLine = 1 ; parser.knownLinePos = 0
    parser.ignoreData = parser.ignoredLastTag = False
    err=""
    try:
        parser.feed(htmlStr) ; parser.close()
    except UnicodeDecodeError as e:
        # sometimes happens in parsing the start of a tag in duff HTML (possibly emitted by a duff htmlFilter if we're currently picking out text for the renderer)
        try: err="UnicodeDecodeError at bytes %d-%d: %s" % (e.start,e.end,e.reason)
        except: err = "UnicodeDecodeError"
    except HTMLParseError as e: # rare?
        try: err="HTMLParseError: "+e.msg+" at "+str(e.lineno)+":"+str(e.offset) # + ' after '+repr(htmlStr[parser.lastCodeStart:])
        except: err = "HTMLParseError"
        logging.info("WARNING: find_text_in_HTML finishing early due to "+err)
    # If either of the above errors occur, we leave the rest of the HTML as "code" i.e. unchanged
    if len(parser.codeTextList)%2: parser.codeTextList.append("") # ensure len is even before appending the remaining code (adjustment is required only if there was an error)
    if not options.renderDebug: err=""
    elif err: err="<!-- "+err+" -->"
    parser.codeTextList.append(B(err)+latin1decode(htmlStr[parser.lastCodeStart:]))
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
                self.out.append(B("</"+tag+">"))
            if (not sst) and tag in options.leaveTags:
                self.ignoreData=False
        def data(self,unidata):
            data = unidata.encode('utf-8')
            if not self.ignoreData==2: data = ampEncode(data) # we want entity refs (which we assume to have been decoded by LXML) to be left as-is.  But DON'T do this in 'script' or 'style' - it could mess everything up (at least some versions of lxml already treat these as cdata)
            if self.ignoreData or not data.strip():
                self.out.append(data) ; return
            if self.ignoredLastTag: self.out = []
            out = B("").join(self.out)
            if self.codeTextList and not out:
                # merge (TODO reduce string concatenation?)
                self.codeTextList[-1] += data
            else:
                self.codeTextList.append(out)
                self.codeTextList.append(data)
            self.out = []
        def comment(self,text): # TODO: same as above's def comment
            self.out.append(B("<!--")+text.encode('utf-8')+B("-->"))
        def close(self): pass
    parser = Parser() ; parser.out = []
    parser.codeTextList = []
    parser.ignoreData = parser.ignoredLastTag = False
    lparser = etree.HTMLParser(target=parser)
    etree.parse(StringIO(htmlStr.decode('utf-8','replace')), lparser)
    if len(parser.codeTextList)%2: parser.codeTextList.append("")
    parser.codeTextList.append(B("").join(parser.out))
    return parser.codeTextList

def find_HTML_in_JSON(jsonStr,htmlListFunc=None):
    # makes a codeTextList from JSON, optionally calling
    # htmlListFunc to make codeTextLists from any HTML
    # parts it finds.  Unescapes the HTML parts.
    jsonStr = S(jsonStr)
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

#@file: charsets.py
# --------------------------------------------------
# HTML character-set rewriting
# --------------------------------------------------

def extractCharsetEquals(value):
    value = S(value)
    charset=value[value.index("charset=")+len("charset="):]
    if ';' in charset: charset=charset[:charset.index(';')]
    return charset

def get_httpequiv_charset(htmlStr):
    class Finished(Exception):
        def __init__(self,charset=None,tagStart=None,tagEnd=None):
            self.charset,self.tagStart,self.tagEnd = charset,tagStart,tagEnd
    htmlStr = fixHTML(htmlStr)
    class Parser(HTMLParser): # better not use LXML yet...
        def handle_starttag(self, tag, attrs):
            tag = S(tag)
            if tag=="body": raise Finished() # only interested in head
            attrs = dict(attrs)
            if tag=="meta" and S(attrs.get("http-equiv",attrs.get("http_equiv","")).lower())=="content-type" and "charset=" in S(attrs.get("content","").lower()):
                charset = extractCharsetEquals(attrs['content'].lower())
                line,offset = self.getpos() ; knownLine = 1 ; knownLinePos = 0
                while line>knownLine:
                    knownLine += 1
                    knownLinePos=htmlStr.find(asT(htmlStr,'\n'),knownLinePos)+1
                tagStart = knownLinePos + offset
                if type(htmlStr)==bytes: tagEnd = htmlStr.index(B(">"),tagStart)+1
                else: tagEnd = htmlStr.index(">",tagStart)+1
                raise Finished(charset,tagStart,tagEnd)
        def handle_endtag(self, tag):
            if S(tag)=="head": raise Finished() # as above
    parser = Parser()
    try:
        parser.feed(htmlStr) ; parser.close()
    except UnicodeDecodeError: pass
    except HTMLParseError: pass
    except Finished as e: return e.charset,e.tagStart,e.tagEnd
    return None,None,None

def get_and_remove_httpequiv_charset(body):
    charset,tagStart,tagEnd = get_httpequiv_charset(body)
    if charset: body = body[:tagStart]+body[tagEnd:]
    if B(body).startswith(B('<?xml version="1.0" encoding')): body = B('<?xml version="1.0"')+body[body.find(B("?>")):] # TODO: honour THIS 'encoding'?  anyway remove it because we've changed it to utf-8 (and if we're using LXML it would get a 'unicode strings with encoding not supported' exception)
    return charset, body

#@file: run-browser.py
# --------------------------------------------------
# Options for running a foreground browser & stopping
# --------------------------------------------------

def runBrowser(*args):
    mainPid = os.getpid()
    def browser_thread():
        helper_threads.append('runBrowser')
        os.system(options.browser)
        helper_threads.remove('runBrowser')
        if options.multicore: # main thread will still be in start_multicore, not IOLoop
            global interruptReason
            interruptReason = "Browser command finished"
            os.kill(mainPid,signal.SIGINT)
        else: stopServer("Browser command finished")
    threading.Thread(target=browser_thread,args=()).start()
def runRun(*args):
    def runner_thread():
        helper_threads.append('runRun')
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
        helper_threads.remove('runRun')
    threading.Thread(target=runner_thread,args=()).start()
def setupRunAndBrowser():
    if options.browser: IOLoopInstance().add_callback(runBrowser)
    if options.run: IOLoopInstance().add_callback(runRun)

def stopServer(reason=None):
    def stop(*args):
        if reason and not reason=="SIG*" and not coreNo:
            # logging from signal handler is not safe, so we
            # defer it until this inner function is called
            if options.background: logging.info(reason)
            else: sys.stderr.write(reason+"\n")
        IOLoopInstance().stop()
    if reason.startswith("SIG") and hasattr(IOLoopInstance(),"add_callback_from_signal"): IOLoopInstance().add_callback_from_signal(stop)
    else: IOLoopInstance().add_callback(stop)

#@file: convert-PDF-etc.py
# --------------------------------------------------
# File conversion options (PDF, MP3 etc)
# --------------------------------------------------

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
        if S(tag)=="a" and attrsD.get("href",None):
            l = S(attrsD["href"].lower())
            if re.match("https?://",l):
                if not self.offsite_ok and not url_is_ours(l): return # "offsite" link, can't process (TODO: unless we send it to ourselves via an alternate syntax)
                # TODO: (if don't implement processing the link anyway) insert explanatory text for why an alternate link wasn't provided?
            elif options.mailtoPath and l.startswith("mailto:"):
                newAttrs = []
                for k,v in items(attrs):
                    if k.lower()=="href": v=options.mailtoPath+S(v)[7:].replace('%','%%+') # see comments in serve_mailtoPage
                    newAttrs.append((k,v))
                return (tag,newAttrs)
            elif ":" in l and l.index(":")<l.find("/"): return # non-HTTP protocol - can't do (TODO: unless we do https, or send the link to ourselves via an alternate syntax)
            if l.endswith(".pdf") or guessCMS(l,"pdf"):
                self.gotPDF = S(attrsD["href"])
                if options.pdfomit and any(re.search(x,self.gotPDF) for x in options.pdfomit.split(",")): self.gotPDF = None
            if l.endswith(".epub") or guessCMS(l,"epub"):
                self.gotEPUB = S(attrsD["href"])
            if l.endswith(".mp3"):
                self.gotMP3 = S(attrsD["href"])
    def handle_endtag(self, tag):
        if S(tag)=="a" and ((self.gotPDF and options.pdftotext) or (self.gotEPUB and (options.epubtozip or options.epubtotext)) or (self.gotMP3 and options.bitrate and options.askBitrate)):
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

def guessCMS(url,fmt):
    # (TODO: more possibilities for this?  Option to HEAD all urls and return what they resolve to? but fetch-ahead might not be a good idea on all sites)
    return fmt and options.guessCMS and "?" in url and "format="+fmt in url.lower() and not ((not fmt=="pdf") and "pdf" in url.lower())

#@file: adjust-HTML.py
# --------------------------------------------------
# Various HTML adjustment options
# --------------------------------------------------

class StripJSEtc:
    # Doesn't have to strip style= and on...= attributes (we'll do that separately) but DOES have to strip javascript: links when AddClickCodes isn't doing it (when AddClickCodes is doing it, we'll just see the PLACEHOLDER which hasn't yet been patched up, so let AddClickCodes do it itself in that case)
    # TODO: change any "[if IE" at the start of comments, in case anyone using affected versions of IE wants to use this mode
    def __init__(self,url,transparent):
        self.url,self.transparent = url,transparent
    def init(self,parser):
        self.parser = parser
        self.suppressing = False
    def handle_starttag(self, tag, attrs):
        tag = S(tag)
        if tag in ["img","svg"] and not options.htmlonly_css:
            self.parser.addDataFromTagHandler(dict(attrs).get("alt",""),1)
            return True
        elif options.js_frames and tag in ["frameset","frame","iframe"]: return True
        elif tag=='script' or (tag=="noscript" and options.js_interpreter) or (tag=='style' and not options.htmlonly_css): # (in js_interpreter mode we want to suppress 'noscript' alternatives to document.write()s or we'll get both; anyway some versions of PhantomJS will ampersand-encode anything inside 'noscript' when we call find_element_by_xpath)
            self.suppressing = True ; return True
        elif tag=="body":
            if not self.transparent:
                if enable_adjustDomainCookieName_URL_override: xtra = "&"+adjust_domain_cookieName+"="+S(adjust_domain_none)
                else: xtra = ""
                self.parser.addDataFromTagHandler('HTML-only mode. <a href="%s">Settings</a> | <a rel="noreferrer" href="%s">Original site</a><p>' % ("//"+hostSuffix()+publicPortStr()+options.urlboxPath+"?d="+quote(self.url)+xtra,self.url)) # TODO: document that htmlonly_mode adds this (can save having to 'hack URLs' if using HTML-only mode with bookmarks, RSS feeds etc)
                # TODO: call request_no_external_referer() on the RequestForwarder as well? (may need a parameter for it)
            return
        elif tag=="a" and not self.suppressing:
            attrsD = dict(attrs)
            if S(attrsD.get("href","")).startswith("javascript:"):
                attrsD["href"] = "#" ; return tag,attrsD
        return self.suppressing or tag=='noscript' or (tag=='link' and not options.htmlonly_css)
    def handle_endtag(self, tag):
        tag = S(tag)
        if tag=="head":
            self.parser.addDataFromTagHandler('<meta name="mobileoptimized" content="0"><meta name="viewport" content="width=device-width"></head>',True) # TODO: document that htmlonly_mode adds this; might also want to have it when CSS is on
            return True # suppress </head> because we've done it ourselves in the above (had to or addDataFromTagHandler would have added it AFTER the closing tag)
        if tag=='script' or (tag=='style' and not options.htmlonly_css) or (tag=="noscript" and options.js_interpreter):
            self.suppressing = False ; return True
        elif tag=='noscript': return True
        else: return self.suppressing
    def handle_data(self,data):
        if self.suppressing: return ""

class RewriteExternalLinks: # for use with cookie_host in htmlOnlyMode (will probably break the site's scripts in non-htmlOnly): make external links go back to URL box and act as though the link had been typed in
    def __init__(self, rqPrefix, baseHref, cookie_host):
        self.rqPrefix = S(rqPrefix)
        self.baseHref = S(baseHref)
        self.cookie_host = S(cookie_host)
    def init(self,parser): self.parser = parser
    def handle_starttag(self, tag, attrs):
        tag = S(tag)
        if tag=="base":
            attrsD = dict(attrs)
            hr = B(attrsD.get("href",""))
            if hr.startswith(B("http")): self.baseHref = hr
        elif tag=="a" or (tag=="iframe" and not options.urlboxPath=="/"):
            att = {"a":"href","iframe":"src"}[tag]
            attrsD = dict(attrs)
            hr = B(attrsD.get(att,B("")))
            if not hr: return # no href
            if hr.startswith(B('#')): return # in-page anchor
            if not hr.startswith(B('http')) and B(':') in hr.split(B('/'),1)[0]: return # non-HTTP(s) protocol?
            if self.baseHref:
                try: hr=B(urlparse.urljoin(self.baseHref,S(hr)))
                except: pass # can't do it
            if not re.match(B("(https?:)?//"),hr): return # still a relative link etc after all that
            realUrl = url_is_ours(hr,self.cookie_host)
            if not options.urlboxPath=="/" and realUrl:
                hr,realUrl = realUrl,None
            if not realUrl: # off-site
              attrsD[att]=B(self.rqPrefix) + B(quote(hr))
              return tag,attrsD
    def handle_endtag(self, tag): pass
    def handle_data(self,data): pass

def HTML_adjust_svc(htmlStr,adjustList,can_use_LXML=True):
    # Runs an HTMLParser on htmlStr, calling multiple adjusters on adjustList.
    # Faster than running the HTMLParser separately for each adjuster,
    # but still limited (find_text_in_HTML is still separate)
    if options.useLXML and can_use_LXML: return HTML_adjust_svc_LXML(htmlStr,adjustList)
    htmlStr = fixHTML(htmlStr)
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
            self.lastStart = htmlStr.index(asT(htmlStr,">"),pos)+1
            return True
        def handle_endtag(self, tag):
            for l in adjustList:
                if l.handle_endtag(tag):
                    return self.suppressTag()
        def addDataFromTagHandler(self,data,replacesTag=0):
            # (if replacesTag=1, tells us the tag will be suppressed later; does not actually do it now. C.f. the lxml version.)
            pos = self.getBytePos()
            if not replacesTag: pos = htmlStr.index(asT(htmlStr,">"),pos)+1 # AFTER the tag (assumes tag not suppressed)
            self.out.append(htmlStr[self.lastStart:pos])
            # Assume none of the other handlers will want to process it:
            if type(htmlStr)==bytes: self.out.append(B(data)) # ensure byte string (so addDataFromTagHandler can be called with literal "" strings in Python 3)
            elif type(data)==bytes: self.out.append(data.decode('latin1')) # so we can do latin1decode after u"".join after
            else: self.out.append(data) # assume it's UTF8 byte values coded in Unicode, so latin1decode should get it later
            self.lastStart = pos
        def getBytePos(self):
            line,offset = self.getpos()
            while line>self.knownLine:
                self.knownLine += 1
                self.knownLinePos=htmlStr.find(asT(htmlStr,'\n'),self.knownLinePos)+1
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
            if any(B(l.handle_data('-'))==B("") for l in adjustList): # suppress entities when necessary, e.g. when suppressing noscript in js_interpreter-processed pages
                dataStart = self.getBytePos()
                self.out.append(htmlStr[self.lastStart:dataStart])
                self.lastStart = dataStart+len(name)+2 # & ... ;
            # else just leave the entity to be copied as-is later
        def handle_charref(self,name):
            if any(B(l.handle_data('-'))==B("") for l in adjustList): # ditto
                dataStart = self.getBytePos()
                self.out.append(htmlStr[self.lastStart:dataStart])
                self.lastStart = dataStart+len(name)+3 # &# ... ;
            # else just leave the char-ref to be copied as-is
    parser = Parser()
    for l in adjustList: l.init(parser)
    parser.out = [] ; parser.lastStart = 0
    parser.knownLine = 1 ; parser.knownLinePos = 0
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
        if debug: parser.out.append(asT(htmlStr," (Debugger: HTML_adjust_svc skipped a character) "))
        htmlStr = htmlStr[parser.lastStart+1:]
        parser2.out = parser.out ; parser2.lastStart = 0
        parser2.knownLine = 1 ; parser2.knownLinePos = 0
        parser = parser2
        numErrs += 1
    try: parser.close()
    except UnicodeDecodeError: pass
    except HTMLParseError: pass
    if debug: parser.out.append(asT(htmlStr,"<!-- Debugger: HTML_adjust_svc ended here -->"))
    parser.out.append(htmlStr[parser.lastStart:])
    if type(htmlStr)==type(u""):
        try: return latin1decode(u"".join(parser.out))
        except: raise Exception("parser.out should be all-Unicode but has some byte strings? "+repr([b for b in parser.out if not type(b)==type(u"")]))
    try: return B("").join(parser.out)
    except UnicodeDecodeError: raise Exception("This should never happen: how did some of parser.out become Unicode when we were working in byte strings? repr: "+repr(parser.out))

def encodeTag(tag,att):
    def encAtt(a,v):
        if v:
            v=B(v).replace(B('&'),B('&amp;')).replace(B('"'),B('&quot;'))
            if not re.search(B('[^A-Za-z_]'),v): return B(a)+B('=')+v # no quotes needed (TODO: option to keep it valid?)
            return B(a)+B('="')+B(v)+B('"')
        else: return B(a)
    return B("<")+B(tag)+B("").join((B(" ")+encAtt(a,v)) for a,v in items(att))+B(">")

html_tags_not_needing_ends = set(['area','base','basefont','br','hr','input','img','link','meta'])

def HTML_adjust_svc_LXML(htmlStr,adjustList):
    class Parser:
        def start(self, tag, att):
            i = len(self.out)
            for l in adjustList:
                r = l.handle_starttag(tag,att)
                if r==True: return # suppress the tag
                elif r: tag,att = r
            self.out.insert(i,encodeTag(tag,dict((k,u8(v)) for k,v in dict(att).items()))) # u8 so latin1decode doesn't pick up on it
        def end(self, tag):
            i = len(self.out)
            for l in adjustList:
                if l.handle_endtag(tag): return
            if tag not in html_tags_not_needing_ends:
                self.out.insert(i,B("</")+B(tag)+B(">"))
        def addDataFromTagHandler(self,data,_=0):
            self.out.append(B(data))
        def data(self,unidata):
            data = unidata.encode('utf-8')
            oldData = data
            for l in adjustList:
                data0 = data
                data = l.handle_data(data)
                if data==None: data = data0
            self.out.append(B(data))
        def comment(self,text): # TODO: option to keep these or not?  some of them could be MSIE conditionals, in which case we might want to take them out or adjust what's inside
            self.out.append(B("<!--")+text.encode('utf-8')+B("-->"))
        def close(self): pass
    parser = Parser() ; parser.out = []
    for l in adjustList: l.init(parser)
    lparser = etree.HTMLParser(target=parser)
    etree.parse(StringIO(htmlStr.decode('utf-8','replace')), lparser)
    return B("").join(parser.out)

def items(maybeDict):
    if type(maybeDict)==dict: return maybeDict.items()
    else: return maybeDict

def zapAllStrOrBytes(s):
    if type(s)==bytes: return B("")
    else: return ""
def zapStrOrBytes(s,r):
    if type(s)==bytes: return re.sub(B(r),B(""),s)
    else: return re.sub(S(r),"",s)
def replaceStrOrBytes(s,r1,r2):
    if type(s)==bytes: return s.replace(B(r1),B(r2))
    else: return s.replace(S(r1),S(r2))
def transform_in_selected_tag(intag,transformFunc,events=False):
    # assumes intag is closed and not nested, e.g. style, although small tags appearing inside it MIGHT work
    # also assumes transformFunc doesn't need to know about entity references etc (it's called for the data between them)
    if intag=="script": events=True # can also set events=True for style if want to strip JS events while stripping style
    class Adjustment:
        def init(self,parser):
            self.intag = False
            self.parser = parser
        def handle_starttag(self, tag, attrs):
            if S(tag)==intag: self.intag=True
            elif intag in ["script","style"]:
              changed = False ; r=[]
              for k,v in items(attrs):
                  if not v==None and (k==intag or (events and k.startswith("on")) or (intag=="script" and k=="id")):
                      v2 = transformFunc(v)
                      if not v2 and k=="id": v2 = v # don't change IDs just because we're removing scripts altogether
                      changed = changed or not v==v2
                      if v2: r.append((k,v2))
                  else: r.append((k,v))
              if changed: return (tag,r)
        def handle_endtag(self, tag):
            if S(tag)==intag: self.intag=False
        def handle_data(self,data):
            if self.intag:
                return transformFunc(data)
    return Adjustment()

class AriaCopier:
    def init(self,parser): self.parser = parser
    def handle_starttag(self, tag, attrs):
        for k,v in items(attrs):
            if k=="aria-label": self.parser.addDataFromTagHandler(v+" ")
    def handle_endtag(*args): pass
    def handle_data(*args): pass

def fixHTML(htmlStr):
    # some versions of Python's HTMLParser can't cope with missing spaces between attributes:
    if type(htmlStr)==type(u""): htmlStr=htmlStr.encode('utf-8') # just in case we're not given a byte-string to start with
    if re.search(B(r'<[^>]*?= *"[^"]*"[A-Za-z]'),htmlStr):
        htmlStr = re.sub(B(r'(= *"[^"]*")([A-Za-z])'),B(r'\1 \2'),htmlStr) # (TODO: that might match cases outside of tags)
    # (TODO: don't need to do the above more than once on same HTML)
    
    # HTMLParser bug in some Python libraries: it can take UTF-8 bytes, but if both non-ASCII UTF-8 and entities (named or numeric) are used in the same attribute of a tag, we get a UnicodeDecodeError on the UTF-8 bytes.
    # HTMLParser's unescape()'s replaceEntities() is inconsistent about whether it returns string or Unicode, and the coercion goes wrong.
    # That happens for example when &quot; or &#34; is used in the attribute along with UTF-8 bytes.
    # It's OK if the entire HTML document is pre-decoded, but that means we can't "stop before" any charset errors; errors are either ignored/replaced or we give up on the whole document.
    # Moreover, if we're being called by get_httpequiv_charset then we might not have UTF-8.
    # Workaround: do a .decode using 'latin1', which maps bytes to Unicode characters in a 'dumb' way.
    # (This is reversed by latin1decode.  If left as byte string, latin1decode does nothing.)
    if type(u"")==type("") or re.search(r'<[^>]*?"[^"]*?&[^"]*?[^ -~]',htmlStr) or re.search(r'<[^>]*?"[^"]*[^ -~][^"]*?&',htmlStr): # looks like there are entities and non-ASCII in same attribute value, or we're in Python 3 in which case HTMLParser can't take byte-strings
        htmlStr = htmlStr.decode('latin1') # now type(u"") but actually a bunch of UTF-8 values
    return htmlStr # either bytes or u"" UTF-8 values
def asT(asType,s):
    # See fixHTML: if htmlStr is of type u"" then it's actually UTF-8 byte-codes plonked into a Unicode string.  Make s the same, assuming that s is either 'proper Unicode' or UTF-8 bytes.
    if type(asType)==type(u""):
        if type(s)==type(u""): return s.encode('utf-8').decode('latin1')
        else: return s.decode('latin1')
    else: return B(s)
def latin1decode(htmlStr):
    # If it's UTF-8 byte values stored in Unicode string, turn it back into a byte string
    if type(htmlStr)==type(u""):
        return htmlStr.encode('latin1')
    else: return htmlStr
def u8(x):
    if type(x)==bytes: return x
    else: return x.encode('utf-8')

def js_process(body,url):
    # Change Javascript code on its way to the end-user
    for prefix, srch, rplac in codeChanges:
        times = None
        if prefix.startswith('*'): cond = (prefix[1:] in body)
        elif '#' in prefix:
                i = prefix.index('#')
                cond = (S(url) == prefix[:i])
                try: times = int(prefix[i+1:])
                except: pass
        else: cond = S(url).startswith(prefix)
        if cond:
            if times: body=B(body).replace(B(srch),B(rplac),times)
            else: body=B(body).replace(B(srch),B(rplac))
    return body

def process_delete(body):
    for d in options.delete:
        body=re.sub(B(d),B(""),B(body))
    if options.delete_doctype:
        body=re.sub(B("^<![dD][oO][cC][tT][yY][pP][eE][^>]*>"),B(""),B(body),1)
    return body

def process_delete_css(body,url):
    url = S(url)
    for d in options.delete_css:
        if '@@' in d: # it's a replace, not a delete
            s,r = d.split('@@',1)
            if '@@' in r: # replace only for certain URLs
                r,urlPart = r.split('@@',1)
                if not urlPart in url:
                    continue # skip this rule
            body = re.sub(B(s),B(r),B(body))
        else: body=re.sub(B(d),B(""),B(body))
    return body

def htmlFind(html,markup):
    # basically html.lower().find(markup), but we need to be
    # aware of things like Tencent's <!--headTrap<body></body><head></head><html></html>-->
    # preferably without running a slow full parser
    markup = B(markup)
    r = html.lower().find(markup)
    if r<0: return r
    c = html.find(B("<!--"))
    if c<0 or c>r: return r
    # If gets here, we might have a headTrap situation
    def blankOut(m): return B(" ")*(m.end()-m.start())
    return re.sub(B("<!--.*?-->"),blankOut,html,flags=re.DOTALL).lower().find(markup) # TODO: improve efficiency of this? (blankOut doesn't need to go through the entire document)

def html_additions(html,toAdd,slow_CSS_switch,cookieDomainStrsJS,urlBoxHost,jsCookieString,canRender,cookie_host,is_password_domain,IsEdge,addHtmlFilterOptions,htmlFilterOutput):
    # Additions to make to HTML only (not on HTML embedded in JSON)
    # called from doResponse2 if do_html_process is set
    html = B(html)
    if html.startswith(B("<?xml")): link_close = B(" /")
    else: link_close = B("")
    if not B("<body") in html.lower() and B("<frameset") in html.lower(): return html # but allow HTML without <body if can't determine it's a frameset (TODO: what about <noframes> blocks?  although browsers that use those are unlikely to apply the kind of CSS/JS/etc things that html_additions puts in)
    bodyAppend = bodyAppend1 = B("")
    bodyPrepend = B(options.bodyPrepend)
    if not bodyPrepend or (options.js_upstream and not is_password_domain=="PjsUpstream"): bodyPrepend = B("")
    headPrepend, headAppend = B(""), B("")
    if set_window_onerror: headAppend += B(r"""<script><!--
window.onerror=function(msg,url,line){alert(msg); return true}
//-->
</script>""")
    if options.alt_dot and altdot_bad_cookie_leak:
        # if experimental, ensure leak-to-domain goes through even if blocked at the HTTP Set-Cookie level (this is documented as bad, and works only on older browsers if the domain has been listed with Mozilla as disallowing cookies)
        headPrepend += B(r"""<script><!--
document.cookie.split('; ').forEach(function(c){document.cookie=c+";domain="+document.domain.match(/\..*/)[0]+";expires=%s;path=/"})
//-->
</script>""" % cookieExpires)
    cssToAdd,attrsToAdd = toAdd
    if cssToAdd:
        # do this BEFORE options.headAppend, because someone might want to refer to it in a script in options.headAppend (although bodyPrepend is a better place to put 'change the href according to screen size' scripts, as some Webkit-based browsers don't make screen size available when processing the HEAD of the 1st document in the session)
        if options.cssName:
          if options.cssName.startswith("*") or options.cssName.startswith("#"): cssName = options.cssName[1:] # omit the * or #
          else: cssName = options.cssName
          if slow_CSS_switch:
              # alternate, slower code involving hard HTML coding and page reload (but still requires some JS)
              bodyAppend += B(reloadSwitchJS("adjustCssSwitch",jsCookieString,False,cssName,cookieDomainStrsJS,cookieExpires))
              if options.cssName.startswith("*"): useCss = not "adjustCssSwitch=0" in jsCookieString
              else: useCss = "adjustCssSwitch=1" in jsCookieString
              # we probably can't do an options.cssName.startswith("#") branch for the cssNameReload browsers (which are unlikely to report system dark mode anyway), so just fall back to default-off in this case
              if useCss:
                  headAppend += B('<link rel="stylesheet" type="text/css" href="%s"%s>' % (cssToAdd,link_close))
                  if attrsToAdd: html=addCssHtmlAttrs(html,attrsToAdd)
          else: # no slow_CSS_switch; client-side only CSS switcher using "disabled" attribute on the LINK element:
            headAppend += B("""<link rel="alternate stylesheet" type="text/css" id="adjustCssSwitch" title="%s" href="%s"%s>""" % (cssName,cssToAdd,link_close))
            # On some Webkit versions, MUST set disabled to true (from JS?) before setting it to false will work. And in MSIE9 it seems must do this from the BODY not the HEAD, so merge into the next script (also done the window.onload thing for MSIE; hope it doesn't interfere with any site's use of window.onload).  (Update: some versions of MSIE9 end up with CSS always-on, so adding these to default cssNameReload)
            if options.cssName.startswith("*"): cond='document.cookie.indexOf("adjustCssSwitch=0")==-1' # CSS should be on by default, so un-disable the 'link rel' if we DON'T have a cookie saying it should be off
            elif options.cssName.startswith("#"): cond='(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches)?document.cookie.indexOf("adjustCssSwitch=0")==-1:(document.cookie.indexOf("adjustCssSwitch=1")>-1)' # CSS should be on by default if system dark mode reported, in which case un-disable the 'link rel' if we don't have a cookie saying it should be off, otherwise un-disable it only if we have a cookie saying it should be on
            else: cond='document.cookie.indexOf("adjustCssSwitch=1")>-1' # CSS should be off by default, so un-disable the 'link rel' only if we have a cookie saying it should be on
            bodyPrepend += B("""<script><!--
if(document.getElementById) { var a=document.getElementById('adjustCssSwitch'); a.disabled=true; if(%s) {a.disabled=false;window.onload=function(e){a.disabled=true;a.disabled=false}} }
//-->
</script>""" % cond)
            bodyAppend += B(r"""<script><!--
if(document.getElementById && !%s && document.readyState!='complete') document.write(" %s: "+'<a href="#" onclick="%s;window.scrollTo(0,0);document.getElementById(\'adjustCssSwitch\').disabled=false;return false">On<\/a> | <a href="#" onclick="%s;window.scrollTo(0,0);document.getElementById(\'adjustCssSwitch\').disabled=true;return false">Off<\/a> ')
//-->
</script>""" % (detect_iframe,cssName,";".join((r"document.cookie=\'adjustCssSwitch=1%s;expires=%s;path=/\'" % (c,cookieExpires)) for c in cookieDomainStrsJS),";".join((r"document.cookie=\'adjustCssSwitch=0%s;expires=%s;path=/\'" % (c,cookieExpires)) for c in cookieDomainStrsJS))) # (hope it helps some MSIE versions to set cookies 1st, THEN scroll, and only THEN change the document. Also using onclick= rather than javascript: URLs)
        else: # no cssName: stylesheet always on
          headAppend += B('<link rel="stylesheet" type="text/css" href="%s"%s>' % (cssToAdd,link_close))
          if attrsToAdd and slow_CSS_switch: html=addCssHtmlAttrs(html,attrsToAdd)
    if options.htmlFilterName and options.htmlFilter and addHtmlFilterOptions:
        if '#' in options.htmlFilter: bodyAppend1 = B(reloadSwitchJSMultiple("adjustNoFilter",jsCookieString,True,options.htmlFilterName.split("#"),cookieDomainStrsJS,cookieExpires)) # (better put the multi-switch at the start of the options; it might be the most-used option.  Put it into bodyAppend1: we don't want the word "Off" to be misread as part of the next option string, seeing as the word before it was probably not "On", unlike normal reloadSwitchJS switches)
        else: bodyAppend += B(reloadSwitchJS("adjustNoFilter",jsCookieString,True,options.htmlFilterName,cookieDomainStrsJS,cookieExpires)) # (after the CSS if it's only an on/off)
    if canRender:
        # TODO: make the script below set a cookie to stop itself from being served on subsequent pages if detect_renderCheck failed? but this might be a false economy if upload bandwidth is significantly smaller than download bandwidth (and making it external could have similar issues)
        # TODO: if cookies are not supported, the script below could go into an infinite reload loop
        if options.renderCheck and not "adjustNoRender=1" in jsCookieString: bodyPrepend += B(r"""<script><!--
if(!%s && %s) { %s;location.reload(true)
}
//-->
</script>""" % (detect_iframe,detect_renderCheck(),";".join((r"document.cookie='adjustNoRender=1%s;expires=%s;path=/'" % (c,cookieExpires)) for c in cookieDomainStrsJS)))
        if options.renderName:
            if options.renderCheck and "adjustNoRender=1" in jsCookieString: extraCondition="!"+detect_renderCheck() # don't want the adjustNoRender=0 (fonts ON) link visible if detect_renderCheck is true, because it won't work anyway (any attempt to use it will be reversed by the script, and if we work around that then legacy pre-renderCheck cookies could interfere; anyway, if implementing some kind of 'show the switch anyway' option, might also have to address showing it on renderOmit browsers)
            else: extraCondition=None
            bodyAppend += B(reloadSwitchJS("adjustNoRender",jsCookieString,True,options.renderName,cookieDomainStrsJS,cookieExpires,extraCondition))
    if cookie_host:
        if enable_adjustDomainCookieName_URL_override: bodyAppend += B(r"""<script><!--
if(!%s&&document.readyState!='complete')document.write('<a href="%s?%s=%s">Back to URL box<\/a>')
//-->
</script><noscript><a href="%s?%s=%s">Back to URL box</a></noscript>""" % (detect_iframe,options.urlscheme+urlBoxHost+publicPortStr()+options.urlboxPath,adjust_domain_cookieName,S(adjust_domain_none),options.urlscheme+urlBoxHost+publicPortStr()+options.urlboxPath,adjust_domain_cookieName,S(adjust_domain_none)))
        else: bodyAppend += B(r"""<script><!--
if(!%s&&document.readyState!='complete')document.write('<a href="javascript:document.cookie=\'%s=%s;expires=%s;path=/\';location.href=\'%s?nocache=\'+Math.random()">Back to URL box<\/a>')
//-->
</script>""" % (detect_iframe,adjust_domain_cookieName,S(adjust_domain_none),cookieExpires,urlBoxHost+publicPortStr()+options.urlboxPath,options.urlscheme+urlBoxHost+publicPortStr()+options.urlboxPath)) # (we should KNOW if location.href is already that, and can write the conditional here not in that 'if', but they might bookmark the link or something)
    if options.headAppend and not (options.js_upstream and not is_password_domain=="PjsUpstream"): headAppend += B(options.headAppend)
    if options.highlighting and not options.js_upstream:
        bodyPrepend += B("""<div id="adjust0_HL" style="display: none; position: fixed !important; background: white !important; color: black !important; right: 0px; top: 3em; size: 130% !important; border: thin red solid !important; cursor: pointer !important; z-index:2147483647; -moz-opacity: 1 !important; opacity: 1 !important;">""")
        for c in options.highlighting: bodyPrepend += B('<a href="#" style="background:'+c+'!important; padding: 1ex !important;" onclick="adjust0_HighlSel('+"'"+c+"'"+');return false">'+S(u"\u270f")+'</a>') # must be <a href> rather than <span> for selection to not be cleared (but on some browsers it's cleared anyway, hence setTimeout etc below)
        bodyPrepend += B("""</div><script><!--
var leaveTags=%s;function adjust0_HighlRange(n,range,colour,lastID,startStr,loading) {
  var docRange=0;
  for(var c=n.firstChild, count=0; c; c=c.nextSibling, ++count) {
    if(c.id) { lastID=c.id; count=0; if(c.id=="adjust0_HL") continue}
    if(range.intersectsNode(c))
      switch(c.nodeType) {
        case 1:
          if(leaveTags.indexOf(c.nodeName)==-1) {
            var w=lastID+(count?"+"+count:"")+"/";
            if(c.getAttribute("style")) c.style.backgroundColor="inherit";
            if(c.nodeName=="RUBY"){if(!docRange){docRange=new Range();docRange.selectNodeContents(document.body)}startStr = adjust0_HighlRange(c,docRange,colour,w,startStr,loading)} // highlight whole of any ruby intersected
            else startStr = adjust0_HighlRange(c,range,colour,w,startStr,loading)
          } break;
        case 3:
          var s=range.startContainer===c,e=range.endContainer===c, so=range.startOffset, eo=range.endOffset;
          if(s) {
            startStr=lastID+(count?"+"+count:"")+"*"+so;
            c=c.splitText(so);
          } if(e) {
            if(!loading && window.localStorage!=undefined) {
              var k="adjustHL:"+(location.href+"#").split("#")[0];
              var x=localStorage.getItem(k); if(x) x += "|";
              localStorage.setItem(k,(x?x:"")+startStr+","+lastID+(count?"+"+count:"")+"*"+eo+","+colour) }
            c.splitText(eo-(s?so:0));
          }
          var d=document.createElement("span"); d.setAttribute("style","background-color: "+colour+" !important"); d.textContent=c.textContent; c.parentNode.replaceChild(d,c); c=d }
  } // for
  return startStr
} // adjust0_HighlRange
function adjust0_HighlSel(colour) { adjust0_HighlRange(document.body,document.oldRange,colour,"",""); }
if(new Range().intersectsNode) document.addEventListener('selectionchange',function(){var e=document.getElementById('adjust0_HL');if(window.getSelection().isCollapsed) window.setTimeout(function(){e.style.display='none'},100);else{e.style.display='block';document.oldRange=window.getSelection().getRangeAt(0)}})
//-->
</script>""" % (repr([t.upper() for t in options.leaveTags]),)) # (need to save to oldRange because some browsers collapse selection before highlighter-button's click event is processed, even if it's an href)
        bodyAppend += B("""<script><!--
if(window.localStorage!=undefined) {
  function findNode(dirs) {
    dirs = dirs.split("/");
    var p=dirs[0].split("+"),i,j;
    var n=p[0].length?document.getElementById(p[0]):document.body;
    if(!n) return null;
    if(p.length==2) for(i=0; i < Number(p[1]); i++) n=n.nextSibling;
    for(i=1; i<dirs.length; i++) {
      n=n.firstChild;
      if(dirs[i].length)for(j=0;j<Number(dirs[i]);j++) n=n.nextSibling;
    } return n;
  }
  var i=localStorage.getItem("adjustHL:"+(location.href+"#").split("#")[0]),h;
  if(i!=null) {
    for(h of i.split("|")) {
      var h2=h.split(","); var s=h2[0].split("*"),e=h2[1].split("*");
      var r=document.createRange();
      var ss=findNode(s[0]),ee=findNode(e[0]); if(!(ss&&ee)) continue;
      r.setStart(findNode(s[0]),Number(s[1]));
      r.setEnd(findNode(e[0]),Number(e[1]));
      adjust0_HighlRange(document.body,r,h2[2],"","",true);
    }
  }
}
//-->
</script>""")
    if options.headAppendRuby and not is_password_domain=="PjsUpstream":
        bodyPrepend += B(rubyScript)
        if IsEdge: bodyPrepend += B("<table><tr><td>") # bug observed in Microsoft Edge 17, only when printing: inline-table with table-header-group gobbles whitespace before next inline-table, unless whole document is wrapped in a table cell
    if is_password_domain=="PjsUpstream": pn = None
    elif options.prominentNotice=="htmlFilter": pn = htmlFilterOutput
    elif options.prominentNotice and not is_password_domain: pn = options.prominentNotice
    else: pn = None
    if pn:
        # if JS is available, use fixed positioning (so it still works on sites that do that, in case we're not overriding it via user CSS) and a JS acknowledge button
        styleAttrib="style=\"width: 80% !important; margin: 10%; border: red solid !important; background: black !important; color: white !important; text-align: center !important; display: block !important; left:0px; top:0px; z-index:2147483647; -moz-opacity: 1 !important; filter: none !important; opacity: 1 !important; visibility: visible !important; max-height: 80% !important; overflow: auto !important; \""
        if slow_CSS_switch: # use a slow version for this as well (TODO document that we do this?) (TODO the detect_iframe exclusion of the whole message)
            if not "_WA_warnOK=1" in jsCookieString: bodyPrepend += B("<div id=_WA_warn0 "+styleAttrib+">")+B(pn)+B(r"""<script><!--
if(document.readyState!='complete'&&document.cookie.indexOf("_WA_warnOK=1")==-1)document.write("<br><button style=\"color: black !important;background:#c0c0c0 !important;border: white solid !important\" onClick=\"document.cookie='_WA_warnOK=1;path=/';location.reload(true)\">Acknowledge<\/button>")
//-->
</script></div><script><!--
if(document.getElementById) document.getElementById('_WA_warn0').style.position="fixed"
}
//-->
</script>""")
            #" # (this comment helps XEmacs21's syntax highlighting)
        else: bodyPrepend += B("<div id=_WA_warn0 "+styleAttrib+">")+B(pn)+B(r"""</div><script><!--
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
//-->
</script>""")
        #" # (this comment helps XEmacs21's syntax highlighting)
        # (Above code works around a bug in MSIE 9 by setting the cookie BEFORE doing the removeChild.  Otherwise the cookie does not persist.)
        if options.prominentNotice=="htmlFilter": bodyPrepend = bodyPrepend.replace(B("document.cookie='_WA_warnOK=1;path=/';"),B("")) # don't set the 'seen' cookie if the notice will be different on every page and if that's the whole point of htmlFilter
    if options.headAppendRuby and not is_password_domain=="PjsUpstream":
        if IsEdge: bodyAppend += B("</td></tr></table>")
        bodyAppend += B(rubyEndScript)
    if headAppend or headPrepend: html=addToHead(html,headAppend,headPrepend)
    if bodyPrepend:
        i=htmlFind(html,"<body")
        if i==-1: i = htmlFind(html,"</head")
        if i==-1: i = htmlFind(html,"<html")
        if i>-1:
            i=html.find(B(">"),i)
            if i>-1: html=html[:i+1]+bodyPrepend+html[i+1:]
    if bodyAppend1 and bodyAppend: bodyAppend = B('<span style="float:left">') + bodyAppend1 + B('</span><span style="float:left;width:1em"><br></span><span style="float: right">')+bodyAppend+B('</span><span style="clear:both"></span>') # (the <br> is in case CSS is off or overrides float)
    elif bodyAppend1: bodyAppend = bodyAppend1
    if options.bodyAppend and not (options.js_upstream and not is_password_domain=="PjsUpstream"): bodyAppend = B(options.bodyAppend) + bodyAppend
    elif bodyAppend: bodyAppend=B('<p>')+bodyAppend # TODO: "if" rather than "elif" if options.bodyAppend doesn't start with <center> etc, or if it's just a script with no text; TODO: is '<p>' always what we want if not options.bodyAppend ?
    if bodyAppend:
        i = -1
        if options.bodyAppendGoesAfter:
            it = re.finditer(B(options.bodyAppendGoesAfter),html)
            while True:
                try: i = next(it).end()
                except StopIteration: break
        if i==-1: i=html.lower().rfind(B("</body"))
        if i==-1: i=html.lower().rfind(B("</html"))
        if i==-1: i=len(html)
        html = html[:i]+bodyAppend+html[i:]
    return html
try: next # Python 2.6+
except:
    def next(i): return i.next() # Python 2.5 (.next() renamed .__next__() in 3.x, but that has a built-in next() anyway)

def addToHead(html,headAppend,headPrepend=None):
    i=htmlFind(html,"</head")
    if i==-1: # no head section?
        headAppend = B("<head>")+headAppend+B("</head>")
        i=htmlFind(html,"<body")
        if i==-1: # no body section either?
            i=htmlFind(html,"<html")
            if i > -1: i = html.find(B('>'),i)
            if i==-1: i=html.find(B('>'))
            i += 1 # 0 if we're still -1, else past the '>'
    html = html[:i]+headAppend+html[i:]
    if headPrepend:
        i = htmlFind(html,"<head") # *will* be there after above
        i = html.index(B(">"),i)+1
        html = html[:i]+headPrepend+html[i:]
    return html

#@file: js-links.py
# --------------------------------------------------
# HTML adjustment to enable interaction w.server-run JS
# --------------------------------------------------

class AddClickCodes:
    # add webdriver_click_code + clickID before any #
    # don't put & or = in it due to checkViewsource's arglist processing, try ;id or -txt
    def __init__(self,url): self.url = S(url)
    def init(self,parser):
        self.parser = parser
        self.linkStart = self.href = None
        self.linkTexts = set() ; self.inA = 0
    def handle_starttag(self, tag, attrs):
        if not S(tag)=="a": return
        if self.inA==0: self.currentLinkText = ""
        self.inA += 1
        attrsD = dict(attrs)
        if not ("onclick" in attrsD or B(attrsD.get("href","")).startswith(B("javascript:"))): return # not a js link
        href = B(attrsD.get("href",""))
        if B('#') in href: href = href[href.index(B('#')):]
        else: href = B("")
        if "id" in attrsD: # we can rewrite it straight away
            attrsD["href"] = B(self.url) + B(webdriver_click_code) + B(';') + B(attrsD["id"]) + B(href)
        else: # we have to wait to see the text inside it
            self.linkStart = len(self.parser.out) # assumes further processing hasn't already appended anything
            self.href = href
            self.original_href = B(attrsD.get("href","#"))
            if self.original_href.startswith(B("javascript:")): self.original_href = B("#") # take it out
            attrsD["href"] = B('"PLACEHOLDER"') + B(webdriver_click_code) # make sure there's quotes in the placeholder so we always get quoted by encAtt (simplifies the back-off replace below)
        return tag, attrsD
    def handle_endtag(self, tag):
        if not S(tag)=="a": return
        self.inA = max(self.inA-1,0)
        if not self.linkStart: return
        # DON'T try to write 'shortest unique text', because
        # that can change if another link is clicked (e.g. if
        # clicking the other link makes it disappear) and we
        # don't know what state the page will be in + could
        # end up with duplicate URLs.  Write full link text.
        if self.currentLinkText in self.linkTexts: replaceWith = B(self.original_href).replace(B('&'),B('&amp;')).replace(B('"'),B('&quot;')) # oops, not unique, back off
        else: replaceWith = B(self.url) + B(webdriver_click_code) + B('-') + B(self.currentLinkText) + B(self.href)
        self.linkTexts.add(self.currentLinkText)
        if type(self.parser.out[self.linkStart])==bytes: self.parser.out[self.linkStart] = self.parser.out[self.linkStart].replace(B('&quot;PLACEHOLDER&quot;') + B(webdriver_click_code),B(replaceWith))
        else: self.parser.out[self.linkStart] = self.parser.out[self.linkStart].replace('&quot;PLACEHOLDER&quot;' + S(webdriver_click_code),S(replaceWith)) # TODO: is this line ever used?
        self.linkStart = None ; self.currentLinkText = ""
    def handle_data(self,data):
        if self.inA==1:
            if not self.currentLinkText: self.currentLinkText = data # Python 3: could be either string or bytes
            else: self.currentLinkText += data

#@file: user-switches.py
# --------------------------------------------------
# Options for allowing user to switch stylesheets etc
# --------------------------------------------------

detect_iframe = """(window.frameElement && window.frameElement.nodeName=="IFRAME" && function(){var i=window.location.href.indexOf("/",7); return (i>-1 && window.top.location.href.slice(0,i)==window.location.href.slice(0,i))}())""" # expression that's true if we're in an iframe that belongs to the same site, so can omit reminders etc
def reloadSwitchJS(cookieName,jsCookieString,flipLogic,readableName,cookieDomainStrsJS,cookieExpires,extraCondition=None):
    # writes a complete <script> to switch something on/off by cookie and reload (TODO: non-JS version would be nice, but would mean intercepting more URLs)
    # if flipLogic, "cookie=1" means OFF, default ON
    # document.write includes spaces around it
    isOn,setOn,setOff = (cookieName+"=1" in jsCookieString),"1","0"
    if flipLogic: isOn,setOn,setOff = (not isOn),setOff,setOn
    if extraCondition: extraCondition = "&&"+extraCondition
    else: extraCondition = ""
    if cssReload_cookieSuffix and isOn: return r"""<script><!--
if(!%s%s&&document.readyState!='complete')document.write(" %s: On | "+'<a href="'+location.href.replace(location.hash,"")+'%s%s=%s">Off<\/a> ')
//-->
</script>""" % (detect_iframe,extraCondition,readableName,cssReload_cookieSuffix,cookieName,setOff) # TODO: create a unique id for the link and # it ? (a test of this didn't always work on Opera Mini though)
    elif cssReload_cookieSuffix: return r"""<script><!--
if(!%s%s&&document.readyState!='complete')document.write(" %s: "+'<a href="'+location.href.replace(location.hash,"")+'%s%s=%s">On<\/a> | Off ')
//-->
</script>""" % (detect_iframe,extraCondition,readableName,cssReload_cookieSuffix,cookieName,setOn)
    elif isOn: return r"""<script><!--
if(!%s%s&&document.readyState!='complete')document.write(" %s: On | "+'<a href="javascript:%s;location.reload(true)">Off<\/a> ')
//-->
</script>""" % (detect_iframe,extraCondition,readableName,";".join((r"document.cookie=\'%s=%s%s;expires=%s;path=/\'" % (cookieName,setOff,c,cookieExpires)) for c in cookieDomainStrsJS))
    else: return r"""<script><!--
if(!%s%s&&document.readyState!='complete')document.write(" %s: "+'<a href="javascript:%s;location.reload(true)">On<\/a> | Off ')
//-->
</script>""" % (detect_iframe,extraCondition,readableName,";".join((r"document.cookie=\'%s=%s%s;expires=%s;path=/\'" % (cookieName,setOn,c,cookieExpires)) for c in cookieDomainStrsJS))

def reloadSwitchJSMultiple(cookieName,jsCookieString,flipInitialItems,readableNames,cookieDomainStrsJS,cookieExpires):
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
            if i==options.htmlFilterCollapse-1:
                spanStart = len(r)
                r.append('<span id=adjustNoFilter>')
                # (gets here if len(readableNames)>options.htmlFilterCollapse; use this as ID because we already have transform_in_selected_tag on it) (NB if quoting the id, use r'\"' because we're in a document.write)
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
        else: r.append(r""""+'<a href="javascript:%s;location.reload(true)">'+"%s<"+"\/a>""" % (";".join((r"document.cookie=\'%s=%s%s;expires=%s;path=/\'" % (cookieName,chk,c,cookieExpires)) for c in cookieDomainStrsJS),rN))
    if spanStart: r.append('<"+"/span>')
    r.append(' ")')
    if spanStart: r.append(r';if(document.getElementById){var v=document.getElementById("adjustNoFilter");if(v.innerHTML){v.OIH=v.innerHTML;if(v.OIH==v.innerHTML)v.innerHTML="<a href=\"#adjustNoFilter\" onClick=\"this.parentNode.innerHTML=this.parentNode.OIH;return false\">More<"+"/A>"; }}') # (hide the span by default, if browser has enough JS support to do it) (TODO: could do it with non-innerHTML DOM functionality if necessary, but that's more long-winded and might also need to look out for non-working 'this' functionality)
    r.append('}\n//-->\n</script>')
    return "".join(r)

def findFilter(reqH,filterNo):
    if not options.htmlFilterName: return options.htmlFilter # unconditional
    if filterNo and '#' in options.htmlFilter:
        return options.htmlFilter.split('#')[filterNo]
    anf = reqH.getCookie("adjustNoFilter")
    if not anf: anf = "0"
    elif '-' in anf: anf = anf[anf.rindex("-")+1:]
    if anf=="1": return None
    elif '#' in options.htmlFilter:
        htmlFilter = options.htmlFilter.split('#')
        if anf=="0": return htmlFilter[0]
        else: return htmlFilter[int(anf)-1]
    else: return options.htmlFilter

def detect_renderCheck(): return r"""(document.getElementsByTagName && function(){var b=document.getElementsByTagName("BODY")[0],d=document.createElement("DIV"),s=document.createElement("SPAN"); if(!(b.appendChild && b.removeChild && s.innerHTML))return 0; d.appendChild(s); function wid(chr) { s.innerHTML = chr; b.appendChild(d); var width = s.offsetWidth; b.removeChild(d); return width; } var w1=wid("\u%s"),w2=wid("\uffff"),w3=wid("\ufffe"),w4=wid("\u2fdf"); return (w1!=w2 && w1!=w3 && w1!=w4)}())""" % options.renderCheck
# ffff, fffe - guaranteed invalid by Unicode, but just might be treated differently by browsers
# 2fdf unallocated character at end of Kangxi radicals block, hopefully won't be used
#  do NOT use fffd, it's sometimes displayed differently to other unrenderable characters
# Works even in Opera Mini, which must somehow communicate the client's font metrics to the proxy

def addCssHtmlAttrs(html,attrsToAdd):
   i=htmlFind(html,"<body")
   if i==-1: return html # TODO: what of HTML documents that lack <body> (and frameset), do we add one somewhere? (after any /head ??)
   i += 5 # after the "<body"
   j = html.find(B('>'), i)
   if j==-1: return html # ?!?
   attrs = html[i:j]
   attrsToAdd = B(attrsToAdd)
   for a in re.findall(B(r'[A-Za-z_0-9]+\='),attrsToAdd): attrs = attrs.replace(a,B("old")+a) # disable corresponding existing attributes (if anyone still uses them these days)
   return html[:i] + attrs + B(" ") + attrsToAdd + html[j:]

#@file: view-source.py
# --------------------------------------------------
# View-source support etc
# --------------------------------------------------

def ampEncode(t):
    if type(t)==bytes: return t.replace(B("&"),B("&amp;")).replace(B("<"),B("&lt;")).replace(B(">"),B("&gt;"))
    else: return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def txt2html(t):
    t = ampEncode(t)
    if type(t)==bytes: return t.replace(B("\n"),B("<br>"))
    else: return t.replace("\n","<br>")

def ampDecode(t): return t.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&") # called with unicode in Python 2 and str in Python 3, either way this should just work
# ampDecode is needed if passing text with entity names to Renderer below (which ampEncode's its result and we might want it to render & < > chars)
# (shouldn't need to cope with other named entities: find_text_in_HTML already processes all known ones in htmlentitydefs, and LXML also decodes all the ones it knows about)

#@file: image-render.py
# --------------------------------------------------
# Support old phones etc: CJK characters to images
# --------------------------------------------------

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
    def getSize(self,unitext):
        if options.renderBlocks and self.hanziW:
            w,h = self.hanziW*len(unitext), self.hanziH
        else:
            f = self.font()
            if hasattr(f,"getsize"): w,h = f.getsize(unitext) # PIL, and Pillow up to 9.5
            else: _,_,w,h = f.getbbox(unitext) # Pillow 10
            if options.renderBlocks:
                self.hanziW = int(w/len(unitext))
                self.hanziH = h
        return w,h
    def getMarkup_inner(self,unitext):
        w,h = self.getSize(unitext)
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
        try: text=imgDecode(uri[len(options.renderPath):])
        except: return False # invalid base64 = fall back to fetching the remote site
        size = self.getSize(text) # w,h
        if options.renderInvert: bkg,fill = 0,1
        else: bkg,fill = 1,0
        img=Image.new("1",size,bkg) # "1" is 1-bit
        ImageDraw.Draw(img).text((0, 0),text,font=self.font(),fill=fill)
        dat=BytesIO()
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
            if unitext in letters+digits+"_.-": return unitext
            elif 0xf<ord(unitext): return hex(ord(unitext))[2:]
        elif o <= 0xFFFF: # (TODO: don't need that test if true for all our render ranges)
            # TODO: make this optional?  hex(ord(u))[-4:] is nearly 5x faster than b64encode(u.encode('utf-8')) in the case of 1 BMP character (it's faster than even just the .encode('utf-8') part), but result could also decode with base64, so we have to add an extra '_' byte to disambiguate, which adds to the traffic (although only a small amount compared to IMG markup anyway)
            return '_'+hex(o)[-4:]
    return S(base64.b64encode(unitext.encode('utf-8')))
def imgDecode(code):
    if len(code)==1: return code
    elif len(code) <= 3: return unichr(int(code,16))
    elif code.startswith("_"): return unichr(int(code[1:],16)) # (see TODO above)
    else: return base64.b64decode(code).decode('utf-8','replace')

#@file: ping.py
# --------------------------------------------------
# Support pinging Dynamic DNS services and PiMote
# --------------------------------------------------

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
        IOLoopInstance().add_callback(lambda *args:self.queryIP())
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
                addr = S(miniupnpc.externalipaddress())
              except: addr = ""
              if addr == self.currentIP: IOLoopInstance().add_callback(lambda *args:(self.newIP(addr),IOLoopInstance().add_timeout(time.time()+options.ip_check_interval2,lambda *args:self.queryLocalIP()))) # (add_timeout doesn't always work when not from the IOLoop thread ??)
              else: IOLoopInstance().add_callback(self.queryIP)
            threading.Thread(target=run,args=()).start()
            return
        def handleResponse(r):
            curlFinished()
            if r.error or not B(self.currentIP) in B(r.body):
                return self.queryIP()
            # otherwise it looks like the IP is unchanged:
            self.newIP(self.currentIP) # in case forceTime is up
            IOLoopInstance().add_timeout(time.time()+options.ip_check_interval2,lambda *args:self.queryLocalIP())
        if ip_query_url2_user:
            # some routers etc insist we send the non-auth'd request first, and the credentials only when prompted (that's what Lynx does with the -auth command line), TODO do we really need to do this every 60secs? (do it only if the other way gets an error??) but low-priority as this is all local-net stuff (and probably a dedicated link to the switch at that)
            if ip_url2_pwd_is_fname: pwd=open(ip_query_url2_pwd).read().strip() # re-read each time
            else: pwd = ip_query_url2_pwd
            callback = lambda r:(curlFinished(),doCallback(None,MyAsyncHTTPClient().fetch,handleResponse, ip_query_url2, auth_username=ip_query_url2_user,auth_password=pwd))
        else: callback = handleResponse
        doCallback(None,MyAsyncHTTPClient().fetch,callback,ip_query_url2)
    def queryIP(self):
        # Queries ip_query_url, and, after receiving a response (optionally via retries if ip_query_aggressive), sets a timeout to go back to queryLocalIP after ip_check_interval (not ip_check_interval2)
        debuglog("queryIP")
        if not "://" in options.ip_query_url: return self.newIP(options.ip_query_url) # not a URL: assume static IP
        def handleResponse(r):
            curlFinished()
            if not r.error:
                self.newIP(S(r.body.strip()))
                if self.aggressive_mode:
                    logging.info("ip_query_url got response, stopping ip_query_aggressive")
                    self.aggressive_mode = False
            elif options.ip_query_aggressive:
                if not self.aggressive_mode:
                    logging.info("ip_query_url got error, starting ip_query_aggressive")
                    self.aggressive_mode = True
                    global pimote_may_need_override ; pimote_may_need_override = True # in case we're running that as well and it fails to detect the router issue via its own DNSRequest (happened once on Zyxel AMG1302-T11C: upnp stopped, connectivity stopped so got here, even DHCP stopped but somehow DNSRequest kept going without returning the internal-only IP or error, so better put this path in too)
                return self.queryIP()
            IOLoopInstance().add_timeout(time.time()+options.ip_check_interval,lambda *args:self.queryLocalIP())
        doCallback(None,MyAsyncHTTPClient().fetch,handleResponse,options.ip_query_url)
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
        sp=subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE)
        self.forceTime=time.time()+options.ip_force_interval
        def retry(sp):
            triesLeft = options.ip_change_tries-1 # -ve if inf
            while triesLeft:
                if not sp.wait():
                    logging.info("ip_change_command succeeded for "+ip)
                    return
                logging.info("ip_change_command failed for "+ip+", retrying in "+str(options.ip_change_delay)+" seconds")
                time.sleep(options.ip_change_delay)
                sp=subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE)
                triesLeft -= 1
            if sp.wait(): logging.error("ip_change_command failed for "+ip)
            else: logging.info("ip_change_command succeeded for "+ip)
        threading.Thread(target=retry,args=(sp,)).start()

pimote_may_need_override=False
def pimote_thread():
    routerIP, ispDomain, internalResponse, deviceNo = options.pimote.split(',')
    try: deviceNo = int(deviceNo)
    except: pass # "all" etc is OK
    import DNS # apt-get install python-dns
    if deviceNo=="all": p17,p22,p23 = 1,1,0
    elif deviceNo==1:   p17,p22,p23 = 1,1,1
    elif deviceNo==2:   p17,p22,p23 = 1,0,1
    elif deviceNo==3:   p17,p22,p23 = 0,1,1
    elif deviceNo==4:   p17,p22,p23 = 0,0,1
    # TODO: unofficial 1 0 0 and 0 1 0 can be programmed (taking number of devices up to 6), + a 7th can be programmed on 000 but only for switch-on (as '0000' just resets the board; can switch off w. 'all').  Can program multiple switches to respond to same signal.
    else: raise Exception("Invalid Pi-mote device number "+repr(deviceNo))
    def t():
      lastOK = True
      helper_threads.append('PiMote')
      global pimote_may_need_override
      while options.pimote:
        if pimote_may_need_override: ok=False
        else:
          try:
            r = DNS.DnsRequest(server=routerIP,timeout=5).req(name=ispDomain,qtype="A")
            ok = r.answers and not(any(i['data']==internalResponse for i in r.answers))
          except: ok = False
        if ok or lastOK:
            for i in xrange(30): # TODO: configurable?
                if options.pimote and not pimote_may_need_override: time.sleep(1)
                else: break
            lastOK = ok ; continue
        if pimote_may_need_override: reason = "" # will be evident from previous log line
        else: reason = " (%s lookup fail)" % ispDomain
        logging.info("PiMote: power-cycling the router"+reason)
        # Takes 2 minutes (because we have no direct way to verify
        # the sockets have received our signal, so just have to make
        # the hopefully-worst-case assumptions)
        def w(g,v):
            f = "/sys/class/gpio/gpio%d/value" % g
            try: open(f,'w').write(str(v)+"\n") # not sure if \n really needed
            except: logging.error("PiMote: unable to write to "+f)
        for OnOff in [0, 1]:
            w(25,0) # stop TX, just in case
            w(17,p17), w(22,p22), w(23,p23), w(27,OnOff)
            for Try in range(10): # sometimes the signal fails
                w(25,1) # start TX
                time.sleep(4)
                w(25,0) # stop TX
                time.sleep(1)
        time.sleep(199) # give it time to start up before we test it again, plus time to ssh in and fix if we're in a reboot cycle due to ISP being taken over and deleting their old domain or something
        pimote_may_need_override = False
      helper_threads.remove('PiMote')
    threading.Thread(target=t,args=()).start()

def open_upnp():
    if options.ip_query_url2=="upnp":
        global miniupnpc ; import miniupnpc # sudo pip install miniupnpc or apt-get install python-miniupnpc
        miniupnpc = miniupnpc.UPnP()
        miniupnpc.discoverdelay=200

#@file: delegate.py
# --------------------------------------------------
# Support for "slow server delegates to fast server"
# (e.g. always-on Raspberry Pi + sometimes-on dev box)
# --------------------------------------------------

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
        IOLoopInstance().add_callback(self)
    def __call__(self):
     if options.fasterServerNew:
         # TODO: might be bytes in the queue if this server somehow gets held up.  Could try readUntilClose(client,close,stream)
         if (self.client and self.count >= 2) or self.pendingClient: # it didn't call serverOK on 2 consecutive seconds (TODO: customizable?), or didn't connect within 1sec - give up
             try: self.pendingClient.close()
             except: pass
             try: self.client.close()
             except: pass
             self.pendingClient = self.client = None
             self.interval = FSU_set(False,self.interval)
             return IOLoopInstance().add_timeout(time.time()+self.interval,lambda *args:checkServer())
         elif self.client: self.count += 1
         else: # create new self.pendingClient
             server,port = options.fasterServer.rsplit(':',1)
             self.pendingClient = tornado.iostream.IOStream(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0))
             def send_request(*args):
                 try:
                     self.pendingClient.write(B('GET /ping2 HTTP/1.0\r\nUser-Agent: ping\r\n\r\n'))
                     self.client = self.pendingClient
                     self.pendingClient = None
                     readUntilClose(self.client,lambda *args:True,lambda *args:self.serverOK())
                 except: pass
             doCallback(None,self.pendingClient.connect,send_request,(server,int(port)))
         IOLoopInstance().add_timeout(time.time()+1,lambda *args:checkServer()) # check back in 1sec to see if it connected OK (should do if it's local)
     else: # old version - issue HTTP requests to /ping
        def callback(r):
            self.interval = FSU_set(not r.error,self.interval)
            if not fasterServer_up: self.client = None
            IOLoopInstance().add_timeout(time.time()+self.interval,lambda *args:checkServer())
        if not self.client:
            self.client=MyAsyncHTTPClient()
            curlFinished() # we won't count it here
        doCallback(None,self.client.fetch,callback,"http://"+options.fasterServer+"/ping",connect_timeout=1,request_timeout=1,user_agent="ping",use_gzip=False)
    def serverOK(self):
        # called when any chunk is available from the stream (normally once a second, but might catch up a few bytes if we've delayed for some reason)
        self.interval = FSU_set(True,0)
        self.count = 0
checkServer=checkServer()

#@file: debug.py
# --------------------------------------------------
# Debugging and status dumps
# --------------------------------------------------

lastDebugMsg = "None"
def debuglog(msg,logRepeats=True,stillIdle=False):
    # This function *must* return None.
    global lastDebugMsg, profileIdle
    if not stillIdle: profileIdle = False
    if logRepeats or not msg==lastDebugMsg:
        if not options.logDebug: logging.debug(msg)
        elif options.background: logging.info(msg)
        else: sys.stderr.write(time.strftime("%X ")+msg+"\n")
    lastDebugMsg = msg ; global status_dump_requested
    if status_dump_requested:
        status_dump_requested = False
        showProfile(pjsOnly=True) # TODO: document that SIGUSR1 also does this? (but doesn't count reqsInFlight if profile wasn't turned on, + it happens on next debuglog call (and shown whether toggled on OR off, to allow rapid toggle just to show this))
def initLogDebug():
    if hasattr(signal,"SIGUSR1") and not wsgi_mode:
        signal.signal(signal.SIGUSR1, toggleLogDebug)
        if hasattr(signal,"SIGUSR2"):
            signal.signal(signal.SIGUSR2, requestStatusDump)
status_dump_requested = False
def toggleLogDebug(*args):
    "SIGUSR1 handler (see logDebug option help)"
    # Don't log anything from the signal handler
    # (as another log message might be in progress)
    # Just toggle the logDebug flag
    options.logDebug = not options.logDebug
    requestStatusDump()
def requestStatusDump(*args):
    "SIGUSR2 handler (requests status dump, currently from JS proxy only)" # TODO: document this (and that SIGUSR1 also calls it)
    global status_dump_requested ; status_dump_requested = True

#@file: end.py
# --------------------------------------------------
# And finally...
# --------------------------------------------------

if __name__ == "__main__": main()
else: setup_defined_globals() # for wrapper import
